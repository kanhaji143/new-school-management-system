@echo off
REM Make the live site functional: backend + tunnel + Firebase redeploy.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0make-live.ps1"
pause
