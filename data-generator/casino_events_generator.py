#!/usr/bin/env python3
"""
Casino Gaming Transaction Generator
Generates realistic casino gaming data to Kafka/Redpanda
"""

import json
import random
import time
from datetime import datetime, timedelta
from kafka import KafkaProducer
import sys

# Configuration
KAFKA_BOOTSTRAP_SERVERS = ['localhost:19092']  # Redpanda external port
KAFKA_TOPIC = 'gaming-transactions'
EVENTS_PER_SECOND = 5

# Member pool (simulated casino members)
# IDs 1001-1005: High rollers (big bets, normal luck)
# IDs 1006-1010: Regular players (medium bets, normal luck)
# IDs 1011-1015: Unlucky players (will lose consistently for drink offers)
MEMBERS = [
    (1001, "John Smith"),
    (1002, "Emily Johnson"),
    (1003, "Michael Chen"),
    (1004, "Sarah Williams"),
    (1005, "David Martinez"),
    (1006, "Lisa Anderson"),
    (1007, "James Taylor"),
    (1008, "Maria Garcia"),
    (1009, "Robert Lee"),
    (1010, "Jennifer Wang"),
    (1011, "Christopher Brown"),    # Unlucky
    (1012, "Amanda Davis"),          # Unlucky
    (1013, "Daniel Kim"),            # Unlucky
    (1014, "Jessica Miller"),        # Unlucky
    (1015, "Matthew Wilson"),        # Unlucky
]

# Unlucky members who lose more often (for drink offers)
UNLUCKY_MEMBERS = {1011, 1012, 1013, 1014, 1015}

# Game types and their house edges / bet ranges
GAMES = {
    'slot': {
        'house_edge': 0.08,  # 8% house edge
        'min_bet': 10,
        'max_bet': 500,
        'win_multiplier': (0, 20),  # Can win 0x to 20x
        'popularity': 0.4  # 40% of all bets
    },
    'blackjack': {
        'house_edge': 0.02,  # 2% house edge (skilled players)
        'min_bet': 25,
        'max_bet': 1000,
        'win_multiplier': (0.95, 1.5),  # Typically win ~1x or lose
        'popularity': 0.25
    },
    'roulette': {
        'house_edge': 0.053,  # 5.3% house edge
        'min_bet': 10,
        'max_bet': 500,
        'win_multiplier': (0, 35),  # Can win up to 35x on single number
        'popularity': 0.20
    },
    'poker': {
        'house_edge': 0.05,  # 5% rake
        'min_bet': 50,
        'max_bet': 2000,
        'win_multiplier': (0, 5),
        'popularity': 0.15
    }
}

