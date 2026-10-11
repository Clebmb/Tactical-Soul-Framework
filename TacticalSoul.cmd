@echo off
setlocal
set "TSF_PYTHON=%~dp0runtime\python\python.exe"
if not exist "%TSF_PYTHON%" set "TSF_PYTHON=%~dp0tools\python-embed\python.exe"
if not exist "%TSF_PYTHON%" set "TSF_PYTHON=python"
"%TSF_PYTHON%" "%~dp0scripts\aria_tool.py" %*
exit /b %errorlevel%
