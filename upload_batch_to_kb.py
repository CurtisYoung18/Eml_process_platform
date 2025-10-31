#!/usr/bin/env python3
"""
手动上传批次文件到知识库的脚本
"""
import sys
import os
from pathlib import Path

# 简单的环境变量读取（不依赖dotenv）
def load_env():
    """读取.env文件"""
    env_file = Path('.env')
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

# 加载环境变量
load_env()

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from tools.api_clients.knowledge_base_api import KnowledgeBaseAPI

# 直接定义目录路径（避免导入config依赖）
DIRECTORIES = {
    "final_output_dir": PROJECT_ROOT / "eml_process" / "final_output",
}

def log_activity(message):
    """简单的日志记录"""
    log_file = PROJECT_ROOT / "logs" / "activity.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    from datetime import datetime
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] {message}\n")
    print(f"[{timestamp}] {message}")

def get_kb_api_key():
    """从环境变量获取KB API Key"""
    # 尝试多种可能的变量名（按优先级）
    possible_keys = [
        'GPTBOTS_KB_API_KEY_1', 
        'KB_API_KEY_1', 
        'KB_API_KEY', 
        'KNOWLEDGE_BASE_API_KEY_1', 
        'KNOWLEDGE_BASE_API_KEY',
        'GPTBOTS_KB_API_KEY'
    ]
    for key_name in possible_keys:
        kb_key = os.getenv(key_name)
        if kb_key:
            print(f"[信息] 使用API Key: {key_name}")
            return kb_key
    
    # 如果都没找到，列出所有KB相关的环境变量
    print("[错误] 未找到KB API Key")
    print("[信息] 当前KB相关的环境变量:")
    for key, value in os.environ.items():
        if 'KB' in key.upper() or 'KNOWLEDGE' in key.upper():
            masked_value = value[:8] + '...' if len(value) > 8 else value
            print(f"  {key} = {masked_value}")
    return None

def find_knowledge_base(kb_client, target_name):
    """查找指定名称的知识库"""
    print(f"正在查找知识库: {target_name}")
    knowledge_bases = kb_client.list_knowledge_bases()
    
    if not knowledge_bases:
        print("[错误] 无法获取知识库列表")
        return None
    
    print(f"\n找到 {len(knowledge_bases)} 个知识库:")
    for kb in knowledge_bases:
        kb_id = kb.get('id', 'N/A')
        kb_name = kb.get('name', 'N/A')
        print(f"  - {kb_name} (ID: {kb_id})")
        if kb_name == target_name:
            print(f"\n[成功] 找到目标知识库: {kb_name} (ID: {kb_id})")
            return kb_id
    
    print(f"\n[错误] 未找到名为 '{target_name}' 的知识库")
    return None

def upload_batch_files(batch_id, kb_id, kb_client):
    """上传批次文件到知识库"""
    final_dir = Path(DIRECTORIES["final_output_dir"])
    batch_dir = final_dir / batch_id
    
    if not batch_dir.exists():
        print(f"[错误] 批次目录不存在: {batch_dir}")
        return False
    
    # 获取所有md文件
    md_files = list(batch_dir.glob("*.md"))
    if not md_files:
        print(f"[错误] 批次目录中没有找到 .md 文件: {batch_dir}")
        return False
    
    print(f"\n找到 {len(md_files)} 个文件，开始上传...")
    print(f"目标知识库ID: {kb_id}")
    print(f"使用chunk_token: 600, splitter: PARAGRAPH\n")
    
    successful_uploads = 0
    failed_uploads = 0
    
    for i, md_file in enumerate(md_files, 1):
        try:
            # 读取文件内容
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 上传文件
            result = kb_client.upload_markdown_content(
                content=content,
                filename=md_file.name,
                knowledge_base_id=kb_id,
                chunk_token=600,
                splitter="PARAGRAPH"
            )
            
            if result and 'error' not in result:
                successful_uploads += 1
                print(f"[{i}/{len(md_files)}] ✓ 成功: {md_file.name}")
                log_activity(f"Manual upload: {md_file.name} -> KB {kb_id}")
            else:
                failed_uploads += 1
                error_msg = result.get('error', 'Unknown error') if result else 'No response'
                print(f"[{i}/{len(md_files)}] ✗ 失败: {md_file.name} - {error_msg}")
                log_activity(f"Manual upload failed: {md_file.name} -> {error_msg}")
            
            # 延迟避免API限流（每3个文件延迟0.5秒）
            if i % 3 == 0:
                import time
                time.sleep(0.5)
                
        except Exception as e:
            failed_uploads += 1
            print(f"[{i}/{len(md_files)}] ✗ 异常: {md_file.name} - {str(e)}")
            log_activity(f"Manual upload exception: {md_file.name} -> {str(e)}")
    
    print(f"\n{'='*60}")
    print(f"上传完成:")
    print(f"  成功: {successful_uploads} 个")
    print(f"  失败: {failed_uploads} 个")
    print(f"  总计: {len(md_files)} 个")
    print(f"{'='*60}")
    
    return successful_uploads > 0

if __name__ == '__main__':
    import sys
    import io
    
    # 设置标准输出为UTF-8编码
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    
    batch_id = 'batch_20251030_174844_binf'
    kb_name = '通用2'
    
    print(f"准备上传批次到知识库...")
    print(f"  批次ID: {batch_id}")
    print(f"  目标知识库: {kb_name}")
    print(f"{'='*60}\n")
    
    # 获取API Key
    kb_api_key = get_kb_api_key()
    if not kb_api_key:
        sys.exit(1)
    
    # 初始化知识库客户端
    kb_client = KnowledgeBaseAPI(kb_api_key)
    
    # 查找知识库
    kb_id = find_knowledge_base(kb_client, kb_name)
    if not kb_id:
        sys.exit(1)
    
    # 上传文件
    print(f"\n{'='*60}")
    print(f"开始上传批次文件...")
    print(f"{'='*60}")
    
    success = upload_batch_files(batch_id, kb_id, kb_client)
    
    if success:
        print(f"\n[成功] 批次 {batch_id} 已上传到知识库 '{kb_name}'")
        log_activity(f"Manual upload completed: batch {batch_id} -> KB {kb_name} ({kb_id})")
    else:
        print(f"\n[失败] 上传失败，请检查错误信息")
        sys.exit(1)

