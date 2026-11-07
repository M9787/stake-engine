@echo off
rem Stake Game Factory editor (docs/10 plan v3.3, M12). Double-click to start; close this window to stop.
cd /d "%~dp0.."
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\doctor.ps1
if errorlevel 1 (
  echo.
  echo The environment check failed. Fix the FAIL rows above, then start again.
  pause
  exit /b 1
)
cd /d "%~dp0"
if not exist node_modules (
  echo Installing the editor once...
  call pnpm install --prefer-offline || (echo Install failed. & pause & exit /b 1)
)
start "" http://127.0.0.1:5174
call pnpm exec vite dev
