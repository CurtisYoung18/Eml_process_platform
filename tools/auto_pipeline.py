"""
全自动处理流水线模块
整合邮件上传、数据清洗、LLM处理、知识库上传的完整流程
"""

import streamlit as st
import os
import time
from pathlib import Path
from .utils import log_activity
from .email_processing import EmailCleaner
from .api_clients import GPTBotsAPI, KnowledgeBaseAPI
from config import DIRECTORIES


class AutoProcessingPipeline:
    """全自动处理流水线类"""
    
    def __init__(self, config, progress_callback=None, status_callback=None):
        """
        初始化自动处理流水线
        
        Args:
            config: 配置参数字典
            progress_callback: 进度回调函数
            status_callback: 状态回调函数
        """
        self.config = config
        self.progress_callback = progress_callback or (lambda x: None)
        self.status_callback = status_callback or (lambda x: None)
        
        # 处理状态
        self.current_step = 0
        self.total_steps = 5
        self.step_names = [
            "保存上传文件",
            "数据清洗",
            "LLM处理", 
            "知识库上传",
            "完成处理"
        ]
        
        # 处理结果
        self.results = {
            "upload_count": 0,
            "cleaned_count": 0,
            "llm_processed_count": 0,
            "kb_uploaded_count": 0,
            "errors": [],
            "success": False
        }
    
    def update_progress(self, step_progress=0):
        """更新总体进度"""
        total_progress = (self.current_step * 100 + step_progress) / self.total_steps
        self.progress_callback(min(int(total_progress), 100))
    
    def update_status(self, message):
        """更新状态信息"""
        step_name = self.step_names[self.current_step] if self.current_step < len(self.step_names) else "处理中"
        full_message = f"[{self.current_step + 1}/{self.total_steps}] {step_name}: {message}"
        self.status_callback(full_message)
        log_activity(full_message)
    
    def extract_llm_content(self, result):
        """从LLM API响应中提取内容"""
        try:
            if "output" in result:
                output_list = result.get("output", [])
                content = ""
                for output_item in output_list:
                    if "content" in output_item:
                        content_obj = output_item["content"]
                        if "text" in content_obj:
                            content += content_obj["text"] + "\n"
                return content.strip() if content else None
            
            # 备用提取方法
            return (result.get("answer") or 
                    result.get("content") or 
                    result.get("message") or
                    None)
                    
        except Exception as e:
            self.results["errors"].append(f"内容提取失败: {str(e)}")
            return None
    
    def save_uploaded_files(self, uploaded_files):
        """步骤1: 保存上传的文件"""
        self.current_step = 0
        self.update_status("开始保存上传的文件...")
        
        try:
            upload_dir = Path(DIRECTORIES["upload_dir"])
            upload_dir.mkdir(parents=True, exist_ok=True)
            
            saved_count = 0
            for i, uploaded_file in enumerate(uploaded_files):
                # 更新进度
                progress = int((i + 1) / len(uploaded_files) * 100)
                self.update_progress(progress)
                self.update_status(f"保存文件 {uploaded_file.name}...")
                
                # 保存文件
                file_path = upload_dir / uploaded_file.name
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                saved_count += 1
                time.sleep(0.1)  # 短暂延迟，让用户看到进度
            
            self.results["upload_count"] = saved_count
            self.update_status(f"成功保存 {saved_count} 个文件")
            return True
            
        except Exception as e:
            error_msg = f"保存文件失败: {str(e)}"
            self.results["errors"].append(error_msg)
            self.update_status(error_msg)
            return False
    
    def run_data_cleaning(self):
        """步骤2: 执行数据清洗"""
        self.current_step = 1
        self.update_status("开始数据清洗...")
        
        try:
            # 检查输入文件
            upload_dir = DIRECTORIES["upload_dir"]
            eml_files = list(Path(upload_dir).glob("*.eml"))
            
            if not eml_files:
                error_msg = "未找到EML文件进行清洗"
                self.results["errors"].append(error_msg)
                self.update_status(error_msg)
                return False
            
            self.update_progress(10)
            self.update_status(f"发现 {len(eml_files)} 个EML文件，开始清洗...")
            
            # 创建邮件清洗器
            cleaner = EmailCleaner(
                input_dir=upload_dir,
                output_dir=DIRECTORIES["processed_dir"]
            )
            
            self.update_progress(20)
            self.update_status("执行邮件清洗处理...")
            
            # 执行清洗
            result = cleaner.process_all_emails()
            
            if result["success"]:
                self.results["cleaned_count"] = result.get("processed_count", 0)
                self.update_progress(100)
                self.update_status(f"数据清洗完成，处理了 {self.results['cleaned_count']} 个文件")
                return True
            else:
                error_msg = f"数据清洗失败: {result.get('error', '未知错误')}"
                self.results["errors"].append(error_msg)
                self.update_status(error_msg)
                return False
                
        except Exception as e:
            error_msg = f"数据清洗异常: {str(e)}"
            self.results["errors"].append(error_msg)
            self.update_status(error_msg)
            return False
    
    def run_llm_processing(self):
        """步骤3: 执行LLM处理"""
        self.current_step = 2
        self.update_status("开始LLM处理...")
        
        try:
            # 初始化API客户端
            self.update_progress(5)
            self.update_status("初始化GPTBots API客户端...")
            
            client = GPTBotsAPI(
                self.config["llm_api_key"]
            )
            
            # 获取待处理文件
            processed_dir = Path(DIRECTORIES["processed_dir"])
            md_files = list(processed_dir.glob("*.md"))
            md_files = [f for f in md_files if f.name != "processing_report.json"]
            
            if not md_files:
                error_msg = "未找到待处理的Markdown文件"
                self.results["errors"].append(error_msg)
                self.update_status(error_msg)
                return False
            
            self.update_progress(10)
            self.update_status(f"发现 {len(md_files)} 个文件，开始LLM处理...")
            
            # LLM提示词模板
            llm_prompt_template = """
            以下是需要处理的邮件内容：

            {email_content}"""
            
            # 处理文件
            processed_count = 0
            failed_count = 0
            
            for i, md_file in enumerate(md_files):
                try:
                    # 更新进度
                    progress = int((i + 1) / len(md_files) * 90) + 10
                    self.update_progress(progress)
                    self.update_status(f"处理文件 {md_file.name}...")
                    
                    # 读取文件内容
                    with open(md_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # 调用LLM API
                    prompt = llm_prompt_template.format(email_content=content)
                    response = client.call_agent(prompt)
                    
                    if response:
                        # 提取LLM处理结果
                        processed_content = self.extract_llm_content(response)
                        
                        if processed_content:
                            # 保存处理结果
                            output_file = Path(DIRECTORIES["final_dir"]) / md_file.name
                            output_file.parent.mkdir(parents=True, exist_ok=True)
                            
                            with open(output_file, 'w', encoding='utf-8') as f:
                                f.write(processed_content)
                            
                            processed_count += 1
                        else:
                            failed_count += 1
                            self.results["errors"].append(f"LLM处理失败: {md_file.name} - 无法提取处理结果")
                    else:
                        failed_count += 1
                        self.results["errors"].append(f"LLM处理失败: {md_file.name} - API调用失败")
                    
                    # 延迟避免API限流
                    time.sleep(self.config.get("delay", 2))
                    
                except Exception as e:
                    failed_count += 1
                    error_msg = f"处理文件 {md_file.name} 时出错: {str(e)}"
                    self.results["errors"].append(error_msg)
            
            self.results["llm_processed_count"] = processed_count
            self.update_progress(100)
            
            if processed_count > 0:
                self.update_status(f"LLM处理完成，成功处理 {processed_count} 个文件")
                return True
            else:
                error_msg = "LLM处理失败，没有文件被成功处理"
                self.results["errors"].append(error_msg)
                self.update_status(error_msg)
                return False
                
        except Exception as e:
            error_msg = f"LLM处理异常: {str(e)}"
            self.results["errors"].append(error_msg)
            self.update_status(error_msg)
            return False
    
    def run_knowledge_base_upload(self):
        """步骤4: 执行知识库上传"""
        self.current_step = 3
        self.update_status("开始知识库上传...")
        
        try:
            # 初始化知识库API客户端
            self.update_progress(5)
            self.update_status("初始化知识库API客户端...")
            
            client = KnowledgeBaseAPI(
                self.config["kb_api_key"]
            )
            
            # 检查要上传的文件
            final_dir = Path(DIRECTORIES["final_dir"])
            files_to_upload = list(final_dir.glob("*.md"))
            
            if not files_to_upload:
                error_msg = "没有找到要上传的文件"
                self.results["errors"].append(error_msg)
                self.update_status(error_msg)
                return False
            
            self.update_progress(10)
            self.update_status(f"准备上传 {len(files_to_upload)} 个文件到知识库...")
            
            # 执行批量上传
            upload_result = client.upload_markdown_files_from_directory(
                directory_path=str(final_dir),
                knowledge_base_id=self.config.get("knowledge_base_id", ""),
                chunk_token=self.config.get("chunk_token"),
                splitter=self.config.get("splitter"),
                batch_size=10
            )
            
            self.update_progress(90)
            
            if upload_result:
                # 检查是否有错误
                if "error" in upload_result:
                    error_msg = f"知识库上传失败: {upload_result['error']}"
                    self.results["errors"].append(error_msg)
                    self.update_status(error_msg)
                    return False
                
                # 检查上传结果
                total_files = upload_result.get("total_files", 0)
                successful_uploads = upload_result.get("successful_uploads", 0)
                failed_uploads = upload_result.get("failed_uploads", 0)
                
                self.results["kb_uploaded_count"] = successful_uploads
                
                if successful_uploads > 0:
                    self.update_progress(100)
                    if failed_uploads > 0:
                        self.update_status(f"知识库上传部分成功，成功 {successful_uploads} 个，失败 {failed_uploads} 个")
                        # 记录失败的文件
                        failed_files = upload_result.get("failed_files", [])
                        for failed_file in failed_files:
                            self.results["errors"].append(f"文件上传失败: {failed_file.get('file_name', 'unknown')} - {failed_file.get('error', 'unknown error')}")
                    else:
                        self.update_status(f"知识库上传完成，成功上传 {successful_uploads} 个文件")
                    return True
                else:
                    error_msg = f"知识库上传失败: 没有文件上传成功 (总计 {total_files} 个文件)"
                    self.results["errors"].append(error_msg)
                    self.update_status(error_msg)
                    # 记录详细的失败信息
                    failed_files = upload_result.get("failed_files", [])
                    for failed_file in failed_files:
                        self.results["errors"].append(f"文件上传失败: {failed_file.get('file_name', 'unknown')} - {failed_file.get('error', 'unknown error')}")
                    return False
            else:
                error_msg = "知识库上传失败: API调用无响应"
                self.results["errors"].append(error_msg)
                self.update_status(error_msg)
                return False
                
        except Exception as e:
            error_msg = f"知识库上传异常: {str(e)}"
            self.results["errors"].append(error_msg)
            self.update_status(error_msg)
            return False
    
    def run_complete_pipeline(self, uploaded_files):
        """运行完整的自动处理流水线"""
        self.update_status("开始全自动处理流水线...")
        log_activity("开始全自动处理流水线")
        
        try:
            # 步骤1: 保存上传文件
            if not self.save_uploaded_files(uploaded_files):
                return self.results
            
            # 步骤2: 数据清洗
            if not self.run_data_cleaning():
                return self.results
            
            # 步骤3: LLM处理
            if not self.run_llm_processing():
                return self.results
            
            # 步骤4: 知识库上传
            if not self.run_knowledge_base_upload():
                return self.results
            
            # 步骤5: 完成处理
            self.current_step = 4
            self.update_progress(100)
            self.update_status("全自动处理流水线完成！")
            
            self.results["success"] = True
            log_activity("全自动处理流水线成功完成")
            
            return self.results
            
        except Exception as e:
            error_msg = f"自动处理流水线异常: {str(e)}"
            self.results["errors"].append(error_msg)
            self.update_status(error_msg)
            log_activity(error_msg)
            return self.results


def run_auto_processing_pipeline(uploaded_files, config):
    """
    运行全自动处理流水线的主函数
    
    Args:
        uploaded_files: 上传的文件列表
        config: 配置参数字典
    
    Returns:
        处理结果字典
    """
    # 创建单独的进度显示区域
    st.markdown("### 📊 处理进度")
    
    # 进度条单独占一行
    progress_container = st.container()
    with progress_container:
        progress_bar = st.progress(0)
    
    # 状态信息单独占一行
    status_container = st.container()
    with status_container:
        status_text = st.empty()
    
    # 结果显示区域
    result_container = st.empty()
    
    def update_progress(progress):
        with progress_container:
            progress_bar.progress(progress)
    
    def update_status(status):
        with status_container:
            status_text.text(status)
    
    # 创建并运行流水线
    pipeline = AutoProcessingPipeline(
        config=config,
        progress_callback=update_progress,
        status_callback=update_status
    )
    
    results = pipeline.run_complete_pipeline(uploaded_files)
    
    # 显示最终结果
    with result_container.container():
        st.markdown("---")
        st.markdown("### 📋 处理结果")
        
        if results["success"]:
            st.success("🎉 全自动处理完成！")
            
            # 结果统计单独一行显示
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("📤 上传文件", results["upload_count"])
            with col2:
                st.metric("🧹 清洗文件", results["cleaned_count"])
            with col3:
                st.metric("🤖 LLM处理", results["llm_processed_count"])
            with col4:
                st.metric("📚 知识库上传", results["kb_uploaded_count"])
            
            if results["errors"]:
                st.markdown("---")
                with st.expander("⚠️ 处理过程中的警告"):
                    for error in results["errors"]:
                        st.warning(error)
        else:
            st.error("❌ 全自动处理失败")
            st.markdown("**错误详情：**")
            for error in results["errors"]:
                st.error(f"• {error}")
    
    return results
