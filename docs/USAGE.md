# 法律AI助手 - 使用指南

## 📍 访问地址

| 服务 | 地址 | 说明 |
|------|------|------|
| 👤 用户前端 | http://localhost:8501 | 用户注册、登录、对话、收藏 |
| 👑 管理员后台 | http://localhost:8502 | 管理员登录、数据统计（独立界面）|
| 🔌 后端 API | http://localhost:8000 | RESTful API 服务 |
| 📖 API 文档 | http://localhost:8000/api/docs | Swagger 接口文档 |

## 🚀 启动服务

### 方式一：使用启动脚本（推荐）

```bash
# 1. 启动后端 API (端口 8000)
./start_backend.sh

# 2. 启动用户前端 (端口 8501)
./start_frontend.sh

# 3. 启动管理员后台 (端口 8502)
./start_admin.sh
```

### 方式二：手动启动

```bash
# 终端1：启动后端
source venv311/bin/activate
python -m backend.main

# 终端2：启动用户前端
source venv311/bin/activate
streamlit run frontend/app.py

# 终端3：启动管理员后台
source venv311/bin/activate
streamlit run admin_app.py --server.port 8502
```

## 🔑 默认账号

### 管理员账号
- **用户名**: `admin`
- **密码**: `admin123`
- **访问地址**: http://localhost:8502
- **说明**: 管理员使用独立的后台界面，无法在用户前端登录

### 普通用户
- 在用户前端自行注册：http://localhost:8501
- 无需邮箱，仅需用户名和密码

## 💡 功能说明

### 用户端功能
- ✅ 登录/注册按钮已居中显示
- ✅ 文件上传按钮（➕）位于输入框左侧
- ✅ 支持多种文件编码（UTF-8, GBK, GB2312, GB18030, Latin1）
- ✅ 支持 PDF、TXT、MD 格式文件
- ✅ 一键收藏重要问答（⭐ 按钮）
- ✅ ChatGPT 风格的暗色主题界面

### 管理员后台功能
- ✅ 独立的登录界面（无注册功能）
- ✅ 登录后直接进入数据统计页面
- ✅ 用户增长趋势图（近30天）
- ✅ 高频问题 Top 10
- ✅ 问题分类统计（民法/刑法/行政法等）

## ⚠️ 重要说明

1. **管理员与普通用户完全分离**
   - 管理员只能在 http://localhost:8502 登录
   - 管理员账号无法在用户前端使用
   - 用户账号无法访问管理员后台

2. **文件上传位置**
   - 文件上传按钮（➕）在聊天输入框的左侧
   - 点击后会弹出文件选择对话框
   - 上传成功后会显示文件名
