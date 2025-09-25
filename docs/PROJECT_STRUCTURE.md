# 📁 项目结构文档

## 🎯 项目概述

邮件知识库处理系统是一个基于Streamlit构建的本地部署应用，用于处理邮件文件并构建智能问答系统。

## 📂 目录结构

```
Eml_process_platform/
├── 📄 app.py                          # 主应用入口文件
├── 📄 run_app.py                       # 应用启动脚本
├── 📄 requirements.txt                 # Python依赖包列表
├── 📄 env_example.txt                  # 环境变量配置示例
├── 📄 README.md                        # 项目说明文档
├── 📄 知识库api接入手册.md               # 知识库API接入文档
├── 📄 项目实施指南.md                   # 项目实施指导文档
│
├── 📁 config/                          # 配置模块
│   ├── 📄 __init__.py                  # 配置模块初始化
│   └── 📄 settings.py                  # 项目配置和环境变量管理
│
├── 📁 docs/                           # 文档目录
│   ├── 📄 PROJECT_STRUCTURE.md        # 项目结构文档（本文件）
│   ├── 📄 知识库api接入手册.md          # 知识库API接入手册
│   └── 📄 项目实施指南.md              # 项目实施指南
│
├── 📁 tools/                          # 功能模块目录
│   ├── 📄 __init__.py                  # 工具模块初始化
│   ├── 📄 utils.py                     # 通用工具函数
│   ├── 📄 api_selector.py              # API Key选择器组件
│   ├── 📄 homepage.py                  # 首页功能模块
│   ├── 📄 email_upload.py              # 邮件上传功能模块
│   ├── 📄 data_cleaning.py             # 数据清洗功能模块
│   ├── 📄 llm_processing.py            # LLM处理功能模块
│   ├── 📄 results_view.py              # 结果查看功能模块
│   ├── 📄 knowledge_base.py            # 知识库管理功能模块
│   ├── 📄 qa_system.py                 # 问答系统功能模块
│   ├── 📄 future_features.py           # 未来功能预留模块
│   │
│   ├── 📁 api_clients/                 # API客户端模块
│   │   ├── 📄 __init__.py              # API客户端初始化
│   │   ├── 📄 gptbots_api.py           # GPTBots通用API客户端
│   │   └── 📄 knowledge_base_api.py    # 知识库专用API客户端
│   │
│   └── 📁 email_processing/            # 邮件处理模块
│       ├── 📄 __init__.py              # 邮件处理初始化
│       └── 📄 email_cleaner.py         # 邮件清洗核心逻辑
│
├── 📁 eml_process/                     # 邮件处理数据目录
│   ├── 📁 uploads/                     # 上传的原始邮件文件
│   ├── 📁 processed/                   # 清洗后的Markdown文件
│   ├── 📁 final_output/                # LLM处理后的最终文件
│   └── 📁 output/                      # 临时输出目录
│
└── 📁 logs/                           # 日志文件目录
    ├── 📄 activity.log                 # 系统活动日志
    ├── 📄 gptbots_api.log              # GPTBots API调用日志
    └── 📄 knowledge_base_api.log       # 知识库API调用日志
```

## 🔧 核心模块说明

### 1. 主应用模块 (`app.py`)
- **功能**: Streamlit应用主入口
- **职责**: 
  - 应用配置和初始化
  - 导航菜单管理
  - 页面路由控制
  - 状态管理

### 2. 配置模块 (`config/`)
- **功能**: 集中管理项目配置
- **核心文件**:
  - `settings.py`: 环境变量、API配置、目录路径等
  - `__init__.py`: 配置导出和初始化

### 3. 工具模块 (`tools/`)
- **功能**: 实现各个功能页面的业务逻辑
- **模块化设计**: 每个功能页面对应一个独立模块

