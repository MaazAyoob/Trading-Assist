"""
Unit Tests for Phase 10 — Target Planner.
Verifies canonical 1.25R, 2.0R, 3.0R multipliers, auditable structural adjustments, and monotonic ordering.
"""

import pytest
from app.data.schema import Candle, CandleStateEnum
from app.indicators.engine import IndicatorEngine
from app.structure.engine import MarketStructureEngine
from app.signals.models import SignalDirectionEnum
from app.trade_decision.targets import TargetPlanner
from app.trade_decision.config import TradeDecisionConfig


def create_candles(n: int = 40, base_price: float = 65000.0):
    candles = []
    curr = base_price
    t = 1700000000000
    for i in range(n):
        c = Candle(
            timestamp=t,
            open=curr,
            high=curr + 100,
            low=curr - 50,
            close=curr + 50,
            volume=150.0,
            close_time=t + 899999,
            quote_volume=(curr + 50) * 150.0,
            trades_count=250,
            is_closed=True,
            state=CandleStateEnum.CLOSED,
        )
        candles.append(c)
        curr += 50
        t += 900000
    return candles


def test_unconstrained_canonical_targets_buy():
    candles = create_candles(45, 60000.0)
    ind = IndicatorEngine.calculate_snapshot(candles, symbol="BTCUSDT", timeframe="15m", is_confirmed=True)
    struct = MarketStructureEngine.evaluate(candles, indicators=ind, is_confirmed=True)
    struct.resistance_zones = []  # Clear zones for unconstrained test

    planned_entry = 65000.0
    stop_loss = 64000.0  # Risk distance = 1000

    targets = TargetPlanner.plan_targets(planned_entry, stop_loss, SignalDirectionEnum.LONG_SETUP, ind, struct)
    assert targets is not None

    # TP1: 65000 + 1000 * 1.25 = 66250
    assert targets.tp1.adjusted_target == 66250.0
    assert targets.tp1.actual_rr_after_adjustment == 1.25

    # TP2: 65000 + 1000 * 2.0 = 67000
    assert targets.tp2.adjusted_target == 67000.0
    assert targets.tp2.actual_rr_after_adjustment == 2.0

    # TP3: 65000 + 1000 * 3.0 = 68000
    assert targets.tp3.adjusted_target == 68000.0
    assert targets.tp3.actual_rr_after_adjustment == 3.0


def test_structural_target_adjustment_buy():
    candles = create_candles(45, 60000.0)
    ind = IndicatorEngine.calculate_snapshot(candles, symbol="BTCUSDT", timeframe="15m", is_confirmed=True)
    struct = MarketStructureEngine.evaluate(candles, indicators=ind, is_confirmed=True)

    planned_entry = 65000.0
    stop_loss = 64000.0

    targets = TargetPlanner.plan_targets(planned_entry, stop_loss, SignalDirectionEnum.LONG_SETUP, ind, struct)
    assert targets is not None
    assert targets.tp1.adjusted_target > planned_entry
    assert targets.tp2.adjusted_target >= targets.tp1.adjusted_target
    assert targets.tp3.adjusted_target >= targets.tp2.adjusted_target
