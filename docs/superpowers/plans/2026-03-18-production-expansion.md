# NCAA Bracket Tracker - Production Expansion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expand from 4-game vertical slice to production-ready system with full 64-team tournament, bracket creation UI, automated polling, and enhanced notifications.

**Architecture:** Three-phase vertical expansion: (1) Foundation - complete tournament data model and navigation, (2) Input & Automation - bracket creation and Celery polling, (3) Intelligence - notifications, logging, comprehensive tests.

**Tech Stack:** FastAPI, PostgreSQL, SQLAlchemy, Alembic, Celery, Redis, React, TypeScript, Tailwind CSS, pytest

---

## File Structure Map

### Phase 1: Foundation
```
backend/
  data/tournaments/2026.yaml          # NEW: Tournament config
  scripts/load_tournament.py          # NEW: YAML importer
  tests/test_tournament_loader.py     # NEW: Loader tests
frontend/
  src/pages/BracketsIndex.tsx         # NEW: Brackets list page
  src/App.tsx                          # MODIFY: Add routing
```

### Phase 2: Input & Automation
```
frontend/
  src/pages/BracketCreate.tsx                # NEW: Bracket creation form
  src/components/Bracket/BracketPicker.tsx   # NEW: Interactive picker
backend/
  app/services/bracket_validator.py          # NEW: Validation logic
  app/services/sync_service.py               # NEW: Extract sync logic
  app/api/v1/brackets.py                     # MODIFY: Add POST, import
  app/api/v1/sync.py                         # MODIFY: Use service
  app/celery_app.py                          # NEW: Celery config
  app/celeryconfig.py                        # NEW: Celery settings
  app/tasks/__init__.py                      # NEW: Tasks package
  app/tasks/polling.py                       # NEW: ESPN polling task
  tests/test_bracket_validation.py           # NEW: Validation tests
  tests/integration/test_api.py              # NEW: API integration tests
docker-compose.yml                           # MODIFY: Add Redis, Celery
```

### Phase 3: Intelligence & Polish
```
backend/
  app/db/models.py                           # MODIFY: Add last_notified_event
  alembic/versions/002_notifications.py      # NEW: Migration
  app/services/notification_scheduler.py     # NEW: Event detection
  app/tasks/notifications.py                 # NEW: Notification tasks
  app/config.py                              # MODIFY: Notification settings
  logging.conf                               # NEW: Logging config
  app/services/espn_client.py                # MODIFY: Error handling
  tests/test_scoring_engine.py               # NEW: Scoring tests
  tests/test_notification_formatter.py       # NEW: Notification tests
  tests/integration/test_celery.py           # NEW: Celery integration tests
.github/workflows/test.yml                   # NEW: CI pipeline
```

---

## PHASE 1: FOUNDATION (Full 64-Team Structure)

### Task 1: Create Tournament YAML Template

**Files:**
- Create: `backend/data/tournaments/2026.yaml`

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p backend/data/tournaments
```

Run: `ls -la backend/data/`
Expected: `tournaments/` directory exists

- [ ] **Step 2: Create 2026 tournament YAML**

Create `backend/data/tournaments/2026.yaml` with complete 64-team structure:

```yaml
tournament:
  year: 2026
  name: "NCAA March Madness 2026"
  start_date: "2026-03-17"
  end_date: "2026-04-06"

regions:
  - name: "East"
    teams:
      - {name: "Duke", seed: 1, espn_id: "duke_001"}
      - {name: "Hampton", seed: 16, espn_id: "hampton_016"}
      - {name: "Kentucky", seed: 2, espn_id: "kentucky_002"}
      - {name: "Norfolk State", seed: 15, espn_id: "norfolk_015"}
      - {name: "Baylor", seed: 3, espn_id: "baylor_003"}
      - {name: "Abilene Christian", seed: 14, espn_id: "abilene_014"}
      - {name: "UCLA", seed: 4, espn_id: "ucla_004"}
      - {name: "Iona", seed: 13, espn_id: "iona_013"}
      - {name: "Gonzaga", seed: 5, espn_id: "gonzaga_005"}
      - {name: "Oklahoma", seed: 12, espn_id: "oklahoma_012"}
      - {name: "Texas", seed: 6, espn_id: "texas_006"}
      - {name: "VCU", seed: 11, espn_id: "vcu_011"}
      - {name: "UConn", seed: 7, espn_id: "uconn_007"}
      - {name: "New Mexico State", seed: 10, espn_id: "nmsu_010"}
      - {name: "Memphis", seed: 8, espn_id: "memphis_008"}
      - {name: "Missouri", seed: 9, espn_id: "missouri_009"}

  - name: "West"
    teams:
      - {name: "Arizona", seed: 1, espn_id: "arizona_w001"}
      - {name: "Wright State", seed: 16, espn_id: "wright_w016"}
      - {name: "TCU", seed: 2, espn_id: "tcu_w002"}
      - {name: "Southeast Missouri State", seed: 15, espn_id: "semo_w015"}
      - {name: "Wisconsin", seed: 3, espn_id: "wisconsin_w003"}
      - {name: "Colgate", seed: 14, espn_id: "colgate_w014"}
      - {name: "Kansas", seed: 4, espn_id: "kansas_w004"}
      - {name: "Howard", seed: 13, espn_id: "howard_w013"}
      - {name: "Saint Mary's", seed: 5, espn_id: "stmarys_w005"}
      - {name: "VCU", seed: 12, espn_id: "vcu_w012"}
      - {name: "Indiana", seed: 6, espn_id: "indiana_w006"}
      - {name: "Kent State", seed: 11, espn_id: "kent_w011"}
      - {name: "Iowa State", seed: 7, espn_id: "iowa_state_w007"}
      - {name: "Pittsburgh", seed: 10, espn_id: "pitt_w010"}
      - {name: "Miami", seed: 8, espn_id: "miami_w008"}
      - {name: "USC", seed: 9, espn_id: "usc_w009"}

  - name: "South"
    teams:
      - {name: "Alabama", seed: 1, espn_id: "alabama_s001"}
      - {name: "Texas A&M Corpus Christi", seed: 16, espn_id: "tamcc_s016"}
      - {name: "Marquette", seed: 2, espn_id: "marquette_s002"}
      - {name: "Vermont", seed: 15, espn_id: "vermont_s015"}
      - {name: "Kansas State", seed: 3, espn_id: "ksu_s003"}
      - {name: "Montana State", seed: 14, espn_id: "montana_s014"}
      - {name: "Tennessee", seed: 4, espn_id: "tennessee_s004"}
      - {name: "Louisiana", seed: 13, espn_id: "louisiana_s013"}
      - {name: "Maryland", seed: 5, espn_id: "maryland_s005"}
      - {name: "West Virginia", seed: 12, espn_id: "wvu_s012"}
      - {name: "San Diego State", seed: 6, espn_id: "sdsu_s006"}
      - {name: "Charleston", seed: 11, espn_id: "charleston_s011"}
      - {name: "Creighton", seed: 7, espn_id: "creighton_s007"}
      - {name: "NC State", seed: 10, espn_id: "ncstate_s010"}
      - {name: "Auburn", seed: 8, espn_id: "auburn_s008"}
      - {name: "Iowa", seed: 9, espn_id: "iowa_s009"}

  - name: "Midwest"
    teams:
      - {name: "Purdue", seed: 1, espn_id: "purdue_m001"}
      - {name: "Fairleigh Dickinson", seed: 16, espn_id: "fdu_m016"}
      - {name: "Texas A&M", seed: 2, espn_id: "tamu_m002"}
      - {name: "Penn State", seed: 15, espn_id: "pennstate_m015"}
      - {name: "Xavier", seed: 3, espn_id: "xavier_m003"}
      - {name: "Kennesaw State", seed: 14, espn_id: "kennesaw_m014"}
      - {name: "Virginia", seed: 4, espn_id: "virginia_m004"}
      - {name: "Furman", seed: 13, espn_id: "furman_m013"}
      - {name: "Florida", seed: 5, espn_id: "florida_m005"}
      - {name: "Oral Roberts", seed: 12, espn_id: "oral_roberts_m012"}
      - {name: "Arkansas", seed: 6, espn_id: "arkansas_m006"}
      - {name: "Illinois", seed: 11, espn_id: "illinois_m011"}
      - {name: "Michigan State", seed: 7, espn_id: "msu_m007"}
      - {name: "Drake", seed: 10, espn_id: "drake_m010"}
      - {name: "Northwestern", seed: 8, espn_id: "northwestern_m008"}
      - {name: "Boise State", seed: 9, espn_id: "boise_m009"}

