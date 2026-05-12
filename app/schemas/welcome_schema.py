from pydantic import BaseModel
from typing import List, Optional
from app.schemas.product_schema import Product

class WelcomeResponse(BaseModel):
    message: str
    recommendations: List[Product]
    conversationId: str
