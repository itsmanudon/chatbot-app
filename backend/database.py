import os
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, Column, String, Text, DateTime, Float
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from datetime import datetime

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://ai_user:ai_pass@localhost:5432/personal_ai")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(String, primary_key=True)
    session_id = Column(String, index=True)
    message = Column(Text)
    response = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    vector_id = Column(String, nullable=True)  # Reference to Pinecone vector

class MemoryContext(Base):
    __tablename__ = "memory_contexts"
    
    id = Column(String, primary_key=True)
    session_id = Column(String, index=True)
    content = Column(Text)
    memory_type = Column(String)  # preference, belief, decision
    confidence = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    vector_id = Column(String, nullable=True)

def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
