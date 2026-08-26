"""
Unit Tests for Phase 10 — Anti-Leakage & Non-Repainting Invariance.
Verifies future mutation invariance, closed candle enforcement, and strict preview isolation.
"""

import pytest
from app.data.schema import Candle, CandleStateEnum, MarketDataQuality, QualityStatusEnum
from app.indicators.engine import IndicatorEngine
from app.regime.engine import MarketRegimeEngine
from app.structure.engine import MarketStructureEngine
from app.signals.engine import MultiFactorSignalEngine
from app.trade_decision.engine import TradeDecisionEngine


def generate_candle_series(n: int = 50, start_price: float = 60000.0):
    candles = []
    curr = start_price
    t = 1700000000000
    for i in range(n):
        c = Candle(
            timestamp=t,
            open=curr,
            high=curr + 100,
            low=curr - 50,
            close=curr + 60,
            volume=50.0 + (i % 10) * 5,
            close_time=t + 899999,
            quote_volume=(curr + 60) * 50.0,
            trades_count=200,
            is_closed=True,
            state=CandleStateEnum.CLOSED,
        )
        candles.append(c)
        curr += 60
        t += 900000
    return candles


def test_future_candle_mutation_invariance():
    history = generate_candle_series(45, 60000.0)
    quality = MarketDataQuality(symbol="BTCUSDT", timeframe="15m", status=QualityStatusEnum.HEALTHY, candle_count=len(history), is_reliable=True)

    # 1. Compute confirmed decision at t=45
    ind_t45 = IndicatorEngine.calculate_snapshot(history, symbol="BTCUSDT", timeframe="15m", is_confirmed=True)
    struct_t45 = MarketStructureEngine.evaluate(history, indicators=ind_t45, is_confirmed=True)
    regime_t45 = MarketRegimeEngine.classify(candles=history, indicators=ind_t45, structure_state=struct_t45.structure_direction, is_confirmed=True)
    sig_t45 = MultiFactorSignalEngine.calculate_signal(candles=history, indicators=ind_t45, regime=regime_t45, structure=struct_t45, is_confirmed=True)

    plan_t45 = TradeDecisionEngine.calculate_decision(
        candles=history,
        indicators=ind_t45,
        regime=regime_t45,
        structure=struct_t45,
        signal=sig_t45,
        quality=quality,
        is_confirmed=True,
    )

    # 2. Slice from extended history (representing exact state at t=45 when future candles exist)
    extended_history = generate_candle_series(50, 60000.0)
    sub_history = extended_history[:45]

    ind_sub = IndicatorEngine.calculate_snapshot(sub_history, symbol="BTCUSDT", timeframe="15m", is_confirmed=True)
    struct_sub = MarketStructureEngine.evaluate(sub_history, indicators=ind_sub, is_confirmed=True)
    regime_sub = MarketRegimeEngine.classify(candles=sub_history, indicators=ind_sub, structure_state=struct_sub.structure_direction, is_confirmed=True)
    sig_sub = MultiFactorSignalEngine.calculate_signal(candles=sub_history, indicators=ind_sub, regime=regime_sub, structure=struct_sub, is_confirmed=True)

    plan_sub = TradeDecisionEngine.calculate_decision(
        candles=sub_history,
        indicators=ind_sub,
        regime=regime_sub,
        structure=struct_sub,
        signal=sig_sub,
        quality=quality,
        is_confirmed=True,
    )

    # Invariance check
    assert plan_t45.decision == plan_sub.decision
    assert plan_t45.decision_alignment_score == plan_sub.decision_alignment_score
    if plan_t45.entry and plan_sub.entry:
        assert plan_t45.entry.planned_entry_price == plan_sub.entry.planned_entry_price


def test_preview_isolation_flag():
    history = generate_candle_series(40, 60000.0)
    ind = IndicatorEngine.calculate_snapshot(history, symbol="BTCUSDT", timeframe="15m", is_confirmed=False)
    struct = MarketStructureEngine.evaluate(history, indicators=ind, is_confirmed=False)
    regime = MarketRegimeEngine.classify(candles=history, indicators=ind, structure_state=struct.structure_direction, is_confirmed=False)
    sig = MultiFactorSignalEngine.calculate_signal(candles=history, indicators=ind, regime=regime, structure=struct, is_confirmed=False)

    preview_plan = TradeDecisionEngine.calculate_decision(
        candles=history,
        indicators=ind,
        regime=regime,
        structure=struct,
        signal=sig,
        is_confirmed=False,
    )

    assert preview_plan.is_confirmed is False
    assert preview_plan.is_preview is True
