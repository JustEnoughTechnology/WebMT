# Mexican Train Dominoes

A multiplayer Mexican Train dominoes game with a web frontend and Python backend.

## Features

- **Multiplayer Support**: 2-8 players per game
- **Real-time Gameplay**: WebSocket-based real-time updates
- **Persistent State**: SQLite database backing in-memory game state
- **Dockerized**: Full Docker support for development and deployment
- **Double-12 & Double-9**: Support for both domino sets

## Technology Stack

### Backend
- Python 3.11+
- FastAPI (REST API and WebSocket)
- SQLAlchemy (ORM with async support)
- SQLite (Database)
- uv (Package management)

### Frontend
- HTML5/CSS3/JavaScript (Vanilla)
- WebSocket client
- Responsive design

### Infrastructure
- Docker & Docker Compose
- Nginx (Frontend server and reverse proxy)

## Project Structure

```
WebMT/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI application
│   │   ├── config.py            # Configuration
│   │   ├── database.py          # Database setup
│   │   ├── models.py            # SQLAlchemy models
│   │   ├── game_logic.py        # Core game logic
│   │   └── game_manager.py      # Game state management
│   ├── tests/
│   ├── Dockerfile
│   ├── pyproject.toml
│   └── .env.example
├── frontend/
│   ├── index.html
│   ├── styles.css
│   ├── app.js
│   ├── nginx.conf
│   └── Dockerfile
├── docker-compose.yml           # Production compose file
└── docker-compose.dev.yml       # Development compose file
```

## Getting Started

### Prerequisites

- Docker and Docker Compose
- (Optional) uv for local Python development

### Development Setup

1. **Clone the repository**
   ```bash
   cd WebMT
   ```

2. **Set up environment variables**
   ```bash
   cd backend
   cp .env.example .env
   # Edit .env if needed
   ```

3. **Start the development environment**
   ```bash
   docker-compose -f docker-compose.dev.yml up --build
   ```

4. **Access the application**
   - Frontend: http://localhost:8080
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

### Production Deployment

```bash
docker-compose up -d --build
```

### Local Development (without Docker)

**Backend:**
```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload
```

**Frontend:**
Serve the frontend directory with any static file server, or use the nginx configuration.

## Game Rules

Mexican Train is a domino game played with a double-12 (or double-9) set. The objective is to be the first player to play all your dominoes.

### Basic Rules:
1. Each round starts with a double domino (12-12, 11-11, etc.)
2. Players take turns playing dominoes that match the open end of any train
3. Each player has their own personal train starting from the center
4. The Mexican Train is a communal train anyone can play on
5. If you can't play, you draw from the boneyard and your train becomes "open"
6. Other players can play on open trains
7. First player to empty their hand wins the round
8. Points are scored based on remaining dominoes

## API Endpoints

- `POST /api/games/create` - Create a new game
- `POST /api/games/{game_code}/join` - Join a game
- `POST /api/games/{game_code}/start` - Start a game
- `GET /api/games/{game_code}/state` - Get game state
- `POST /api/games/{game_code}/play` - Play a domino
- `POST /api/games/{game_code}/draw` - Draw from boneyard
- `WS /ws/{game_code}/{player_id}` - WebSocket connection

## Development

### Running Tests
```bash
cd backend
uv run pytest
```

### Code Formatting
```bash
cd backend
uv run black app/
uv run ruff check app/
```

## Future Enhancements

- [ ] User authentication and accounts
- [ ] Game history and statistics
- [ ] AI opponents
- [ ] Chat functionality
- [ ] Tournament mode
- [ ] Mobile app
- [ ] Sound effects and animations
- [ ] Multiple simultaneous games per user

## License

See LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
