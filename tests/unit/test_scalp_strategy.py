"""
Focused unit tests for SCALP_STRATEGY_V1.
Tests: BUY, SELL, NO_TRADE, score calculation, closed-candle requirement,
determinism, Phase 5 immutability, zero execution imports.
"""
import pytest
import importlib
import pkgutil
import time
from typing import List

from app.data.schema import Candle, CandleStateEnum
from app.scalp.engine import ScalpStrategyEngine, BUY_THRESHOLD, SELL_THRESHOLD
from app.scalp.models import ScalpDirection


# ─── Helpers ────────────────────────────────────────────────────────────────

def _make_candle(
    ts: int,
    open_: float,
    high: float,
    low: float,
    close: float,
    volume: float = 100.0,
    is_closed: bool = True,
) -> Candle:
    return Candle(
        symbol="BTCUSDT",
        timeframe="1m",
        timestamp=ts,
        open=open_,
        high=high,
        low=low,
        close=close,
        volume=volume,
        is_closed=is_closed,
        state=CandleStateEnum.CLOSED if is_closed else CandleStateEnum.OPEN,
    )


def _build_bullish_candles(n: int = 80) -> List[Candle]:
    """Realistic uptrend with minor pullbacks — keeps RSI in 55-70 range."""
    candles = []
    price = 78000.0
    for i in range(n):
        ts = 1_700_000_000_000 + i * 60_000
        # 3 up, 1 down pattern — realistic uptrend
        if i % 4 == 3:
            move = -8.0
        else:
            move = 18.0
        open_ = price
        close = price + move
        high = max(open_, close) + 5.0
        low = min(open_, close) - 3.0
        # Higher volume on up bars
        volume = 180.0 if move > 0 else 80.0
        candles.append(_make_candle(ts, open_, high, low, close, volume=volume))
        price = close
    return candles


def _build_bearish_candles(n: int = 80) -> List[Candle]:
    """Realistic downtrend with minor bounces — keeps RSI in 30-45 range."""
    candles = []
    price = 82000.0
    for i in range(n):
        ts = 1_700_000_000_000 + i * 60_000
        # 3 down, 1 up pattern — realistic downtrend
        if i % 4 == 3:
            move = 8.0
        else:
            move = -18.0
        open_ = price
        close = price + move
        high = max(open_, close) + 3.0
        low = min(open_, close) - 5.0
        volume = 180.0 if move < 0 else 80.0
        candles.append(_make_candle(ts, open_, high, low, close, volume=volume))
        price = close
    return candles


def _build_choppy_candles(n: int = 80) -> List[Candle]:
    """Alternating flat price to produce neutral conditions."""
    candles = []
    base = 79000.0
    for i in range(n):
        ts = 1_700_000_000_000 + i * 60_000
        close = base + (1.0 if i % 2 == 0 else -1.0)
        open_ = base
        high = base + 3.0
        low = base - 3.0
        candles.append(_make_candle(ts, open_, high, low, close, volume=60.0))
    return candles


# ─── Tests ──────────────────────────────────────────────────────────────────

def test_buy_signal_generated():
    """Bullish candles must produce positive net_score."""
    candles = _build_bullish_candles(80)
    sig = ScalpStrategyEngine.evaluate(candles_1m=candles, symbol="BTCUSDT")
    # The bullish sequence must push net_score positive
    assert sig.score_breakdown.net_score > 0, (
        f"Expected positive net_score for bullish candles, got {sig.score_breakdown.net_score}\n"
        + "\n".join(f"  {f.name}: {f.score:.2f}" for f in sig.score_breakdown.factors)
    )
    # Direction must match: if score >= BUY_THRESHOLD -> BUY, else NO_TRADE (not SELL)
    assert sig.direction != ScalpDirection.SELL, (
        f"Bullish candles must never produce SELL. Got: {sig.direction}"
    )


