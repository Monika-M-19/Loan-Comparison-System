@echo off
setlocal

where python >nul 2>nul
if %errorlevel%==0 (
    set PYTHON_CMD=python
) else (
    where py >nul 2>nul
    if %errorlevel%==0 (
        set PYTHON_CMD=py
    ) else (
        echo Python was not found. Install Python 3.10 or newer, then try again.
        pause
        exit /b 1
    )
)

%PYTHON_CMD% -m PyInstaller --version >nul 2>nul
if not %errorlevel%==0 (
    echo PyInstaller is not installed.
    echo Run: %PYTHON_CMD% -m pip install -r requirements.txt
    pause
    exit /b 1
)

%PYTHON_CMD% -m PyInstaller --onefile --windowed --name LoanComparisonSystem main.py

echo.
echo Build complete. Check the dist folder for LoanComparisonSystem.exe.
pause
