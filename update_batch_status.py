#!/usr/bin/env python3
"""
手动更新批次状态的脚本
用于修复批次状态标记
"""
import sys
from pathlib import Path
from datetime import datetime
import json

# 项目根目录
PROJECT_ROOT = Path(__file__).parent

# 直接定义目录路径（避免导入依赖）
DIRECTORIES = {
    "upload_dir": PROJECT_ROOT / "eml_process" / "uploads",
    "processed_dir": PROJECT_ROOT / "eml_process" / "processed",
    "final_output_dir": PROJECT_ROOT / "eml_process" / "final_output",
    "log_dir": PROJECT_ROOT / "logs",
}

def log_activity(message):
    """简单的日志记录"""
    log_file = PROJECT_ROOT / "logs" / "activity.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] {message}\n")
    print(f"[{timestamp}] {message}")

def update_batch_status_file(batch_id: str, status_key: str, status_value: bool = True):
    """更新批次状态到元数据文件"""
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
        
        # 显示当前状态
        current_status = batch_info.get('status', {})
        print(f"\n当前批次状态:")
        print(f"   uploaded_to_kb: {current_status.get('uploaded_to_kb', False)}")
        print(f"   cleaned: {current_status.get('cleaned', False)}")
        print(f"   llm_processed: {current_status.get('llm_processed', False)}")
        
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
        
        print(f"\n[成功] 批次状态已更新:")
        print(f"   {status_key} = {status_value}")
        print(f"   更新时间: {batch_info['processing_history'].get(f'{status_key}_at', 'N/A')}")
        
        log_activity(f"Manual update: Batch {batch_id} status updated: {status_key} = {status_value}")
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
    status_key = 'uploaded_to_kb'
    
    print(f"正在更新批次状态...")
    print(f"   批次ID: {batch_id}")
    print(f"   状态键: {status_key}")
    print(f"   状态值: True")
    
    success = update_batch_status_file(batch_id, status_key, True)
    
    if success:
        print(f"\n更新成功！批次 {batch_id} 已标记为已上传到知识库")
    else:
        print(f"\n更新失败，请检查错误信息")
        sys.exit(1)
