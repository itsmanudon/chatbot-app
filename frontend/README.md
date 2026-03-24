# Frontend

Next.js chat UI that connects to the FastAPI backend.

## Structure

```
frontend/
├── src/app/
│   ├── page.tsx      # Chat interface component (main UI with sidebar)
│   ├── layout.tsx    # Root layout, metadata, and font loading
│   └── globals.css   # Tailwind CSS base imports
├── Dockerfile
├── next.config.ts    # Next.js configuration
├── package.json
└── tsconfig.json
```

## Component Overview

### `page.tsx` — Chat Interface

The single-page chat UI with an ai-webui–style layout. Key responsibilities:

- **Sidebar** — collapsible left panel listing all past chat sessions (fetched
  from `GET /sessions`).  Each entry shows the session title (first message),
  a response preview, and the relative timestamp.  Clicking an entry loads its
  full history.  A trash icon (visible on hover) deletes the session via
  `DELETE /session/{id}`.
- **New Chat button** — creates a fresh UUID session and clears the active
  chat area.
- **Session switching** — clicking a session in the sidebar loads its complete
  interleaved history from `GET /session/{id}/history` and displays it in the
  main chat area.
- **Session management** — reads/generates a UUID session ID from
  `localStorage` (`chat_session_id`) so the active session persists across
  page refreshes.
- **Message list** — renders user and AI messages with distinct avatars and
  bubble styles.  Scrolls to the latest message automatically.
- **Typing indicator** — shows a spinner while waiting for the backend
  response.
- **API communication** — sends `POST /chat` requests via axios to
  `NEXT_PUBLIC_API_URL` and displays the `reply` field from the response.
  Refreshes the sidebar session list after each successful exchange.
- **Error handling** — shows a user-friendly error message if the backend is
  unreachable.

### `layout.tsx` — Root Layout

Sets page metadata (title, description) and loads the Geist Sans and Geist
Mono fonts from Google Fonts.

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Backend API base URL |

When running via Docker Compose, this is set automatically in
`docker-compose.yml`.  For local development, create a `.env.local` file:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Running Locally (without Docker)

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000.

## Session Persistence

Each browser generates a UUID session ID on first load, stored in
`localStorage` under the key `chat_session_id`.  This means:

- Conversation history persists across page refreshes.
- Different browsers and devices get independent sessions.
- Clearing `localStorage` (or opening a private/incognito window) starts a
  fresh session.
- Switching sessions in the sidebar updates `localStorage` so the active
  session is remembered on next page load.

The session ID is sent with every `POST /chat` request so the backend can
scope memory retrieval and storage to the correct conversation.

## Chat History Feature

All conversations are stored in PostgreSQL.  The sidebar loads the sessions
list on mount and after each message exchange.  When a session is selected:

1. `GET /session/{id}/history` returns the full interleaved conversation.
2. The UI replaces the current message list with the loaded history.
3. Sending a new message in this session appends to the existing history.

## Dependencies

| Package | Purpose |
|---|---|
| `next` | React framework with server-side rendering and routing |
| `react` / `react-dom` | UI library |
| `axios` | HTTP client for backend API calls |
| `tailwindcss` | Utility-first CSS framework |
| `lucide-react` | Icon library (Send, Bot, User, Loader2, Sparkles, PlusCircle, MessageSquare, Trash2, Menu, X) |
| `clsx` + `tailwind-merge` | Conditional className composition |

