"""
SCALP_STRATEGY_V2 — Signal Quality & Historical Outcome Evaluation Layer.

Pure, deterministic historical evaluation engine that benchmarks SCALP_STRATEGY_V2
against chronological 1-minute BTCUSDT candles with zero future leakage.
"""
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
import time

from app.data.schema import Candle
from app.scalp.engine import ScalpStrategyEngine as ScalpV1Engine
from app.scalp.models import ScalpDirection as ScalpV1Direction
from app.scalp_v2.engine import ScalpV2StrategyEngine
from app.scalp_v2.models import ScalpV2Direction, ScalpV2SetupType


class HorizonResult(BaseModel):
    horizon_candles: int
    signals: int
    tp1_hits: int
    sl_hits: int
    ambiguous: int
    neither: int
    historical_tp1_hit_rate: float = Field(
        description="Historical TP1 hit percentage. Strictly labeled Historical TP1 Hit Rate, not probability."
    )


class SetupQualityResult(BaseModel):
    setup_type: str
    signals: int
    tp1_hits: int
    sl_hits: int
    ambiguous: int
    neither: int
    historical_tp1_hit_rate: float


class ScoreBucketResult(BaseModel):
    bucket_label: str
    min_score: float
    max_score: float
    signals: int
    buy_count: int
    sell_count: int
    tp1_hits: int
    sl_hits: int
    ambiguous: int
    neither: int
    historical_tp1_hit_rate: float


class SignalFrequencyComparison(BaseModel):
    dataset_duration_hours: float
    candles_evaluated: int
    v1_signals: int
    v1_signals_per_hour: float
    v2_signals: int
    v2_signals_per_hour: float


class ScalpV2EvaluationReport(BaseModel):
    symbol: str
    dataset_candles: int
    candles_evaluated: int
    dataset_duration_hours: float
    total_signals: int
    buy_signals: int
    sell_signals: int
    watch_states: int
    no_trade_states: int
    frequency_comparison: SignalFrequencyComparison
    horizon_analysis: List[HorizonResult]
    score_breakdown: List[ScoreBucketResult]
    setup_breakdown: List[SetupQualityResult]
    best_performing_score_bucket: str
    calculation_timestamp: int
    disclaimer: str = "This is historical signal analysis, not a prediction of future results."


class EvaluatedSignalOutcome:
    """Internal lightweight structure tracking a signal and its multi-horizon outcomes."""
    def __init__(
        self,
        candle_idx: int,
        timestamp: int,
        direction: ScalpV2Direction,
        score: float,
        setup_type: ScalpV2SetupType,
        entry: float,
        stop_loss: float,
        tp1: float,
        tp2: Optional[float],
        tp3: Optional[float],
    ):
        self.candle_idx = candle_idx
        self.timestamp = timestamp
        self.direction = direction
        self.score = score
        self.setup_type = setup_type
        self.entry = entry
        self.stop_loss = stop_loss
        self.tp1 = tp1
        self.tp2 = tp2
        self.tp3 = tp3
        # Mapping horizon (1, 3, 5, 10, 20) -> outcome status: 'TP1_HIT', 'SL_HIT', 'AMBIGUOUS', 'NEITHER'
        self.horizon_outcomes: Dict[int, str] = {}


def evaluate_signal_against_future_candles(
    signal: EvaluatedSignalOutcome,
    future_candles: List[Candle],
    horizon: int,
) -> str:
    """
    Chronologically inspect future closed candles up to horizon limit.
    Zero future leakage: strictly sequential examination.
    
    Returns:
        'TP1_HIT' | 'SL_HIT' | 'AMBIGUOUS' | 'NEITHER'
    """
    limit = min(horizon, len(future_candles))
    if limit == 0:
        return "NEITHER"

    for i in range(limit):
        c = future_candles[i]

        if signal.direction == ScalpV2Direction.BUY:
            hit_tp = c.high >= signal.tp1
            hit_sl = c.low <= signal.stop_loss

            if hit_tp and hit_sl:
                return "AMBIGUOUS"
            if hit_tp:
                return "TP1_HIT"
            if hit_sl:
                return "SL_HIT"

        elif signal.direction == ScalpV2Direction.SELL:
            hit_tp = c.low <= signal.tp1
            hit_sl = c.high >= signal.stop_loss

            if hit_tp and hit_sl:
                return "AMBIGUOUS"
            if hit_tp:
                return "TP1_HIT"
            if hit_sl:
                return "SL_HIT"

    return "NEITHER"


