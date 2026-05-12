from fastapi import APIRouter, Depends, HTTPException
from app.schemas.user_schema import UserProfile, AddressBase
from app.services.user_service import UserService
from app.api.dependencies import get_user_service, get_current_user_required
from app.core.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/user", tags=["User"])

@router.get("/profile", response_model=UserProfile)
async def get_profile(
    user_service: UserService = Depends(get_user_service),
    current_user: dict = Depends(get_current_user_required)
):
    """Obtiene la información del perfil del usuario actual."""
    return user_service.get_profile(current_user["id"])

@router.patch("/profile", response_model=UserProfile)
async def update_profile(
    update_data: dict,
    user_service: UserService = Depends(get_user_service),
    current_user: dict = Depends(get_current_user_required)
):
    """Actualiza parcialmente el perfil del usuario."""
    return user_service.update_profile(current_user["id"], update_data)

@router.get("/addresses")
async def list_addresses(
    user_service: UserService = Depends(get_user_service),
    current_user: dict = Depends(get_current_user_required)
):
    profile = user_service.get_profile(current_user["id"])
    return profile.direcciones

@router.post("/addresses", status_code=201)
async def add_address(
    address_in: AddressBase,
    user_service: UserService = Depends(get_user_service),
    current_user: dict = Depends(get_current_user_required)
):
    return user_service.add_address(current_user["id"], address_in)

@router.delete("/addresses/{address_id}")
async def delete_address(
    address_id: str,
    user_service: UserService = Depends(get_user_service),
    current_user: dict = Depends(get_current_user_required)
):
    user_service.remove_address(current_user["id"], address_id)
    return {"message": "Dirección eliminada"}

@router.post("/favorites/{product_id}", status_code=201)
async def add_favorite(
    product_id: str,
    user_service: UserService = Depends(get_user_service),
    current_user: dict = Depends(get_current_user_required)
):
    user_service.add_to_favorites(current_user["id"], product_id)
    return {"message": "Agregado a favoritos"}

@router.delete("/favorites/{product_id}")
async def remove_favorite(
    product_id: str,
    user_service: UserService = Depends(get_user_service),
    current_user: dict = Depends(get_current_user_required)
):
    user_service.remove_from_favorites(current_user["id"], product_id)
    return {"message": "Eliminado de favoritos"}

@router.get("/favorites")
async def list_favorites(
    user_service: UserService = Depends(get_user_service),
    current_user: dict = Depends(get_current_user_required)
):
    return user_service.list_favorites(current_user["id"])