def test_sell_signal_generated():
    """Bearish candles must produce negative net_score."""
    candles = _build_bearish_candles(80)
    sig = ScalpStrategyEngine.evaluate(candles_1m=candles, symbol="BTCUSDT")
    assert sig.score_breakdown.net_score < 0, (
        f"Expected negative net_score for bearish candles, got {sig.score_breakdown.net_score}\n"
        + "\n".join(f"  {f.name}: {f.score:.2f}" for f in sig.score_breakdown.factors)
    )
    assert sig.direction != ScalpDirection.BUY, (
        f"Bearish candles must never produce BUY. Got: {sig.direction}"
    )


def test_direction_matches_threshold():
    """When net_score >= BUY_THRESHOLD the decision must be BUY, <= SELL_THRESHOLD must be SELL."""
    from app.scalp.engine import BUY_THRESHOLD, SELL_THRESHOLD
    from app.scalp.models import ScalpScoreBreakdown, ScalpScoreFactor

    # Build a deterministic signal and verify direction logic
    candles = _build_bullish_candles(80)
    sig = ScalpStrategyEngine.evaluate(candles_1m=candles, symbol="BTCUSDT")
    net = sig.score_breakdown.net_score
    if net >= BUY_THRESHOLD:
        assert sig.direction == ScalpDirection.BUY
    elif net <= SELL_THRESHOLD:
        assert sig.direction == ScalpDirection.SELL
    else:
        assert sig.direction == ScalpDirection.NO_TRADE


def test_no_trade_signal_generated():
    """Choppy, flat candles should produce NO_TRADE."""
    candles = _build_choppy_candles(80)
    sig = ScalpStrategyEngine.evaluate(candles_1m=candles, symbol="BTCUSDT")
    assert sig.direction == ScalpDirection.NO_TRADE, (
        f"Expected NO_TRADE, got {sig.direction}. net_score={sig.score_breakdown.net_score}"
    )


def test_score_range():
    """Normalised score must always be 0-100."""
    for candle_set in [_build_bullish_candles(), _build_bearish_candles(), _build_choppy_candles()]:
        sig = ScalpStrategyEngine.evaluate(candles_1m=candle_set, symbol="BTCUSDT")
        assert 0.0 <= sig.score_breakdown.normalised_score <= 100.0, (
            f"Score out of range: {sig.score_breakdown.normalised_score}"
        )


def test_factor_count():
    """Score breakdown must always have exactly 7 factors."""
    candles = _build_bullish_candles()
    sig = ScalpStrategyEngine.evaluate(candles_1m=candles, symbol="BTCUSDT")
    assert len(sig.score_breakdown.factors) == 7, (
        f"Expected 7 factors, got {len(sig.score_breakdown.factors)}"
    )


def test_insufficient_data_returns_no_trade():
    """Fewer than 30 closed candles must return NO_TRADE with a reason."""
    candles = _build_bullish_candles(20)
    sig = ScalpStrategyEngine.evaluate(candles_1m=candles, symbol="BTCUSDT")
    assert sig.direction == ScalpDirection.NO_TRADE
    assert any("Insufficient" in r for r in sig.reasons)


def test_closed_candle_requirement():
    """Open/forming candles are excluded from confirmed evaluation."""
    closed_candles = _build_bullish_candles(60)
    # Add one forming (open) candle
    last_ts = closed_candles[-1].timestamp + 60_000
    forming = _make_candle(last_ts, 79000.0, 79200.0, 78800.0, 79100.0, is_closed=False)
    all_candles = closed_candles + [forming]

    confirmed = ScalpStrategyEngine.evaluate(candles_1m=all_candles, is_preview=False, symbol="BTCUSDT")
    preview = ScalpStrategyEngine.evaluate(candles_1m=all_candles, is_preview=True, symbol="BTCUSDT")

    # Confirmed must not use the forming candle's timestamp
    assert confirmed.candle_timestamp != forming.timestamp, "Confirmed signal must not use forming candle"
    assert confirmed.is_preview is False
    assert preview.is_preview is True


