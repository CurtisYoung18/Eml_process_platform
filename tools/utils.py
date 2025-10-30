"""
工具函数模块
包含系统通用的辅助函数
"""

import os
from pathlib import Path
from datetime import datetime


def count_files(directory, pattern):
    """计算目录中匹配模式的文件数量"""
    try:
        path = Path(directory)
        if pattern == "*.eml":
            return len(list(path.glob("*.eml")))
        elif pattern == "*.md":
            return len(list(path.glob("*.md")))
        else:
            return len(list(path.glob(pattern)))
    except:
        return 0


def log_activity(message):
    """记录活动日志"""
    import os
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}\n"
    
    # 确保logs目录存在
    os.makedirs("logs", exist_ok=True)
    
    with open("logs/activity.log", "a", encoding="utf-8") as f:
        f.write(log_entry)


def get_processing_status():
    """获取各步骤的处理状态"""
    from app import CONFIG
    
    status = {}
    
    # 检查邮件上传状态
    upload_file_count = count_files(CONFIG["upload_dir"], "*.eml")
    eml_demo_files = count_files("Eml", "*.eml")
    
    if upload_file_count > 0:
        status["邮件上传"] = "completed"
    elif eml_demo_files > 0:
        status["邮件上传"] = "completed"  # 有示例文件可用
    else:
        status["邮件上传"] = "pending"
    
    # 检查数据清洗状态
    processed_files = count_files(CONFIG["processed_dir"], "*.md")
    if processed_files > 0:
        status["数据清洗"] = "completed"
    else:
        status["数据清洗"] = "pending"
    
    # 检查LLM处理状态
    final_files = count_files(CONFIG["final_dir"], "*.md")
    if final_files > 0:
        status["LLM处理"] = "completed"
    else:
        status["LLM处理"] = "pending"
    
    # 检查知识库构建状态（暂时为pending）
    status["知识库构建"] = "scheduled"
    
    return status
