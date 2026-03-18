# NCAA Bracket Tracker - Production Expansion Design

**Date:** March 18, 2026
**Status:** Approved
**Implementation Approach:** Vertical Expansion (3 Phases)

---

## Executive Summary

This design expands the NCAA Bracket Tracker from a 4-game vertical slice to a production-ready system supporting full 64-team tournament brackets with automated polling and bracket input capabilities. The system will be tested with smaller tournaments this season before March Madness 2027.

**Key Decisions:**
- Deferred: Multi-bracket comparison view (future version)
- Deployment: Docker Compose on Mac Mini (no cloud infrastructure)
- Polling: Every 5-10 minutes during tournaments
- Notifications: Game start, halftime, final + upsets
- Testing: Unit and integration tests written as we go

---

## Current State

**Vertical Slice (Completed):**
- 4 games across 2 regions (East, West)
- ESPN API integration with caching
- Scoring engine with ESPN Tournament Challenge rules
- WhatsApp notifications via OpenClaw
- React frontend with "Court-Side Drama" aesthetic
- Database schema supports multiple brackets (used by single bracket)

**Code Stats:**
- Backend: ~900 lines (FastAPI, SQLAlchemy, Alembic)
- Frontend: ~500 lines (React, TypeScript, Tailwind CSS)
- Database: 6 models (User, Tournament, Team, Game, Bracket, Pick)

---

## Architecture Overview

### Data Flow
```
Tournament YAML → Database → ESPN Sync (Celery) → Score Calculation → Frontend Display
                                    ↓
                              WhatsApp Notifications
```

### Component Structure
```
backend/
  data/
    tournaments/        # YAML tournament configs
  scripts/
    load_tournament.py  # Import YAML to DB
  app/
    tasks/             # Celery tasks (polling, notifications)
    services/          # Existing: ESPN, scoring, notifier
    api/v1/            # REST endpoints
  tests/               # pytest test suite

frontend/
  src/
    pages/             # Index, Create, Detail
    components/
      Bracket/         # Existing visualization
      BracketPicker/   # New interactive picker
```

---

## Phase 1: Foundation (Full 64-Team Structure)

**Goal:** Complete tournament data model and brackets navigation.

### 1.1 Tournament Configuration Format

**File:** `backend/data/tournaments/2026.yaml`

```yaml
tournament:
  year: 2026
  name: "NCAA March Madness 2026"
  start_date: "2026-03-17"
  end_date: "2026-04-06"

regions:
  - name: "East"
    teams:
      - name: "Duke"
        seed: 1
        espn_id: "duke_001"
      - name: "Hampton"
        seed: 16
        espn_id: "hampton_016"
      # ... 14 more teams (seeds 2-15)

  - name: "West"
    teams:
      # ... 16 teams

  - name: "South"
    teams:
      # ... 16 teams

  - name: "Midwest"
    teams:
      # ... 16 teams

matchups:
  round_64:
    - region: "East"
      game_id: "game_001"
      home_seed: 1
      away_seed: 16
    - region: "East"
      game_id: "game_002"
      home_seed: 8
      away_seed: 9
    # ... 30 more Round 64 games (32 total)
```

**Design Notes:**
- Only Round 64 matchups are predefined (32 games)
- Subsequent rounds populate as winners are determined
- ESPN IDs can be looked up from ESPN API during tournament
- Template file provided for manual editing each year

### 1.2 Tournament Loader

**File:** `backend/scripts/load_tournament.py`

**Functionality:**
1. Parse YAML file (use PyYAML)
2. Create or update `Tournament` record
3. Create `Team` records (64 teams)
4. Create `Game` records for Round 64 (32 games, status="scheduled")
5. Skip if tournament already exists (idempotent)

**Validation:**
- Exactly 64 teams (16 per region)
- Seeds 1-16 in each region
- 32 Round 64 matchups (1v16, 2v15, 3v14, etc.)

**CLI Usage:**
```bash
python scripts/load_tournament.py data/tournaments/2026.yaml
```

