from fastapi import APIRouter, Depends, Header, HTTPException
from typing import List
from app.schemas.admin_schema import AdminAnalytics, UpdateOrderStatusRequest
from app.schemas.product_schema import Product
from app.services.support_service import AdminService
from app.api.dependencies import get_admin_service
from app.core.config import settings

router = APIRouter(prefix="/admin", tags=["Admin"])

def verify_admin_token(x_admin_token: str = Header(..., alias="X-Admin-Token")):
    if x_admin_token != settings.ADMIN_SECRET_TOKEN:
        raise HTTPException(status_code=403, detail="No tienes permisos de administrador")
    return x_admin_token

@router.get("/analytics", response_model=AdminAnalytics, dependencies=[Depends(verify_admin_token)])
async def get_analytics(admin_service: AdminService = Depends(get_admin_service)):
    """Obtiene analíticas detalladas para el dashboard de administración."""
    return admin_service.get_analytics()

@router.post("/products", status_code=201, dependencies=[Depends(verify_admin_token)])
async def create_product(product_in: Product, admin_service: AdminService = Depends(get_admin_service)):
    """Crea un nuevo producto en el catálogo."""
    return admin_service.create_product(product_in)

@router.patch("/products/{product_id}", dependencies=[Depends(verify_admin_token)])
async def update_product(product_id: str, update_data: dict, admin_service: AdminService = Depends(get_admin_service)):
    """Actualiza parcialmente un producto."""
    return admin_service.update_product(product_id, update_data)

@router.delete("/products/{product_id}", dependencies=[Depends(verify_admin_token)])
async def delete_product(product_id: str, admin_service: AdminService = Depends(get_admin_service)):
    """Elimina o desactiva un producto."""
    admin_service.delete_product(product_id)
    return {"message": "Producto eliminado"}

@router.get("/orders", dependencies=[Depends(verify_admin_token)])
async def list_all_orders(admin_service: AdminService = Depends(get_admin_service)):
    """Lista todos los pedidos registrados en el sistema."""
    return admin_service.list_all_orders()

@router.patch("/orders/{order_id}/status", dependencies=[Depends(verify_admin_token)])
async def update_order_status(
    order_id: str,
    request: UpdateOrderStatusRequest,
    admin_service: AdminService = Depends(get_admin_service)
):
    """Actualiza el estado de un pedido (ej: de 'preparing' a 'ready')."""
    return admin_service.update_order_status(order_id, request.status)
