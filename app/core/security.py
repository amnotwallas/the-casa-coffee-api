from fastapi import Header, HTTPException, Security
from fastapi.security import APIKeyHeader
from app.core.config import settings

api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)

def validate_api_key(x_api_key: str = Security(api_key_header)):
    """
    Validate that the request includes a valid API Key.
    """
    if x_api_key != settings.ADMIN_SECRET_TOKEN:
        raise HTTPException(
            status_code=403,
            detail="Access denied: Invalid API Key"
        )
    return x_api_key
