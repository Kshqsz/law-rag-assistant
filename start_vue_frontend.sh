#!/bin/bash
# 启动 Vue 前端

cd "$(dirname "$0")/frontend-vue"

# 检查是否已安装依赖
if [ ! -d "node_modules" ]; then
    echo "📦 正在安装依赖..."
    npm install
fi

echo "🚀 启动 Vue 前端 (http://localhost:3000)"
npm run dev
