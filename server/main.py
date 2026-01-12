from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from .models import RegisterRequest, SendMessageRequest
from .database import init_db, add_user, get_user, save_msg, fetch_msgs
from lib.crypto import verify_signature

app = FastAPI()

@app.on_event("startup")
def startup():
    init_db()

@app.middleware("http")
async def verify_request(request: Request, call_next):
    # Các API không cần bảo mật
    if request.url.path in ["/register", "/get_prekey", "/docs", "/openapi.json"]:
        return await call_next(request)
    
    user_id = request.headers.get("X-User-ID")
    sig = request.headers.get("X-Signature")
    ts = request.headers.get("X-Timestamp")
    
    # 1. Kiểm tra thiếu Header
    if not user_id or not sig:
        return JSONResponse(status_code=401, content={"detail": "Missing Security Headers"})
    
    # 2. Kiểm tra User có tồn tại không
    user_row = get_user(user_id)
    if not user_row:
        return JSONResponse(status_code=404, content={"detail": "User not found"})
    
    # 3. Kiểm tra Chữ ký (Signature)
    body = await request.body()
    data = f"{request.method}{request.url.path}{ts}".encode() + body
    
    if verify_signature(user_row[0], data, sig):
        return await call_next(request)
    else:
        return JSONResponse(status_code=401, content={"detail": "Invalid Signature"})

# --- CÁC API DƯỚI ĐÂY GIỮ NGUYÊN ---
@app.post("/register")
def register(req: RegisterRequest):
    if add_user(req.username, req.identity_public_key, req.prekey_bundle):
        return {"status": "ok"}
    return JSONResponse(status_code=400, content={"detail": "User exists"})

@app.get("/get_prekey")
def get_prekey(username: str):
    row = get_user(username)
    if row: return {"id_key": row[0], "pre_key": row[1]}
    return JSONResponse(status_code=404, content={"detail": "User not found"})

@app.post("/send")
def send(req: SendMessageRequest, request: Request):
    sender = request.headers.get("X-User-ID")
    save_msg(sender, req.to_user, req.encrypted_content, req.header)
    return {"status": "sent"}

@app.get("/fetch")
def fetch(request: Request):
    user = request.headers.get("X-User-ID")
    return {"messages": fetch_msgs(user)}