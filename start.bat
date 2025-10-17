@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM ================================================================
REM 邮件知识库处理系统 - 一键启动脚本 (Windows)
REM ================================================================
REM 功能：自动检测并安装所有必需的环境和依赖
REM 使用：双击运行 start.bat
REM ================================================================

echo ════════════════════════════════════════════════════════════
echo         📧 邮件知识库处理系统 - 一键启动
echo ════════════════════════════════════════════════════════════
echo.

REM ================================================================
REM 1. 检查 Python 环境
REM ================================================================
echo [INFO] 检查 Python 环境...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] ❌ 未检测到 Python！
    echo.
    echo 请按照以下步骤安装 Python:
    echo 1. 访问 https://www.python.org/downloads/
    echo 2. 下载 Python 3.12 或更高版本
    echo 3. 安装时务必勾选 "Add Python to PATH"
    echo 4. 安装完成后重新运行本脚本
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo [SUCCESS] ✅ Python 已安装: !PYTHON_VERSION!

REM ================================================================
REM 2. 检查 Node.js 环境
REM ================================================================
echo [INFO] 检查 Node.js 环境...
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] ⚠️  未检测到 Node.js，正在安装...
    echo.
    echo 正在下载 Node.js 20 LTS 安装程序...
    
    REM 检查系统架构
    if "%PROCESSOR_ARCHITECTURE%"=="AMD64" (
        set NODE_INSTALLER=node-v20.11.1-x64.msi
        set NODE_URL=https://nodejs.org/dist/v20.11.1/node-v20.11.1-x64.msi
    ) else (
        set NODE_INSTALLER=node-v20.11.1-x86.msi
        set NODE_URL=https://nodejs.org/dist/v20.11.1/node-v20.11.1-x86.msi
    )
    
    REM 下载 Node.js 安装程序
    echo [INFO] 下载地址: !NODE_URL!
    powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '!NODE_URL!' -OutFile '!NODE_INSTALLER!'}"
    
    if exist !NODE_INSTALLER! (
        echo [INFO] 下载完成，正在安装 Node.js...
        echo [INFO] 请在弹出的安装向导中点击"下一步"完成安装
        echo [INFO] 安装路径使用默认即可
        echo.
        
        REM 静默安装 Node.js
        msiexec /i !NODE_INSTALLER! /qn /norestart
        
        REM 等待安装完成
        timeout /t 30 /nobreak >nul
        
        REM 刷新环境变量
        call refreshenv.cmd 2>nul
        
        REM 删除安装程序
        del !NODE_INSTALLER!
        
        echo [SUCCESS] ✅ Node.js 安装完成！
        echo [INFO] 正在刷新环境变量...
        
        REM 需要重新启动脚本以加载新的 PATH
        echo.
        echo [WARNING] ⚠️  需要重新启动脚本以加载 Node.js 环境变量
        echo [INFO] 请关闭此窗口，然后重新运行 start.bat
        echo.
        pause
        exit /b 0
    ) else (
        echo [ERROR] ❌ Node.js 下载失败！
        echo.
        echo 请手动安装 Node.js:
        echo 1. 访问 https://nodejs.org/
        echo 2. 下载 20 LTS 版本
        echo 3. 运行安装程序
        echo 4. 安装完成后重新运行本脚本
        echo.
        pause
        exit /b 1
    )
) else (
    for /f "tokens=*" %%i in ('node --version') do set NODE_VERSION=%%i
    for /f "tokens=*" %%i in ('npm --version') do set NPM_VERSION=%%i
    echo [SUCCESS] ✅ Node.js 已安装: !NODE_VERSION!
    echo [SUCCESS] ✅ npm 已安装: v!NPM_VERSION!
)

REM ================================================================
REM 3. 创建 Python 虚拟环境
REM ================================================================
echo [INFO] 配置 Python 虚拟环境...
if not exist "venv" (
    echo [INFO] 创建 Python 虚拟环境...
    python -m venv venv
    echo [SUCCESS] ✅ 虚拟环境创建完成
) else (
    echo [SUCCESS] ✅ 虚拟环境已存在
)

