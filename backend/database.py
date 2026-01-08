# coding: utf-8
"""
数据库模块：使用 SQLite + SQLAlchemy 管理用户、对话和消息

数据库设计：
- users: 用户表（用户名、密码哈希）
- conversations: 对话表（用户ID、对话标题、创建时间）
- messages: 消息表（对话ID、角色、内容、来源引用、时间戳）
- documents: 上传文档表（用户ID、文件名、存储路径、处理状态）
"""
import os
from datetime import datetime
from typing import Optional, List
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session

# 数据库文件路径
DATABASE_URL = "sqlite:///./law_assistant.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    """用户表"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)  # 管理员标识
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关联
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="user", cascade="all, delete-orphan")
    favorites = relationship("Favorite", back_populates="user", cascade="all, delete-orphan")


class Conversation(Base):
    """对话表"""
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), default="新对话")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    """消息表"""
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    role = Column(String(20), nullable=False)  # "user" 或 "assistant"
    content = Column(Text, nullable=False)
    law_context = Column(Text, nullable=True)  # 法律条文引用
    web_context = Column(Text, nullable=True)  # 网页来源引用
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关联
    conversation = relationship("Conversation", back_populates="messages")


class Document(Base):
    """上传文档表"""
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)  # 文件大小（字节）
    file_type = Column(String(50), nullable=False)  # 文件类型
    is_processed = Column(Boolean, default=False)  # 是否已处理入库
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关联
    user = relationship("User", back_populates="documents")


class Favorite(Base):
    """收藏夹表"""
    __tablename__ = "favorites"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=False)
    question = Column(Text, nullable=False)  # 问题内容
    answer = Column(Text, nullable=False)  # 回答内容
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关联
    user = relationship("User", back_populates="favorites")
    message = relationship("Message")


class QuestionLog(Base):
    """问题日志表（用于统计）"""
    __tablename__ = "question_logs"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    question = Column(Text, nullable=False)
    category = Column(String(50), nullable=True)  # 法律分类：民法/刑法/行政法等
    created_at = Column(DateTime, default=datetime.utcnow)


def init_db():
    """初始化数据库，创建所有表"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """获取数据库会话（用于 FastAPI 依赖注入）"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 初始化数据库
init_db()
