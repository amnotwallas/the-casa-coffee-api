from sqlmodel import SQLModel, Field, Column, JSON, Relationship
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.core.datetime_utils import get_now
import uuid

class Review(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    product_id: str = Field(index=True)
    user_id: str = Field(index=True)
    user_name: str
    rating: int
    comentario: str
    fotos: List[str] = Field(default=[], sa_column=Column(JSON))
    fecha: datetime = Field(default_factory=get_now)
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
    fecha: datetime = Field(default_factory=get_now)
    leida: bool = False
    tipo: str = "info"

class FAQ(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    pregunta: str
    respuesta: str
    categoria: str

class StoreSchedule(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    store_id: int = Field(foreign_key="storeinfo.id")
    dia: str # Ej: "Lunes-Viernes"
    apertura: str # Ej: "07:00"
    cierre: str # Ej: "21:00"
    abierto: bool = True
    
    store: "StoreInfo" = Relationship(back_populates="horarios")

class StoreInfo(SQLModel, table=True):
    id: int = Field(default=1, primary_key=True)
    nombre: str
    direccion: str
    telefono: str
    email: str
    estaAbierto: bool = True
    tiempo_espera_actual: int = 15
    volumen_pedidos: str = "medio"
    
    horarios: List[StoreSchedule] = Relationship(back_populates="store", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
