"""
Unit Tests for Phase 10 — Entry Planner.
Verifies separation of reference_price and planned_entry_price, entry zone bounds, and TradePlanState.
"""

import pytest
from app.data.schema import Candle, CandleStateEnum, QualityStatusEnum, MarketDataQuality
from app.indicators.engine import IndicatorEngine
from app.regime.engine import MarketRegimeEngine
from app.structure.engine import MarketStructureEngine
from app.signals.engine import MultiFactorSignalEngine
from app.signals.models import SignalDirectionEnum, SignalStatusEnum
from app.trade_decision.entry import EntryPlanner
from app.trade_decision.models import EntryTypeEnum, TradePlanState


def create_sample_candles(n: int = 40, base_price: float = 65000.0):
    candles = []
    curr = base_price
    t = 1700000000000
    for i in range(n):
        c = Candle(
            timestamp=t,
            open=curr,
            high=curr + 100,
            low=curr - 50,
            close=curr + 60,
            volume=150.0,
            close_time=t + 899999,
            quote_volume=(curr + 60) * 150.0,
            trades_count=250,
            is_closed=True,
            state=CandleStateEnum.CLOSED,
        )
        candles.append(c)
        curr += 60
        t += 900000
    return candles


def test_entry_planner_execution():
    candles = create_sample_candles(45, 60000.0)
    ind = IndicatorEngine.calculate_snapshot(candles, symbol="BTCUSDT", timeframe="15m", is_confirmed=True)
    struct = MarketStructureEngine.evaluate(candles, indicators=ind, is_confirmed=True)
    regime = MarketRegimeEngine.classify(candles=candles, indicators=ind, structure_state=struct.structure_direction, is_confirmed=True)
    sig = MultiFactorSignalEngine.calculate_signal(candles=candles, indicators=ind, regime=regime, structure=struct, is_confirmed=True)
    sig.direction = SignalDirectionEnum.LONG_SETUP
    sig.status = SignalStatusEnum.VALID

    result = EntryPlanner.plan_entry(candles[-1], ind, struct, sig)
    assert result is not None
    entry_plan, state = result

    assert entry_plan.planned_entry_price > 0
    assert entry_plan.reference_price == candles[-1].close
    assert entry_plan.entry_zone_low <= entry_plan.planned_entry_price <= entry_plan.entry_zone_high
    assert state in (TradePlanState.WAITING_FOR_ENTRY, TradePlanState.ENTRY_ZONE_ACTIVE)
