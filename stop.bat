@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM ================================================================
REM Email Knowledge Base Processing System - Stop Script (Windows)
REM ================================================================

echo ================================================================
echo         Email Knowledge Base Processing System - Stop Services
echo ================================================================
echo.

echo [INFO] Stopping all services...
echo.

REM Stop Backend API Server
echo [INFO] Stopping backend API server...
taskkill /FI "WINDOWTITLE eq Email Processing API Server*" /T /F >nul 2>&1
if %errorlevel% equ 0 (
    echo [SUCCESS] Backend service stopped
) else (
    echo [WARNING] Backend service not running or already stopped
)

REM Stop Frontend Development Server
echo [INFO] Stopping frontend development server...
taskkill /FI "WINDOWTITLE eq Frontend Development Server*" /T /F >nul 2>&1
if %errorlevel% equ 0 (
    echo [SUCCESS] Frontend service stopped
) else (
    echo [WARNING] Frontend service not running or already stopped
)

REM Additional cleanup: Stop all related processes
echo.
echo [INFO] Cleaning up remaining processes...

REM Stop all Python api_server processes
for /f "tokens=2" %%i in ('tasklist /FI "IMAGENAME eq python.exe" /FO LIST ^| findstr /C:"PID:"') do (
    wmic process where "ProcessId=%%i" get CommandLine 2>nul | findstr /C:"api_server.py" >nul
    if !errorlevel! equ 0 (
        taskkill /PID %%i /F >nul 2>&1
        echo [SUCCESS] Cleaned up api_server.py process (PID: %%i)
    )
)

REM Stop all Node.js processes (frontend)
for /f "tokens=2" %%i in ('tasklist /FI "IMAGENAME eq node.exe" /FO LIST ^| findstr /C:"PID:"') do (
    wmic process where "ProcessId=%%i" get CommandLine 2>nul | findstr /C:"next" >nul
    if !errorlevel! equ 0 (
        taskkill /PID %%i /F /T >nul 2>&1
        echo [SUCCESS] Cleaned up next-server process (PID: %%i)
    )
)

REM Clean up PID files
if exist "logs\api_server.pid" del /q logs\api_server.pid
if exist "logs\frontend.pid" del /q logs\frontend.pid

echo.
echo ================================================================
echo All services stopped
echo ================================================================
echo.
pause
