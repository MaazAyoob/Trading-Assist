"""
Unit tests for SCALP_STRATEGY_V2 — Setup Types: Trend Continuation, Pullback, and Momentum Breakout.
"""
import pytest
from app.data.schema import Candle, CandleStateEnum
from app.scalp_v2.engine import ScalpV2StrategyEngine
from app.scalp_v2.models import (
    ScalpV2Direction,
    ScalpV2SetupType,
)


def _make_candle(ts: int, o: float, h: float, l: float, c: float, v: float = 100.0) -> Candle:
    return Candle(
        symbol="BTCUSDT",
        timeframe="1m",
        timestamp=ts,
        open=o,
        high=h,
        low=l,
        close=c,
        volume=v,
        is_closed=True,
        state=CandleStateEnum.CLOSED,
    )


def test_momentum_breakout_detection():
    ScalpV2StrategyEngine.reset_state()
    candles = []
    price = 65000.0
    # 30 candles ranging between 65000 and 65100
    for i in range(30):
        ts = 1_700_000_000_000 + i * 60_000
        candles.append(_make_candle(ts, price, price + 40.0, price - 40.0, price + 10.0, v=100.0))

    # Breakout candle: surge above resistance to 65350 with high volume
    ts_breakout = 1_700_000_000_000 + 30 * 60_000
    candles.append(_make_candle(ts_breakout, price + 10.0, 65380.0, price, 65350.0, v=350.0))

    sig = ScalpV2StrategyEngine.evaluate(candles_1m=candles, symbol="BTCUSDT")
    assert sig.setup_type == ScalpV2SetupType.MOMENTUM_BREAKOUT
    assert sig.direction == ScalpV2Direction.BUY
    assert any("Breakout" in r for r in sig.supporting_factors)


def test_pullback_setup_detection():
    ScalpV2StrategyEngine.reset_state()
    # 5m bullish context candles
    candles_5m = []
    p5 = 65000.0
    for i in range(30):
        ts = 1_700_000_000_000 + i * 300_000
        candles_5m.append(_make_candle(ts, p5, p5 + 30.0, p5 - 10.0, p5 + 20.0, v=500.0))
        p5 += 20.0

    # 1m candles: steady uptrend with realistic steps
    candles_1m = []
    p1 = 65000.0
    for i in range(50):
        ts = 1_700_000_000_000 + i * 60_000
        step = -3.0 if i % 3 == 0 else 6.0
        p1 += step
        candles_1m.append(_make_candle(ts, p1 - step, p1 + 4.0, p1 - 4.0, p1, v=120.0))

    # Pullback candles into EMA21
    last_p = p1
    for i in range(4):
        ts = 1_700_000_000_000 + (50 + i) * 60_000
        last_p -= 6.0
        candles_1m.append(_make_candle(ts, last_p + 6.0, last_p + 7.0, last_p - 3.0, last_p, v=90.0))

    # Reversal bounce candle (green candle closing up)
    ts_bounce = 1_700_000_000_000 + 54 * 60_000
    candles_1m.append(_make_candle(ts_bounce, last_p, last_p + 15.0, last_p - 1.0, last_p + 12.0, v=180.0))

    sig = ScalpV2StrategyEngine.evaluate(
        candles_1m=candles_1m,
        candles_5m=candles_5m,
        symbol="BTCUSDT",
    )
    assert sig.direction in (ScalpV2Direction.BUY, ScalpV2Direction.WATCH)
    assert sig.score_breakdown.setup_bonus > 0


def test_continuation_setup_detection():
    ScalpV2StrategyEngine.reset_state()
    candles = []
    price = 65000.0
    for i in range(60):
        ts = 1_700_000_000_000 + i * 60_000
        price += 10.0
        candles.append(_make_candle(ts, price - 5.0, price + 6.0, price - 6.0, price, v=110.0))

    sig = ScalpV2StrategyEngine.evaluate(candles_1m=candles, symbol="BTCUSDT")
    assert sig.direction == ScalpV2Direction.BUY
    assert sig.setup_type in (ScalpV2SetupType.TREND_CONTINUATION, ScalpV2SetupType.MOMENTUM_BREAKOUT)
