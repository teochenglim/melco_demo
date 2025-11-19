"""
Display and UI utilities for Streamlit dashboard
"""
import streamlit as st
import time


def get_custom_css():
    """Return custom CSS for the dashboard"""
    return """
<style>
    .big-reward {
        font-size: 24px;
        font-weight: bold;
        color: #FFD700;
        text-align: center;
        padding: 20px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        margin: 10px 0;
    }
    .loss-reward {
        font-size: 24px;
        font-weight: bold;
        color: #FFD700;
        text-align: center;
        padding: 20px;
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        border-radius: 10px;
        margin: 10px 0;
    }
    .metric-card {
        background: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #667eea;
    }
    .watermark {
        position: relative;
        opacity: 0.5;
        background: rgba(128, 128, 128, 0.1);
        border: 2px dashed #888;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .watermark::before {
        content: "⏰ Previous Interval";
        position: absolute;
        top: 5px;
        right: 10px;
        font-size: 12px;
        color: #666;
        font-weight: bold;
    }
    .redeemed {
        opacity: 0.6;
        background: #e0e0e0 !important;
        position: relative;
    }
    .redeemed::after {
        content: "✓ REDEEMED";
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        font-size: 48px;
        color: rgba(0, 128, 0, 0.3);
        font-weight: bold;
        pointer-events: none;
    }
</style>
"""


def render_hotel_offer_card(row, is_redeemed=False, watermark=True):
    """
    Render a hotel offer card

    Args:
        row: DataFrame row with member data
        is_redeemed: Whether offer has been redeemed
        watermark: Whether to show watermark styling
    """
    div_class = "big-reward"
    if watermark:
        div_class += " watermark"
    if is_redeemed:
        div_class += " redeemed"

    status = "✓ Already Redeemed Today" if is_redeemed else "✓ Eligible"

    st.markdown(f"""
    <div class="{div_class}">
        🏨 <b>{row['member_name']}</b> (ID: {row['member_id']})<br>
        Total Spend: <b>${row['total_spend']:,.2f}</b> |
        Transactions: {int(row['transaction_count'])} |
        Net: ${row['net_amount']:,.2f}<br>
        <small>🎁 Status: {status}</small>
    </div>
    """, unsafe_allow_html=True)


def render_drink_offer_card(row, is_redeemed=False, watermark=True):
    """
    Render a drink offer card

    Args:
        row: DataFrame row with member data
        is_redeemed: Whether offer has been redeemed
        watermark: Whether to show watermark styling
    """
    div_class = "loss-reward"
    if watermark:
        div_class += " watermark"
    if is_redeemed:
        div_class += " redeemed"

    status = "✓ Already Redeemed Today" if is_redeemed else "✓ Eligible"

    st.markdown(f"""
    <div class="{div_class}">
        🍹 <b>{row['member_name']}</b> (ID: {row['member_id']})<br>
        Loss Amount: <b>${row['loss_amount']:,.2f}</b> |
        Transactions: {int(row['transaction_count'])} |
        Total Spent: ${row['total_spend']:,.2f}<br>
        <small>🎁 Status: {status}</small>
    </div>
    """, unsafe_allow_html=True)


def render_redeem_button(member_id, member_name, offer_type, key_prefix, mark_offer_redeemed_func):
    """
    Render a redeem button and handle redemption

    Args:
        member_id: Member ID
        member_name: Member name
        offer_type: 'hotel' or 'drink'
        key_prefix: Unique key prefix for button
        mark_offer_redeemed_func: Function to call to mark as redeemed

    Returns:
        bool: True if redeemed successfully
    """
    if st.button(f"✓ Mark as Redeemed", key=f"{key_prefix}_{member_id}"):
        if mark_offer_redeemed_func(member_id, member_name, offer_type):
            st.success(f"{offer_type.title()} offer marked as redeemed for {member_name}!")
            time.sleep(1)
            st.rerun()
            return True
    return False


def render_history_batch(interval_data, offer_type='hotel'):
    """
    Render a history batch for an interval

    Args:
        interval_data: DataFrame with data for this interval
        offer_type: 'hotel' or 'drink'
    """
    for idx, row in interval_data.iterrows():
        if offer_type == 'hotel':
            st.markdown(f"""
            - **{row['member_name']}** (ID: {row['member_id']}) - Spent: ${row['total_spend']:,.2f} | Transactions: {int(row['transaction_count'])} | Net: ${row['net_amount']:,.2f}
            """)
        else:  # drink
            st.markdown(f"""
            - **{row['member_name']}** (ID: {row['member_id']}) - Lost: ${row['loss_amount']:,.2f} | Transactions: {int(row['transaction_count'])} | Total Spent: ${row['total_spend']:,.2f}
            """)
