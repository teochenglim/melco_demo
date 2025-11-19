#!/bin/bash
set -e

# Wait for RisingWave to be ready
echo "Waiting for RisingWave to be ready..."
until psql -h risingwave -p 4566 -d dev -U root -c '\q' 2>/dev/null; do
    sleep 2
done

echo "RisingWave is ready!"

# Start Streamlit dashboard
echo "Starting Streamlit dashboard..."
exec streamlit run app.py --server.port=8501 --server.address=0.0.0.0
