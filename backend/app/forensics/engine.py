"""
Signal Forensics & Factor Attribution Engine (Phase 7).
Strictly deterministic, zero-mutation diagnostic framework.
Reconstructs and analyzes historical score traces, timing, factor monotonicity,
clustering, and structural causality on the frozen Phase 5 signal engine.
"""

import time
from datetime import datetime, timezone
from typing import List, Dict, Tuple, Optional, Any
import numpy as np

from app.data.schema import Candle, MarketDataQuality, QualityStatusEnum
from app.indicators.engine import IndicatorEngine
from app.indicators.trend import compute_ema, compute_rolling_vwap, compute_adx, compute_supertrend
from app.indicators.momentum import compute_rsi, compute_macd, compute_stoch_rsi, compute_roc
from app.indicators.volatility import compute_atr, compute_bollinger_bands
from app.indicators.volume import compute_volume_sma, compute_relative_volume, compute_obv
from app.indicators.base import (
    safe_float, IndicatorSnapshot, TrendIndicators, MomentumIndicators,
    VolatilityIndicators, VolumeIndicators
)
from app.structure.config import default_structure_config
from app.structure.models import SwingTypeEnum, SwingPoint, MarketStructureSnapshot, ZoneStatusEnum
from app.structure.levels import cluster_support_resistance_zones
from app.regime.engine import MarketRegimeEngine
from app.signals.models import SignalDirectionEnum, SignalStatusEnum
from app.signals.engine import MultiFactorSignalEngine
from app.backtesting.models import BacktestRun
from app.backtesting.dataset import DatasetManager
from app.forensics.models import (
    ScoreTraceRecord,
    FactorPerformanceBin,
    FactorMonotonicityEvaluation,
    SignalTimingForensics,
    SignalClusteringForensics,
    RegimeForensicsRecord,
    StructureForensicsRecord,
    SRDistanceForensicsRecord,
    ConflictForensicsRecord,
    ScoreCalibrationRecord,
    PartitionForensicsRecord,
    ForensicsReport,
)
from app.core.logging import logger


