from pydantic import BaseModel
from typing import List, Optional
import uuid

class ChatRequest(BaseModel):
    message: str
    session_id: str  # UUID v4 string

class MemorySuggestion(BaseModel):
    type: str  # "preference", "belief", "decision"
    content: str
    confidence: float  # 0.0 to 1.0
    context: Optional[str] = None

class ChatResponse(BaseModel):
    reply: str
    memory_suggestions: List[MemorySuggestion] = []
