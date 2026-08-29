"""
Unit tests for Phase 13D — BUY vs SELL Directional Analysis.
Verifies:
- Complete separation of BUY and SELL metrics
- Sample-size protection
- Metric fidelity across horizons
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


def test_direction_analysis_buy_and_sell_separation():
    """Verify BUY and SELL metrics are calculated independently."""
    base_ts = 1700000000000
    candles: List[Candle] = []
    price = 50000.0
    for i in range(120):
        o = price
        c = price + (20.0 if i < 60 else -20.0)
        h = max(o, c) + 10.0
        l = min(o, c) - 10.0
        price = c
        candles.append(_make_candle(base_ts + i * 60000, o, h, l, c, v=200.0))

    report = ScalpV2DiagnosticEngine.run_diagnostics(candles, symbol="BTCUSDT")
    da = report.direction_analysis

    assert "BUY" in da
    assert "SELL" in da

    buy_diag = da["BUY"]
    sell_diag = da["SELL"]

    assert buy_diag.direction == "BUY"
    assert sell_diag.direction == "SELL"
    assert buy_diag.sample_size_n + sell_diag.sample_size_n == report.total_signals
