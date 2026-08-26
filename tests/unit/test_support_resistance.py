import pytest
from app.data.schema import Candle, CandleStateEnum
from app.structure.config import StructureConfig
from app.structure.models import (
    SwingPoint,
    SwingTypeEnum,
    ZoneTypeEnum,
    ZoneStatusEnum,
    ZoneStrengthEnum,
)
from app.structure.levels import cluster_support_resistance_zones


def create_candle(ts: int, c: float) -> Candle:
    return Candle(
        timestamp=ts,
        open=c - 5.0,
        high=c + 10.0,
        low=c - 10.0,
        close=c,
        volume=100.0,
        is_closed=True,
        state=CandleStateEnum.CLOSED,
    )


def test_support_resistance_clustering_and_strength():
    """
    Verify that swing highs within ATR proximity cluster into a single resistance zone
    with aggregated touch count and proper strength.
    """
    base_ts = 1700000000000
    # 3 swing highs near 100.0: 99.5, 100.2, 100.8 (within ATR=5.0 proximity)
    sh1 = SwingPoint(id="SH_1", type=SwingTypeEnum.SWING_HIGH, price=99.5, swing_timestamp=base_ts, confirmation_timestamp=base_ts + 1000, is_confirmed=True)
    sh2 = SwingPoint(id="SH_2", type=SwingTypeEnum.SWING_HIGH, price=100.2, swing_timestamp=base_ts + 2000, confirmation_timestamp=base_ts + 3000, is_confirmed=True)
    sh3 = SwingPoint(id="SH_3", type=SwingTypeEnum.SWING_HIGH, price=100.8, swing_timestamp=base_ts + 4000, confirmation_timestamp=base_ts + 5000, is_confirmed=True)

    # 1 swing low at 80.0
    sl1 = SwingPoint(id="SL_1", type=SwingTypeEnum.SWING_LOW, price=80.0, swing_timestamp=base_ts + 1500, confirmation_timestamp=base_ts + 2500, is_confirmed=True)

    confirmed_swings = [sh1, sh2, sh3, sl1]
    candles = [create_candle(base_ts + 6000, 92.0)]  # Current close = 92.0 (Inside range)

    support_zones, resistance_zones = cluster_support_resistance_zones(
        candles=candles,
        confirmed_swings=confirmed_swings,
        latest_atr=5.0,
    )

    # 3 swing highs should form 1 resistance zone with touch_count = 3
    assert len(resistance_zones) == 1
    res = resistance_zones[0]
    assert res.zone_type == ZoneTypeEnum.RESISTANCE
    assert res.touch_count == 3
    assert res.strength == ZoneStrengthEnum.STRONG
    assert res.status == ZoneStatusEnum.TESTED
    assert res.price_low == 99.5
    assert res.price_high == 100.8

    # 1 swing low should form 1 support zone with touch_count = 1
    assert len(support_zones) == 1
    sup = support_zones[0]
    assert sup.zone_type == ZoneTypeEnum.SUPPORT
    assert sup.touch_count == 1
    assert sup.strength == ZoneStrengthEnum.WEAK
    assert sup.status == ZoneStatusEnum.ACTIVE


def test_support_zone_broken_lifecycle():
    """
    Verify zone status transitions to BROKEN when price closes well past it.
    """
    base_ts = 1700000000000
    sl1 = SwingPoint(id="SL_1", type=SwingTypeEnum.SWING_LOW, price=80.0, swing_timestamp=base_ts, confirmation_timestamp=base_ts + 1000, is_confirmed=True)
    
    # Current close = 70.0 (Below support 80.0 - 0.5*ATR)
    candles = [create_candle(base_ts + 2000, 70.0)]

    support_zones, _ = cluster_support_resistance_zones(
        candles=candles,
        confirmed_swings=[sl1],
        latest_atr=5.0,
    )

    assert len(support_zones) == 1
    assert support_zones[0].status == ZoneStatusEnum.BROKEN
