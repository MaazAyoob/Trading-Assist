"""
Phase 10 — Deterministic Trade Decision Evaluator.
Executes the strict 11-step analytical hierarchy to convert multi-factor research intelligence into
an actionable BUY, SELL, or NO_TRADE trade plan.
"""

import time
from typing import List, Optional, Tuple, Dict, Any
from app.data.schema import Candle, MarketDataQuality, QualityStatusEnum, CandleStateEnum
from app.indicators.base import IndicatorSnapshot
from app.regime.models import MarketRegimeSnapshot, OverallRegimeEnum, DirectionEnum, TrendStrengthEnum
from app.structure.models import MarketStructureSnapshot, StructureEventTypeEnum
from app.signals.models import ResearchSignal, SignalDirectionEnum, SignalStatusEnum
from app.trade_decision.config import TradeDecisionConfig, DEFAULT_TRADE_DECISION_CONFIG
from app.trade_decision.models import (
    TradeDecisionEnum,
    TradePlanState,
    DecisionStatusEnum,
    ConfidenceGradeEnum,
    AuditCheckStatusEnum,
    AuditCheckItem,
    DecisionAuditTrace,
    DecisionContext,
    TradePlan,
    RiskRewardSummary,
)
from app.trade_decision.entry import EntryPlanner
from app.trade_decision.stops import StopLossPlanner
from app.trade_decision.targets import TargetPlanner
from app.trade_decision.risk import RiskPlanner


