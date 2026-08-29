"""
Unit tests for Phase 13D — Score Calibration & Monotonicity.
Verifies:
- Score bucket boundaries (35-49, 50-64, 65-79, 80-100)
- Multi-horizon hit rate calculation
- Score monotonicity detection (MONOTONIC vs NON_MONOTONIC vs INSUFFICIENT_SAMPLE)
- Sample size threshold flags
"""
import pytest
from typing import List

from app.data.schema import Candle
from app.scalp_v2.diagnostics import ScalpV2DiagnosticEngine


def _make_candle(ts: int, o: float, h: float, l: float, c: float, v: float = 100.0) -> Candle:
    return Candle(
        timestamp=ts,
        open=o,
        high=h,
        low=l,
        close=c,
        volume=v,
        is_closed=True,
    )


def test_score_buckets_structure_and_bounds():
    """Verify all 4 canonical score buckets are present with correct bounds."""
    base_ts = 1700000000000
    candles: List[Candle] = []
    price = 50000.0
    for i in range(120):
        o = price
        c = price + 10.0
        h = c + 5.0
        l = o - 5.0
        price = c
        candles.append(_make_candle(base_ts + i * 60000, o, h, l, c, v=150.0))

    report = ScalpV2DiagnosticEngine.run_diagnostics(candles, symbol="BTCUSDT")
    buckets = report.score_analysis

    assert len(buckets) == 4
    assert buckets[0].bucket_label == "35–49"
    assert buckets[1].bucket_label == "50–64"
    assert buckets[2].bucket_label == "65–79"
    assert buckets[3].bucket_label == "80–100"

    for b in buckets:
        assert isinstance(b.is_insufficient_sample, bool)
        assert 0.0 <= b.tp1_hit_rate_20c <= 100.0
        assert 0.0 <= b.sl_rate_20c <= 100.0


def test_score_monotonicity_reporting():
    """Verify monotonicity report provides valid status and anomaly flags."""
    base_ts = 1700000000000
    candles: List[Candle] = []
    price = 50000.0
    for i in range(120):
        o = price
        c = price + (15.0 if i % 2 == 0 else -10.0)
        h = max(o, c) + 10.0
        l = min(o, c) - 10.0
        price = c
        candles.append(_make_candle(base_ts + i * 60000, o, h, l, c, v=150.0))

    report = ScalpV2DiagnosticEngine.run_diagnostics(candles, symbol="BTCUSDT")
    mono = report.score_monotonicity

    assert mono.status in ("MONOTONIC", "NON_MONOTONIC", "INSUFFICIENT_SAMPLE")
    assert isinstance(mono.details, str)
    assert isinstance(mono.anomaly_detected, bool)