matchups:
  round_64:
    # East Region
    - {region: "East", game_id: "game_e_1v16", home_seed: 1, away_seed: 16}
    - {region: "East", game_id: "game_e_8v9", home_seed: 8, away_seed: 9}
    - {region: "East", game_id: "game_e_5v12", home_seed: 5, away_seed: 12}
    - {region: "East", game_id: "game_e_4v13", home_seed: 4, away_seed: 13}
    - {region: "East", game_id: "game_e_6v11", home_seed: 6, away_seed: 11}
    - {region: "East", game_id: "game_e_3v14", home_seed: 3, away_seed: 14}
    - {region: "East", game_id: "game_e_7v10", home_seed: 7, away_seed: 10}
    - {region: "East", game_id: "game_e_2v15", home_seed: 2, away_seed: 15}

    # West Region
    - {region: "West", game_id: "game_w_1v16", home_seed: 1, away_seed: 16}
    - {region: "West", game_id: "game_w_8v9", home_seed: 8, away_seed: 9}
    - {region: "West", game_id: "game_w_5v12", home_seed: 5, away_seed: 12}
    - {region: "West", game_id: "game_w_4v13", home_seed: 4, away_seed: 13}
    - {region: "West", game_id: "game_w_6v11", home_seed: 6, away_seed: 11}
    - {region: "West", game_id: "game_w_3v14", home_seed: 3, away_seed: 14}
    - {region: "West", game_id: "game_w_7v10", home_seed: 7, away_seed: 10}
    - {region: "West", game_id: "game_w_2v15", home_seed: 2, away_seed: 15}

    # South Region
    - {region: "South", game_id: "game_s_1v16", home_seed: 1, away_seed: 16}
    - {region: "South", game_id: "game_s_8v9", home_seed: 8, away_seed: 9}
    - {region: "South", game_id: "game_s_5v12", home_seed: 5, away_seed: 12}
    - {region: "South", game_id: "game_s_4v13", home_seed: 4, away_seed: 13}
    - {region: "South", game_id: "game_s_6v11", home_seed: 6, away_seed: 11}
    - {region: "South", game_id: "game_s_3v14", home_seed: 3, away_seed: 14}
    - {region: "South", game_id: "game_s_7v10", home_seed: 7, away_seed: 10}
    - {region: "South", game_id: "game_s_2v15", home_seed: 2, away_seed: 15}

    # Midwest Region
    - {region: "Midwest", game_id: "game_m_1v16", home_seed: 1, away_seed: 16}
    - {region: "Midwest", game_id: "game_m_8v9", home_seed: 8, away_seed: 9}
    - {region: "Midwest", game_id: "game_m_5v12", home_seed: 5, away_seed: 12}
    - {region: "Midwest", game_id: "game_m_4v13", home_seed: 4, away_seed: 13}
    - {region: "Midwest", game_id: "game_m_6v11", home_seed: 6, away_seed: 11}
    - {region: "Midwest", game_id: "game_m_3v14", home_seed: 3, away_seed: 14}
    - {region: "Midwest", game_id: "game_m_7v10", home_seed: 7, away_seed: 10}
    - {region: "Midwest", game_id: "game_m_2v15", home_seed: 2, away_seed: 15}
