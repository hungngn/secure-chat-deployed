import sqlite3
import json
from lib.crypto import encrypt_gcm, decrypt_gcm, derive_master_key

class LocalVault:
    def __init__(self, db_filename="client_vault.db"):
        # Cho phép đặt tên file DB khác nhau cho mỗi user
        self.db_filename = db_filename
        self.master_key = None
        self._init_db()

    def _init_db(self):
        # Dùng self.db_filename thay vì DB_NAME cố định
        conn = sqlite3.connect(self.db_filename)
        conn.execute('CREATE TABLE IF NOT EXISTS my_identity (key_name TEXT PRIMARY KEY, blob BLOB)')
        conn.execute('CREATE TABLE IF NOT EXISTS sessions (username TEXT PRIMARY KEY, blob BLOB)')
        conn.commit()
        conn.close()

    def login(self, password: str) -> bool:
        try:
            self.master_key = derive_master_key(password)
            return True
        except: return False

    def _save(self, table, key, data_dict):
        if not self.master_key: raise Exception("Vault Locked")
        pt = json.dumps(data_dict).encode()
        iv, ct, tag = encrypt_gcm(self.master_key, pt)
        blob = iv + tag + ct
        
        conn = sqlite3.connect(self.db_filename) # <--- Sửa ở đây
        conn.execute(f"INSERT OR REPLACE INTO {table} VALUES (?, ?)", (key, blob))
        conn.commit()
        conn.close()

    def _load(self, table, key):
        if not self.master_key: raise Exception("Vault Locked")
        conn = sqlite3.connect(self.db_filename)
        
        # SỬA DÒNG NÀY: Dùng tham số key thay vì ép cứng 'user_main'
        query = f"SELECT blob FROM {table} WHERE key_name=?" if table=='my_identity' else f"SELECT blob FROM {table} WHERE username=?"
        row = conn.execute(query, (key,)).fetchone()
        
        conn.close()
        if not row: return None
        blob = row[0]
        try:
            return json.loads(decrypt_gcm(self.master_key, blob[:16], blob[32:], blob[16:32]))
        except:
            return None

    def save_identity(self, username, sk_hex):
        self._save('my_identity', 'user_main', {"username": username, "sk": sk_hex})

    def load_identity(self):
        return self._load('my_identity', 'user_main')

    def save_session(self, friend, state):
        self._save('sessions', friend, state)

    def load_session(self, friend):
        return self._load('sessions', friend)