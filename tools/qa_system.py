"""
问答系统模块
支持iframe集成的智能问答功能
"""

import streamlit as st


def show_qa_system_page():
    """显示问答系统页面"""
    
    # 直接显示问答界面
    st.markdown("""
    ### 💬 基于知识库的智能问答
    这是基于GPTBots的智能问答系统，可以回答关于已上传知识库的问题。
    
    分享链接：[Agent: NolatoEml](http://10.52.20.41:19080/s/cspI1GSw)
    
    ---
    """)
    
    # 嵌入GPTBots聊天界面
    import streamlit.components.v1 as components
    
    iframe_html = """
    <iframe 
        width="100%" 
        height="1200px" 
        allow="microphone *" 
        src="http://10.52.20.41:19080/widget/eerfztrnqsiqkxj85aobcwb/chat.html"
        style="border: 1px solid #ddd; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
    </iframe>
    """
    
  
    
    components.html(iframe_html, height=1300)

    
    # 使用说明
    st.markdown("---")
    st.info("💡 这是独立的智能问答系统，您可以直接提问而无需处理任何文件。问答基于预先配置的知识库内容。")