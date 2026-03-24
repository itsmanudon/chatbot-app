"""
memory_engine.py
----------------
Hybrid memory orchestration layer combining PostgreSQL and Pinecone.

The ``MemoryEngine`` class is the single point of contact between the FastAPI
routes and the two persistence layers.  It exposes four operations:

store_chat_message
    Persists a user/AI exchange to PostgreSQL and, when available, embeds the
    combined text into Pinecone for future semantic search.

store_memory_context
    Persists an extracted memory (preference, belief, decision) to PostgreSQL
    and Pinecone with a confidence score.

retrieve_relevant_context
    Builds a context string for the LLM by combining three sources:

    1. **Semantic search** (Pinecone) — top-k most similar past messages and
       memories for the current query.
    2. **Recent messages** (PostgreSQL) — the 3 most recent exchanges in the
       session, regardless of semantic relevance.
    3. **High-confidence memories** (PostgreSQL) — stored memories with
       ``confidence ≥ 0.7``.

    Duplicate entries are deduplicated before returning.

get_session_history
    Returns the N most recent user messages in a session formatted as the
    ``[{"role": "user", "content": "..."}]`` list expected by the LLM adapter.

A single global instance (``memory_engine``) is created at module import
time and shared across all requests.
"""

import uuid
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime
from database import ChatMessage, MemoryContext
from vector_store import vector_store

# Maximum length of the session title (first user message, truncated)
_TITLE_MAX_LENGTH = 60
# Maximum length of the session preview (most recent AI response, truncated)
_PREVIEW_MAX_LENGTH = 80

