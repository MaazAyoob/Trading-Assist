"""
Unit tests for SCALP_STRATEGY_V2 — Determinism.
Identical candle sequences must produce identical outputs.
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
        volume=120.0,
        is_closed=True,
        state=CandleStateEnum.CLOSED,
    )


def test_scalp_v2_deterministic_reproducibility():
    candles = []
    price = 65000.0
    for i in range(60):
        ts = 1_700_000_000_000 + i * 60_000
        price += (12.0 if i % 3 != 0 else -6.0)
        candles.append(_make_candle(ts, price - 4.0, price + 6.0, price - 6.0, price))

    ScalpV2StrategyEngine.reset_state()
    sig1 = ScalpV2StrategyEngine.evaluate(candles_1m=candles, symbol="BTCUSDT", is_preview=False)

    ScalpV2StrategyEngine.reset_state()
    sig2 = ScalpV2StrategyEngine.evaluate(candles_1m=candles, symbol="BTCUSDT", is_preview=False)

    assert sig1.direction == sig2.direction
    assert sig1.score == sig2.score
    assert sig1.alignment_score == sig2.alignment_score
    assert sig1.setup_type == sig2.setup_type
    assert sig1.strength == sig2.strength
    assert sig1.entry.planned_entry == sig2.entry.planned_entry
    assert sig1.stop_loss.price == sig2.stop_loss.price
    assert sig1.take_profits.tp1 == sig2.take_profits.tp1
