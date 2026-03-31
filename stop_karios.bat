@echo off
setlocal EnableDelayedExpansion

call :stop_port 8000 "KARIOS Backend"
call :stop_port 5173 "KARIOS Frontend"

echo.
echo Stop check complete.
echo.
pause
exit /b 0

:stop_port
set "PORT=%~1"
set "LABEL=%~2"
set "FOUND=0"

for /f "tokens=5" %%P in ('netstat -ano ^| findstr /R /C:":%PORT% .*LISTENING"') do (
  set "PID=%%P"
  if not "!PID!"=="" (
    set "FOUND=1"
    echo Stopping %LABEL% on port %PORT% ^(PID !PID!^)...
    taskkill /F /PID !PID! >nul 2>&1
    if errorlevel 1 (
      echo Could not stop PID !PID! on port %PORT%.
    ) else (
      echo Stopped PID !PID! on port %PORT%.
    )
  )
)

if "!FOUND!"=="0" (
  echo No process is listening on port %PORT% for %LABEL%.
)

echo.
exit /b 0
