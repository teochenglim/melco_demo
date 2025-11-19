# Casino Gaming Transaction Generator

A FastAPI-based transaction generator service for realistic casino gaming transactions.

## Key Features

- **Auto-Start**: Automatically generates data at 5 events/sec on startup
- **FastAPI REST API**: Control data generation via HTTP endpoints
- **Start/Stop Control**: Start and stop generation with simple curl commands
- **Dynamic Rate Control**: Adjust events per second on the fly (without restart)
- **Status Monitoring**: Check generator status via REST API
- **Schema Initialization**: Automatically initializes RisingWave schema on startup
- **Modular Architecture**: Separated configuration, simulation, and production logic
- **No Volume Mounts**: All files copied during Docker build for portability
- **Pre-installed Dependencies**: fastapi, uvicorn, kafka-python, psql installed in Dockerfile
- **Realistic Simulation**: House edges, win probabilities, and member types

## Project Structure

```
data-generator/
├── Dockerfile                 # Container definition (FastAPI service)
├── init.sh                    # Entrypoint script (RisingWave init + auto-start)
├── api.py                     # FastAPI REST API endpoints (auto-starts at 5/sec)
├── setup_risingwave.sql       # RisingWave schema (5-minute windows)
├── generate.py                # CLI entry point (legacy)
├── config.py                  # Configuration & constants
├── casino_simulator.py        # Core simulation logic
├── producers.py               # Kafka & batch producers
└── requirements.txt           # Python dependencies (fastapi, uvicorn, kafka-python)
```

## Features

### Modular Architecture
- **Separation of Concerns**: Configuration, simulation, and production are separated
- **Reusability**: Import and use components in other projects
- **Configurability**: Easy to adjust game types, members, probabilities
- **Testability**: Each module can be tested independently

### Core Modules

#### `config.py`
All configuration in one place:
```python
from config import MEMBERS, GAMES, KAFKA_TOPIC

# Access configuration
print(f"Topic: {KAFKA_TOPIC}")
print(f"Games: {GAMES.keys()}")
```

#### `casino_simulator.py`
Core casino simulation logic:
```python
from casino_simulator import CasinoSimulator

simulator = CasinoSimulator()
transactions = simulator.generate_bet()  # Returns [bet] or [bet, win]
```

#### `producers.py`
Multiple production modes:
```python
from producers import run_kafka_producer, run_batch_mode

# Stream to Kafka
run_kafka_producer(events_per_second=10)

# Generate batch
run_batch_mode(num_events=1000)
```

## Running the Generator

### In Docker (Recommended)
```bash
# Start the FastAPI service
docker-compose up data-generator

# Service automatically:
# 1. Waits for Redpanda and RisingWave to be ready
# 2. Initializes RisingWave schema (5-minute windows)
# 3. Starts generating data at 5 events/sec
#
# No manual intervention needed!
# Service runs on http://localhost:8000
```

### Using REST API

#### Start Generation
```bash
# Note: Generator auto-starts at 5 events/sec on container startup
# Only use this if you stopped it manually

curl -X POST http://localhost:8000/start
```

#### Get Current Rate
```bash
# View current event generation rate
curl http://localhost:8000/rate
```

#### Update Rate (Increase/Decrease)
```bash
# Simple GET request - set rate to 10 events/sec
curl http://localhost:8000/rate/10

# Decrease rate to 2 events/sec
curl http://localhost:8000/rate/2

# Or use PATCH with JSON body
curl -X PATCH http://localhost:8000/rate \
  -H "Content-Type: application/json" \
  -d '{"rate": 10}'
```

#### Stop Generation
```bash
curl -X POST http://localhost:8000/stop
```

#### Check Status
```bash
curl http://localhost:8000/status
```

#### Health Check
```bash
curl http://localhost:8000/health
```

### With Make Commands
```bash
# Use Makefile shortcuts for easy access
make inject           # Start at 5 events/sec
make inject-fast      # Start at 10 events/sec
make inject-stop      # Stop generation
make inject-status    # Check status
```

### API Documentation
Once the service is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--mode` | `kafka` or `batch` | `kafka` |
| `--rate` | Events per second (kafka mode) | `5` |
| `--count` | Number of events (batch mode) | `1000` |
| `--broker` | Kafka broker address | `localhost:19092` |

## Examples

### Stream at High Rate
```bash
python generate.py --rate 20
```

### Generate Test Data
```bash
python generate.py --mode batch --count 5000 > test_data.json
```

### Use with Different Kafka Broker
```bash
python generate.py --broker kafka.example.com:9092
```

## Configuration

### Adding New Games
Edit `config.py`:
```python
GAMES = {
    'baccarat': {
        'house_edge': 0.01,
        'min_bet': 100,
        'max_bet': 5000,
        'win_multiplier': (0.95, 1.95),
        'popularity': 0.10
    },
    # ... existing games
}
```

### Adding New Members
Edit `config.py`:
```python
MEMBERS = [
    (1016, "New Member"),
    # ... existing members
]
```

### Adjusting Win Probabilities
Edit `config.py`:
```python
WIN_PROBABILITIES = {
    'slot': 0.50,  # Increase slot win rate
    # ... other games
}
```

## Architecture Benefits

### Modular Design
- ✅ Separated into 4 focused modules
- ✅ Each module < 150 lines
- ✅ Easy to test, maintain, and extend
- ✅ Reusable components
- ✅ Clear separation of concerns

### Docker Optimization
- ✅ All files copied at build time (no volume mounts)
- ✅ kafka-python pre-installed in Dockerfile
- ✅ Faster container startup
- ✅ No runtime dependency installation
- ✅ Portable images

## Extending the Generator

### Add Custom Transaction Types
Modify `casino_simulator.py`:
```python
def generate_cashout(self, member_id, amount):
    return {
        'transaction_type': 'cashout',
        'amount': amount,
        # ... other fields
    }
```

### Add Custom Output Formats
Modify `producers.py`:
```python
def run_csv_producer(filename):
    simulator = CasinoSimulator()
    with open(filename, 'w') as f:
        # Write CSV format
        pass
```

### Add Monitoring
```python
from casino_simulator import CasinoSimulator

simulator = CasinoSimulator()
stats = {'wins': 0, 'losses': 0}

for _ in range(1000):
    transactions = simulator.generate_bet()
    if len(transactions) > 1:  # Has win
        stats['wins'] += 1
    else:
        stats['losses'] += 1

print(f"Win rate: {stats['wins'] / 1000 * 100}%")
```
