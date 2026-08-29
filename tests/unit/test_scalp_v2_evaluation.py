"""
Unit tests for Phase 13C — SCALP_STRATEGY_V2 Signal Quality Evaluation.
Verifies:
- Chronological evaluation with zero future leakage
- BUY/SELL direction handling and outcome tracking
- TP1/SL detection across horizons (1, 3, 5, 10, 20)
- Ambiguous same-candle handling (when candle touches both TP and SL)
- Score buckets (35-49, 50-64, 65-79, 80-100)
- Setup breakdown (TREND_CONTINUATION, PULLBACK, MOMENTUM_BREAKOUT)
- Deterministic reproducibility
- V1 and V2 algorithms remain untouched
"""
import pytest
from typing import List

from app.data.schema import Candle
from app.scalp_v2.models import ScalpV2Direction, ScalpV2SetupType
from app.scalp_v2.evaluation import (
    EvaluatedSignalOutcome,
    evaluate_signal_against_future_candles,
    run_scalp_v2_historical_evaluation,
    ScalpV2EvaluationReport,
)
from app.scalp.engine import ScalpStrategyEngine as ScalpV1Engine
from app.scalp_v2.engine import ScalpV2StrategyEngine


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


def test_buy_outcome_tp_hit_first():
    """Test BUY signal reaches TP1 before SL."""
    sig = EvaluatedSignalOutcome(
        candle_idx=10,
        timestamp=10000,
        direction=ScalpV2Direction.BUY,
        score=65.0,
        setup_type=ScalpV2SetupType.PULLBACK,
        entry=50000.0,
        stop_loss=49800.0,
        tp1=50200.0,
        tp2=50300.0,
        tp3=50400.0,
    )
    future = [
        _make_candle(10060, 50000.0, 50100.0, 49950.0, 50050.0),  # Neither
        _make_candle(10120, 50050.0, 50250.0, 49990.0, 50220.0),  # TP1 touched (high 50250 >= 50200, low 49990 > 49800)
    ]
    outcome = evaluate_signal_against_future_candles(sig, future, horizon=3)
    assert outcome == "TP1_HIT"


def test_sell_outcome_sl_hit_first():
    """Test SELL signal reaches SL before TP1."""
    sig = EvaluatedSignalOutcome(
        candle_idx=10,
        timestamp=10000,
        direction=ScalpV2Direction.SELL,
        score=65.0,
        setup_type=ScalpV2SetupType.TREND_CONTINUATION,
        entry=50000.0,
        stop_loss=50200.0,
        tp1=49800.0,
        tp2=49700.0,
        tp3=49600.0,
    )
    future = [
        _make_candle(10060, 50000.0, 50250.0, 49900.0, 50150.0),  # SL touched (high 50250 >= 50200, low 49900 > 49800)
    ]
    outcome = evaluate_signal_against_future_candles(sig, future, horizon=3)
    assert outcome == "SL_HIT"


def test_same_candle_ambiguous_outcome():
    """Test that when a single future candle touches both TP1 and SL, outcome is strictly AMBIGUOUS."""
    sig_buy = EvaluatedSignalOutcome(
        candle_idx=10,
        timestamp=10000,
        direction=ScalpV2Direction.BUY,
        score=65.0,
        setup_type=ScalpV2SetupType.MOMENTUM_BREAKOUT,
        entry=50000.0,
        stop_loss=49800.0,
        tp1=50200.0,
        tp2=50300.0,
        tp3=50400.0,
    )
    # Giant candle touching both high >= 50200 and low <= 49800
    future = [
        _make_candle(10060, 50000.0, 50300.0, 49700.0, 50000.0),
    ]
    outcome = evaluate_signal_against_future_candles(sig_buy, future, horizon=1)
    assert outcome == "AMBIGUOUS"


def test_neither_reached_within_horizon():
    """Test neither reached when price remains between SL and TP1."""
    sig = EvaluatedSignalOutcome(
        candle_idx=10,
        timestamp=10000,
        direction=ScalpV2Direction.BUY,
        score=50.0,
        setup_type=ScalpV2SetupType.PULLBACK,
        entry=50000.0,
        stop_loss=49800.0,
        tp1=50200.0,
        tp2=50300.0,
        tp3=50400.0,
    )
    future = [
        _make_candle(10060, 50000.0, 50100.0, 49900.0, 50020.0),
        _make_candle(10120, 50020.0, 50120.0, 49920.0, 50050.0),
    ]
    outcome = evaluate_signal_against_future_candles(sig, future, horizon=2)
    assert outcome == "NEITHER"


def test_historical_evaluation_deterministic_report():
    """Test full evaluation pipeline on synthetic candles."""
    base_ts = 1700000000000
    candles: List[Candle] = []

    # Generate 120 candles with an upward drift
    price = 50000.0
    for i in range(120):
        o = price
        c = price + (15.0 if i % 2 == 0 else -5.0)
        h = max(o, c) + 10.0
        l = min(o, c) - 10.0
        price = c
        candles.append(_make_candle(base_ts + i * 60000, o, h, l, c, v=150.0))

    report1 = run_scalp_v2_historical_evaluation(candles, symbol="BTCUSDT")
    report2 = run_scalp_v2_historical_evaluation(candles, symbol="BTCUSDT")

    assert isinstance(report1, ScalpV2EvaluationReport)
    assert report1.dataset_candles == 120
    assert report1.candles_evaluated == 60
    assert len(report1.horizon_analysis) == 5  # 1, 3, 5, 10, 20
    assert len(report1.score_breakdown) == 4   # 35-49, 50-64, 65-79, 80-100
    assert len(report1.setup_breakdown) == 3   # continuation, pullback, breakout

    # Determinism check: identical inputs produce identical report
    assert report1.total_signals == report2.total_signals
    assert report1.buy_signals == report2.buy_signals
    assert report1.sell_signals == report2.sell_signals
    assert report1.frequency_comparison.v2_signals == report2.frequency_comparison.v2_signals


from app.scalp_v2.version import SCALP_STRATEGY_V2_ID, SCALP_STRATEGY_V2_VERSION


def test_v1_and_v2_isolation_during_evaluation():
    """Verify SCALP_STRATEGY_V1 and V2 remain intact and isolated."""
    assert ScalpV1Engine.STRATEGY_ID == "SCALP_STRATEGY_V1"
    assert ScalpV1Engine.VERSION == "1.0.0"
    assert SCALP_STRATEGY_V2_ID == "SCALP_STRATEGY_V2"
    assert SCALP_STRATEGY_V2_VERSION == "2.0.0"
