#!/usr/bin/env python
# coding: utf-8
"""
修复 favorites 表的 message_id 字段，使其可以为 NULL
"""
import sqlite3
import os
from datetime import datetime

DB_PATH = "./law_rag.db"

def fix_favorites_table():
    """修复 favorites 表"""
    if not os.path.exists(DB_PATH):
        print(f"❌ 数据库文件不存在: {DB_PATH}")
        return
    
    # 备份数据库
    backup_path = f"./law_rag_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    print(f"📦 备份数据库到: {backup_path}")
    import shutil
    shutil.copy2(DB_PATH, backup_path)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # 1. 查看当前表结构
        print("\n📋 当前 favorites 表结构:")
        cursor.execute("PRAGMA table_info(favorites)")
        for row in cursor.fetchall():
            print(f"  {row}")
        
        # 2. 查看现有数据
        cursor.execute("SELECT COUNT(*) FROM favorites")
        count = cursor.fetchone()[0]
        print(f"\n📊 当前收藏记录数: {count}")
        
        # 3. 创建新表（message_id 可为 NULL）
        print("\n🔧 创建新的 favorites 表...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS favorites_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                message_id INTEGER,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (message_id) REFERENCES messages (id)
            )
        """)
        
        # 4. 复制数据
        print("📝 复制现有数据到新表...")
        cursor.execute("""
            INSERT INTO favorites_new (id, user_id, message_id, question, answer, created_at)
            SELECT id, user_id, message_id, question, answer, created_at
            FROM favorites
        """)
        
        # 5. 删除旧表
        print("🗑️  删除旧表...")
        cursor.execute("DROP TABLE favorites")
        
        # 6. 重命名新表
        print("✏️  重命名新表...")
        cursor.execute("ALTER TABLE favorites_new RENAME TO favorites")
        
        # 7. 提交更改
        conn.commit()
        
        # 8. 验证新表结构
        print("\n✅ 新的 favorites 表结构:")
        cursor.execute("PRAGMA table_info(favorites)")
        for row in cursor.fetchall():
            print(f"  {row}")
        
        cursor.execute("SELECT COUNT(*) FROM favorites")
        new_count = cursor.fetchone()[0]
        print(f"\n✅ 修复完成！收藏记录数: {new_count}")
        
        if new_count == count:
            print("✅ 所有数据已成功迁移")
        else:
            print(f"⚠️  数据数量不匹配: {count} → {new_count}")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("修复 favorites 表 - 允许 message_id 为 NULL")
    print("=" * 60)
    fix_favorites_table()
    print("\n" + "=" * 60)
    print("修复完成！请重启后端服务。")
    print("=" * 60)
