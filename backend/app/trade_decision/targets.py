"""
Phase 10 — Deterministic Target Planner.
Calculates multi-tiered take-profit targets based on risk distance, predefined canonical R-multiples,
and intelligent, auditable structural constraints using deterministic ATR buffers.
"""

from typing import Optional, List
from app.indicators.base import IndicatorSnapshot
from app.structure.models import MarketStructureSnapshot
from app.signals.models import SignalDirectionEnum
from app.trade_decision.config import TradeDecisionConfig, DEFAULT_TRADE_DECISION_CONFIG
from app.trade_decision.models import TakeProfitPlan, TargetLevelDetail


class TargetPlanner:
    """
    Deterministic Target Planner.
    Calculates TP1, TP2, TP3 targets from planned_entry_price and risk_distance.
    Applies auditable structural constraint rules with deterministic ATR buffers.
    """

    @staticmethod
    def plan_targets(
        planned_entry_price: float,
        stop_loss_price: float,
        direction: SignalDirectionEnum,
        indicators: IndicatorSnapshot,
        structure: MarketStructureSnapshot,
        config: TradeDecisionConfig = DEFAULT_TRADE_DECISION_CONFIG,
    ) -> Optional[TakeProfitPlan]:
        """
        Calculates TakeProfitPlan containing TP1, TP2, and TP3 details.
        Returns None if risk distance is invalid or target calculations violate directional invariants.
        """
        if planned_entry_price <= 0 or stop_loss_price <= 0 or indicators is None or indicators.volatility is None or indicators.volatility.atr is None:
            return None

        risk_distance = abs(planned_entry_price - stop_loss_price)
        if risk_distance <= 0:
            return None

        atr = float(indicators.volatility.atr)
        buffer = config.structure_target_buffer_atr

        m1 = config.default_tp1_r_multiple  # 1.25
        m2 = config.default_tp2_r_multiple  # 2.00
        m3 = config.default_tp3_r_multiple  # 3.00

        if direction == SignalDirectionEnum.LONG_SETUP:
            # Theoretical unconstrained targets
            orig_tp1 = round(planned_entry_price + (risk_distance * m1), 4)
            orig_tp2 = round(planned_entry_price + (risk_distance * m2), 4)
            orig_tp3 = round(planned_entry_price + (risk_distance * m3), 4)

            # Available confirmed resistance zones and swing highs above planned entry
            resistance_levels: List[float] = []
            if structure.resistance_zones:
                for rz in structure.resistance_zones:
                    if rz.price_low > planned_entry_price:
                        resistance_levels.append(float(rz.price_low))
            if structure.active_structural_high and structure.active_structural_high.price > planned_entry_price:
                resistance_levels.append(float(structure.active_structural_high.price))
            resistance_levels.sort()

            def adjust_buy_target(orig: float, base_mult: float, min_floor: float) -> TargetLevelDetail:
                # Find if any structural resistance lies directly in the path (between planned_entry and original target)
                hit_res = None
                for r in resistance_levels:
                    # If resistance is slightly below or near original target (within 0.3 ATR), front-run it by buffer
                    if planned_entry_price < r <= orig + 0.1 * atr:
                        hit_res = r
                        break

                if hit_res is not None:
                    struct_adj = round(hit_res - (buffer * atr), 4)
                    # Don't let adjustment fall below previous TP floor or entry
                    if struct_adj > min_floor:
                        actual_rr = round(abs(struct_adj - planned_entry_price) / risk_distance, 4)
                        dist = round(abs(struct_adj - planned_entry_price), 4)
                        return TargetLevelDetail(
                            original_target=orig,
                            adjusted_target=struct_adj,
                            structural_level=round(hit_res, 4),
                            adjustment_reason=f"Constrained by resistance at ${hit_res:,.2f} - ({buffer:.2f} ATR buffer).",
                            r_multiple_base=base_mult,
                            actual_rr_after_adjustment=actual_rr,
                            distance=dist,
                            constrained_by_structure=True,
                        )

                # Unconstrained target
                actual_rr = round(abs(orig - planned_entry_price) / risk_distance, 4)
                dist = round(abs(orig - planned_entry_price), 4)
                return TargetLevelDetail(
                    original_target=orig,
                    adjusted_target=orig,
                    structural_level=None,
                    adjustment_reason=f"Canonical {base_mult:.2f}R mathematical risk multiple.",
                    r_multiple_base=base_mult,
                    actual_rr_after_adjustment=actual_rr,
                    distance=dist,
                    constrained_by_structure=False,
                )

            tp1_detail = adjust_buy_target(orig_tp1, m1, planned_entry_price)
            tp2_detail = adjust_buy_target(orig_tp2, m2, tp1_detail.adjusted_target)
            tp3_detail = adjust_buy_target(orig_tp3, m3, tp2_detail.adjusted_target)

            # Ensure monotonic ordering: planned_entry < TP1 <= TP2 <= TP3
            if not (planned_entry_price < tp1_detail.adjusted_target <= tp2_detail.adjusted_target <= tp3_detail.adjusted_target):
                # Fallback to pure unconstrained canonical targets if structural constraints created inverted order
                tp1_detail = TargetLevelDetail(
                    original_target=orig_tp1,
                    adjusted_target=orig_tp1,
                    structural_level=None,
                    adjustment_reason=f"Canonical {m1:.2f}R risk multiple.",
                    r_multiple_base=m1,
                    actual_rr_after_adjustment=round(m1, 4),
                    distance=round(abs(orig_tp1 - planned_entry_price), 4),
                    constrained_by_structure=False,
                )
                tp2_detail = TargetLevelDetail(
                    original_target=orig_tp2,
                    adjusted_target=orig_tp2,
                    structural_level=None,
                    adjustment_reason=f"Canonical {m2:.2f}R risk multiple.",
                    r_multiple_base=m2,
                    actual_rr_after_adjustment=round(m2, 4),
                    distance=round(abs(orig_tp2 - planned_entry_price), 4),
                    constrained_by_structure=False,
                )
                tp3_detail = TargetLevelDetail(
                    original_target=orig_tp3,
                    adjusted_target=orig_tp3,
                    structural_level=None,
                    adjustment_reason=f"Canonical {m3:.2f}R risk multiple.",
                    r_multiple_base=m3,
                    actual_rr_after_adjustment=round(m3, 4),
                    distance=round(abs(orig_tp3 - planned_entry_price), 4),
                    constrained_by_structure=False,
                )

            return TakeProfitPlan(tp1=tp1_detail, tp2=tp2_detail, tp3=tp3_detail)

        elif direction == SignalDirectionEnum.SHORT_SETUP:
            # Theoretical unconstrained targets
            orig_tp1 = round(planned_entry_price - (risk_distance * m1), 4)
            orig_tp2 = round(planned_entry_price - (risk_distance * m2), 4)
            orig_tp3 = round(planned_entry_price - (risk_distance * m3), 4)

            # Available confirmed support zones and swing lows below planned entry
            support_levels: List[float] = []
            if structure.support_zones:
                for sz in structure.support_zones:
                    if sz.price_high < planned_entry_price:
                        support_levels.append(float(sz.price_high))
            if structure.active_structural_low and structure.active_structural_low.price < planned_entry_price:
                support_levels.append(float(structure.active_structural_low.price))
            support_levels.sort(reverse=True)

            def adjust_sell_target(orig: float, base_mult: float, max_ceiling: float) -> TargetLevelDetail:
                hit_sup = None
                for s in support_levels:
                    if planned_entry_price > s >= orig - 0.1 * atr:
                        hit_sup = s
                        break

                if hit_sup is not None:
                    struct_adj = round(hit_sup + (buffer * atr), 4)
                    if struct_adj < max_ceiling:
                        actual_rr = round(abs(planned_entry_price - struct_adj) / risk_distance, 4)
                        dist = round(abs(planned_entry_price - struct_adj), 4)
                        return TargetLevelDetail(
                            original_target=orig,
                            adjusted_target=struct_adj,
                            structural_level=round(hit_sup, 4),
                            adjustment_reason=f"Constrained by support at ${hit_sup:,.2f} + ({buffer:.2f} ATR buffer).",
                            r_multiple_base=base_mult,
                            actual_rr_after_adjustment=actual_rr,
                            distance=dist,
                            constrained_by_structure=True,
                        )

                actual_rr = round(abs(planned_entry_price - orig) / risk_distance, 4)
                dist = round(abs(planned_entry_price - orig), 4)
                return TargetLevelDetail(
                    original_target=orig,
                    adjusted_target=orig,
                    structural_level=None,
                    adjustment_reason=f"Canonical {base_mult:.2f}R mathematical risk multiple.",
                    r_multiple_base=base_mult,
                    actual_rr_after_adjustment=actual_rr,
                    distance=dist,
                    constrained_by_structure=False,
                )

            tp1_detail = adjust_sell_target(orig_tp1, m1, planned_entry_price)
            tp2_detail = adjust_sell_target(orig_tp2, m2, tp1_detail.adjusted_target)
            tp3_detail = adjust_sell_target(orig_tp3, m3, tp2_detail.adjusted_target)

            # Ensure monotonic ordering: planned_entry > TP1 >= TP2 >= TP3
            if not (planned_entry_price > tp1_detail.adjusted_target >= tp2_detail.adjusted_target >= tp3_detail.adjusted_target):
                tp1_detail = TargetLevelDetail(
                    original_target=orig_tp1,
                    adjusted_target=orig_tp1,
                    structural_level=None,
                    adjustment_reason=f"Canonical {m1:.2f}R risk multiple.",
                    r_multiple_base=m1,
                    actual_rr_after_adjustment=round(m1, 4),
                    distance=round(abs(planned_entry_price - orig_tp1), 4),
                    constrained_by_structure=False,
                )
                tp2_detail = TargetLevelDetail(
                    original_target=orig_tp2,
                    adjusted_target=orig_tp2,
                    structural_level=None,
                    adjustment_reason=f"Canonical {m2:.2f}R risk multiple.",
                    r_multiple_base=m2,
                    actual_rr_after_adjustment=round(m2, 4),
                    distance=round(abs(planned_entry_price - orig_tp2), 4),
                    constrained_by_structure=False,
                )
                tp3_detail = TargetLevelDetail(
                    original_target=orig_tp3,
                    adjusted_target=orig_tp3,
                    structural_level=None,
                    adjustment_reason=f"Canonical {m3:.2f}R risk multiple.",
                    r_multiple_base=m3,
                    actual_rr_after_adjustment=round(m3, 4),
                    distance=round(abs(planned_entry_price - orig_tp3), 4),
                    constrained_by_structure=False,
                )

            return TakeProfitPlan(tp1=tp1_detail, tp2=tp2_detail, tp3=tp3_detail)

        return None
