#!/bin/bash
set -e

# Wait for Redpanda to be ready
echo "Waiting for Redpanda to be ready..."
until rpk cluster info --brokers localhost:9092 2>/dev/null; do
    sleep 2
done

# Create topic
echo "Creating Kafka topic 'gaming-transactions'..."
rpk topic create gaming-transactions \
    --brokers localhost:9092 \
    --partitions 3 \
    --replicas 1 2>/dev/null || echo "Topic already exists"

echo "✓ Redpanda initialization complete!"
