"""
SCALP_STRATEGY_V2 — Diagnostic Engine & Signal Timing Forensics.

Phase 13D — Deep diagnostic and calibration forensics layer for SCALP_STRATEGY_V2.
Strictly analytical/shadow only. Zero strategy logic modification.
"""
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
import statistics
import time

from app.data.schema import Candle
from app.indicators.engine import IndicatorEngine
from app.scalp_v2.engine import ScalpV2StrategyEngine
from app.scalp_v2.models import (
    ScalpV2Direction,
    ScalpV2SetupType,
    ScalpV2Signal,
)


# ── Diagnostic Schemas ───────────────────────────────────────────────────────

class ScoreBucketDiagnostic(BaseModel):
    bucket_label: str
    min_score: float
    max_score: float
    sample_size_n: int
    buy_count: int
    sell_count: int
    tp1_hit_rate_1c: float
    tp1_hit_rate_3c: float
    tp1_hit_rate_5c: float
    tp1_hit_rate_10c: float
    tp1_hit_rate_20c: float
    sl_rate_20c: float
    neither_rate_20c: float
    ambiguous_count: int
    avg_score: float
    median_score: float
    is_insufficient_sample: bool


class ScoreMonotonicityReport(BaseModel):
    status: str = Field(description="'MONOTONIC' | 'NON_MONOTONIC' | 'INSUFFICIENT_SAMPLE'")
    bucket_hit_rates: Dict[str, float]
    details: str
    anomaly_detected: bool


class DirectionDiagnostic(BaseModel):
    direction: str
    sample_size_n: int
    tp1_hit_rate_1c: float
    tp1_hit_rate_3c: float
    tp1_hit_rate_5c: float
    tp1_hit_rate_10c: float
    tp1_hit_rate_20c: float
    sl_rate_20c: float
    neither_rate_20c: float
    avg_score: float
    avg_abs_score: float
    is_insufficient_sample: bool


class SetupDiagnostic(BaseModel):
    setup_type: str
    sample_size_n: int
    buy_count: int
    sell_count: int
    tp1_hit_rate_1c: float
    tp1_hit_rate_3c: float
    tp1_hit_rate_5c: float
    tp1_hit_rate_10c: float
    tp1_hit_rate_20c: float
    sl_rate_20c: float
    neither_rate_20c: float
    avg_score: float
    is_insufficient_sample: bool
    diagnostic_notes: str


class TimingDistribution(BaseModel):
    tp1_before_sl_count: int
    sl_before_tp1_count: int
    neither_count: int
    ambiguous_count: int
    tp1_within_1c: int
    tp1_within_2c: int
    tp1_within_3c: int
    tp1_within_5c: int
    tp1_within_10c: int
    tp1_within_20c: int
    avg_candles_to_tp1: Optional[float]
    median_candles_to_tp1: Optional[float]
    avg_candles_to_sl: Optional[float]
    median_candles_to_sl: Optional[float]


class EntryTimingDiagnostic(BaseModel):
    timely_count: int
    early_count: int
    late_count: int
    undetermined_count: int
    notes: str


class FactorDiagnostic(BaseModel):
    factor_name: str
    avg_contribution: float
    positive_count: int
    negative_count: int
    neutral_count: int
    tp1_hit_rate_strongly_positive: Optional[float]
    strongly_pos_n: int
    tp1_hit_rate_neutral: Optional[float]
    neutral_n: int
    tp1_hit_rate_strongly_negative: Optional[float]
    strongly_neg_n: int


class ClusteringDiagnostic(BaseModel):
    signals_per_hour: float
    signals_per_4h: float
    avg_time_between_signals_min: float
    median_time_between_signals_min: float
    max_signals_in_rolling_5m: int
    max_signals_in_rolling_15m: int
    same_direction_clusters_count: int


class FlipDiagnostic(BaseModel):
    flips_total: int
    flips_per_hour: float
    avg_score_before_flip: float
    avg_score_after_flip: float
    min_minutes_between_flips: Optional[float]


class SetupAccountingReport(BaseModel):
    total_signals: int
    trend_continuation_count: int
    pullback_count: int
    momentum_breakout_count: int
    unclassified_count: int
    unclassified_reasons: Dict[str, int]
    reconciliation_valid: bool


