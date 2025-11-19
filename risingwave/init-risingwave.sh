#!/bin/bash
# Initialize RisingWave schema on startup

echo "Waiting for RisingWave to be ready..."
until psql -h risingwave -p 4566 -d dev -U root -c '\q' 2>/dev/null; do
    sleep 1
done

echo "RisingWave is ready! Initializing schema..."
psql -h risingwave -p 4566 -d dev -U root -f /app/setup_risingwave.sql

echo "RisingWave schema initialized successfully!"
