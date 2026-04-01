@echo off
setlocal

cd /d "%~dp0"

if "%CONDA_ENV_NAME%"=="" set "CONDA_ENV_NAME=ksbody"
if not "%CONDA_PREFIX%"=="" goto :build
if not "%CONDA_EXE%"=="" (
  call "%CONDA_EXE%" activate "%CONDA_ENV_NAME%" >nul 2>&1
)

:build
echo Building frontend...
cd frontend
call npm run build
cd ..

echo.
echo   KS Recipe Analysis WebUI
echo   http://localhost:12010/
echo.

python app.py

endlocal
