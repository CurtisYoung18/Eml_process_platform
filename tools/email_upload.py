"""
邮件上传模块
处理EML邮件文件的上传功能
"""

import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime
from .utils import count_files, log_activity


def show_upload_page():
    """显示邮件上传页面"""
    from app import CONFIG
    
    st.header("邮件上传")
    
    upload_method = st.radio(
        "选择上传方式",
        ["📁 本地路径文件扫描", "📄 浏览本地文件上传"]
    )
    
    if upload_method == "📄 浏览本地文件上传":
        uploaded_files = st.file_uploader(
            "选择EML邮件文件",
            type=['eml'],
            accept_multiple_files=True,
            help="支持选择多个EML格式的邮件文件"
        )
        
        if uploaded_files:
            st.success(f"已选择 {len(uploaded_files)} 个文件")
            
            # 检查重复文件
            upload_path = Path(CONFIG["upload_dir"])
            existing_files = {f.name for f in upload_path.glob("*.eml")} if upload_path.exists() else set()
            
            # 显示文件列表和重复检查结果
            file_data = []
            duplicate_files = []
            
            for file in uploaded_files:
                is_duplicate = file.name in existing_files
                if is_duplicate:
                    duplicate_files.append(file.name)
                
                file_data.append({
                    "文件名": file.name,
                    "大小": f"{file.size / 1024:.1f} KB",
                    "类型": file.type,
                    "状态": "🔄 重复" if is_duplicate else "✅ 新文件"
                })
            
            st.dataframe(pd.DataFrame(file_data))
            
            # 如果有重复文件，显示警告和处理选项
            if duplicate_files:
                st.warning(f"⚠️ 发现 {len(duplicate_files)} 个重复文件:")
                for dup_file in duplicate_files:
                    st.write(f"• {dup_file}")
                
                st.info("💡 **重复文件处理说明**：重复上传相同文件可能导致后续处理时出现重复数据，建议先检查uploads文件夹。")
                
                duplicate_action = st.radio(
                    "选择重复文件处理方式：",
                    ["🚫 跳过重复文件", "🔄 覆盖现有文件", "📝 重命名上传（不推荐）"],
                    help="跳过：不上传重复文件；覆盖：替换现有文件；重命名：添加时间戳后缀"
                )
                
                if st.button("🚀 开始上传", type="primary"):
                    upload_files(uploaded_files, duplicate_action, CONFIG)
            else:
                if st.button("🚀 开始上传", type="primary"):
                    upload_files(uploaded_files, None, CONFIG)
    
    else:
        upload_method == "📁 本地路径文件扫描"
        st.info("📝 **批量上传说明**")
        st.markdown("""
        1. 将您的EML邮件文件复制到 `eml_process/uploads/` 目录中
        2. 点击下方的"扫描文件夹"按钮
        3. 确认文件列表后开始处理
        """)
        
        if st.button("🔍 扫描uploads文件夹"):
            scan_upload_folder(CONFIG)
    
    # 导航按钮
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("⬅️ 上一步", help="返回首页概览", key="upload_prev_btn"):
            st.session_state.current_step = "首页概览"
            st.rerun()
    with col3:
        if st.button("➡️ 下一步", help="前往数据清洗页面", key="upload_next_btn"):
            # 检查是否有邮件文件可处理
            upload_file_count = count_files(CONFIG["upload_dir"], "*.eml")
            demo_files = count_files("Eml", "*.eml")
            if upload_file_count > 0 or demo_files > 0:
                st.session_state.current_step = "数据清洗"
                st.rerun()
            else:
                st.warning("⚠️ 请先上传邮件文件再进入下一步")


def upload_files(uploaded_files, duplicate_action=None, config=None):
    """处理文件上传"""
    st.info("🚀 开始上传文件...")
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    upload_path = Path(config["upload_dir"])
    upload_path.mkdir(parents=True, exist_ok=True)
    existing_files = {f.name for f in upload_path.glob("*.eml")}
    
    uploaded_count = 0
    skipped_count = 0
    
    for i, file in enumerate(uploaded_files):
        is_duplicate = file.name in existing_files
        file_path = upload_path / file.name
        
        # 处理重复文件
        if is_duplicate and duplicate_action:
            if duplicate_action == "🚫 跳过重复文件":
                status_text.text(f"跳过重复文件: {file.name}")
                skipped_count += 1
                continue
            elif duplicate_action == "📝 重命名上传":
                # 添加时间戳后缀
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                name_parts = file.name.rsplit('.', 1)
                new_name = f"{name_parts[0]}_{timestamp}.{name_parts[1]}"
                file_path = upload_path / new_name
            # 如果是覆盖模式，直接使用原文件名
        
        # 保存文件
        with open(file_path, "wb") as f:
            f.write(file.getbuffer())
        
        uploaded_count += 1
        
        # 更新进度
        progress = (i + 1) / len(uploaded_files)
        progress_bar.progress(progress)
        status_text.text(f"正在上传: {file_path.name}")
        
        # 记录活动
        action_type = "覆盖" if (is_duplicate and duplicate_action == "🔄 覆盖现有文件") else "上传"
        log_activity(f"{action_type}文件: {file_path.name}")
    
    # 显示上传结果
    if skipped_count > 0:
        st.success(f"✅ 成功上传 {uploaded_count} 个文件，跳过 {skipped_count} 个重复文件！")
    else:
        st.success(f"✅ 成功上传 {uploaded_count} 个文件！")


def scan_upload_folder(config):
    """扫描上传文件夹"""
    upload_path = Path(config["upload_dir"])
    eml_files = list(upload_path.glob("*.eml"))
    
    if not eml_files:
        st.warning("📂 uploads文件夹中未发现EML文件")
        st.info("💡 请将EML文件复制到 `eml_process/uploads/` 目录后再扫描")
        return
    
    st.success(f"📁 发现 {len(eml_files)} 个EML文件")
    
    # 检查是否已处理过
    processed_path = Path(config["processed_dir"])
    processed_files = {f.stem for f in processed_path.glob("*.md")} if processed_path.exists() else set()
    
    # 显示文件列表和处理状态
    file_data = []
    for eml_file in eml_files:
        file_stem = eml_file.stem
        is_processed = file_stem in processed_files
        
        file_data.append({
            "文件名": eml_file.name,
            "大小": f"{eml_file.stat().st_size / 1024:.1f} KB",
            "修改时间": eml_file.stat().st_mtime,
            "处理状态": "✅ 已处理" if is_processed else "⏳ 未处理"
        })
    
    # 按修改时间排序
    file_data.sort(key=lambda x: x["修改时间"], reverse=True)
    
    # 格式化时间显示
    for item in file_data:
        item["修改时间"] = datetime.fromtimestamp(item["修改时间"]).strftime("%Y-%m-%d %H:%M")
    
    st.dataframe(pd.DataFrame(file_data))
    
    # 显示统计信息
    processed_count = sum(1 for item in file_data if "✅" in item["处理状态"])
    unprocessed_count = len(file_data) - processed_count
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("总文件数", len(file_data))
    with col2:
        st.metric("已处理", processed_count)
    with col3:
        st.metric("未处理", unprocessed_count)
    
    if unprocessed_count > 0:
        st.info(f"💡 有 {unprocessed_count} 个文件尚未处理，可前往 **数据清洗** 页面进行处理")
    
    if processed_count > 0:
        st.warning("⚠️ **重复处理提醒**：部分文件已经处理过，重复处理可能导致数据重复")
