# 📧 邮件知识库处理系统 (React版本)

基于Next.js + React + Flask构建的现代化邮件处理平台，提供完整的邮件处理、AI智能分析和知识库问答功能。

## 🎯 系统特点

- **🎨 现代化UI**: 采用React + Next.js构建，精美的界面设计
- **💬 QA首页**: 主页面直接展示问答系统（iframe方式）
- **🔐 权限管理**: 邮件处理功能需要管理员登录
- **⚡ 高性能**: 前后端分离架构，API驱动
- **💻 本地部署**: 完全本地运行，数据安全可控
- **🚀 一键启动**: 自动检测并安装所有依赖，无需手动配置

## 🚀 快速开始

### 系统要求

**最低要求：**
- **Python**: 3.8+ （必须已安装）
- **内存**: 至少4GB RAM
- **硬盘**: 至少2GB可用空间

**自动安装：**
- Node.js 20 LTS（脚本会自动下载安装）
- npm（随Node.js自动安装）
- 所有Python和前端依赖（脚本会自动安装）

### 📥 部署步骤

1. **下载项目到桌面**
   - 将整个 `Eml_process_platform` 文件夹放到桌面

2. **配置API密钥**
   - 打开 `Eml_process_platform/.env` 文件
   - 填入您的GPTBots API Keys

3. **一键启动**

#### 🪟 Windows系统
双击桌面上的 `启动邮件处理系统.vbs` 

或进入项目文件夹，双击 `start.bat`

#### 🍎 macOS/Linux系统
双击桌面上的 `启动邮件处理系统.command`

或进入项目文件夹，运行：
```bash
./start.sh
```

**首次启动说明：**
- 脚本会自动检测环境
- 如果没有Node.js，会自动下载安装
- 会自动安装所有依赖包
- 首次启动可能需要5-10分钟
- 完成后会自动打开浏览器

### 🛑 停止服务

#### Windows系统
双击桌面上的 `停止邮件处理系统.vbs`

#### macOS/Linux系统
双击桌面上的 `停止邮件处理系统.command`

### 访问系统

启动后自动打开: `http://localhost:3000`

- **主页**: QA问答系统（无需登录）
- **管理后台**: 点击右上角"邮件处理管理"
  - 默认账号: `admin`
  - 默认密码: `admin123`

## 📚 功能模块

### 公开访问（无需登录）
- **QA问答系统**: 主页面直接展示，支持知识库问答

### 管理员功能（需要登录）
1. **邮件上传**: 拖拽上传EML文件，批量处理
2. **数据清洗**: 自动提取和格式化邮件内容
3. **LLM处理**: AI智能内容优化和结构化
4. **结果查看**: 查看处理结果，下载文件
5. **知识库管理**: 上传到知识库，配置分块参数

## ⚙️ 配置说明

### API Key配置

在项目根目录创建 `.env` 文件：

```bash
# LLM处理API Keys
GPTBOTS_LLM_API_KEY_1=app-YOUR_LLM_API_KEY_1

# 知识库上传API Keys  
GPTBOTS_KB_API_KEY_1=app-YOUR_KB_API_KEY_1

# 问答系统API Keys
GPTBOTS_QA_API_KEY_1=app-YOUR_QA_API_KEY_1
```

### 修改iframe URL

编辑 `frontend/pages/index.tsx`，修改问答系统的iframe地址：
```typescript
<iframe src="YOUR_IFRAME_URL_HERE" />
```

## 📁 项目结构

```
Eml_process_platform/
├── frontend/                 # React前端应用
│   ├── components/          # 功能组件
│   ├── pages/               # 页面
│   │   ├── index.tsx        # 主页（QA系统）
│   │   ├── login.tsx        # 登录页
│   │   └── admin.tsx        # 管理后台
│   ├── lib/                 # 工具库
│   │   └── mockDb.ts        # Mock数据库
│   └── styles/              # 样式文件
│
├── api_server.py            # Flask API服务器
├── tools/                   # Python工具模块
├── config/                  # 配置模块
├── requirements.txt         # 后端依赖
├── start.sh / start.bat     # 启动脚本
└── README.md               # 本文档
```

## 🔧 开发指南

### 前端开发
```bash
cd frontend
npm run dev       # 开发模式 (http://localhost:3000)
npm run build     # 生产构建
npm run start     # 生产运行
```

### 后端开发
```bash
python api_server.py  # API服务 (http://localhost:5000)
```

## 🐛 故障排除

### 端口占用
- 修改前端端口: `frontend/package.json` 中的 `dev` 脚本
- 修改后端端口: `api_server.py` 中的端口号

### 依赖安装失败
```bash
# 使用国内镜像
pip install -r requirements_api.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
npm install --registry=https://registry.npmmirror.com
```

## 📝 更新日志

### v2.0.0 (2025-10-16)
- ✨ 全新React + Next.js前端界面
- 💬 主页直接展示QA问答系统（iframe）
- 🔐 添加管理员登录系统
- 🚀 Flask API后端
- 📱 现代化响应式设计

## 📄 许可证

本项目仅用于内部使用。
