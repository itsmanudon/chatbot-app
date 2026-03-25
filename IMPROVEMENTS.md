# Chatbot App — Improvement Tracker

Tracks all planned robustness improvements. Updated as each item is implemented.

---

## Status Legend
- `[ ]` Not started
- `[~]` In progress
- `[x]` Done

---

## Critical

| # | Task | Status | Notes |
|---|------|--------|-------|
| C1 | ~~API Keys in Git~~ | `[x]` | Verified — `.env` files are in `.gitignore`, not committed |
| C2 | CORS lockdown — restrict `allow_origins` from `*` to explicit domain | `[x]` | `ALLOWED_ORIGINS` env var, defaults to `localhost:3000` |
| C3 | Rate limiting on `/chat` endpoint (protect against LLM credit drain) | `[x]` | `slowapi` — 20 req/min per IP |

---

## High Impact

| # | Task | Status | Notes |
|---|------|--------|-------|
| H1 | Structured logging — replace all `print()` with Python `logging` module | `[x]` | `logging_config.py`, request latency middleware, `LOG_LEVEL` env var |
| H2 | Input validation — max message length + request body size limit | `[x]` | `Field(max_length=4000)` in schema, 32 KB body limit middleware |
| H3 | Database migrations with Alembic | `[x]` | `migrations/` scaffold + initial migration `0001` |
| H4 | Frontend error visibility — replace silent failures with toast notifications | `[x]` | In-file `ToastContainer`, covers sessions/history/delete/chat failures |

---

## Robustness & Reliability

| # | Task | Status | Notes |
|---|------|--------|-------|
| R1 | Retry logic for Pinecone + OpenAI calls using `tenacity` | `[x]` | 3 attempts, exponential backoff 1–10s on LLM + vector store calls |
| R2 | SQLAlchemy connection pool tuning + `pool_pre_ping=True` | `[x]` | `pool_size=5`, `max_overflow=10`, `pool_pre_ping=True` |
| R3 | Axios request timeout on frontend (30s) | `[x]` | 30s on `/chat`, 10s on all other calls |
| R4 | Graceful shutdown signal handling in FastAPI | `[x]` | Replaced `@on_event` with `lifespan` context manager; `engine.dispose()` on shutdown |
| R5 | Environment variable validation at startup (fail-fast) | `[x]` | Raises `RuntimeError` if `DATABASE_URL` or both AI keys are missing |

---

## Developer Experience & Maintainability

| # | Task | Status | Notes |
|---|------|--------|-------|
| D1 | GitHub Actions CI pipeline — run backend tests on every PR | `[x]` | `.github/workflows/ci.yml` — backend tests + frontend lint + frontend tests |
| D2 | Pre-commit hooks — `ruff`, `black`, `mypy` for backend | `[x]` | `.pre-commit-config.yaml` — black, ruff, prettier, general hygiene hooks |
| D3 | Frontend tests — Playwright or Vitest for core chat flow | `[x]` | `vitest` + `@testing-library/react` — 3 tests covering welcome msg, send/reply, error toast |

---

## Nice to Have (Long Term)

| # | Task | Status | Notes |
|---|------|--------|-------|
| N1 | Prometheus + Grafana observability stack via docker-compose | `[ ]` | |
| N2 | JWT-based authentication (multi-user support) | `[ ]` | |
| N3 | Streaming LLM responses via SSE/WebSockets | `[ ]` | |
| N4 | LLM-based memory extraction (replace keyword detection) | `[ ]` | |
| N5 | Composite DB index on `(session_id, created_at)` | `[ ]` | |

---

## Implementation Order

Critical → High Impact → Robustness → Dev Experience → Nice to Have

1. C2 — CORS lockdown
2. C3 — Rate limiting
3. H1 — Structured logging
4. H2 — Input validation
5. H3 — Alembic migrations
6. H4 — Frontend error toasts
7. R1 — Retry logic
8. R2 — DB connection pool
9. R3 — Axios timeout
10. R4 — Graceful shutdown
11. R5 — Env var validation at startup
12. D1 — GitHub Actions CI
13. D2 — Pre-commit hooks
14. D3 — Frontend tests
