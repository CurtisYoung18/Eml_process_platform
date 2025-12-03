<div align="center">

# 📧 邮件知识库处理系统 (Email Process Platform)

### Built with Next.js + Flask + GPTBots AI

**现代化邮件处理平台，提供完整的邮件处理、AI智能分析和知识库问答功能**

[部署指南](DEPLOYMENT.md) | [使用文档](docs/USER_WORKFLOW_GUIDE.md) | [API文档](docs/API_CONFIGURATION_GUIDE.md)

---

</div>

## 📖 简介 (Overview)

本系统是一个基于 Next.js (React) 和 Flask 构建的现代化邮件处理平台。旨在简化邮件数据的清洗、分析与知识库构建流程。通过集成 GPTBots AI，系统能够自动提取邮件内容、进行智能分析，并将其转化为结构化的知识库条目，配合内置的 QA 问答系统，实现对历史邮件数据的即时查询与利用。

---

## ✨ 核心功能 (Key Features)

### 1. 智能问答系统 (AI-Powered QA System)

无需登录即可访问的智能问答界面，基于处理后的邮件知识库提供精准回答。

![QA System Demo](imgs/chat.gif)

**主要优势:**
- **即时响应**: 直接在主页与知识库对话，快速获取历史邮件中的信息。
- **上下文理解**: AI 理解多轮对话上下文，提供连贯的回答。
- **无缝集成**: 通过 iframe 嵌入 GPTBots 问答组件，体验流畅。

---

### 2. 高性能批量处理 (High-Performance Batch Processing)

通过批次来管理全流程的邮件，可检测去重，打进度标签
![create batch](imgs/create_batch.gif)

采用哈希算法与流式处理技术，高效处理大规模邮件数据。
![Batch Processing](imgs/batch_processing.gif)

**主要优势:**
- **算法优化**: 采用 **Hash 边读边去重** 策略，替代传统的全量加载比对，内存占用极低，轻松处理百万级邮件批次。
- **智能批次管理**: 自动识别并管理邮件批次，全流程追踪批次状态（已上传、清洗中、已处理），支持断点续传。
- **全局去重**: 维护全局去重索引，不仅在批次内去重，还能自动识别跨批次的重复邮件，避免知识库数据冗余。
- **可视化进度**: 实时监控批次处理状态，清晰展示处理进度与去重统计。

---

### 3. AI 智能分析与结构化 (AI Analysis & Structuring)

利用 LLM 对清洗后的邮件内容进行深度分析与优化。

![AI Analysis Demo](imgs/output.gif)

**主要优势:**
- **内容提炼**: AI 自动总结邮件核心内容，提取关键信息。
- **结构化输出**: 将非结构化邮件转化为标准的 Markdown 格式，便于阅读与存储。
- **智能优化**: 修正格式错误，优化可读性，为知识库录入做准备。

---

### 4. 知识库一键构建 (One-Click Knowledge Base Integration)

打通数据处理到知识沉淀的最后一步。

**主要优势:**
- **一键上传**: 处理完成的批次数据可直接上传至 GPTBots 知识库。
- **自动RAG切片**: 支持配置切片参数，优化知识库检索效率。
- **版本管理**: 记录批次上传状态，避免重复录入。

---

## 🛠️ 技术栈 (Tech Stack)

- **前端**: Next.js, React, TypeScript, Tailwind CSS
- **后端**: Python, Flask (Hashlib, Multiprocessing)
- **AI/LLM**: GPTBots API
- **部署**: Shell/Batch Scripts (跨平台支持)

---

## 🚀 快速开始

详细的安装与部署步骤请参考 [DEPLOYMENT.md](DEPLOYMENT.md)。

### 简易启动

**Windows**: 双击 `点我运行.bat`
**macOS/Linux**: 运行 `./start.sh`

启动后访问: `http://localhost:3000`

---

## 📄 许可证

本项目仅用于内部使用。
