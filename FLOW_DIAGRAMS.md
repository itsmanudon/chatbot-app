# System Flow Diagrams

## Chat Request Flow

```
┌─────────────┐
│   Client    │
│  (Frontend) │
└──────┬──────┘
       │
       │ POST /chat
       │ { message, session_id }
       │
┌──────▼────────────────────────────────────────────────┐
│                  FastAPI Backend                       │
│                                                        │
│  ┌────────────────────────────────────────────────┐  │
│  │          1. Receive Request                     │  │
│  │             (main.py /chat endpoint)            │  │
│  └────────────────┬───────────────────────────────┘  │
│                   │                                    │
│  ┌────────────────▼───────────────────────────────┐  │
│  │     2. Retrieve Context (memory_engine.py)     │  │
│  │                                                 │  │
│  │  ┌──────────────────────────────────────────┐ │  │
│  │  │ a) Vector Search (Pinecone)              │ │  │
│  │  │    • Semantic similarity                 │ │  │
│  │  │    • Top K similar conversations         │ │  │
│  │  └──────────────────────────────────────────┘ │  │
│  │  ┌──────────────────────────────────────────┐ │  │
│  │  │ b) Recent Messages (PostgreSQL)          │ │  │
│  │  │    • Last N messages in session          │ │  │
│  │  └──────────────────────────────────────────┘ │  │
│  │  ┌──────────────────────────────────────────┐ │  │
│  │  │ c) High-Confidence Memories (PostgreSQL) │ │  │
│  │  │    • Confidence > 0.7                    │ │  │
│  │  └──────────────────────────────────────────┘ │  │
│  │                                                 │  │
│  │  Result: Aggregated context string             │  │
│  └────────────────┬───────────────────────────────┘  │
│                   │                                    │
│  ┌────────────────▼───────────────────────────────┐  │
│  │      3. Generate AI Response (llm_adapter.py)  │  │
│  │                                                 │  │
│  │  Context + Message → OpenAI/Anthropic → Reply  │  │
│  └────────────────┬───────────────────────────────┘  │
│                   │                                    │
│  ┌────────────────▼───────────────────────────────┐  │
│  │    4. Store Conversation (memory_engine.py)    │  │
│  │                                                 │  │
│  │  ┌──────────────────────────────────────────┐ │  │
│  │  │ a) Generate embedding (vector_store.py)  │ │  │
│  │  └──────────────────────────────────────────┘ │  │
│  │  ┌──────────────────────────────────────────┐ │  │
│  │  │ b) Store in Pinecone                     │ │  │
│  │  │    • Vector + metadata                   │ │  │
│  │  └──────────────────────────────────────────┘ │  │
│  │  ┌──────────────────────────────────────────┐ │  │
│  │  │ c) Store in PostgreSQL                   │ │  │
│  │  │    • Structured record                   │ │  │
│  │  └──────────────────────────────────────────┘ │  │
│  └────────────────┬───────────────────────────────┘  │
│                   │                                    │
│  ┌────────────────▼───────────────────────────────┐  │
│  │    5. Return Response                          │  │
│  │       { reply, memory_suggestions }            │  │
│  └────────────────────────────────────────────────┘  │
└───────────────────┬────────────────────────────────┬─┘
                    │                                │
         ┌──────────▼──────────┐        ┌───────────▼──────────┐
         │    PostgreSQL        │        │      Pinecone        │
         │                      │        │                      │
         │  • Chat history      │        │  • Embeddings        │
         │  • Memories          │        │  • Semantic search   │
         │  • Metadata          │        │                      │
         └──────────────────────┘        └──────────────────────┘
```

## Component Interaction

