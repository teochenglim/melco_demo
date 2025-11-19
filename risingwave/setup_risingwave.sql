-- Casino Gaming Loyalty System - RisingWave Setup
-- This demonstrates native Kafka source connector (no Kafka Connect needed!)

-- 1. Create Kafka source for gaming transactions
-- RisingWave connects DIRECTLY to Kafka - no Kafka Connect required!
CREATE SOURCE IF NOT EXISTS gaming_transactions (
    transaction_id BIGINT,
    member_id BIGINT,
    member_name VARCHAR,
    transaction_type VARCHAR,  -- 'bet', 'win', 'cashout'
    amount DECIMAL,
    game_type VARCHAR,         -- 'slot', 'blackjack', 'roulette', 'poker'
    transaction_time TIMESTAMP,
    -- Watermark for handling late arrivals (10 second tolerance)
    WATERMARK FOR transaction_time AS transaction_time - INTERVAL '10' SECOND
) WITH (
    connector = 'kafka',
    topic = 'gaming-transactions',
    properties.bootstrap.server = 'redpanda:9092',
    scan.startup.mode = 'earliest'
) FORMAT PLAIN ENCODE JSON;

-- 2. Create materialized view for member daily summary
-- This aggregates transactions per member per day in real-time
-- Using 5-minute windows for demo purposes (change to 1 DAY for production)
CREATE MATERIALIZED VIEW IF NOT EXISTS member_daily_summary AS
SELECT
    member_id,
    member_name,
    window_start,
    window_end,
    -- Total amount wagered/spent
    SUM(CASE WHEN transaction_type = 'bet' THEN amount ELSE 0 END) as total_spend,
    -- Total winnings
    SUM(CASE WHEN transaction_type = 'win' THEN amount ELSE 0 END) as total_winnings,
    -- Net amount (winnings - bets)
    SUM(CASE
        WHEN transaction_type = 'win' THEN amount
        WHEN transaction_type = 'bet' THEN -amount
        ELSE 0
    END) as net_amount,
    -- Transaction count
    COUNT(*) as transaction_count,
    -- Last transaction time
    MAX(transaction_time) as last_transaction
FROM TUMBLE(gaming_transactions, transaction_time, INTERVAL '5' MINUTE)
GROUP BY member_id, member_name, window_start, window_end;

-- 3. View for hotel room offers (spent >= $5000)
CREATE MATERIALIZED VIEW IF NOT EXISTS hotel_room_offers AS
SELECT
    member_id,
    member_name,
    total_spend,
    transaction_count,
    net_amount,
    last_transaction,
    window_start,
    window_end,
    '🏨 Complimentary Hotel Room (1 night)' as reward_type
FROM member_daily_summary
WHERE total_spend >= 5000;

-- 4. View for drink offers (lost >= $1000)
CREATE MATERIALIZED VIEW IF NOT EXISTS drink_offers AS
SELECT
    member_id,
    member_name,
    total_spend,
    transaction_count,
    net_amount,
    ABS(net_amount) as loss_amount,
    last_transaction,
    window_start,
    window_end,
    '🍹 Complimentary Premium Drink' as reward_type
FROM member_daily_summary
WHERE net_amount < 0
  AND ABS(net_amount) >= 1000;

-- 5. Real-time game statistics
CREATE MATERIALIZED VIEW IF NOT EXISTS game_stats AS
SELECT 
    game_type,
    COUNT(*) as total_bets,
    SUM(CASE WHEN transaction_type = 'bet' THEN amount ELSE 0 END) as total_wagered,
    SUM(CASE WHEN transaction_type = 'win' THEN amount ELSE 0 END) as total_paid_out,
    SUM(CASE 
        WHEN transaction_type = 'win' THEN amount 
        WHEN transaction_type = 'bet' THEN -amount 
        ELSE 0 
    END) as house_edge
FROM gaming_transactions
GROUP BY game_type;

-- 6. Member leaderboard (all-time)
CREATE MATERIALIZED VIEW IF NOT EXISTS member_leaderboard AS
SELECT 
    member_id,
    member_name,
    SUM(CASE WHEN transaction_type = 'bet' THEN amount ELSE 0 END) as lifetime_spend,
    SUM(CASE WHEN transaction_type = 'win' THEN amount ELSE 0 END) as lifetime_winnings,
    COUNT(*) as lifetime_transactions,
    MAX(transaction_time) as last_seen
FROM gaming_transactions
GROUP BY member_id, member_name;

-- Query examples:

-- Check hotel room offers
-- SELECT * FROM hotel_room_offers ORDER BY total_spend DESC;

-- Check drink offers
-- SELECT * FROM drink_offers ORDER BY loss_amount DESC;

-- View all member summaries for today
-- SELECT * FROM member_daily_summary 
-- WHERE DATE(window_start) = CURRENT_DATE
-- ORDER BY total_spend DESC;

-- Game performance
-- SELECT * FROM game_stats ORDER BY house_edge DESC;

-- Top members
-- SELECT * FROM member_leaderboard ORDER BY lifetime_spend DESC LIMIT 10;
