import requests
import json
import time
from lib.crypto import sign_data

# URL Render của bạn
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
            try:
                sig = sign_data(self.sk_hex, data)
                h.update({"X-User-ID": self.username, "X-Timestamp": ts, "X-Signature": sig})
            except: pass
        return h

    def post(self, ep, data):
        url = BASE_URL + ep
        body = json.dumps(data).encode()
        try:
            # Timeout 30s để chờ Render thức dậy
            res = requests.post(url, data=body, headers=self._headers("POST", ep, body), timeout=30)
            return res.json() if res.status_code == 200 else None
        except: return None

    def get(self, ep, params=None):
        url = BASE_URL + ep
        try:
            # Timeout 10s cho polling
            res = requests.get(url, params=params, headers=self._headers("GET", ep), timeout=10)
            return res.json() if res.status_code == 200 else None
        except: return None