from sqlmodel import SQLModel, Field, Column, JSON, Relationship
from typing import List, Optional, Dict, Any
import uuid

class UserFavorite(SQLModel, table=True):
    user_id: str = Field(foreign_key="user.id", primary_key=True)
    product_id: str = Field(foreign_key="product.id", primary_key=True)

class Category(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str
    productos: List["Product"] = Relationship(back_populates="categoria")

class Nutrition(SQLModel, table=True):
    product_id: str = Field(foreign_key="product.id", primary_key=True)
    calorias: int = Field(default=0)
    proteinas: float = Field(default=0.0)
    grasas: float = Field(default=0.0)
    carbohidratos: float = Field(default=0.0)
    
    product: "Product" = Relationship(back_populates="valores_nutricionales")

class Customization(SQLModel, table=True):
    id: str = Field(default_factory=lambda: f"cust-{str(uuid.uuid4())[:8]}", primary_key=True)
    product_id: str = Field(foreign_key="product.id", index=True)
    tipo: str # Ej: "Leche", "Tamaño"
    
    opciones: List["CustomizationOption"] = Relationship(back_populates="customization", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    product: "Product" = Relationship(back_populates="personalizaciones")

class CustomizationOption(SQLModel, table=True):
    id: str = Field(default_factory=lambda: f"opt-{str(uuid.uuid4())[:8]}", primary_key=True)
    customization_id: str = Field(foreign_key="customization.id", index=True)
    nombre: str # Ej: "Almendra"
    extra_precio: float = 0.0
    valor: Optional[str] = None
    
    customization: Customization = Relationship(back_populates="opciones")

class Product(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    nombre: str
    descripcion: str
    precio: float
    intensidad: int
    imagenes: List[str] = Field(default=[], sa_column=Column(JSON))
    
    category_id: Optional[int] = Field(default=None, foreign_key="category.id")
    categoria: Optional[Category] = Relationship(back_populates="productos")
    
    # Nueva relación Nutrición (1:1)
    valores_nutricionales: Optional[Nutrition] = Relationship(back_populates="product", sa_relationship_kwargs={"cascade": "all, delete-orphan", "uselist": False})
    
    # Nueva relación Personalizaciones (1:N)
    personalizaciones: List[Customization] = Relationship(back_populates="product", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    
    ingredientes: List[str] = Field(default=[], sa_column=Column(JSON))
    
    usuarios_favoritos: List["User"] = Relationship(back_populates="favoritos", link_model=UserFavorite)
    embedding: Optional[List[float]] = Field(default=None, sa_column=Column(JSON))
    
    reviews_count: int = 0
    rating_avg: float = 0.0
    disponible: bool = True
