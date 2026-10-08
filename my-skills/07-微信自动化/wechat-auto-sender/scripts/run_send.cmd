@echo off
rem ============================================================
rem  WeChat auto-sender -- launcher
rem  Called by Windows Task Scheduler (e.g. 01:00 / 02:00 daily).
rem  NOTE: keep this file pure ASCII. Non-ASCII comments break
rem        cmd.exe parsing under non-UTF8 console code pages.
rem
rem  Python interpreter resolution order:
rem    1) %PY%  environment variable (full path to python.exe)
rem    2) python found in PATH
rem ============================================================
setlocal
set "SCRIPT_DIR=%~dp0"

if defined PY (
  set "PYEXE=%PY%"
) else (
  set "PYEXE=python"
)

cd /d "%SCRIPT_DIR%"
"%PYEXE%" "%SCRIPT_DIR%send_daily.py" %*
set "RC=%ERRORLEVEL%"
if not defined RC set "RC=0"
echo [%DATE% %TIME%] launcher done (exit=%RC%) >> "%SCRIPT_DIR%launcher.log"
endlocal
exit /b %RC%
