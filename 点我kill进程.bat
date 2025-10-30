@echo off
echo ================================================
echo   Stop All Services
echo ================================================
echo.

echo Stopping Python processes...
taskkill /F /IM python.exe /T >nul 2>&1
if errorlevel 1 (
    echo No Python processes found
) else (
    echo Python processes stopped
)

echo Stopping Node.js processes...
taskkill /F /IM node.exe /T >nul 2>&1
if errorlevel 1 (
    echo No Node.js processes found
) else (
    echo Node.js processes stopped
)

timeout /t 2 /nobreak >nul

echo.
echo ================================================
echo All services stopped!
echo ================================================
echo.
echo Press any key to close...
pause >nul
