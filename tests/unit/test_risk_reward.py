"""
Unit Tests for Phase 10 — Risk/Reward Filter & Mathematical Invariants.
Verifies rejection of sub-threshold R:R setups and mathematical exactness of reconstructed ratios.
"""

import pytest
from app.trade_decision.models import StopLossPlan, TakeProfitPlan, TargetLevelDetail
from app.trade_decision.risk import RiskPlanner
from app.trade_decision.config import TradeDecisionConfig


def make_tp_detail(target: float, planned_entry: float, risk_dist: float, r_base: float) -> TargetLevelDetail:
    actual_rr = abs(target - planned_entry) / risk_dist
    return TargetLevelDetail(
        original_target=target,
        adjusted_target=target,
        structural_level=None,
        adjustment_reason="Test",
        r_multiple_base=r_base,
        actual_rr_after_adjustment=round(actual_rr, 4),
        distance=round(abs(target - planned_entry), 4),
        constrained_by_structure=False,
    )


def test_risk_reward_acceptance():
    planned_entry = 65000.0
    stop_loss = StopLossPlan(
        price=64000.0,
        distance=1000.0,
        distance_atr=2.5,
        reason="Swing Low",
        structural_reference_level=64200.0,
        atr_buffer_used=0.5,
    )
    take_profits = TakeProfitPlan(
        tp1=make_tp_detail(66250.0, planned_entry, 1000.0, 1.25),
        tp2=make_tp_detail(67000.0, planned_entry, 1000.0, 2.00),
        tp3=make_tp_detail(68000.0, planned_entry, 1000.0, 3.00),
    )

    summary = RiskPlanner.evaluate_risk_reward(planned_entry, stop_loss, take_profits)
    assert summary.is_acceptable is True
    assert summary.tp1_rr == 1.25
    assert summary.tp2_rr == 2.00
    assert summary.tp3_rr == 3.00


def test_risk_reward_rejection_tp1_below_minimum():
    planned_entry = 65000.0
    stop_loss = StopLossPlan(
        price=64000.0,
        distance=1000.0,
        distance_atr=2.5,
        reason="Swing Low",
        atr_buffer_used=0.5,
    )
    # TP1 is structurally capped at 66100 (1.10R < 1.20R minimum)
    take_profits = TakeProfitPlan(
        tp1=make_tp_detail(66100.0, planned_entry, 1000.0, 1.25),
        tp2=make_tp_detail(67000.0, planned_entry, 1000.0, 2.00),
        tp3=make_tp_detail(68000.0, planned_entry, 1000.0, 3.00),
    )

    summary = RiskPlanner.evaluate_risk_reward(planned_entry, stop_loss, take_profits)
    assert summary.is_acceptable is False
    assert "Insufficient structural reward" in summary.rejection_reason


def test_mathematical_rr_reconstruction_invariant():
    planned_entry = 65432.10
    stop_price = 64987.65
    risk_dist = abs(planned_entry - stop_price)

    tp1_target = 66000.00
    tp2_target = 66500.00
    tp3_target = 67000.00

    tp1_detail = make_tp_detail(tp1_target, planned_entry, risk_dist, 1.25)
    tp2_detail = make_tp_detail(tp2_target, planned_entry, risk_dist, 2.00)
    tp3_detail = make_tp_detail(tp3_target, planned_entry, risk_dist, 3.00)

    # Invariant formula
    calculated_rr1 = abs(tp1_target - planned_entry) / risk_dist
    assert abs(tp1_detail.actual_rr_after_adjustment - calculated_rr1) < 1e-4
