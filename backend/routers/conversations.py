# coding: utf-8
"""
API 路由模块：对话管理接口
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from ..database import get_db, Conversation, Message, User, Feedback
from ..schemas import (
    ConversationCreate, ConversationUpdate, ConversationResponse,
    ConversationListResponse, MessageResponse, MessageListResponse,
    SuccessResponse
)
from ..auth import get_current_user

router = APIRouter(prefix="/conversations", tags=["对话管理"])


@router.get("", response_model=ConversationListResponse, summary="获取对话列表")
async def list_conversations(
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取当前用户的对话列表，按更新时间倒序排列，支持分页"""
    query = db.query(Conversation).filter(
        Conversation.user_id == current_user.id
    ).order_by(desc(Conversation.updated_at))
    
    total = query.count()
    conversations = query.offset((page - 1) * page_size).limit(page_size).all()
    
    return {
        "conversations": conversations,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.post("", response_model=ConversationResponse, summary="创建新对话")
async def create_conversation(
    data: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建一个新对话"""
    conversation = Conversation(
        user_id=current_user.id,
        title=data.title or "新对话"
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    
    return conversation


@router.get("/{conversation_id}", response_model=ConversationResponse, summary="获取对话详情")
async def get_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取指定对话的详情"""
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在"
        )
    
    return conversation


@router.put("/{conversation_id}", response_model=ConversationResponse, summary="更新对话标题")
async def update_conversation(
    conversation_id: int,
    data: ConversationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新对话标题"""
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在"
        )
    
    conversation.title = data.title
    db.commit()
    db.refresh(conversation)
    
    return conversation


@router.delete("/{conversation_id}", response_model=SuccessResponse, summary="删除对话")
async def delete_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除指定对话及其所有消息"""
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在"
        )
    
    db.delete(conversation)
    db.commit()
    
    return {"success": True, "message": "对话已删除"}


@router.get("/{conversation_id}/messages", response_model=MessageListResponse, summary="获取对话消息")
async def list_messages(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取指定对话的所有消息"""
    # 验证对话存在且属于当前用户
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在"
        )
    
    messages = db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).order_by(Message.created_at).all()
    
    # 查询当前用户对这些消息的反馈
    message_ids = [m.id for m in messages]
    feedbacks = db.query(Feedback).filter(
        Feedback.user_id == current_user.id,
        Feedback.message_id.in_(message_ids)
    ).all() if message_ids else []
    feedback_map = {f.message_id: f.rating for f in feedbacks}
    
    # 构建响应，附带反馈信息
    result = []
    for msg in messages:
        msg_dict = {
            "id": msg.id,
            "role": msg.role,
            "content": msg.content,
            "law_context": msg.law_context,
            "web_context": msg.web_context,
            "created_at": msg.created_at,
            "feedback": feedback_map.get(msg.id, 0)
        }
        result.append(msg_dict)
    
    return {"messages": result}


@router.delete("/{conversation_id}/messages", response_model=SuccessResponse, summary="清空对话消息")
async def clear_messages(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """清空指定对话的所有消息"""
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在"
        )
    
    db.query(Message).filter(Message.conversation_id == conversation_id).delete()
    db.commit()
    
    return {"success": True, "message": "消息已清空"}
