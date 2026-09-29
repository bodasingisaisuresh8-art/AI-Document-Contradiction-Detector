"""
Database Module for AI Document Contradiction Detector
Uses SQLite for persistent storage of scan sessions, extracted statements, and comparison results.
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

DB_FILE = "contradiction_detector.db"


def get_connection():
    """Get a SQLite database connection with row factory enabled."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database tables if they do not exist."""
    conn = get_connection()
    cursor = conn.cursor()

    # Table for high-level analysis runs/sessions
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS analysis_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_name TEXT NOT NULL,
        created_at TEXT NOT NULL,
        documents_analyzed TEXT,  -- JSON list of filenames
        total_statements INTEGER DEFAULT 0,
        total_pairs INTEGER DEFAULT 0,
        consistent_count INTEGER DEFAULT 0,
        context_diff_count INTEGER DEFAULT 0,
        contradiction_count INTEGER DEFAULT 0,
        uncertain_count INTEGER DEFAULT 0
    )
    """)

    # Table for individual contradiction/comparison results
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS comparison_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER,
        doc_a TEXT NOT NULL,
        page_a INTEGER,
        statement_a TEXT NOT NULL,
        doc_b TEXT NOT NULL,
        page_b INTEGER,
        statement_b TEXT NOT NULL,
        category TEXT NOT NULL,  -- Consistent, Contextual Difference, Potential Contradiction, Uncertain
        confidence REAL NOT NULL,
        reason TEXT NOT NULL,
        similarity_score REAL,
        FOREIGN KEY (session_id) REFERENCES analysis_sessions (id) ON DELETE CASCADE
    )
    """)

    conn.commit()
    conn.close()


def save_analysis_session(
    session_name: str,
    documents: List[str],
    results: List[Dict[str, Any]],
    total_statements: int
) -> int:
    """
    Saves an entire analysis run and its comparison pairs into SQLite.
    Returns the newly created session ID.
    """
    init_db()
    conn = get_connection()
    cursor = conn.cursor()

    # Calculate summary metrics
    total_pairs = len(results)
    consistent_count = sum(1 for r in results if "Consistent" in r.get("category", ""))
    context_diff_count = sum(1 for r in results if "Contextual" in r.get("category", ""))
    contradiction_count = sum(1 for r in results if "Contradiction" in r.get("category", ""))
    uncertain_count = sum(1 for r in results if "Uncertain" in r.get("category", ""))

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
    INSERT INTO analysis_sessions (
        session_name, created_at, documents_analyzed, total_statements,
        total_pairs, consistent_count, context_diff_count, contradiction_count, uncertain_count
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        session_name,
        now_str,
        json.dumps(documents),
        total_statements,
        total_pairs,
        consistent_count,
        context_diff_count,
        contradiction_count,
        uncertain_count
    ))

    session_id = cursor.lastrowid

    # Insert individual comparison pairs
    for r in results:
        cursor.execute("""
        INSERT INTO comparison_results (
            session_id, doc_a, page_a, statement_a,
            doc_b, page_b, statement_b, category,
            confidence, reason, similarity_score
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session_id,
            r.get("doc_a", ""),
            r.get("page_a", 1),
            r.get("statement_a", ""),
            r.get("doc_b", ""),
            r.get("page_b", 1),
            r.get("statement_b", ""),
            r.get("category", "Uncertain"),
            round(float(r.get("confidence", 0.0)), 3),
            r.get("reason", ""),
            round(float(r.get("similarity_score", 0.0)), 3)
        ))

    conn.commit()
    conn.close()
    return session_id


def list_saved_sessions() -> List[Dict[str, Any]]:
    """Retrieve all historical sessions ordered by most recent first."""
    init_db()
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT id, session_name, created_at, documents_analyzed, total_statements,
           total_pairs, consistent_count, context_diff_count, contradiction_count, uncertain_count
    FROM analysis_sessions
    ORDER BY id DESC
    """)
    rows = cursor.fetchall()
    
    sessions = []
    for r in rows:
        d = dict(r)
        try:
            d["documents_analyzed"] = json.loads(d["documents_analyzed"])
        except Exception:
            d["documents_analyzed"] = []
        sessions.append(d)

    conn.close()
    return sessions


def get_session_results(session_id: int) -> List[Dict[str, Any]]:
    """Retrieve all comparison results for a specific session."""
    init_db()
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT doc_a, page_a, statement_a, doc_b, page_b, statement_b,
           category, confidence, reason, similarity_score
    FROM comparison_results
    WHERE session_id = ?
    ORDER BY id ASC
    """, (session_id,))

    rows = cursor.fetchall()
    results = [dict(r) for r in rows]
    conn.close()
    return results


def delete_session(session_id: int):
    """Delete a session and all its associated comparison records."""
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM comparison_results WHERE session_id = ?", (session_id,))
    cursor.execute("DELETE FROM analysis_sessions WHERE id = ?", (session_id,))
    conn.commit()
    conn.close()
