from sqlmodel import SQLModel, Field, Column, JSON, Relationship
from typing import List, Optional, Dict, Any
import uuid
from app.models.product import UserFavorite

class Preference(SQLModel, table=True):
    user_id: str = Field(foreign_key="user.id", primary_key=True)
    notificacionesPush: bool = Field(default=True)
    tipoLecheFavorita: Optional[str] = Field(default="Almendra")
    idioma: str = Field(default="es")
    
    user: "User" = Relationship(back_populates="preferencias")

class Address(SQLModel, table=True):
    id: str = Field(default_factory=lambda: f"addr-{str(uuid.uuid4())[:8]}", primary_key=True)
    user_id: str = Field(foreign_key="user.id", index=True)
    calle: str
    ciudad: str
    codigoPostal: str
    referencia: Optional[str] = None
    esDefault: bool = Field(default=False)
    
    # Relación inversa
    user: "User" = Relationship(back_populates="direcciones")

class User(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    firebase_uid: str = Field(unique=True, index=True)
    nombre: str
    email: str = Field(unique=True, index=True)
    is_admin: bool = Field(default=False)
    telefono: Optional[str] = None
    foto: Optional[str] = None
    
    # Relación uno a muchos con direcciones
    direcciones: List[Address] = Relationship(back_populates="user", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    
    # Relación muchos a muchos con favoritos
    favoritos: List["Product"] = Relationship(back_populates="usuarios_favoritos", link_model=UserFavorite)
    
    # Relación uno a uno con preferencias
    preferencias: Optional[Preference] = Relationship(back_populates="user", sa_relationship_kwargs={"cascade": "all, delete-orphan", "uselist": False})
