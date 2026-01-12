import json

def to_hex(data: bytes) -> str:
    return data.hex()

def from_hex(data: str) -> bytes:
    return bytes.fromhex(data)