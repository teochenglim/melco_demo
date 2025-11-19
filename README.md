# 🎰 Casino Gaming Loyalty System

Real-time casino gaming loyalty rewards powered by **RisingWave** and **Redpanda**.

## 🚀 Quick Start

```bash
# Start the demo
./scripts/run-demo.sh

# Or use make commands
make demo          # Complete demo with data generation
make start         # Start services only
make inject        # Start data injection (5 events/sec)
make dashboard     # Open dashboard at http://localhost:8501
make stop          # Stop all services
```

**That's it!** The dashboard will start showing real-time rewards in ~30 seconds.

### What It Does
- Automatically starts Redpanda (Kafka), RisingWave (Stream Processor), and Streamlit (Dashboard)
- Creates Kafka topics and RisingWave schema automatically
- Generates realistic casino transaction data
- Displays real-time loyalty rewards based on spending/losses

## 📋 Loyalty Rewards

Real-time rewards based on member activity:

| Reward | Trigger | Prize |
|--------|---------|-------|
| **🏨 VIP Hotel** | Spent ≥ $5,000 today | Free hotel room (1 night) |
| **🍹 Consolation** | Lost ≥ $1,000 today | Premium drink voucher |

## 🏗️ Architecture

```
┌──────────────┐      ┌────────────┐      ┌─────────────┐      ┌────────────┐
│   Python     │─────▶│  Redpanda  │─────▶│ RisingWave  │◀────▶│ Streamlit  │
│  Generator   │      │   (Kafka)  │      │  (Stream    │      │ Dashboard  │
└──────────────┘      └────────────┘      │  Processor) │      └────────────┘
                                           └─────────────┘
```

**4 Services:**
- **Redpanda** - Kafka-compatible message broker (port 19092)
- **RisingWave** - Stream processor with PostgreSQL protocol (port 4566)
- **Streamlit** - Real-time dashboard (port 8501)
- **Console** - Redpanda web UI (port 8080)

**No PostgreSQL needed** - Streamlit connects directly to RisingWave!

## 📊 How to Generate Data

The demo script automatically starts the data generator, but you can control it manually:

### Automatic (Recommended)
```bash
./scripts/run-demo.sh
# Generator starts automatically at 5 events/sec
```

### Manual Control

**Start data injection:**
```bash
make inject              # 5 events/sec (runs in container, no Python needed!)
make inject-fast         # 10 events/sec

# Or with Docker directly:
docker run --rm --network risingwave_casino-net \
  -v $(PWD)/data-generator/casino_events_generator.py:/app/casino_events_generator.py:ro \
  python:3.11-slim sh -c "pip install -q kafka-python && \
  python /app/casino_events_generator.py --mode kafka --rate 5 --broker redpanda:9092"
```

**Stop:** Press `Ctrl+C` in the generator terminal

**Check if data is flowing:**
```bash
# Query RisingWave directly
docker exec -i streamlit-dashboard psql -h risingwave -p 4566 -d dev -U root -c \
  "SELECT COUNT(*) FROM member_daily_summary;"
```

### Data Generator Details

The generator creates realistic casino transactions:

**Game Types:**
- Slots (40% of bets, 45% win rate, 8% house edge)
- Blackjack (25% of bets, 48% win rate, 2% house edge)
- Roulette (20% of bets, 47% win rate, 5.3% house edge)
- Poker (15% of bets, 46% win rate, 5% house edge)

**Member Types:**
- High Rollers (IDs 1001-1005): Bet 50-100% of max, normal luck
- Regular Players (IDs 1006-1010): Bet 10-30% of max, normal luck
- Unlucky Players (IDs 1011-1015): Bet 30-60% of max, **win only 35% as often** (guaranteed to lose for drink offers!)

**Transaction Types:**
- `bet` - Money wagered
- `win` - Money won
- Realistic house edges ensure casino profit over time

## 🎮 Using the Demo

