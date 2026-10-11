from datetime import datetime, timedelta, timezone
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, InvalidHashError
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.config import settings
from app.database.connection import get_db
from app.models import User

password_hasher = PasswordHasher()
bearer = HTTPBearer(auto_error=False)

def hash_password(password: str) -> str:
    return password_hasher.hash(password)

def verify_password(password: str, encoded: str) -> bool:
    try: return password_hasher.verify(encoded, password)
    except (VerificationError, InvalidHashError): return False

def create_token(user: User) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode({'sub':str(user.user_id),'iat':now,'exp':now+timedelta(minutes=settings.jwt_expire_minutes),'iss':'caretrack'}, settings.jwt_secret, algorithm='HS256')

def current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer), db: Session = Depends(get_db)) -> User:
    if credentials is None: raise HTTPException(401, 'Please sign in to continue')
    try:
        claims = jwt.decode(credentials.credentials, settings.jwt_secret, algorithms=['HS256'], issuer='caretrack', options={'require':['exp','sub','iat','iss']})
        user_id = int(claims['sub'])
    except (jwt.PyJWTError, ValueError, TypeError): raise HTTPException(401, 'Your session has expired. Please sign in again')
    user = db.get(User, user_id)
    if not user or not user.is_active: raise HTTPException(401, 'This account is unavailable')
    db.execute(text('SET @caretrack_user_id = :id, @caretrack_system = NULL'), {'id':user.user_id})
    return user

def roles(user: User, *allowed: str):
    if user.role not in allowed: raise HTTPException(403, 'Your role cannot perform this action')
