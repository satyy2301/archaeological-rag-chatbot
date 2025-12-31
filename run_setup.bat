@echo off
echo Setting up Archaeological Survey RAG Chatbot...
echo.

REM Activate virtual environment if it exists
if exist "..\venv\Scripts\activate.bat" (
    call ..\venv\Scripts\activate.bat
)

REM Run setup script
python setup.py

pause

