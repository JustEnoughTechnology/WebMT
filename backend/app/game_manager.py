from typing import Dict, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import Game, Player
from app.game_logic import MexicanTrainGame, Domino
import random
import string


class GameManager:
    """Manages active games in memory with database persistence"""

    def __init__(self):
        self.active_games: Dict[str, MexicanTrainGame] = {}

    def generate_game_code(self) -> str:
        """Generate a unique 6-character game code"""
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

    async def create_game(self, session: AsyncSession, starting_double: int = 12) -> str:
        """Create a new game and return the game code"""
        code = self.generate_game_code()

        # Create database entry
        db_game = Game(
            code=code,
            starting_double=starting_double,
            status="waiting"
        )
        session.add(db_game)
        await session.commit()
        await session.refresh(db_game)

        return code

    async def join_game(self, session: AsyncSession, game_code: str, player_name: str) -> Optional[dict]:
        """Add a player to a game"""
        # Get game from database
        result = await session.execute(
            select(Game).where(Game.code == game_code)
        )
        db_game = result.scalar_one_or_none()

        if not db_game or db_game.status != "waiting":
            return None

        # Check max players (8 for Mexican Train)
        player_count = len(db_game.players)
        if player_count >= 8:
            return None

        # Create player
        db_player = Player(
            game_id=db_game.id,
            name=player_name,
            player_index=player_count
        )
        session.add(db_player)
        await session.commit()
        await session.refresh(db_player)

        return {
            "game_code": game_code,
            "player_id": db_player.id,
            "player_index": db_player.player_index,
            "player_count": player_count + 1
        }

    async def start_game(self, session: AsyncSession, game_code: str) -> bool:
        """Start a game (must have at least 2 players)"""
        result = await session.execute(
            select(Game).where(Game.code == game_code)
        )
        db_game = result.scalar_one_or_none()

        if not db_game or db_game.status != "waiting":
            return False

        player_count = len(db_game.players)
        if player_count < 2:
            return False

        # Create in-memory game
        game = MexicanTrainGame(player_count, db_game.starting_double)
        game.setup_round(db_game.starting_double)
        self.active_games[game_code] = game

        # Update database
        db_game.status = "active"
        db_game.current_round = db_game.starting_double
        db_game.boneyard = [d.to_dict() for d in game.boneyard]
        db_game.mexican_train = game.mexican_train.to_dict()["dominoes"]

        # Update player hands
        for i, db_player in enumerate(db_game.players):
            db_player.hand = [d.to_dict() for d in game.player_hands[i]]
            db_player.train = []

        await session.commit()
        return True

    async def get_game_state(self, session: AsyncSession, game_code: str, player_id: int) -> Optional[dict]:
        """Get current game state for a specific player"""
        result = await session.execute(
            select(Game).where(Game.code == game_code)
        )
        db_game = result.scalar_one_or_none()

        if not db_game:
            return None

        # Find the requesting player
        player = next((p for p in db_game.players if p.id == player_id), None)
        if not player:
            return None

        # Get in-memory game if active
        game = self.active_games.get(game_code)

        return {
            "game_code": game_code,
            "status": db_game.status,
            "current_round": db_game.current_round,
            "current_player_index": db_game.current_player_index,
            "starting_double": db_game.starting_double,
            "player": {
                "id": player.id,
                "name": player.name,
                "index": player.player_index,
                "hand": player.hand,
                "score": player.score,
                "train_open": player.train_open
            },
            "players": [
                {
                    "name": p.name,
                    "index": p.player_index,
                    "hand_size": len(p.hand),
                    "score": p.score,
                    "train_open": p.train_open,
                    "train_size": len(p.train)
                }
                for p in sorted(db_game.players, key=lambda x: x.player_index)
            ],
            "mexican_train": db_game.mexican_train,
            "boneyard_size": len(db_game.boneyard) if db_game.boneyard else 0,
            "is_current_player": player.player_index == db_game.current_player_index
        }

    async def play_domino(
        self,
        session: AsyncSession,
        game_code: str,
        player_id: int,
        domino_data: dict,
        train_target: str,
        target_player_index: Optional[int] = None
    ) -> dict:
        """Process a domino play"""
        # Get game
        result = await session.execute(
            select(Game).where(Game.code == game_code)
        )
        db_game = result.scalar_one_or_none()

        if not db_game or db_game.status != "active":
            return {"success": False, "error": "Game not found or not active"}

        # Get player
        player = next((p for p in db_game.players if p.id == player_id), None)
        if not player:
            return {"success": False, "error": "Player not found"}

        # Get in-memory game
        game = self.active_games.get(game_code)
        if not game:
            return {"success": False, "error": "Game not in memory"}

        # Create domino
        domino = Domino.from_dict(domino_data)

        # Attempt play
        success = game.play_domino(player.player_index, domino, train_target, target_player_index)

        if success:
            # Update database
            player.hand = [d.to_dict() for d in game.player_hands[player.player_index]]
            db_game.mexican_train = [d.to_dict() for d in game.mexican_train.dominoes]

            # Update player trains
            for i, db_player in enumerate(db_game.players):
                db_player.train = [d.to_dict() for d in game.player_trains[i].dominoes]
                db_player.train_open = game.player_trains[i].is_open

            await session.commit()

            return {"success": True, "round_won": len(player.hand) == 0}

        return {"success": False, "error": "Invalid play"}

    async def draw_domino(self, session: AsyncSession, game_code: str, player_id: int) -> dict:
        """Player draws from boneyard"""
        result = await session.execute(
            select(Game).where(Game.code == game_code)
        )
        db_game = result.scalar_one_or_none()

        if not db_game or db_game.status != "active":
            return {"success": False, "error": "Game not found or not active"}

        player = next((p for p in db_game.players if p.id == player_id), None)
        if not player:
            return {"success": False, "error": "Player not found"}

        game = self.active_games.get(game_code)
        if not game:
            return {"success": False, "error": "Game not in memory"}

        domino = game.draw_from_boneyard(player.player_index)
        if not domino:
            return {"success": False, "error": "Boneyard is empty"}

        # Update database
        player.hand = [d.to_dict() for d in game.player_hands[player.player_index]]
        db_game.boneyard = [d.to_dict() for d in game.boneyard]
        await session.commit()

        return {"success": True, "domino": domino.to_dict()}


# Global game manager instance
game_manager = GameManager()
