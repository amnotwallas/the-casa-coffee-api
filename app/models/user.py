from sqlmodel import SQLModel, Field, Column, JSON
from typing import List, Optional, Dict, Any
import uuid

class User(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    firebase_uid: str = Field(unique=True, index=True)
    nombre: str
    email: str = Field(unique=True, index=True)
    telefono: Optional[str] = None
    foto: Optional[str] = None
    direcciones: List[Dict[str, Any]] = Field(default=[], sa_column=Column(JSON))
    preferencias: Dict[str, Any] = Field(
        default={
            "notificacionesPush": True,
            "tipoLecheFavorita": "Almendra",
            "idioma": "es"
        }, 
        sa_column=Column(JSON)
    )
    favoritos: List[str] = Field(default=[], sa_column=Column(JSON))
