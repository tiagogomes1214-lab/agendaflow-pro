import base64
import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from .database import get_db
from .models import Admin

bearer = HTTPBearer(auto_error=False)
ITERATIONS = 600_000


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, ITERATIONS)
    return f"pbkdf2_sha256${ITERATIONS}${base64.b64encode(salt).decode()}${base64.b64encode(digest).decode()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algorithm, iterations, salt, digest = stored.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        expected = base64.b64decode(digest)
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), base64.b64decode(salt), int(iterations))
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def secret_key() -> str:
    secret = os.getenv("JWT_SECRET", "")
    if len(secret) < 32 or "CHANGE_ME" in secret:
        raise RuntimeError("Configure JWT_SECRET seguro no .env antes de iniciar.")
    return secret


def create_token(admin_id: int) -> str:
    payload = {"sub": str(admin_id), "iat": datetime.now(timezone.utc), "exp": datetime.now(timezone.utc) + timedelta(hours=8)}
    return jwt.encode(payload, secret_key(), algorithm="HS256")


def require_admin(credentials: HTTPAuthorizationCredentials | None = Depends(bearer), db: Session = Depends(get_db)) -> Admin:
    if not credentials:
        raise HTTPException(status_code=401, detail="Faça login para continuar")
    try:
        payload = jwt.decode(credentials.credentials, secret_key(), algorithms=["HS256"])
        admin_id = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise HTTPException(status_code=401, detail="Sessão inválida ou expirada") from None
    admin = db.get(Admin, admin_id)
    if not admin:
        raise HTTPException(status_code=401, detail="Conta não encontrada")
    return admin