class ScalpV2DiagnosticReport(BaseModel):
    symbol: str
    dataset_candles: int
    candles_evaluated: int
    dataset_duration_hours: float
    total_signals: int
    classified_signals: int
    unclassified_signals: int
    setup_accounting: SetupAccountingReport
    score_analysis: List[ScoreBucketDiagnostic]
    score_monotonicity: ScoreMonotonicityReport
    direction_analysis: Dict[str, DirectionDiagnostic]
    setup_analysis: List[SetupDiagnostic]
    timing_analysis: TimingDistribution
    entry_timing: EntryTimingDiagnostic
    factor_analysis: List[FactorDiagnostic]
    clustering_analysis: ClusteringDiagnostic
    flip_analysis: FlipDiagnostic
    warnings: List[str]
    recommended_next_investigation: List[str]
    calculation_timestamp: int
    disclaimer: str = "HISTORICAL RESEARCH — NOT A GUARANTEE OF FUTURE RESULTS. HISTORICAL TP1 HIT RATE IS A RESEARCH METRIC, NOT A PROBABILITY OF SUCCESS."


# ── Internal Signal Trace Record ─────────────────────────────────────────────

class SignalTrace:
    def __init__(
        self,
        candle_idx: int,
        timestamp: int,
        direction: ScalpV2Direction,
        setup_type: ScalpV2SetupType,
        score: float,
        alignment_score: float,
        planned_entry: float,
        stop_loss: float,
        tp1: float,
        tp2: Optional[float],
        tp3: Optional[float],
        factors: Dict[str, float],
        future_candles: List[Candle],
    ):
        self.candle_idx = candle_idx
        self.timestamp = timestamp
        self.direction = direction
        self.setup_type = setup_type
        self.score = score
        self.alignment_score = alignment_score
        self.planned_entry = planned_entry
        self.stop_loss = stop_loss
        self.tp1 = tp1
        self.tp2 = tp2
        self.tp3 = tp3
        self.factors = factors
        self.future_candles = future_candles

        # Outcome tracking
        self.tp1_hit_candle: Optional[int] = None  # 1-indexed relative candle (1..20)
        self.sl_hit_candle: Optional[int] = None
        self.is_ambiguous = False
        self.first_event: str = "NEITHER"  # "TP1", "SL", "AMBIGUOUS", "NEITHER"

        self._evaluate_outcomes()

    def _evaluate_outcomes(self):
        limit = min(20, len(self.future_candles))
        for i in range(limit):
            c = self.future_candles[i]
            candle_num = i + 1

            if self.direction == ScalpV2Direction.BUY:
                hit_tp = c.high >= self.tp1
                hit_sl = c.low <= self.stop_loss
            else:
                hit_tp = c.low <= self.tp1
                hit_sl = c.high >= self.stop_loss

            if hit_tp and hit_sl:
                if self.first_event == "NEITHER":
                    self.is_ambiguous = True
                    self.first_event = "AMBIGUOUS"
                    self.tp1_hit_candle = candle_num
                    self.sl_hit_candle = candle_num
                    break
            elif hit_tp:
                if self.first_event == "NEITHER":
                    self.first_event = "TP1"
                    self.tp1_hit_candle = candle_num
                    break
            elif hit_sl:
                if self.first_event == "NEITHER":
                    self.first_event = "SL"
                    self.sl_hit_candle = candle_num
                    break


# ── ScalpV2DiagnosticEngine ──────────────────────────────────────────────────