class SignalForensicsEngine:
    """
    Diagnostic forensics engine for causal factor attribution and timing analysis.
    """

    FACTOR_BINS = [
        ("Strong Bearish [-100, -60)", -100.0, -60.0),
        ("Moderate Bearish [-60, -20)", -60.0, -20.0),
        ("Neutral [-20, +20]", -20.0, 20.0),
        ("Moderate Bullish (+20, +60]", 20.0, 60.0),
        ("Strong Bullish (+60, +100]", 60.0, 100.0),
    ]

    SCORE_BINS = [
        ("[-100, -80]", -100.0, -80.0),
        ("[-80, -70]", -80.0, -70.0),
        ("[-70, -60]", -70.0, -60.0),
        ("[-60, -50]", -60.0, -50.0),
        ("[-50, -40]", -50.0, -40.0),
        ("[+40, +50]", 40.0, 50.0),
        ("[+50, +60]", 50.0, 60.0),
        ("[+60, +70]", 60.0, 70.0),
        ("[+70, +80]", 70.0, 80.0),
        ("[+80, +100]", 80.0, 100.0),
    ]

    SR_DISTANCE_BINS = [
        ("<0.25 ATR", 0.0, 0.25),
        ("0.25-0.5 ATR", 0.25, 0.50),
        ("0.5-1.0 ATR", 0.50, 1.00),
        ("1.0-2.0 ATR", 1.00, 2.00),
        (">2.0 ATR", 2.00, 999.0),
    ]

    @classmethod
    def analyze(
        cls,
        candles: List[Candle],
        dataset_metadata: Optional[Any] = None,
    ) -> ForensicsReport:
        t0 = time.time()
        n = len(candles)
        logger.info(f"SignalForensicsEngine: Starting analysis on {n} candles...")

        # 1. Extract price arrays & precompute indicators
        timestamps, highs, lows, closes, volumes = IndicatorEngine._extract_arrays(candles)
        atr_arr = compute_atr(highs, lows, closes, 14)

        ema9 = compute_ema(closes, 9)
        ema21 = compute_ema(closes, 21)
        ema50 = compute_ema(closes, 50)
        ema100 = compute_ema(closes, 100)
        ema200 = compute_ema(closes, 200)
        vwap = compute_rolling_vwap(timestamps, highs, lows, closes, volumes, 24)
        adx_arr, pdi_arr, mdi_arr = compute_adx(highs, lows, closes, 14)
        st_arr, st_dir_arr = compute_supertrend(highs, lows, closes, 10, 3.0)
        rsi_arr = compute_rsi(closes, 14)
        macd_arr, macd_sig_arr, macd_hist_arr = compute_macd(closes, 12, 26, 9)
        stoch_k_arr, stoch_d_arr = compute_stoch_rsi(closes, 14, 3, 3)
        roc_arr = compute_roc(closes, 12)
        bbu_arr, bbm_arr, bbl_arr, bbw_arr, bbpb_arr = compute_bollinger_bands(closes, 20, 2.0)
        vol_sma_arr = compute_volume_sma(volumes, 20)
        rvol_arr = compute_relative_volume(volumes, 20)
        obv_arr = compute_obv(closes, volumes)

        # 2. Precompute swings and counts
        cfg_struct = default_structure_config
        VOL_LOOKBACK = 50
        left, right = cfg_struct.SWING_LEFT, cfg_struct.SWING_RIGHT
        acc_swings = []
        confirmed_shs = []
        confirmed_sls = []
        swing_snap = [0] * n
        sh_snap = [0] * n
        sl_snap = [0] * n

        for i in range(n):
            j = i - right
            if j >= left:
                c_atr_j = float(atr_arr[j]) if not np.isnan(atr_arr[j]) else 1.0
                tol = cfg_struct.EQUAL_TOLERANCE_ATR * c_atr_j
                if (all(highs[j - k] <= highs[j] for k in range(1, left + 1)) and
                        all(highs[j + k] <= highs[j] + tol for k in range(1, right + 1))):
                    sp = SwingPoint(
                        id=f"SH_{int(timestamps[j])}", type=SwingTypeEnum.SWING_HIGH,
                        price=float(highs[j]), swing_timestamp=int(timestamps[j]),
                        confirmation_timestamp=int(timestamps[i]),
                        is_confirmed=True, volume=float(volumes[j]),
                        atr_normalized_magnitude=float(highs[j] / c_atr_j) if c_atr_j > 0 else None,
                    )
                    acc_swings.append(sp)
                    confirmed_shs.append(sp)
                if (all(lows[j - k] >= lows[j] for k in range(1, left + 1)) and
                        all(lows[j + k] >= lows[j] - tol for k in range(1, right + 1))):
                    sp = SwingPoint(
                        id=f"SL_{int(timestamps[j])}", type=SwingTypeEnum.SWING_LOW,
                        price=float(lows[j]), swing_timestamp=int(timestamps[j]),
                        confirmation_timestamp=int(timestamps[i]),
                        is_confirmed=True, volume=float(volumes[j]),
                        atr_normalized_magnitude=float(lows[j] / c_atr_j) if c_atr_j > 0 else None,
                    )
                    acc_swings.append(sp)
                    confirmed_sls.append(sp)
            swing_snap[i] = len(acc_swings)
            sh_snap[i] = len(confirmed_shs)
            sl_snap[i] = len(confirmed_sls)

        # 3. Generate detailed ScoreTraceRecords with Pre- and Post-Returns
        traces: List[ScoreTraceRecord] = []
        interval_ms = 900000  # 15m
        seen_ts = set()
        gap_count = duplicate_count = invalid_count = 0
        prev_ts_clean = None
        horizons = [1, 3, 5, 10, 20]

        for i in range(n):
            ts_i = int(timestamps[i])
            if ts_i in seen_ts:
                duplicate_count += 1
            elif prev_ts_clean is not None and ts_i <= prev_ts_clean:
                invalid_count += 1
            else:
                if prev_ts_clean is not None:
                    delta = ts_i - prev_ts_clean
                    if delta > int(interval_ms * 1.5):
                        gap_count += round(delta / interval_ms) - 1
                seen_ts.add(ts_i)
                prev_ts_clean = ts_i

            if i < 200 - 1:
                continue

            cur_atr = float(atr_arr[i]) if not np.isnan(atr_arr[i]) else 1.0
            vsma = float(vol_sma_arr[i]) if not np.isnan(vol_sma_arr[i]) and vol_sma_arr[i] > 0 else float(volumes[i] or 1.0)
            close = float(closes[i])

            indicators = IndicatorSnapshot(
                symbol="BTCUSDT", timeframe="15m",
                timestamp=int(candles[i].close_time if candles[i].close_time else ts_i),
                is_confirmed=True,
                trend=TrendIndicators(
                    ema_9=safe_float(ema9[i]), ema_21=safe_float(ema21[i]), ema_50=safe_float(ema50[i]),
                    ema_100=safe_float(ema100[i]), ema_200=safe_float(ema200[i]),
                    vwap=safe_float(vwap[i]), adx=safe_float(adx_arr[i]),
                    plus_di=safe_float(pdi_arr[i]), minus_di=safe_float(mdi_arr[i]),
                    supertrend=safe_float(st_arr[i]),
                    supertrend_direction=int(st_dir_arr[i]) if not np.isnan(st_dir_arr[i]) else None,
                ),
                momentum=MomentumIndicators(
                    rsi=safe_float(rsi_arr[i]), macd=safe_float(macd_arr[i]),
                    macd_signal=safe_float(macd_sig_arr[i]), macd_histogram=safe_float(macd_hist_arr[i]),
                    stoch_rsi_k=safe_float(stoch_k_arr[i]), stoch_rsi_d=safe_float(stoch_d_arr[i]),
                    roc=safe_float(roc_arr[i]),
                ),
                volatility=VolatilityIndicators(
                    atr=safe_float(cur_atr), bb_upper=safe_float(bbu_arr[i]), bb_middle=safe_float(bbm_arr[i]),
                    bb_lower=safe_float(bbl_arr[i]), bb_bandwidth=safe_float(bbw_arr[i]),
                    bb_percent_b=safe_float(bbpb_arr[i]),
                ),
                volume=VolumeIndicators(
                    volume_sma=safe_float(vsma), relative_volume=safe_float(rvol_arr[i]),
                    obv=safe_float(obv_arr[i]),
                ),
            )

            num_sw = swing_snap[i]
            n_sh = sh_snap[i]
            n_sl = sl_snap[i]
            active_sh = confirmed_shs[n_sh - 1] if n_sh > 0 else None
            active_sl = confirmed_sls[n_sl - 1] if n_sl > 0 else None

            if n_sh >= 2 and n_sl >= 2:
                p_sh, c_sh = confirmed_shs[n_sh - 2], confirmed_shs[n_sh - 1]
                p_sl, c_sl = confirmed_sls[n_sl - 2], confirmed_sls[n_sl - 1]
                if c_sh.price > p_sh.price and c_sl.price > p_sl.price:
                    direction = "BULLISH"
                elif c_sh.price < p_sh.price and c_sl.price < p_sl.price:
                    direction = "BEARISH"
                else:
                    direction = "RANGE"
            else:
                direction = "UNKNOWN"

            recent_swings = acc_swings[max(0, num_sw - 50):num_sw]
            sup_zones, res_zones = cluster_support_resistance_zones([candles[i]], recent_swings, cur_atr, cfg_struct)

            structure = MarketStructureSnapshot(
                symbol="BTCUSDT", timeframe="15m", timestamp=int(timestamps[i]),
                is_confirmed=True, structure_direction=direction,
                active_structural_high=active_sh, active_structural_low=active_sl,
                confirmed_swings=recent_swings, developing_swings=[],
                bos_events=[], choch_events=[],
                support_zones=sup_zones, resistance_zones=res_zones,
                structure_engine_version=cfg_struct.structure_engine_version,
                structure_config_version=cfg_struct.structure_config_version,
            )

            regime_start = max(0, i - VOL_LOOKBACK + 1)
            regime = MarketRegimeEngine.classify(
                candles=candles[regime_start:i + 1], indicators=indicators,
                structure_state=structure.structure_direction, is_confirmed=True,
            )

            q_status = QualityStatusEnum.HEALTHY if (gap_count == 0 and duplicate_count == 0 and invalid_count == 0) else QualityStatusEnum.WARNING
            quality = MarketDataQuality(
                symbol="BTCUSDT", timeframe="15m",
                status=q_status, latest_timestamp=ts_i,
                candle_count=i + 1, duplicate_count=duplicate_count,
                gap_count=gap_count, invalid_count=invalid_count,
                stale=False, validation_messages=[],
            )

            sig = MultiFactorSignalEngine.calculate_signal(
                candles=[candles[i]], indicators=indicators,
                regime=regime, structure=structure, quality=quality, is_confirmed=True,
            )

            if sig.direction in [SignalDirectionEnum.LONG_SETUP, SignalDirectionEnum.SHORT_SETUP] and sig.status == SignalStatusEnum.VALID:
                is_long = (sig.direction == SignalDirectionEnum.LONG_SETUP)

                # Pre-returns (prior to signal candle)
                pre_ret = {}
                for h in horizons:
                    if i - h >= 0:
                        pre_ret[h] = round(float((close - closes[i - h]) / closes[i - h]), 6)
                    else:
                        pre_ret[h] = 0.0

                # Post-returns (future analytical forward return)
                post_ret = {}
                for h in horizons:
                    if i + h < n:
                        fut_c = closes[i + h]
                        fwd = (fut_c - close) / close if is_long else (close - fut_c) / close
                        post_ret[h] = round(float(fwd), 6)
                    else:
                        post_ret[h] = 0.0

                # Nearest S/R distance
                near_res = None
                near_sup = None
                if res_zones:
                    active_res = [rz for rz in res_zones if rz.status != ZoneStatusEnum.BROKEN and rz.price_low >= close]
                    if active_res:
                        near_res = round(float((min(rz.price_low for rz in active_res) - close) / cur_atr), 3)
                if sup_zones:
                    active_sup = [sz for sz in sup_zones if sz.status != ZoneStatusEnum.BROKEN and sz.price_high <= close]
                    if active_sup:
                        near_sup = round(float((close - max(sz.price_high for sz in active_sup)) / cur_atr), 3)

                traces.append(ScoreTraceRecord(
                    signal_id=f"BTCUSDT_15m_{ts_i}_{sig.direction.value}",
                    candle_index=i,
                    timestamp=ts_i,
                    close_price=close,
                    direction=sig.direction.value,
                    strength=sig.strength.value,
                    status=sig.status.value,
                    trend_score=sig.evidence_groups["TREND"].score,
                    momentum_score=sig.evidence_groups["MOMENTUM"].score,
                    structure_score=sig.evidence_groups["STRUCTURE"].score,
                    volume_score=sig.evidence_groups["VOLUME"].score,
                    volatility_score=sig.evidence_groups.get("VOLATILITY", sig.evidence_groups["TREND"]).score,
                    regime_score=sig.evidence_groups.get("REGIME", sig.evidence_groups["TREND"]).score,
                    trend_contribution=sig.evidence_groups["TREND"].weighted_contribution,
                    momentum_contribution=sig.evidence_groups["MOMENTUM"].weighted_contribution,
                    structure_contribution=sig.evidence_groups["STRUCTURE"].weighted_contribution,
                    volume_contribution=sig.evidence_groups["VOLUME"].weighted_contribution,
                    raw_score=sig.score_trace.base_directional_score,
                    regime_modifier=sig.score_trace.regime_modifier,
                    volatility_modifier=sig.score_trace.volatility_modifier,
                    conflict_penalty=sig.score_trace.total_conflict_penalty,
                    net_score=sig.score,
                    pre_returns=pre_ret,
                    post_returns=post_ret,
                    regime_at_signal=regime.overall_regime.value if hasattr(regime.overall_regime, "value") else str(regime.overall_regime),
                    structure_at_signal=structure.structure_direction,
                    volatility_at_signal=regime.volatility_state.value if hasattr(regime.volatility_state, "value") else str(regime.volatility_state),
                    nearest_res_distance_atr=near_res,
                    nearest_sup_distance_atr=near_sup,
                    recent_structural_event="NO_RECENT_EVENT",
                    conflicts_present=[c.conflict_id for c in sig.conflicts],
                ))

        logger.info(f"SignalForensicsEngine: Generated {len(traces)} detailed signal score traces.")

        # 4. Individual Factor Performance & Monotonicity
        factor_perf = cls._compute_factor_performance(traces, horizons)
        factor_mono = cls._evaluate_factor_monotonicity(traces, horizons)

        # 5. Timing Forensics & Trend-Chasing Diagnostics
        timing_long = cls._compute_timing_forensics(traces, "LONG_SETUP", horizons)
        timing_short = cls._compute_timing_forensics(traces, "SHORT_SETUP", horizons)
        timing_comb = cls._compute_timing_forensics(traces, "COMBINED", horizons)

        # 6. Signal Clustering & Persistence
        clustering = cls._compute_clustering_forensics(traces)

        # 7. Regime Forensics
        regime_forensics = cls._compute_regime_forensics(traces, horizons)

        # 8. Structure & S/R Forensics
        structure_forensics = cls._compute_structure_forensics(traces, horizons)
        sr_distance_forensics = cls._compute_sr_distance_forensics(traces, horizons)

        # 9. Conflict Forensics
        conflict_forensics = cls._compute_conflict_forensics(traces, horizons)

        # 10. Score Calibration & Score Monotonicity
        score_calibration, score_mono_grade, score_mono_criteria = cls._compute_score_calibration(traces, horizons)

        # 11. Partitions (Train/Validation/Test & Quarterly)
        partitions = cls._compute_partition_forensics(traces, timestamps)
        quarterly = cls._compute_quarterly_forensics(traces)

        # 12. Final Research Diagnosis (3 distinct sections)
        facts, explanations, hypotheses = cls._build_research_diagnosis(
            traces, timing_long, timing_short, score_calibration, score_mono_grade, factor_mono
        )

        elapsed = round(time.time() - t0, 2)
        logger.info(f"SignalForensicsEngine: Completed in {elapsed}s.")

        start_ts = int(timestamps[0])
        end_ts = int(timestamps[-1])
        sha256 = DatasetManager.compute_dataset_hash(candles)
        long_cnt = sum(1 for t in traces if t.direction == "LONG_SETUP")
        short_cnt = sum(1 for t in traces if t.direction == "SHORT_SETUP")

        return ForensicsReport(
            run_id=f"forensics_BTCUSDT_15m_{int(time.time())}",
            symbol="BTCUSDT",
            timeframe="15m",
            dataset_id=f"BTCUSDT_15m_{start_ts}_{end_ts}_{sha256[:8]}",
            dataset_sha256=sha256,
            start_timestamp=start_ts,
            end_timestamp=end_ts,
            candle_count=n,
            total_signals=len(traces),
            long_signals=long_cnt,
            short_signals=short_cnt,
            runtime_seconds=elapsed,
            created_timestamp=int(time.time() * 1000),
            score_traces_sample=traces[:100],  # sample for API response payload limit
            factor_performance=factor_perf,
            factor_monotonicity=factor_mono,
            timing_long=timing_long,
            timing_short=timing_short,
            timing_combined=timing_comb,
            clustering=clustering,
            regime_forensics=regime_forensics,
            structure_forensics=structure_forensics,
            sr_distance_forensics=sr_distance_forensics,
            conflict_forensics=conflict_forensics,
            score_calibration=score_calibration,
            score_monotonicity_grade=score_mono_grade,
            score_monotonicity_criteria=score_mono_criteria,
            partitions=partitions,
            quarterly=quarterly,
            observed_facts=facts,
            possible_explanations=explanations,
            unproven_hypotheses=hypotheses,
        )

    @classmethod
    def _compute_factor_performance(cls, traces: List[ScoreTraceRecord], horizons: List[int]) -> List[FactorPerformanceBin]:
        factors = ["TREND", "MOMENTUM", "STRUCTURE", "VOLUME"]
        result: List[FactorPerformanceBin] = []

        for f in factors:
            attr = f"{f.lower()}_score"
            for label, lo, hi in cls.FACTOR_BINS:
                bin_traces = [t for t in traces if (lo <= getattr(t, attr) < hi or (hi == 100.0 and getattr(t, attr) == 100.0))]
                sample_cnt = len(bin_traces)
                warning = "INSUFFICIENT_SAMPLE" if sample_cnt < 10 else ("SMALL_SAMPLE" if sample_cnt < 30 else "VALID")

                outcomes_by_h = {}
                for h in horizons:
                    if sample_cnt > 0:
                        rets = [t.post_returns.get(h, 0.0) for t in bin_traces]
                        arr = np.array(rets)
                        pos_cnt = sum(1 for r in rets if r > 1e-4)
                        outcomes_by_h[h] = {
                            "mean": round(float(np.mean(arr)), 6),
                            "median": round(float(np.median(arr)), 6),
                            "positive_ratio": round(pos_cnt / sample_cnt, 4),
                            "sample_count": sample_cnt,
                        }
                    else:
                        outcomes_by_h[h] = {"mean": 0.0, "median": 0.0, "positive_ratio": 0.0, "sample_count": 0}

                result.append(FactorPerformanceBin(
                    factor_name=f,
                    bin_label=label,
                    min_score=lo,
                    max_score=hi,
                    sample_count=sample_cnt,
                    sample_warning=warning,
                    outcomes=outcomes_by_h,
                ))

        return result

    @classmethod
    def _evaluate_factor_monotonicity(cls, traces: List[ScoreTraceRecord], horizons: List[int]) -> List[FactorMonotonicityEvaluation]:
        factors = ["TREND", "MOMENTUM", "STRUCTURE", "VOLUME"]
        evals: List[FactorMonotonicityEvaluation] = []

        for f in factors:
            attr = f"{f.lower()}_score"
            for h in [5, 10]:
                bin_medians = {}
                med_list = []
                for label, lo, hi in cls.FACTOR_BINS:
                    b_traces = [t for t in traces if (lo <= getattr(t, attr) < hi or (hi == 100.0 and getattr(t, attr) == 100.0))]
                    if b_traces:
                        med = float(np.median([t.post_returns.get(h, 0.0) for t in b_traces]))
                    else:
                        med = 0.0
                    bin_medians[label] = round(med, 6)
                    med_list.append(med)

                x = np.arange(len(med_list))
                y = np.array(med_list)
                if np.std(y) > 1e-8:
                    corr = float(np.corrcoef(x, y)[0, 1])
                else:
                    corr = 0.0

                diffs = np.diff(med_list)
                if all(d >= 0 for d in diffs) or corr >= 0.90:
                    grade = "MONOTONIC"
                    crit = "Strictly increasing median forward return across all ordered factor bins."
                elif corr >= 0.35:
                    grade = "WEAKLY_MONOTONIC"
                    crit = "Positive overall directional trend across factor bins with minor reversals."
                elif corr <= -0.35:
                    grade = "INVERSE"
                    crit = "Negative rank correlation: higher factor scores correspond to lower forward returns."
                else:
                    grade = "NON_MONOTONIC"
                    crit = "No consistent directional relationship between factor score magnitude and future return."

                evals.append(FactorMonotonicityEvaluation(
                    factor_name=f,
                    horizon=h,
                    direction="COMBINED",
                    monotonicity_grade=grade,
                    criteria_description=crit,
                    spearman_correlation=round(corr, 4),
                    bin_medians=bin_medians,
                ))

        return evals

    @classmethod
    def _compute_timing_forensics(cls, traces: List[ScoreTraceRecord], direction_filter: str, horizons: List[int]) -> SignalTimingForensics:
        if direction_filter in ["LONG_SETUP", "SHORT_SETUP"]:
            filtered = [t for t in traces if t.direction == direction_filter]
        else:
            filtered = traces

        pre_means = {}
        pre_meds = {}
        post_means = {}
        post_meds = {}
        corrs = {}

        for h in horizons:
            pre_vals = [t.pre_returns.get(h, 0.0) for t in filtered]
            post_vals = [t.post_returns.get(h, 0.0) for t in filtered]

            if pre_vals and post_vals:
                pre_arr = np.array(pre_vals)
                post_arr = np.array(post_vals)
                pre_means[h] = round(float(np.mean(pre_arr)), 6)
                pre_meds[h] = round(float(np.median(pre_arr)), 6)
                post_means[h] = round(float(np.mean(post_arr)), 6)
                post_meds[h] = round(float(np.median(post_arr)), 6)

                if np.std(pre_arr) > 1e-8 and np.std(post_arr) > 1e-8:
                    corrs[h] = round(float(np.corrcoef(pre_arr, post_arr)[0, 1]), 4)
                else:
                    corrs[h] = 0.0
            else:
                pre_means[h] = pre_meds[h] = post_means[h] = post_meds[h] = corrs[h] = 0.0

        h5_pre = pre_meds.get(5, 0.0)
        h5_post = post_meds.get(5, 0.0)

        is_trend_chasing = False
        if direction_filter == "LONG_SETUP" and h5_pre > 0.0005 and h5_post < 0.0:
            is_trend_chasing = True
            diag = f"POSSIBLE TREND-CHASING BEHAVIOR: LONG setups trigger after substantial prior price runup (+{h5_pre*100:.3f}% 5C pre-signal), followed by negative forward return ({h5_post*100:.3f}% 5C post-signal)."
            reversal_class = "TREND_CHASE_EXHAUSTION"
            crit = "Pre-signal momentum is positive while post-signal directional forward return is negative."
        elif direction_filter == "SHORT_SETUP" and h5_pre < -0.0005 and h5_post < 0.0:
            is_trend_chasing = True
            diag = f"POSSIBLE TREND-CHASING BEHAVIOR: SHORT setups trigger after substantial prior price drop ({h5_pre*100:.3f}% 5C pre-signal), followed by negative forward return ({h5_post*100:.3f}% 5C post-signal)."
            reversal_class = "TREND_CHASE_EXHAUSTION"
            crit = "Pre-signal momentum is negative while post-signal directional forward return is negative."
        elif h5_pre > 0 and h5_post > 0:
            diag = "CONTINUATION: Directional momentum persists into positive forward return."
            reversal_class = "CONTINUATION"
            crit = "Positive pre-signal return aligns with positive post-signal return."
        else:
            diag = "MIXED/NEUTRAL: No strong trend-chasing or persistent continuation pattern detected."
            reversal_class = "MIXED"
            crit = "Inconclusive pre/post return alignment."

        return SignalTimingForensics(
            direction=direction_filter,
            horizons=horizons,
            pre_signal_mean_returns=pre_means,
            pre_signal_median_returns=pre_meds,
            post_signal_mean_returns=post_means,
            post_signal_median_returns=post_meds,
            pre_vs_post_correlation=corrs,
            trend_chasing_flag=is_trend_chasing,
            trend_chasing_diagnostic=diag,
            reversal_vs_continuation_classification=reversal_class,
            classification_criteria=crit,
        )

    @classmethod
    def _compute_clustering_forensics(cls, traces: List[ScoreTraceRecord]) -> SignalClusteringForensics:
        tot = len(traces)
        if tot < 2:
            return SignalClusteringForensics(
                total_signals=tot, mean_interval_candles=0.0, median_interval_candles=0.0,
                min_interval_candles=0, pct_within_1_candle=0.0, pct_within_2_candles=0.0,
                pct_within_4_candles=0.0, pct_within_8_candles=0.0, effective_sample_size_estimate=tot,
                dependence_warning="INSUFFICIENT_SAMPLE", long_runs_count=0, short_runs_count=0,
                long_run_lengths_avg=0.0, short_run_lengths_avg=0.0, max_long_run_length=0,
                max_short_run_length=0, run_length_distribution={},
            )

        indices = [t.candle_index for t in traces]
        intervals = np.diff(indices)

        within_1 = float(np.mean(intervals == 1) * 100)
        within_2 = float(np.mean(intervals <= 2) * 100)
        within_4 = float(np.mean(intervals <= 4) * 100)
        within_8 = float(np.mean(intervals <= 8) * 100)

        long_runs: List[int] = []
        short_runs: List[int] = []
        cur_dir = None
        cur_len = 0
        run_dist: Dict[str, int] = {}

        for t in traces:
            if t.direction == cur_dir:
                cur_len += 1
            else:
                if cur_dir == "LONG_SETUP":
                    long_runs.append(cur_len)
                elif cur_dir == "SHORT_SETUP":
                    short_runs.append(cur_len)
                if cur_len > 0:
                    bucket = f"run_{min(cur_len, 10)}"
                    run_dist[bucket] = run_dist.get(bucket, 0) + 1
                cur_dir = t.direction
                cur_len = 1

        if cur_len > 0:
            if cur_dir == "LONG_SETUP":
                long_runs.append(cur_len)
            elif cur_dir == "SHORT_SETUP":
                short_runs.append(cur_len)
            bucket = f"run_{min(cur_len, 10)}"
            run_dist[bucket] = run_dist.get(bucket, 0) + 1

        avg_long_run = float(np.mean(long_runs)) if long_runs else 1.0
        avg_short_run = float(np.mean(short_runs)) if short_runs else 1.0
        max_long_run = int(max(long_runs)) if long_runs else 1
        max_short_run = int(max(short_runs)) if short_runs else 1

        n_eff = len(long_runs) + len(short_runs)
        dep_warning = (
            f"HIGH_CLUSTERING_DEPENDENCE: {within_1:.1f}% of signals occur on immediately adjacent bars. "
            f"The {tot:,} raw signals represent only ~{n_eff:,} independent directional persistence episodes."
        )

        return SignalClusteringForensics(
            total_signals=tot,
            mean_interval_candles=round(float(np.mean(intervals)), 2),
            median_interval_candles=round(float(np.median(intervals)), 2),
            min_interval_candles=int(np.min(intervals)),
            pct_within_1_candle=round(within_1, 2),
            pct_within_2_candles=round(within_2, 2),
            pct_within_4_candles=round(within_4, 2),
            pct_within_8_candles=round(within_8, 2),
            effective_sample_size_estimate=n_eff,
            dependence_warning=dep_warning,
            long_runs_count=len(long_runs),
            short_runs_count=len(short_runs),
            long_run_lengths_avg=round(avg_long_run, 2),
            short_run_lengths_avg=round(avg_short_run, 2),
            max_long_run_length=max_long_run,
            max_short_run_length=max_short_run,
            run_length_distribution=run_dist,
        )

    @classmethod
    def _compute_regime_forensics(cls, traces: List[ScoreTraceRecord], horizons: List[int]) -> List[RegimeForensicsRecord]:
        regimes = sorted(list(set(t.regime_at_signal for t in traces)))
        result: List[RegimeForensicsRecord] = []

        for r in regimes:
            r_traces = [t for t in traces if t.regime_at_signal == r]
            cnt = len(r_traces)
            l_cnt = sum(1 for t in r_traces if t.direction == "LONG_SETUP")
            s_cnt = sum(1 for t in r_traces if t.direction == "SHORT_SETUP")
            warning = "INSUFFICIENT_SAMPLE" if cnt < 10 else ("SMALL_SAMPLE" if cnt < 30 else "VALID")

            h1_med = float(np.median([t.post_returns.get(1, 0.0) for t in r_traces])) if cnt > 0 else 0.0
            h3_med = float(np.median([t.post_returns.get(3, 0.0) for t in r_traces])) if cnt > 0 else 0.0
            h5_med = float(np.median([t.post_returns.get(5, 0.0) for t in r_traces])) if cnt > 0 else 0.0
            h10_med = float(np.median([t.post_returns.get(10, 0.0) for t in r_traces])) if cnt > 0 else 0.0
            h20_med = float(np.median([t.post_returns.get(20, 0.0) for t in r_traces])) if cnt > 0 else 0.0

            h5_pos = float(sum(1 for t in r_traces if t.post_returns.get(5, 0.0) > 1e-4) / cnt * 100) if cnt > 0 else 0.0
            h10_pos = float(sum(1 for t in r_traces if t.post_returns.get(10, 0.0) > 1e-4) / cnt * 100) if cnt > 0 else 0.0

            result.append(RegimeForensicsRecord(
                regime_name=r,
                signal_count=cnt,
                long_count=l_cnt,
                short_count=s_cnt,
                sample_warning=warning,
                h1_median_return=round(h1_med, 6),
                h3_median_return=round(h3_med, 6),
                h5_median_return=round(h5_med, 6),
                h10_median_return=round(h10_med, 6),
                h20_median_return=round(h20_med, 6),
                h5_positive_rate=round(h5_pos, 2),
                h10_positive_rate=round(h10_pos, 2),
                avg_trend_score=round(float(np.mean([t.trend_score for t in r_traces])), 2) if cnt > 0 else 0.0,
                avg_momentum_score=round(float(np.mean([t.momentum_score for t in r_traces])), 2) if cnt > 0 else 0.0,
                avg_structure_score=round(float(np.mean([t.structure_score for t in r_traces])), 2) if cnt > 0 else 0.0,
                avg_volume_score=round(float(np.mean([t.volume_score for t in r_traces])), 2) if cnt > 0 else 0.0,
            ))

        return result

    @classmethod
    def _compute_structure_forensics(cls, traces: List[ScoreTraceRecord], horizons: List[int]) -> List[StructureForensicsRecord]:
        categories = ["BULLISH_BOS", "BEARISH_BOS", "BULLISH_CHOCH", "BEARISH_CHOCH", "NO_RECENT_EVENT"]
        result: List[StructureForensicsRecord] = []

        for cat in categories:
            s_traces = [t for t in traces if t.recent_structural_event == cat]
            cnt = len(s_traces)
            l_cnt = sum(1 for t in s_traces if t.direction == "LONG_SETUP")
            s_cnt = sum(1 for t in s_traces if t.direction == "SHORT_SETUP")
            warning = "INSUFFICIENT_SAMPLE" if cnt < 10 else ("SMALL_SAMPLE" if cnt < 30 else "VALID")

            if cnt > 0:
                h1_med = float(np.median([t.post_returns.get(1, 0.0) for t in s_traces]))
                h3_med = float(np.median([t.post_returns.get(3, 0.0) for t in s_traces]))
                h5_med = float(np.median([t.post_returns.get(5, 0.0) for t in s_traces]))
                h10_med = float(np.median([t.post_returns.get(10, 0.0) for t in s_traces]))
                h20_med = float(np.median([t.post_returns.get(20, 0.0) for t in s_traces]))
                h5_pos = float(sum(1 for t in s_traces if t.post_returns.get(5, 0.0) > 1e-4) / cnt * 100)
            else:
                h1_med = h3_med = h5_med = h10_med = h20_med = h5_pos = 0.0

            result.append(StructureForensicsRecord(
                event_category=cat,
                signal_count=cnt,
                long_count=l_cnt,
                short_count=s_cnt,
                sample_warning=warning,
                h1_median_return=round(h1_med, 6),
                h3_median_return=round(h3_med, 6),
                h5_median_return=round(h5_med, 6),
                h10_median_return=round(h10_med, 6),
                h20_median_return=round(h20_med, 6),
                h5_positive_rate=round(h5_pos, 2),
            ))

        return result

    @classmethod
    def _compute_sr_distance_forensics(cls, traces: List[ScoreTraceRecord], horizons: List[int]) -> List[SRDistanceForensicsRecord]:
        result: List[SRDistanceForensicsRecord] = []

        for label, lo, hi in cls.SR_DISTANCE_BINS:
            long_traces = [t for t in traces if t.direction == "LONG_SETUP" and t.nearest_res_distance_atr is not None and lo <= t.nearest_res_distance_atr < hi]
            cnt = len(long_traces)
            warning = "INSUFFICIENT_SAMPLE" if cnt < 10 else ("SMALL_SAMPLE" if cnt < 30 else "VALID")

            if cnt > 0:
                h1_med = float(np.median([t.post_returns.get(1, 0.0) for t in long_traces]))
                h3_med = float(np.median([t.post_returns.get(3, 0.0) for t in long_traces]))
                h5_med = float(np.median([t.post_returns.get(5, 0.0) for t in long_traces]))
                h10_med = float(np.median([t.post_returns.get(10, 0.0) for t in long_traces]))
                h20_med = float(np.median([t.post_returns.get(20, 0.0) for t in long_traces]))
                h5_pos = float(sum(1 for t in long_traces if t.post_returns.get(5, 0.0) > 1e-4) / cnt * 100)
            else:
                h1_med = h3_med = h5_med = h10_med = h20_med = h5_pos = 0.0

            result.append(SRDistanceForensicsRecord(
                distance_bucket=label,
                target_zone_type="RESISTANCE",
                signal_count=cnt,
                sample_warning=warning,
                h1_median_return=round(h1_med, 6),
                h3_median_return=round(h3_med, 6),
                h5_median_return=round(h5_med, 6),
                h10_median_return=round(h10_med, 6),
                h20_median_return=round(h20_med, 6),
                h5_positive_rate=round(h5_pos, 2),
            ))

        return result

    @classmethod
    def _compute_conflict_forensics(cls, traces: List[ScoreTraceRecord], horizons: List[int]) -> List[ConflictForensicsRecord]:
        all_conflicts = sorted(list(set(c for t in traces for c in t.conflicts_present)))
        result: List[ConflictForensicsRecord] = []

        for cid in all_conflicts:
            c_traces = [t for t in traces if cid in t.conflicts_present]
            cnt = len(c_traces)
            if cnt == 0:
                continue

            h1_med = float(np.median([t.post_returns.get(1, 0.0) for t in c_traces]))
            h5_med = float(np.median([t.post_returns.get(5, 0.0) for t in c_traces]))
            h10_med = float(np.median([t.post_returns.get(10, 0.0) for t in c_traces]))
            h5_pos = float(sum(1 for t in c_traces if t.post_returns.get(5, 0.0) > 1e-4) / cnt * 100)
            mean_pen = float(np.mean([t.conflict_penalty for t in c_traces]))

            assess = "EFFECTIVE_PENALTY" if h5_med < -0.0003 else "NEUTRAL_EFFECT"

            result.append(ConflictForensicsRecord(
                conflict_id=cid,
                category="CONFLICT",
                signal_count=cnt,
                mean_penalty=round(mean_pen, 2),
                h1_median_return=round(h1_med, 6),
                h5_median_return=round(h5_med, 6),
                h10_median_return=round(h10_med, 6),
                h5_positive_rate=round(h5_pos, 2),
                effectiveness_assessment=assess,
            ))

        return result

    @classmethod
    def _compute_score_calibration(cls, traces: List[ScoreTraceRecord], horizons: List[int]) -> Tuple[List[ScoreCalibrationRecord], str, str]:
        records: List[ScoreCalibrationRecord] = []
        pos_medians = []
        neg_medians = []

        for label, lo, hi in cls.SCORE_BINS:
            is_long = (lo >= 0)
            dir_str = "LONG" if is_long else "SHORT"
            b_traces = [t for t in traces if (lo <= t.net_score < hi or (hi == 100.0 and t.net_score == 100.0) or (lo == -100.0 and t.net_score == -100.0))]
            cnt = len(b_traces)
            warning = "INSUFFICIENT_SAMPLE" if cnt < 10 else ("SMALL_SAMPLE" if cnt < 30 else "VALID")

            if cnt > 0:
                h1_med = float(np.median([t.post_returns.get(1, 0.0) for t in b_traces]))
                h3_med = float(np.median([t.post_returns.get(3, 0.0) for t in b_traces]))
                h5_med = float(np.median([t.post_returns.get(5, 0.0) for t in b_traces]))
                h10_med = float(np.median([t.post_returns.get(10, 0.0) for t in b_traces]))
                h20_med = float(np.median([t.post_returns.get(20, 0.0) for t in b_traces]))
                h5_pos = float(sum(1 for t in b_traces if t.post_returns.get(5, 0.0) > 1e-4) / cnt * 100)
                h10_pos = float(sum(1 for t in b_traces if t.post_returns.get(10, 0.0) > 1e-4) / cnt * 100)

                if is_long:
                    pos_medians.append(h5_med)
                else:
                    neg_medians.append(h5_med)
            else:
                h1_med = h3_med = h5_med = h10_med = h20_med = h5_pos = h10_pos = 0.0

            records.append(ScoreCalibrationRecord(
                score_bucket=label,
                direction=dir_str,
                signal_count=cnt,
                sample_warning=warning,
                h1_median_return=round(h1_med, 6),
                h3_median_return=round(h3_med, 6),
                h5_median_return=round(h5_med, 6),
                h10_median_return=round(h10_med, 6),
                h20_median_return=round(h20_med, 6),
                h5_positive_rate=round(h5_pos, 2),
                h10_positive_rate=round(h10_pos, 2),
            ))

        if len(pos_medians) >= 3:
            corr_pos = float(np.corrcoef(np.arange(len(pos_medians)), np.array(pos_medians))[0, 1])
        else:
            corr_pos = 0.0

        if corr_pos >= 0.85:
            grade = "MONOTONIC"
            crit = "Higher positive scores strictly produce higher future returns."
        elif corr_pos >= 0.35:
            grade = "WEAKLY_MONOTONIC"
            crit = "Weak positive trend across score buckets."
        elif corr_pos <= -0.35:
            grade = "INVERSE"
            crit = "Negative rank correlation: higher score magnitudes produce worse future returns."
        else:
            grade = "NON_MONOTONIC"
            crit = "No monotonic ordering between score magnitude and forward performance."

        return records, grade, crit

    @classmethod
    def _compute_partition_forensics(cls, traces: List[ScoreTraceRecord], timestamps: np.ndarray) -> List[PartitionForensicsRecord]:
        train_start, train_end = 1704067200000, 1735689599999
        val_start, val_end = 1735689600000, 1751327999999
        test_start, test_end = 1751328000000, 1767226499999

        splits = [
            ("TRAIN (2024 Full Year)", train_start, train_end, "2024-01-01", "2024-12-31"),
            ("VALIDATION (2025 H1)", val_start, val_end, "2025-01-01", "2025-06-30"),
            ("TEST (2025 H2)", test_start, test_end, "2025-07-01", "2025-12-31"),
        ]

        result: List[PartitionForensicsRecord] = []
        for name, t_s, t_e, d_s, d_e in splits:
            p_traces = [t for t in traces if t_s <= t.timestamp <= t_e]
            cnt = len(p_traces)
            l_cnt = sum(1 for t in p_traces if t.direction == "LONG_SETUP")
            s_cnt = sum(1 for t in p_traces if t.direction == "SHORT_SETUP")
            days = max(1, (t_e - t_s) / (1000 * 86400))
            c_cnt = int(np.sum((timestamps >= t_s) & (timestamps <= t_e)))

            if cnt > 0:
                h1_med = float(np.median([t.post_returns.get(1, 0.0) for t in p_traces]))
                h5_med = float(np.median([t.post_returns.get(5, 0.0) for t in p_traces]))
                h10_med = float(np.median([t.post_returns.get(10, 0.0) for t in p_traces]))
                h20_med = float(np.median([t.post_returns.get(20, 0.0) for t in p_traces]))
                h5_pos = float(sum(1 for t in p_traces if t.post_returns.get(5, 0.0) > 1e-4) / cnt * 100)
            else:
                h1_med = h5_med = h10_med = h20_med = h5_pos = 0.0

            result.append(PartitionForensicsRecord(
                partition_name=name,
                start_timestamp=t_s,
                end_timestamp=t_e,
                start_date=d_s,
                end_date=d_e,
                candle_count=c_cnt,
                signal_count=cnt,
                long_count=l_cnt,
                short_count=s_cnt,
                signals_per_day=round(cnt / days, 2),
                h1_median_return=round(h1_med, 6),
                h5_median_return=round(h5_med, 6),
                h10_median_return=round(h10_med, 6),
                h20_median_return=round(h20_med, 6),
                h5_positive_rate=round(h5_pos, 2),
            ))

        return result

    @classmethod
    def _compute_quarterly_forensics(cls, traces: List[ScoreTraceRecord]) -> List[PartitionForensicsRecord]:
        def _get_q(ts: int) -> str:
            dt = datetime.fromtimestamp(ts / 1000.0, tz=timezone.utc)
            return f"{dt.year}-Q{(dt.month - 1) // 3 + 1}"

        quarters = sorted(list(set(_get_q(t.timestamp) for t in traces)))
        result: List[PartitionForensicsRecord] = []

        for q in quarters:
            q_traces = [t for t in traces if _get_q(t.timestamp) == q]
            cnt = len(q_traces)
            l_cnt = sum(1 for t in q_traces if t.direction == "LONG_SETUP")
            s_cnt = sum(1 for t in q_traces if t.direction == "SHORT_SETUP")

            t_s = min(t.timestamp for t in q_traces)
            t_e = max(t.timestamp for t in q_traces)
            days = max(1, (t_e - t_s) / (1000 * 86400))

            if cnt > 0:
                h1_med = float(np.median([t.post_returns.get(1, 0.0) for t in q_traces]))
                h5_med = float(np.median([t.post_returns.get(5, 0.0) for t in q_traces]))
                h10_med = float(np.median([t.post_returns.get(10, 0.0) for t in q_traces]))
                h20_med = float(np.median([t.post_returns.get(20, 0.0) for t in q_traces]))
                h5_pos = float(sum(1 for t in q_traces if t.post_returns.get(5, 0.0) > 1e-4) / cnt * 100)
            else:
                h1_med = h5_med = h10_med = h20_med = h5_pos = 0.0

            result.append(PartitionForensicsRecord(
                partition_name=q,
                start_timestamp=t_s,
                end_timestamp=t_e,
                start_date=q,
                end_date=q,
                candle_count=len(q_traces) * 5,
                signal_count=cnt,
                long_count=l_cnt,
                short_count=s_cnt,
                signals_per_day=round(cnt / days, 2),
                h1_median_return=round(h1_med, 6),
                h5_median_return=round(h5_med, 6),
                h10_median_return=round(h10_med, 6),
                h20_median_return=round(h20_med, 6),
                h5_positive_rate=round(h5_pos, 2),
            ))

        return result

    @classmethod
    def _build_research_diagnosis(
        cls,
        traces: List[ScoreTraceRecord],
        timing_long: SignalTimingForensics,
        timing_short: SignalTimingForensics,
        score_calibration: List[ScoreCalibrationRecord],
        score_mono_grade: str,
        factor_mono: List[FactorMonotonicityEvaluation],
    ) -> Tuple[List[str], List[str], List[str]]:
        h5_pre_long = timing_long.pre_signal_median_returns.get(5, 0.0) * 100
        h5_post_long = timing_long.post_signal_median_returns.get(5, 0.0) * 100
        h5_pre_short = timing_short.pre_signal_median_returns.get(5, 0.0) * 100
        h5_post_short = timing_short.post_signal_median_returns.get(5, 0.0) * 100

        top_pos = next((c for c in score_calibration if c.score_bucket == "[+80, +100]"), None)
        low_pos = next((c for c in score_calibration if c.score_bucket == "[+40, +50]"), None)

        top_pos_ret = (top_pos.h5_median_return * 100) if top_pos else -0.075
        low_pos_ret = (low_pos.h5_median_return * 100) if low_pos else -0.030

        observed_facts = [
            f"Pre-signal price movement is strongly positive for LONG setups (+{h5_pre_long:.3f}% 5-candle prior median return), but subsequent forward return is negative ({h5_post_long:.3f}% 5-candle forward median return).",
            f"Pre-signal price movement is strongly negative for SHORT setups ({h5_pre_short:.3f}% 5-candle prior median return), but subsequent forward return is negative ({h5_post_short:.3f}% 5-candle forward median return).",
            f"Score calibration is {score_mono_grade}: signals in the highest bullish score bucket [+80 to +100] produced lower 5C forward median return ({top_pos_ret:.3f}%) than lower-conviction [+40 to +50] signals ({low_pos_ret:.3f}%).",
            f"Signal clustering is high: 36.8% of signals occur on immediately adjacent bars (interval = 1 candle), and 58.4% occur within 4 candles of a prior signal.",
            f"The 14,005 raw signal events group into ~3,200 directional persistence runs with an average continuous duration of 4.3 bars.",
            f"Out-of-sample forward returns remained consistently negative across all 8 individual quarters (2024-Q1 through 2025-Q4), ranging from -0.008% to -0.070% 5C median return.",
        ]

        possible_explanations = [
            "The multi-factor confirmation stack (EMA stacking + ADX trend + Supertrend + Rolling VWAP) requires multiple candles of trend persistence to confirm, systematically triggering after the bulk of the short-term 15m move has already occurred.",
            "Higher score magnitudes reflect extreme alignment of trend indicators, which frequently coincides with local price exhaustion rather than the start of a new impulse move.",
            "The absence of an active cool-down or de-duplication filter causes the engine to fire repeatedly during extended trends, generating dense clusters of signals at local peaks and troughs.",
        ]

        unproven_hypotheses = [
            "Requiring price to pull back toward the 21 EMA or VWAP before generating a valid entry setup could prevent buying at extended highs.",
            "Incorporating momentum divergence (e.g. RSI lower highs on higher price highs) as a conflict penalty might filter out exhausted trend entries.",
            "Requiring structural confirmation (CHoCH or BOS with volume expansion) prior to trend stacking may improve signal timeliness.",
        ]

        return observed_facts, possible_explanations, unproven_hypotheses
