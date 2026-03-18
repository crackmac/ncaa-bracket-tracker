import json

import yaml
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.db.models import Bracket, Pick, Game, Tournament, User, Team
from app.services.bracket_validator import BracketValidator, ValidationError

router = APIRouter()


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


class BracketImportResponse(BaseModel):
    """Bracket import response."""
    id: int
    name: str
    bracket_type: str
    total_picks: int


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


@router.post("/brackets", response_model=BracketCreateResponse, status_code=201)
async def create_bracket(bracket_data: BracketCreate, db: Session = Depends(get_db)):
    """Create a new bracket with picks."""
    validator = BracketValidator()

    try:
        # Get active tournament
        stmt = select(Tournament).order_by(Tournament.year.desc())
        tournament = db.execute(stmt).scalar_one_or_none()
        if not tournament:
            raise HTTPException(status_code=404, detail="No active tournament found")

        # MVP: Get first user (auth in Phase 3)
        stmt2 = select(User)
        user = db.execute(stmt2).scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="No user found")

        # Validate picks
        picks_dicts = [p.model_dump() for p in bracket_data.picks]

        # Get all games for tournament
        stmt3 = select(Game).where(Game.tournament_id == tournament.id)
        total_games = len(db.execute(stmt3).scalars().all())

        try:
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

        # Fetch all games for tournament once (avoid N+1 queries)
        games_stmt = select(Game).where(Game.tournament_id == tournament.id)
        games = {g.id: g for g in db.execute(games_stmt).scalars().all()}

        # Create picks
        for pick_data in bracket_data.picks:
            # Get game from pre-fetched dictionary
            game = games.get(pick_data.game_id)
            if not game:
                raise HTTPException(status_code=400, detail=f"Game {pick_data.game_id} not found")

            # Validate predicted winner is playing in this game
            if pick_data.predicted_winner_id not in [game.home_team_id, game.away_team_id]:
                raise HTTPException(
                    status_code=400,
                    detail=f"Team {pick_data.predicted_winner_id} is not playing in game {pick_data.game_id}"
                )

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
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create bracket: {str(e)}")


@router.post("/brackets/import", response_model=BracketImportResponse, status_code=201)
async def import_bracket(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Import bracket from YAML or JSON file."""
    validator = BracketValidator()

    try:
        # Read file content
        content = await file.read()

        # Parse based on file extension
        if file.filename.endswith('.yaml') or file.filename.endswith('.yml'):
            data = yaml.safe_load(content)
        elif file.filename.endswith('.json'):
            data = json.loads(content)
        else:
            raise HTTPException(status_code=400, detail="File must be .yaml, .yml, or .json")

        # Validate structure
        if not isinstance(data, dict) or 'name' not in data or 'bracket_type' not in data or 'picks' not in data:
            raise HTTPException(status_code=400, detail="Invalid file format. Expected: name, bracket_type, picks")

        # Get tournament and user (same as create_bracket)
        stmt = select(Tournament).order_by(Tournament.year.desc())
        tournament = db.execute(stmt).scalar_one_or_none()
        if not tournament:
            raise HTTPException(status_code=404, detail="No active tournament found")

        stmt2 = select(User)
        user = db.execute(stmt2).scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="No user found")

        # Build team lookup maps
        teams_stmt = select(Team).where(Team.tournament_id == tournament.id)
        teams_list = db.execute(teams_stmt).scalars().all()
        teams_by_id = {t.id: t for t in teams_list}
        teams_by_name = {}
        for t in teams_list:
            name_lower = t.name.lower()
            if name_lower not in teams_by_name:
                teams_by_name[name_lower] = []
            teams_by_name[name_lower].append(t.id)

        # Resolve winners in picks
        resolved_picks = []
        for pick in data['picks']:
            winner = pick.get('winner') or pick.get('predicted_winner_id')
            if not winner:
                raise HTTPException(status_code=400, detail="Each pick must have 'winner' or 'predicted_winner_id'")

            # Resolve team reference
            try:
                if isinstance(winner, int):
                    team_id = winner
                elif str(winner).isdigit():
                    team_id = int(winner)
                else:
                    team_id = validator.resolve_team_by_name(winner, teams_by_name)
            except ValidationError as e:
                raise HTTPException(status_code=400, detail=str(e))

            resolved_picks.append({
                'game_id': pick['game_id'],
                'predicted_winner_id': team_id
            })

        # Validate picks
        try:
            games_stmt = select(Game).where(Game.tournament_id == tournament.id)
            total_games = len(db.execute(games_stmt).scalars().all())
            validator.validate_picks(resolved_picks, total_games=total_games)
        except ValidationError as e:
            raise HTTPException(status_code=400, detail=str(e))

        # Fetch all games (avoid N+1)
        games = {g.id: g for g in db.execute(games_stmt).scalars().all()}

        # Create bracket
        bracket = Bracket(
            user_id=user.id,
            tournament_id=tournament.id,
            name=data['name'],
            bracket_type=data['bracket_type'],
            total_points=0,
            possible_points=0,
        )
        db.add(bracket)
        db.flush()

        # Create picks
        for pick_data in resolved_picks:
            game = games.get(pick_data['game_id'])
            if not game:
                raise HTTPException(status_code=400, detail=f"Game {pick_data['game_id']} not found")

            # Validate winner is in game
            if pick_data['predicted_winner_id'] not in [game.home_team_id, game.away_team_id]:
                raise HTTPException(
                    status_code=400,
                    detail=f"Team {pick_data['predicted_winner_id']} is not playing in game {pick_data['game_id']}"
                )

            from app.services.scoring_engine import ROUND_POINTS
            points_value = ROUND_POINTS.get(game.round, 10)

            pick = Pick(
                bracket_id=bracket.id,
                game_id=pick_data['game_id'],
                predicted_winner_id=pick_data['predicted_winner_id'],
                points_value=points_value,
                points_earned=0,
            )
            db.add(pick)

        db.commit()

        return BracketImportResponse(
            id=bracket.id,
            name=bracket.name,
            bracket_type=bracket.bracket_type,
            total_picks=len(resolved_picks),
        )
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to import bracket: {str(e)}")
