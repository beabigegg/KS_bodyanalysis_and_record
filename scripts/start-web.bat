@echo off
setlocal

cd /d "%~dp0\.."

if "%CONDA_ENV_NAME%"=="" set "CONDA_ENV_NAME=ksbody"
if "%RUN_NPM_CI%"=="" set "RUN_NPM_CI=auto"

if not "%CONDA_PREFIX%"=="" goto :build
where conda >nul 2>nul
if not errorlevel 1 (
  for /f "delims=" %%i in ('conda info --base 2^>nul') do set "CONDA_BASE=%%i"
  if exist "%CONDA_BASE%\condabin\conda.bat" (
    call "%CONDA_BASE%\condabin\conda.bat" activate "%CONDA_ENV_NAME%"
    if errorlevel 1 exit /b 1
    goto :build
  )
)
if exist ".venv\Scripts\activate.bat" (
  call ".venv\Scripts\activate.bat"
  goto :build
)
echo No active conda env and no local .venv found.
exit /b 1

:build
echo Building frontend...
cd ksbody\web\frontend
if "%RUN_NPM_CI%"=="1" call npm ci
if "%RUN_NPM_CI%"=="true" call npm ci
if not exist node_modules call npm ci
call npm run build
cd /d "%~dp0\.."

echo.
echo   KS Body Analysis Web
echo   http://localhost:12010/
echo.

python -m ksbody web

endlocal
