from typing import List, Optional
import numpy as np
from app.data.schema import Candle, CandleStateEnum
from app.indicators.base import IndicatorSnapshot
from app.indicators.volatility import compute_atr
from app.indicators.volume import compute_volume_sma
from app.structure.config import StructureConfig, default_structure_config
from app.structure.models import (
    SwingPoint,
    SwingTypeEnum,
    StructureEvent,
    SupportResistanceZone,
    MarketStructureSnapshot,
)
from app.structure.swings import detect_swings
from app.structure.bos import detect_bos
from app.structure.choch import detect_choch
from app.structure.levels import cluster_support_resistance_zones


class MarketStructureEngine:
    """
    Deterministic quantitative price action structure engine.
    Computes confirmed/developing pivot swings, BOS events, CHoCH transitions,
    and ATR-clustered Support & Resistance zones.
    """

    @classmethod
    def evaluate(
        cls,
        candles: List[Candle],
        indicators: Optional[IndicatorSnapshot] = None,
        is_confirmed: bool = True,
        config: Optional[StructureConfig] = None,
    ) -> MarketStructureSnapshot:
        cfg = config or default_structure_config
        n = len(candles)

        if not candles:
            return MarketStructureSnapshot(
                symbol="BTCUSDT",
                timeframe="15m",
                timestamp=0,
                is_confirmed=is_confirmed,
                structure_direction="UNKNOWN",
                structure_engine_version=cfg.structure_engine_version,
                structure_config_version=cfg.structure_config_version,
            )

        symbol = candles[0].symbol if hasattr(candles[0], "symbol") and candles[0].symbol else (indicators.symbol if indicators else "BTCUSDT")
        timeframe = indicators.timeframe if indicators else "15m"
        latest_ts = candles[-1].timestamp

        # Extract NumPy arrays
        highs = np.array([c.high for c in candles], dtype=np.float64)
        lows = np.array([c.low for c in candles], dtype=np.float64)
        closes = np.array([c.close for c in candles], dtype=np.float64)
        volumes = np.array([c.volume for c in candles], dtype=np.float64)

        atr_arr = compute_atr(highs, lows, closes, period=14)
        vol_sma_arr = compute_volume_sma(volumes, period=20)
        latest_atr = float(atr_arr[-1]) if len(atr_arr) > 0 and not np.isnan(atr_arr[-1]) else 100.0

        # 1. Detect Swings (Confirmed vs Developing)
        confirmed_swings, developing_swings = detect_swings(candles, atr_arr, cfg)

        # 2. Detect BOS & CHoCH
        bos_events = detect_bos(candles, confirmed_swings, atr_arr, volumes, vol_sma_arr, cfg)
        choch_events = detect_choch(candles, confirmed_swings, atr_arr, volumes, vol_sma_arr, cfg)

        # 3. Cluster Support & Resistance Zones
        support_zones, resistance_zones = cluster_support_resistance_zones(
            candles, confirmed_swings, latest_atr, cfg
        )

        # 4. Determine Structural Direction (BULLISH, BEARISH, RANGE, TRANSITION, UNKNOWN)
        shs = [s for s in confirmed_swings if s.type == SwingTypeEnum.SWING_HIGH]
        sls = [s for s in confirmed_swings if s.type == SwingTypeEnum.SWING_LOW]

        active_sh = shs[-1] if shs else None
        active_sl = sls[-1] if sls else None

        if len(shs) >= 2 and len(sls) >= 2:
            prev_sh, curr_sh = shs[-2], shs[-1]
            prev_sl, curr_sl = sls[-2], sls[-1]

            if curr_sh.price > prev_sh.price and curr_sl.price > prev_sl.price:
                direction = "BULLISH"
            elif curr_sh.price < prev_sh.price and curr_sl.price < prev_sl.price:
                direction = "BEARISH"
            elif choch_events and choch_events[-1].break_timestamp >= max(curr_sh.swing_timestamp, curr_sl.swing_timestamp):
                direction = "TRANSITION"
            else:
                direction = "RANGE"
        else:
            direction = "UNKNOWN"

        return MarketStructureSnapshot(
            symbol=symbol.upper(),
            timeframe=timeframe,
            timestamp=latest_ts,
            is_confirmed=is_confirmed,
            structure_direction=direction,
            active_structural_high=active_sh,
            active_structural_low=active_sl,
            confirmed_swings=confirmed_swings,
            developing_swings=developing_swings,
            bos_events=bos_events,
            choch_events=choch_events,
            support_zones=support_zones,
            resistance_zones=resistance_zones,
            structure_engine_version=cfg.structure_engine_version,
            structure_config_version=cfg.structure_config_version,
        )
