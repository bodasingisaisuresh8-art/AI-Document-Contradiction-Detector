@echo off
title Context-Aware AI Document Contradiction Detector
echo ========================================================
echo Starting AI Document Contradiction Detector...
echo ========================================================

IF EXIST "C:\doc_detector_venv\Scripts\streamlit.exe" (
    "C:\doc_detector_venv\Scripts\streamlit.exe" run app.py
) ELSE (
    streamlit run app.py
)
pause
