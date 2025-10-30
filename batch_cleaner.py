#!/usr/bin/env python3
"""
批次清理工具 - 清理垃圾批次和释放磁盘空间
支持：
1. 检测上传失败的垃圾批次（文件数过少）
2. 清理仅上传但未处理的批次
3. 清除全局处理记录
"""

import json
import shutil
import sys
import argparse
from pathlib import Path
from datetime import datetime


class BatchCleaner:
    def __init__(self, base_dir="eml_process"):
        self.base_dir = Path(base_dir)
        self.upload_dir = self.base_dir / "uploads"
        self.processed_dir = self.base_dir / "processed"
        self.final_dir = self.base_dir / "final_output"
        self.global_file = self.base_dir / ".global_processed_emails.json"
    
    def scan_batches(self, min_file_threshold=100):
        """
        扫描所有批次，分类：
        - JUNK: 垃圾批次（文件数少于阈值）
        - UPLOADED_ONLY: 仅上传未处理
        - CLEANED: 已清洗
        - LLM_DONE: 已LLM处理
        - COMPLETED: 已完成全部流程
        - NO_METADATA: 缺少元数据
        - CORRUPTED: 元数据损坏
        """
        if not self.upload_dir.exists():
            print("[ERROR] uploads directory not found")
            return []
        
        batches = []
        
        for batch_dir in sorted(self.upload_dir.iterdir()):
            if not batch_dir.is_dir() or not batch_dir.name.startswith('batch_'):
                continue
            
            batch_info_file = batch_dir / ".batch_info.json"
            
            # 统计实际文件数
            actual_file_count = len(list(batch_dir.glob("*.eml")))
            
            # 检查是否有元数据
            if not batch_info_file.exists():
                status = "NO_METADATA"
                file_count = actual_file_count
                upload_time = None
                cleaned = False
                llm_processed = False
                uploaded_to_kb = False
            else:
                try:
                    with open(batch_info_file, 'r', encoding='utf-8') as f:
                        info = json.load(f)
                    
                    file_count = info.get('file_count', actual_file_count)
                    upload_time = info.get('upload_time')
                    
                    batch_status = info.get('status', {})
                    cleaned = batch_status.get('cleaned', False)
                    llm_processed = batch_status.get('llm_processed', False)
                    uploaded_to_kb = batch_status.get('uploaded_to_kb', False)
                    
                    # 判断状态
                    if uploaded_to_kb:
                        status = "COMPLETED"
                    elif llm_processed:
                        status = "LLM_DONE"
                    elif cleaned:
                        status = "CLEANED"
                    else:
                        status = "UPLOADED_ONLY"
                        
                except Exception as e:
                    status = "CORRUPTED"
                    file_count = actual_file_count
                    upload_time = None
                    cleaned = False
                    llm_processed = False
                    uploaded_to_kb = False
            
            # 判断是否为垃圾批次（文件数过少）
            if file_count < min_file_threshold and status in ["UPLOADED_ONLY", "NO_METADATA"]:
                status = "JUNK"
            
            batches.append({
                'batch_id': batch_dir.name,
                'status': status,
                'file_count': file_count,
                'actual_file_count': actual_file_count,
                'upload_time': upload_time,
                'cleaned': cleaned,
                'llm_processed': llm_processed,
                'uploaded_to_kb': uploaded_to_kb,
                'path': batch_dir
            })
        
        return batches
    
    def print_batches(self, batches, filter_status=None):
        """打印批次信息"""
        if filter_status:
            batches = [b for b in batches if b['status'] in filter_status]
        
        if not batches:
            print("No batches found")
            return
        
        print(f"\nFound {len(batches)} batches:\n")
        print(f"{'Batch ID':<35} {'Files':<8} {'Status':<15} {'Upload Time'}")
        print("-" * 90)
        
        for batch in batches:
            batch_id = batch['batch_id']
            file_count = batch['file_count']
            status = batch['status']
            upload_time = batch['upload_time'] or 'N/A'
            
            if upload_time != 'N/A':
                try:
                    dt = datetime.fromisoformat(upload_time)
                    upload_time = dt.strftime('%Y-%m-%d %H:%M')
                except:
                    pass
            
            print(f"{batch_id:<35} {file_count:<8} {status:<15} {upload_time}")
    
    def delete_batch(self, batch_id, remove_from_global=True, verbose=True):
        """删除指定批次的所有文件和记录"""
        deleted = []
        
        # 删除上传目录
        upload_path = self.upload_dir / batch_id
        if upload_path.exists():
            shutil.rmtree(upload_path)
            deleted.append(f"uploads/{batch_id}")
            if verbose:
                print(f"  [OK] Deleted: uploads/{batch_id}")
        
        # 删除处理目录
        processed_path = self.processed_dir / batch_id
        if processed_path.exists():
            shutil.rmtree(processed_path)
            deleted.append(f"processed/{batch_id}")
            if verbose:
                print(f"  [OK] Deleted: processed/{batch_id}")
        
        # 删除最终输出目录
        final_path = self.final_dir / batch_id
        if final_path.exists():
            shutil.rmtree(final_path)
            deleted.append(f"final_output/{batch_id}")
            if verbose:
                print(f"  [OK] Deleted: final_output/{batch_id}")
        
        # 从全局记录中删除
        if remove_from_global and self.global_file.exists():
            with open(self.global_file, 'r', encoding='utf-8') as f:
                global_data = json.load(f)
            
            before_count = len(global_data)
            global_data = {
                k: v for k, v in global_data.items()
                if v.get('batch_id') != batch_id
            }
            after_count = len(global_data)
            removed = before_count - after_count
            
            if removed > 0:
                with open(self.global_file, 'w', encoding='utf-8') as f:
                    json.dump(global_data, f, ensure_ascii=False, indent=2)
                if verbose:
                    print(f"  [OK] Removed {removed} files from global record")
        
        return deleted
    
    def clean_junk_batches(self, dry_run=False):
        """清理垃圾批次（文件数过少的上传失败批次）"""
        batches = self.scan_batches()
        junk_batches = [b for b in batches if b['status'] == 'JUNK']
        
        if not junk_batches:
            print("[INFO] No junk batches found")
            return
        
        print(f"\n[INFO] Found {len(junk_batches)} junk batches:")
        self.print_batches(junk_batches)
        
        if dry_run:
            print("\n[DRY RUN] Would delete these batches")
            return
        
        print(f"\n[WARNING] Will delete {len(junk_batches)} junk batches")
        confirm = input("Continue? (yes/no): ").strip().lower()
        
        if confirm != 'yes':
            print("[CANCELLED]")
            return
        
        print("\n[INFO] Cleaning junk batches...")
        for batch in junk_batches:
            print(f"\nCleaning: {batch['batch_id']}")
            self.delete_batch(batch['batch_id'], remove_from_global=True)
        
        print(f"\n[SUCCESS] Cleaned {len(junk_batches)} junk batches")
    
    def clean_uploaded_only(self, dry_run=False):
        """清理仅上传但未处理的批次"""
        batches = self.scan_batches()
        uploaded_only = [b for b in batches if b['status'] == 'UPLOADED_ONLY']
        
        if not uploaded_only:
            print("[INFO] No uploaded-only batches found")
            return
        
        print(f"\n[INFO] Found {len(uploaded_only)} uploaded-only batches:")
        self.print_batches(uploaded_only)
        
        if dry_run:
            print("\n[DRY RUN] Would delete these batches")
            return
        
        print(f"\n[WARNING] Will delete {len(uploaded_only)} uploaded-only batches")
        confirm = input("Continue? (yes/no): ").strip().lower()
        
        if confirm != 'yes':
            print("[CANCELLED]")
            return
        
        print("\n[INFO] Cleaning uploaded-only batches...")
        for batch in uploaded_only:
            print(f"\nCleaning: {batch['batch_id']}")
            self.delete_batch(batch['batch_id'], remove_from_global=True)
        
        print(f"\n[SUCCESS] Cleaned {len(uploaded_only)} uploaded-only batches")
    
    def clear_global_record(self, batch_id):
        """清除指定批次的全局处理记录"""
        if not self.global_file.exists():
            print(f"[ERROR] Global record file not found: {self.global_file}")
            return False
        
        with open(self.global_file, 'r', encoding='utf-8') as f:
            global_data = json.load(f)
        
        files_to_remove = [
            filename for filename, info in global_data.items() 
            if info.get('batch_id') == batch_id
        ]
        
        if not files_to_remove:
            print(f"[WARNING] Batch {batch_id} not found in global record")
            return False
        
        print(f"[INFO] Found {len(files_to_remove)} files for batch {batch_id}")
        
        for filename in files_to_remove:
            del global_data[filename]
        
        with open(self.global_file, 'w', encoding='utf-8') as f:
            json.dump(global_data, f, ensure_ascii=False, indent=2)
        
        print(f"[SUCCESS] Cleared {len(files_to_remove)} files from global record")
        print(f"           Batch {batch_id} can now be reprocessed")
        
        return True


