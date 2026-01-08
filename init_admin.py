#!/usr/bin/env python
# coding: utf-8
"""
初始化管理员账号脚本
用法: python init_admin.py [username] [password]
默认: admin / admin123
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.database import get_db, User, init_db
from backend.auth import get_password_hash, get_user_by_username

def create_admin(username: str = "admin", password: str = "admin123"):
    """创建管理员账号"""
    init_db()
    
    # 获取数据库连接
    db = next(get_db())
    
    try:
        existing = get_user_by_username(db, username)
        if existing:
            existing.is_admin = True
            db.commit()
            print(f"✅ 用户 '{username}' 已设置为管理员")
        else:
            admin = User(
                username=username,
                hashed_password=get_password_hash(password),
                is_admin=True
            )
            db.add(admin)
            db.commit()
            print(f"✅ 管理员 '{username}' 创建成功")
            print(f"   用户名: {username}")
            print(f"   密码: {password}")
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) >= 3:
        create_admin(sys.argv[1], sys.argv[2])
    elif len(sys.argv) == 2:
        create_admin(sys.argv[1])
    else:
        create_admin()
