"""
配置模块
包含项目的所有配置信息
"""

from .settings import (
    APP_CONFIG,
    DIRECTORIES,
    API_CONFIG,
    NAVIGATION,
    LOGGING_CONFIG,
    FILE_CONFIG,
    get_env_config,
    get_api_key,
    get_available_api_keys,
    get_api_key_display_name,
    init_directories,
    get_full_config
)

# 为了向后兼容，保持原有的CONFIG格式
CONFIG = DIRECTORIES

__all__ = [
    'APP_CONFIG',
    'DIRECTORIES', 
    'API_CONFIG',
    'NAVIGATION',
    'LOGGING_CONFIG',
    'FILE_CONFIG',
    'CONFIG',  # 向后兼容
    'get_env_config',
    'get_api_key',
    'get_available_api_keys',
    'get_api_key_display_name',
    'init_directories',
    'get_full_config'
]
