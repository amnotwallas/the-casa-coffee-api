import uuid
from typing import List, Optional
from app.repositories.order_repo import OrderRepository
from app.repositories.product_repo import ProductRepository
from app.schemas.cart_schema import Cart, CartItem, AddToCartRequest, UpdateCartItemRequest
from app.core.logger import get_logger
from fastapi import HTTPException

logger = get_logger(__name__)

class CartService:
    """
    Service layer for shopping cart orchestration and calculations.
    """
    def __init__(self, order_repo: OrderRepository, product_repo: ProductRepository):
        self.order_repo = order_repo
        self.product_repo = product_repo

    async def get_user_cart(self, user_id: str) -> Cart:
        """
        Get the current user cart formatted as a schema.
        """
        cart_data = await self.order_repo.get_cart(user_id)
        return Cart(**cart_data)

    async def add_to_cart(self, user_id: str, request: AddToCartRequest) -> Cart:
        """
        Add a product to the cart and recalculate totals.
        """
        product = await self.product_repo.find_product_by_id(request.productId)
        if not product:
            logger.warning(f"Attempted to add non-existent product: {request.productId}")
            raise HTTPException(status_code=404, detail="Product not found")

        cart = await self.get_user_cart(user_id)
        
        new_item = CartItem(
            cartItemId=f"citem-{str(uuid.uuid4())[:8]}",
            productId=product.id,
            nombre=product.nombre,
            cantidad=request.cantidad,
            personalizaciones=request.personalizaciones,
            subtotal=product.precio * request.cantidad
        )
        
        cart.items.append(new_item)
        self._recalculate_cart(cart)
        
        await self.order_repo.save_cart(user_id, cart.model_dump())
        logger.info(f"Product {product.nombre} added to cart for user {user_id}")
        return cart

    async def remove_item(self, user_id: str, cart_item_id: str) -> Cart:
        """
        Remove a specific item from the cart.
        """
        cart = await self.get_user_cart(user_id)
        cart.items = [item for item in cart.items if item.cartItemId != cart_item_id]
        
        self._recalculate_cart(cart)
        await self.order_repo.save_cart(user_id, cart.model_dump())
        return cart

    async def update_item(self, user_id: str, cart_item_id: str, request: UpdateCartItemRequest) -> Cart:
        """
        Modify the quantity or customizations of a cart item.
        """
        cart = await self.get_user_cart(user_id)
        item = next((i for i in cart.items if i.cartItemId == cart_item_id), None)
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        
        if request.cantidad is not None:
            current_qty = item.cantidad if item.cantidad > 0 else 1
            unit_price = item.subtotal / current_qty
            item.cantidad = request.cantidad
            item.subtotal = unit_price * request.cantidad
        
        if request.personalizaciones is not None:
            item.personalizaciones.update(request.personalizaciones)
            
        self._recalculate_cart(cart)
        await self.order_repo.save_cart(user_id, cart.model_dump())
        return cart

    async def apply_coupon(self, user_id: str, code: str) -> dict:
        """
        Validate and apply a discount coupon to the cart.
        """
        if code.upper() == "COFFEE10":
            cart = await self.get_user_cart(user_id)
            discount = cart.total * 0.10
            return {
                "discount": discount,
                "newTotal": cart.total - discount,
                "couponApplied": code.upper()
            }
        raise HTTPException(status_code=404, detail="Invalid coupon code")

    async def clear_cart(self, user_id: str):
        """
        Empty all items from the user's cart.
        """
        await self.order_repo.save_cart(user_id, {"items": [], "total": 0.0, "itemsCount": 0})

    def _recalculate_cart(self, cart: Cart):
        """
        Perform server-side calculations for totals and item counts.
        """
        cart.total = sum(item.subtotal for item in cart.items)
        cart.itemsCount = sum(item.cantidad for item in cart.items)

class OrderService:
    """
    Service layer for processing orders and managing the checkout flow.
    """
    def __init__(self, order_repo: OrderRepository, cart_service: CartService):
        self.order_repo = order_repo
        self.cart_service = cart_service

    async def checkout(self, user_id: str, address_id: str, idempotency_key: str) -> dict:
        """
        Convert cart items into a finalized order.
        """
        logger.info(f"Processing checkout for user {user_id}. Key: {idempotency_key}")
        
        cart = await self.cart_service.get_user_cart(user_id)
        if not cart.items:
            raise HTTPException(status_code=400, detail="Cart is empty.")

        new_order_data = {
            "user_id": user_id,
            "items": [item.model_dump() for item in cart.items],
            "total": cart.total
        }

        order = await self.order_repo.create_order(new_order_data)
        await self.cart_service.clear_cart(user_id)
        
        return {
            "orderId": order.id,
            "total": order.total,
            "estimatedTime": "20-30 min",
            "status": order.status,
            "createdAt": order.fecha
        }
