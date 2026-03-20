# AI Chatbot with Hybrid Memory

A full-stack AI chatbot that remembers conversations using a hybrid memory system — PostgreSQL for structured storage and Pinecone for semantic vector search.

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 16, React 19, Tailwind CSS |
| Backend | FastAPI, Python 3.12 |
| Database | PostgreSQL 16 |
| Vector Store | Pinecone |
| AI Providers | OpenAI (default) or Anthropic |

## Project Structure

```
chatbot-app/
├── backend/            # FastAPI application
├── frontend/           # Next.js application
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

Edit `backend/.env` and add your API keys.

**3. Start everything**

```bash
docker-compose up --build
```

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |

## Architecture

```
┌─────────────┐
│   Frontend  │  (Next.js — browser)
└──────┬──────┘
       │ HTTP
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

For detailed backend docs see [backend/README.md](backend/README.md).
For frontend docs see [frontend/README.md](frontend/README.md).