```

- [ ] **Step 3: Verify YAML structure**

Run: `python -c "import yaml; yaml.safe_load(open('backend/data/tournaments/2026.yaml'))"`
Expected: No errors, successful parse

- [ ] **Step 4: Commit**

```bash
git add backend/data/
git commit -m "Add 2026 tournament YAML template with 64 teams"
```

---

### Task 2: Tournament Loader - Write Failing Tests

**Files:**
- Create: `backend/tests/test_tournament_loader.py`

- [ ] **Step 1: Create tests directory**

```bash
mkdir -p backend/tests
touch backend/tests/__init__.py
```

- [ ] **Step 2: Write failing test for YAML parsing**

Create `backend/tests/test_tournament_loader.py`:

```python
import pytest
from pathlib import Path
from datetime import datetime


def test_parse_valid_tournament_yaml():
    """Test parsing a valid tournament YAML file."""
    from scripts.load_tournament import parse_tournament_yaml

    yaml_path = Path("data/tournaments/2026.yaml")
    result = parse_tournament_yaml(yaml_path)

    assert result["tournament"]["year"] == 2026
    assert result["tournament"]["name"] == "NCAA March Madness 2026"
    assert len(result["regions"]) == 4
    assert len(result["matchups"]["round_64"]) == 32


def test_validate_tournament_structure():
    """Test tournament structure validation."""
    from scripts.load_tournament import validate_tournament

    yaml_path = Path("data/tournaments/2026.yaml")
    from scripts.load_tournament import parse_tournament_yaml
    data = parse_tournament_yaml(yaml_path)

    # Should not raise exception
    validate_tournament(data)


def test_validate_rejects_invalid_team_count():
    """Test validation rejects wrong number of teams."""
    from scripts.load_tournament import validate_tournament

    invalid_data = {
        "tournament": {"year": 2026, "name": "Test", "start_date": "2026-03-17", "end_date": "2026-04-06"},
        "regions": [
            {"name": "East", "teams": [{"name": "Duke", "seed": 1, "espn_id": "duke"}]}  # Only 1 team
        ],
        "matchups": {"round_64": []}
    }

    with pytest.raises(ValueError, match="must have exactly 16 teams"):
        validate_tournament(invalid_data)


def test_validate_rejects_invalid_seeds():
    """Test validation rejects invalid seed numbers."""
    from scripts.load_tournament import validate_tournament

    teams = [{"name": f"Team{i}", "seed": i, "espn_id": f"t{i}"} for i in range(1, 17)]
    teams[0]["seed"] = 0  # Invalid seed

    invalid_data = {
        "tournament": {"year": 2026, "name": "Test", "start_date": "2026-03-17", "end_date": "2026-04-06"},
        "regions": [{"name": "East", "teams": teams}],
        "matchups": {"round_64": []}
    }

    with pytest.raises(ValueError, match="Seeds must be 1-16"):
        validate_tournament(invalid_data)
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `cd backend && pytest tests/test_tournament_loader.py -v`
Expected: 4 FAILED (module 'load_tournament' not found)

- [ ] **Step 4: Commit**

```bash
git add backend/tests/
git commit -m "test: add tournament loader tests (failing)"
```

---

### Task 3: Tournament Loader - Implement Core Functions

**Files:**
- Create: `backend/scripts/load_tournament.py`

- [ ] **Step 1: Create load_tournament.py with parsing function**

Create `backend/scripts/load_tournament.py`:

```python
"""Load tournament data from YAML file into database."""
import sys
from pathlib import Path
from datetime import datetime

import yaml
from sqlalchemy.orm import Session

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from app.db.models import Tournament, Team, Game
from app.db.session import engine, SessionLocal


def parse_tournament_yaml(yaml_path: Path) -> dict:
    """Parse tournament YAML file.

    Args:
        yaml_path: Path to YAML file

    Returns:
        Parsed tournament data dictionary
    """
    with open(yaml_path, 'r') as f:
        data = yaml.safe_load(f)
    return data


def validate_tournament(data: dict) -> None:
    """Validate tournament data structure.

    Args:
        data: Parsed tournament data

    Raises:
        ValueError: If validation fails
    """
    # Validate tournament section
    if "tournament" not in data:
        raise ValueError("Missing 'tournament' section")

    if "regions" not in data:
        raise ValueError("Missing 'regions' section")

    # Validate regions
    if len(data["regions"]) != 4:
        raise ValueError("Must have exactly 4 regions")

    for region in data["regions"]:
        # Check team count
        teams = region.get("teams", [])
        if len(teams) != 16:
            raise ValueError(f"Region {region['name']} must have exactly 16 teams")

        # Check seeds
        seeds = [t["seed"] for t in teams]
        if set(seeds) != set(range(1, 17)):
            raise ValueError(f"Region {region['name']}: Seeds must be 1-16 with no duplicates")

        for team in teams:
            if not (1 <= team["seed"] <= 16):
                raise ValueError("Seeds must be 1-16")

    # Validate matchups
    if "matchups" not in data or "round_64" not in data["matchups"]:
        raise ValueError("Missing 'matchups.round_64' section")

    if len(data["matchups"]["round_64"]) != 32:
        raise ValueError("Must have exactly 32 Round 64 matchups")


def load_tournament(yaml_path: Path, db: Session) -> tuple[int, int, int]:
    """Load tournament from YAML into database.

    Args:
        yaml_path: Path to YAML file
        db: Database session

    Returns:
        Tuple of (tournament_id, teams_created, games_created)
    """
    # Parse and validate
    data = parse_tournament_yaml(yaml_path)
    validate_tournament(data)

    tournament_data = data["tournament"]

    # Check if tournament already exists
    existing = db.query(Tournament).filter(Tournament.year == tournament_data["year"]).first()
    if existing:
        print(f"Tournament {tournament_data['year']} already exists (id={existing.id})")
        return (existing.id, 0, 0)

    # Create tournament
    tournament = Tournament(
        year=tournament_data["year"],
        name=tournament_data["name"],
        start_date=datetime.fromisoformat(tournament_data["start_date"]),
        end_date=datetime.fromisoformat(tournament_data["end_date"])
    )
    db.add(tournament)
    db.flush()  # Get tournament ID

    # Create teams
    teams_created = 0
    team_map = {}  # (region, seed) -> team_id

    for region_data in data["regions"]:
        region_name = region_data["name"]
        for team_data in region_data["teams"]:
            team = Team(
                tournament_id=tournament.id,
                name=team_data["name"],
                seed=team_data["seed"],
                region=region_name,
                espn_id=team_data["espn_id"]
            )
            db.add(team)
            db.flush()
            team_map[(region_name, team_data["seed"])] = team.id
            teams_created += 1

    # Create Round 64 games
    games_created = 0
    for matchup in data["matchups"]["round_64"]:
        region = matchup["region"]
        home_team_id = team_map[(region, matchup["home_seed"])]
        away_team_id = team_map[(region, matchup["away_seed"])]

        game = Game(
            tournament_id=tournament.id,
            espn_id=matchup["game_id"],
            round="Round 64",
            region=region,
            home_team_id=home_team_id,
            away_team_id=away_team_id,
            status="scheduled"
        )
        db.add(game)
        games_created += 1

    db.commit()
    return (tournament.id, teams_created, games_created)


def main():
    """CLI entry point."""
    if len(sys.argv) != 2:
        print("Usage: python load_tournament.py <yaml_file>")
        sys.exit(1)

    yaml_path = Path(sys.argv[1])
    if not yaml_path.exists():
        print(f"Error: File not found: {yaml_path}")
        sys.exit(1)

    print(f"Loading tournament from {yaml_path}...")
    db = SessionLocal()

    try:
        tournament_id, teams, games = load_tournament(yaml_path, db)
        print(f"✓ Tournament loaded successfully")
        print(f"  Tournament ID: {tournament_id}")
        print(f"  Teams created: {teams}")
        print(f"  Games created: {games}")
    except Exception as e:
        print(f"✗ Error: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Add PyYAML to dependencies**

Edit `backend/pyproject.toml`, add to dependencies array:

```toml
"pyyaml>=6.0.1",
```

- [ ] **Step 3: Run tests to verify they pass**

Run: `cd backend && pytest tests/test_tournament_loader.py -v`
Expected: 4 PASSED

- [ ] **Step 4: Commit**

```bash
git add backend/scripts/load_tournament.py backend/pyproject.toml
git commit -m "feat: implement tournament YAML loader with validation"
```

---

### Task 4: Test Tournament Loader Integration

**Files:**
- Create: `backend/tests/integration/__init__.py`
- Create: `backend/tests/integration/test_tournament_loader.py`

- [ ] **Step 1: Write integration test**

Create `backend/tests/integration/test_tournament_loader.py`:

```python
"""Integration tests for tournament loader."""
import pytest
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.models import Tournament, Team, Game
from scripts.load_tournament import load_tournament


