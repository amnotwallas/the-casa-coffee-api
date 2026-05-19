from pydantic import BaseModel, Field, model_validator
from typing import List, Optional, Dict, Any

class CartItem(BaseModel):
    cartItemId: str
    productId: str
    nombre: str
    cantidad: int
    personalizaciones: Dict[str, Any]
    subtotal: float

class Cart(BaseModel):
    items: List[CartItem] = []
    total: float = 0.0
    itemsCount: int = 0

    model_config = {"from_attributes": True}

    @model_validator(mode="before")
    @classmethod
    def map_items(cls, data: any):
        if hasattr(data, "items"):
            data_dict = data.__dict__.copy()
            data_dict["items"] = [
                {
                    "cartItemId": item.id,
                    "productId": item.product_id,
                    "nombre": item.nombre,
                    "cantidad": item.cantidad,
                    "personalizaciones": item.personalizaciones,
                    "subtotal": item.subtotal
                } for item in data.items
            ]
            return data_dict
        return data

class AddToCartRequest(BaseModel):
    productId: str
    cantidad: int = Field(..., gt=0)
    personalizaciones: Dict[str, Any] = {}

class UpdateCartItemRequest(BaseModel):
    cantidad: Optional[int] = Field(None, gt=0)
    personalizaciones: Optional[Dict[str, Any]] = None
