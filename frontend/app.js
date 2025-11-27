// API Configuration
const API_BASE = window.location.hostname === 'localhost'
    ? 'http://localhost:8000'
    : '/api';

const WS_BASE = window.location.hostname === 'localhost'
    ? 'ws://localhost:8000'
    : `ws://${window.location.host}`;

// Game State
let gameState = {
    gameCode: null,
    playerId: null,
    playerName: null,
    socket: null,
    selectedDomino: null,
    currentState: null
};

// DOM Elements
const screens = {
    welcome: document.getElementById('welcome-screen'),
    createGame: document.getElementById('create-game-screen'),
    joinGame: document.getElementById('join-game-screen'),
    lobby: document.getElementById('lobby-screen'),
    game: document.getElementById('game-screen')
};

// Screen Navigation
function showScreen(screenName) {
    Object.values(screens).forEach(screen => screen.classList.remove('active'));
    screens[screenName].classList.add('active');
}

// Message Display
function showMessage(message) {
    document.getElementById('message-text').textContent = message;
    document.getElementById('message-overlay').classList.remove('hidden');
}

function hideMessage() {
    document.getElementById('message-overlay').classList.add('hidden');
}

// API Calls
async function apiCall(endpoint, method = 'GET', data = null) {
    const options = {
        method,
        headers: {
            'Content-Type': 'application/json'
        }
    };

    if (data && method !== 'GET') {
        options.body = JSON.stringify(data);
    }

    const url = method === 'GET' && data
        ? `${API_BASE}${endpoint}?${new URLSearchParams(data)}`
        : `${API_BASE}${endpoint}`;

    const response = await fetch(url, options);
    return await response.json();
}

// WebSocket Connection
function connectWebSocket() {
    if (gameState.socket) {
        gameState.socket.close();
    }

    const wsUrl = `${WS_BASE}/ws/${gameState.gameCode}/${gameState.playerId}`;
    gameState.socket = new WebSocket(wsUrl);

    gameState.socket.onopen = () => {
        console.log('WebSocket connected');
    };

    gameState.socket.onmessage = (event) => {
        const message = JSON.parse(event.data);
        handleWebSocketMessage(message);
    };

    gameState.socket.onerror = (error) => {
        console.error('WebSocket error:', error);
    };

    gameState.socket.onclose = () => {
        console.log('WebSocket disconnected');
    };
}

function handleWebSocketMessage(message) {
    console.log('WebSocket message:', message);

    switch (message.type) {
        case 'game_started':
            loadGameState();
            showScreen('game');
            break;
        case 'domino_played':
            loadGameState();
            break;
        case 'domino_drawn':
            loadGameState();
            break;
        case 'player_disconnected':
            showMessage('A player has disconnected');
            break;
    }
}

// Create Game
document.getElementById('create-game-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const playerName = document.getElementById('player-name-create').value;
    const startingDouble = parseInt(document.getElementById('starting-double').value);

    try {
        // Create game
        const createResult = await apiCall('/api/games/create', 'POST', { starting_double: startingDouble });
        gameState.gameCode = createResult.game_code;

        // Join the game
        const joinResult = await apiCall(`/api/games/${gameState.gameCode}/join`, 'POST', { player_name: playerName });

        if (joinResult.success) {
            gameState.playerId = joinResult.player_id;
            gameState.playerName = playerName;

            connectWebSocket();
            showLobby();
        }
    } catch (error) {
        showMessage('Error creating game: ' + error.message);
    }
});

// Join Game
document.getElementById('join-game-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const playerName = document.getElementById('player-name-join').value;
    const gameCode = document.getElementById('game-code').value.toUpperCase();

    try {
        const result = await apiCall(`/api/games/${gameCode}/join`, 'POST', { player_name: playerName });

        if (result.success) {
            gameState.gameCode = gameCode;
            gameState.playerId = result.player_id;
            gameState.playerName = playerName;

            connectWebSocket();
            showLobby();
        } else {
            showMessage(result.error || 'Could not join game');
        }
    } catch (error) {
        showMessage('Error joining game: ' + error.message);
    }
});

// Show Lobby
async function showLobby() {
    showScreen('lobby');
    document.getElementById('game-code-display').textContent = `Game Code: ${gameState.gameCode}`;
    await updateLobby();
}

async function updateLobby() {
    try {
        const state = await apiCall(`/api/games/${gameState.gameCode}/state`, 'GET', { player_id: gameState.playerId });

        const playerList = document.getElementById('player-list');
        playerList.innerHTML = '';

        state.players.forEach(player => {
            const li = document.createElement('li');
            li.textContent = player.name;
            playerList.appendChild(li);
        });
    } catch (error) {
        console.error('Error updating lobby:', error);
    }
}

