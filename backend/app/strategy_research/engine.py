"""
Phase 8 — Strategy Research Engine.
Orchestrates causal execution of baseline and candidate experiments across Train, Validation, and Test.
"""

import time
from typing import List, Dict, Optional, Tuple, Any
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
from app.forensics.models import ScoreTraceRecord
from app.strategy_research.config import (
    STRATEGY_BASELINE,
    TRAIN_START, TRAIN_END,
    VAL_START, VAL_END,
    TEST_START, TEST_END,
    EXPERIMENT_DEFINITIONS,
)
from app.strategy_research.models import (
    ExperimentEvaluation,
    PartitionPerformanceMetrics,
    ResearchStatusEnum,
)
from app.strategy_research.experiments import (
    PullbackResearchFilter,
    DivergenceResearchFilter,
    FirstStructuralEventFilter,
    EpisodeCooldownFilter,
    ExtensionResearchFilter,
    CombinedStrategyFilter,
)
from app.strategy_research.evaluation import StrategyEvaluator
from app.strategy_research.selection import StrategySelectionEngine
from app.backtesting.dataset import DatasetManager
from app.core.logging import logger


class StrategyResearchEngine:
    """
    Scientific experiment execution engine. Runs baseline and candidate filters causally.
    """

    @classmethod
    def run_all_experiments(cls, candles: List[Candle]) -> Dict[str, ExperimentEvaluation]:
        logger.info(f"StrategyResearchEngine: Running full research battery on {len(candles)} candles...")
        results: Dict[str, ExperimentEvaluation] = {}

        # 1. Precompute Indicator & Market Structure Data causally
        traces_baseline, traces_by_exp = cls._execute_causal_pass(candles)

        # 2. Evaluate Baseline across partitions
        n_total = len(candles)
        c_train = int(sum(1 for c in candles if TRAIN_START <= c.timestamp <= TRAIN_END))
        c_val = int(sum(1 for c in candles if VAL_START <= c.timestamp <= VAL_END))
        c_test = int(sum(1 for c in candles if TEST_START <= c.timestamp <= TEST_END))

        base_train = StrategyEvaluator.evaluate_partition("TRAIN (2024)", TRAIN_START, TRAIN_END, c_train, traces_baseline)
        base_val = StrategyEvaluator.evaluate_partition("VALIDATION (2025 H1)", VAL_START, VAL_END, c_val, traces_baseline)
        base_test = StrategyEvaluator.evaluate_partition("TEST (2025 H2)", TEST_START, TEST_END, c_test, traces_baseline)

        # Save Baseline Evaluation
        results["BASELINE"] = ExperimentEvaluation(
            experiment_id="BASELINE",
            experiment_name="Phase 5 Multi-Factor Baseline (v0.5.0)",
            description="Immutable frozen baseline reference",
            hypothesis="Frozen Phase 5 Multi-Factor Trend & Structure Signal Engine",
            parameters={},
            engine_version="0.5.0",
            dataset_hash=DatasetManager.compute_dataset_hash(candles),
            created_timestamp=int(time.time() * 1000),
            status=ResearchStatusEnum.VALIDATION_FAILED,  # Baseline failed Phase 7 validation
            train_metrics=base_train,
            validation_metrics=base_val,
            test_metrics=base_test,
            promotion_gates=[],
            gates_passed_count=0,
            total_gates_count=10,
            final_decision="BASELINE_REFERENCE",
            decision_rationale="Immutable baseline against which all candidate experiments are evaluated.",
        )

        # 3. Evaluate each experiment (A1 to E2) on TRAIN and VALIDATION
        validation_winners = []

        for exp_id, exp_def in EXPERIMENT_DEFINITIONS.items():
            if exp_id == "EXP_F1_COMBINED_CANDIDATE":
                continue  # Evaluated after A-E

            exp_traces = traces_by_exp.get(exp_id, [])
            e_train = StrategyEvaluator.evaluate_partition("TRAIN (2024)", TRAIN_START, TRAIN_END, c_train, exp_traces)
            e_val = StrategyEvaluator.evaluate_partition("VALIDATION (2025 H1)", VAL_START, VAL_END, c_val, exp_traces)

            # Evaluate against promotion gates on Validation (Test remains None at this stage)
            gates_val, status_val, rationale_val = StrategySelectionEngine.evaluate_gates(
                candidate_val=e_val,
                baseline_val=base_val,
                candidate_test=None,
                baseline_test=None,
            )

            # Open Test evaluation once frozen
            e_test = StrategyEvaluator.evaluate_partition("TEST (2025 H2)", TEST_START, TEST_END, c_test, exp_traces)
            gates_full, status_full, rationale_full = StrategySelectionEngine.evaluate_gates(
                candidate_val=e_val,
                baseline_val=base_val,
                candidate_test=e_test,
                baseline_test=base_test,
            )

            if status_val == ResearchStatusEnum.VALIDATION_PASSED or e_val.h5_median > base_val.h5_median:
                validation_winners.append(exp_id)

            passed_count = sum(1 for g in gates_full if g.passed)

            results[exp_id] = ExperimentEvaluation(
                experiment_id=exp_id,
                experiment_name=exp_def["name"],
                description=exp_def["description"],
                hypothesis=exp_def["hypothesis"],
                parameters=exp_def["parameters"],
                engine_version="0.8.0-research",
                dataset_hash=DatasetManager.compute_dataset_hash(candles),
                created_timestamp=int(time.time() * 1000),
                status=status_full,
                train_metrics=e_train,
                validation_metrics=e_val,
                test_metrics=e_test,
                promotion_gates=gates_full,
                gates_passed_count=passed_count,
                total_gates_count=len(gates_full),
                final_decision=status_full.value,
                decision_rationale=rationale_full,
            )

        # 4. Evaluate Experiment F (Combined Candidate)
        f_def = EXPERIMENT_DEFINITIONS["EXP_F1_COMBINED_CANDIDATE"]
        f_traces = traces_by_exp.get("EXP_F1_COMBINED_CANDIDATE", [])
        f_train = StrategyEvaluator.evaluate_partition("TRAIN (2024)", TRAIN_START, TRAIN_END, c_train, f_traces)
        f_val = StrategyEvaluator.evaluate_partition("VALIDATION (2025 H1)", VAL_START, VAL_END, c_val, f_traces)
        f_test = StrategyEvaluator.evaluate_partition("TEST (2025 H2)", TEST_START, TEST_END, c_test, f_traces)

        f_gates, f_status, f_rationale = StrategySelectionEngine.evaluate_gates(
            candidate_val=f_val,
            baseline_val=base_val,
            candidate_test=f_test,
            baseline_test=base_test,
        )

        f_passed_count = sum(1 for g in f_gates if g.passed)

        results["EXP_F1_COMBINED_CANDIDATE"] = ExperimentEvaluation(
            experiment_id="EXP_F1_COMBINED_CANDIDATE",
            experiment_name=f_def["name"],
            description=f_def["description"],
            hypothesis=f_def["hypothesis"],
            parameters=f_def["parameters"],
            engine_version="0.8.0-research",
            dataset_hash=DatasetManager.compute_dataset_hash(candles),
            created_timestamp=int(time.time() * 1000),
            status=f_status,
            train_metrics=f_train,
            validation_metrics=f_val,
            test_metrics=f_test,
            promotion_gates=f_gates,
            gates_passed_count=f_passed_count,
            total_gates_count=len(f_gates),
            final_decision=f_status.value,
            decision_rationale=f_rationale,
        )

        logger.info("StrategyResearchEngine: Research battery complete.")
        return results

    @classmethod
    def _execute_causal_pass(
        cls, candles: List[Candle]
    ) -> Tuple[List[ScoreTraceRecord], Dict[str, List[ScoreTraceRecord]]]:
        """
        Executes an $O(N)$ single-pass causal evaluation generating baseline traces
        and filtering candidate experiment streams simultaneously.
        """
        n = len(candles)
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

        cfg_struct = default_structure_config
        VOL_LOOKBACK = 50
        left, right = cfg_struct.SWING_LEFT, cfg_struct.SWING_RIGHT
        acc_swings: List[SwingPoint] = []
        confirmed_shs: List[SwingPoint] = []
        confirmed_sls: List[SwingPoint] = []
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

        traces_baseline: List[ScoreTraceRecord] = []
        traces_by_exp: Dict[str, List[ScoreTraceRecord]] = {exp_id: [] for exp_id in EXPERIMENT_DEFINITIONS}

        # Initialize candidate filter objects
        episode_filter_d1 = EpisodeCooldownFilter()
        combined_filter_f1 = CombinedStrategyFilter(EXPERIMENT_DEFINITIONS["EXP_F1_COMBINED_CANDIDATE"]["parameters"])

        horizons = [1, 3, 5, 10, 20]
        last_struct_event_idx = None

        for i in range(200 - 1, n):
            ts_i = int(timestamps[i])
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
                symbol="BTCUSDT", timeframe="15m", timestamp=ts_i,
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

            quality = MarketDataQuality(
                symbol="BTCUSDT", timeframe="15m",
                status=QualityStatusEnum.HEALTHY, latest_timestamp=ts_i,
                candle_count=i + 1, duplicate_count=0, gap_count=0, invalid_count=0,
                stale=False, validation_messages=[],
            )

            sig = MultiFactorSignalEngine.calculate_signal(
                candles=[candles[i]], indicators=indicators,
                regime=regime, structure=structure, quality=quality, is_confirmed=True,
            )

            if sig.direction in [SignalDirectionEnum.LONG_SETUP, SignalDirectionEnum.SHORT_SETUP] and sig.status == SignalStatusEnum.VALID:
                is_long = (sig.direction == SignalDirectionEnum.LONG_SETUP)

                pre_ret = {h: round(float((close - closes[i - h]) / closes[i - h]), 6) if i - h >= 0 else 0.0 for h in horizons}
                post_ret = {h: round(float(((closes[i + h] - close) / close) if is_long else ((close - closes[i + h]) / close)), 6) if i + h < n else 0.0 for h in horizons}

                trace = ScoreTraceRecord(
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
                    nearest_res_distance_atr=None,
                    nearest_sup_distance_atr=None,
                    recent_structural_event="NO_RECENT_EVENT",
                    conflicts_present=[c.conflict_id for c in sig.conflicts],
                )

                traces_baseline.append(trace)

                # Experiment A1: Pullback to 21 EMA
                if PullbackResearchFilter.evaluate(candles[i], indicators, sig.direction, "EMA_21", 0.75):
                    traces_by_exp["EXP_A1_PULLBACK_EMA21"].append(trace)

                # Experiment A2: Pullback to VWAP
                if PullbackResearchFilter.evaluate(candles[i], indicators, sig.direction, "VWAP", 0.75):
                    traces_by_exp["EXP_A2_PULLBACK_VWAP"].append(trace)

                # Experiment B1: RSI Divergence check
                if DivergenceResearchFilter.evaluate(sig.direction, recent_swings, indicators, "RSI_14"):
                    traces_by_exp["EXP_B1_DIVERGENCE_RSI"].append(trace)

                # Experiment B2: MACD Histogram Divergence check
                if DivergenceResearchFilter.evaluate(sig.direction, recent_swings, indicators, "MACD_HIST"):
                    traces_by_exp["EXP_B2_DIVERGENCE_MACD"].append(trace)

                # Experiment C1: First Structural Event
                if FirstStructuralEventFilter.evaluate(i, last_struct_event_idx, 3):
                    traces_by_exp["EXP_C1_FIRST_STRUCTURAL_EVENT"].append(trace)

                # Experiment D1: Episode Cooldown Filter
                if episode_filter_d1.evaluate(sig.direction.value):
                    traces_by_exp["EXP_D1_EPISODE_COOLDOWN"].append(trace)

                # Experiment E1: Extension Cap (21 EMA <= 1.5 ATR)
                if ExtensionResearchFilter.evaluate(candles[i], indicators, "EMA21_DISTANCE_ATR", 1.5):
                    traces_by_exp["EXP_E1_EXTENSION_FILTER_EMA21"].append(trace)

                # Experiment E2: Extension Cap (VWAP <= 1.75 ATR)
                if ExtensionResearchFilter.evaluate(candles[i], indicators, "VWAP_DISTANCE_ATR", 1.75):
                    traces_by_exp["EXP_E2_EXTENSION_FILTER_VWAP"].append(trace)

                # Experiment F1: Combined Candidate Filter
                if combined_filter_f1.evaluate(candles[i], i, indicators, sig.direction, recent_swings, last_struct_event_idx):
                    traces_by_exp["EXP_F1_COMBINED_CANDIDATE"].append(trace)

        return traces_baseline, traces_by_exp
