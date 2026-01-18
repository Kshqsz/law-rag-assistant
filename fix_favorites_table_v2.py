#!/usr/bin/env python3
# coding: utf-8
"""
修复 favorites 表结构
- 将 message_id 改为可为 NULL
- 添加 law_context 和 web_context 字段
"""

import sqlite3
import os

DB_PATH = "./law_assistant.db"

def fix_favorites_table():
    """修复 favorites 表"""
    
    if not os.path.exists(DB_PATH):
        print(f"❌ 数据库文件不存在: {DB_PATH}")
        return
    
    print(f"📂 打开数据库: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # 1. 检查当前表结构
        print("\n📋 当前 favorites 表结构:")
        cursor.execute("PRAGMA table_info(favorites)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  - {col[1]}: {col[2]} {'NOT NULL' if col[3] else 'NULL'}")
        
        # 2. 备份现有数据
        print("\n💾 备份现有收藏数据...")
        cursor.execute("SELECT * FROM favorites")
        old_data = cursor.fetchall()
        print(f"  找到 {len(old_data)} 条收藏记录")
        
        # 3. 删除旧表
        print("\n🗑️  删除旧表...")
        cursor.execute("DROP TABLE IF EXISTS favorites")
        
        # 4. 创建新表（message_id 可为 NULL，添加 law_context 和 web_context）
        print("\n🔨 创建新表结构...")
        cursor.execute("""
            CREATE TABLE favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                message_id INTEGER,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                law_context TEXT,
                web_context TEXT,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (message_id) REFERENCES messages(id)
            )
        """)
        
        # 5. 恢复数据（只恢复前5列，新字段设为空）
        print("\n📥 恢复收藏数据...")
        if old_data:
            # 旧表结构: id, user_id, message_id, question, answer, created_at
            for row in old_data:
                cursor.execute("""
                    INSERT INTO favorites (id, user_id, message_id, question, answer, law_context, web_context, created_at)
                    VALUES (?, ?, ?, ?, ?, '', '', ?)
                """, (row[0], row[1], row[2], row[3], row[4], row[5]))
            print(f"  ✅ 恢复了 {len(old_data)} 条记录")
        
        # 6. 验证新表结构
        print("\n✅ 新的 favorites 表结构:")
        cursor.execute("PRAGMA table_info(favorites)")
        columns = cursor.fetchall()
        for col in columns:
            nullable = "NULL" if not col[3] else "NOT NULL"
            print(f"  - {col[1]}: {col[2]} {nullable}")
        
        # 7. 提交更改
        conn.commit()
        print("\n🎉 数据库修复完成！")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ 修复失败: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    fix_favorites_table()
