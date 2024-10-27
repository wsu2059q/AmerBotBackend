import json
import sqlite3
from config import sqlite_db_path

def get_bind(group_id, source):
    conn = sqlite3.connect(sqlite_db_path)
    c = conn.cursor()
    if source == "QQ":
        c.execute("SELECT YH_group_id FROM bindings WHERE QQ_group_id=?", (group_id,))
    elif source == "云湖":
        c.execute("SELECT QQ_group_id FROM bindings WHERE YH_group_id=?", (group_id,))
    results = c.fetchall()
    conn.close()
    return [result[0] for result in results] if results else []

def bind_qq_group(QQ_group_id, YH_group_id, user_id, sync_mode='AllSync'):
    try:
        conn = sqlite3.connect(sqlite_db_path)
        c = conn.cursor()
        c.execute("SELECT QQ_group_id FROM bindings WHERE YH_group_id=?", (YH_group_id,))
        existing_binding = c.fetchone()
        if existing_binding:
            return "Repeat"
        if not YH_group_id.isdigit():
            return "NotDigit"
        c.execute("INSERT INTO bindings (QQ_group_id, YH_group_id, sync_mode, user_id) VALUES (?, ?, ?, ?)", (QQ_group_id, YH_group_id, sync_mode, user_id))
        conn.commit()
        conn.close()
        return "Success"
    except sqlite3.Error as e:
        return "Failed"

def set_sync(YH_group_id, sync_mode):
    try:
        conn = sqlite3.connect(sqlite_db_path)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM bindings WHERE YH_group_id=?", (YH_group_id,))
        count = c.fetchone()[0]
        if count == 0:
            conn.close()
            return "NotBind"
        c.execute("UPDATE bindings SET sync_mode=? WHERE YH_group_id=?", (sync_mode, YH_group_id))
        conn.commit()
        conn.close()
        return "Success"
    except sqlite3.Error as e:
        return "Failed"

def unbind_qq_group(YH_group_id):
    try:
        conn = sqlite3.connect(sqlite_db_path)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM bindings WHERE YH_group_id=?", (YH_group_id,))
        count = c.fetchone()[0]
        if count == 0:
            conn.close()
            return "NotBind"
        c.execute("DELETE FROM bindings WHERE YH_group_id=?", (YH_group_id,))
        conn.commit()
        conn.close()
        return "Success"
    except sqlite3.Error as e:
        return "Failed"

def get_sync_mode(group_id, source):
    conn = sqlite3.connect(sqlite_db_path)
    c = conn.cursor()
    
    # 查询同步模式
    if source == "QQ":
        c.execute("SELECT sync_mode FROM bindings WHERE QQ_group_id=?", (group_id,))
    elif source == "云湖":
        c.execute("SELECT sync_mode FROM bindings WHERE YH_group_id=?", (group_id,))
    
    result = c.fetchone()
    conn.close()
    print(result)
    return result[0] if result else None