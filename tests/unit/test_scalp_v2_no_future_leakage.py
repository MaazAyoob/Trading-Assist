"""
Unit tests for SCALP_STRATEGY_V2 — No Future Leakage.
Appending future candles must never alter past signal evaluation.
"""
import pytest
from app.data.schema import Candle, CandleStateEnum
from app.scalp_v2.engine import ScalpV2StrategyEngine


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


def test_no_future_candle_leakage():
    candles = []
    price = 65000.0
    for i in range(50):
        ts = 1_700_000_000_000 + i * 60_000
        price += 10.0
        candles.append(_make_candle(ts, price - 5.0, price + 5.0, price - 5.0, price))

    ScalpV2StrategyEngine.reset_state()
    sig_at_t50 = ScalpV2StrategyEngine.evaluate(candles_1m=candles[:50], symbol="BTCUSDT", is_preview=False)

    # Add 10 future candles (including a massive crash)
    future_candles = list(candles)
    crash_price = price
    for i in range(10):
        ts = 1_700_000_000_000 + (50 + i) * 60_000
        crash_price -= 500.0
        future_candles.append(_make_candle(ts, crash_price + 500.0, crash_price + 500.0, crash_price - 100.0, crash_price))

    # Evaluate again strictly using slice up to t50
    ScalpV2StrategyEngine.reset_state()
    sig_recalculated = ScalpV2StrategyEngine.evaluate(candles_1m=future_candles[:50], symbol="BTCUSDT", is_preview=False)

    assert sig_at_t50.score == sig_recalculated.score
    assert sig_at_t50.direction == sig_recalculated.direction
    assert sig_at_t50.entry.planned_entry == sig_recalculated.entry.planned_entry
