# coding: utf-8
"""
Pydantic 数据模型：用于 API 请求/响应验证
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# ==================== 用户相关 ====================

class UserCreate(BaseModel):
    """用户注册请求"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, max_length=100, description="密码")


class UserLogin(BaseModel):
    """用户登录请求"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class UserResponse(BaseModel):
    """用户信息响应"""
    id: int
    username: str
    is_active: bool
    is_admin: bool = False
    created_at: datetime
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    """JWT Token 响应"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token 解析后的数据"""
    username: Optional[str] = None
    user_id: Optional[int] = None


# ==================== 对话相关 ====================

class ConversationCreate(BaseModel):
    """创建对话请求"""
    title: Optional[str] = Field(default="新对话", max_length=200)


class ConversationUpdate(BaseModel):
    """更新对话标题请求"""
    title: str = Field(..., max_length=200)


class ConversationResponse(BaseModel):
    """对话信息响应"""
    id: int
    title: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ConversationListResponse(BaseModel):
    """对话列表响应"""
    conversations: List[ConversationResponse]


# ==================== 消息相关 ====================

class MessageCreate(BaseModel):
    """发送消息请求"""
    content: str = Field(..., min_length=1, max_length=5000, description="消息内容")


class MessageResponse(BaseModel):
    """消息响应"""
    id: int
    role: str
    content: str
    law_context: Optional[str] = None
    web_context: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class MessageListResponse(BaseModel):
    """消息列表响应"""
    messages: List[MessageResponse]


class ChatRequest(BaseModel):
    """聊天请求"""
    conversation_id: Optional[int] = Field(None, description="对话ID，不提供则创建新对话")
    message: str = Field(..., min_length=1, max_length=5000, description="用户消息")
    use_document: Optional[int] = Field(None, description="使用的文档ID")


class ChatResponse(BaseModel):
    """聊天响应"""
    conversation_id: int
    message: MessageResponse
    law_context: Optional[str] = None
    web_context: Optional[str] = None


# ==================== 文档相关 ====================

class DocumentResponse(BaseModel):
    """文档信息响应"""
    id: int
    filename: str
    original_filename: str
    file_size: int
    file_type: str
    is_processed: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """文档列表响应"""
    documents: List[DocumentResponse]


# ==================== 通用响应 ====================

class SuccessResponse(BaseModel):
    """通用成功响应"""
    success: bool = True
    message: str = "操作成功"


class ErrorResponse(BaseModel):
    """通用错误响应"""
    success: bool = False
    message: str
    detail: Optional[str] = None


# ==================== 收藏夹相关 ====================

class FavoriteCreate(BaseModel):
    """创建收藏请求"""
    message_id: int
    question: str
    answer: str


class FavoriteResponse(BaseModel):
    """收藏响应"""
    id: int
    message_id: int
    question: str
    answer: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class FavoriteListResponse(BaseModel):
    """收藏列表响应"""
    favorites: List[FavoriteResponse]


# ==================== 管理员统计相关 ====================

class UserGrowthItem(BaseModel):
    """用户增长数据项"""
    date: str
    count: int


class TopQuestionItem(BaseModel):
    """高频问题数据项"""
    question: str
    count: int


class CategoryStatItem(BaseModel):
    """分类统计数据项"""
    category: str
    count: int
    percentage: float


class AdminStatsResponse(BaseModel):
    """管理员统计响应"""
    total_users: int
    total_conversations: int
    total_messages: int
    user_growth: List[UserGrowthItem]
    top_questions: List[TopQuestionItem]
    category_stats: List[CategoryStatItem]
