@echo off
setlocal
set "PYTHON="
where py >nul 2>nul && set "PYTHON=py -3"
if not defined PYTHON where python >nul 2>nul && set "PYTHON=python"
if not defined PYTHON (
  echo Python 3.10+ was not found. Install it from https://www.python.org/downloads/windows/
  exit /b 2
)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0install_qoder.ps1" %*
exit /b %errorlevel%
