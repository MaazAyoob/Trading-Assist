"""
Phase 9 — Live Performance Statistics Aggregator.
Calculates statistical distributions and sample size adequacy for live shadow signals.
"""

from typing import List, Dict, Tuple
import numpy as np

from app.shadow_validation.models import ShadowSignal, CandidateLiveMetrics, HorizonStatusEnum
from app.shadow_validation.config import CANDIDATES


class LiveStatisticsAggregator:
    """
    Computes statistical aggregates for each candidate stream during shadow validation.
    """

    @classmethod
    def aggregate_candidate_metrics(
        cls,
        candidate_id: str,
        signals: List[ShadowSignal],
        session_duration_days: float = 1.0,
    ) -> CandidateLiveMetrics:
        c_name = CANDIDATES.get(candidate_id, {}).get("name", candidate_id)
        c_signals = [s for s in signals if s.candidate_id == candidate_id]
        total_sig = len(c_signals)

        if total_sig == 0:
            return CandidateLiveMetrics(
                candidate_id=candidate_id,
                candidate_name=c_name,
                total_signals=0,
                sample_status="INSUFFICIENT_SAMPLE",
            )

        long_sigs = [s for s in c_signals if s.direction == "LONG_SETUP"]
        short_sigs = [s for s in c_signals if s.direction == "SHORT_SETUP"]

        # Sample size status determination
        if total_sig < 10:
            sample_status = "INSUFFICIENT_SAMPLE"
        elif total_sig < 30:
            sample_status = "SMALL_SAMPLE"
        else:
            sample_status = "ADEQUATE_SAMPLE"

        # Count pending, completed, and insufficient outcomes
        pending_cnt = 0
        completed_cnt = 0
        insufficient_cnt = 0

        for s in c_signals:
            for outcome in s.outcomes.values():
                if outcome.status == HorizonStatusEnum.PENDING:
                    pending_cnt += 1
                elif outcome.status == HorizonStatusEnum.COMPLETE:
                    completed_cnt += 1
                elif outcome.status == HorizonStatusEnum.INSUFFICIENT_HORIZON:
                    insufficient_cnt += 1

        # Extract completed returns per horizon
        def get_horizon_returns(h: int, subset: List[ShadowSignal] = None) -> List[float]:
            pool = subset if subset is not None else c_signals
            res = []
            for s in pool:
                o = s.outcomes.get(h)
                if o and o.status == HorizonStatusEnum.COMPLETE and o.raw_analytical_return is not None:
                    res.append(o.raw_analytical_return)
            return res

        h1_rets = get_horizon_returns(1)
        h3_rets = get_horizon_returns(3)
        h5_rets = get_horizon_returns(5)
        h10_rets = get_horizon_returns(10)
        h20_rets = get_horizon_returns(20)

        h5_long = get_horizon_returns(5, long_sigs)
        h5_short = get_horizon_returns(5, short_sigs)

        # MFE / MAE for 5C
        h5_mfes = [s.outcomes[5].mfe for s in c_signals if 5 in s.outcomes and s.outcomes[5].mfe is not None]
        h5_maes = [s.outcomes[5].mae for s in c_signals if 5 in s.outcomes and s.outcomes[5].mae is not None]

        h5_pos_rate = float(np.mean(np.array(h5_rets) > 1e-4) * 100) if h5_rets else 0.0
        h10_pos_rate = float(np.mean(np.array(h10_rets) > 1e-4) * 100) if h10_rets else 0.0

        med_5c = float(np.median(h5_rets)) if h5_rets else 0.0

        # Clustering & persistence
        adjacent_rate, episodes = cls._compute_clustering(c_signals)

        return CandidateLiveMetrics(
            candidate_id=candidate_id,
            candidate_name=c_name,
            total_signals=total_sig,
            long_count=len(long_sigs),
            short_count=len(short_sigs),
            signals_per_day=round(total_sig / max(0.01, session_duration_days), 2),
            pending_outcomes_count=pending_cnt,
            completed_outcomes_count=completed_cnt,
            incomplete_horizons_count=insufficient_cnt,
            sample_status=sample_status,
            h1_median_raw=round(float(np.median(h1_rets)) if h1_rets else 0.0, 6),
            h3_median_raw=round(float(np.median(h3_rets)) if h3_rets else 0.0, 6),
            h5_median_raw=round(med_5c, 6),
            h10_median_raw=round(float(np.median(h10_rets)) if h10_rets else 0.0, 6),
            h20_median_raw=round(float(np.median(h20_rets)) if h20_rets else 0.0, 6),
            h5_positive_rate=round(h5_pos_rate, 2),
            h10_positive_rate=round(h10_pos_rate, 2),
            h5_mfe_median=round(float(np.median(h5_mfes)) if h5_mfes else 0.0, 6),
            h5_mae_median=round(float(np.median(h5_maes)) if h5_maes else 0.0, 6),
            h5_median_cost_5bps=round(med_5c - 0.0005, 6),
            h5_median_cost_10bps=round(med_5c - 0.0010, 6),
            long_5c_median=round(float(np.median(h5_long)) if h5_long else 0.0, 6),
            short_5c_median=round(float(np.median(h5_short)) if h5_short else 0.0, 6),
            adjacent_signal_rate=round(adjacent_rate, 2),
            independent_episodes_count=episodes,
        )

    @staticmethod
    def _compute_clustering(signals: List[ShadowSignal]) -> Tuple[float, int]:
        if len(signals) < 2:
            return 0.0, len(signals)

        indices = [s.candle_index for s in signals]
        diffs = np.diff(indices)
        adj_rate = float(np.mean(diffs == 1) * 100)

        episodes = 0
        cur_dir = None
        for s in signals:
            if s.direction != cur_dir:
                episodes += 1
                cur_dir = s.direction

        return adj_rate, max(1, episodes)