### 1.3 Brackets Index Page

**File:** `frontend/src/pages/BracketsIndex.tsx`

**Features:**
- Table view of all brackets
- Columns:
  - Bracket Name (clickable link to detail)
  - Owner (user name)
  - Current Points
  - Predicted Champion (team picked to win Championship game)
  - Actions (View Details button)
- Empty state: "No brackets yet" message
- Responsive table (stacks on mobile)

**API Endpoint:** `GET /api/v1/brackets` (already exists)

**Routing:**
- `/` → BracketsIndex
- `/brackets/:id` → BracketDetail (existing Bracket component)

### 1.4 Database Changes

**No schema changes needed** - existing models already support:
- Multiple regions (Team.region field)
- All 64 teams
- All 63 games (Game model)
- Multiple brackets (Bracket model)

**Data changes only:**
- Expand from 4 games → 32 Round 64 games
- Expand from 8 teams → 64 teams
- Add South and Midwest regions

### 1.5 Testing

**Unit Tests:**
- `test_tournament_loader.py`:
  - Parse valid YAML
  - Reject invalid YAML (wrong team count, invalid seeds)
  - Idempotency (load same tournament twice)

**Integration Tests:**
- Load tournament YAML → verify 64 teams in database
- Load tournament YAML → verify 32 Round 64 games
- API: GET /brackets returns multiple brackets

**Manual Tests:**
- Run loader script with 2026.yaml
- View brackets index page with multiple brackets
- Click through to bracket detail

---

## Phase 2: Input & Automation

**Goal:** Enable bracket creation and automated ESPN polling.

### 2.1 Bracket Creation - Web Form

**File:** `frontend/src/pages/BracketCreate.tsx`

**Features:**
- Two tabs: "Interactive Picker" and "Upload File"
- Form fields:
  - Bracket name (required, text input)
  - Bracket type (dropdown: Chalk, Balanced, Chaos, Custom)
- Submit button creates bracket + 63 picks

**Interactive Picker Component:**

**File:** `frontend/src/components/Bracket/BracketPicker.tsx`

**UI Flow:**
1. Display all Round 64 matchups (32 games)
2. User clicks team to pick as winner
3. Winning teams advance to Round 32 → user picks again
4. Repeat through Sweet 16, Elite 8, Final Four, Championship
5. Visual bracket tree updates as picks are made
6. Validation: All 63 games must have a pick

**Design:**
- Similar aesthetic to existing Bracket component
- Clickable team cards (hover state, selected state)
- Disabled games until previous round is complete
- Progress indicator: "32/63 picks completed"

**API Endpoint:**
```
POST /api/v1/brackets
{
  "name": "My Chalk Bracket",
  "bracket_type": "chalk",
  "picks": [
    {"game_id": "game_001", "predicted_winner_id": 1},
    // ... 62 more picks
  ]
}
```

**Backend Validation:**
- All 63 games have picks
- Predicted winners form valid bracket tree (no orphan teams)
- Predicted winner IDs exist in database

### 2.2 Bracket Import - File Upload

**File Upload UI:**
- File input accepting `.json`, `.yaml`, `.yml`
- Drag-and-drop zone
- Preview parsed data before submit
- Error messages for invalid files

**File Format:**
```yaml
bracket:
  name: "My Balanced Bracket"
  type: "balanced"
  picks:
    - game_id: "game_001"
      winner: "Duke"  # or team ID
    - game_id: "game_002"
      winner: "Missouri"
    # ... 61 more picks
```

**Backend Endpoint:**
```
POST /api/v1/brackets/import
Content-Type: multipart/form-data

{
  "file": <uploaded file>
}
```

**Implementation:**
- Parse JSON/YAML
- Resolve team names to IDs
- Validate bracket tree structure
- Create Bracket + Pick records
- Return bracket ID or validation errors

### 2.3 Automated ESPN Polling

**New Services:**

