from fastapi import APIRouter, Depends, Header, HTTPException
from typing import List, Optional
from app.schemas.admin_schema import AdminAnalytics, UpdateOrderStatusRequest
from app.schemas.product_schema import Product, ProductCreate
from app.services.admin_service import AdminService
from app.api.dependencies import get_admin_service, get_current_user_required
from app.core.config import settings

router = APIRouter(prefix="/admin", tags=["Admin"])

async def verify_admin_access(
    current_user: dict = Depends(get_current_user_required)
):
    """Verifica estrictamente si el usuario tiene rol de administrador en la BD."""
    if current_user.get("is_admin"):
        return current_user
        
    raise HTTPException(
        status_code=403, 
        detail="Acceso denegado: Se requieren permisos de administrador"
    )

@router.get("/analytics", response_model=AdminAnalytics, dependencies=[Depends(verify_admin_access)])
async def get_analytics(admin_service: AdminService = Depends(get_admin_service)):
    """Obtiene analíticas detalladas para el dashboard de administración."""
    return await admin_service.get_analytics()

@router.post("/products", status_code=201, dependencies=[Depends(verify_admin_access)])
async def create_product(product_in: ProductCreate, admin_service: AdminService = Depends(get_admin_service)):
    """Crea un nuevo producto en el catálogo usando category_id."""
    return await admin_service.create_product(product_in)

@router.patch("/products/{product_id}", dependencies=[Depends(verify_admin_access)])
async def update_product(product_id: str, update_data: dict, admin_service: AdminService = Depends(get_admin_service)):
    """Actualiza parcialmente un producto."""
    return await admin_service.update_product(product_id, update_data)

@router.delete("/products/{product_id}", dependencies=[Depends(verify_admin_access)])
async def delete_product(product_id: str, admin_service: AdminService = Depends(get_admin_service)):
    """Elimina o desactiva un producto."""
    await admin_service.delete_product(product_id)
    return {"message": "Producto eliminado"}

@router.get("/orders", dependencies=[Depends(verify_admin_access)])
async def list_all_orders(admin_service: AdminService = Depends(get_admin_service)):
    """Lista todos los pedidos registrados en el sistema."""
    return await admin_service.list_all_orders()

@router.patch("/orders/{order_id}/status", dependencies=[Depends(verify_admin_access)])
async def update_order_status(
    order_id: str,
    request: UpdateOrderStatusRequest,
    admin_service: AdminService = Depends(get_admin_service)
):
    """Actualiza el estado de un pedido (ej: de 'preparing' a 'ready')."""
    return await admin_service.update_order_status(order_id, request.status)
