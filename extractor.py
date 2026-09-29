"""
Document Extractor Module
Handles text extraction from PDF and DOCX files with document, page, and paragraph metadata.
Uses PyMuPDF (fitz) for PDF files and python-docx for DOCX files.
"""

import io
import re
from typing import List, Dict, Any, Union
import pymupdf  # PyMuPDF
import docx


def clean_text(text: str) -> str:
    """Clean and normalize whitespace while preserving punctuation."""
    if not text:
        return ""
    # Replace weird unicode spaces or dashes
    text = text.replace('\u2013', '-').replace('\u2014', '-').replace('\u2018', "'").replace('\u2019', "'")
    text = text.replace('\u201c', '"').replace('\u201d', '"')
    # Collapse multiple spaces and newlines
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n+', '\n', text)
    return text.strip()


def split_into_statements(text: str) -> List[str]:
    """
    Split text into individual statements/sentences or bullet items.
    Preserves meaningful short assertions like 'CSM DBMS - Oct 10'.
    """
    text = clean_text(text)
    if not text:
        return []

    # First split by explicit line breaks or bullet points
    raw_lines = re.split(r'[\r\n]+|[•▪*]\s*', text)
    statements = []

    for line in raw_lines:
        line = line.strip()
        if not line:
            continue
        # If line contains multiple sentences (period followed by space and capital letter)
        # but avoid splitting decimals like 3.14 or abbreviations like Oct. 10
        sentence_candidates = re.split(r'(?<=[.!?])\s+(?=[A-Z0-9])', line)
        for cand in sentence_candidates:
            cand = cand.strip()
            # Only keep statements with at least 4 characters
            if len(cand) >= 4:
                statements.append(cand)

    return statements


def extract_from_pdf(file_source: Union[str, bytes, io.BytesIO], doc_name: str) -> List[Dict[str, Any]]:
    """
    Extracts pages and statement-level segments from a PDF document using PyMuPDF.
    
    Returns:
        List of dicts:
        [{
            "doc_name": str,
            "page_num": int,
            "statement": str,
            "full_context": str
        }]
    """
    records = []
    
    if isinstance(file_source, bytes):
        doc = pymupdf.open(stream=file_source, filetype="pdf")
    elif isinstance(file_source, io.BytesIO):
        doc = pymupdf.open(stream=file_source.getvalue(), filetype="pdf")
    else:
        doc = pymupdf.open(file_source)

    try:
        for page_idx in range(len(doc)):
            page = doc[page_idx]
            page_text = page.get_text("text")
            cleaned_page = clean_text(page_text)
            
            if not cleaned_page:
                continue

            statements = split_into_statements(cleaned_page)
            for stmt in statements:
                records.append({
                    "doc_name": doc_name,
                    "page_num": page_idx + 1,
                    "statement": stmt,
                    "full_context": cleaned_page[:300]  # snippet for contextual reference
                })
    finally:
        doc.close()

    return records


def extract_from_docx(file_source: Union[str, bytes, io.BytesIO], doc_name: str) -> List[Dict[str, Any]]:
    """
    Extracts paragraphs and statements from a DOCX document using python-docx.
    
    Returns:
        List of dicts matching the PDF extractor format.
    """
    records = []
    
    if isinstance(file_source, (bytes, io.BytesIO)):
        bio = file_source if isinstance(file_source, io.BytesIO) else io.BytesIO(file_source)
        doc = docx.Document(bio)
    else:
        doc = docx.Document(file_source)

    paragraph_idx = 0
    full_text_list = []

    # Read paragraphs
    for p in doc.paragraphs:
        p_text = clean_text(p.text)
        if not p_text:
            continue
        paragraph_idx += 1
        full_text_list.append(p_text)
        stmts = split_into_statements(p_text)
        for stmt in stmts:
            # For DOCX, we treat paragraph groups or page estimates
            estimated_page = max(1, (paragraph_idx // 8) + 1)
            records.append({
                "doc_name": doc_name,
                "page_num": estimated_page,
                "statement": stmt,
                "full_context": p_text[:300]
            })

    # Also read tables if present
    for table in doc.tables:
        for row in table.rows:
            row_text = " | ".join([clean_text(cell.text) for cell in row.cells if clean_text(cell.text)])
            if row_text:
                paragraph_idx += 1
                estimated_page = max(1, (paragraph_idx // 8) + 1)
                records.append({
                    "doc_name": doc_name,
                    "page_num": estimated_page,
                    "statement": row_text,
                    "full_context": f"Table Row: {row_text}"
                })

    return records


def extract_document(file_source: Union[str, bytes, io.BytesIO], doc_name: str) -> List[Dict[str, Any]]:
    """
    Universal dispatcher that handles PDF, DOCX, and TXT files.
    """
    lower_name = doc_name.lower()
    if lower_name.endswith(".pdf"):
        return extract_from_pdf(file_source, doc_name)
    elif lower_name.endswith(".docx"):
        return extract_from_docx(file_source, doc_name)
    elif lower_name.endswith(".txt"):
        if isinstance(file_source, (bytes, io.BytesIO)):
            content = file_source.getvalue().decode('utf-8', errors='ignore') if isinstance(file_source, io.BytesIO) else file_source.decode('utf-8', errors='ignore')
        else:
            with open(file_source, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        stmts = split_into_statements(content)
        return [{
            "doc_name": doc_name,
            "page_num": 1,
            "statement": stmt,
            "full_context": content[:300]
        } for stmt in stmts]
    else:
        raise ValueError(f"Unsupported file format: {doc_name}. Please provide a .pdf, .docx, or .txt file.")
