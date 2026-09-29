"""
Sample Document Generator
Generates realistic PDF and DOCX documents to test and demonstrate the
Context-Aware AI Document Contradiction Detector during university viva presentations.
"""

import os
import pymupdf  # PyMuPDF
import docx

SAMPLE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_documents")


def generate_sample_files():
    """Create sample PDF and DOCX documents with carefully tailored benchmark test cases."""
    os.makedirs(SAMPLE_DIR, exist_ok=True)

    # ---------------------------------------------------------
    # Document 1: CSM_Exam_Schedule_v1.pdf (PyMuPDF)
    # ---------------------------------------------------------
    doc1_path = os.path.join(SAMPLE_DIR, "CSM_Exam_Schedule_v1.pdf")
    doc1 = pymupdf.open()
    page1 = doc1.new_page()
    text_csm = (
        "DEPARTMENT OF COMPUTER SCIENCE & MACHINE LEARNING (CSM)\n"
        "Official Examination Schedule - Semester V\n\n"
        "Important Timetable Notice:\n"
        "• CSM DBMS - Oct 10\n"
        "• CSM Computer Networks - Oct 12\n"
        "• CSM Operating Systems - Oct 14\n"
        "• The final lab assessment will be held on Nov 05.\n"
        "• Minimum attendance required for examination is 75%.\n"
        "• Mobile phones are strictly prohibited in the exam hall.\n"
    )
    page1.insert_text((50, 72), text_csm, fontsize=12)
    doc1.save(doc1_path)
    doc1.close()

    # ---------------------------------------------------------
    # Document 2: CSD_Exam_Schedule_v1.pdf (PyMuPDF)
    # (Notice: CSD DBMS is Oct 11 -> Contextual difference with CSM DBMS Oct 10!)
    # ---------------------------------------------------------
    doc2_path = os.path.join(SAMPLE_DIR, "CSD_Exam_Schedule_v1.pdf")
    doc2 = pymupdf.open()
    page2 = doc2.new_page()
    text_csd = (
        "DEPARTMENT OF COMPUTER SCIENCE & DATA SCIENCE (CSD)\n"
        "Official Examination Schedule - Semester V\n\n"
        "Important Timetable Notice:\n"
        "• CSD DBMS - Oct 11\n"
        "• CSD Computer Networks - Oct 12\n"
        "• CSD Operating Systems - Oct 16\n"
        "• The final lab assessment will be held on Nov 08.\n"
        "• Minimum attendance required for examination is 75%.\n"
        "• Mobile phones are strictly prohibited in the exam hall.\n"
    )
    page2.insert_text((50, 72), text_csd, fontsize=12)
    doc2.save(doc2_path)
    doc2.close()

    # ---------------------------------------------------------
    # Document 3: College_Circular_Revised.docx (python-docx)
    # (Notice: CSM DBMS is stated as Oct 15 -> Contradiction with CSM Exam Schedule v1 Oct 10!)
    # (Notice: Attendance requirement stated as 65% -> Contradiction with 75%!)
    # ---------------------------------------------------------
    doc3_path = os.path.join(SAMPLE_DIR, "College_Circular_Revised.docx")
    d3 = docx.Document()
    d3.add_heading("Academic Controller Circular - Revised Dates", level=1)
    d3.add_paragraph("This circular serves as the latest update for departmental assessments.")
    
    p = d3.add_paragraph()
    p.add_run("Key Subject Schedules:\n").bold = True
    d3.add_paragraph("CSM DBMS - Oct 15", style='List Bullet')
    d3.add_paragraph("CSD DBMS - Oct 11", style='List Bullet')
    d3.add_paragraph("CSM Computer Networks - Oct 12", style='List Bullet')
    d3.add_paragraph("Minimum attendance required for examination is 65%.", style='List Bullet')
    d3.add_paragraph("The final lab assessment will be held on Nov 05.", style='List Bullet')
    d3.save(doc3_path)

    # ---------------------------------------------------------
    # Document 4: System_Architecture_Specs.pdf
    # Hardware architecture requirements (Mobile vs Server)
    # ---------------------------------------------------------
    doc4_path = os.path.join(SAMPLE_DIR, "System_Architecture_Specs.pdf")
    doc4 = pymupdf.open()
    page4 = doc4.new_page()
    text_sys = (
        "ENTERPRISE CLOUD ARCHITECTURE SPECIFICATION\n"
        "Section 3: Infrastructure and Node Sizing\n\n"
        "• Server node requires 32GB RAM for production workloads.\n"
        "• Mobile client application requires 4GB RAM to execute.\n"
        "• Database backup retention period is 30 days.\n"
        "• Multi-factor authentication is mandatory for all administrators.\n"
    )
    page4.insert_text((50, 72), text_sys, fontsize=12)
    doc4.save(doc4_path)
    doc4.close()

    # ---------------------------------------------------------
    # Document 5: Client_Deployment_Guide.docx
    # ---------------------------------------------------------
    doc5_path = os.path.join(SAMPLE_DIR, "Client_Deployment_Guide.docx")
    d5 = docx.Document()
    d5.add_heading("Client Deployment Guidelines & Environment Settings", level=1)
    d5.add_paragraph("• Mobile client application requires 4GB RAM to execute.")
    d5.add_paragraph("• Server node requires 16GB RAM for production workloads.")  # Contradiction: 16GB vs 32GB
    d5.add_paragraph("• Multi-factor authentication is mandatory for all administrators.")  # Consistent
    d5.add_paragraph("• Database backup retention period is 90 days.")  # Contradiction: 90 vs 30 days
    d5.save(doc5_path)

    print("Sample test documents successfully generated in:", SAMPLE_DIR)
    return [doc1_path, doc2_path, doc3_path, doc4_path, doc5_path]


if __name__ == "__main__":
    generate_sample_files()