class DecisionEvaluator:
    """
    Deterministic 11-step decision engine evaluator.
    Constructs an auditable TradePlan with full audit trace.
    """

    @staticmethod
    def evaluate(
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
        now_ms = int(time.time() * 1000)
        latest_candle = candles[-1] if candles else None

        open_time = latest_candle.timestamp if latest_candle else 0
        close_time = latest_candle.close_time if latest_candle else 0
        timeframe = signal.timeframe if signal else "15m"
        symbol = signal.symbol if signal else "BTCUSDT"

        # Timeframe interval in ms for validity window
        tf_ms = 15 * 60 * 1000
        if timeframe.endswith("m"):
            tf_ms = int(timeframe[:-1]) * 60 * 1000
        elif timeframe.endswith("h"):
            tf_ms = int(timeframe[:-1]) * 60 * 60 * 1000
        elif timeframe.endswith("d"):
            tf_ms = int(timeframe[:-1]) * 24 * 60 * 60 * 1000

        valid_until = close_time + (config.default_max_valid_candles * tf_ms)

        # Context Object
        context = DecisionContext(
            signal_score=round(signal.score, 2) if signal else 0.0,
            regime=regime.overall_regime.value if regime and regime.overall_regime else "UNKNOWN",
            trend_strength=regime.trend_strength.value if regime and regime.trend_strength else "UNKNOWN",
            structure=str(structure.structure_direction) if structure else "UNKNOWN",
            volatility=str(regime.volatility_state.value) if regime and regime.volatility_state else "UNKNOWN",
            momentum=str(regime.momentum_state.value) if regime and regime.momentum_state else "UNKNOWN",
            volume=str(regime.volume_state.value) if regime and regime.volume_state else "UNKNOWN",
        )

        supporting_factors: List[str] = []
        conflicting_factors: List[str] = []
        reasons_for_no_trade: List[str] = []
        invalidation_conditions: List[str] = []

        # Helper to construct no_trade plan
        def build_no_trade(audit: DecisionAuditTrace, alignment_score: float = 0.0) -> TradePlan:
            grade = DecisionEvaluator._grade_confidence(alignment_score)
            return TradePlan(
                decision=TradeDecisionEnum.NO_TRADE,
                direction="NEUTRAL",
                state=TradePlanState.NO_TRADE,
                status=DecisionStatusEnum.WAITING if reasons_for_no_trade else DecisionStatusEnum.INSUFFICIENT_DATA,
                decision_alignment_score=round(alignment_score, 1),
                confidence_grade=grade,
                strategy_context_id=strategy_context_id,
                strategy_context_version="1.0.0",
                strategy_config_hash="BASE_V1",
                symbol=symbol,
                timeframe=timeframe,
                decision_candle_open_time=open_time,
                decision_candle_close_time=close_time,
                calculated_at=now_ms,
                market_data_last_updated_at=quality.latest_timestamp if (quality and quality.latest_timestamp) else now_ms,
                created_at=close_time if is_confirmed else now_ms,
                valid_until=valid_until,
                max_valid_candles=config.default_max_valid_candles,
                bars_since_creation=0,
                is_confirmed=is_confirmed,
                is_preview=not is_confirmed,
                entry=None,
                stop_loss=None,
                take_profits=None,
                risk_reward=None,
                context=context,
                supporting_factors=supporting_factors,
                conflicting_factors=conflicting_factors,
                reasons_for_no_trade=reasons_for_no_trade,
                invalidation_conditions=invalidation_conditions,
                audit_trace=audit,
            )

        # -------------------------------------------------------------
        # STEP 1: Data Quality Check
        # -------------------------------------------------------------
        q_status = quality.status if quality else QualityStatusEnum.HEALTHY
        if q_status in (QualityStatusEnum.INVALID, QualityStatusEnum.INSUFFICIENT_DATA, QualityStatusEnum.OFFLINE) or (quality and (quality.stale or quality.gap_count > 0 or quality.invalid_count > 0)):
            msg = f"Data quality status is {q_status.value} (stale={quality.stale if quality else False}, gap_count={quality.gap_count if quality else 0})."
            reasons_for_no_trade.append(msg)
            conflicting_factors.append(msg)
            audit = DecisionEvaluator._empty_audit_trace()
            audit.data_quality_check = AuditCheckItem(check_name="data_quality_check", status=AuditCheckStatusEnum.FAIL, reason=msg)
            audit.final_decision = AuditCheckItem(check_name="final_decision", status=AuditCheckStatusEnum.FAIL, reason="Data quality failed.")
            return build_no_trade(audit)

        audit_data_quality = AuditCheckItem(check_name="data_quality_check", status=AuditCheckStatusEnum.PASS, reason="Market data quality verified healthy.")

        # -------------------------------------------------------------
        # STEP 2: Research Signal Status Check
        # -------------------------------------------------------------
        if not signal or signal.status != SignalStatusEnum.VALID or signal.direction == SignalDirectionEnum.NEUTRAL:
            sig_msg = f"Research signal is {signal.status.value if signal else 'MISSING'} ({signal.direction.value if signal else 'NEUTRAL'})."
            reasons_for_no_trade.append(sig_msg)
            audit = DecisionEvaluator._empty_audit_trace()
            audit.data_quality_check = audit_data_quality
            audit.signal_check = AuditCheckItem(check_name="signal_check", status=AuditCheckStatusEnum.FAIL, reason=sig_msg)
            audit.final_decision = AuditCheckItem(check_name="final_decision", status=AuditCheckStatusEnum.FAIL, reason="No actionable directional research signal.")
            return build_no_trade(audit)

        audit_signal = AuditCheckItem(
            check_name="signal_check",
            status=AuditCheckStatusEnum.PASS,
            reason=f"Valid {signal.direction.value} research signal with score {signal.score:+.1f}.",
            details={"score": signal.score, "strength": signal.strength.value},
        )
        supporting_factors.extend(signal.supporting_evidence[:3])

        # -------------------------------------------------------------
        # STEP 3: Strategy Candidate Filter Check
        # -------------------------------------------------------------
        strat_pass, strat_msg = DecisionEvaluator._evaluate_strategy_filter(
            strategy_context_id=strategy_context_id,
            signal=signal,
            indicators=indicators,
            candles=candles,
        )
        if not strat_pass:
            reasons_for_no_trade.append(strat_msg)
            conflicting_factors.append(strat_msg)
            audit = DecisionEvaluator._empty_audit_trace()
            audit.data_quality_check = audit_data_quality
            audit.signal_check = audit_signal
            audit.strategy_filter_check = AuditCheckItem(check_name="strategy_filter_check", status=AuditCheckStatusEnum.FAIL, reason=strat_msg)
            audit.final_decision = AuditCheckItem(check_name="final_decision", status=AuditCheckStatusEnum.FAIL, reason=f"Strategy {strategy_context_id} filter rejected setup.")
            return build_no_trade(audit)

        audit_strategy = AuditCheckItem(check_name="strategy_filter_check", status=AuditCheckStatusEnum.PASS, reason=strat_msg)

        # -------------------------------------------------------------
        # STEP 4: Regime Compatibility Check
        # -------------------------------------------------------------
        regime_pass, regime_msg = DecisionEvaluator._evaluate_regime_compatibility(signal.direction, regime)
        if not regime_pass:
            reasons_for_no_trade.append(regime_msg)
            conflicting_factors.append(regime_msg)
            audit = DecisionEvaluator._empty_audit_trace()
            audit.data_quality_check = audit_data_quality
            audit.signal_check = audit_signal
            audit.strategy_filter_check = audit_strategy
            audit.regime_check = AuditCheckItem(check_name="regime_check", status=AuditCheckStatusEnum.FAIL, reason=regime_msg)
            audit.final_decision = AuditCheckItem(check_name="final_decision", status=AuditCheckStatusEnum.FAIL, reason="Market regime contradicts trade direction.")
            return build_no_trade(audit)

        audit_regime = AuditCheckItem(check_name="regime_check", status=AuditCheckStatusEnum.PASS, reason=regime_msg)
        supporting_factors.append(f"Regime alignment: {regime.overall_regime.value} ({regime.trend_strength.value})")

        # -------------------------------------------------------------
        # STEP 5: Market Structure Compatibility Check
        # -------------------------------------------------------------
        struct_pass, struct_msg = DecisionEvaluator._evaluate_structure_compatibility(signal.direction, structure)
        if not struct_pass:
            reasons_for_no_trade.append(struct_msg)
            conflicting_factors.append(struct_msg)
            audit = DecisionEvaluator._empty_audit_trace()
            audit.data_quality_check = audit_data_quality
            audit.signal_check = audit_signal
            audit.strategy_filter_check = audit_strategy
            audit.regime_check = audit_regime
            audit.structure_check = AuditCheckItem(check_name="structure_check", status=AuditCheckStatusEnum.FAIL, reason=struct_msg)
            audit.final_decision = AuditCheckItem(check_name="final_decision", status=AuditCheckStatusEnum.FAIL, reason="Market structure contradicts trade direction.")
            return build_no_trade(audit)

        audit_structure = AuditCheckItem(check_name="structure_check", status=AuditCheckStatusEnum.PASS, reason=struct_msg)
        supporting_factors.append(f"Structure alignment: {structure.structure_direction} structure")

        # -------------------------------------------------------------
        # STEP 6: S/R Clearance Check
        # -------------------------------------------------------------
        sr_pass, sr_msg = DecisionEvaluator._evaluate_sr_clearance(signal.direction, latest_candle, indicators, structure)
        if not sr_pass:
            reasons_for_no_trade.append(sr_msg)
            conflicting_factors.append(sr_msg)
            audit = DecisionEvaluator._empty_audit_trace()
            audit.data_quality_check = audit_data_quality
            audit.signal_check = audit_signal
            audit.strategy_filter_check = audit_strategy
            audit.regime_check = audit_regime
            audit.structure_check = audit_structure
            audit.sr_clearance_check = AuditCheckItem(check_name="sr_clearance_check", status=AuditCheckStatusEnum.FAIL, reason=sr_msg)
            audit.final_decision = AuditCheckItem(check_name="final_decision", status=AuditCheckStatusEnum.FAIL, reason="Immediate S/R barrier directly opposing entry.")
            return build_no_trade(audit)

        audit_sr = AuditCheckItem(check_name="sr_clearance_check", status=AuditCheckStatusEnum.PASS, reason=sr_msg)

        # -------------------------------------------------------------
        # STEP 7: Entry Planning
        # -------------------------------------------------------------
        entry_result = EntryPlanner.plan_entry(latest_candle, indicators, structure, signal, config)
        if not entry_result:
            entry_msg = "Could not establish a rule-based analytical entry reference."
            reasons_for_no_trade.append(entry_msg)
            audit = DecisionEvaluator._empty_audit_trace()
            audit.data_quality_check = audit_data_quality
            audit.signal_check = audit_signal
            audit.strategy_filter_check = audit_strategy
            audit.regime_check = audit_regime
            audit.structure_check = audit_structure
            audit.sr_clearance_check = audit_sr
            audit.entry_check = AuditCheckItem(check_name="entry_check", status=AuditCheckStatusEnum.FAIL, reason=entry_msg)
            audit.final_decision = AuditCheckItem(check_name="final_decision", status=AuditCheckStatusEnum.FAIL, reason="Entry calculation failed.")
            return build_no_trade(audit)

        entry_plan, plan_state = entry_result
        audit_entry = AuditCheckItem(
            check_name="entry_check",
            status=AuditCheckStatusEnum.PASS,
            reason=f"Planned entry established at ${entry_plan.planned_entry_price:,.2f} ({entry_plan.entry_type.value}).",
            details=entry_plan.model_dump(),
        )

        # -------------------------------------------------------------
        # STEP 8: Stop Loss Planning
        # -------------------------------------------------------------
        stop_loss_plan = StopLossPlanner.plan_stop_loss(entry_plan.planned_entry_price, signal.direction, indicators, structure, config)
        if not stop_loss_plan:
            sl_msg = "Could not place a mathematically valid structural stop loss."
            reasons_for_no_trade.append(sl_msg)
            audit = DecisionEvaluator._empty_audit_trace()
            audit.data_quality_check = audit_data_quality
            audit.signal_check = audit_signal
            audit.strategy_filter_check = audit_strategy
            audit.regime_check = audit_regime
            audit.structure_check = audit_structure
            audit.sr_clearance_check = audit_sr
            audit.entry_check = audit_entry
            audit.stop_check = AuditCheckItem(check_name="stop_check", status=AuditCheckStatusEnum.FAIL, reason=sl_msg)
            audit.final_decision = AuditCheckItem(check_name="final_decision", status=AuditCheckStatusEnum.FAIL, reason="Stop loss placement rejected.")
            return build_no_trade(audit)

        audit_stop = AuditCheckItem(
            check_name="stop_check",
            status=AuditCheckStatusEnum.PASS,
            reason=f"Stop loss positioned at ${stop_loss_plan.price:,.2f} ({stop_loss_plan.distance_atr:.2f} ATR).",
            details=stop_loss_plan.model_dump(),
        )

        # -------------------------------------------------------------
        # STEP 9: Take Profit Planning
        # -------------------------------------------------------------
        take_profit_plan = TargetPlanner.plan_targets(
            entry_plan.planned_entry_price,
            stop_loss_plan.price,
            signal.direction,
            indicators,
            structure,
            config,
        )
        if not take_profit_plan:
            tp_msg = "Could not calculate valid monotonic take profit targets."
            reasons_for_no_trade.append(tp_msg)
            audit = DecisionEvaluator._empty_audit_trace()
            audit.data_quality_check = audit_data_quality
            audit.signal_check = audit_signal
            audit.strategy_filter_check = audit_strategy
            audit.regime_check = audit_regime
            audit.structure_check = audit_structure
            audit.sr_clearance_check = audit_sr
            audit.entry_check = audit_entry
            audit.stop_check = audit_stop
            audit.target_check = AuditCheckItem(check_name="target_check", status=AuditCheckStatusEnum.FAIL, reason=tp_msg)
            audit.final_decision = AuditCheckItem(check_name="final_decision", status=AuditCheckStatusEnum.FAIL, reason="Target calculations rejected.")
            return build_no_trade(audit)

        audit_target = AuditCheckItem(
            check_name="target_check",
            status=AuditCheckStatusEnum.PASS,
            reason=f"Targets calculated: TP1=${take_profit_plan.tp1.adjusted_target:,.2f}, TP2=${take_profit_plan.tp2.adjusted_target:,.2f}, TP3=${take_profit_plan.tp3.adjusted_target:,.2f}.",
            details=take_profit_plan.model_dump(),
        )

        # -------------------------------------------------------------
        # STEP 10: Risk/Reward Requirements Check
        # -------------------------------------------------------------
        risk_summary = RiskPlanner.evaluate_risk_reward(entry_plan.planned_entry_price, stop_loss_plan, take_profit_plan, config)
        if not risk_summary.is_acceptable:
            rr_msg = risk_summary.rejection_reason or "Insufficient structural reward relative to calculated risk."
            reasons_for_no_trade.append(rr_msg)
            conflicting_factors.append(rr_msg)
            audit = DecisionEvaluator._empty_audit_trace()
            audit.data_quality_check = audit_data_quality
            audit.signal_check = audit_signal
            audit.strategy_filter_check = audit_strategy
            audit.regime_check = audit_regime
            audit.structure_check = audit_structure
            audit.sr_clearance_check = audit_sr
            audit.entry_check = audit_entry
            audit.stop_check = audit_stop
            audit.target_check = audit_target
            audit.risk_reward_check = AuditCheckItem(check_name="risk_reward_check", status=AuditCheckStatusEnum.FAIL, reason=rr_msg)
            audit.final_decision = AuditCheckItem(check_name="final_decision", status=AuditCheckStatusEnum.FAIL, reason="Minimum risk-reward threshold not satisfied.")
            return build_no_trade(audit)

        audit_risk_reward = AuditCheckItem(
            check_name="risk_reward_check",
            status=AuditCheckStatusEnum.PASS,
            reason=f"Risk/reward verified: TP1=1:{risk_summary.tp1_rr:.2f}, TP2=1:{risk_summary.tp2_rr:.2f}, TP3=1:{risk_summary.tp3_rr:.2f}.",
            details=risk_summary.model_dump(),
        )

        # -------------------------------------------------------------
        # STEP 11: Confidence & Alignment Score Calculation
        # -------------------------------------------------------------
        alignment_score = DecisionEvaluator._calculate_alignment_score(
            signal=signal,
            regime=regime,
            structure=structure,
            indicators=indicators,
            risk_summary=risk_summary,
        )

        confidence_grade = DecisionEvaluator._grade_confidence(alignment_score)
        if alignment_score < config.min_alignment_score_actionable:
            low_score_msg = f"Decision alignment score ({alignment_score:.1f}/100) below minimum actionable threshold ({config.min_alignment_score_actionable:.1f})."
            reasons_for_no_trade.append(low_score_msg)
            conflicting_factors.append(low_score_msg)
            audit = DecisionEvaluator._empty_audit_trace()
            audit.data_quality_check = audit_data_quality
            audit.signal_check = audit_signal
            audit.strategy_filter_check = audit_strategy
            audit.regime_check = audit_regime
            audit.structure_check = audit_structure
            audit.sr_clearance_check = audit_sr
            audit.entry_check = audit_entry
            audit.stop_check = audit_stop
            audit.target_check = audit_target
            audit.risk_reward_check = audit_risk_reward
            audit.confidence_check = AuditCheckItem(check_name="confidence_check", status=AuditCheckStatusEnum.FAIL, reason=low_score_msg)
            audit.final_decision = AuditCheckItem(check_name="final_decision", status=AuditCheckStatusEnum.FAIL, reason="Low analytical alignment score.")
            return build_no_trade(audit, alignment_score)

        audit_confidence = AuditCheckItem(
            check_name="confidence_check",
            status=AuditCheckStatusEnum.PASS,
            reason=f"Decision alignment score {alignment_score:.1f}/100 [{confidence_grade.value}].",
        )

        # Generate Invalidation Conditions
        if signal.direction == SignalDirectionEnum.LONG_SETUP:
            invalidation_conditions = [
                f"Confirmed close below structural stop at ${stop_loss_plan.price:,.2f}.",
                "Bearish Change of Character (CHoCH) detected before entry zone fill.",
                f"Break and close below confirmed support (${structure.support_zones[0].price_low:,.2f})" if structure.support_zones else "Break of active structural swing low.",
                "Market data quality transition to STALE, GAP, or OFFLINE status.",
                f"Exceeding maximum holding window of {config.default_max_valid_candles} closed candles ({config.default_max_valid_candles * 15}m) without fill.",
            ]
            final_decision_type = TradeDecisionEnum.BUY
            direction_str = "LONG"
        else:
            invalidation_conditions = [
                f"Confirmed close above structural stop at ${stop_loss_plan.price:,.2f}.",
                "Bullish Change of Character (CHoCH) detected before entry zone fill.",
                f"Break and close above confirmed resistance (${structure.resistance_zones[0].price_high:,.2f})" if structure.resistance_zones else "Break of active structural swing high.",
                "Market data quality transition to STALE, GAP, or OFFLINE status.",
                f"Exceeding maximum holding window of {config.default_max_valid_candles} closed candles ({config.default_max_valid_candles * 15}m) without fill.",
            ]
            final_decision_type = TradeDecisionEnum.SELL
            direction_str = "SHORT"

        audit_final = AuditCheckItem(
            check_name="final_decision",
            status=AuditCheckStatusEnum.PASS,
            reason=f"Actionable {final_decision_type.value} setup confirmed with alignment score {alignment_score:.1f}/100.",
        )

        final_audit_trace = DecisionAuditTrace(
            data_quality_check=audit_data_quality,
            signal_check=audit_signal,
            strategy_filter_check=audit_strategy,
            regime_check=audit_regime,
            structure_check=audit_structure,
            sr_clearance_check=audit_sr,
            entry_check=audit_entry,
            stop_check=audit_stop,
            target_check=audit_target,
            risk_reward_check=audit_risk_reward,
            confidence_check=audit_confidence,
            final_decision=audit_final,
        )

        return TradePlan(
            decision=final_decision_type,
            direction=direction_str,
            state=plan_state,
            status=DecisionStatusEnum.VALID,
            decision_alignment_score=round(alignment_score, 1),
            confidence_grade=confidence_grade,
            strategy_context_id=strategy_context_id,
            strategy_context_version="1.0.0",
            strategy_config_hash="BASE_V1",
            symbol=symbol,
            timeframe=timeframe,
            decision_candle_open_time=open_time,
            decision_candle_close_time=close_time,
            calculated_at=now_ms,
            market_data_last_updated_at=quality.latest_timestamp if (quality and quality.latest_timestamp) else now_ms,
            created_at=close_time if is_confirmed else now_ms,
            valid_until=valid_until,
            max_valid_candles=config.default_max_valid_candles,
            bars_since_creation=0,
            is_confirmed=is_confirmed,
            is_preview=not is_confirmed,
            entry=entry_plan,
            stop_loss=stop_loss_plan,
            take_profits=take_profit_plan,
            risk_reward=risk_summary,
            context=context,
            supporting_factors=supporting_factors,
            conflicting_factors=conflicting_factors,
            reasons_for_no_trade=[],
            invalidation_conditions=invalidation_conditions,
            audit_trace=final_audit_trace,
        )

    # -------------------------------------------------------------------------
    # Helper Validation & Scoring Functions
    # -------------------------------------------------------------------------

    @staticmethod
    def _evaluate_strategy_filter(
        strategy_context_id: str,
        signal: ResearchSignal,
        indicators: IndicatorSnapshot,
        candles: List[Candle],
    ) -> Tuple[bool, str]:
        if strategy_context_id == "EXP_A2_PULLBACK_VWAP":
            # A2 Filter: Price must be in moderate proximity to VWAP (not excessively extended > 1.2 ATR)
            if indicators and indicators.trend and indicators.trend.vwap and indicators.volatility and indicators.volatility.atr and candles:
                ref = candles[-1].close
                vwap_dist = abs(ref - indicators.trend.vwap) / indicators.volatility.atr
                if vwap_dist > 1.5:
                    return False, f"A2 Strategy Filter: Price is overextended from VWAP ({vwap_dist:.2f} ATR > 1.50 limit)."
            return True, "A2 Pullback Strategy filter passed."

        elif strategy_context_id == "EXP_E2_EXTENSION_VWAP":
            # E2 Filter: Pre-signal run-up limit
            if candles and len(candles) >= 6 and indicators and indicators.volatility and indicators.volatility.atr:
                pre_move = abs(candles[-1].close - candles[-6].close) / indicators.volatility.atr
                if pre_move > 3.0:
                    return False, f"E2 Strategy Filter: Pre-signal extension too high ({pre_move:.2f} ATR > 3.00 limit)."
            return True, "E2 Extension Strategy filter passed."

        # Default: Baseline
        return True, "Phase 5 Baseline strategy context applied."

    @staticmethod
    def _evaluate_regime_compatibility(
        direction: SignalDirectionEnum,
        regime: MarketRegimeSnapshot,
    ) -> Tuple[bool, str]:
        if not regime:
            return True, "Regime not available."

        if direction == SignalDirectionEnum.LONG_SETUP:
            if regime.overall_regime == OverallRegimeEnum.TRENDING_BEARISH and regime.trend_strength in (TrendStrengthEnum.STRONG, TrendStrengthEnum.VERY_STRONG):
                return False, f"Strong opposing downtrend regime active ({regime.overall_regime.value})."
        elif direction == SignalDirectionEnum.SHORT_SETUP:
            if regime.overall_regime == OverallRegimeEnum.TRENDING_BULLISH and regime.trend_strength in (TrendStrengthEnum.STRONG, TrendStrengthEnum.VERY_STRONG):
                return False, f"Strong opposing uptrend regime active ({regime.overall_regime.value})."

        return True, f"Regime {regime.overall_regime.value} is compatible."

    @staticmethod
    def _evaluate_structure_compatibility(
        direction: SignalDirectionEnum,
        structure: MarketStructureSnapshot,
    ) -> Tuple[bool, str]:
        if not structure:
            return True, "Structure not available."

        recent_choch = structure.choch_events[-1] if structure.choch_events else None
        if direction == SignalDirectionEnum.LONG_SETUP:
            if recent_choch and recent_choch.event_type.value == "BEARISH_CHOCH":
                return False, "Recent Bearish Change of Character (CHoCH) detected in structure."
        elif direction == SignalDirectionEnum.SHORT_SETUP:
            if recent_choch and recent_choch.event_type.value == "BULLISH_CHOCH":
                return False, "Recent Bullish Change of Character (CHoCH) detected in structure."

        return True, f"Market structure direction ({structure.structure_direction}) is compatible."

    @staticmethod
    def _evaluate_sr_clearance(
        direction: SignalDirectionEnum,
        candle: Optional[Candle],
        indicators: Optional[IndicatorSnapshot],
        structure: Optional[MarketStructureSnapshot],
    ) -> Tuple[bool, str]:
        if not candle or not indicators or not indicators.volatility or not indicators.volatility.atr or not structure:
            return True, "S/R clearance check skipped (insufficient data)."

        ref = candle.close
        atr = indicators.volatility.atr

        if direction == SignalDirectionEnum.LONG_SETUP and structure.resistance_zones:
            for rz in structure.resistance_zones:
                if 0 <= (rz.price_low - ref) < 0.20 * atr:
                    return False, f"Price (${ref:,.2f}) is directly underneath resistance zone (${rz.price_low:,.2f}) with < 0.20 ATR clearance."

        elif direction == SignalDirectionEnum.SHORT_SETUP and structure.support_zones:
            for sz in structure.support_zones:
                if 0 <= (ref - sz.price_high) < 0.20 * atr:
                    return False, f"Price (${ref:,.2f}) is directly above support zone (${sz.price_high:,.2f}) with < 0.20 ATR clearance."

        return True, "S/R clearance verified with adequate headway."

    @staticmethod
    def _calculate_alignment_score(
        signal: ResearchSignal,
        regime: MarketRegimeSnapshot,
        structure: MarketStructureSnapshot,
        indicators: IndicatorSnapshot,
        risk_summary: RiskRewardSummary,
    ) -> float:
        """
        Calculates deterministic decision_alignment_score (0.0 to 100.0).
        Measures agreement between existing analytical components.
        """
        base_score = abs(signal.score) if signal else 50.0  # signal score is in [0, 100]

        bonus = 0.0
        # 1. Regime alignment
        if regime and ((signal.direction == SignalDirectionEnum.LONG_SETUP and "BULLISH" in regime.overall_regime.value) or
                       (signal.direction == SignalDirectionEnum.SHORT_SETUP and "BEARISH" in regime.overall_regime.value)):
            bonus += 10.0

        # 2. Structure alignment
        if structure and ((signal.direction == SignalDirectionEnum.LONG_SETUP and structure.structure_direction == "BULLISH") or
                          (signal.direction == SignalDirectionEnum.SHORT_SETUP and structure.structure_direction == "BEARISH")):
            bonus += 10.0

        # 3. Risk/Reward bonus
        if risk_summary and risk_summary.tp1_rr >= 1.5:
            bonus += 5.0

        # 4. Conflict penalties
        conflict_penalty = 0.0
        if signal and signal.conflicts:
            conflict_penalty = min(len(signal.conflicts) * 8.0, 25.0)

        final_score = base_score + bonus - conflict_penalty
        return max(0.0, min(100.0, final_score))

    @staticmethod
    def _grade_confidence(score: float) -> ConfidenceGradeEnum:
        if score >= 90.0:
            return ConfidenceGradeEnum.VERY_HIGH
        if score >= 75.0:
            return ConfidenceGradeEnum.HIGH
        if score >= 60.0:
            return ConfidenceGradeEnum.MODERATE
        if score >= 40.0:
            return ConfidenceGradeEnum.LOW
        return ConfidenceGradeEnum.VERY_LOW

    @staticmethod
    def _empty_audit_trace() -> DecisionAuditTrace:
        na = AuditCheckItem(check_name="pending", status=AuditCheckStatusEnum.NOT_APPLICABLE, reason="Not reached.")
        return DecisionAuditTrace(
            data_quality_check=na,
            signal_check=na,
            strategy_filter_check=na,
            regime_check=na,
            structure_check=na,
            sr_clearance_check=na,
            entry_check=na,
            stop_check=na,
            target_check=na,
            risk_reward_check=na,
            confidence_check=na,
            final_decision=na,
        )
