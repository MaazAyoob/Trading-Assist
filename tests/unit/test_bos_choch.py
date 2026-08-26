import pytest
import numpy as np
from app.data.schema import Candle, CandleStateEnum
from app.structure.config import StructureConfig
from app.structure.models import (
    SwingPoint,
    SwingTypeEnum,
    StructureEventTypeEnum,
    BreakQualityEnum,
)
from app.structure.bos import detect_bos
from app.structure.choch import detect_choch


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


def test_bos_confirmed_close_vs_wick_only():
    """
    Verify that wick-only crosses do NOT create BOS, whereas confirmed candle CLOSE does.
    """
    base_ts = 1700000000000
    # Established confirmed swing high at price = 100.0, confirmed at ts = base_ts + 300000
    sh = SwingPoint(
        id="SH_1",
        type=SwingTypeEnum.SWING_HIGH,
        price=100.0,
        swing_timestamp=base_ts,
        confirmation_timestamp=base_ts + 300000,
        is_confirmed=True,
    )

    # Candle 1: Wick crossed to 105.0, but CLOSE is 98.0 (Below level)
    c1 = create_candle(base_ts + 400000, 95.0, 105.0, 94.0, 98.0, 150.0)

    # Candle 2: Wick at 103.0, and CLOSE is 102.5 (Confirmed above level!)
    c2 = create_candle(base_ts + 500000, 98.0, 103.0, 97.0, 102.5, 200.0)

    candles = [c1, c2]
    atr_values = np.array([2.0, 2.0])
    volumes = np.array([150.0, 200.0])
    vol_sma = np.array([100.0, 100.0])

    # First test c1 alone
    bos_events_1 = detect_bos([c1], [sh], atr_values[:1], volumes[:1], vol_sma[:1])
    assert len(bos_events_1) == 0, "Wick cross must NOT produce confirmed BOS"

    # Now test with c2
    bos_events_2 = detect_bos(candles, [sh], atr_values, volumes, vol_sma)
    assert len(bos_events_2) == 1, "Confirmed close above level must produce BOS"
    assert bos_events_2[0].event_type == StructureEventTypeEnum.BULLISH_BOS
    assert bos_events_2[0].broken_level == 100.0
    assert bos_events_2[0].close_price == 102.5


def test_bos_duplicate_prevention():
    """
    Verify that consecutive closes above the same broken level do not create duplicate BOS events.
    """
    base_ts = 1700000000000
    sh = SwingPoint(
        id="SH_1",
        type=SwingTypeEnum.SWING_HIGH,
        price=100.0,
        swing_timestamp=base_ts,
        confirmation_timestamp=base_ts + 100000,
        is_confirmed=True,
    )

    # 3 consecutive closes above 100.0
    c1 = create_candle(base_ts + 200000, 99.0, 103.0, 98.0, 102.0, 150.0)
    c2 = create_candle(base_ts + 300000, 102.0, 106.0, 101.0, 105.0, 160.0)
    c3 = create_candle(base_ts + 400000, 105.0, 108.0, 104.0, 107.0, 170.0)

    candles = [c1, c2, c3]
    atr_values = np.array([2.0, 2.0, 2.0])
    volumes = np.array([150.0, 160.0, 170.0])
    vol_sma = np.array([100.0, 100.0, 100.0])

    bos_events = detect_bos(candles, [sh], atr_values, volumes, vol_sma)
    assert len(bos_events) == 1, "Must generate exactly 1 BOS event for a single broken swing level"


def test_choch_bearish_to_bullish_transition():
    """
    Verify CHoCH state machine: In established bearish structure (LH1 > LH2 and LL1 > LL2),
    a confirmed close above LH2 creates BULLISH_CHOCH.
    """
    base_ts = 1700000000000
    # Bearish swing sequence:
    # SH1: 120.0, SL1: 100.0, SH2: 110.0 (Lower High), SL2: 90.0 (Lower Low)
    sh1 = SwingPoint(id="SH_1", type=SwingTypeEnum.SWING_HIGH, price=120.0, swing_timestamp=base_ts, confirmation_timestamp=base_ts + 10000, is_confirmed=True)
    sl1 = SwingPoint(id="SL_1", type=SwingTypeEnum.SWING_LOW, price=100.0, swing_timestamp=base_ts + 20000, confirmation_timestamp=base_ts + 30000, is_confirmed=True)
    sh2 = SwingPoint(id="SH_2", type=SwingTypeEnum.SWING_HIGH, price=110.0, swing_timestamp=base_ts + 40000, confirmation_timestamp=base_ts + 50000, is_confirmed=True)
    sl2 = SwingPoint(id="SL_2", type=SwingTypeEnum.SWING_LOW, price=90.0, swing_timestamp=base_ts + 60000, confirmation_timestamp=base_ts + 70000, is_confirmed=True)

    confirmed_swings = [sh1, sl1, sh2, sl2]

    # Candle that closes at 112.0 (Above Lower High SH2 at 110.0)
    c_break = create_candle(base_ts + 80000, 108.0, 114.0, 107.0, 112.0, 300.0)

    candles = [c_break]
    atr_values = np.array([3.0])
    volumes = np.array([300.0])
    vol_sma = np.array([100.0])

    choch_events = detect_choch(candles, confirmed_swings, atr_values, volumes, vol_sma)
    assert len(choch_events) == 1
    assert choch_events[0].event_type == StructureEventTypeEnum.BULLISH_CHOCH
    assert choch_events[0].broken_level == 110.0
    assert choch_events[0].close_price == 112.0
    assert choch_events[0].break_quality in [BreakQualityEnum.STRONG_BREAK, BreakQualityEnum.NORMAL_BREAK]
