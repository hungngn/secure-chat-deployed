# client/core/local_vault.py
import sqlite3
import json

class LocalVault:
    def __init__(self, db_filename):
        self.db_filename = db_filename
        self.conn = sqlite3.connect(db_filename, check_same_thread=False)
        self._init_db()

    def _init_db(self):
        # Đảm bảo tạo đủ 3 bảng quan trọng
        self.conn.execute("CREATE TABLE IF NOT EXISTS identity (key_name TEXT PRIMARY KEY, data TEXT)")
        self.conn.execute("CREATE TABLE IF NOT EXISTS sessions (friend_id TEXT PRIMARY KEY, state TEXT)")
        self.conn.execute('''CREATE TABLE IF NOT EXISTS chat_history 
                          (friend_id TEXT, message TEXT, is_me INTEGER, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
        self.conn.commit()

    def login(self, password):
        return True # MVP chấp nhận mọi pass

    def _save(self, table, pk_value, data_dict):
        # Tự động chọn tên cột khóa chính dựa trên tên bảng
        pk_col = "key_name" if table == "identity" else "friend_id"
        col_data = "data" if table == "identity" else "state"
        
        query = f"INSERT OR REPLACE INTO {table} ({pk_col}, {col_data}) VALUES (?, ?)"
        self.conn.execute(query, (pk_value, json.dumps(data_dict)))
        self.conn.commit()

    def _load(self, table, pk_value):
        pk_col = "key_name" if table == "identity" else "friend_id"
        col_data = "data" if table == "identity" else "state"
        
        cursor = self.conn.execute(f"SELECT {col_data} FROM {table} WHERE {pk_col} = ?", (pk_value,))
        row = cursor.fetchone()
        return json.loads(row[0]) if row else None

    def save_identity(self, username, sk): self._save('identity', 'my_identity', {"username": username, "sk": sk})
    def load_identity(self): return self._load('identity', 'my_identity')
    def save_session(self, friend_id, state): self._save('sessions', friend_id, state)
    def load_session(self, friend_id): return self._load('sessions', friend_id)

    def save_message(self, friend_id, message, is_me):
        self.conn.execute("INSERT INTO chat_history (friend_id, message, is_me) VALUES (?, ?, ?)",
                          (friend_id, message, 1 if is_me else 0))
        self.conn.commit()

    def get_chat_history(self, friend_id):
        cursor = self.conn.execute("SELECT message, is_me FROM chat_history WHERE friend_id = ? ORDER BY timestamp ASC", (friend_id,))
        return cursor.fetchall()