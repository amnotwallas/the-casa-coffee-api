from pydantic import BaseModel, Field, model_validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.core.config import settings

class TrackingStatus(BaseModel):
    preparando: bool = False
    listo: bool = False
    enCamino: bool = False
    entregado: bool = False

class OrderBase(BaseModel):
    id: str
    fecha: datetime
    items: List[Dict[str, Any]] = []
    total: float
    status: str
    tracking: TrackingStatus

    @model_validator(mode="before")
    @classmethod
    def map_items(cls, data: any):
        if hasattr(data, "items"):
            data_dict = data.__dict__.copy()
            data_dict["items"] = [
                {
                    "id": item.id,
                    "productId": item.product_id,
                    "nombre": item.nombre,
                    "imagen": f"{settings.BASE_URL}/api/v1/media/products/{item.imagen}" if item.imagen and not item.imagen.startswith("http") else item.imagen,
                    "cantidad": item.cantidad,
                    "precio": item.precio,
                    "personalizaciones": item.personalizaciones,
                    "subtotal": item.subtotal
                } for item in data.items
            ]
            return data_dict
        return data

class OrderCheckoutRequest(BaseModel):
    shippingMethodId: int
    addressId: Optional[str] = None
    tipoPago: str = Field(..., pattern="^(efectivo|tarjeta)$")
    notas: Optional[str] = None
    propina: float = 0.0

class ShippingMethodResponse(BaseModel):
    id: int
    nombre: str
    costo: float
    requiere_direccion: bool
    disponible: bool
    model_config = {"from_attributes": True}

class OrderResponse(BaseModel):
    orderId: str
    total: float
    estimatedTime: str
    status: str
    createdAt: datetime
