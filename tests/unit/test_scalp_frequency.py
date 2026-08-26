"""
Unit tests for SCALP Signal Frequency, Density, and Clustering Metrics.
"""

import pytest
from app.profiles.config import SCALP_1M_CONFIG
from app.profile_validation.dataset import build_synthetic_multi_tf_dataset
from app.profile_validation.evaluation import ProfileEvaluationRunner
from app.profile_validation.metrics import ProfileValidationMetricsCalculator


def test_scalp_frequency_and_density_calculation():
    dataset = build_synthetic_multi_tf_dataset(primary_count=250)
    eval_res = ProfileEvaluationRunner.evaluate_profile_over_dataset(
        symbol="BTCUSDT",
        profile_config=SCALP_1M_CONFIG,
        multi_tf_dataset=dataset,
        warmup_bars=50,
    )

    assert "signal_density" in eval_res
    density = eval_res["signal_density"]
    assert "signals_per_day" in density
    assert "signals_per_hour" in density
    assert "clustering_factor" in density
    assert density["signals_per_day"] >= 0.0


def test_horizon_returns_monotonic_keys():
    dataset = build_synthetic_multi_tf_dataset(primary_count=200)
    eval_res = ProfileEvaluationRunner.evaluate_profile_over_dataset(
        symbol="BTCUSDT",
        profile_config=SCALP_1M_CONFIG,
        multi_tf_dataset=dataset,
        warmup_bars=50,
    )

    fwd = eval_res.get("forward_returns", {})
    assert "1C" in fwd
    assert "3C" in fwd
    assert "5C" in fwd
    assert "10C" in fwd
    assert "20C" in fwd
