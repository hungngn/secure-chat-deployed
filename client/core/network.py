import requests
import json
import time
from lib.crypto import sign_data

# THAY ĐỔI: Dán URL từ Render của bạn vào đây (nhớ giữ https và không có dấu / ở cuối)
BASE_URL = "https://secure-chat-deployed.onrender.com"

class NetworkClient:
    def __init__(self):
        self.username = None
        self.sk_hex = None

    def set_identity(self, u, sk):
        self.username = u
        self.sk_hex = sk

    def _headers(self, method, path, body=b""):
        h = {"Content-Type": "application/json"}
        if self.username and self.sk_hex:
            ts = str(time.time())
            data = f"{method}{path}{ts}".encode() + body
            sig = sign_data(self.sk_hex, data)
            h.update({
                "X-User-ID": self.username, 
                "X-Timestamp": ts, 
                "X-Signature": sig
            })
        return h

    def post(self, ep, data):
        url = BASE_URL + ep
        body = json.dumps(data).encode()
        try:
            res = requests.post(url, data=body, headers=self._headers("POST", ep, body))
            return res.json()
        except Exception as e:
            print(f"Network Error POST: {e}")
            return None

    def get(self, ep, params=None):
        url = BASE_URL + ep
        try:
            res = requests.get(url, params=params, headers=self._headers("GET", ep))
            return res.json()
        except Exception as e:
            print(f"Network Error GET: {e}")
            return None