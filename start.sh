#!/bin/bash

# ================================================================
# 邮件知识库处理系统 - 一键启动脚本 (macOS/Linux)
# ================================================================
# 功能：自动检测并安装所有必需的环境和依赖
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
        PACKAGE_MANAGER=""
        if command -v apt-get &> /dev/null; then
            PACKAGE_MANAGER="apt-get"
        elif command -v yum &> /dev/null; then
            PACKAGE_MANAGER="yum"
        elif command -v brew &> /dev/null; then
            PACKAGE_MANAGER="brew"
        fi
        ;;
    Darwin*)    
        OS="macOS"
        PACKAGE_MANAGER="brew"
        ;;
    *)          
        OS="Unknown"
        ;;
esac
log_success "操作系统: $OS"

# ================================================================
# 2. 检查并安装 Homebrew (仅macOS)
# ================================================================
if [ "$OS" = "macOS" ]; then
    if ! command -v brew &> /dev/null; then
        log_warning "未检测到 Homebrew，正在安装..."
        log_info "这可能需要几分钟时间，请耐心等待..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        
        # 配置环境变量
        if [ -f "/opt/homebrew/bin/brew" ]; then
            echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
            eval "$(/opt/homebrew/bin/brew shellenv)"
        fi
        
        log_success "Homebrew 安装完成！"
    else
        log_success "Homebrew 已安装"
    fi
fi

# ================================================================
# 3. 检查并安装 Python3
# ================================================================
log_info "检查 Python 环境..."
if ! command -v python3 &> /dev/null; then
    log_warning "未检测到 Python3，正在安装..."
    
    if [ "$OS" = "macOS" ]; then
        brew install python@3.12
    elif [ "$PACKAGE_MANAGER" = "apt-get" ]; then
        sudo apt-get update
        sudo apt-get install -y python3 python3-pip python3-venv
    elif [ "$PACKAGE_MANAGER" = "yum" ]; then
        sudo yum install -y python3 python3-pip
    else
        log_error "无法自动安装 Python，请手动安装 Python 3.12+"
        exit 1
    fi
    
    log_success "Python3 安装完成！"
else
    PYTHON_VERSION=$(python3 --version)
    log_success "Python 已安装: $PYTHON_VERSION"
fi

# ================================================================
# 4. 检查并安装 Node.js 和 npm
# ================================================================
log_info "检查 Node.js 环境..."
NODE_REQUIRED=true

if ! command -v node &> /dev/null; then
    log_warning "未检测到 Node.js，正在安装 Node.js 20 LTS..."
    
    if [ "$OS" = "macOS" ]; then
        # macOS 使用 Homebrew 安装
        brew install node@20
        
        # 添加到 PATH
        if [ -d "/opt/homebrew/opt/node@20/bin" ]; then
            export PATH="/opt/homebrew/opt/node@20/bin:$PATH"
        fi
    elif [ "$OS" = "Linux" ]; then
        # Linux 使用 NodeSource 安装
        log_info "正在配置 NodeSource 仓库..."
        curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
        
        if [ "$PACKAGE_MANAGER" = "apt-get" ]; then
            sudo apt-get install -y nodejs
        elif [ "$PACKAGE_MANAGER" = "yum" ]; then
            sudo yum install -y nodejs
        fi
    else
        log_error "无法自动安装 Node.js"
        log_info "请访问 https://nodejs.org/ 手动下载安装 Node.js 20 LTS"
        log_info "安装完成后，请重新运行此脚本"
        exit 1
    fi
    
    log_success "Node.js 安装完成！"
else
    NODE_VERSION=$(node --version)
    NPM_VERSION=$(npm --version)
    log_success "Node.js 已安装: $NODE_VERSION"
    log_success "npm 已安装: v$NPM_VERSION"
fi

# 验证 Node.js 和 npm
if ! command -v node &> /dev/null || ! command -v npm &> /dev/null; then
    log_error "Node.js 或 npm 安装失败，请检查安装过程"
    exit 1
fi

# ================================================================
# 5. 创建并激活 Python 虚拟环境
# ================================================================
log_info "配置 Python 虚拟环境..."
if [ ! -d "venv" ]; then
    log_info "创建 Python 虚拟环境..."
    python3 -m venv venv
    log_success "虚拟环境创建完成"
else
    log_success "虚拟环境已存在"
fi

# 激活虚拟环境
source venv/bin/activate
log_success "虚拟环境已激活"

# ================================================================
# 6. 安装 Python 依赖
# ================================================================
log_info "安装 Python 依赖..."
pip install --upgrade pip -q
pip install -r requirements.txt -q
log_success "Python 依赖安装完成"

# ================================================================
# 7. 检查并创建 .env 文件
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
# 8. 安装前端依赖
# ================================================================
log_info "安装前端依赖..."
cd frontend

if [ ! -d "node_modules" ]; then
    log_info "首次安装，这可能需要几分钟..."
    npm install
    log_success "前端依赖安装完成"
else
    log_info "检查依赖更新..."
    npm install
    log_success "前端依赖已是最新"
fi

cd ..

# ================================================================
# 9. 创建日志目录
# ================================================================
if [ ! -d "logs" ]; then
    mkdir -p logs
    log_success "日志目录创建完成"
fi

# ================================================================
# 10. 启动后端 API 服务器
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
# 11. 启动前端开发服务器
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
# 12. 启动成功提示
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