```
┌────────────────────────────────────────────────────────────┐
│                        main.py                              │
│                     (FastAPI App)                           │
│                                                             │
│  • Routes: /chat, /health, /memory, /session/:id/history   │
│  • CORS middleware                                          │
│  • Dependency injection                                     │
└──────┬──────────────────┬────────────────┬─────────────────┘
       │                  │                │
       │                  │                │
┌──────▼──────┐   ┌───────▼───────┐   ┌───▼────────────────┐
│ schemas.py  │   │ database.py   │   │ memory_engine.py   │
│             │   │               │   │                    │
│ • Request   │   │ • Models      │   │ • Hybrid retrieval │
│ • Response  │   │ • Connection  │   │ • Store/retrieve   │
│ • Validation│   │ • init_db()   │   │ • Context agg.     │
└─────────────┘   └───────┬───────┘   └───┬────────────────┘
                          │               │
                          │               │
                  ┌───────▼───────────────▼────┐
                  │    PostgreSQL Database      │
                  │                             │
                  │  • chat_messages            │
                  │  • memory_contexts          │
                  └─────────────────────────────┘

       ┌──────────────────────┐    ┌─────────────────────┐
       │   llm_adapter.py     │    │  vector_store.py    │
       │                      │    │                     │
       │  • AIProvider (ABC)  │    │  • Pinecone client  │
       │  • OpenAIProvider    │    │  • Embeddings       │
       │  • AnthropicProvider │    │  • Search           │
       └──────────────────────┘    └─────────┬───────────┘
                                              │
                                   ┌──────────▼──────────┐
                                   │  Pinecone VectorDB  │
                                   │                     │
                                   │  • 384-dim vectors  │
                                   │  • Cosine similarity│
                                   └─────────────────────┘
```

## Memory Storage Flow

```
User Message
     │
     ▼
┌─────────────────────────────────┐
│  memory_engine.store_chat_message │
└────────┬────────────────────────┘
         │
         ├─────────────────┬──────────────────┐
         │                 │                  │
         ▼                 ▼                  ▼
┌─────────────────┐  ┌──────────────┐  ┌──────────────┐
│ Generate UUID   │  │ Create       │  │ Generate     │
│ for message     │  │ embedding    │  │ metadata     │
└────────┬────────┘  └──────┬───────┘  └──────┬───────┘
         │                  │                  │
         └──────────────────┼──────────────────┘
                            │
         ┌──────────────────┴──────────────────┐
         │                                     │
         ▼                                     ▼
┌───────────────────┐              ┌──────────────────┐
│  PostgreSQL       │              │  Pinecone        │
│                   │              │                  │
│  INSERT INTO      │              │  upsert([        │
│  chat_messages    │              │    id,           │
│  (id, session_id, │              │    embedding,    │
│   message,        │              │    metadata      │
│   response,       │              │  ])              │
│   timestamp,      │              │                  │
│   vector_id)      │              │                  │
└───────────────────┘              └──────────────────┘
```

## Hybrid Context Retrieval

```
User Query: "What should I learn next?"
     │
     ▼
┌──────────────────────────────────────────────┐
│ memory_engine.retrieve_relevant_context()    │
└──────────┬───────────────────────────────────┘
           │
    ┌──────┴───────┬──────────────┐
    │              │              │
    ▼              ▼              ▼
┌─────────┐  ┌──────────┐  ┌─────────────┐
│ Vector  │  │ Recent   │  │ High-Conf   │
│ Search  │  │ Messages │  │ Memories    │
└────┬────┘  └────┬─────┘  └──────┬──────┘
     │            │               │
     │            │               │
     └────────────┼───────────────┘
                  │
                  ▼
         ┌────────────────┐
         │ Aggregate &    │
         │ Format Context │
         └────────┬───────┘
                  │
                  ▼
    "Recent: You want to learn Python
     Memory: You prefer hands-on projects
     Previous: You built a REST API"
                  │
                  ▼
           ┌──────────────┐
           │ LLM Provider │
           └──────────────┘
```

## AI Provider Selection

```
Chat Request
     │
     ▼
┌──────────────────────────┐
│ llm_adapter.get_response │
└──────────┬───────────────┘
           │
           ▼
┌──────────────────────────┐
│ Check DEFAULT_AI_PROVIDER│
│ (from environment)       │
└──────────┬───────────────┘
           │
    ┌──────┴──────┐
    │             │
    ▼             ▼
┌─────────┐  ┌──────────┐
│ openai  │  │anthropic │
└────┬────┘  └────┬─────┘
     │            │
     ▼            ▼
┌──────────┐  ┌────────────┐
│ OpenAI   │  │ Anthropic  │
│ API      │  │ API        │
│          │  │            │
│ gpt-3.5- │  │ claude-3-  │
│ turbo    │  │ haiku      │
└──────────┘  └────────────┘
```

## Error Handling Flow

```
Request → Validation → DB Check → AI Check → Process
   │         │            │           │          │
   ▼         ▼            ▼           ▼          ▼
 422       422          500         500        200
Invalid  Validation   Database    AI API      Success
Request    Error       Error      Error
```
