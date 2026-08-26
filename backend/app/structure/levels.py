from typing import List, Tuple, Optional
import numpy as np
from app.data.schema import Candle, CandleStateEnum
from app.structure.config import StructureConfig, default_structure_config
from app.structure.models import (
    SwingPoint,
    SwingTypeEnum,
    SupportResistanceZone,
    ZoneTypeEnum,
    ZoneStatusEnum,
    ZoneStrengthEnum,
)


def cluster_support_resistance_zones(
    candles: List[Candle],
    confirmed_swings: List[SwingPoint],
    latest_atr: float,
    config: Optional[StructureConfig] = None,
) -> Tuple[List[SupportResistanceZone], List[SupportResistanceZone]]:
    """
    Deterministic ATR-relative Support and Resistance Clustering Engine.
    Clusters confirmed swing highs into Resistance zones and swing lows into Support zones.
    Calculates touch counts, lifecycle status, and strength rating.
    """
    cfg = config or default_structure_config
    support_zones: List[SupportResistanceZone] = []
    resistance_zones: List[SupportResistanceZone] = []

    if not confirmed_swings:
        return support_zones, resistance_zones

    atr_thresh = max(1.0, latest_atr * cfg.SR_CLUSTER_ATR_MULTIPLIER)
    latest_close = candles[-1].close if candles else 0.0

    # 1. Cluster Swing Highs -> Resistance Zones
    swing_highs = sorted([s for s in confirmed_swings if s.type == SwingTypeEnum.SWING_HIGH], key=lambda s: s.price)
    res_clusters: List[List[SwingPoint]] = []

    for sh in swing_highs:
        if not res_clusters:
            res_clusters.append([sh])
        else:
            last_cluster = res_clusters[-1]
            cluster_avg = sum(s.price for s in last_cluster) / len(last_cluster)
            if abs(sh.price - cluster_avg) <= atr_thresh:
                last_cluster.append(sh)
            else:
                res_clusters.append([sh])

    for i, cluster in enumerate(res_clusters):
        prices = [s.price for s in cluster]
        low_p = min(prices)
        high_p = max(prices)
        center_p = sum(prices) / len(prices)
        touch_count = len(cluster)
        created_ts = min(s.swing_timestamp for s in cluster)
        last_touch_ts = max(s.swing_timestamp for s in cluster)

        # Lifecycle Status
        if latest_close > (high_p + latest_atr * 0.5):
            status = ZoneStatusEnum.BROKEN
        elif touch_count >= 2:
            status = ZoneStatusEnum.TESTED
        else:
            status = ZoneStatusEnum.ACTIVE

        # Strength
        if touch_count >= cfg.SR_MIN_TOUCHES_STRONG:
            strength = ZoneStrengthEnum.STRONG
        elif touch_count >= cfg.SR_MIN_TOUCHES_MODERATE:
            strength = ZoneStrengthEnum.MODERATE
        else:
            strength = ZoneStrengthEnum.WEAK

        resistance_zones.append(
            SupportResistanceZone(
                zone_id=f"RES_{int(center_p)}_{created_ts}",
                zone_type=ZoneTypeEnum.RESISTANCE,
                price_low=float(low_p),
                price_high=float(high_p),
                price_center=float(center_p),
                touch_count=touch_count,
                strength=strength,
                status=status,
                created_timestamp=int(created_ts),
                last_touch_timestamp=int(last_touch_ts),
            )
        )

    # 2. Cluster Swing Lows -> Support Zones
    swing_lows = sorted([s for s in confirmed_swings if s.type == SwingTypeEnum.SWING_LOW], key=lambda s: s.price)
    sup_clusters: List[List[SwingPoint]] = []

    for sl in swing_lows:
        if not sup_clusters:
            sup_clusters.append([sl])
        else:
            last_cluster = sup_clusters[-1]
            cluster_avg = sum(s.price for s in last_cluster) / len(last_cluster)
            if abs(sl.price - cluster_avg) <= atr_thresh:
                last_cluster.append(sl)
            else:
                sup_clusters.append([sl])

    for i, cluster in enumerate(sup_clusters):
        prices = [s.price for s in cluster]
        low_p = min(prices)
        high_p = max(prices)
        center_p = sum(prices) / len(prices)
        touch_count = len(cluster)
        created_ts = min(s.swing_timestamp for s in cluster)
        last_touch_ts = max(s.swing_timestamp for s in cluster)

        # Lifecycle Status
        if latest_close < (low_p - latest_atr * 0.5):
            status = ZoneStatusEnum.BROKEN
        elif touch_count >= 2:
            status = ZoneStatusEnum.TESTED
        else:
            status = ZoneStatusEnum.ACTIVE

        # Strength
        if touch_count >= cfg.SR_MIN_TOUCHES_STRONG:
            strength = ZoneStrengthEnum.STRONG
        elif touch_count >= cfg.SR_MIN_TOUCHES_MODERATE:
            strength = ZoneStrengthEnum.MODERATE
        else:
            strength = ZoneStrengthEnum.WEAK

        support_zones.append(
            SupportResistanceZone(
                zone_id=f"SUP_{int(center_p)}_{created_ts}",
                zone_type=ZoneTypeEnum.SUPPORT,
                price_low=float(low_p),
                price_high=float(high_p),
                price_center=float(center_p),
                touch_count=touch_count,
                strength=strength,
                status=status,
                created_timestamp=int(created_ts),
                last_touch_timestamp=int(last_touch_ts),
            )
        )

    return support_zones, resistance_zones
