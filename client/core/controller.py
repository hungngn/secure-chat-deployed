import threading
import time
import os
import base64
import json

from client.core.network import NetworkClient
from client.core.local_vault import LocalVault
from lib.crypto import generate_identity_keys, generate_dh_keypair
from lib.ratchet import RatchetSession

class Controller:
    def __init__(self, app):
        self.app = app
        self.vault = None 
        self.net = NetworkClient()
        self.sessions = {} 
        self.running = True

    def login(self, username, password, is_register=False):
        self.vault = LocalVault(f"{username}.db")
        if not self.vault.login(password): return False
        data = self.vault.load_identity()
        
        if is_register:
            if data: return self.login(username, password, False)
            sk, vk = generate_identity_keys()
            pre_dh = generate_dh_keypair()
            payload = {"username": username, "identity_public_key": vk.to_string().hex(), 
                       "prekey_bundle": pre_dh.get_public_key().to_string().hex()}
            if self.net.post("/register", payload):
                self.vault.save_identity(username, sk.to_string().hex())
                self.vault._save('identity', 'prekey_private', {"pk": pre_dh.private_key.to_string().hex()})
                self.net.set_identity(username, sk.to_string().hex())
                self.start_polling(); return True
        elif data and data['username'] == username:
            self.net.set_identity(username, data['sk'])
            self.start_polling(); return True
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
            sess = RatchetSession(is_initiator=True, peer_pub=bytes.fromhex(res['pre_key']))
            self.sessions[friend] = sess
            return sess
        return None

    def send_msg(self, friend, text):
        sess = self.get_session(friend)
        if not sess: return
        packet = sess.encrypt(text.encode())
        payload = {"to_user": friend, "encrypted_content": packet['iv'] + packet['tag'] + packet['ciphertext'], "header": packet['header']}
        if self.net.post("/send", payload):
            self.vault.save_message(friend, text, True)
            self.vault.save_session(friend, sess.get_state())
            self.app.on_new_message(friend, text, True)

    def send_file(self, friend, file_path):
        sess = self.get_session(friend)
        if not sess: return
        try:
            fname = os.path.basename(file_path)
            with open(file_path, "rb") as f: content = base64.b64encode(f.read()).decode()
            raw = f"FILE_SHARE|{fname}|{content}"
            packet = sess.encrypt(raw.encode())
            payload = {"to_user": friend, "encrypted_content": packet['iv'] + packet['tag'] + packet['ciphertext'], "header": packet['header']}
            if self.net.post("/send", payload):
                self.vault.save_message(friend, raw, True)
                self.vault.save_session(friend, sess.get_state())
                self.app.on_new_message(friend, raw, True)
        except: pass

    def start_polling(self):
        self.running = True
        threading.Thread(target=self._poll_loop, daemon=True).start()

    def _poll_loop(self):
        while self.running:
            try:
                msgs = self.net.get("/fetch")
                if msgs and "messages" in msgs:
                    for m in msgs["messages"]:
                        sender, blob = m['sender'], m['content']
                        packet = {"header": m['header'], "iv": blob[:32], "tag": blob[32:64], "ciphertext": blob[64:]}
                        sess = self.get_session(sender)
                        if not sess:
                            p_data = self.vault._load('identity', 'prekey_private')
                            sess = RatchetSession(prekey_priv=p_data['pk'])
                            self.sessions[sender] = sess
                        try:
                            pt = sess.decrypt(packet).decode()
                            self.vault.save_message(sender, pt, False)
                            self.vault.save_session(sender, sess.get_state())
                            if self.app: self.app.after(0, lambda s=sender, t=pt: self.app.on_new_message(s, t, False))
                        except: pass
                time.sleep(2)
            except: time.sleep(5)