class CasinoSimulator:
    def __init__(self):
        self.transaction_id = 1
        self.member_states = {}  # Track member balances and behavior
        
    def select_game(self):
        """Select game based on popularity"""
        games = list(GAMES.keys())
        weights = [GAMES[g]['popularity'] for g in games]
        return random.choices(games, weights=weights)[0]
    
    def select_member(self):
        """Select a member (some members play more than others)"""
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
    
    def generate_bet(self):
        """Generate a bet transaction"""
        member_id, member_name = self.select_member()
        game_type = self.select_game()
        game_info = GAMES[game_type]
        
        # Determine bet amount (some members bet bigger)
        if member_id <= 1005:  # High rollers
            bet_amount = random.uniform(game_info['max_bet'] * 0.5, game_info['max_bet'])
        elif member_id in UNLUCKY_MEMBERS:  # Unlucky players bet medium-high
            bet_amount = random.uniform(game_info['max_bet'] * 0.3, game_info['max_bet'] * 0.6)
        else:  # Regular players
            bet_amount = random.uniform(game_info['min_bet'], game_info['max_bet'] * 0.3)
        
        bet_amount = round(bet_amount, 2)
        
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
        # Win probability adjusted to create realistic house edge
        # For slots: ~45% win rate to achieve 8% house edge with variable payouts
        # For other games: adjusted similarly
        win_probabilities = {
            'slot': 0.45,      # Win 45% of time, but payouts average to 92% RTP
            'blackjack': 0.48, # Win 48% of time (2% house edge)
            'roulette': 0.47,  # Win 47% of time (5.3% house edge with payouts)
            'poker': 0.46      # Win 46% of time (5% house edge)
        }

        # Unlucky members win less often (for drink consolation offers)
        win_probability = win_probabilities[game_type]
        if member_id in UNLUCKY_MEMBERS:
            win_probability *= 0.35  # Unlucky members win only 35% as often

        if random.random() < win_probability:
            # Player wins
            win_multiplier = random.uniform(*game_info['win_multiplier'])
            win_amount = round(bet_amount * win_multiplier, 2)

            if win_amount > 0:
                return [transaction, self.generate_win(member_id, member_name, win_amount, game_type)]

        return [transaction]
    
    def generate_win(self, member_id, member_name, amount, game_type):
        """Generate a win transaction"""
        return {
            'transaction_id': self.transaction_id,
            'member_id': member_id,
            'member_name': member_name,
            'transaction_type': 'win',
            'amount': amount,
            'game_type': game_type,
            'transaction_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

def run_producer():
    """Send transactions to Kafka/Redpanda"""
    print(f"🎰 Starting Casino Gaming Transaction Generator")
    print(f"📡 Kafka: {KAFKA_BOOTSTRAP_SERVERS}")
    print(f"📊 Topic: {KAFKA_TOPIC}")
    print(f"⚡ Events per second: {EVENTS_PER_SECOND}")
    print(f"🎮 Games: {', '.join(GAMES.keys())}")
    print(f"👥 Members: {len(MEMBERS)}")
    print("-" * 70)
    
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        acks='all'
    )
    
    simulator = CasinoSimulator()
    
    try:
        while True:
            # Generate multiple transactions (bet + potential win)
            transactions = simulator.generate_bet()
            
            for transaction in transactions:
                producer.send(KAFKA_TOPIC, value=transaction)
                
                # Pretty print
                emoji = "💰" if transaction['transaction_type'] == 'win' else "🎲"
                color = "\033[92m" if transaction['transaction_type'] == 'win' else "\033[94m"
                reset = "\033[0m"
                
                print(f"{color}{emoji} {transaction['member_name']:20} | "
                      f"{transaction['game_type']:10} | "
                      f"{transaction['transaction_type']:5} | "
                      f"${transaction['amount']:8.2f} | "
                      f"{transaction['transaction_time']}{reset}")
                
                simulator.transaction_id += 1
            
            time.sleep(1.0 / EVENTS_PER_SECOND)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down producer...")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        producer.flush()
        producer.close()
        print("✅ Producer closed cleanly")

def run_batch_mode(num_events=1000):
    """Generate batch events and print to console"""
    print(f"🎰 Generating {num_events} casino transactions...")
    print("=" * 70)
    
    simulator = CasinoSimulator()
    
    for i in range(num_events):
        transactions = simulator.generate_bet()
        
        for transaction in transactions:
            print(json.dumps(transaction))
        
        if (i + 1) % 100 == 0:
            print(f"# Generated {i + 1}/{num_events} events...", file=sys.stderr)

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Casino Gaming Transaction Generator')
    parser.add_argument('--mode', choices=['kafka', 'batch'], default='kafka',
                      help='kafka: send to Kafka | batch: print JSON to stdout')
    parser.add_argument('--count', type=int, default=1000,
                      help='Number of events for batch mode')
    parser.add_argument('--rate', type=int, default=5,
                      help='Events per second for kafka mode')
    parser.add_argument('--broker', type=str, default='localhost:19092',
                      help='Kafka broker address (default: localhost:19092)')

    args = parser.parse_args()

    EVENTS_PER_SECOND = args.rate
    KAFKA_BOOTSTRAP_SERVERS = [args.broker]

    if args.mode == 'kafka':
        run_producer()
    else:
        run_batch_mode(args.count)
