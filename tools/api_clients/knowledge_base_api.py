#!/usr/bin/env python3
"""
GPTBots 知识库API 集成工具
用于调用GPTBots知识库相关API
"""

import requests
import json
import time
import logging
import base64
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

# 配置日志
import os
os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/knowledge_base_api.log'),
        logging.StreamHandler()
    ]
)

class KnowledgeBaseAPI:
    def __init__(self, api_key: str, base_url: str = None):
        """
        初始化GPTBots知识库API客户端
        
        Args:
            api_key: API密钥
            base_url: API基础URL（可选，默认从环境变量读取）
        """
        self.api_key = api_key
        self.logger = logging.getLogger(__name__)
        
        # 从环境变量读取API URL，如果没有则使用默认值
        if base_url:
            self.base_url = base_url
        else:
            # 尝试从环境变量读取
            import os
            self.base_url = os.getenv("KNOWLEDGE_BASE_API_URL", "https://api-sg.gptbots.ai")
            logging.info(f"知识库API URL: {self.base_url}")
        
        # API端点URLs
        self.knowledge_base_list_url = f"{self.base_url}/v1/bot/knowledge/base/page"
        self.doc_list_url = f"{self.base_url}/v1/bot/doc/query/page"
        self.add_text_doc_url = f"{self.base_url}/v1/bot/doc/text/add"
        self.add_spreadsheet_doc_url = f"{self.base_url}/v1/bot/doc/spreadsheet/add"
        self.update_text_doc_url = f"{self.base_url}/v1/bot/doc/text/update"
        self.update_spreadsheet_doc_url = f"{self.base_url}/v1/bot/doc/spreadsheet/update"
        self.delete_doc_url = f"{self.base_url}/v1/bot/doc/batch/delete"
        self.add_chunks_url = f"{self.base_url}/v1/bot/doc/chunks/add"
        self.doc_status_url = f"{self.base_url}/v1/bot/data/detail/list"
        self.vector_match_url = f"{self.base_url}/v1/vector/match"
        self.retry_embedding_url = f"{self.base_url}/v1/bot/data/retry/batch"
        
        self.session = requests.Session()
        self.timeout = None  # 无超时限制
        
    def _get_headers(self) -> Dict[str, str]:
        """获取标准请求头"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def _make_request(self, method: str, url: str, **kwargs) -> Optional[Dict]:
        """
        统一的HTTP请求处理
        
        Args:
            method: HTTP方法
            url: 请求URL
            **kwargs: 其他请求参数
            
        Returns:
            响应数据或None
        """
        try:
            # 如果没有指定timeout，使用默认值
            if 'timeout' not in kwargs:
                kwargs['timeout'] = self.timeout
            
            response = self.session.request(method, url, **kwargs)
            
            if response.status_code == 200:
                return response.json()
            else:
                logging.error(f"API请求失败 - 状态码: {response.status_code}, 响应: {response.text}")
                return {"error": f"HTTP {response.status_code}", "message": response.text}
                
        except Exception as e:
            logging.error(f"API请求异常: {str(e)}")
            return {"error": "Exception", "message": str(e)}
    
    def get_knowledge_bases(self) -> Optional[Dict]:
        """
        获取知识库列表
        
        Returns:
            知识库列表或None
        """
        logging.info("正在获取知识库列表...")
        
        return self._make_request(
            "GET",
            self.knowledge_base_list_url,
            headers=self._get_headers()
        )
    
    def list_knowledge_bases(self) -> Optional[List[Dict]]:
        """
        获取格式化的知识库列表，用于前端显示
        
        Returns:
            格式化的知识库列表 [{'id': '', 'name': ''}] 或 None
        """
        try:
            result = self.get_knowledge_bases()
            
            logging.info(f"知识库API响应: {result}")
            
            if not result:
                logging.error("知识库API返回空结果")
                return None
                
            if 'error' in result:
                logging.error(f"知识库API返回错误: {result.get('error')}, {result.get('message')}")
                return None
            
            # 尝试多种数据结构格式
            data_list = None
            
            # 格式1: {'knowledge_base': [...]} (实际API返回格式)
            if 'knowledge_base' in result and isinstance(result['knowledge_base'], list):
                data_list = result['knowledge_base']
            # 格式2: {'data': [...]}
            elif 'data' in result and isinstance(result['data'], list):
                data_list = result['data']
            # 格式3: {'data': {'list': [...]}}
            elif 'data' in result and isinstance(result['data'], dict) and 'list' in result['data']:
                data_list = result['data']['list']
            # 格式4: 直接是列表
            elif isinstance(result, list):
                data_list = result
            
            if data_list:
                knowledge_bases = []
                for kb in data_list:
                    knowledge_bases.append({
                        'id': kb.get('id', ''),
                        'name': kb.get('name', '未命名知识库'),
                        'doc_count': kb.get('doc', kb.get('doc_count', 0)),  # 'doc' 是实际字段名
                        'created_at': kb.get('created_at', ''),
                        'desc': kb.get('desc', '')
                    })
                logging.info(f"成功解析 {len(knowledge_bases)} 个知识库")
                return knowledge_bases
            
            logging.error(f"无法从响应中提取知识库列表，响应结构: {list(result.keys()) if isinstance(result, dict) else type(result)}")
            return None
            
        except Exception as e:
            logging.error(f"list_knowledge_bases异常: {str(e)}")
            return None
    
    def get_documents(self, knowledge_base_id: str, page: int = 1, page_size: int = 10) -> Optional[Dict]:
        """
        获取知识库文档列表
        
        Args:
            knowledge_base_id: 知识库ID
            page: 页码
            page_size: 每页数量
            
        Returns:
            文档列表或None
        """
        logging.info(f"正在获取知识库 {knowledge_base_id} 的文档列表...")
        
        params = {
            "knowledge_base_id": knowledge_base_id,
            "page": page,
            "page_size": page_size
        }
        
        return self._make_request(
            "GET",
            self.doc_list_url,
            headers=self._get_headers(),
            params=params
        )
    
    def add_text_documents(self, files: List[Dict], knowledge_base_id: str = None, 
                          chunk_token: int = None, chunk_separator: str = None, 
                          splitter: str = None) -> Optional[Dict]:
        """
        添加文本类文档
        
        Args:
            files: 文档文件列表
            knowledge_base_id: 目标知识库ID（可选）
            chunk_token: 分块Token数（与chunk_separator二选一）
            chunk_separator: 自定义分隔符（与chunk_token二选一）
            splitter: 分隔符类型（可选）
            
        Returns:
            上传结果或None
        """
        logging.info(f"正在添加 {len(files)} 个文本文档...")
        
        payload = {
            "files": files
        }
        
        # 可选参数
        if knowledge_base_id:
            payload["knowledge_base_id"] = knowledge_base_id
        
        # 分块参数
        if splitter:
            payload["splitter"] = splitter
        
        # 分块大小或分隔符（二选一）
        if chunk_token:
            payload["chunk_token"] = chunk_token
        elif chunk_separator:
            payload["chunk_separator"] = chunk_separator
        else:
            payload["chunk_token"] = 600  # 默认值
        
        return self._make_request(
            "POST",
            self.add_text_doc_url,
            headers=self._get_headers(),
            json=payload
        )
    
    def add_spreadsheet_documents(self, files: List[Dict], knowledge_base_id: str = None,
                                 chunk_token: int = 600, header_row: int = 1) -> Optional[Dict]:
        """
        添加表格类文档
        
        Args:
            files: 文档文件列表
            knowledge_base_id: 目标知识库ID（可选）
            chunk_token: 分块Token数（默认600）
            header_row: 表头行数（默认1）
            
        Returns:
            上传结果或None
        """
        logging.info(f"正在添加 {len(files)} 个表格文档...")
        
        payload = {
            "files": files,
            "chunk_token": chunk_token,
            "header_row": header_row
        }
        
        if knowledge_base_id:
            payload["knowledge_base_id"] = knowledge_base_id
        
        return self._make_request(
            "POST",
            self.add_spreadsheet_doc_url,
            headers=self._get_headers(),
            json=payload
        )
    
    def update_text_documents(self, files: List[Dict], chunk_token: int = 600, 
                             splitter: str = None) -> Optional[Dict]:
        """
        更新文本类文档
        
        Args:
            files: 文档文件列表（需包含doc_id）
            chunk_token: 分块Token数（默认600）
            splitter: 分隔符（可选）
            
        Returns:
            更新结果或None
        """
        logging.info(f"正在更新 {len(files)} 个文本文档...")
        
        payload = {
            "files": files
        }
        
        # 分块参数（二选一）
        if splitter:
            payload["splitter"] = splitter
        else:
            payload["chunk_token"] = chunk_token
        
        return self._make_request(
            "PUT",
            self.update_text_doc_url,
            headers=self._get_headers(),
            json=payload
        )
    
    def delete_documents(self, doc_ids: List[str]) -> Optional[Dict]:
        """
        删除知识文档
        
        Args:
            doc_ids: 要删除的文档ID列表
            
        Returns:
            删除结果或None
        """
        logging.info(f"正在删除 {len(doc_ids)} 个文档...")
        
        params = {
            "doc": ",".join(doc_ids)
        }
        
        return self._make_request(
            "DELETE",
            self.delete_doc_url,
            headers=self._get_headers(),
            params=params
        )
    
    def add_document_chunks(self, doc_id: str, chunks: List[Dict]) -> Optional[Dict]:
        """
        为文档添加知识块
        
        Args:
            doc_id: 文档ID
            chunks: 知识块列表
            
        Returns:
            添加结果或None
        """
        logging.info(f"正在为文档 {doc_id} 添加 {len(chunks)} 个知识块...")
        
        payload = {
            "doc_id": doc_id,
            "chunks": chunks
        }
        
        return self._make_request(
            "POST",
            self.add_chunks_url,
            headers=self._get_headers(),
            json=payload
        )
    
    def get_document_status(self, data_ids: List[str]) -> Optional[Dict]:
        """
        查询文档状态
        
        Args:
            data_ids: 文档ID列表
            
        Returns:
            文档状态或None
        """
        logging.info(f"正在查询 {len(data_ids)} 个文档的状态...")
        
        params = {}
        for i, data_id in enumerate(data_ids):
            params[f"data_ids"] = data_id if i == 0 else params["data_ids"] + f"&data_ids={data_id}"
        
        return self._make_request(
            "GET",
            self.doc_status_url,
            headers=self._get_headers(),
            params=params
        )
    
    def vector_similarity_search(self, prompt: str, embedding_rate: float = 1.0,
                                group_ids: List[str] = None, data_ids: List[str] = None,
                                top_k: int = 10, rerank_version: str = None,
                                doc_correlation: float = None) -> Optional[Dict]:
        """
        向量相似度匹配
        
        Args:
            prompt: 查询关键词
            embedding_rate: 关键词和语义检索权重占比
            group_ids: 知识库ID列表
            data_ids: 文档ID列表
            top_k: 返回相似度最高的K个值
            rerank_version: 知识重排模型名称
            doc_correlation: 知识相关性得分
            
        Returns:
            匹配结果或None
        """
        logging.info(f"正在进行向量相似度匹配: {prompt[:50]}...")
        
        payload = {
            "prompt": prompt,
            "embedding_rate": embedding_rate,
            "top_k": top_k
        }
        
        if group_ids is not None:
            payload["group_ids"] = group_ids
        if data_ids is not None:
            payload["data_ids"] = data_ids
        if rerank_version:
            payload["rerank_version"] = rerank_version
        if doc_correlation is not None:
            payload["doc_correlation"] = doc_correlation
        
        return self._make_request(
            "POST",
            self.vector_match_url,
            headers=self._get_headers(),
            json=payload
        )
    
    def retry_failed_embeddings(self) -> Optional[Dict]:
        """
        重新嵌入失败的文档
        
        Returns:
            重新嵌入结果或None
        """
        logging.info("正在重新嵌入失败的文档...")
        
        return self._make_request(
            "POST",
            self.retry_embedding_url,
            headers=self._get_headers(),
            json={}
        )
    
    def upload_markdown_files_from_directory(self, directory_path: str, 
                                           knowledge_base_id: str = None,
                                           chunk_token: int = None,
                                           chunk_separator: str = None,
                                           splitter: str = None,
                                           batch_size: int = 20) -> Dict:
        """
        批量上传目录中的Markdown文件到知识库
        
        Args:
            directory_path: 包含Markdown文件的目录路径
            knowledge_base_id: 目标知识库ID
            chunk_token: 分块Token数（与chunk_separator二选一）
            chunk_separator: 自定义分隔符（与chunk_token二选一）
            splitter: 分隔符类型
            batch_size: 批处理大小（最多20个）
            
        Returns:
            上传结果统计
        """
        directory = Path(directory_path)
        if not directory.exists() or not directory.is_dir():
            return {"error": "目录不存在或不是有效目录"}
        
        md_files = list(directory.glob("*.md"))
        if not md_files:
            return {"error": "目录中没有找到Markdown文件"}
        
        logging.info(f"发现 {len(md_files)} 个Markdown文件待上传")
        
        # 结果统计
        results = {
            "total_files": len(md_files),
            "successful_uploads": 0,
            "failed_uploads": 0,
            "uploaded_files": [],
            "failed_files": [],
            "batches_processed": 0
        }
        
        # 分批处理文件
        total_batches = (len(md_files) + batch_size - 1) // batch_size
        logging.info(f"总共 {len(md_files)} 个文件，将分 {total_batches} 批处理，每批最多 {batch_size} 个")
        
        for i in range(0, len(md_files), batch_size):
            batch_files = md_files[i:i + batch_size]
            batch_num = i // batch_size + 1
            
            logging.info(f"处理批次 {batch_num}/{total_batches}: {len(batch_files)} 个文件")
            
            # 准备文件数据
            files_data = []
            for md_file in batch_files:
                try:
                    # 读取文件内容
                    with open(md_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # 编码为base64
                    content_base64 = base64.b64encode(content.encode('utf-8')).decode('utf-8')
                    
                    file_data = {
                        "file_name": md_file.name,
                        "file_base64": content_base64,
                        "source_url": f"local://{md_file.name}"
                    }
                    files_data.append(file_data)
                    
                except Exception as e:
                    logging.error(f"读取文件 {md_file.name} 失败: {str(e)}")
                    results["failed_files"].append({
                        "file_name": md_file.name,
                        "error": f"读取文件失败: {str(e)}"
                    })
                    results["failed_uploads"] += 1
            
            if not files_data:
                continue
            
            # 调用API上传
            try:
                # 构建上传参数
                upload_params = {
                    'files': files_data,
                    'knowledge_base_id': knowledge_base_id,
                    'splitter': splitter
                }
                
                # 根据分块模式选择参数
                if chunk_token:
                    upload_params['chunk_token'] = chunk_token
                elif chunk_separator:
                    upload_params['chunk_separator'] = chunk_separator
                else:
                    upload_params['chunk_token'] = 600  # 默认值
                
                upload_result = self.add_text_documents(**upload_params)
                
                if upload_result and "doc" in upload_result:
                    # 上传成功
                    successful_docs = upload_result.get("doc", [])
                    failed_docs = upload_result.get("failed", [])
                    
                    results["successful_uploads"] += len(successful_docs)
                    results["failed_uploads"] += len(failed_docs)
                    
                    for doc in successful_docs:
                        results["uploaded_files"].append(doc)
                    
                    for failed_file in failed_docs:
                        results["failed_files"].append({
                            "file_name": failed_file,
                            "error": "API上传失败"
                        })
                    
                    logging.info(f"批次 {batch_num} 完成: 成功 {len(successful_docs)}, 失败 {len(failed_docs)}")
                    
                else:
                    # API调用失败
                    error_msg = upload_result.get("message", "未知错误") if upload_result else "API调用失败"
                    logging.error(f"批次 {batch_num} API调用失败: {error_msg}")
                    
                    for file_data in files_data:
                        results["failed_files"].append({
                            "file_name": file_data["file_name"],
                            "error": f"API调用失败: {error_msg}"
                        })
                    results["failed_uploads"] += len(files_data)
                
            except Exception as e:
                logging.error(f"批次 {batch_num} 处理异常: {str(e)}")
                for file_data in files_data:
                    results["failed_files"].append({
                        "file_name": file_data["file_name"],
                        "error": f"处理异常: {str(e)}"
                    })
                results["failed_uploads"] += len(files_data)
            
            results["batches_processed"] += 1
            
            # 批次间延迟，避免API限流
            if i + batch_size < len(md_files):
                time.sleep(1)
        
        logging.info(f"批量上传完成: 总计 {results['total_files']} 个文件, "
                    f"成功 {results['successful_uploads']} 个, 失败 {results['failed_uploads']} 个")
        
        return results


    def upload_markdown_content(self, content: str, filename: str = "document.md",
                               knowledge_base_id: str = None,
                               chunk_token: int = 600,
                               splitter: str = None) -> Dict:
        """
        上传单个Markdown内容到知识库
        
        Args:
            content: Markdown文件内容
            filename: 文件名
            knowledge_base_id: 目标知识库ID
            chunk_token: 分块大小（Token数）
            splitter: 分隔符
            
        Returns:
            dict: 上传结果
        """
        try:
            # 编码内容为base64
            content_base64 = base64.b64encode(content.encode('utf-8')).decode('utf-8')
            
            # 准备文件数据（与批量上传格式一致）
            file_data = {
                "file_name": filename,
                "file_base64": content_base64,
                "source_url": f"local://{filename}"
            }
            
            # 准备上传数据
            upload_data = {
                "files": [file_data]  # 包装成文件列表
            }
            
            # 可选参数
            if knowledge_base_id:
                upload_data["knowledge_base_id"] = knowledge_base_id
                self.logger.info(f"上传到知识库: {knowledge_base_id}")
            else:
                self.logger.warning(f"警告: 未指定知识库ID，将使用默认知识库")
            
            # 分块参数（二选一）
            if splitter:
                upload_data["splitter"] = splitter
            else:
                upload_data["chunk_token"] = chunk_token
            
            self.logger.info(f"上传请求数据: KB_ID={knowledge_base_id}, filename={filename}, chunk_token={chunk_token}")
            
            # 发送上传请求
            response = requests.post(
                self.add_text_doc_url,
                headers=self._get_headers(),
                json=upload_data,
                timeout=None  # 无超时限制
            )
            
            self.logger.info(f"上传响应状态: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                self.logger.info(f"上传响应内容: {result}")
                self.logger.info(f"单文件上传成功: {filename}")
                return {
                    "success": True,
                    "filename": filename,
                    "chunks_count": result.get("data", {}).get("chunks_count", 0),
                    "message": "上传成功"
                }
            else:
                error_msg = f"上传失败: HTTP {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg = error_data.get("message", error_msg)
                except:
                    pass
                    
                self.logger.error(f"单文件上传失败: {filename} - {error_msg}")
                return {
                    "error": error_msg,
                    "filename": filename,
                    "status_code": response.status_code
                }
                
        except requests.exceptions.Timeout:
            error_msg = "上传超时"
            self.logger.error(f"单文件上传超时: {filename}")
            return {"error": error_msg, "filename": filename}
            
        except Exception as e:
            error_msg = f"上传异常: {str(e)}"
            self.logger.error(f"单文件上传异常: {filename} - {error_msg}")
            return {"error": error_msg, "filename": filename}


def main():
    """使用示例"""
    # 设置API密钥
    api_key = "app-YOUR_API_KEY_HERE"  # 请替换为您的API密钥
    
    # 初始化知识库API客户端
    client = KnowledgeBaseAPI(api_key)
    
    # 测试获取知识库列表
    knowledge_bases = client.get_knowledge_bases()
    if knowledge_bases:
        print("知识库列表:")
        print(json.dumps(knowledge_bases, indent=2, ensure_ascii=False))
    else:
        print("获取知识库列表失败")

if __name__ == "__main__":
    main()
