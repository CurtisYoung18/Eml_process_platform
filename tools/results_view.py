"""
结果查看模块
展示各个处理阶段的结果和统计信息
"""

import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime
from .utils import count_files


def show_results_page():
    """显示结果查看页面"""
    from app import CONFIG
    
    st.header("处理结果")
    
    # 结果统计
    col1, col2, col3 = st.columns(3)
    
    with col1:
        original_count = count_files(CONFIG["upload_dir"], "*.eml")
        st.metric("原始邮件", original_count)
    
    with col2:
        cleaned_count = count_files(CONFIG["processed_dir"], "*.md")
        st.metric("清洗后邮件", cleaned_count)
    
    with col3:
        final_count = count_files(CONFIG["final_dir"], "*.md")
        st.metric("最终处理完成", final_count)
    
    # 文件浏览器
    st.subheader("📁 文件浏览器")
    
    view_option = st.radio(
        "选择查看内容",
        ["🔧 清洗结果", "🤖 LLM处理结果", "📄 所有文件"],
        horizontal=True
    )
    
    if view_option == "🔧 清洗结果":
        show_file_browser(CONFIG["processed_dir"], "*.md")
    elif view_option == "🤖 LLM处理结果":
        show_file_browser(CONFIG["final_dir"], "*.md")
    else:
        show_all_files(CONFIG)
    
    # 导航按钮
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("⬅️ 上一步", help="返回LLM处理页面", key="results_prev_btn"):
            st.session_state.current_step = "LLM处理"
            st.rerun()
    with col3:
        if st.button("➡️ 下一步", help="前往知识库管理", key="results_next_btn"):
            st.session_state.current_step = "知识库管理"
            st.rerun()


def show_file_browser(directory, pattern):
    """显示文件浏览器"""
    path = Path(directory)
    if not path.exists():
        st.warning(f"📂 目录 {directory} 不存在")
        return
    
    files = list(path.glob(pattern))
    if not files:
        st.info(f"📂 {directory} 目录中暂无 {pattern} 文件")
        return
    
    # 文件选择器
    selected_file = st.radio(
        "选择要查看的文件",
        options=[f.name for f in files]
    )
    
    if selected_file:
        file_path = path / selected_file
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            st.subheader(f"📄 {selected_file}")
            st.markdown(content)
            
            # 下载按钮
            st.download_button(
                label="💾 下载文件",
                data=content,
                file_name=selected_file,
                mime="text/markdown"
            )
        except Exception as e:
            st.error(f"❌ 读取文件失败: {str(e)}")


def show_all_files(config):
    """显示所有文件概览"""
    st.subheader("📁 全部文件概览")
    
    all_files = []
    
    # 收集所有目录的文件
    directories = [
        (config["upload_dir"], "原始邮件", "*.eml"),
        (config["processed_dir"], "清洗结果", "*.md"),
        (config["final_dir"], "最终结果", "*.md")
    ]
    
    for dir_path, dir_name, pattern in directories:
        path = Path(dir_path)
        if path.exists():
            files = list(path.glob(pattern))
            for file in files:
                stat = file.stat()
                all_files.append({
                    "目录": dir_name,
                    "文件名": file.name,
                    "大小": f"{stat.st_size / 1024:.1f} KB",
                    "修改时间": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                    "路径": str(file)
                })
    
    if all_files:
        df = pd.DataFrame(all_files)
        st.dataframe(df, width='stretch')
    else:
        st.info("📂 暂无文件")
