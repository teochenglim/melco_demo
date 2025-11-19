#!/usr/bin/env python3
"""
Casino Gaming Transaction Generator - Main Entry Point
Generates realistic casino gaming data to Kafka/Redpanda
"""
import argparse
import config
from producers import run_kafka_producer, run_batch_mode


def main():
    """Main entry point for the generator"""
    parser = argparse.ArgumentParser(
        description='Casino Gaming Transaction Generator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Stream to Kafka at 5 events/sec (default)
  python generate.py

  # Stream to Kafka at custom rate
  python generate.py --mode kafka --rate 10

  # Generate batch JSON output
  python generate.py --mode batch --count 1000

  # Use custom Kafka broker
  python generate.py --broker localhost:9092
        """
    )

    parser.add_argument(
        '--mode',
        choices=['kafka', 'batch'],
        default='kafka',
        help='kafka: stream to Kafka | batch: print JSON to stdout'
    )

    parser.add_argument(
        '--count',
        type=int,
        default=1000,
        help='Number of events for batch mode (default: 1000)'
    )

    parser.add_argument(
        '--rate',
        type=int,
        default=5,
        help='Events per second for kafka mode (default: 5)'
    )

    parser.add_argument(
        '--broker',
        type=str,
        default='localhost:19092',
        help='Kafka broker address (default: localhost:19092)'
    )

    args = parser.parse_args()

    # Update config based on arguments
    events_per_second = args.rate
    bootstrap_servers = [args.broker]

    # Run in selected mode
    if args.mode == 'kafka':
        run_kafka_producer(events_per_second, bootstrap_servers)
    else:
        run_batch_mode(args.count)


if __name__ == '__main__':
    main()