REM 激活虚拟环境
call venv\Scripts\activate
echo [SUCCESS] ✅ 虚拟环境已激活

REM ================================================================
REM 4. 安装 Python 依赖
REM ================================================================
echo [INFO] 安装 Python 依赖...
python -m pip install --upgrade pip -q
pip install -r requirements.txt -q
echo [SUCCESS] ✅ Python 依赖安装完成

REM ================================================================
REM 5. 检查并创建 .env 文件
REM ================================================================
if not exist ".env" (
    if exist "env_example.txt" (
        echo [WARNING] ⚠️  .env 文件不存在，正在从 env_example.txt 创建...
        copy env_example.txt .env >nul
        echo [SUCCESS] ✅ .env 文件创建完成
        echo [WARNING] ⚠️  请编辑 .env 文件，填入您的实际 API Keys
    ) else (
        echo [WARNING] ⚠️  .env 文件不存在，请手动创建并配置 API Keys
    )
) else (
    echo [SUCCESS] ✅ .env 文件已存在
)

REM ================================================================
REM 6. 安装前端依赖
REM ================================================================
echo [INFO] 安装前端依赖...
cd frontend

if not exist "node_modules" (
    echo [INFO] 首次安装，这可能需要几分钟...
    call npm install
    if %errorlevel% neq 0 (
        echo [ERROR] ❌ 前端依赖安装失败！
        cd ..
        pause
        exit /b 1
    )
    echo [SUCCESS] ✅ 前端依赖安装完成
) else (
    echo [INFO] 检查依赖更新...
    call npm install
    echo [SUCCESS] ✅ 前端依赖已是最新
)

cd ..

REM ================================================================
REM 7. 创建日志目录
REM ================================================================
if not exist "logs" (
    mkdir logs
    echo [SUCCESS] ✅ 日志目录创建完成
)

REM ================================================================
REM 8. 启动后端 API 服务器
REM ================================================================
echo.
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo [INFO] 🔧 启动后端 API 服务器...
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

REM 启动后端（新窗口）
start "邮件处理API服务器" /min cmd /k "call venv\Scripts\activate && python api_server.py > logs\api_server.log 2>&1"

REM 等待后端启动
echo [INFO] 等待后端服务启动...
timeout /t 5 /nobreak >nul
echo [SUCCESS] ✅ 后端 API 服务器启动成功

REM ================================================================
REM 9. 启动前端开发服务器
REM ================================================================
echo.
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo [INFO] 🎨 启动前端开发服务器...
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

REM 启动前端（新窗口）
cd frontend
start "前端开发服务器" /min cmd /k "npm run dev > ..\logs\frontend.log 2>&1"
cd ..

REM 等待前端启动
echo [INFO] 等待前端服务启动...
timeout /t 8 /nobreak >nul
echo [SUCCESS] ✅ 前端开发服务器启动成功

REM ================================================================
REM 10. 启动成功提示
REM ================================================================
echo.
echo ════════════════════════════════════════════════════════════
echo ✅ 邮件处理平台启动成功！
echo ════════════════════════════════════════════════════════════
echo.
echo 📍 访问地址：
echo    前端应用: http://localhost:3000
echo    后端API:  http://localhost:5001
echo.
echo 📂 日志文件：
echo    后端日志: logs\api_server.log
echo    前端日志: logs\frontend.log
echo.
echo ⚠️  停止服务：
echo    关闭 "邮件处理API服务器" 和 "前端开发服务器" 窗口
echo    或运行: stop.bat
echo.
echo ════════════════════════════════════════════════════════════
echo.
echo 🎉 系统已就绪，正在打开浏览器...
echo.

REM 等待服务完全启动
timeout /t 3 /nobreak >nul

REM 自动打开浏览器
start http://localhost:3000

echo 📌 提示：
echo    - 两个服务器窗口已最小化到任务栏
echo    - 请保持这些窗口运行，不要关闭
echo    - 可以关闭本窗口，服务将继续运行
echo.
echo 按任意键关闭本窗口（服务将继续在后台运行）...
pause >nul
