# Casino VIP Rewards Dashboard

A modular, real-time Streamlit dashboard for casino VIP loyalty rewards powered by RisingWave.

## Key Features

- **Real-Time Updates**: Auto-refreshes every 5 seconds to show latest offers
- **5-Minute Windows**: RisingWave aggregates data in 5-minute tumbling windows
- **Watermark Display**: Shows previous 5-minute interval data during current interval
- **Configurable Intervals**: Adjust window size from 5-60 seconds in sidebar
- **One-Per-Day Policy**: Each customer can redeem only 1 offer per day per type
- **Fulfillment Tracking**: Dedicated tab for tracking redeemed offers
- **Modular Architecture**: Separated utilities, tabs, and query builders for maintainability
- **No Volume Mounts**: All files copied during Docker build for portability

## Project Structure

```
streamlit/
├── Dockerfile                 # Container definition (copies all files at build time)
├── entrypoint.sh              # Simple startup script (no schema init)
├── requirements.txt           # Python dependencies
├── app.py                     # Main application entry point (5 tabs)
├── utils/                     # Reusable utilities
│   ├── __init__.py           # Package exports
│   ├── db_utils.py           # Database connection & queries (uses explicit timestamps)
│   ├── time_utils.py         # Interval & time calculations (5-minute watermark logic)
│   ├── display_utils.py      # UI rendering components (watermark CSS)
│   └── queries.py            # SQL query builders (RisingWave-compatible)
└── tabs/                      # Dashboard tabs
    ├── __init__.py           # Tab exports
    ├── hotel_tab.py          # Hotel room offers tab (with watermark & redemption)
    ├── drink_tab.py          # Drink offers tab (with watermark & redemption)
    └── fulfillment_tab.py    # Fulfillment tab (consolidated redemptions view)
```

## Features

### Modular Architecture
- **Separation of Concerns**: Database, UI, time logic, and queries are separated
- **Reusability**: All utilities can be imported and reused
- **Maintainability**: Easy to update specific functionality without touching other code
- **Testability**: Each module can be tested independently

### Core Modules

#### `utils/db_utils.py`
Database connection and query execution:
```python
from utils import query_data, mark_offer_redeemed

# Execute queries
df = query_data("SELECT * FROM member_daily_summary")

# Mark offers as redeemed
mark_offer_redeemed(member_id=1001, member_name="John", offer_type="hotel")
```

#### `utils/time_utils.py`
Interval and watermark logic:
```python
from utils import get_current_interval_bounds

# Get current and previous 5-minute intervals
curr_start, curr_end, prev_start, prev_end = get_current_interval_bounds(10)
```

#### `utils/display_utils.py`
Reusable UI components:
```python
from utils import render_hotel_offer_card, render_drink_offer_card

# Render offer cards with watermark and redemption status
render_hotel_offer_card(row, is_redeemed=False, watermark=True)
```

#### `utils/queries.py`
SQL query builders:
```python
from utils import queries

# Build queries dynamically
query = queries.build_hotel_watermark_query(
    hotel_threshold=5000,
    prev_start=datetime_obj,
    prev_end=datetime_obj
)
```

## Running the Dashboard

### In Docker (Recommended)
```bash
# Automatic with docker-compose
docker-compose up streamlit

# Dashboard runs on http://localhost:8501
# Auto-refreshes every 5 seconds
# Shows 5-minute window data from RisingWave
```

### Locally (Development)
```bash
# Export environment variables
export RISINGWAVE_HOST=localhost
export RISINGWAVE_PORT=4566
export RISINGWAVE_DB=dev
export RISINGWAVE_USER=root

# Run the modular app
streamlit run app.py
```

## Configuration

Set environment variables for RisingWave connection:
```bash
export RISINGWAVE_HOST=localhost
export RISINGWAVE_PORT=4566
export RISINGWAVE_DB=dev
export RISINGWAVE_USER=root
```

## Dashboard Features

1. **Real-Time Updates**: Auto-refreshes every 5 seconds (configurable in sidebar)
   - Shows latest qualifying offers immediately
   - Sub-second query latency from RisingWave

2. **10-Second Tumbling Windows**: RisingWave aggregates data in 5-minute windows
   - Configurable from 5-60 seconds in sidebar
   - Fast, real-time responsiveness for demos

3. **Watermark Display**: Shows data from previous interval during current interval
   - Example: During 14:35:10-14:35:20, displays 14:35:00-14:35:10 data
   - Watermark intervals sync with window size slider

4. **One-Per-Day Policy**: Enforces one offer redemption per customer per day
   - Tracks redemptions in `redeemed_offers` table
   - Displays redemption status on offer cards
   - Prevents duplicate redemptions

5. **Fulfillment Tab**: Consolidated view of all redeemed offers
   - See all hotel and drink redemptions in one place
   - Filter by offer type or search by member name
   - Summary metrics (total redeemed, by type, unique members)
   - Download fulfillment reports as CSV

6. **Batch History**: Historical data organized in collapsible time-based batches
   - Grouped by 5-minute interval windows
   - Shows all qualifying members per interval

7. **Visual Indicators**: Color-coded cards for different offer types and redemption status
   - Watermark style for previous interval
   - Greyed-out style for redeemed offers
   - Click buttons to mark offers as redeemed

8. **RisingWave Compatibility**: All queries work with RisingWave SQL dialect
   - Uses explicit timestamps instead of CURRENT_DATE
   - Parenthesized DISTINCT ON queries in UNIONs
   - Compatible with PostgreSQL wire protocol

## Extending the Dashboard

### Adding a New Tab
1. Create a new file in `tabs/` (e.g., `my_tab.py`)
2. Implement a `render()` function
3. Import and use in `app.py`:
   ```python
   from tabs import my_tab

   with tab_new:
       my_tab.render(params)
   ```

### Adding New Queries
Add query builders to `utils/queries.py`:
```python
def build_my_query(param1, param2):
    return f"""
    SELECT * FROM my_table
    WHERE field1 = {param1}
      AND field2 = {param2}
    """
```

### Adding New UI Components
Add rendering functions to `utils/display_utils.py`:
```python
def render_my_component(data):
    st.markdown(f"<div class='my-class'>{data}</div>", unsafe_allow_html=True)
```
