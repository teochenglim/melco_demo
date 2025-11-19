"""
Fulfillment Tab - Shows unfulfilled offers (top) and fulfilled offers (bottom)
"""
import streamlit as st
import pandas as pd
from utils import query_data, mark_offer_redeemed, check_offer_redeemed
from datetime import datetime


def render():
    """Render the Fulfillment tab"""
    st.header("📋 Offer Fulfillment")
    st.markdown("**Track pending and fulfilled offers**")

    # ====================
    # TOP SECTION: UNFULFILLED OFFERS (Haven't been redeemed)
    # ====================
    st.subheader("⏳ Pending Offers (Not Yet Fulfilled)")
    st.markdown("*These members qualify for offers but haven't redeemed them yet*")

    # Get all qualifying members from hotel_room_offers and drink_offers
    # Exclude those who already redeemed today
    today_date = datetime.now().strftime('%Y-%m-%d')

    unfulfilled_query = f"""
    WITH latest_offers AS (
        -- Get the latest/highest qualifying window for each member for hotel offers
        (SELECT DISTINCT ON (member_id)
            member_id,
            member_name,
            'hotel' as offer_type,
            '🏨 Hotel Room' as offer_display,
            total_spend as metric_value,
            'Spend: $' || ROUND(total_spend, 2) as metric_label,
            window_start,
            window_end
        FROM hotel_room_offers
        ORDER BY member_id, window_end DESC, total_spend DESC)

        UNION ALL

        -- Get the latest/highest qualifying window for each member for drink offers
        (SELECT DISTINCT ON (member_id)
            member_id,
            member_name,
            'drink' as offer_type,
            '🍹 Free Drink' as offer_display,
            loss_amount as metric_value,
            'Lost: $' || ROUND(loss_amount, 2) as metric_label,
            window_start,
            window_end
        FROM drink_offers
        ORDER BY member_id, window_end DESC, loss_amount DESC)
    ),
    redeemed_today AS (
        SELECT DISTINCT member_id, offer_type
        FROM redeemed_offers
        WHERE redemption_date = '{today_date}'::date
    )
    SELECT
        lo.member_id,
        lo.member_name,
        lo.offer_type,
        lo.offer_display,
        lo.metric_value,
        lo.metric_label,
        lo.window_start,
        lo.window_end
    FROM latest_offers lo
    LEFT JOIN redeemed_today rt
        ON lo.member_id = rt.member_id
        AND lo.offer_type = rt.offer_type
    WHERE rt.member_id IS NULL
    ORDER BY lo.window_end DESC, lo.metric_value DESC
    """

    unfulfilled_df = query_data(unfulfilled_query)

    if not unfulfilled_df.empty:
        # Summary metrics for unfulfilled
        col1, col2, col3 = st.columns(3)

        total_pending = len(unfulfilled_df)
        pending_hotel = len(unfulfilled_df[unfulfilled_df['offer_type'] == 'hotel'])
        pending_drink = len(unfulfilled_df[unfulfilled_df['offer_type'] == 'drink'])

        with col1:
            st.metric("Total Pending", total_pending)
        with col2:
            st.metric("🏨 Hotel Rooms", pending_hotel)
        with col3:
            st.metric("🍹 Drinks", pending_drink)

        st.markdown("")

        # Display unfulfilled offers with checkboxes (auto-fulfill when checked)
        for idx, row in unfulfilled_df.iterrows():
            col1, col2 = st.columns([0.5, 4.5])

            with col1:
                # Checkbox for selecting the offer - auto-fulfill when checked
                checked = st.checkbox(
                    "",
                    key=f"check_{row['offer_type']}_{row['member_id']}_{idx}",
                    label_visibility="collapsed",
                    value=False
                )

                # When checked, immediately mark as fulfilled
                if checked:
                    if mark_offer_redeemed(row['member_id'], row['member_name'], row['offer_type']):
                        st.success(f"✓ Fulfilled: {row['member_name']} - {row['offer_display']}")
                        import time
                        time.sleep(0.5)
                        st.rerun()

            with col2:
                st.markdown(f"""
                <div style="background-color: #fff3cd; padding: 15px; border-radius: 8px; margin-bottom: 10px; border-left: 5px solid #ffc107;">
                    <h4 style="margin: 0; color: #856404;">{row['offer_display']} - {row['member_name']}</h4>
                    <p style="margin: 5px 0 0 0; color: #856404;">
                        <strong>Member ID:</strong> {row['member_id']} |
                        <strong>{row['metric_label']}</strong> |
                        <strong>Window:</strong> {pd.to_datetime(row['window_start']).strftime('%H:%M:%S')} - {pd.to_datetime(row['window_end']).strftime('%H:%M:%S')}
                    </p>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("🎉 No pending offers - all qualifying offers have been fulfilled!")

    st.markdown("---")

    # ====================
    # BOTTOM SECTION: FULFILLED OFFERS (Already redeemed)
    # ====================
    st.subheader("✅ Fulfilled Offers")
    st.markdown("*These members have already redeemed their offers*")

    # Query all redeemed offers
    fulfilled_query = """
    SELECT
        member_id,
        member_name,
        offer_type,
        redeemed_at,
        CASE
            WHEN offer_type = 'hotel' THEN '🏨 Hotel Room'
            WHEN offer_type = 'drink' THEN '🍹 Free Drink'
            ELSE offer_type
        END as offer_display
    FROM redeemed_offers
    ORDER BY redeemed_at DESC
    """

    fulfilled_df = query_data(fulfilled_query)

    if not fulfilled_df.empty:
        # Summary metrics for fulfilled
        col1, col2, col3, col4 = st.columns(4)

        total_fulfilled = len(fulfilled_df)
        fulfilled_hotel = len(fulfilled_df[fulfilled_df['offer_type'] == 'hotel'])
        fulfilled_drink = len(fulfilled_df[fulfilled_df['offer_type'] == 'drink'])
        unique_members = fulfilled_df['member_id'].nunique()

        with col1:
            st.metric("Total Fulfilled", total_fulfilled)
        with col2:
            st.metric("🏨 Hotel Rooms", fulfilled_hotel)
        with col3:
            st.metric("🍹 Drinks", fulfilled_drink)
        with col4:
            st.metric("Unique Members", unique_members)

        st.markdown("")

        # Filters
        col1, col2 = st.columns(2)

        with col1:
            offer_filter = st.selectbox(
                "Filter by Offer Type",
                ["All", "🏨 Hotel Room", "🍹 Free Drink"],
                key="fulfilled_offer_filter"
            )

        with col2:
            member_search = st.text_input(
                "Search by Member Name",
                key="fulfilled_member_search"
            )

        # Apply filters
        filtered_df = fulfilled_df.copy()

        if offer_filter != "All":
            offer_type_map = {
                "🏨 Hotel Room": "hotel",
                "🍹 Free Drink": "drink"
            }
            filtered_df = filtered_df[filtered_df['offer_type'] == offer_type_map[offer_filter]]

        if member_search:
            filtered_df = filtered_df[
                filtered_df['member_name'].str.contains(member_search, case=False, na=False)
            ]

        st.markdown(f"**Showing {len(filtered_df)} fulfilled offer(s)**")

        # Display fulfilled table
        if not filtered_df.empty:
            # Format for display
            display_df = filtered_df[[
                'member_id', 'member_name', 'offer_display', 'redeemed_at'
            ]].copy()
            display_df.columns = ['Member ID', 'Member Name', 'Offer Type', 'Fulfilled At']

            # Format datetime
            display_df['Fulfilled At'] = pd.to_datetime(display_df['Fulfilled At']).dt.strftime('%Y-%m-%d %H:%M:%S')

            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True
            )

            # Download button
            csv = display_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Fulfillment Report (CSV)",
                data=csv,
                file_name="fulfilled_offers_report.csv",
                mime="text/csv"
            )
        else:
            st.info("No fulfilled offers match your filters")

    else:
        st.info("No offers have been fulfilled yet")
        st.markdown("""
        **How to fulfill offers:**
        1. Qualifying offers will appear in the **Pending Offers** section above
        2. Click the **✓ Fulfill** button next to each offer
        3. Fulfilled offers will move to this section
        """)
