from pydantic import BaseModel, field_validator
from typing import List, Optional
from app.core.config import settings

class Category(BaseModel):
    id: str
    nombre: str

class CustomizationOption(BaseModel):
    nombre: str
    extra_precio: float
    valor: Optional[int] = None

class Customization(BaseModel):
    tipo: str
    opciones: List[CustomizationOption]

class NutritionalValues(BaseModel):
    calorias: str
    proteinas: str
    grasas: str
    carbohidratos: Optional[str] = None

class Product(BaseModel):
    id: str
    nombre: str
    descripcion: str
    precio: float
    intensidad: int
    imagenes: List[str]
    categoria: Category
    ingredientes: List[str]
    valores_nutricionales: NutritionalValues
    personalizaciones: List[Customization]
    reviews_count: int
    rating_avg: float
    disponible: bool

    @field_validator("imagenes", mode="after")
    @classmethod
    def format_image_urls(cls, v: List[str]) -> List[str]:
        """Convierte nombres de archivos en URLs absolutas si no lo son ya."""
        formatted_urls = []
        for img in v:
            if img.startswith(("http://", "https://")):
                formatted_urls.append(img)
            else:
                formatted_urls.append(f"{settings.BASE_URL}/api/v1/media/products/{img}")
        return formatted_urls

class ProductListResponse(BaseModel):
    data: List[Product]
    total: int
    page: int