### View the Dashboard
```bash
make dashboard
# Opens http://localhost:8501
```

**Tabs:**
1. **🏨 Hotel Room Offers** - Members who spent ≥ $5,000
2. **🍹 Drink Offers** - Members who lost ≥ $1,000
3. **📊 Analytics** - Overall stats and charts
4. **👥 All Members** - Complete member activity

**Features:**
- Auto-refresh every 10 seconds (configurable)
- Adjust reward thresholds in sidebar
- Download member data as CSV

### View Kafka Messages
```bash
make console
# Opens http://localhost:8080
```

Navigate to **Topics → gaming-transactions** to see raw messages.

### Query RisingWave Directly
```bash
# Connect with psql
psql -h localhost -p 4566 -d dev -U root

# Or via container
docker exec -i streamlit-dashboard psql -h risingwave -p 4566 -d dev -U root
```

**Example queries:**
```sql
-- All member summaries
SELECT * FROM member_daily_summary ORDER BY total_spend DESC;

-- Hotel offers
SELECT * FROM hotel_room_offers ORDER BY total_spend DESC;

-- Drink offers
SELECT * FROM drink_offers ORDER BY loss_amount DESC;

-- Game statistics
SELECT * FROM game_stats ORDER BY house_edge DESC;
```

## 🛠️ Available Commands

```bash
make help          # Show all commands
make demo          # Run complete demo
make start         # Start services only
make stop          # Stop all services
make restart       # Restart services
make clean         # Remove everything
make check         # Health check
make status        # Show service status
make logs          # View all logs
make dashboard     # Open Streamlit dashboard
make console       # Open Redpanda Console
make inject        # Start data injection (5/sec)
make inject-fast   # Start data injection (10/sec)
```

## 📐 Data Schema

### Source: gaming_transactions
```sql
CREATE SOURCE gaming_transactions (
    transaction_id BIGINT,
    member_id BIGINT,
    member_name VARCHAR,
    transaction_type VARCHAR,  -- 'bet' or 'win'
    amount DECIMAL,
    game_type VARCHAR,         -- 'slot', 'blackjack', 'roulette', 'poker'
    transaction_time TIMESTAMP,
    WATERMARK FOR transaction_time AS transaction_time - INTERVAL '10' SECOND
) WITH (
    connector = 'kafka',
    topic = 'gaming-transactions',
    properties.bootstrap.server = 'redpanda:9092'
) FORMAT PLAIN ENCODE JSON;
```

### View: member_daily_summary
Aggregates transactions per member using **TUMBLE** windows:
- `total_spend` - Total bets
- `total_winnings` - Total wins
- `net_amount` - Winnings minus bets
- `transaction_count` - Number of transactions
- `window_start`, `window_end` - Window boundaries

**Window Size:** 5 minutes (for demo - see data immediately!)
- For production, change to `INTERVAL '1' DAY` in setup_risingwave.sql

## 🔧 Troubleshooting

### Dashboard shows "No data yet"
```bash
# 1. Check if generator is running
ps aux | grep casino_generator

# 2. Start generator manually
make inject

# 3. Verify data in RisingWave (wait 10-15 seconds)
docker exec -i streamlit-dashboard psql -h risingwave -p 4566 -d dev -U root -c \
  "SELECT COUNT(*) FROM member_daily_summary;"
```

### Services not starting
```bash
# Check status
make status

# View logs
make logs

# Restart everything
make restart
```

### Reset everything
```bash
make clean
./scripts/run-demo.sh
```

### Port conflicts
If ports 4566, 8501, 8080, or 19092 are in use:
```bash
# Stop the demo
make stop

# Kill processes using the ports
lsof -ti:8501 | xargs kill -9
lsof -ti:4566 | xargs kill -9

# Restart
./scripts/run-demo.sh
```

## 🎯 Key Features

