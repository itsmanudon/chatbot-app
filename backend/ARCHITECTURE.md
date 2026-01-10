# Architecture Documentation

## Overview

This chatbot application implements a **hybrid memory system** that combines:
- **PostgreSQL**: Structured data storage for chat history and memory contexts
- **Pinecone**: Vector database for semantic search and context retrieval
- **Multi-AI Provider Support**: OpenAI and Anthropic (Claude) with easy extensibility

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      Client Layer                        │
│                    (Frontend/API)                        │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                   FastAPI Backend                        │
│  ┌──────────────────────────────────────────────────┐  │
│  │              API Routes (main.py)                 │  │
│  │   /chat  /health  /memory  /session/:id/history  │  │
│  └───────────────────┬──────────────────────────────┘  │
│                      │                                   │
│  ┌───────────────────▼──────────────────────────────┐  │
│  │           Memory Engine (memory_engine.py)        │  │
│  │  • Hybrid retrieval (SQL + Vector)                │  │
│  │  • Context aggregation                            │  │
│  │  • Storage coordination                           │  │
│  └──┬──────────────────────────────────────────┬────┘  │
│     │                                           │        │
│  ┌──▼────────────┐                    ┌────────▼─────┐ │
│  │ LLM Adapter   │                    │ Vector Store │ │
│  │               │                    │              │ │
│  │ • OpenAI      │                    │ • Pinecone   │ │
│  │ • Anthropic   │                    │ • Embeddings │ │
│  └───────────────┘                    └──────────────┘ │
└─────────────┬──────────────────────────────────────────┘
              │
┌─────────────▼───────────────┐
│    Database (database.py)   │
│                             │
│  • ChatMessage model        │
│  • MemoryContext model      │
│  • SQLAlchemy ORM           │
└─────────────┬───────────────┘
              │
┌─────────────▼───────────────┐
│       PostgreSQL DB         │
│                             │
│  • Chat history             │
│  • Memory contexts          │
│  • Session data             │
└─────────────────────────────┘
```

## Component Details

### 1. FastAPI Application (main.py)

**Responsibility**: HTTP request handling and routing

**Key Endpoints**:
- `POST /chat`: Main conversation endpoint
  - Retrieves relevant context
  - Generates AI response
  - Stores conversation
  - Returns memory suggestions
- `GET /health`: Service health check
- `POST /memory`: Manual memory storage
- `GET /session/{id}/history`: Retrieve session history

**Features**:
- CORS middleware for frontend integration
- Database dependency injection
- Error handling and validation
- OpenAPI documentation

### 2. Memory Engine (memory_engine.py)

**Responsibility**: Hybrid memory management

**Core Functions**:

#### store_chat_message()
```python
# Stores message in both PostgreSQL and Pinecone
# Returns: chat_id
```

#### store_memory_context()
```python
# Stores structured memory (preferences, beliefs, decisions)
# Returns: memory_id
```

#### retrieve_relevant_context()
```python
# Hybrid retrieval strategy:
# 1. Vector search in Pinecone (semantic similarity)
# 2. Recent messages from PostgreSQL
# 3. High-confidence memories from PostgreSQL
# Returns: aggregated context string
```

**Design Pattern**: Facade pattern - provides simple interface to complex subsystems

### 3. LLM Adapter (llm_adapter.py)

**Responsibility**: Multi-provider AI integration

**Architecture**:
```
AIProvider (ABC)
    ├── OpenAIProvider
    │   └── Uses OpenAI API (gpt-3.5-turbo)
    └── AnthropicProvider
        └── Uses Anthropic API (claude-3-haiku)
