"""
Tools模块 - 功能模块化
包含邮件知识库处理系统的各个功能模块
"""

# 页面功能模块
from .homepage import show_homepage
from .email_upload import show_upload_page
from .data_cleaning import show_cleaning_page
from .llm_processing import show_llm_processing_page
from .results_view import show_results_page
from .knowledge_base import show_knowledge_base_page
from .qa_system import show_qa_system_page
from .future_features import show_future_features_page

# 工具函数
from .utils import *

# 邮件处理模块
from .email_processing import EmailCleaner

# API客户端模块
from .api_clients import GPTBotsAPI, KnowledgeBaseAPI

# 自动处理流水线模块
from .auto_pipeline import AutoProcessingPipeline, run_auto_processing_pipeline

__all__ = [
    # 页面功能
    'show_homepage',
    'show_upload_page', 
    'show_cleaning_page',
    'show_llm_processing_page',
    'show_results_page',
    'show_knowledge_base_page',
    'show_qa_system_page',
    'show_future_features_page',
    
    # 工具函数
    'count_files',
    'log_activity',
    'get_processing_status',
    
    # 邮件处理
    'EmailCleaner',
    
    # API客户端
    'GPTBotsAPI',
    'KnowledgeBaseAPI',
    
    # 自动处理流水线
    'AutoProcessingPipeline',
    'run_auto_processing_pipeline'
]
