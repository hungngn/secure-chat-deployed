import sqlite3
import json
import time

DB_NAME = "server.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, id_key TEXT, pre_key TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY, sender TEXT, receiver TEXT, content TEXT, header TEXT, timestamp REAL)')
    conn.commit()
    conn.close()

def add_user(u, id_k, pre_k):
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.execute("INSERT INTO users VALUES (?, ?, ?)", (u, id_k, pre_k))
        conn.commit()
        return True
    except: return False

def get_user(u):
    conn = sqlite3.connect(DB_NAME)
    row = conn.execute("SELECT id_key, pre_key FROM users WHERE username=?", (u,)).fetchone()
    conn.close()
    return row

def save_msg(sender, receiver, content, header):
    conn = sqlite3.connect(DB_NAME)
    conn.execute("INSERT INTO messages (sender, receiver, content, header, timestamp) VALUES (?, ?, ?, ?, ?)",
                 (sender, receiver, content, json.dumps(header), time.time()))
    conn.commit()
    conn.close()

def fetch_msgs(receiver):
    conn = sqlite3.connect(DB_NAME)
    rows = conn.execute("SELECT id, sender, content, header, timestamp FROM messages WHERE receiver=?", (receiver,)).fetchall()
    if rows:
        ids = [str(r[0]) for r in rows]
        conn.execute(f"DELETE FROM messages WHERE id IN ({','.join(ids)})")
        conn.commit()
    conn.close()
    return [{"sender": r[1], "content": r[2], "header": json.loads(r[3]), "ts": r[4]} for r in rows]