FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files (modular structure)
COPY . .

# Expose Streamlit port
EXPOSE 8501

# Run entrypoint script (initializes RisingWave + starts Streamlit)
ENTRYPOINT ["/app/entrypoint.sh"]
