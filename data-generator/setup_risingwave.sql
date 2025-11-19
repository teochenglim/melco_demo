-- Casino Gaming Loyalty System - RisingWave Setup
-- This demonstrates native Kafka source connector (no Kafka Connect needed!)

-- Drop existing views first to ensure clean recreation
DROP MATERIALIZED VIEW IF EXISTS drink_offers CASCADE;
DROP MATERIALIZED VIEW IF EXISTS hotel_room_offers CASCADE;
DROP MATERIALIZED VIEW IF EXISTS member_daily_summary CASCADE;

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
-- This aggregates transactions per member in real-time
-- Using 5-minute windows for real-time demo (change to 1 DAY for production)
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

-- 5. Redeemed offers tracking table
-- This table tracks which members have redeemed offers to enforce one-per-day limit
-- Primary key on (member_id, offer_type, redemption_date) prevents multiple redemptions per day
CREATE TABLE IF NOT EXISTS redeemed_offers (
    member_id BIGINT NOT NULL,
    member_name VARCHAR NOT NULL,
    offer_type VARCHAR NOT NULL,  -- 'hotel' or 'drink'
    redeemed_at TIMESTAMP NOT NULL,
    redemption_date DATE NOT NULL,  -- Date portion for enforcing one-per-day
    PRIMARY KEY (member_id, offer_type, redemption_date)
);

-- Query examples:

-- Check hotel room offers
-- SELECT * FROM hotel_room_offers ORDER BY total_spend DESC;

-- Check drink offers
-- SELECT * FROM drink_offers ORDER BY loss_amount DESC;

-- View all member summaries
-- SELECT * FROM member_daily_summary
-- ORDER BY window_end DESC, total_spend DESC;
