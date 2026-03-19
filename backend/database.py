# database.py
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from beanie import PydanticObjectId

from models import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(plain_password: str) -> str:
    return pwd_context.hash(plain_password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

SECRET_KEY  = os.getenv("SECRET_KEY", "your_secret_key_here")
ALGORITHM   = "HS256"
EXPIRE_MINS = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    payload = data.copy()
    expire  = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=EXPIRE_MINS))
    payload.update({"exp": expire})
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

# Chuyển sang HTTPBearer để hiện ô "Value" dán Token trong Swagger
security = HTTPBearer()

async def get_current_user(auth: HTTPAuthorizationCredentials = Depends(security)) -> User:
    token = auth.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    try:
        # Ép kiểu string ID sang PydanticObjectId để Beanie tìm được trong MongoDB
        user = await User.get(PydanticObjectId(user_id))
    except Exception:
        raise credentials_exception

    if user is None:
        raise credentials_exception

    return user
