from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.db.models import Game, Team

router = APIRouter()


class GameResponse(BaseModel):
    """Game response model."""

    id: int
    espn_id: str
    round: str
    region: str
    home_team_id: int
    away_team_id: int
    home_team_name: str
    away_team_name: str
    home_team_seed: int
    away_team_seed: int
    home_score: int | None
    away_score: int | None
    status: str
    is_upset: bool

    class Config:
        from_attributes = True


@router.get("/games", response_model=list[GameResponse])
async def list_games(db: Session = Depends(get_db)):
    """List all tournament games."""
    games = db.query(Game).all()

    result = []
    for game in games:
        home_team = db.query(Team).filter(Team.id == game.home_team_id).first()
        away_team = db.query(Team).filter(Team.id == game.away_team_id).first()

        if home_team and away_team:
            result.append(
                GameResponse(
                    id=game.id,
                    espn_id=game.espn_id,
                    round=game.round,
                    region=game.region,
                    home_team_id=home_team.id,
                    away_team_id=away_team.id,
                    home_team_name=home_team.name,
                    away_team_name=away_team.name,
                    home_team_seed=home_team.seed,
                    away_team_seed=away_team.seed,
                    home_score=game.home_score,
                    away_score=game.away_score,
                    status=game.status,
                    is_upset=game.is_upset,
                )
            )

    return result
