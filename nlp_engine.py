"""
Context-Aware NLP & Contradiction Detection Engine
Uses Sentence Transformers for semantic embeddings and an intelligent Context-Aware
Logic Resolver to distinguish between:
🟢 Consistent information
🟡 Contextual differences (e.g., CSM DBMS vs CSD DBMS)
🔴 Potential contradictions (e.g., CSM DBMS Oct 10 vs CSM DBMS Oct 11)
⚪ Uncertain cases
"""

import re
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# Global model cache to avoid re-downloading/re-loading on every call
_EMBEDDING_MODEL = None


def get_embedding_model():
    """
    Lazy loader for SentenceTransformer model ('all-MiniLM-L6-v2').
    Lightweight, fast, and highly accurate for sentence semantics.
    """
    global _EMBEDDING_MODEL
    if _EMBEDDING_MODEL is None:
        try:
            from sentence_transformers import SentenceTransformer
            _EMBEDDING_MODEL = SentenceTransformer('all-MiniLM-L6-v2')
        except Exception as e:
            print(f"Warning: SentenceTransformer initialization error: {e}")
            _EMBEDDING_MODEL = None
    return _EMBEDDING_MODEL


# Common date patterns (e.g., Oct 10, October 10th, 10-10-2026, 2026/10/10)
DATE_REGEX = re.compile(
    r'\b(?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2}(?:st|nd|rd|th)?(?:,?\s+\d{4})?'
    r'|\d{1,2}[/-]\d{1,2}[/-]\d{2,4}'
    r'|\d{4}[/-]\d{1,2}[/-]\d{1,2})\b',
    re.IGNORECASE
)

# Number with unit or currency (e.g., $500, 16GB, 80%, 25 days)
VALUE_REGEX = re.compile(
    r'(?:[\$€₹£]\s*\d+(?:,\d+)*(?:\.\d+)?|\b\d+(?:,\d+)*(?:\.\d+)?\s*(?:%|gb|mb|tb|days|months|years|hours|credits|usd|inr)?\b)',
    re.IGNORECASE
)

# Common negation words
NEGATION_WORDS = {"not", "never", "no", "cannot", "won't", "shouldn't", "don't", "neither", "prohibited", "banned", "forbidden"}

# Common scope indicators: branch, department, audience, device, version, condition
SCOPE_KEYWORDS = {
    "csm", "csd", "cse", "it", "ece", "eee", "mech", "civil", "aiml", "aids",
    "ug", "pg", "phd", "btech", "mtech", "bba", "mca",
    "faculty", "student", "students", "staff", "admin", "client", "server",
    "mobile", "desktop", "android", "ios", "windows", "linux", "mac",
    "online", "offline", "morning", "evening", "batch a", "batch b", "v1", "v2"
}


def extract_context_features(statement: str) -> Dict[str, Any]:
    """
    Extracts structured entities, contextual scopes, values, dates, and polarity from a statement.
    """
    clean_s = statement.strip()
    words = re.findall(r'\b[A-Za-z0-9_-]+\b', clean_s)
    lower_words = [w.lower() for w in words]

    # 1. Dates
    dates = [d.strip() for d in DATE_REGEX.findall(clean_s)]

    # 2. Values & Numbers
    raw_vals = VALUE_REGEX.findall(clean_s)
    # Filter out standalone calendar numbers like '10' if already in dates
    values = [v.strip() for v in raw_vals if not any(v in d for d in dates)]
    val_lower = [v.lower() for v in values]

    # 3. Contextual Scope Tokens (e.g. CSM, CSD, Faculty, Student, Online, Server, Mobile, etc.)
    scopes = set()
    for w in words:
        wl = w.lower()
        # If token is part of a value/number, it is a predicate value, NOT a context scope
        if any(w in v or wl in v.lower() for v in values) or any(c.isdigit() for c in w):
            continue
            
        if wl in SCOPE_KEYWORDS:
            scopes.add(wl.upper())
        # Acronyms (e.g., CSM, CSD, AI, DBMS, HR, IT) - must be pure letters
        elif len(w) >= 2 and w.isupper() and w.isalpha():
            scopes.add(w)

    # 4. Negation / Polarity check
    has_negation = any(nw in lower_words for nw in NEGATION_WORDS)

    # 5. Core Subject Anchor (words without dates/numbers/stop words)
    stop_words = {"the", "a", "an", "is", "are", "was", "were", "be", "on", "at", "for", "in", "to", "of", "and", "or", "by"}
    topic_tokens = set([w.lower() for w in words if len(w) > 2 and w.lower() not in stop_words and not w.isdigit()])

    return {
        "dates": dates,
        "values": values,
        "scopes": scopes,
        "has_negation": has_negation,
        "topic_tokens": topic_tokens,
        "text": clean_s
    }


