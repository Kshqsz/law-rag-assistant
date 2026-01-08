# coding: utf-8
"""
API 路由模块：认证相关接口
"""
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import (
    UserCreate, UserResponse, UserLogin, Token, SuccessResponse
)
from ..auth import (
    authenticate_user, create_user, get_user_by_username,
    create_access_token, get_current_user, ACCESS_TOKEN_EXPIRE_MINUTES
)
from ..database import User

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/register", response_model=UserResponse, summary="用户注册")
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    用户注册接口
    
    - **username**: 用户名（3-50字符）
    - **password**: 密码（至少6位）
    """
    # 检查用户名是否已存在
    existing_user = get_user_by_username(db, user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已被注册"
        )
    
    # 创建用户
    user = create_user(db, user_data.username, user_data.password)
    return user


@router.post("/login", response_model=Token, summary="用户登录")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    用户登录接口，返回 JWT Token
    
    使用 OAuth2 表单格式：
    - **username**: 用户名
    - **password**: 密码
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id}
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/login/json", response_model=Token, summary="用户登录(JSON)")
async def login_json(user_data: UserLogin, db: Session = Depends(get_db)):
    """
    用户登录接口（JSON 格式），返回 JWT Token
    
    - **username**: 用户名
    - **password**: 密码
    """
    user = authenticate_user(db, user_data.username, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )
    
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id}
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse, summary="获取当前用户信息")
async def get_me(current_user: User = Depends(get_current_user)):
    """获取当前登录用户信息"""
    return current_user


@router.post("/logout", response_model=SuccessResponse, summary="用户登出")
async def logout(current_user: User = Depends(get_current_user)):
    """
    用户登出（客户端需要删除 Token）
    
    注：JWT 是无状态的，服务端无法主动失效 Token，
    登出操作需要客户端配合删除本地存储的 Token
    """
    return {"success": True, "message": "登出成功"}
