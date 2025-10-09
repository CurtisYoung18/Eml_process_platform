"""
首页概览模块
显示系统概览、处理进度和全自动运行配置
"""

import streamlit as st
import os
from pathlib import Path
from .utils import count_files, log_activity
from .api_selector import create_api_selector_with_guide
from config import DIRECTORIES

# 尝试导入streamlit_mermaid，如果失败则使用备用方案
try:
    from streamlit_mermaid import st_mermaid
    MERMAID_AVAILABLE = True
except ImportError:
    MERMAID_AVAILABLE = False


def show_homepage():
    """显示首页概览"""
    
    
    # 当前进度概览
    st.subheader("📊 当前进度")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="📧 已上传邮件",
            value=count_files(DIRECTORIES["upload_dir"], "*.eml"),
            delta="0"
        )
    
    with col2:
        st.metric(
            label="🔧 已清洗邮件", 
            value=count_files(DIRECTORIES["processed_dir"], "*.md"),
            delta="0"
        )
    
    with col3:
        st.metric(
            label="🤖 LLM处理完成",
            value=count_files(DIRECTORIES["final_dir"], "*.md"),
            delta="0"
        )
    
    st.markdown("---")
    
    # 创建两个主要板块
    tab1, tab2 = st.tabs(["🔄 流程介绍", "⚙️ 全自动运行配置"])
    
    with tab1:
        show_process_introduction()
    
    with tab2:
        show_auto_run_configuration()


def show_process_introduction():
    """显示流程介绍板块"""
    st.markdown("### 📋 系统介绍")
    st.info("这是一个邮件知识库管理系统，帮助您管理邮件内容，构建知识库，提供智能问答功能。")
    
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.markdown("**邮件知识库管理系统** 是一个本地部署的应用，完整的处理流程如下：")
        
        # 系统流程图
        st.subheader("🔄 处理流程")
        mermaid_code = """
        graph TD
            A["📁 上传EML邮件文件"] --> B["📤 批量邮件上传<br/>支持EML格式邮件的<br/>批量上传和管理"]
            B --> C["🔧 智能数据清洗<br/>自动去除重复内容<br/>保留独特信息"]
            C --> D["🤖 LLM二次处理<br/>使用AI技术提取<br/>结构化项目信息"]
            D --> E["📚 知识库构建<br/>将处理后的数据构建为<br/>可查询的知识库"]
            E --> F["💬 智能问答<br/>基于邮件内容提供<br/>项目经验查询"]
            
            B --> G["📊 结果查看<br/>查看处理结果和统计"]
            C --> G
            D --> G
            E --> G
            
            style A fill:#e1f5fe
            style B fill:#f3e5f5
            style C fill:#e8f5e8
            style D fill:#fff3e0
            style E fill:#fce4ec
            style F fill:#e0f2f1
            style G fill:#f1f8e9
        """
        
        # 使用Mermaid显示流程图
        if MERMAID_AVAILABLE:
            st_mermaid(mermaid_code, height="1000px")
        else:
            # 备用方案：使用HTML+JavaScript显示Mermaid
            st.components.v1.html(
                f"""
                <div class="mermaid">
                {mermaid_code}
                </div>
                <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
                <script>
                    mermaid.initialize({{startOnLoad:true, theme: 'default'}});
                </script>
                """,
                height=1000
            )
            st.info("💡 提示：如需更好的图表显示效果，请运行 `pip install streamlit-mermaid`")
    
    with col2:
        st.markdown("### 🚀 使用方式")
        
        # 手动模式
        st.markdown("#### 🔧 手动模式")
        st.markdown("""
        1. 点击 **"邮件上传"** 开始上传您的EML邮件文件
        2. 使用 **"数据清洗"** 功能去除重复内容
        3. 通过 **"LLM处理"** 提取结构化信息
        4. 在 **"知识库管理"** 中上传到知识库
        5. 使用 **"问答系统"** 进行智能查询
        """)
        
        # 全自动模式
        st.markdown("#### 🤖 全自动模式")
        st.success("""
        **新功能！** 一键完成所有处理步骤：
        1. 上传邮件文件
        2. 配置处理参数（右侧标签页）
        3. 点击"全自动运行"按钮
        4. 系统自动完成所有处理步骤
        """)
        
        # 导航按钮
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔧 手动模式", help="逐步进行处理", type="secondary", key="manual_mode_btn"):
                st.session_state.current_step = "邮件上传"
                st.rerun()
        with col2:
            if st.button("🤖 全自动模式", help="切换到全自动配置", type="primary", key="auto_mode_btn"):
                st.info("👉 请切换到右侧的'全自动运行配置'标签页")
        
        # 最近活动
        st.markdown("---")
        st.subheader("📅 最近活动")
        if os.path.exists("logs/activity.log"):
            with open("logs/activity.log", "r", encoding="utf-8") as f:
                activities = f.readlines()[-5:]  # 显示最近5条活动
                for activity in activities:
                    st.text(activity.strip())
        else:
            st.info("暂无活动记录")


