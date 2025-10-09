# 📧 邮件知识库处理系统

一个基于Streamlit构建的本地部署应用，支持邮件文件处理、AI智能分析和知识库问答系统。

## 🎯 系统概述

本系统提供完整的邮件处理工作流：
- 📤 **邮件上传**: 批量上传EML格式邮件文件
- 🧹 **数据清洗**: 自动提取和清洗邮件内容
- 🤖 **LLM处理**: 使用AI进行内容结构化和优化
- 📚 **知识库管理**: 上传到GPTBots知识库
- 💬 **智能问答**: 基于知识库的问答系统

---

## 🚀 快速部署

### 方法一：一键部署（推荐）

1. **下载项目**
   - 下载并解压项目源码到本地文件夹

2. **安装Python**（如果未安装）
   - 下载Python 3.12.7：https://www.python.org/downloads/release/python-3127/
   - ⚠️ **重要**：安装时请勾选"Add Python to PATH"选项

3. **运行部署脚本**
   - 双击运行 `一键部署.bat`
   - 脚本会自动：
     - 检查Python环境
     - 创建虚拟环境
     - 安装所有依赖包
     - 创建启动脚本

4. **启动系统**
   - 双击运行生成的 `启动邮件系统.bat`
   - 系统会自动在浏览器打开：http://localhost:8501

### 方法二：命令行部署

如果一键部署失败，可使用命令行手动部署：

```bash
# 1. 进入项目目录
cd Eml_process_platform

# 2. 创建虚拟环境
python -m venv venv

# 3. 激活虚拟环境
venv\Scripts\activate

# 4. 安装依赖
python -m pip install -r requirements.txt

# 5. 启动应用
python run_app.py
```

### 配置API Key

复制环境变量示例文件并配置：
```bash
# 复制配置文件
copy env_example.txt .env

# 编辑.env文件，填入您的API Key
```

**支持的API Key类型**：
- `GPTBOTS_LLM_API_KEY_1/2/3`: LLM处理专用
- `GPTBOTS_KB_API_KEY_1/2/3`: 知识库上传专用  
- `GPTBOTS_QA_API_KEY_1/2/3`: 问答系统专用

> 📋 详细配置说明请参考：[env_example.txt](./env_example.txt)

---

## 📚 使用指南

### 步骤1: 邮件上传 📤
- **功能**: 批量上传EML格式的邮件文件
- **支持**: 多文件选择、文件验证、进度跟踪
- **输出**: 原始邮件文件存储到 `eml_process/uploads/`

### 步骤2: 数据清洗 🧹
- **功能**: 自动提取邮件内容并转换为Markdown格式
- **处理**: 移除HTML标签、提取纯文本、格式化输出
- **输出**: 清洗后的Markdown文件存储到 `eml_process/processed/`

### 步骤3: LLM处理 🤖
- **功能**: 使用GPTBots API进行内容智能处理
- **特性**: API Key选择、节点配置、批量处理、进度跟踪
- **输出**: AI优化后的文件存储到 `eml_process/final_output/`
- **配置**: 支持多个LLM API Key，可选择处理节点

### 步骤4: 结果查看 📊
- **功能**: 查看各阶段处理结果和统计信息
- **展示**: 文件列表、内容预览、处理报告
- **操作**: 文件下载、批量打包

### 步骤5: 知识库管理 📚
- **功能**: 将处理后的文件上传到GPTBots知识库
- **特性**: 知识库列表获取、批量上传、进度监控
- **配置**: 支持多个知识库API Key选择
- **输出**: 上传结果和知识库管理

### 步骤6: 问答系统 💬
- **功能**: 基于知识库的智能问答界面
- **模式**: 
  - 🤖 直接问答：iframe嵌入式问答界面
  - 💬 交互式问答：基于API的问答功能
  - 🖼️ iframe代码：生成嵌入代码
  - 🔧 API测试：连接和功能测试
- **特性**: 语音输入、多轮对话、上下文理解

---

## 🔧 技术架构

### 核心技术栈
- **前端框架**: Streamlit
- **后端语言**: Python 3.12+
- **API服务**: GPTBots API
- **文件处理**: Python标准库 + 自定义模块

### 项目结构
```
📁 项目根目录/
├── 📄 一键部署.bat              # 自动部署脚本
├── 📄 app.py                    # 主应用入口
├── 📄 run_app.py                # 启动脚本
├── 📄 requirements.txt          # 依赖列表
├── 📄 env_example.txt           # 环境变量示例
├── 📁 config/                   # 配置模块
├── 📁 tools/                    # 功能模块
├── 📁 docs/                     # 文档目录
├── 📁 eml_process/              # 数据处理目录
└── 📁 logs/                     # 日志目录
```

---

## 🔍 故障排除

### 常见问题

1. **Python未安装或版本不对**
   - 下载安装Python 3.12.7：https://www.python.org/downloads/release/python-3127/
   - 安装时务必勾选"Add Python to PATH"

2. **一键部署失败**
   - 检查是否以管理员身份运行
   - 尝试使用命令行手动部署
   - 查看生成的 `deploy.log` 日志文件

3. **依赖安装失败**
   - 检查网络连接
   - 尝试使用国内镜像：
     ```bash
     python -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
     ```

4. **API Key无效**
   - 确认Key格式正确
   - 检查API Key权限和额度

5. **端口占用**
   - 关闭其他使用8501端口的程序
   - 或修改`run_app.py`中的端口设置

### 管理脚本

部署完成后会自动生成以下管理脚本：
- `启动邮件系统.bat` - 启动应用
- `更新依赖.bat` - 更新依赖包
- `卸载系统.bat` - 清理环境

### 日志系统
- **部署日志**: `deploy.log` - 部署过程记录
- **活动日志**: `logs/activity.log` - 用户操作记录
- **API日志**: `logs/gptbots_api.log` - API调用记录

---

## 🛡️ 安全说明

### 数据安全
- 所有邮件数据仅在本地处理
- API Key通过环境变量安全存储
- 敏感信息脱敏显示
- 处理日志不包含敏感内容

### 系统要求
- **操作系统**: Windows 10/11
- **Python版本**: 3.12+ (推荐3.12.7)
- **内存**: 至少4GB RAM
- **磁盘空间**: 至少2GB可用空间

---