#### 3.1 页面功能模块
- `homepage.py`: 首页概览和系统状态
- `email_upload.py`: 邮件文件上传功能
- `data_cleaning.py`: 邮件数据清洗
- `llm_processing.py`: LLM智能处理
- `results_view.py`: 处理结果查看
- `knowledge_base.py`: 知识库管理
- `qa_system.py`: 智能问答系统

#### 3.2 核心组件模块
- `api_selector.py`: API Key选择器组件
- `utils.py`: 通用工具函数
- `future_features.py`: 未来功能预留

#### 3.3 API客户端模块 (`api_clients/`)
- `gptbots_api.py`: GPTBots通用API封装
- `knowledge_base_api.py`: 知识库专用API封装

#### 3.4 邮件处理模块 (`email_processing/`)
- `email_cleaner.py`: 邮件内容清洗和结构化

## 🔄 数据流程

### 1. 邮件上传阶段
```
原始EML文件 → eml_process/uploads/ → 文件验证 → 上传成功
```

### 2. 数据清洗阶段
```
uploads/*.eml → EmailCleaner → processed/*.md → 清洗报告
```

### 3. LLM处理阶段
```
processed/*.md → GPTBots API → final_output/*.md → 处理完成
```

### 4. 知识库上传阶段
```
final_output/*.md → KnowledgeBase API → 知识库 → 上传完成
```

### 5. 问答系统阶段
```
知识库内容 → GPTBots问答API → iframe界面 → 智能问答
```

## ⚙️ 配置系统

### 环境变量配置
- **文件**: `env_example.txt` (示例) → `.env` (实际配置)
- **支持**: 多编号API Key配置 (每种类型支持3个编号)
- **类型**:
  - `GPTBOTS_LLM_API_KEY_1/2/3`: LLM处理API Key
  - `GPTBOTS_KB_API_KEY_1/2/3`: 知识库API Key  
  - `GPTBOTS_QA_API_KEY_1/2/3`: 问答API Key

### 应用配置
- **导航配置**: 菜单选项、图标、样式
- **目录配置**: 各阶段数据存储路径
- **API配置**: 节点选择、超时设置
- **日志配置**: 日志级别、文件路径

## 📊 状态管理

### Session State
- 当前处理步骤状态
- 文件处理进度
- API配置选择
- 用户界面状态

### 文件系统状态
- 各阶段文件数量统计
- 处理进度跟踪
- 错误日志记录

## 🔍 日志系统

### 日志类型
- **活动日志** (`logs/activity.log`): 用户操作记录
- **API日志** (`logs/gptbots_api.log`): API调用记录
- **知识库日志** (`logs/knowledge_base_api.log`): 知识库操作记录

### 日志格式
```
时间戳 - 日志级别 - 模块名 - 操作描述 - 详细信息
```

## 🚀 部署架构

### 本地部署
- **Web框架**: Streamlit
- **Python版本**: 3.8+
- **依赖管理**: requirements.txt
- **环境隔离**: Python虚拟环境

### 外部服务
- **GPTBots API**: LLM处理和问答服务
- **知识库服务**: 文档存储和检索
- **iframe集成**: 问答界面嵌入

## 📈 扩展性设计

### 模块化架构
- 功能模块独立，便于维护和扩展
- API客户端统一封装，支持多种服务
- 配置集中管理，便于环境切换

### 插件化支持
- 新功能模块可独立开发
- API Key支持多编号配置
- 处理流程支持自定义扩展

## 🔒 安全考虑

### API Key管理
- 环境变量存储，避免硬编码
- 脱敏显示，保护敏感信息
- 多Key支持，降低单点风险

### 文件处理安全
- 文件类型验证
- 大小限制控制
- 路径安全检查

## 📝 开发规范

### 代码组织
- 每个功能模块独立文件
- 统一的导入和导出规范
- 清晰的函数和类命名

### 文档规范
- 模块级docstring说明
- 函数参数和返回值注释
- 关键业务逻辑注释

---