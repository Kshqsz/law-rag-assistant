# coding: utf-8
"""
API 路由模块
"""
from .auth import router as auth_router
from .conversations import router as conversations_router
from .chat import router as chat_router
from .documents import router as documents_router

__all__ = [
    "auth_router",
    "conversations_router", 
    "chat_router",
    "documents_router"
]

