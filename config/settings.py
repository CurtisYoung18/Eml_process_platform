"""
项目配置文件
集中管理应用的所有配置信息
"""

import os
from pathlib import Path

# 应用基础配置
APP_CONFIG = {
    "app_title": "邮件知识库处理系统",
    "page_icon": "📧",
    "layout": "wide",
    "initial_sidebar_state": "expanded"
}

# 目录配置
DIRECTORIES = {
    "upload_dir": "eml_process/uploads",
    "output_dir": "eml_process/output", 
    "processed_dir": "eml_process/processed",
    "final_dir": "eml_process/final_output",
    "logs_dir": "logs",
    "config_dir": "config"
}

# API配置
API_CONFIG = {
    "base_url": "http://10.52.20.41:19080",
    "default_chunk_token": 600,
    "default_batch_size": 10,
    "default_delay": 2,
    "max_retries": 3
}

# 导航配置
NAVIGATION = {
    "options": [
        "首页概览",
        "邮件上传", 
        "数据清洗",
        "LLM处理",
        "结果查看",
        "知识库管理",
        "问答系统"
    ],
    "icons": [
        "house", 
        "cloud-upload", 
        "tools", 
        "robot", 
        "bar-chart", 
        "database", 
        "chat-dots"
    ]
}

# 日志配置
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(levelname)s - %(message)s",
    "activity_log": "logs/activity.log",
    "api_log": "logs/gptbots_api.log",
    "kb_log": "logs/knowledge_base_api.log"
}

# 文件处理配置
FILE_CONFIG = {
    "supported_email_formats": ["eml"],
    "output_format": "md",
    "max_file_size": 50 * 1024 * 1024,  # 50MB
    "batch_size_limit": 3000  # 单批次最多3000个文件
}

def get_env_config():
    """获取环境变量配置"""
    return {
        # LLM邮件清洗API Keys (支持多个编号)
        "llm_api_keys": {
            "1": os.getenv("GPTBOTS_LLM_API_KEY_1", "app-YOUR_LLM_API_KEY_1"),
            "2": os.getenv("GPTBOTS_LLM_API_KEY_2", ""),
            "3": os.getenv("GPTBOTS_LLM_API_KEY_3", "")
        },
        
        # 知识库上传API Keys (支持多个编号)
        "kb_api_keys": {
            "1": os.getenv("GPTBOTS_KB_API_KEY_1", "app-YOUR_KB_API_KEY_1"),
            "2": os.getenv("GPTBOTS_KB_API_KEY_2", ""),
            "3": os.getenv("GPTBOTS_KB_API_KEY_3", "")
        },
        
        # 问答系统API Keys (支持多个编号)
        "qa_api_keys": {
            "1": os.getenv("GPTBOTS_QA_API_KEY_1", "app-YOUR_QA_API_KEY_1"),
            "2": os.getenv("GPTBOTS_QA_API_KEY_2", ""),
            "3": os.getenv("GPTBOTS_QA_API_KEY_3", "")
        },
        
        # 通用配置
        "debug": os.getenv("DEBUG", "false").lower() == "true",
        
        # 向后兼容的通用API Key
        "general_api_key": os.getenv("GPTBOTS_API_KEY", ""),
        
        # 其他配置
        "server_port": os.getenv("STREAMLIT_SERVER_PORT", "8501"),
        "log_level": os.getenv("LOG_LEVEL", "INFO"),
        "max_file_size": int(os.getenv("MAX_FILE_SIZE", "50")),
        "batch_size_limit": int(os.getenv("BATCH_SIZE_LIMIT", "3000")),
        "max_content_length": int(os.getenv("MAX_CONTENT_LENGTH", "2000"))
    }

def init_directories():
    """初始化必要的目录结构"""
    for dir_name in DIRECTORIES.values():
        Path(dir_name).mkdir(parents=True, exist_ok=True)

def get_api_key(purpose="general", key_number="1"):
    """
    获取指定用途和编号的API Key
    
    Args:
        purpose: API Key用途 ("llm", "knowledge_base", "qa", "general")
        key_number: API Key编号 ("1", "2", "3")
    
    Returns:
        对应的API Key字符串
    """
    env_config = get_env_config()
    
    # 如果设置了通用API Key，优先使用
    if env_config["general_api_key"]:
        return env_config["general_api_key"]
    
    # 根据用途和编号返回对应的API Key
    if purpose == "llm":
        return env_config["llm_api_keys"].get(key_number, env_config["llm_api_keys"]["1"])
    elif purpose in ["knowledge_base", "kb"]:
        return env_config["kb_api_keys"].get(key_number, env_config["kb_api_keys"]["1"])
    elif purpose == "qa":
        return env_config["qa_api_keys"].get(key_number, env_config["qa_api_keys"]["1"])
    else:
        # 默认返回LLM API Key编号1
        return env_config["llm_api_keys"]["1"]


def get_available_api_keys(purpose):
    """
    获取指定用途的所有可用API Keys
    
    Args:
        purpose: API Key用途 ("llm", "knowledge_base", "qa")
    
    Returns:
        dict: {编号: API Key} 的字典，只包含非空的API Key
    """
    env_config = get_env_config()
    
    if purpose == "llm":
        api_keys = env_config["llm_api_keys"]
    elif purpose in ["knowledge_base", "kb"]:
        api_keys = env_config["kb_api_keys"]
    elif purpose == "qa":
        api_keys = env_config["qa_api_keys"]
    else:
        return {}
    
    # 只返回非空的API Key
    return {k: v for k, v in api_keys.items() if v.strip()}


def get_api_key_display_name(purpose, key_number):
    """
    获取API Key的显示名称
    
    Args:
        purpose: API Key用途
        key_number: API Key编号
    
    Returns:
        显示名称字符串
    """
    purpose_names = {
        "llm": "LLM清洗",
        "knowledge_base": "知识库",
        "kb": "知识库",
        "qa": "问答系统"
    }
    
    purpose_name = purpose_names.get(purpose, purpose)
    return f"{purpose_name} API Key #{key_number}"

def get_full_config():
    """获取完整配置"""
    return {
        "app": APP_CONFIG,
        "directories": DIRECTORIES,
        "api": API_CONFIG,
        "navigation": NAVIGATION,
        "logging": LOGGING_CONFIG,
        "file": FILE_CONFIG,
        "env": get_env_config()
    }
