# coding: utf-8
"""收藏夹 API 路由"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db, Favorite, Message
from ..schemas import FavoriteCreate, FavoriteResponse, FavoriteListResponse, SuccessResponse
from ..auth import get_current_user
from ..database import User

router = APIRouter(prefix="/favorites", tags=["收藏夹"])


@router.post("", response_model=FavoriteResponse, summary="添加收藏")
async def add_favorite(
    data: FavoriteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """添加消息到收藏夹"""
    # 检查消息是否存在
    message = db.query(Message).filter(Message.id == data.message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="消息不存在")
    
    # 检查是否已收藏
    existing = db.query(Favorite).filter(
        Favorite.user_id == current_user.id,
        Favorite.message_id == data.message_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="已收藏过此消息")
    
    favorite = Favorite(
        user_id=current_user.id,
        message_id=data.message_id,
        question=data.question,
        answer=data.answer
    )
    db.add(favorite)
    db.commit()
    db.refresh(favorite)
    return favorite


@router.get("", response_model=FavoriteListResponse, summary="获取收藏列表")
async def list_favorites(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取用户的收藏列表"""
    favorites = db.query(Favorite).filter(
        Favorite.user_id == current_user.id
    ).order_by(Favorite.created_at.desc()).all()
    return {"favorites": favorites}


@router.delete("/{favorite_id}", response_model=SuccessResponse, summary="删除收藏")
async def delete_favorite(
    favorite_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除收藏"""
    favorite = db.query(Favorite).filter(
        Favorite.id == favorite_id,
        Favorite.user_id == current_user.id
    ).first()
    
    if not favorite:
        raise HTTPException(status_code=404, detail="收藏不存在")
    
    db.delete(favorite)
    db.commit()
    return {"success": True, "message": "删除成功"}
