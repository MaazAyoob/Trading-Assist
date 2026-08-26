"""
Unit tests for Profile Evaluation Determinism.
"""

import pytest
from app.profiles.config import SCALP_1M_CONFIG, INTRADAY_5M_CONFIG
from app.profiles.engine import TradingProfileEngine
from app.profile_validation.dataset import build_synthetic_multi_tf_dataset


def test_profile_evaluation_determinism_across_iterations():
    dataset = build_synthetic_multi_tf_dataset(primary_count=200)

    res_a = TradingProfileEngine.evaluate_profile(
        symbol="BTCUSDT",
        profile_config=SCALP_1M_CONFIG,
        primary_candles=dataset["1m"],
        context_candles_map={"5m": dataset["5m"], "15m": dataset["15m"]},
    )

    res_b = TradingProfileEngine.evaluate_profile(
        symbol="BTCUSDT",
        profile_config=SCALP_1M_CONFIG,
        primary_candles=dataset["1m"],
        context_candles_map={"5m": dataset["5m"], "15m": dataset["15m"]},
    )

    assert res_a.profile_state == res_b.profile_state
    assert res_a.alignment_score == res_b.alignment_score
    assert len(res_a.cost_sensitivity) == len(res_b.cost_sensitivity)
    assert res_a.reasons == res_b.reasons