@pytest.fixture
def test_db():
    """Create a test database."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_load_tournament_creates_all_entities(test_db):
    """Test loading tournament creates all teams and games."""
    yaml_path = Path("data/tournaments/2026.yaml")

    tournament_id, teams, games = load_tournament(yaml_path, test_db)

    assert tournament_id > 0
    assert teams == 64
    assert games == 32

    # Verify in database
    assert test_db.query(Tournament).count() == 1
    assert test_db.query(Team).count() == 64
    assert test_db.query(Game).count() == 32


def test_load_tournament_is_idempotent(test_db):
    """Test loading same tournament twice doesn't create duplicates."""
    yaml_path = Path("data/tournaments/2026.yaml")

    # Load once
    tournament_id1, teams1, games1 = load_tournament(yaml_path, test_db)

    # Load again
    tournament_id2, teams2, games2 = load_tournament(yaml_path, test_db)

    assert tournament_id1 == tournament_id2
    assert teams2 == 0  # No new teams
    assert games2 == 0  # No new games

    # Still only one tournament
    assert test_db.query(Tournament).count() == 1


def test_load_tournament_teams_have_correct_regions(test_db):
    """Test loaded teams have correct region assignments."""
    yaml_path = Path("data/tournaments/2026.yaml")
    load_tournament(yaml_path, test_db)

    regions = ["East", "West", "South", "Midwest"]
    for region in regions:
        teams_in_region = test_db.query(Team).filter(Team.region == region).all()
        assert len(teams_in_region) == 16

        # Check seeds 1-16 all present
        seeds = sorted([t.seed for t in teams_in_region])
        assert seeds == list(range(1, 17))


def test_load_tournament_creates_correct_matchups(test_db):
    """Test Round 64 games have correct seed matchups."""
    yaml_path = Path("data/tournaments/2026.yaml")
    load_tournament(yaml_path, test_db)

    games = test_db.query(Game).filter(Game.round == "Round 64").all()
    assert len(games) == 32

    # Check typical matchups (1v16, 8v9, etc.)
    for game in games:
        home_team = test_db.query(Team).get(game.home_team_id)
        away_team = test_db.query(Team).get(game.away_team_id)

        # Verify teams are from same region
        assert home_team.region == away_team.region == game.region

        # Verify seed sum is 17 (1+16, 2+15, 3+14, etc.)
        assert home_team.seed + away_team.seed == 17
```

- [ ] **Step 2: Run integration tests**

Run: `cd backend && pytest tests/integration/test_tournament_loader.py -v`
Expected: 4 PASSED

- [ ] **Step 3: Commit**

```bash
git add backend/tests/integration/
git commit -m "test: add tournament loader integration tests"
```

---

### Task 5: Brackets Index Page - Frontend Setup

**Files:**
- Create: `frontend/src/pages/BracketsIndex.tsx`
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: Install React Router**

Run: `cd frontend && pnpm add react-router-dom@latest`
Expected: Package installed successfully

- [ ] **Step 2: Create BracketsIndex page**

Create `frontend/src/pages/BracketsIndex.tsx`:

```typescript
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { apiClient, type Bracket } from '../api/client'

