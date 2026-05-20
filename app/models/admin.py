from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field
import uuid

class AdminNotification(SQLModel, table=True):
    __tablename__ = "admin_notifications"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    type: str = Field(index=True) # 'order', 'system'
    title: str
    body: str
    read: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
