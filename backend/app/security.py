import hashlib
import secrets
from datetime import timedelta
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pwdlib import PasswordHash
from sqlalchemy.orm import Session
from .config import settings
from .db import get_db
from .models import User, Role, now

passwords = PasswordHash.recommended()
bearer = HTTPBearer(auto_error=False)


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def token(user):
    return jwt.encode({"sub": user.id, "ver": user.token_version, "exp": now() + timedelta(hours=8)}, settings.jwt_secret, algorithm="HS256")


def authenticate(value, db):
    try:
        claims = jwt.decode(value, settings.jwt_secret, algorithms=["HS256"])
        user = db.get(User, claims["sub"])
        if not user or not user.active or user.token_version != claims["ver"]:
            raise ValueError()
        return user
    except (jwt.InvalidTokenError, KeyError, ValueError):
        raise HTTPException(401, "Your session has expired. Please sign in again.")


def current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer), db: Session = Depends(get_db)):
    if not credentials:
        raise HTTPException(401, "Sign in to continue")
    return authenticate(credentials.credentials, db)


def require(permission):
    def dependency(user=Depends(current_user), db=Depends(get_db)):
        role = db.get(Role, user.role)
        if not role or not ("*" in role.permissions or permission in role.permissions):
            raise HTTPException(403, "Your role does not allow this action")
        return user
    return dependency
