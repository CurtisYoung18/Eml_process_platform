"""
LLM处理模块
使用GPTBots API处理清洗后的邮件内容
"""

import streamlit as st
import os
import time
from pathlib import Path
from datetime import datetime
from .utils import count_files, log_activity


def show_llm_processing_page():
    """显示LLM处理页面"""
    from app import CONFIG
    
    st.header("LLM数据处理")
    
    # 初始化LLM处理状态
    if "llm_processing_state" not in st.session_state:
        st.session_state.llm_processing_state = "idle"  # idle, processing, paused
    if "llm_processed_count" not in st.session_state:
        st.session_state.llm_processed_count = 0
    if "llm_total_files" not in st.session_state:
        st.session_state.llm_total_files = 0
    
    # 检查清洗后的文件
    md_files = count_files(CONFIG["processed_dir"], "*.md")
    
    if md_files == 0:
        st.warning("⚠️ 未发现已清洗的Markdown文件，请先完成数据清洗步骤。")
        return
    
    st.success(f"✅ 发现 {md_files} 个已清洗的Markdown文件待处理")
    
    # API配置
    st.subheader("🔑 LLM处理API配置")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 节点选择
        endpoint = st.selectbox(
            "选择API节点",
            options=["sg", "cn", "th"],
            index=0,  # 默认sg
            format_func=lambda x: {
                "sg": "🌏 新加坡 (sg) - 推荐",
                "cn": "🇨🇳 中国 (cn)",
                "th": "🇹🇭 泰国 (th)"
            }[x],
            help="选择GPTBots API数据中心节点",
            key="llm_endpoint_selector"
        )

        # API Key选择器
        from .api_selector import create_api_selector_with_guide
        api_key, key_number = create_api_selector_with_guide(
            purpose="llm",
            key_prefix="llm_processing",
            show_guide=True
        )
        
        if not api_key:
            st.warning("⚠️ 请配置LLM API Key")
            st.info("💡 请在.env文件中配置GPTBOTS_LLM_API_KEY_1等环境变量")
            return

        # 验证API配置
        st.subheader("🔍 API连接测试")
        if st.button("🧪 测试API连接", key="test_api_btn"):
            test_api_connection(api_key)

    with col2:
        # LLM处理参数
        st.subheader("⚙️ 处理参数")

        delay_seconds = st.number_input(
            "请求间隔(秒)",
            min_value=0,
            max_value=10,
            value=1,
            help="API请求之间的延迟时间"
        )
    
        # 动态按钮逻辑
        processing_state = st.session_state.llm_processing_state
        
        if processing_state == "idle":
            # 未开始处理
            if st.button("🚀 开始LLM处理", type="primary", key="start_llm_btn"):
                st.session_state.llm_processing_state = "processing"
                st.session_state.llm_processed_count = 0
                st.rerun()
        elif processing_state == "processing":
            # 正在处理中
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("⏸️ 暂停处理", type="secondary", key="pause_llm_btn"):
                    st.session_state.llm_processing_state = "paused"
                    st.rerun()
            with col_btn2:
                st.info("🔄 正在处理中...")
        elif processing_state == "paused":
            # 已暂停
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("▶️ 继续处理", type="primary", key="resume_llm_btn"):
                    st.session_state.llm_processing_state = "processing"
                    st.rerun()
            with col_btn2:
                if st.button("🛑 停止处理", type="secondary", key="stop_llm_btn"):
                    st.session_state.llm_processing_state = "idle"
                    st.session_state.llm_processed_count = 0
                    st.rerun()
        
        # 显示处理进度
        if processing_state in ["processing", "paused"]:
            if st.session_state.llm_total_files > 0:
                progress_pct = st.session_state.llm_processed_count / st.session_state.llm_total_files
                st.progress(progress_pct)
                st.text(f"进度: {st.session_state.llm_processed_count}/{st.session_state.llm_total_files} 文件")
        
        # 执行处理逻辑
        if processing_state == "processing":
            start_llm_processing(api_key, delay_seconds, CONFIG)
        
    # 导航按钮
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("⬅️ 上一步", help="返回数据清洗页面", key="llm_prev_btn"):
            st.session_state.current_step = "数据清洗"
            st.rerun()
    with col3:
        if st.button("➡️ 下一步", help="前往结果查看页面", key="llm_next_btn"):
            st.session_state.current_step = "结果查看"
            st.rerun()


def test_api_connection(api_key):
    """测试API连接"""
    st.info("🔄 正在测试API连接...")
    
    try:
        from .api_clients import GPTBotsAPI
        
        # 创建API客户端
        client = GPTBotsAPI(api_key)
        
        # 发送测试消息
        test_query = "你好，这是一个连接测试。"
        result = client.call_agent(test_query)
        
        if result:
            st.success("✅ API连接测试成功！")
            st.info("🎉 GPTBots API工作正常，可以开始LLM处理")
            
            # 显示API响应示例
            with st.expander("查看API响应示例"):
                st.json(result)
                
        else:
            st.error("❌ API连接测试失败")
            st.warning("请检查API Key和网络连接")
            
    except Exception as e:
        st.error(f"❌ API测试出错: {str(e)}")
        st.warning("请确认API配置正确")


