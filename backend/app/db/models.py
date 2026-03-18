from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    """User model - for MVP, just one user."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    brackets: Mapped[list["Bracket"]] = relationship("Bracket", back_populates="user")


class Tournament(Base):
    """Tournament model - represents a March Madness tournament year."""

    __tablename__ = "tournaments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    year: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    start_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    teams: Mapped[list["Team"]] = relationship("Team", back_populates="tournament")
    games: Mapped[list["Game"]] = relationship("Game", back_populates="tournament")
    brackets: Mapped[list["Bracket"]] = relationship("Bracket", back_populates="tournament")


class Team(Base):
    """Team model - represents a team in the tournament."""

    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tournament_id: Mapped[int] = mapped_column(Integer, ForeignKey("tournaments.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    seed: Mapped[int] = mapped_column(Integer, nullable=False)
    region: Mapped[str] = mapped_column(String(50), nullable=False)
    espn_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    tournament: Mapped["Tournament"] = relationship("Tournament", back_populates="teams")


class Game(Base):
    """Game model - represents a single tournament game."""

    __tablename__ = "games"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tournament_id: Mapped[int] = mapped_column(Integer, ForeignKey("tournaments.id"), nullable=False)
    espn_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    round: Mapped[str] = mapped_column(String(50), nullable=False)  # Round 64, Round 32, Sweet 16, etc.
    region: Mapped[str] = mapped_column(String(50), nullable=False)

    home_team_id: Mapped[int] = mapped_column(Integer, ForeignKey("teams.id"), nullable=False)
    away_team_id: Mapped[int] = mapped_column(Integer, ForeignKey("teams.id"), nullable=False)

    home_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    away_score: Mapped[int | None] = mapped_column(Integer, nullable=True)

    status: Mapped[str] = mapped_column(String(50), nullable=False)  # scheduled, in_progress, completed
    last_notified_event: Mapped[str | None] = mapped_column(String, nullable=True)
    scheduled_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    is_upset: Mapped[bool] = mapped_column(Boolean, default=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tournament: Mapped["Tournament"] = relationship("Tournament", back_populates="games")
    home_team: Mapped["Team"] = relationship("Team", foreign_keys=[home_team_id])
    away_team: Mapped["Team"] = relationship("Team", foreign_keys=[away_team_id])
    picks: Mapped[list["Pick"]] = relationship("Pick", back_populates="game")


class Bracket(Base):
    """Bracket model - represents a user's tournament bracket."""

    __tablename__ = "brackets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    tournament_id: Mapped[int] = mapped_column(Integer, ForeignKey("tournaments.id"), nullable=False)

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    bracket_type: Mapped[str] = mapped_column(String(50), nullable=False)  # chalk, balanced, chaos, custom

    total_points: Mapped[int] = mapped_column(Integer, default=0)
    possible_points: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user: Mapped["User"] = relationship("User", back_populates="brackets")
    tournament: Mapped["Tournament"] = relationship("Tournament", back_populates="brackets")
    picks: Mapped[list["Pick"]] = relationship("Pick", back_populates="bracket")


class Pick(Base):
    """Pick model - represents a single game pick in a bracket."""

    __tablename__ = "picks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    bracket_id: Mapped[int] = mapped_column(Integer, ForeignKey("brackets.id"), nullable=False)
    game_id: Mapped[int] = mapped_column(Integer, ForeignKey("games.id"), nullable=False)

    predicted_winner_id: Mapped[int] = mapped_column(Integer, ForeignKey("teams.id"), nullable=False)
    points_value: Mapped[int] = mapped_column(Integer, nullable=False)  # Points available for this pick
    points_earned: Mapped[int] = mapped_column(Integer, default=0)

    is_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)  # None = not decided yet
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    bracket: Mapped["Bracket"] = relationship("Bracket", back_populates="picks")
    game: Mapped["Game"] = relationship("Game", back_populates="picks")
    predicted_winner: Mapped["Team"] = relationship("Team", foreign_keys=[predicted_winner_id])
