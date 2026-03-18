from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.db.models import Bracket, Game
from app.services.espn_client import espn_client
from app.services.scoring_engine import ScoringEngine

router = APIRouter()


class SyncResponse(BaseModel):
    """Sync response model."""

    message: str
    games_updated: int


@router.post("/sync", response_model=SyncResponse)
async def sync_espn_data(db: Session = Depends(get_db)):
    """
    Manually trigger ESPN data sync.
    Fetches latest game data and updates database.
    """
    games_updated = 0

    try:
        # Fetch today's games from ESPN
        events = await espn_client.get_tournament_games()

        for event in events:
            for competition in event.competitions:
                # Find game in database by ESPN ID
                game = db.query(Game).filter(Game.espn_id == event.id).first()

                if game:
                    # Update game scores and status
                    if len(competition.competitors) >= 2:
                        home_competitor = next((c for c in competition.competitors if c.homeAway == "home"), None)
                        away_competitor = next((c for c in competition.competitors if c.homeAway == "away"), None)

                        if home_competitor and home_competitor.score:
                            game.home_score = int(home_competitor.score)

                        if away_competitor and away_competitor.score:
                            game.away_score = int(away_competitor.score)

                        # Update status
                        status_type = competition.status.get("type", {}).get("name", "")
                        if status_type == "STATUS_FINAL":
                            game.status = "completed"
                        elif status_type == "STATUS_IN_PROGRESS":
                            game.status = "in_progress"
                        else:
                            game.status = "scheduled"

                        games_updated += 1

        db.commit()

        # Recalculate all bracket scores
        brackets = db.query(Bracket).all()
        for bracket in brackets:
            engine = ScoringEngine(db)
            engine.calculate_bracket_score(bracket.id)

        return SyncResponse(message=f"Successfully synced ESPN data", games_updated=games_updated)

    except Exception as e:
        return SyncResponse(message=f"Error syncing data: {str(e)}", games_updated=0)
