"""
Context-Aware AI Document Contradiction Detector
Streamlit Web Application & Interactive Dashboard
Final Year Project Implementation
"""

import os
import sys
import io
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Custom project modules
from extractor import extract_document
from nlp_engine import analyze_documents
from database import (
    init_db,
    save_analysis_session,
    list_saved_sessions,
    get_session_results,
    delete_session
)

# Page configuration
st.set_page_config(
    page_title="AI Document Contradiction Detector",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling for polished dashboard UI
st.markdown("""
<style>
    /* Metric Cards */
    .metric-card {
        border-radius: 12px;
        padding: 16px 20px;
        background: #ffffff;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        border: 1px solid #e2e8f0;
        text-align: center;
        margin-bottom: 12px;
    }
    .metric-title {
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: #64748b;
        margin-bottom: 4px;
    }
    .metric-val {
        font-size: 1.8rem;
        font-weight: 700;
        margin: 0;
    }
    .badge-contradiction { color: #dc2626; border-left: 4px solid #dc2626; }
    .badge-context { color: #d97706; border-left: 4px solid #d97706; }
    .badge-consistent { color: #16a34a; border-left: 4px solid #16a34a; }
    .badge-uncertain { color: #475569; border-left: 4px solid #475569; }

    /* Evidence Cards */
    .evidence-box {
        background-color: #f8fafc;
        border-radius: 10px;
        padding: 18px;
        border: 1px solid #e2e8f0;
        margin-bottom: 18px;
        transition: all 0.2s ease-in-out;
    }
    .evidence-box:hover {
        border-color: #cbd5e1;
        box-shadow: 0 6px 16px rgba(0,0,0,0.06);
    }
    .tag {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-right: 6px;
    }
    .tag-doc { background: #e0e7ff; color: #3730a3; }
    .tag-page { background: #f1f5f9; color: #334155; }
    .tag-contradiction { background: #fee2e2; color: #991b1b; }
    .tag-context { background: #fef3c7; color: #92400e; }
    .tag-consistent { background: #dcfce7; color: #166534; }
    .tag-uncertain { background: #f3f4f6; color: #374151; }

    /* Statement Quote */
    .stmt-text {
        font-size: 1.05rem;
        font-weight: 500;
        color: #1e293b;
        background: #ffffff;
        padding: 10px 14px;
        border-radius: 6px;
        border: 1px solid #e2e8f0;
        margin: 8px 0;
    }
    .reason-box {
        background: #f1f5f9;
        border-left: 3px solid #3b82f6;
        padding: 10px 14px;
        font-size: 0.92rem;
        color: #1e293b;
        border-radius: 0 6px 6px 0;
        margin-top: 10px;
    }
</style>
""", unsafe_allow_html=True)


# Initialize SQLite
init_db()

# Session State Initialization
if "extracted_records" not in st.session_state:
    st.session_state["extracted_records"] = []
if "uploaded_file_names" not in st.session_state:
    st.session_state["uploaded_file_names"] = []
if "analysis_results" not in st.session_state:
    st.session_state["analysis_results"] = []
if "last_session_id" not in st.session_state:
    st.session_state["last_session_id"] = None


# -------------------------------------------------------------
# SIDEBAR CONTROLS & SAMPLE DEMOS
# -------------------------------------------------------------
with st.sidebar:
    st.image("https://img.icons8.com/color/96/artificial-intelligence.png", width=64)
    st.title("Context-Aware AI")
    st.markdown("**Document Contradiction Detector**\n\n*Final Year Capstone Project*")
    st.divider()

    st.subheader("⚙️ Analysis Parameters")
    similarity_thresh = st.slider(
        "Semantic Relevance Threshold",
        min_value=0.20,
        max_value=0.80,
        value=0.38,
        step=0.02,
        help="Filters out pairs of statements that do not talk about the same general topic."
    )

    top_k = st.slider(
        "Max Matches Per Statement",
        min_value=1,
        max_value=5,
        value=3,
        help="Number of cross-document candidate statements to evaluate for each claim."
    )

    st.divider()
    st.subheader("🎓 1-Click Viva Demo Presets")
    st.caption("Instantly test the model with curated academic benchmark cases.")

    sample_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_documents")

    if st.button("📚 Load University Exam Benchmark", use_container_width=True):
        files_to_load = [
            ("CSM_Exam_Schedule_v1.pdf", os.path.join(sample_dir, "CSM_Exam_Schedule_v1.pdf")),
            ("CSD_Exam_Schedule_v1.pdf", os.path.join(sample_dir, "CSD_Exam_Schedule_v1.pdf")),
            ("College_Circular_Revised.docx", os.path.join(sample_dir, "College_Circular_Revised.docx"))
        ]
        all_recs = []
        names = []
        for fname, fpath in files_to_load:
            if os.path.exists(fpath):
                recs = extract_document(fpath, fname)
                all_recs.extend(recs)
                names.append(fname)
        
        st.session_state["extracted_records"] = all_recs
        st.session_state["uploaded_file_names"] = names
        with st.spinner("Analyzing cross-document statements..."):
            res = analyze_documents(all_recs, similarity_threshold=similarity_thresh, top_k_per_statement=top_k)
            st.session_state["analysis_results"] = res
            sess_id = save_analysis_session(
                session_name="University Exam Schedule Demo",
                documents=names,
                results=res,
                total_statements=len(all_recs)
            )
            st.session_state["last_session_id"] = sess_id
        st.success("Loaded & Analyzed University Exam benchmark!")
        st.rerun()

    if st.button("☁️ Load Cloud Architecture Benchmark", use_container_width=True):
        files_to_load = [
            ("System_Architecture_Specs.pdf", os.path.join(sample_dir, "System_Architecture_Specs.pdf")),
            ("Client_Deployment_Guide.docx", os.path.join(sample_dir, "Client_Deployment_Guide.docx"))
        ]
        all_recs = []
        names = []
        for fname, fpath in files_to_load:
            if os.path.exists(fpath):
                recs = extract_document(fpath, fname)
                all_recs.extend(recs)
                names.append(fname)
        
        st.session_state["extracted_records"] = all_recs
        st.session_state["uploaded_file_names"] = names
        with st.spinner("Analyzing architecture statements..."):
            res = analyze_documents(all_recs, similarity_threshold=similarity_thresh, top_k_per_statement=top_k)
            st.session_state["analysis_results"] = res
            sess_id = save_analysis_session(
                session_name="Cloud Architecture Specs Demo",
                documents=names,
                results=res,
                total_statements=len(all_recs)
            )
            st.session_state["last_session_id"] = sess_id
        st.success("Loaded & Analyzed Cloud Specs benchmark!")
        st.rerun()

    if st.button("🗑️ Reset All Data", use_container_width=True):
        st.session_state["extracted_records"] = []
        st.session_state["uploaded_file_names"] = []
        st.session_state["analysis_results"] = []
        st.session_state["last_session_id"] = None
        st.rerun()

    st.divider()
    st.markdown("""
    **Core Classification Matrix:**
    - 🟢 **Consistent**: Identical scope & fact
    - 🟡 **Context Diff**: Different scope/entity
    - 🔴 **Contradiction**: Same scope, conflicting fact
    - ⚪ **Uncertain**: Ambiguous or partial match
    """)


# -------------------------------------------------------------
# HEADER & OVERVIEW
# -------------------------------------------------------------
st.title("⚖️ Context-Aware AI Document Contradiction Detector")
st.markdown("""
Automated cross-document verification system using **Sentence Transformers**, **Context Logic Disambiguation**, and **PyMuPDF / python-docx**.
It identifies true contradictions vs contextual variations across multiple documents.
""")

# -------------------------------------------------------------
# NAVIGATION TABS
# -------------------------------------------------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📁 1. Document Upload & Extraction",
    "📊 2. Contradiction Dashboard",
    "🔍 3. Evidence & Explanation Viewer",
    "⚖️ 4. Side-by-Side Comparison",
    "📜 5. Database History & Viva Export"
])


