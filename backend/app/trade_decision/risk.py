"""
Phase 10 — Deterministic Risk & Reward Filter.
Enforces strict minimum risk/reward standards against actual structurally-adjusted targets.
Rejects setups as NO_TRADE if structural reward is insufficient relative to risk.
"""

from typing import Optional
from app.trade_decision.config import TradeDecisionConfig, DEFAULT_TRADE_DECISION_CONFIG
from app.trade_decision.models import StopLossPlan, TakeProfitPlan, RiskRewardSummary


class RiskPlanner:
    """
    Deterministic Risk & Reward Engine.
    Validates that actual (post-structural adjustment) R:R ratios satisfy canonical minimum requirements.
    """

    @staticmethod
    def evaluate_risk_reward(
        planned_entry_price: float,
        stop_loss: StopLossPlan,
        take_profits: TakeProfitPlan,
        config: TradeDecisionConfig = DEFAULT_TRADE_DECISION_CONFIG,
    ) -> RiskRewardSummary:
        """
        Computes actual R:R ratios and checks against minimum thresholds.
        Never fabricates or forces a trade with sub-threshold reward.
        """
        risk_distance = abs(planned_entry_price - stop_loss.price)
        if risk_distance <= 0:
            return RiskRewardSummary(
                tp1_rr=0.0,
                tp2_rr=0.0,
                tp3_rr=0.0,
                risk_distance=0.0,
                is_acceptable=False,
                rejection_reason="Calculated risk distance is zero or negative.",
            )

        tp1_rr = round(take_profits.tp1.actual_rr_after_adjustment, 4)
        tp2_rr = round(take_profits.tp2.actual_rr_after_adjustment, 4)
        tp3_rr = round(take_profits.tp3.actual_rr_after_adjustment, 4)

        # Enforce canonical minimums
        if tp1_rr < config.min_acceptable_tp1_rr:
            return RiskRewardSummary(
                tp1_rr=tp1_rr,
                tp2_rr=tp2_rr,
                tp3_rr=tp3_rr,
                risk_distance=risk_distance,
                is_acceptable=False,
                rejection_reason=f"Insufficient structural reward relative to calculated risk (TP1 R:R is {tp1_rr:.2f} < {config.min_acceptable_tp1_rr:.2f} required).",
            )

        if tp2_rr < config.min_acceptable_tp2_rr:
            return RiskRewardSummary(
                tp1_rr=tp1_rr,
                tp2_rr=tp2_rr,
                tp3_rr=tp3_rr,
                risk_distance=risk_distance,
                is_acceptable=False,
                rejection_reason=f"Insufficient structural reward relative to calculated risk (TP2 R:R is {tp2_rr:.2f} < {config.min_acceptable_tp2_rr:.2f} required).",
            )

        if tp3_rr < config.min_acceptable_tp3_rr:
            return RiskRewardSummary(
                tp1_rr=tp1_rr,
                tp2_rr=tp2_rr,
                tp3_rr=tp3_rr,
                risk_distance=risk_distance,
                is_acceptable=False,
                rejection_reason=f"Insufficient structural reward relative to calculated risk (TP3 R:R is {tp3_rr:.2f} < {config.min_acceptable_tp3_rr:.2f} required).",
            )

        return RiskRewardSummary(
            tp1_rr=tp1_rr,
            tp2_rr=tp2_rr,
            tp3_rr=tp3_rr,
            risk_distance=risk_distance,
            is_acceptable=True,
            rejection_reason=None,
        )
