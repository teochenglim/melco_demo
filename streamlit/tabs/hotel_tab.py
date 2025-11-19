"""
Hotel Room Offers Tab
"""
import streamlit as st
from utils import (
    query_data,
    mark_offer_redeemed,
    get_current_interval_bounds,
    format_interval_label,
    render_hotel_offer_card,
    queries
)


def render(hotel_threshold, time_filter="1=1", interval_seconds=300):
    """Render the Hotel Room Offers tab"""
    st.header("🏨 VIP Hotel Room Offers")
    interval_minutes = interval_seconds // 60
    st.markdown(f"**Threshold:** Members who spent **≥ ${hotel_threshold:,}** in any {interval_minutes}-minute window")
    st.markdown("**Policy:** Each customer can only enjoy 1 hotel offer per day")

    # Get interval bounds
    curr_start, curr_end, prev_start, prev_end = get_current_interval_bounds(interval_seconds)

    # Query for both current and watermark intervals
    hotel_current_query = queries.build_hotel_watermark_query(hotel_threshold, curr_start, curr_end)
    hotel_watermark_query = queries.build_hotel_watermark_query(hotel_threshold, prev_start, prev_end)
    hotel_history_query = queries.build_hotel_history_query(hotel_threshold, prev_start, time_filter)

    hotel_current_df = query_data(hotel_current_query)
    hotel_watermark_df = query_data(hotel_watermark_query)
    hotel_history_df = query_data(hotel_history_query)

    # Display current interval progress (who's accumulating now)
    st.info(f"⏱️ **Current Interval:** {curr_start.strftime('%H:%M:%S')} - {curr_end.strftime('%H:%M:%S')} | **{len(hotel_current_df) if not hotel_current_df.empty else 0} members** on track to qualify")

    if not hotel_current_df.empty:
        # Display member details for current watermark
        for idx, row in hotel_current_df.iterrows():
            st.markdown(f"""
            <div style="background-color: #fff9e6; padding: 15px; border-radius: 8px; margin-bottom: 10px; border-left: 5px solid #ffc107;">
                <h4 style="margin: 0; color: #856404;">🏨 {row['member_name']}</h4>
                <p style="margin: 5px 0 0 0; color: #856404;">
                    <strong>Member ID:</strong> {row['member_id']} |
                    <strong>Spent:</strong> ${row['total_spend']:,.2f} |
                    <strong>Transactions:</strong> {int(row['transaction_count'])} |
                    <strong>Net:</strong> ${row['net_amount']:,.2f}
                </p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    # Display completed watermark section (last completed interval)
    if not hotel_watermark_df.empty:
        st.subheader(f"🏨 Qualified Members from Last Completed Interval")
        st.caption(f"📺 {prev_start.strftime('%H:%M:%S')} - {prev_end.strftime('%H:%M:%S')}")
        st.info(f"💡 **{len(hotel_watermark_df)} members** qualified in the last interval. Visit the **Fulfillment** tab to redeem offers.")

        # Display nice summary cards without buttons
        for idx, row in hotel_watermark_df.iterrows():
            is_redeemed = row.get('already_redeemed', False)
            status_badge = "✅ Redeemed" if is_redeemed else "⏳ Pending"
            status_color = "#d4edda" if is_redeemed else "#fff3cd"

            st.markdown(f"""
            <div style="background-color: {status_color}; padding: 15px; border-radius: 8px; margin-bottom: 10px; border-left: 5px solid #ffc107;">
                <h4 style="margin: 0; color: #856404;">🏨 {row['member_name']} - {status_badge}</h4>
                <p style="margin: 5px 0 0 0; color: #856404;">
                    <strong>Member ID:</strong> {row['member_id']} |
                    <strong>Spent:</strong> ${row['total_spend']:,.2f} |
                    <strong>Transactions:</strong> {int(row['transaction_count'])} |
                    <strong>Net:</strong> ${row['net_amount']:,.2f}
                </p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    # History view in batches downward (last 3 windows only)
    if not hotel_history_df.empty:
        st.subheader("📜 Historical Qualifying Periods (last 3 windows)")

        # Group by 5-minute intervals
        hotel_history_df['interval_label'] = hotel_history_df.apply(
            lambda x: format_interval_label(x['window_start'], x['window_end']),
            axis=1
        )

        # Get unique intervals (most recent 3 only)
        unique_intervals = hotel_history_df['interval_label'].unique()[:3]

        for interval_label in unique_intervals:
            interval_data = hotel_history_df[hotel_history_df['interval_label'] == interval_label]

            with st.expander(f"⏰ {interval_label} ({len(interval_data)} qualifying members)"):
                for idx, row in interval_data.iterrows():
                    is_redeemed = row.get('already_redeemed', False)
                    status_badge = "✅ Redeemed" if is_redeemed else "⏳ Pending"
                    status_color = "#d4edda" if is_redeemed else "#fff3cd"

                    st.markdown(f"""
                    <div style="background-color: {status_color}; padding: 15px; border-radius: 8px; margin-bottom: 10px; border-left: 5px solid #ffc107;">
                        <h4 style="margin: 0; color: #856404;">🏨 {row['member_name']} - {status_badge}</h4>
                        <p style="margin: 5px 0 0 0; color: #856404;">
                            <strong>Member ID:</strong> {row['member_id']} |
                            <strong>Spent:</strong> ${row['total_spend']:,.2f} |
                            <strong>Transactions:</strong> {int(row['transaction_count'])} |
                            <strong>Net:</strong> ${row['net_amount']:,.2f}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
    else:
        st.info("No historical data yet.")
