"""
Unit tests for SCALP Transaction Cost Sensitivity Evaluation (0, 5, 10, 15 bps).
"""

import pytest
from app.profiles.validation import ProfileValidator


def test_cost_sensitivity_tiers():
    raw_return = 0.80  # 80 bps movement (0.80%)
    tiers = ProfileValidator.evaluate_cost_sensitivity(
        raw_analytical_return_pct=raw_return,
        cost_tiers_bps=[0, 5, 10, 15],
    )

    assert len(tiers) == 4
    
    # 0 bps tier: round-trip = 0.00% -> net = 0.80%
    assert tiers[0].cost_bps == 0
    assert tiers[0].estimated_cost_adjusted_return_pct == 0.80
    assert tiers[0].is_cost_viable is True

    # 5 bps tier: round-trip = 0.10% -> net = 0.70%
    assert tiers[1].cost_bps == 5
    assert tiers[1].cost_impact_pct == 0.10
    assert tiers[1].estimated_cost_adjusted_return_pct == 0.70

    # 15 bps tier: round-trip = 0.30% -> net = 0.50%
    assert tiers[3].cost_bps == 15
    assert tiers[3].cost_impact_pct == 0.30
    assert tiers[3].estimated_cost_adjusted_return_pct == 0.50


def test_cost_warning_trigger_on_high_drag():
    low_movement = 0.15  # 15 bps movement
    tiers = ProfileValidator.evaluate_cost_sensitivity(
        raw_analytical_return_pct=low_movement,
        cost_tiers_bps=[0, 5, 10, 15],
    )

    # 10 bps tier = 0.20% cost >= 50% of 0.15% movement -> warning triggered
    assert tiers[2].warning_flag is not None
    assert "High cost drag" in tiers[2].warning_flag