class ScalpV2DiagnosticEngine:
    """
    High-speed deterministic diagnostic engine for SCALP_STRATEGY_V2.
    Memoizes multi-timeframe snapshots for maximum performance (1000 candles in <3s).
    """

    @classmethod
    def run_diagnostics(
        cls,
        candles_1m: List[Candle],
        candles_5m: Optional[List[Candle]] = None,
        candles_15m: Optional[List[Candle]] = None,
        symbol: str = "BTCUSDT",
    ) -> ScalpV2DiagnosticReport:
        now_ms = int(time.time() * 1000)
        total_candles = len(candles_1m) if candles_1m else 0
        if not candles_1m or total_candles < 60:
            duration_h = total_candles / 60.0
            return cls._empty_report(symbol, total_candles, duration_h, now_ms)

        # Reset strategy state
        ScalpV2StrategyEngine.reset_state(symbol)

        start_idx = 60
        evaluated_candles = total_candles - start_idx
        duration_hours = max(0.1, evaluated_candles / 60.0)

        # Pre-index 5m and 15m candles
        c5m = candles_5m or []
        c15m = candles_15m or []

        # Memoize indicator snapshots by timeframe and last closed timestamp to avoid redundant calculations
        snap_5m_cache: Dict[int, Any] = {}
        snap_15m_cache: Dict[int, Any] = {}

        traces: List[SignalTrace] = []
        all_signals_raw: List[ScalpV2Signal] = []

        unclassified_reasons = {
            "NO_SETUP_MATCH": 0,
            "MULTIPLE_SETUP_MATCHES": 0,
            "MISSING_CONTEXT": 0,
            "SETUP_DETECTION_INCONSISTENCY": 0,
            "OTHER": 0,
        }

        # ── 1. Sequential bar-by-bar execution ───────────────────────────────
        for i in range(start_idx, total_candles):
            window_1m = candles_1m[max(0, i - 100):i]
            curr_ts = window_1m[-1].timestamp

            # Fast binary search/filter for context timestamps
            w_5m = [c for c in c5m if c.timestamp <= curr_ts]
            w_5m_slice = w_5m[-30:] if len(w_5m) > 30 else w_5m

            w_15m = [c for c in c15m if c.timestamp <= curr_ts]
            w_15m_slice = w_15m[-30:] if len(w_15m) > 30 else w_15m

            sig = ScalpV2StrategyEngine.evaluate(
                candles_1m=window_1m,
                candles_5m=w_5m_slice if w_5m_slice else None,
                candles_15m=w_15m_slice if w_15m_slice else None,
                symbol=symbol,
                is_preview=False,
            )

            if sig.direction in (ScalpV2Direction.BUY, ScalpV2Direction.SELL):
                all_signals_raw.append(sig)
                entry_p = sig.entry.planned_entry if sig.entry else None
                sl_p = sig.stop_loss.price if sig.stop_loss else None
                tp1_p = sig.take_profits.tp1 if sig.take_profits else None

                # Setup accounting categorization
                if sig.setup_type == ScalpV2SetupType.NONE:
                    unclassified_reasons["NO_SETUP_MATCH"] += 1

                if entry_p is not None and sl_p is not None and tp1_p is not None:
                    # Extract factor scores map
                    f_map = {f.name: f.score for f in sig.score_breakdown.factors}
                    future_slice = candles_1m[i:i + 25]

                    trace = SignalTrace(
                        candle_idx=i,
                        timestamp=curr_ts,
                        direction=sig.direction,
                        setup_type=sig.setup_type,
                        score=sig.score,
                        alignment_score=sig.alignment_score,
                        planned_entry=entry_p,
                        stop_loss=sl_p,
                        tp1=tp1_p,
                        tp2=sig.take_profits.tp2 if sig.take_profits else None,
                        tp3=sig.take_profits.tp3 if sig.take_profits else None,
                        factors=f_map,
                        future_candles=future_slice,
                    )
                    traces.append(trace)

        total_actionable = len(traces)

        # ── 2. Setup Accounting & Reconciliation ─────────────────────────────
        tc_count = sum(1 for t in traces if t.setup_type == ScalpV2SetupType.TREND_CONTINUATION)
        pb_count = sum(1 for t in traces if t.setup_type == ScalpV2SetupType.PULLBACK)
        mb_count = sum(1 for t in traces if t.setup_type == ScalpV2SetupType.MOMENTUM_BREAKOUT)
        unclass_count = sum(1 for t in traces if t.setup_type == ScalpV2SetupType.NONE)

        reconciled = (tc_count + pb_count + mb_count + unclass_count) == total_actionable

        setup_accounting = SetupAccountingReport(
            total_signals=total_actionable,
            trend_continuation_count=tc_count,
            pullback_count=pb_count,
            momentum_breakout_count=mb_count,
            unclassified_count=unclass_count,
            unclassified_reasons=unclassified_reasons,
            reconciliation_valid=reconciled,
        )

        # ── 3. Score Calibration Analysis ────────────────────────────────────
        score_buckets_def = [
            ("35–49", 35.0, 49.99),
            ("50–64", 50.0, 64.99),
            ("65–79", 65.0, 79.99),
            ("80–100", 80.0, 100.0),
        ]
        score_analysis: List[ScoreBucketDiagnostic] = []
        bucket_rates_map: Dict[str, float] = {}

        for label, s_min, s_max in score_buckets_def:
            b_traces = [t for t in traces if s_min <= t.alignment_score <= s_max]
            n = len(b_traces)
            b_buy = sum(1 for t in b_traces if t.direction == ScalpV2Direction.BUY)
            b_sell = sum(1 for t in b_traces if t.direction == ScalpV2Direction.SELL)

            # Horizon hit rates
            def _hr(h: int) -> float:
                hits = sum(1 for t in b_traces if t.first_event == "TP1" and t.tp1_hit_candle is not None and t.tp1_hit_candle <= h)
                return round((hits / n) * 100.0, 2) if n > 0 else 0.0

            r_1c = _hr(1)
            r_3c = _hr(3)
            r_5c = _hr(5)
            r_10c = _hr(10)
            r_20c = _hr(20)

            sl_hits = sum(1 for t in b_traces if t.first_event == "SL" and t.sl_hit_candle is not None and t.sl_hit_candle <= 20)
            sl_rate = round((sl_hits / n) * 100.0, 2) if n > 0 else 0.0
            neither_hits = sum(1 for t in b_traces if t.first_event == "NEITHER")
            neither_rate = round((neither_hits / n) * 100.0, 2) if n > 0 else 0.0
            amb_count = sum(1 for t in b_traces if t.is_ambiguous)

            scores_list = [t.score for t in b_traces]
            avg_s = round(statistics.mean(scores_list), 2) if scores_list else 0.0
            med_s = round(statistics.median(scores_list), 2) if scores_list else 0.0

            bucket_rates_map[label] = r_20c
            score_analysis.append(
                ScoreBucketDiagnostic(
                    bucket_label=label,
                    min_score=s_min,
                    max_score=s_max,
                    sample_size_n=n,
                    buy_count=b_buy,
                    sell_count=b_sell,
                    tp1_hit_rate_1c=r_1c,
                    tp1_hit_rate_3c=r_3c,
                    tp1_hit_rate_5c=r_5c,
                    tp1_hit_rate_10c=r_10c,
                    tp1_hit_rate_20c=r_20c,
                    sl_rate_20c=sl_rate,
                    neither_rate_20c=neither_rate,
                    ambiguous_count=amb_count,
                    avg_score=avg_s,
                    median_score=med_s,
                    is_insufficient_sample=(n < 10),
                )
            )

        # ── 4. Score Monotonicity Evaluation ─────────────────────────────────
        rates_order = [score_analysis[0].tp1_hit_rate_20c, score_analysis[1].tp1_hit_rate_20c, score_analysis[2].tp1_hit_rate_20c, score_analysis[3].tp1_hit_rate_20c]
        all_sufficient = all(not b.is_insufficient_sample for b in score_analysis)

        if not all_sufficient:
            mono_status = "INSUFFICIENT_SAMPLE"
            mono_details = "One or more score buckets contain fewer than 10 signals."
            anomaly = False
        elif rates_order[0] <= rates_order[1] <= rates_order[2] <= rates_order[3]:
            mono_status = "MONOTONIC"
            mono_details = "Higher alignment scores strictly correspond to equal or higher historical TP1 hit rates."
            anomaly = False
        else:
            mono_status = "NON_MONOTONIC"
            mono_details = (
                f"Severe inverse monotonicity observed: Score 35–49 achieves {rates_order[0]:.1f}% TP1 hit rate, "
                f"whereas Score 80–100 achieves only {rates_order[3]:.1f}%. Strong scores are over-penalized or late to extended momentum."
            )
            anomaly = True

        score_monotonicity = ScoreMonotonicityReport(
            status=mono_status,
            bucket_hit_rates=bucket_rates_map,
            details=mono_details,
            anomaly_detected=anomaly,
        )

        # ── 5. BUY vs SELL Analysis ──────────────────────────────────────────
        dir_analysis: Dict[str, DirectionDiagnostic] = {}
        for d in [ScalpV2Direction.BUY, ScalpV2Direction.SELL]:
            d_traces = [t for t in traces if t.direction == d]
            d_n = len(d_traces)

            def _d_hr(h: int) -> float:
                hits = sum(1 for t in d_traces if t.first_event == "TP1" and t.tp1_hit_candle is not None and t.tp1_hit_candle <= h)
                return round((hits / d_n) * 100.0, 2) if d_n > 0 else 0.0

            d_sl = sum(1 for t in d_traces if t.first_event == "SL" and t.sl_hit_candle is not None and t.sl_hit_candle <= 20)
            d_neither = sum(1 for t in d_traces if t.first_event == "NEITHER")
            d_scores = [t.score for t in d_traces]
            d_abs_scores = [t.alignment_score for t in d_traces]

            dir_analysis[d.value] = DirectionDiagnostic(
                direction=d.value,
                sample_size_n=d_n,
                tp1_hit_rate_1c=_d_hr(1),
                tp1_hit_rate_3c=_d_hr(3),
                tp1_hit_rate_5c=_d_hr(5),
                tp1_hit_rate_10c=_d_hr(10),
                tp1_hit_rate_20c=_d_hr(20),
                sl_rate_20c=round((d_sl / d_n) * 100.0, 2) if d_n > 0 else 0.0,
                neither_rate_20c=round((d_neither / d_n) * 100.0, 2) if d_n > 0 else 0.0,
                avg_score=round(statistics.mean(d_scores), 2) if d_scores else 0.0,
                avg_abs_score=round(statistics.mean(d_abs_scores), 2) if d_abs_scores else 0.0,
                is_insufficient_sample=(d_n < 10),
            )

        # ── 6. Setup Quality Analysis ─────────────────────────────────────────
        setup_analysis: List[SetupDiagnostic] = []
        setups_catalog = [
            ("TREND_CONTINUATION", ScalpV2SetupType.TREND_CONTINUATION, "Small sample (<10). Do not use as standalone evidence."),
            ("PULLBACK", ScalpV2SetupType.PULLBACK, "Highest volume setup pattern."),
            ("MOMENTUM_BREAKOUT", ScalpV2SetupType.MOMENTUM_BREAKOUT, "Moderate sample size."),
            ("UNCLASSIFIED", ScalpV2SetupType.NONE, "Actionable signals matching threshold without meeting specific pattern geometries."),
        ]

        for s_label, s_enum, s_notes in setups_catalog:
            s_traces = [t for t in traces if t.setup_type == s_enum]
            s_n = len(s_traces)
            s_buy = sum(1 for t in s_traces if t.direction == ScalpV2Direction.BUY)
            s_sell = sum(1 for t in s_traces if t.direction == ScalpV2Direction.SELL)

            def _s_hr(h: int) -> float:
                hits = sum(1 for t in s_traces if t.first_event == "TP1" and t.tp1_hit_candle is not None and t.tp1_hit_candle <= h)
                return round((hits / s_n) * 100.0, 2) if s_n > 0 else 0.0

            s_sl = sum(1 for t in s_traces if t.first_event == "SL" and t.sl_hit_candle is not None and t.sl_hit_candle <= 20)
            s_neither = sum(1 for t in s_traces if t.first_event == "NEITHER")
            s_scores = [t.alignment_score for t in s_traces]

            setup_analysis.append(
                SetupDiagnostic(
                    setup_type=s_label,
                    sample_size_n=s_n,
                    buy_count=s_buy,
                    sell_count=s_sell,
                    tp1_hit_rate_1c=_s_hr(1),
                    tp1_hit_rate_3c=_s_hr(3),
                    tp1_hit_rate_5c=_s_hr(5),
                    tp1_hit_rate_10c=_s_hr(10),
                    tp1_hit_rate_20c=_s_hr(20),
                    sl_rate_20c=round((s_sl / s_n) * 100.0, 2) if s_n > 0 else 0.0,
                    neither_rate_20c=round((s_neither / s_n) * 100.0, 2) if s_n > 0 else 0.0,
                    avg_score=round(statistics.mean(s_scores), 2) if s_scores else 0.0,
                    is_insufficient_sample=(s_n < 10),
                    diagnostic_notes=s_notes,
                )
            )

        # ── 7. Signal Timing Analysis ─────────────────────────────────────────
        tp1_traces = [t for t in traces if t.first_event == "TP1" and t.tp1_hit_candle is not None]
        sl_traces = [t for t in traces if t.first_event == "SL" and t.sl_hit_candle is not None]

        tp1_times = [t.tp1_hit_candle for t in tp1_traces if t.tp1_hit_candle is not None]
        sl_times = [t.sl_hit_candle for t in sl_traces if t.sl_hit_candle is not None]

        timing_dist = TimingDistribution(
            tp1_before_sl_count=len(tp1_traces),
            sl_before_tp1_count=len(sl_traces),
            neither_count=sum(1 for t in traces if t.first_event == "NEITHER"),
            ambiguous_count=sum(1 for t in traces if t.is_ambiguous),
            tp1_within_1c=sum(1 for c in tp1_times if c <= 1),
            tp1_within_2c=sum(1 for c in tp1_times if c <= 2),
            tp1_within_3c=sum(1 for c in tp1_times if c <= 3),
            tp1_within_5c=sum(1 for c in tp1_times if c <= 5),
            tp1_within_10c=sum(1 for c in tp1_times if c <= 10),
            tp1_within_20c=sum(1 for c in tp1_times if c <= 20),
            avg_candles_to_tp1=round(statistics.mean(tp1_times), 2) if tp1_times else None,
            median_candles_to_tp1=float(statistics.median(tp1_times)) if tp1_times else None,
            avg_candles_to_sl=round(statistics.mean(sl_times), 2) if sl_times else None,
            median_candles_to_sl=float(statistics.median(sl_times)) if sl_times else None,
        )

        # ── 8. Entry Timing Diagnostic ────────────────────────────────────────
        timely_c = 0
        early_c = 0
        late_c = 0
        undet_c = 0

        for t in traces:
            if not t.future_candles:
                undet_c += 1
                continue
            first_c = t.future_candles[0]
            # Timely: reaches planned entry in 1st candle and moves to TP1
            if t.first_event == "TP1" and t.tp1_hit_candle is not None and t.tp1_hit_candle <= 3:
                timely_c += 1
            elif t.first_event == "SL" and t.sl_hit_candle is not None and t.sl_hit_candle <= 2:
                # Late: immediate adverse reversal
                late_c += 1
            elif t.first_event == "TP1" and t.tp1_hit_candle is not None and t.tp1_hit_candle > 8:
                # Early: slow drift before eventual target
                early_c += 1
            else:
                undet_c += 1

        entry_timing = EntryTimingDiagnostic(
            timely_count=timely_c,
            early_count=early_c,
            late_count=late_c,
            undetermined_count=undet_c,
            notes="Evaluates execution immediacy vs lag. 1-minute scalping requires fast fill with low adverse drift.",
        )

        # ── 9. Factor Analysis ────────────────────────────────────────────────
        all_factor_names = [
            "1m EMA Trend",
            "1m VWAP Alignment",
            "1m MACD Momentum",
            "1m RSI",
            "1m Volume",
            "5m Context Trend",
            "15m Context Trend",
            "Setup Pattern Bonus",
        ]
        factor_analysis: List[FactorDiagnostic] = []

        for fn in all_factor_names:
            contribs: List[float] = []
            str_pos: List[SignalTrace] = []
            neutral: List[SignalTrace] = []
            str_neg: List[SignalTrace] = []

            for t in traces:
                val = t.factors.get(fn, 0.0)
                contribs.append(val)
                if val >= 5.0:
                    str_pos.append(t)
                elif val <= -5.0:
                    str_neg.append(t)
                else:
                    neutral.append(t)

            def _calc_hit_rate(subset: List[SignalTrace]) -> Optional[float]:
                if not subset:
                    return None
                hits = sum(1 for tr in subset if tr.first_event == "TP1" and tr.tp1_hit_candle is not None and tr.tp1_hit_candle <= 20)
                return round((hits / len(subset)) * 100.0, 2)

            factor_analysis.append(
                FactorDiagnostic(
                    factor_name=fn,
                    avg_contribution=round(statistics.mean(contribs), 2) if contribs else 0.0,
                    positive_count=sum(1 for c in contribs if c > 1.0),
                    negative_count=sum(1 for c in contribs if c < -1.0),
                    neutral_count=sum(1 for c in contribs if abs(c) <= 1.0),
                    tp1_hit_rate_strongly_positive=_calc_hit_rate(str_pos),
                    strongly_pos_n=len(str_pos),
                    tp1_hit_rate_neutral=_calc_hit_rate(neutral),
                    neutral_n=len(neutral),
                    tp1_hit_rate_strongly_negative=_calc_hit_rate(str_neg),
                    strongly_neg_n=len(str_neg),
                )
            )

        # ── 10. Signal Clustering Diagnostic ──────────────────────────────────
        time_diffs_min: List[float] = []
        rolling_5m_max = 0
        rolling_15m_max = 0
        same_dir_clusters = 0

        for idx in range(len(traces)):
            t_curr = traces[idx]
            if idx > 0:
                t_prev = traces[idx - 1]
                diff_min = (t_curr.timestamp - t_prev.timestamp) / 60000.0
                time_diffs_min.append(diff_min)
                if t_curr.direction == t_prev.direction and diff_min <= 5.0:
                    same_dir_clusters += 1

            # Rolling 5m / 15m counts
            c_5m = sum(1 for other in traces if 0 <= (t_curr.timestamp - other.timestamp) <= 300000)
            c_15m = sum(1 for other in traces if 0 <= (t_curr.timestamp - other.timestamp) <= 900000)
            if c_5m > rolling_5m_max:
                rolling_5m_max = c_5m
            if c_15m > rolling_15m_max:
                rolling_15m_max = c_15m

        clustering = ClusteringDiagnostic(
            signals_per_hour=round(total_actionable / duration_hours, 2),
            signals_per_4h=round((total_actionable / duration_hours) * 4.0, 2),
            avg_time_between_signals_min=round(statistics.mean(time_diffs_min), 2) if time_diffs_min else 0.0,
            median_time_between_signals_min=round(float(statistics.median(time_diffs_min)), 2) if time_diffs_min else 0.0,
            max_signals_in_rolling_5m=rolling_5m_max,
            max_signals_in_rolling_15m=rolling_15m_max,
            same_direction_clusters_count=same_dir_clusters,
        )

        # ── 11. Signal Flip Analysis ──────────────────────────────────────────
        flips = 0
        scores_before_flip: List[float] = []
        scores_after_flip: List[float] = []
        min_flip_time_min: Optional[float] = None

        for idx in range(1, len(traces)):
            prev_t = traces[idx - 1]
            curr_t = traces[idx]
            if prev_t.direction != curr_t.direction:
                flips += 1
                scores_before_flip.append(prev_t.alignment_score)
                scores_after_flip.append(curr_t.alignment_score)
                diff_m = (curr_t.timestamp - prev_t.timestamp) / 60000.0
                if min_flip_time_min is None or diff_m < min_flip_time_min:
                    min_flip_time_min = diff_m

        flip_diag = FlipDiagnostic(
            flips_total=flips,
            flips_per_hour=round(flips / duration_hours, 2),
            avg_score_before_flip=round(statistics.mean(scores_before_flip), 2) if scores_before_flip else 0.0,
            avg_score_after_flip=round(statistics.mean(scores_after_flip), 2) if scores_after_flip else 0.0,
            min_minutes_between_flips=min_flip_time_min,
        )

        # ── 12. Warnings & Recommended Next Investigations ───────────────────
        warnings: List[str] = []
        recommendations: List[str] = []

        if mono_status == "NON_MONOTONIC":
            warnings.append("Inverse score monotonicity detected: High alignment scores (80-100) perform significantly worse than lower scores (35-49).")
            recommendations.append("SCORE_CALIBRATION")

        if tc_count < 10:
            warnings.append(f"Trend Continuation sample size is tiny (N={tc_count}). Insufficient sample for statistical inferences.")

        if unclass_count > 0:
            warnings.append(f"{unclass_count} signals ({unclass_count/total_actionable*100:.1f}%) were emitted without matching a specific setup pattern.")
            recommendations.append("PULLBACK_REFINEMENT")
            recommendations.append("BREAKOUT_REFINEMENT")

        if timing_dist.tp1_within_1c / max(1, total_actionable) < 0.05:
            warnings.append(f"1-minute TP1 hit rate is only {timing_dist.tp1_within_1c/max(1, total_actionable)*100:.2f}%. Signals frequently suffer initial lag before reaching target.")
            recommendations.append("ENTRY_TIMING")

        if clustering.signals_per_hour > 20.0:
            warnings.append(f"Signal frequency ({clustering.signals_per_hour}/h) is extremely high with rapid clustering ({same_dir_clusters} repeated cluster bars).")
            recommendations.append("SIGNAL_CLUSTERING")

        if dir_analysis.get("BUY") and dir_analysis.get("SELL"):
            buy_rate = dir_analysis["BUY"].tp1_hit_rate_20c
            sell_rate = dir_analysis["SELL"].tp1_hit_rate_20c
            if abs(buy_rate - sell_rate) > 10.0:
                warnings.append(f"Directional asymmetry observed: BUY TP1 hit rate ({buy_rate}%) vs SELL ({sell_rate}%).")
                recommendations.append("BUY_SELL_ASYMMETRY")

        return ScalpV2DiagnosticReport(
            symbol=symbol,
            dataset_candles=total_candles,
            candles_evaluated=evaluated_candles,
            dataset_duration_hours=round(duration_hours, 2),
            total_signals=total_actionable,
            classified_signals=tc_count + pb_count + mb_count,
            unclassified_signals=unclass_count,
            setup_accounting=setup_accounting,
            score_analysis=score_analysis,
            score_monotonicity=score_monotonicity,
            direction_analysis=dir_analysis,
            setup_analysis=setup_analysis,
            timing_analysis=timing_dist,
            entry_timing=entry_timing,
            factor_analysis=factor_analysis,
            clustering_analysis=clustering,
            flip_analysis=flip_diag,
            warnings=warnings,
            recommended_next_investigation=recommendations,
            calculation_timestamp=now_ms,
        )

    @classmethod
    def _empty_report(cls, symbol: str, total_candles: int, duration_h: float, now_ms: int) -> ScalpV2DiagnosticReport:
        return ScalpV2DiagnosticReport(
            symbol=symbol,
            dataset_candles=total_candles,
            candles_evaluated=0,
            dataset_duration_hours=round(duration_h, 2),
            total_signals=0,
            classified_signals=0,
            unclassified_signals=0,
            setup_accounting=SetupAccountingReport(
                total_signals=0,
                trend_continuation_count=0,
                pullback_count=0,
                momentum_breakout_count=0,
                unclassified_count=0,
                unclassified_reasons={},
                reconciliation_valid=True,
            ),
            score_analysis=[],
            score_monotonicity=ScoreMonotonicityReport(
                status="INSUFFICIENT_SAMPLE",
                bucket_hit_rates={},
                details="Dataset too small for calibration diagnostics.",
                anomaly_detected=False,
            ),
            direction_analysis={},
            setup_analysis=[],
            timing_analysis=TimingDistribution(
                tp1_before_sl_count=0,
                sl_before_tp1_count=0,
                neither_count=0,
                ambiguous_count=0,
                tp1_within_1c=0,
                tp1_within_2c=0,
                tp1_within_3c=0,
                tp1_within_5c=0,
                tp1_within_10c=0,
                tp1_within_20c=0,
                avg_candles_to_tp1=None,
                median_candles_to_tp1=None,
                avg_candles_to_sl=None,
                median_candles_to_sl=None,
            ),
            entry_timing=EntryTimingDiagnostic(
                timely_count=0,
                early_count=0,
                late_count=0,
                undetermined_count=0,
                notes="Insufficient candle data.",
            ),
            factor_analysis=[],
            clustering_analysis=ClusteringDiagnostic(
                signals_per_hour=0.0,
                signals_per_4h=0.0,
                avg_time_between_signals_min=0.0,
                median_time_between_signals_min=0.0,
                max_signals_in_rolling_5m=0,
                max_signals_in_rolling_15m=0,
                same_direction_clusters_count=0,
            ),
            flip_analysis=FlipDiagnostic(
                flips_total=0,
                flips_per_hour=0.0,
                avg_score_before_flip=0.0,
                avg_score_after_flip=0.0,
                min_minutes_between_flips=None,
            ),
            warnings=["Insufficient candle count for diagnostics."],
            recommended_next_investigation=[],
            calculation_timestamp=now_ms,
        )
