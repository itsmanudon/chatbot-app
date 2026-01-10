# Chatbot App

A robust AI chatbot application with hybrid memory system combining PostgreSQL and Pinecone vector database.

## 🚀 Quick Start

```bash
# 1. Configure environment
cd backend
cp .env.example .env
# Edit .env and add your API keys

# 2. Start services
cd ..
docker-compose up --build

# 3. Access the API
# - API: http://localhost:8000
# - Docs: http://localhost:8000/docs
# - Frontend: http://localhost:3000
```

**See [QUICKSTART.md](QUICKSTART.md) for detailed setup instructions.**

## ✨ Features

- **FastAPI Backend**: Modern, high-performance API with automatic documentation
- **Multiple AI Providers**: Support for OpenAI and Anthropic (Claude) with easy extensibility
- **Hybrid Memory System**: 
  - PostgreSQL for structured data storage
  - Pinecone for semantic vector search
- **Context-Aware Conversations**: AI retrieves relevant context from past interactions
- **Memory Suggestions**: Automatic detection and storage of user preferences and decisions
- **Graceful Degradation**: Works without optional services (Pinecone)
- **Minimalist Design**: ~600 lines of clean, maintainable code

## 📚 Documentation

- **[QUICKSTART.md](QUICKSTART.md)**: Step-by-step setup guide
- **[backend/ARCHITECTURE.md](backend/ARCHITECTURE.md)**: Detailed system architecture
- **[example_usage.py](example_usage.py)**: Python example demonstrating API usage
- **API Docs**: http://localhost:8000/docs (when running)

## 🏗️ Architecture

```
┌─────────────┐
│   Frontend  │
└──────┬──────┘
       │
┌──────▼──────────────────────────┐
│      FastAPI Backend            │
│  ┌──────────────────────────┐  │
│  │   Chat Endpoint          │  │
│  │   Memory Engine          │  │
│  │   LLM Adapter            │  │
│  └──────────────────────────┘  │
└───┬──────────────────────┬──────┘
    │                      │
┌───▼──────┐        ┌──────▼──────┐
│PostgreSQL│        │  Pinecone   │
│ Database │        │  VectorDB   │
└──────────┘        └─────────────┘
```

## Setup

### Prerequisites

- Docker and Docker Compose
- API keys for:
  - OpenAI (optional)
  - Anthropic (optional)
  - Pinecone (optional for vector search)

### Configuration

1. Copy the example environment file:
```bash
cp backend/.env.example backend/.env
```

2. Edit `backend/.env` and add your API keys:
```env
DATABASE_URL=postgresql://ai_user:ai_pass@db:5432/personal_ai
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_ENVIRONMENT=us-east-1
PINECONE_INDEX_NAME=chatbot-memory
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
DEFAULT_AI_PROVIDER=openai
```

### Running the Application

Start all services:
```bash
docker-compose up --build
```

Services will be available at:
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Frontend: http://localhost:3000
- PostgreSQL: localhost:5432

## API Endpoints

### POST /chat
Send a message and get AI response with context

**Request:**
```json
{
  "message": "What programming languages should I learn?",
  "session_id": "uuid-v4-string"
}
```

**Response:**
```json
{
  "reply": "Based on your interest in web development...",
  "memory_suggestions": [
    {
      "type": "preference",
      "content": "User prefers backend development",
      "confidence": 0.8,
      "context": "Detected from conversation"
    }
  ]
}
```

### GET /health
Health check endpoint

### POST /memory
Manually store a memory context

### GET /session/{session_id}/history
Retrieve chat history for a session

## Components

### 1. Database Layer (`database.py`)
- SQLAlchemy models for chat messages and memory contexts
- PostgreSQL connection management
- Schema initialization

### 2. Vector Store (`vector_store.py`)
- Pinecone integration for semantic search
- Sentence transformers for embeddings
- Vector storage and similarity search

### 3. LLM Adapter (`llm_adapter.py`)
- Abstract AI provider interface
- OpenAI and Anthropic implementations
- Context-aware response generation

### 4. Memory Engine (`memory_engine.py`)
- Hybrid retrieval system
- Stores conversations in both PostgreSQL and Pinecone
- Retrieves relevant context using semantic search and SQL queries

### 5. API Routes (`main.py`)
- FastAPI application setup
- Chat endpoint with memory integration
- Health checks and utility endpoints

## 🔧 Development

### Running Tests

```bash
cd backend

# Validate structure and dependencies
python validate.py

# Integration tests
python test_integration.py

# API endpoint tests
python test_api.py
```

### Local Development

```bash
cd backend
./start.sh
# Or manually:
pip install -r requirements.txt
uvicorn main:app --reload
```

## 📊 Project Stats

- **Production Code**: ~600 lines
- **Languages**: Python, TypeScript
- **Framework**: FastAPI
- **Databases**: PostgreSQL, Pinecone
- **AI Providers**: OpenAI, Anthropic

## 🛠️ Technology Stack

**Backend:**
- FastAPI 0.104.1
- SQLAlchemy 2.0.23
- PostgreSQL 16
- Pinecone (vector database)
- OpenAI / Anthropic APIs
- Sentence Transformers (embeddings)

**Frontend:**
- Next.js / React
- TypeScript

## Development

### Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### Run Backend Locally
```bash
cd backend
uvicorn main:app --reload
```

## Minimalist Design

The codebase follows minimalist principles:
- Single responsibility per module
- No unnecessary abstractions
- Clear separation of concerns
- Simple, readable code

## Future Enhancements

- [ ] User authentication
- [ ] Multiple conversation threads
- [ ] Advanced memory categorization
- [ ] Export/import conversations
- [ ] Voice input/output
- [ ] Additional AI providers
