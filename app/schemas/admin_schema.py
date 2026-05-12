from pydantic import BaseModel
from typing import List, Dict, Any

class AdminAnalytics(BaseModel):
    ventasHoy: float
    ventasMes: float
    pedidosPendientes: int
    productosPopulares: List[Dict[str, Any]]
    ingresos: Dict[str, float]

class UpdateOrderStatusRequest(BaseModel):
    status: str # pending, preparing, ready, on_the_way, delivered, cancelled
