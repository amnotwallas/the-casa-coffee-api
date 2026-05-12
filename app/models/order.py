from sqlmodel import SQLModel, Field, Column, JSON
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

class Order(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(index=True)
    fecha: datetime = Field(default_factory=datetime.utcnow)
    items: List[Dict[str, Any]] = Field(default=[], sa_column=Column(JSON))
    total: float
    status: str = "pending"
    tracking: Dict[str, bool] = Field(
        default={
            "preparando": True,
            "listo": False,
            "enCamino": False,
            "entregado": False
        },
        sa_column=Column(JSON)
    )

class CartDB(SQLModel, table=True):
    user_id: str = Field(primary_key=True)
    items: List[Dict[str, Any]] = Field(default=[], sa_column=Column(JSON))
    total: float = 0.0
    itemsCount: int = 0
