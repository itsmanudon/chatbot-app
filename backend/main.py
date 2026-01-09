from fastapi import FastAPI, HTTPException
from pydantic import ValidationError
from .schemas import ChatRequest, ChatResponse
import uuid

app = FastAPI(title="Personal AI Memory System")

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        # Dummy response for MVP
        reply = f"Hi! I'm processing your message: '{request.message}'. I'll soon suggest memories."
        
        # Mock memory proposal (will improve in Phase 2)
        memory_suggestions = [
            {
                "type": "preference",
                "content": "You prefer deep technical learning over surface-level tutorials.",
                "confidence": 0.75,
                "context": "Based on past messages about learning goals."
            }
        ]

        return ChatResponse(reply=reply, memory_suggestions=memory_suggestions)

    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors())

