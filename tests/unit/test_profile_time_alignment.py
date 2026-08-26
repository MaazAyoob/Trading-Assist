"""
Unit tests for Strict Time Alignment across Multi-Timeframe Hierarchies.
"""

import pytest
from app.profiles.config import SCALP_1M_CONFIG, INTRADAY_5M_CONFIG, SWING_4H_CONFIG
from app.profiles.context import MultiTimeframeContextBuilder
from app.profile_validation.dataset import build_synthetic_multi_tf_dataset


def test_strict_timestamp_monotonicity():
    dataset = build_synthetic_multi_tf_dataset(primary_count=200)
    
    # 1m Primary with 5m and 15m context
    p_candles = dataset["1m"][:120]
    p_ts = p_candles[-1].timestamp

    ctx = MultiTimeframeContextBuilder.build_context(
        symbol="BTCUSDT",
        profile_config=SCALP_1M_CONFIG,
        primary_candles=p_candles,
        context_candles_map={"5m": dataset["5m"], "15m": dataset["15m"]},
        is_confirmed=True,
    )

    for tf, candle in ctx.context_candles.items():
        assert candle.timestamp <= p_ts, f"Context {tf} timestamp {candle.timestamp} exceeded primary timestamp {p_ts}"


def test_swing_4h_time_alignment():
    dataset = build_synthetic_multi_tf_dataset(primary_count=500)
    p_candles = dataset["4h"][:40]
    p_ts = p_candles[-1].timestamp

    ctx = MultiTimeframeContextBuilder.build_context(
        symbol="BTCUSDT",
        profile_config=SWING_4H_CONFIG,
        primary_candles=p_candles,
        context_candles_map={"1h": dataset["1h"], "1d": dataset["1d"]},
        is_confirmed=True,
    )

    for tf, candle in ctx.context_candles.items():
        assert candle.timestamp <= p_ts
