# coding: utf-8
"""
API 路由模块：聊天接口
"""
import asyncio
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc
import json

from ..database import get_db, Conversation, Message, Document, User
from ..schemas import (
    ChatRequest, ChatResponse, MessageResponse, SuccessResponse
)
from ..auth import get_current_user
from ..law_service import law_qa_service

router = APIRouter(prefix="/chat", tags=["聊天"])


async def read_document_content(file_path: str) -> str:
    """读取文档内容"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return None


@router.post("", response_model=ChatResponse, summary="发送消息")
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    发送消息并获取AI回答
    
    - **conversation_id**: 对话ID（可选，不提供则创建新对话）
    - **message**: 用户消息
    - **use_document**: 使用的文档ID（可选）
    """
    # 如果提供了对话ID，验证对话是否存在
    conversation = None
    if request.conversation_id:
        conversation = db.query(Conversation).filter(
            Conversation.id == request.conversation_id,
            Conversation.user_id == current_user.id
        ).first()
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="对话不存在"
            )
    else:
        # 创建新对话，使用问题的前20个字符作为标题
        title = request.message[:20] + "..." if len(request.message) > 20 else request.message
        conversation = Conversation(
            user_id=current_user.id,
            title=title
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
    
    # 保存用户消息
    user_message = Message(
        conversation_id=conversation.id,
        role="user",
        content=request.message
    )
    db.add(user_message)
    db.commit()
    
    # 如果使用文档，读取文档内容
    document_content = None
    if request.use_document:
        doc = db.query(Document).filter(
            Document.id == request.use_document,
            Document.user_id == current_user.id
        ).first()
        
        if doc:
            document_content = await read_document_content(doc.file_path)
    
    # 调用法律问答服务
    answer, law_context, web_context = await law_qa_service.ask_question(
        request.message,
        use_document_content=document_content
    )
    
    # 保存AI回答
    ai_message = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=answer,
        law_context=law_context,
        web_context=web_context
    )
    db.add(ai_message)
    db.commit()
    db.refresh(ai_message)
    
    # 更新对话时间
    from datetime import datetime
    conversation.updated_at = datetime.utcnow()
    db.commit()
    
    return ChatResponse(
        conversation_id=conversation.id,
        message=MessageResponse.model_validate(ai_message),
        law_context=law_context,
        web_context=web_context
    )


@router.post("/stream", summary="流式发送消息")
async def chat_stream(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    流式发送消息并获取AI回答
    
    返回 Server-Sent Events (SSE) 格式的流式响应
    """
    # 如果提供了对话ID，验证对话是否存在
    conversation = None
    if request.conversation_id:
        conversation = db.query(Conversation).filter(
            Conversation.id == request.conversation_id,
            Conversation.user_id == current_user.id
        ).first()
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="对话不存在"
            )
    else:
        # 创建新对话
        title = request.message[:20] + "..." if len(request.message) > 20 else request.message
        conversation = Conversation(
            user_id=current_user.id,
            title=title
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
    
    # 保存用户消息
    user_message = Message(
        conversation_id=conversation.id,
        role="user",
        content=request.message
    )
    db.add(user_message)
    db.commit()
    
    # 如果使用文档，读取文档内容
    document_content = None
    if request.use_document:
        doc = db.query(Document).filter(
            Document.id == request.use_document,
            Document.user_id == current_user.id
        ).first()
        
        if doc:
            document_content = await read_document_content(doc.file_path)
    
    conversation_id = conversation.id
    
    async def generate():
        full_answer = ""
        law_ctx = ""
        web_ctx = ""
        message_id = None
        
        try:
            # 流式生成回答 - 使用 law_service 的流式方法
            async for chunk in law_qa_service.stream_answer(
                request.message,
                use_document_content=document_content
            ):
                if isinstance(chunk, dict):
                    # 如果是字典，包含最终的上下文信息
                    law_ctx = chunk.get("law_context", "")
                    web_ctx = chunk.get("web_context", "")
                else:
                    # 如果是字符串，是流式token
                    full_answer += chunk
                    yield f"data: {json.dumps({'token': chunk}, ensure_ascii=False)}\n\n"
            
            # 保存AI回答到数据库
            ai_message = Message(
                conversation_id=conversation_id,
                role="assistant",
                content=full_answer,
                law_context=law_ctx,
                web_context=web_ctx
            )
            db.add(ai_message)
            db.commit()
            db.refresh(ai_message)
            message_id = ai_message.id
            
            # 发送完成信号，包含上下文
            completion_data = {
                'done': True,
                'conversation_id': conversation_id,
                'message_id': message_id,
                'law_context': law_ctx,
                'web_context': web_ctx
            }
            yield f"data: {json.dumps(completion_data, ensure_ascii=False)}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@router.get("/check-law", summary="检查问题是否与法律相关")
async def check_law_related(
    question: str,
    current_user: User = Depends(get_current_user)
):
    """检查问题是否与法律相关"""
    is_law = law_qa_service.is_law_related(question)
    return {"is_law_related": is_law}
