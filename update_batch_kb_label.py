#!/usr/bin/env python3
"""
手动更新批次知识库标签的脚本
"""
import sys
import os
from pathlib import Path
from datetime import datetime
import json

# 项目根目录
PROJECT_ROOT = Path(__file__).parent

# 直接定义目录路径
DIRECTORIES = {
    "upload_dir": PROJECT_ROOT / "eml_process" / "uploads",
}

def log_activity(message):
    """简单的日志记录"""
    log_file = PROJECT_ROOT / "logs" / "activity.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] {message}\n")
    print(f"[{timestamp}] {message}")

def update_batch_kb_label(batch_id: str, kb_name: str):
    """更新批次的知识库标签"""
    try:
        upload_dir = Path(DIRECTORIES["upload_dir"])
        batch_dir = upload_dir / batch_id
        
        if not batch_dir.exists():
            print(f"[错误] 批次目录不存在: {batch_id}")
            print(f"   路径: {batch_dir}")
            return False
        
        batch_info_file = batch_dir / ".batch_info.json"
        if not batch_info_file.exists():
            print(f"[错误] 批次元数据文件不存在: {batch_id}")
            print(f"   路径: {batch_info_file}")
            return False
        
        # 读取并更新元数据
        with open(batch_info_file, 'r', encoding='utf-8') as f:
            batch_info = json.load(f)
        
        # 显示当前标签
        current_kb_name = batch_info.get('kb_name', '未设置')
        print(f"\n当前知识库标签: {current_kb_name}")
        
        # 更新知识库名称
        batch_info['kb_name'] = kb_name
        batch_info['kb_labeled_at'] = datetime.now().isoformat()
        
        # 保存
        with open(batch_info_file, 'w', encoding='utf-8') as f:
            json.dump(batch_info, f, ensure_ascii=False, indent=2)
        
        print(f"\n[成功] 批次知识库标签已更新:")
        print(f"   kb_name = {kb_name}")
        print(f"   更新时间: {batch_info['kb_labeled_at']}")
        
        log_activity(f"Manual update: Batch {batch_id} KB label updated to: {kb_name}")
        return True
    except Exception as e:
        print(f"[错误] 更新失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    import sys
    import io
    
    # 设置标准输出为UTF-8编码
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    
    batch_id = 'batch_20251030_174844_binf'
    kb_name = '通用2'
    
    print(f"正在更新批次知识库标签...")
    print(f"   批次ID: {batch_id}")
    print(f"   知识库名称: {kb_name}")
    
    success = update_batch_kb_label(batch_id, kb_name)
    
    if success:
        print(f"\n[成功] 批次 {batch_id} 已标记知识库: {kb_name}")
    else:
        print(f"\n[失败] 更新失败，请检查错误信息")
        sys.exit(1)

