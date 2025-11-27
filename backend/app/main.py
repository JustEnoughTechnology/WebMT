from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager
from typing import Dict, Set
import json

from app.config import get_settings
from app.database import init_db, get_session
from app.game_manager import game_manager
from app import models


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    yield
    # Shutdown
    pass


app = FastAPI(title=settings.app_name, lifespan=lifespan)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, game_code: str):
        await websocket.accept()
        if game_code not in self.active_connections:
            self.active_connections[game_code] = set()
        self.active_connections[game_code].add(websocket)

    def disconnect(self, websocket: WebSocket, game_code: str):
        if game_code in self.active_connections:
            self.active_connections[game_code].discard(websocket)
            if not self.active_connections[game_code]:
                del self.active_connections[game_code]

    async def broadcast(self, game_code: str, message: dict):
        if game_code in self.active_connections:
            for connection in self.active_connections[game_code]:
                try:
                    await connection.send_json(message)
                except:
                    pass


manager = ConnectionManager()


@app.get("/")
async def root():
    return {"message": "Mexican Train Game API", "status": "running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.post("/api/games/create")
async def create_game(starting_double: int = 12, session: AsyncSession = Depends(get_session)):
    """Create a new game"""
    game_code = await game_manager.create_game(session, starting_double)
    return {"game_code": game_code}


@app.post("/api/games/{game_code}/join")
async def join_game(game_code: str, player_name: str, session: AsyncSession = Depends(get_session)):
    """Join an existing game"""
    result = await game_manager.join_game(session, game_code, player_name)
    if not result:
        return {"success": False, "error": "Game not found or full"}
    return {"success": True, **result}


@app.post("/api/games/{game_code}/start")
async def start_game(game_code: str, session: AsyncSession = Depends(get_session)):
    """Start a game"""
    success = await game_manager.start_game(session, game_code)
    if success:
        # Notify all connected clients
        await manager.broadcast(game_code, {
            "type": "game_started",
            "game_code": game_code
        })
        return {"success": True}
    return {"success": False, "error": "Cannot start game"}


@app.get("/api/games/{game_code}/state")
async def get_game_state(game_code: str, player_id: int, session: AsyncSession = Depends(get_session)):
    """Get current game state for a player"""
    state = await game_manager.get_game_state(session, game_code, player_id)
    if not state:
        return {"error": "Game or player not found"}
    return state


@app.post("/api/games/{game_code}/play")
async def play_domino(
    game_code: str,
    player_id: int,
    domino: dict,
    train_target: str,
    target_player_index: int = None,
    session: AsyncSession = Depends(get_session)
):
    """Play a domino"""
    result = await game_manager.play_domino(
        session, game_code, player_id, domino, train_target, target_player_index
    )

    if result.get("success"):
        # Broadcast game update
        await manager.broadcast(game_code, {
            "type": "domino_played",
            "player_id": player_id,
            "domino": domino,
            "train_target": train_target,
            "round_won": result.get("round_won", False)
        })

    return result


@app.post("/api/games/{game_code}/draw")
async def draw_domino(game_code: str, player_id: int, session: AsyncSession = Depends(get_session)):
    """Draw a domino from the boneyard"""
    result = await game_manager.draw_domino(session, game_code, player_id)

    if result.get("success"):
        await manager.broadcast(game_code, {
            "type": "domino_drawn",
            "player_id": player_id
        })

    return result


@app.websocket("/ws/{game_code}/{player_id}")
async def websocket_endpoint(websocket: WebSocket, game_code: str, player_id: int):
    """WebSocket connection for real-time game updates"""
    await manager.connect(websocket, game_code)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            # Handle different message types
            if message.get("type") == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        manager.disconnect(websocket, game_code)
        await manager.broadcast(game_code, {
            "type": "player_disconnected",
            "player_id": player_id
        })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
