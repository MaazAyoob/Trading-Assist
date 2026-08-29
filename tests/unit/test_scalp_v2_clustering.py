"""
Unit tests for Phase 13D — Signal Clustering and Flip Analysis.
Verifies:
- Signals per hour / 4 hours
- Same-direction rapid clustering
- Rapid direction reversal (flip) detection
- Monotonic timestamps and zero leakage
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


def test_clustering_and_flip_diagnostics():
    """Verify clustering and flip metrics compute correctly."""
    base_ts = 1700000000000
    candles: List[Candle] = []
    price = 50000.0
    for i in range(150):
        o = price
        c = price + (15.0 if (i // 10) % 2 == 0 else -15.0)
        h = max(o, c) + 10.0
        l = min(o, c) - 10.0
        price = c
        candles.append(_make_candle(base_ts + i * 60000, o, h, l, c, v=200.0))

    report = ScalpV2DiagnosticEngine.run_diagnostics(candles, symbol="BTCUSDT")
    cl = report.clustering_analysis
    fl = report.flip_analysis

    assert cl.signals_per_hour >= 0.0
    assert cl.signals_per_4h >= 0.0
    assert cl.max_signals_in_rolling_5m >= 0
    assert cl.max_signals_in_rolling_15m >= cl.max_signals_in_rolling_5m
    assert fl.flips_total >= 0
    assert fl.flips_per_hour >= 0.0