**Docker Compose Changes:**
```yaml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  celery-beat:
    build:
      context: .
      dockerfile: Dockerfile.backend
    command: celery -A app.celery_app beat --loglevel=info
    depends_on:
      - redis
      - db
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - CELERY_BROKER_URL=redis://redis:6379/0

  celery-worker:
    build:
      context: .
      dockerfile: Dockerfile.backend
    command: celery -A app.celery_app worker --loglevel=info
    depends_on:
      - redis
      - db
```

**File:** `backend/app/celery_app.py`
```python
from celery import Celery
from celery.schedules import crontab

celery = Celery('bracket_tracker')
celery.config_from_object('app.celeryconfig')

@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Poll every 5 minutes during tournament
    sender.add_periodic_task(
        300.0,  # 5 minutes
        poll_espn_scores.s(),
    )
```

**File:** `backend/app/tasks/polling.py`
```python
from app.celery_app import celery
from app.services.espn_client import espn_client
from app.db.session import SessionLocal
from datetime import datetime

@celery.task
def poll_espn_scores():
    """Fetch ESPN scores and update database."""
    # Check if we're in tournament dates
    tournament = get_active_tournament()
    if not tournament or not is_tournament_active(tournament):
        return

    # Call existing sync endpoint logic
    # (refactor sync.py endpoint into reusable function)
    db = SessionLocal()
    try:
        games_updated = sync_espn_data(db)
        logger.info(f"Poll complete: {games_updated} games updated")
    finally:
        db.close()
```

**Behavior:**
- Runs every 5 minutes (300 seconds)
- Only during tournament dates (March 17 - April 6)
- Logs to file: `logs/celery.log`
- Gracefully handles ESPN API errors (log and continue)

### 2.4 Brackets Index Updates

**Add to BracketsIndex page:**
- "Create New Bracket" button (routes to `/brackets/new`)
- Sort brackets by points (descending)
- Show tournament progress: "X of 63 games completed"

### 2.5 Testing

**Unit Tests:**
- Bracket validation logic (63 picks, valid tree)
- File import parsing (JSON, YAML)
- Team name resolution

**Integration Tests:**
- POST /brackets with 63 picks → creates bracket
- POST /brackets/import with YAML → creates bracket
- Invalid picks rejected with error messages
- Celery task runs (mock ESPN API)

**Manual Tests:**
- Create bracket via web form (all 63 picks)
- Upload bracket YAML file
- Verify Celery beat logs show 5-min polling
- Trigger sync manually, verify scores update

---

## Phase 3: Intelligence & Polish

**Goal:** Enhanced notifications, logging, and testing.

### 3.1 Enhanced Notifications

**Notification Events:**

1. **Game Start** (5 minutes before scheduled_time)
   - Message: "🏀 Game Starting: [1] Duke vs [16] Hampton in 5 minutes!"

2. **Halftime** (when ESPN status = "STATUS_HALFTIME")
   - Message: "⏸️ Halftime: [1] Duke 42 - [16] Hampton 28"

3. **Game Final** (when status = "completed")
   - Message: "✅ Final: [1] Duke 78 - [16] Hampton 62\n📊 Your Pick: Duke ✅ (+10 pts)"

4. **Upset Alert** (already implemented)
   - Message: "🚨 UPSET! [9] Missouri 75 - [8] Memphis 71"

**File:** `backend/app/services/notification_scheduler.py`

**Functionality:**
- Query database for games needing notifications
- Compare current state vs last notified state (track in Game model)
- Queue notification tasks for Celery

**New Game Model Fields:**
```python
class Game(Base):
    # ... existing fields
    last_notified_event: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # Values: "game_start", "halftime", "final"
```

**File:** `backend/app/tasks/notifications.py`

```python
@celery.task
def send_game_notification(game_id: int, event_type: str):
    """Send notification for game event."""
    db = SessionLocal()
    try:
        game = db.query(Game).get(game_id)
        # Format message based on event_type
        # Send via notifier service
        # Update game.last_notified_event
    finally:
        db.close()
```