export default function BracketsIndex() {
  const [brackets, setBrackets] = useState<Bracket[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchBrackets = async () => {
      try {
        setLoading(true)
        const data = await apiClient.getBrackets()
        // Sort by points descending
        const sorted = data.sort((a, b) => b.total_points - a.total_points)
        setBrackets(sorted)
        setError(null)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load brackets')
      } finally {
        setLoading(false)
      }
    }

    fetchBrackets()
  }, [])

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0a0e14] flex items-center justify-center">
        <div className="text-slate-400 text-xl">Loading brackets...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-[#0a0e14] flex items-center justify-center">
        <div className="text-rose-400 text-xl">Error: {error}</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-[#0a0e14] relative overflow-hidden">
      {/* Stadium Lighting Effect */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-amber-500/10 rounded-full blur-[128px]" />
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-emerald-500/10 rounded-full blur-[128px]" />
      </div>

      <div className="relative z-10 container mx-auto px-4 py-8 lg:py-12">
        {/* Header */}
        <div className="mb-12 text-center">
          <h1
            className="text-5xl lg:text-7xl font-black tracking-tighter mb-3 bg-clip-text text-transparent bg-gradient-to-r from-amber-200 via-amber-400 to-amber-200"
            style={{ fontFamily: "'Bebas Neue', sans-serif" }}
          >
            My Brackets
          </h1>
          <p className="text-slate-400 text-lg">Track your March Madness predictions</p>
        </div>

        {/* Empty State */}
        {brackets.length === 0 ? (
          <div className="text-center py-20">
            <div className="inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-slate-900/50 border border-slate-800 mb-6">
              <svg
                className="w-10 h-10 text-slate-600"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
            </div>
            <p className="text-xl text-slate-400 font-medium mb-8">No brackets yet</p>
          </div>
        ) : (
          /* Brackets Table */
          <div className="bg-slate-900/50 rounded-2xl border border-slate-800 backdrop-blur-sm overflow-hidden">
            <table className="w-full">
              <thead className="bg-slate-800/50 border-b border-slate-700">
                <tr>
                  <th className="px-6 py-4 text-left text-xs font-bold text-slate-400 uppercase tracking-wider">
                    Bracket Name
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-bold text-slate-400 uppercase tracking-wider">
                    Type
                  </th>
                  <th className="px-6 py-4 text-center text-xs font-bold text-slate-400 uppercase tracking-wider">
                    Points
                  </th>
                  <th className="px-6 py-4 text-center text-xs font-bold text-slate-400 uppercase tracking-wider">
                    Accuracy
                  </th>
                  <th className="px-6 py-4 text-right text-xs font-bold text-slate-400 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {brackets.map((bracket) => {
                  const accuracy =
                    bracket.total_picks > 0
                      ? Math.round((bracket.correct_picks / bracket.total_picks) * 100)
                      : 0

                  return (
                    <tr key={bracket.id} className="hover:bg-slate-800/30 transition-colors">
                      <td className="px-6 py-4">
                        <Link
                          to={`/brackets/${bracket.id}`}
                          className="text-white font-semibold hover:text-amber-400 transition-colors"
                        >
                          {bracket.name}
                        </Link>
                      </td>
                      <td className="px-6 py-4">
                        <span className="inline-flex px-3 py-1 rounded-full text-xs font-medium bg-slate-800 text-slate-300 capitalize">
                          {bracket.bracket_type}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-center">
                        <span
                          className="text-2xl font-black text-amber-400"
                          style={{ fontFamily: "'Bebas Neue', sans-serif" }}
                        >
                          {bracket.total_points}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-center">
                        <div className="flex flex-col items-center gap-1">
                          <span className="text-lg font-bold text-white">{accuracy}%</span>
                          <span className="text-xs text-slate-400">
                            {bracket.correct_picks}/{bracket.total_picks}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-right">
                        <Link
                          to={`/brackets/${bracket.id}`}
                          className="inline-flex items-center gap-2 px-4 py-2 bg-amber-500/10 hover:bg-amber-500/20 border border-amber-500/30 rounded-lg text-amber-400 font-semibold text-sm transition-colors"
                        >
                          View Details
                          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M9 5l7 7-7 7"
                            />
                          </svg>
                        </Link>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
```

- [ ] **Step 3: Update App.tsx with routing**

Edit `frontend/src/App.tsx`:

```typescript
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import BracketsIndex from './pages/BracketsIndex'
import Bracket from './components/Bracket/Bracket'
import { useGames } from './hooks/useGames'

function BracketDetailPage() {
  const { games } = useGames()

  // Convert games to Bracket component format
  const bracketGames = games.map((g) => ({
    id: g.id,
    round: g.round,
    region: g.region,
    homeTeam: {
      id: g.home_team_id,
      name: g.home_team_name,
      seed: g.home_team_seed,
      score: g.home_score ?? undefined,
    },
    awayTeam: {
      id: g.away_team_id,
      name: g.away_team_name,
      seed: g.away_team_seed,
      score: g.away_score ?? undefined,
    },
    status: g.status as 'scheduled' | 'in_progress' | 'completed',
    isUpset: g.is_upset,
  }))

  return <Bracket games={bracketGames} title="Bracket Details" />
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<BracketsIndex />} />
        <Route path="/brackets/:id" element={<BracketDetailPage />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
```

- [ ] **Step 4: Test in browser**

Run: `cd frontend && pnpm dev`
Navigate to: http://localhost:3000
Expected: Brackets index page loads, shows existing brackets

- [ ] **Step 5: Commit**

```bash
git add frontend/
git commit -m "feat: add brackets index page with routing"
```

---

### Task 6: Load Full Tournament Data

**Files:**
- Modify: `backend/scripts/seed_data.py`

- [ ] **Step 1: Backup existing seed script**

Run: `cp backend/scripts/seed_data.py backend/scripts/seed_data.py.bak`

- [ ] **Step 2: Update seed script to use tournament loader**

Edit `backend/scripts/seed_data.py`, replace the team/game creation logic:

```python
"""Seed database with sample tournament data."""
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session

from app.config import settings
from app.db.base import Base
from app.db.models import Bracket, Game, Pick, Team, Tournament, User
from app.db.session import engine
from scripts.load_tournament import load_tournament


def seed_database():
    """Seed database with sample data."""
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)

    print("Seeding data...")
    session = Session(bind=engine)

    try:
        # Create user
        user = User(
            name="Demo User",
            email="demo@example.com",
        )
        session.add(user)
        session.commit()
        print(f"✓ Created user: {user.email}")

        # Load tournament from YAML
        yaml_path = Path("data/tournaments/2026.yaml")
        tournament_id, teams, games = load_tournament(yaml_path, session)
        print(f"✓ Loaded tournament: {teams} teams, {games} games")

        # Get tournament
        tournament = session.query(Tournament).get(tournament_id)

        # Create sample bracket with picks for first 4 games
        bracket = Bracket(
            user_id=user.id,
            tournament_id=tournament.id,
            name="Championship Run",
            bracket_type="balanced",
            total_points=0,
            possible_points=0,
        )
        session.add(bracket)
        session.commit()
        print(f"✓ Created bracket: {bracket.name}")

        # Create picks for first few games (for demo)
        first_games = session.query(Game).filter(
            Game.tournament_id == tournament.id,
            Game.round == "Round 64"
        ).limit(4).all()

        for game in first_games:
            # Predict higher seed wins
            home_team = session.query(Team).get(game.home_team_id)
            away_team = session.query(Team).get(game.away_team_id)
            predicted_winner_id = home_team.id if home_team.seed < away_team.seed else away_team.id

            pick = Pick(
                bracket_id=bracket.id,
                game_id=game.id,
                predicted_winner_id=predicted_winner_id,
                points_value=10,  # Round 64
                points_earned=0,
            )
            session.add(pick)

        session.commit()
        print(f"✓ Created {len(first_games)} sample picks")

        # Calculate bracket scores
        from app.services.scoring_engine import ScoringEngine
        engine_service = ScoringEngine(session)
        scores = engine_service.calculate_bracket_score(bracket.id)
        print(f"✓ Calculated bracket scores: {scores}")

        print("\n✅ Database seeded successfully!")
        print(f"\nSummary:")
        print(f"  - User: {user.email}")
        print(f"  - Tournament: {tournament.name}")
        print(f"  - Teams: {teams}")
        print(f"  - Games: {games}")
        print(f"  - Bracket: {bracket.name}")
        print(f"  - Total Points: {bracket.total_points}")
        print(f"  - Possible Points: {bracket.possible_points}")

    except Exception as e:
        print(f"❌ Error seeding database: {e}")
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    print("NCAA Bracket Tracker - Database Seeder")
    print("=" * 50)
    seed_database()
```

- [ ] **Step 3: Test seed script**

Run: `docker-compose exec backend python scripts/seed_data.py`
Expected: ✓ Loaded tournament: 64 teams, 32 games

- [ ] **Step 4: Verify in database**

Run: `docker-compose exec db psql -U postgres -d bracket_tracker -c "SELECT COUNT(*) FROM teams;"`
Expected: 64 rows

Run: `docker-compose exec db psql -U postgres -d bracket_tracker -c "SELECT COUNT(*) FROM games;"`
Expected: 32 rows

- [ ] **Step 5: Commit**

```bash
git add backend/scripts/seed_data.py
git commit -m "feat: update seed script to load full 64-team tournament"
```

---

## PHASE 1 COMPLETE ✅

Verify Phase 1 success criteria:
- [ ] 64 teams loaded from YAML
- [ ] 32 Round 64 games created
- [ ] Brackets index shows brackets
- [ ] Navigation to bracket detail works

Run full test suite: `cd backend && pytest -v`

---

## PHASE 2: INPUT & AUTOMATION

### Task 7: Bracket Validation Service - Write Tests

**Files:**
- Create: `backend/tests/test_bracket_validation.py`

- [ ] **Step 1: Write bracket validation tests**

Create `backend/tests/test_bracket_validation.py`:

```python
"""Tests for bracket validation logic."""
import pytest
from app.services.bracket_validator import BracketValidator, ValidationError


def test_validate_all_games_have_picks():
    """Test validation requires picks for all 63 games."""
    validator = BracketValidator()

    # Only 62 picks (missing one)
    picks = [{"game_id": f"game_{i}", "predicted_winner_id": 1} for i in range(62)]

    with pytest.raises(ValidationError, match="Must have exactly 63 picks"):
        validator.validate_picks(picks, total_games=63)


def test_validate_no_duplicate_game_picks():
    """Test validation rejects duplicate picks for same game."""
    validator = BracketValidator()

    picks = [
        {"game_id": "game_1", "predicted_winner_id": 1},
        {"game_id": "game_1", "predicted_winner_id": 2},  # Duplicate
    ] + [{"game_id": f"game_{i}", "predicted_winner_id": 1} for i in range(2, 64)]

    with pytest.raises(ValidationError, match="Duplicate picks for game"):
        validator.validate_picks(picks, total_games=63)


def test_resolve_team_by_id():
    """Test resolving team by numeric ID."""
    from app.db.models import Team

    validator = BracketValidator()
    mock_teams = {
        1: Team(id=1, name="Duke", seed=1, region="East", espn_id="duke")
    }

    result = validator.resolve_team("1", mock_teams)
    assert result == 1


def test_resolve_team_by_name_case_insensitive():
    """Test resolving team by name (case-insensitive)."""
    from app.db.models import Team

    validator = BracketValidator()
    mock_teams = {
        1: Team(id=1, name="Duke", seed=1, region="East", espn_id="duke")
    }
    mock_teams_by_name = {"duke": [1]}

    result = validator.resolve_team_by_name("DUKE", mock_teams_by_name)
    assert result == 1


def test_resolve_team_ambiguous_name():
    """Test ambiguous team name raises error."""
    validator = BracketValidator()
    mock_teams_by_name = {"duke": [1, 2]}  # Multiple teams named "Duke"

    with pytest.raises(ValidationError, match="Ambiguous team name"):
        validator.resolve_team_by_name("Duke", mock_teams_by_name)


def test_resolve_team_not_found():
    """Test unknown team name raises error."""
    validator = BracketValidator()
    mock_teams_by_name = {}

    with pytest.raises(ValidationError, match="not found in tournament"):
        validator.resolve_team_by_name("Unknown Team", mock_teams_by_name)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && pytest tests/test_bracket_validation.py -v`
Expected: 7 FAILED (module not found)

- [ ] **Step 3: Commit**

```bash
git add backend/tests/test_bracket_validation.py
git commit -m "test: add bracket validation tests (failing)"
```

---

### Task 8: Implement Bracket Validator

**Files:**
- Create: `backend/app/services/bracket_validator.py`

- [ ] **Step 1: Create bracket validator service**

Create `backend/app/services/bracket_validator.py`:

```python
"""Bracket validation logic."""
from typing import Any


class ValidationError(Exception):
    """Bracket validation error."""
    pass


class BracketValidator:
    """Validates bracket picks and resolves team references."""

    def validate_picks(self, picks: list[dict[str, Any]], total_games: int) -> None:
        """Validate bracket picks structure.

        Args:
            picks: List of pick dictionaries
            total_games: Expected number of games

        Raises:
            ValidationError: If validation fails
        """
        if len(picks) != total_games:
            raise ValidationError(f"Must have exactly {total_games} picks, got {len(picks)}")

        # Check for duplicate game_ids
        game_ids = [p["game_id"] for p in picks]
        if len(game_ids) != len(set(game_ids)):
            duplicates = [gid for gid in game_ids if game_ids.count(gid) > 1]
            raise ValidationError(f"Duplicate picks for game: {duplicates[0]}")

    def resolve_team(self, winner: str | int, teams_by_id: dict[int, Any]) -> int:
        """Resolve team reference to team ID.

        Args:
            winner: Team ID (int) or name (str)
            teams_by_id: Dictionary of team ID -> Team object

        Returns:
            Team ID

        Raises:
            ValidationError: If team cannot be resolved
        """
        # If numeric, treat as ID
        if isinstance(winner, int) or (isinstance(winner, str) and winner.isdigit()):
            team_id = int(winner)
            if team_id not in teams_by_id:
                raise ValidationError(f"Team ID {team_id} not found")
            return team_id

        # Otherwise, resolve by name
        return self.resolve_team_by_name(winner, self._build_name_map(teams_by_id))

    def resolve_team_by_name(self, name: str, teams_by_name: dict[str, list[int]]) -> int:
        """Resolve team by name (case-insensitive).

        Args:
            name: Team name
            teams_by_name: Dictionary of lowercase name -> list of team IDs

        Returns:
            Team ID

        Raises:
            ValidationError: If name is ambiguous or not found
        """
        name_lower = name.lower()

        if name_lower not in teams_by_name:
            raise ValidationError(f"Team '{name}' not found in tournament")

        team_ids = teams_by_name[name_lower]
        if len(team_ids) > 1:
            raise ValidationError(f"Ambiguous team name '{name}' - use team ID instead")

        return team_ids[0]

    def _build_name_map(self, teams_by_id: dict[int, Any]) -> dict[str, list[int]]:
        """Build name -> team IDs mapping."""
        name_map: dict[str, list[int]] = {}
        for team_id, team in teams_by_id.items():
            name_lower = team.name.lower()
            if name_lower not in name_map:
                name_map[name_lower] = []
            name_map[name_lower].append(team_id)
        return name_map
```

- [ ] **Step 2: Run tests to verify they pass**

Run: `cd backend && pytest tests/test_bracket_validation.py -v`
Expected: 7 PASSED

- [ ] **Step 3: Commit**

```bash
git add backend/app/services/bracket_validator.py
git commit -m "feat: implement bracket validation service"
```

---

### Task 9: Add Bracket Creation Endpoint

**Files:**
- Modify: `backend/app/api/v1/brackets.py`
- Create: `backend/tests/integration/test_api.py`

- [ ] **Step 1: Write API integration test**

Create `backend/tests/integration/test_api.py`:

```python
"""Integration tests for API endpoints."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.base import Base
from app.db.models import Tournament, Team, Game, User
from app.api.deps import get_db


@pytest.fixture
def test_db():
    """Create test database."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine)

    # Override dependency
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    # Seed minimal data
    db = TestingSessionLocal()
    user = User(name="Test User", email="test@example.com")
    db.add(user)

    tournament = Tournament(
        year=2026,
        name="Test Tournament",
        start_date="2026-03-17",
        end_date="2026-04-06"
    )
    db.add(tournament)
    db.flush()

    # Add 2 teams
    team1 = Team(tournament_id=tournament.id, name="Duke", seed=1, region="East", espn_id="d1")
    team2 = Team(tournament_id=tournament.id, name="Hampton", seed=16, region="East", espn_id="h16")
    db.add_all([team1, team2])
    db.flush()

    # Add 1 game
    game = Game(
        tournament_id=tournament.id,
        espn_id="g1",
        round="Round 64",
        region="East",
        home_team_id=team1.id,
        away_team_id=team2.id,
        status="scheduled"
    )
    db.add(game)
    db.commit()
    db.close()

    yield TestingSessionLocal

    app.dependency_overrides.clear()


def test_create_bracket_with_valid_picks(test_db):
    """Test creating bracket with all required picks."""
    client = TestClient(app)

    # Get game ID
    db = test_db()
    game = db.query(Game).first()
    team = db.query(Team).first()
    db.close()

    response = client.post(
        "/api/v1/brackets",
        json={
            "name": "Test Bracket",
            "bracket_type": "chalk",
            "picks": [
                {"game_id": game.id, "predicted_winner_id": team.id}
            ]
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Bracket"
    assert "id" in data


def test_create_bracket_rejects_missing_picks(test_db):
    """Test creating bracket without all picks fails."""
    client = TestClient(app)

    response = client.post(
        "/api/v1/brackets",
        json={
            "name": "Incomplete Bracket",
            "bracket_type": "chalk",
            "picks": []
        }
    )

    assert response.status_code == 400
    assert "picks" in response.json()["detail"].lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/integration/test_api.py::test_create_bracket_with_valid_picks -v`
Expected: FAILED (endpoint not found)

- [ ] **Step 3: Add POST endpoint to brackets.py**

Edit `backend/app/api/v1/brackets.py`, add after existing endpoints:

```python
from fastapi import HTTPException
from pydantic import BaseModel

from app.services.bracket_validator import BracketValidator, ValidationError


class PickCreate(BaseModel):
    """Pick creation model."""
    game_id: int
    predicted_winner_id: int


class BracketCreate(BaseModel):
    """Bracket creation model."""
    name: str
    bracket_type: str
    picks: list[PickCreate]


class BracketCreateResponse(BaseModel):
    """Bracket creation response."""
    id: int
    name: str
    bracket_type: str
    total_picks: int


@router.post("/brackets", response_model=BracketCreateResponse, status_code=201)
async def create_bracket(bracket_data: BracketCreate, db: Session = Depends(get_db)):
    """Create a new bracket with picks."""
    validator = BracketValidator()

    # Get active tournament
    tournament = db.query(Tournament).order_by(Tournament.year.desc()).first()
    if not tournament:
        raise HTTPException(status_code=404, detail="No active tournament found")

    # Get user (for now, just first user)
    user = db.query(User).first()
    if not user:
        raise HTTPException(status_code=404, detail="No user found")

    # Validate picks
    picks_dicts = [p.dict() for p in bracket_data.picks]

    try:
        # Get all games for tournament
        total_games = db.query(Game).filter(Game.tournament_id == tournament.id).count()
        validator.validate_picks(picks_dicts, total_games=total_games)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Create bracket
    bracket = Bracket(
        user_id=user.id,
        tournament_id=tournament.id,
        name=bracket_data.name,
        bracket_type=bracket_data.bracket_type,
        total_points=0,
        possible_points=0,
    )
    db.add(bracket)
    db.flush()

    # Create picks
    for pick_data in bracket_data.picks:
        # Get game to determine points value
        game = db.query(Game).filter(Game.id == pick_data.game_id).first()
        if not game:
            raise HTTPException(status_code=400, detail=f"Game {pick_data.game_id} not found")

        # Determine points value based on round
        from app.services.scoring_engine import ROUND_POINTS
        points_value = ROUND_POINTS.get(game.round, 10)

        pick = Pick(
            bracket_id=bracket.id,
            game_id=pick_data.game_id,
            predicted_winner_id=pick_data.predicted_winner_id,
            points_value=points_value,
            points_earned=0,
        )
        db.add(pick)

    db.commit()

    return BracketCreateResponse(
        id=bracket.id,
        name=bracket.name,
        bracket_type=bracket.bracket_type,
        total_picks=len(bracket_data.picks),
    )
```

Also add imports at top:

```python
from app.db.models import Bracket, Pick, Tournament, User
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/integration/test_api.py::test_create_bracket_with_valid_picks -v`
Expected: PASSED

- [ ] **Step 5: Commit**

```bash
git add backend/app/api/v1/brackets.py backend/tests/integration/test_api.py
git commit -m "feat: add bracket creation POST endpoint"
```

---

Due to length constraints, I'll continue this plan in the next response. The plan follows the same detailed structure for:
- Task 10-15: File upload endpoint, sync service refactoring
- Task 16-20: Docker Compose Celery setup, polling task
- Task 21-25: Frontend bracket creation UI
- Phase 3: All notification, logging, and testing tasks

Would you like me to continue with the complete plan, or would you prefer to start execution with the tasks completed so far?


---

### Remaining Phase 2 Tasks (Summary)

**Task 10-12: File Upload & Import Endpoint**
- Add file upload UI component to BracketCreate page
- Implement POST /api/v1/brackets/import endpoint
- Parse YAML/JSON, resolve team names using BracketValidator
- Integration tests for file import

**Task 13-15: Sync Service Refactoring**
- Extract sync logic from sync.py endpoint into sync_service.py
- Refactor endpoint to call service
- Unit tests for sync service

**Task 16-18: Celery Setup**
- Add Redis and Celery services to docker-compose.yml
- Create celery_app.py and celeryconfig.py
- Create polling task in app/tasks/polling.py
- Tests for Celery task execution

**Task 19-21: Frontend Bracket Creation**
- Build BracketPicker component (interactive 63-game picker)
- Build BracketCreate page with tabs (picker vs upload)
- Update BracketsIndex with "Create New Bracket" button
- Manual testing of full creation flow

---

## PHASE 3: INTELLIGENCE & POLISH

### Task 22-24: Notification System
- Add last_notified_event field to Game model (Alembic migration)
- Create notification_scheduler.py service
- Create notifications.py Celery task
- Add notification config to settings
- Unit tests for notification formatting

### Task 25-27: Logging & Error Handling
- Create logging.conf with structured logging
- Improve error handling in ESPN client
- Add logging throughout services and tasks
- Integration tests verify logs

### Task 28-32: Comprehensive Testing
- Write test_scoring_engine.py (unit tests)
- Write test_notification_formatter.py (unit tests)
- Write test_celery.py (integration tests)
- Set up GitHub Actions CI (.github/workflows/test.yml)
- Achieve 70%+ coverage on critical paths

### Task 33: End-to-End Verification
- Load full tournament
- Create 3 brackets via UI
- Verify Celery polling works
- Trigger all notification types
- Run 48-hour stability test
- Document any issues found

---

## Execution Notes

**Task Granularity:** Each task above represents 5-15 minutes of work. Within each task, steps should take 2-5 minutes (write test → run failing → implement → run passing → commit).

**Testing Approach:** TDD throughout - write failing test first, implement minimal code to pass, refactor if needed.

**Checkpoints:** Commit after each task. Push after each phase complete. Review Phase 1 results before starting Phase 2.

**Reference Skills:**
- @superpowers:test-driven-development for testing guidance
- @superpowers:verification-before-completion before claiming tasks done

---

## Plan Review Required

This plan requires review by plan-document-reviewer subagent before execution.

