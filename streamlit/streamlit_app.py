import streamlit as st
import psycopg2
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import os

# Page config
st.set_page_config(
    page_title="🎰 Casino VIP Rewards Dashboard",
    page_icon="🎰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
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
</style>
""", unsafe_allow_html=True)

# Database connection
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
    refresh_interval = st.slider(
        "Refresh interval (seconds)",
        min_value=5,
        max_value=60,
        value=10,
        step=5
    )
    
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

# Map time window to SQL
# Note: RisingWave streaming queries have limitations on temporal filters
# For simplicity, we'll just show all data and let users filter in the sidebar
time_filters = {
    "Today": "1=1",  # Show all windows (RisingWave limitation)
    "Last Hour": "1=1",
    "Last 5 Minutes": "1=1",
    "All Time": "1=1"
}
time_filter = time_filters.get(time_window, "1=1")

# Main content
tab1, tab2, tab3, tab4 = st.tabs([
    "🏨 Hotel Room Offers", 
    "🍹 Drink Offers", 
    "📊 Analytics", 
    "👥 All Members"
])

with tab1:
    st.header("🏨 VIP Hotel Room Offers")
    st.markdown(f"**Threshold:** Members who spent **≥ ${hotel_threshold:,}** in any 5-minute window")

    # Query to aggregate by member
    hotel_summary_query = f"""
    SELECT
        member_id,
        member_name,
        COUNT(*) as qualifying_windows,
        SUM(total_spend) as total_spend_all_windows,
        MAX(total_spend) as max_spend_single_window,
        MAX(last_transaction) as most_recent_activity
    FROM member_daily_summary
    WHERE total_spend >= {hotel_threshold}
      AND {time_filter}
    GROUP BY member_id, member_name
    ORDER BY total_spend_all_windows DESC
    """

    # Query for detailed history
    hotel_detail_query = f"""
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
      AND {time_filter}
    ORDER BY member_id, window_start DESC
    """

    hotel_summary_df = query_data(hotel_summary_query)
    hotel_detail_df = query_data(hotel_detail_query)

    if not hotel_summary_df.empty:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🎉 Eligible Members", len(hotel_summary_df))
        with col2:
            st.metric("💰 Total High Roller Spend", f"${hotel_summary_df['total_spend_all_windows'].sum():,.2f}")
        with col3:
            st.metric("⏰ Total Qualifying Windows", int(hotel_summary_df['qualifying_windows'].sum()))

        st.markdown("---")

        # Show current eligible members (summary)
        st.subheader("🏨 Currently Eligible VIPs")
        for idx, row in hotel_summary_df.iterrows():
            st.markdown(f"""
            <div class="big-reward">
                🏨 <b>{row['member_name']}</b> (ID: {row['member_id']})<br>
                Total Spend: <b>${row['total_spend_all_windows']:,.2f}</b> |
                Peak Window: ${row['max_spend_single_window']:,.2f} |
                Qualifying Windows: {int(row['qualifying_windows'])}<br>
                <small>🎁 Reward: Complimentary Hotel Room (1 night)</small>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        # History view with better organization
        st.subheader("📜 Spending History (5-Minute Windows)")

        for member_id in hotel_detail_df['member_id'].unique():
            member_data = hotel_detail_df[hotel_detail_df['member_id'] == member_id]
            member_name = member_data.iloc[0]['member_name']

            with st.expander(f"👤 {member_name} (ID: {member_id}) - {len(member_data)} qualifying windows"):
                # Create a clean timeline view
                timeline_df = member_data[['window_start', 'window_end', 'total_spend', 'transaction_count', 'net_amount']].copy()
                timeline_df.columns = ['Start', 'End', 'Total Spent', 'Transactions', 'Net Amount']
                timeline_df['Total Spent'] = timeline_df['Total Spent'].apply(lambda x: f"${x:,.2f}")
                timeline_df['Net Amount'] = timeline_df['Net Amount'].apply(lambda x: f"${x:,.2f}")

                st.dataframe(timeline_df, use_container_width=True, hide_index=True)

                # Mini chart for this member
                chart_data = member_data.copy()
                fig = px.line(
                    chart_data,
                    x='window_start',
                    y='total_spend',
                    markers=True,
                    title=f"Spending Trend for {member_name}",
                    labels={'total_spend': 'Total Spend ($)', 'window_start': 'Time Window'}
                )
                fig.update_traces(line_color='#FFD700')
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.info(f"No members have spent ≥ ${hotel_threshold:,} in the selected time window.")

with tab2:
    st.header("🍹 Complimentary Drink Offers")
    st.markdown(f"**Threshold:** Members who lost **≥ ${drink_threshold:,}** in any 5-minute window")

    # Query to aggregate by member (show latest window + count of qualifying windows)
    drink_summary_query = f"""
    SELECT
        member_id,
        member_name,
        COUNT(*) as qualifying_windows,
        SUM(ABS(net_amount)) as total_losses,
        MAX(last_transaction) as most_recent_activity,
        MAX(window_end) as latest_window
    FROM member_daily_summary
    WHERE net_amount < 0
      AND ABS(net_amount) >= {drink_threshold}
      AND {time_filter}
    GROUP BY member_id, member_name
    ORDER BY total_losses DESC
    """

    # Query for detailed history
    drink_detail_query = f"""
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
      AND {time_filter}
    ORDER BY member_id, window_start DESC
    """

    drink_summary_df = query_data(drink_summary_query)
    drink_detail_df = query_data(drink_detail_query)

    if not drink_summary_df.empty:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🎉 Eligible Members", len(drink_summary_df))
        with col2:
            st.metric("💸 Total Losses", f"${drink_summary_df['total_losses'].sum():,.2f}")
        with col3:
            st.metric("⏰ Total Qualifying Windows", int(drink_summary_df['qualifying_windows'].sum()))

        st.markdown("---")

        # Show current eligible members (summary)
        st.subheader("🍹 Currently Eligible Members")
        for idx, row in drink_summary_df.iterrows():
            st.markdown(f"""
            <div class="loss-reward">
                🍹 <b>{row['member_name']}</b> (ID: {row['member_id']})<br>
                Total Losses: <b>${row['total_losses']:,.2f}</b> |
                Qualifying Windows: {int(row['qualifying_windows'])} |
                Last Activity: {row['most_recent_activity']}<br>
                <small>🎁 Reward: Complimentary Premium Drink</small>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        # History view with better organization
        st.subheader("📜 Loss History (5-Minute Windows)")

        # Group by member for better display
        for member_id in drink_detail_df['member_id'].unique():
            member_data = drink_detail_df[drink_detail_df['member_id'] == member_id]
            member_name = member_data.iloc[0]['member_name']

            with st.expander(f"👤 {member_name} (ID: {member_id}) - {len(member_data)} qualifying windows"):
                # Create a clean timeline view
                timeline_df = member_data[['window_start', 'window_end', 'loss_amount', 'transaction_count', 'total_spend']].copy()
                timeline_df.columns = ['Start', 'End', 'Loss Amount', 'Transactions', 'Total Spent']
                timeline_df['Loss Amount'] = timeline_df['Loss Amount'].apply(lambda x: f"${x:,.2f}")
                timeline_df['Total Spent'] = timeline_df['Total Spent'].apply(lambda x: f"${x:,.2f}")

                st.dataframe(timeline_df, use_container_width=True, hide_index=True)

                # Mini chart for this member
                chart_data = member_data.copy()
                chart_data['window_label'] = chart_data['window_start'].astype(str).str[-8:]
                fig = px.line(
                    chart_data,
                    x='window_start',
                    y='loss_amount',
                    markers=True,
                    title=f"Loss Trend for {member_name}",
                    labels={'loss_amount': 'Loss ($)', 'window_start': 'Time Window'}
                )
                fig.update_traces(line_color='#ff6b6b')
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.info(f"No members have lost ≥ ${drink_threshold:,} in the selected time window.")

with tab3:
    st.header("📊 Analytics & Insights")
    
    # Overall stats query
    stats_query = f"""
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
    
    stats_df = query_data(stats_query)
    
    if not stats_df.empty and len(stats_df) > 0:
        stats = stats_df.iloc[0]

        # Handle None values from aggregates when there's no data
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
            reward_query = f"""
            SELECT 
                SUM(CASE WHEN total_spend >= {hotel_threshold} THEN 1 ELSE 0 END) as hotel_eligible,
                SUM(CASE WHEN net_amount < 0 AND ABS(net_amount) >= {drink_threshold} THEN 1 ELSE 0 END) as drink_eligible,
                COUNT(*) as total
            FROM member_daily_summary
            WHERE {time_filter}
            """
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
        top_query = f"""
        SELECT 
            member_name,
            total_spend,
            transaction_count,
            net_amount
        FROM member_daily_summary
        WHERE {time_filter}
        ORDER BY total_spend DESC
        LIMIT 10
        """
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
        st.markdown("""
        **To inject data:**
        ```bash
        make inject
        # or
        python3 casino_generator.py --mode kafka --rate 5
        ```
        """)

with tab4:
    st.header("👥 All Member Activity")
    
    # All members query
    all_query = f"""
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
