@echo off
setlocal
cd /d "%~dp0"
set "PATH=%ProgramFiles%\nodejs;%PATH%"
if not exist "%ProgramFiles%\nodejs\node.exe" (
  echo Khong tim thay Node.js tai Program Files\nodejs.
  pause
  exit /b 1
)
"%ProgramFiles%\nodejs\node.exe" node_modules\@playwright\test\cli.js test --config playwright.employees-review.config.ts
pause
