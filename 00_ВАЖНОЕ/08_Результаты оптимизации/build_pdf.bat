@echo off
setlocal

cd /d "%~dp0"

set "PANDOC_EXE=pandoc"
where pandoc >nul 2>&1
if errorlevel 1 (
  if exist "%LOCALAPPDATA%\Pandoc\pandoc.exe" (
    set "PANDOC_EXE=%LOCALAPPDATA%\Pandoc\pandoc.exe"
  ) else (
    echo [ERROR] pandoc is not installed or not in PATH.
    echo Install Pandoc: https://pandoc.org/installing.html
    exit /b 1
  )
)

where xelatex >nul 2>&1
if errorlevel 1 (
  echo [ERROR] xelatex is not installed or not in PATH.
  echo Install TeX Live or MiKTeX with xelatex support.
  exit /b 1
)

"%PANDOC_EXE%" ew_rp_comparison.md -o ew_rp_comparison_beautified.pdf --pdf-engine=xelatex -V geometry:margin=1in
if errorlevel 1 (
  echo [ERROR] PDF build failed.
  exit /b 1
)

echo [OK] Created ew_rp_comparison_beautified.pdf
exit /b 0
