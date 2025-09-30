"""
This module provides utility functions for working with dates and times.
"""

import datetime

def timestamp_as_datetime(timestamp):
    """
    Converts a Unix timestamp to a timezone-aware datetime object.

    Args:
        timestamp (int): A Unix timestamp.

    Returns:
        A datetime object representing the timestamp in UTC, or None if the
        timestamp is invalid.
    """
    try:
        return datetime.datetime.fromtimestamp(timestamp,tz=datetime.UTC)
    except (ValueError, TypeError, OSError):
        return None