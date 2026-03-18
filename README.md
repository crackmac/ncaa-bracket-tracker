# NCAA Bracket Tracker - Vertical Slice Prototype

A real-time NCAA March Madness bracket tracking system with live scoring, ESPN API integration, and WhatsApp notifications via OpenClaw.

## Architecture

```
ESPN API → FastAPI Backend → PostgreSQL → Scoring Engine → React Frontend
                ↓
         OpenClaw WhatsApp
```

## Tech Stack

**Backend:**
- FastAPI (Python 3.11+)
- PostgreSQL 15
- SQLAlchemy 2.0 + Alembic
- httpx for async HTTP requests
- uvicorn for ASGI server

**Frontend:**
- React 18 + TypeScript
- Vite
- Tailwind CSS 4.0 (alpha)
- Custom bracket visualization with "Court-Side Drama" aesthetic

**Infrastructure:**
- Docker Compose
- Nginx (reverse proxy)

## Project Structure

```
ncaa-bracket-tracker/
├── backend/
│   ├── alembic/              # Database migrations
│   ├── app/
│   │   ├── api/v1/           # REST API endpoints
│   │   ├── db/               # Database models
│   │   └── services/         # Business logic
│   ├── scripts/              # Utility scripts
│   └── pyproject.toml        # Python dependencies (uv)
├── frontend/
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── hooks/            # Custom hooks
│   │   └── api/              # API client
│   └── package.json          # Node dependencies (pnpm)
├── docker-compose.yml
└── README.md
```

## Setup Instructions

### Prerequisites

- Docker & Docker Compose
- Node.js 18+ (for local frontend development)
- pnpm (for frontend dependencies)

### 1. Clone and Configure

```bash
# Create environment file
cp backend/.env.example backend/.env

# Edit backend/.env with your OpenClaw credentials (optional for basic testing)
```

### 2. Start Backend Services

```bash
# Start PostgreSQL and FastAPI backend
docker-compose up -d

# Check services are running
docker-compose ps

# View logs
docker-compose logs -f backend
```

The backend API will be available at: http://localhost:8000

API docs (Swagger): http://localhost:8000/docs

### 3. Seed Database

```bash
# Run seed script inside the backend container
docker-compose exec backend python scripts/seed_data.py
```

This creates:
- 1 demo user
- 2026 tournament
- 8 teams (East and West regions)
- 4 games (2 completed, 1 in-progress, 1 scheduled)
- 1 sample bracket with picks

### 4. Start Frontend

```bash
cd frontend

# Install dependencies
pnpm install

# Start dev server
pnpm dev
```

Frontend will be available at: http://localhost:3000

## Testing the Vertical Slice

### Manual Testing Checklist

1. **Backend Health Check**
   ```bash
   curl http://localhost:8000/health
   # Should return: {"status":"healthy","app":"NCAA Bracket Tracker"}
   ```

2. **List Brackets**
   ```bash
   curl http://localhost:8000/api/v1/brackets
   # Should return array with "Championship Run" bracket
   ```

3. **Get Bracket Details**
   ```bash
   curl http://localhost:8000/api/v1/brackets/1
   # Should return bracket with picks
   ```

4. **List Games**
   ```bash
   curl http://localhost:8000/api/v1/games
   # Should return 4 games with scores and status
   ```

5. **Get Bracket Score**
   ```bash
   curl http://localhost:8000/api/v1/scores/1
   # Should show points earned and pick accuracy
   ```

6. **Frontend Visualization**
   - Open http://localhost:3000
   - Should see "March Madness 2026" bracket
   - Games color-coded: Green (correct), Red (incorrect), Yellow (in-progress)
   - Score card showing 10 points, 1/2 correct picks
   - Click "Switch to Live Data" to test empty state

### ESPN API Sync Test

```bash
# Manually trigger ESPN data sync
curl -X POST http://localhost:8000/api/v1/sync

# Note: This will attempt to fetch live data from ESPN API
# May return 0 games_updated if no matching games found
```

### WhatsApp Notification Test

Configure OpenClaw credentials in `backend/.env`:

```env
OPENCLAW_API_URL=https://your-openclaw-instance.com/api/send
OPENCLAW_API_TOKEN=your_token_here
WHATSAPP_NOTIFICATION_NUMBER=+1234567890
```

Then test notification:

```bash
curl -X POST http://localhost:8000/api/v1/notify
# Check your WhatsApp for test message
```

## API Endpoints

### Brackets
- `GET /api/v1/brackets` - List all brackets
- `GET /api/v1/brackets/{id}` - Get bracket details with picks

### Games
- `GET /api/v1/games` - List all games with scores

### Scores
- `GET /api/v1/scores/{bracket_id}` - Get bracket score
- `GET /api/v1/scores/{bracket_id}/health` - Get bracket health metrics

### Sync
- `POST /api/v1/sync` - Manually trigger ESPN data sync

### Notifications
- `POST /api/v1/notify` - Send test WhatsApp notification
- `POST /api/v1/notify/bracket/{bracket_id}` - Send bracket score update

## Scoring Rules (ESPN Tournament Challenge)

| Round | Points per Correct Pick |
|-------|-------------------------|
| Round 64 | 10 |
| Round 32 | 20 |
| Sweet 16 | 40 |
| Elite 8 | 80 |
| Final Four | 160 |
| Championship | 320 |

**Upset Detection:** Automatically flags games where a lower-seeded team (higher number) defeats a higher-seeded team.

## Development

### Backend

```bash
# Run tests (when implemented)
docker-compose exec backend pytest

# Format code
docker-compose exec backend ruff format .

# Lint code
docker-compose exec backend ruff check .

# Create new migration
docker-compose exec backend alembic revision --autogenerate -m "description"

# Run migrations
docker-compose exec backend alembic upgrade head
```

### Frontend

```bash
cd frontend

# Type check
pnpm tsc

# Lint
pnpm lint

# Build for production
pnpm build
```

## Troubleshooting

### Database Connection Issues

```bash
# Reset database
docker-compose down -v
docker-compose up -d
docker-compose exec backend python scripts/seed_data.py
```

### Frontend Not Connecting to Backend

Check CORS settings in `backend/app/config.py`. For local development:

```python
cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]
```

### Port Conflicts

If ports are already in use:

```bash
# Edit docker-compose.yml and change port mappings:
# PostgreSQL: 5432 -> 5433
# Backend: 8000 -> 8001
# Nginx: 80 -> 8080
```

## Next Steps

After validating this vertical slice:

1. ✅ Expand to full 64-team bracket
2. ✅ Add remaining regions (South, Midwest)
3. ✅ Add bracket input UI
4. ✅ Implement automated polling (Celery + Redis)
5. ✅ Add more notification types
6. ✅ Add unit and integration tests
7. ✅ Improve error handling and logging

## License

MIT
