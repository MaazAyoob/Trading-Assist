from typing import List, Optional
from app.data.schema import Candle, CandleStateEnum, MarketDataQuality
from app.indicators.base import IndicatorSnapshot
from app.regime.models import MarketRegimeSnapshot
from app.structure.models import MarketStructureSnapshot
from app.signals.config import SignalConfig, default_signal_config
from app.signals.models import ResearchSignal
from app.signals.evidence import EvidenceExtractor
from app.signals.conflicts import ConflictDetector
from app.signals.scoring import SignalScorer


class MultiFactorSignalEngine:
    """
    Deterministic quantitative Multi-Factor Signal Research Engine.
    Consumes Indicators, Regime, Structure, and Quality state to produce auditable research setups.
    Guarantees:
    - Pure calculation: zero side-effects, no network, no database calls, no LLM.
    - Mathematical traceability via ScoreTrace.
    - Strictly non-predictive research classifications.
    """

    @classmethod
    def calculate_signal(
        cls,
        candles: List[Candle],
        indicators: IndicatorSnapshot,
        regime: MarketRegimeSnapshot,
        structure: MarketStructureSnapshot,
        quality: Optional[MarketDataQuality] = None,
        is_confirmed: bool = True,
        config: Optional[SignalConfig] = None,
    ) -> ResearchSignal:
        cfg = config or default_signal_config
        symbol = indicators.symbol
        timeframe = indicators.timeframe
        ts = indicators.timestamp

        # 1. Extract Directional Evidence Groups
        trend_group = EvidenceExtractor.extract_trend_evidence(indicators, candles, cfg)
        mom_group = EvidenceExtractor.extract_momentum_evidence(indicators, regime, cfg)
        struct_group = EvidenceExtractor.extract_structure_evidence(structure, cfg)
        vol_group = EvidenceExtractor.extract_volume_evidence(indicators, structure, cfg)

        evidence_groups = {
            "TREND": trend_group,
            "MOMENTUM": mom_group,
            "STRUCTURE": struct_group,
            "VOLUME": vol_group,
        }

        # 2. Detect Conflicts & S/R Constraints
        conflicts = ConflictDetector.detect_conflicts(
            candles=candles,
            indicators=indicators,
            regime=regime,
            structure=structure,
            trend_group=trend_group,
            momentum_group=mom_group,
            structure_group=struct_group,
            volume_group=vol_group,
            quality=quality,
            config=cfg,
        )

        # 3. Calculate Scores, Trace, and Setup Classification
        net_score, trace, direction, strength, status = SignalScorer.calculate_score_and_classification(
            trend_group=trend_group,
            momentum_group=mom_group,
            structure_group=struct_group,
            volume_group=vol_group,
            regime=regime,
            conflicts=conflicts,
            config=cfg,
        )

        # 4. Synthesize Supporting Evidence & Contradictions lists for UI
        supporting_evidence: List[str] = []
        contradictions: List[str] = []

        for group in evidence_groups.values():
            for comp in group.components:
                if (direction.value.startswith("LONG") and comp.direction == "BULLISH") or (
                    direction.value.startswith("SHORT") and comp.direction == "BEARISH"
                ):
                    supporting_evidence.append(f"[{group.group_name}] {comp.explanation}")
                elif (direction.value.startswith("LONG") and comp.direction == "BEARISH") or (
                    direction.value.startswith("SHORT") and comp.direction == "BULLISH"
                ):
                    contradictions.append(f"[{group.group_name}] {comp.explanation}")

        for c in conflicts:
            contradictions.append(f"[{c.category}] {c.explanation}")

        candle_state = CandleStateEnum.CLOSED if is_confirmed else CandleStateEnum.UPDATING
        data_quality_status = quality.status.value if quality else "HEALTHY"

        return ResearchSignal(
            symbol=symbol.upper(),
            timeframe=timeframe,
            timestamp=ts,
            candle_state=candle_state,
            is_confirmed=is_confirmed,
            is_historical=is_confirmed,
            direction=direction,
            strength=strength,
            status=status,
            score=net_score,
            evidence_groups=evidence_groups,
            score_trace=trace,
            conflicts=conflicts,
            supporting_evidence=supporting_evidence,
            contradictions=contradictions,
            data_quality_status=data_quality_status,
            engine_version=cfg.engine_version,
            config_version=cfg.config_version,
        )
