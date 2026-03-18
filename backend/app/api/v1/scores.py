from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.services.scoring_engine import ScoringEngine

router = APIRouter()


class ScoreResponse(BaseModel):
    """Score response model."""

    bracket_id: int
    total_points: int
    correct_picks: int
    total_picks: int
    possible_points: int


class BracketHealthResponse(BaseModel):
    """Bracket health response model."""

    bracket_id: int
    current_points: int
    max_possible_points: int
    health_percentage: float
    correct_picks: int
    total_picks: int
    accuracy: float


@router.get("/scores/{bracket_id}", response_model=ScoreResponse)
async def get_bracket_score(bracket_id: int, db: Session = Depends(get_db)):
    """Get calculated score for a bracket."""
    engine = ScoringEngine(db)

    try:
        scores = engine.calculate_bracket_score(bracket_id)
        return ScoreResponse(bracket_id=bracket_id, **scores)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/scores/{bracket_id}/health", response_model=BracketHealthResponse)
async def get_bracket_health(bracket_id: int, db: Session = Depends(get_db)):
    """Get bracket health metrics."""
    engine = ScoringEngine(db)

    try:
        health = engine.get_bracket_health(bracket_id)
        return BracketHealthResponse(bracket_id=bracket_id, **health)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