def start_llm_processing(api_key, delay, config):
    """开始LLM处理"""
    # 检查处理状态
    if st.session_state.llm_processing_state != "processing":
        return
    
    st.info("🚀 开始LLM处理...")
    log_activity("开始LLM处理")
    
    # 创建进度条
    progress_bar = st.progress(0)
    status_text = st.empty()
    result_container = st.empty()
    
    try:
        from .api_clients import GPTBotsAPI
        
        # 初始化API客户端
        status_text.text("🔍 初始化GPTBots API客户端...")
        client = GPTBotsAPI(api_key)
        
        # 获取待处理的Markdown文件
        processed_dir = Path(config["processed_dir"])
        md_files = list(processed_dir.glob("*.md"))
        
        # 过滤掉处理报告文件
        md_files = [f for f in md_files if f.name != "processing_report.json"]
        
        if not md_files:
            st.error("❌ 未找到待处理的Markdown文件")
            return
        
        progress_bar.progress(10)
        status_text.text(f"📧 发现 {len(md_files)} 个Markdown文件待处理...")
        
        # 更新session state中的总文件数
        st.session_state.llm_total_files = len(md_files)
        
        # LLM提示词模板
        llm_prompt_template = """
            以下是需要处理的邮件内容：

            {email_content}"""
            
        # 开始处理文件
        processed_files = []
        failed_files = []
        
        # 从上次暂停的位置继续处理
        start_index = st.session_state.llm_processed_count
        
        for i, md_file in enumerate(md_files):
            # 检查是否需要暂停
            if st.session_state.llm_processing_state != "processing":
                status_text.text("⏸️ 处理已暂停")
                return
            
            # 跳过已经处理过的文件（从暂停位置继续）
            if i < start_index:
                continue
                
            try:
                # 更新进度
                progress = 10 + (i / len(md_files)) * 80
                progress_bar.progress(int(progress))
                status_text.text(f"🤖 处理中: {md_file.name} ({i+1}/{len(md_files)})")
                
                # 更新session state中的当前进度
                st.session_state.llm_processed_count = i
                
                # 读取文件内容
                with open(md_file, 'r', encoding='utf-8') as f:
                    email_content = f.read()
                
                # 构建完整的提示词
                full_prompt = llm_prompt_template.format(email_content=email_content)
                
                # 调用LLM API
                result = client.call_agent(full_prompt)
                
                if result and "output" in result:
                    # 提取LLM响应内容
                    llm_response = extract_llm_content(result)
                    
                    if llm_response:
                        # 保存LLM处理结果
                        output_filename = f"llm_{md_file.name}"
                        output_path = Path(config["final_dir"]) / output_filename
                        
                        # 确保输出目录存在
                        output_path.parent.mkdir(parents=True, exist_ok=True)
                        
                        # 生成最终的Markdown内容
                        final_content = f"""# LLM处理结果 - {md_file.name}

## 🤖 AI提取的结构化信息

{llm_response}

---

## 📄 原始邮件内容

{email_content}

---
*LLM处理时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
*使用节点: {endpoint}*
*API Key: {api_key[:8]}...{api_key[-8:]}*
"""
                        
                        with open(output_path, 'w', encoding='utf-8') as f:
                            f.write(final_content)
                        
                        processed_files.append(output_filename)
                        
                        # 添加延迟避免API限流
                        if i < len(md_files) - 1:  # 不是最后一个文件
                            time.sleep(delay)
                    else:
                        failed_files.append(md_file.name)
                        st.warning(f"⚠️ {md_file.name} - 无法提取LLM响应内容")
                        
                else:
                    failed_files.append(md_file.name)
                    st.warning(f"⚠️ {md_file.name} - LLM处理失败")
                    
            except Exception as e:
                failed_files.append(md_file.name)
                st.error(f"❌ {md_file.name} - 处理出错: {str(e)}")
        
        # 显示处理结果
        progress_bar.progress(100)
        status_text.empty()
        
        # 处理完成，重置状态
        st.session_state.llm_processing_state = "idle"
        st.session_state.llm_processed_count = 0
        
        with result_container.container():
            st.success("🎉 LLM处理完成！")
            
            # 统计信息
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("输入文件", len(md_files))
            
            with col2:
                st.metric("处理成功", len(processed_files))
            
            with col3:
                st.metric("处理失败", len(failed_files))
            
            # 显示处理结果
            if processed_files:
                st.subheader("✅ 处理成功的文件")
                for filename in processed_files[:5]:  # 显示前5个
                    st.code(filename)
                if len(processed_files) > 5:
                    with st.expander(f"查看剩余 {len(processed_files) - 5} 个文件"):
                        for filename in processed_files[5:]:
                            st.code(filename)
            
            if failed_files:
                st.subheader("❌ 处理失败的文件")
                for filename in failed_files:
                    st.error(filename)
            
            # 输出位置
            st.subheader("📁 输出位置")
            st.success("📁 LLM处理结果保存至:")
            st.code(config["final_dir"])
            
            log_activity(f"LLM处理完成: {len(processed_files)}/{len(md_files)} 成功")
    
    except Exception as e:
        progress_bar.progress(0)
        status_text.empty()
        result_container.error(f"❌ LLM处理过程中发生错误: {str(e)}")
        # 出错时重置状态
        st.session_state.llm_processing_state = "idle"
        st.session_state.llm_processed_count = 0
        log_activity(f"LLM处理失败: {str(e)}")
        st.exception(e)


def extract_llm_content(result):
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
            return content.strip()
        
        # 备用提取方法
        return (result.get("answer") or 
                result.get("content") or 
                result.get("message") or
                None)
                
    except Exception as e:
        st.error(f"内容提取失败: {e}")
        return None
