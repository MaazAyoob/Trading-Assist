import pytest
import numpy as np
from app.data.schema import Candle, CandleStateEnum
from app.structure.config import StructureConfig
from app.structure.models import SwingTypeEnum
from app.structure.swings import detect_swings


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


def test_swing_high_low_confirmation_timing():
    """
    Verify causally correct confirmation:
    For LEFT=3, RIGHT=3, a peak at index 4 (timestamp T4) must only be confirmed at index 7 (timestamp T7).
    """
    prices = [
        # 0, 1, 2, 3 (left window)
        (100, 105, 95, 102),
        (102, 108, 98, 106),
        (106, 112, 104, 110),
        (110, 115, 108, 112),
        # 4: The Swing Peak
        (112, 130, 110, 125),
        # 5, 6, 7 (right window to confirm peak 4)
        (125, 122, 115, 118),
        (118, 116, 110, 112),
        (112, 110, 100, 105),  # Right window completed here
        # 8 (further candle)
        (105, 108, 98, 102),
    ]

    base_ts = 1700000000000
    candles = [create_candle(base_ts + i * 60000, p[0], p[1], p[2], p[3]) for i, p in enumerate(prices)]
    atr_values = np.full(len(candles), 5.0)

    cfg = StructureConfig(SWING_LEFT=3, SWING_RIGHT=3)
    confirmed, developing = detect_swings(candles, atr_values, cfg)

    # Check that swing high was detected
    swing_highs = [s for s in confirmed if s.type == SwingTypeEnum.SWING_HIGH]
    assert len(swing_highs) >= 1

    sh = swing_highs[0]
    assert sh.price == 130.0
    assert sh.swing_timestamp == base_ts + 4 * 60000  # Index 4
    assert sh.confirmation_timestamp == base_ts + 7 * 60000  # Index 4 + 3 = 7


def test_developing_swings_separation():
    """
    Verify that candidate pivots in the right-side window remain in developing_swings and NOT in confirmed_swings.
    """
    # 6 bars total (not enough right bars to confirm index 4)
    prices = [
        (100, 105, 95, 102),
        (102, 108, 98, 106),
        (106, 112, 104, 110),
        (110, 115, 108, 112),
        (112, 135, 110, 130),  # Potential peak
        (130, 128, 120, 125),  # Only 1 right bar!
    ]

    base_ts = 1700000000000
    candles = [create_candle(base_ts + i * 60000, p[0], p[1], p[2], p[3]) for i, p in enumerate(prices)]
    atr_values = np.full(len(candles), 5.0)

    cfg = StructureConfig(SWING_LEFT=3, SWING_RIGHT=3)
    confirmed, developing = detect_swings(candles, atr_values, cfg)

    # No confirmed swing highs yet because right window (3) is not complete
    confirmed_shs = [s for s in confirmed if s.type == SwingTypeEnum.SWING_HIGH]
    assert len(confirmed_shs) == 0

    # Developing swing should capture the potential peak at index 4
    dev_shs = [s for s in developing if s.type == SwingTypeEnum.SWING_HIGH]
    assert len(dev_shs) >= 1
    assert dev_shs[0].price == 135.0
    assert dev_shs[0].is_confirmed is False


def test_equal_highs_deterministic_tie_handling():
    """
    Verify deterministic behavior when two bars have identical high prices within ATR tolerance.
    """
    prices = [
        (100, 105, 95, 102),
        (102, 108, 98, 106),
        (106, 112, 104, 110),
        (110, 120, 108, 115),  # Peak 1 (High 120.0)
        (115, 120.02, 110, 114),  # Peak 2 (Nearly identical High)
        (114, 110, 105, 108),
        (108, 105, 98, 100),
        (100, 95, 90, 92),
    ]

    base_ts = 1700000000000
    candles = [create_candle(base_ts + i * 60000, p[0], p[1], p[2], p[3]) for i, p in enumerate(prices)]
    atr_values = np.full(len(candles), 5.0)

    cfg = StructureConfig(SWING_LEFT=3, SWING_RIGHT=3, EQUAL_TOLERANCE_ATR=0.1)
    confirmed1, _ = detect_swings(candles, atr_values, cfg)
    confirmed2, _ = detect_swings(candles, atr_values, cfg)

    # Output must be deterministic
    assert len(confirmed1) == len(confirmed2)
    for s1, s2 in zip(confirmed1, confirmed2):
        assert s1.id == s2.id
        assert s1.price == s2.price
