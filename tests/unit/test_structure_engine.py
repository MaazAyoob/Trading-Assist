import pytest
import numpy as np
from app.data.schema import Candle, CandleStateEnum, QualityStatusEnum
from app.indicators.engine import IndicatorEngine
from app.structure.engine import MarketStructureEngine


def create_candle(ts: int, o: float, h: float, l: float, c: float, v: float = 100.0) -> Candle:
    return Candle(
        timestamp=ts,
        open=o,
        high=h,
        low=l,
        close=c,
        volume=v,
        is_closed=True,
        state=CandleStateEnum.CLOSED,
    )


def test_structure_determinism():
    """
    Verify running MarketStructureEngine twice on the same input yields identical results.
    """
    np.random.seed(42)
    base_ts = 1700000000000
    candles = []
    price = 60000.0
    for i in range(120):
        price += np.random.uniform(-100, 105)
        h = price + np.random.uniform(10, 50)
        l = price - np.random.uniform(10, 50)
        c = price + np.random.uniform(-10, 10)
        candles.append(create_candle(base_ts + i * 60000, price, h, l, c))

    ind = IndicatorEngine.calculate_snapshot(candles, symbol="BTCUSDT", timeframe="15m", is_confirmed=True)

    struct1 = MarketStructureEngine.evaluate(candles, indicators=ind, is_confirmed=True)
    struct2 = MarketStructureEngine.evaluate(candles, indicators=ind, is_confirmed=True)

    assert struct1.structure_direction == struct2.structure_direction
    assert len(struct1.confirmed_swings) == len(struct2.confirmed_swings)
    assert len(struct1.bos_events) == len(struct2.bos_events)
    assert len(struct1.support_zones) == len(struct2.support_zones)
    for s1, s2 in zip(struct1.confirmed_swings, struct2.confirmed_swings):
        assert s1.id == s2.id
        assert s1.price == s2.price


def test_structure_non_repainting():
    """
    Verify that appending future candles does NOT modify or erase previously confirmed swings or BOS events.
    """
    base_ts = 1700000000000
    candles_initial = []
    price = 50000.0
    for i in range(80):
        price += 10.0 if i % 2 == 0 else -8.0
        candles_initial.append(create_candle(base_ts + i * 60000, price, price + 30, price - 30, price))

    ind_initial = IndicatorEngine.calculate_snapshot(candles_initial, symbol="BTCUSDT", timeframe="15m", is_confirmed=True)
    struct_initial = MarketStructureEngine.evaluate(candles_initial, indicators=ind_initial, is_confirmed=True)
    initial_confirmed_ids = [s.id for s in struct_initial.confirmed_swings]

    # Append 30 more future candles
    candles_extended = list(candles_initial)
    for i in range(80, 110):
        price += 15.0
        candles_extended.append(create_candle(base_ts + i * 60000, price, price + 20, price - 20, price))

    ind_extended = IndicatorEngine.calculate_snapshot(candles_extended, symbol="BTCUSDT", timeframe="15m", is_confirmed=True)
    struct_extended = MarketStructureEngine.evaluate(candles_extended, indicators=ind_extended, is_confirmed=True)
    extended_confirmed_ids = [s.id for s in struct_extended.confirmed_swings]

    # All initial confirmed swing IDs must still be present in the extended structure
    for s_id in initial_confirmed_ids:
        assert s_id in extended_confirmed_ids, f"Previously confirmed swing {s_id} must not disappear!"
