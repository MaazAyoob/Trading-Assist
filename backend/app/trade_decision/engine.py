"""
Phase 10 — Trade Decision Engine Orchestrator.
Coordinates evaluation of rule-based trade decisions, multi-candidate comparisons,
and non-repainting historical trade decision series.
"""

from typing import List, Optional, Dict
from app.data.schema import Candle, MarketDataQuality
from app.indicators.base import IndicatorSnapshot
from app.regime.models import MarketRegimeSnapshot
from app.structure.models import MarketStructureSnapshot
from app.signals.models import ResearchSignal
from app.trade_decision.config import TradeDecisionConfig, DEFAULT_TRADE_DECISION_CONFIG
from app.trade_decision.models import TradePlan, MultiStrategyTradeDecisions
from app.trade_decision.decision import DecisionEvaluator


class TradeDecisionEngine:
    """
    Main trade decision engine.
    Calculates deterministic trade plans from multi-factor snapshots.
    """

    @classmethod
    def calculate_decision(
        cls,
        candles: List[Candle],
        indicators: IndicatorSnapshot,
        regime: MarketRegimeSnapshot,
        structure: MarketStructureSnapshot,
        signal: ResearchSignal,
        quality: Optional[MarketDataQuality] = None,
        strategy_context_id: str = "PHASE5_BASELINE",
        is_confirmed: bool = True,
        config: TradeDecisionConfig = DEFAULT_TRADE_DECISION_CONFIG,
    ) -> TradePlan:
        """
        Calculates deterministic analytical TradePlan.
        """
        return DecisionEvaluator.evaluate(
            candles=candles,
            indicators=indicators,
            regime=regime,
            structure=structure,
            signal=signal,
            quality=quality,
            strategy_context_id=strategy_context_id,
            is_confirmed=is_confirmed,
            config=config,
        )

    @classmethod
    def calculate_multi_strategy_decisions(
        cls,
        candles: List[Candle],
        indicators: IndicatorSnapshot,
        regime: MarketRegimeSnapshot,
        structure: MarketStructureSnapshot,
        signal: ResearchSignal,
        quality: Optional[MarketDataQuality] = None,
        primary_strategy_id: str = "EXP_A2_PULLBACK_VWAP",
        is_confirmed: bool = True,
        config: TradeDecisionConfig = DEFAULT_TRADE_DECISION_CONFIG,
    ) -> MultiStrategyTradeDecisions:
        """
        Calculates separate, auditable trade plans for Baseline, A2, and E2 candidate contexts.
        Never combines candidate strategies silently.
        """
        strategies = ["PHASE5_BASELINE", "EXP_A2_PULLBACK_VWAP", "EXP_E2_EXTENSION_VWAP"]
        candidate_decisions: Dict[str, TradePlan] = {}

        for strat_id in strategies:
            candidate_decisions[strat_id] = cls.calculate_decision(
                candles=candles,
                indicators=indicators,
                regime=regime,
                structure=structure,
                signal=signal,
                quality=quality,
                strategy_context_id=strat_id,
                is_confirmed=is_confirmed,
                config=config,
            )

        primary_plan = candidate_decisions.get(primary_strategy_id, candidate_decisions["PHASE5_BASELINE"])

        return MultiStrategyTradeDecisions(
            symbol=signal.symbol if signal else "BTCUSDT",
            timeframe=signal.timeframe if signal else "15m",
            timestamp=candles[-1].close_time if candles else 0,
            selected_strategy_id=primary_strategy_id,
            primary_decision=primary_plan,
            candidate_decisions=candidate_decisions,
        )
