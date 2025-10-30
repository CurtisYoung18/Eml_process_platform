#!/usr/bin/env python3
"""
邮件处理平台 - 清理维护工具
提供各种清理和维护功能
"""

import sys
import argparse
from pathlib import Path

# 导入清理模块
try:
    from cleanup_orphaned_batches import OrphanedBatchCleaner
    from clear_batch_from_global import clear_batch_from_global
except ImportError:
    print("❌ 无法导入清理模块，请确保 cleanup_orphaned_batches.py 和 clear_batch_from_global.py 存在")
    sys.exit(1)


def show_menu():
    """显示交互式菜单"""
    print("\n" + "="*60)
    print("邮件处理平台 - 清理维护工具")
    print("="*60)
    print("\n可用功能:\n")
    print("  1. 扫描垃圾批次文件")
    print("  2. 自动清理垃圾批次（预演模式）")
    print("  3. 自动清理垃圾批次（实际删除）")
    print("  4. 清理指定批次")
    print("  5. 清除批次的全局处理记录")
    print("  6. 查看批次状态")
    print("  0. 退出")
    print("\n" + "="*60)


def scan_orphaned_batches(min_files=5, age_days=7):
    """扫描垃圾批次"""
    print("\n🔍 扫描垃圾批次文件...")
    print(f"参数: 最小文件数={min_files}, 年龄阈值={age_days}天\n")
    
    cleaner = OrphanedBatchCleaner()
    orphaned = cleaner.find_orphaned_batches(min_file_count=min_files, age_days=age_days)
    cleaner.print_report(orphaned)
    
    return orphaned


def auto_clean_orphaned(dry_run=True, severity_levels=None):
    """自动清理垃圾批次"""
    if severity_levels is None:
        severity_levels = ['no_metadata', 'inconsistent']
    
    cleaner = OrphanedBatchCleaner()
    orphaned = cleaner.find_orphaned_batches()
    
    if not dry_run:
        total = sum(len(orphaned.get(level, [])) for level in severity_levels)
        if total == 0:
            print("✅ 没有需要清理的批次")
            return
        
        print(f"\n⚠️  将清理 {total} 个批次")
        confirm = input("确认继续? (yes/no): ")
        if confirm.lower() != 'yes':
            print("❌ 已取消")
            return
    
    cleaner.auto_clean(orphaned, severity_levels=severity_levels, dry_run=dry_run)


def clean_specific_batch(batch_id):
    """清理指定批次"""
    print(f"\n🗑️  清理批次: {batch_id}")
    
    cleaner = OrphanedBatchCleaner()
    upload_path = cleaner.upload_dir / batch_id
    
    if not upload_path.exists():
        print(f"❌ 批次不存在: {batch_id}")
        return
    
    # 显示批次信息
    batch_info_file = upload_path / ".batch_info.json"
    if batch_info_file.exists():
        import json
        try:
            with open(batch_info_file, 'r', encoding='utf-8') as f:
                info = json.load(f)
            print(f"\n批次信息:")
            print(f"  - 文件数: {info.get('file_count', 0)}")
            print(f"  - 上传时间: {info.get('upload_time', 'N/A')}")
            print(f"  - 标签: {info.get('custom_label', 'N/A')}")
            
            status = info.get('status', {})
            print(f"  - 已清洗: {'是' if status.get('cleaned') else '否'}")
            print(f"  - 已LLM处理: {'是' if status.get('llm_processed') else '否'}")
            print(f"  - 已上传知识库: {'是' if status.get('uploaded_to_kb') else '否'}")
        except:
            pass
    
    confirm = input(f"\n确认删除批次 '{batch_id}' 的所有文件? (yes/no): ")
    if confirm.lower() != 'yes':
        print("❌ 已取消")
        return
    
    cleaner.clean_batch(batch_id, remove_from_global=True)
    print(f"\n✅ 批次 {batch_id} 已清理完成")


def clear_global_record(batch_id):
    """清除批次的全局处理记录"""
    print(f"\n🔄 清除批次的全局处理记录: {batch_id}")
    
    confirm = input(f"确认清除批次 '{batch_id}' 的全局处理记录? (yes/no): ")
    if confirm.lower() != 'yes':
        print("❌ 已取消")
        return
    
    success = clear_batch_from_global(batch_id)
    if success:
        print(f"\n✅ 已清除批次 {batch_id} 的全局处理记录")
        print("   现在可以重新处理此批次")


