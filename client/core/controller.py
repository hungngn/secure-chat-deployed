import base64
import os
from .local_vault import LocalVault
from .network import NetworkClient
from lib.crypto import file_to_bytes, generate_identity_keys, generate_dh_keypair
from lib.ratchet import RatchetSession
import threading
import time

class Controller:
    def __init__(self, app):
        self.app = app
        self.vault = None 
        self.net = NetworkClient()
        self.sessions = {} 
        self.running = True

    def login(self, username, password, is_register=False):
        db_name = f"{username}.db"
        self.vault = LocalVault(db_name)
        
        # Thử mở Vault bằng mật khẩu
        if not self.vault.login(password):
            return False
        
        try:
            data = self.vault.load_identity()
        except Exception:
            data = None
        
        if is_register:
            # Nếu đăng ký nhưng file đã có data, có thể coi như login thành công hoặc báo lỗi
            if data:
                print("DEBUG: User already exists in local DB, logging in instead.")
                self.net.set_identity(username, data['sk'])
                self.start_polling()
                return True

            sk, vk = generate_identity_keys()
            pre_dh = generate_dh_keypair()
            pre_priv_hex = pre_dh.private_key.to_string().hex()
            
            payload = {
                "username": username,
                "identity_public_key": vk.to_string().hex(),
                "prekey_bundle": pre_dh.get_public_key().to_string().hex()
            }
            
            res = self.net.post("/register", payload)
            if res and res.get("status") == "ok":
                self.vault.save_identity(username, sk.to_string().hex())
                self.vault._save('my_identity', 'prekey_private', {"pk": pre_priv_hex})
                self.net.set_identity(username, sk.to_string().hex())
                self.start_polling()
                return True
            return False
            
        else: # TRƯỜNG HỢP LOGIN
            if data and data['username'] == username:
                # Nạp Identity Key vào NetworkClient để ký các yêu cầu API
                self.net.set_identity(username, data['sk'])
                self.start_polling()
                return True
            else:
                print(f"DEBUG: No identity found for {username} in {db_name}")
                return False

    def get_session(self, friend):
        if friend in self.sessions: return self.sessions[friend]
        state = self.vault.load_session(friend)
        if state:
            sess = RatchetSession()
            sess.load_state(state)
            self.sessions[friend] = sess
            return sess
            
        res = self.net.get("/get_prekey", {"username": friend})
        if res and "pre_key" in res:
            remote_pre_key = bytes.fromhex(res['pre_key'])
            # SỬA THAM SỐ ĐỒNG BỘ
            sess = RatchetSession(is_initiator=True, peer_pub=remote_pre_key)
            self.sessions[friend] = sess
            return sess
        return None

    def send_msg(self, friend, text):
        sess = self.get_session(friend)
        if not sess: return
        packet = sess.encrypt(text.encode())
        
        full_blob = packet['iv'] + packet['tag'] + packet['ciphertext']
        payload = {
            "to_user": friend,
            "encrypted_content": full_blob,
            "header": packet['header']
        }
        self.net.post("/send", payload)
        
        # CỰC KỲ QUAN TRỌNG: Lưu ngay lập tức
        self.vault.save_session(friend, sess.get_state())
        self.app.on_new_message(friend, text, True)

    def start_polling(self):
        threading.Thread(target=self._poll_loop, daemon=True).start()

    def _poll_loop(self):
        while self.running:
            try:
                msgs = self.net.get("/fetch")
                if msgs and "messages" in msgs:
                    for m in msgs["messages"]:
                        sender, blob = m['sender'], m['content']
                        packet = {
                            "header": m['header'], "iv": blob[:32],
                            "tag": blob[32:64], "ciphertext": blob[64:]
                        }
                        sess = self.get_session(sender)
                        if not sess:
                            vault_data = self.vault._load('my_identity', 'prekey_private')
                            pre_priv = vault_data['pk'] if vault_data else None
                            sess = RatchetSession(prekey_priv=pre_priv)
                            self.sessions[sender] = sess
                        
                        try:
                            plaintext = sess.decrypt(packet)
                            msg_text = plaintext.decode() # Giữ nguyên chuỗi thô để GUI check marker
                            self.app.on_new_message(sender, msg_text, False)
                            self.vault.save_session(sender, sess.get_state())
                        except Exception as e:
                            print(f"Decryption Error: {e}")
            except: pass
            time.sleep(2)

    def send_file(self, friend, file_path):
        sess = self.get_session(friend)
        if not sess: 
            print(f"Error: Không tìm thấy phiên làm việc với {friend}")
            return
            
        try:
            file_name = os.path.basename(file_path)
            with open(file_path, "rb") as f:
                file_bytes = f.read()
            
            # Đóng gói: FILE_SHARE|filename|content
            # Sử dụng base64 để bọc dữ liệu nhị phân của file vào chuỗi an toàn
            content_b64 = base64.b64encode(file_bytes).decode()
            raw_data = f"FILE_SHARE|{file_name}|{content_b64}".encode()
            
            packet = sess.encrypt(raw_data)
            full_blob = packet['iv'] + packet['tag'] + packet['ciphertext']
            
            payload = {
                "to_user": friend,
                "encrypted_content": full_blob,
                "header": packet['header']
            }
            
            res = self.net.post("/send", payload)
            if res:
                self.vault.save_session(friend, sess.get_state())
                self.app.on_new_message(friend, f"📎 Đã gửi file: {file_name}", True)
        except Exception as e:
            print(f"Lỗi gửi file: {e}")