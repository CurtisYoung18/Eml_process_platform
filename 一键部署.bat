@echo off
chcp 65001 >nul
title 邮件知识库管理系统 - 一键部署
color 0B

echo.
echo ================================================================
echo                   邮件知识库管理系统
echo                     一键部署脚本
echo ================================================================
echo.
echo 🚀 开始自动部署...
echo.

REM 记录开始时间
echo [%date% %time%] 开始部署 >> deploy.log

REM 检查Python版本
echo 🔍 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误：未找到Python，请先安装Python 3.11或3.12
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM 获取Python版本信息
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✅ 检测到Python版本: %PYTHON_VERSION%

REM 检查Python版本是否合适
echo %PYTHON_VERSION% | findstr /r "3.1[12]" >nul
if errorlevel 1 (
    echo ⚠️  警告：建议使用Python 3.11或3.12版本以获得最佳兼容性
    echo 当前版本: %PYTHON_VERSION%
    echo 是否继续? (Y/N)
    set /p choice=
    if /i not "%choice%"=="Y" (
        echo 部署已取消
        pause
        exit /b 1
    )
)

REM 检查pip是否可用
echo 🔍 检查pip...
python -m pip --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误：pip不可用，请重新安装Python
    pause
    exit /b 1
)
echo ✅ pip可用

REM 清理旧的虚拟环境
if exist venv (
    echo 🧹 清理旧的虚拟环境...
    rmdir /s /q venv
)

REM 创建虚拟环境
echo 🏗️  创建Python虚拟环境...
python -m venv venv
if errorlevel 1 (
    echo ❌ 创建虚拟环境失败
    pause
    exit /b 1
)
echo ✅ 虚拟环境创建成功

REM 激活虚拟环境
echo 🔧 激活虚拟环境...
call venv\Scripts\activate
if errorlevel 1 (
    echo ❌ 激活虚拟环境失败
    pause
    exit /b 1
)
echo ✅ 虚拟环境已激活

REM 升级pip
echo 📦 升级pip到最新版本...
python -m pip install --upgrade pip
if errorlevel 1 (
    echo ⚠️  pip升级失败，继续使用当前版本
)

REM 清理pip缓存
echo 🧹 清理pip缓存...
python -m pip cache purge

REM 安装基础依赖
echo 📦 安装基础依赖包...
python -m pip install wheel setuptools
if errorlevel 1 (
    echo ❌ 安装基础依赖失败
    pause
    exit /b 1
)

REM 检查requirements.txt是否存在
if not exist requirements.txt (
    echo ❌ 错误：找不到requirements.txt文件
    echo 请确保在正确的项目目录下运行此脚本
    pause
    exit /b 1
)

REM 安装项目依赖
echo 📦 安装项目依赖包...
echo 这可能需要几分钟时间，请耐心等待...
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo ❌ 安装依赖包失败
    echo 正在尝试逐个安装关键包...
    
    REM 逐个安装关键包
    echo 安装Streamlit...
    python -m pip install streamlit>=1.28.0
    
    echo 安装requests...
    python -m pip install requests>=2.28.0
    
    echo 安装pandas...
    python -m pip install pandas>=1.5.0
    
    echo 安装其他包...
    python -m pip install email-validator>=1.3.0
    python -m pip install python-magic>=0.4.27
    python -m pip install markdown>=3.4.0
    python -m pip install streamlit-option-menu>=0.3.6
    python -m pip install python-dotenv>=0.21.0
)

REM 尝试安装streamlit-mermaid（可选）
echo 📦 安装Mermaid图表支持...
python -m pip install streamlit-mermaid
if errorlevel 1 (
    echo ⚠️  streamlit-mermaid安装失败，将使用备用显示方案
) else (
    echo ✅ Mermaid图表支持安装成功
)

REM 验证关键包安装
echo 🔍 验证依赖包安装...
python -c "import streamlit; print('✅ Streamlit:', streamlit.__version__)" 2>nul || echo "❌ Streamlit安装失败"
python -c "import requests; print('✅ Requests:', requests.__version__)" 2>nul || echo "❌ Requests安装失败"
python -c "import pandas; print('✅ Pandas:', pandas.__version__)" 2>nul || echo "❌ Pandas安装失败"

REM 检查主要文件是否存在
echo 🔍 检查项目文件...
if not exist app.py (
    echo ❌ 错误：找不到app.py文件
    pause
    exit /b 1
)
if not exist run_app.py (
    echo ❌ 错误：找不到run_app.py文件
    pause
    exit /b 1
)
if not exist tools (
    echo ❌ 错误：找不到tools目录
    pause
    exit /b 1
)
echo ✅ 项目文件检查完成

