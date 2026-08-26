from typing import List, Optional
from app.data.schema import Candle, MarketDataQuality, QualityStatusEnum
from app.indicators.base import IndicatorSnapshot
from app.regime.models import MarketRegimeSnapshot, VolatilityStateEnum
from app.structure.models import MarketStructureSnapshot, BreakQualityEnum, ZoneStatusEnum, ZoneStrengthEnum
from app.signals.config import SignalConfig, default_signal_config
from app.signals.models import ConflictItem, ConflictSeverityEnum, EvidenceGroupScore


class ConflictDetector:
    """
    Identifies deterministic contradictions, anomalies, and structural proximity constraints.
    Returns explicit ConflictItems with category, severity, and auditable penalty values.
    """

    @classmethod
    def detect_conflicts(
        cls,
        candles: List[Candle],
        indicators: IndicatorSnapshot,
        regime: MarketRegimeSnapshot,
        structure: MarketStructureSnapshot,
        trend_group: EvidenceGroupScore,
        momentum_group: EvidenceGroupScore,
        structure_group: EvidenceGroupScore,
        volume_group: EvidenceGroupScore,
        quality: Optional[MarketDataQuality] = None,
        config: Optional[SignalConfig] = None,
    ) -> List[ConflictItem]:
        cfg = config or default_signal_config
        conflicts: List[ConflictItem] = []

        # 1. Critical Data Quality Invalidation
        if quality and quality.status in [QualityStatusEnum.INVALID, QualityStatusEnum.INSUFFICIENT_DATA]:
            conflicts.append(
                ConflictItem(
                    conflict_id="DATA_QUALITY_CRITICAL",
                    category="DATA_QUALITY",
                    severity=ConflictSeverityEnum.CRITICAL,
                    raw_penalty=100.0,
                    applied_penalty=100.0,
                    explanation=f"Market data quality is {quality.status.value}; cannot form valid directional setup",
                    affected_groups=["ALL"],
                )
            )
            return conflicts

        # 2. Opposing Trend vs Structure
        if trend_group.score >= 30.0 and structure_group.score <= -30.0:
            conflicts.append(
                ConflictItem(
                    conflict_id="TREND_STRUCTURE_OPPOSITION_BEAR_STRUCT",
                    category="STRUCTURAL_CONTRADICTION",
                    severity=ConflictSeverityEnum.HIGH,
                    raw_penalty=cfg.PENALTY_HIGH,
                    applied_penalty=cfg.PENALTY_HIGH,
                    explanation="Bullish trend indicators conflict directly with confirmed bearish price structure",
                    affected_groups=["TREND", "STRUCTURE"],
                )
            )
        elif trend_group.score <= -30.0 and structure_group.score >= 30.0:
            conflicts.append(
                ConflictItem(
                    conflict_id="TREND_STRUCTURE_OPPOSITION_BULL_STRUCT",
                    category="STRUCTURAL_CONTRADICTION",
                    severity=ConflictSeverityEnum.HIGH,
                    raw_penalty=cfg.PENALTY_HIGH,
                    applied_penalty=cfg.PENALTY_HIGH,
                    explanation="Bearish trend indicators conflict directly with confirmed bullish price structure",
                    affected_groups=["TREND", "STRUCTURE"],
                )
            )

        # 3. Low Volume on Structural Break
        if structure.bos_events:
            latest_bos = structure.bos_events[-1]
            if latest_bos.volume_ratio < 0.8:
                conflicts.append(
                    ConflictItem(
                        conflict_id="BOS_VOLUME_ANOMALY",
                        category="VOLUME_ANOMALY",
                        severity=ConflictSeverityEnum.MEDIUM,
                        raw_penalty=cfg.PENALTY_MEDIUM,
                        applied_penalty=cfg.PENALTY_MEDIUM,
                        explanation=f"Structural break ({latest_bos.event_type.value}) occurred with sub-par volume ({latest_bos.volume_ratio:.2f}x)",
                        affected_groups=["STRUCTURE", "VOLUME"],
                    )
                )

        # 4. Support / Resistance Proximity Constraints
        last_close = candles[-1].close if candles else 0.0
        atr_val = indicators.volatility.atr or 100.0
        prox_thresh = atr_val * cfg.SR_PROXIMITY_ATR_MULTIPLIER

        # Bullish setup near Resistance
        if trend_group.score > 0 and structure.resistance_zones:
            for rz in structure.resistance_zones:
                if rz.status in [ZoneStatusEnum.ACTIVE, ZoneStatusEnum.TESTED] and rz.strength in [ZoneStrengthEnum.STRONG, ZoneStrengthEnum.MODERATE]:
                    dist = rz.price_low - last_close
                    if 0 <= dist <= prox_thresh:
                        conflicts.append(
                            ConflictItem(
                                conflict_id="SR_RESISTANCE_PROXIMITY",
                                category="STRUCTURAL_PROXIMITY",
                                severity=ConflictSeverityEnum.HIGH,
                                raw_penalty=cfg.PENALTY_HIGH,
                                applied_penalty=cfg.PENALTY_HIGH,
                                explanation=f"Price (${last_close:.2f}) is within {cfg.SR_PROXIMITY_ATR_MULTIPLIER:.2f} ATR of a strong Resistance zone (${rz.price_low:.0f}-${rz.price_high:.0f})",
                                affected_groups=["STRUCTURE", "TREND"],
                            )
                        )
                        break

        # Bearish setup near Support
        if trend_group.score < 0 and structure.support_zones:
            for sz in structure.support_zones:
                if sz.status in [ZoneStatusEnum.ACTIVE, ZoneStatusEnum.TESTED] and sz.strength in [ZoneStrengthEnum.STRONG, ZoneStrengthEnum.MODERATE]:
                    dist = last_close - sz.price_high
                    if 0 <= dist <= prox_thresh:
                        conflicts.append(
                            ConflictItem(
                                conflict_id="SR_SUPPORT_PROXIMITY",
                                category="STRUCTURAL_PROXIMITY",
                                severity=ConflictSeverityEnum.HIGH,
                                raw_penalty=cfg.PENALTY_HIGH,
                                applied_penalty=cfg.PENALTY_HIGH,
                                explanation=f"Price (${last_close:.2f}) is within {cfg.SR_PROXIMITY_ATR_MULTIPLIER:.2f} ATR of a strong Support zone (${sz.price_low:.0f}-${sz.price_high:.0f})",
                                affected_groups=["STRUCTURE", "TREND"],
                            )
                        )
                        break

        # 5. Extreme Volatility Warning
        if regime.volatility_state == VolatilityStateEnum.EXTREME:
            conflicts.append(
                ConflictItem(
                    conflict_id="EXTREME_VOLATILITY_WARNING",
                    category="VOLATILITY_ANOMALY",
                    severity=ConflictSeverityEnum.MEDIUM,
                    raw_penalty=cfg.PENALTY_MEDIUM,
                    applied_penalty=cfg.PENALTY_MEDIUM,
                    explanation="Extreme market volatility detected (ATR% > 88th percentile)",
                    affected_groups=["VOLATILITY"],
                )
            )

        return conflicts
