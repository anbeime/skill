@echo off
setlocal
where py >nul 2>nul
if %errorlevel%==0 (set "PYTHON=py -3") else (set "PYTHON=python")
%PYTHON% "%~dp0setup_auto.py" --project-dir "%~dp0" %*
exit /b %errorlevel%