REM 创建启动脚本
echo 🚀 创建启动脚本...
(
echo @echo off
echo chcp 65001 ^>nul
echo title 邮件知识库管理系统
echo color 0B
echo.
echo ================================================================
echo                   邮件知识库管理系统
echo                      正在启动...
echo ================================================================
echo.
echo.
echo REM 检查虚拟环境是否存在
echo if not exist venv ^(
echo     echo ❌ 错误：找不到虚拟环境文件夹 venv
echo     echo 请先运行"一键部署.bat"进行部署
echo     pause
echo     exit /b 1
echo ^)
echo.
echo REM 检查激活脚本是否存在
echo if not exist venv\Scripts\activate.bat ^(
echo     echo ❌ 错误：虚拟环境损坏，请重新运行"一键部署.bat"
echo     pause
echo     exit /b 1
echo ^)
echo.
echo echo 🔧 激活Python环境...
echo call venv\Scripts\activate
echo.
echo echo 🚀 启动邮件知识库管理系统...
echo echo.
echo echo 系统启动后将自动在浏览器中打开
echo echo 如果没有自动打开，请访问：http://localhost:8501
echo echo.
echo echo 按 Ctrl+C 可以停止系统
echo echo ================================================================
echo echo.
echo.
echo python run_app.py
echo.
echo if errorlevel 1 ^(
echo     echo.
echo     echo ❌ 系统启动失败！
echo     echo 可能的原因：
echo     echo 1. 依赖包未正确安装
echo     echo 2. Python环境有问题  
echo     echo 3. 项目文件缺失
echo     echo.
echo     echo 请尝试重新运行"一键部署.bat"
echo     pause
echo ^) else ^(
echo     echo.
echo     echo 👋 系统已关闭
echo     pause
echo ^)
) > "启动邮件系统.bat"

echo ✅ 启动脚本创建成功

REM 创建卸载脚本
echo 🗑️  创建卸载脚本...
(
echo @echo off
echo chcp 65001 ^>nul
echo title 邮件知识库管理系统 - 卸载
echo color 0C
echo.
echo ================================================================
echo                   邮件知识库管理系统
echo                      卸载脚本
echo ================================================================
echo.
echo 警告：此操作将删除虚拟环境和所有已安装的依赖包
echo 是否确认卸载？ ^(Y/N^)
echo.
set /p choice=
echo if /i "%%choice%%"=="Y" ^(
echo     echo 🗑️  正在删除虚拟环境...
echo     if exist venv ^(
echo         rmdir /s /q venv
echo         echo ✅ 虚拟环境已删除
echo     ^) else ^(
echo         echo ⚠️  虚拟环境不存在
echo     ^)
echo     echo.
echo     echo ✅ 卸载完成
echo ^) else ^(
echo     echo 卸载已取消
echo ^)
echo pause
) > "卸载系统.bat"

echo ✅ 卸载脚本创建成功

REM 创建更新脚本
echo 🔄 创建更新脚本...
(
echo @echo off
echo chcp 65001 ^>nul
echo title 邮件知识库管理系统 - 更新依赖
echo color 0B
echo.
echo ================================================================
echo                   邮件知识库管理系统
echo                     更新依赖包
echo ================================================================
echo.
echo echo 🔧 激活虚拟环境...
echo call venv\Scripts\activate
echo.
echo echo 📦 更新依赖包...
echo python -m pip install --upgrade pip
echo python -m pip install -r requirements.txt --upgrade
echo.
echo echo ✅ 依赖包更新完成
echo pause
) > "更新依赖.bat"

echo ✅ 更新脚本创建成功

REM 记录部署完成时间
echo [%date% %time%] 部署完成 >> deploy.log

echo.
echo ================================================================
echo                     🎉 部署完成！
echo ================================================================
echo.
echo ✅ 虚拟环境已创建
echo ✅ 依赖包已安装
echo ✅ 启动脚本已创建
echo ✅ 管理脚本已创建
echo.
echo 📁 创建的文件：
echo    - 启动邮件系统.bat    （启动应用）
echo    - 更新依赖.bat        （更新依赖包）
echo    - 卸载系统.bat        （卸载虚拟环境）
echo    - deploy.log          （部署日志）
echo.
echo 🚀 使用方法：
echo    1. 双击"启动邮件系统.bat"启动应用
echo    2. 浏览器访问 http://localhost:8501
echo    3. 使用完毕后按 Ctrl+C 停止
echo.
echo 📝 注意事项：
echo    - 首次启动可能需要等待几秒钟
echo    - 如遇问题可查看deploy.log日志
echo    - 如需更新依赖，运行"更新依赖.bat"
echo.
echo ================================================================
echo.

REM 询问是否立即启动
echo 是否立即启动系统？ (Y/N)
set /p start_choice=
if /i "%start_choice%"=="Y" (
    echo.
    echo 🚀 正在启动系统...
    call "启动邮件系统.bat"
) else (
    echo.
    echo 👋 部署完成，您可以随时双击"启动邮件系统.bat"启动系统
    pause
)