def run_scalp_v2_historical_evaluation(
    candles_1m: List[Candle],
    candles_5m: Optional[List[Candle]] = None,
    candles_15m: Optional[List[Candle]] = None,
    symbol: str = "BTCUSDT",
) -> ScalpV2EvaluationReport:
    """
    Run fast chronological evaluation of SCALP_STRATEGY_V2 over the dataset.
    Compares frequency against frozen V1 baseline without altering any strategy code.
    """
    if not candles_1m or len(candles_1m) < 60:
        duration_h = len(candles_1m) / 60.0 if candles_1m else 0.0
        return ScalpV2EvaluationReport(
            symbol=symbol,
            dataset_candles=len(candles_1m) if candles_1m else 0,
            candles_evaluated=0,
            dataset_duration_hours=round(duration_h, 2),
            total_signals=0,
            buy_signals=0,
            sell_signals=0,
            watch_states=0,
            no_trade_states=0,
            frequency_comparison=SignalFrequencyComparison(
                dataset_duration_hours=round(duration_h, 2),
                candles_evaluated=0,
                v1_signals=0,
                v1_signals_per_hour=0.0,
                v2_signals=0,
                v2_signals_per_hour=0.0,
            ),
            horizon_analysis=[],
            score_breakdown=[],
            setup_breakdown=[],
            best_performing_score_bucket="N/A",
            calculation_timestamp=int(time.time() * 1000),
        )

    # Reset engine state for clean sequential reproducibility
    ScalpV2StrategyEngine.reset_state(symbol)

    horizons = [1, 3, 5, 10, 20]
    evaluated_signals: List[EvaluatedSignalOutcome] = []

    buy_count = 0
    sell_count = 0
    watch_count = 0
    no_trade_count = 0
    v1_signal_count = 0

    start_idx = 60
    total_candles = len(candles_1m)

    for i in range(start_idx, total_candles):
        window_1m = candles_1m[max(0, i - 100):i]
        curr_ts = window_1m[-1].timestamp

        window_5m = [c for c in (candles_5m or []) if c.timestamp <= curr_ts]
        if len(window_5m) > 30:
            window_5m = window_5m[-30:]

        window_15m = [c for c in (candles_15m or []) if c.timestamp <= curr_ts]
        if len(window_15m) > 30:
            window_15m = window_15m[-30:]

        # ── 1. Evaluate V2 ───────────────────────────────────────────────────
        sig_v2 = ScalpV2StrategyEngine.evaluate(
            candles_1m=window_1m,
            candles_5m=window_5m if window_5m else None,
            candles_15m=window_15m if window_15m else None,
            symbol=symbol,
            is_preview=False,
        )

        # ── 2. Evaluate V1 (strictly for objective frequency comparison) ─────
        sig_v1 = ScalpV1Engine.evaluate(
            candles_1m=window_1m,
            candles_5m=window_5m if window_5m else None,
            candles_15m=window_15m if window_15m else None,
            symbol=symbol,
            is_preview=False,
        )
        if sig_v1.direction in (ScalpV1Direction.BUY, ScalpV1Direction.SELL):
            v1_signal_count += 1

        if sig_v2.direction == ScalpV2Direction.BUY:
            buy_count += 1
        elif sig_v2.direction == ScalpV2Direction.SELL:
            sell_count += 1
        elif sig_v2.direction == ScalpV2Direction.WATCH:
            watch_count += 1
        else:
            no_trade_count += 1

        if sig_v2.direction in (ScalpV2Direction.BUY, ScalpV2Direction.SELL):
            entry_p = sig_v2.entry.planned_entry if sig_v2.entry else None
            sl_p = sig_v2.stop_loss.price if sig_v2.stop_loss else None
            tp1_p = sig_v2.take_profits.tp1 if sig_v2.take_profits else None

            if entry_p is not None and sl_p is not None and tp1_p is not None:
                record = EvaluatedSignalOutcome(
                    candle_idx=i,
                    timestamp=curr_ts,
                    direction=sig_v2.direction,
                    score=sig_v2.alignment_score,
                    setup_type=sig_v2.setup_type,
                    entry=entry_p,
                    stop_loss=sl_p,
                    tp1=tp1_p,
                    tp2=sig_v2.take_profits.tp2 if sig_v2.take_profits else None,
                    tp3=sig_v2.take_profits.tp3 if sig_v2.take_profits else None,
                )

                # Evaluate outcomes for each horizon using subsequent candles
                future_slice = candles_1m[i:i + 20]
                for h in horizons:
                    outcome = evaluate_signal_against_future_candles(record, future_slice, h)
                    record.horizon_outcomes[h] = outcome

                evaluated_signals.append(record)

    evaluated_candle_count = total_candles - start_idx
    duration_hours = max(0.1, evaluated_candle_count / 60.0)
    total_v2_signals = buy_count + sell_count

    # ── Horizon Analysis Table ───────────────────────────────────────────────
    horizon_results: List[HorizonResult] = []
    for h in horizons:
        h_signals = len(evaluated_signals)
        tp1_hits = sum(1 for s in evaluated_signals if s.horizon_outcomes.get(h) == "TP1_HIT")
        sl_hits = sum(1 for s in evaluated_signals if s.horizon_outcomes.get(h) == "SL_HIT")
        ambiguous = sum(1 for s in evaluated_signals if s.horizon_outcomes.get(h) == "AMBIGUOUS")
        neither = sum(1 for s in evaluated_signals if s.horizon_outcomes.get(h) == "NEITHER")
        hit_rate = round((tp1_hits / h_signals) * 100.0, 2) if h_signals > 0 else 0.0

        horizon_results.append(
            HorizonResult(
                horizon_candles=h,
                signals=h_signals,
                tp1_hits=tp1_hits,
                sl_hits=sl_hits,
                ambiguous=ambiguous,
                neither=neither,
                historical_tp1_hit_rate=hit_rate,
            )
        )

    # ── Score Breakdown Buckets (35-49, 50-64, 65-79, 80-100) ─────────────────
    # Evaluated at reference horizon 20
    ref_h = 20
    buckets_def = [
        ("35–49", 35.0, 49.99),
        ("50–64", 50.0, 64.99),
        ("65–79", 65.0, 79.99),
        ("80–100", 80.0, 100.0),
    ]

    score_results: List[ScoreBucketResult] = []
    best_bucket_label = "N/A"
    best_bucket_rate = -1.0

    for label, min_s, max_s in buckets_def:
        bucket_sigs = [s for s in evaluated_signals if min_s <= s.score <= max_s]
        b_total = len(bucket_sigs)
        b_buy = sum(1 for s in bucket_sigs if s.direction == ScalpV2Direction.BUY)
        b_sell = sum(1 for s in bucket_sigs if s.direction == ScalpV2Direction.SELL)
        b_tp1 = sum(1 for s in bucket_sigs if s.horizon_outcomes.get(ref_h) == "TP1_HIT")
        b_sl = sum(1 for s in bucket_sigs if s.horizon_outcomes.get(ref_h) == "SL_HIT")
        b_amb = sum(1 for s in bucket_sigs if s.horizon_outcomes.get(ref_h) == "AMBIGUOUS")
        b_neither = sum(1 for s in bucket_sigs if s.horizon_outcomes.get(ref_h) == "NEITHER")
        b_rate = round((b_tp1 / b_total) * 100.0, 2) if b_total > 0 else 0.0

        if b_total >= 3 and b_rate > best_bucket_rate:
            best_bucket_rate = b_rate
            best_bucket_label = f"{label} ({b_rate:.1f}%)"

        score_results.append(
            ScoreBucketResult(
                bucket_label=label,
                min_score=min_s,
                max_score=max_s,
                signals=b_total,
                buy_count=b_buy,
                sell_count=b_sell,
                tp1_hits=b_tp1,
                sl_hits=b_sl,
                ambiguous=b_amb,
                neither=b_neither,
                historical_tp1_hit_rate=b_rate,
            )
        )

    # ── Setup Type Breakdown (TREND_CONTINUATION, PULLBACK, MOMENTUM_BREAKOUT) ─
    setups_def = [
        ("TREND_CONTINUATION", ScalpV2SetupType.TREND_CONTINUATION),
        ("PULLBACK", ScalpV2SetupType.PULLBACK),
        ("MOMENTUM_BREAKOUT", ScalpV2SetupType.MOMENTUM_BREAKOUT),
    ]

    setup_results: List[SetupQualityResult] = []
    for label, st in setups_def:
        st_sigs = [s for s in evaluated_signals if s.setup_type == st]
        st_total = len(st_sigs)
        st_tp1 = sum(1 for s in st_sigs if s.horizon_outcomes.get(ref_h) == "TP1_HIT")
        st_sl = sum(1 for s in st_sigs if s.horizon_outcomes.get(ref_h) == "SL_HIT")
        st_amb = sum(1 for s in st_sigs if s.horizon_outcomes.get(ref_h) == "AMBIGUOUS")
        st_neither = sum(1 for s in st_sigs if s.horizon_outcomes.get(ref_h) == "NEITHER")
        st_rate = round((st_tp1 / st_total) * 100.0, 2) if st_total > 0 else 0.0

        setup_results.append(
            SetupQualityResult(
                setup_type=label,
                signals=st_total,
                tp1_hits=st_tp1,
                sl_hits=st_sl,
                ambiguous=st_amb,
                neither=st_neither,
                historical_tp1_hit_rate=st_rate,
            )
        )

    freq_comp = SignalFrequencyComparison(
        dataset_duration_hours=round(duration_hours, 2),
        candles_evaluated=evaluated_candle_count,
        v1_signals=v1_signal_count,
        v1_signals_per_hour=round(v1_signal_count / duration_hours, 2),
        v2_signals=total_v2_signals,
        v2_signals_per_hour=round(total_v2_signals / duration_hours, 2),
    )

    return ScalpV2EvaluationReport(
        symbol=symbol,
        dataset_candles=total_candles,
        candles_evaluated=evaluated_candle_count,
        dataset_duration_hours=round(duration_hours, 2),
        total_signals=total_v2_signals,
        buy_signals=buy_count,
        sell_signals=sell_count,
        watch_states=watch_count,
        no_trade_states=no_trade_count,
        frequency_comparison=freq_comp,
        horizon_analysis=horizon_results,
        score_breakdown=score_results,
        setup_breakdown=setup_results,
        best_performing_score_bucket=best_bucket_label,
        calculation_timestamp=int(time.time() * 1000),
    )