def main():
    parser = argparse.ArgumentParser(
        description='Batch Cleaner - Clean junk batches and free disk space',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scan all batches
  python batch_cleaner.py --scan

  # Clean junk batches (file count < 100)
  python batch_cleaner.py --clean-junk

  # Clean junk batches with custom threshold
  python batch_cleaner.py --clean-junk --min-files 50

  # Clean uploaded-only batches
  python batch_cleaner.py --clean-uploaded

  # Dry run (preview without deleting)
  python batch_cleaner.py --clean-junk --dry-run

  # Delete specific batch
  python batch_cleaner.py --delete-batch batch_20251029_143252_mm1r

  # Clear global record for a batch (allow reprocessing)
  python batch_cleaner.py --clear-global batch_20251029_143252_mm1r
        """
    )
    
    parser.add_argument('--scan', action='store_true',
                       help='Scan and display all batches')
    parser.add_argument('--clean-junk', action='store_true',
                       help='Clean junk batches (file count < min-files)')
    parser.add_argument('--clean-uploaded', action='store_true',
                       help='Clean uploaded-only batches')
    parser.add_argument('--delete-batch', metavar='BATCH_ID',
                       help='Delete specific batch')
    parser.add_argument('--clear-global', metavar='BATCH_ID',
                       help='Clear global record for a batch')
    parser.add_argument('--min-files', type=int, default=100,
                       help='Minimum file count threshold for junk detection (default: 100)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Dry run (preview without deleting)')
    parser.add_argument('--filter', choices=['JUNK', 'UPLOADED_ONLY', 'CLEANED', 'LLM_DONE', 'COMPLETED'],
                       help='Filter batches by status when scanning')
    
    args = parser.parse_args()
    
    cleaner = BatchCleaner()
    
    if args.scan:
        batches = cleaner.scan_batches(min_file_threshold=args.min_files)
        filter_status = [args.filter] if args.filter else None
        cleaner.print_batches(batches, filter_status=filter_status)
        
        # Statistics
        stats = {}
        for batch in batches:
            status = batch['status']
            stats[status] = stats.get(status, 0) + 1
        
        print("\nStatistics:")
        for status, count in sorted(stats.items()):
            print(f"  {status}: {count}")
    
    elif args.clean_junk:
        cleaner.clean_junk_batches(dry_run=args.dry_run)
    
    elif args.clean_uploaded:
        cleaner.clean_uploaded_only(dry_run=args.dry_run)
    
    elif args.delete_batch:
        print(f"\n[INFO] Deleting batch: {args.delete_batch}")
        cleaner.delete_batch(args.delete_batch, remove_from_global=True)
        print(f"\n[SUCCESS] Batch {args.delete_batch} deleted")
    
    elif args.clear_global:
        cleaner.clear_global_record(args.clear_global)
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()

