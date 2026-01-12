from pydantic import BaseModel
from typing import Dict, Any

class RegisterRequest(BaseModel):
    username: str
    identity_public_key: str
    prekey_bundle: str 

class SendMessageRequest(BaseModel):
    to_user: str
    encrypted_content: str
    header: Dict[str, Any]