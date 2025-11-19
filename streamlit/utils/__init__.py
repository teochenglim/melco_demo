"""
Utilities package for Casino VIP Rewards Dashboard
"""
from .db_utils import (
    get_connection,
    query_data,
    execute_query,
    check_offer_redeemed,
    mark_offer_redeemed
)
from .time_utils import (
    get_current_interval_bounds,
    format_interval_label
)
from .display_utils import (
    get_custom_css,
    render_hotel_offer_card,
    render_drink_offer_card,
    render_redeem_button,
    render_history_batch
)
from . import queries

__all__ = [
    # Database utilities
    'get_connection',
    'query_data',
    'execute_query',
    'check_offer_redeemed',
    'mark_offer_redeemed',
    # Time utilities
    'get_current_interval_bounds',
    'format_interval_label',
    # Display utilities
    'get_custom_css',
    'render_hotel_offer_card',
    'render_drink_offer_card',
    'render_redeem_button',
    'render_history_batch',
    # Query builders
    'queries',
]
