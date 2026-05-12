from typing import List, Optional
from sqlmodel import Session, select
from app.models.order import Order, CartDB
from app.core.logger import get_logger

logger = get_logger(__name__)

class OrderRepository:
    def __init__(self, session: Session):
        self.session = session

    # --- CARRITO ---
    def get_cart(self, user_id: str) -> dict:
        cart = self.session.get(CartDB, user_id)
        if not cart:
            return {"items": [], "total": 0.0, "itemsCount": 0}
        return {"items": cart.items, "total": cart.total, "itemsCount": cart.itemsCount}

    def save_cart(self, user_id: str, cart_data: dict):
        cart = self.session.get(CartDB, user_id)
        if not cart:
            cart = CartDB(user_id=user_id)
        
        cart.items = cart_data.get("items", [])
        cart.total = cart_data.get("total", 0.0)
        cart.itemsCount = cart_data.get("itemsCount", 0)
        
        self.session.add(cart)
        self.session.commit()

    # --- PEDIDOS ---
    def create_order(self, order_data: dict) -> Order:
        order = Order(**order_data)
        self.session.add(order)
        self.session.commit()
        self.session.refresh(order)
        return order

    def list_orders_by_user(self, user_id: str) -> List[Order]:
        statement = select(Order).where(Order.user_id == user_id)
        return self.session.exec(statement).all()

    def find_order_by_id(self, order_id: str) -> Optional[Order]:
        return self.session.get(Order, order_id)

    def update_order_status(self, order_id: str, status: str, tracking_updates: dict = None) -> Optional[Order]:
        order = self.find_order_by_id(order_id)
        if order:
            order.status = status
            if tracking_updates:
                new_tracking = dict(order.tracking)
                new_tracking.update(tracking_updates)
                order.tracking = new_tracking
            self.session.add(order)
            self.session.commit()
            self.session.refresh(order)
            return order
        return None
