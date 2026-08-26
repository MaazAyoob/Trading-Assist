"""
Unit tests for Anti-Leakage & Future Candle Mutation Invariance in Profile Contexts.
"""

import pytest
from app.profiles.config import SCALP_1M_CONFIG
from app.profiles.context import MultiTimeframeContextBuilder
from app.profile_validation.dataset import build_synthetic_multi_tf_dataset


def test_future_higher_timeframe_mutation_invariance():
    dataset = build_synthetic_multi_tf_dataset(primary_count=200)
    p_candles = dataset["1m"][:100]

    ctx_1 = MultiTimeframeContextBuilder.build_context(
        symbol="BTCUSDT",
        profile_config=SCALP_1M_CONFIG,
        primary_candles=p_candles,
        context_candles_map={"5m": dataset["5m"][:20], "15m": dataset["15m"][:7]},
    )

    # Mutate future higher timeframe candles that haven't occurred yet (e.g. 5m bar 25)
    mutated_5m = [c.model_copy(deep=True) for c in dataset["5m"]]
    if len(mutated_5m) > 25:
        mutated_5m[25].close += 5000.0

    ctx_2 = MultiTimeframeContextBuilder.build_context(
        symbol="BTCUSDT",
        profile_config=SCALP_1M_CONFIG,
        primary_candles=p_candles,
        context_candles_map={"5m": mutated_5m, "15m": dataset["15m"]},
    )

    # Invariance check: context at t=100m MUST remain identical
    assert ctx_1.context_indicators["5m"].momentum.rsi == ctx_2.context_indicators["5m"].momentum.rsi
    assert ctx_1.context_signals["5m"].score == ctx_2.context_signals["5m"].score