# =============================================================
# TAB 1: DOCUMENT UPLOAD & EXTRACTION
# =============================================================
with tab1:
    st.subheader("Upload Multi-Format Documents (PDF / DOCX)")
    st.info("Upload two or more documents to cross-examine. The system extracts page numbers, statements, and contextual scopes.")

    uploaded_files = st.file_uploader(
        "Choose PDF or DOCX files",
        type=["pdf", "docx", "txt"],
        accept_multiple_files=True
    )

    col_btn1, col_btn2 = st.columns([2, 5])
    with col_btn1:
        if st.button("🚀 Process & Extract Text", type="primary", use_container_width=True):
            if not uploaded_files and not st.session_state["uploaded_file_names"]:
                st.warning("Please upload at least 2 files or use the 1-Click presets in the sidebar.")
            else:
                all_extracted = []
                fnames = []
                for uf in uploaded_files:
                    f_bytes = io.BytesIO(uf.read())
                    recs = extract_document(f_bytes, uf.name)
                    all_extracted.extend(recs)
                    fnames.append(uf.name)

                st.session_state["extracted_records"] = all_extracted
                st.session_state["uploaded_file_names"] = fnames

                with st.spinner("Executing Context-Aware Cross Comparison..."):
                    results = analyze_documents(
                        all_extracted,
                        similarity_threshold=similarity_thresh,
                        top_k_per_statement=top_k
                    )
                    st.session_state["analysis_results"] = results
                    sess_id = save_analysis_session(
                        session_name=f"Upload Analysis ({', '.join(fnames[:2])})",
                        documents=fnames,
                        results=results,
                        total_statements=len(all_extracted)
                    )
                    st.session_state["last_session_id"] = sess_id
                st.success(f"Analysis complete! Found {len(results)} cross-document comparisons. View results in the Dashboard tab.")

    # Show Extracted Content Preview
    if st.session_state["extracted_records"]:
        st.divider()
        st.subheader("📑 Document Extraction Summary")
        
        # Summary metrics
        doc_names = list(set(r["doc_name"] for r in st.session_state["extracted_records"]))
        c1, c2, c3 = st.columns(3)
        c1.metric("Documents Loaded", len(doc_names))
        c2.metric("Total Statements Extracted", len(st.session_state["extracted_records"]))
        c3.metric("Candidate Comparisons", len(st.session_state["analysis_results"]))

        # Detailed statement viewer per document
        for doc_name in doc_names:
            doc_stmts = [r for r in st.session_state["extracted_records"] if r["doc_name"] == doc_name]
            with st.expander(f"📄 {doc_name} ({len(doc_stmts)} statements extracted)"):
                df_preview = pd.DataFrame([
                    {"Page / Section": f"Page {r['page_num']}", "Statement": r["statement"]}
                    for r in doc_stmts
                ])
                st.dataframe(df_preview, use_container_width=True, height=200)


