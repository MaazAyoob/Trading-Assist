"""
Phase 8 — Strategy Research Registry & Disk Persistence.
Stores, caches, and retrieves experiment evaluations and comparison artifacts.
"""

import os
import json
from typing import Dict, Optional, List
from app.strategy_research.models import ExperimentEvaluation, BaselineComparisonItem, ExperimentComparisonReport
from app.core.logging import logger

RESEARCH_DATA_DIR = "data/research"
REGISTRY_FILE = os.path.join(RESEARCH_DATA_DIR, "experiment_registry.json")


class ResearchRegistry:
    """
    Persistent store for Phase 8 research experiment evaluations.
    """

    _CACHE: Optional[Dict[str, ExperimentEvaluation]] = None

    @classmethod
    def get_all_experiments(cls) -> Dict[str, ExperimentEvaluation]:
        if cls._CACHE is not None:
            return cls._CACHE

        os.makedirs(RESEARCH_DATA_DIR, exist_ok=True)
        if os.path.exists(REGISTRY_FILE):
            try:
                with open(REGISTRY_FILE, "r") as f:
                    raw = json.load(f)
                    cls._CACHE = {k: ExperimentEvaluation(**v) for k, v in raw.items()}
                    return cls._CACHE
            except Exception as e:
                logger.warning(f"Failed to load research registry from disk: {e}")

        return {}

    @classmethod
    def save_all_experiments(cls, evaluations: Dict[str, ExperimentEvaluation]):
        cls._CACHE = evaluations
        os.makedirs(RESEARCH_DATA_DIR, exist_ok=True)
        try:
            with open(REGISTRY_FILE, "w") as f:
                payload = {k: v.model_dump() for k, v in evaluations.items()}
                json.dump(payload, f, indent=2)
            logger.info(f"ResearchRegistry: Persisted {len(evaluations)} experiments to {REGISTRY_FILE}")
        except Exception as e:
            logger.error(f"Failed to persist research registry: {e}")

    @classmethod
    def get_experiment(cls, exp_id: str) -> Optional[ExperimentEvaluation]:
        exps = cls.get_all_experiments()
        return exps.get(exp_id)

    @classmethod
    def generate_comparison(cls, exp_id: str, partition: str = "VALIDATION") -> Optional[ExperimentComparisonReport]:
        exps = cls.get_all_experiments()
        baseline = exps.get("BASELINE")
        exp = exps.get(exp_id)

        if not baseline or not exp:
            return None

        if partition == "VALIDATION":
            b_m = baseline.validation_metrics
            c_m = exp.validation_metrics
        elif partition == "TEST":
            b_m = baseline.test_metrics or baseline.validation_metrics
            c_m = exp.test_metrics or exp.validation_metrics
        else:
            b_m = baseline.train_metrics
            c_m = exp.train_metrics

        comparisons = [
            BaselineComparisonItem(
                metric_name="Signal Count",
                baseline_val=f"{b_m.signal_count:,}",
                candidate_val=f"{c_m.signal_count:,}",
                delta_str=f"{c_m.signal_count - b_m.signal_count:+,}",
                improved=(c_m.signal_count < b_m.signal_count),
                description="Signal reduction reflects elimination of clustered redundant triggers.",
            ),
            BaselineComparisonItem(
                metric_name="5-Candle Median Return",
                baseline_val=f"{b_m.h5_median * 100:+.3f}%",
                candidate_val=f"{c_m.h5_median * 100:+.3f}%",
                delta_str=f"{(c_m.h5_median - b_m.h5_median) * 100:+.3f}%",
                improved=(c_m.h5_median > b_m.h5_median),
                description="Primary outcome metric: forward directional performance over 75 minutes.",
            ),
            BaselineComparisonItem(
                metric_name="5-Candle Positive Rate",
                baseline_val=f"{b_m.positive_rate_5c:.1f}%",
                candidate_val=f"{c_m.positive_rate_5c:.1f}%",
                delta_str=f"{c_m.positive_rate_5c - b_m.positive_rate_5c:+.1f}%",
                improved=(c_m.positive_rate_5c > b_m.positive_rate_5c),
                description="Percentage of signals experiencing positive forward price movement.",
            ),
            BaselineComparisonItem(
                metric_name="Pre-Signal 5C Extension",
                baseline_val=f"{b_m.timing.pre_5_median * 100:+.3f}%",
                candidate_val=f"{c_m.timing.pre_5_median * 100:+.3f}%",
                delta_str=f"{(c_m.timing.pre_5_median - b_m.timing.pre_5_median) * 100:+.3f}%",
                improved=(c_m.timing.pre_5_median < b_m.timing.pre_5_median),
                description="Lower pre-signal extension indicates reduced trend-chasing behavior.",
            ),
            BaselineComparisonItem(
                metric_name="Adjacent Bar Clustering (dt=1)",
                baseline_val=f"{b_m.clustering.adjacent_signal_rate:.1f}%",
                candidate_val=f"{c_m.clustering.adjacent_signal_rate:.1f}%",
                delta_str=f"{c_m.clustering.adjacent_signal_rate - b_m.clustering.adjacent_signal_rate:+.1f}%",
                improved=(c_m.clustering.adjacent_signal_rate < b_m.clustering.adjacent_signal_rate),
                description="Reduction in back-to-back repetitive triggers across adjacent candles.",
            ),
            BaselineComparisonItem(
                metric_name="Score Monotonicity Grade",
                baseline_val=b_m.score_monotonicity_grade,
                candidate_val=c_m.score_monotonicity_grade,
                delta_str=f"{c_m.score_monotonicity_grade} (r={c_m.score_spearman_corr:+.3f})",
                improved=(c_m.score_monotonicity_grade != "INVERSE"),
                description="Monotonicity ordering between conviction score and forward returns.",
            ),
        ]

        obs_facts = [
            f"Candidate signal frequency on {partition} is {c_m.signal_count:,} signals vs baseline {b_m.signal_count:,}.",
            f"5C median return is {c_m.h5_median * 100:+.3f}% vs baseline {b_m.h5_median * 100:+.3f}%.",
            f"Adjacent bar clustering is {c_m.clustering.adjacent_signal_rate:.1f}% vs baseline {b_m.clustering.adjacent_signal_rate:.1f}%.",
        ]

        poss_exps = [
            f"Filter discipline reduces late-stage impulse chasing by restricting setup entry conditions.",
            f"Eliminating multi-bar repetition compresses trailing signals into localized entry episodes.",
        ]

        unproven_hyps = [
            f"Further combining dynamic volatility-adjusted ATR bands may further refine entry precision.",
        ]

        return ExperimentComparisonReport(
            experiment_id=exp_id,
            experiment_name=exp.experiment_name,
            baseline_id="PHASE5_V0.5.0",
            status=exp.status,
            partition_evaluated=partition,
            comparisons=comparisons,
            promotion_status=exp.status.value,
            summary_observed_facts=obs_facts,
            summary_possible_explanations=poss_exps,
            summary_unproven_hypotheses=unproven_hyps,
        )
