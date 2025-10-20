#!/bin/bash

# ================================================================
# 邮件知识库处理系统 - 一键启动脚本 (macOS/Linux)
# ================================================================
# 功能：检查环境并启动服务
# 使用：chmod +x start.sh && ./start.sh
# ================================================================

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

echo "════════════════════════════════════════════════════════════"
echo "        📧 邮件知识库处理系统 - 一键启动"
echo "════════════════════════════════════════════════════════════"
echo ""

# ================================================================
# 1. 检查操作系统
# ================================================================
log_info "检测操作系统..."
OS_TYPE="$(uname -s)"
case "${OS_TYPE}" in
    Linux*)     
        OS="Linux"
        ;;
    Darwin*)    
        OS="macOS"
        ;;
    *)          
        OS="Unknown"
        ;;
esac
log_success "操作系统: $OS"

# ================================================================
# 2. 检查 Python3
# ================================================================
log_info "检查 Python 环境..."
if ! command -v python3 &> /dev/null; then
    log_error "未检测到 Python3！"
    echo ""
    echo "请手动安装 Python："
    if [ "$OS" = "macOS" ]; then
        echo "  方法1: 访问 https://www.python.org/downloads/ 下载安装"
        echo "  方法2: 使用 Homebrew: brew install python@3.12"
    elif [ "$OS" = "Linux" ]; then
        echo "  Ubuntu/Debian: sudo apt-get install python3 python3-pip python3-venv"
        echo "  CentOS/RHEL: sudo yum install python3 python3-pip"
    fi
    echo ""
    echo "安装完成后，请重新运行此脚本"
    exit 1
else
    PYTHON_VERSION=$(python3 --version)
    log_success "Python 已安装: $PYTHON_VERSION"
fi

# ================================================================
# 3. 检查 Node.js 和 npm
# ================================================================
log_info "检查 Node.js 环境..."

if ! command -v node &> /dev/null; then
    log_error "未检测到 Node.js！"
    echo ""
    echo "请手动安装 Node.js 20 LTS："
    if [ "$OS" = "macOS" ]; then
        echo "  方法1: 访问 https://nodejs.org/ 下载安装"
        echo "  方法2: 使用 Homebrew: brew install node@20"
    elif [ "$OS" = "Linux" ]; then
        echo "  访问 https://nodejs.org/ 下载安装"
        echo "  或参考: https://github.com/nodesource/distributions"
    fi
    echo ""
    echo "安装完成后，请重新运行此脚本"
    exit 1
else
    NODE_VERSION=$(node --version)
    NPM_VERSION=$(npm --version)
    log_success "Node.js 已安装: $NODE_VERSION"
    log_success "npm 已安装: v$NPM_VERSION"
fi

# 验证 Node.js 和 npm
if ! command -v node &> /dev/null || ! command -v npm &> /dev/null; then
    log_error "Node.js 或 npm 未正确安装，请检查安装"
    exit 1
fi

# ================================================================
# 4. 创建并激活 Python 虚拟环境
# ================================================================
log_info "配置 Python 虚拟环境..."
if [ ! -d "venv" ]; then
    log_info "创建 Python 虚拟环境..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        log_error "创建虚拟环境失败！"
        echo ""
        echo "请确保 Python 已正确安装，并且包含 venv 模块"
        exit 1
    fi
    log_success "虚拟环境创建完成"
else
    log_success "虚拟环境已存在"
fi

# 激活虚拟环境
source venv/bin/activate
if [ $? -ne 0 ]; then
    log_error "激活虚拟环境失败！"
    exit 1
fi
log_success "虚拟环境已激活"

# ================================================================
# 5. 安装 Python 依赖
# ================================================================
log_info "安装 Python 依赖..."
pip install --upgrade pip -q
if [ $? -ne 0 ]; then
    log_warning "升级 pip 失败，继续..."
fi

pip install -r requirements.txt -q
if [ $? -ne 0 ]; then
    log_error "安装 Python 依赖失败！"
    echo ""
    echo "请尝试手动安装："
    echo "  1. source venv/bin/activate"
    echo "  2. pip install -r requirements.txt"
    echo ""
    exit 1
fi
log_success "Python 依赖安装完成"

