"""
SCALP_STRATEGY_V2 — Main Strategy Engine.
Independent higher-frequency 1m BTCUSDT strategy engine with duplicate protection,
in-memory history tracking, and frequency statistics monitor.
"""
import time
from typing import Dict, List, Optional
from collections import deque

from app.data.schema import Candle, CandleStateEnum
from app.indicators.engine import IndicatorEngine
from app.indicators.base import IndicatorSnapshot
from app.scalp_v2.version import SCALP_STRATEGY_V2_ID, SCALP_STRATEGY_V2_VERSION
from app.scalp_v2.config import (
    MAX_COOLDOWN_CANDLES,
    MAX_HISTORY_BUFFER_SIZE,
)
from app.scalp_v2.models import (
    ScalpV2Signal,
    ScalpV2Direction,
    ScalpV2SetupType,
    ScalpV2HistoryItem,
    ScalpV2StatsResponse,
)
from app.scalp_v2.signals import evaluate_scalp_v2_signal
from app.scalp_v2.trade_plan import generate_scalp_v2_trade_plan


class ScalpV2StrategyEngine:
    """
    Independent engine for SCALP_STRATEGY_V2.
    """
    # In-memory history buffer (per symbol)
    _history_buffers: Dict[str, deque] = {}
    _last_confirmed_signals: Dict[str, ScalpV2Signal] = {}
    _candles_since_signal: Dict[str, int] = {}
    _stats_counters: Dict[str, Dict] = {}

    @classmethod
    def _get_history_buffer(cls, symbol: str) -> deque:
        if symbol not in cls._history_buffers:
            cls._history_buffers[symbol] = deque(maxlen=MAX_HISTORY_BUFFER_SIZE)
        return cls._history_buffers[symbol]

    @classmethod
    def reset_state(cls, symbol: Optional[str] = None) -> None:
        """Reset state (useful for unit tests and deterministic isolation)."""
        if symbol:
            cls._history_buffers.pop(symbol, None)
            cls._last_confirmed_signals.pop(symbol, None)
            cls._candles_since_signal.pop(symbol, None)
            cls._stats_counters.pop(symbol, None)
        else:
            cls._history_buffers.clear()
            cls._last_confirmed_signals.clear()
            cls._candles_since_signal.clear()
            cls._stats_counters.clear()

    @classmethod
    def evaluate(
        cls,
        candles_1m: List[Candle],
        candles_5m: Optional[List[Candle]] = None,
        candles_15m: Optional[List[Candle]] = None,
        symbol: str = "BTCUSDT",
        is_preview: bool = False,
    ) -> ScalpV2Signal:
        """
        Evaluate candle data and produce a deterministic ScalpV2Signal.
        """
        if not candles_1m:
            return ScalpV2Signal(
                symbol=symbol,
                is_preview=is_preview,
                calculation_timestamp=int(time.time() * 1000),
            )

        # ── 1. Select candles for evaluation ─────────────────────────────────
        if is_preview:
            eval_1m = candles_1m
        else:
            eval_1m = [c for c in candles_1m if c.is_closed]
            if not eval_1m:
                eval_1m = candles_1m

        # ── 2. Compute Indicators ────────────────────────────────────────────
        snap_1m = IndicatorEngine.calculate_snapshot(
            eval_1m, symbol=symbol, timeframe="1m", is_confirmed=not is_preview
        )

        snap_5m: Optional[IndicatorSnapshot] = None
        if candles_5m:
            closed_5m = [c for c in candles_5m if c.is_closed]
            eval_5m = closed_5m if closed_5m else candles_5m
            if len(eval_5m) >= 5:
                snap_5m = IndicatorEngine.calculate_snapshot(
                    eval_5m, symbol=symbol, timeframe="5m", is_confirmed=True
                )

        snap_15m: Optional[IndicatorSnapshot] = None
        if candles_15m:
            closed_15m = [c for c in candles_15m if c.is_closed]
            eval_15m = closed_15m if closed_15m else candles_15m
            if len(eval_15m) >= 5:
                snap_15m = IndicatorEngine.calculate_snapshot(
                    eval_15m, symbol=symbol, timeframe="15m", is_confirmed=True
                )

        # ── 3. Evaluate Signal Multi-Factor Score & Setup ─────────────────────
        (
            raw_direction,
            strength,
            setup_type,
            net_score,
            alignment_score,
            breakdown,
            supporting,
            conflicting,
            trend_5m,
            trend_15m,
        ) = evaluate_scalp_v2_signal(
            candles_1m=eval_1m,
            snap_1m=snap_1m,
            snap_5m=snap_5m,
            snap_15m=snap_15m,
            symbol=symbol,
            is_preview=is_preview,
        )

        direction = raw_direction

        # ── 4. Apply Duplicate Protection & Cooldown (Confirmed only) ─────────
        if not is_preview and symbol in cls._last_confirmed_signals:
            last_sig = cls._last_confirmed_signals[symbol]
            current_ts = eval_1m[-1].timestamp
            last_ts = last_sig.candle_timestamp

            # Count candles if on a new candle
            if current_ts > last_ts:
                cls._candles_since_signal[symbol] = cls._candles_since_signal.get(symbol, 0) + 1
            
            candles_passed = cls._candles_since_signal.get(symbol, 0)

            # If same direction & same setup within cooldown window, convert to WATCH to avoid duplicate spam
            if (
                direction in (ScalpV2Direction.BUY, ScalpV2Direction.SELL)
                and direction == last_sig.direction
                and setup_type == last_sig.setup_type
                and candles_passed < MAX_COOLDOWN_CANDLES
            ):
                # Duplicate protection active
                direction = ScalpV2Direction.WATCH
                supporting.append(f"Duplicate protection active ({candles_passed}/{MAX_COOLDOWN_CANDLES} candles)")

        # ── 5. Generate Scalp Trade Plan ──────────────────────────────────────
        trade_state, lifecycle, entry, sl, tp, invalidations = generate_scalp_v2_trade_plan(
            candles_1m=eval_1m,
            snap_1m=snap_1m,
            direction=direction,
        )

        last_candle_ts = eval_1m[-1].timestamp if eval_1m else 0
        calc_ts = int(time.time() * 1000)

        signal = ScalpV2Signal(
            strategy_id=SCALP_STRATEGY_V2_ID,
            strategy_version=SCALP_STRATEGY_V2_VERSION,
            symbol=symbol,
            primary_timeframe="1m",
            direction=direction,
            trade_state=trade_state,
            lifecycle=lifecycle,
            setup_type=setup_type,
            score=net_score,
            alignment_score=alignment_score,
            strength=strength,
            is_preview=is_preview,
            candle_timestamp=last_candle_ts,
            calculation_timestamp=calc_ts,
            score_breakdown=breakdown,
            entry=entry,
            stop_loss=sl,
            take_profits=tp,
            supporting_factors=supporting,
            conflicting_factors=conflicting,
            invalidation_conditions=invalidations,
            context_5m_trend=trend_5m,
            context_15m_trend=trend_15m,
        )

        # ── 6. Record Confirmed Signal into History Buffer ────────────────────
        if not is_preview:
            # Check if this is a newly closed candle
            prev_sig = cls._last_confirmed_signals.get(symbol)
            if prev_sig is None or prev_sig.candle_timestamp != signal.candle_timestamp:
                history_buf = cls._get_history_buffer(symbol)
                history_item = ScalpV2HistoryItem(
                    timestamp=signal.candle_timestamp,
                    direction=signal.direction,
                    score=signal.score,
                    alignment_score=signal.alignment_score,
                    setup_type=signal.setup_type,
                    strength=signal.strength,
                    entry_price=signal.entry.planned_entry,
                    stop_loss=signal.stop_loss.price,
                    tp1=signal.take_profits.tp1,
                    lifecycle=signal.lifecycle,
                )
                history_buf.append(history_item)

                if signal.direction in (ScalpV2Direction.BUY, ScalpV2Direction.SELL):
                    cls._candles_since_signal[symbol] = 0

            cls._last_confirmed_signals[symbol] = signal

        return signal

    @classmethod
    def get_history(cls, symbol: str = "BTCUSDT", limit: int = 50) -> List[ScalpV2HistoryItem]:
        """Return recent signal history."""
        buf = cls._get_history_buffer(symbol)
        items = list(buf)
        return items[-limit:] if limit > 0 else items

    @classmethod
    def get_stats(cls, symbol: str = "BTCUSDT") -> ScalpV2StatsResponse:
        """Compute frequency and diagnostic statistics for V2."""
        buf = cls._get_history_buffer(symbol)
        items = list(buf)
        now_ms = int(time.time() * 1000)

        one_hour_ms = 60 * 60 * 1000
        four_hours_ms = 4 * one_hour_ms
        twenty_four_hours_ms = 24 * one_hour_ms

        signals_1h = [i for i in items if now_ms - i.timestamp <= one_hour_ms and i.direction in (ScalpV2Direction.BUY, ScalpV2Direction.SELL)]
        signals_4h = [i for i in items if now_ms - i.timestamp <= four_hours_ms and i.direction in (ScalpV2Direction.BUY, ScalpV2Direction.SELL)]
        signals_24h = [i for i in items if now_ms - i.timestamp <= twenty_four_hours_ms and i.direction in (ScalpV2Direction.BUY, ScalpV2Direction.SELL)]

        buy_count = sum(1 for i in items if i.direction == ScalpV2Direction.BUY)
        sell_count = sum(1 for i in items if i.direction == ScalpV2Direction.SELL)
        watch_count = sum(1 for i in items if i.direction == ScalpV2Direction.WATCH)
        no_trade_count = sum(1 for i in items if i.direction == ScalpV2Direction.NO_TRADE)

        scores = [i.score for i in items] if items else [0.0]
        abs_scores = [i.alignment_score for i in items] if items else [0.0]

        setup_dist: Dict[str, int] = {
            ScalpV2SetupType.TREND_CONTINUATION.value: sum(1 for i in items if i.setup_type == ScalpV2SetupType.TREND_CONTINUATION),
            ScalpV2SetupType.PULLBACK.value: sum(1 for i in items if i.setup_type == ScalpV2SetupType.PULLBACK),
            ScalpV2SetupType.MOMENTUM_BREAKOUT.value: sum(1 for i in items if i.setup_type == ScalpV2SetupType.MOMENTUM_BREAKOUT),
            ScalpV2SetupType.NONE.value: sum(1 for i in items if i.setup_type == ScalpV2SetupType.NONE),
        }

        return ScalpV2StatsResponse(
            strategy_id=SCALP_STRATEGY_V2_ID,
            symbol=symbol,
            total_candles_evaluated=len(items),
            signals_last_hour=len(signals_1h),
            signals_last_4_hours=len(signals_4h),
            signals_last_24_hours=len(signals_24h),
            buy_count=buy_count,
            sell_count=sell_count,
            watch_count=watch_count,
            no_trade_count=no_trade_count,
            average_score=round(sum(scores) / len(scores), 2) if scores else 0.0,
            average_abs_score=round(sum(abs_scores) / len(abs_scores), 2) if abs_scores else 0.0,
            min_score=min(scores) if scores else 0.0,
            max_score=max(scores) if scores else 0.0,
            setup_distribution=setup_dist,
            calculation_timestamp=now_ms,
        )
