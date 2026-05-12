from pydantic import BaseModel, Field
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

class AddToCartRequest(BaseModel):
    productId: str
    cantidad: int = Field(..., gt=0)
    personalizaciones: Dict[str, Any] = {}

class UpdateCartItemRequest(BaseModel):
    cantidad: Optional[int] = Field(None, gt=0)
    personalizaciones: Optional[Dict[str, Any]] = None
