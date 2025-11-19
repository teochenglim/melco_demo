#!/bin/bash
set -e

# Initialize RisingWave schema
echo "Waiting for RisingWave to be ready..."
until psql -h risingwave -p 4566 -d dev -U root -c '\q' 2>/dev/null; do
    sleep 2
done

echo "RisingWave is ready! Initializing schema..."
if psql -h risingwave -p 4566 -d dev -U root -f /app/setup_risingwave.sql; then
    echo "✓ RisingWave schema initialized successfully!"
else
    echo "⚠ Schema initialization failed or already exists"
fi

# Start Streamlit
echo "Starting Streamlit dashboard..."
exec streamlit run streamlit_app.py --server.port=8501 --server.address=0.0.0.0
