FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    curl \
    unzip \
    netcat-openbsd \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install rpk - detect architecture and download correct version
RUN ARCH=$(dpkg --print-architecture) && \
    case "$ARCH" in \
        "amd64") \
            curl -LO https://github.com/redpanda-data/redpanda/releases/latest/download/rpk-linux-amd64.zip \
            && unzip -q rpk-linux-amd64.zip \
            && rm rpk-linux-amd64.zip \
            ;; \
        "arm64") \
            curl -LO https://github.com/redpanda-data/redpanda/releases/latest/download/rpk-linux-arm64.zip \
            && unzip -q rpk-linux-arm64.zip \
            && rm rpk-linux-arm64.zip \
            ;; \
        *) echo "Unsupported architecture: $ARCH"; exit 1 ;; \
    esac && \
    chmod +x rpk && \
    mv rpk /usr/local/bin/

# Copy application files
COPY . .

# Expose FastAPI port
EXPOSE 8000

# Run initialization script then start FastAPI server
CMD ["./init.sh"]