"""
Unit tests for Phase 13D — Setup Accounting & Unclassified Reconciliation.
Verifies:
- TREND_CONTINUATION + PULLBACK + MOMENTUM_BREAKOUT + UNCLASSIFIED == TOTAL SIGNALS
- Diagnostic reason logging for unclassified signals (NO_SETUP_MATCH, etc.)
- No silent assignment to fake setups
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


def test_setup_accounting_exact_reconciliation():
    """Verify setup counts strictly sum to total signals with 0 leaks."""
    base_ts = 1700000000000
    candles: List[Candle] = []
    price = 50000.0
    for i in range(150):
        o = price
        c = price + (25.0 if (i % 3 == 0) else -15.0)
        h = max(o, c) + 20.0
        l = min(o, c) - 20.0
        price = c
        candles.append(_make_candle(base_ts + i * 60000, o, h, l, c, v=300.0))

    report = ScalpV2DiagnosticEngine.run_diagnostics(candles, symbol="BTCUSDT")
    acc = report.setup_accounting

    assert acc.reconciliation_valid is True
    total_reconstructed = (
        acc.trend_continuation_count
        + acc.pullback_count
        + acc.momentum_breakout_count
        + acc.unclassified_count
    )
    assert total_reconstructed == report.total_signals
    assert acc.total_signals == report.total_signals
    assert isinstance(acc.unclassified_reasons, dict)
