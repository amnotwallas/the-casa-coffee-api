from typing import List, Optional
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.order import Order, CartDB
from app.core.logger import get_logger

logger = get_logger(__name__)

class OrderRepository:
    """
    Data access layer for Orders and persistent Shopping Cart management.
    """
    def __init__(self, session: AsyncSession):
        self.session = session

    # --- CART MANAGEMENT ---
    async def get_cart(self, user_id: str) -> dict:
        """
        Retrieve the current state of a user's shopping cart.
        """
        cart = await self.session.get(CartDB, user_id)
        if not cart:
            return {"items": [], "total": 0.0, "itemsCount": 0}
        return {"items": cart.items, "total": cart.total, "itemsCount": cart.itemsCount}

    async def save_cart(self, user_id: str, cart_data: dict):
        """
        Update or create a persistent shopping cart for a user.
        """
        cart = await self.session.get(CartDB, user_id)
        if not cart:
            cart = CartDB(user_id=user_id)
        
        cart.items = cart_data.get("items", [])
        cart.total = cart_data.get("total", 0.0)
        cart.itemsCount = cart_data.get("itemsCount", 0)
        
        self.session.add(cart)
        await self.session.commit()

    # --- ORDER MANAGEMENT ---
    async def create_order(self, order_data: dict) -> Order:
        """
        Persist a new order record in the database.
        """
        order = Order(**order_data)
        self.session.add(order)
        await self.session.commit()
        await self.session.refresh(order)
        return order

    async def list_orders_by_user(self, user_id: str) -> List[Order]:
        """
        Retrieve all orders associated with a specific user.
        """
        statement = select(Order).where(Order.user_id == user_id)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def find_order_by_id(self, order_id: str) -> Optional[Order]:
        """
        Locate an order by its unique identifier.
        """
        return await self.session.get(Order, order_id)

    async def update_order_status(self, order_id: str, status: str, tracking_updates: dict = None) -> Optional[Order]:
        """
        Update the progress and status of an existing order.
        """
        order = await self.find_order_by_id(order_id)
        if order:
            order.status = status
            if tracking_updates:
                # Merge tracking updates into the existing JSON field
                new_tracking = dict(order.tracking)
                new_tracking.update(tracking_updates)
                order.tracking = new_tracking
            self.session.add(order)
            await self.session.commit()
            await self.session.refresh(order)
            return order
        return None
