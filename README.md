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
make inject-rate   # Get current event generation rate
make inject-fast   # Increase to 10 events/sec
make inject-slow   # Decrease to 2 events/sec
make stop          # Stop all services
```

**That's it!** The dashboard will start showing real-time rewards in ~30 seconds.

### What It Does
- Automatically starts all 5 services (Redpanda, RisingWave, Streamlit, Console, Data Generator)
- RisingWave schema initialized automatically by data-generator entrypoint
- Kafka topics auto-created when data is first sent
- **Auto-generates** realistic casino transaction data at 5 events/sec (configurable)
- Displays real-time loyalty rewards with **5-minute window** intervals

## 📋 Loyalty Rewards

Real-time rewards based on member activity with watermark display:

| Reward | Trigger | Prize | Policy |
|--------|---------|-------|--------|
| **🏨 VIP Hotel** | Spent ≥ $5,000 in any interval | Free hotel room (1 night) | 1 per customer per day |
| **🍹 Consolation** | Lost ≥ $1,000 in any interval | Premium drink voucher | 1 per customer per day |

**Window Size:** 5-minute tumbling windows for real-time responsiveness
**Watermark Feature:** Dashboard displays data from the previous interval (e.g., during 0:00:10-0:00:20, shows 0:00:00-0:00:10 data)

## 🏗️ Architecture

```
┌──────────────┐      ┌────────────┐      ┌─────────────┐      ┌────────────┐
│   Python     │─────▶│  Redpanda  │─────▶│ RisingWave  │◀────▶│ Streamlit  │
│  Generator   │      │   (Kafka)  │      │  (Stream    │      │ Dashboard  │
└──────────────┘      └────────────┘      │  Processor) │      └────────────┘
                                           └─────────────┘
```

**5 Services:**
- **Redpanda** - Kafka-compatible message broker (port 19092)
- **RisingWave** - Stream processor with PostgreSQL protocol (port 4566)
- **Streamlit** - Real-time dashboard (port 8501)
- **Console** - Redpanda web UI (port 8080)
- **Data Generator** - FastAPI service with automatic data generation (port 8000)

**No PostgreSQL needed** - Streamlit connects directly to RisingWave!
**No init containers** - Schema initialization handled by data-generator entrypoint!
**Auto-generation** - Data generation starts automatically at 5 events/sec!
**REST API Control** - Adjust generation rate on the fly with simple curl commands!

## 📊 How to Generate Data

The demo script automatically starts the data generator, but you can control it manually:

### Automatic (Default)
```bash
./scripts/run-demo.sh
# Generator auto-starts at 5 events/sec
# No manual intervention needed!
```

### Manual Control

**Start data injection:**
```bash
make inject              # Start at 5 events/sec (default)
make inject-rate         # Get current event generation rate
make inject-fast         # Increase rate to 10 events/sec
make inject-slow         # Decrease rate to 2 events/sec
make inject-stop         # Stop generation
make inject-status       # Check status

# Or with curl directly:
# Start generator (default 5 events/sec)
curl -X POST http://localhost:8000/start

# Get current rate
curl http://localhost:8000/rate

# Increase/decrease rate dynamically (simple GET)
curl http://localhost:8000/rate/10  # Set to 10 events/sec
curl http://localhost:8000/rate/2   # Set to 2 events/sec

# Stop generator
curl -X POST http://localhost:8000/stop