# =============================================================
# TAB 2: CONTRADICTION DASHBOARD
# =============================================================
with tab2:
    st.subheader("📊 Executive Analysis Summary")

    results = st.session_state["analysis_results"]
    if not results:
        st.info("No analysis results found yet. Upload documents in Tab 1 or click a 1-Click Viva Demo Preset in the sidebar!")
    else:
        # Group counts
        consistent = [r for r in results if "Consistent" in r["category"]]
        context_diff = [r for r in results if "Contextual" in r["category"]]
        contradictions = [r for r in results if "Contradiction" in r["category"]]
        uncertain = [r for r in results if "Uncertain" in r["category"]]

        # Display Top KPI Cards
        kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
        with kpi1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Total Compared</div>
                <div class="metric-val" style="color: #3b82f6;">{len(results)}</div>
            </div>
            """, unsafe_allow_html=True)
        with kpi2:
            st.markdown(f"""
            <div class="metric-card badge-contradiction">
                <div class="metric-title">🔴 Contradictions</div>
                <div class="metric-val" style="color: #dc2626;">{len(contradictions)}</div>
            </div>
            """, unsafe_allow_html=True)
        with kpi3:
            st.markdown(f"""
            <div class="metric-card badge-context">
                <div class="metric-title">🟡 Contextual Diffs</div>
                <div class="metric-val" style="color: #d97706;">{len(context_diff)}</div>
            </div>
            """, unsafe_allow_html=True)
        with kpi4:
            st.markdown(f"""
            <div class="metric-card badge-consistent">
                <div class="metric-title">🟢 Consistent</div>
                <div class="metric-val" style="color: #16a34a;">{len(consistent)}</div>
            </div>
            """, unsafe_allow_html=True)
        with kpi5:
            st.markdown(f"""
            <div class="metric-card badge-uncertain">
                <div class="metric-title">⚪ Uncertain</div>
                <div class="metric-val" style="color: #475569;">{len(uncertain)}</div>
            </div>
            """, unsafe_allow_html=True)

        st.divider()

        # Visual Analytics Charts
        chart_col1, chart_col2 = st.columns(2)
        with chart_col1:
            st.markdown("##### Distribution of Classification Categories")
            cat_counts = {
                "🔴 Contradiction": len(contradictions),
                "🟡 Contextual Diff": len(context_diff),
                "🟢 Consistent": len(consistent),
                "⚪ Uncertain": len(uncertain)
            }
            fig_pie = px.pie(
                names=list(cat_counts.keys()),
                values=list(cat_counts.values()),
                color=list(cat_counts.keys()),
                color_discrete_map={
                    "🔴 Contradiction": "#ef4444",
                    "🟡 Contextual Diff": "#f59e0b",
                    "🟢 Consistent": "#10b981",
                    "⚪ Uncertain": "#94a3b8"
                },
                hole=0.45
            )
            fig_pie.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=300)
            st.plotly_chart(fig_pie, use_container_width=True)

        with chart_col2:
            st.markdown("##### Average Confidence by Category")
            avg_conf = {
                "🔴 Contradiction": round(sum(r["confidence"] for r in contradictions) / max(1, len(contradictions)), 2),
                "🟡 Contextual Diff": round(sum(r["confidence"] for r in context_diff) / max(1, len(context_diff)), 2),
                "🟢 Consistent": round(sum(r["confidence"] for r in consistent) / max(1, len(consistent)), 2),
                "⚪ Uncertain": round(sum(r["confidence"] for r in uncertain) / max(1, len(uncertain)), 2)
            }
            fig_bar = px.bar(
                x=list(avg_conf.keys()),
                y=list(avg_conf.values()),
                labels={"x": "Category", "y": "Confidence Score"},
                color=list(avg_conf.keys()),
                color_discrete_map={
                    "🔴 Contradiction": "#ef4444",
                    "🟡 Contextual Diff": "#f59e0b",
                    "🟢 Consistent": "#10b981",
                    "⚪ Uncertain": "#94a3b8"
                }
            )
            fig_bar.update_layout(showlegend=False, yaxis_range=[0, 1.0], margin=dict(t=10, b=10, l=10, r=10), height=300)
            st.plotly_chart(fig_bar, use_container_width=True)

        # Quick Insights Callout
        st.markdown("##### 💡 Key Findings & Contextual Disambiguation")
        if contradictions:
            st.warning(f"**Attention:** Found **{len(contradictions)}** direct contradiction(s) where documents assert incompatible facts for the exact same subject/context.")
        if context_diff:
            st.info(f"**Context Protection:** Identified **{len(context_diff)}** contextual variation(s) (e.g. branch, role, or environment specific differences) that are correctly NOT flagged as contradictions.")
        if consistent:
            st.success(f"**Corroboration:** Verified **{len(consistent)}** congruent statement(s) that match across documents.")


# =============================================================
# TAB 3: EVIDENCE & DEEP EXPLANATION VIEWER
# =============================================================
with tab3:
    st.subheader("🔍 Side-by-Side Evidence Viewer & Reason Explainer")
    st.caption("Inspect the exact statements, document provenance (page number), AI confidence, and the logic reason.")

    results = st.session_state["analysis_results"]
    if not results:
        st.info("No comparison results available. Please run an analysis first.")
    else:
        # Filter controls
        f_col1, f_col2, f_col3 = st.columns([2, 2, 3])
        with f_col1:
            category_filter = st.selectbox(
                "Filter by Category",
                options=["All Categories", "🔴 Potential Contradiction", "🟡 Contextual Difference", "🟢 Consistent Information", "⚪ Uncertain Case"]
            )
        with f_col2:
            min_conf = st.slider("Minimum Confidence", 0.0, 1.0, 0.50, 0.05)
        with f_col3:
            keyword_search = st.text_input("Search Statement Keyword", placeholder="e.g. DBMS, Oct, RAM, attendance")

        # Apply filters
        filtered_results = results
        if category_filter != "All Categories":
            filtered_results = [r for r in filtered_results if category_filter in r["category"]]
        filtered_results = [r for r in filtered_results if r["confidence"] >= min_conf]
        if keyword_search:
            kw = keyword_search.lower()
            filtered_results = [
                r for r in filtered_results
                if kw in r["statement_a"].lower() or kw in r["statement_b"].lower() or kw in r["reason"].lower()
            ]

        st.write(f"Showing **{len(filtered_results)}** comparison item(s):")

        # Render evidence cards
        for idx, item in enumerate(filtered_results):
            cat = item["category"]
            badge_class = "tag-uncertain"
            if "Contradiction" in cat:
                badge_class = "tag-contradiction"
            elif "Contextual" in cat:
                badge_class = "tag-context"
            elif "Consistent" in cat:
                badge_class = "tag-consistent"

            conf_pct = int(item["confidence"] * 100)
            sim_pct = int(item["similarity_score"] * 100)

            with st.container():
                st.markdown(f"""
                <div class="evidence-box">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <span class="tag {badge_class}" style="font-size: 0.9rem;">{cat}</span>
                        <span style="font-size: 0.85rem; color: #64748b; font-weight: 600;">
                            Confidence: <b>{conf_pct}%</b> | Semantic Relevance: <b>{sim_pct}%</b>
                        </span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                col_a, col_b = st.columns(2)
                with col_a:
                    st.markdown(f"""
                    <div>
                        <span class="tag tag-doc">📄 {item['doc_a']}</span>
                        <span class="tag tag-page">Page {item['page_a']}</span>
                        <div class="stmt-text">"{item['statement_a']}"</div>
                    </div>
                    """, unsafe_allow_html=True)

                with col_b:
                    st.markdown(f"""
                    <div>
                        <span class="tag tag-doc">📄 {item['doc_b']}</span>
                        <span class="tag tag-page">Page {item['page_b']}</span>
                        <div class="stmt-text">"{item['statement_b']}"</div>
                    </div>
                    """, unsafe_allow_html=True)

                # Explanation Box
                st.markdown(f"""
                <div class="reason-box">
                    <b>💡 AI Logic & Reason:</b> {item['reason']}
                </div>
                """, unsafe_allow_html=True)

                st.write("")  # spacing


