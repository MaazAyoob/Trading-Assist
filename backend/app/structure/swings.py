import numpy as np
from typing import List, Tuple, Optional
from app.data.schema import Candle
from app.structure.config import StructureConfig, default_structure_config
from app.structure.models import SwingPoint, SwingTypeEnum


def detect_swings(
    candles: List[Candle],
    atr_values: np.ndarray,
    config: Optional[StructureConfig] = None,
) -> Tuple[List[SwingPoint], List[SwingPoint]]:
    """
    Deterministic pivot swing detection with causally verified confirmation lifecycle.
    - Confirmed Swings: Have full SWING_RIGHT confirmed right-side bars.
      Event timestamp = candles[i+RIGHT].timestamp, Swing timestamp = candles[i].timestamp.
    - Developing Swings: Candidate pivots in the latest SWING_RIGHT bars that are still forming.
    """
    cfg = config or default_structure_config
    n = len(candles)
    left = cfg.SWING_LEFT
    right = cfg.SWING_RIGHT

    confirmed_swings: List[SwingPoint] = []
    developing_swings: List[SwingPoint] = []

    if n < (left + 1):
        return confirmed_swings, developing_swings

    highs = np.array([c.high for c in candles], dtype=np.float64)
    lows = np.array([c.low for c in candles], dtype=np.float64)
    timestamps = np.array([c.timestamp for c in candles], dtype=np.int64)
    volumes = np.array([c.volume for c in candles], dtype=np.float64)

    # 1. Detect Confirmed Swings (Requires full left and right confirmation window)
    if n >= (left + right + 1):
        for i in range(left, n - right):
            current_high = highs[i]
            current_low = lows[i]
            current_atr = atr_values[i] if i < len(atr_values) and not np.isnan(atr_values[i]) else 1.0
            tol = cfg.EQUAL_TOLERANCE_ATR * current_atr

            # Check Swing High
            is_swing_high = True
            for k in range(1, left + 1):
                if highs[i - k] > current_high:
                    is_swing_high = False
                    break
            if is_swing_high:
                for k in range(1, right + 1):
                    if highs[i + k] > (current_high + tol):
                        is_swing_high = False
                        break

            if is_swing_high:
                confirmed_swings.append(
                    SwingPoint(
                        id=f"SH_{timestamps[i]}",
                        type=SwingTypeEnum.SWING_HIGH,
                        price=float(current_high),
                        swing_timestamp=int(timestamps[i]),
                        confirmation_timestamp=int(timestamps[i + right]),
                        is_confirmed=True,
                        volume=float(volumes[i]),
                        atr_normalized_magnitude=float(current_high / current_atr) if current_atr > 0 else None,
                    )
                )

            # Check Swing Low
            is_swing_low = True
            for k in range(1, left + 1):
                if lows[i - k] < current_low:
                    is_swing_low = False
                    break
            if is_swing_low:
                for k in range(1, right + 1):
                    if lows[i + k] < (current_low - tol):
                        is_swing_low = False
                        break

            if is_swing_low:
                confirmed_swings.append(
                    SwingPoint(
                        id=f"SL_{timestamps[i]}",
                        type=SwingTypeEnum.SWING_LOW,
                        price=float(current_low),
                        swing_timestamp=int(timestamps[i]),
                        confirmation_timestamp=int(timestamps[i + right]),
                        is_confirmed=True,
                        volume=float(volumes[i]),
                        atr_normalized_magnitude=float(current_low / current_atr) if current_atr > 0 else None,
                    )
                )

    # 2. Detect Developing Swings (in the latest right window)
    start_dev = max(left, n - right) if n >= (left + right + 1) else left
    for i in range(start_dev, n):
        current_high = highs[i]
        current_low = lows[i]
        available_right = n - 1 - i

        # Check developing high
        is_dev_high = True
        for k in range(1, left + 1):
            if highs[i - k] > current_high:
                is_dev_high = False
                break
        if is_dev_high and available_right > 0:
            for k in range(1, available_right + 1):
                if highs[i + k] > current_high:
                    is_dev_high = False
                    break

        if is_dev_high:
            developing_swings.append(
                SwingPoint(
                    id=f"DEV_SH_{timestamps[i]}",
                    type=SwingTypeEnum.SWING_HIGH,
                    price=float(current_high),
                    swing_timestamp=int(timestamps[i]),
                    confirmation_timestamp=int(timestamps[-1]),
                    is_confirmed=False,
                    volume=float(volumes[i]),
                )
            )

        # Check developing low
        is_dev_low = True
        for k in range(1, left + 1):
            if lows[i - k] < current_low:
                is_dev_low = False
                break
        if is_dev_low and available_right > 0:
            for k in range(1, available_right + 1):
                if lows[i + k] < current_low:
                    is_dev_low = False
                    break

        if is_dev_low:
            developing_swings.append(
                SwingPoint(
                    id=f"DEV_SL_{timestamps[i]}",
                    type=SwingTypeEnum.SWING_LOW,
                    price=float(current_low),
                    swing_timestamp=int(timestamps[i]),
                    confirmation_timestamp=int(timestamps[-1]),
                    is_confirmed=False,
                    volume=float(volumes[i]),
                )
            )

    # Sort confirmed swings chronologically by confirmation_timestamp
    confirmed_swings.sort(key=lambda s: s.confirmation_timestamp)

    return confirmed_swings, developing_swings
