"""
Time and interval utilities for watermark display logic
"""
from datetime import datetime, timedelta


def get_current_interval_bounds(interval_seconds=300):
    """
    Get the current and previous interval bounds

    Args:
        interval_seconds: Size of each interval in seconds (default: 300 = 5 minutes)

    Returns:
        tuple: (current_start, current_end, previous_start, previous_end)

    Example:
        At 14:37:00 with 5-minute intervals:
        - Current interval: 14:35:00 - 14:40:00
        - Previous interval: 14:30:00 - 14:35:00 (displayed as watermark)
    """
    now = datetime.now()
    # Calculate which interval we're in
    seconds_since_epoch = int(now.timestamp())
    current_interval_num = seconds_since_epoch // interval_seconds

    current_start = datetime.fromtimestamp(current_interval_num * interval_seconds)
    current_end = current_start + timedelta(seconds=interval_seconds)

    previous_start = current_start - timedelta(seconds=interval_seconds)
    previous_end = current_start

    return current_start, current_end, previous_start, previous_end


def format_interval_label(window_start, window_end):
    """
    Format interval as readable label

    Args:
        window_start: Start timestamp
        window_end: End timestamp

    Returns:
        str: Formatted label like "14:35:00 - 14:35:10"
    """
    return f"{window_start.strftime('%H:%M:%S')} - {window_end.strftime('%H:%M:%S')}"
