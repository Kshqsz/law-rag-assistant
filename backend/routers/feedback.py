# coding: utf-8
"""API 路由模块：用户反馈"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db, Feedback, Message, User
from ..schemas import FeedbackCreate, FeedbackResponse, SuccessResponse
from ..auth import get_current_user

router = APIRouter(prefix="/feedback", tags=["反馈"])


@router.post("", response_model=FeedbackResponse, summary="提交反馈")
async def create_feedback(
    request: FeedbackCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    对AI回答进行 👍👎 评价
    
    - **message_id**: 消息ID
    - **rating**: 1=好评, -1=差评
    - **comment**: 可选的文字反馈
    """
    # 验证 rating 值
    if request.rating not in (1, -1):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="rating 只能为 1（好评）或 -1（差评）"
        )
    
    # 验证消息是否存在
    message = db.query(Message).filter(Message.id == request.message_id).first()
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="消息不存在"
        )
    
    # 检查是否已经评价过（允许更新）
    existing = db.query(Feedback).filter(
        Feedback.user_id == current_user.id,
        Feedback.message_id == request.message_id
    ).first()
    
    if existing:
        # 更新已有评价
        existing.rating = request.rating
        existing.comment = request.comment
        db.commit()
        db.refresh(existing)
        return existing
    
    # 创建新评价
    feedback = Feedback(
        user_id=current_user.id,
        message_id=request.message_id,
        rating=request.rating,
        comment=request.comment
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return feedback


@router.get("/message/{message_id}", summary="获取某条消息的反馈")
async def get_message_feedback(
    message_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取当前用户对某条消息的反馈"""
    feedback = db.query(Feedback).filter(
        Feedback.user_id == current_user.id,
        Feedback.message_id == message_id
    ).first()
    
    if feedback:
        return {"rating": feedback.rating, "comment": feedback.comment}
    return {"rating": 0, "comment": None}


@router.delete("/{message_id}", response_model=SuccessResponse, summary="取消反馈")
async def delete_feedback(
    message_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """取消对某条消息的反馈"""
    feedback = db.query(Feedback).filter(
        Feedback.user_id == current_user.id,
        Feedback.message_id == message_id
    ).first()
    
    if not feedback:
        raise HTTPException(status_code=404, detail="未找到反馈记录")
    
    db.delete(feedback)
    db.commit()
    return {"success": True, "message": "反馈已取消"}
