@echo off
chcp 65001 >nul
title 邮件知识库管理系统
color 0B

echo.
echo ================================================================
echo                   邮件知识库管理系统
echo                      正在启动...
echo ================================================================
echo.

REM 检查虚拟环境是否存在
if not exist venv (
    echo ❌ 错误：找不到虚拟环境文件夹 venv
    echo 请确保在正确的项目目录下运行此文件
    pause
    exit /b 1
)

REM 检查激活脚本是否存在
if not exist venv\Scripts\activate.bat (
    echo ❌ 错误：虚拟环境损坏，找不到激活脚本
    pause
    exit /b 1
)

echo 🔧 激活Python环境...
call venv\Scripts\activate

echo 🚀 启动邮件知识库管理系统...
echo.
echo 系统启动后将自动在浏览器中打开
echo 如果没有自动打开，请访问：http://localhost:8501
echo.
echo 按 Ctrl+C 可以停止系统
echo ================================================================
echo.

python run_app.py

if errorlevel 1 (
    echo.
    echo ❌ 系统启动失败！
    echo 可能的原因：
    echo 1. 依赖包未正确安装
    echo 2. Python环境有问题  
    echo 3. 项目文件缺失
    echo.
    pause
) else (
    echo.
    echo 👋 系统已关闭
    pause
)