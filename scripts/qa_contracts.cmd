@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0qa_contracts.ps1" %*
exit /b %ERRORLEVEL%
