from fastapi import Header, Security
from fastapi.security import APIKeyHeader
from app.core.config import settings
from app.core.exceptions import ForbiddenException

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
