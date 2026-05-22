from fastapi import Header, Security, HTTPException
from fastapi.security import APIKeyHeader
from app.core.config import settings
from app.core.exceptions import ForbiddenException, UnauthorizedException
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from typing import Optional

api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)

def validate_api_key(x_api_key: str = Security(api_key_header)):
    """
    Validate that the request includes a valid API Key using domain exceptions.
    """
    if x_api_key != settings.ADMIN_SECRET_TOKEN:
        raise ForbiddenException(
            message="Access denied: Invalid API Key"
        )
    return x_api_key

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    Create a local JWT access token.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> dict:
    """
    Verify and decode a local JWT access token.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        raise UnauthorizedException(message="Could not validate credentials")