# Check status
curl http://localhost:8000/status
```

**API Documentation:**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

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
1. **🏨 Hotel Room Offers** - Members who spent ≥ $5,000 (with watermark & redemption tracking)
2. **🍹 Drink Offers** - Members who lost ≥ $1,000 (with watermark & redemption tracking)
3. **📋 Fulfillment** - NEW! Consolidated view of all redeemed offers
4. **📊 Analytics** - Overall stats and charts
5. **👥 All Members** - Complete member activity

**Features:**
- **Watermark Display**: Shows previous interval data as watermark during current interval
- **Configurable Intervals**: Refresh interval controls watermark window size (default 10s)
- **One-Per-Day Policy**: Each customer can redeem only 1 offer per day per type
- **Mark as Redeemed**: Click buttons to mark offers as redeemed
- **Historical Batches**: View past qualifying periods in collapsible sections
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
make inject-rate   # Get current event rate
make inject-fast   # Increase to 10/sec
make inject-slow   # Decrease to 2/sec
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

**Window Size:** 5 minutes (real-time demo responsiveness!)
- For production, change to `INTERVAL '1' DAY` in setup_risingwave.sql

## 🔧 Troubleshooting

### Dashboard shows "No data yet"
```bash
# 1. Check if generator is running (should auto-start)
curl http://localhost:8000/status

# 2. If not running, check data-generator logs
docker logs casino-data-generator

# 3. Verify data in RisingWave (wait 10-15 seconds)
docker exec casino-data-generator psql -h risingwave -p 4566 -d dev -U root -c \
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
   - Data Generator (modular Python generator)

2. **Automatic Initialization** (5-10 seconds)
   - Data-generator entrypoint waits for RisingWave to be ready
   - Data-generator runs schema initialization script automatically
   - RisingWave schema created (source, 3 materialized views, redeemed_offers table)
   - Kafka topics auto-created when first data arrives

3. **Data Generation Auto-Starts**
   - FastAPI service automatically starts producing casino transactions
   - 5 events/sec by default (configurable via REST API)
   - Events sent directly to Redpanda (Kafka)
   - No manual intervention needed!

4. **Real-Time Processing**
   - RisingWave consumes from Kafka continuously
   - Aggregates data in 5-minute tumbling windows
   - Updates materialized views in real-time

5. **Dashboard Updates**
   - Streamlit queries RisingWave every 5 seconds (configurable)
   - Displays watermark data (previous 5-minute interval) during current interval
   - Shows live rewards with redemption tracking
   - One-per-day offer policy enforced
   - Sub-second query latency!

## 📝 Project Structure

```
.
├── docker-compose.yml                    # Services orchestration (5 services, no init containers)
├── Makefile                              # Quick commands (make help)
├── README.md                             # This file
│
├── scripts/                              # Utility scripts
│   ├── run-demo.sh                       # Main demo orchestrator
│   └── check-demo.sh                     # Health checker
│
├── streamlit/                            # Dashboard service (modular)
│   ├── Dockerfile                        # Container definition
│   ├── app.py                            # Main application entry point
│   ├── requirements.txt                  # Python dependencies
│   ├── entrypoint.sh                     # Init script (auto-initializes RisingWave)
│   ├── setup_risingwave.sql              # Database schema (copied during build)
│   ├── utils/                            # Reusable utilities
│   │   ├── db_utils.py                   # Database queries & connections
│   │   ├── time_utils.py                 # Interval & watermark logic
│   │   ├── display_utils.py              # UI rendering components
│   │   └── queries.py                    # SQL query builders
│   └── tabs/                             # Dashboard tabs
│       ├── hotel_tab.py                  # Hotel offers with watermark
│       └── drink_tab.py                  # Drink offers with watermark
│
├── risingwave/                           # Stream processor config
│   ├── setup_risingwave.sql              # Database schema & views (source)
│   └── init-risingwave.sh                # Manual init script (for reference)
│
├── redpanda/                             # Kafka broker config
│   └── init-redpanda.sh                  # Topic creation script (topics auto-created)
│
└── data-generator/                       # Event generator (modular)
    ├── generate.py                       # Main entry point
    ├── config.py                         # Configuration & constants
    ├── casino_simulator.py               # Core simulation logic
    └── producers.py                      # Kafka & batch producers
```

## 💡 Tips

**Adjust reward thresholds:** Use the sidebar in the Streamlit dashboard

**See more data faster:**
```bash
make inject-fast  # Increase to 10 events/sec
make inject-slow  # Decrease to 2 events/sec
make inject-rate  # Check current rate
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
