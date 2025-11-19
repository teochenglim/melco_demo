"""
Kafka/Redpanda producers for casino transactions
"""
import json
import time
import sys
from kafka import KafkaProducer
from casino_simulator import CasinoSimulator
from config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_TOPIC, EVENTS_PER_SECOND, GAMES, MEMBERS


def format_transaction_output(transaction):
    """
    Format transaction for console output with colors

    Args:
        transaction: Transaction dict

    Returns:
        str: Formatted string for console
    """
    emoji = "💰" if transaction['transaction_type'] == 'win' else "🎲"
    color = "\033[92m" if transaction['transaction_type'] == 'win' else "\033[94m"
    reset = "\033[0m"

    return (f"{color}{emoji} {transaction['member_name']:20} | "
            f"{transaction['game_type']:10} | "
            f"{transaction['transaction_type']:5} | "
            f"${transaction['amount']:8.2f} | "
            f"{transaction['transaction_time']}{reset}")


def run_kafka_producer(events_per_second=EVENTS_PER_SECOND, bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS):
    """
    Send transactions to Kafka/Redpanda in real-time

    Args:
        events_per_second: Rate of event generation
        bootstrap_servers: Kafka broker addresses
    """
    print(f"🎰 Starting Casino Gaming Transaction Generator")
    print(f"📡 Kafka: {bootstrap_servers}")
    print(f"📊 Topic: {KAFKA_TOPIC}")
    print(f"⚡ Events per second: {events_per_second}")
    print(f"🎮 Games: {', '.join(GAMES.keys())}")
    print(f"👥 Members: {len(MEMBERS)}")
    print("-" * 70)

    producer = KafkaProducer(
        bootstrap_servers=bootstrap_servers,
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
                print(format_transaction_output(transaction))

            time.sleep(1.0 / events_per_second)

    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down producer...")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        producer.flush()
        producer.close()
        print("✅ Producer closed cleanly")


def run_batch_mode(num_events=1000):
    """
    Generate batch events and print to console (JSON format)

    Args:
        num_events: Number of events to generate
    """
    print(f"🎰 Generating {num_events} casino transactions...")
    print("=" * 70)

    simulator = CasinoSimulator()

    for i in range(num_events):
        transactions = simulator.generate_bet()

        for transaction in transactions:
            print(json.dumps(transaction))

        if (i + 1) % 100 == 0:
            print(f"# Generated {i + 1}/{num_events} events...", file=sys.stderr)
