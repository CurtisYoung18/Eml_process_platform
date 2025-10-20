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
    def __init__(self, input_dir: str = "Eml", output_dir: str = "eml_process/processed"):
        """
        初始化邮件清洗器
        
        Args:
            input_dir: 输入EML文件目录
            output_dir: 输出Markdown文件目录
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 存储处理过的邮件信息
        self.processed_emails = []
        self.duplicate_info = []
        
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
        """查找并处理重复邮件 - 100%内容包含检测"""
        # 按内容长度排序（长的在前）
        emails_sorted = sorted(emails, key=lambda x: len(x['cleaned_content']), reverse=True)
        
        unique_emails = []
        duplicates = []
        
        for email_info in emails_sorted:
            # 标准化内容用于比较 - 移除所有空白字符和换行
            current_content = re.sub(r'\s+', '', email_info['cleaned_content'].lower())
            
            is_duplicate = False
            container_email = None
            
            # 检查当前邮件是否被已处理的邮件100%包含
            for unique_email in unique_emails:
                unique_content = re.sub(r'\s+', '', unique_email['cleaned_content'].lower())
                
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
                    'content_length_ratio': f"{len(current_content)}/{len(re.sub(r'\s+', '', container_email['cleaned_content'].lower()))}"
                })
                
                # 在容器邮件中记录包含的源文件
                if 'contained_files' not in container_email:
                    container_email['contained_files'] = []
                container_email['contained_files'].append(email_info['filename'])
                
                print(f"[DUPLICATE] Found 100% duplicate: {email_info['filename']} contained in {container_email['filename']}")
                
            else:
                # 不是重复邮件，添加到唯一列表
                unique_emails.append(email_info)
                print(f"[UNIQUE] Unique email: {email_info['filename']} (length: {len(current_content)})")
        
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
    
    def save_markdown_file(self, email_info: Dict) -> str:
        """保存Markdown文件"""
        # 生成文件名（去除.eml扩展名，添加.md）
        base_name = email_info['filename'].replace('.eml', '')
        md_filename = f"{base_name}.md"
        md_path = self.output_dir / md_filename
        
        # 生成Markdown内容
        md_content = self.generate_markdown(email_info)
        
        # 保存文件
        try:
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(md_content)
            return str(md_path)
        except Exception as e:
            print(f"❌ 保存Markdown文件失败 {md_filename}: {e}")
            return ""
    
    def process_all_emails(self) -> Dict:
        """处理所有邮件文件"""
        print(f"[SCAN] Scanning directory: {self.input_dir}")
        
        # 获取所有EML文件
        eml_files = list(self.input_dir.glob("*.eml"))
        
        if not eml_files:
            print(f"❌ 未在 {self.input_dir} 中找到EML文件")
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
