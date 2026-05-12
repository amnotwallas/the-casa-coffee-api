from pydantic import BaseModel, Field
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
    items: List[Dict[str, Any]]
    total: float
    status: str
    tracking: TrackingStatus

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
