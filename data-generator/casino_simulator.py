"""
Casino Simulator - Core logic for generating realistic casino transactions
"""
import random
from datetime import datetime
from config import MEMBERS, UNLUCKY_MEMBERS, GAMES, WIN_PROBABILITIES, UNLUCKY_WIN_MULTIPLIER


class CasinoSimulator:
    """Simulates casino gaming transactions with realistic behavior"""

    def __init__(self):
        self.transaction_id = 1
        self.member_states = {}  # Track member balances and behavior

    def select_game(self):
        """Select game based on popularity weights"""
        games = list(GAMES.keys())
        weights = [GAMES[g]['popularity'] for g in games]
        return random.choices(games, weights=weights)[0]

    def select_member(self):
        """
        Select a member with realistic distribution:
        - High rollers: 40% of transactions
        - Regular players: 30% of transactions
        - Unlucky players: 30% of transactions
        """
        rand = random.random()

        if rand < 0.4:
            # High rollers (40% of transactions)
            return random.choice(MEMBERS[:5])
        elif rand < 0.7:
            # Regular players (30% of transactions)
            return random.choice(MEMBERS[5:10])
        else:
            # Unlucky players (30% of transactions - play often to lose money)
            return random.choice(MEMBERS[10:])

    def calculate_bet_amount(self, member_id, game_info):
        """
        Calculate bet amount based on member type

        Args:
            member_id: Member ID
            game_info: Game configuration dict

        Returns:
            float: Bet amount rounded to 2 decimals
        """
        if member_id <= 1005:  # High rollers
            bet_amount = random.uniform(game_info['max_bet'] * 0.5, game_info['max_bet'])
        elif member_id in UNLUCKY_MEMBERS:  # Unlucky players bet medium-high
            bet_amount = random.uniform(game_info['max_bet'] * 0.3, game_info['max_bet'] * 0.6)
        else:  # Regular players
            bet_amount = random.uniform(game_info['min_bet'], game_info['max_bet'] * 0.3)

        return round(bet_amount, 2)

    def should_win(self, member_id, game_type):
        """
        Determine if a bet should win based on game probabilities

        Args:
            member_id: Member ID
            game_type: Type of game

        Returns:
            bool: True if player wins
        """
        win_probability = WIN_PROBABILITIES[game_type]

        # Unlucky members win less often (for drink consolation offers)
        if member_id in UNLUCKY_MEMBERS:
            win_probability *= UNLUCKY_WIN_MULTIPLIER

        return random.random() < win_probability

    def calculate_win_amount(self, bet_amount, game_info):
        """
        Calculate win amount based on game multipliers

        Args:
            bet_amount: Original bet amount
            game_info: Game configuration dict

        Returns:
            float: Win amount rounded to 2 decimals
        """
        win_multiplier = random.uniform(*game_info['win_multiplier'])
        return round(bet_amount * win_multiplier, 2)

    def generate_bet(self):
        """
        Generate a bet transaction (and potential win transaction)

        Returns:
            list: List of transaction dicts (bet + optional win)
        """
        member_id, member_name = self.select_member()
        game_type = self.select_game()
        game_info = GAMES[game_type]

        # Calculate bet amount
        bet_amount = self.calculate_bet_amount(member_id, game_info)

        # Create bet transaction
        transaction = {
            'transaction_id': self.transaction_id,
            'member_id': member_id,
            'member_name': member_name,
            'transaction_type': 'bet',
            'amount': bet_amount,
            'game_type': game_type,
            'transaction_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        self.transaction_id += 1

        # Determine if this bet wins
        if self.should_win(member_id, game_type):
            win_amount = self.calculate_win_amount(bet_amount, game_info)

            if win_amount > 0:
                win_transaction = self.generate_win(member_id, member_name, win_amount, game_type)
                return [transaction, win_transaction]

        return [transaction]

    def generate_win(self, member_id, member_name, amount, game_type):
        """
        Generate a win transaction

        Args:
            member_id: Member ID
            member_name: Member name
            amount: Win amount
            game_type: Type of game

        Returns:
            dict: Win transaction
        """
        transaction = {
            'transaction_id': self.transaction_id,
            'member_id': member_id,
            'member_name': member_name,
            'transaction_type': 'win',
            'amount': amount,
            'game_type': game_type,
            'transaction_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        self.transaction_id += 1
        return transaction
