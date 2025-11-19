"""
Database utilities for RisingWave connection and queries
"""
import os
import streamlit as st
import psycopg2
import pandas as pd


@st.cache_resource
def get_connection():
    """Connect to RisingWave"""
    return psycopg2.connect(
        host=os.getenv('RISINGWAVE_HOST', 'localhost'),
        port=int(os.getenv('RISINGWAVE_PORT', 4566)),
        database=os.getenv('RISINGWAVE_DB', 'dev'),
        user=os.getenv('RISINGWAVE_USER', 'root')
    )


def query_data(query):
    """Execute query and return DataFrame"""
    try:
        conn = get_connection()
        df = pd.read_sql_query(query, conn)
        return df
    except Exception as e:
        st.error(f"Database error: {e}")
        return pd.DataFrame()


def execute_query(query):
    """Execute a query without returning results"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(query)
        conn.commit()
        cursor.close()
        return True
    except Exception as e:
        st.error(f"Database error: {e}")
        return False


def check_offer_redeemed(member_id, offer_type):
    """Check if member has already redeemed an offer today"""
    from datetime import datetime
    today_date = datetime.now().strftime('%Y-%m-%d')

    query = f"""
    SELECT COUNT(*) as count
    FROM redeemed_offers
    WHERE member_id = {member_id}
      AND offer_type = '{offer_type}'
      AND redemption_date = '{today_date}'::date
    """
    result = query_data(query)
    if not result.empty and result.iloc[0]['count'] > 0:
        return True
    return False


def mark_offer_redeemed(member_id, member_name, offer_type):
    """Mark an offer as redeemed (prevents duplicates via check)"""
    from datetime import datetime
    now = datetime.now()
    redeemed_at = now.strftime('%Y-%m-%d %H:%M:%S')
    redemption_date = now.strftime('%Y-%m-%d')

    # First check if already redeemed today (prevents duplicates)
    if check_offer_redeemed(member_id, offer_type):
        st.warning(f"Already redeemed {offer_type} offer today!")
        return False

    # Insert only if not already redeemed (primary key will prevent duplicates)
    query = f"""
    INSERT INTO redeemed_offers (member_id, member_name, offer_type, redeemed_at, redemption_date)
    VALUES ({member_id}, '{member_name}', '{offer_type}', '{redeemed_at}', '{redemption_date}')
    """
    return execute_query(query)
