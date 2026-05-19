from sqlmodel import SQLModel, Field, Column, JSON, Relationship
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

class OrderItem(SQLModel, table=True):
    id: str = Field(default_factory=lambda: f"oit-{str(uuid.uuid4())[:8]}", primary_key=True)
    order_id: str = Field(foreign_key="order.id", index=True)
    product_id: str = Field(index=True)
    nombre: str
    cantidad: int
    precio: float
    personalizaciones: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    subtotal: float
    
    order: "Order" = Relationship(back_populates="items")

class Order(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(index=True)
    fecha: datetime = Field(default_factory=datetime.utcnow)
    
    # Normalización de ítems
    items: List[OrderItem] = Relationship(back_populates="order", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    
    total: float
    status: str = "pending"
    tracking: Dict[str, bool] = Field(
        default={
            "preparando": True,
            "listo": False,
            "enCamino": False,
            "entregado": False
        },
        sa_column=Column(JSON)
    )

class CartItem(SQLModel, table=True):
    id: str = Field(default_factory=lambda: f"cit-{str(uuid.uuid4())[:8]}", primary_key=True)
    cart_id: str = Field(foreign_key="cartdb.user_id", index=True)
    product_id: str = Field(index=True)
    nombre: str
    cantidad: int
    precio: float
    personalizaciones: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    subtotal: float
    
    cart: "CartDB" = Relationship(back_populates="items")

class CartDB(SQLModel, table=True):
    user_id: str = Field(primary_key=True)
    
    # Normalización de ítems
    items: List[CartItem] = Relationship(back_populates="cart", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    
    total: float = 0.0
    itemsCount: int = 0
