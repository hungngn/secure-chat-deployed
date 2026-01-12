from Crypto.Hash import HMAC, SHA256
from .crypto import (
    generate_dh_keypair, compute_dh, encrypt_gcm, decrypt_gcm,
    load_dh_keypair 
)
import json

class RatchetSession:
    SALT = b'Secret_Share_V1_Salt' # Đồng bộ lại Salt

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
            # Khởi tạo chuỗi rk và ck_s ban đầu
            self.rk, self.ck_s = self._kdf_root(self.SALT, secret)

    def _kdf_root(self, rk, dh_out):
        derived = HMAC.new(rk, dh_out, digestmod=SHA256).digest()
        return derived[:32], derived[32:]

    def _kdf_chain(self, ck):
        if ck is None:
            raise ValueError("Chưa thiết lập Chain Key!")
        # Đảm bảo dùng đúng định dạng bytes cho hmac
        new_ck = HMAC.new(ck, b'\x01', SHA256).digest()
        mk = HMAC.new(ck, b'\x02', SHA256).digest()
        return new_ck, mk

    def encrypt(self, pt: bytes) -> dict:
        self.ck_s, mk = self._kdf_chain(self.ck_s)
        header = {
            "dh_pub": self.dh_pair.get_public_key().to_string().hex(),
            "n": self.n_s
        }
        self.n_s += 1
        # Sử dụng separators để tránh sai lệch khoảng trắng khi Server xử lý JSON
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
        
        # Lưu trạng thái để Rollback nếu giải mã thất bại (tránh lệch chuỗi)
        old_state = (self.rk, self.ck_r, self.ck_s, self.dh_remote, self.dh_pair, self.n_r)
        
        try:
            # Bước bắt tay đầu tiên cho người nhận
            if self.ck_r is None:
                secret = compute_dh(self.dh_pair, remote_pub)
                self.rk, self.ck_r = self._kdf_root(self.SALT, secret)
                self.dh_remote = remote_pub
                # Chuẩn bị sẵn ck_s để phản hồi
                self.dh_pair = generate_dh_keypair()
                self.rk, self.ck_s = self._kdf_root(self.rk, compute_dh(self.dh_pair, self.dh_remote))
            
            # Xoay khóa DH nếu đối phương đổi cặp khóa mới
            elif remote_pub != self.dh_remote:
                self.rk, self.ck_r = self._kdf_root(self.rk, compute_dh(self.dh_pair, remote_pub))
                self.dh_remote = remote_pub
                self.dh_pair = generate_dh_keypair()
                self.rk, self.ck_s = self._kdf_root(self.rk, compute_dh(self.dh_pair, self.dh_remote))
                self.n_r = 0

            new_ck_r, mk = self._kdf_chain(self.ck_r)
            ad = json.dumps(header, sort_keys=True, separators=(',', ':')).encode()
            
            plaintext = decrypt_gcm(
                mk, 
                bytes.fromhex(packet['iv']), 
                bytes.fromhex(packet['ciphertext']), 
                bytes.fromhex(packet['tag']), 
                associated_data=ad
            )
            
            # Chỉ khi giải mã thành công mới cập nhật chuỗi khóa
            self.ck_r = new_ck_r
            self.n_r += 1
            return plaintext
            
        except Exception as e:
            # Khôi phục trạng thái cũ nếu lỗi MAC (tránh hỏng session vĩnh viễn)
            self.rk, self.ck_r, self.ck_s, self.dh_remote, self.dh_pair, self.n_r = old_state
            raise e

    def get_state(self):
        return {
            "rk": self.rk.hex(), 
            "dh_priv": self.dh_pair.private_key.to_string().hex(),
            "dh_remote": self.dh_remote.hex() if self.dh_remote else None,
            "ck_s": self.ck_s.hex() if self.ck_s else None, 
            "ck_r": self.ck_r.hex() if self.ck_r else None,
            "ns": self.n_s, "nr": self.n_r
        }