# Backend

FastAPI application providing the chat API with hybrid memory (PostgreSQL + Pinecone).

## Structure

```
backend/
├── main.py           # FastAPI app, route definitions
├── database.py       # SQLAlchemy models and DB session
├── schemas.py        # Pydantic request/response models
├── memory_engine.py  # Hybrid memory retrieval and storage
├── vector_store.py   # Pinecone integration
├── llm_adapter.py    # OpenAI / Anthropic provider abstraction
├── requirements.txt
├── Dockerfile
├── .env.example
└── start.sh          # Local dev helper script
```

## API Endpoints

### `POST /chat`
Send a message and receive an AI response with memory context.

**Request**
```json
{ "message": "string", "session_id": "uuid-string" }
```

**Response**
```json
{
  "reply": "string",
  "memory_suggestions": [
    { "type": "preference", "content": "string", "confidence": 0.8, "context": "string" }
  ]
}
```

### `GET /health`
Returns service availability for LLM and vector store.

### `POST /memory`
Manually store a memory context.

Query params: `session_id`, `content`, `memory_type`, `confidence` (default 0.8)

### `GET /session/{session_id}/history`
Returns the last 20 messages for a session.

## Environment Variables

Copy `.env.example` to `.env` and fill in:

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | Yes | Injected by docker-compose — leave as-is |
| `OPENAI_API_KEY` | One of these | OpenAI API key |
| `ANTHROPIC_API_KEY` | One of these | Anthropic API key |
| `DEFAULT_AI_PROVIDER` | Yes | `openai` or `anthropic` |
| `PINECONE_API_KEY` | No | Enables semantic vector search |
| `PINECONE_ENVIRONMENT` | No | Pinecone region (e.g. `us-east-1`) |
| `PINECONE_INDEX_NAME` | No | Index name (default: `chatbot-memory`) |

## Running Locally (without Docker)

Requires PostgreSQL running on `localhost:5432`.

```bash
cd backend

# Using uv (recommended)
./start.sh

# Using pip
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

## Tests

```bash
cd backend

# Structure and schema tests
python test_integration.py

# Endpoint tests
python test_api.py
```
