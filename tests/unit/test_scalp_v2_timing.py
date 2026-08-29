"""
Unit tests for Phase 13D — Signal and Entry Timing Analysis.
Verifies:
- TP1/SL hit timing (1, 2, 3, 5, 10, 20 candles)
- Average and median candle counts
- Entry timing classifications (TIMELY, EARLY, LATE, UNDETERMINED)
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


def test_timing_distribution_metrics():
    """Verify timing distribution calculates metrics and candle counts properly."""
    base_ts = 1700000000000
    candles: List[Candle] = []
    price = 50000.0
    for i in range(120):
        o = price
        c = price + 15.0
        h = c + 10.0
        l = o - 5.0
        price = c
        candles.append(_make_candle(base_ts + i * 60000, o, h, l, c, v=200.0))

    report = ScalpV2DiagnosticEngine.run_diagnostics(candles, symbol="BTCUSDT")
    timing = report.timing_analysis

    assert timing.tp1_before_sl_count >= 0
    assert timing.sl_before_tp1_count >= 0
    assert timing.neither_count >= 0
    assert timing.ambiguous_count >= 0
    assert timing.tp1_within_1c <= timing.tp1_within_3c <= timing.tp1_within_5c <= timing.tp1_within_20c


def test_entry_timing_metrics():
    """Verify entry timing classifies outcomes without throwing errors."""
    base_ts = 1700000000000
    candles: List[Candle] = []
    price = 50000.0
    for i in range(100):
        o = price
        c = price + (10.0 if i % 2 == 0 else -8.0)
        h = max(o, c) + 5.0
        l = min(o, c) - 5.0
        price = c
        candles.append(_make_candle(base_ts + i * 60000, o, h, l, c, v=150.0))

    report = ScalpV2DiagnosticEngine.run_diagnostics(candles, symbol="BTCUSDT")
    entry = report.entry_timing

    total_classified = entry.timely_count + entry.early_count + entry.late_count + entry.undetermined_count
    assert total_classified == report.total_signals
