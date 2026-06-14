@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0qa_exhaustive.ps1" %*
exit /b %ERRORLEVEL%

