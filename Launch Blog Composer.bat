@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>&1
if %ERRORLEVEL%==0 (
  py -3 "tools\blog-composer\composer.py"
) else (
  python "tools\blog-composer\composer.py"
)

if %ERRORLEVEL% NEQ 0 (
  echo.
  echo Failed to launch Blog Composer. Make sure Python 3 is installed.
  pause
)
