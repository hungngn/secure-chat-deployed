# lib/ratchet.py
from Crypto.Hash import HMAC, SHA256
from .crypto import (
    generate_dh_keypair, compute_dh, encrypt_gcm, decrypt_gcm,
    load_dh_keypair 
)
import json

class RatchetSession:
    SALT = b'SecureChat_V1_Initial_Salt'

    def __init__(self, rk=None, is_initiator=False, peer_pub=None, prekey_priv=None):
        self.rk = rk if rk else b'\x00' * 32
        self.ck_s = None
        self.ck_r = None
        self.n_s = 0
        self.n_r = 0
        self.dh_remote = peer_pub
        
        if prekey_priv:
            self.dh_pair = load_dh_keypair(prekey_priv)
        else:
            self.dh_pair = generate_dh_keypair()
            
        if is_initiator and peer_pub:
            secret = compute_dh(self.dh_pair, peer_pub)
            # Khởi tạo chuỗi gửi ngay lập tức cho người chủ động
            self.rk, self.ck_s = self._kdf_root(self.SALT, secret)

    def _kdf_root(self, rk, dh_out):
        derived = HMAC.new(rk, dh_out, digestmod=SHA256).digest()
        return derived[:32], derived[32:]

    def _kdf_chain(self, ck):
        if ck is None:
            # Sửa lỗi: Thay vì báo lỗi, hãy cố gắng cảnh báo hoặc kiểm tra lại logic khởi tạo
            raise ValueError("Chain Key is not initialized. Handshake might be incomplete.")
        # Sử dụng đúng cú pháp HMAC.new static method
        new_ck = HMAC.new(ck, b'\x01', SHA256).digest()
        mk = HMAC.new(ck, b'\x02', SHA256).digest()
        return new_ck, mk

    def encrypt(self, pt: bytes) -> dict:
        # Đảm bảo ck_s tồn tại
        if self.ck_s is None:
             raise ValueError("Khởi tạo phiên chat thất bại: Thiếu khóa gửi (Chain Key S)")
             
        self.ck_s, mk = self._kdf_chain(self.ck_s)
        header = {
            "dh_pub": self.dh_pair.get_public_key().to_string().hex(),
            "n": self.n_s
        }
        self.n_s += 1
        ad = json.dumps(header, sort_keys=True, separators=(',', ':')).encode()
        iv, ct, tag = encrypt_gcm(mk, pt, associated_data=ad)
        
        return {
            "header": header, 
            "ciphertext": ct.hex(), 
            "iv": iv.hex(), 
            "tag": tag.hex()
        }

    def decrypt(self, packet: dict) -> bytes:
        header = packet['header']
        remote_pub = bytes.fromhex(header['dh_pub'])
        
        # Lưu state để rollback nếu fail
        old_state = (self.rk, self.ck_r, self.ck_s, self.dh_remote)
        
        try:
            if self.ck_r is None:
                secret = compute_dh(self.dh_pair, remote_pub)
                self.rk, self.ck_r = self._kdf_root(self.SALT, secret)
                self.dh_remote = remote_pub
                # Tự động tạo ck_s cho Bob để có thể phản hồi Alice ngay lập tức
                self.dh_pair = generate_dh_keypair()
                self.rk, self.ck_s = self._kdf_root(self.rk, compute_dh(self.dh_pair, self.dh_remote))
            
            elif remote_pub != self.dh_remote:
                self.rk, self.ck_r = self._kdf_root(self.rk, compute_dh(self.dh_pair, remote_pub))
                self.dh_remote = remote_pub
                self.dh_pair = generate_dh_keypair()
                self.rk, self.ck_s = self._kdf_root(self.rk, compute_dh(self.dh_pair, self.dh_remote))
                self.n_r = 0

            self.ck_r, mk = self._kdf_chain(self.ck_r)
            ad = json.dumps(header, sort_keys=True, separators=(',', ':')).encode()
            
            return decrypt_gcm(mk, bytes.fromhex(packet['iv']), bytes.fromhex(packet['ciphertext']), 
                             bytes.fromhex(packet['tag']), associated_data=ad)
        except Exception as e:
            self.rk, self.ck_r, self.ck_s, self.dh_remote = old_state
            raise e

    def get_state(self):
        return {
            "rk": self.rk.hex(), "dh_priv": self.dh_pair.private_key.to_string().hex(),
            "dh_remote": self.dh_remote.hex() if self.dh_remote else None,
            "ck_s": self.ck_s.hex() if self.ck_s else None, 
            "ck_r": self.ck_r.hex() if self.ck_r else None,
            "ns": self.n_s, "nr": self.n_r
        }

    def load_state(self, s):
        self.rk = bytes.fromhex(s['rk'])
        self.dh_pair = load_dh_keypair(s['dh_priv'])
        self.dh_remote = bytes.fromhex(s['dh_remote']) if s['dh_remote'] else None
        self.ck_s = bytes.fromhex(s['ck_s']) if s['ck_s'] else None
        self.ck_r = bytes.fromhex(s['ck_r']) if s['ck_r'] else None
        self.n_s, self.n_r = s['ns'], s['nr']