def compare_statement_pair(
    stmt_a: str,
    stmt_b: str,
    similarity_score: float
) -> Tuple[str, float, str]:
    """
    Context-Aware Logic Resolver.
    
    Compares two statements and determines if they represent:
    - 🟢 Consistent information
    - 🟡 Contextual difference
    - 🔴 Potential contradiction
    - ⚪ Uncertain case
    
    Returns:
        (category, confidence_score, explanation_reason)
    """
    fa = extract_context_features(stmt_a)
    fb = extract_context_features(stmt_b)

    # Check shared topic tokens
    shared_topics = fa["topic_tokens"].intersection(fb["topic_tokens"])
    
    # Check context scopes (e.g., CSM vs CSD)
    scopes_a = fa["scopes"]
    scopes_b = fb["scopes"]
    shared_scopes = scopes_a.intersection(scopes_b)
    diff_scopes_a = scopes_a - scopes_b
    diff_scopes_b = scopes_b - scopes_a

    # Check Dates & Values
    dates_a = set(d.lower() for d in fa["dates"])
    dates_b = set(d.lower() for d in fb["dates"])
    common_dates = dates_a.intersection(dates_b)
    has_conflicting_dates = bool(dates_a and dates_b and not common_dates)

    vals_a = set(v.lower() for v in fa["values"])
    vals_b = set(v.lower() for v in fb["values"])
    common_vals = vals_a.intersection(vals_b)
    has_conflicting_vals = bool(vals_a and vals_b and not common_vals)

    # Polarity conflict (e.g., one negated, one positive)
    has_polarity_clash = (fa["has_negation"] != fb["has_negation"])

    # -------------------------------------------------------------
    # CASE 1: Exact / Near-Identical High Semantic Consistency (🟢)
    # -------------------------------------------------------------
    if similarity_score >= 0.88 and not has_conflicting_dates and not has_conflicting_vals and not has_polarity_clash:
        # Check if scopes match or both lack specific scopes
        if not (diff_scopes_a or diff_scopes_b) or shared_scopes:
            conf = min(0.98, similarity_score + 0.05)
            reason = "Both documents state congruent facts with matching context and compatible assertions."
            return "🟢 Consistent Information", conf, reason

    # -------------------------------------------------------------
    # CASE 2: Contextual Difference (🟡)
    # Different contextual scopes (e.g., CSM vs CSD) but overlapping topic
    # e.g., CSM DBMS - Oct 10 vs CSD DBMS - Oct 11
    # -------------------------------------------------------------
    if (diff_scopes_a or diff_scopes_b) and (shared_topics or shared_scopes):
        # Format the distinguishing scopes
        scope_diff_desc = f"'{list(diff_scopes_a)[0]}'" if diff_scopes_a else "Doc A scope"
        scope_diff_desc_b = f"'{list(diff_scopes_b)[0]}'" if diff_scopes_b else "Doc B scope"

        val_diff_note = ""
        if has_conflicting_dates:
            val_diff_note = f" (dates: '{list(fa['dates'])[0]}' vs '{list(fb['dates'])[0]}')"
        elif has_conflicting_vals:
            val_diff_note = f" (values: '{list(fa['values'])[0]}' vs '{list(fb['values'])[0]}')"

        confidence = 0.88 if (diff_scopes_a and diff_scopes_b) else 0.82
        reason = (
            f"Contextual scope differs: Statement A applies to {scope_diff_desc} while "
            f"Statement B applies to {scope_diff_desc_b}{val_diff_note}. "
            f"Because the target groups or conditions differ, this is a valid contextual variation rather than a contradiction."
        )
        return "🟡 Contextual Difference", confidence, reason

    # -------------------------------------------------------------
    # CASE 3: Potential Contradiction (🔴)
    # Same context/topic, but incompatible dates, values, or polarity
    # e.g., CSM DBMS - Oct 10 vs CSM DBMS - Oct 15
    # -------------------------------------------------------------
    if has_conflicting_dates:
        # If contexts are identical or shared
        d_a_str = list(fa['dates'])[0]
        d_b_str = list(fb['dates'])[0]
        shared_ctx_str = f" for '{list(shared_scopes)[0]}'" if shared_scopes else ""
        confidence = 0.94 if shared_scopes else 0.86
        reason = (
            f"Direct date mismatch{shared_ctx_str}: Statement A specifies '{d_a_str}' "
            f"whereas Statement B specifies '{d_b_str}' for the same subject."
        )
        return "🔴 Potential Contradiction", confidence, reason

    if has_conflicting_vals:
        v_a_str = list(fa['values'])[0]
        v_b_str = list(fb['values'])[0]
        shared_ctx_str = f" for '{list(shared_scopes)[0]}'" if shared_scopes else ""
        confidence = 0.92 if shared_scopes else 0.84
        reason = (
            f"Quantitative conflict{shared_ctx_str}: Statement A claims '{v_a_str}' "
            f"while Statement B claims '{v_b_str}' on the same subject."
        )
        return "🔴 Potential Contradiction", confidence, reason

    if has_polarity_clash and similarity_score >= 0.65:
        reason = (
            "Polarity contradiction: One statement asserts an affirmative rule/condition "
            "while the other contains an explicit negation ('not', 'no', 'prohibited')."
        )
        return "🔴 Potential Contradiction", 0.90, reason

    # -------------------------------------------------------------
    # CASE 4: Consistent (Medium-High similarity without conflict) (🟢)
    # -------------------------------------------------------------
    if similarity_score >= 0.75:
        reason = "Statements express aligned facts and conditions across both documents."
        return "🟢 Consistent Information", round(similarity_score, 2), reason

    # -------------------------------------------------------------
    # CASE 5: Uncertain Cases (⚪)
    # -------------------------------------------------------------
    confidence = round(max(0.50, similarity_score), 2)
    reason = (
        "Statements share thematic vocabulary, but lack explicit qualifying attributes "
        "or sufficient contextual details to conclusively confirm consistency or conflict."
    )
    return "⚪ Uncertain Case", confidence, reason


