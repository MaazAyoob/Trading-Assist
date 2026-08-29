"""
Unit tests for SCALP_STRATEGY_V2 — Signal frequency, duplicate protection cooldown, and stats.
"""
import pytest
from app.data.schema import Candle, CandleStateEnum
from app.scalp_v2.engine import ScalpV2StrategyEngine
from app.scalp_v2.models import ScalpV2Direction


def _make_candle(ts: int, o: float, h: float, l: float, c: float) -> Candle:
    return Candle(
        symbol="BTCUSDT",
        timeframe="1m",
        timestamp=ts,
        open=o,
        high=h,
        low=l,
        close=c,
        volume=100.0,
        is_closed=True,
        state=CandleStateEnum.CLOSED,
    )


def test_duplicate_protection_cooldown():
    ScalpV2StrategyEngine.reset_state()
    candles = []
    price = 65000.0
    for i in range(50):
        ts = 1_700_000_000_000 + i * 60_000
        price += 10.0
        candles.append(_make_candle(ts, price - 5.0, price + 5.0, price - 5.0, price))

    # First evaluation: BUY signal
    sig1 = ScalpV2StrategyEngine.evaluate(candles_1m=candles, symbol="BTCUSDT")
    assert sig1.direction == ScalpV2Direction.BUY

    # Next immediate candle (same continuation): duplicate protection converts to WATCH
    ts_next = 1_700_000_000_000 + 50 * 60_000
    price += 10.0
    candles.append(_make_candle(ts_next, price - 5.0, price + 5.0, price - 5.0, price))

    sig2 = ScalpV2StrategyEngine.evaluate(candles_1m=candles, symbol="BTCUSDT")
    assert sig2.direction == ScalpV2Direction.WATCH
    assert any("Duplicate protection active" in s for s in sig2.supporting_factors)


def test_frequency_statistics():
    ScalpV2StrategyEngine.reset_state()
    candles = []
    price = 65000.0
    for i in range(60):
        ts = 1_700_000_000_000 + i * 60_000
        price += (10.0 if i % 2 == 0 else -8.0)
        candles.append(_make_candle(ts, price, price + 5.0, price - 5.0, price + 2.0))
        ScalpV2StrategyEngine.evaluate(candles_1m=candles, symbol="BTCUSDT")

    stats = ScalpV2StrategyEngine.get_stats(symbol="BTCUSDT")
    assert stats.total_candles_evaluated > 0
    assert stats.setup_distribution is not None
    assert "TREND_CONTINUATION" in stats.setup_distribution
    assert "PULLBACK" in stats.setup_distribution
    assert "MOMENTUM_BREAKOUT" in stats.setup_distribution