# ================================================================
# 6. 检查并创建 .env 文件
# ================================================================
if [ ! -f ".env" ]; then
    if [ -f "env_example.txt" ]; then
        log_warning ".env 文件不存在，正在从 env_example.txt 创建..."
        cp env_example.txt .env
        log_success ".env 文件创建完成"
        log_warning "⚠️  请编辑 .env 文件，填入您的实际 API Keys"
    else
        log_warning ".env 文件不存在，请手动创建并配置 API Keys"
    fi
else
    log_success ".env 文件已存在"
fi

# ================================================================
# 7. 安装前端依赖
# ================================================================
log_info "安装前端依赖..."
cd frontend

if [ ! -d "node_modules" ]; then
    log_info "首次安装，这可能需要几分钟..."
    npm install
    if [ $? -ne 0 ]; then
        log_error "前端依赖安装失败！"
        echo ""
        echo "请尝试手动安装："
        echo "  1. cd frontend"
        echo "  2. npm install"
        echo ""
        cd ..
        exit 1
    fi
    log_success "前端依赖安装完成"
else
    log_info "检查依赖更新..."
    npm install
    if [ $? -ne 0 ]; then
        log_warning "更新依赖失败，使用现有依赖..."
    else
        log_success "前端依赖已是最新"
    fi
fi

cd ..

# ================================================================
# 8. 创建日志目录
# ================================================================
if [ ! -d "logs" ]; then
    mkdir -p logs
    log_success "日志目录创建完成"
fi

# ================================================================
# 9. 启动后端 API 服务器
# ================================================================
echo ""
log_info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log_info "🔧 启动后端 API 服务器..."
log_info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 启动后端（后台运行）
source venv/bin/activate
nohup python3 api_server.py > logs/api_server.log 2>&1 &
API_PID=$!

# 保存 PID
echo $API_PID > logs/api_server.pid

# 等待后端启动
log_info "等待后端服务启动..."
sleep 5

# 检查后端是否启动成功
if ps -p $API_PID > /dev/null; then
    log_success "后端 API 服务器启动成功 (PID: $API_PID)"
else
    log_error "后端 API 服务器启动失败，请检查 logs/api_server.log"
    exit 1
fi

# ================================================================
# 10. 启动前端开发服务器
# ================================================================
echo ""
log_info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log_info "🎨 启动前端开发服务器..."
log_info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

cd frontend
nohup npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!

# 保存 PID
echo $FRONTEND_PID > ../logs/frontend.pid

cd ..

# 等待前端启动
log_info "等待前端服务启动..."
sleep 8

# 检查前端是否启动成功
if ps -p $FRONTEND_PID > /dev/null; then
    log_success "前端开发服务器启动成功 (PID: $FRONTEND_PID)"
else
    log_error "前端开发服务器启动失败，请检查 logs/frontend.log"
    kill $API_PID 2>/dev/null
    exit 1
fi

# ================================================================
# 11. 启动成功提示
# ================================================================
echo ""
echo "════════════════════════════════════════════════════════════"
echo -e "${GREEN}✅ 邮件处理平台启动成功！${NC}"
echo "════════════════════════════════════════════════════════════"
echo ""
echo -e "${BLUE}📍 访问地址：${NC}"
echo -e "   前端应用: ${GREEN}http://localhost:3000${NC}"
echo -e "   后端API:  ${GREEN}http://localhost:5001${NC}"
echo ""
echo -e "${BLUE}📂 日志文件：${NC}"
echo -e "   后端日志: logs/api_server.log"
echo -e "   前端日志: logs/frontend.log"
echo ""
echo -e "${BLUE}🔧 进程管理：${NC}"
echo -e "   后端 PID: $API_PID"
echo -e "   前端 PID: $FRONTEND_PID"
echo ""
echo -e "${YELLOW}⚠️  停止服务：${NC}"
echo -e "   运行: ${GREEN}./stop.sh${NC}"
echo -e "   或手动: kill $API_PID $FRONTEND_PID"
echo ""
echo "════════════════════════════════════════════════════════════"
echo ""
echo -e "${GREEN}🎉 系统已就绪，请在浏览器中访问 http://localhost:3000${NC}"
echo ""

# 自动打开浏览器（可选）
if [ "$OS" = "macOS" ]; then
    sleep 2
    open http://localhost:3000
elif command -v xdg-open &> /dev/null; then
    sleep 2
    xdg-open http://localhost:3000
fi

# 保持脚本运行，显示日志
log_info "按 Ctrl+C 可查看实时日志..."
echo ""

# 等待用户中断
wait $API_PID $FRONTEND_PID
