import os
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Hash import SHA256, HMAC
from Crypto.Random import get_random_bytes
from ecdsa import SigningKey, VerifyingKey, SECP256k1, ECDH

# --- PROJECT 1: AES & KDF ---
def derive_master_key(password: str, salt: bytes = b'static_salt_MVP') -> bytes:
    return PBKDF2(password, salt, dkLen=32, count=100000, hmac_hash_module=SHA256)

def encrypt_gcm(key: bytes, plaintext: bytes, associated_data: bytes = b"") -> tuple[bytes, bytes, bytes]:
    iv = get_random_bytes(16)
    cipher = AES.new(key, AES.MODE_GCM, nonce=iv)
    cipher.update(associated_data)
    ciphertext, tag = cipher.encrypt_and_digest(plaintext)
    # TRẢ VỀ BYTES (Không gọi .hex() ở đây)
    return iv, ciphertext, tag

def decrypt_gcm(key: bytes, iv: bytes, ciphertext: bytes, tag: bytes, associated_data: bytes = b"") -> bytes:
    cipher = AES.new(key, AES.MODE_GCM, nonce=iv)
    cipher.update(associated_data)
    return cipher.decrypt_and_verify(ciphertext, tag)

# --- PROJECT 2: ECDSA ---
def generate_identity_keys():
    sk = SigningKey.generate(curve=SECP256k1)
    return sk, sk.verifying_key

def sign_data(private_key_hex: str, data: bytes) -> str:
    sk = SigningKey.from_string(bytes.fromhex(private_key_hex), curve=SECP256k1)
    return sk.sign(data).hex()

def verify_signature(public_key_hex: str, data: bytes, signature_hex: str) -> bool:
    try:
        vk = VerifyingKey.from_string(bytes.fromhex(public_key_hex), curve=SECP256k1)
        return vk.verify(bytes.fromhex(signature_hex), data)
    except:
        return False

# --- DOUBLE RATCHET PRIMITIVES ---
def generate_dh_keypair():
    ecdh = ECDH(curve=SECP256k1)
    ecdh.generate_private_key()
    return ecdh

def compute_dh(my_ecdh, peer_pub_bytes: bytes) -> bytes:
    my_ecdh.load_received_public_key_bytes(peer_pub_bytes)
    return my_ecdh.generate_sharedsecret_bytes()

def load_dh_keypair(priv_hex: str):
    sk = SigningKey.from_string(bytes.fromhex(priv_hex), curve=SECP256k1)
    ecdh = ECDH(curve=SECP256k1)
    ecdh.private_key = sk
    return ecdh