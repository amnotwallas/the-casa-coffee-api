import uuid
from typing import List, Optional
from app.core.exceptions import EntityNotFoundException, BusinessLogicException, ResourceGoneException, ForbiddenException
from app.repositories.order_repo import OrderRepository
from app.repositories.product_repo import ProductRepository
from app.repositories.user_repo import UserRepository
from app.repositories.admin_repo import AdminRepository
from app.schemas.cart_schema import Cart, CartItem, AddToCartRequest, UpdateCartItemRequest
from app.core.logger import get_logger

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
        cart_db = await self.order_repo.get_cart(user_id)
        return Cart.model_validate(cart_db)

    async def add_to_cart(self, user_id: str, request: AddToCartRequest) -> Cart:
        """
        Add a product to the cart using an atomic DB operation.
        """
        product = await self.product_repo.find_product_by_id(request.productId)
        if not product:
            logger.warning(f"Attempted to add non-existent product: {request.productId}")
            raise EntityNotFoundException(message="Product not found")

        # 1. Añadir item individualmente
        item_data = {
            "id": f"citem-{str(uuid.uuid4())[:8]}",
            "product_id": product.id,
            "nombre": product.nombre,
            "imagen": product.imagenes[0] if product.imagenes else None,
            "cantidad": request.cantidad,
            "precio": product.precio,
            "personalizaciones": request.personalizaciones,
            "subtotal": product.precio * request.cantidad
        }
        await self.order_repo.add_item_to_cart(user_id, item_data)
        
        # 2. Recalcular y devolver carrito completo
        return await self._refresh_and_get_cart(user_id)

    async def remove_item(self, user_id: str, cart_item_id: str) -> Cart:
        """
        Remove a specific item from the cart atomically.
        """
        if not await self.order_repo.remove_item_from_cart(user_id, cart_item_id):
            raise EntityNotFoundException(message="Item not found in your cart")
            
        return await self._refresh_and_get_cart(user_id)

    async def update_item(self, user_id: str, cart_item_id: str, request: UpdateCartItemRequest) -> Cart:
        """
        Modify a cart item atomically and refresh totals.
        """
        updates = {}
        if request.cantidad is not None:
            updates["cantidad"] = request.cantidad
        if request.personalizaciones is not None:
            updates["personalizaciones"] = request.personalizaciones

        # Si hay cambio de cantidad, necesitamos el precio unitario real para el subtotal
        item = await self.order_repo.update_cart_item(user_id, cart_item_id, updates)
        if not item:
            raise EntityNotFoundException(message="Item not found")

        # Recalcular subtotal del item si cambió cantidad
        if request.cantidad is not None:
            await self.order_repo.update_cart_item(user_id, cart_item_id, {
                "subtotal": item.precio * request.cantidad
            })
            
        return await self._refresh_and_get_cart(user_id)

    async def _refresh_and_get_cart(self, user_id: str) -> Cart:
        """
        Helper to recalculate totals in DB and return the current Cart schema.
        """
        cart_db = await self.order_repo.get_cart(user_id)
        
        total = sum(item.subtotal for item in cart_db.items)
        count = sum(item.cantidad for item in cart_db.items)
        
        await self.order_repo.update_cart_totals(user_id, total, count)
        
        # Recargar para devolver data fresca
        cart_db = await self.order_repo.get_cart(user_id)
        return Cart.model_validate(cart_db)

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
        raise BusinessLogicException(message="Invalid coupon code")

    async def clear_cart(self, user_id: str):
        """
        Empty all items from the user's cart atomically.
        """
        await self.order_repo.clear_cart(user_id)

    def _recalculate_cart(self, cart: Cart):
        """
        Perform server-side calculations for totals and item counts.
        (Deprecated in favor of DB-driven refresh)
        """
        pass

class OrderService:
    """
    Service layer for processing orders and managing the checkout flow.
    """
    def __init__(self, order_repo: OrderRepository, cart_service: CartService, user_repo: UserRepository, product_repo: ProductRepository, admin_repo: AdminRepository):
        self.order_repo = order_repo
        self.cart_service = cart_service
        self.user_repo = user_repo
        self.product_repo = product_repo
        self.admin_repo = admin_repo

    async def list_shipping_methods(self) -> List[any]:
        """List all available shipping methods."""
        return await self.order_repo.get_shipping_methods()

    async def checkout(self, user_id: str, request: any, idempotency_key: str) -> dict:
        """
        Convert cart items into a finalized order with real-time validation.
        """
        logger.info(f"Processing checkout for user {user_id}. Key: {idempotency_key}")
        
        # 1. Recuperar carrito actual
        cart = await self.cart_service.get_user_cart(user_id)
        if not cart.items:
            raise BusinessLogicException(message="Cart is empty.")

        # 2. Validar Método de Envío
        shipping_method = await self.order_repo.get_shipping_method(request.shippingMethodId)
        if not shipping_method or not shipping_method.disponible:
            raise EntityNotFoundException(message="Método de envío no válido o no disponible.")

        # 3. Validar Dirección si es requerida
        if shipping_method.requiere_direccion:
            if not request.addressId:
                raise BusinessLogicException(message="Este método de envío requiere una dirección.")
            
            user = await self.user_repo.find_by_id(user_id)
            if not any(addr.id == request.addressId for addr in user.direcciones):
                raise ForbiddenException(message="La dirección seleccionada no pertenece a tu cuenta.")

        # 4. Validar precios y disponibilidad
        product_ids = [item.productId for item in cart.items]
        products_db = await self.product_repo.find_products_by_ids(product_ids)
        product_map = {p.id: p for p in products_db}

        verified_items = []
        verified_total = 0.0
        
        for item in cart.items:
            product = product_map.get(item.productId)
            if not product or not product.disponible:
                raise ResourceGoneException(
                    message=f"El producto '{item.nombre}' ya no está disponible."
                )
            
            verified_subtotal = product.precio * item.cantidad
            verified_items.append({
                "productId": product.id,
                "nombre": product.nombre,
                "imagen": product.imagenes[0] if product.imagenes else None,
                "cantidad": item.cantidad,
                "precio": product.precio,
                "personalizaciones": item.personalizaciones,
                "subtotal": verified_subtotal
            })
            verified_total += verified_subtotal

        # 5. Calcular Total Final con Envío
        final_total = verified_total + shipping_method.costo

        # 6. Crear la orden
        new_order_data = {
            "user_id": user_id,
            "items": verified_items,
            "total": final_total,
            "tipo_pago": request.tipoPago,
            "shipping_method_id": shipping_method.id,
            "costo_envio": shipping_method.costo,
            "address_id": request.addressId if shipping_method.requiere_direccion else None
        }

        order = await self.order_repo.create_order(new_order_data)
        
        # 7. Generar notificación admin
        try:
            user_full = await self.user_repo.find_by_id(user_id)
            customer_name = user_full.nombre if user_full else "Cliente"
            await self.admin_repo.create_notification(
                type="order",
                title="Nuevo pedido recibido",
                body=f"El cliente {customer_name} ha realizado un pedido por ${order.total:.2f} ({shipping_method.nombre})"
            )
        except Exception as e:
            logger.error(f"Error al crear notificación de pedido: {e}")

        # 8. Limpiar carrito
        await self.cart_service.clear_cart(user_id)
        
        return {
            "orderId": order.id,
            "total": order.total,
            "estimatedTime": "20-30 min",
            "status": order.status,
            "createdAt": order.fecha
        }
