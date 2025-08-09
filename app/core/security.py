import hmac
import hashlib
import secrets
from typing import Optional

from fastapi import Security, HTTPException, Depends, Header, Request
from fastapi.security.api_key import APIKeyHeader
from starlette.status import HTTP_403_FORBIDDEN, HTTP_401_UNAUTHORIZED

from app.core.config import get_settings
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = "your-secret-key" 
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_api_key(
    api_key: str = Security(api_key_header),
) -> str:
    """Validate API key for protected endpoints"""
    settings = get_settings()
    
    if api_key is None:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="API Key header is missing",
        )
        
    if api_key != settings.API_KEY:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="Invalid API Key",
        )
        
    return api_key


async def verify_github_webhook(
    request: Request,
    x_hub_signature_256: str = Header(None),
) -> bool:
    """
    Verify GitHub webhook request using the X-Hub-Signature-256 header.
    GitHub uses HMAC hex digest of the payload with the webhook secret as the key.
    """
    settings = get_settings()
    payload = await request.body()
    
    if not x_hub_signature_256:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="X-Hub-Signature-256 header is missing",
        )
        
    if not x_hub_signature_256.startswith("sha256="):
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="Invalid signature format",
        )
        
    signature = x_hub_signature_256[7:]  # Remove "sha256=" prefix
    
    secret = settings.GITHUB_WEBHOOK_SECRET.encode('utf-8')
    expected_signature = hmac.new(
        key=secret,
        msg=payload,
        digestmod=hashlib.sha256
    ).hexdigest()
    
    if not secrets.compare_digest(signature, expected_signature):
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="Invalid signature",
        )
        
    return True