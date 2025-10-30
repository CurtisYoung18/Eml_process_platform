# 🔑 API配置指南

## 📋 概述

邮件知识库处理系统支持灵活的API Key配置，您可以为不同功能配置多个API Key，并在应用中动态选择使用。

## 🎯 API Key类型

### 1. LLM邮件清洗 API Key
- **用途**: 邮件内容清洗和结构化处理
- **功能**: 调用GPTBots LLM服务进行文本处理
- **环境变量**: 
  - `GPTBOTS_LLM_API_KEY_1` (主要)
  - `GPTBOTS_LLM_API_KEY_2` (备用)
  - `GPTBOTS_LLM_API_KEY_3` (扩展)
- **默认值**: `app-YOUR_LLM_API_KEY_1`

### 2. 知识库上传 API Key
- **用途**: 将处理后的文档上传到GPTBots知识库
- **功能**: 文档分片、上传、索引管理
- **环境变量**:
  - `GPTBOTS_KB_API_KEY_1` (主要)
  - `GPTBOTS_KB_API_KEY_2` (备用)
  - `GPTBOTS_KB_API_KEY_3` (扩展)
- **默认值**: `app-YOUR_KB_API_KEY_1`

### 3. 问答系统 API Key
- **用途**: 智能问答功能，也可用于知识库操作
- **功能**: 问答对话、知识检索、上下文理解
- **环境变量**:
  - `GPTBOTS_QA_API_KEY_1` (主要)
  - `GPTBOTS_QA_API_KEY_2` (备用)
  - `GPTBOTS_QA_API_KEY_3` (扩展)
- **默认值**: `app-YOUR_QA_API_KEY_1`

## ⚙️ 配置步骤

### 步骤1: 准备API Key
1. 获取GPTBots API Key
2. 根据用途分类API Key
3. 确认API Key权限和限制

### 步骤2: 创建环境配置文件
```bash
# 复制示例文件
cp env_example.txt .env

# 编辑配置文件
nano .env  # 或使用其他编辑器
```

### 步骤3: 配置API Key
编辑`.env`文件，添加您的API Key：

```bash
# ===================================================
# LLM邮件清洗 API Keys
# ===================================================
GPTBOTS_LLM_API_KEY_1=your-primary-llm-key
GPTBOTS_LLM_API_KEY_2=your-secondary-llm-key
GPTBOTS_LLM_API_KEY_3=your-backup-llm-key

# ===================================================
# 知识库上传 API Keys
# ===================================================
GPTBOTS_KB_API_KEY_1=your-primary-kb-key
GPTBOTS_KB_API_KEY_2=your-secondary-kb-key
GPTBOTS_KB_API_KEY_3=your-backup-kb-key

# ===================================================
# 问答系统 API Keys
# ===================================================
GPTBOTS_QA_API_KEY_1=your-primary-qa-key
GPTBOTS_QA_API_KEY_2=your-secondary-qa-key
GPTBOTS_QA_API_KEY_3=your-backup-qa-key

# ===================================================
# 通用配置（向后兼容）
# ===================================================
GPTBOTS_API_KEY=your-general-api-key
```

### 步骤4: 验证配置
重启应用后，系统会自动检测可用的API Key：

```bash
# 停止应用
Ctrl+C

# 重新启动
streamlit run app.py
```

## 🎮 使用指南

### 在LLM处理页面
1. 访问"LLM处理"页面
2. 在API配置区域查看可用的API Key
3. 从下拉框选择要使用的API Key
4. 点击"配置指南"查看详细说明
5. 使用"测试API连接"验证配置

### 在知识库管理页面
1. 访问"知识库管理"页面
2. 选择知识库API Key
3. 获取知识库列表验证连接
4. 配置上传参数
5. 执行批量上传

### 在问答系统页面
1. 访问"问答系统"页面
2. 选择API Key来源：
   - **问答专用**: 使用QA API Key
   - **知识库复用**: 使用KB API Key
   - **手动输入**: 临时输入API Key
3. 选择具体的API Key编号
4. 开始问答交互

## 🔧 高级配置