def show_auto_run_configuration():
    """显示全自动运行配置板块"""
    st.markdown("### 🤖 全自动运行配置")
    st.info("配置以下参数后，系统将自动完成从邮件上传到知识库构建的全部流程")
    
    # 初始化session state
    if 'auto_config' not in st.session_state:
        st.session_state.auto_config = {
            'llm_api_key': None,
            'llm_key_number': None,
            'kb_api_key': None,
            'kb_key_number': None,
            'endpoint': 'sg',
            'delay': 2,
            'chunk_token': 600,
            'knowledge_base_id': '',
            'splitter': None,
            'knowledge_bases': [],
            'files_uploaded': False
        }
    
    # 步骤1：邮件文件管理
    st.markdown("#### 📤 步骤1：邮件文件管理")
    
    # 获取本地已有文件
    existing_files = get_existing_email_files()
    
    # 显示当前状态
    if existing_files:
        st.info(f"📊 **本地邮件状态**: 检测到 {len(existing_files)} 个邮件文件")
        st.warning(f"⚠️ **重要提示**: 全自动处理将处理本地文件夹中的所有 {len(existing_files)} 个邮件文件")
        
        # 显示文件列表摘要
        with st.expander(f"📋 查看本地邮件文件列表 ({len(existing_files)} 个)"):
            for i, file_info in enumerate(existing_files, 1):
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.text(f"{i}. 📧 {file_info['name']}")
                with col2:
                    st.text(f"{file_info['size_mb']} MB")
                with col3:
                    if st.button("🗑️", key=f"quick_delete_{i}", help=f"删除 {file_info['name']}"):
                        if delete_email_file(file_info['path']):
                            st.success(f"✅ 已删除 {file_info['name']}")
                            st.rerun()
        
        # 文件管理操作
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("📤 添加更多邮件", key="add_more_emails"):
                st.session_state.show_upload_section = True
                st.rerun()
        
        with col2:
            if st.button("🗑️ 清空所有邮件", key="clear_all_emails_main"):
                if st.session_state.get('confirm_clear_all_main', False):
                    deleted_count = 0
                    for file_info in existing_files:
                        if delete_email_file(file_info['path']):
                            deleted_count += 1
                    st.success(f"✅ 已删除 {deleted_count} 个文件")
                    st.session_state['confirm_clear_all_main'] = False
                    log_activity(f"批量删除邮件文件: {deleted_count} 个")
                    st.rerun()
                else:
                    st.session_state['confirm_clear_all_main'] = True
                    st.warning("⚠️ 再次点击确认删除所有文件")
        
        with col3:
            if st.button("🔄 刷新列表", key="refresh_main_list"):
                st.rerun()
        
        # 设置文件状态为已有
        st.session_state.auto_config['files_uploaded'] = True
        uploaded_files = None  # 没有新上传的文件
        
    else:
        st.warning("📭 **本地没有邮件文件**，请先上传EML邮件文件")
        st.session_state.auto_config['files_uploaded'] = False
        uploaded_files = None
    
    # 上传新文件区域（条件显示）
    if not existing_files or st.session_state.get('show_upload_section', False):
        st.markdown("---")
        st.markdown("**📤 上传新的EML邮件文件**")
        
        uploaded_files = st.file_uploader(
            "选择EML邮件文件",
            type=['eml'],
            accept_multiple_files=True,
            key="auto_upload_files",
            help="支持批量上传EML格式的邮件文件，上传后将与本地文件一起处理"
        )
        
        if uploaded_files:
            st.success(f"✅ 已选择 {len(uploaded_files)} 个新邮件文件")
            total_files = len(existing_files) + len(uploaded_files)
            st.info(f"📊 **处理预览**: 将处理 {len(existing_files)} 个本地文件 + {len(uploaded_files)} 个新上传文件 = 共 {total_files} 个文件")
            
            # 显示新上传文件列表
            with st.expander("📋 查看新上传文件列表"):
                for file in uploaded_files:
                    st.text(f"📧 {file.name} ({file.size} bytes)")
            
            st.session_state.auto_config['files_uploaded'] = True
        
        # 隐藏上传区域按钮
        if st.session_state.get('show_upload_section', False):
            if st.button("❌ 隐藏上传区域", key="hide_upload_section"):
                st.session_state.show_upload_section = False
                st.rerun()
    
    st.markdown("---")
    
    # 步骤2：LLM处理配置
    st.markdown("#### 🤖 步骤2：LLM处理配置")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**LLM API Key配置**")
        
        # API Key选择方式
        llm_api_mode = st.radio(
            "LLM API配置方式",
            ["使用预配置", "手动输入"],
            key="llm_api_mode",
            help="选择使用预配置的API Key还是手动输入"
        )
        
        if llm_api_mode == "使用预配置":
            llm_api_key, llm_key_number = create_api_selector_with_guide(
                "llm", 
                key_prefix="auto_config",
                show_guide=False
            )
            st.session_state.auto_config['llm_api_key'] = llm_api_key
            st.session_state.auto_config['llm_key_number'] = llm_key_number
        else:
            llm_api_key = st.text_input(
                "LLM API Key",
                type="password",
                key="manual_llm_api_key",
                help="手动输入LLM处理API Key"
            )
            st.session_state.auto_config['llm_api_key'] = llm_api_key
            st.session_state.auto_config['llm_key_number'] = "manual"
        
        # 显示配置帮助
        with st.expander("📋 LLM API配置说明"):
            st.markdown("""
            **预配置方式**：
            - 在项目根目录的 `.env` 文件中配置
            - 环境变量名：`GPTBOTS_LLM_API_KEY_1`, `GPTBOTS_LLM_API_KEY_2`, `GPTBOTS_LLM_API_KEY_3`
            
            **手动输入方式**：
            - 直接在上方输入框中输入API Key
            - 适用于临时使用或测试
            
            **配置文件位置**：
            ```
            项目根目录/.env
            ```
            """)
    
    with col2:
        st.markdown("**LLM处理参数**")
        
        # 使用固定的内网API地址
        st.info("🌐 **API服务地址**: http://10.52.20.41:19080")
        endpoint = "internal"  # 使用固定标识
        st.session_state.auto_config['endpoint'] = endpoint
        
        delay = st.slider(
            "处理延迟(秒)",
            min_value=1,
            max_value=10,
            value=2,
            key="auto_delay",
            help="API请求间隔，避免限流"
        )
        st.session_state.auto_config['delay'] = delay
        
        # LLM处理说明
        with st.expander("🔧 LLM处理说明"):
            st.markdown("""
            **API节点选择**：
            - 🌏 新加坡 (sg)：推荐，稳定性最好
            - 🇨🇳 中国 (cn)：国内用户可选
            - 🇹🇭 泰国 (th)：备用节点
            
            **处理延迟**：
            - 设置API请求间的延迟时间
            - 避免触发API限流
            - 推荐值：2-3秒
            """)
    
    st.markdown("---")
    
    # 步骤3：知识库配置
    st.markdown("#### 📚 步骤3：知识库配置")
    
    # 知识库API配置
    st.markdown("**知识库API Key配置**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # API Key选择方式
        kb_api_mode = st.radio(
            "知识库API配置方式",
            ["使用预配置", "手动输入"],
            key="kb_api_mode",
            help="选择使用预配置的API Key还是手动输入"
        )
        
        if kb_api_mode == "使用预配置":
            kb_api_key, kb_key_number = create_api_selector_with_guide(
                "knowledge_base", 
                key_prefix="auto_config",
                show_guide=False
            )
            st.session_state.auto_config['kb_api_key'] = kb_api_key
            st.session_state.auto_config['kb_key_number'] = kb_key_number
        else:
            kb_api_key = st.text_input(
                "知识库API Key",
                type="password",
                key="manual_kb_api_key",
                help="手动输入知识库上传API Key"
            )
            st.session_state.auto_config['kb_api_key'] = kb_api_key
            st.session_state.auto_config['kb_key_number'] = "manual"
        
        # 显示配置帮助
        with st.expander("📋 知识库API配置说明"):
            st.markdown("""
            **预配置方式**：
            - 在项目根目录的 `.env` 文件中配置
            - 环境变量名：`GPTBOTS_KB_API_KEY_1`, `GPTBOTS_KB_API_KEY_2`, `GPTBOTS_KB_API_KEY_3`
            
            **手动输入方式**：
            - 直接在上方输入框中输入API Key
            - 适用于临时使用或测试
            
            **配置文件位置**：
            ```
            项目根目录/.env
            ```
            """)
    
    with col2:
        # 刷新知识库列表按钮
        if kb_api_key:
            if st.button("🔄 刷新知识库列表", key="refresh_kb_list", help="获取当前API Key可访问的知识库列表"):
                with st.spinner("正在获取知识库列表..."):
                    knowledge_bases = get_knowledge_base_list_for_auto(kb_api_key)
                    if knowledge_bases:
                        st.session_state.auto_config['knowledge_bases'] = knowledge_bases
                        st.success(f"✅ 成功获取 {len(knowledge_bases)} 个知识库")
                    else:
                        st.error("❌ 获取知识库列表失败，请检查API Key是否正确")
        else:
            st.info("💡 请先配置知识库API Key，然后刷新知识库列表")
    
    # 目标知识库选择
    st.markdown("**目标知识库选择**")
    
    # 知识库选择
    if st.session_state.auto_config.get('knowledge_bases'):
        knowledge_bases = st.session_state.auto_config['knowledge_bases']
        
        # 构建知识库选项
        kb_options = [{"name": "默认知识库", "id": ""}]  # 默认选项
        kb_options.extend([
            {"name": f"{kb['name']} ({kb['id'][:8]}...)", "id": kb['id']} 
            for kb in knowledge_bases
        ])
        
        selected_kb_index = st.selectbox(
            "选择目标知识库",
            range(len(kb_options)),
            format_func=lambda x: kb_options[x]["name"],
            help="选择要上传文件的目标知识库",
            key="auto_kb_selection"
        )
        knowledge_base_id = kb_options[selected_kb_index]["id"]
        st.session_state.auto_config['knowledge_base_id'] = knowledge_base_id
        
        if knowledge_base_id:
            st.success(f"✅ 已选择知识库: {kb_options[selected_kb_index]['name']}")
        else:
            st.info("💡 将使用默认知识库")
    else:
        st.warning("⚠️ 请先点击上方的'刷新知识库列表'按钮获取可用的知识库")
        st.session_state.auto_config['knowledge_base_id'] = ""
    
    st.markdown("---")
    
    # 文档分割配置
    st.markdown("**文档分割配置**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 分块方式选择（与API对齐）
        chunk_method = st.radio(
            "分块方式",
            ["按Token数分块", "按分隔符分块"],
            help="选择文档分块方式",
            key="auto_chunk_method"
        )
        
        if chunk_method == "按Token数分块":
            chunk_token = st.number_input(
                "分块Token数",
                min_value=1,
                max_value=1000,
                value=600,
                help="单个知识块的最大Token数（1-1000）",
                key="auto_chunk_token_input"
            )
            st.session_state.auto_config['chunk_token'] = chunk_token
            st.session_state.auto_config['splitter'] = None
        else:
            splitter = st.text_input(
                "分隔符",
                value="\\n",
                help="使用自定义分隔符进行分块，支持 \\n（换行）、\\t（制表符）等",
                key="auto_splitter_input"
            )
            # 处理转义字符
            if splitter == "\\n":
                splitter = "\n"
            elif splitter == "\\t":
                splitter = "\t"
            st.session_state.auto_config['splitter'] = splitter
            st.session_state.auto_config['chunk_token'] = None
    
    with col2:
        st.markdown("**分块方式说明**")
        if chunk_method == "按Token数分块":
            st.info("""
            📊 **按Token数分块**
            - 根据Token数量自动分割文档
            - 适合大多数文档类型
            - 推荐值：600 Token
            - 范围：1-1000 Token
            """)
        else:
            st.info("""
            📝 **按分隔符分块**
            - 使用指定字符串分割文档
            - 适合有明确结构的文档
            - 常用分隔符：
              - `\\n` : 按换行分割
              - `\\t` : 按制表符分割
              - 自定义字符串
            """)
        
        # API参数说明
        with st.expander("🔧 API参数说明"):
            st.markdown("""
            根据GPTBots知识库API规范：
            
            **chunk_token** 与 **splitter** 参数：
            - 必须二选一，不能同时为空
            - 同时提供时优先使用分隔符
            - chunk_token范围：1-1000
            - splitter支持任意自定义字符串
            """)
    
    st.markdown("---")
    
    # 步骤4：全自动运行
    st.markdown("#### 🚀 步骤4：全自动运行")
    
    # 检查配置完整性
    config_status = check_auto_config_status()
    

    if config_status['ready']:
            st.success("✅ 配置完整，可以开始全自动运行")
    else:
        st.warning("⚠️ 配置不完整，请检查以下项目：")
        for item in config_status['missing']:
            st.error(f"❌ {item}")
    
    if st.button(
         "🤖 开始全自动运行",
         type="primary",
         disabled=not config_status['ready'],
         key="start_auto_run",
         help="一键完成所有处理步骤" if config_status['ready'] else "请先完成配置"
     ):
         start_auto_processing(uploaded_files)
    
    # 检查是否有已完成的处理结果需要显示后续操作
    if st.session_state.get('auto_processing_completed', False):
        results = st.session_state.get('auto_processing_results', {})
        
        st.markdown("---")
        st.markdown("### 🎉 处理完成")
        
        # 显示处理结果摘要
        if results:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("📤 上传文件", results.get("upload_count", 0))
            with col2:
                st.metric("🧹 清洗文件", results.get("cleaned_count", 0))
            with col3:
                st.metric("🤖 LLM处理", results.get("llm_processed_count", 0))
            with col4:
                st.metric("📚 知识库上传", results.get("kb_uploaded_count", 0))
        
        # 提供后续操作选项
        st.markdown("### 🎯 后续操作")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("📊 查看结果", key="persistent_view_results_btn"):
                st.session_state.current_step = "结果查看"
                st.success("🔄 正在跳转到结果查看页面...")
                st.rerun()
        
        with col2:
            if st.button("💬 开始问答", key="persistent_start_qa_btn"):
                st.session_state.current_step = "问答系统"
                st.rerun()
        
        with col3:
            if st.button("🔄 重新处理", key="persistent_restart_processing_btn"):
                # 清理session state，准备重新处理
                if 'auto_config' in st.session_state:
                    st.session_state.auto_config['files_uploaded'] = False
                st.session_state.auto_processing_completed = False
                st.session_state.auto_processing_results = None
                st.rerun()


def check_auto_config_status():
    """检查全自动配置状态"""
    config = st.session_state.auto_config
    missing = []
    
    if not config.get('files_uploaded', False):
        missing.append("请上传邮件文件")
    
    if not config.get('llm_api_key'):
        missing.append("请配置LLM处理API Key")
    
    if not config.get('kb_api_key'):
        missing.append("请配置知识库上传API Key")
    
    return {
        'ready': len(missing) == 0,
        'missing': missing
    }


def start_auto_processing(uploaded_files):
    """开始全自动处理"""
    st.info("🚀 开始全自动处理流程...")
    
    # 获取配置参数
    config = st.session_state.auto_config
    
    # 验证配置
    if not config.get('llm_api_key') or not config.get('kb_api_key'):
        st.error("❌ API配置不完整，无法开始处理")
        return
    
    if not uploaded_files:
        st.error("❌ 没有上传文件，无法开始处理")
        return
    
    # 准备配置参数
    pipeline_config = {
        'llm_api_key': config['llm_api_key'],
        'kb_api_key': config['kb_api_key'],
        'endpoint': config['endpoint'],
        'delay': config['delay'],
        'chunk_token': config['chunk_token'],
        'knowledge_base_id': config['knowledge_base_id'],
        'splitter': config['splitter']
    }
    
    # 运行自动处理流水线
    from .auto_pipeline import run_auto_processing_pipeline
    
    try:
        results = run_auto_processing_pipeline(uploaded_files, pipeline_config)
        
        # 处理完成后的操作
        if results["success"]:
            st.balloons()  # 显示庆祝动画
            
            # 保存处理结果到session state
            st.session_state.auto_processing_completed = True
            st.session_state.auto_processing_results = results
            
            # 提供后续操作选项
            st.markdown("---")
            st.markdown("### 🎯 后续操作")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("📊 查看结果", key="view_results_btn"):
                    st.session_state.current_step = "结果查看"
                    st.success("🔄 正在跳转到结果查看页面...")
                    st.rerun()
            
            with col2:
                if st.button("💬 开始问答", key="start_qa_btn"):
                    st.session_state.current_step = "问答系统"
                    st.rerun()
            
            with col3:
                if st.button("🔄 重新处理", key="restart_processing_btn"):
                    # 清理session state，准备重新处理
                    if 'auto_config' in st.session_state:
                        st.session_state.auto_config['files_uploaded'] = False
                    st.session_state.auto_processing_completed = False
                    st.session_state.auto_processing_results = None
                    st.rerun()
        else:
            # 处理失败时也清理状态
            st.session_state.auto_processing_completed = False
            st.session_state.auto_processing_results = None
        
    except Exception as e:
        st.error(f"❌ 自动处理过程中发生错误: {str(e)}")
        st.error("请检查配置和网络连接，然后重试")


def get_knowledge_base_list_for_auto(api_key):
    """
    为全自动配置获取知识库列表
    
    Args:
        api_key: API密钥
        endpoint: API端点
    
    Returns:
        知识库列表或None
    """
    try:
        from .api_clients import KnowledgeBaseAPI
        
        # 初始化API客户端
        client = KnowledgeBaseAPI(api_key)
        
        # 获取知识库列表
        response = client.get_knowledge_bases()
        
        if response:
            # 检查不同的响应格式
            if "data" in response and "list" in response["data"]:
                # 格式1: {"data": {"list": [...]}}
                knowledge_bases = response["data"]["list"]
                return knowledge_bases
            elif "knowledge_base" in response:
                # 格式2: {"knowledge_base": [...]}
                knowledge_bases = response["knowledge_base"]
                return knowledge_bases
            elif "error" in response:
                # 错误响应
                log_activity(f"获取知识库列表API错误: {response['message']}")
                return None
            else:
                log_activity(f"获取知识库列表响应格式未知: {response}")
                return None
        else:
            log_activity("获取知识库列表无响应")
            return None
            
    except Exception as e:
        log_activity(f"获取知识库列表异常: {str(e)}")
        return None


def get_existing_email_files():
    """
    获取已上传的邮件文件列表
    
    Returns:
        list: 邮件文件信息列表
    """
    try:
        upload_dir = Path(DIRECTORIES["upload_dir"])
        if not upload_dir.exists():
            return []
        
        eml_files = list(upload_dir.glob("*.eml"))
        file_info_list = []
        
        for eml_file in eml_files:
            file_stat = eml_file.stat()
            file_info = {
                'name': eml_file.name,
                'path': str(eml_file),
                'size': file_stat.st_size,
                'modified_time': file_stat.st_mtime,
                'size_mb': round(file_stat.st_size / (1024 * 1024), 2)
            }
            file_info_list.append(file_info)
        
        # 按修改时间排序（最新的在前）
        file_info_list.sort(key=lambda x: x['modified_time'], reverse=True)
        return file_info_list
        
    except Exception as e:
        log_activity(f"获取邮件文件列表异常: {str(e)}")
        return []


def delete_email_file(file_path):
    """
    删除指定的邮件文件
    
    Args:
        file_path: 文件路径
    
    Returns:
        bool: 删除是否成功
    """
    try:
        file_to_delete = Path(file_path)
        if file_to_delete.exists():
            file_to_delete.unlink()
            log_activity(f"删除邮件文件: {file_to_delete.name}")
            return True
        else:
            return False
    except Exception as e:
        log_activity(f"删除邮件文件失败: {str(e)}")
        return False




def show_email_preview(file_path):
    """显示邮件内容预览"""
    try:
        import email
        from email.header import decode_header
        
        with open(file_path, 'rb') as f:
            msg = email.message_from_bytes(f.read())
        
        # 解析邮件头信息
        def decode_mime_words(s):
            if s is None:
                return ""
            decoded_parts = decode_header(s)
            decoded_string = ""
            for part, encoding in decoded_parts:
                if isinstance(part, bytes):
                    if encoding:
                        decoded_string += part.decode(encoding)
                    else:
                        decoded_string += part.decode('utf-8', errors='ignore')
                else:
                    decoded_string += part
            return decoded_string
        
        subject = decode_mime_words(msg.get('Subject', ''))
        from_addr = decode_mime_words(msg.get('From', ''))
        to_addr = decode_mime_words(msg.get('To', ''))
        date = msg.get('Date', '')
        
        # 显示邮件信息
        with st.expander(f"📧 邮件预览: {subject[:50]}...", expanded=True):
            st.markdown("**📋 邮件信息**")
            st.text(f"主题: {subject}")
            st.text(f"发件人: {from_addr}")
            st.text(f"收件人: {to_addr}")
            st.text(f"日期: {date}")
            
            # 获取邮件正文
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        try:
                            body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                            break
                        except:
                            continue
            else:
                try:
                    body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
                except:
                    body = "无法解析邮件内容"
            
            if body:
                st.markdown("**📄 邮件内容预览**")
                # 只显示前500个字符
                preview_text = body[:500] + "..." if len(body) > 500 else body
                st.text_area("内容预览", preview_text, height=150, disabled=True)
            else:
                st.info("📭 无法获取邮件文本内容")
                
    except Exception as e:
        st.error(f"❌ 邮件预览失败: {str(e)}")
        log_activity(f"邮件预览失败: {file_path} - {str(e)}")
