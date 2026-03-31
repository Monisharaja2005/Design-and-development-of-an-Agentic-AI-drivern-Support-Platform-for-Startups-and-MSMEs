@echo off
setlocal

set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

set "BACKEND_DIR=%ROOT%"
set "FRONTEND_DIR=%ROOT%\frontend"
set "VENV_PY=%ROOT%\.venv\Scripts\python.exe"

if not exist "%FRONTEND_DIR%\package.json" (
  echo Frontend folder not found at "%FRONTEND_DIR%".
  pause
  exit /b 1
)

if not exist "%VENV_PY%" (
  echo Python virtual environment not found at "%VENV_PY%".
  echo.
  echo Create it with:
  echo   cd /d "%BACKEND_DIR%"
  echo   python -m venv .venv
  echo   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
  echo   .\.venv\Scripts\python.exe -m pip install openai python-dotenv
  echo.
  pause
  exit /b 1
)

echo Starting KARIOS backend...
start "KARIOS Backend" powershell -NoExit -ExecutionPolicy Bypass -Command ^
  "Set-Location '%BACKEND_DIR%'; & '%VENV_PY%' -m pip install -r requirements.txt; & '%VENV_PY%' -m pip install openai python-dotenv; & '%VENV_PY%' ai_scheme_server.py"

echo Starting KARIOS frontend...
start "KARIOS Frontend" powershell -NoExit -ExecutionPolicy Bypass -Command ^
  "Set-Location '%FRONTEND_DIR%'; npm install; npm run dev"

echo.
echo Backend  : http://127.0.0.1:8000
echo Frontend : http://127.0.0.1:5173
echo.
echo Two PowerShell windows were opened.
echo Close those windows when you want to stop the app.
echo.
pause
