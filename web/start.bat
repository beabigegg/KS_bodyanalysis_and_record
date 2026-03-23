@echo off
setlocal

cd /d "%~dp0"

if "%CONDA_ENV_NAME%"=="" set "CONDA_ENV_NAME=base"
if not "%CONDA_PREFIX%"=="" goto :run
if not "%CONDA_EXE%"=="" (
  call "%CONDA_EXE%" activate "%CONDA_ENV_NAME%" >nul 2>&1
)

:run
if "%APP_HOST%"=="" set "APP_HOST=0.0.0.0"
if "%APP_PORT%"=="" set "APP_PORT=12010"
if "%APP_MODE%"=="" set "APP_MODE=dev"

if /I "%APP_MODE%"=="dev" (
  uvicorn app:app --app-dir backend --host %APP_HOST% --port %APP_PORT% --reload
) else (
  uvicorn app:app --app-dir backend --host %APP_HOST% --port %APP_PORT%
)

endlocal

