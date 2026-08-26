"""
Centralized timeframe constants and validation utilities.
Single source of truth for interval durations, seconds, and milliseconds across the platform.
"""

from typing import Dict

TIMEFRAME_SECONDS: Dict[str, int] = {
    "1m": 60,
    "5m": 300,
    "15m": 900,
    "1h": 3600,
    "4h": 14400,
    "1d": 86400,
}

TIMEFRAME_MS: Dict[str, int] = {
    tf: sec * 1000 for tf, sec in TIMEFRAME_SECONDS.items()
}

SUPPORTED_TIMEFRAMES = list(TIMEFRAME_SECONDS.keys())


def get_timeframe_seconds(timeframe: str) -> int:
    """Return interval duration in seconds."""
    tf = timeframe.lower()
    if tf not in TIMEFRAME_SECONDS:
        raise ValueError(f"Unsupported timeframe '{timeframe}'. Supported: {SUPPORTED_TIMEFRAMES}")
    return TIMEFRAME_SECONDS[tf]


def get_timeframe_ms(timeframe: str) -> int:
    """Return interval duration in milliseconds."""
    return get_timeframe_seconds(timeframe) * 1000
