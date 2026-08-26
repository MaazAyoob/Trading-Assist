"""
Phase 8 — Strategy Research Performance Evaluator.
Computes complete statistical, timing, clustering, score calibration, and cost metrics.
"""

from typing import List, Dict, Tuple, Optional, Any
import numpy as np

from app.strategy_research.models import (
    PartitionPerformanceMetrics,
    PartitionTimingMetrics,
    PartitionClusteringMetrics,
)
from app.forensics.models import ScoreTraceRecord


class StrategyEvaluator:
    """
    Computes rigorous statistical evaluation across chronological data partitions.
    """

    @classmethod
    def evaluate_partition(
        cls,
        partition_name: str,
        start_ts: int,
        end_ts: int,
        candle_count: int,
        traces: List[ScoreTraceRecord],
    ) -> PartitionPerformanceMetrics:
        # Filter traces to partition window
        p_traces = [t for t in traces if start_ts <= t.timestamp <= end_ts]
        n_sig = len(p_traces)
        days = max(1.0, (end_ts - start_ts) / (1000.0 * 86400.0))

        if n_sig == 0:
            return PartitionPerformanceMetrics(
                partition_name=partition_name,
                start_timestamp=start_ts,
                end_timestamp=end_ts,
                candle_count=candle_count,
                signal_count=0,
                long_count=0,
                short_count=0,
                signals_per_day=0.0,
                signals_per_100_candles=0.0,
                sample_warning="INSUFFICIENT_SAMPLE",
            )

        long_traces = [t for t in p_traces if t.direction == "LONG_SETUP"]
        short_traces = [t for t in p_traces if t.direction == "SHORT_SETUP"]
        l_cnt, s_cnt = len(long_traces), len(short_traces)

        # Forward analytical returns
        h1_arr = np.array([t.post_returns.get(1, 0.0) for t in p_traces])
        h3_arr = np.array([t.post_returns.get(3, 0.0) for t in p_traces])
        h5_arr = np.array([t.post_returns.get(5, 0.0) for t in p_traces])
        h10_arr = np.array([t.post_returns.get(10, 0.0) for t in p_traces])
        h20_arr = np.array([t.post_returns.get(20, 0.0) for t in p_traces])

        # Long vs Short breakdown
        l_h5 = np.array([t.post_returns.get(5, 0.0) for t in long_traces]) if long_traces else np.array([0.0])
        s_h5 = np.array([t.post_returns.get(5, 0.0) for t in short_traces]) if short_traces else np.array([0.0])
        l_h10 = np.array([t.post_returns.get(10, 0.0) for t in long_traces]) if long_traces else np.array([0.0])
        s_h10 = np.array([t.post_returns.get(10, 0.0) for t in short_traces]) if short_traces else np.array([0.0])
        l_h20 = np.array([t.post_returns.get(20, 0.0) for t in long_traces]) if long_traces else np.array([0.0])
        s_h20 = np.array([t.post_returns.get(20, 0.0) for t in short_traces]) if short_traces else np.array([0.0])

        pos_5c = float(np.mean(h5_arr > 1e-4) * 100)
        pos_10c = float(np.mean(h10_arr > 1e-4) * 100)

        # Cost sensitivity (0 bps, 5 bps = 0.0005, 10 bps = 0.0010)
        med_5c = float(np.median(h5_arr))
        cost_0 = med_5c
        cost_5 = med_5c - 0.0005
        cost_10 = med_5c - 0.0010

        # Timing metrics (Pre vs Post)
        pre_1 = float(np.median([t.pre_returns.get(1, 0.0) for t in p_traces]))
        pre_3 = float(np.median([t.pre_returns.get(3, 0.0) for t in p_traces]))
        pre_5 = float(np.median([t.pre_returns.get(5, 0.0) for t in p_traces]))
        pre_10 = float(np.median([t.pre_returns.get(10, 0.0) for t in p_traces]))
        pre_20 = float(np.median([t.pre_returns.get(20, 0.0) for t in p_traces]))

        post_1 = float(np.median(h1_arr))
        post_3 = float(np.median(h3_arr))
        post_5 = float(np.median(h5_arr))
        post_10 = float(np.median(h10_arr))
        post_20 = float(np.median(h20_arr))

        # Long pre vs post for trend-chasing flag
        l_pre5 = float(np.median([t.pre_returns.get(5, 0.0) for t in long_traces])) if long_traces else 0.0
        l_post5 = float(np.median(l_h5))
        is_trend_chasing = (l_pre5 > 0.0015 and l_post5 < 0.0)

        corr_5c = 0.0
        pre_arr5 = np.array([t.pre_returns.get(5, 0.0) for t in p_traces])
        if np.std(pre_arr5) > 1e-8 and np.std(h5_arr) > 1e-8:
            corr_5c = float(np.corrcoef(pre_arr5, h5_arr)[0, 1])

        timing = PartitionTimingMetrics(
            pre_1_median=round(pre_1, 6),
            pre_3_median=round(pre_3, 6),
            pre_5_median=round(pre_5, 6),
            pre_10_median=round(pre_10, 6),
            pre_20_median=round(pre_20, 6),
            post_1_median=round(post_1, 6),
            post_3_median=round(post_3, 6),
            post_5_median=round(post_5, 6),
            post_10_median=round(post_10, 6),
            post_20_median=round(post_20, 6),
            pre_vs_post_5c_corr=round(corr_5c, 4),
            trend_chasing_flag=is_trend_chasing,
            timing_diagnostic="REDUCED_EXTENSION" if l_pre5 < 0.0015 else ("TREND_CHASING" if is_trend_chasing else "NEUTRAL"),
        )

        # Clustering & Episodes
        clustering = cls._compute_clustering(p_traces)

        # Score Monotonicity
        mono_grade, mono_corr = cls._compute_score_monotonicity(p_traces)

        # Regime breakdown
        regime_breakdown = {}
        regimes = set(t.regime_at_signal for t in p_traces)
        for r in regimes:
            r_traces = [t for t in p_traces if t.regime_at_signal == r]
            if r_traces:
                r_rets = [t.post_returns.get(5, 0.0) for t in r_traces]
                regime_breakdown[r] = {
                    "count": len(r_traces),
                    "h5_median": round(float(np.median(r_rets)), 6),
                    "pos_rate": round(float(np.mean(np.array(r_rets) > 1e-4) * 100), 2),
                }

        warning = "INSUFFICIENT_SAMPLE" if n_sig < 10 else ("SMALL_SAMPLE" if n_sig < 30 else "VALID")

        return PartitionPerformanceMetrics(
            partition_name=partition_name,
            start_timestamp=start_ts,
            end_timestamp=end_ts,
            candle_count=candle_count,
            signal_count=n_sig,
            long_count=l_cnt,
            short_count=s_cnt,
            signals_per_day=round(n_sig / days, 2),
            signals_per_100_candles=round((n_sig / max(1, candle_count)) * 100, 2),
            h1_median=round(post_1, 6),
            h1_mean=round(float(np.mean(h1_arr)), 6),
            h3_median=round(post_3, 6),
            h3_mean=round(float(np.mean(h3_arr)), 6),
            h5_median=round(post_5, 6),
            h5_mean=round(float(np.mean(h5_arr)), 6),
            h10_median=round(post_10, 6),
            h10_mean=round(float(np.mean(h10_arr)), 6),
            h20_median=round(post_20, 6),
            h20_mean=round(float(np.mean(h20_arr)), 6),
            long_5c_median=round(float(np.median(l_h5)), 6),
            short_5c_median=round(float(np.median(s_h5)), 6),
            long_10c_median=round(float(np.median(l_h10)), 6),
            short_10c_median=round(float(np.median(s_h10)), 6),
            long_20c_median=round(float(np.median(l_h20)), 6),
            short_20c_median=round(float(np.median(s_h20)), 6),
            positive_rate_5c=round(pos_5c, 2),
            positive_rate_10c=round(pos_10c, 2),
            mfe_5c_median=round(float(np.median(h5_arr[h5_arr > 0])) if np.any(h5_arr > 0) else 0.0, 6),
            mae_5c_median=round(float(np.median(h5_arr[h5_arr < 0])) if np.any(h5_arr < 0) else 0.0, 6),
            h5_median_cost_0bps=round(cost_0, 6),
            h5_median_cost_5bps=round(cost_5, 6),
            h5_median_cost_10bps=round(cost_10, 6),
            timing=timing,
            clustering=clustering,
            score_monotonicity_grade=mono_grade,
            score_spearman_corr=round(mono_corr, 4),
            regime_breakdown=regime_breakdown,
            sample_warning=warning,
        )

    @staticmethod
    def _compute_clustering(traces: List[ScoreTraceRecord]) -> PartitionClusteringMetrics:
        tot = len(traces)
        if tot < 2:
            return PartitionClusteringMetrics(
                adjacent_signal_rate=0.0,
                signals_within_2_bars=0.0,
                signals_within_4_bars=0.0,
                signals_within_8_bars=0.0,
                independent_episodes_count=tot,
                avg_episode_length_bars=1.0,
                max_episode_length_bars=1,
            )

        indices = [t.candle_index for t in traces]
        intervals = np.diff(indices)

        within_1 = float(np.mean(intervals == 1) * 100)
        within_2 = float(np.mean(intervals <= 2) * 100)
        within_4 = float(np.mean(intervals <= 4) * 100)
        within_8 = float(np.mean(intervals <= 8) * 100)

        # Persistence runs
        runs = []
        cur_dir = None
        cur_len = 0
        for t in traces:
            if t.direction == cur_dir:
                cur_len += 1
            else:
                if cur_len > 0:
                    runs.append(cur_len)
                cur_dir = t.direction
                cur_len = 1
        if cur_len > 0:
            runs.append(cur_len)

        return PartitionClusteringMetrics(
            adjacent_signal_rate=round(within_1, 2),
            signals_within_2_bars=round(within_2, 2),
            signals_within_4_bars=round(within_4, 2),
            signals_within_8_bars=round(within_8, 2),
            independent_episodes_count=len(runs),
            avg_episode_length_bars=round(float(np.mean(runs)) if runs else 1.0, 2),
            max_episode_length_bars=int(max(runs)) if runs else 1,
        )

    @staticmethod
    def _compute_score_monotonicity(traces: List[ScoreTraceRecord]) -> Tuple[str, float]:
        if len(traces) < 10:
            return "NON_MONOTONIC", 0.0

        bins = [
            (40.0, 50.0),
            (50.0, 60.0),
            (60.0, 70.0),
            (70.0, 100.0),
        ]
        meds = []
        for lo, hi in bins:
            b_traces = [t for t in traces if lo <= t.net_score < hi or (hi == 100.0 and t.net_score == 100.0)]
            if b_traces:
                meds.append(float(np.median([t.post_returns.get(5, 0.0) for t in b_traces])))
            else:
                meds.append(0.0)

        if len(meds) >= 3 and np.std(meds) > 1e-8:
            corr = float(np.corrcoef(np.arange(len(meds)), np.array(meds))[0, 1])
        else:
            corr = 0.0

        if corr >= 0.85:
            grade = "MONOTONIC"
        elif corr >= 0.35:
            grade = "WEAKLY_MONOTONIC"
        elif corr <= -0.35:
            grade = "INVERSE"
        else:
            grade = "NON_MONOTONIC"

        return grade, corr
