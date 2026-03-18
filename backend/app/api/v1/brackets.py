from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.db.models import Bracket, Pick

router = APIRouter()


class BracketResponse(BaseModel):
    """Bracket response model."""

    id: int
    name: str
    bracket_type: str
    total_points: int
    possible_points: int
    correct_picks: int
    total_picks: int

    class Config:
        from_attributes = True


class PickResponse(BaseModel):
    """Pick response model."""

    id: int
    game_id: int
    predicted_winner_id: int
    points_value: int
    points_earned: int
    is_correct: bool | None

    class Config:
        from_attributes = True


class BracketDetailResponse(BracketResponse):
    """Detailed bracket response with picks."""

    picks: list[PickResponse]


@router.get("/brackets", response_model=list[BracketResponse])
async def list_brackets(db: Session = Depends(get_db)):
    """List all brackets."""
    brackets = db.query(Bracket).all()

    result = []
    for bracket in brackets:
        # Count picks
        picks = db.query(Pick).filter(Pick.bracket_id == bracket.id).all()
        correct = sum(1 for p in picks if p.is_correct is True)

        result.append(
            BracketResponse(
                id=bracket.id,
                name=bracket.name,
                bracket_type=bracket.bracket_type,
                total_points=bracket.total_points,
                possible_points=bracket.possible_points,
                correct_picks=correct,
                total_picks=len(picks),
            )
        )

    return result


@router.get("/brackets/{bracket_id}", response_model=BracketDetailResponse)
async def get_bracket(bracket_id: int, db: Session = Depends(get_db)):
    """Get detailed bracket information including all picks."""
    bracket = db.query(Bracket).filter(Bracket.id == bracket_id).first()
    if not bracket:
        raise HTTPException(status_code=404, detail="Bracket not found")

    picks = db.query(Pick).filter(Pick.bracket_id == bracket_id).all()
    correct = sum(1 for p in picks if p.is_correct is True)

    pick_responses = [
        PickResponse(
            id=p.id,
            game_id=p.game_id,
            predicted_winner_id=p.predicted_winner_id,
            points_value=p.points_value,
            points_earned=p.points_earned,
            is_correct=p.is_correct,
        )
        for p in picks
    ]

    return BracketDetailResponse(
        id=bracket.id,
        name=bracket.name,
        bracket_type=bracket.bracket_type,
        total_points=bracket.total_points,
        possible_points=bracket.possible_points,
        correct_picks=correct,
        total_picks=len(picks),
        picks=pick_responses,
    )
