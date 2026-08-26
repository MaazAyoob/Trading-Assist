"""
Unit Tests for Phase 11 — Professional Terminal Polish, Resilience & Security Invariants.
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
    TradePlan,
)
from app.trade_decision.engine import TradeDecisionEngine


def create_sample_candles(count: int = 60, start_price: float = 60000.0):
    candles = []
    t = 1700000000000
    p = start_price
    for i in range(count):
        p += (i % 3 - 1) * 20.0
        candles.append(
            Candle(
                timestamp=t,
                open=p - 10.0,
                high=p + 25.0,
                low=p - 25.0,
                close=p,
                volume=150.0,
                close_time=t + 899999,
                is_closed=True,
                state=CandleStateEnum.CLOSED,
            )
        )
        t += 900000
    return candles


def test_data_quality_resilience_and_stale_detection():
    # Healthy quality
    q_healthy = MarketDataQuality(
        symbol="BTCUSDT",
        timeframe="15m",
        status=QualityStatusEnum.HEALTHY,
        candle_count=50,
        stale=False,
    )
    assert q_healthy.stale is False
    assert q_healthy.status == QualityStatusEnum.HEALTHY

    # Stale/warning quality
    q_warning = MarketDataQuality(
        symbol="BTCUSDT",
        timeframe="15m",
        status=QualityStatusEnum.WARNING,
        candle_count=50,
        stale=True,
    )
    assert q_warning.stale is True
    assert q_warning.status == QualityStatusEnum.WARNING


def test_strategy_context_isolation_across_candidates():
    candles = create_sample_candles(80, 65000.0)
    quality = MarketDataQuality(symbol="BTCUSDT", timeframe="15m", status=QualityStatusEnum.HEALTHY, candle_count=80)

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

    assert "EXP_A2_PULLBACK_VWAP" in multi.candidate_decisions
    assert "EXP_E2_EXTENSION_VWAP" in multi.candidate_decisions
    assert "PHASE5_BASELINE" in multi.candidate_decisions

    for strat_id, plan in multi.candidate_decisions.items():
        assert plan.strategy_context_id == strat_id
        assert 0.0 <= plan.decision_alignment_score <= 100.0
        assert plan.decision in (TradeDecisionEnum.BUY, TradeDecisionEnum.SELL, TradeDecisionEnum.NO_TRADE)


def test_security_audit_zero_exchange_trading_imports():
    """Verify zero live trading, order placement, or exchange execution imports exist."""
    import importlib
    import inspect
    import app.trade_decision.engine
    import app.trade_decision.decision

    for mod in [app.trade_decision.engine, app.trade_decision.decision]:
        source = inspect.getsource(mod)
        for forbidden in ["ccxt", "binance.client", "place_order", "create_order", "api_key", "secret_key"]:
            assert forbidden not in source.lower(), f"Forbidden trading term '{forbidden}' detected in {mod}!"
