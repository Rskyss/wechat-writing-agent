#!/bin/bash

# 公众号小助手 - 预览应用启动脚本

echo "🚀 启动公众号小助手预览应用"
echo "================================"
echo ""

# 检查Python3是否安装
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到 python3"
    echo "请先安装 Python 3.8+"
    exit 1
fi

# 虚拟环境目录
VENV_DIR=".venv"

# 检查并创建虚拟环境
if [ ! -d "$VENV_DIR" ]; then
    echo "📦 首次运行,正在创建虚拟环境..."
    python3 -m venv "$VENV_DIR"
    echo "✅ 虚拟环境创建完成"
    echo ""
fi

# 激活虚拟环境
echo "🔧 激活虚拟环境..."
source "$VENV_DIR/bin/activate"

# 检查Flask是否安装
if ! python -c "import flask" &> /dev/null 2>&1; then
    echo "📦 正在安装依赖..."
    pip install -q -r preview_app/requirements.txt
    echo "✅ 依赖安装完成"
    echo ""
fi

# 启动API服务器(后台)
echo "🔧 启动质量检查API服务器 (端口 8001)..."
python preview_app/api_server.py &
API_PID=$!
echo "✅ API服务器已启动 (PID: $API_PID)"
echo ""

# 等待API服务器启动
sleep 2

# 启动前端服务器(前台)
echo "🌐 启动预览应用服务器 (端口 8000)..."
echo "📱 访问地址: http://localhost:8000/preview_app/"
echo ""
echo "⏹️  停止服务: Ctrl+C"
echo "================================"
echo ""

# 捕获Ctrl+C信号,关闭所有服务
trap "echo ''; echo '⏹️  正在关闭服务...'; kill $API_PID 2>/dev/null; deactivate 2>/dev/null; exit 0" INT

# 启动前端服务器
python -m http.server 8000

# 如果http.server退出,也关闭API服务器并退出虚拟环境
kill $API_PID 2>/dev/null
deactivate 2>/dev/null
