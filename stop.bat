@echo off
chcp 65001 >nul

REM ================================================================
REM 邮件知识库处理系统 - 停止脚本 (Windows)
REM ================================================================

echo ════════════════════════════════════════════════════════════
echo         📧 邮件知识库处理系统 - 停止服务
echo ════════════════════════════════════════════════════════════
echo.

echo [INFO] 正在停止所有服务...
echo.

REM 停止后端 API 服务器
echo [INFO] 停止后端 API 服务器...
taskkill /FI "WINDOWTITLE eq 邮件处理API服务器*" /T /F >nul 2>&1
if %errorlevel% equ 0 (
    echo [SUCCESS] ✅ 后端服务已停止
) else (
    echo [WARNING] ⚠️  后端服务未运行或已停止
)

REM 停止前端开发服务器
echo [INFO] 停止前端开发服务器...
taskkill /FI "WINDOWTITLE eq 前端开发服务器*" /T /F >nul 2>&1
if %errorlevel% equ 0 (
    echo [SUCCESS] ✅ 前端服务已停止
) else (
    echo [WARNING] ⚠️  前端服务未运行或已停止
)

REM 额外清理：停止所有相关进程
echo.
echo [INFO] 清理残留进程...

REM 停止所有 Python api_server 进程
for /f "tokens=2" %%i in ('tasklist /FI "IMAGENAME eq python.exe" /FO LIST ^| findstr /C:"PID:"') do (
    wmic process where "ProcessId=%%i" get CommandLine 2>nul | findstr /C:"api_server.py" >nul
    if !errorlevel! equ 0 (
        taskkill /PID %%i /F >nul 2>&1
        echo [SUCCESS] ✅ 清理了 api_server.py 进程 (PID: %%i)
    )
)

REM 停止所有 Node.js 进程（前端）
for /f "tokens=2" %%i in ('tasklist /FI "IMAGENAME eq node.exe" /FO LIST ^| findstr /C:"PID:"') do (
    wmic process where "ProcessId=%%i" get CommandLine 2>nul | findstr /C:"next" >nul
    if !errorlevel! equ 0 (
        taskkill /PID %%i /F /T >nul 2>&1
        echo [SUCCESS] ✅ 清理了 next-server 进程 (PID: %%i)
    )
)

REM 清理 PID 文件
if exist "logs\api_server.pid" del /q logs\api_server.pid
if exist "logs\frontend.pid" del /q logs\frontend.pid

echo.
echo ════════════════════════════════════════════════════════════
echo ✅ 所有服务已停止
echo ════════════════════════════════════════════════════════════
echo.
pause

