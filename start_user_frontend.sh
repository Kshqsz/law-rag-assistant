#!/bin/bash
# 启动用户前端 (端口 3000)

cd "$(dirname "$0")/frontend-user"

# 检查 node_modules 是否存在，不存在则安装依赖
if [ ! -d "node_modules" ]; then
  echo "📦 首次运行，正在安装依赖..."
  npm install
fi

npm run dev
