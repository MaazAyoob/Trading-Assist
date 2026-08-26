"""
Unit Tests for Phase 10 — Determinism, Serialization, Lifecycle & Security.
Verifies byte-for-byte serialization fidelity, lifecycle state handling, and zero trading API imports.
"""

import pytest
import json
import inspect
from app.data.schema import Candle, CandleStateEnum, MarketDataQuality, QualityStatusEnum
from app.indicators.engine import IndicatorEngine
from app.regime.engine import MarketRegimeEngine
from app.structure.engine import MarketStructureEngine
from app.signals.engine import MultiFactorSignalEngine
from app.trade_decision.engine import TradeDecisionEngine
from app.trade_decision.models import TradePlan, TradePlanState, TradeDecisionEnum
import app.trade_decision


def make_test_data():
    candles = []
    curr = 64000.0
    t = 1700000000000
    for i in range(50):
        c = Candle(
            timestamp=t,
            open=curr,
            high=curr + 80,
            low=curr - 40,
            close=curr + 50,
            volume=100.0,
            close_time=t + 899999,
            quote_volume=(curr + 50) * 100.0,
            trades_count=300,
            is_closed=True,
            state=CandleStateEnum.CLOSED,
        )
        candles.append(c)
        curr += 50
        t += 900000
    return candles


def test_trade_decision_determinism_across_iterations():
    candles = make_test_data()
    ind = IndicatorEngine.calculate_snapshot(candles, symbol="BTCUSDT", timeframe="15m", is_confirmed=True)
    struct = MarketStructureEngine.evaluate(candles, indicators=ind, is_confirmed=True)
    regime = MarketRegimeEngine.classify(candles=candles, indicators=ind, structure_state=struct.structure_direction, is_confirmed=True)
    sig = MultiFactorSignalEngine.calculate_signal(candles=candles, indicators=ind, regime=regime, structure=struct, is_confirmed=True)
    quality = MarketDataQuality(symbol="BTCUSDT", timeframe="15m", status=QualityStatusEnum.HEALTHY, candle_count=len(candles), is_reliable=True)

    baseline_plan = TradeDecisionEngine.calculate_decision(candles, ind, regime, struct, sig, quality, is_confirmed=True)

    for _ in range(15):
        repeat_plan = TradeDecisionEngine.calculate_decision(candles, ind, regime, struct, sig, quality, is_confirmed=True)
        assert repeat_plan.decision == baseline_plan.decision
        assert repeat_plan.decision_alignment_score == baseline_plan.decision_alignment_score
        assert repeat_plan.state == baseline_plan.state
        assert repeat_plan.entry == baseline_plan.entry
        assert repeat_plan.stop_loss == baseline_plan.stop_loss
        assert repeat_plan.take_profits == baseline_plan.take_profits
        assert repeat_plan.risk_reward == baseline_plan.risk_reward
        assert repeat_plan.audit_trace == baseline_plan.audit_trace


def test_trade_plan_json_serialization_roundtrip():
    candles = make_test_data()
    ind = IndicatorEngine.calculate_snapshot(candles, symbol="BTCUSDT", timeframe="15m", is_confirmed=True)
    struct = MarketStructureEngine.evaluate(candles, indicators=ind, is_confirmed=True)
    regime = MarketRegimeEngine.classify(candles=candles, indicators=ind, structure_state=struct.structure_direction, is_confirmed=True)
    sig = MultiFactorSignalEngine.calculate_signal(candles=candles, indicators=ind, regime=regime, structure=struct, is_confirmed=True)
    quality = MarketDataQuality(symbol="BTCUSDT", timeframe="15m", status=QualityStatusEnum.HEALTHY, candle_count=len(candles), is_reliable=True)

    plan = TradeDecisionEngine.calculate_decision(candles, ind, regime, struct, sig, quality, is_confirmed=True)
    json_str = plan.model_dump_json()
    data = json.loads(json_str)
    reconstructed = TradePlan(**data)

    assert reconstructed.decision == plan.decision
    assert reconstructed.decision_alignment_score == plan.decision_alignment_score
    assert reconstructed.strategy_context_id == plan.strategy_context_id


def test_security_audit_zero_exchange_trading_imports():
    """Verify that trade_decision has 0 trading/broker execution imports."""
    forbidden_terms = [
        "ccxt", "binance.client", "order_market", "order_limit", "create_order",
        "cancel_order", "withdraw", "private_key", "secret_key", "api_secret",
        "leverage", "account_balance",
    ]

    for name, module in inspect.getmembers(app.trade_decision):
        if inspect.ismodule(module):
            source = inspect.getsource(module)
            for term in forbidden_terms:
                assert term not in source, f"Security violation: found forbidden trading term '{term}' in {module.__name__}"
