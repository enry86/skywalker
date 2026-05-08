@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
set "PROJECT_DIR=%SCRIPT_DIR%.."
set "PYTHON_EXE=%PROJECT_DIR%\venv\Scripts\python.exe"

if not exist "%PYTHON_EXE%" (
  echo [ERROR] venv python not found: "%PYTHON_EXE%"
  echo Create it first: python -m venv venv
  exit /b 1
)

if "%~1"=="" (
  echo Usage:
  echo   scripts\run_motor_step.bat --port COM5 [extra options]
  echo Example:
  echo   scripts\run_motor_step.bat --port COM5 --levels 0.2,0.5,1.0,1.5,2.0 --hold 2
  exit /b 1
)

"%PYTHON_EXE%" "%PROJECT_DIR%\scripts\motor_step_test.py" --mode step %*