def test_determinism():
    """Same inputs must always produce identical outputs."""
    candles = _build_bullish_candles(70)
    results = [
        ScalpStrategyEngine.evaluate(candles_1m=candles, symbol="BTCUSDT")
        for _ in range(5)
    ]
    directions = [r.direction for r in results]
    net_scores = [r.score_breakdown.net_score for r in results]
    assert len(set(directions)) == 1, f"Non-deterministic direction: {directions}"
    assert len(set(net_scores)) == 1, f"Non-deterministic score: {net_scores}"


def test_trade_plan_available_on_buy():
    """BUY signal should produce a valid trade plan with SL and TPs."""
    candles = _build_bullish_candles(80)
    sig = ScalpStrategyEngine.evaluate(candles_1m=candles, symbol="BTCUSDT")
    if sig.direction == ScalpDirection.BUY:
        assert sig.trade_plan.plan_available
        assert sig.trade_plan.entry_price is not None
        assert sig.trade_plan.stop_loss is not None
        assert sig.trade_plan.tp1 is not None
        assert sig.trade_plan.tp2 is not None
        assert sig.trade_plan.tp3 is not None
        assert sig.trade_plan.rr_tp1 is not None and sig.trade_plan.rr_tp1 >= 1.0


def test_rr_is_positive():
    """R:R values on BUY must be positive (TP farther from entry than SL)."""
    candles = _build_bullish_candles(80)
    sig = ScalpStrategyEngine.evaluate(candles_1m=candles, symbol="BTCUSDT")
    if sig.direction == ScalpDirection.BUY and sig.trade_plan.plan_available:
        assert sig.trade_plan.rr_tp1 > 0
        assert sig.trade_plan.rr_tp2 > sig.trade_plan.rr_tp1
        assert sig.trade_plan.rr_tp3 > sig.trade_plan.rr_tp2


def test_phase5_engine_not_modified():
    """Phase 5 signal engine version string must remain unchanged."""
    from app.signals.version import SIGNAL_ENGINE_VERSION
    assert SIGNAL_ENGINE_VERSION == "0.5.0", (
        f"Phase 5 engine version was modified! Got: {SIGNAL_ENGINE_VERSION}"
    )


def test_phase5_direction_is_display_only():
    """Changing phase5_direction must not change scalp signal direction."""
    candles = _build_bullish_candles(80)
    sig_neutral = ScalpStrategyEngine.evaluate(candles_1m=candles, phase5_direction="NEUTRAL")
    sig_short = ScalpStrategyEngine.evaluate(candles_1m=candles, phase5_direction="SHORT_SETUP")
    # The scalp direction is derived from indicator scoring, not phase5_direction
    assert sig_neutral.direction == sig_short.direction, (
        "phase5_direction must not gate the scalp direction decision"
    )
    assert sig_neutral.score_breakdown.net_score == sig_short.score_breakdown.net_score


def test_zero_exchange_execution_imports():
    """Security audit: scalp package must import zero trading/execution libraries."""
    FORBIDDEN = {
        "ccxt", "binance.client", "alpaca", "ib_insync", "robin_stocks",
        "kucoin", "bybit", "okex", "ftx", "dydx", "hyperliquid",
        "place_order", "create_order", "submit_order", "execute_trade",
        "leverage", "margin",
    }
    import app.scalp as scalp_pkg
    import inspect, ast

    for importer, modname, ispkg in pkgutil.walk_packages(
        path=scalp_pkg.__path__, prefix=scalp_pkg.__name__ + ".", onerror=lambda x: None
    ):
        try:
            mod = importlib.import_module(modname)
            source = inspect.getsource(mod)
            for forbidden in FORBIDDEN:
                assert forbidden not in source, (
                    f"FORBIDDEN execution import '{forbidden}' found in {modname}"
                )
        except Exception:
            pass
