"""
Unit Tests for Phase 10 — NO_TRADE Decision Scenarios.
Verifies deterministic rejection reasons and diagnostic audit trails when market conditions
do not satisfy the decision criteria.
"""

import pytest
from app.data.schema import Candle, CandleStateEnum, MarketDataQuality, QualityStatusEnum
from app.indicators.engine import IndicatorEngine
from app.regime.engine import MarketRegimeEngine
from app.structure.engine import MarketStructureEngine
from app.signals.engine import MultiFactorSignalEngine
from app.signals.models import SignalDirectionEnum, SignalStatusEnum
from app.regime.models import OverallRegimeEnum, TrendStrengthEnum
from app.structure.models import StructureEvent, StructureEventTypeEnum, BreakQualityEnum, SupportResistanceZone, ZoneTypeEnum, ZoneStrengthEnum, ZoneStatusEnum
from app.trade_decision.models import TradeDecisionEnum, TradePlanState, AuditCheckStatusEnum
from app.trade_decision.engine import TradeDecisionEngine


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


def test_no_trade_on_stale_data():
    candles = create_candles(45, 60000.0)
    ind = IndicatorEngine.calculate_snapshot(candles, symbol="BTCUSDT", timeframe="15m", is_confirmed=True)
    struct = MarketStructureEngine.evaluate(candles, indicators=ind, is_confirmed=True)
    regime = MarketRegimeEngine.classify(candles=candles, indicators=ind, structure_state=struct.structure_direction, is_confirmed=True)
    sig = MultiFactorSignalEngine.calculate_signal(candles=candles, indicators=ind, regime=regime, structure=struct, is_confirmed=True)

    quality = MarketDataQuality(symbol="BTCUSDT", timeframe="15m", status=QualityStatusEnum.INVALID, candle_count=len(candles), stale=True)

    plan = TradeDecisionEngine.calculate_decision(candles, ind, regime, struct, sig, quality)
    assert plan.decision == TradeDecisionEnum.NO_TRADE
    assert plan.state == TradePlanState.NO_TRADE
    assert plan.audit_trace.data_quality_check.status == AuditCheckStatusEnum.FAIL


def test_no_trade_on_opposing_regime():
    candles = create_candles(45, 60000.0)
    ind = IndicatorEngine.calculate_snapshot(candles, symbol="BTCUSDT", timeframe="15m", is_confirmed=True)
    struct = MarketStructureEngine.evaluate(candles, indicators=ind, is_confirmed=True)
    regime = MarketRegimeEngine.classify(candles=candles, indicators=ind, structure_state=struct.structure_direction, is_confirmed=True)
    sig = MultiFactorSignalEngine.calculate_signal(candles=candles, indicators=ind, regime=regime, structure=struct, is_confirmed=True)
    sig.direction = SignalDirectionEnum.LONG_SETUP
    sig.status = SignalStatusEnum.VALID
    sig.score = 75.0

    # Force strong opposing regime
    regime.overall_regime = OverallRegimeEnum.TRENDING_BEARISH
    regime.trend_strength = TrendStrengthEnum.VERY_STRONG

    quality = MarketDataQuality(symbol="BTCUSDT", timeframe="15m", status=QualityStatusEnum.HEALTHY, candle_count=len(candles), is_reliable=True)

    plan = TradeDecisionEngine.calculate_decision(candles, ind, regime, struct, sig, quality)
    assert plan.decision == TradeDecisionEnum.NO_TRADE
    assert plan.audit_trace.regime_check.status == AuditCheckStatusEnum.FAIL


def test_no_trade_on_opposing_choch():
    candles = create_candles(45, 60000.0)
    ind = IndicatorEngine.calculate_snapshot(candles, symbol="BTCUSDT", timeframe="15m", is_confirmed=True)
    struct = MarketStructureEngine.evaluate(candles, indicators=ind, is_confirmed=True)
    regime = MarketRegimeEngine.classify(candles=candles, indicators=ind, structure_state=struct.structure_direction, is_confirmed=True)
    sig = MultiFactorSignalEngine.calculate_signal(candles=candles, indicators=ind, regime=regime, structure=struct, is_confirmed=True)
    sig.direction = SignalDirectionEnum.LONG_SETUP
    sig.status = SignalStatusEnum.VALID
    sig.score = 75.0

    # Force opposing CHoCH
    struct.choch_events = [
        StructureEvent(
            event_id="CH_1",
            event_type=StructureEventTypeEnum.BEARISH_CHOCH,
            broken_swing_id="SL_1",
            broken_level=62000.0,
            break_timestamp=candles[-1].timestamp,
            confirmation_timestamp=candles[-1].timestamp,
            close_price=61900.0,
            break_distance=100.0,
            atr_normalized_distance=0.25,
            volume_ratio=1.5,
            candle_body_ratio=0.8,
            break_quality=BreakQualityEnum.NORMAL_BREAK,
            is_confirmed=True,
        )
    ]

    quality = MarketDataQuality(symbol="BTCUSDT", timeframe="15m", status=QualityStatusEnum.HEALTHY, candle_count=len(candles), is_reliable=True)

    plan = TradeDecisionEngine.calculate_decision(candles, ind, regime, struct, sig, quality)
    assert plan.decision == TradeDecisionEnum.NO_TRADE
    assert plan.audit_trace.structure_check.status == AuditCheckStatusEnum.FAIL


def test_no_trade_on_immediate_resistance_barrier():
    candles = create_candles(45, 60000.0)
    ind = IndicatorEngine.calculate_snapshot(candles, symbol="BTCUSDT", timeframe="15m", is_confirmed=True)
    struct = MarketStructureEngine.evaluate(candles, indicators=ind, is_confirmed=True)
    regime = MarketRegimeEngine.classify(candles=candles, indicators=ind, structure_state=struct.structure_direction, is_confirmed=True)
    sig = MultiFactorSignalEngine.calculate_signal(candles=candles, indicators=ind, regime=regime, structure=struct, is_confirmed=True)
    sig.direction = SignalDirectionEnum.LONG_SETUP
    sig.status = SignalStatusEnum.VALID
    sig.score = 75.0

    close_p = candles[-1].close
    struct.resistance_zones = [
        SupportResistanceZone(
            zone_id="RES_CLOSE",
            zone_type=ZoneTypeEnum.RESISTANCE,
            price_low=close_p + 10.0,  # 10 dollars above close (< 0.20 ATR)
            price_high=close_p + 100.0,
            price_center=close_p + 55.0,
            strength=ZoneStrengthEnum.MODERATE,
            status=ZoneStatusEnum.ACTIVE,
            touch_count=3,
            created_timestamp=candles[-1].timestamp - 500000,
            last_touch_timestamp=candles[-1].timestamp - 100000,
        )
    ]

    quality = MarketDataQuality(symbol="BTCUSDT", timeframe="15m", status=QualityStatusEnum.HEALTHY, candle_count=len(candles), is_reliable=True)

    plan = TradeDecisionEngine.calculate_decision(candles, ind, regime, struct, sig, quality)
    assert plan.decision == TradeDecisionEnum.NO_TRADE
    assert plan.audit_trace.sr_clearance_check.status == AuditCheckStatusEnum.FAIL
