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


@app.route('/api/delete-uploaded/<path:filename>', methods=['DELETE'])
def delete_uploaded_file(filename):
    """删除已上传的文件（支持批次路径）"""
    try:
        from urllib.parse import unquote
        
        # URL 解码文件名
        filename = unquote(filename)
        
        file_path = Path(UPLOAD_FOLDER) / filename
        if file_path.exists():
            file_path.unlink()
            log_activity(f"删除上传文件: {filename}")
            return jsonify({'success': True, 'message': '文件删除成功'})
        else:
            log_activity(f"文件不存在: {filename}, 路径: {file_path}")
            return jsonify({'success': False, 'error': '文件不存在'}), 404
    except Exception as e:
        log_activity(f"删除文件失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/delete-processed/<path:filename>', methods=['DELETE'])
def delete_processed_file(filename):
    """删除已去重的文件（支持批次路径）"""
    try:
        from urllib.parse import unquote
        
        # URL 解码文件名
        filename = unquote(filename)
        
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


@app.route('/api/delete-llm-processed/<path:filename>', methods=['DELETE'])
def delete_llm_processed_file(filename):
    """删除LLM处理的文件（支持批次路径）"""
    try:
        from urllib.parse import unquote
        
        # URL 解码文件名
        filename = unquote(filename)
        
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
    """上传EML文件 - 自动批次管理"""
    try:
        if 'files' not in request.files:
            return jsonify({'success': False, 'error': '没有文件'}), 400
        
        files = request.files.getlist('files')
        
        # 生成批次ID (精确到分钟)
        from datetime import datetime
        batch_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M')}"
        
        # 获取必填的批次标签
        batch_label = request.form.get('label', '').strip()
        if not batch_label:
            return jsonify({'success': False, 'error': '批次标签为必填项'}), 400
        
        # 创建批次目录
        batch_dir = Path(UPLOAD_FOLDER) / batch_id
        batch_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存文件
        uploaded_files = []
        file_details = []
        
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = batch_dir / filename
                file.save(str(filepath))
                uploaded_files.append(filename)
                
                file_details.append({
                    "filename": filename,
                    "size": filepath.stat().st_size,
                    "upload_time": datetime.now().isoformat()
                })
                log_activity(f"上传文件到批次 {batch_id}: {filename}")
        
        # 创建批次元数据
        batch_info = {
            "batch_id": batch_id,
            "upload_time": datetime.now().isoformat(),
            "file_count": len(uploaded_files),
            "custom_label": batch_label,
            "status": {
                "uploaded": True,
                "cleaned": False,
                "llm_processed": False,
                "uploaded_to_kb": False
            },
            "files": file_details,
            "processing_history": {}
        }
        
        # 保存批次元数据
        # batch_id 保持简单稳定，不包含标签和文件数
        # 标签和文件数仅存储在元数据中，用于前端展示
        batch_info_file = batch_dir / ".batch_info.json"
        with open(batch_info_file, 'w', encoding='utf-8') as f:
            import json
            json.dump(batch_info, f, ensure_ascii=False, indent=2)
        
        log_activity(f"批次创建完成: {batch_id}, {len(uploaded_files)} 个文件")
        
        return jsonify({
            'success': True,
            'batch_id': batch_id,
            'uploaded_files': uploaded_files,
            'count': len(uploaded_files)
        })
    except Exception as e:
        log_activity(f"上传失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/uploaded-files', methods=['GET'])
def get_uploaded_files():
    """获取已上传的文件列表（支持批次模式）"""
    try:
        upload_dir = Path(DIRECTORIES["upload_dir"])
        files = []
        
        # 检查是否有批次文件夹
        batch_dirs = [d for d in upload_dir.iterdir() if d.is_dir()]
        
        if batch_dirs:
            # 批次模式：从所有批次文件夹中收集文件
            for batch_dir in batch_dirs:
                batch_files = [f"{batch_dir.name}/{f.name}" for f in batch_dir.glob("*.eml")]
                files.extend(batch_files)
        else:
            # 非批次模式：直接从上传目录获取
            files = [f.name for f in upload_dir.glob("*.eml")]
        
        return jsonify({'success': True, 'files': files})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/processed-files', methods=['GET'])
def get_processed_files():
    """获取已去重的文件列表（支持批次模式）"""
    try:
        processed_dir = Path(DIRECTORIES["processed_dir"])
        files = []
        
        # 检查是否有批次文件夹
        batch_dirs = [d for d in processed_dir.iterdir() if d.is_dir()]
        
        if batch_dirs:
            # 批次模式：从所有批次文件夹中收集文件
            for batch_dir in batch_dirs:
                batch_files = [f"{batch_dir.name}/{f.name}" for f in batch_dir.glob("*.md")]
                files.extend(batch_files)
        else:
            # 非批次模式：直接从处理目录获取
            files = [f.name for f in processed_dir.glob("*.md")]
        
        return jsonify({'success': True, 'files': files})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/llm-processed-files', methods=['GET'])
def get_llm_processed_files():
    """获取LLM处理的文件列表（支持批次模式）"""
    try:
        final_dir = Path(DIRECTORIES["final_output_dir"])
        files = []
        
        # 检查是否有批次文件夹
        batch_dirs = [d for d in final_dir.iterdir() if d.is_dir()]
        
        if batch_dirs:
            # 批次模式：从所有批次文件夹中收集文件
            for batch_dir in batch_dirs:
                batch_files = [f"{batch_dir.name}/{f.name}" for f in batch_dir.glob("*.md")]
                files.extend(batch_files)
        else:
            # 非批次模式：直接从最终输出目录获取
            files = [f.name for f in final_dir.glob("*.md")]
        
        return jsonify({'success': True, 'files': files})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/file-content/uploaded/<path:filename>', methods=['GET'])
def get_uploaded_file_content(filename):
    """获取已上传文件的内容（支持批次路径）"""
    try:
        from urllib.parse import unquote
        
        # URL 解码文件名
        filename = unquote(filename)
        
        upload_dir = Path(DIRECTORIES["upload_dir"])
        file_path = upload_dir / filename
        
        if not file_path.exists():
            log_activity(f"文件不存在: {filename}, 路径: {file_path}")
            return jsonify({'success': False, 'error': '文件不存在'}), 404
        
        # 读取EML文件内容
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        return jsonify({'success': True, 'content': content})
    except Exception as e:
        log_activity(f"读取文件内容失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/file-content/processed/<path:filename>', methods=['GET'])
def get_processed_file_content(filename):
    """获取已去重文件的内容（支持批次路径）"""
    try:
        from urllib.parse import unquote
        
        # URL 解码文件名
        filename = unquote(filename)
        
        processed_dir = Path(DIRECTORIES["processed_dir"])
        file_path = processed_dir / filename
        
        if not file_path.exists():
            return jsonify({'success': False, 'error': '文件不存在'}), 404
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return jsonify({'success': True, 'content': content})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/file-content/llm-processed/<path:filename>', methods=['GET'])
def get_llm_processed_file_content(filename):
    """获取LLM处理文件的内容（支持批次路径）"""
    try:
        from urllib.parse import unquote
        
        # URL 解码文件名
        filename = unquote(filename)
        
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


# 辅助函数：更新批次状态
def update_batch_status_file(batch_id: str, status_key: str, status_value: bool = True):
    """更新批次状态到元数据文件"""
    try:
        from datetime import datetime
        import json
        
        upload_dir = Path(DIRECTORIES["upload_dir"])
        batch_dir = upload_dir / batch_id
        
        if not batch_dir.exists():
            log_activity(f"警告: 批次目录不存在: {batch_id}")
            return False
        
        batch_info_file = batch_dir / ".batch_info.json"
        if not batch_info_file.exists():
            log_activity(f"警告: 批次元数据不存在: {batch_id}")
            return False
        
        # 读取并更新元数据
        with open(batch_info_file, 'r', encoding='utf-8') as f:
            batch_info = json.load(f)
        
        # 更新状态
        if 'status' not in batch_info:
            batch_info['status'] = {}
        batch_info['status'][status_key] = status_value
        
        # 记录处理时间
        if 'processing_history' not in batch_info:
            batch_info['processing_history'] = {}
        if status_value:
            batch_info['processing_history'][f"{status_key}_at"] = datetime.now().isoformat()
        
        # 保存
        with open(batch_info_file, 'w', encoding='utf-8') as f:
            json.dump(batch_info, f, ensure_ascii=False, indent=2)
        
        log_activity(f"批次 {batch_id} 状态已更新: {status_key} = {status_value}")
        return True
    except Exception as e:
        log_activity(f"更新批次状态失败 {batch_id}: {str(e)}")
        return False


# 全自动处理流程API
@app.route('/api/auto/clean', methods=['POST'])
def auto_clean():
    """全自动流程 - 步骤1: 邮件清洗"""
    try:
        data = request.json
        batch_ids = data.get('batch_ids', [])
        skip_if_exists = data.get('skip_if_exists', True)  # 默认启用智能跳过
        
        upload_dir = Path(DIRECTORIES["upload_dir"])
        processed_dir = Path(DIRECTORIES["processed_dir"])
        
        # 智能跳过：检查是否已有处理后的文件
        if skip_if_exists and batch_ids:
            skipped_batches = []
            batches_to_process = []
            
            for batch_id in batch_ids:
                processed_batch_dir = processed_dir / batch_id
                if processed_batch_dir.exists():
                    md_files = list(processed_batch_dir.glob("*.md"))
                    if md_files:
                        log_activity(f"批次 {batch_id} 已有 {len(md_files)} 个处理后的文件，跳过清洗步骤")
                        skipped_batches.append(batch_id)
                        continue
                batches_to_process.append(batch_id)
            
            if not batches_to_process:
                log_activity(f"所有批次都已完成清洗，跳过此步骤")
                return jsonify({
                    'success': True,
                    'processed_count': 0,
                    'total_files': 0,
                    'duplicates': 0,
                    'skipped': True,
                    'skipped_batches': skipped_batches,
                    'message': '所有批次都已完成清洗，已跳过'
                })
            
            batch_ids = batches_to_process
            log_activity(f"将处理 {len(batch_ids)} 个批次，跳过 {len(skipped_batches)} 个已处理批次")
        
        if batch_ids:
            # 批次模式：只处理选中的批次
            log_activity(f"开始邮件清洗 (选中 {len(batch_ids)} 个批次): {batch_ids}")
            cleaner = EmailCleaner(input_dir=str(upload_dir), output_dir=str(processed_dir), batch_mode=True)
            result = cleaner.process_all_emails(selected_batches=batch_ids)
        else:
            # 非批次模式：处理所有文件
            log_activity(f"开始邮件清洗: {upload_dir}")
            cleaner = EmailCleaner(input_dir=str(upload_dir), output_dir=str(processed_dir))
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
        batch_ids = data.get('batch_ids', [])
        skip_if_exists = data.get('skip_if_exists', True)  # 默认启用智能跳过
        
        if not api_key:
            return jsonify({'success': False, 'error': '缺少API Key'}), 400
        
        processed_dir = Path(DIRECTORIES["processed_dir"])
        final_dir = Path(DIRECTORIES["final_output_dir"])
        final_dir.mkdir(parents=True, exist_ok=True)
        
        # 智能跳过：检查是否已有LLM处理后的文件
        if skip_if_exists and batch_ids:
            skipped_batches = []
            batches_to_process = []
            
            for batch_id in batch_ids:
                final_batch_dir = final_dir / batch_id
                if final_batch_dir.exists():
                    llm_files = list(final_batch_dir.glob("*.md"))
                    if llm_files:
                        log_activity(f"批次 {batch_id} 已有 {len(llm_files)} 个LLM处理后的文件，跳过LLM处理步骤")
                        skipped_batches.append(batch_id)
                        # 更新状态（如果尚未更新）
                        update_batch_status_file(batch_id, 'llm_processed', True)
                        continue
                batches_to_process.append(batch_id)
            
            if not batches_to_process:
                log_activity(f"所有批次都已完成LLM处理，跳过此步骤")
                return jsonify({
                    'success': True,
                    'processed_count': 0,
                    'failed_count': 0,
                    'skipped': True,
                    'skipped_batches': skipped_batches,
                    'message': '所有批次都已完成LLM处理，已跳过'
                })
            
            batch_ids = batches_to_process
            log_activity(f"将处理 {len(batch_ids)} 个批次，跳过 {len(skipped_batches)} 个已处理批次")
        
        # 获取所有markdown文件（支持批次模式）
        md_files = []
        
        # 检查是否有批次文件夹
        batch_dirs = [d for d in processed_dir.iterdir() if d.is_dir()]
        
        if batch_dirs:
            # 批次模式：从指定批次文件夹中收集文件
            if batch_ids:
                # 只处理选中的批次
                log_activity(f"LLM处理: 选中 {len(batch_ids)} 个批次")
                for batch_id in batch_ids:
                    batch_dir = processed_dir / batch_id
                    if batch_dir.exists() and batch_dir.is_dir():
                        batch_md_files = list(batch_dir.glob("*.md"))
                        batch_md_files = [f for f in batch_md_files if f.name != "processing_report.json"]
                        md_files.extend(batch_md_files)
                        log_activity(f"批次 {batch_id}: 找到 {len(batch_md_files)} 个文件")
            else:
                # 处理所有批次
                for batch_dir in batch_dirs:
                    batch_md_files = list(batch_dir.glob("*.md"))
                    batch_md_files = [f for f in batch_md_files if f.name != "processing_report.json"]
                    md_files.extend(batch_md_files)
        else:
            # 非批次模式：直接从处理目录获取
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
                        # 保存处理结果（保持批次目录结构）
                        # 检查文件是否在批次目录中
                        if md_file.parent != processed_dir:
                            # 批次模式：在final_dir中创建对应的批次目录
                            batch_name = md_file.parent.name
                            batch_final_dir = final_dir / batch_name
                            batch_final_dir.mkdir(parents=True, exist_ok=True)
                            output_file = batch_final_dir / md_file.name
                        else:
                            # 非批次模式：直接保存到final_dir
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
        
        # 更新批次状态
        if batch_ids and processed_count > 0:
            for batch_id in batch_ids:
                update_batch_status_file(batch_id, 'llm_processed', True)
        
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
        skip_if_exists = data.get('skip_if_exists', True)  # 默认启用智能跳过
        
        if not api_key or not kb_id:
            return jsonify({'success': False, 'error': '缺少必需参数'}), 400
        
        # 必须提供chunk_token或chunk_separator之一
        if not chunk_token and not chunk_separator:
            return jsonify({'success': False, 'error': '必须提供chunk_token或chunk_separator'}), 400
        
        batch_ids = data.get('batch_ids', [])
        
        # 智能跳过：检查批次状态
        if skip_if_exists and batch_ids:
            import json
            skipped_batches = []
            batches_to_process = []
            upload_dir = Path(DIRECTORIES["upload_dir"])
            
            for batch_id in batch_ids:
                batch_dir = upload_dir / batch_id
                batch_info_file = batch_dir / ".batch_info.json"
                
                if batch_info_file.exists():
                    try:
                        with open(batch_info_file, 'r', encoding='utf-8') as f:
                            batch_info = json.load(f)
                        
                        if batch_info.get('status', {}).get('uploaded_to_kb', False):
                            log_activity(f"批次 {batch_id} 已完成知识库上传，跳过上传步骤")
                            skipped_batches.append(batch_id)
                            continue
                    except Exception as e:
                        log_activity(f"读取批次元数据失败 {batch_id}: {str(e)}")
                
                batches_to_process.append(batch_id)
            
            if not batches_to_process:
                log_activity(f"所有批次都已完成知识库上传，跳过此步骤")
                return jsonify({
                    'success': True,
                    'uploaded_count': 0,
                    'skipped': True,
                    'skipped_batches': skipped_batches,
                    'message': '所有批次都已完成知识库上传，已跳过'
                })
            
            batch_ids = batches_to_process
            log_activity(f"将上传 {len(batch_ids)} 个批次，跳过 {len(skipped_batches)} 个已上传批次")
        
        final_dir = Path(DIRECTORIES["final_output_dir"])
        
        # 检查是否有批次文件夹
        batch_dirs = [d for d in final_dir.iterdir() if d.is_dir()]
        
        if batch_dirs:
            # 批次模式：收集指定批次中的文件
            md_files = []
            if batch_ids:
                # 只处理选中的批次
                log_activity(f"知识库上传: 选中 {len(batch_ids)} 个批次")
                for batch_id in batch_ids:
                    batch_dir = final_dir / batch_id
                    if batch_dir.exists() and batch_dir.is_dir():
                        batch_md_files = list(batch_dir.glob("*.md"))
                        md_files.extend(batch_md_files)
                        log_activity(f"批次 {batch_id}: 找到 {len(batch_md_files)} 个文件")
            else:
                # 处理所有批次
                for batch_dir in batch_dirs:
                    batch_md_files = list(batch_dir.glob("*.md"))
                    md_files.extend(batch_md_files)
        else:
            # 非批次模式：直接从final_dir获取
            md_files = list(final_dir.glob("*.md"))
        
        if not md_files:
            return jsonify({'success': False, 'error': '没有找到待上传的文件'}), 404
        
        kb_client = KnowledgeBaseAPI(api_key)
        
        # 批次模式需要逐个上传文件，非批次模式可以使用目录上传
        if batch_dirs:
            # 批次模式：逐个文件上传
            successful_uploads = 0
            failed_uploads = 0
            
            for md_file in md_files:
                try:
                    log_activity(f"上传文件到知识库: {md_file.name}")
                    
                    # 读取文件内容
                    with open(md_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # 构建上传参数
                    upload_params = {
                        'knowledge_base_id': kb_id,
                        'filename': md_file.name,  # 修正参数名
                        'content': content
                    }
                    
                    if chunk_token:
                        upload_params['chunk_token'] = chunk_token
                        upload_params['splitter'] = "PARAGRAPH"
                    else:
                        # upload_markdown_content 不支持 chunk_separator，使用默认的 chunk_token
                        upload_params['chunk_token'] = 600
                        upload_params['splitter'] = "PARAGRAPH"
                        log_activity(f"注意: 批次模式暂不支持自定义分隔符，使用默认Token分块(600)")
                    
                    # 上传单个文件
                    result = kb_client.upload_markdown_content(**upload_params)
                    
                    if result and 'error' not in result:
                        successful_uploads += 1
                        log_activity(f"成功上传: {md_file.name}")
                    else:
                        failed_uploads += 1
                        log_activity(f"上传失败: {md_file.name}, 错误: {result.get('error', '未知错误')}")
                    
                    # 延迟避免API限流
                    time.sleep(0.5)
                    
                except Exception as e:
                    failed_uploads += 1
                    log_activity(f"上传异常 {md_file.name}: {str(e)}")
            
            # 更新批次状态
            if batch_ids and successful_uploads > 0:
                for batch_id in batch_ids:
                    update_batch_status_file(batch_id, 'uploaded_to_kb', True)
            
            if successful_uploads > 0:
                return jsonify({
                    'success': True,
                    'uploaded_count': successful_uploads,
                    'message': f'知识库上传完成: 成功 {successful_uploads} 个，失败 {failed_uploads} 个'
                })
            else:
                return jsonify({'success': False, 'error': '所有文件上传失败'}), 500
        
        # 非批次模式：使用目录上传
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


# ========== 批次管理 API ==========

@app.route('/api/batches', methods=['GET'])
def get_batches():
    """获取所有批次列表"""
    try:
        upload_dir = Path(DIRECTORIES["upload_dir"])
        import json
        from datetime import datetime
        
        batches = []
        for batch_dir in sorted(upload_dir.iterdir(), key=lambda x: x.name, reverse=True):
            if not batch_dir.is_dir():
                continue
            
            # 读取批次元数据
            batch_info_file = batch_dir / ".batch_info.json"
            if batch_info_file.exists():
                with open(batch_info_file, 'r', encoding='utf-8') as f:
                    batch_info = json.load(f)
            else:
                # 如果没有元数据，生成基本信息（兼容旧数据）
                eml_files = list(batch_dir.glob("*.eml"))
                batch_info = {
                    "batch_id": batch_dir.name,
                    "upload_time": datetime.fromtimestamp(batch_dir.stat().st_mtime).isoformat(),
                    "file_count": len(eml_files),
                    "custom_label": "",
                    "status": {
                        "uploaded": True,
                        "cleaned": False,
                        "llm_processed": False,
                        "uploaded_to_kb": False
                    }
                }
            
            batches.append(batch_info)
        
        return jsonify({
            'success': True,
            'batches': batches,
            'total': len(batches)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/batches/<path:batch_id>', methods=['GET'])
def get_batch_details(batch_id):
    """获取特定批次的详细信息"""
    try:
        from urllib.parse import unquote
        
        # URL 解码批次ID
        batch_id = unquote(batch_id)
        
        upload_dir = Path(DIRECTORIES["upload_dir"])
        batch_dir = upload_dir / batch_id
        
        if not batch_dir.exists():
            log_activity(f"批次不存在: {batch_id}, 路径: {batch_dir}")
            return jsonify({'success': False, 'error': f'批次不存在: {batch_id}'}), 404
        
        # 读取批次元数据
        batch_info_file = batch_dir / ".batch_info.json"
        if batch_info_file.exists():
            with open(batch_info_file, 'r', encoding='utf-8') as f:
                import json
                batch_info = json.load(f)
        else:
            log_activity(f"批次元数据不存在: {batch_id}")
            return jsonify({'success': False, 'error': '批次元数据不存在'}), 404
        
        # 获取文件列表
        files = [f.name for f in batch_dir.glob("*.eml")]
        batch_info['current_files'] = files
        
        return jsonify({
            'success': True,
            'batch': batch_info
        })
    except Exception as e:
        log_activity(f"获取批次详情失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/batches/<path:batch_id>/status', methods=['PUT'])
def update_batch_status(batch_id):
    """更新批次状态"""
    try:
        from urllib.parse import unquote
        
        # URL 解码批次ID
        batch_id = unquote(batch_id)
        
        data = request.json
        status_key = data.get('status_key')  # cleaned, llm_processed, uploaded_to_kb
        status_value = data.get('status_value', True)
        
        upload_dir = Path(DIRECTORIES["upload_dir"])
        batch_dir = upload_dir / batch_id
        
        if not batch_dir.exists():
            return jsonify({'success': False, 'error': '批次不存在'}), 404
        
        batch_info_file = batch_dir / ".batch_info.json"
        if not batch_info_file.exists():
            return jsonify({'success': False, 'error': '批次元数据不存在'}), 404
        
        # 读取并更新元数据
        with open(batch_info_file, 'r', encoding='utf-8') as f:
            import json
            from datetime import datetime
            batch_info = json.load(f)
        
        # 更新状态
        if 'status' not in batch_info:
            batch_info['status'] = {}
        batch_info['status'][status_key] = status_value
        
        # 记录处理时间
        if 'processing_history' not in batch_info:
            batch_info['processing_history'] = {}
        if status_value:
            batch_info['processing_history'][f"{status_key}_at"] = datetime.now().isoformat()
        
        # 保存
        with open(batch_info_file, 'w', encoding='utf-8') as f:
            json.dump(batch_info, f, ensure_ascii=False, indent=2)
        
        return jsonify({'success': True, 'batch_info': batch_info})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/batches/<path:batch_id>/kb-label', methods=['PUT'])
def update_batch_kb_label(batch_id):
    """更新批次的知识库标签"""
    try:
        from urllib.parse import unquote
        
        # URL 解码批次ID
        batch_id = unquote(batch_id)
        
        data = request.json
        kb_name = data.get('kb_name', '').strip()
        
        if not kb_name:
            return jsonify({'success': False, 'error': '知识库名称不能为空'}), 400
        
        upload_dir = Path(DIRECTORIES["upload_dir"])
        batch_dir = upload_dir / batch_id
        
        if not batch_dir.exists():
            return jsonify({'success': False, 'error': '批次不存在'}), 404
        
        batch_info_file = batch_dir / ".batch_info.json"
        if not batch_info_file.exists():
            return jsonify({'success': False, 'error': '批次元数据不存在'}), 404
        
        # 读取并更新元数据
        with open(batch_info_file, 'r', encoding='utf-8') as f:
            import json
            from datetime import datetime
            batch_info = json.load(f)
        
        # 检查是否已完成上传到知识库
        if not batch_info.get('status', {}).get('uploaded_to_kb', False):
            return jsonify({'success': False, 'error': '该批次尚未完成知识库上传'}), 400
        
        # 更新知识库名称
        batch_info['kb_name'] = kb_name
        batch_info['kb_labeled_at'] = datetime.now().isoformat()
        
        # 保存
        with open(batch_info_file, 'w', encoding='utf-8') as f:
            json.dump(batch_info, f, ensure_ascii=False, indent=2)
        
        log_activity(f"批次 {batch_id} 标记知识库: {kb_name}")
        
        return jsonify({'success': True, 'batch_info': batch_info})
    except Exception as e:
        log_activity(f"更新知识库标签失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/batches/<path:batch_id>', methods=['DELETE'])
def delete_batch(batch_id):
    """删除整个批次"""
    try:
        from urllib.parse import unquote
        import shutil
        
        # URL 解码批次ID
        batch_id = unquote(batch_id)
        
        # 删除上传目录中的批次
        upload_dir = Path(DIRECTORIES["upload_dir"])
        batch_dir = upload_dir / batch_id
        if batch_dir.exists():
            shutil.rmtree(batch_dir)
        
        # 删除处理目录中的批次
        processed_dir = Path(DIRECTORIES["processed_dir"])
        processed_batch_dir = processed_dir / batch_id
        if processed_batch_dir.exists():
            shutil.rmtree(processed_batch_dir)
        
        # 删除最终输出目录中的批次
        final_dir = Path(DIRECTORIES["final_output_dir"])
        final_batch_dir = final_dir / batch_id
        if final_batch_dir.exists():
            shutil.rmtree(final_batch_dir)
        
        log_activity(f"删除批次: {batch_id}")
        
        return jsonify({'success': True, 'message': f'批次 {batch_id} 已删除'})
    except Exception as e:
        log_activity(f"删除批次失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    import time
    print("=" * 60)
    print("Email Processing API Server - Starting...")
    print("=" * 60)
    print("Server Address: http://localhost:5001")
    print("Frontend Address: http://localhost:3000")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5001, debug=True)

