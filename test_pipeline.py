"""
Automated Test Suite for Context-Aware AI Document Contradiction Detector.
Validates:
1. PyMuPDF and python-docx extraction with metadata (page/section).
2. The user's core context-aware benchmark:
   - 'CSM DBMS - Oct 10' vs 'CSD DBMS - Oct 11' -> Contextual difference
   - 'CSM DBMS - Oct 10' vs 'CSM DBMS - Oct 15' -> Potential contradiction
3. Hardware spec comparison (Mobile 4GB vs Server 32GB vs Server 16GB).
4. SQLite persistence (saving session, reading results back).
"""

import os
import sys

# Ensure UTF-8 output on Windows terminal
if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from extractor import extract_document
from nlp_engine import compare_statement_pair, analyze_documents
from database import init_db, save_analysis_session, list_saved_sessions, get_session_results

def run_tests():
    print("=" * 60)
    print("STARTING CONTRADICTION DETECTOR VALIDATION SUITE")
    print("=" * 60)

    # 1. Test User's Core Context-Aware Criterion
    print("\n[TEST 1] Testing User Benchmark Cases...")
    
    # Case A: CSM DBMS Oct 10 vs CSD DBMS Oct 11
    # Different context (CSM vs CSD) -> Must be Contextual Difference!
    cat_a, conf_a, reason_a = compare_statement_pair(
        "CSM DBMS - Oct 10",
        "CSD DBMS - Oct 11",
        0.85
    )
    print(f"Case A: 'CSM DBMS - Oct 10' vs 'CSD DBMS - Oct 11'")
    print(f" -> Result: {cat_a} (Confidence: {conf_a})")
    print(f" -> Reason: {reason_a}")
    assert "Contextual" in cat_a, f"Expected Contextual Difference but got {cat_a}"

    # Case B: CSM DBMS Oct 10 vs CSM DBMS Oct 15
    # Same context (CSM DBMS), conflicting dates -> Must be Potential Contradiction!
    cat_b, conf_b, reason_b = compare_statement_pair(
        "CSM DBMS - Oct 10",
        "CSM DBMS - Oct 15",
        0.90
    )
    print(f"\nCase B: 'CSM DBMS - Oct 10' vs 'CSM DBMS - Oct 15'")
    print(f" -> Result: {cat_b} (Confidence: {conf_b})")
    print(f" -> Reason: {reason_b}")
    assert "Contradiction" in cat_b, f"Expected Potential Contradiction but got {cat_b}"

    # Case C: Exact match / consistent
    cat_c, conf_c, reason_c = compare_statement_pair(
        "CSD DBMS - Oct 11",
        "CSD DBMS - Oct 11",
        1.0
    )
    print(f"\nCase C: 'CSD DBMS - Oct 11' vs 'CSD DBMS - Oct 11'")
    print(f" -> Result: {cat_c} (Confidence: {conf_c})")
    assert "Consistent" in cat_c, f"Expected Consistent Information but got {cat_c}"

    # Case D: Hardware specification context check
    # Server 32GB RAM vs Mobile 4GB RAM -> Contextual Difference
    cat_d, conf_d, reason_d = compare_statement_pair(
        "Server node requires 32GB RAM for production workloads.",
        "Mobile client application requires 4GB RAM to execute.",
        0.80
    )
    print(f"\nCase D: 'Server node requires 32GB RAM' vs 'Mobile client requires 4GB RAM'")
    print(f" -> Result: {cat_d} (Confidence: {conf_d})")
    assert "Contextual" in cat_d, f"Expected Contextual Difference but got {cat_d}"

    # Case E: Server 32GB RAM vs Server 16GB RAM -> Potential Contradiction
    cat_e, conf_e, reason_e = compare_statement_pair(
        "Server node requires 32GB RAM for production workloads.",
        "Server node requires 16GB RAM for production workloads.",
        0.92
    )
    print(f"\nCase E: 'Server 32GB RAM' vs 'Server 16GB RAM'")
    print(f" -> Result: {cat_e} (Confidence: {conf_e})")
    assert "Contradiction" in cat_e, f"Expected Potential Contradiction but got {cat_e}"

    print("\n>>> All Unit Logic Tests PASSED successfully!")

    # 2. Test Document Extraction
    print("\n[TEST 2] Testing File Extraction (PDF & DOCX)...")
    sample_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_documents")
    pdf_path = os.path.join(sample_dir, "CSM_Exam_Schedule_v1.pdf")
    docx_path = os.path.join(sample_dir, "College_Circular_Revised.docx")

    pdf_records = extract_document(pdf_path, "CSM_Exam_Schedule_v1.pdf")
    docx_records = extract_document(docx_path, "College_Circular_Revised.docx")

    print(f"Extracted {len(pdf_records)} statements from PDF.")
    print(f"Extracted {len(docx_records)} statements from DOCX.")
    assert len(pdf_records) > 0, "PDF extraction failed to yield statements"
    assert len(docx_records) > 0, "DOCX extraction failed to yield statements"
    print(f"Sample PDF Statement (Page {pdf_records[0]['page_num']}): {pdf_records[0]['statement']}")
    print(f"Sample DOCX Statement (Page {docx_records[0]['page_num']}): {docx_records[0]['statement']}")
    print(">>> Extraction Test PASSED!")

    # 3. Test Full Multi-Document Analysis Pipeline
    print("\n[TEST 3] Testing Full Multi-Document Cross-Analysis...")
    all_records = pdf_records + docx_records
    results = analyze_documents(all_records, similarity_threshold=0.35)
    print(f"Generated {len(results)} cross-document comparisons.")

    categories_found = set(r["category"] for r in results)
    print("Categories detected across sample documents:", categories_found)
    assert any("Contradiction" in c for c in categories_found), "Expected to find at least one contradiction!"
    print(">>> Multi-Document Pipeline Test PASSED!")

    # 4. Test SQLite Database
    print("\n[TEST 4] Testing SQLite Database Persistence...")
    init_db()
    sess_id = save_analysis_session(
        session_name="Automated Test Run",
        documents=["CSM_Exam_Schedule_v1.pdf", "College_Circular_Revised.docx"],
        results=results,
        total_statements=len(all_records)
    )
    print(f"Saved session ID: {sess_id}")
    
    saved_sessions = list_saved_sessions()
    assert len(saved_sessions) > 0, "Failed to retrieve saved sessions"
    
    saved_results = get_session_results(sess_id)
    assert len(saved_results) == len(results), f"Result count mismatch in DB: {len(saved_results)} vs {len(results)}"
    print(f"Successfully verified {len(saved_results)} results saved and retrieved from SQLite.")
    print(">>> SQLite Persistence Test PASSED!")

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED! PROJECT ENGINE READY.")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