### 1. No Kafka Connect Required
RisingWave connects **directly** to Kafka using native connectors:
```sql
CREATE SOURCE ... WITH (
    connector = 'kafka',  -- Built-in!
    topic = 'gaming-transactions',
    properties.bootstrap.server = 'redpanda:9092'
)
```

### 2. Watermark-Based Windowing
```sql
-- 1-day tumbling windows with 10-second late arrival tolerance
CREATE MATERIALIZED VIEW member_daily_summary AS
SELECT ...
FROM TUMBLE(gaming_transactions, transaction_time, INTERVAL '1' DAY)
GROUP BY member_id, member_name, window_start, window_end
EMIT ON WINDOW CLOSE;
```

### 3. Real-Time Materialized Views
- `member_daily_summary` - Daily aggregates per member
- `hotel_room_offers` - Members who spent ≥ $5,000
- `drink_offers` - Members who lost ≥ $1,000
- `game_stats` - Real-time game performance
- `member_leaderboard` - All-time rankings

## 📦 Requirements

- Docker & Docker Compose
- 8GB RAM recommended

**That's it!** No Python installation needed - the data generator runs in a container.

## 🎬 What Happens When You Run the Demo

1. **Services Start** (10-15 seconds)
   - Redpanda (Kafka broker)
   - RisingWave (stream processor)
   - Streamlit (dashboard)
   - Console (Redpanda UI)

2. **Setup** (5 seconds)
   - Kafka topic `gaming-transactions` created
   - RisingWave schema initialized (source + 5 materialized views)

3. **Data Generation Begins**
   - Python generator produces casino transactions
   - 5 events/sec by default
   - Sent to Kafka topic

4. **Real-Time Processing**
   - RisingWave consumes from Kafka
   - Aggregates data in 1-day tumbling windows
   - Updates materialized views continuously

5. **Dashboard Updates**
   - Streamlit queries RisingWave every 10 seconds
   - Shows live rewards and analytics
   - No delays, sub-second latency!

## 📝 Project Structure

```
.
├── docker-compose.yml                    # Services orchestration
├── Makefile                              # Quick commands (make help)
├── README.md                             # This file
│
├── scripts/                              # Utility scripts
│   ├── run-demo.sh                       # Main demo orchestrator
│   └── check-demo.sh                     # Health checker
│
├── streamlit/                            # Dashboard service
│   ├── Dockerfile.streamlit              # Container definition
│   ├── streamlit_app.py                  # Dashboard application
│   ├── requirements.txt                  # Python dependencies
│   └── entrypoint.sh                     # Init script (auto-loads schema)
│
├── risingwave/                           # Stream processor config
│   ├── setup_risingwave.sql              # Database schema & views
│   └── init-risingwave.sh                # Manual init script
│
├── redpanda/                             # Kafka broker config
│   └── init-redpanda.sh                  # Topic creation script
│
└── data-generator/                       # Event generator
    └── casino_events_generator.py        # Casino transaction simulator
```

## 💡 Tips

**Adjust reward thresholds:** Use the sidebar in the Streamlit dashboard

**See more data faster:**
```bash
make inject-fast  # 10 events/sec instead of 5
```

**View raw Kafka messages:**
```bash
docker exec redpanda rpk topic consume gaming-transactions --num 10
```

**Check RisingWave materialized views:**
```bash
docker exec -i streamlit-dashboard psql -h risingwave -p 4566 -d dev -U root -c \
  "SHOW MATERIALIZED VIEWS;"
```

## 🎓 Learn More

This demo showcases:
- **Stream Processing** - RisingWave's SQL-based stream processing
- **Watermarks** - Handling late-arriving events
- **Tumbling Windows** - Time-based aggregations
- **Kafka Integration** - Native Kafka source connector
- **Real-Time Dashboards** - Streamlit + PostgreSQL protocol

**RisingWave Docs:** https://docs.risingwave.com
**Redpanda Docs:** https://docs.redpanda.com

---

**Made to showcase RisingWave + Redpanda streaming**

🎰 Happy streaming!
