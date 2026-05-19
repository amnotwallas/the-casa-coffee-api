from pydantic import BaseModel, Field, model_validator
from typing import List, Optional
from datetime import datetime

# --- REVIEWS ---
class ReviewCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comentario: str
    fotos: List[str] = []

class Review(ReviewCreate):
    id: str
    userId: str
    userName: str
    userPhoto: Optional[str] = None
    fecha: datetime
    helpful_count: int = 0

class ProductReviewsResponse(BaseModel):
    reviews: List[Review]
    avgRating: float
    totalReviews: int

# --- PROMOCIONES ---
class Promotion(BaseModel):
    id: str
    titulo: str
    descripcion: str
    descuento: str
    codigo: Optional[str] = None
    imagen: Optional[str] = None

# --- NOTIFICACIONES ---
class Notification(BaseModel):
    id: str
    tipo: str # PROMO, ORDER_STATUS
    titulo: str
    mensaje: str
    leida: bool = False
    fecha: datetime
    data: dict = {}

# --- INFO & FAQ ---
class FAQ(BaseModel):
    pregunta: str
    respuesta: str
    categoria: str

class StoreHours(BaseModel):
    horarios: List[dict]
    estaAbierto: bool
    tiempo_espera_actual: int
    volumen_pedidos: str
    
    model_config = {"from_attributes": True}

    @model_validator(mode="before")
    @classmethod
    def map_horarios(cls, data: any):
        """Mapea horarios a la lista de horarios."""
        if hasattr(data, "horarios"):
            data_dict = data.__dict__.copy()
            data_dict["horarios"] = [
                {
                    "dia": h.dia,
                    "apertura": h.apertura,
                    "cierre": h.cierre,
                    "abierto": h.abierto
                } for h in data.horarios
            ]
            return data_dict
        return data
