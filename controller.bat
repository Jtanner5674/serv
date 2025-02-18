@echo off
:: Check if running as admin
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo This script requires administrative privileges.
    echo Please run it as an administrator.
    pause
    exit /b
)

:: Run controller.py
echo Running controller.py as administrator...
python "%~dp0controller.py"
pause
