# Quick Start Guide

## Prerequisites

1. **Docker** and **Docker Compose** installed
2. **API Keys** (at least one AI provider):
   - OpenAI API key (recommended) OR
   - Anthropic API key
   - Pinecone API key (optional, for vector search)

## Setup in 3 Steps

### 1. Configure Environment

```bash
cd backend
cp .env.example .env
```

Edit `.env` and add your API keys:
```env
# Required: At least one AI provider
OPENAI_API_KEY=sk-...
# OR
ANTHROPIC_API_KEY=sk-ant-...

# Optional: For semantic search (recommended)
PINECONE_API_KEY=your_key
PINECONE_ENVIRONMENT=us-east-1
PINECONE_INDEX_NAME=chatbot-memory

# Database (default works with docker-compose)
DATABASE_URL=postgresql://ai_user:ai_pass@db:5432/personal_ai
```

### 2. Start Services

```bash
# From project root
docker-compose up --build
```

Wait for services to start:
- ✅ PostgreSQL on port 5432
- ✅ Backend API on port 8000
- ✅ Frontend on port 3000

### 3. Test the API

Open your browser to:
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## Using the API

### Send a Chat Message

```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is FastAPI?",
    "session_id": "user-123"
  }'
```

Response:
```json
{
  "reply": "FastAPI is a modern, fast web framework for building APIs...",
  "memory_suggestions": []
}
```

### Continue Conversation

```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Should I use it for my project?",
    "session_id": "user-123"
  }'
```

The AI will remember your previous messages and provide context-aware responses!

### Get Chat History

```bash
curl "http://localhost:8000/session/user-123/history"
```

## Interactive API Documentation

Visit http://localhost:8000/docs for interactive Swagger UI where you can:
- Try all endpoints
- See request/response schemas
- Test with different parameters

## Running Locally (without Docker)

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql://user:pass@localhost/chatbot"
export OPENAI_API_KEY="sk-..."

# Run the server
uvicorn main:app --reload
```

Or use the quick start script:
```bash
cd backend
./start.sh
```

## Features in Action

### Context-Aware Responses

The system remembers your preferences:

1. **First message**: "I prefer Python over JavaScript"
2. **Later message**: "What should I learn next?"
3. **AI Response**: Uses stored preference about Python

### Semantic Search

With Pinecone configured, the system finds relevant past conversations:

1. **Past**: "I'm building a REST API"
2. **Now**: "What framework should I use?"
3. **Result**: AI recalls your REST API project

### Memory Suggestions

The system automatically detects important information:

```json
{
  "reply": "That's great!",
  "memory_suggestions": [
    {
      "type": "preference",
      "content": "User prefers TypeScript for frontend",
      "confidence": 0.85,
      "context": "Mentioned multiple times"
    }
  ]
}
```

## Troubleshooting

### "LLM is not configured"
→ Add OPENAI_API_KEY or ANTHROPIC_API_KEY to .env

### "Database connection failed"
→ Ensure PostgreSQL is running (docker-compose includes it)

### "Vector store unavailable"
→ This is optional. System works without Pinecone, just without semantic search

### Port already in use
→ Change ports in docker-compose.yml

## Next Steps

- **Frontend**: The frontend at port 3000 provides a UI
- **Customize**: Edit prompts in llm_adapter.py
- **Add Providers**: Extend AIProvider class for more AI services
- **Production**: Use proper secrets management and environment configs

## Architecture

For detailed architecture information, see [ARCHITECTURE.md](ARCHITECTURE.md)

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Root info |
| `/health` | GET | Health check |
| `/chat` | POST | Send message, get AI response |
| `/memory` | POST | Store memory manually |
| `/session/{id}/history` | GET | Get session history |

## Development

Run tests:
```bash
cd backend
python validate.py        # Structure validation
python test_integration.py  # Integration tests
python test_api.py        # API tests
```

## Support

For issues or questions:
1. Check logs: `docker-compose logs backend`
2. Review ARCHITECTURE.md
3. Check API docs: http://localhost:8000/docs
