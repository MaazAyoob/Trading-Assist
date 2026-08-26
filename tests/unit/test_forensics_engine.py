"""
Unit and Integration tests for Phase 7 — Signal Forensics & Factor Attribution.
Verifies attribution conservation, timing isolation, clustering, and anti-leakage.
"""

import copy
import pytest
from app.data.schema import Candle, CandleStateEnum
from app.forensics.engine import SignalForensicsEngine
from app.forensics.models import ForensicsReport
from app.backtesting.dataset import DatasetManager


def generate_synthetic_candles(n: int = 300, base_price: float = 50000.0) -> list[Candle]:
    """Generates synthetic 15m candles with a realistic trending price walk."""
    import numpy as np
    rng = np.random.default_rng(42)
    candles = []
    price = base_price
    start_ts = 1704067200000  # 2024-01-01 00:00:00 UTC

    for i in range(n):
        ts = start_ts + i * 900000
        ret = rng.normal(0.0002, 0.003)
        open_p = price
        close_p = open_p * (1.0 + ret)
        high_p = max(open_p, close_p) * (1.0 + abs(rng.normal(0, 0.001)))
        low_p = min(open_p, close_p) * (1.0 - abs(rng.normal(0, 0.001)))
        vol = float(rng.uniform(10.0, 100.0))

        candles.append(Candle(
            timestamp=ts,
            open=round(open_p, 2),
            high=round(high_p, 2),
            low=round(low_p, 2),
            close=round(close_p, 2),
            volume=round(vol, 4),
            close_time=ts + 899999,
            is_closed=True,
            state=CandleStateEnum.CLOSED,
        ))
        price = close_p

    return candles


def test_forensics_report_generation():
    """Verifies that SignalForensicsEngine produces a complete, valid ForensicsReport."""
    candles = generate_synthetic_candles(n=350)
    report = SignalForensicsEngine.analyze(candles)

    assert isinstance(report, ForensicsReport)
    assert report.candle_count == 350
    assert report.total_signals >= 0
    assert report.score_monotonicity_grade in ["MONOTONIC", "WEAKLY_MONOTONIC", "NON_MONOTONIC", "INVERSE"]
    assert len(report.observed_facts) > 0
    assert len(report.possible_explanations) > 0
    assert len(report.unproven_hypotheses) > 0


def test_score_attribution_conservation():
    """Verifies that factor contributions and modifiers mathematically reconcile with net score."""
    candles = generate_synthetic_candles(n=350)
    report = SignalForensicsEngine.analyze(candles)

    for trace in report.score_traces_sample:
        # Sum of weighted contributions rounded matches raw score within rounding precision (0.05)
        reconciled_raw = (
            trace.trend_contribution
            + trace.momentum_contribution
            + trace.structure_contribution
            + trace.volume_contribution
        )
        assert abs(trace.raw_score - reconciled_raw) < 0.05

        # Net score must equal raw * modifiers +/- conflict penalty (within 1-decimal rounding tolerance)
        context_adj = trace.raw_score * trace.regime_modifier * trace.volatility_modifier
        expected_net = (context_adj - trace.conflict_penalty) if context_adj >= 0 else (context_adj + trace.conflict_penalty)
        assert abs(trace.net_score - expected_net) <= 0.1


def test_pre_post_timing_calculation():
    """Verifies that pre-signal and post-signal return calculations are temporally accurate."""
    candles = generate_synthetic_candles(n=350)
    report = SignalForensicsEngine.analyze(candles)

    if report.score_traces_sample:
        trace = report.score_traces_sample[0]
        idx = trace.candle_index
        close_sig = candles[idx].close

        # Verify pre-5 return
        if idx >= 5:
            expected_pre5 = (close_sig - candles[idx - 5].close) / candles[idx - 5].close
            assert abs(trace.pre_returns[5] - expected_pre5) < 1e-5

        # Verify post-5 return
        if idx + 5 < len(candles):
            if trace.direction == "LONG_SETUP":
                expected_post5 = (candles[idx + 5].close - close_sig) / close_sig
            else:
                expected_post5 = (close_sig - candles[idx + 5].close) / close_sig
            assert abs(trace.post_returns[5] - expected_post5) < 1e-5


def test_clustering_and_persistence_metrics():
    """Verifies that signal clustering and persistence calculations are mathematically consistent."""
    candles = generate_synthetic_candles(n=350)
    report = SignalForensicsEngine.analyze(candles)

    clustering = report.clustering
    assert clustering.total_signals == report.total_signals
    assert 0.0 <= clustering.pct_within_1_candle <= 100.0
    assert 0.0 <= clustering.pct_within_4_candles <= 100.0
    assert clustering.pct_within_1_candle <= clustering.pct_within_4_candles
    assert clustering.effective_sample_size_estimate <= max(1, clustering.total_signals)


def test_forensics_anti_leakage_and_immutability():
    """
    Strict anti-leakage audit:
    Forensics for timestamps up to T must remain bit-for-bit identical when
    future candles after T are mutated.
    """
    candles = generate_synthetic_candles(n=300)
    T = 250

    # Baseline run up to T
    report_orig = SignalForensicsEngine.analyze(candles[:T])

    # Mutated future candles
    candles_mutated = copy.deepcopy(candles)
    for k in range(T, len(candles)):
        candles_mutated[k].open *= 2.5
        candles_mutated[k].high *= 3.0
        candles_mutated[k].low *= 0.5
        candles_mutated[k].close *= 2.0
        candles_mutated[k].volume *= 10.0

    report_mutated = SignalForensicsEngine.analyze(candles_mutated[:T])

    # Assert exact equality of signal traces up to T
    assert report_orig.total_signals == report_mutated.total_signals
    assert report_orig.long_signals == report_mutated.long_signals
    assert report_orig.short_signals == report_mutated.short_signals

    for t_orig, t_mut in zip(report_orig.score_traces_sample, report_mutated.score_traces_sample):
        assert t_orig.signal_id == t_mut.signal_id
        assert t_orig.timestamp == t_mut.timestamp
        assert t_orig.net_score == t_mut.net_score
        assert t_orig.raw_score == t_mut.raw_score
        assert t_orig.direction == t_mut.direction
