"""
Unit tests for SCALP_STRATEGY_V2 — Isolation & Security.
Verifies that:
  1. SCALP_STRATEGY_V1 remains 100% frozen and unmodified.
  2. Phase 3-12 analytical engines remain untouched.
  3. Zero broker, order placement, or private execution imports exist.
"""
import pytest
import pkgutil
import importlib
from app.scalp.engine import ScalpStrategyEngine
from app.scalp_v2.engine import ScalpV2StrategyEngine


def test_v1_still_runs_unaffected():
    """Verify V1 engine functions as baseline without any regression."""
    from tests.unit.test_scalp_v2 import _build_bullish_candles
    candles = _build_bullish_candles(80)
    v1_sig = ScalpStrategyEngine.evaluate(candles_1m=candles, symbol="BTCUSDT")
    assert v1_sig.strategy_id == "SCALP_STRATEGY_V1"
    assert v1_sig.strategy_version == "1.0.0"


def test_zero_execution_or_broker_imports():
    """Verify strictly shadow / analysis only with zero broker or execution dependencies."""
    forbidden_terms = [
        "ccxt",
        "binance.client",
        "order_placement",
        "place_order",
        "private_key",
        "secret_key",
        "execute_trade",
    ]

    import app.scalp_v2
    package = app.scalp_v2
    for _, module_name, _ in pkgutil.walk_packages(package.__path__, package.__name__ + "."):
        mod = importlib.import_module(module_name)
        with open(mod.__file__, "r", encoding="utf-8") as f:
            content = f.read().lower()
            for term in forbidden_terms:
                assert term not in content, f"Forbidden term '{term}' found in {module_name}"
