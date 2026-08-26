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


def detect_choch(
    candles: List[Candle],
    confirmed_swings: List[SwingPoint],
    atr_values: np.ndarray,
    volumes: np.ndarray,
    vol_sma: np.ndarray,
    config: Optional[StructureConfig] = None,
) -> List[StructureEvent]:
    """
    Deterministic Change of Character (CHoCH) structural transition detector.
    - Bullish CHoCH: In an established bearish structure (sequence of LH/LL), a confirmed close
      above the most recent confirmed Lower High (LH) marks a structural shift toward bullish.
    - Bearish CHoCH: In an established bullish structure (sequence of HH/HL), a confirmed close
      below the most recent confirmed Higher Low (HL) marks a structural shift toward bearish.
    """
    cfg = config or default_structure_config
    choch_events: List[StructureEvent] = []

    if len(confirmed_swings) < 4:
        return choch_events

    broken_choch_swing_ids: Set[str] = set()

    for i, candle in enumerate(candles):
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

        available_swings = [s for s in confirmed_swings if s.confirmation_timestamp <= c_time]
        if len(available_swings) < 4:
            continue

        # Separate highs and lows
        shs = [s for s in available_swings if s.type == SwingTypeEnum.SWING_HIGH]
        sls = [s for s in available_swings if s.type == SwingTypeEnum.SWING_LOW]

        if len(shs) < 2 or len(sls) < 2:
            continue

        prev_sh, latest_sh = shs[-2], shs[-1]
        prev_sl, latest_sl = sls[-2], sls[-1]

        # 1. Check Bullish CHoCH (Prev structure was Bearish: latest_sh < prev_sh and latest_sl < prev_sl)
        # Price closes above latest Lower High
        if latest_sh.price < prev_sh.price and latest_sl.price < prev_sl.price:
            if close > latest_sh.price and latest_sh.id not in broken_choch_swing_ids:
                break_dist = close - latest_sh.price
                atr_dist = break_dist / atr if atr > 0 else 0.0

                if atr_dist >= cfg.BREAK_STRONG_ATR_DISTANCE and vol_ratio >= cfg.BREAK_STRONG_VOLUME_RATIO and body_ratio >= cfg.BREAK_STRONG_BODY_RATIO:
                    quality = BreakQualityEnum.STRONG_BREAK
                elif atr_dist <= 0.10 or body_ratio <= 0.30:
                    quality = BreakQualityEnum.WEAK_BREAK
                else:
                    quality = BreakQualityEnum.NORMAL_BREAK

                choch_events.append(
                    StructureEvent(
                        event_id=f"CHOCH_BULL_{latest_sh.id}_{c_time}",
                        event_type=StructureEventTypeEnum.BULLISH_CHOCH,
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
                broken_choch_swing_ids.add(latest_sh.id)

        # 2. Check Bearish CHoCH (Prev structure was Bullish: latest_sh > prev_sh and latest_sl > prev_sl)
        # Price closes below latest Higher Low
        if latest_sh.price > prev_sh.price and latest_sl.price > prev_sl.price:
            if close < latest_sl.price and latest_sl.id not in broken_choch_swing_ids:
                break_dist = latest_sl.price - close
                atr_dist = break_dist / atr if atr > 0 else 0.0

                if atr_dist >= cfg.BREAK_STRONG_ATR_DISTANCE and vol_ratio >= cfg.BREAK_STRONG_VOLUME_RATIO and body_ratio >= cfg.BREAK_STRONG_BODY_RATIO:
                    quality = BreakQualityEnum.STRONG_BREAK
                elif atr_dist <= 0.10 or body_ratio <= 0.30:
                    quality = BreakQualityEnum.WEAK_BREAK
                else:
                    quality = BreakQualityEnum.NORMAL_BREAK

                choch_events.append(
                    StructureEvent(
                        event_id=f"CHOCH_BEAR_{latest_sl.id}_{c_time}",
                        event_type=StructureEventTypeEnum.BEARISH_CHOCH,
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
                broken_choch_swing_ids.add(latest_sl.id)

    return choch_events
