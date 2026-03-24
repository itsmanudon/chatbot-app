# Frontend

Next.js chat UI that connects to the FastAPI backend.

## Structure

```
frontend/
├── src/app/
│   ├── page.tsx      # Chat interface component (main UI)
│   ├── layout.tsx    # Root layout, metadata, and font loading
│   └── globals.css   # Tailwind CSS base imports
├── Dockerfile
├── next.config.ts    # Next.js configuration
├── package.json
└── tsconfig.json
```

## Component Overview

### `page.tsx` — Chat Interface

The single-page chat UI. Key responsibilities:

- **Session management** — reads/generates a UUID session ID from
  `localStorage` on first load so conversations persist across page refreshes.
- **Message list** — renders user and AI messages with distinct avatars and
  bubble styles.  Scrolls to the latest message automatically.
- **Typing indicator** — shows a spinner while waiting for the backend
  response.
- **API communication** — sends `POST /chat` requests via axios to
  `NEXT_PUBLIC_API_URL` and displays the `reply` field from the response.
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

The session ID is sent with every `POST /chat` request so the backend can
scope memory retrieval and storage to the correct conversation.

## Dependencies

| Package | Purpose |
|---|---|
| `next` | React framework with server-side rendering and routing |
| `react` / `react-dom` | UI library |
| `axios` | HTTP client for backend API calls |
| `tailwindcss` | Utility-first CSS framework |
| `lucide-react` | Icon library (Send, Bot, User, Loader2, Sparkles) |
| `clsx` + `tailwind-merge` | Conditional className composition |
