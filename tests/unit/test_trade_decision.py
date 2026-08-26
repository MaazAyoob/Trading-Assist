"""
Unit Tests for Phase 10 — Trade Decision Engine.
Tests BUY, SELL, and NO_TRADE generation, multi-strategy evaluations, and schema adherence.
"""

import pytest
from app.data.schema import Candle, CandleStateEnum, MarketDataQuality, QualityStatusEnum
from app.indicators.engine import IndicatorEngine
from app.regime.engine import MarketRegimeEngine
from app.structure.engine import MarketStructureEngine
from app.signals.engine import MultiFactorSignalEngine
from app.trade_decision.models import (
    TradeDecisionEnum,
    TradePlanState,
    DecisionStatusEnum,
    TradePlan,
)
from app.trade_decision.engine import TradeDecisionEngine


def create_bullish_candles(num_cycles: int = 15):
    candles = []
    base_price = 50000.0
    t = 1700000000000

    for k in range(num_cycles):
        peak_base = base_price + k * 250.0
        for j in range(5):
            close = peak_base + j * 50.0
            spread = close * 0.002
            candles.append(
                Candle(
                    timestamp=t,
                    open=close - spread * 0.5,
                    high=close + spread,
                    low=close - spread,
                    close=close,
                    volume=200.0 + k * 10.0 + j * 20.0,
                    close_time=t + 899999,
                    is_closed=True,
                    state=CandleStateEnum.CLOSED,
                )
            )
            t += 900000
        if k < num_cycles - 1:
            top_close = candles[-1].close
            for j in range(1, 5):
                close = top_close - j * 30.0
                spread = close * 0.002
                candles.append(
                    Candle(
                        timestamp=t,
                        open=close + spread * 0.5,
                        high=close + spread,
                        low=close - spread,
                        close=close,
                        volume=80.0,
                        close_time=t + 899999,
                        is_closed=True,
                        state=CandleStateEnum.CLOSED,
                    )
                )
                t += 900000
    return candles


def create_bearish_candles(num_cycles: int = 15):
    candles = []
    base_price = 60000.0
    t = 1700000000000

    for k in range(num_cycles):
        trough_base = base_price - k * 250.0
        for j in range(5):
            close = trough_base - j * 50.0
            spread = close * 0.002
            candles.append(
                Candle(
                    timestamp=t,
                    open=close + spread * 0.5,
                    high=close + spread,
                    low=close - spread,
                    close=close,
                    volume=200.0 + k * 10.0 + j * 20.0,
                    close_time=t + 899999,
                    is_closed=True,
                    state=CandleStateEnum.CLOSED,
                )
            )
            t += 900000
        if k < num_cycles - 1:
            bot_close = candles[-1].close
            for j in range(1, 5):
                close = bot_close + j * 30.0
                spread = close * 0.002
                candles.append(
                    Candle(
                        timestamp=t,
                        open=close - spread * 0.5,
                        high=close + spread,
                        low=close - spread,
                        close=close,
                        volume=80.0,
                        close_time=t + 899999,
                        is_closed=True,
                        state=CandleStateEnum.CLOSED,
                    )
                )
                t += 900000
    return candles


