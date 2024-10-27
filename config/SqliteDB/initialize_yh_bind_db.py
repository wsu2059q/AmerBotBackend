import sqlite3
import os
sqlite_db_path = "config/SqliteDB/bind/yh.db"
def initialize_database():
    if not os.path.exists(sqlite_db_path):
        print(f"数据库文件 {sqlite_db_path} 不存在，正在创建...")
        os.makedirs(os.path.dirname(sqlite_db_path), exist_ok=True)
        open(sqlite_db_path, 'a').close()
    conn = sqlite3.connect(sqlite_db_path)
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS bindings (
        QQ_group_id TEXT,
        YH_group_id TEXT UNIQUE,
        user_id TEXT,
        sync_mode TEXT
    )
    ''')
    conn.commit()
    conn.close()
    print(f"数据库初始化完成。")

if __name__ == "__main__":
    initialize_database()