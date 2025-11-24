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
import traceback
import json
import time
from datetime import datetime
import random
import string
import shutil

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

# 配置上传大小限制
max_content_mb = int(os.getenv('MAX_CONTENT_LENGTH', '2000'))
app.config['MAX_CONTENT_LENGTH'] = max_content_mb * 1024 * 1024  # 转换为字节

# 初始化目录
init_directories()

# 配置上传
UPLOAD_FOLDER = DIRECTORIES["upload_dir"]
ALLOWED_EXTENSIONS = {'eml'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_disk_usage():
    """获取当前磁盘使用情况"""
    try:
        import psutil
        # 获取当前工作目录所在的磁盘分区
        current_path = os.getcwd()
        disk_usage = psutil.disk_usage(current_path)
        
        total_gb = disk_usage.total / (1024 ** 3)
        used_gb = disk_usage.used / (1024 ** 3)
        free_gb = disk_usage.free / (1024 ** 3)
        percent = disk_usage.percent
        
        return {
            'total_gb': round(total_gb, 2),
            'used_gb': round(used_gb, 2),
            'free_gb': round(free_gb, 2),
            'percent': percent,
            'status': 'warning' if percent > 85 else 'critical' if percent > 95 else 'normal'
        }
    except ImportError:
        # psutil未安装，使用shutil作为备选方案
        try:
            import shutil
            current_path = os.getcwd()
            disk_stat = shutil.disk_usage(current_path)
            
            total_gb = disk_stat.total / (1024 ** 3)
            used_gb = disk_stat.used / (1024 ** 3)
            free_gb = disk_stat.free / (1024 ** 3)
            percent = (disk_stat.used / disk_stat.total) * 100
            
            return {
                'total_gb': round(total_gb, 2),
                'used_gb': round(used_gb, 2),
                'free_gb': round(free_gb, 2),
                'percent': round(percent, 2),
                'status': 'warning' if percent > 85 else 'critical' if percent > 95 else 'normal'
            }
        except Exception as e:
            return {
                'error': str(e),
                'status': 'unknown'
            }
    except Exception as e:
        return {
            'error': str(e),
            'status': 'unknown'
        }

def log_disk_usage(prefix=""):
    """记录磁盘使用情况到日志"""
    disk_info = get_disk_usage()
    if 'error' not in disk_info:
        status_emoji = "⚠️" if disk_info['status'] == 'warning' else "🔴" if disk_info['status'] == 'critical' else "💾"
        log_activity(
            f"{prefix}{status_emoji} Disk usage: {disk_info['used_gb']:.2f}GB / {disk_info['total_gb']:.2f}GB "
            f"({disk_info['percent']:.1f}%) | Free: {disk_info['free_gb']:.2f}GB"
        )
        return disk_info
    else:
        log_activity(f"{prefix}⚠️ Unable to get disk usage: {disk_info['error']}")
        return None


@app.route('/api/config/env', methods=['GET'])
def get_env_config():
    """获取环境变量配置"""
    try:
        # 尝试多个可能的.env文件位置
        possible_paths = [
            Path(__file__).parent / '.env',  # 与api_server.py同目录
            Path.cwd() / '.env',  # 当前工作目录
            Path(__file__).parent.parent / '.env',  # 父目录
        ]
        
        env_path = None
        for path in possible_paths:
            log_activity(f"Trying to read .env file: {path.absolute()}")
            if path.exists():
                env_path = path
                log_activity(f"✅ Found .env file: {path.absolute()}")
                break
        
        if not env_path:
            error_msg = f'.env file not found. Attempted paths:\n' + '\n'.join([f'  - {p.absolute()}' for p in possible_paths])
            log_activity(f"❌ {error_msg}")
            return jsonify({
                'success': False, 
                'error': '.env文件不存在',
                'details': error_msg,
                'cwd': str(Path.cwd().absolute()),
                'script_dir': str(Path(__file__).parent.absolute())
            }), 404
        
        env_vars = dotenv_values(env_path)
        log_activity(f"Successfully read .env file, {len(env_vars)} variables")
        
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
        
        log_activity(f"Returning config: {len(llm_keys)} LLM Keys, {len(kb_keys)} KB Keys")
        return jsonify({'success': True, 'config': config})
    except Exception as e:
        error_msg = f'Error reading environment config: {str(e)}'
        log_activity(error_msg)
        return jsonify({
            'success': False, 
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


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
                'error': '无法获取知识库列表，请检查API Key是否正确、网络连接是否正常，或知识库服务是否可访问'
            }), 200  # 改为200状态码，让前端能正确处理
            
    except Exception as e:
        error_msg = str(e)
        # 检查是否是连接超时错误
        if 'timeout' in error_msg.lower() or 'Connection' in error_msg:
            error_msg = '无法连接到知识库服务，请检查网络连接或服务地址配置'
        elif 'Max retries exceeded' in error_msg:
            error_msg = '知识库服务连接超时，请检查服务是否正常运行'
        
        log_activity(f"Error getting knowledge base list: {error_msg}")
        return jsonify({
            'success': False, 
            'error': f'获取知识库列表失败: {error_msg}'
        }), 200  # 改为200状态码，让前端能正确处理


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
            log_activity(f"Deleted upload file: {filename}")
            return jsonify({'success': True, 'message': '文件删除成功'})
        else:
            log_activity(f"文件不存在: {filename}, 路径: {file_path}")
            return jsonify({'success': False, 'error': '文件不存在'}), 404
    except Exception as e:
        log_activity(f"Failed to delete file: {str(e)}")
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
            log_activity(f"Deleted deduplicated file: {filename}")
            return jsonify({'success': True, 'message': '文件删除成功'})
        else:
            return jsonify({'success': False, 'error': '文件不存在'}), 404
    except Exception as e:
        log_activity(f"Failed to delete file: {str(e)}")
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
            log_activity(f"Deleted LLM processed file: {filename}")
            return jsonify({'success': True, 'message': '文件删除成功'})
        else:
            return jsonify({'success': False, 'error': '文件不存在'}), 404
    except Exception as e:
        log_activity(f"Failed to delete file: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/check-duplicates', methods=['GET'])
def check_duplicates():
    """检查哪些文件是重复的（检查所有已上传的邮件）"""
    try:
        filenames_str = request.args.get('filenames', '')
        if not filenames_str:
            return jsonify({'success': True, 'duplicates': []})
        
        filenames = filenames_str.split(',')
        
        # 收集所有批次中已上传的邮件文件名
        upload_dir = Path(DIRECTORIES["upload_dir"])
        existing_files = set()
        
        # 检查所有批次目录
        if upload_dir.exists():
            for batch_dir in upload_dir.iterdir():
                if batch_dir.is_dir() and batch_dir.name.startswith('batch_'):
                    # 收集该批次中的所有.eml文件
                    for eml_file in batch_dir.glob('*.eml'):
                        existing_files.add(eml_file.name)
        
        # 找出重复的文件名（已在其他批次中上传过）
        duplicates = [fname for fname in filenames if fname in existing_files]
        
        return jsonify({
            'success': True,
            'duplicates': duplicates
        })
    except Exception as e:
        log_activity(f"Error checking duplicate files: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/upload', methods=['POST'])
def upload_files():
    """上传EML文件 - 自动批次管理"""
    try:
        if 'files' not in request.files:
            return jsonify({'success': False, 'error': '没有文件'}), 400
        
        files = request.files.getlist('files')
        
        # 生成批次ID (精确到秒 + 随机后缀，确保唯一性)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
        batch_id = f"batch_{timestamp}_{random_suffix}"
        
        # 获取必填的批次标签
        batch_label = request.form.get('label', '').strip()
        if not batch_label:
            return jsonify({'success': False, 'error': '批次标签为必填项'}), 400
        
        # 检查所有批次中已上传的文件
        upload_dir = Path(UPLOAD_FOLDER)
        existing_files = {}  # {filename: batch_id}
        
        if upload_dir.exists():
            for existing_batch_dir in upload_dir.iterdir():
                if existing_batch_dir.is_dir() and existing_batch_dir.name.startswith('batch_'):
                    # 收集所有已上传的.eml文件
                    for eml_file in existing_batch_dir.glob('*.eml'):
                        existing_files[eml_file.name] = existing_batch_dir.name
        
        # 创建批次目录
        batch_dir = Path(UPLOAD_FOLDER) / batch_id
        batch_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存文件并检测重复
        uploaded_files = []
        file_details = []
        duplicate_files = []  # 记录重复的文件
        
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                
                # 检查是否在其他批次中已存在
                if filename in existing_files:
                    previous_batch = existing_files[filename]
                    duplicate_files.append({
                        'filename': filename,
                        'previous_batch': previous_batch,
                        'previous_time': 'N/A'
                    })
                    log_activity(f"⚠️ Skipped duplicate file: {filename} (already uploaded in batch {previous_batch})")
                    continue  # 跳过这个文件，不保存
                
                # 保存文件
                filepath = batch_dir / filename
                file.save(str(filepath))
                uploaded_files.append(filename)
                
                file_details.append({
                    "filename": filename,
                    "size": filepath.stat().st_size,
                    "upload_time": datetime.now().isoformat()
                })
                log_activity(f"Uploaded file to batch {batch_id}: {filename}")
        
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
            json.dump(batch_info, f, ensure_ascii=False, indent=2)
        
        # 即使全部重复也不报错，返回成功（但count为0）
        if len(uploaded_files) == 0 and len(duplicate_files) > 0:
            log_activity(f"All files are duplicates, batch {batch_id} created but no new files")
        
        log_activity(f"Batch created: {batch_id}, {len(uploaded_files)} files uploaded successfully")
        if duplicate_files:
            log_activity(f"Skipped {len(duplicate_files)} duplicate files")
        
        return jsonify({
            'success': True,
            'batch_id': batch_id,
            'uploaded_files': uploaded_files,
            'count': len(uploaded_files),
            'duplicate_files': duplicate_files,
            'duplicate_count': len(duplicate_files),
            'message': f'成功上传 {len(uploaded_files)} 个文件' + (f'，跳过 {len(duplicate_files)} 个重复文件' if duplicate_files else '')
        })
    except Exception as e:
        log_activity(f"Upload failed: {str(e)}")
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
    """获取LLM处理的文件列表（支持批次模式和批次过滤）"""
    try:
        final_dir = Path(DIRECTORIES["final_output_dir"])
        files = []
        
        # 获取可选的batch_id参数
        batch_id_filter = request.args.get('batch_id')
        
        # 检查是否有批次文件夹
        batch_dirs = [d for d in final_dir.iterdir() if d.is_dir()]
        
        if batch_dirs:
            # 批次模式：从批次文件夹中收集文件
            for batch_dir in batch_dirs:
                # 如果指定了batch_id，只处理该批次
                if batch_id_filter and batch_dir.name != batch_id_filter:
                    continue
                    
                batch_files = [f"{batch_dir.name}/{f.name}" for f in batch_dir.glob("*.md")]
                files.extend(batch_files)
        else:
            # 非批次模式：直接从最终输出目录获取
            files = [f.name for f in final_dir.glob("*.md")]
        
        # 检查全局进度状态
        global llm_processing_progress
        batch_key = batch_id_filter if batch_id_filter else 'default'
        is_processing = llm_processing_progress.get(batch_key, {}).get('is_processing', False)
        
        return jsonify({
            'success': True, 
            'files': files, 
            'count': len(files),
            'is_processing': is_processing  # 新增：是否正在处理
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/kb-upload-progress', methods=['GET'])
def get_kb_upload_progress():
    """获取知识库上传进度（用于进度监控，支持批次隔离）"""
    try:
        global kb_upload_progress
        
        # 获取批次key（兼容旧接口）
        batch_key = request.args.get('batch_key', 'default')
        
        # 如果没有该批次的进度，返回默认值
        if batch_key not in kb_upload_progress:
            return jsonify({
                'success': True,
                'total': 0,
                'uploaded': 0,
                'is_uploading': False,
                'batch_key': batch_key
            })
        
        progress = kb_upload_progress[batch_key]
        
        # 如果上传完成（uploaded === total 且 total > 0），自动更新批次状态
        # 这确保即使请求返回500或 is_uploading 标志未及时更新，状态也会被更新
        if progress['total'] > 0 and progress['uploaded'] == progress['total']:
            # 尝试从 batch_key 提取批次ID（可能是单个批次ID或下划线连接的多个）
            # 如果是单个批次，直接使用；如果是多个批次，需要拆分
            batch_ids_from_key = batch_key.split('_') if '_' in batch_key and not batch_key.startswith('batch_') else [batch_key]
            # 但通常单个批次时，batch_key就是batch_id，多个批次时用下划线连接
            # 检查是否是批次ID格式
            if batch_key.startswith('batch_'):
                # 单个批次，直接使用
                batch_ids_to_update = [batch_key]
            else:
                # 可能是多个批次用下划线连接，尝试解析
                # 但实际使用中，batch_key通常是单个批次ID
                batch_ids_to_update = [batch_key] if len(batch_key.split('_')) < 3 else batch_key.split('_')
            
            # 更新批次状态（只更新已上传完成的批次）
            for batch_id in batch_ids_to_update:
                try:
                    # 验证是否是有效的批次ID格式
                    if batch_id.startswith('batch_'):
                        # 检查批次是否存在且状态未更新
                        upload_dir = Path(DIRECTORIES["upload_dir"])
                        batch_dir = upload_dir / batch_id
                        if batch_dir.exists():
                            batch_info_file = batch_dir / ".batch_info.json"
                            if batch_info_file.exists():
                                with open(batch_info_file, 'r', encoding='utf-8') as f:
                                    batch_info = json.load(f)
                                if not batch_info.get('status', {}).get('uploaded_to_kb', False):
                                    update_batch_status_file(batch_id, 'uploaded_to_kb', True)
                                    log_activity(f"Auto-updated batch {batch_id} status to 'uploaded_to_kb': True (from progress check)")
                except Exception as e:
                    log_activity(f"Failed to auto-update batch status from progress check: {str(e)}")
        
        return jsonify({
            'success': True,
            'total': progress['total'],
            'uploaded': progress['uploaded'],
            'is_uploading': progress['is_uploading'],
            'batch_key': batch_key
        })
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
        log_activity(f"Failed to read file content: {str(e)}")
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
            log_activity(f"Batch cleaning completed: {processed_count} files")
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
        log_activity(f"Cleaning process failed: {str(e)}")
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
                    log_activity(f"LLM processing file: {filename}")
                else:
                    raise Exception("LLM未返回有效响应")
                
                # 延迟避免限流
                import time
                time.sleep(delay)
                
            except Exception as e:
                error_msg = f"处理失败: {filename} - {str(e)}"
                errors.append(error_msg)
                log_activity(f"LLM {error_msg}")
        
        return jsonify({
            'success': len(processed_files) > 0,
            'processed_files': processed_files,
            'count': len(processed_files),
            'errors': errors
        })
    except Exception as e:
        log_activity(f"LLM processing failed: {str(e)}")
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
                log_activity(f"File not found: {filename}")
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
                    log_activity(f"Uploaded to knowledge base: {filename}")
                    
            except Exception as e:
                log_activity(f"Failed to upload to knowledge base: {filename} - {str(e)}")
        
        return jsonify({
            'success': True,
            'uploaded_count': uploaded_count
        })
    except Exception as e:
        log_activity(f"Knowledge base upload process failed: {str(e)}")
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
        log_activity(f"QA chat failed: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({'status': 'ok'})


@app.errorhandler(500)
def internal_error(error):
    """全局500错误处理器"""
    import traceback
    error_trace = traceback.format_exc()
    error_msg = str(error)
    
    # 记录详细的错误信息
    log_activity(f"[500 ERROR] {error_msg}")
    log_activity(f"[500 ERROR] Traceback: {error_trace}")
    
    # 也打印到控制台
    print(f"[500 ERROR] {error_msg}")
    print(f"[500 ERROR] Traceback:\n{error_trace}")
    
    return jsonify({
        'success': False,
        'error': f'Internal Server Error: {error_msg}',
        'traceback': error_trace
    }), 500


@app.errorhandler(Exception)
def handle_exception(e):
    """全局异常处理器"""
    import traceback
    error_trace = traceback.format_exc()
    error_msg = str(e)
    
    # 记录详细的错误信息
    log_activity(f"[EXCEPTION] {error_msg}")
    log_activity(f"[EXCEPTION] Traceback: {error_trace}")
    
    # 也打印到控制台
    print(f"[EXCEPTION] {error_msg}")
    print(f"[EXCEPTION] Traceback:\n{error_trace}")
    
    return jsonify({
        'success': False,
        'error': f'Exception: {error_msg}',
        'traceback': error_trace
    }), 500


# 辅助函数：更新批次状态
def update_batch_status_file(batch_id: str, status_key: str, status_value: bool = True):
    """更新批次状态到元数据文件"""
    try:
        from datetime import datetime
        import json
        
        upload_dir = Path(DIRECTORIES["upload_dir"])
        batch_dir = upload_dir / batch_id
        
        if not batch_dir.exists():
            log_activity(f"Warning: Batch directory not found: {batch_id}")
            return False
        
        batch_info_file = batch_dir / ".batch_info.json"
        if not batch_info_file.exists():
            log_activity(f"Warning: Batch metadata not found: {batch_id}")
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
        
        log_activity(f"Batch {batch_id} status updated: {status_key} = {status_value}")
        return True
    except Exception as e:
        log_activity(f"Failed to update batch status {batch_id}: {str(e)}")
        return False


# 全局停止标志（用于跨请求通信）
from threading import Event
global_stop_event = Event()

# 全局知识库上传进度跟踪（批次隔离）
# 格式: {batch_key: {'total': int, 'uploaded': int, 'is_uploading': bool}}
kb_upload_progress = {}

# 全局LLM处理进度跟踪（批次隔离）
# 格式: {batch_key: {'total': int, 'processed': int, 'failed': int, 'is_processing': bool}}
llm_processing_progress = {}

@app.route('/api/auto/stop', methods=['POST'])
def auto_stop():
    """停止当前的自动处理流程"""
    try:
        global_stop_event.set()
        log_activity("Received stop request, stopping processing...")
        return jsonify({'success': True, 'message': '停止信号已发送'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/auto/clear-processing-status', methods=['POST'])
def clear_processing_status():
    """清除处理状态标志（用于解决卡住的状态）"""
    try:
        data = request.json
        batch_id = data.get('batch_id')
        
        global llm_processing_progress, kb_upload_progress
        
        if batch_id:
            # 清除特定批次的状态
            if batch_id in llm_processing_progress:
                llm_processing_progress[batch_id]['is_processing'] = False
                log_activity(f"Cleared LLM processing status for batch: {batch_id}")
            
            if batch_id in kb_upload_progress:
                kb_upload_progress[batch_id]['is_uploading'] = False
                log_activity(f"Cleared KB upload status for batch: {batch_id}")
            
            return jsonify({
                'success': True,
                'message': f'已清除批次 {batch_id} 的处理状态'
            })
        else:
            # 清除所有批次的状态
            for key in llm_processing_progress:
                llm_processing_progress[key]['is_processing'] = False
            for key in kb_upload_progress:
                kb_upload_progress[key]['is_uploading'] = False
            
            log_activity("Cleared all processing status flags")
            return jsonify({
                'success': True,
                'message': '已清除所有处理状态'
            })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# 全自动处理流程API
@app.route('/api/auto/clean', methods=['POST'])
def auto_clean():
    """全自动流程 - 步骤1: 邮件清洗"""
    try:
        # 安全获取请求数据
        try:
            if not request.is_json:
                log_activity("Email cleaning error: Request is not JSON")
                return jsonify({'success': False, 'error': '请求必须是JSON格式'}), 400
            
            data = request.get_json(silent=True)
            if not data:
                log_activity("Email cleaning error: Request JSON is None or invalid")
                return jsonify({'success': False, 'error': '请求数据为空或格式错误'}), 400
        except Exception as e:
            log_activity(f"Email cleaning error: Failed to parse request JSON: {str(e)}")
            return jsonify({'success': False, 'error': f'解析请求数据失败: {str(e)}'}), 400
        
        batch_ids = data.get('batch_ids', [])
        skip_if_exists = data.get('skip_if_exists', True)  # 默认启用智能跳过
        
        log_activity(f"Email cleaning request received: batch_ids={batch_ids}, skip_if_exists={skip_if_exists}")
        
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
                        log_activity(f"Batch {batch_id} already has {len(md_files)} processed files, skipping cleaning step")
                        skipped_batches.append(batch_id)
                        continue  # 只有在有MD文件时才跳过
                # 目录不存在，或者存在但没有MD文件，都应该处理
                batches_to_process.append(batch_id)
            
            if not batches_to_process:
                log_activity(f"All batches already cleaned, skipping this step")
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
            log_activity(f"Will process {len(batch_ids)} batches, skipping {len(skipped_batches)} already processed batches")
        
        if batch_ids:
            # 批次模式：只处理选中的批次
            log_activity(f"Starting email cleaning (selected {len(batch_ids)} batches): {batch_ids}")
            log_disk_usage("[清洗前] ")
            cleaner = EmailCleaner(input_dir=str(upload_dir), output_dir=str(processed_dir), batch_mode=True)
            result = cleaner.process_all_emails(selected_batches=batch_ids)
        else:
            # 非批次模式：处理所有文件
            log_activity(f"Starting email cleaning: {upload_dir}")
            log_disk_usage("[清洗前] ")
            cleaner = EmailCleaner(input_dir=str(upload_dir), output_dir=str(processed_dir))
            result = cleaner.process_all_emails()
        
        if result.get('success'):
            # 从report中获取处理数量
            report = result.get('report', {})
            processed_count = report.get('unique_emails', len(result.get('generated_files', [])))
            log_activity(f"Email cleaning completed: {processed_count} files")
            log_disk_usage("[清洗后] ")
            
            # 记录全局去重信息
            global_duplicates = report.get('all_global_duplicates', [])
            if global_duplicates:
                log_activity(f"Detected {len(global_duplicates)} cross-batch duplicate emails, automatically skipped")
                for dup in global_duplicates:
                    log_activity(f"  - {dup['file_name']} (已在批次 {dup['previous_batch']} 中处理)")
            
            return jsonify({
                'success': True,
                'processed_count': processed_count,
                'total_files': report.get('total_input_files', 0),
                'duplicates': report.get('duplicate_emails', 0),
                'global_duplicates': global_duplicates,
                'message': '邮件清洗完成'
            })
        else:
            error_msg = result.get('message', '邮件清洗失败')
            log_activity(f"Email cleaning failed: {error_msg}")
            return jsonify({'success': False, 'error': error_msg})
            
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        log_activity(f"Email cleaning error: {str(e)}")
        log_activity(f"错误堆栈: {error_trace}")
        print(f"邮件清洗异常: {str(e)}")
        print(f"错误堆栈:\n{error_trace}")
        return jsonify({'success': False, 'error': str(e), 'traceback': error_trace}), 500


@app.route('/api/auto/llm-process', methods=['POST'])
def auto_llm_process():
    """全自动流程 - 步骤2: LLM处理（支持并发和停止）"""
    try:
        # 清除之前的停止标志
        global_stop_event.clear()
        
        # 安全获取请求数据
        try:
            if not request.is_json:
                log_activity("LLM processing error: Request is not JSON")
                return jsonify({'success': False, 'error': '请求必须是JSON格式'}), 400
            
            data = request.get_json(silent=True)
            if not data:
                log_activity("LLM processing error: Request JSON is None or invalid")
                return jsonify({'success': False, 'error': '请求数据为空或格式错误'}), 400
        except Exception as e:
            log_activity(f"LLM processing error: Failed to parse request JSON: {str(e)}")
            return jsonify({'success': False, 'error': f'解析请求数据失败: {str(e)}'}), 400
        
        api_key = data.get('api_key')
        delay = data.get('delay', 1)  # 默认1秒间隔
        batch_ids = data.get('batch_ids', [])
        skip_if_exists = data.get('skip_if_exists', True)  # 默认启用智能跳过
        max_workers = data.get('max_workers', 1)  # 并发数，默认1个（串行）
        
        # 确保 batch_ids 是列表格式
        if batch_ids and not isinstance(batch_ids, list):
            if isinstance(batch_ids, str):
                batch_ids = [batch_ids]
            else:
                log_activity(f"LLM processing error: Invalid batch_ids type: {type(batch_ids)}")
                batch_ids = []
        
        if not api_key:
            log_activity("LLM processing error: Missing API Key")
            return jsonify({'success': False, 'error': '缺少API Key'}), 400
        
        # 记录请求参数（隐藏敏感信息）
        log_activity(f"LLM processing request: batch_ids={batch_ids}, delay={delay}, max_workers={max_workers}, skip_if_exists={skip_if_exists}")
        
        processed_dir = Path(DIRECTORIES["processed_dir"])
        final_dir = Path(DIRECTORIES["final_output_dir"])
        final_dir.mkdir(parents=True, exist_ok=True)
        
        # 智能跳过：检查是否已有LLM处理后的文件（比较processed和final_output的文件数）
        if skip_if_exists and batch_ids:
            skipped_batches = []
            batches_to_process = []
            
            for batch_id in batch_ids:
                final_batch_dir = final_dir / batch_id
                processed_batch_dir = processed_dir / batch_id
                
                if final_batch_dir.exists() and processed_batch_dir.exists():
                    # 统计两个目录的文件数
                    llm_files = list(final_batch_dir.glob("*.md"))
                    processed_files = [f for f in processed_batch_dir.glob("*.md") if f.name != "processing_report.json"]
                    
                    # 只有当final_output的文件数等于processed的文件数时，才认为已完成
                    if llm_files and len(llm_files) >= len(processed_files):
                        log_activity(f"Batch {batch_id} LLM processing completed: {len(llm_files)}/{len(processed_files)} files, skipping LLM processing step")
                        skipped_batches.append(batch_id)
                        # 更新状态（如果尚未更新）
                        update_batch_status_file(batch_id, 'llm_processed', True)
                        continue
                    elif llm_files:
                        log_activity(f"Batch {batch_id} LLM processing incomplete: processed {len(llm_files)}/{len(processed_files)} files, continuing with remaining files")
                
                batches_to_process.append(batch_id)
            
            if not batches_to_process:
                log_activity(f"All batches already LLM processed, skipping this step")
                # 更新所有跳过批次的状态
                for batch_id in skipped_batches:
                    update_batch_status_file(batch_id, 'llm_processed', True)
                
                return jsonify({
                    'success': True,
                    'processed_count': 0,
                    'failed_count': 0,
                    'total_files_after_dedup': 0,
                    'skipped': True,
                    'skipped_batches': skipped_batches,
                    'message': '所有批次都已完成LLM处理，已跳过'
                })
            
            batch_ids = batches_to_process
            log_activity(f"Will process {len(batch_ids)} batches, skipping {len(skipped_batches)} already processed batches")
        
        # 获取所有markdown文件（支持批次模式）
        md_files = []
        
        # 检查是否有批次文件夹
        batch_dirs = [d for d in processed_dir.iterdir() if d.is_dir()]
        
        if batch_dirs:
            # 批次模式：从指定批次文件夹中收集文件
            if batch_ids:
                # 只处理选中的批次
                log_activity(f"LLM processing: selected {len(batch_ids)} batches")
                for batch_id in batch_ids:
                    batch_dir = processed_dir / batch_id
                    if batch_dir.exists() and batch_dir.is_dir():
                        batch_md_files = list(batch_dir.glob("*.md"))
                        batch_md_files = [f for f in batch_md_files if f.name != "processing_report.json"]
                        md_files.extend(batch_md_files)
                        log_activity(f"Batch {batch_id}: found {len(batch_md_files)} files")
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
        
        # 记录去重后的实际文件数
        total_files_after_dedup = len(md_files)
        log_activity(f"LLM processing: total {total_files_after_dedup} files to process after deduplication")
        
        # 检查有多少文件实际上需要处理（不包括已存在的文件）
        files_needing_processing = []
        for md_file in md_files:
            # 确定输出文件路径
            if md_file.parent != processed_dir:
                batch_name = md_file.parent.name
                batch_final_dir = final_dir / batch_name
                output_file = batch_final_dir / md_file.name
            else:
                output_file = final_dir / md_file.name
            
            # 只添加不存在的文件
            if not output_file.exists():
                files_needing_processing.append(md_file)
        
        # 如果所有文件都已处理过，直接返回成功
        if not files_needing_processing:
            log_activity(f"All {total_files_after_dedup} files already processed, nothing to do")
            # 更新批次状态
            if batch_ids:
                for batch_id in batch_ids:
                    update_batch_status_file(batch_id, 'llm_processed', True)
            
            return jsonify({
                'success': True,
                'processed_count': total_files_after_dedup,
                'failed_count': 0,
                'total_files_after_dedup': total_files_after_dedup,
                'message': f'所有文件已处理完成（共 {total_files_after_dedup} 个文件）',
                'all_already_processed': True
            })
        
        log_activity(f"Found {len(files_needing_processing)} files that need processing (out of {total_files_after_dedup} total)")
        log_activity(f"LLM processing: concurrency set to {max_workers}")
        log_disk_usage("[LLM处理前] ")
        
        # 初始化全局进度跟踪
        global llm_processing_progress
        batch_key = batch_ids[0] if batch_ids else 'default'
        llm_processing_progress[batch_key] = {
            'total': total_files_after_dedup,
            'processed': 0,
            'failed': 0,
            'is_processing': True
        }
        
        # 初始化GPTBots API客户端
        client = GPTBotsAPI(api_key)
        processed_count = 0
        failed_count = 0
        
        # 使用线程安全的计数器和停止标志
        from threading import Lock, Event
        count_lock = Lock()
        # 使用全局停止标志（可以被/api/auto/stop触发）
        stop_event = global_stop_event
        
        # LLM提示词模板
        llm_prompt_template = """以下是需要处理的邮件内容，请帮我整理和优化：

{email_content}"""
        
        def process_single_file(md_file):
            """处理单个文件（线程安全，支持停止）"""
            nonlocal processed_count, failed_count
            
            # 检查停止信号
            if stop_event.is_set():
                log_activity(f"Received stop signal, skipping: {md_file.name}")
                return False
            
            try:
                # 确定输出文件路径
                if md_file.parent != processed_dir:
                    # 批次模式：在final_dir中创建对应的批次目录
                    batch_name = md_file.parent.name
                    batch_final_dir = final_dir / batch_name
                    batch_final_dir.mkdir(parents=True, exist_ok=True)
                    output_file = batch_final_dir / md_file.name
                else:
                    # 非批次模式：直接保存到final_dir
                    output_file = final_dir / md_file.name
                
                # 检查文件是否已经处理过（跳过已存在的文件）
                if output_file.exists():
                    log_activity(f"File already processed, skipped: {md_file.name}")
                    with count_lock:
                        processed_count += 1  # 计入已处理数
                    return True
                
                # 再次检查停止信号（在开始处理前）
                if stop_event.is_set():
                    log_activity(f"Received stop signal, aborting processing: {md_file.name}")
                    return False
                
                # 记录当前处理进度
                with count_lock:
                    current_progress = processed_count + failed_count + 1
                log_activity(f"[{current_progress}/{total_files_after_dedup}] Processing: {md_file.name}")
                
                # 读取文件内容
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 创建对话
                conversation_id = client.create_conversation()
                if not conversation_id:
                    log_activity(f"Failed to create conversation: {md_file.name}")
                    with count_lock:
                        failed_count += 1
                    return False
                
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
                        with open(output_file, 'w', encoding='utf-8') as f:
                            f.write(processed_content.strip())
                        
                        with count_lock:
                            processed_count += 1
                            current_count = processed_count
                        log_activity(f"[{current_count}/{total_files_after_dedup}] Successfully processed: {md_file.name}")
                        return True
                    else:
                        log_activity(f"LLM returned empty content: {md_file.name}")
                        with count_lock:
                            failed_count += 1
                        return False
                else:
                    # 记录响应详情以便排查
                    if response:
                        if isinstance(response, dict):
                            # 打印完整的错误响应
                            error_code = response.get('code', 'N/A')
                            error_msg = response.get('message', 'N/A')
                            log_activity(f"LLM call failed (no output): {md_file.name}")
                            log_activity(f"  Error code: {error_code}, Error message: {error_msg}")
                            log_activity(f"  Full response keys: {list(response.keys())}")
                        else:
                            log_activity(f"LLM call failed (no output): {md_file.name}, response type: {type(response)}")
                    else:
                        log_activity(f"LLM call failed (no response): {md_file.name}")
                    with count_lock:
                        failed_count += 1
                    return False
                
            except Exception as e:
                log_activity(f"File processing error {md_file.name}: {str(e)}")
                with count_lock:
                    failed_count += 1
                return False
        
        # 并发处理文件
        try:
            if max_workers > 1:
                # 使用线程池并发处理
                from concurrent.futures import ThreadPoolExecutor, as_completed
                import threading
                
                log_activity(f"使用并发模式处理 (workers={max_workers})")
                
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    # 提交所有任务
                    futures = {executor.submit(process_single_file, md_file): md_file for md_file in files_needing_processing}
                    
                    # 等待完成，添加延迟避免过快
                    for future in as_completed(futures):
                        try:
                            future.result()
                            # 并发时的延迟：总延迟/并发数，避免API限流
                            time.sleep(delay / max_workers)
                        except Exception as e:
                            log_activity(f"并发任务异常: {str(e)}")
            else:
                # 串行处理（兼容模式）
                log_activity(f"使用串行模式处理")
                for md_file in files_needing_processing:
                    try:
                        process_single_file(md_file)
                        time.sleep(delay)  # 延迟避免API限流
                    except Exception as e:
                        # 单个文件处理失败不应该中断整个流程，继续处理下一个
                        log_activity(f"处理文件时发生异常，继续处理下一个: {md_file.name}, 错误: {str(e)}")
                        continue
        except Exception as e:
            # 处理循环中的异常不应该中断，应该记录并继续
            log_activity(f"文件处理循环中的异常: {str(e)}")
            import traceback
            log_activity(f"处理循环异常堆栈: {traceback.format_exc()}")
        
        # 更新批次状态
        if batch_ids and processed_count > 0:
            for batch_id in batch_ids:
                update_batch_status_file(batch_id, 'llm_processed', True)
        
        log_activity(f"LLM processing completed: {processed_count} successful, {failed_count} failed")
        log_disk_usage("[LLM处理后] ")
        
        # 标记处理完成
        if batch_key in llm_processing_progress:
            llm_processing_progress[batch_key]['is_processing'] = False
            llm_processing_progress[batch_key]['processed'] = processed_count
            llm_processing_progress[batch_key]['failed'] = failed_count
        
        if processed_count > 0:
            return jsonify({
                'success': True,
                'processed_count': processed_count,
                'failed_count': failed_count,
                'total_files_after_dedup': total_files_after_dedup,
                'message': f'LLM处理完成: 成功 {processed_count} 个，失败 {failed_count} 个（去重后共 {total_files_after_dedup} 个文件）'
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
        import traceback
        error_trace = traceback.format_exc()
        log_activity(f"LLM processing error: {str(e)}")
        log_activity(f"错误堆栈: {error_trace}")
        print(f"LLM处理异常: {str(e)}")
        print(f"错误堆栈:\n{error_trace}")
        
        # 异常时也标记处理完成，并保存已处理的进度
        if 'batch_key' in locals() and batch_key in llm_processing_progress:
            llm_processing_progress[batch_key]['is_processing'] = False
            # 如果有部分处理成功，保存进度
            if 'processed_count' in locals():
                llm_processing_progress[batch_key]['processed'] = processed_count
            if 'failed_count' in locals():
                llm_processing_progress[batch_key]['failed'] = failed_count
        
        # 如果已有部分文件处理成功，即使发生异常也返回部分成功的结果
        if 'processed_count' in locals() and processed_count > 0:
            log_activity(f"LLM处理部分完成: {processed_count} 成功，发生异常但已处理的文件已保存")
            return jsonify({
                'success': True,
                'processed_count': processed_count,
                'failed_count': failed_count if 'failed_count' in locals() else 0,
                'total_files_after_dedup': total_files_after_dedup if 'total_files_after_dedup' in locals() else 0,
                'message': f'LLM处理部分完成: 成功 {processed_count} 个（处理过程中发生异常: {str(e)}）',
                'warning': f'处理过程中发生异常: {str(e)}'
            })
        
        return jsonify({'success': False, 'error': str(e), 'traceback': error_trace}), 500


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
                            log_activity(f"Batch {batch_id} already uploaded to knowledge base, skipping upload step")
                            skipped_batches.append(batch_id)
                            continue
                    except Exception as e:
                        log_activity(f"Failed to read batch metadata {batch_id}: {str(e)}")
                
                batches_to_process.append(batch_id)
            
            if not batches_to_process:
                log_activity(f"All batches already uploaded to knowledge base, skipping this step")
                return jsonify({
                    'success': True,
                    'uploaded_count': 0,
                    'skipped': True,
                    'skipped_batches': skipped_batches,
                    'message': '所有批次都已完成知识库上传，已跳过'
                })
            
            batch_ids = batches_to_process
            log_activity(f"Will upload {len(batch_ids)} batches, skipping {len(skipped_batches)} already uploaded batches")
        
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
                        log_activity(f"Batch {batch_id}: found {len(batch_md_files)} files")
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
        
        # 初始化上传进度（使用批次key隔离）
        global kb_upload_progress
        batch_key = '_'.join(batch_ids) if batch_ids else 'default'
        kb_upload_progress[batch_key] = {
            'total': len(md_files),
            'uploaded': 0,
            'is_uploading': True
        }
        
        log_activity(f"Starting upload of {len(md_files)} files to knowledge base")
        log_disk_usage("[上传前] ")
        
        kb_client = KnowledgeBaseAPI(api_key)
        
        # 批次模式需要逐个上传文件，非批次模式可以使用目录上传
        if batch_dirs:
            # 批次模式：使用并发上传提高速度
            successful_uploads = 0
            failed_uploads = 0
            
            # 使用线程锁保护计数器
            from threading import Lock
            upload_lock = Lock()
            
            # 定义单个文件上传函数
            def upload_single_file(md_file):
                nonlocal successful_uploads, failed_uploads
                try:
                    # 读取文件内容
                    with open(md_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # 构建上传参数
                    upload_params = {
                        'content': content,
                        'filename': md_file.name,
                        'knowledge_base_id': kb_id
                    }
                    
                    if chunk_token:
                        upload_params['chunk_token'] = chunk_token
                        upload_params['splitter'] = "PARAGRAPH"
                    else:
                        upload_params['chunk_token'] = 600
                        upload_params['splitter'] = "PARAGRAPH"
                    
                    # 上传单个文件
                    result = kb_client.upload_markdown_content(**upload_params)
                    
                    with upload_lock:
                        if result and 'error' not in result:
                            successful_uploads += 1
                            kb_upload_progress[batch_key]['uploaded'] = successful_uploads
                            log_activity(f"✓ Uploaded: {md_file.name}")
                        else:
                            failed_uploads += 1
                            log_activity(f"✗ Upload failed: {md_file.name}, error: {result.get('error', 'Unknown error')}")
                    
                    return True
                    
                except Exception as e:
                    with upload_lock:
                        failed_uploads += 1
                        kb_upload_progress[batch_key]['uploaded'] = successful_uploads
                        log_activity(f"✗ Upload error {md_file.name}: {str(e)}")
                    return False
            
            # 使用线程池并发上传（3个并发，平衡速度和API压力）
            from concurrent.futures import ThreadPoolExecutor, as_completed
            max_upload_workers = 3  # 3个文件同时上传
            
            log_activity(f"Starting concurrent upload with {max_upload_workers} workers")
            
            with ThreadPoolExecutor(max_workers=max_upload_workers) as executor:
                futures = {executor.submit(upload_single_file, f): f for f in md_files}
                
                for future in as_completed(futures):
                    try:
                        future.result()
                        # 小延迟避免过快（每个worker都有延迟）
                        time.sleep(0.5)
                    except Exception as e:
                        log_activity(f"Upload task exception: {str(e)}")
            
            # 更新批次状态 - 标记为已上传并添加知识库名称标签
            # 即使后续发生异常，也要确保状态已更新
            if batch_ids and successful_uploads > 0:
                # 先更新批次状态（无论是否成功获取知识库名称）
                try:
                    for batch_id in batch_ids:
                        update_batch_status_file(batch_id, 'uploaded_to_kb', True)
                        log_activity(f"Batch {batch_id} status updated to 'uploaded_to_kb': True")
                except Exception as e:
                    log_activity(f"Warning: Failed to update batch status: {str(e)}")
                
                # 获取知识库名称（可选操作，失败不影响主流程）
                kb_name = None
                try:
                    log_activity(f"正在获取知识库名称，KB ID: {kb_id}")
                    kb_response = kb_client.get_knowledge_bases()
                    log_activity(f"知识库API响应: {kb_response}")
                    
                    # 尝试多种可能的响应结构
                    kb_list = None
                    if kb_response:
                        # 格式1: {'data': {'list': [...]}}
                        if 'data' in kb_response and isinstance(kb_response['data'], dict) and 'list' in kb_response['data']:
                            kb_list = kb_response['data']['list']
                        # 格式2: {'data': [...]}
                        elif 'data' in kb_response and isinstance(kb_response['data'], list):
                            kb_list = kb_response['data']
                        # 格式3: {'knowledge_base': [...]}
                        elif 'knowledge_base' in kb_response and isinstance(kb_response['knowledge_base'], list):
                            kb_list = kb_response['knowledge_base']
                        # 格式4: 直接是列表
                        elif isinstance(kb_response, list):
                            kb_list = kb_response
                    
                    if kb_list:
                        log_activity(f"Found {len(kb_list)} knowledge bases")
                        for kb in kb_list:
                            if kb.get('id') == kb_id:
                                kb_name = kb.get('name', '')
                                log_activity(f"匹配到知识库: {kb_name}")
                                break
                    else:
                        log_activity(f"无法从响应中解析知识库列表")
                        
                except Exception as e:
                    log_activity(f"Failed to get knowledge base name (non-critical): {str(e)}")
                
                # 如果成功获取知识库名称，保存到批次元数据（可选操作，失败不影响主流程）
                if kb_name:
                    for batch_id in batch_ids:
                        try:
                            upload_dir = Path(DIRECTORIES["upload_dir"])
                            batch_dir = upload_dir / batch_id
                            batch_info_file = batch_dir / ".batch_info.json"
                            
                            if batch_info_file.exists():
                                with open(batch_info_file, 'r', encoding='utf-8') as f:
                                    batch_info = json.load(f)
                                
                                batch_info['kb_name'] = kb_name
                                
                                with open(batch_info_file, 'w', encoding='utf-8') as f:
                                    json.dump(batch_info, f, ensure_ascii=False, indent=2)
                                
                                log_activity(f"Batch {batch_id} automatically tagged with knowledge base: {kb_name}")
                            else:
                                log_activity(f"Warning: Batch info file not found for {batch_id}, cannot save KB name")
                        except Exception as e:
                            log_activity(f"Failed to save knowledge base name to batch {batch_id} (non-critical): {str(e)}")
                else:
                    log_activity(f"Warning: Unable to get knowledge base name, batches need manual tagging")
            
            log_activity(f"Knowledge base upload completed: {successful_uploads} successful, {failed_uploads} failed")
            log_disk_usage("[上传后] ")
            
            if successful_uploads > 0:
                kb_upload_progress[batch_key]['is_uploading'] = False  # 标记上传完成
                return jsonify({
                    'success': True,
                    'uploaded_count': successful_uploads,
                    'message': f'知识库上传完成: 成功 {successful_uploads} 个，失败 {failed_uploads} 个'
                })
            else:
                kb_upload_progress[batch_key]['is_uploading'] = False  # 标记上传完成（即使失败）
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
        
        if batch_key in kb_upload_progress:
            kb_upload_progress[batch_key]['is_uploading'] = False  # 标记上传完成
        
        if result and 'error' not in result:
            return jsonify({
                'success': True,
                'uploaded_count': result.get('successful_uploads', 0),
                'message': '知识库上传完成'
            })
        else:
            return jsonify({'success': False, 'error': result.get('error', '上传失败')}), 500
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        log_activity(f"KB upload error: {str(e)}")
        log_activity(f"错误堆栈: {error_trace}")
        
        # 即使发生异常，如果有部分上传成功，也要更新批次状态
        if 'batch_ids' in locals() and 'successful_uploads' in locals():
            if batch_ids and successful_uploads > 0:
                try:
                    log_activity(f"Exception occurred but {successful_uploads} files uploaded successfully, updating batch status...")
                    for batch_id in batch_ids:
                        update_batch_status_file(batch_id, 'uploaded_to_kb', True)
                        log_activity(f"Batch {batch_id} status updated to 'uploaded_to_kb': True (despite exception)")
                except Exception as status_error:
                    log_activity(f"Failed to update batch status after exception: {str(status_error)}")
        
        # 标记上传完成
        if 'batch_key' in locals() and batch_key in kb_upload_progress:
            kb_upload_progress[batch_key]['is_uploading'] = False  # 异常时也标记完成
        
        # 如果有部分成功，返回部分成功的结果而不是完全失败
        if 'successful_uploads' in locals() and successful_uploads > 0:
            log_activity(f"Returning partial success: {successful_uploads} files uploaded despite exception")
            return jsonify({
                'success': True,
                'uploaded_count': successful_uploads,
                'failed_count': failed_uploads if 'failed_uploads' in locals() else 0,
                'message': f'知识库上传部分完成: 成功 {successful_uploads} 个（处理过程中发生异常: {str(e)}）',
                'warning': f'处理过程中发生异常: {str(e)}'
            })
        
        return jsonify({'success': False, 'error': str(e), 'traceback': error_trace}), 500


# ========== 单批次完整处理 API（用于并行处理） ==========

@app.route('/api/auto/process-single-batch', methods=['POST'])
def process_single_batch():
    """处理单个批次的完整流程（清洗→LLM→上传）
    
    用于多批次并行处理场景，每个批次独立调用此API
    """
    try:
        data = request.json
        batch_id = data.get('batch_id')
        llm_api_key = data.get('llm_api_key')
        kb_api_key = data.get('kb_api_key')
        kb_id = data.get('knowledge_base_id')
        chunk_token = data.get('chunk_token')
        chunk_separator = data.get('chunk_separator')
        max_workers = data.get('max_workers', 1)  # 单批次默认1个并发（串行）
        delay = data.get('delay', 1)  # 默认1秒间隔
        skip_if_exists = data.get('skip_if_exists', True)
        
        if not all([batch_id, llm_api_key, kb_api_key, kb_id]):
            return jsonify({'success': False, 'error': '缺少必需参数'}), 400
        
        log_activity(f"[Batch {batch_id}] Starting complete processing flow")
        
        result = {
            'batch_id': batch_id,
            'success': True,
            'steps': {}
        }
        
        # ========== 步骤1: 邮件清洗 ==========
        try:
            log_activity(f"[Batch {batch_id}] Step 1/3: Email cleaning")
            
            upload_dir = Path(DIRECTORIES["upload_dir"])
            processed_dir = Path(DIRECTORIES["processed_dir"])
            
            # 检查是否已清洗
            should_clean = True
            if skip_if_exists:
                processed_batch_dir = processed_dir / batch_id
                if processed_batch_dir.exists():
                    md_files = list(processed_batch_dir.glob("*.md"))
                    if md_files:
                        log_activity(f"[Batch {batch_id}] Already cleaned ({len(md_files)} files), skipping")
                        should_clean = False
                        result['steps']['clean'] = {
                            'success': True,
                            'processed_count': len(md_files),
                            'skipped': True
                        }
            
            if should_clean:
                cleaner = EmailCleaner(
                    input_dir=str(upload_dir),
                    output_dir=str(processed_dir),
                    batch_mode=True
                )
                clean_result = cleaner.process_all_emails(selected_batches=[batch_id])
                
                result['steps']['clean'] = {
                    'success': clean_result.get('success', False),
                    'processed_count': clean_result.get('unique_files', 0),
                    'duplicates': clean_result.get('duplicates', 0)
                }
                
                if not clean_result.get('success'):
                    raise Exception(f"Cleaning failed: {clean_result.get('message', 'Unknown error')}")
                
                log_activity(f"[Batch {batch_id}] Cleaned: {result['steps']['clean']['processed_count']} files")
        
        except Exception as e:
            log_activity(f"[Batch {batch_id}] Cleaning error: {str(e)}")
            result['steps']['clean'] = {'success': False, 'error': str(e)}
            result['success'] = False
            return jsonify(result), 500
        
        # ========== 步骤2: LLM处理 ==========
        try:
            log_activity(f"[Batch {batch_id}] Step 2/3: LLM processing")
            
            processed_dir = Path(DIRECTORIES["processed_dir"])
            final_dir = Path(DIRECTORIES["final_output_dir"])
            final_dir.mkdir(parents=True, exist_ok=True)
            
            # 检查是否已处理
            should_process_llm = True
            if skip_if_exists:
                final_batch_dir = final_dir / batch_id
                processed_batch_dir = processed_dir / batch_id
                
                if final_batch_dir.exists() and processed_batch_dir.exists():
                    llm_files = list(final_batch_dir.glob("*.md"))
                    processed_files = [f for f in processed_batch_dir.glob("*.md") if f.name != "processing_report.json"]
                    
                    if llm_files and len(llm_files) >= len(processed_files):
                        log_activity(f"[Batch {batch_id}] Already LLM processed ({len(llm_files)} files), skipping")
                        should_process_llm = False
                        result['steps']['llm'] = {
                            'success': True,
                            'processed_count': len(llm_files),
                            'skipped': True
                        }
            
            if should_process_llm:
                # 收集该批次的MD文件
                batch_dir = processed_dir / batch_id
                if not batch_dir.exists():
                    raise Exception(f"Processed directory not found: {batch_dir}")
                
                md_files = list(batch_dir.glob("*.md"))
                md_files = [f for f in md_files if f.name != "processing_report.json"]
                
                if not md_files:
                    raise Exception(f"No files to process in batch {batch_id}")
                
                log_activity(f"[Batch {batch_id}] Found {len(md_files)} files for LLM processing")
                
                # LLM处理（使用并发）
                from concurrent.futures import ThreadPoolExecutor, as_completed
                import threading
                
                llm_api = GPTBotsAPI(llm_api_key)
                processed_count = 0
                failed_count = 0
                count_lock = threading.Lock()
                
                def process_file(md_file):
                    nonlocal processed_count, failed_count
                    try:
                        if global_stop_event.is_set():
                            return False
                        
                        with open(md_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        conversation_id = llm_api.create_conversation()
                        if not conversation_id:
                            with count_lock:
                                failed_count += 1
                            return False
                        
                        response = llm_api.send_message(conversation_id, content)
                        if not response:
                            with count_lock:
                                failed_count += 1
                            return False
                        
                        # 提取实际的回复内容
                        llm_content = response.get('data', {}).get('answer', '') if isinstance(response, dict) else str(response)
                        
                        if not llm_content:
                            log_activity(f"[Batch {batch_id}] Warning: Empty LLM response for {md_file.name}")
                            with count_lock:
                                failed_count += 1
                            return False
                        
                        # 保存结果
                        output_batch_dir = final_dir / batch_id
                        output_batch_dir.mkdir(parents=True, exist_ok=True)
                        output_file = output_batch_dir / md_file.name
                        
                        with open(output_file, 'w', encoding='utf-8') as f:
                            f.write(llm_content)
                        
                        with count_lock:
                            processed_count += 1
                        
                        return True
                    except Exception as e:
                        log_activity(f"[Batch {batch_id}] File processing error {md_file.name}: {str(e)}")
                        with count_lock:
                            failed_count += 1
                        return False
                
                # 并发处理
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    futures = {executor.submit(process_file, f): f for f in md_files}
                    
                    for future in as_completed(futures):
                        try:
                            future.result()
                            time.sleep(delay / max_workers)
                        except Exception as e:
                            log_activity(f"[Batch {batch_id}] Task error: {str(e)}")
                
                result['steps']['llm'] = {
                    'success': processed_count > 0,
                    'processed_count': processed_count,
                    'failed_count': failed_count
                }
                
                log_activity(f"[Batch {batch_id}] LLM processed: {processed_count} success, {failed_count} failed")
                
                if processed_count == 0:
                    raise Exception("All LLM processing failed")
        
        except Exception as e:
            log_activity(f"[Batch {batch_id}] LLM processing error: {str(e)}")
            result['steps']['llm'] = {'success': False, 'error': str(e)}
            result['success'] = False
            return jsonify(result), 500
        
        # ========== 步骤3: 知识库上传 ==========
        try:
            log_activity(f"[Batch {batch_id}] Step 3/3: Knowledge base upload")
            
            # 检查是否已上传
            should_upload = True
            if skip_if_exists:
                upload_dir = Path(DIRECTORIES["upload_dir"])
                batch_dir = upload_dir / batch_id
                batch_info_file = batch_dir / ".batch_info.json"
                
                if batch_info_file.exists():
                    import json
                    with open(batch_info_file, 'r', encoding='utf-8') as f:
                        batch_info = json.load(f)
                    
                    if batch_info.get('status', {}).get('uploaded_to_kb', False):
                        log_activity(f"[Batch {batch_id}] Already uploaded to KB, skipping")
                        should_upload = False
                        result['steps']['upload'] = {
                            'success': True,
                            'uploaded_count': 0,
                            'skipped': True
                        }
            
            if should_upload:
                # 收集该批次的最终文件
                final_batch_dir = final_dir / batch_id
                if not final_batch_dir.exists():
                    raise Exception(f"Final output directory not found: {final_batch_dir}")
                
                md_files = list(final_batch_dir.glob("*.md"))
                if not md_files:
                    raise Exception(f"No files to upload in batch {batch_id}")
                
                log_activity(f"[Batch {batch_id}] Found {len(md_files)} files for upload")
                
                # 初始化进度追踪
                batch_key = batch_id
                global kb_upload_progress
                kb_upload_progress[batch_key] = {
                    'total': len(md_files),
                    'uploaded': 0,
                    'is_uploading': True
                }
                
                # 上传文件
                kb_client = KnowledgeBaseAPI(kb_api_key)
                successful_uploads = 0
                failed_uploads = 0
                
                for i, md_file in enumerate(md_files, 1):
                    try:
                        with open(md_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        upload_params = {
                            'content': content,
                            'filename': md_file.name,
                            'knowledge_base_id': kb_id
                        }
                        
                        # 添加分块参数
                        if chunk_token:
                            upload_params['chunk_token'] = chunk_token
                            upload_params['splitter'] = "PARAGRAPH"
                        elif chunk_separator:
                            upload_params['chunk_separator'] = chunk_separator
                            upload_params['splitter'] = "CUSTOM"
                        else:
                            upload_params['chunk_token'] = 600
                            upload_params['splitter'] = "PARAGRAPH"
                        
                        result_upload = kb_client.upload_markdown_content(**upload_params)
                        
                        if result_upload and 'error' not in result_upload:
                            successful_uploads += 1
                            kb_upload_progress[batch_key]['uploaded'] = successful_uploads
                        else:
                            failed_uploads += 1
                        
                        time.sleep(2.0)  # API限流（增加到2秒，降低并发）
                    
                    except Exception as e:
                        failed_uploads += 1
                        kb_upload_progress[batch_key]['uploaded'] = successful_uploads
                        log_activity(f"[Batch {batch_id}] Upload error {md_file.name}: {str(e)}")
                
                kb_upload_progress[batch_key]['is_uploading'] = False
                
                # 更新批次状态
                if successful_uploads > 0:
                    update_batch_status_file(batch_id, 'uploaded_to_kb', True)
                
                result['steps']['upload'] = {
                    'success': successful_uploads > 0,
                    'uploaded_count': successful_uploads,
                    'failed_count': failed_uploads
                }
                
                log_activity(f"[Batch {batch_id}] Uploaded: {successful_uploads} success, {failed_uploads} failed")
                
                if successful_uploads == 0:
                    raise Exception("All uploads failed")
        
        except Exception as e:
            log_activity(f"[Batch {batch_id}] Upload error: {str(e)}")
            if 'batch_key' in locals() and batch_key in kb_upload_progress:
                kb_upload_progress[batch_key]['is_uploading'] = False
            result['steps']['upload'] = {'success': False, 'error': str(e)}
            result['success'] = False
            return jsonify(result), 500
        
        # 检查整体成功状态
        result['success'] = all(
            step.get('success', False) 
            for step in result['steps'].values()
        )
        
        log_activity(f"[Batch {batch_id}] Complete! Success: {result['success']}")
        
        return jsonify(result)
    
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        log_activity(f"[Batch {batch_id if 'batch_id' in locals() else 'Unknown'}] Fatal error: {str(e)}")
        print(f"错误堆栈:\n{error_trace}")
        return jsonify({'success': False, 'error': str(e), 'traceback': error_trace}), 500


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
        log_activity(f"Failed to get batch details: {str(e)}")
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


@app.route('/api/batches/<path:batch_id>/label', methods=['PUT'])
def update_batch_label(batch_id):
    """更新批次的自定义标签"""
    try:
        from urllib.parse import unquote
        import json
        
        # URL 解码批次ID
        batch_id = unquote(batch_id)
        
        data = request.json
        custom_label = data.get('custom_label', '').strip()
        
        if not custom_label:
            return jsonify({'success': False, 'error': '批次标签不能为空'}), 400
        
        upload_dir = Path(DIRECTORIES["upload_dir"])
        batch_dir = upload_dir / batch_id
        
        if not batch_dir.exists():
            return jsonify({'success': False, 'error': '批次不存在'}), 404
        
        batch_info_file = batch_dir / ".batch_info.json"
        if not batch_info_file.exists():
            return jsonify({'success': False, 'error': '批次元数据不存在'}), 404
        
        # 读取并更新元数据
        with open(batch_info_file, 'r', encoding='utf-8') as f:
            batch_info = json.load(f)
        
        # 更新自定义标签
        batch_info['custom_label'] = custom_label
        
        # 保存更新后的元数据
        with open(batch_info_file, 'w', encoding='utf-8') as f:
            json.dump(batch_info, f, ensure_ascii=False, indent=2)
        
        log_activity(f"Batch {batch_id} label updated to: {custom_label}")
        
        return jsonify({
            'success': True,
            'message': '批次标签更新成功',
            'custom_label': custom_label
        })
        
    except Exception as e:
        log_activity(f"Failed to update batch label: {str(e)}")
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
        log_activity(f"Failed to update knowledge base label: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/batches/<path:batch_id>', methods=['DELETE'])
def delete_batch(batch_id):
    """删除整个批次"""
    try:
        from urllib.parse import unquote
        import shutil
        import json
        
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
        
        # 清理全局已处理邮件记录
        global_file = Path("eml_process/.global_processed_emails.json")
        if global_file.exists():
            try:
                with open(global_file, 'r', encoding='utf-8') as f:
                    global_processed = json.load(f)
                
                # 删除该批次的所有记录
                emails_to_remove = [
                    email_name for email_name, info in global_processed.items()
                    if info.get('batch_id') == batch_id
                ]
                
                for email_name in emails_to_remove:
                    del global_processed[email_name]
                
                # 保存更新后的全局文件
                with open(global_file, 'w', encoding='utf-8') as f:
                    json.dump(global_processed, f, ensure_ascii=False, indent=2)
                
                if emails_to_remove:
                    log_activity(f"从全局记录中删除 {len(emails_to_remove)} 个邮件记录")
            except Exception as e:
                log_activity(f"Failed to clean global email records: {str(e)}")
        
        log_activity(f"删除批次: {batch_id}")
        
        return jsonify({'success': True, 'message': f'批次 {batch_id} 已删除'})
    except Exception as e:
        log_activity(f"Failed to delete batch: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/batches/<path:batch_id>/reset', methods=['POST'])
def reset_batch(batch_id):
    """重置批次状态：重置处理状态并清理全局记录"""
    try:
        from urllib.parse import unquote
        import shutil
        import json
        
        # URL 解码批次ID
        batch_id = unquote(batch_id)
        
        upload_dir = Path(DIRECTORIES["upload_dir"])
        batch_dir = upload_dir / batch_id
        
        if not batch_dir.exists():
            return jsonify({'success': False, 'error': '批次不存在'}), 404
        
        # 删除处理目录中的批次
        processed_dir = Path(DIRECTORIES["processed_dir"])
        processed_batch_dir = processed_dir / batch_id
        if processed_batch_dir.exists():
            file_count = len(list(processed_batch_dir.glob("*.md")))
            shutil.rmtree(processed_batch_dir)
            log_activity(f"Deleted processed directory for batch {batch_id} ({file_count} files)")
        else:
            log_activity(f"Processed directory for batch {batch_id} does not exist, skipping")
        
        # 删除最终输出目录中的批次
        final_dir = Path(DIRECTORIES["final_output_dir"])
        final_batch_dir = final_dir / batch_id
        if final_batch_dir.exists():
            file_count = len(list(final_batch_dir.glob("*.md")))
            shutil.rmtree(final_batch_dir)
            log_activity(f"Deleted final_output directory for batch {batch_id} ({file_count} files)")
        else:
            log_activity(f"Final_output directory for batch {batch_id} does not exist, skipping")
        
        # 清理全局已处理邮件记录中该批次的记录
        global_file = Path("eml_process/.global_processed_emails.json")
        if global_file.exists():
            try:
                with open(global_file, 'r', encoding='utf-8') as f:
                    global_processed = json.load(f)
                
                # 删除该批次的所有记录
                emails_to_remove = [
                    email_name for email_name, info in global_processed.items()
                    if info.get('batch_id') == batch_id
                ]
                
                for email_name in emails_to_remove:
                    del global_processed[email_name]
                
                # 保存更新后的全局文件
                with open(global_file, 'w', encoding='utf-8') as f:
                    json.dump(global_processed, f, ensure_ascii=False, indent=2)
                
                if emails_to_remove:
                    log_activity(f"Removed {len(emails_to_remove)} email records from global tracking for batch {batch_id}")
                else:
                    log_activity(f"No email records found in global tracking for batch {batch_id}")
            except Exception as e:
                log_activity(f"Failed to clean global email records: {str(e)}")
        
        # 更新批次状态（完全重置，不保留知识库标签）
        batch_info_file = batch_dir / ".batch_info.json"
        if batch_info_file.exists():
            with open(batch_info_file, 'r', encoding='utf-8') as f:
                batch_info = json.load(f)
            
            # 重置状态，同时清除知识库标签
            batch_info['status'] = {
                'uploaded': True,
                'cleaned': False,
                'llm_processed': False,
                'uploaded_to_kb': False
            }
            
            # 清除知识库标签（如果存在）
            if 'kb_name' in batch_info:
                del batch_info['kb_name']
            
            # 保存
            with open(batch_info_file, 'w', encoding='utf-8') as f:
                json.dump(batch_info, f, ensure_ascii=False, indent=2)
        
        log_activity(f"Batch {batch_id} status reset to 'uploaded'")
        
        return jsonify({
            'success': True, 
            'message': f'批次 {batch_id} 已重置，可重新处理'
        })
    except Exception as e:
        log_activity(f"Failed to reset batch status: {str(e)}")
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

