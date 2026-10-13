@echo off
setlocal
pushd "%~dp0..\.."
call TacticalSoul.cmd play "examples\custom_room\mod.json" %*
set "mod_exit=%errorlevel%"
popd
if not "%mod_exit%"=="0" pause
exit /b %mod_exit%
