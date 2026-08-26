"""
Unit Tests for Phase 10 — Stop Loss Planner.
Verifies structural stop calculation, ATR safety buffers, and directional invariant enforcement.
"""

import pytest
from app.data.schema import Candle, CandleStateEnum
from app.indicators.engine import IndicatorEngine
from app.structure.engine import MarketStructureEngine
from app.signals.models import SignalDirectionEnum
from app.trade_decision.stops import StopLossPlanner
from app.trade_decision.config import TradeDecisionConfig


def create_candles(n: int = 40, base_price: float = 65000.0):
    candles = []
    curr = base_price
    t = 1700000000000
    for i in range(n):
        c = Candle(
            timestamp=t,
            open=curr,
            high=curr + 120,
            low=curr - 60,
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


def test_buy_stop_loss_planning():
    candles = create_candles(45, 60000.0)
    ind = IndicatorEngine.calculate_snapshot(candles, symbol="BTCUSDT", timeframe="15m", is_confirmed=True)
    struct = MarketStructureEngine.evaluate(candles, indicators=ind, is_confirmed=True)
    planned_entry = candles[-1].close

    stop_plan = StopLossPlanner.plan_stop_loss(planned_entry, SignalDirectionEnum.LONG_SETUP, ind, struct)
    assert stop_plan is not None
    assert stop_plan.price < planned_entry
    assert stop_plan.distance > 0
    assert stop_plan.distance_atr > 0


def test_sell_stop_loss_planning():
    candles = create_candles(45, 60000.0)
    ind = IndicatorEngine.calculate_snapshot(candles, symbol="BTCUSDT", timeframe="15m", is_confirmed=True)
    struct = MarketStructureEngine.evaluate(candles, indicators=ind, is_confirmed=True)
    planned_entry = candles[-1].close

    stop_plan = StopLossPlanner.plan_stop_loss(planned_entry, SignalDirectionEnum.SHORT_SETUP, ind, struct)
    assert stop_plan is not None
    assert stop_plan.price > planned_entry
    assert stop_plan.distance > 0


def test_stop_loss_rejects_excessive_distance():
    candles = create_candles(45, 60000.0)
    ind = IndicatorEngine.calculate_snapshot(candles, symbol="BTCUSDT", timeframe="15m", is_confirmed=True)
    struct = MarketStructureEngine.evaluate(candles, indicators=ind, is_confirmed=True)
    planned_entry = 60000.0

    # Custom config with very tight max stop distance (0.1 ATR) -> should reject
    tight_config = TradeDecisionConfig(max_stop_distance_atr=0.1)
    stop_plan = StopLossPlanner.plan_stop_loss(planned_entry, SignalDirectionEnum.LONG_SETUP, ind, struct, tight_config)
    assert stop_plan is None
