"""
数据清洗模块
处理邮件内容的清洗和去重功能
"""

import streamlit as st
import pandas as pd
from pathlib import Path
from .utils import count_files, log_activity


def show_cleaning_page():
    """显示数据清洗页面"""
    from app import CONFIG
    
    st.header("数据清洗")
    
    st.info("**清洗功能说明**：系统会自动检测100%被包含的邮件内容，将重复邮件合并到包含它们的完整邮件中，生成Markdown格式文件")
    
    # 检查是否有待处理的邮件
    eml_files = count_files(CONFIG["upload_dir"], "*.eml")
    
    if eml_files == 0:
        st.warning("⚠️ 未发现待处理的EML邮件文件，请先上传邮件。")
        return
    
    st.success(f"✅ 发现 {eml_files} 个EML邮件文件待处理")
    
    # 开始清洗按钮
    if st.button("🚀 开始数据清洗", type="primary"):
        start_data_cleaning(CONFIG)
    
    # 导航按钮
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("⬅️ 上一步", help="返回邮件上传页面", key="cleaning_prev_btn"):
            st.session_state.current_step = "邮件上传"
            st.rerun()
    with col3:
        if st.button("➡️ 下一步", help="前往LLM处理页面", key="cleaning_next_btn"):
            # 检查是否有处理结果
            processed_files = count_files(CONFIG["processed_dir"], "*.md")
            if processed_files > 0:
                st.session_state.current_step = "LLM处理"
                st.rerun()
            else:
                st.warning("⚠️ 请先完成数据清洗再进入下一步")


def start_data_cleaning(config):
    """开始数据清洗"""
    st.info("🚀 开始邮件清洗处理...")
    log_activity("开始数据清洗")
    
    # 创建进度条
    progress_bar = st.progress(0)
    status_text = st.empty()
    result_container = st.empty()
    
    try:
        # 检查输入目录
        eml_dir = config["upload_dir"]
        eml_files = list(Path(eml_dir).glob("*.eml"))
        
        if not eml_files:
            # 如果uploads目录没有文件，尝试从Eml目录读取示例文件
            eml_dir = "Eml"
            eml_files = list(Path(eml_dir).glob("*.eml"))
            
            if eml_files:
                status_text.info(f"📁 未在uploads目录发现文件，使用示例邮件目录: {eml_dir}")
            else:
                st.error("❌ 未找到任何EML文件进行处理")
                return
        
        progress_bar.progress(10)
        status_text.text("🔍 初始化邮件清洗器...")
        
        # 创建邮件清洗器实例
        from .email_processing import EmailCleaner
        cleaner = EmailCleaner(
            input_dir=eml_dir,
            output_dir=config["processed_dir"]
        )
        
        progress_bar.progress(20)
        status_text.text(f"📧 发现 {len(eml_files)} 个EML文件，开始解析...")
        
        # 执行清洗处理
        result = cleaner.process_all_emails()
        
        progress_bar.progress(90)
        status_text.text("📝 生成处理报告...")
        
        if result["success"]:
            progress_bar.progress(100)
            status_text.empty()
            
            # 显示处理结果
            report = result["report"]
            
            with result_container.container():
                st.success("🎉 邮件清洗完成！")
                
                # 统计信息
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("原始邮件", report["total_input_files"])
                
                with col2:
                    st.metric("解析成功", report["successfully_parsed"])
                
                with col3:
                    st.metric("去重后邮件", report["unique_emails"])
                
                with col4:
                    st.metric("压缩率", report["compression_ratio"])
                
                # 详细信息
                st.subheader("📊 处理详情")
                
                if report["duplicate_emails"] > 0:
                    st.info(f"🗑️ 发现 {report['duplicate_emails']} 封重复邮件已合并")
                    
                    with st.expander("查看重复邮件详情"):
                        duplicate_details = report["duplicate_details"]
                        st.info(f"📊 共发现 {len(duplicate_details)} 封重复邮件")
                        
                        if duplicate_details:
                            # 直接显示所有重复邮件，支持滚动
                            duplicate_data = []
                            for dup in duplicate_details:
                                duplicate_data.append({
                                    "重复文件": dup["duplicate_file"],
                                    "被包含于": dup["contained_by_file"],
                                    "重复主题": dup["duplicate_subject"][:50] + "..." if len(dup["duplicate_subject"]) > 50 else dup["duplicate_subject"]
                                })
                            
                            st.dataframe(pd.DataFrame(duplicate_data), width='stretch', height=400)
                            st.caption(f"共 {len(duplicate_details)} 封重复邮件，可滚动查看全部")
                        else:
                            st.info("没有发现重复邮件")
                
                # 生成的文件列表
                st.subheader("📁 生成的Markdown文件")
                
                generated_files = report["generated_markdown_files"]
                st.info(f"📊 共生成 {len(generated_files)} 个Markdown文件")
                
                if generated_files:
                    # 显示文件网格
                    num_cols = 3
                    for i in range(0, len(generated_files), num_cols):
                        cols = st.columns(num_cols)
                        for j, filename in enumerate(generated_files[i:i+num_cols]):
                            with cols[j]:
                                st.code(filename)
                
                # 路径信息
                st.subheader("📂 文件位置")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.success("📁 Markdown文件保存至:")
                    st.code(config["processed_dir"])
                
                with col2:
                    st.success("📋 处理报告保存至:")
                    st.code(f"{config['processed_dir']}/processing_report.json")
                
                # 记录成功日志
                log_activity(f"邮件清洗完成: {report['total_input_files']} -> {report['unique_emails']} 封")
        
        else:
            progress_bar.progress(0)
            status_text.empty()
            result_container.error(f"❌ 处理失败: {result.get('message', '未知错误')}")
            log_activity(f"邮件清洗失败: {result.get('message', '未知错误')}")
    
    except Exception as e:
        progress_bar.progress(0)
        status_text.empty()
        result_container.error(f"❌ 处理过程中发生错误: {str(e)}")
        log_activity(f"邮件清洗错误: {str(e)}")
        st.exception(e)
