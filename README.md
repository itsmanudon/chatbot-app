# AI Chatbot with Hybrid Memory

A full-stack AI chatbot that remembers conversations using a hybrid memory
system — PostgreSQL for structured storage and Pinecone for semantic vector
search.

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 16, React 19, Tailwind CSS |
| Backend | FastAPI, Python 3.12 |
| Database | PostgreSQL 16 |
| Vector Store | Pinecone (optional) |
| AI Providers | OpenAI (default) or Anthropic |

## Project Structure

```
chatbot-app/
├── backend/            # FastAPI application
│   ├── main.py         # Route definitions and app entry point
│   ├── database.py     # SQLAlchemy models and session management
│   ├── schemas.py      # Pydantic request/response models
│   ├── memory_engine.py# Hybrid memory retrieval and storage
│   ├── vector_store.py # Pinecone integration
│   ├── llm_adapter.py  # OpenAI / Anthropic provider abstraction
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/           # Next.js application
│   ├── src/app/
│   │   ├── page.tsx    # Chat UI component
│   │   └── layout.tsx  # Root layout and metadata
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
├── .env.example        # Root env template (DB credentials)
└── example_usage.py    # Python client demo
```

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose
- An API key from [OpenAI](https://platform.openai.com) or [Anthropic](https://console.anthropic.com)
- A [Pinecone](https://app.pinecone.io) account (optional — app works without it using PostgreSQL-only memory)

## Setup

**1. Clone the repo**

```bash
git clone https://github.com/itsmanudon/chatbot-app.git
cd chatbot-app
```

**2. Create environment files**

```bash
# Root .env — DB credentials used by docker-compose
cp .env.example .env

# Backend .env — API keys for AI providers and Pinecone
cp backend/.env.example backend/.env
```

Edit `backend/.env` and add your API keys:

```env
OPENAI_API_KEY=sk-...          # or leave blank and set ANTHROPIC_API_KEY
ANTHROPIC_API_KEY=             # optional alternative provider
DEFAULT_AI_PROVIDER=openai     # "openai" or "anthropic"

PINECONE_API_KEY=              # optional — enables semantic vector search
PINECONE_ENVIRONMENT=us-east-1 # Pinecone serverless region
PINECONE_INDEX_NAME=chatbot-memory
```

**3. Start everything**

```bash
docker-compose up --build
```

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| API Docs (ReDoc) | http://localhost:8000/redoc |

## How the Hybrid Memory System Works

Every conversation is stored in two places simultaneously:

```
User message
     │
     ▼
┌─────────────────────────────────┐
│         Memory Engine           │
│                                 │
│  1. Retrieve relevant context   │
│     ├─ Pinecone semantic search │
│     ├─ Recent SQL messages      │
│     └─ High-confidence memories │
│                                 │
│  2. Generate AI response        │
│     └─ LLM Adapter (context     │
│        injected as system msg)  │
│                                 │
│  3. Store exchange              │
│     ├─ PostgreSQL (structured)  │
│     └─ Pinecone (vector embed)  │
└─────────────────────────────────┘
```

**PostgreSQL** stores every message and extracted memory with full metadata.
It is always available and provides reliable, filtered retrieval (by session
ID, recency, or confidence threshold).

**Pinecone** stores 384-dimensional embeddings of each message/memory using
the `llama-text-embed-v2` model.  It enables semantic similarity search —
finding past messages that are *conceptually* similar to the current query,
even when they share no keywords.

When Pinecone is not configured, the system falls back to PostgreSQL-only
retrieval transparently.

### Memory Types

| Type | Description | Example |
|---|---|---|
| `preference` | Things the user likes or prefers | "I prefer Python for backend work" |
| `belief` | Facts the user states as true | "I think async is always better" |
| `decision` | Choices the user has made | "I decided to use FastAPI" |

Memories with a confidence score ≥ 0.7 are automatically injected into the
LLM context for future turns.

## Architecture

```
┌─────────────┐
│   Frontend  │  (Next.js — browser)
└──────┬──────┘
       │ HTTP (axios)
┌──────▼──────────────────────────┐
│         FastAPI Backend         │
│  ┌────────────────────────────┐ │
│  │  Memory Engine             │ │
│  │  LLM Adapter (OpenAI/      │ │
│  │              Anthropic)    │ │
│  └────────────────────────────┘ │
└──────┬──────────────────┬───────┘
       │                  │
┌──────▼──────┐    ┌───────▼──────┐
│ PostgreSQL  │    │   Pinecone   │
│ (messages,  │    │  (semantic   │
│  memories)  │    │   vectors)   │
└─────────────┘    └──────────────┘
```

## Troubleshooting

**Backend fails to start**

Check that `backend/.env` exists and contains valid values.  The startup log
prints which services are available:

```
Vector store available: True/False
LLM available: True/False
```

**`LLM available: False`**

Neither `OPENAI_API_KEY` nor `ANTHROPIC_API_KEY` is set, or
`DEFAULT_AI_PROVIDER` points to a provider whose key is missing.

**`Vector store available: False`**

`PINECONE_API_KEY` is not set — this is expected if you want to run without
Pinecone.  The app will use PostgreSQL-only memory.

**Database connection errors**

The backend depends on the `db` service.  With Docker Compose this is handled
automatically.  For local development, ensure PostgreSQL is running on
`localhost:5432` and `DATABASE_URL` is set correctly in `backend/.env`.

**Frontend cannot reach the backend**

`NEXT_PUBLIC_API_URL` defaults to `http://localhost:8000`.  If you change the
backend port, update this variable in `docker-compose.yml` or create a
`frontend/.env.local` file.

## Development (without Docker)

**Backend**

Requires PostgreSQL running on `localhost:5432`.

```bash
cd backend

# Using uv (recommended)
./start.sh

# Using pip
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**Frontend**

```bash
cd frontend
npm install
npm run dev       # http://localhost:3000
```

**Tests**

```bash
cd backend
python test_integration.py   # schema and structure tests
python test_api.py           # endpoint tests (uses SQLite)
```

**Python client example**

```bash
# Requires the backend to be running
python example_usage.py
```

## Detailed Documentation

- [Backend README](backend/README.md) — API reference, environment variables, local dev
- [Frontend README](frontend/README.md) — component overview, session persistence
