from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

class AdminAnalyticsDeltas(BaseModel):
    ventasHoy: float
    pedidosSemanales: float
    ingresosSemanales: float

class AdminAnalytics(BaseModel):
    ventasHoy: float
    ventasMes: float
    pedidosPendientes: int
    productosPopulares: List[Dict[str, Any]]
    ingresos: Dict[str, float]
    clientesTotales: int
    productosTotales: int
    ventasSemanales: List[Dict[str, Any]] = []
    deltas: AdminAnalyticsDeltas

class UpdateOrderStatusRequest(BaseModel):
    status: str

class AdminOrderResponse(BaseModel):
    id: str
    user_id: str
    customerName: str
    fecha: datetime
    items: List[Dict[str, Any]] = []
    total: float
    status: str
    tracking: Dict[str, bool]

class NotificationBase(BaseModel):
    id: str
    type: str
    title: str
    body: str
    read: bool
    created_at: datetime

class NotificationRead(NotificationBase):
    pass
