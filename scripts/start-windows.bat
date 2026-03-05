@echo off
setlocal

cd /d "%~dp0\.."

docker compose up --build -d
if errorlevel 1 exit /b 1

if "%APP_PORT%"=="" set APP_PORT=8010
echo App started at http://127.0.0.1:%APP_PORT%
