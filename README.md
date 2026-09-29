# Context-Aware AI Document Contradiction Detector
### 🎓 Final-Year Capstone Project in Artificial Intelligence & Natural Language Processing

---

## 📌 1. Project Overview & Motivation
In legal, academic, enterprise, and compliance domains, organizations frequently update policies, schedules, and specifications across dozens of documents. Traditional text comparison tools (like Diff or basic keyword matchers) flag any textual variation as a conflict. 

This project implements a **Context-Aware AI Document Contradiction Detector** that distinguishes between:
1. **🟢 Consistent Information**: Statements asserting identical facts across documents.
2. **🟡 Contextual Differences**: Statements with different values/dates that apply to distinct scopes, departments, or conditions (and are therefore **NOT** contradictions).
3. **🔴 Potential Contradictions**: Statements that share the exact same contextual scope/entity but assert mutually exclusive facts, dates, or numbers.
4. **⚪ Uncertain Cases**: Statements with topical overlap but lacking conclusive evidence or qualifiers.

---

## 💡 The Core Problem Solved: Understanding Context

### Benchmark Case:
Consider two statements from university exam circulars:
- **Statement A**: `CSM DBMS – Oct 10`
- **Statement B**: `CSD DBMS – Oct 11`

> **Result**: `🟡 Contextual Difference`  
> *Reason*: `CSM` (Computer Science & Machine Learning) and `CSD` (Computer Science & Data Science) are distinct departmental scopes. Differing exam dates are expected and legitimate. A naive detector would erroneously flag this as a contradiction.

Now consider:
- **Statement A**: `CSM DBMS – Oct 10`
- **Statement B**: `CSM DBMS – Oct 15`

> **Result**: `🔴 Potential Contradiction`  
> *Reason*: Both circulars specify the schedule for the exact same entity (`CSM DBMS`), but specify conflicting dates (`Oct 10` vs `Oct 15`). This is a critical conflict.

---

## 🏗️ 2. System Architecture

```
                       +-------------------------------+
                       |   Multi-Document Ingestion    |
                       |      (PDF, DOCX, TXT)         |
                       +---------------+---------------+
                                       |
                                       v
                       +-------------------------------+
                       | Text Extraction & Provenance  |
                       |    (PyMuPDF & python-docx)    |
                       |     Tracks Doc & Page Num     |
                       +---------------+---------------+
                                       |
                                       v
                       +-------------------------------+
                       | Sentence Transformers Encoder |
                       |    ('all-MiniLM-L6-v2')       |
                       +---------------+---------------+
                                       |
                                       v
                       +-------------------------------+
                       | Cross-Document Pair Retrieval |
                       |  (Cosine Similarity Pruning)  |
                       +---------------+---------------+
                                       |
                                       v
                       +-------------------------------+
                       | Context & Entity Disambiguator|
                       | (Scopes, Dates, Values, Pol.) |
                       +---------------+---------------+
                                       |
                     +-----------------+-----------------+
                     |                 |                 |
                     v                 v                 v
           [🔴 Contradiction] [🟡 Context Diff] [🟢 Consistent / ⚪ Uncertain]
                     |                 |                 |
                     +-----------------+-----------------+
                                       |
                                       v
                       +-------------------------------+
                       |   SQLite Audit Persistence    |
                       +---------------+---------------+
                                       |
                                       v
                       +-------------------------------+
                       | Streamlit Executive Dashboard |
                       | (Evidence Viewer, Analytics)  |
                       +-------------------------------+
```

---

## 🛠️ 3. Technologies Used

| Technology | Purpose |
| :--- | :--- |
| **Python 3.13** | Core programming language |
| **Streamlit** | Interactive web dashboard and visualization interface |
| **Sentence-Transformers** | `all-MiniLM-L6-v2` dense neural embeddings for semantic representation |
| **PyMuPDF (`pymupdf`)** | High-performance PDF parsing and page-level provenance extraction |
| **python-docx** | Parsing `.docx` documents, paragraphs, and tables |
| **SQLite 3** | Session persistence, audit trail, and cross-comparison storage |
| **Scikit-Learn / NumPy** | Cosine similarity matrix operations and vector math |
| **Plotly** | Dynamic distribution charts (donut charts, confidence distributions) |

---

## 🚀 4. How to Run the Project

### Quick Launch (Windows)
Double-click `run.bat` or run in PowerShell:
```powershell
C:\doc_detector_venv\Scripts\streamlit.exe run app.py
```

### Manual Installation (If setting up on a new PC)
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python sample_generator.py
streamlit run app.py
```

---

## 📂 5. Project Directory Structure
```
AI Document Contradiction Detector/
│
├── app.py                  # Main Streamlit web dashboard (5 tabs, evidence viewer)
├── extractor.py            # PDF (PyMuPDF) and DOCX (python-docx) extraction engine
├── nlp_engine.py           # SentenceTransformers embedding + context classification logic
├── database.py             # SQLite database layer for session persistence
├── sample_generator.py     # Generates benchmark sample PDF & DOCX test files
├── test_pipeline.py        # Automated test suite verifying all 5 core benchmarks
├── requirements.txt        # Python dependency manifest
├── run.bat                 # One-click Windows runner
├── contradiction_detector.db # SQLite database
└── sample_documents/       # Pre-generated academic and enterprise test files
    ├── CSM_Exam_Schedule_v1.pdf
    ├── CSD_Exam_Schedule_v1.pdf
    ├── College_Circular_Revised.docx
    ├── System_Architecture_Specs.pdf
    └── Client_Deployment_Guide.docx
```

---

## 🎓 6. University Viva Questions & Answers (Preparation Guide)

### Q1: What makes your system "context-aware" compared to standard NLI models?
> **Answer**: Standard Natural Language Inference (NLI) models often classify any sentence pair with conflicting dates or numbers as a contradiction (e.g., classifying `CSM DBMS on Oct 10` and `CSD DBMS on Oct 11` as contradictory because of the date mismatch). Our system extracts contextual scope qualifiers (e.g., department codes, target user groups, deployment environments). It checks whether the differing predicates apply to the same scope. If scopes are disjoint, it correctly classifies them as a **🟡 Contextual Difference**.

### Q2: Why did you choose `all-MiniLM-L6-v2`?
> **Answer**: `all-MiniLM-L6-v2` is a 6-layer distilled MiniLM model with 384-dimensional embeddings. It achieves a 5x speedup and requires only ~80MB memory compared to larger BERT models while maintaining >99% semantic accuracy for sentence-level similarity retrieval.

### Q3: How do you extract and track provenance?
> **Answer**: PyMuPDF (`fitz`) parses the PDF document structure page-by-page. Each extracted statement is saved with a metadata dictionary tracking `doc_name`, `page_num`, and surrounding paragraph context. When a contradiction is flagged, the user can see the exact document and page number in the Evidence Viewer.

### Q4: How is data stored and audited?
> **Answer**: An embedded SQLite database (`contradiction_detector.db`) persists every analysis session with timestamps, document filenames, summary counts, and the full record of comparison pairs with confidence scores and reasoning. This enables auditability and retrospective reporting.
