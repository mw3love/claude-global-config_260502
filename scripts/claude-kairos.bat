@echo off
rem ASCII only. Korean text lives in claude-kairos.ps1 (cmd.exe cannot parse a UTF-8 .bat).
rem find.exe is called by full path: a Git Bash PATH shadows it with GNU find.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0claude-kairos.ps1" %*
echo %cmdcmdline% | %SystemRoot%\System32\find.exe /i "%~nx0" >nul && pause
