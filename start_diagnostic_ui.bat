@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo.
echo Portfolio MRI - Diagnostic UI
echo ===========================
echo.
python --version >nul 2>&1
if errorlevel 1 (
  echo Python not found. Install Python 3 and add it to PATH.
  pause
  exit /b 1
)
python -c "import flask" >nul 2>&1
if errorlevel 1 (
  echo Installing Flask...
  python -m pip install flask pyyaml
)
echo Starting server... Do not close this window.
echo.
python -m diagnostic_journey
pause
