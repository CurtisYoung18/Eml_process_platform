#!/usr/bin/env python3
"""
Flask API服务器
为前端React应用提供API接口，对接现有的tools模块
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
from pathlib import Path
import glob
from dotenv import dotenv_values

# 导入现有的工具模块
from tools.utils import count_files, log_activity
from tools.email_processing.email_cleaner import EmailCleaner
# from tools.data_cleaning import clean_email_files  # 包含streamlit依赖，不导入
# from tools.llm_processing import process_with_llm  # 包含streamlit依赖，不导入
from tools.api_clients.knowledge_base_api import KnowledgeBaseAPI
from tools.api_clients.gptbots_api import GPTBotsAPI
from config import DIRECTORIES, init_directories

app = Flask(__name__)
# 配置CORS - 允许所有来源访问所有路由
CORS(app, 
     resources={r"/*": {"origins": "*"}},
     allow_headers=["Content-Type", "Authorization"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     supports_credentials=False)

# 初始化目录
init_directories()

# 配置上传
UPLOAD_FOLDER = DIRECTORIES["upload_dir"]
ALLOWED_EXTENSIONS = {'eml'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/api/config/env', methods=['GET'])
def get_env_config():
    """获取环境变量配置"""
    try:
        env_path = Path(__file__).parent / '.env'
        if not env_path.exists():
            return jsonify({'success': False, 'error': '.env文件不存在'}), 404
        
        env_vars = dotenv_values(env_path)
        
        # 提取LLM API Keys
        llm_keys = []
        for i in range(1, 4):
            key = env_vars.get(f'GPTBOTS_LLM_API_KEY_{i}')
            if key:
                llm_keys.append({
                    'id': f'llm_key_{i}',
                    'name': f'LLM API Key {i}',
                    'value': key,
                    'masked': key[:8] + '...' + key[-4:] if len(key) > 12 else key
                })
        
        # 提取知识库 API Keys
        kb_keys = []
        for i in range(1, 4):
            key = env_vars.get(f'GPTBOTS_KB_API_KEY_{i}')
            if key:
                kb_keys.append({
                    'id': f'kb_key_{i}',
                    'name': f'知识库 API Key {i}',
                    'value': key,
                    'masked': key[:8] + '...' + key[-4:] if len(key) > 12 else key
                })
        
        config = {
            'llm_api_keys': llm_keys,
            'kb_api_keys': kb_keys,
            'default_llm_key': env_vars.get('GPTBOTS_LLM_API_KEY_1', ''),
            'default_kb_key': env_vars.get('GPTBOTS_KB_API_KEY_1', ''),
        }
        
        return jsonify({'success': True, 'config': config})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/knowledge-bases', methods=['POST'])
def fetch_knowledge_bases():
    """获取知识库列表"""
    try:
        data = request.json
        api_key = data.get('api_key')
        
        if not api_key:
            return jsonify({'success': False, 'error': '缺少API Key'}), 400
        
        kb_client = KnowledgeBaseAPI(api_key)
        knowledge_bases = kb_client.list_knowledge_bases()
        
        if knowledge_bases:
            return jsonify({
                'success': True,
                'knowledge_bases': knowledge_bases
            })
        else:
            # 返回更友好的错误信息
            return jsonify({
                'success': False, 
                'error': '无法获取知识库列表，请检查API Key是否正确或是否有权限访问知识库'
            }), 200  # 改为200状态码，让前端能正确处理
            
    except Exception as e:
        log_activity(f"获取知识库列表异常: {str(e)}")
        return jsonify({
            'success': False, 
            'error': f'获取知识库列表失败: {str(e)}'
        }), 200  # 改为200状态码


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """获取系统统计信息"""
    try:
        # 知识库文档数 = LLM处理完成的文件数（这些文件应该已上传到知识库）
        llm_processed_count = count_files(DIRECTORIES["final_output_dir"], "*.md")
        
        stats = {
            'uploaded': count_files(DIRECTORIES["upload_dir"], "*.eml"),
            'cleaned': count_files(DIRECTORIES["processed_dir"], "*.md"),
            'processed': llm_processed_count,
            'inKnowledgeBase': llm_processed_count  # 已LLM处理的文件即为上传到知识库的文件
        }
        return jsonify({'success': True, 'stats': stats})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/delete-uploaded/<filename>', methods=['DELETE'])
def delete_uploaded_file(filename):
    """删除已上传的文件"""
    try:
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            log_activity(f"删除上传文件: {filename}")
            return jsonify({'success': True, 'message': '文件删除成功'})
        else:
            return jsonify({'success': False, 'error': '文件不存在'}), 404
    except Exception as e:
        log_activity(f"删除文件失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/delete-processed/<filename>', methods=['DELETE'])
def delete_processed_file(filename):
    """删除已去重的文件"""
    try:
        processed_dir = Path(DIRECTORIES["processed_dir"])
        file_path = processed_dir / filename
        if file_path.exists():
            file_path.unlink()
            log_activity(f"删除去重文件: {filename}")
            return jsonify({'success': True, 'message': '文件删除成功'})
        else:
            return jsonify({'success': False, 'error': '文件不存在'}), 404
    except Exception as e:
        log_activity(f"删除文件失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/delete-llm-processed/<filename>', methods=['DELETE'])
def delete_llm_processed_file(filename):
    """删除LLM处理的文件"""
    try:
        final_dir = Path(DIRECTORIES["final_output_dir"])
        file_path = final_dir / filename
        if file_path.exists():
            file_path.unlink()
            log_activity(f"删除LLM处理文件: {filename}")
            return jsonify({'success': True, 'message': '文件删除成功'})
        else:
            return jsonify({'success': False, 'error': '文件不存在'}), 404
    except Exception as e:
        log_activity(f"删除文件失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/upload', methods=['POST'])
def upload_files():
    """上传EML文件"""
    try:
        if 'files' not in request.files:
            return jsonify({'success': False, 'error': '没有文件'}), 400
        
        files = request.files.getlist('files')
        uploaded_files = []
        
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                file.save(filepath)
                uploaded_files.append(filename)
                log_activity(f"上传文件: {filename}")
        
        return jsonify({
            'success': True,
            'uploaded_files': uploaded_files,
            'count': len(uploaded_files)
        })
    except Exception as e:
        log_activity(f"上传失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/uploaded-files', methods=['GET'])
def get_uploaded_files():
    """获取已上传的文件列表"""
    try:
        upload_dir = Path(DIRECTORIES["upload_dir"])
        files = [f.name for f in upload_dir.glob("*.eml")]
        return jsonify({'success': True, 'files': files})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/processed-files', methods=['GET'])
def get_processed_files():
    """获取已去重的文件列表"""
    try:
        processed_dir = Path(DIRECTORIES["processed_dir"])
        files = [f.name for f in processed_dir.glob("*.md")]
        return jsonify({'success': True, 'files': files})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/llm-processed-files', methods=['GET'])
def get_llm_processed_files():
    """获取LLM处理的文件列表"""
    try:
        final_dir = Path(DIRECTORIES["final_output_dir"])
        files = [f.name for f in final_dir.glob("*.md")]
        return jsonify({'success': True, 'files': files})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/file-content/uploaded/<filename>', methods=['GET'])
def get_uploaded_file_content(filename):
    """获取已上传文件的内容"""
    try:
        upload_dir = Path(DIRECTORIES["upload_dir"])
        file_path = upload_dir / filename
        
        if not file_path.exists():
            return jsonify({'success': False, 'error': '文件不存在'}), 404
        
        # 读取EML文件内容
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        return jsonify({'success': True, 'content': content})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/file-content/processed/<filename>', methods=['GET'])
def get_processed_file_content(filename):
    """获取已去重文件的内容"""
    try:
        processed_dir = Path(DIRECTORIES["processed_dir"])
        file_path = processed_dir / filename
        
        if not file_path.exists():
            return jsonify({'success': False, 'error': '文件不存在'}), 404
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return jsonify({'success': True, 'content': content})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/file-content/llm-processed/<filename>', methods=['GET'])
def get_llm_processed_file_content(filename):
    """获取LLM处理文件的内容"""
    try:
        final_dir = Path(DIRECTORIES["final_output_dir"])
        file_path = final_dir / filename
        
        if not file_path.exists():
            return jsonify({'success': False, 'error': '文件不存在'}), 404
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return jsonify({'success': True, 'content': content})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/clean', methods=['POST'])
def clean_files():
    """清洗邮件文件"""
    try:
        data = request.json
        files = data.get('files', [])
        
        if not files:
            return jsonify({'success': False, 'error': '没有文件需要清洗'}), 400
        
        # 使用EmailCleaner批量处理
        cleaner = EmailCleaner(
            input_dir=DIRECTORIES["upload_dir"],
            output_dir=DIRECTORIES["processed_dir"]
        )
        
        # 执行清洗
        result = cleaner.process_all_emails()
        
        if result.get("success"):
            processed_count = len(result.get("generated_files", []))
            log_activity(f"批量清洗完成: {processed_count} 个文件")
            return jsonify({
                'success': True,
                'processed_files': [Path(f).name for f in result.get("generated_files", [])],
                'count': processed_count,
                'report': result.get("report")
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get("message", "清洗失败")
            }), 500
            
    except Exception as e:
        log_activity(f"清洗过程失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/cleaned-files', methods=['GET'])
def get_cleaned_files():
    """获取已清洗的文件列表"""
    try:
        processed_dir = Path(DIRECTORIES["processed_dir"])
        files = [f.name for f in processed_dir.glob("*.md")]
        return jsonify({'success': True, 'files': files})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/llm-process', methods=['POST'])
def llm_process():
    """LLM处理文件"""
    try:
        data = request.json
        files = data.get('files', [])
        api_key = data.get('api_key')
        endpoint = data.get('endpoint', 'internal')
        delay = data.get('delay', 2)
        
        if not files or not api_key:
            return jsonify({'success': False, 'error': '缺少必要参数'}), 400
        
        # 初始化API客户端
        api_client = GPTBotsAPI(api_key)
        
        processed_files = []
        errors = []
        
        for filename in files:
            input_path = os.path.join(DIRECTORIES["processed_dir"], filename)
            output_path = os.path.join(DIRECTORIES["final_output_dir"], filename)
            
            try:
                # 读取文件内容
                with open(input_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 创建对话
                conversation_id = api_client.create_conversation()
                if not conversation_id:
                    raise Exception("创建对话失败")
                
                # 发送内容到LLM处理
                result = api_client.send_message(conversation_id, content)
                
                if result and result.get('answer'):
                    # 保存处理后的内容
                    processed_content = result['answer']
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(processed_content)
                    
                    processed_files.append(filename)
                    log_activity(f"LLM处理文件: {filename}")
                else:
                    raise Exception("LLM未返回有效响应")
                
                # 延迟避免限流
                import time
                time.sleep(delay)
                
            except Exception as e:
                error_msg = f"处理失败: {filename} - {str(e)}"
                errors.append(error_msg)
                log_activity(f"LLM{error_msg}")
        
        return jsonify({
            'success': len(processed_files) > 0,
            'processed_files': processed_files,
            'count': len(processed_files),
            'errors': errors
        })
    except Exception as e:
        log_activity(f"LLM处理过程失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/results', methods=['GET'])
def get_results():
    """获取所有处理结果"""
    try:
        results = []
        
        # 获取所有阶段的文件
        upload_dir = Path(DIRECTORIES["upload_dir"])
        processed_dir = Path(DIRECTORIES["processed_dir"])
        final_dir = Path(DIRECTORIES["final_output_dir"])
        
        # LLM处理完成的文件
        for f in final_dir.glob("*.md"):
            results.append({
                'filename': f.name,
                'stage': 'llm_processed',
                'size': f'{f.stat().st_size / 1024:.2f} KB',
                'processed_time': None
            })
        
        # 只清洗的文件
        for f in processed_dir.glob("*.md"):
            if not (final_dir / f.name).exists():
                results.append({
                    'filename': f.name,
                    'stage': 'cleaned',
                    'size': f'{f.stat().st_size / 1024:.2f} KB',
                    'processed_time': None
                })
        
        return jsonify({'success': True, 'results': results})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/file-content', methods=['GET'])
def get_file_content():
    """获取文件内容"""
    try:
        filename = request.args.get('file')
        if not filename:
            return jsonify({'success': False, 'error': '缺少文件名'}), 400
        
        # 尝试从各个目录查找文件
        for dir_path in [DIRECTORIES["final_output_dir"], DIRECTORIES["processed_dir"], DIRECTORIES["upload_dir"]]:
            filepath = Path(dir_path) / filename
            if filepath.exists():
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                return jsonify({'success': True, 'content': content})
        
        return jsonify({'success': False, 'error': '文件不存在'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/download', methods=['GET'])
def download_file():
    """下载文件"""
    try:
        filename = request.args.get('file')
        if not filename:
            return jsonify({'success': False, 'error': '缺少文件名'}), 400
        
        # 尝试从各个目录查找文件
        for dir_path in [DIRECTORIES["final_output_dir"], DIRECTORIES["processed_dir"], DIRECTORIES["upload_dir"]]:
            filepath = Path(dir_path) / filename
            if filepath.exists():
                return send_file(filepath, as_attachment=True)
        
        return jsonify({'success': False, 'error': '文件不存在'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/knowledge-bases', methods=['POST'])
def get_knowledge_bases():
    """获取知识库列表"""
    try:
        data = request.json
        api_key = data.get('api_key')
        
        if not api_key:
            return jsonify({'success': False, 'error': '缺少API Key'}), 400
        
        kb_api = KnowledgeBaseAPI(api_key)
        response = kb_api.get_knowledge_bases()
        
        if response and 'data' in response and 'list' in response['data']:
            knowledge_bases = response['data']['list']
            return jsonify({
                'success': True,
                'knowledge_bases': knowledge_bases
            })
        else:
            return jsonify({'success': False, 'error': '获取知识库列表失败'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/upload-to-kb', methods=['POST'])
def upload_to_knowledge_base():
    """上传文件到知识库"""
    try:
        data = request.json
        files = data.get('files', [])
        api_key = data.get('api_key')
        knowledge_base_id = data.get('knowledge_base_id', '')
        chunk_token = data.get('chunk_token', 600)
        
        if not files or not api_key:
            return jsonify({'success': False, 'error': '缺少必要参数'}), 400
        
        kb_api = KnowledgeBaseAPI(api_key)
        uploaded_count = 0
        
        for filename in files:
            filepath = os.path.join(DIRECTORIES["final_output_dir"], filename)
            
            if not os.path.exists(filepath):
                log_activity(f"文件不存在: {filename}")
                continue
            
            try:
                # 上传到知识库
                result = kb_api.upload_file(
                    filepath,
                    knowledge_base_id=knowledge_base_id,
                    chunk_token=chunk_token
                )
                
                if result:
                    uploaded_count += 1
                    log_activity(f"上传到知识库: {filename}")
                    
            except Exception as e:
                log_activity(f"上传知识库失败: {filename} - {str(e)}")
        
        return jsonify({
            'success': True,
            'uploaded_count': uploaded_count
        })
    except Exception as e:
        log_activity(f"知识库上传过程失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/qa-chat', methods=['POST'])
def qa_chat():
    """问答聊天"""
    try:
        data = request.json
        message = data.get('message')
        api_key = data.get('api_key')
        conversation_id = data.get('conversation_id', '')
        
        if not message or not api_key:
            return jsonify({'success': False, 'error': '缺少必要参数'}), 400
        
        # 初始化GPTBots API
        api_client = GPTBotsAPI(api_key)
        
        # 如果没有conversation_id，先创建
        if not conversation_id:
            conversation_id = api_client.create_conversation()
            if not conversation_id:
                return jsonify({'success': False, 'error': '创建对话失败'}), 500
        
        # 发送消息并获取回复
        response = api_client.send_message(conversation_id, message)
        
        if response and 'answer' in response:
            return jsonify({
                'success': True,
                'reply': response['answer'],
                'conversation_id': conversation_id
            })
        else:
            return jsonify({'success': False, 'error': 'API响应异常'}), 500
            
    except Exception as e:
        log_activity(f"QA聊天失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({'status': 'ok'})


# 全自动处理流程API
@app.route('/api/auto/clean', methods=['POST'])
def auto_clean():
    """全自动流程 - 步骤1: 邮件清洗"""
    try:
        upload_dir = DIRECTORIES["upload_dir"]
        processed_dir = DIRECTORIES["processed_dir"]
        
        log_activity(f"开始邮件清洗: {upload_dir}")
        cleaner = EmailCleaner(input_dir=upload_dir, output_dir=processed_dir)
        result = cleaner.process_all_emails()
        
        if result.get('success'):
            # 从report中获取处理数量
            report = result.get('report', {})
            processed_count = report.get('unique_emails', len(result.get('generated_files', [])))
            log_activity(f"邮件清洗完成: {processed_count} 个文件")
            
            return jsonify({
                'success': True,
                'processed_count': processed_count,
                'total_files': report.get('total_input_files', 0),
                'duplicates': report.get('duplicate_emails', 0),
                'message': '邮件清洗完成'
            })
        else:
            error_msg = result.get('message', '邮件清洗失败')
            log_activity(f"邮件清洗失败: {error_msg}")
            return jsonify({'success': False, 'error': error_msg})
            
    except Exception as e:
        log_activity(f"邮件清洗异常: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/auto/llm-process', methods=['POST'])
def auto_llm_process():
    """全自动流程 - 步骤2: LLM处理"""
    try:
        data = request.json
        api_key = data.get('api_key')
        delay = data.get('delay', 2)
        
        if not api_key:
            return jsonify({'success': False, 'error': '缺少API Key'}), 400
        
        processed_dir = Path(DIRECTORIES["processed_dir"])
        final_dir = Path(DIRECTORIES["final_output_dir"])
        final_dir.mkdir(parents=True, exist_ok=True)
        
        # 获取所有markdown文件，排除报告文件
        md_files = list(processed_dir.glob("*.md"))
        md_files = [f for f in md_files if f.name != "processing_report.json"]
        
        if not md_files:
            return jsonify({'success': False, 'error': '没有找到待处理的文件'}), 404
        
        # 初始化GPTBots API客户端
        client = GPTBotsAPI(api_key)
        processed_count = 0
        failed_count = 0
        
        # LLM提示词模板
        llm_prompt_template = """以下是需要处理的邮件内容，请帮我整理和优化：

