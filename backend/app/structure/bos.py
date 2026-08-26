from typing import List, Optional, Set
import numpy as np
from app.data.schema import Candle, CandleStateEnum
from app.structure.config import StructureConfig, default_structure_config
from app.structure.models import (
    SwingPoint,
    SwingTypeEnum,
    StructureEvent,
    StructureEventTypeEnum,
    BreakQualityEnum,
)


def detect_bos(
    candles: List[Candle],
    confirmed_swings: List[SwingPoint],
    atr_values: np.ndarray,
    volumes: np.ndarray,
    vol_sma: np.ndarray,
    config: Optional[StructureConfig] = None,
) -> List[StructureEvent]:
    """
    Deterministic Break of Structure (BOS) detector.
    Requirements:
    - Confirmed candle CLOSE required (wicks alone never trigger confirmed BOS).
    - Event recorded at the candle close where the break was confirmed.
    - Prevents duplicate BOS events for the same broken swing level.
    """
    cfg = config or default_structure_config
    bos_events: List[StructureEvent] = []

    if not candles or not confirmed_swings:
        return bos_events

    broken_swing_ids: Set[str] = set()

    for i, candle in enumerate(candles):
        # Only evaluate closed candles
        if not candle.is_closed and candle.state != CandleStateEnum.CLOSED:
            continue

        c_time = candle.timestamp
        close = candle.close
        open_p = candle.open
        high = candle.high
        low = candle.low
        vol = candle.volume

        atr = atr_values[i] if i < len(atr_values) and not np.isnan(atr_values[i]) else 1.0
        vsma = vol_sma[i] if i < len(vol_sma) and not np.isnan(vol_sma[i]) and vol_sma[i] > 0 else (vol or 1.0)
        vol_ratio = vol / vsma if vsma > 0 else 1.0

        candle_range = high - low if high > low else 1.0
        body_ratio = abs(close - open_p) / candle_range

        # Find confirmed swings that existed before this candle's close time
        available_swings = [
            s for s in confirmed_swings if s.confirmation_timestamp <= c_time and s.id not in broken_swing_ids
        ]

        # 1. Check Bullish BOS (Close > active Swing High)
        recent_swing_highs = [s for s in available_swings if s.type == SwingTypeEnum.SWING_HIGH]
        if recent_swing_highs:
            latest_sh = recent_swing_highs[-1]
            if close > latest_sh.price:
                # Confirmed Close above swing high
                break_dist = close - latest_sh.price
                atr_dist = break_dist / atr if atr > 0 else 0.0

                if atr_dist >= cfg.BREAK_STRONG_ATR_DISTANCE and vol_ratio >= cfg.BREAK_STRONG_VOLUME_RATIO and body_ratio >= cfg.BREAK_STRONG_BODY_RATIO:
                    quality = BreakQualityEnum.STRONG_BREAK
                elif atr_dist <= 0.10 or body_ratio <= 0.30:
                    quality = BreakQualityEnum.WEAK_BREAK
                else:
                    quality = BreakQualityEnum.NORMAL_BREAK

                bos_events.append(
                    StructureEvent(
                        event_id=f"BOS_BULL_{latest_sh.id}_{c_time}",
                        event_type=StructureEventTypeEnum.BULLISH_BOS,
                        broken_swing_id=latest_sh.id,
                        broken_level=latest_sh.price,
                        break_timestamp=c_time,
                        confirmation_timestamp=candle.close_time or (c_time + 900000),
                        close_price=close,
                        break_distance=float(break_dist),
                        atr_normalized_distance=float(atr_dist),
                        volume_ratio=float(vol_ratio),
                        candle_body_ratio=float(body_ratio),
                        break_quality=quality,
                        is_confirmed=True,
                    )
                )
                broken_swing_ids.add(latest_sh.id)

        # 2. Check Bearish BOS (Close < active Swing Low)
        recent_swing_lows = [s for s in available_swings if s.type == SwingTypeEnum.SWING_LOW]
        if recent_swing_lows:
            latest_sl = recent_swing_lows[-1]
            if close < latest_sl.price:
                # Confirmed Close below swing low
                break_dist = latest_sl.price - close
                atr_dist = break_dist / atr if atr > 0 else 0.0

                if atr_dist >= cfg.BREAK_STRONG_ATR_DISTANCE and vol_ratio >= cfg.BREAK_STRONG_VOLUME_RATIO and body_ratio >= cfg.BREAK_STRONG_BODY_RATIO:
                    quality = BreakQualityEnum.STRONG_BREAK
                elif atr_dist <= 0.10 or body_ratio <= 0.30:
                    quality = BreakQualityEnum.WEAK_BREAK
                else:
                    quality = BreakQualityEnum.NORMAL_BREAK

                bos_events.append(
                    StructureEvent(
                        event_id=f"BOS_BEAR_{latest_sl.id}_{c_time}",
                        event_type=StructureEventTypeEnum.BEARISH_BOS,
                        broken_swing_id=latest_sl.id,
                        broken_level=latest_sl.price,
                        break_timestamp=c_time,
                        confirmation_timestamp=candle.close_time or (c_time + 900000),
                        close_price=close,
                        break_distance=float(break_dist),
                        atr_normalized_distance=float(atr_dist),
                        volume_ratio=float(vol_ratio),
                        candle_body_ratio=float(body_ratio),
                        break_quality=quality,
                        is_confirmed=True,
                    )
                )
                broken_swing_ids.add(latest_sl.id)

    return bos_events
