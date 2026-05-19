from pydantic import BaseModel, Field, model_validator
from typing import List, Optional, Dict, Any
from datetime import datetime

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
                    "cantidad": item.cantidad,
                    "precio": item.precio,
                    "personalizaciones": item.personalizaciones,
                    "subtotal": item.subtotal
                } for item in data.items
            ]
            return data_dict
        return data

class OrderCheckoutRequest(BaseModel):
    addressId: str
    tipoPago: str = Field(..., pattern="^(efectivo|tarjeta)$")
    tipoPedido: str = Field(..., pattern="^(recoger|delivery)$")
    notas: Optional[str] = None
    propina: float = 0.0

class OrderResponse(BaseModel):
    orderId: str
    total: float
    estimatedTime: str
    status: str
    createdAt: datetime
