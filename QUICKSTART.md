# Quick Start Guide

Get the NCAA Bracket Tracker running in 5 minutes.

## Prerequisites

- Docker & Docker Compose installed
- Node.js 18+ and pnpm installed (for frontend)

## Start Backend (30 seconds)

```bash
# Start services
make up

# Wait for services to be healthy (check with docker-compose ps)
# Then seed the database
make seed
```

✅ Backend running at http://localhost:8000
✅ API docs at http://localhost:8000/docs

## Start Frontend (30 seconds)

```bash
# In a new terminal
cd frontend
pnpm install
pnpm dev
```

✅ Frontend running at http://localhost:3000

## What You'll See

Open http://localhost:3000 in your browser:

- **Bracket visualization** with 4 sample games
  - Color-coded results: 🟢 Correct pick, 🔴 Incorrect pick, 🟡 In-progress
  - "Court-Side Drama" aesthetic with arena lighting effects
  - Team seeds, names, and scores

- **Score card** showing:
  - Total points earned
  - Pick accuracy percentage
  - Bracket health meter
  - Breakdown of correct/incorrect picks

- **Sample data included:**
  - Duke vs Hampton (completed, correct pick) ✅
  - Memphis vs Missouri (upset! incorrect pick) ❌
  - Kansas vs Iona (in-progress) 🟡
  - Gonzaga vs Norfolk State (scheduled) ⏰

## Test the API

```bash
# Get brackets
curl http://localhost:8000/api/v1/brackets

# Get games with scores
curl http://localhost:8000/api/v1/games

# Get bracket score
curl http://localhost:8000/api/v1/scores/1

# Trigger ESPN sync (requires live games)
curl -X POST http://localhost:8000/api/v1/sync
```

## Optional: WhatsApp Notifications

Edit `backend/.env` with your OpenClaw credentials:

```env
OPENCLAW_API_URL=https://your-instance.com/api/send
OPENCLAW_API_TOKEN=your_token
WHATSAPP_NOTIFICATION_NUMBER=+1234567890
```

Then test:

```bash
curl -X POST http://localhost:8000/api/v1/notify
```

## Troubleshooting

**Port conflicts?**
```bash
# Edit docker-compose.yml and change ports
# Then: make down && make up
```

**Database issues?**
```bash
make clean  # Removes all data
make up
make seed
```

**Frontend won't connect?**
- Check backend is running: `curl http://localhost:8000/health`
- Verify CORS settings in `backend/app/config.py`

## Next Steps

1. Explore the API at http://localhost:8000/docs
2. Modify sample data in `backend/scripts/seed_data.py`
3. Customize frontend colors/styles in `frontend/src/components/`
4. Add more teams and games to test full bracket

See [README.md](README.md) for full documentation.
