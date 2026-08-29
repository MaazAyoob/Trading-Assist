"""
Unit tests for SCALP_STRATEGY_V2 — Trade Plan (Entry, SL, TP1/2/3, R:R calculation, Invalidation).
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


def test_buy_trade_plan_ordering():
    ScalpV2StrategyEngine.reset_state()
    candles = []
    price = 65000.0
    for i in range(60):
        ts = 1_700_000_000_000 + i * 60_000
        price += 15.0
        candles.append(_make_candle(ts, price - 5.0, price + 5.0, price - 5.0, price))

    sig = ScalpV2StrategyEngine.evaluate(candles_1m=candles, symbol="BTCUSDT")
    assert sig.direction == ScalpV2Direction.BUY

    entry = sig.entry.planned_entry
    sl = sig.stop_loss.price
    tp1 = sig.take_profits.tp1
    tp2 = sig.take_profits.tp2
    tp3 = sig.take_profits.tp3

    assert entry is not None
    assert sl is not None
    assert tp1 is not None and tp2 is not None and tp3 is not None

    # Crucial Buy Invariant: SL < Entry < TP1 < TP2 < TP3
    assert sl < entry < tp1 < tp2 < tp3
    assert sig.take_profits.rr_tp1 == 1.0
    assert sig.take_profits.rr_tp2 == 1.5
    assert sig.take_profits.rr_tp3 == 2.0


def test_sell_trade_plan_ordering():
    ScalpV2StrategyEngine.reset_state()
    candles = []
    price = 68000.0
    for i in range(60):
        ts = 1_700_000_000_000 + i * 60_000
        price -= 15.0
        candles.append(_make_candle(ts, price + 5.0, price + 5.0, price - 5.0, price))

    sig = ScalpV2StrategyEngine.evaluate(candles_1m=candles, symbol="BTCUSDT")
    assert sig.direction == ScalpV2Direction.SELL

    entry = sig.entry.planned_entry
    sl = sig.stop_loss.price
    tp1 = sig.take_profits.tp1
    tp2 = sig.take_profits.tp2
    tp3 = sig.take_profits.tp3

    assert entry is not None
    assert sl is not None
    assert tp1 is not None and tp2 is not None and tp3 is not None

    # Crucial Sell Invariant: TP3 < TP2 < TP1 < Entry < SL
    assert tp3 < tp2 < tp1 < entry < sl
    assert sig.take_profits.rr_tp1 == 1.0
    assert sig.take_profits.rr_tp2 == 1.5
    assert sig.take_profits.rr_tp3 == 2.0


def test_invalidation_conditions_present():
    ScalpV2StrategyEngine.reset_state()
    candles = []
    price = 65000.0
    for i in range(60):
        ts = 1_700_000_000_000 + i * 60_000
        price += 15.0
        candles.append(_make_candle(ts, price - 5.0, price + 5.0, price - 5.0, price))

    sig = ScalpV2StrategyEngine.evaluate(candles_1m=candles, symbol="BTCUSDT")
    assert len(sig.invalidation_conditions) > 0
    assert any("stop loss" in c.lower() for c in sig.invalidation_conditions)