def view_batch_status(batch_id=None):
    """查看批次状态"""
    import json
    from datetime import datetime
    
    upload_dir = Path("eml_process/uploads")
    
    if batch_id:
        # 查看指定批次
        batch_dirs = [upload_dir / batch_id]
    else:
        # 查看所有批次
        batch_dirs = sorted(
            [d for d in upload_dir.iterdir() if d.is_dir() and d.name.startswith('batch_')],
            key=lambda x: x.name,
            reverse=True
        )
    
    if not batch_dirs or (batch_id and not batch_dirs[0].exists()):
        print(f"❌ 批次不存在: {batch_id or '无批次'}")
        return
    
    print("\n📊 批次状态:\n")
    
    for batch_dir in batch_dirs[:20]:  # 最多显示20个
        batch_id = batch_dir.name
        batch_info_file = batch_dir / ".batch_info.json"
        
        if not batch_info_file.exists():
            print(f"⚠️  {batch_id} - 缺少元数据")
            continue
        
        try:
            with open(batch_info_file, 'r', encoding='utf-8') as f:
                info = json.load(f)
            
            upload_time = info.get('upload_time', 'N/A')
            if upload_time != 'N/A':
                try:
                    dt = datetime.fromisoformat(upload_time)
                    upload_time = dt.strftime('%Y-%m-%d %H:%M')
                except:
                    pass
            
            status = info.get('status', {})
            label = info.get('custom_label', 'N/A')
            file_count = info.get('file_count', 0)
            
            # 状态图标
            if status.get('uploaded_to_kb'):
                status_icon = "✅"
                status_text = "已完成全部流程"
            elif status.get('llm_processed'):
                status_icon = "🤖"
                status_text = "已LLM处理"
            elif status.get('cleaned'):
                status_icon = "🧹"
                status_text = "已清洗"
            else:
                status_icon = "📤"
                status_text = "仅上传"
            
            print(f"{status_icon} {batch_id}")
            print(f"   标签: {label}")
            print(f"   文件: {file_count} 个")
            print(f"   时间: {upload_time}")
            print(f"   状态: {status_text}")
            
            if info.get('kb_name'):
                print(f"   知识库: {info['kb_name']}")
            print()
            
        except Exception as e:
            print(f"❌ {batch_id} - 读取失败: {str(e)}")


def interactive_mode():
    """交互式模式"""
    while True:
        show_menu()
        choice = input("请选择功能 (0-6): ").strip()
        
        if choice == '0':
            print("\n再见！")
            break
        
        elif choice == '1':
            min_files = input("最小文件数 (默认5): ").strip() or "5"
            age_days = input("年龄阈值/天 (默认7): ").strip() or "7"
            scan_orphaned_batches(int(min_files), int(age_days))
            input("\n按回车继续...")
        
        elif choice == '2':
            auto_clean_orphaned(dry_run=True)
            input("\n按回车继续...")
        
        elif choice == '3':
            auto_clean_orphaned(dry_run=False)
            input("\n按回车继续...")
        
        elif choice == '4':
            batch_id = input("请输入批次ID: ").strip()
            if batch_id:
                clean_specific_batch(batch_id)
            input("\n按回车继续...")
        
        elif choice == '5':
            batch_id = input("请输入批次ID: ").strip()
            if batch_id:
                clear_global_record(batch_id)
            input("\n按回车继续...")
        
        elif choice == '6':
            batch_id = input("批次ID (留空查看全部): ").strip() or None
            view_batch_status(batch_id)
            input("\n按回车继续...")
        
        else:
            print("❌ 无效选择")
            input("\n按回车继续...")


def main():
    parser = argparse.ArgumentParser(
        description='邮件处理平台 - 清理维护工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 交互式模式
  python cleanup.py

  # 扫描垃圾批次
  python cleanup.py --scan

  # 自动清理垃圾批次（预演）
  python cleanup.py --auto-clean --dry-run

  # 自动清理垃圾批次（实际删除）
  python cleanup.py --auto-clean

  # 清理指定批次
  python cleanup.py --clean-batch batch_20251029_143252_mm1r

  # 清除批次的全局处理记录
  python cleanup.py --clear-global batch_20251029_143252_mm1r

  # 查看所有批次状态
  python cleanup.py --status

  # 查看指定批次状态
  python cleanup.py --status --batch batch_20251029_143252_mm1r
        """
    )
    
    parser.add_argument('--scan', action='store_true',
                       help='扫描垃圾批次')
    parser.add_argument('--auto-clean', action='store_true',
                       help='自动清理垃圾批次')
    parser.add_argument('--clean-batch', metavar='BATCH_ID',
                       help='清理指定批次')
    parser.add_argument('--clear-global', metavar='BATCH_ID',
                       help='清除批次的全局处理记录')
    parser.add_argument('--status', action='store_true',
                       help='查看批次状态')
    parser.add_argument('--batch', metavar='BATCH_ID',
                       help='指定批次ID（配合 --status 使用）')
    parser.add_argument('--dry-run', action='store_true',
                       help='预演模式（不实际删除）')
    parser.add_argument('--min-files', type=int, default=5,
                       help='最小文件数阈值')
    parser.add_argument('--age-days', type=int, default=7,
                       help='批次年龄阈值（天）')
    
    args = parser.parse_args()
    
    # 如果没有参数，进入交互模式
    if len(sys.argv) == 1:
        interactive_mode()
        return
    
    # 处理命令行参数
    if args.scan:
        scan_orphaned_batches(args.min_files, args.age_days)
    
    elif args.auto_clean:
        auto_clean_orphaned(dry_run=args.dry_run)
    
    elif args.clean_batch:
        clean_specific_batch(args.clean_batch)
    
    elif args.clear_global:
        clear_global_record(args.clear_global)
    
    elif args.status:
        view_batch_status(args.batch)
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()

