import uuid
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from database import ChatMessage, MemoryContext
from vector_store import vector_store

class MemoryEngine:
    """Hybrid memory system combining PostgreSQL and Pinecone"""
    
    def __init__(self):
        self.vector_store = vector_store
    
    def store_chat_message(
        self, 
        db: Session, 
        session_id: str, 
        message: str, 
        response: str
    ) -> str:
        """Store chat message in both PostgreSQL and Pinecone"""
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
        """Store memory context in both PostgreSQL and Pinecone"""
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
        """Hybrid retrieval: combine vector search and SQL queries"""
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
        """Get recent chat history for a session"""
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

# Global instance
memory_engine = MemoryEngine()
