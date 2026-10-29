from fastapi import Request, HTTPException, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from itsdangerous import URLSafeSerializer
import os
import hashlib
import secrets

from .database import get_db, User

SECRET_KEY = os.environ.get("SECRET_KEY", "nds-secret-key-change-me-2025")
serializer = URLSafeSerializer(SECRET_KEY)


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100000)
    return salt + ":" + h.hex()


def verify_password(plain: str, hashed: str) -> bool:
    try:
        salt, hash_hex = hashed.split(":")
        h = hashlib.pbkdf2_hmac("sha256", plain.encode(), salt.encode(), 100000)
        return h.hex() == hash_hex
    except Exception:
        return False


def create_session_token(user_id: int, role: str) -> str:
    return serializer.dumps({"user_id": user_id, "role": role})


def read_session_token(token: str):
    try:
        return serializer.loads(token)
    except Exception:
        return None


def get_current_user(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("nds_session")
    if not token:
        return None
    data = read_session_token(token)
    if not data:
        return None
    user = db.query(User).filter(User.id == data["user_id"], User.is_active == True).first()
    return user


def require_login(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=303, headers={"Location": "/login"})
    return user


def require_staff(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role not in ("admin", "staff"):
        raise HTTPException(status_code=303, headers={"Location": "/login"})
    return user


def require_admin(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="غير مصرح")
    return user