def test_bullish_trade_decision_generation():
    candles = create_bullish_candles(15)
    quality = MarketDataQuality(symbol="BTCUSDT", timeframe="15m", status=QualityStatusEnum.HEALTHY, candle_count=len(candles), is_reliable=True)

    ind = IndicatorEngine.calculate_snapshot(candles, symbol="BTCUSDT", timeframe="15m", is_confirmed=True)
    struct = MarketStructureEngine.evaluate(candles, indicators=ind, is_confirmed=True)
    regime = MarketRegimeEngine.classify(candles=candles, indicators=ind, structure_state=struct.structure_direction, is_confirmed=True)
    signal = MultiFactorSignalEngine.calculate_signal(candles=candles, indicators=ind, regime=regime, structure=struct, is_confirmed=True)

    plan = TradeDecisionEngine.calculate_decision(
        candles=candles,
        indicators=ind,
        regime=regime,
        structure=struct,
        signal=signal,
        quality=quality,
        strategy_context_id="PHASE5_BASELINE",
        is_confirmed=True,
    )

    assert plan.decision in (TradeDecisionEnum.BUY, TradeDecisionEnum.NO_TRADE)
    if plan.decision == TradeDecisionEnum.BUY:
        assert plan.direction == "LONG"
        assert plan.entry is not None
        assert plan.stop_loss is not None
        assert plan.take_profits is not None
        assert plan.stop_loss.price < plan.entry.planned_entry_price < plan.take_profits.tp1.adjusted_target <= plan.take_profits.tp2.adjusted_target <= plan.take_profits.tp3.adjusted_target
        assert plan.risk_reward.tp1_rr >= 1.20


def test_bearish_trade_decision_generation():
    candles = create_bearish_candles(15)
    quality = MarketDataQuality(symbol="BTCUSDT", timeframe="15m", status=QualityStatusEnum.HEALTHY, candle_count=len(candles), is_reliable=True)

    ind = IndicatorEngine.calculate_snapshot(candles, symbol="BTCUSDT", timeframe="15m", is_confirmed=True)
    struct = MarketStructureEngine.evaluate(candles, indicators=ind, is_confirmed=True)
    regime = MarketRegimeEngine.classify(candles=candles, indicators=ind, structure_state=struct.structure_direction, is_confirmed=True)
    signal = MultiFactorSignalEngine.calculate_signal(candles=candles, indicators=ind, regime=regime, structure=struct, is_confirmed=True)

    plan = TradeDecisionEngine.calculate_decision(
        candles=candles,
        indicators=ind,
        regime=regime,
        structure=struct,
        signal=signal,
        quality=quality,
        strategy_context_id="PHASE5_BASELINE",
        is_confirmed=True,
    )

    assert plan.decision in (TradeDecisionEnum.SELL, TradeDecisionEnum.NO_TRADE)
    if plan.decision == TradeDecisionEnum.SELL:
        assert plan.direction == "SHORT"
        assert plan.entry is not None
        assert plan.stop_loss is not None
        assert plan.take_profits is not None
        assert plan.stop_loss.price > plan.entry.planned_entry_price > plan.take_profits.tp1.adjusted_target >= plan.take_profits.tp2.adjusted_target >= plan.take_profits.tp3.adjusted_target


def test_multi_strategy_decisions_separation():
    candles = create_bullish_candles(15)
    quality = MarketDataQuality(symbol="BTCUSDT", timeframe="15m", status=QualityStatusEnum.HEALTHY, candle_count=len(candles), is_reliable=True)

    ind = IndicatorEngine.calculate_snapshot(candles, symbol="BTCUSDT", timeframe="15m", is_confirmed=True)
    struct = MarketStructureEngine.evaluate(candles, indicators=ind, is_confirmed=True)
    regime = MarketRegimeEngine.classify(candles=candles, indicators=ind, structure_state=struct.structure_direction, is_confirmed=True)
    signal = MultiFactorSignalEngine.calculate_signal(candles=candles, indicators=ind, regime=regime, structure=struct, is_confirmed=True)

    multi = TradeDecisionEngine.calculate_multi_strategy_decisions(
        candles=candles,
        indicators=ind,
        regime=regime,
        structure=struct,
        signal=signal,
        quality=quality,
        primary_strategy_id="EXP_A2_PULLBACK_VWAP",
        is_confirmed=True,
    )

    assert multi.selected_strategy_id == "EXP_A2_PULLBACK_VWAP"
    assert "PHASE5_BASELINE" in multi.candidate_decisions
    assert "EXP_A2_PULLBACK_VWAP" in multi.candidate_decisions
    assert "EXP_E2_EXTENSION_VWAP" in multi.candidate_decisions
