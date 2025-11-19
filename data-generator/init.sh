#!/bin/bash
set -e

echo "=== Casino Demo Initialization ==="
export PATH=$PATH:/usr/local/bin

# 1. Wait for Redpanda to be ready
echo "▶ Waiting for Redpanda to be ready..."
until rpk cluster info --brokers redpanda:9092 2>/dev/null; do
    sleep 2
done
echo "✓ Redpanda is ready"

# 2. Create Kafka topic
echo "▶ Creating Kafka topic: gaming-transactions..."
rpk topic create gaming-transactions --brokers redpanda:9092 || echo "  Topic already exists"
echo "✓ Kafka topic ready"

# 3. Wait for RisingWave to be ready
echo "▶ Waiting for RisingWave to be ready..."
until psql -h risingwave -p 4566 -d dev -U root -c '\q' 2>/dev/null; do
    sleep 2
done
echo "✓ RisingWave is ready"

# 4. Initialize RisingWave schema
echo "▶ Initializing RisingWave schema..."
if psql -h risingwave -p 4566 -d dev -U root -f /app/setup_risingwave.sql 2>&1 | tee /tmp/rw_init.log; then
    echo "✓ RisingWave schema initialized successfully"
else
    echo "⚠ Schema initialization had errors (may be normal if schema already exists)"
    cat /tmp/rw_init.log
fi

echo "=== Initialization Complete ==="
echo ""
echo "▶ Starting data generator API..."

# 5. Start the FastAPI application
exec uvicorn api:app --host 0.0.0.0 --port 8000
