from pydantic import BaseModel, field_validator, model_validator
from typing import List, Optional, Dict, Any
from app.core.config import settings

class Category(BaseModel):
    id: int
    nombre: str

class CustomizationOption(BaseModel):
    nombre: str
    extra_precio: float
    valor: Optional[str] = None

class Customization(BaseModel):
    tipo: str
    opciones: List[CustomizationOption]

class NutritionalValues(BaseModel):
    calorias: int
    proteinas: float
    grasas: float
    carbohidratos: Optional[float] = None

class Product(BaseModel):
    id: str
    nombre: str
    descripcion: str
    precio: float
    intensidad: int
    imagenes: List[str]
    icon: str = "coffee"
    categoria: Optional[Category] = None
    ingredientes: List[str]
    valores_nutricionales: Optional[NutritionalValues] = None
    personalizaciones: Optional[List[Customization]] = None

    reviews_count: int
    rating_avg: float
    disponible: bool

    model_config = {"from_attributes": True}

    @model_validator(mode="before")
    @classmethod
    def map_relational_data(cls, data: any):
        """Mapea relaciones de BD a campos JSON para compatibilidad."""
        # Si es un objeto de base de datos (tiene atributos)
        if not isinstance(data, dict):
            # Reconstruir el objeto como un diccionario para Pydantic
            data_dict = {}
            
            # Copiar campos básicos que están en el modelo
            for field in cls.model_fields:
                if field not in ["categoria", "valores_nutricionales", "personalizaciones"]:
                    data_dict[field] = getattr(data, field, None)

            # Mapear Categoría
            categoria = getattr(data, "categoria", None)
            if categoria:
                data_dict["categoria"] = {
                    "id": categoria.id,
                    "nombre": categoria.nombre
                }
            else:
                data_dict["categoria"] = None
            
            # Mapear Nutrición
            nutricion = getattr(data, "valores_nutricionales", None)
            if nutricion:
                data_dict["valores_nutricionales"] = {
                    "calorias": nutricion.calorias,
                    "proteinas": nutricion.proteinas,
                    "grasas": nutricion.grasas,
                    "carbohidratos": nutricion.carbohidratos
                }
            else:
                data_dict["valores_nutricionales"] = None
            
            # Mapear Personalizaciones
            personalizaciones = getattr(data, "personalizaciones", [])
            if personalizaciones:
                data_dict["personalizaciones"] = [
                    {
                        "tipo": cust.tipo,
                        "opciones": [
                            {
                                "nombre": opt.nombre,
                                "extra_precio": opt.extra_precio,
                                "valor": opt.valor
                            } for opt in cust.opciones
                        ]
                    } for cust in personalizaciones
                ]
            else:
                data_dict["personalizaciones"] = None
                
            return data_dict
        return data

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

class ProductCreate(BaseModel):
    id: Optional[str] = None
    nombre: str
    descripcion: str
    precio: float
    intensidad: int
    imagenes: List[str]
    icon: str = "coffee"
    category_id: int
    ingredientes: List[str] = []
    valores_nutricionales: Optional[NutritionalValues] = None
    personalizaciones: List[Customization] = []
    disponible: bool = True

class ProductListResponse(BaseModel):
    data: List[Product]
    total: int
    page: int