// Start Game
document.getElementById('start-game-btn').addEventListener('click', async () => {
    try {
        const result = await apiCall(`/api/games/${gameState.gameCode}/start`, 'POST');
        if (result.success) {
            await loadGameState();
            showScreen('game');
        } else {
            showMessage(result.error || 'Could not start game');
        }
    } catch (error) {
        showMessage('Error starting game: ' + error.message);
    }
});

// Load Game State
async function loadGameState() {
    try {
        const state = await apiCall(`/api/games/${gameState.gameCode}/state`, 'GET', { player_id: gameState.playerId });
        gameState.currentState = state;
        renderGameState(state);
    } catch (error) {
        console.error('Error loading game state:', error);
    }
}

// Render Game State
function renderGameState(state) {
    // Update header
    document.getElementById('current-round').textContent = `Round: ${state.current_round}`;
    const currentPlayer = state.players[state.current_player_index];
    document.getElementById('current-player').textContent = `Current Player: ${currentPlayer.name}`;
    document.getElementById('player-score').textContent = `Your Score: ${state.player.score}`;

    // Render center domino
    const centerDomino = document.getElementById('center-domino');
    centerDomino.innerHTML = `
        <div class="domino-pip">${state.starting_double}</div>
        <div class="domino-pip">${state.starting_double}</div>
    `;

    // Render Mexican Train
    renderTrain('mexican-train-dominoes', state.mexican_train);

    // Render player trains
    renderPlayerTrains(state.players);

    // Render player hand
    renderHand(state.player.hand);

    // Update boneyard count
    document.getElementById('boneyard-count').textContent = state.boneyard_size;

    // Enable/disable controls
    const isMyTurn = state.is_current_player;
    document.getElementById('draw-btn').disabled = !isMyTurn;
    document.getElementById('end-turn-btn').disabled = !isMyTurn;
}

function renderTrain(containerId, dominoes) {
    const container = document.getElementById(containerId);
    container.innerHTML = '';

    dominoes.forEach(domino => {
        const dominoEl = createDominoElement(domino, false);
        container.appendChild(dominoEl);
    });
}

function renderPlayerTrains(players) {
    const container = document.getElementById('player-trains');
    container.innerHTML = '';

    players.forEach(player => {
        const trainDiv = document.createElement('div');
        trainDiv.className = 'player-train';
        if (player.train_open) trainDiv.classList.add('open');
        if (player.index === gameState.currentState.current_player_index) {
            trainDiv.classList.add('current-player');
        }

        trainDiv.innerHTML = `
            <h3>${player.name}'s Train ${player.train_open ? '(Open)' : ''}</h3>
            <div class="train-dominoes" data-player-index="${player.index}"></div>
        `;

        container.appendChild(trainDiv);

        // Render dominoes (for now just show count)
        const trainDominoes = trainDiv.querySelector('.train-dominoes');
        trainDominoes.textContent = `${player.train_size} dominoes`;
    });
}

function renderHand(hand) {
    const container = document.getElementById('hand-dominoes');
    container.innerHTML = '';

    hand.forEach((domino, index) => {
        const dominoEl = createDominoElement(domino, true);
        dominoEl.dataset.index = index;
        dominoEl.addEventListener('click', () => selectDomino(domino, dominoEl));
        container.appendChild(dominoEl);
    });
}

function createDominoElement(domino, clickable = false) {
    const div = document.createElement('div');
    div.className = 'domino';
    if (domino.left === domino.right) div.classList.add('double');

    div.innerHTML = `
        <div class="domino-pip">${domino.left}</div>
        <div class="domino-pip">${domino.right}</div>
    `;

    return div;
}

function selectDomino(domino, element) {
    // Deselect all
    document.querySelectorAll('.domino.selected').forEach(el => el.classList.remove('selected'));

    if (gameState.selectedDomino === domino) {
        gameState.selectedDomino = null;
    } else {
        gameState.selectedDomino = domino;
        element.classList.add('selected');
        showMessage('Select a train to play this domino');
    }
}

// Draw Domino
document.getElementById('draw-btn').addEventListener('click', async () => {
    try {
        const result = await apiCall(`/api/games/${gameState.gameCode}/draw`, 'POST', {
            player_id: gameState.playerId
        });

        if (result.success) {
            await loadGameState();
        } else {
            showMessage(result.error || 'Could not draw domino');
        }
    } catch (error) {
        showMessage('Error drawing domino: ' + error.message);
    }
});

// Navigation Buttons
document.getElementById('create-game-btn').addEventListener('click', () => showScreen('createGame'));
document.getElementById('join-game-btn').addEventListener('click', () => showScreen('joinGame'));
document.getElementById('back-from-create').addEventListener('click', () => showScreen('welcome'));
document.getElementById('back-from-join').addEventListener('click', () => showScreen('welcome'));
document.getElementById('leave-game-btn').addEventListener('click', () => {
    if (gameState.socket) gameState.socket.close();
    showScreen('welcome');
});
document.getElementById('message-close').addEventListener('click', hideMessage);

// Initialize
showScreen('welcome');
