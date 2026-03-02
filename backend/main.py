# coding: utf-8
"""
FastAPI 主应用入口
"""
import sys
import os
import time

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 导入路由
from backend.routers.auth import router as auth_router
from backend.routers.conversations import router as conversations_router
from backend.routers.chat import router as chat_router
from backend.routers.documents import router as documents_router
from backend.routers.favorites import router as favorites_router
from backend.routers.admin import router as admin_router
from backend.routers.feedback import router as feedback_router
from law_ai.logger import app_logger

# 创建 FastAPI 应用
app = FastAPI(
    title="法律AI助手 API",
    description="""
    基于 RAG 技术的法律智能问答系统后端 API
    
    ## 功能特性
    
    * 🔐 用户注册与登录（JWT 认证）
    * 💬 对话管理（创建、删除、历史记录）
    * 🤖 智能法律问答（基于知识库 + 网络检索）
    * 📄 文档上传与管理
    * 📚 法律条文引用与来源追溯
    
    ## 技术栈
    
    * FastAPI + SQLAlchemy
    * LangChain + Qwen 大模型
    * ChromaDB 向量数据库
    * DuckDuckGo 网络搜索
    """,
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# ── 请求日志中间件 ────────────────────────────────────────────────────────────
# 跳过高频、无实质内容的路径，避免日志噪音
_SKIP_LOG_PATHS = {"/api/health", "/", "/api/docs", "/api/redoc", "/api/openapi.json"}

@app.middleware("http")
async def log_requests(request: Request, call_next):
    if request.url.path not in _SKIP_LOG_PATHS:
        start = time.time()
        client_ip = request.client.host if request.client else "unknown"
        app_logger.info(
            f"➡  {request.method} {request.url.path} | IP={client_ip}"
        )
        response = await call_next(request)
        elapsed = (time.time() - start) * 1000
        app_logger.info(
            f"⬅  {request.method} {request.url.path} | "
            f"status={response.status_code} | {elapsed:.0f}ms"
        )
        return response
    return await call_next(request)

# 配置 CORS（允许 Streamlit 前端访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制为具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth_router, prefix="/api")
app.include_router(conversations_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
app.include_router(documents_router, prefix="/api")
app.include_router(favorites_router, prefix="/api")
app.include_router(admin_router, prefix="/api")
app.include_router(feedback_router, prefix="/api")


@app.get("/", tags=["根路径"])
async def root():
    """API 根路径"""
    return {
        "message": "欢迎使用法律AI助手 API",
        "docs": "/api/docs",
        "version": "1.0.0"
    }


@app.get("/api/health", tags=["健康检查"])
async def health_check():
    """API 健康检查"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
