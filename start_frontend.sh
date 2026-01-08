#!/bin/bash
# 法律AI助手 - 仅启动前端

echo "🚀 启动 Streamlit 前端服务..."

cd "$(dirname "$0")"

# 检查虚拟环境
if [ -d "venv311" ]; then
    source venv311/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
fi

streamlit run frontend/app.py --server.port 8501 --server.address 0.0.0.0
