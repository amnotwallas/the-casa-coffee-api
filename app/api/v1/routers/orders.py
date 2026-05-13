from fastapi import APIRouter, Depends, Header, HTTPException
from app.schemas.order_schema import OrderCheckoutRequest, OrderResponse
from app.services.order_service import OrderService
from app.api.dependencies import get_order_service, get_current_user_required

router = APIRouter(prefix="/orders", tags=["Orders"])

@router.post("/checkout", response_model=OrderResponse, status_code=201)
async def checkout(
    request: OrderCheckoutRequest,
    x_idempotency_key: str = Header(..., alias="X-Idempotency-Key"),
    order_service: OrderService = Depends(get_order_service),
    current_user: dict = Depends(get_current_user_required)
):
    """Finaliza la compra. REQUIERE LOGIN."""
    return await order_service.checkout(current_user["id"], request.addressId, x_idempotency_key)

@router.get("/")
async def list_orders(
    order_service: OrderService = Depends(get_order_service),
    current_user: dict = Depends(get_current_user_required)
):
    """Lista historial. REQUIERE LOGIN."""
    return await order_service.order_repo.list_orders_by_user(current_user["id"])

@router.get("/active")
async def list_active_orders(
    order_service: OrderService = Depends(get_order_service),
    current_user: dict = Depends(get_current_user_required)
):
    """Lista pedidos en curso. REQUIERE LOGIN."""
    all_orders = await order_service.order_repo.list_orders_by_user(current_user["id"])
    active_statuses = ["pending", "preparing", "ready", "on_the_way"]
    return [o for o in all_orders if o.status in active_statuses]

@router.get("/{order_id}")
async def get_order_detail(
    order_id: str,
    order_service: OrderService = Depends(get_order_service),
    current_user: dict = Depends(get_current_user_required)
):
    """Detalle de pedido específico. REQUIERE LOGIN."""
    order = await order_service.order_repo.find_order_by_id(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    return order

@router.get("/{order_id}/tracking")
async def get_order_tracking(
    order_id: str,
    order_service: OrderService = Depends(get_order_service),
    current_user: dict = Depends(get_current_user_required)
):
    """Seguimiento en tiempo real. REQUIERE LOGIN."""
    order = await order_service.order_repo.find_order_by_id(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    return order.tracking

@router.patch("/{order_id}/cancel")
async def cancel_order(
    order_id: str,
    order_service: OrderService = Depends(get_order_service),
    current_user: dict = Depends(get_current_user_required)
):
    """Cancela un pedido pendiente. REQUIERE LOGIN."""
    updated = await order_service.order_repo.update_order_status(order_id, "cancelled")
    if not updated:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    return {"message": "Pedido cancelado correctamente"}
