#!/bin/bash
# 启动管理员后台

echo "🚀 正在启动管理员后台..."
source venv311/bin/activate
streamlit run admin_app.py --server.port 8502
