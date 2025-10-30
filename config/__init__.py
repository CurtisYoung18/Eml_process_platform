"""
Config模块 - 用于API服务器的配置
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

# 目录配置
DIRECTORIES = {
    "upload_dir": PROJECT_ROOT / "eml_process" / "uploads",
    "processed_dir": PROJECT_ROOT / "eml_process" / "processed",
    "final_output_dir": PROJECT_ROOT / "eml_process" / "final_output",
    "log_dir": PROJECT_ROOT / "logs",
}

# API配置
API_CONFIG = {
    "gptbots_endpoint": os.getenv("GPTBOTS_ENDPOINT", "sg"),
    "conversation_api_url": os.getenv("GPTBOTS_CONVERSATION_API_URL", "https://api-sg.gptbots.ai/v2/conversation/message"),
    "knowledge_base_api_url": os.getenv("KNOWLEDGE_BASE_API_URL", "https://api-sg.gptbots.ai"),
}

def init_directories():
    """初始化所有必要的目录"""
    for dir_path in DIRECTORIES.values():
        dir_path.mkdir(parents=True, exist_ok=True)

def get_api_url(api_type: str) -> str:
    """
    获取API URL
    
    Args:
        api_type: API类型 ('conversation' 或 'knowledge_base')
    
    Returns:
        API URL
    """
    if api_type == 'conversation':
        return API_CONFIG['conversation_api_url']
    elif api_type == 'knowledge_base':
        return API_CONFIG['knowledge_base_api_url']
    else:
        raise ValueError(f"未知的API类型: {api_type}")
