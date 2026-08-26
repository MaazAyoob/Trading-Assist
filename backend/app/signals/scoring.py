from typing import List, Tuple, Dict, Optional
import numpy as np
from app.regime.models import MarketRegimeSnapshot, DirectionEnum, OverallRegimeEnum, VolatilityStateEnum
from app.signals.config import SignalConfig, default_signal_config
from app.signals.models import (
    SignalDirectionEnum,
    SignalStrengthEnum,
    SignalStatusEnum,
    ConflictItem,
    ConflictSeverityEnum,
    EvidenceGroupScore,
    ScoreTrace,
)


class SignalScorer:
    """
    Computes deterministic multi-factor signal scores, context adjustments,
    conflict penalties, and setup classifications.
    """

    @classmethod
    def calculate_score_and_classification(
        cls,
        trend_group: EvidenceGroupScore,
        momentum_group: EvidenceGroupScore,
        structure_group: EvidenceGroupScore,
        volume_group: EvidenceGroupScore,
        regime: MarketRegimeSnapshot,
        conflicts: List[ConflictItem],
        config: Optional[SignalConfig] = None,
    ) -> Tuple[float, ScoreTrace, SignalDirectionEnum, SignalStrengthEnum, SignalStatusEnum]:
        cfg = config or default_signal_config

        # 1. Base Directional Score (-100.0 to +100.0)
        base_directional_score = (
            trend_group.score * cfg.WEIGHT_TREND
            + momentum_group.score * cfg.WEIGHT_MOMENTUM
            + structure_group.score * cfg.WEIGHT_STRUCTURE
            + volume_group.score * cfg.WEIGHT_VOLUME
        )

        # 2. Contextual Regime Modifier (0.0 to 1.0)
        regime_mod = cfg.REGIME_MOD_NEUTRAL
        if base_directional_score > 0:  # Bullish tendency
            if regime.overall_regime == OverallRegimeEnum.TRENDING_BULLISH:
                regime_mod = cfg.REGIME_MOD_COMPATIBLE
            elif regime.overall_regime in [OverallRegimeEnum.RANGING, OverallRegimeEnum.TRANSITION, OverallRegimeEnum.LOW_VOLATILITY]:
                regime_mod = cfg.REGIME_MOD_NEUTRAL
            elif regime.overall_regime == OverallRegimeEnum.TRENDING_BEARISH:
                regime_mod = cfg.REGIME_MOD_OPPOSING
            else:
                regime_mod = cfg.REGIME_MOD_UNCERTAIN
        elif base_directional_score < 0:  # Bearish tendency
            if regime.overall_regime == OverallRegimeEnum.TRENDING_BEARISH:
                regime_mod = cfg.REGIME_MOD_COMPATIBLE
            elif regime.overall_regime in [OverallRegimeEnum.RANGING, OverallRegimeEnum.TRANSITION, OverallRegimeEnum.LOW_VOLATILITY]:
                regime_mod = cfg.REGIME_MOD_NEUTRAL
            elif regime.overall_regime == OverallRegimeEnum.TRENDING_BULLISH:
                regime_mod = cfg.REGIME_MOD_OPPOSING
            else:
                regime_mod = cfg.REGIME_MOD_UNCERTAIN
        else:
            regime_mod = 1.0

        # 3. Contextual Volatility Quality Modifier (0.0 to 1.0)
        if regime.volatility_state == VolatilityStateEnum.EXTREME:
            vol_mod = cfg.VOL_MOD_EXTREME
        elif regime.volatility_state == VolatilityStateEnum.HIGH:
            vol_mod = cfg.VOL_MOD_HIGH
        elif regime.volatility_state == VolatilityStateEnum.VERY_LOW:
            vol_mod = cfg.VOL_MOD_VERY_LOW
        elif regime.volatility_state == VolatilityStateEnum.LOW:
            vol_mod = cfg.VOL_MOD_LOW
        else:
            vol_mod = cfg.VOL_MOD_NORMAL

        # 4. Context-Adjusted Score
        context_adjusted_score = base_directional_score * regime_mod * vol_mod

        # 5. Apply Conflict Penalties
        total_penalties = sum(c.applied_penalty for c in conflicts if c.severity != ConflictSeverityEnum.CRITICAL)

        if context_adjusted_score > 0:
            net_score = max(0.0, context_adjusted_score - total_penalties)
        elif context_adjusted_score < 0:
            net_score = min(0.0, context_adjusted_score + total_penalties)
        else:
            net_score = 0.0

        net_score = round(float(np.clip(net_score, -100.0, 100.0)), 1)

        trace = ScoreTrace(
            trend_score=round(trend_group.score, 1),
            momentum_score=round(momentum_group.score, 1),
            structure_score=round(structure_group.score, 1),
            volume_score=round(volume_group.score, 1),
            base_directional_score=round(base_directional_score, 1),
            regime_modifier=round(regime_mod, 2),
            volatility_modifier=round(vol_mod, 2),
            context_adjusted_score=round(context_adjusted_score, 1),
            total_conflict_penalty=round(total_penalties, 1),
            net_score=net_score,
        )

        # 6. Classification Logic
        has_critical = any(c.severity == ConflictSeverityEnum.CRITICAL for c in conflicts)
        has_high_conflict = any(c.severity == ConflictSeverityEnum.HIGH for c in conflicts)

        if has_critical:
            direction = SignalDirectionEnum.NEUTRAL
            strength = SignalStrengthEnum.VERY_WEAK
            status = SignalStatusEnum.INVALID_DATA
            return net_score, trace, direction, strength, status

        # Check Minimum Independent Agreement Gates
        is_long_eligible = (
            net_score >= cfg.SCORE_LONG_THRESHOLD
            and trend_group.score >= cfg.MIN_TREND_AGREEMENT
            and structure_group.score >= cfg.MIN_STRUCTURE_AGREEMENT
            and not has_high_conflict
        )

        is_short_eligible = (
            net_score <= cfg.SCORE_SHORT_THRESHOLD
            and trend_group.score <= -cfg.MIN_TREND_AGREEMENT
            and structure_group.score <= -cfg.MIN_STRUCTURE_AGREEMENT
            and not has_high_conflict
        )

        if is_long_eligible:
            direction = SignalDirectionEnum.LONG_SETUP
            status = SignalStatusEnum.VALID
        elif is_short_eligible:
            direction = SignalDirectionEnum.SHORT_SETUP
            status = SignalStatusEnum.VALID
        elif abs(base_directional_score) >= 35.0:
            direction = SignalDirectionEnum.NEUTRAL
            status = SignalStatusEnum.WAIT
        else:
            direction = SignalDirectionEnum.NEUTRAL
            status = SignalStatusEnum.VALID

        # Determine Signal Strength
        abs_score = abs(net_score)
        if direction != SignalDirectionEnum.NEUTRAL:
            if abs_score >= 75.0 and momentum_group.score * (1 if direction == SignalDirectionEnum.LONG_SETUP else -1) >= 20.0:
                strength = SignalStrengthEnum.VERY_STRONG
            elif abs_score >= 60.0:
                strength = SignalStrengthEnum.STRONG
            elif abs_score >= 45.0:
                strength = SignalStrengthEnum.MODERATE
            elif abs_score >= 30.0:
                strength = SignalStrengthEnum.WEAK
            else:
                strength = SignalStrengthEnum.VERY_WEAK
        else:
            strength = SignalStrengthEnum.VERY_WEAK

        return net_score, trace, direction, strength, status
