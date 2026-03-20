from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError
from sqlalchemy.orm import Session
from schemas import ChatRequest, ChatResponse, MemorySuggestion
from database import get_db, init_db
from llm_adapter import llm_adapter
from memory_engine import memory_engine
from vector_store import vector_store

app = FastAPI(
    title="Personal AI Memory System",
    description="AI chatbot with hybrid memory system (PostgreSQL + Pinecone)",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    try:
        init_db()
        print("Database initialized")
    except Exception as e:
        print(f"Database initialization failed: {e}")
    
    # Debugging API Keys
    import os
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        print(f"DEBUG: OPENAI_API_KEY found (starts with {openai_key[:7]}...)")
    else:
        print("DEBUG: OPENAI_API_KEY is Missing/None")

    print(f"Vector store available: {vector_store.is_available()}")
    print(f"LLM available: {llm_adapter.is_available()}")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Personal AI Memory System API",
        "status": "running",
        "vector_store": vector_store.is_available(),
        "llm": llm_adapter.is_available()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "services": {
            "vector_store": vector_store.is_available(),
            "llm": llm_adapter.is_available()
        }
    }

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Main chat endpoint with AI integration and memory retrieval
    
    - Retrieves relevant context from hybrid memory system
    - Generates AI response using configured provider
    - Stores conversation in PostgreSQL and Pinecone
    """
    try:
        # Retrieve relevant context from hybrid system
        context = memory_engine.retrieve_relevant_context(
            db=db,
            query=request.message,
            session_id=request.session_id,
            limit=5
        )
        
        # Get conversation history
        history = memory_engine.get_session_history(
            db=db,
            session_id=request.session_id,
            limit=5
        )
        
        # Generate AI response with context
        reply = llm_adapter.get_response(
            message=request.message,
            context=context,
            conversation_history=history
        )
        
        # Store the conversation
        memory_engine.store_chat_message(
            db=db,
            session_id=request.session_id,
            message=request.message,
            response=reply
        )
        
        # Generate memory suggestions (simplified for now)
        memory_suggestions = []
        
        # Example: detect preferences or decisions
        if any(word in request.message.lower() for word in ["prefer", "like", "love", "favorite"]):
            memory_suggestions.append(
                MemorySuggestion(
                    type="preference",
                    content=f"User expressed: {request.message[:100]}",
                    confidence=0.8,
                    context="Detected from conversation"
                )
            )
        
        return ChatResponse(reply=reply, memory_suggestions=memory_suggestions)
    
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/memory")
async def store_memory(
    session_id: str,
    content: str,
    memory_type: str,
    confidence: float = 0.8,
    db: Session = Depends(get_db)
):
    """Store a memory context manually"""
    try:
        memory_id = memory_engine.store_memory_context(
            db=db,
            session_id=session_id,
            content=content,
            memory_type=memory_type,
            confidence=confidence
        )
        
        return {
            "status": "success",
            "memory_id": memory_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/session/{session_id}/history")
async def get_session_history(session_id: str, db: Session = Depends(get_db)):
    """Get chat history for a session"""
    try:
        history = memory_engine.get_session_history(
            db=db,
            session_id=session_id,
            limit=20
        )
        
        return {
            "session_id": session_id,
            "history": history
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