**Configuration:**
Enable/disable per event in `backend/.env`:
```env
NOTIFY_GAME_START=true
NOTIFY_HALFTIME=true
NOTIFY_GAME_FINAL=true
NOTIFY_UPSETS=true
```

**Celery Task:**
- Runs every minute to check for notification-worthy events
- Prevents duplicate notifications via `last_notified_event` tracking

### 3.2 Logging Improvements

**File:** `backend/logging.conf`

```ini
[loggers]
keys=root,app,espn,celery

[handlers]
keys=console,file

[formatters]
keys=detailed

[logger_root]
level=INFO
handlers=console,file

[logger_app]
level=INFO
handlers=console,file
qualname=app

[logger_espn]
level=INFO
handlers=console,file
qualname=app.services.espn_client

[logger_celery]
level=INFO
handlers=console,file
qualname=app.tasks

[handler_console]
class=StreamHandler
formatter=detailed
args=(sys.stdout,)

[handler_file]
class=logging.handlers.RotatingFileHandler
formatter=detailed
args=('logs/app.log', 'a', 10485760, 5)  # 10MB, 5 backups

[formatter_detailed]
format=%(asctime)s [%(levelname)s] %(name)s: %(message)s
```

**Key Events to Log:**

| Event | Level | Example Message |
|-------|-------|----------------|
| ESPN API call | INFO | `ESPN API: Fetched 32 games` |
| ESPN API failure | WARNING | `ESPN API error: 429 rate limit, retrying in 60s` |
| Score update | INFO | `Updated 5 games: game_001, game_002...` |
| Bracket created | INFO | `Bracket created: id=5, name="My Chalk Bracket"` |
| Notification sent | INFO | `WhatsApp notification sent: game_001 final` |
| Notification failed | ERROR | `Failed to send notification: connection timeout` |
| Celery task start | INFO | `Task started: poll_espn_scores` |
| Celery task complete | INFO | `Task complete: poll_espn_scores (3.2s)` |

**Error Handling Pattern:**

```python
try:
    response = await espn_client.get_tournament_games()
except httpx.TimeoutException:
    logger.warning("ESPN API timeout, will retry next poll")
    return  # Don't crash, continue
except httpx.HTTPStatusError as e:
    if e.response.status_code == 429:
        logger.warning("ESPN API rate limit hit, backing off")
        await asyncio.sleep(60)
    else:
        logger.error(f"ESPN API error: {e.response.status_code}")
    return
```

### 3.3 Testing Strategy

**Unit Tests (pytest):**

**File:** `backend/tests/test_scoring_engine.py`
- Test point calculations for each round
- Test upset detection logic
- Test bracket health calculation

**File:** `backend/tests/test_bracket_validation.py`
- Validate 63 picks required
- Validate bracket tree structure
- Validate predicted winners are valid teams

**File:** `backend/tests/test_tournament_loader.py`
- Parse valid YAML
- Reject invalid YAML
- Test idempotency

**File:** `backend/tests/test_notification_formatter.py`
- Test message formatting for each event type
- Test upset message generation

**Integration Tests:**

**File:** `backend/tests/integration/test_api.py`
- Test all API endpoints (brackets, games, scores, sync)
- Test bracket creation with 63 picks
- Test bracket import from file

**File:** `backend/tests/integration/test_celery.py`
- Test polling task execution (mocked ESPN)
- Test notification task execution (mocked WhatsApp)

**Coverage Goal:**
- Critical paths: 70%+ (scoring, validation, bracket creation)
- Services: 60%+ (ESPN client, notifier)
- API endpoints: 80%+ (high user impact)

**CI Setup:**

**File:** `.github/workflows/test.yml`
```yaml
name: Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
      redis:
        image: redis:7-alpine

    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          cd backend
          pip install uv
          uv pip install --system -r pyproject.toml
          uv pip install --system pytest pytest-asyncio pytest-cov
      - name: Run tests
        run: |
          cd backend
          pytest --cov=app --cov-report=term
```

