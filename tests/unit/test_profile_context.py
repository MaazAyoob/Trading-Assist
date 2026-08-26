"""
Unit tests for Multi-Timeframe Context Construction & Validation.
"""

import pytest
from app.profiles.config import SCALP_1M_CONFIG, INTRADAY_5M_CONFIG
from app.profiles.context import MultiTimeframeContextBuilder
from app.profiles.validation import ProfileValidator
from app.profile_validation.dataset import build_synthetic_multi_tf_dataset


def test_multi_timeframe_context_construction():
    dataset = build_synthetic_multi_tf_dataset(primary_count=150)
    scalp_ctx = MultiTimeframeContextBuilder.build_context(
        symbol="BTCUSDT",
        profile_config=SCALP_1M_CONFIG,
        primary_candles=dataset["1m"],
        context_candles_map={"5m": dataset["5m"], "15m": dataset["15m"]},
        is_confirmed=True,
    )

    assert scalp_ctx.is_causally_valid is True
    assert scalp_ctx.primary_timeframe == "1m"
    assert "5m" in scalp_ctx.context_indicators
    assert "15m" in scalp_ctx.context_regimes


def test_causal_alignment_validator():
    dataset = build_synthetic_multi_tf_dataset(primary_count=150)
    scalp_ctx = MultiTimeframeContextBuilder.build_context(
        symbol="BTCUSDT",
        profile_config=SCALP_1M_CONFIG,
        primary_candles=dataset["1m"],
        context_candles_map={"5m": dataset["5m"], "15m": dataset["15m"]},
        is_confirmed=True,
    )

    is_valid, errors = ProfileValidator.validate_causal_alignment(scalp_ctx)
    assert is_valid is True
    assert len(errors) == 0
