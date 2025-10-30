@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM ================================================================
REM Email Knowledge Base Processing System - One-Click Startup Script
REM ================================================================
REM Function: Check environment and start services
REM Usage: Double-click to run start.bat
REM ================================================================

echo ================================================================
echo         Email Knowledge Base Processing System - Startup
echo ================================================================
echo.

REM ================================================================
REM 1. Check Python Environment
REM ================================================================
echo [INFO] Checking Python environment...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not detected!
    echo.
    echo Please install Python manually:
    echo 1. Visit https://www.python.org/downloads/
    echo 2. Download Python 3.12 or higher
    echo 3. Make sure to check "Add Python to PATH" during installation
    echo 4. Restart this script after installation
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo [SUCCESS] Python installed: !PYTHON_VERSION!

REM ================================================================
REM 2. Check Node.js Environment
REM ================================================================
echo [INFO] Checking Node.js environment...

REM Try to find Node.js in common installation paths and add to PATH
if exist "C:\Program Files\nodejs\node.exe" (
    set "PATH=C:\Program Files\nodejs;%APPDATA%\npm;%PATH%"
)
if exist "C:\Program Files (x86)\nodejs\node.exe" (
    set "PATH=C:\Program Files (x86)\nodejs;%APPDATA%\npm;%PATH%"
)
if exist "%LOCALAPPDATA%\Programs\nodejs\node.exe" (
    set "PATH=%LOCALAPPDATA%\Programs\nodejs;%APPDATA%\npm;%PATH%"
)

REM Test if node command works
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js not detected!
    echo.
    echo Please check:
    echo 1. Is Node.js installed? Check "Add/Remove Programs"
    echo 2. Try running in a NEW command prompt: node --version
    echo 3. If that works, close this window and run start.bat again
    echo.
    echo If Node.js is NOT installed:
    echo 1. Visit https://nodejs.org/
    echo 2. Download Node.js 20 LTS version
    echo 3. Run installer and check "Add to PATH"
    echo 4. Restart computer
    echo 5. Run this script again
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('node --version') do set NODE_VERSION=%%i
for /f "tokens=*" %%i in ('npm --version') do set NPM_VERSION=%%i
echo [SUCCESS] Node.js installed: !NODE_VERSION!
echo [SUCCESS] npm installed: v!NPM_VERSION!

REM ================================================================
REM 3. Create Python Virtual Environment
REM ================================================================
echo [INFO] Setting up Python virtual environment...
if not exist "venv" (
    echo [INFO] Creating Python virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment!
        echo Please ensure Python is properly installed.
        pause
        exit /b 1
    )
    echo [SUCCESS] Virtual environment created
) else (
    echo [SUCCESS] Virtual environment already exists
)

REM Activate virtual environment
call venv\Scripts\activate
if %errorlevel% neq 0 (
    echo [ERROR] Failed to activate virtual environment!
    pause
    exit /b 1
)
echo [SUCCESS] Virtual environment activated

REM ================================================================
REM 4. Install Python Dependencies
REM ================================================================
echo [INFO] Installing Python dependencies...
python -m pip install --upgrade pip -q
if %errorlevel% neq 0 (
    echo [WARNING] Failed to upgrade pip, continuing...
)

pip install -r requirements.txt -q
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install Python dependencies!
    echo.
    echo Please try installing manually:
    echo   1. Open command prompt in project directory
    echo   2. Run: venv\Scripts\activate
    echo   3. Run: pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)
echo [SUCCESS] Python dependencies installed

REM ================================================================
REM 5. Check and Create .env File
REM ================================================================
if not exist ".env" (
    if exist "env_example.txt" (
        echo [WARNING] .env file not found, creating from env_example.txt...
        copy env_example.txt .env >nul
        echo [SUCCESS] .env file created
        echo [WARNING] Please edit .env file and enter your actual API Keys
    ) else (
        echo [WARNING] .env file not found, please create and configure API Keys manually
    )
) else (
    echo [SUCCESS] .env file already exists
)

REM ================================================================
REM 6. Install Frontend Dependencies
REM ================================================================
echo [INFO] Installing frontend dependencies...
cd frontend

if not exist "node_modules" (
    echo [INFO] First time installation, this may take a few minutes...
    call npm install
    if %errorlevel% neq 0 (
        echo [ERROR] Frontend dependencies installation failed!
        echo.
        echo Please try installing manually:
        echo   1. Open command prompt
        echo   2. cd frontend
        echo   3. npm install
        echo.
        cd ..
        pause
        exit /b 1
    )
    echo [SUCCESS] Frontend dependencies installed
) else (
    echo [INFO] Checking for dependency updates...
    call npm install
    if %errorlevel% neq 0 (
        echo [WARNING] Failed to update dependencies, using existing ones...
    ) else (
        echo [SUCCESS] Frontend dependencies are up to date
    )
)

cd ..

REM ================================================================
REM 7. Create Log Directory
REM ================================================================
if not exist "logs" (
    mkdir logs
    echo [SUCCESS] Log directory created
)

REM ================================================================
REM 8. Start Backend API Server
REM ================================================================
echo.
echo ================================================================
echo [INFO] Starting backend API server...
echo ================================================================

REM Start backend (new window)
start "Email Processing API Server" /min cmd /k "call venv\Scripts\activate && python api_server.py > logs\api_server.log 2>&1"

REM Wait for backend to start
echo [INFO] Waiting for backend service to start...
timeout /t 5 /nobreak >nul
echo [SUCCESS] Backend API server started successfully

REM ================================================================
REM 9. Start Frontend Development Server
REM ================================================================
echo.
echo ================================================================
echo [INFO] Starting frontend development server...
echo ================================================================

REM Start frontend (new window)
cd frontend
start "Frontend Development Server" /min cmd /k "npm run dev > ..\logs\frontend.log 2>&1"
cd ..

REM Wait for frontend to start
echo [INFO] Waiting for frontend service to start...
timeout /t 8 /nobreak >nul
echo [SUCCESS] Frontend development server started successfully

REM ================================================================
REM 10. Startup Success Message
REM ================================================================
echo.
echo ================================================================
echo Email Processing Platform Started Successfully!
echo ================================================================
echo.
echo Access URLs:
echo    Frontend App: http://localhost:3000
echo    Backend API:  http://localhost:5001
echo.
echo Log Files:
echo    Backend Log: logs\api_server.log
echo    Frontend Log: logs\frontend.log
echo.
echo To Stop Services:
echo    Close "Email Processing API Server" and "Frontend Development Server" windows
echo    Or run: stop.bat
echo.
echo ================================================================
echo.
echo System ready, opening browser...
echo.

REM Wait for services to fully start
timeout /t 3 /nobreak >nul

REM Auto open browser
start http://localhost:3000

echo Tips:
echo    - Two server windows are minimized to taskbar
echo    - Please keep these windows running, do not close them
echo    - You can close this window, services will continue running
echo.
echo Press any key to close this window (services will continue in background)...
pause >nul