class MemoryEngine:
    """Hybrid memory system combining PostgreSQL and Pinecone.

    All methods require a SQLAlchemy ``Session`` obtained via the
    ``get_db`` FastAPI dependency.  Pinecone operations are gated behind
    ``self.vector_store.is_available()`` so the engine degrades gracefully
    to PostgreSQL-only mode when Pinecone is not configured.
    """

    def __init__(self):
        self.vector_store = vector_store
    
    def store_chat_message(
        self,
        db: Session,
        session_id: str,
        message: str,
        response: str
    ) -> str:
        """Persist a user/AI exchange to PostgreSQL (and Pinecone if available).

        The combined ``"<message> <response>"`` string is embedded and stored
        in Pinecone so it can be retrieved by semantic similarity in future
        turns.  The returned ``vector_id`` is also saved in the SQL row for
        cross-referencing.

        Args:
            db: Active SQLAlchemy session.
            session_id: UUID identifying the conversation.
            message: The user's message text.
            response: The AI-generated reply text.

        Returns:
            The UUID string of the new ``ChatMessage`` row.
        """
        chat_id = str(uuid.uuid4())
        
        # Store embedding in Pinecone if available
        vector_id = ""
        if self.vector_store.is_available():
            metadata = {
                "session_id": session_id,
                "message": message,
                "response": response,
                "type": "chat",
                "timestamp": datetime.utcnow().isoformat()
            }
            vector_id = self.vector_store.store_embedding(
                f"{message} {response}", 
                metadata
            )
        
        # Store in PostgreSQL
        chat_message = ChatMessage(
            id=chat_id,
            session_id=session_id,
            message=message,
            response=response,
            vector_id=vector_id,
            timestamp=datetime.utcnow()
        )
        db.add(chat_message)
        db.commit()
        
        return chat_id
    
    def store_memory_context(
        self,
        db: Session,
        session_id: str,
        content: str,
        memory_type: str,
        confidence: float
    ) -> str:
        """Persist an extracted memory to PostgreSQL (and Pinecone if available).

        Args:
            db: Active SQLAlchemy session.
            session_id: UUID identifying the conversation this memory belongs to.
            content: Human-readable description of the memory.
            memory_type: One of ``"preference"``, ``"belief"``, or
                ``"decision"``.
            confidence: Float in ``[0.0, 1.0]`` indicating certainty.
                Memories with ``confidence ≥ 0.7`` are injected into future
                LLM context.

        Returns:
            The UUID string of the new ``MemoryContext`` row.
        """
        memory_id = str(uuid.uuid4())
        
        # Store embedding in Pinecone if available
        vector_id = ""
        if self.vector_store.is_available():
            metadata = {
                "session_id": session_id,
                "memory_type": memory_type,
                "content": content,
                "confidence": confidence,
                "type": "memory",
                "timestamp": datetime.utcnow().isoformat()
            }
            vector_id = self.vector_store.store_embedding(content, metadata)
        
        # Store in PostgreSQL
        memory = MemoryContext(
            id=memory_id,
            session_id=session_id,
            content=content,
            memory_type=memory_type,
            confidence=confidence,
            vector_id=vector_id,
            timestamp=datetime.utcnow()
        )
        db.add(memory)
        db.commit()
        
        return memory_id
    
    def retrieve_relevant_context(
        self,
        db: Session,
        query: str,
        session_id: str,
        limit: int = 5
    ) -> str:
        """Build a context string for the LLM using hybrid retrieval.

        Combines three sources (deduplicating across all of them):

        1. **Pinecone semantic search** — top ``limit`` vectors most similar
           to *query*, scoped to *session_id*.
        2. **Recent SQL messages** — the 3 most recent ``ChatMessage`` rows
           for *session_id*, added regardless of semantic relevance.
        3. **High-confidence SQL memories** — up to 3 ``MemoryContext`` rows
           for *session_id* where ``confidence ≥ 0.7``.

        Args:
            db: Active SQLAlchemy session.
            query: The user's current message, used as the semantic search
                query.
            session_id: UUID scoping all lookups to a single conversation.
            limit: Maximum total context items to return (default 5).

        Returns:
            A newline-separated string of context fragments ready to be
            injected into the LLM system prompt, or an empty string when no
            relevant context is found.
        """
        context_parts = []
        
        # 1. Vector search for semantic similarity
        if self.vector_store.is_available():
            similar_items = self.vector_store.search_similar(
                query,
                top_k=limit,
                filter={"session_id": session_id}
            )
            
            for item in similar_items:
                metadata = item.get("metadata", {})
                if metadata.get("type") == "chat":
                    context_parts.append(
                        f"Previous: {metadata.get('message', '')} -> {metadata.get('response', '')}"
                    )
                elif metadata.get("type") == "memory":
                    context_parts.append(
                        f"Memory ({metadata.get('memory_type', '')}): {metadata.get('content', '')}"
                    )
        
        # 2. PostgreSQL: Get recent messages from the session
        recent_messages = db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(
            ChatMessage.timestamp.desc()
        ).limit(3).all()
        
        for msg in reversed(recent_messages):
            context_parts.append(f"Recent: {msg.message} -> {msg.response}")
        
        # 3. PostgreSQL: Get high-confidence memories
        high_confidence_memories = db.query(MemoryContext).filter(
            MemoryContext.session_id == session_id,
            MemoryContext.confidence >= 0.7
        ).order_by(
            MemoryContext.timestamp.desc()
        ).limit(3).all()
        
        for memory in high_confidence_memories:
            context_parts.append(
                f"Known {memory.memory_type}: {memory.content}"
            )
        
        # Deduplicate and return
        unique_parts = list(set(context_parts))
        return "\n\n".join(unique_parts[:limit])
    
    def get_session_history(
        self,
        db: Session,
        session_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Return the most recent user messages for *session_id*.

        The result is formatted as a list of ``{"role": "user", "content":
        "..."}`` dicts, compatible with both the OpenAI and Anthropic message
        schemas.  Only the user-side of each exchange is included; the AI
        replies are omitted because the LLM adapter prepends them via the
        context string.

        Args:
            db: Active SQLAlchemy session.
            session_id: UUID identifying the conversation.
            limit: Maximum number of messages to return (default 10).

        Returns:
            List of message dicts ordered oldest-first, up to *limit* entries.
        """
        messages = db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(
            ChatMessage.timestamp.desc()
        ).limit(limit).all()
        
        return [
            {
                "role": "user",
                "content": msg.message
            }
            for msg in reversed(messages)
        ]

    def get_full_session_history(
        self,
        db: Session,
        session_id: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Return the full conversation history for *session_id*, interleaved.

        Each exchange row in the database is expanded into two message dicts —
        one for the user turn and one for the AI turn — preserving the
        chronological order.

        Args:
            db: Active SQLAlchemy session.
            session_id: UUID identifying the conversation.
            limit: Maximum number of exchange *rows* to fetch (default 100).
                The returned list may contain up to ``2 * limit`` entries.

        Returns:
            List of message dicts ordered oldest-first, each with keys
            ``id``, ``role`` (``"user"`` or ``"ai"``), ``content``, and
            ``timestamp``.
        """
        rows = db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(
            ChatMessage.timestamp.asc()
        ).limit(limit).all()

        result: List[Dict[str, Any]] = []
        for row in rows:
            result.append({
                "id": f"{row.id}-user",
                "role": "user",
                "content": row.message,
                "timestamp": row.timestamp,
            })
            result.append({
                "id": f"{row.id}-ai",
                "role": "ai",
                "content": row.response,
                "timestamp": row.timestamp,
            })
        return result

    def get_all_sessions(
        self,
        db: Session,
    ) -> List[Dict[str, Any]]:
        """Return a summary list of all distinct chat sessions.

        For each unique ``session_id`` found in ``chat_messages`` the method
        returns the first user message (used as the display title), a snippet
        of the most recent AI response (preview), the total number of exchange
        rows, and the timestamp of the most recent row.

        Args:
            db: Active SQLAlchemy session.

        Returns:
            List of session summary dicts ordered most-recently-active first,
            each containing ``session_id``, ``title``, ``preview``,
            ``message_count``, and ``last_message_at``.
        """
        from sqlalchemy import func

        # Aggregate per session: count, latest timestamp
        agg = (
            db.query(
                ChatMessage.session_id,
                func.count(ChatMessage.id).label("message_count"),
                func.max(ChatMessage.timestamp).label("last_message_at"),
            )
            .group_by(ChatMessage.session_id)
            .all()
        )

        sessions = []
        for row in agg:
            # First message (title)
            first = (
                db.query(ChatMessage)
                .filter(ChatMessage.session_id == row.session_id)
                .order_by(ChatMessage.timestamp.asc())
                .first()
            )
            # Most recent message (preview)
            last = (
                db.query(ChatMessage)
                .filter(ChatMessage.session_id == row.session_id)
                .order_by(ChatMessage.timestamp.desc())
                .first()
            )

            title = (first.message[:_TITLE_MAX_LENGTH] + "…") if first and len(first.message) > _TITLE_MAX_LENGTH else (first.message if first else "New Chat")
            preview = (last.response[:_PREVIEW_MAX_LENGTH] + "…") if last and len(last.response) > _PREVIEW_MAX_LENGTH else (last.response if last else "")

            sessions.append({
                "session_id": row.session_id,
                "title": title,
                "preview": preview,
                "message_count": row.message_count,
                "last_message_at": row.last_message_at,
            })

        # Most recent first
        sessions.sort(key=lambda s: s["last_message_at"], reverse=True)
        return sessions

    def delete_session(
        self,
        db: Session,
        session_id: str,
    ) -> int:
        """Delete all messages and memory contexts for *session_id*.

        Args:
            db: Active SQLAlchemy session.
            session_id: UUID of the session to remove.

        Returns:
            The number of ``ChatMessage`` rows deleted.
        """
        deleted = (
            db.query(ChatMessage)
            .filter(ChatMessage.session_id == session_id)
            .delete(synchronize_session=False)
        )
        db.query(MemoryContext).filter(
            MemoryContext.session_id == session_id
        ).delete(synchronize_session=False)
        db.commit()
        return deleted

# Global instance
memory_engine = MemoryEngine()
