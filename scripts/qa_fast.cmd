@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0qa_fast.ps1" %*
exit /b %ERRORLEVEL%