# =============================================================
# TAB 4: DOCUMENT SIDE-BY-SIDE COMPARISON
# =============================================================
with tab4:
    st.subheader("⚖️ Document-to-Document Direct Inspection")
    records = st.session_state["extracted_records"]
    doc_names = list(set(r["doc_name"] for r in records)) if records else []

    if len(doc_names) < 2:
        st.info("Please load at least two documents in Tab 1 to enable direct document comparison.")
    else:
        sel_c1, sel_c2 = st.columns(2)
        with sel_c1:
            doc_1 = st.selectbox("Select First Document (A)", options=doc_names, index=0)
        with sel_c2:
            default_idx2 = 1 if len(doc_names) > 1 else 0
            doc_2 = st.selectbox("Select Second Document (B)", options=doc_names, index=default_idx2)

        if doc_1 == doc_2:
            st.warning("Please choose two different documents to compare.")
        else:
            # Filter results between these two specific documents
            pair_results = [
                r for r in st.session_state["analysis_results"]
                if (r["doc_a"] == doc_1 and r["doc_b"] == doc_2) or (r["doc_a"] == doc_2 and r["doc_b"] == doc_1)
            ]

            st.write(f"Found **{len(pair_results)}** cross-correlations between **{doc_1}** and **{doc_2}**.")

            if pair_results:
                df_pair = pd.DataFrame([
                    {
                        "Category": r["category"],
                        f"{doc_1} Claim": r["statement_a"] if r["doc_a"] == doc_1 else r["statement_b"],
                        f"{doc_2} Claim": r["statement_b"] if r["doc_a"] == doc_1 else r["statement_a"],
                        "Confidence": f"{int(r['confidence'] * 100)}%",
                        "AI Explanation": r["reason"]
                    }
                    for r in pair_results
                ])
                st.dataframe(df_pair, use_container_width=True)
            else:
                st.write("No direct statement matches met the similarity threshold between these two documents.")


