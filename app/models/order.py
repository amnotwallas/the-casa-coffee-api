from sqlmodel import SQLModel, Field, Column, JSON, Relationship
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

class OrderItem(SQLModel, table=True):
    id: str = Field(default_factory=lambda: f"oit-{str(uuid.uuid4())[:8]}", primary_key=True)
    order_id: str = Field(foreign_key="order.id", index=True)
    product_id: str = Field(index=True)
    nombre: str
    imagen: Optional[str] = None
    cantidad: int
    precio: float
    personalizaciones: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    subtotal: float
    
    order: "Order" = Relationship(back_populates="items")

class ShippingMethod(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str
    costo: float = 0.0
    requiere_direccion: bool = False
    disponible: bool = True

class Order(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(index=True)
    fecha: datetime = Field(default_factory=datetime.utcnow, index=True)
    
    # Normalización de ítems
    items: List[OrderItem] = Relationship(back_populates="order", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    
    total: float
    tipo_pago: str = Field(default="efectivo")
    status: str = Field(default="pending", index=True)
    
    # Envío Relacional
    shipping_method_id: Optional[int] = Field(default=None, foreign_key="shippingmethod.id")
    costo_envio: float = 0.0
    address_id: Optional[str] = Field(default=None)

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
    imagen: Optional[str] = None
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