**Manual Testing Checklist:**
- [ ] Load 2026 tournament YAML
- [ ] Create bracket via web form (all 63 picks)
- [ ] Upload bracket from YAML file
- [ ] Verify Celery polling every 5 minutes
- [ ] Trigger manual ESPN sync
- [ ] Verify WhatsApp notifications for each event type
- [ ] Check logs for errors during tournament simulation
- [ ] View brackets index with 3+ brackets
- [ ] Navigate to bracket detail page

---

## Implementation Sequence

### Phase 1: Foundation (Week 1-2)
1. Create tournament YAML format and 2026.yaml template
2. Implement tournament loader script
3. Add South and Midwest regions to seed data
4. Implement brackets index page with routing
5. Write unit tests for loader
6. Manual test: Load tournament, view brackets index

**Deliverable:** Full 64-team tournament structure, browsable brackets

### Phase 2: Input & Automation (Week 3-4)
1. Implement bracket creation page (web form)
2. Build interactive BracketPicker component
3. Implement file upload and import endpoint
4. Add Redis + Celery to Docker Compose
5. Implement ESPN polling Celery task
6. Update brackets index with "Create" button
7. Write unit tests for validation logic
8. Write integration tests for bracket creation
9. Manual test: Create bracket, verify polling

**Deliverable:** Fully functional bracket input + automated score updates

### Phase 3: Intelligence & Polish (Week 5-6)
1. Add notification event detection
2. Implement notification scheduling task
3. Add structured logging configuration
4. Improve error handling in ESPN client
5. Write comprehensive test suite
6. Set up GitHub Actions CI
7. Document manual testing procedures
8. Perform end-to-end testing with simulated tournament

**Deliverable:** Production-ready system with notifications, logging, tests

---

## Success Criteria

**Phase 1 Complete:**
- ✅ 64 teams loaded from YAML
- ✅ 32 Round 64 games created
- ✅ Brackets index shows multiple brackets
- ✅ Navigation to bracket detail works

**Phase 2 Complete:**
- ✅ Create bracket with all 63 picks via web form
- ✅ Upload bracket from YAML file
- ✅ Celery polls ESPN every 5 minutes
- ✅ Scores update automatically

**Phase 3 Complete:**
- ✅ Notifications sent for all 4 event types
- ✅ Logs capture key events
- ✅ Test suite runs in CI
- ✅ 70%+ coverage on critical paths
- ✅ System runs stable for 48-hour test

**Ready for Real Tournament:**
- ✅ All phases complete
- ✅ Tested with historical tournament data
- ✅ Docker Compose stack runs reliably
- ✅ Notifications configured and working
- ✅ Can create brackets for real tournament

---

## Non-Goals (Future Versions)

- Multi-bracket comparison view (side-by-side visualization)
- Cloud deployment (Kubernetes, AWS/GCP)
- User authentication and multi-user support
- Historical bracket archives
- Advanced analytics (win probability, bracket similarity)
- Mobile app
- Social features (bracket sharing, leaderboards)

---

## Risk Mitigation

**Risk:** ESPN API rate limits during heavy polling
**Mitigation:** 5-10 minute intervals, exponential backoff on 429 errors

**Risk:** Tournament structure changes year-to-year
**Mitigation:** YAML configuration per year, loader validates structure

**Risk:** Celery tasks fail silently
**Mitigation:** Structured logging, health check endpoint, manual monitoring

**Risk:** Incorrect scoring calculations
**Mitigation:** Unit tests with known bracket scenarios, manual verification

**Risk:** WhatsApp notifications overwhelming
**Mitigation:** Event type configuration, quiet hours support (future)

---

## Technical Debt

**Acceptable for MVP:**
- No user authentication (single user)
- Console/file logging only (no monitoring dashboard)
- Manual tournament YAML creation
- No automated deployment
- Limited error recovery (log and continue)

**Future Improvements:**
- Structured error tracking (Sentry)
- Health monitoring dashboard
- Automated tournament data import from ESPN
- Database backup strategy
- Performance optimization (caching, indexing)
