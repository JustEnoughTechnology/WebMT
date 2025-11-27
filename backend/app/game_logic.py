import random
from typing import List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class Domino:
    """Represents a single domino tile"""
    left: int
    right: int

    def flip(self) -> 'Domino':
        """Returns a new domino with sides flipped"""
        return Domino(self.right, self.left)

    def is_double(self) -> bool:
        """Check if this is a double domino"""
        return self.left == self.right

    def total(self) -> int:
        """Sum of both sides"""
        return self.left + self.right

    def to_dict(self) -> dict:
        return {"left": self.left, "right": self.right}

    @classmethod
    def from_dict(cls, data: dict) -> 'Domino':
        return cls(left=data["left"], right=data["right"])

    def __eq__(self, other):
        if not isinstance(other, Domino):
            return False
        return (self.left == other.left and self.right == other.right) or \
               (self.left == other.right and self.right == other.left)

    def __hash__(self):
        return hash((min(self.left, self.right), max(self.left, self.right)))

    def __repr__(self):
        return f"[{self.left}|{self.right}]"


class DominoSet:
    """Manages a set of dominoes"""

    @staticmethod
    def create_double_twelve_set() -> List[Domino]:
        """Creates a standard double-12 domino set (91 tiles)"""
        dominoes = []
        for i in range(13):  # 0 to 12
            for j in range(i, 13):
                dominoes.append(Domino(i, j))
        return dominoes

    @staticmethod
    def create_double_nine_set() -> List[Domino]:
        """Creates a double-9 domino set (55 tiles)"""
        dominoes = []
        for i in range(10):  # 0 to 9
            for j in range(i, 10):
                dominoes.append(Domino(i, j))
        return dominoes


class Train:
    """Represents a train of dominoes"""

    def __init__(self, engine: int, is_mexican: bool = False):
        self.engine = engine  # The starting number for this train
        self.dominoes: List[Domino] = []
        self.is_mexican = is_mexican
        self.is_open = is_mexican  # Mexican train always starts open

    def get_end(self) -> int:
        """Get the open end of the train"""
        if not self.dominoes:
            return self.engine
        last_domino = self.dominoes[-1]
        # The end is the side that's not connected to the previous domino
        if len(self.dominoes) == 1:
            # First domino: the end is the side not matching the engine
            return last_domino.right if last_domino.left == self.engine else last_domino.left
        # For subsequent dominoes, we need to track which end is open
        # We'll maintain that the 'right' side is always the open end after placement
        return last_domino.right

    def can_play(self, domino: Domino) -> bool:
        """Check if a domino can be played on this train"""
        end = self.get_end()
        return domino.left == end or domino.right == end

    def play_domino(self, domino: Domino) -> bool:
        """
        Attempt to play a domino on this train.
        Returns True if successful, False otherwise.
        """
        end = self.get_end()
        if domino.left == end:
            self.dominoes.append(domino)
            return True
        elif domino.right == end:
            self.dominoes.append(domino.flip())
            return True
        return False

    def to_dict(self) -> dict:
        return {
            "engine": self.engine,
            "dominoes": [d.to_dict() for d in self.dominoes],
            "is_mexican": self.is_mexican,
            "is_open": self.is_open
        }


class MexicanTrainGame:
    """Core game logic for Mexican Train"""

    def __init__(self, num_players: int, starting_double: int = 12):
        self.num_players = num_players
        self.starting_double = starting_double
        self.current_round = starting_double
        self.boneyard: List[Domino] = []
        self.mexican_train: Train = Train(starting_double, is_mexican=True)
        self.player_trains: List[Train] = []
        self.player_hands: List[List[Domino]] = []
        self.player_scores: List[int] = [0] * num_players
        self.current_player = 0

    def setup_round(self, round_number: Optional[int] = None):
        """Set up a new round"""
        if round_number is not None:
            self.current_round = round_number

        # Create and shuffle dominoes
        if self.starting_double == 12:
            all_dominoes = DominoSet.create_double_twelve_set()
        else:
            all_dominoes = DominoSet.create_double_nine_set()

        random.shuffle(all_dominoes)

        # Remove the starting double
        starting_domino = Domino(self.current_round, self.current_round)
        all_dominoes.remove(starting_domino)

        # Determine hand size based on number of players
        hand_sizes = {
            2: 16, 3: 16, 4: 15, 5: 14,
            6: 12, 7: 10, 8: 9
        }
        hand_size = hand_sizes.get(self.num_players, 10)

        # Deal hands
        self.player_hands = []
        for i in range(self.num_players):
            hand = all_dominoes[:hand_size]
            all_dominoes = all_dominoes[hand_size:]
            self.player_hands.append(hand)

        # Remaining dominoes go to boneyard
        self.boneyard = all_dominoes

        # Initialize trains
        self.mexican_train = Train(self.current_round, is_mexican=True)
        self.player_trains = [Train(self.current_round) for _ in range(self.num_players)]

        # Determine starting player (player with highest double if any, or random)
        self.current_player = self._determine_starting_player()

    def _determine_starting_player(self) -> int:
        """Determine which player starts the round"""
        # Could implement logic to find player with highest double
        # For now, just return 0
        return 0

    def can_play_domino(self, player_index: int, domino: Domino, train_target: str, target_player: Optional[int] = None) -> bool:
        """
        Check if a player can play a specific domino on a specific train.

        train_target can be: 'mexican', 'own', 'opponent'
        """
        if train_target == 'mexican':
            return self.mexican_train.can_play(domino)
        elif train_target == 'own':
            return self.player_trains[player_index].can_play(domino)
        elif train_target == 'opponent' and target_player is not None:
            if self.player_trains[target_player].is_open:
                return self.player_trains[target_player].can_play(domino)
        return False

    def play_domino(self, player_index: int, domino: Domino, train_target: str, target_player: Optional[int] = None) -> bool:
        """
        Play a domino from player's hand onto a train.
        Returns True if successful.
        """
        # Verify it's the player's turn
        if player_index != self.current_player:
            return False

        # Verify player has the domino
        if domino not in self.player_hands[player_index]:
            return False

        # Try to play on the specified train
        success = False
        if train_target == 'mexican':
            success = self.mexican_train.play_domino(domino)
        elif train_target == 'own':
            success = self.player_trains[player_index].play_domino(domino)
            # If successful on own train, close it
            if success:
                self.player_trains[player_index].is_open = False
        elif train_target == 'opponent' and target_player is not None:
            if self.player_trains[target_player].is_open:
                success = self.player_trains[target_player].play_domino(domino)

        if success:
            self.player_hands[player_index].remove(domino)

            # Check if player won the round
            if len(self.player_hands[player_index]) == 0:
                return True  # Round over

        return success

    def draw_from_boneyard(self, player_index: int) -> Optional[Domino]:
        """Player draws a domino from the boneyard"""
        if not self.boneyard:
            return None
        domino = self.boneyard.pop(0)
        self.player_hands[player_index].append(domino)
        return domino

    def end_turn(self, player_index: int, could_not_play: bool = False):
        """End the current player's turn"""
        if could_not_play:
            # Mark player's train as open
            self.player_trains[player_index].is_open = True

        # Move to next player
        self.current_player = (self.current_player + 1) % self.num_players

    def calculate_hand_score(self, hand: List[Domino]) -> int:
        """Calculate the score of a hand (sum of all pips)"""
        return sum(domino.total() for domino in hand)

    def end_round(self):
        """End the current round and calculate scores"""
        for i in range(self.num_players):
            self.player_scores[i] += self.calculate_hand_score(self.player_hands[i])
