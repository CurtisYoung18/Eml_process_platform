#!/usr/bin/env python3
"""
邮件清洗脚本 - 第一轮清洗
功能：解析EML文件，去重，生成Markdown格式文件
"""

import os
import re
import email
import json
from pathlib import Path
from email.header import decode_header
from email.utils import parsedate_to_datetime
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import hashlib

class EmailCleaner:
    def __init__(self, input_dir: str = "Eml", output_dir: str = "eml_process/processed", batch_mode: bool = True):
        """
        初始化邮件清洗器
        
        Args:
            input_dir: 输入EML文件目录
            output_dir: 输出Markdown文件目录
            batch_mode: 是否使用批次模式（自动检测批次文件夹）
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.batch_mode = batch_mode
        
        # 存储处理过的邮件信息
        self.processed_emails = []
        self.duplicate_info = []
        
        # 全局邮件跟踪文件
        self.global_processed_file = Path("eml_process/.global_processed_emails.json")
        self.global_processed_emails = self._load_global_processed()
        
    def _load_global_processed(self) -> Dict:
        """加载全局已处理邮件记录"""
        if self.global_processed_file.exists():
            try:
                with open(self.global_processed_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"[WARNING] Failed to load global processed emails: {e}")
        return {}
    
    def _save_global_processed(self):
        """保存全局已处理邮件记录"""
        try:
            self.global_processed_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.global_processed_file, 'w', encoding='utf-8') as f:
                json.dump(self.global_processed_emails, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[WARNING] Failed to save global processed emails: {e}")
        
    def decode_email_header(self, header_value: str) -> str:
        """解码邮件头部信息"""
        if not header_value:
            return ""
        
        try:
            decoded_parts = decode_header(header_value)
            result = ""
            for part, encoding in decoded_parts:
                if isinstance(part, bytes):
                    if encoding:
                        result += part.decode(encoding)
                    else:
                        result += part.decode('utf-8', errors='ignore')
                else:
                    result += str(part)
            return result.strip()
        except Exception as e:
            print(f"[WARNING] Header decode failed: {e}")
            return str(header_value)
    
    def extract_email_content(self, msg) -> str:
        """提取邮件正文内容"""
        content = ""
        
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                
                # 只处理文本内容，忽略附件
                if content_type == "text/plain" and "attachment" not in content_disposition:
                    try:
                        payload = part.get_payload(decode=True)
                        if payload:
                            charset = part.get_content_charset() or 'utf-8'
                            content += payload.decode(charset, errors='ignore') + "\n"
                    except Exception as e:
                        print(f"[WARNING] Content decode failed: {e}")
                        
                elif content_type == "text/html" and "attachment" not in content_disposition and not content:
                    # 如果没有纯文本，尝试HTML（简单处理）
                    try:
                        payload = part.get_payload(decode=True)
                        if payload:
                            charset = part.get_content_charset() or 'utf-8'
                            html_content = payload.decode(charset, errors='ignore')
                            # 简单去除HTML标签
                            clean_content = re.sub(r'<[^>]+>', '', html_content)
                            content += clean_content + "\n"
                    except Exception as e:
                        print(f"[WARNING] HTML content decode failed: {e}")
        else:
            # 非多部分邮件
            try:
                payload = msg.get_payload(decode=True)
                if payload:
                    charset = msg.get_content_charset() or 'utf-8'
                    content = payload.decode(charset, errors='ignore')
            except Exception as e:
                print(f"[WARNING] Email content decode failed: {e}")
        
        return content.strip()
    
    def clean_content(self, content: str) -> str:
        """清理邮件内容"""
        if not content:
            return ""
        
        # 移除多余的空白行
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
        
        # 移除邮件头部的技术信息（Received, Message-ID等）
        lines = content.split('\n')
        cleaned_lines = []
        skip_technical = False
        
        for line in lines:
            line = line.strip()
            
            # 跳过技术头部信息
            if line.startswith(('Received:', 'Message-ID:', 'Return-Path:', 'X-')):
                skip_technical = True
                continue
            elif skip_technical and line and not line.startswith(' '):
                skip_technical = False
            
            if not skip_technical:
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines).strip()
    
    def parse_eml_file(self, file_path: Path) -> Optional[Dict]:
        """解析单个EML文件"""
        try:
            with open(file_path, 'rb') as f:
                msg = email.message_from_bytes(f.read())
            
            # 提取基本信息
            email_info = {
                'filename': file_path.name,
                'from': self.decode_email_header(msg.get('From', '')),
                'to': self.decode_email_header(msg.get('To', '')),
                'cc': self.decode_email_header(msg.get('Cc', '')),
                'subject': self.decode_email_header(msg.get('Subject', '')),
                'date': msg.get('Date', ''),
                'content': self.extract_email_content(msg)
            }
            
            # 解析日期
            try:
                if email_info['date']:
                    parsed_date = parsedate_to_datetime(email_info['date'])
                    email_info['parsed_date'] = parsed_date
                    email_info['date_str'] = parsed_date.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    email_info['parsed_date'] = None
                    email_info['date_str'] = "未知时间"
            except:
                email_info['parsed_date'] = None
                email_info['date_str'] = "未知时间"
            
            # 清理内容
            email_info['cleaned_content'] = self.clean_content(email_info['content'])
            
            # 生成内容哈希用于去重
            content_for_hash = email_info['cleaned_content'].lower().replace(' ', '').replace('\n', '')
            email_info['content_hash'] = hashlib.md5(content_for_hash.encode()).hexdigest()
            
            return email_info
            
        except Exception as e:
            print(f"❌ 解析文件失败 {file_path.name}: {e}")
            return None
    
    def find_duplicates(self, emails: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """查找并处理重复邮件 - 优化版：使用hash加速，减少内存"""
        print(f"[DEDUP] Starting optimized deduplication for {len(emails)} emails...")
        # 按内容长度排序（长的在前）
        emails_sorted = sorted(emails, key=lambda x: len(x['cleaned_content']), reverse=True)
        
        unique_emails = []
        duplicates = []
        
        # 【内存优化】使用hash字典加速查找，避免重复的正则化计算
        unique_normalized = {}  # {email_index: normalized_content}
        unique_hashes = set()  # 快速hash查找集合
        
        for idx, email_info in enumerate(emails_sorted):
            # 标准化内容用于比较 - 移除所有空白字符和换行
            current_content = re.sub(r'\s+', '', email_info['cleaned_content'].lower())
            current_hash = hashlib.md5(current_content.encode('utf-8')).hexdigest()
            
            is_duplicate = False
            container_email = None
            
            # 【优化1】快速hash检查：完全相同的内容
            if current_hash in unique_hashes:
                # 找到hash匹配的邮件
                for i, u_email in enumerate(unique_emails):
                    u_content = unique_normalized.get(i, "")
                    u_hash = hashlib.md5(u_content.encode('utf-8')).hexdigest() if u_content else ""
                    if u_hash == current_hash:
                        is_duplicate = True
                        container_email = u_email
                        break
            
            # 【优化2】如果hash不同，检查内容包含（限制检查范围以节省内存）
            if not is_duplicate:
                # 只与最近的100个唯一邮件比较，避免O(n²)爆炸
                check_range = min(len(unique_emails), 100)
                for i in range(check_range):
                    unique_email = unique_emails[-(i+1)]  # 从最新的开始检查
                    
                    # 获取或计算归一化内容
                    if len(unique_emails) - (i+1) not in unique_normalized:
                        unique_content = re.sub(r'\s+', '', unique_email['cleaned_content'].lower())
                        unique_normalized[len(unique_emails) - (i+1)] = unique_content
                    else:
                        unique_content = unique_normalized[len(unique_emails) - (i+1)]
                    
                    # 100%包含检测：较短内容必须完全在较长内容中
                    if (len(current_content) > 0 and 
                        len(current_content) <= len(unique_content) and 
                        current_content in unique_content):
                        is_duplicate = True
                        container_email = unique_email
                        break
            
            if is_duplicate and container_email:
                # 记录重复信息
                duplicates.append({
                    'duplicate_file': email_info['filename'],
                    'duplicate_subject': email_info['subject'],
                    'contained_by_file': container_email['filename'],
                    'contained_by_subject': container_email['subject'],
                    'content_length_ratio': f"{len(current_content)}/?"
                })
                
                # 在容器邮件中记录包含的源文件
                if 'contained_files' not in container_email:
                    container_email['contained_files'] = []
                container_email['contained_files'].append(email_info['filename'])
                
                print(f"[DUPLICATE] Found 100% duplicate: {email_info['filename']} contained in {container_email['filename']}")
                
            else:
                # 不是重复邮件，添加到唯一列表
                unique_emails.append(email_info)
                unique_normalized[len(unique_emails) - 1] = current_content
                unique_hashes.add(current_hash)
                print(f"[UNIQUE] Unique email: {email_info['filename']} (length: {len(current_content)})")
            
            # 【内存优化】定期清理旧的归一化内容缓存，只保留最近100个
            if len(unique_normalized) > 150:
                # 删除最旧的50个缓存项
                keys_to_remove = sorted(unique_normalized.keys())[:50]
                for key in keys_to_remove:
                    del unique_normalized[key]
            
            # 进度显示
            if (idx + 1) % 100 == 0:
                print(f"[PROGRESS] Processed {idx + 1}/{len(emails_sorted)} emails, {len(unique_emails)} unique, {len(duplicates)} duplicates")
        
        print(f"[DEDUP] Completed: {len(unique_emails)} unique, {len(duplicates)} duplicates")
        return unique_emails, duplicates
    
    def generate_markdown(self, email_info: Dict) -> str:
        """生成Markdown格式的邮件内容"""
        md_content = []
        
        # 标题
        md_content.append(f"# 邮件内容 - {email_info['filename']}")
        md_content.append("")
        
        # 基本信息
        md_content.append("## Email Information")
        md_content.append("")
        md_content.append(f"- **源文件名**: `{email_info['filename']}`")
        md_content.append(f"- **发件人**: {email_info['from']}")
        md_content.append(f"- **收件人**: {email_info['to']}")
        
        if email_info['cc']:
            md_content.append(f"- **抄送**: {email_info['cc']}")
        
        md_content.append(f"- **主题**: {email_info['subject']}")
        md_content.append(f"- **时间**: {email_info['date_str']}")
        
        # 如果包含其他文件，列出来
        if 'contained_files' in email_info:
            md_content.append(f"- **包含的其他邮件**: {len(email_info['contained_files'])} 封")
            md_content.append("")
            md_content.append("### Source Files List")
            md_content.append("")
            for contained_file in email_info['contained_files']:
                md_content.append(f"- `{contained_file}`")
        
        md_content.append("")
        
        # 邮件内容
        md_content.append("## 📄 邮件内容")
        md_content.append("")
        
        if email_info['cleaned_content']:
            # 将邮件内容按段落分割，保持格式
            content_lines = email_info['cleaned_content'].split('\n')
            for line in content_lines:
                if line.strip():
                    md_content.append(line)
                else:
                    md_content.append("")
        else:
            md_content.append("*（邮件内容为空或无法解析）*")
        
        md_content.append("")
        md_content.append("---")
        md_content.append(f"*处理时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
        
        return '\n'.join(md_content)
    
    def save_markdown_file(self, email_info: Dict, batch_id: Optional[str] = None) -> str:
        """保存Markdown文件"""
        # 生成文件名（去除.eml扩展名，添加.md）
        base_name = email_info['filename'].replace('.eml', '')
        md_filename = f"{base_name}.md"
        
        # 如果有批次ID，创建批次子目录
        if batch_id:
            batch_output_dir = self.output_dir / batch_id
            batch_output_dir.mkdir(parents=True, exist_ok=True)
            md_path = batch_output_dir / md_filename
        else:
            md_path = self.output_dir / md_filename
        
        # 生成Markdown内容
        md_content = self.generate_markdown(email_info)
        
        # 保存文件
        try:
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(md_content)
            return str(md_path)
        except Exception as e:
            print(f"[ERROR] Failed to save Markdown file {md_filename}: {e}")
            return ""
    
    def process_batch(self, batch_dir: Path, batch_id: str) -> Dict:
        """处理单个批次"""
        print(f"[INFO] Processing batch: {batch_id}")
        
        # 读取批次元数据
        batch_info_file = batch_dir / ".batch_info.json"
        batch_info = None
        
        if batch_info_file.exists():
            with open(batch_info_file, 'r', encoding='utf-8') as f:
                batch_info = json.load(f)
            
            # 检查是否已处理
            if batch_info.get('status', {}).get('cleaned', False):
                print(f"[INFO] Batch {batch_id} already cleaned, skipping...")
                return {
                    "success": True,
                    "batch_id": batch_id,
                    "skipped": True,
                    "message": "批次已处理"
                }
        
        # 获取批次中的所有EML文件
        eml_files = list(batch_dir.glob("*.eml"))
        
        if not eml_files:
            print(f"[WARNING] No EML files found in batch {batch_id}")
            return {"success": False, "batch_id": batch_id, "message": "未找到EML文件"}
        
        print(f"[FOUND] Found {len(eml_files)} EML files in batch {batch_id}")
        
        # 解析所有邮件
        emails = []
        failed_files = []
        global_duplicates = []  # 全局重复的邮件
        
        for eml_file in eml_files:
            print(f"[PARSE] Parsing: {eml_file.name}")
            
            # 检查是否是全局重复
            file_name = eml_file.name
            if file_name in self.global_processed_emails:
                previous_batch = self.global_processed_emails[file_name].get('batch_id', 'unknown')
                previous_time = self.global_processed_emails[file_name].get('processed_at', 'unknown')
                print(f"[GLOBAL DUPLICATE] {file_name} already processed in batch {previous_batch} at {previous_time}")
                global_duplicates.append({
                    'file_name': file_name,
                    'previous_batch': previous_batch,
                    'previous_time': previous_time
                })
                continue
            
            email_info = self.parse_eml_file(eml_file)
            
            if email_info:
                emails.append(email_info)
                # 记录到全局已处理（仅内存，稍后批量保存）
                self.global_processed_emails[file_name] = {
                    'batch_id': batch_id,
                    'processed_at': datetime.now().isoformat(),
                    'subject': email_info.get('subject', '')
                }
            else:
                failed_files.append(eml_file.name)
        
        if not emails:
            return {"success": False, "batch_id": batch_id, "message": "所有邮件解析失败"}
        
        print(f"[SUCCESS] Successfully parsed {len(emails)} emails")
        
        # 【性能优化】批量保存全局已处理记录（移出循环，只保存一次）
        print(f"[SAVE] Saving global processed emails to {self.global_processed_file}...")
        self._save_global_processed()
        print(f"[SAVE] Global processed emails saved successfully")
        
        # 去重处理（只在批次内去重）
        print("[DEDUP] Starting deduplication...")
        unique_emails, duplicates = self.find_duplicates(emails)
        
        print(f"[RESULT] Deduplication result: {len(emails)} -> {len(unique_emails)} emails")
        print(f"[DUPLICATE] Duplicate emails: {len(duplicates)}")
        
        # 保存去重后的邮件为Markdown（带批次ID）
        saved_files = []
        for email_info in unique_emails:
            md_path = self.save_markdown_file(email_info, batch_id=batch_id)
            if md_path:
                saved_files.append(md_path)
        
        # 更新批次元数据
        if batch_info:
            batch_info['status']['cleaned'] = True
            batch_info['processing_history']['cleaned_at'] = datetime.now().isoformat()
            batch_info['dedup_stats'] = {
                'total_emails': len(eml_files),
                'unique_emails': len(unique_emails),
                'duplicates': len(duplicates),
                'global_duplicates': len(global_duplicates)
            }
            
            with open(batch_info_file, 'w', encoding='utf-8') as f:
                json.dump(batch_info, f, ensure_ascii=False, indent=2)
        
        return {
            "success": True,
            "batch_id": batch_id,
            "total_files": len(eml_files),
            "parsed_files": len(emails),
            "unique_files": len(unique_emails),
            "duplicate_files": len(duplicates),
            "global_duplicate_files": len(global_duplicates),
            "global_duplicates": global_duplicates,
            "failed_files": failed_files,
            "saved_files": saved_files
        }
    
    def process_all_emails(self, selected_batches=None) -> Dict:
        """处理所有邮件文件 - 支持批次模式
        
        Args:
            selected_batches: 可选，指定要处理的批次ID列表。如果为None，处理所有批次。
        """
        print(f"[SCAN] Scanning directory: {self.input_dir}")
        
        # 检查是否使用批次模式
        if self.batch_mode:
            # 查找所有批次目录
            all_batch_dirs = [d for d in self.input_dir.iterdir() if d.is_dir()]
            
            if not all_batch_dirs:
                print(f"[WARNING] No batch directories found in {self.input_dir}")
                # 降级到非批次模式
                self.batch_mode = False
            else:
                # 如果指定了批次列表，只处理这些批次
                if selected_batches:
                    batch_dirs = [d for d in all_batch_dirs if d.name in selected_batches]
                    print(f"[INFO] Processing {len(batch_dirs)} selected batch(es) out of {len(all_batch_dirs)} total")
                else:
                    batch_dirs = all_batch_dirs
                    print(f"[INFO] Found {len(batch_dirs)} batch(es)")
                
                if not batch_dirs:
                    return {
                        "success": False,
                        "message": "未找到指定的批次"
                    }
                
                results = []
                
                for batch_dir in sorted(batch_dirs, key=lambda x: x.name):
                    batch_id = batch_dir.name
                    result = self.process_batch(batch_dir, batch_id)
                    results.append(result)
                
                # 汇总统计
                total_unique = sum(r.get('unique_files', 0) for r in results if r.get('success'))
                total_duplicates = sum(r.get('duplicate_files', 0) for r in results if r.get('success'))
                total_global_duplicates = sum(r.get('global_duplicate_files', 0) for r in results if r.get('success'))
                total_failed = sum(len(r.get('failed_files', [])) for r in results if r.get('success'))
                all_global_duplicates = []
                for r in results:
                    if r.get('success') and r.get('global_duplicates'):
                        all_global_duplicates.extend(r['global_duplicates'])
                
                print(f"[STATS] All batches processed:")
                print(f"  - Total unique emails: {total_unique}")
                print(f"  - Total duplicates (in batch): {total_duplicates}")
                print(f"  - Total global duplicates (cross-batch): {total_global_duplicates}")
                print(f"  - Total failed: {total_failed}")
                
                return {
                    "success": True,
                    "mode": "batch",
                    "batches": results,
                    "summary": {
                        "total_batches": len(results),
                        "total_unique": total_unique,
                        "total_duplicates": total_duplicates,
                        "total_global_duplicates": total_global_duplicates,
                        "total_failed": total_failed
                    },
                    "global_duplicates": all_global_duplicates,
                    "report": {
                        "unique_emails": total_unique,
                        "duplicate_emails": total_duplicates,
                        "total_input_files": total_unique + total_duplicates
                    }
                }
        
        # 非批次模式（兼容旧逻辑）
        # 获取所有EML文件
        eml_files = list(self.input_dir.glob("*.eml"))
        
        if not eml_files:
            print(f"[ERROR] No EML files found in {self.input_dir}")
            return {"success": False, "message": "未找到EML文件"}
        
        print(f"[FOUND] Found {len(eml_files)} EML files")
        
        # 解析所有邮件
        emails = []
        failed_files = []
        
        for eml_file in eml_files:
            print(f"[PARSE] Parsing: {eml_file.name}")
            email_info = self.parse_eml_file(eml_file)
            
            if email_info:
                emails.append(email_info)
            else:
                failed_files.append(eml_file.name)
        
        if not emails:
            return {"success": False, "message": "所有邮件解析失败"}
        
        print(f"[SUCCESS] Successfully parsed {len(emails)} emails")
        
        # 去重处理
        print("[DEDUP] Starting deduplication...")
        unique_emails, duplicates = self.find_duplicates(emails)
        
        print(f"[RESULT] Deduplication result: {len(emails)} -> {len(unique_emails)} emails")
        print(f"[DUPLICATE] Duplicate emails: {len(duplicates)}")
        
        # 生成Markdown文件
        print("[GENERATE] Generating Markdown files...")
        generated_files = []
        
        for email_info in unique_emails:
            md_path = self.save_markdown_file(email_info)
            if md_path:
                generated_files.append(md_path)
                print(f"[SUCCESS] Generated: {Path(md_path).name}")
        
        # 保存处理报告
        report = {
            "processing_time": datetime.now().isoformat(),
            "input_directory": str(self.input_dir),
            "output_directory": str(self.output_dir),
            "total_input_files": len(eml_files),
            "successfully_parsed": len(emails),
            "failed_to_parse": len(failed_files),
            "failed_files": failed_files,
            "unique_emails": len(unique_emails),
            "duplicate_emails": len(duplicates),
            "duplicate_details": duplicates,
            "generated_markdown_files": [Path(f).name for f in generated_files],
            "compression_ratio": f"{len(duplicates) / len(emails) * 100:.1f}%" if emails else "0%"
        }
        
        report_path = self.output_dir / "processing_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n[REPORT] Processing report saved: {report_path}")
        print(f"[STATS] Compression ratio: {report['compression_ratio']}")
        
        return {
            "success": True,
            "report": report,
            "generated_files": generated_files
        }

def main():
    """主函数 - 命令行使用"""
    print("=" * 60)
    print("Email Cleaner Script - Starting...")
    print("=" * 60)
    print("=" * 50)
    
    # 创建清洗器实例
    cleaner = EmailCleaner()
    
    # 处理邮件
    result = cleaner.process_all_emails()
    
    if result["success"]:
        print("\n🎉 邮件清洗完成!")
        print(f"📁 输出目录: {cleaner.output_dir}")
        print(f"📄 生成文件数: {len(result['generated_files'])}")
    else:
        print(f"\n❌ 处理失败: {result['message']}")

if __name__ == "__main__":
    main()
