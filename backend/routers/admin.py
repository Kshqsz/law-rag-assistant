# coding: utf-8
"""管理员 API 路由"""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from collections import Counter
import re

from ..database import get_db, User, Conversation, Message, QuestionLog
from ..schemas import AdminStatsResponse, SuccessResponse
from ..auth import get_current_user

router = APIRouter(prefix="/admin", tags=["管理员"])


def require_admin(current_user: User = Depends(get_current_user)):
    """验证管理员权限"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return current_user


# 法律分类关键词
LAW_CATEGORIES = {
    "刑法": ["杀人", "盗窃", "抢劫", "诈骗", "故意伤害", "强奸", "犯罪", "刑事", "判刑", "死刑", "无期徒刑"],
    "民法": ["合同", "债务", "借款", "租赁", "买卖", "侵权", "赔偿", "民事", "财产", "物权"],
    "婚姻家庭法": ["离婚", "结婚", "抚养", "赡养", "婚姻", "家庭", "遗产", "继承", "子女"],
    "劳动法": ["劳动", "工资", "辞退", "解雇", "加班", "社保", "工伤", "劳动合同", "裁员"],
    "行政法": ["行政", "处罚", "拘留", "罚款", "许可", "执法", "复议", "诉讼"],
    "公司法": ["公司", "股权", "股东", "法人", "注册", "破产", "清算"],
    "知识产权法": ["专利", "商标", "著作权", "版权", "侵权", "知识产权"],
    "其他": []
}


def classify_question(question: str) -> str:
    """对问题进行法律分类"""
    for category, keywords in LAW_CATEGORIES.items():
        if category == "其他":
            continue
        for keyword in keywords:
            if keyword in question:
                return category
    return "其他"


@router.get("/stats", response_model=AdminStatsResponse, summary="获取统计数据")
async def get_admin_stats(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """获取管理员统计数据"""
    
    # 基础统计
    total_users = db.query(User).count()
    total_conversations = db.query(Conversation).count()
    total_messages = db.query(Message).count()
    
    # 用户增长趋势（最近30天）
    user_growth = []
    for i in range(30, -1, -1):
        date = datetime.utcnow() - timedelta(days=i)
        date_str = date.strftime("%Y-%m-%d")
        count = db.query(User).filter(
            func.date(User.created_at) <= date_str
        ).count()
        user_growth.append({"date": date_str, "count": count})
    
    # 高频问题 Top 10
    user_messages = db.query(Message).filter(
        Message.role == "user"
    ).order_by(Message.created_at.desc()).limit(500).all()
    
    question_counter = Counter()
    for msg in user_messages:
        # 简化问题（取前20个字符作为关键）
        short_q = msg.content[:30] if len(msg.content) > 30 else msg.content
        question_counter[short_q] += 1
    
    top_questions = [
        {"question": q, "count": c}
        for q, c in question_counter.most_common(10)
    ]
    
    # 知识库覆盖领域统计
    category_counter = Counter()
    for msg in user_messages:
        cat = classify_question(msg.content)
        category_counter[cat] += 1
    
    total_categorized = sum(category_counter.values()) or 1
    category_stats = [
        {
            "category": cat,
            "count": count,
            "percentage": round(count / total_categorized * 100, 1)
        }
        for cat, count in category_counter.most_common()
    ]
    
    return {
        "total_users": total_users,
        "total_conversations": total_conversations,
        "total_messages": total_messages,
        "user_growth": user_growth,
        "top_questions": top_questions,
        "category_stats": category_stats
    }


@router.post("/create-admin", response_model=SuccessResponse, summary="创建管理员账号")
async def create_admin_user(
    username: str = "admin",
    password: str = "admin123",
    db: Session = Depends(get_db)
):
    """创建管理员账号（仅用于初始化）"""
    from ..auth import get_password_hash, get_user_by_username
    
    existing = get_user_by_username(db, username)
    if existing:
        # 更新为管理员
        existing.is_admin = True
        db.commit()
        return {"success": True, "message": f"用户 {username} 已设置为管理员"}
    
    # 创建新管理员
    admin = User(
        username=username,
        hashed_password=get_password_hash(password),
        is_admin=True
    )
    db.add(admin)
    db.commit()
    return {"success": True, "message": f"管理员 {username} 创建成功"}
