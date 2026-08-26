"""
Phase 9 — Observational Drift Monitor.
Compares live observed candidate behavior against Phase 8 historical Validation & Test benchmarks.
"""

from typing import List, Dict
from app.shadow_validation.models import (
    CandidateLiveMetrics,
    DriftMetricComparison,
    DriftStatusEnum,
)
from app.shadow_validation.config import HISTORICAL_BENCHMARKS


class DriftMonitor:
    """
    Evaluates empirical drift between live shadow signals and historical baseline/candidate expectations.
    """

    @classmethod
    def evaluate_candidate_drift(
        cls,
        metrics: CandidateLiveMetrics,
    ) -> List[DriftMetricComparison]:
        c_id = metrics.candidate_id
        hist = HISTORICAL_BENCHMARKS.get(c_id, {})
        if not hist:
            return []

        results: List[DriftMetricComparison] = []

        # 1. 5C Median Return Drift
        h_val_5c = hist.get("validation_5c_median", 0.0)
        h_test_5c = hist.get("test_5c_median", 0.0)
        live_5c = metrics.h5_median_raw

        delta_5c = live_5c - h_test_5c

        if metrics.total_signals < 10:
            status_5c = DriftStatusEnum.INSUFFICIENT_SAMPLE
        elif abs(delta_5c) <= 0.0005:  # Within 5 bps
            status_5c = DriftStatusEnum.ALIGNED
        elif abs(delta_5c) <= 0.0015:  # Within 15 bps
            status_5c = DriftStatusEnum.MILD_DRIFT
        else:
            status_5c = DriftStatusEnum.SIGNIFICANT_DRIFT

        results.append(DriftMetricComparison(
            candidate_id=c_id,
            metric_name="5-Candle Median Return",
            historical_validation=round(h_val_5c, 6),
            historical_test=round(h_test_5c, 6),
            live_observed=round(live_5c, 6),
            drift_delta=round(delta_5c, 6),
            drift_status=status_5c,
            details=f"Live 5C return is {live_5c*100:+.3f}% vs Untouched Test {h_test_5c*100:+.3f}% (Delta: {delta_5c*100:+.3f}%).",
        ))

        # 2. 5C Positive Outcome Rate Drift
        h_val_pos = hist.get("validation_5c_pos_rate", 0.0)
        h_test_pos = hist.get("test_5c_pos_rate", 0.0)
        live_pos = metrics.h5_positive_rate
        delta_pos = live_pos - h_test_pos

        if metrics.total_signals < 10:
            status_pos = DriftStatusEnum.INSUFFICIENT_SAMPLE
        elif abs(delta_pos) <= 5.0:
            status_pos = DriftStatusEnum.ALIGNED
        elif abs(delta_pos) <= 12.0:
            status_pos = DriftStatusEnum.MILD_DRIFT
        else:
            status_pos = DriftStatusEnum.SIGNIFICANT_DRIFT

        results.append(DriftMetricComparison(
            candidate_id=c_id,
            metric_name="5-Candle Positive Rate (%)",
            historical_validation=round(h_val_pos, 2),
            historical_test=round(h_test_pos, 2),
            live_observed=round(live_pos, 2),
            drift_delta=round(delta_pos, 2),
            drift_status=status_pos,
            details=f"Live 5C win rate is {live_pos:.1f}% vs Untouched Test {h_test_pos:.1f}% (Delta: {delta_pos:+.1f}%).",
        ))

        # 3. Adjacent Bar Clustering Drift
        h_clust = hist.get("adjacent_clustering", 0.0)
        live_clust = metrics.adjacent_signal_rate
        delta_clust = live_clust - h_clust

        if metrics.total_signals < 10:
            status_clust = DriftStatusEnum.INSUFFICIENT_SAMPLE
        elif abs(delta_clust) <= 10.0:
            status_clust = DriftStatusEnum.ALIGNED
        elif abs(delta_clust) <= 20.0:
            status_clust = DriftStatusEnum.MILD_DRIFT
        else:
            status_clust = DriftStatusEnum.SIGNIFICANT_DRIFT

        results.append(DriftMetricComparison(
            candidate_id=c_id,
            metric_name="Adjacent Bar Clustering (%)",
            historical_validation=round(h_clust, 2),
            historical_test=round(h_clust, 2),
            live_observed=round(live_clust, 2),
            drift_delta=round(delta_clust, 2),
            drift_status=status_clust,
            details=f"Live clustering is {live_clust:.1f}% vs Expected {h_clust:.1f}%.",
        ))

        return results
