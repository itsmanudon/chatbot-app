# Frontend

Next.js chat UI that connects to the FastAPI backend.

## Structure

```
frontend/
├── src/app/
│   ├── page.tsx      # Chat interface
│   ├── layout.tsx    # Root layout and metadata
│   └── globals.css   # Tailwind CSS imports
├── Dockerfile
├── package.json
└── next.config.ts
```

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Backend API URL |

When running via Docker this is set automatically in `docker-compose.yml`. For local dev, create a `.env.local` file:

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

Each browser generates a UUID session ID on first load, stored in `localStorage`. This means:
- Conversation history persists across page refreshes
- Different browsers/devices get independent sessions
- Clearing `localStorage` starts a fresh session
