#!/usr/bin/env python3
"""
GPTBots API 集成工具
用于调用GPTBots API
"""

import requests
import json
import time
import logging
from typing import Dict, Optional
from datetime import datetime

# 配置日志
import os
os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/gptbots_api.log'),
        logging.StreamHandler()
    ]
)

class GPTBotsAPI:
    def __init__(self, app_key: str, conversation_api_url: str = None):
        """
        初始化GPTBots API客户端
        
        Args:
            app_key: API应用密钥
            conversation_api_url: 对话API URL（可选，默认从环境变量读取）
        """
        self.app_key = app_key
        
        # 从环境变量读取API URL，如果没有则使用默认值
        if conversation_api_url:
            self.send_message_url = conversation_api_url
        else:
            self.send_message_url = os.getenv("GPTBOTS_CONVERSATION_API_URL", "https://api-sg.gptbots.ai/v2/conversation/message")
            logging.info(f"对话API URL: {self.send_message_url}")
        
        # 从send_message_url推断base_url
        # 例如: https://api-sg.gptbots.ai/v2/conversation/message -> https://api-sg.gptbots.ai
        if self.send_message_url.startswith('http'):
            parts = self.send_message_url.split('/')
            self.base_url = f"{parts[0]}//{parts[2]}"
        else:
            self.base_url = "https://api-sg.gptbots.ai"
        
        self.create_conversation_url = f"{self.base_url}/v1/conversation"
        self.session = requests.Session()
        self.timeout = None  # 无超时限制
        
    def create_conversation(self, user_id: str = "api-user", timeout: int = None) -> Optional[str]:
        """
        创建对话ID
        
        Args:
            user_id: 用户标识
            timeout: 超时时间（秒），None表示无超时
        
        Returns:
            conversation_id或None（如果失败）
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.app_key}"
        }
        
        payload = {
            "user_id": user_id
        }
        
        try:
            response = self.session.post(
                self.create_conversation_url,
                headers=headers,
                json=payload,
                timeout=timeout or self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                conversation_id = result.get("conversation_id")
                logging.info(f"成功创建对话ID: {conversation_id}")
                return conversation_id
            else:
                logging.error(f"创建对话ID失败 - 状态码: {response.status_code}, 响应: {response.text}")
                return None
                
        except Exception as e:
            logging.error(f"创建对话ID出错: {str(e)}")
            return None

    def send_message(self, conversation_id: str, query: str, timeout: int = None, max_retries: int = 3) -> Optional[Dict]:
        """
        发送消息到指定对话（带重试机制）
        
        Args:
            conversation_id: 对话ID
            query: 查询内容
            timeout: 超时时间（秒），None表示无超时
            max_retries: 最大重试次数
        
        Returns:
            API响应内容或None（如果失败）
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.app_key}"
        }
        
        # 按照官方文档格式构建payload
        payload = {
            "conversation_id": conversation_id,
            "response_mode": "blocking",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": query
                        }
                    ]
                }
            ]
        }
        
        import random
        
        for attempt in range(max_retries):
            try:
                response = self.session.post(
                    self.send_message_url,
                    headers=headers,
                    json=payload,
                    timeout=timeout or self.timeout
                )
                
                if response.status_code == 200:
                    result = response.json()
                    logging.info(f"消息发送成功 (尝试 {attempt + 1}/{max_retries})")
                    return result
                elif response.status_code == 429:  # Rate limit
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    logging.warning(f"触发限流，等待 {wait_time:.2f} 秒后重试...")
                    time.sleep(wait_time)
                    continue
                else:
                    logging.error(f"发送消息失败 - 状态码: {response.status_code}, 响应: {response.text}")
                    if attempt == max_retries - 1:
                        return None
                    
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                logging.warning(f"网络错误 (尝试 {attempt + 1}/{max_retries}): {str(e)}, 等待 {wait_time:.2f} 秒后重试...")
                if attempt < max_retries - 1:
                    time.sleep(wait_time)
                else:
                    logging.error(f"网络请求最终失败: {str(e)}")
                    return None
                    
            except Exception as e:
                logging.error(f"发送消息出错 (尝试 {attempt + 1}/{max_retries}): {str(e)}")
                if attempt == max_retries - 1:
                    return None
                    
        return None

    def call_agent(self, query: str, timeout: int = None) -> Optional[Dict]:
        """
        调用GPTBots Agent（完整流程：创建对话->发送消息）
        
        Args:
            query: 查询内容
            timeout: 超时时间（秒），None表示无超时
        
        Returns:
            API响应内容或None（如果失败）
        """
        logging.info(f"正在查询: {query}")
        
        # 步骤1: 创建对话ID
        conversation_id = self.create_conversation()
        if not conversation_id:
            logging.error("无法创建对话ID")
            return None
        
        # 步骤2: 发送消息
        result = self.send_message(conversation_id, query, timeout)
        if result:
            logging.info(f"查询成功: {query[:50]}...")
        else:
            logging.error(f"查询失败: {query}")
        
        return result

def main():
    """使用示例"""
    # 设置API密钥
    api_key = "app-YOUR_API_KEY_HERE"  # 请替换为您的API密钥
    
    # 初始化API客户端
    client = GPTBotsAPI(api_key)
    
    # 测试API调用
    test_query = "你好，请介绍一下GPTBots的功能"
    result = client.call_agent(test_query)
    
    if result:
        print("API调用成功！")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("API调用失败")

if __name__ == "__main__":
    main()
