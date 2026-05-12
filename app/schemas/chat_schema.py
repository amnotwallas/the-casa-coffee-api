from pydantic import BaseModel
from typing import List, Optional

class ChatRequest(BaseModel):
    message: str
    conversationId: Optional[str] = None

class ChatResponse(BaseModel):
    reply: str
    conversationId: str
    suggestions: List[str]
