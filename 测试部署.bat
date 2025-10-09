@echo off
chcp 65001 >nul
title 邮件知识库管理系统 - 部署测试
color 0E

echo.
echo ================================================================
echo                   邮件知识库管理系统
echo                     部署测试脚本
echo ================================================================
echo.
echo 🔍 开始检查部署状态...
echo.

REM 检查虚拟环境
if not exist venv (
    echo ❌ 虚拟环境不存在
    echo 请先运行"一键部署.bat"
    pause
    exit /b 1
)
echo ✅ 虚拟环境存在

REM 激活虚拟环境
call venv\Scripts\activate
if errorlevel 1 (
    echo ❌ 虚拟环境激活失败
    pause
    exit /b 1
)
echo ✅ 虚拟环境激活成功

REM 检查Python版本
echo.
echo 🐍 Python环境信息：
python --version
echo.

REM 检查关键依赖包
echo 📦 检查依赖包安装状态：
python -c "import streamlit; print('✅ Streamlit:', streamlit.__version__)"
if errorlevel 1 (
    echo ❌ Streamlit 未安装或有问题
    set has_error=1
)

python -c "import requests; print('✅ Requests:', requests.__version__)"
if errorlevel 1 (
    echo ❌ Requests 未安装或有问题
    set has_error=1
)

python -c "import pandas; print('✅ Pandas:', pandas.__version__)"
if errorlevel 1 (
    echo ❌ Pandas 未安装或有问题
    set has_error=1
)

python -c "from dotenv import load_dotenv; print('✅ Python-dotenv 可用')"
if errorlevel 1 (
    echo ❌ Python-dotenv 未安装或有问题
    set has_error=1
)

python -c "from streamlit_option_menu import option_menu; print('✅ Streamlit-option-menu 可用')"
if errorlevel 1 (
    echo ❌ Streamlit-option-menu 未安装或有问题
    set has_error=1
)

python -c "from streamlit_mermaid import st_mermaid; print('✅ Streamlit-mermaid 可用')" 2>nul
if errorlevel 1 (
    echo ⚠️  Streamlit-mermaid 未安装（可选包，不影响基本功能）
)

echo.

REM 检查项目文件
echo 📁 检查项目文件：
if exist app.py (
    echo ✅ app.py 存在
) else (
    echo ❌ app.py 不存在
    set has_error=1
)

if exist run_app.py (
    echo ✅ run_app.py 存在
) else (
    echo ❌ run_app.py 不存在
    set has_error=1
)

if exist tools (
    echo ✅ tools 目录存在
) else (
    echo ❌ tools 目录不存在
    set has_error=1
)

if exist config (
    echo ✅ config 目录存在
) else (
    echo ❌ config 目录不存在
    set has_error=1
)

if exist requirements.txt (
    echo ✅ requirements.txt 存在
) else (
    echo ❌ requirements.txt 不存在
    set has_error=1
)

echo.

REM 检查配置文件
echo ⚙️  检查配置文件：
if exist .env (
    echo ✅ .env 文件存在
) else (
    if exist env_example.txt (
        echo ⚠️  .env 文件不存在，但找到 env_example.txt
        echo 💡 建议复制 env_example.txt 为 .env 并配置API Key
    ) else (
        echo ❌ .env 和 env_example.txt 都不存在
        set has_error=1
    )
)

echo.

REM 测试导入
echo 🧪 测试Python模块导入：
python -c "
try:
    from tools import *
    from config import CONFIG, APP_CONFIG, NAVIGATION, init_directories
    print('✅ 所有模块导入成功')
except ImportError as e:
    print(f'❌ 模块导入失败: {e}')
    exit(1)
except Exception as e:
    print(f'❌ 其他错误: {e}')
    exit(1)
"
if errorlevel 1 (
    echo ❌ 模块导入测试失败
    set has_error=1
)

echo.

REM 最终结果
if defined has_error (
    echo ================================================================
    echo                     ❌ 部署测试失败
    echo ================================================================
    echo.
    echo 发现问题，请：
    echo 1. 重新运行"一键部署.bat"
    echo 2. 检查上述错误信息
    echo 3. 确保网络连接正常
    echo.
) else (
    echo ================================================================
    echo                     ✅ 部署测试通过
    echo ================================================================
    echo.
    echo 🎉 系统已正确部署，可以正常使用！
    echo.
    echo 🚀 启动方法：
    echo    双击运行"启动邮件系统.bat"
    echo.
    echo 📋 使用提示：
    echo    1. 首次使用请配置.env文件中的API Key
    echo    2. 浏览器访问 http://localhost:8501
    echo    3. 按照系统指引完成邮件处理流程
    echo.
)

pause
