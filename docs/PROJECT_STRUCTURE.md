# 法律AI助手 - 项目结构说明

## 📁 目录结构

```
law-rag-assistant/
├── backend/                    # FastAPI 后端服务
│   ├── __init__.py
│   ├── main.py                 # 应用入口
│   ├── auth.py                 # 认证逻辑
│   ├── database.py             # 数据库模型
│   ├── schemas.py              # Pydantic 数据模型
│   ├── law_service.py          # 法律问答服务
│   └── routers/                # API 路由
│       ├── admin.py            # 管理员 API
│       ├── auth.py             # 认证 API
│       ├── chat.py             # 聊天 API
│       ├── conversations.py    # 对话 API
│       ├── documents.py        # 文档 API
│       └── favorites.py        # 收藏 API
│
├── frontend-user/              # Vue3 用户前端 (端口 3000)
│   ├── src/
│   │   ├── api/                # API 接口封装
│   │   ├── router/             # 路由配置
│   │   ├── stores/             # Pinia 状态管理
│   │   ├── styles/             # 样式文件
│   │   └── views/              # 页面组件
│   ├── package.json
│   └── vite.config.js
│
├── frontend-admin/             # Vue3 管理员前端 (端口 3001)
│   ├── src/
│   │   ├── api/                # API 接口封装
│   │   ├── router/             # 路由配置
│   │   ├── stores/             # Pinia 状态管理
│   │   ├── styles/             # 样式文件
│   │   └── views/              # 页面组件
│   ├── package.json
│   └── vite.config.js
│
├── law_ai/                     # RAG 核心模块
│   ├── __init__.py
│   ├── chain.py                # LangChain 链定义
│   ├── callback.py             # 回调处理器
│   ├── combine.py              # 文档合并
│   ├── loader.py               # 文档加载器
│   ├── logger.py               # 日志配置
│   ├── prompt.py               # 提示词模板
│   ├── retriever.py            # 检索器
│   ├── splitter.py             # 文本分割器
│   └── utils.py                # 工具函数
│
├── Law-Book/                   # 法律知识库 (Markdown 格式)
│   ├── 1-宪法/
│   ├── 2-宪法相关法/
│   ├── 3-民法典/
│   └── ...
│
├── scripts/                    # 启动脚本
│   ├── start.sh                # 统一启动（后端+用户前端）
│   ├── start_backend.sh        # 仅启动后端
│   ├── start_user_frontend.sh  # 仅启动用户前端
│   └── start_admin_frontend.sh # 仅启动管理员前端
│
├── tests/                      # 测试文件
│   ├── test_law_related_check.py
│   ├── test_document_qa.py
│   ├── test_document_search.py
│   └── ...
│
├── docs/                       # 项目文档
│   ├── DEPLOYMENT_GUIDE.md     # 部署指南
│   ├── TESTING_GUIDE.md        # 测试指南
│   ├── UI_IMPROVEMENTS.md      # UI改进说明
│   └── USAGE.md                # 使用说明
│
├── _archive/                   # 归档文件（废弃代码）
│   ├── frontend-streamlit/     # 旧 Streamlit 前端
│   ├── frontend-vue-old/       # 旧 Vue 前端
│   └── ...
│
├── chroma_db/                  # ChromaDB 向量数据库
├── uploads/                    # 用户上传的文件
├── image/                      # 文档图片资源
├── venv311/                    # Python 虚拟环境
│
├── config.py                   # 项目配置
├── init_admin.py               # 初始化管理员账户
├── requirements.txt            # Python 依赖
├── README.md                   # 项目说明
└── .env                        # 环境变量配置
```

## 🚀 快速启动

### 方式一：统一启动（推荐）
```bash
./scripts/start.sh
```
同时启动后端 API (8000) 和用户前端 (3000)

### 方式二：分别启动

```bash
# 终端 1: 启动后端
./scripts/start_backend.sh

# 终端 2: 启动用户前端
./scripts/start_user_frontend.sh

# 终端 3: 启动管理员前端（可选）
./scripts/start_admin_frontend.sh
```

## 🌐 服务端口

| 服务 | 端口 | 说明 |
|------|------|------|
| FastAPI 后端 | 8000 | API 服务、文档 /docs |
| 用户前端 | 3000 | Vue3 用户界面 |
| 管理员前端 | 3001 | Vue3 管理后台 |

## 📦 技术栈

### 后端
- **框架**: FastAPI
- **数据库**: SQLite
- **向量库**: ChromaDB
- **LLM**: 阿里云 DashScope (Qwen)
- **RAG**: LangChain

### 前端
- **框架**: Vue 3.4 + Vite 5
- **UI 库**: Element Plus
- **状态管理**: Pinia
- **HTTP 客户端**: Axios
- **流式输出**: SSE (Server-Sent Events)
- **图表**: ECharts
- **PDF导出**: html2pdf.js
