"""
Unit tests for Profile Switching Isolation & Zero Stale Leakage.
"""

import pytest
from app.profiles.config import SCALP_1M_CONFIG, SWING_4H_CONFIG
from app.profiles.engine import TradingProfileEngine
from app.profile_validation.dataset import build_synthetic_multi_tf_dataset


def test_profile_switching_isolation():
    dataset = build_synthetic_multi_tf_dataset(primary_count=300)

    # 1. Run Scalp evaluation
    scalp_res = TradingProfileEngine.evaluate_profile(
        symbol="BTCUSDT",
        profile_config=SCALP_1M_CONFIG,
        primary_candles=dataset["1m"],
        context_candles_map={"5m": dataset["5m"], "15m": dataset["15m"]},
    )

    # 2. Run Swing evaluation
    swing_res = TradingProfileEngine.evaluate_profile(
        symbol="BTCUSDT",
        profile_config=SWING_4H_CONFIG,
        primary_candles=dataset["4h"],
        context_candles_map={"1h": dataset["1h"], "1d": dataset["1d"]},
    )

    assert scalp_res.profile_id == "SCALP_1M_V1"
    assert scalp_res.primary_timeframe == "1m"
    assert swing_res.profile_id == "SWING_4H_V1"
    assert swing_res.primary_timeframe == "4h"

    # Verify no state bleeding between result objects
    assert scalp_res.context_timeframes != swing_res.context_timeframes
