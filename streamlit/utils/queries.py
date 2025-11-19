"""
SQL query builders for casino dashboard
"""


def build_hotel_watermark_query(hotel_threshold, prev_start, prev_end, today_date=None):
    """Build query for hotel offers in previous interval (watermark)"""
    if today_date is None:
        from datetime import datetime
        today_date = datetime.now().strftime('%Y-%m-%d')

    return f"""
    WITH today_offers AS (
        SELECT member_id
        FROM redeemed_offers
        WHERE offer_type = 'hotel'
          AND redemption_date = '{today_date}'::date
    )
    SELECT
        m.member_id,
        m.member_name,
        m.total_spend,
        m.transaction_count,
        m.net_amount,
        m.last_transaction,
        m.window_start,
        m.window_end,
        CASE WHEN r.member_id IS NOT NULL THEN true ELSE false END as already_redeemed
    FROM member_daily_summary m
    LEFT JOIN today_offers r ON m.member_id = r.member_id
    WHERE m.total_spend >= {hotel_threshold}
      AND m.window_start >= '{prev_start}'::timestamp
      AND m.window_end <= '{prev_end}'::timestamp
    ORDER BY m.member_id, m.window_start DESC
    """


def build_hotel_history_query(hotel_threshold, prev_start, time_filter="1=1"):
    """Build query for hotel offers history (before watermark interval)"""
    return f"""
    SELECT
        member_id,
        member_name,
        total_spend,
        transaction_count,
        net_amount,
        last_transaction,
        window_start,
        window_end
    FROM member_daily_summary
    WHERE total_spend >= {hotel_threshold}
      AND window_end < '{prev_start}'::timestamp
      AND {time_filter}
    ORDER BY window_start DESC
    """


def build_drink_watermark_query(drink_threshold, prev_start, prev_end, today_date=None):
    """Build query for drink offers in previous interval (watermark)"""
    if today_date is None:
        from datetime import datetime
        today_date = datetime.now().strftime('%Y-%m-%d')

    return f"""
    WITH today_offers AS (
        SELECT member_id
        FROM redeemed_offers
        WHERE offer_type = 'drink'
          AND redemption_date = '{today_date}'::date
    )
    SELECT
        m.member_id,
        m.member_name,
        m.total_spend,
        m.transaction_count,
        m.net_amount,
        ABS(m.net_amount) as loss_amount,
        m.last_transaction,
        m.window_start,
        m.window_end,
        CASE WHEN r.member_id IS NOT NULL THEN true ELSE false END as already_redeemed
    FROM member_daily_summary m
    LEFT JOIN today_offers r ON m.member_id = r.member_id
    WHERE m.net_amount < 0
      AND ABS(m.net_amount) >= {drink_threshold}
      AND m.window_start >= '{prev_start}'::timestamp
      AND m.window_end <= '{prev_end}'::timestamp
    ORDER BY m.member_id, m.window_start DESC
    """


def build_drink_history_query(drink_threshold, prev_start, time_filter="1=1"):
    """Build query for drink offers history (before watermark interval)"""
    return f"""
    SELECT
        member_id,
        member_name,
        total_spend,
        transaction_count,
        net_amount,
        ABS(net_amount) as loss_amount,
        last_transaction,
        window_start,
        window_end
    FROM member_daily_summary
    WHERE net_amount < 0
      AND ABS(net_amount) >= {drink_threshold}
      AND window_end < '{prev_start}'::timestamp
      AND {time_filter}
    ORDER BY window_start DESC
    """


def build_stats_query(time_filter="1=1"):
    """Build query for overall analytics stats"""
    return f"""
    SELECT
        COUNT(DISTINCT member_id) as total_members,
        SUM(total_spend) as total_revenue,
        SUM(transaction_count) as total_transactions,
        AVG(total_spend) as avg_spend_per_member,
        SUM(CASE WHEN net_amount >= 0 THEN 1 ELSE 0 END) as winning_members,
        SUM(CASE WHEN net_amount < 0 THEN 1 ELSE 0 END) as losing_members
    FROM member_daily_summary
    WHERE {time_filter}
    """


def build_reward_query(hotel_threshold, drink_threshold, time_filter="1=1"):
    """Build query for reward eligibility stats"""
    return f"""
    SELECT
        SUM(CASE WHEN total_spend >= {hotel_threshold} THEN 1 ELSE 0 END) as hotel_eligible,
        SUM(CASE WHEN net_amount < 0 AND ABS(net_amount) >= {drink_threshold} THEN 1 ELSE 0 END) as drink_eligible,
        COUNT(*) as total
    FROM member_daily_summary
    WHERE {time_filter}
    """


def build_top_spenders_query(time_filter="1=1", limit=10):
    """Build query for top spenders"""
    return f"""
    SELECT
        member_name,
        total_spend,
        transaction_count,
        net_amount
    FROM member_daily_summary
    WHERE {time_filter}
    ORDER BY total_spend DESC
    LIMIT {limit}
    """


def build_all_members_query(hotel_threshold, drink_threshold, time_filter="1=1"):
    """Build query for all member activity"""
    return f"""
    SELECT
        member_id,
        member_name,
        total_spend,
        transaction_count,
        net_amount,
        last_transaction,
        CASE
            WHEN total_spend >= {hotel_threshold} THEN '🏨 Hotel Room'
            WHEN net_amount < 0 AND ABS(net_amount) >= {drink_threshold} THEN '🍹 Free Drink'
            ELSE '❌ No Reward'
        END as reward_status
    FROM member_daily_summary
    WHERE {time_filter}
    ORDER BY total_spend DESC
    """
