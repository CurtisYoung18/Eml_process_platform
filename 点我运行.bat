@echo off
echo ================================================
echo   Email Processing Platform - Startup
echo ================================================
echo.

echo [1/6] Checking Python...
python --version
if errorlevel 1 (
    echo [ERROR] Python not found!
    pause
    exit /b 1
)
echo.

echo [2/6] Checking Node.js...
node --version
if errorlevel 1 (
    echo [ERROR] Node.js not found!
    pause
    exit /b 1
)
echo.

echo [3/6] Checking virtual environment...
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)
echo [SUCCESS] Virtual environment ready
echo.

echo [4/6] Activating virtual environment...
call venv\Scripts\activate
echo [SUCCESS] Activated
echo.

echo [5/6] Installing dependencies...
if not exist "venv\Lib\site-packages\flask" (
    pip install -r requirements.txt -q
)
cd frontend
if not exist "node_modules" (
    call npm install
)
cd ..
echo [SUCCESS] Dependencies ready
echo.

echo [6/6] Starting services...
taskkill /F /IM python.exe /T >nul 2>&1
taskkill /F /IM node.exe /T >nul 2>&1
timeout /t 2 /nobreak >nul
echo.

echo Starting Backend...
start "Backend" cmd /k "cd /d %~dp0 && call venv\Scripts\activate && python api_server.py"
timeout /t 8 /nobreak >nul

echo Starting Frontend...
cd frontend
start "Frontend" cmd /k "npm run dev"
cd ..
timeout /t 10 /nobreak >nul

echo.
echo ================================================
echo Services Started!
echo ================================================
echo.
echo Frontend: http://localhost:3000
echo Backend:  http://localhost:5001
echo.
echo Keep the two service windows open!
echo.
timeout /t 3 /nobreak
start http://localhost:3000

echo.
echo Press any key to close this window...
pause >nul
