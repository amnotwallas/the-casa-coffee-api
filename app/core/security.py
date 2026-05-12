from fastapi import Header, HTTPException, Security
from fastapi.security import APIKeyHeader
from app.core.config import settings

api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)

def validate_api_key(x_api_key: str = Security(api_key_header)):
    """
    Valida que la petición incluya una API KEY válida.
    Útil para proteger recursos internos o limitar el consumo de ancho de banda.
    """
    if x_api_key != settings.ADMIN_SECRET_TOKEN:
        raise HTTPException(
            status_code=403,
            detail="Acceso denegado: API Key inválida"
        )
    return x_api_key
