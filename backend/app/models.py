from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, JSON, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True, nullable=False)
    status = Column(String, default="waiting")  # waiting, active, completed
    current_round = Column(Integer, default=1)
    current_player_index = Column(Integer, default=0)
    starting_double = Column(Integer, default=12)  # Starting domino (e.g., 12 for double-12)
    boneyard = Column(JSON, default=list)  # List of remaining dominoes
    mexican_train = Column(JSON, default=list)  # List of dominoes on Mexican train
    mexican_train_open = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    players = relationship("Player", back_populates="game", cascade="all, delete-orphan")


class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False)
    name = Column(String, nullable=False)
    player_index = Column(Integer, nullable=False)  # Order in the game (0, 1, 2, ...)
    hand = Column(JSON, default=list)  # List of dominoes in hand
    train = Column(JSON, default=list)  # Player's personal train
    train_open = Column(Boolean, default=False)  # Whether train is marked
    score = Column(Integer, default=0)
    is_connected = Column(Boolean, default=True)
    session_id = Column(String, nullable=True)  # WebSocket session ID

    game = relationship("Game", back_populates="players")
