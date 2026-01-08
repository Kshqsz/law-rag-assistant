#!/bin/bash
# 法律AI助手 - 仅启动后端

echo "🚀 启动 FastAPI 后端服务..."

cd "$(dirname "$0")"

# 检查虚拟环境
if [ -d "venv311" ]; then
    source venv311/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
fi

uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
