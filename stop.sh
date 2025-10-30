#!/bin/bash

# ================================================================
# 邮件知识库处理系统 - 停止脚本 (macOS/Linux)
# ================================================================

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "════════════════════════════════════════════════════════════"
echo "        📧 邮件知识库处理系统 - 停止服务"
echo "════════════════════════════════════════════════════════════"
echo ""

# 读取 PID
API_PID=""
FRONTEND_PID=""

if [ -f "logs/api_server.pid" ]; then
    API_PID=$(cat logs/api_server.pid)
fi

if [ -f "logs/frontend.pid" ]; then
    FRONTEND_PID=$(cat logs/frontend.pid)
fi

# 停止后端服务
if [ -n "$API_PID" ] && ps -p $API_PID > /dev/null 2>&1; then
    echo -e "${BLUE}[INFO]${NC} 正在停止后端 API 服务器 (PID: $API_PID)..."
    kill $API_PID
    sleep 2
    
    # 强制kill如果还在运行
    if ps -p $API_PID > /dev/null 2>&1; then
        kill -9 $API_PID 2>/dev/null
    fi
    
    rm -f logs/api_server.pid
    echo -e "${GREEN}[SUCCESS]${NC} ✅ 后端服务已停止"
else
    echo -e "${YELLOW}[WARNING]${NC} 后端服务未运行或PID文件不存在"
fi

# 停止前端服务
if [ -n "$FRONTEND_PID" ] && ps -p $FRONTEND_PID > /dev/null 2>&1; then
    echo -e "${BLUE}[INFO]${NC} 正在停止前端开发服务器 (PID: $FRONTEND_PID)..."
    kill $FRONTEND_PID
    sleep 2
    
    # 强制kill如果还在运行
    if ps -p $FRONTEND_PID > /dev/null 2>&1; then
        kill -9 $FRONTEND_PID 2>/dev/null
    fi
    
    rm -f logs/frontend.pid
    echo -e "${GREEN}[SUCCESS]${NC} ✅ 前端服务已停止"
else
    echo -e "${YELLOW}[WARNING]${NC} 前端服务未运行或PID文件不存在"
fi

# 额外清理：查找并停止所有相关进程
echo ""
echo -e "${BLUE}[INFO]${NC} 清理残留进程..."

# 停止所有 api_server.py 进程
pkill -f "python.*api_server.py" 2>/dev/null && echo -e "${GREEN}[SUCCESS]${NC} 清理了 api_server.py 进程"

# 停止所有 npm run dev 进程（前端）
pkill -f "npm.*run.*dev" 2>/dev/null && echo -e "${GREEN}[SUCCESS]${NC} 清理了 npm dev 进程"
pkill -f "next-server" 2>/dev/null && echo -e "${GREEN}[SUCCESS]${NC} 清理了 next-server 进程"

echo ""
echo "════════════════════════════════════════════════════════════"
echo -e "${GREEN}✅ 所有服务已停止${NC}"
echo "════════════════════════════════════════════════════════════"
echo ""

