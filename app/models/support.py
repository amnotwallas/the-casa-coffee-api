from sqlmodel import SQLModel, Field, Column, JSON
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

class Review(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    product_id: str = Field(index=True)
    user_id: str = Field(index=True)
    user_name: str
    rating: int
    comentario: str
    fotos: List[str] = Field(default=[], sa_column=Column(JSON))
    fecha: datetime = Field(default_factory=datetime.utcnow)
    helpful_count: int = 0

class Promotion(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    titulo: str
    descripcion: str
    imagen: str
    codigo: Optional[str] = None
    descuento: float = 0.0
    activo: bool = True

class Notification(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(index=True)
    titulo: str
    mensaje: str
    fecha: datetime = Field(default_factory=datetime.utcnow)
    leida: bool = False
    tipo: str = "info"

class FAQ(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    pregunta: str
    respuesta: str
    categoria: str

class StoreInfo(SQLModel, table=True):
    id: int = Field(default=1, primary_key=True)
    nombre: str
    direccion: str
    telefono: str
    email: str
    horarios: List[Dict[str, Any]] = Field(default=[], sa_column=Column(JSON))
    estaAbierto: bool = True
    tiempo_espera_actual: int = 15
    volumen_pedidos: str = "medio"
