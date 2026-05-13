from fastapi import APIRouter, Depends, HTTPException
from app.schemas.user_schema import FirebaseAuthRequest, AuthResponse
from app.services.user_service import AuthService
from app.api.dependencies import get_auth_service
from app.core.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/verify", response_model=AuthResponse)
async def verify_auth(
    auth_data: FirebaseAuthRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Punto de entrada único para autenticación.
    Verifica el token de Firebase y sincroniza el perfil en PostgreSQL.
    """
    return await auth_service.verify_and_sync_user(auth_data)

@router.post("/login", response_model=AuthResponse)
async def login_legacy(
    auth_data: FirebaseAuthRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Alias de /verify para compatibilidad con flujos de login."""
    return await auth_service.verify_and_sync_user(auth_data)

@router.post("/logout")
async def logout():
    """El cierre de sesión se gestiona principalmente en el cliente con Firebase."""
    return {"message": "Sesión cerrada (localmente)"}
