#!/usr/bin/env python3
"""
邮件知识库处理系统 - 主应用
基于Streamlit构建的本地部署应用
"""

import streamlit as st
from streamlit_option_menu import option_menu
from dotenv import load_dotenv
from tools import *
from config import CONFIG, APP_CONFIG, NAVIGATION, init_directories

# 加载.env环境变量
load_dotenv()

# 设置页面配置
st.set_page_config(
    page_title=APP_CONFIG["app_title"],
    page_icon=APP_CONFIG["page_icon"],
    layout=APP_CONFIG["layout"],
    initial_sidebar_state=APP_CONFIG["initial_sidebar_state"]
)

def main():
    """主应用函数"""
    init_directories()
    
    # 主标题
    st.title(APP_CONFIG["app_title"])
    
    # 初始化session state
    if 'current_step' not in st.session_state:
        st.session_state.current_step = "首页概览"
    
    # 侧边栏导航
    with st.sidebar:
        st.header("📋 功能导航")
        
        selected_step = option_menu(
            None,
            NAVIGATION["options"],
            icons=NAVIGATION["icons"],
            menu_icon="cast",
            default_index=NAVIGATION["options"].index(st.session_state.current_step) if 'current_step' in st.session_state and st.session_state.current_step in NAVIGATION["options"] else 0,
            orientation="vertical",
            styles={
                "container": {"padding": "5px", "background-color": "#fafafa"},
                "icon": {"color": "#fa8800", "font-size": "20px"},
                "nav-link": {"font-size": "16px", "text-align": "left", "margin":"0px", "--hover-color": "#eee"},
                "nav-link-selected": {"background-color": "#02ab21", "color": "white"},
            }
        )
        
        # 更新session state
        if selected_step != st.session_state.current_step:
            st.session_state.current_step = selected_step
            st.rerun()
        
        current_step = st.session_state.current_step
        
        st.markdown("---")
        st.markdown("### 📈 处理状态")
        
        # 显示各步骤状态
        status_data = get_processing_status()
        for step, status in status_data.items():
            if status == "completed":
                st.success(f"✅ {step}")
            elif status == "processing":
                st.warning(f"⏳ {step}")
            else:
                st.info(f"📅 {step}")
    
    # 主内容区域
    if current_step == "首页概览":
        show_homepage()
    elif current_step == "邮件上传":
        show_upload_page()
    elif current_step == "数据清洗":
        show_cleaning_page()
    elif current_step == "LLM处理":
        show_llm_processing_page()
    elif current_step == "结果查看":
        show_results_page()
    elif current_step == "知识库管理":
        show_knowledge_base_page()
    elif current_step == "问答系统":
        show_qa_system_page()

if __name__ == "__main__":
    main()
