#!/bin/bash
# 法律AI助手 - 启动脚本
# 同时启动 FastAPI 后端和 Streamlit 前端

echo "⚖️  法律AI助手启动脚本"
echo "========================"

# 切换到项目目录
cd "$(dirname "$0")"

# 检查虚拟环境
if [ -d "venv311" ]; then
    source venv311/bin/activate
    echo "✅ 已激活虚拟环境: venv311"
elif [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ 已激活虚拟环境: venv"
fi

# 检查 .env 文件
if [ ! -f ".env" ]; then
    echo "⚠️  警告: 未找到 .env 文件，请确保已配置 API 密钥"
fi

# 启动后端服务
echo ""
echo "🚀 启动 FastAPI 后端服务 (端口: 8000)..."
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# 等待后端启动
sleep 3

# 启动前端服务
echo ""
echo "🚀 启动 Streamlit 前端服务 (端口: 8501)..."
streamlit run frontend/app.py --server.port 8501 --server.address 0.0.0.0 &
FRONTEND_PID=$!

echo ""
echo "========================"
echo "✅ 服务已启动!"
echo ""
echo "📍 后端 API:  http://localhost:8000"
echo "📍 API 文档:  http://localhost:8000/api/docs"
echo "📍 前端界面:  http://localhost:8501"
echo ""
echo "按 Ctrl+C 停止所有服务"
echo "========================"

# 捕获退出信号
trap "echo '正在停止服务...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" SIGINT SIGTERM

# 等待子进程
wait
