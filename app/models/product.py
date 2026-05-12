from sqlmodel import SQLModel, Field, Column, JSON
from typing import List, Optional, Dict, Any
import uuid

class Product(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    nombre: str
    descripcion: str
    precio: float
    intensidad: int
    imagenes: List[str] = Field(default=[], sa_column=Column(JSON))
    categoria: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    ingredientes: List[str] = Field(default=[], sa_column=Column(JSON))
    valores_nutricionales: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    personalizaciones: List[Dict[str, Any]] = Field(default=[], sa_column=Column(JSON))
    reviews_count: int = 0
    rating_avg: float = 0.0
    disponible: bool = True
