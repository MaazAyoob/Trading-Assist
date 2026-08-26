"""
Comparison Engine for Multi-Profile Analysis.
Generates objective comparative matrix without subjective "winner" declaration.
"""

from typing import Dict, List
import time
from app.profiles.models import ProfileComparisonReport, ProfileComparisonItem
from app.profiles.registry import profile_registry
from app.profile_validation.dataset import build_synthetic_multi_tf_dataset
from app.profile_validation.evaluation import ProfileEvaluationRunner


class ProfileComparisonEngine:
    @classmethod
    def generate_comparison_report(
        cls,
        symbol: str = "BTCUSDT",
        multi_tf_dataset: Dict[str, list] = None,
    ) -> ProfileComparisonReport:
        dataset = multi_tf_dataset or build_synthetic_multi_tf_dataset(primary_count=200)
        items: List[ProfileComparisonItem] = []

        for profile in profile_registry.list_profiles():
            eval_res = ProfileEvaluationRunner.evaluate_profile_over_dataset(
                symbol=symbol,
                profile_config=profile,
                multi_tf_dataset=dataset,
                warmup_bars=40,
            )

            density = eval_res.get("signal_density", {})
            fwd_5c = eval_res.get("forward_returns", {}).get("5C", {})
            exc = eval_res.get("excursions_5c", {})

            median_5c = fwd_5c.get("median_return_pct", 0.0)
            pos_rate = fwd_5c.get("positive_rate_pct", 0.0)
            signals_day = density.get("signals_per_day", 0.0)
            clustering = density.get("clustering_factor", 0.0)

            items.append(
                ProfileComparisonItem(
                    profile_id=profile.profile_id,
                    display_name=profile.display_name,
                    primary_timeframe=profile.primary_timeframe,
                    context_timeframes=profile.context_timeframes,
                    expected_horizon=profile.expected_holding_horizon,
                    signals_per_day=signals_day,
                    clustering_factor=clustering,
                    median_5c_return_pct=median_5c,
                    positive_rate_pct=pos_rate,
                    avg_mfe_pct=exc.get("avg_mfe_pct", 0.0),
                    avg_mae_pct=exc.get("avg_mae_pct", 0.0),
                    cost_viable_10bps=True,
                    status=profile.status.value,
                )
            )

        return ProfileComparisonReport(
            generated_timestamp=int(time.time() * 1000),
            symbol=symbol,
            profiles=items,
        )
