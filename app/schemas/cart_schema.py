from pydantic import BaseModel, Field, model_validator, field_validator
from typing import List, Optional, Dict, Any
from app.core.config import settings

class CartItem(BaseModel):
    cartItemId: str
    productId: str
    nombre: str
    imagen: Optional[str] = None
    cantidad: int
    personalizaciones: Dict[str, Any]
    subtotal: float

    @field_validator("imagen", mode="after")
    @classmethod
    def format_image_url(cls, v: Optional[str]) -> Optional[str]:
        """Convierte nombre de archivo en URL absoluta."""
        if v and not v.startswith(("http://", "https://")):
            return f"{settings.BASE_URL}/api/v1/media/products/{v}"
        return v

class Cart(BaseModel):
    items: List[CartItem] = []
    total: float = 0.0
    itemsCount: int = 0

    model_config = {"from_attributes": True}

    @model_validator(mode="before")
    @classmethod
    def map_items(cls, data: any):
        """Mapea CartDB (SQLModel) a esquema Pydantic Cart."""
        if isinstance(data, dict):
            return data

        if hasattr(data, "items"):
            # Si es un objeto de BD (SQLModel/SQLAlchemy)
            return {
                "total": getattr(data, "total", 0.0),
                "itemsCount": getattr(data, "itemsCount", 0),
                "items": [
                    {
                        "cartItemId": item.id,
                        "productId": item.product_id,
                        "nombre": item.nombre,
                        "imagen": item.imagen,
                        "cantidad": item.cantidad,
                        "personalizaciones": item.personalizaciones,
                        "subtotal": item.subtotal
                    } for item in data.items
                ]
            }
        return data

class AddToCartRequest(BaseModel):
    productId: str
    cantidad: int = Field(..., gt=0)
    personalizaciones: Dict[str, Any] = {}

class UpdateCartItemRequest(BaseModel):
    cantidad: Optional[int] = Field(None, gt=0)
    personalizaciones: Optional[Dict[str, Any]] = None