```

**Key Features**:
- Abstract base class for easy provider addition
- Context injection
- Conversation history management
- Graceful fallback when API keys missing

**Design Pattern**: Strategy pattern - interchangeable AI providers

### 4. Vector Store (vector_store.py)

**Responsibility**: Semantic search using embeddings

**Components**:
- **Pinecone Client**: Vector database connection
- **Sentence Transformers**: Embedding generation (all-MiniLM-L6-v2)

**Operations**:
- `generate_embedding()`: Convert text to vector
- `store_embedding()`: Store vector with metadata
- `search_similar()`: Semantic similarity search

**Embedding Model**: all-MiniLM-L6-v2 (384 dimensions)
- Fast inference
- Good quality for chat use cases
- Can be swapped for other models

### 5. Database Layer (database.py)

**Responsibility**: PostgreSQL ORM and models

**Models**:

#### ChatMessage
```python
- id: Primary key
- session_id: User session identifier
- message: User message
- response: AI response
- timestamp: Message timestamp
- vector_id: Reference to Pinecone vector
```

#### MemoryContext
```python
- id: Primary key
- session_id: User session identifier
- content: Memory content
- memory_type: preference/belief/decision
- confidence: 0.0 to 1.0
- timestamp: Creation timestamp
- vector_id: Reference to Pinecone vector
```

**Design Pattern**: Active Record pattern via SQLAlchemy ORM

## Data Flow

### Chat Request Flow

1. **Request Arrives**: `POST /chat` with message and session_id
2. **Context Retrieval**: Memory engine queries:
   - Pinecone: Semantic similar conversations
   - PostgreSQL: Recent messages
   - PostgreSQL: High-confidence memories
3. **Context Aggregation**: Combine results into context string
4. **AI Generation**: LLM generates response with context
5. **Storage**: Store conversation in both databases:
   - PostgreSQL: Structured record
   - Pinecone: Vector embedding
6. **Response**: Return AI reply + memory suggestions

### Hybrid Retrieval Strategy

The system uses a **hybrid approach** for optimal context retrieval:

```
Query: "What programming languages should I learn?"

┌─────────────────────────────────────────────────┐
│         Pinecone Vector Search                   │
│  • Semantic similarity (cosine)                  │
│  • Finds conceptually related messages          │
│  • Returns: "You mentioned liking Python..."    │
└─────────────────────────────────────────────────┘
                      +
┌─────────────────────────────────────────────────┐
│         PostgreSQL Recent History                │
│  • Last N messages in session                    │
│  • Temporal context                              │
│  • Returns: Recent conversation flow             │
└─────────────────────────────────────────────────┘
                      +
┌─────────────────────────────────────────────────┐
│    PostgreSQL High-Confidence Memories           │
│  • Confidence > 0.7                              │
│  • Important user preferences                    │
│  • Returns: "User prefers backend dev"           │
└─────────────────────────────────────────────────┘
                      ↓
            Aggregated Context
                      ↓
                 LLM Provider
```

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| DATABASE_URL | Yes | - | PostgreSQL connection string |
| PINECONE_API_KEY | Optional | - | Pinecone API key |
| PINECONE_ENVIRONMENT | No | us-east-1 | Pinecone region |
| PINECONE_INDEX_NAME | No | chatbot-memory | Index name |
| OPENAI_API_KEY | Optional* | - | OpenAI API key |
| ANTHROPIC_API_KEY | Optional* | - | Anthropic API key |
| DEFAULT_AI_PROVIDER | No | openai | Default provider |
| EMBEDDING_MODEL | No | all-MiniLM-L6-v2 | Sentence transformer model |

*At least one AI provider key required

## Minimalist Design Principles

This implementation follows minimalist principles:

1. **Single Responsibility**: Each module has one clear purpose
2. **No Over-Engineering**: Only necessary abstractions
3. **Graceful Degradation**: Works without optional services (Pinecone)
4. **Clear Interfaces**: Simple, intuitive APIs
5. **Explicit Configuration**: Environment-based, no magic
6. **Minimal Dependencies**: Only essential packages

## Extending the System

### Adding a New AI Provider

1. Create new class inheriting from `AIProvider`
2. Implement `generate_response()` method
3. Register in `LLMAdapter.providers`

Example:
```python
class CohereProvider(AIProvider):
    def generate_response(self, messages, context=""):
        # Implementation
        pass

# In LLMAdapter.__init__:
self.providers["cohere"] = CohereProvider()
```

### Adding New Memory Types

1. Update schemas.py if needed
2. Store via `memory_engine.store_memory_context()`
3. Query pattern already handles any type

### Custom Embedding Models

Change `EMBEDDING_MODEL` environment variable to any Sentence Transformers model:
- `all-mpnet-base-v2`: Better quality, slower
- `all-distilroberta-v1`: Good balance
- `paraphrase-MiniLM-L6-v2`: Paraphrase detection

## Performance Considerations

- **Embedding Generation**: ~10-50ms per text
- **Vector Search**: <100ms for millions of vectors
- **PostgreSQL Queries**: <10ms for indexed lookups
- **LLM API Calls**: 500-2000ms (varies by provider)

**Bottleneck**: LLM API calls (can be optimized with streaming)

## Security Considerations

- API keys stored in environment variables (never in code)
- Database connection strings in secure env vars
- No sensitive data in vector metadata
- CORS configured for production deployment

## Future Enhancements

- [ ] Response streaming for better UX
- [ ] Batch embedding generation
- [ ] Redis caching layer
- [ ] User authentication/authorization
- [ ] Rate limiting
- [ ] Conversation branching
- [ ] Memory importance scoring
- [ ] Automatic memory consolidation
