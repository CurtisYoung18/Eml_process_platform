"""
API Key选择器组件
提供通用的API Key选择界面
"""

import streamlit as st
from config import get_available_api_keys, get_api_key_display_name, get_api_key


def show_api_selector(purpose, key="api_selector", default_number="1"):
    """
    显示API Key选择器
    
    Args:
        purpose: API Key用途 ("llm", "knowledge_base", "qa")
        key: Streamlit组件的key
        default_number: 默认选择的API Key编号
    
    Returns:
        tuple: (选择的API Key, 选择的编号)
    """
    available_keys = get_available_api_keys(purpose)
    
    if not available_keys:
        st.error(f"❌ 未找到{purpose}用途的API Key配置")
        st.info("💡 请检查.env文件中的API Key配置")
        return None, None
    
    # 创建选择选项
    options = []
    values = []
    
    for number, api_key in available_keys.items():
        display_name = get_api_key_display_name(purpose, number)
        masked_key = f"{api_key[:8]}...{api_key[-8:]}" if len(api_key) > 16 else api_key
        option_text = f"{display_name}: {masked_key}"
        
        options.append(option_text)
        values.append(number)
    
    # 确定默认索引
    default_index = 0
    if default_number in values:
        default_index = values.index(default_number)
    
    # 显示选择器
    selected_option = st.selectbox(
        f"选择{purpose.upper()} API Key",
        options,
        index=default_index,
        key=key,
        help=f"选择用于{purpose}功能的API Key"
    )
    
    if selected_option:
        selected_index = options.index(selected_option)
        selected_number = values[selected_index]
        selected_api_key = available_keys[selected_number]
        
        return selected_api_key, selected_number
    
    return None, None


def show_api_key_status(purpose, api_key, key_number):
    """
    显示API Key状态信息
    
    Args:
        purpose: API Key用途
        api_key: API Key值
        key_number: API Key编号
    """
    if api_key:
        display_name = get_api_key_display_name(purpose, key_number)
        masked_key = f"{api_key[:8]}...{api_key[-8:]}" if len(api_key) > 16 else api_key
        
        st.success(f"✅ 当前使用: {display_name}")
        st.code(f"API Key: {masked_key}")
    else:
        st.error("❌ 未选择有效的API Key")


def show_api_configuration_guide(purpose):
    """
    显示API配置指南
    
    Args:
        purpose: API Key用途
    """
    purpose_info = {
        "llm": {
            "name": "LLM邮件清洗",
            "description": "用于邮件内容清洗和结构化处理",
            "env_vars": ["GPTBOTS_LLM_API_KEY_1", "GPTBOTS_LLM_API_KEY_2", "GPTBOTS_LLM_API_KEY_3"]
        },
        "knowledge_base": {
            "name": "知识库上传",
            "description": "用于将处理后的文档上传到GPTBots知识库",
            "env_vars": ["GPTBOTS_KB_API_KEY_1", "GPTBOTS_KB_API_KEY_2", "GPTBOTS_KB_API_KEY_3"]
        },
        "qa": {
            "name": "问答系统",
            "description": "用于智能问答功能",
            "env_vars": ["GPTBOTS_QA_API_KEY_1", "GPTBOTS_QA_API_KEY_2", "GPTBOTS_QA_API_KEY_3"]
        }
    }
    
    info = purpose_info.get(purpose, {})
    if not info:
        return
    
    with st.expander(f"📋 {info['name']} API配置说明"):
        st.markdown(f"""
        **用途**: {info['description']}
        
        **环境变量配置**:
        """)
        
        for env_var in info['env_vars']:
            st.code(f"{env_var}=your-api-key-here")
        
        st.markdown("""
        **配置步骤**:
        1. 在项目根目录创建或编辑 `.env` 文件
        2. 添加上述环境变量和您的API Key
        3. 重启应用以加载新配置
        4. 在此页面选择要使用的API Key
        
        **注意事项**:
        - 至少需要配置一个API Key (编号1)
        - 可以配置多个API Key用于不同场景
        - API Key请妥善保管，不要泄露给他人
        """)


def create_api_selector_with_guide(purpose, key_prefix="", show_guide=True):
    """
    创建带配置指南的API选择器
    
    Args:
        purpose: API Key用途
        key_prefix: key前缀，用于避免重复
        show_guide: 是否显示配置指南
    
    Returns:
        tuple: (选择的API Key, 选择的编号)
    """
    col1, col2 = st.columns([3, 1])
    
    with col1:
        api_key, key_number = show_api_selector(
            purpose, 
            key=f"{key_prefix}_{purpose}_api_selector"
        )
    
    with col2:
        if show_guide:
            if st.button("📋 配置指南", key=f"{key_prefix}_{purpose}_guide_btn"):
                st.session_state[f"show_{purpose}_guide"] = not st.session_state.get(f"show_{purpose}_guide", False)
    
    # 显示状态
    if api_key and key_number:
        show_api_key_status(purpose, api_key, key_number)
    
    # 显示配置指南
    if show_guide and st.session_state.get(f"show_{purpose}_guide", False):
        show_api_configuration_guide(purpose)
    
    return api_key, key_number