{email_content}"""
        
        for md_file in md_files:
            try:
                log_activity(f"处理文件: {md_file.name}")
                
                # 读取文件内容
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 创建对话
                conversation_id = client.create_conversation()
                if not conversation_id:
                    log_activity(f"创建对话失败: {md_file.name}")
                    failed_count += 1
                    continue
                
                # 发送消息
                prompt = llm_prompt_template.format(email_content=content)
                response = client.send_message(conversation_id, prompt)
                
                if response and "output" in response:
                    # 提取LLM处理结果
                    output_list = response.get("output", [])
                    processed_content = ""
                    
                    for output_item in output_list:
                        if "content" in output_item:
                            content_obj = output_item["content"]
                            if "text" in content_obj:
                                processed_content += content_obj["text"] + "\n"
                    
                    if processed_content.strip():
                        # 保存处理结果
                        output_file = final_dir / md_file.name
                        with open(output_file, 'w', encoding='utf-8') as f:
                            f.write(processed_content.strip())
                        
                        processed_count += 1
                        log_activity(f"成功处理: {md_file.name}")
                    else:
                        log_activity(f"LLM返回空内容: {md_file.name}")
                        failed_count += 1
                else:
                    log_activity(f"LLM调用失败: {md_file.name}")
                    failed_count += 1
                
                # 延迟避免API限流
                time.sleep(delay)
                
            except Exception as e:
                log_activity(f"处理文件异常 {md_file.name}: {str(e)}")
                failed_count += 1
                continue
        
        if processed_count > 0:
            return jsonify({
                'success': True,
                'processed_count': processed_count,
                'failed_count': failed_count,
                'message': f'LLM处理完成: 成功 {processed_count} 个，失败 {failed_count} 个'
            })
        else:
            error_msg = f'LLM处理失败: 所有文件处理失败。请检查API Key是否正确，是否有对话权限'
            log_activity(error_msg)
            return jsonify({
                'success': False,
                'processed_count': 0,
                'failed_count': failed_count,
                'error': error_msg
            })
    except Exception as e:
        log_activity(f"LLM处理异常: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/auto/upload-kb', methods=['POST'])
def auto_upload_kb():
    """全自动流程 - 步骤3: 上传到知识库"""
    try:
        data = request.json
        api_key = data.get('api_key')
        kb_id = data.get('knowledge_base_id')
        chunk_token = data.get('chunk_token')
        chunk_separator = data.get('chunk_separator')
        batch_size = data.get('batch_size', 10)
        
        if not api_key or not kb_id:
            return jsonify({'success': False, 'error': '缺少必需参数'}), 400
        
        # 必须提供chunk_token或chunk_separator之一
        if not chunk_token and not chunk_separator:
            return jsonify({'success': False, 'error': '必须提供chunk_token或chunk_separator'}), 400
        
        final_dir = Path(DIRECTORIES["final_output_dir"])
        md_files = list(final_dir.glob("*.md"))
        
        if not md_files:
            return jsonify({'success': False, 'error': '没有找到待上传的文件'}), 404
        
        kb_client = KnowledgeBaseAPI(api_key)
        
        # 根据分块方式构建参数
        upload_params = {
            'directory_path': str(final_dir),
            'knowledge_base_id': kb_id,
            'batch_size': batch_size
        }
        
        if chunk_token:
            upload_params['chunk_token'] = chunk_token
            upload_params['splitter'] = "PARAGRAPH"
        else:
            upload_params['chunk_separator'] = chunk_separator
            upload_params['splitter'] = "CUSTOM"
        
        result = kb_client.upload_markdown_files_from_directory(**upload_params)
        
        if result and 'error' not in result:
            return jsonify({
                'success': True,
                'uploaded_count': result.get('successful_uploads', 0),
                'message': '知识库上传完成'
            })
        else:
            return jsonify({'success': False, 'error': result.get('error', '上传失败')}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    import time
    print("🚀 启动邮件处理API服务器...")
    print("📍 服务地址: http://localhost:5001")
    print("💡 前端地址: http://localhost:3000")
    app.run(host='0.0.0.0', port=5001, debug=True)

