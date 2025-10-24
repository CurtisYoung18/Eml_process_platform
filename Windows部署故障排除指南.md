# Windows远程部署故障排除指南

## 问题：无法读取.env配置文件

### 症状
- 前端显示"❌ 无法加载环境配置"
- LLM和知识库配置显示为空

### 解决方案

#### 1. 确认.env文件位置
`.env` 文件必须放在项目根目录（与 `api_server.py` 同级）

```
Eml_process_platform/
├── api_server.py
├── .env          ← 必须在这里
├── frontend/
├── tools/
└── ...
```

#### 2. 检查.env文件内容格式
**Windows上必须注意**：
- 文件编码必须是 **UTF-8**（不能是UTF-8 with BOM）
- 行尾符必须是 **LF** 或 **CRLF**（Windows推荐CRLF）
- 不能有多余的空格或特殊字符

正确的.env文件示例：
```env
GPTBOTS_LLM_API_KEY_1=app-xxxxxxxxxxxxxxxxxx
GPTBOTS_LLM_API_KEY_2=app-yyyyyyyyyyyyyyyy
GPTBOTS_LLM_API_KEY_3=app-zzzzzzzzzzzzzzzz

GPTBOTS_KB_API_KEY_1=app-aaaaaaaaaaaaaaaa
GPTBOTS_KB_API_KEY_2=app-bbbbbbbbbbbbbbbb
GPTBOTS_KB_API_KEY_3=app-cccccccccccccccc
```

#### 3. 验证工作目录
启动服务时，必须在项目根目录执行：

**正确的启动方式（Windows CMD）：**
```cmd
cd C:\path\to\Eml_process_platform
start.bat
```

**或者使用PowerShell：**
```powershell
cd C:\path\to\Eml_process_platform
.\start.bat
```

#### 4. 检查日志文件
查看后端日志以确认.env文件是否被找到：

```cmd
type logs\api_server.log | findstr ".env"
```

或查看活动日志：
```cmd
type logs\activity.log | findstr ".env"
```

你应该看到类似这样的日志：
```
尝试读取.env文件: C:\path\to\Eml_process_platform\.env
✅ 找到.env文件: C:\path\to\Eml_process_platform\.env
成功读取.env文件，共6个变量
```

#### 5. 手动测试读取
创建一个测试脚本 `test_env.py`：

```python
from pathlib import Path
from dotenv import dotenv_values

# 测试不同路径
possible_paths = [
    Path(__file__).parent / '.env',
    Path.cwd() / '.env',
]

for path in possible_paths:
    print(f"尝试: {path.absolute()}")
    if path.exists():
        print(f"  ✅ 文件存在")
        env_vars = dotenv_values(path)
        print(f"  读取到 {len(env_vars)} 个变量")
        for key in env_vars.keys():
            print(f"    - {key}")
    else:
        print(f"  ❌ 文件不存在")
```

运行测试：
```cmd
cd C:\path\to\Eml_process_platform
python test_env.py
```

#### 6. Windows特定问题

**问题A：文件被隐藏**
- 在文件资源管理器中，确保显示隐藏文件
- `.env` 文件以点开头，在Windows中可能被视为隐藏文件

**问题B：文件扩展名**
- 确保文件名是 `.env`，不是 `.env.txt`
- 在Windows资源管理器中，启用"文件扩展名"显示

**问题C：权限问题**
- 确保运行Python进程的用户有读取.env文件的权限
- 右键 `.env` → 属性 → 安全 → 确认权限

#### 7. 临时解决方案：使用绝对路径

如果以上方法都不行，可以在 `api_server.py` 中硬编码绝对路径：

```python
# 在 get_env_config() 函数中修改
env_path = Path(r"C:\path\to\Eml_process_platform\.env")
```

⚠️ 注意：路径前面要加 `r` 前缀（原始字符串）

#### 8. 重启服务
修改后，必须重启服务：

```cmd
stop.bat
start.bat
```

## 远程访问配置

### 允许局域网访问

确保 `start.bat` 中的启动命令使用 `0.0.0.0`：

**后端（api_server.py）：**
```python
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=False)
```

**前端（package.json）：**
```json
"scripts": {
  "dev": "next dev -H 0.0.0.0"
}
```

### 防火墙规则
Windows防火墙需要允许：
- **入站规则**：端口 3000（前端）
- **入站规则**：端口 5001（后端）

添加防火墙规则（以管理员身份运行）：
```cmd
netsh advfirewall firewall add rule name="Email Processing Frontend" dir=in action=allow protocol=TCP localport=3000
netsh advfirewall firewall add rule name="Email Processing Backend" dir=in action=allow protocol=TCP localport=5001
```

### 局域网访问地址
假设服务器内网IP是 `192.168.1.100`：
- 前端：`http://192.168.1.100:3000`
- 后端API：`http://192.168.1.100:5001`

## 常见错误及解决

### 错误1：ModuleNotFoundError
```
ModuleNotFoundError: No module named 'dotenv'
```

**解决**：安装依赖
```cmd
pip install -r requirements.txt
```

### 错误2：端口被占用
```
Address already in use
```

**解决**：
```cmd
# 查找占用端口的进程
netstat -ano | findstr :5001

# 结束进程（替换PID）
taskkill /PID <PID> /F
```

### 错误3：Node.js未找到
```
'node' is not recognized as an internal or external command
```

**解决**：
1. 安装Node.js（建议v18或更高）
2. 重启CMD/PowerShell
3. 验证：`node --version`

## 联系支持

如果问题仍然存在，请提供以下信息：
1. `logs/api_server.log` 的最后50行
2. `logs/activity.log` 的最后50行
3. `.env` 文件的路径（不要发送内容）
4. Python版本：`python --version`
5. 工作目录：`cd` 命令的输出

