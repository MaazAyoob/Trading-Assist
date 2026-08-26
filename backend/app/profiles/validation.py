"""
Validation utilities for Phase 12 Trading Profiles.
"""

from typing import Dict, List, Tuple
from app.data.schema import Candle
from app.profiles.models import TradingProfileConfig, MultiTimeframeContext, CostSensitivityTier


class ProfileValidator:
    @staticmethod
    def validate_data_sufficiency(candles: List[Candle], min_required: int = 60) -> Tuple[bool, str]:
        """Validates that sufficient closed candles exist for deterministic analysis."""
        if not candles:
            return False, "Candle series is empty"
        if len(candles) < min_required:
            return False, f"Insufficient candle history: {len(candles)}/{min_required} required"
        return True, "Data sufficiency verified"

    @staticmethod
    def validate_causal_alignment(context: MultiTimeframeContext) -> Tuple[bool, List[str]]:
        """Verifies strict causal alignment across primary and all context timeframes."""
        errors = []
        p_ts = context.analytical_timestamp

        for ctx_tf, candle in context.context_candles.items():
            if ctx_tf == context.primary_timeframe:
                continue
            if candle.timestamp > p_ts:
                errors.append(f"Causal violation on {ctx_tf}: candle timestamp {candle.timestamp} > primary {p_ts}")
            if not candle.is_closed and ctx_tf != context.primary_timeframe:
                errors.append(f"Context candle on {ctx_tf} is not closed")

        return len(errors) == 0, errors

    @staticmethod
    def evaluate_cost_sensitivity(
        raw_analytical_return_pct: float,
        cost_tiers_bps: List[int],
    ) -> List[CostSensitivityTier]:
        """
        Evaluates impact of transaction costs across declared bps tiers (0, 5, 10, 15 bps).
        Round-trip cost in pct = 2 * (cost_bps / 10000) * 100% = cost_bps * 0.02%.
        """
        results = []
        for bps in cost_tiers_bps:
            round_trip_cost_pct = (bps * 2.0) / 100.0  # e.g., 5 bps each way = 10 bps total = 0.10%
            net_return_pct = raw_analytical_return_pct - round_trip_cost_pct if raw_analytical_return_pct > 0 else raw_analytical_return_pct + round_trip_cost_pct
            cost_impact = round_trip_cost_pct
            is_viable = abs(raw_analytical_return_pct) > (round_trip_cost_pct * 1.5)

            warning = None
            if round_trip_cost_pct >= abs(raw_analytical_return_pct) * 0.5:
                warning = f"High cost drag: {bps} bps consumes >=50% of analytical return"

            results.append(
                CostSensitivityTier(
                    cost_bps=bps,
                    raw_analytical_return_pct=round(raw_analytical_return_pct, 4),
                    estimated_cost_adjusted_return_pct=round(net_return_pct, 4),
                    cost_impact_pct=round(cost_impact, 4),
                    is_cost_viable=is_viable,
                    warning_flag=warning,
                )
            )
        return results
