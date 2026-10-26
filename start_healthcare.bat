@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Python environment not found. Please check the .venv folder.
    pause
    exit /b 1
)
".venv\Scripts\python.exe" -m streamlit run app.py
pause
