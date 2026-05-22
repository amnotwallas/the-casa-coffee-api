from fastapi import APIRouter, Depends, Header, HTTPException
from app.schemas.cart_schema import Cart, AddToCartRequest, UpdateCartItemRequest
from app.services.order_service import CartService
from app.api.dependencies import get_cart_service, get_current_user_optional

router = APIRouter(prefix="/cart", tags=["Cart"])

@router.get("/", response_model=Cart)
async def get_cart(
    cart_service: CartService = Depends(get_cart_service),
    current_user: dict = Depends(get_current_user_optional)
):
    """Obtiene el carrito. Si no hay login, devuelve carrito vacío."""
    if not current_user:
        return {"items": [], "total": 0.0, "itemsCount": 0}
    return await cart_service.get_user_cart(current_user["id"])

@router.post("/add", response_model=Cart)
async def add_item(
    request: AddToCartRequest,
    cart_service: CartService = Depends(get_cart_service),
    current_user: dict = Depends(get_current_user_optional)
):
    """Añade un producto al carrito en la nube."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Inicia sesión para sincronizar tu carrito.")
    return await cart_service.add_to_cart(current_user["id"], request)

@router.patch("/item/{item_id}", response_model=Cart)
async def update_item(
    item_id: str,
    request: UpdateCartItemRequest,
    cart_service: CartService = Depends(get_cart_service),
    current_user: dict = Depends(get_current_user_optional)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Inicia sesión para actualizar tu carrito.")
    return await cart_service.update_item(current_user["id"], item_id, request)

@router.delete("/item/{item_id}", response_model=Cart)
async def remove_item(
    item_id: str,
    cart_service: CartService = Depends(get_cart_service),
    current_user: dict = Depends(get_current_user_optional)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Inicia sesión para gestionar tu carrito.")
    return await cart_service.remove_item(current_user["id"], item_id)

@router.post("/apply-coupon")
async def apply_coupon(
    code: str,
    cart_service: CartService = Depends(get_cart_service),
    current_user: dict = Depends(get_current_user_optional)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Inicia sesión para aplicar cupones.")
    return await cart_service.apply_coupon(current_user["id"], code)

@router.delete("/clear")
async def clear_cart(
    cart_service: CartService = Depends(get_cart_service),
    current_user: dict = Depends(get_current_user_optional)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Inicia sesión para vaciar tu carrito.")
    await cart_service.clear_cart(current_user["id"])
    return {"message": "Carrito vaciado correctamente"}
