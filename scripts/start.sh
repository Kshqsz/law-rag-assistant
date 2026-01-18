#!/bin/bash
# 法律AI助手 - 统一启动脚本
# 同时启动后端和用户前端

echo "⚖️  法律AI助手启动脚本"
echo "========================"

# 切换到项目根目录
cd "$(dirname "$0")/.."

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

# 启动用户前端
echo ""
echo "🌐 启动用户前端 (端口: 3000)..."
cd frontend-user
npm run dev &
FRONTEND_USER_PID=$!
cd ..

# 等待2秒
sleep 2

# 启动管理员前端
echo ""
echo "🛡️ 启动管理员前端 (端口: 3001)..."
cd frontend-admin
npm run dev &
FRONTEND_ADMIN_PID=$!
cd ..

echo ""
echo "✅ 所有服务已启动:"
echo "   - 后端 API: http://localhost:8000"
echo "   - 用户前端: http://localhost:3000"
echo "   - 管理员前端: http://localhost:3001"
echo "   - API 文档: http://localhost:8000/docs"
echo ""
echo "按 Ctrl+C 停止所有服务"

# 等待并捕获退出信号
trap "kill $BACKEND_PID $FRONTEND_USER_PID $FRONTEND_ADMIN_PID 2>/dev/null; exit" SIGINT SIGTERM
wait
