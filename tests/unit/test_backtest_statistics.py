import pytest
import numpy as np
from app.backtesting.statistics import StatisticalEngine


def test_statistics_empty_and_small_sample():
    # Empty sample
    stats_empty = StatisticalEngine.compute_distribution_stats([])
    assert stats_empty.sample_count == 0
    assert stats_empty.status == "EMPTY"
    assert stats_empty.mean is None

    # Small sample (N=5 < 10)
    small_data = [0.01, 0.02, -0.01, 0.03, 0.00]
    stats_small = StatisticalEngine.compute_distribution_stats(small_data, min_sample_size=10)
    assert stats_small.sample_count == 5
    assert stats_small.status == "INSUFFICIENT_SAMPLE"
    assert stats_small.mean is not None
    assert stats_small.ci_lower_normal is None
    assert stats_small.bootstrap_mean_ci_lower is None


def test_statistics_parametric_and_bootstrap_ci():
    np.random.seed(42)
    # Generate 50 normally distributed returns with mean +1.0%
    data = list(np.random.normal(0.01, 0.02, 50))

    stats = StatisticalEngine.compute_distribution_stats(
        data,
        confidence_level=0.95,
        bootstrap_seed=42,
        bootstrap_iterations=1000,
        min_sample_size=10,
    )

    assert stats.sample_count == 50
    assert stats.status == "VALID"
    assert stats.mean is not None
    assert stats.median is not None
    assert stats.std_dev is not None
    assert stats.std_error is not None

    # Verify normal CI boundaries
    assert stats.ci_lower_normal < stats.mean < stats.ci_upper_normal

    # Verify bootstrap CI boundaries
    assert stats.bootstrap_mean_ci_lower < stats.mean < stats.bootstrap_mean_ci_upper
    assert stats.bootstrap_median_ci_lower < stats.median < stats.bootstrap_median_ci_upper

    # Verify percentiles ordering
    assert stats.p5 <= stats.p25 <= stats.p50 <= stats.p75 <= stats.p95


def test_bootstrap_determinism():
    data = [0.01 * i for i in range(-15, 25)]

    stats1 = StatisticalEngine.compute_distribution_stats(data, bootstrap_seed=123, bootstrap_iterations=500)
    stats2 = StatisticalEngine.compute_distribution_stats(data, bootstrap_seed=123, bootstrap_iterations=500)

    assert stats1.bootstrap_mean_ci_lower == stats2.bootstrap_mean_ci_lower
    assert stats1.bootstrap_mean_ci_upper == stats2.bootstrap_mean_ci_upper
    assert stats1.bootstrap_median_ci_lower == stats2.bootstrap_median_ci_lower
    assert stats1.bootstrap_median_ci_upper == stats2.bootstrap_median_ci_upper