# =============================================================
# TAB 5: DATABASE HISTORY & VIVA EXPORT
# =============================================================
with tab5:
    st.subheader("📜 SQLite Audit History & Project Report Export")

    st.markdown("##### 💾 Historical Analysis Sessions in SQLite")
    history_sessions = list_saved_sessions()

    if not history_sessions:
        st.write("No historical sessions recorded yet.")
    else:
        history_df = pd.DataFrame([
            {
                "Session ID": s["id"],
                "Session Name": s["session_name"],
                "Analyzed At": s["created_at"],
                "Documents": ", ".join(s["documents_analyzed"]),
                "Contradictions": s["contradiction_count"],
                "Context Diffs": s["context_diff_count"],
                "Consistent": s["consistent_count"],
                "Total Compared": s["total_pairs"]
            }
            for s in history_sessions
        ])
        st.dataframe(history_df, use_container_width=True)

        # Reload a session
        sel_hist = st.selectbox(
            "Select Session to Reload or Manage",
            options=[s["id"] for s in history_sessions],
            format_func=lambda x: f"Session #{x}: {[s['session_name'] for s in history_sessions if s['id'] == x][0]}"
        )

        h_col1, h_col2 = st.columns([2, 5])
        with h_col1:
            if st.button("🔄 Reload Selected Session", use_container_width=True):
                loaded_res = get_session_results(sel_hist)
                st.session_state["analysis_results"] = loaded_res
                st.success(f"Loaded {len(loaded_res)} results from Session #{sel_hist}!")
                st.rerun()

    st.divider()
    st.subheader("🎓 Final-Year Viva Technical Dossier & Interview Guide")
    pdf_guide_path = "AI_Document_Contradiction_Detector_Architecture_and_Interview_Guide.pdf"
    if os.path.exists(pdf_guide_path):
        with open(pdf_guide_path, "rb") as f_pdf:
            pdf_bytes = f_pdf.read()
        st.download_button(
            label="📕 Download Complete Architecture & Viva Interview Guide (.PDF)",
            data=pdf_bytes,
            file_name="AI_Document_Contradiction_Detector_Architecture_and_Interview_Guide.pdf",
            mime="application/pdf",
            type="primary",
            use_container_width=True,
            help="7-page comprehensive technical dossier containing system architecture, data flow diagrams, and 23+ viva examiner Q&A."
        )

    st.divider()
    st.subheader("📥 Export Final-Year Project Report")

    current_res = st.session_state["analysis_results"]
    if current_res:
        # 1. CSV Export
        df_export = pd.DataFrame(current_res)
        csv_data = df_export.to_csv(index=False).encode('utf-8')
        
        # 2. Markdown Project Viva Report
        md_report = f"""# Final-Year Project Report: AI Document Contradiction Detector
Generated On: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}

## 1. Executive Summary
- Total Statement Comparisons: {len(current_res)}
- Potential Contradictions (🔴): {sum(1 for r in current_res if 'Contradiction' in r['category'])}
- Contextual Differences (🟡): {sum(1 for r in current_res if 'Contextual' in r['category'])}
- Consistent Information (🟢): {sum(1 for r in current_res if 'Consistent' in r['category'])}
- Uncertain Cases (⚪): {sum(1 for r in current_res if 'Uncertain' in r['category'])}

## 2. Key Findings & Detailed Evidence
"""
        for i, r in enumerate(current_res, 1):
            md_report += f"""
### Comparison #{i}: {r['category']}
- **Doc A**: {r['doc_a']} (Page {r['page_a']}): "{r['statement_a']}"
- **Doc B**: {r['doc_b']} (Page {r['page_b']}): "{r['statement_b']}"
- **Confidence**: {int(r['confidence'] * 100)}% | **Similarity**: {int(r['similarity_score'] * 100)}%
- **AI Explanation**: {r['reason']}
"""

        exp_col1, exp_col2, exp_col3 = st.columns(3)
        with exp_col1:
            st.download_button(
                label="📄 Download Project Viva Report (.md)",
                data=md_report,
                file_name="Contradiction_Detector_Viva_Report.md",
                mime="text/markdown",
                use_container_width=True
            )
        with exp_col2:
            st.download_button(
                label="📊 Download Findings Table (.csv)",
                data=csv_data,
                file_name="Contradiction_Detector_Results.csv",
                mime="text/csv",
                use_container_width=True
            )
        with exp_col3:
            json_data = json.dumps(current_res, indent=2).encode('utf-8')
            st.download_button(
                label="💻 Download Raw Data (.json)",
                data=json_data,
                file_name="Contradiction_Detector_Results.json",
                mime="application/json",
                use_container_width=True
            )
    else:
        st.info("Run an analysis or load sample data to generate exportable project reports.")
