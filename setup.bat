@echo off
echo ========================================
echo ImmortyX - Multi-Agent Longevity System
echo ========================================
echo.

echo Checking Python installation...
python --version
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH
    pause
    exit /b 1
)

echo.
echo Installing required packages...
pip install -r requirements.txt

echo.
echo Running system demo...
python demo.py

echo.
echo Demo completed. You can now start the chatbot interface:
echo   python app.py
echo.
echo Or run the full system:
echo   python main.py
echo.
pause