def analyze_documents(
    extracted_records: List[Dict[str, Any]],
    similarity_threshold: float = 0.40,
    top_k_per_statement: int = 3
) -> List[Dict[str, Any]]:
    """
    Main analysis pipeline:
    1. Extracts embeddings using Sentence Transformers.
    2. Compares statements across different documents using cosine similarity.
    3. Filters out candidate pairs below similarity threshold.
    4. Evaluates context awareness and classifies each pair.
    
    Returns:
        List of structured comparison records.
    """
    if len(extracted_records) < 2:
        return []

    # Get distinct documents
    doc_names = list(set(r["doc_name"] for r in extracted_records))
    if len(doc_names) < 2:
        # If user only uploaded one document, compare statements across distinct pages or sections
        pass

    texts = [r["statement"] for r in extracted_records]
    model = get_embedding_model()

    if model is not None:
        embeddings = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
        # Cosine similarity matrix
        sim_matrix = np.dot(embeddings, embeddings.T)
    else:
        # Fallback to TF-IDF if SentenceTransformer not loaded
        from sklearn.feature_extraction.text import TfidfVectorizer
        vectorizer = TfidfVectorizer(stop_words='english')
        tfidf_mat = vectorizer.fit_transform(texts)
        sim_matrix = cosine_similarity(tfidf_mat, tfidf_mat)

    n = len(extracted_records)
    results = []
    seen_pairs = set()

    for i in range(n):
        rec_a = extracted_records[i]
        # Sort potential matching indices by similarity score
        sorted_indices = np.argsort(sim_matrix[i])[::-1]
        
        matches_found = 0
        for j in sorted_indices:
            if i == j:
                continue

            rec_b = extracted_records[j]
            # Ensure we compare statements from different documents
            # (or if same document, from different pages)
            if len(doc_names) > 1 and rec_a["doc_name"] == rec_b["doc_name"]:
                continue

            # Deduplicate pair (i, j) vs (j, i)
            pair_key = tuple(sorted([rec_a["statement"], rec_b["statement"]]))
            if pair_key in seen_pairs:
                continue

            score = float(sim_matrix[i, j])
            if score < similarity_threshold:
                # Since array is sorted descending, we can break
                break

            category, confidence, reason = compare_statement_pair(
                rec_a["statement"],
                rec_b["statement"],
                score
            )

            results.append({
                "doc_a": rec_a["doc_name"],
                "page_a": rec_a["page_num"],
                "statement_a": rec_a["statement"],
                "context_a": rec_a.get("full_context", ""),
                "doc_b": rec_b["doc_name"],
                "page_b": rec_b["page_num"],
                "statement_b": rec_b["statement"],
                "context_b": rec_b.get("full_context", ""),
                "category": category,
                "confidence": confidence,
                "reason": reason,
                "similarity_score": score
            })

            seen_pairs.add(pair_key)
            matches_found += 1
            if matches_found >= top_k_per_statement:
                break

    # Sort results: Contradictions first, then Contextual Differences, then Uncertain, then Consistent
    priority = {
        "🔴 Potential Contradiction": 1,
        "🟡 Contextual Difference": 2,
        "⚪ Uncertain Case": 3,
        "🟢 Consistent Information": 4
    }
    results.sort(key=lambda x: (priority.get(x["category"], 5), -x["confidence"]))

    return results
