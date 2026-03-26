"""
main.py
-------
FastAPI application entry point for the Personal AI Memory System.

Endpoints
---------
GET  /
    Root endpoint — returns API name, status, and dependency availability.
GET  /health
    Lightweight health check — returns LLM and vector store availability.
POST /chat
    Main conversational endpoint.  Retrieves hybrid memory context, generates
    an AI response, persists the exchange, and returns memory suggestions.
POST /memory
    Manually store a typed memory context for a session.
GET  /sessions
    List all chat sessions with summary metadata (title, preview, count,
    last-active timestamp).
GET  /session/{session_id}/history
    Retrieve the full interleaved conversation history for a given session.
DELETE /session/{session_id}
    Delete all messages and memory contexts for a session.

Interactive API documentation is available at ``/docs`` (Swagger UI) and
``/redoc`` (ReDoc) when the backend is running.
"""

import os
import time
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from database import get_db, init_db
from llm_adapter import llm_adapter
from logging_config import get_logger
from memory_engine import memory_engine
from schemas import (
    ChatHistoryMessage,
    ChatRequest,
    ChatResponse,
    MemorySuggestion,
    SessionSummary,
)
from vector_store import vector_store

logger = get_logger(__name__)

limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and graceful shutdown."""
    # --- startup: fail fast if required env vars are missing ---
    required_vars = ["DATABASE_URL"]
    missing = [v for v in required_vars if not os.getenv(v)]
    if missing:
        raise RuntimeError(
            f"Missing required environment variables: {', '.join(missing)}"
        )

    if not os.getenv("OPENAI_API_KEY") and not os.getenv("ANTHROPIC_API_KEY"):
        raise RuntimeError(
            "At least one AI provider key must be set: OPENAI_API_KEY or ANTHROPIC_API_KEY"
        )

    try:
        init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.error("Database initialization failed: %s", e)

    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        logger.info("OPENAI_API_KEY found (starts with %s...)", openai_key[:7])
    else:
        logger.warning("OPENAI_API_KEY is missing")

    logger.info("Vector store available: %s", vector_store.is_available())
    logger.info("LLM available: %s", llm_adapter.is_available())

    yield  # application runs here

    # --- shutdown ---
    logger.info("Shutting down — closing database connections")
    from database import engine

    engine.dispose()


app = FastAPI(
    title="Personal AI Memory System",
    description="AI chatbot with hybrid memory system (PostgreSQL + Pinecone)",
    version="1.0.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


_MAX_BODY_BYTES = 32_768  # 32 KB


@app.middleware("http")
async def enforce_body_size(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > _MAX_BODY_BYTES:
        from fastapi.responses import JSONResponse

        return JSONResponse(
            status_code=413,
            content={"detail": "Request body too large (max 32 KB)"},
        )
    return await call_next(request)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "%s %s %s %.1fms",
        request.method,
        request.url.path,
        response.status_code,
        elapsed_ms,
    )
    return response


# CORS middleware — restrict origins via ALLOWED_ORIGINS env var (comma-separated)
# Defaults to localhost:3000 for local development
_raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000")
allowed_origins = [o.strip() for o in _raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Personal AI Memory System API",
        "status": "running",
        "vector_store": vector_store.is_available(),
        "llm": llm_adapter.is_available(),
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "services": {
            "vector_store": vector_store.is_available(),
            "llm": llm_adapter.is_available(),
        },
    }


@app.post("/chat", response_model=ChatResponse)
@limiter.limit("20/minute")
async def chat(request: Request, body: ChatRequest, db: Session = Depends(get_db)):
    """
    Main chat endpoint with AI integration and memory retrieval

    - Retrieves relevant context from hybrid memory system
    - Generates AI response using configured provider
    - Stores conversation in PostgreSQL and Pinecone
    """
    try:
        # Retrieve relevant context from hybrid system
        context = memory_engine.retrieve_relevant_context(
            db=db, query=body.message, session_id=body.session_id, limit=5
        )

        # Get conversation history
        history = memory_engine.get_session_history(
            db=db, session_id=body.session_id, limit=5
        )

        # Generate AI response with context
        reply = llm_adapter.get_response(
            message=body.message, context=context, conversation_history=history
        )

        # Store the conversation
        memory_engine.store_chat_message(
            db=db, session_id=body.session_id, message=body.message, response=reply
        )

        # Generate memory suggestions (simplified for now)
        memory_suggestions = []

        # Example: detect preferences or decisions
        if any(
            word in body.message.lower()
            for word in ["prefer", "like", "love", "favorite"]
        ):
            memory_suggestions.append(
                MemorySuggestion(
                    type="preference",
                    content=f"User expressed: {body.message[:100]}",
                    confidence=0.8,
                    context="Detected from conversation",
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
    db: Session = Depends(get_db),
):
    """Store a memory context manually"""
    try:
        memory_id = memory_engine.store_memory_context(
            db=db,
            session_id=session_id,
            content=content,
            memory_type=memory_type,
            confidence=confidence,
        )

        return {"status": "success", "memory_id": memory_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sessions", response_model=list[SessionSummary])
async def list_sessions(db: Session = Depends(get_db)):
    """List all chat sessions ordered by most recently active."""
    try:
        sessions = memory_engine.get_all_sessions(db=db)
        return sessions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/session/{session_id}/history", response_model=list[ChatHistoryMessage])
async def get_session_history(session_id: str, db: Session = Depends(get_db)):
    """Get full interleaved chat history for a session (user + AI messages)."""
    try:
        history = memory_engine.get_full_session_history(
            db=db, session_id=session_id, limit=100
        )
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/session/{session_id}")
async def delete_session(session_id: str, db: Session = Depends(get_db)):
    """Delete all messages and memory contexts for a session."""
    try:
        deleted = memory_engine.delete_session(db=db, session_id=session_id)
        return {"status": "success", "deleted_messages": deleted}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