### 多Key策略
```bash
# 场景1: 按功能分离
GPTBOTS_LLM_API_KEY_1=llm-specialized-key
GPTBOTS_KB_API_KEY_1=kb-specialized-key  
GPTBOTS_QA_API_KEY_1=qa-specialized-key

# 场景2: 按环境分离
GPTBOTS_LLM_API_KEY_1=production-key
GPTBOTS_LLM_API_KEY_2=staging-key
GPTBOTS_LLM_API_KEY_3=development-key

# 场景3: 按负载分离
GPTBOTS_KB_API_KEY_1=high-quota-key
GPTBOTS_KB_API_KEY_2=medium-quota-key
GPTBOTS_KB_API_KEY_3=low-quota-key
```

### API节点配置
```bash
# 默认节点配置
GPTBOTS_DEFAULT_ENDPOINT=sg

# 可选节点:
# sg - 新加坡 (推荐，延迟低)
# cn - 中国 (国内网络优化)
# th - 泰国 (备用节点)
```

### 其他配置参数
```bash
# 文件处理限制
MAX_FILE_SIZE=50              # 单文件最大50MB
BATCH_SIZE_LIMIT=200          # 批处理最大200文件

# 日志配置
LOG_LEVEL=INFO                # 日志级别: DEBUG, INFO, ERROR

# 应用配置
STREAMLIT_SERVER_PORT=8501    # Web服务端口
```

## 🔍 API Key管理最佳实践

### 安全性
1. **定期轮换**: 建议每3-6个月更换API Key
2. **权限最小化**: 为不同功能分配最小必需权限
3. **监控使用**: 定期检查API Key使用情况和配额
4. **备份策略**: 配置多个API Key避免单点故障

### 性能优化
1. **负载均衡**: 使用多个API Key分散请求压力
2. **节点选择**: 选择延迟最低的API节点
3. **并发控制**: 根据API限制调整处理并发数
4. **缓存策略**: 合理使用缓存减少API调用

### 成本控制
1. **配额管理**: 设置API Key使用配额上限
2. **智能选择**: 根据任务复杂度选择合适的API Key
3. **使用监控**: 跟踪API调用成本和频率
4. **优化策略**: 减少不必要的API调用

## ⚠️ 故障排除

### 常见问题

#### 1. API Key无效
**现象**: 连接测试失败，提示API Key无效
**解决方案**:
- 检查API Key格式是否正确
- 确认API Key是否已激活
- 验证API Key权限设置
- 联系GPTBots支持团队

#### 2. 看不到API Key选项
**现象**: 下拉框中没有可选的API Key
**解决方案**:
- 检查`.env`文件是否存在
- 确认环境变量配置正确
- 重启应用加载新配置
- 检查API Key是否为空

#### 3. API连接超时
**现象**: API请求超时或连接失败
**解决方案**:
- 检查网络连接
- 尝试其他API节点
- 确认API服务状态
- 调整请求超时设置

#### 4. 配额超限
**现象**: API调用返回配额超限错误
**解决方案**:
- 检查API Key剩余配额
- 切换到其他API Key
- 调整处理批次大小
- 联系服务提供商增加配额

### 调试技巧

#### 启用详细日志
```bash
# 在.env文件中设置
LOG_LEVEL=DEBUG
```

#### 检查API响应
1. 使用"API连接测试"功能
2. 查看`logs/gptbots_api.log`日志
3. 检查API响应格式和内容
4. 验证请求参数正确性

#### 监控API使用
1. 定期检查日志文件
2. 统计API调用频率
3. 分析错误模式
4. 优化调用策略

## 📊 监控和维护

### 日志监控
- **活动日志**: 用户操作和系统事件
- **API日志**: API调用详情和响应
- **错误日志**: 异常和错误信息

### 性能监控
- **响应时间**: API调用延迟统计
- **成功率**: API调用成功率监控
- **配额使用**: API配额消耗跟踪

### 定期维护
- **配置审查**: 定期检查API Key配置
- **性能优化**: 根据使用情况优化配置
- **安全更新**: 及时更新API Key和权限
- **文档更新**: 保持配置文档最新

---
