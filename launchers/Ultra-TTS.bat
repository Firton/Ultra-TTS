@echo off
setlocal

set "ROOT=%~dp0.."
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%ROOT%\desktop-launcher.ps1"

endlocal
