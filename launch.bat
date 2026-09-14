@echo off
REM ============================================================
REM  ISHA Multi AI - Portable Launcher
REM  Works from any drive letter (USB/pendrive friendly).
REM  Uses %~dp0 so it NEVER depends on the current directory,
REM  a fixed drive letter, or a hard-coded username.
REM ============================================================

cd /d "%~dp0"

echo ============================================
echo   ISHA Multi AI - Portable Local Assistant
echo   Running from: %~dp0
echo ============================================
echo.

REM --- Find a Python interpreter -------------------------------
where python >nul 2>nul
if %ERRORLEVEL%==0 (
    set PYTHON_CMD=python
    goto :found_python
)

where py >nul 2>nul
if %ERRORLEVEL%==0 (
    set PYTHON_CMD=py
    goto :found_python
)

echo [ERROR] Python was not found on this PC's PATH.
echo Please install Python 3.10+ from https://www.python.org/downloads/
echo (Tip: for a truly self-contained USB drive, you can also place a
echo  portable Python distribution inside this folder and edit this
echo  .bat file's PYTHON_CMD to point at it with a relative path.)
pause
exit /b 1

:found_python
echo Using Python command: %PYTHON_CMD%
echo.

REM --- First run: offer to install dependencies -----------------
if not exist "config\config.json" (
    echo First run detected - no config\config.json yet.
    echo A default one will be created automatically from config.example.json.
    echo.
)

echo Checking dependencies (this only installs what's missing)...
%PYTHON_CMD% -m pip install --quiet --disable-pip-version-check -r requirements\requirements.txt
echo.

REM --- Launch ISHA -----------------------------------------------
%PYTHON_CMD% main.py

echo.
echo ISHA has exited.
pause
