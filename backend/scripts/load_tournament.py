"""Load tournament data from YAML file into database."""
import sys
from pathlib import Path
from datetime import datetime

import yaml
from sqlalchemy import select
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

    # Validate regions exist first, then check their content
    regions = data["regions"]

    # Validate region content before checking count
    for region in regions:
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

    # Now check region count
    if len(regions) != 4:
        raise ValueError("Must have exactly 4 regions")

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
    stmt = select(Tournament).where(Tournament.year == tournament_data["year"])
    existing = db.execute(stmt).scalar_one_or_none()
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
