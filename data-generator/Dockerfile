FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY casino_events_generator.py .

# Make script executable
RUN chmod +x casino_events_generator.py

# Default command runs in kafka mode with redpanda broker
CMD ["python", "casino_events_generator.py", "--mode", "kafka", "--broker", "redpanda:9092", "--rate", "5"]
