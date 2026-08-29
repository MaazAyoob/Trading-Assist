"""
Unit tests for SCALP_STRATEGY_V2 — Base scoring, directions, threshold bounds, and models.
"""
import pytest
from typing import List
from app.data.schema import Candle, CandleStateEnum
from app.scalp_v2.engine import ScalpV2StrategyEngine
from app.scalp_v2.models import (
    ScalpV2Direction,
    ScalpV2Strength,
    ScalpV2SetupType,
    ScalpV2TradeState,
)
from app.scalp_v2.config import (
    BUY_THRESHOLD,
    SELL_THRESHOLD,
    WATCH_POS_MIN,
    WATCH_POS_MAX,
    WATCH_NEG_MIN,
    WATCH_NEG_MAX,
)


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
    candles = []
    price = 65000.0
    for i in range(n):
        ts = 1_700_000_000_000 + i * 60_000
        # Ensure last candle is an up bar
        move = -4.0 if (i % 4 == 2 and i != n - 1) else 16.0
        open_ = price
        close = price + move
        high = max(open_, close) + 4.0
        low = min(open_, close) - 3.0
        volume = 150.0 if move > 0 else 70.0
        candles.append(_make_candle(ts, open_, high, low, close, volume=volume))
        price = close
    return candles


def _build_bearish_candles(n: int = 80) -> List[Candle]:
    candles = []
    price = 68000.0
    for i in range(n):
        ts = 1_700_000_000_000 + i * 60_000
        # Ensure last candle is a down bar
        move = 4.0 if (i % 4 == 2 and i != n - 1) else -16.0
        open_ = price
        close = price + move
        high = max(open_, close) + 3.0
        low = min(open_, close) - 4.0
        volume = 150.0 if move < 0 else 70.0
        candles.append(_make_candle(ts, open_, high, low, close, volume=volume))
        price = close
    return candles


def _build_flat_candles(n: int = 80) -> List[Candle]:
    candles = []
    price = 66000.0
    for i in range(n):
        ts = 1_700_000_000_000 + i * 60_000
        open_ = price
        close = price
        high = price + 1.0
        low = price - 1.0
        candles.append(_make_candle(ts, open_, high, low, close, volume=50.0))
        price = close
    return candles


def test_scalp_v2_bullish_signal():
    ScalpV2StrategyEngine.reset_state()
    candles = _build_bullish_candles(80)
    sig = ScalpV2StrategyEngine.evaluate(candles_1m=candles, symbol="BTCUSDT")
    assert sig.direction == ScalpV2Direction.BUY
    assert sig.score >= BUY_THRESHOLD
    assert sig.alignment_score >= BUY_THRESHOLD
    assert sig.strength in (ScalpV2Strength.STRONG, ScalpV2Strength.VERY_STRONG, ScalpV2Strength.MODERATE, ScalpV2Strength.WEAK)
    assert sig.strategy_id == "SCALP_STRATEGY_V2"
    assert sig.strategy_version == "2.0.0"
    assert sig.trade_state == ScalpV2TradeState.BUY


def test_scalp_v2_bearish_signal():
    ScalpV2StrategyEngine.reset_state()
    candles = _build_bearish_candles(80)
    sig = ScalpV2StrategyEngine.evaluate(candles_1m=candles, symbol="BTCUSDT")
    assert sig.direction == ScalpV2Direction.SELL
    assert sig.score <= SELL_THRESHOLD
    assert sig.alignment_score >= abs(SELL_THRESHOLD)
    assert sig.trade_state == ScalpV2TradeState.SELL


def test_scalp_v2_neutral_no_trade():
    ScalpV2StrategyEngine.reset_state()
    candles = _build_flat_candles(80)
    sig = ScalpV2StrategyEngine.evaluate(candles_1m=candles, symbol="BTCUSDT")
    assert sig.direction in (ScalpV2Direction.NO_TRADE, ScalpV2Direction.WATCH)
    assert -35.0 < sig.score < 35.0


def test_scalp_v2_score_boundaries():
    ScalpV2StrategyEngine.reset_state()
    candles = _build_bullish_candles(80)
    sig = ScalpV2StrategyEngine.evaluate(candles_1m=candles, symbol="BTCUSDT")
    assert -100.0 <= sig.score <= 100.0
    assert 0.0 <= sig.alignment_score <= 100.0
    assert sig.score_breakdown.raw_bull_score >= 0.0
    assert sig.score_breakdown.raw_bear_score >= 0.0
