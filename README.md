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

## 🚀 快速开始

### Mac
```bash
# 克隆项目
git clone https://github.com/CurtisYoung18/Eml_process_platform.git
cd Eml_process_platform
# 创建虚拟环境
python -m venv venv
source venv/bin/activate
# 安装依赖
pip install -r requirements.txt
# 运行app
python3 run_app.py
```


### Windows
```bash
# 克隆项目
git clone https://github.com/CurtisYoung18/Eml_process_platform.git
cd Eml_process_platform
# 创建虚拟环境
python -m venv venv
venv\Scripts\activate.bat
# 安装依赖
pip install -r requirements.txt
# 运行app
python run_app.py
```

### 配置API Key
复制环境变量示例文件并配置：
```bash
cp env_example.txt .env
# 编辑.env文件，填入您的API Key
```

**支持的API Key类型**：
- `GPTBOTS_LLM_API_KEY_1/2/3`: LLM处理专用
- `GPTBOTS_KB_API_KEY_1/2/3`: 知识库上传专用  
- `GPTBOTS_QA_API_KEY_1/2/3`: 问答系统专用

> 📋 详细配置说明请参考：[env_example.txt](./env_example.txt)


### 访问app
浏览器访问：[http://localhost:8501](http://localhost:8501)

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
- **后端语言**: Python 3.8+
- **API服务**: GPTBots API
- **文件处理**: Python标准库 + 自定义模块

### 项目结构
```
📁 项目根目录/
├── 📄 app.py                    # 主应用入口
├── 📄 run_app.py                 # 启动脚本
├── 📄 requirements.txt           # 依赖列表
├── 📄 env_example.txt            # 环境变量示例
├── 📁 config/                   # 配置模块
├── 📁 tools/                    # 功能模块
├── 📁 docs/                     # 文档目录
├── 📁 eml_process/              # 数据处理目录
└── 📁 logs/                     # 日志目录
```

> 📋 详细结构说明请参考：[docs/PROJECT_STRUCTURE.md](./docs/PROJECT_STRUCTURE.md)

---

## 📖 详细文档

### 📚 系统文档
- 📁 **[项目结构文档](./docs/PROJECT_STRUCTURE.md)** - 完整的项目架构和模块说明
- 🛠️ **[项目实施指南](./docs/项目实施指南.md)** - 详细的实施步骤和最佳实践
- 🔗 **[知识库API接入手册](./docs/知识库api接入手册.md)** - GPTBots API详细使用说明

### ⚙️ 配置文档
- 🔑 **[API配置指南](./docs/API_CONFIGURATION_GUIDE.md)** - 多编号API Key配置和管理
- ⚙️ **[环境变量配置](./env_example.txt)** - API Key和系统配置示例

### 📖 使用文档
- 🔄 **[用户工作流程指南](./docs/USER_WORKFLOW_GUIDE.md)** - 完整的6步骤操作指南

#### 分步骤详细指南：

1. **📤 邮件上传**
   - 支持EML格式文件批量上传
   - 文件验证和错误处理
   - 上传进度监控

2. **🧹 数据清洗**
   - 邮件内容提取和格式转换
   - Markdown格式输出
   - 质量检查和报告

3. **🤖 LLM处理**
   - 多API Key选择和配置
   - AI内容优化和结构化
   - 批量处理和进度监控

4. **📊 结果查看**
   - 多阶段结果预览和管理
   - 文件导出和打包下载
   - 处理统计和质量评估

5. **📚 知识库管理**
   - 知识库列表获取和选择
   - 文档分片和批量上传
   - 上传状态监控

6. **💬 问答系统**
   - 4种问答模式选择
   - iframe集成和代码生成
   - 语音输入和多轮对话

---

## ⚙️ 高级配置

### API Key管理
系统支持多个API Key配置，提供灵活的选择和管理：

```bash
# LLM处理API Key（支持3个编号）
GPTBOTS_LLM_API_KEY_1=your-llm-key-1
GPTBOTS_LLM_API_KEY_2=your-llm-key-2
GPTBOTS_LLM_API_KEY_3=your-llm-key-3

# 知识库API Key（支持3个编号）
GPTBOTS_KB_API_KEY_1=your-kb-key-1
GPTBOTS_KB_API_KEY_2=your-kb-key-2
GPTBOTS_KB_API_KEY_3=your-kb-key-3

# 问答系统API Key（支持3个编号）
GPTBOTS_QA_API_KEY_1=your-qa-key-1
GPTBOTS_QA_API_KEY_2=your-qa-key-2
GPTBOTS_QA_API_KEY_3=your-qa-key-3
```

### 系统配置
- **批处理限制**: 最大200个文件同时处理
- **文件大小限制**: 单文件最大50MB
- **API节点**: 支持新加坡、中国、泰国节点选择
- **日志级别**: 可配置INFO、DEBUG、ERROR级别

---

## 🔍 故障排除

### 常见问题
1. **Python版本要求**: >= 3.8
2. **依赖安装失败**: 检查网络连接或更换PyPI源
3. **API Key无效**: 确认Key格式和权限
4. **文件上传失败**: 检查文件格式和大小限制
5. **处理中断**: 查看日志文件获取详细错误信息

### 日志系统
- **活动日志**: `logs/activity.log` - 用户操作记录
- **API日志**: `logs/gptbots_api.log` - API调用记录  
- **知识库日志**: `logs/knowledge_base_api.log` - 知识库操作记录

### 性能优化
- 使用多个API Key提高并发处理能力
- 根据文件大小调整批处理参数
- 选择最近的API节点减少延迟

---

## 🛡️ 安全说明

### 数据安全
- 所有邮件数据仅在本地处理
- API Key通过环境变量安全存储
- 敏感信息脱敏显示
- 处理日志不包含敏感内容

### 文件管理
- 原始邮件文件存储在 `eml_process/uploads/`
- 处理结果存储在 `eml_process/processed/` 和 `eml_process/final_output/`

---