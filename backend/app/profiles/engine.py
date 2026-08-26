"""
Trading Profile Engine for Phase 12.
Orchestrates multi-timeframe context and feeds into authoritative TradeDecisionEngine.
"""

from typing import Dict, List, Optional
from app.data.schema import Candle
from app.profiles.models import (
    TradingProfileConfig,
    ProfileStateEnum,
    ProfileAnalysisResult,
    CostSensitivityTier,
)
from app.profiles.context import MultiTimeframeContextBuilder
from app.profiles.validation import ProfileValidator
from app.trade_decision.engine import TradeDecisionEngine
from app.trade_decision.models import TradeDecisionEnum


class TradingProfileEngine:
    @classmethod
    def evaluate_profile(
        cls,
        symbol: str,
        profile_config: TradingProfileConfig,
        primary_candles: List[Candle],
        context_candles_map: Optional[Dict[str, List[Candle]]] = None,
        is_confirmed: bool = True,
        strategy_context_id: str = "EXP_A2_PULLBACK_VWAP",
    ) -> ProfileAnalysisResult:
        context_map = context_candles_map or {}
        
        # 1. Check Data Sufficiency
        has_sufficient_data, data_msg = ProfileValidator.validate_data_sufficiency(
            primary_candles, profile_config.minimum_data_requirements
        )
        if not has_sufficient_data:
            return ProfileAnalysisResult(
                profile_id=profile_config.profile_id,
                symbol=symbol,
                primary_timeframe=profile_config.primary_timeframe,
                context_timeframes=profile_config.context_timeframes,
                profile_state=ProfileStateEnum.INSUFFICIENT_DATA,
                state_description=f"Insufficient data: {data_msg}",
                trade_plan=None,
                context_confirmed={tf: False for tf in profile_config.context_timeframes},
                alignment_score=0.0,
                score_tier="AWAITING",
                cost_sensitivity=[],
                analytical_timestamp=primary_candles[-1].timestamp if primary_candles else 0,
                is_preview=not is_confirmed,
                reasons=[data_msg],
            )

        # 2. Build Causally Synchronized Multi-Timeframe Context
        mtf_context = MultiTimeframeContextBuilder.build_context(
            symbol=symbol,
            profile_config=profile_config,
            primary_candles=primary_candles,
            context_candles_map=context_map,
            is_confirmed=is_confirmed,
        )

        prim_tf = profile_config.primary_timeframe
        prim_ind = mtf_context.context_indicators.get(prim_tf)
        prim_struct = mtf_context.context_structures.get(prim_tf)
        prim_regime = mtf_context.context_regimes.get(prim_tf)
        prim_sig = mtf_context.context_signals.get(prim_tf)
        prim_qual = mtf_context.context_qualities.get(prim_tf)

        if not (prim_ind and prim_struct and prim_regime and prim_sig):
            return ProfileAnalysisResult(
                profile_id=profile_config.profile_id,
                symbol=symbol,
                primary_timeframe=prim_tf,
                context_timeframes=profile_config.context_timeframes,
                profile_state=ProfileStateEnum.INSUFFICIENT_DATA,
                state_description="Primary analytical pipeline failed to produce complete snapshots",
                trade_plan=None,
                context_confirmed={},
                alignment_score=0.0,
                score_tier="AWAITING",
                cost_sensitivity=[],
                analytical_timestamp=mtf_context.analytical_timestamp,
                is_preview=not is_confirmed,
                reasons=["Incomplete primary indicator/regime/structure snapshot"],
            )

        # 3. Authoritative Phase 10 Trade Plan Evaluation on Primary Timeframe
        trade_plan = TradeDecisionEngine.calculate_decision(
            candles=primary_candles,
            indicators=prim_ind,
            regime=prim_regime,
            structure=prim_struct,
            signal=prim_sig,
            quality=prim_qual,
            strategy_context_id=strategy_context_id,
            is_confirmed=is_confirmed,
        )

        # 4. Multi-Timeframe Confirmation Logic
        context_confirmed: Dict[str, bool] = {}
        alignment_score = trade_plan.decision_alignment_score
        
        # Check context agreement
        reasons: List[str] = []
        is_context_aligned = True

        for ctx_tf in profile_config.context_timeframes:
            ctx_sig = mtf_context.context_signals.get(ctx_tf)
            ctx_regime = mtf_context.context_regimes.get(ctx_tf)
            
            if ctx_sig and ctx_regime:
                # Directional check: if trade plan is BUY, higher timeframe should not be strongly opposing
                if trade_plan.decision == TradeDecisionEnum.BUY:
                    aligned = ctx_sig.direction != "BEARISH"
                elif trade_plan.decision == TradeDecisionEnum.SELL:
                    aligned = ctx_sig.direction != "BULLISH"
                else:
                    aligned = True
                context_confirmed[ctx_tf] = aligned
                if not aligned:
                    is_context_aligned = False
                    reasons.append(f"Context conflict on {ctx_tf}: direction opposes setup")
            else:
                context_confirmed[ctx_tf] = False
                reasons.append(f"Missing confirmed context data for {ctx_tf}")

        # 5. Derive Profile State
        if trade_plan.decision in (TradeDecisionEnum.BUY, TradeDecisionEnum.SELL):
            if is_context_aligned and trade_plan.risk_reward and trade_plan.risk_reward.is_acceptable:
                profile_state = ProfileStateEnum.ENTRY_READY
                state_desc = f"{trade_plan.decision.value} opportunity confirmed across {prim_tf} and context timeframes."
            elif not is_context_aligned:
                profile_state = ProfileStateEnum.WATCH
                state_desc = f"{trade_plan.decision.value} setup detected on {prim_tf}, awaiting higher-timeframe confirmation."
            else:
                profile_state = ProfileStateEnum.SETUP
                state_desc = f"{trade_plan.decision.value} setup forming on {prim_tf}."
        else:
            profile_state = ProfileStateEnum.NO_TRADE
            state_desc = "No valid directional trade setup."
            reasons.extend(trade_plan.reasons_for_no_trade)

        # 6. Score Tier Mapping
        if alignment_score >= 80:
            score_tier = "VERY HIGH"
        elif alignment_score >= 65:
            score_tier = "HIGH"
        elif alignment_score >= 50:
            score_tier = "MODERATE"
        elif alignment_score >= 35:
            score_tier = "LOW"
        else:
            score_tier = "VERY LOW"

        # 7. Cost Sensitivity Evaluation
        # Expected movement base pct from TP1 target or ATR
        raw_movement_pct = 0.50  # Default 50 bps baseline
        if trade_plan.take_profits and trade_plan.entry:
            diff = abs(trade_plan.take_profits.tp1.adjusted_target - trade_plan.entry.planned_entry_price)
            if trade_plan.entry.planned_entry_price > 0:
                raw_movement_pct = (diff / trade_plan.entry.planned_entry_price) * 100.0

        cost_tiers = ProfileValidator.evaluate_cost_sensitivity(
            raw_analytical_return_pct=raw_movement_pct,
            cost_tiers_bps=profile_config.cost_sensitivity_bps,
        )

        cost_warning = None
        for ct in cost_tiers:
            if ct.warning_flag:
                cost_warning = ct.warning_flag
                break

        return ProfileAnalysisResult(
            profile_id=profile_config.profile_id,
            symbol=symbol,
            primary_timeframe=prim_tf,
            context_timeframes=profile_config.context_timeframes,
            profile_state=profile_state,
            state_description=state_desc,
            trade_plan=trade_plan,
            context_confirmed=context_confirmed,
            alignment_score=round(alignment_score, 1),
            score_tier=score_tier,
            cost_sensitivity=cost_tiers,
            cost_warning=cost_warning,
            analytical_timestamp=mtf_context.analytical_timestamp,
            is_preview=not is_confirmed,
            reasons=reasons,
        )
