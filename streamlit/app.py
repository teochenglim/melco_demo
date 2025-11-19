#!/usr/bin/env python3
"""
Casino VIP Loyalty Rewards Dashboard
Real-time dashboard for casino VIP rewards powered by RisingWave
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import time

# Import custom utilities
from utils import query_data, get_custom_css, queries
from tabs import hotel_tab, drink_tab, fulfillment_tab

# Page config
st.set_page_config(
    page_title="🎰 Casino VIP Rewards Dashboard",
    page_icon="🎰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply custom CSS
st.markdown(get_custom_css(), unsafe_allow_html=True)

# Header
st.title("🎰 Casino VIP Loyalty Rewards Dashboard")
st.markdown("### Real-time rewards for high-value players")

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")

    # Reward thresholds
    st.subheader("💰 Reward Thresholds")
    hotel_threshold = st.number_input(
        "Hotel Room Offer (Spend ≥)",
        min_value=1000,
        max_value=50000,
        value=5000,
        step=500,
        help="Members who spend above this get a free hotel room"
    )

    drink_threshold = st.number_input(
        "Free Drink Offer (Loss ≥)",
        min_value=100,
        max_value=10000,
        value=1000,
        step=100,
        help="Members who lose above this get a complimentary drink"
    )

    # Refresh settings
    st.subheader("🔄 Auto Refresh")
    auto_refresh = st.checkbox("Enable auto-refresh", value=True)
    st.markdown("**Refresh Interval:** 5 seconds")
    refresh_interval = 5  # Fixed at 5 seconds

    # Fixed interval (5-minute windows in RisingWave)
    interval_seconds = 300  # Fixed at 5 minutes (300 seconds) to match RisingWave TUMBLE window
    st.info("⏱️ **Window Interval:** 5 minutes (fixed in RisingWave schema)")

    # Time window
    st.subheader("📅 Time Window")
    time_window = st.selectbox(
        "Show data for:",
        ["Today", "Last Hour", "Last 5 Minutes", "All Time"],
        index=0
    )

    st.markdown("---")
    st.markdown("**Status:** 🟢 Live")
    st.caption(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")

# Time filter mapping
time_filters = {
    "Today": "1=1",
    "Last Hour": "1=1",
    "Last 5 Minutes": "1=1",
    "All Time": "1=1"
}
time_filter = time_filters.get(time_window, "1=1")

# Main content tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🏨 Hotel Room Offers",
    "🍹 Drink Offers",
    "📋 Fulfillment",
    "📊 Analytics",
    "👥 All Members"
])

# Tab 1: Hotel Room Offers
with tab1:
    hotel_tab.render(hotel_threshold, time_filter, interval_seconds=interval_seconds)

# Tab 2: Drink Offers
with tab2:
    drink_tab.render(drink_threshold, time_filter, interval_seconds=interval_seconds)

# Tab 3: Fulfillment
with tab3:
    fulfillment_tab.render()

# Tab 4: Analytics
with tab4:
    st.header("📊 Analytics & Insights")

    # Overall stats query
    stats_query = queries.build_stats_query(time_filter)
    stats_df = query_data(stats_query)

    if not stats_df.empty and len(stats_df) > 0:
        stats = stats_df.iloc[0]

        # Handle None values from aggregates
        total_members = int(stats['total_members']) if stats['total_members'] is not None else 0
        total_revenue = float(stats['total_revenue']) if stats['total_revenue'] is not None else 0.0
        total_transactions = int(stats['total_transactions']) if stats['total_transactions'] is not None else 0
        avg_spend = float(stats['avg_spend_per_member']) if stats['avg_spend_per_member'] is not None else 0.0
        winning_members = int(stats['winning_members']) if stats['winning_members'] is not None else 0
        losing_members = int(stats['losing_members']) if stats['losing_members'] is not None else 0

        # Metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("👥 Active Members", f"{total_members:,}")
        with col2:
            st.metric("💰 Total Revenue", f"${total_revenue:,.2f}")
        with col3:
            st.metric("🎰 Transactions", f"{total_transactions:,}")
        with col4:
            st.metric("📊 Avg Spend", f"${avg_spend:,.2f}")

        st.markdown("---")

        # Winning vs Losing
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("🎲 Win/Loss Distribution")
            win_loss_data = {
                'Status': ['Winners', 'Losers'],
                'Count': [winning_members, losing_members]
            }
            fig = px.pie(
                win_loss_data,
                values='Count',
                names='Status',
                color='Status',
                color_discrete_map={'Winners': '#00cc88', 'Losers': '#ff6b6b'},
                hole=0.4
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("🎁 Reward Eligibility")
            reward_query = queries.build_reward_query(hotel_threshold, drink_threshold, time_filter)
            reward_df = query_data(reward_query)

            if not reward_df.empty:
                r = reward_df.iloc[0]
                hotel_count = int(r['hotel_eligible']) if r['hotel_eligible'] is not None else 0
                drink_count = int(r['drink_eligible']) if r['drink_eligible'] is not None else 0
                total_count = int(r['total']) if r['total'] is not None else 0
                reward_data = {
                    'Reward': ['Hotel Room', 'Free Drink', 'No Reward'],
                    'Count': [
                        hotel_count,
                        drink_count,
                        total_count - hotel_count - drink_count
                    ]
                }
                fig = px.bar(
                    reward_data,
                    x='Reward',
                    y='Count',
                    color='Reward',
                    color_discrete_map={
                        'Hotel Room': '#FFD700',
                        'Free Drink': '#FF6B6B',
                        'No Reward': '#cccccc'
                    }
                )
                st.plotly_chart(fig, use_container_width=True)

        # Top spenders
        st.subheader("🏆 Top 10 Spenders")
        top_query = queries.build_top_spenders_query(time_filter, limit=10)
        top_df = query_data(top_query)

        if not top_df.empty:
            fig = px.bar(
                top_df,
                x='member_name',
                y='total_spend',
                color='net_amount',
                color_continuous_scale='RdYlGn',
                labels={'total_spend': 'Total Spend ($)', 'member_name': 'Member'},
                text='total_spend'
            )
            fig.update_traces(texttemplate='$%{text:,.0f}', textposition='outside')
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("📊 No data yet. Start the data generator to see analytics!")

# Tab 5: All Members
with tab5:
    st.header("👥 All Member Activity")

    # All members query
    all_query = queries.build_all_members_query(hotel_threshold, drink_threshold, time_filter)
    all_df = query_data(all_query)

    if not all_df.empty:
        st.metric("Total Members", len(all_df))

        # Format for display
        display_df = all_df.copy()
        display_df['total_spend'] = display_df['total_spend'].apply(lambda x: f"${x:,.2f}")
        display_df['net_amount'] = display_df['net_amount'].apply(lambda x: f"${x:,.2f}")

        # Style the dataframe
        def highlight_rewards(row):
            if '🏨' in row['reward_status']:
                return ['background-color: #fff4cc'] * len(row)
            elif '🍹' in row['reward_status']:
                return ['background-color: #ffe6e6'] * len(row)
            else:
                return [''] * len(row)

        styled_df = display_df.style.apply(highlight_rewards, axis=1)
        st.dataframe(styled_df, use_container_width=True, height=600)

        # Download button
        csv = all_df.to_csv(index=False)
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name=f"casino_members_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    else:
        st.info("No member activity in the selected time window.")

# Footer with auto-refresh
if auto_refresh:
    time.sleep(refresh_interval)
    st.rerun()
else:
    if st.button("🔄 Refresh Now"):
        st.rerun()
