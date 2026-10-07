@echo off
REM Double-click to start the MS Break Assistant on Windows.
cd /d "%~dp0"
where py >nul 2>nul && (set PY=py -3) || (set PY=python)
%PY% --version >nul 2>nul || (
  echo Python 3 is not installed. Get it from https://www.python.org/downloads/
  echo During install, tick "Add python.exe to PATH". Then run this again.
  pause & exit /b 1
)
if not exist .venv (
  echo First run: setting up, this takes a minute...
  %PY% -m venv .venv || (pause & exit /b 1)
)
.venv\Scripts\python -m pip install -q -r requirements.txt || (pause & exit /b 1)
.venv\Scripts\python run_local.py %*
pause
