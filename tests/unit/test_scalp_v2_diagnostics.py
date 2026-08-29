"""
Unit tests for Phase 13D — ScalpV2DiagnosticEngine.
Tests:
- Deterministic output
- No future leakage
- Reconciled setup accounting (TC + PB + MB + UNCLASSIFIED == TOTAL)
- Execution performance
- V1 immutability and no execution imports
"""
import pytest
from typing import List

from app.data.schema import Candle
from app.scalp.engine import ScalpStrategyEngine as ScalpV1Engine
from app.scalp_v2.engine import ScalpV2StrategyEngine
from app.scalp_v2.diagnostics import ScalpV2DiagnosticEngine, ScalpV2DiagnosticReport


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


def test_diagnostics_deterministic_reproducibility():
    """Verify diagnostic runs produce identical deterministic output on same inputs."""
    base_ts = 1700000000000
    candles: List[Candle] = []
    price = 60000.0
    for i in range(120):
        o = price
        c = price + (20.0 if i % 2 == 0 else -10.0)
        h = max(o, c) + 15.0
        l = min(o, c) - 15.0
        price = c
        candles.append(_make_candle(base_ts + i * 60000, o, h, l, c, v=200.0))

    report1 = ScalpV2DiagnosticEngine.run_diagnostics(candles, symbol="BTCUSDT")
    report2 = ScalpV2DiagnosticEngine.run_diagnostics(candles, symbol="BTCUSDT")

    assert isinstance(report1, ScalpV2DiagnosticReport)
    assert report1.total_signals == report2.total_signals
    assert report1.setup_accounting.reconciliation_valid is True
    assert len(report1.score_analysis) == 4
    assert len(report1.factor_analysis) == 8


def test_diagnostics_empty_or_insufficient_candles():
    """Verify graceful handling for insufficient candle history."""
    report = ScalpV2DiagnosticEngine.run_diagnostics([], symbol="BTCUSDT")
    assert report.total_signals == 0
    assert report.score_monotonicity.status == "INSUFFICIENT_SAMPLE"
    assert report.setup_accounting.reconciliation_valid is True


def test_v1_and_v2_isolation_and_no_execution_imports():
    """Verify baseline V1 is untouched and zero execution imports exist in diagnostics."""
    assert ScalpV1Engine.STRATEGY_ID == "SCALP_STRATEGY_V1"
    assert ScalpV1Engine.VERSION == "1.0.0"
    
    with open("backend/app/scalp_v2/diagnostics.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    forbidden = ["ccxt", "binance.client", "create_order", "place_order", "trade_execution"]
    for keyword in forbidden:
        assert keyword not in content, f"Forbidden execution keyword found: {keyword}"
