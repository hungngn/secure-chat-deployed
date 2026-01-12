import requests
import json
import time
from lib.crypto import sign_data

BASE_URL = "http://127.0.0.1:8000"

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
            h.update({"X-User-ID": self.username, "X-Timestamp": ts, "X-Signature": sig})
        return h

    def post(self, ep, data):
        url = BASE_URL + ep
        body = json.dumps(data).encode()
        try:
            return requests.post(url, data=body, headers=self._headers("POST", ep, body)).json()
        except: return None

    def get(self, ep, params=None):
        url = BASE_URL + ep
        try:
            return requests.get(url, params=params, headers=self._headers("GET", ep)).json()
        except: return None