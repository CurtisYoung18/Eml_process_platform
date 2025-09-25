#!/usr/bin/env python3
"""
邮件知识库管理系统启动脚本
"""

import subprocess
import sys
import os
from pathlib import Path

def check_dependencies():
    """检查并安装依赖"""
    print("🔍 检查依赖包...")
    
    try:
        import streamlit
        print("✅ Streamlit 已安装")
    except ImportError:
        print("⚠️ Streamlit 未安装，正在安装...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "streamlit>=1.28.0"])
    
    try:
        import requests
        print("✅ Requests 已安装")
    except ImportError:
        print("⚠️ Requests 未安装，正在安装...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "requests>=2.28.0"])

def create_directories():
    """创建必要的目录"""
    directories = [
        "eml_process/uploads", 
        "eml_process/output", 
        "eml_process/processed", 
        "eml_process/final_output"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"📁 目录已创建: {directory}/")

def main():
    """主函数"""
    print("🚀 启动邮件知识库管理系统...")
    print("=" * 50)
    
    # 检查依赖
    check_dependencies()
    
    # 创建目录
    create_directories()
    
    print("\n✅ 系统准备完成！")
    print("🌐 正在启动 Streamlit 应用...")
    print("=" * 50)
    
    # 启动Streamlit应用
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "app.py",
            "--server.port", "8501",
            "--server.address", "localhost",
            "--browser.gatherUsageStats", "false"
        ])
    except KeyboardInterrupt:
        print("\n👋 应用已停止")
    except Exception as e:
        print(f"\n❌ 启动失败: {str(e)}")
        print("\n🔧 手动启动命令:")
        print("streamlit run app.py")

if __name__ == "__main__":
    main()
