"""
SCALP_STRATEGY_V1 — Deterministic scoring engine for 1m BTCUSDT scalping.

Scoring Model (BUY side, symmetric for SELL):
  +20  1m EMA 9 > EMA 21            (trend alignment)
  +15  1m price >= VWAP             (VWAP position)
  +15  1m RSI bullish               (30-70 = neutral, <30 = oversold buy bonus, >70 mild penalty)
  +15  1m MACD bullish              (histogram + crossover)
  +10  1m volume confirmation       (relative volume >= 0.8)
  +15  5m trend bullish             (EMA 9 > EMA 21 on 5m)
  +10  15m context supportive       (not strongly bearish)

BUY threshold  : net_score >= +45
SELL threshold : net_score <= -45

This engine is COMPLETELY INDEPENDENT of:
  - Phase 5 MultiFactorSignalEngine
  - Phase 10 TradeDecisionEngine
  - Phase 6 Backtesting
  - Phase 7 Forensics
  - Phase 8 Strategy Research
  - Phase 9 Shadow Validation

These engines remain frozen and unmodified.
"""
import time
from typing import List, Optional, Tuple

from app.data.schema import Candle, CandleStateEnum
from app.indicators.engine import IndicatorEngine
from app.indicators.base import IndicatorSnapshot
from app.scalp.models import (
    ScalpSignal,
    ScalpDirection,
    ScalpScoreBreakdown,
    ScalpScoreFactor,
    ScalpTradePlan,
)


# ── Scoring weights ──────────────────────────────────────────────────────────
W_EMA_TREND  = 20.0  # 1m EMA 9 vs EMA 21
W_VWAP       = 15.0  # 1m price vs VWAP
W_RSI        = 15.0  # 1m RSI
W_MACD       = 15.0  # 1m MACD histogram
W_VOLUME     = 10.0  # 1m relative volume
W_5M_TREND   = 15.0  # 5m EMA trend context
W_15M_CTX    = 10.0  # 15m context (not strongly opposing)

BUY_THRESHOLD  =  45.0   # net bull score needed (4-5 of 7 factors aligning)
SELL_THRESHOLD = -45.0   # net bear score needed (signed)


def _ema_trend_score(snap: IndicatorSnapshot) -> ScalpScoreFactor:
    """1m EMA 9 vs EMA 21 crossover alignment."""
    e9 = snap.trend.ema_9
    e21 = snap.trend.ema_21
    if e9 is None or e21 is None:
        return ScalpScoreFactor(
            name="EMA Trend (1m)", timeframe="1m",
            score=0.0, max_score=W_EMA_TREND,
            direction="NEUTRAL", detail="EMA data unavailable"
        )
    diff = e9 - e21
    if diff > 0:
        # Stronger the gap relative to e21, more conviction
        pct = min(abs(diff) / e21 * 100, 1.0) if e21 > 0 else 0.0
        score = W_EMA_TREND * (0.5 + 0.5 * pct / 0.1)   # full at 0.1% gap
        score = min(score, W_EMA_TREND)
        return ScalpScoreFactor(
            name="EMA Trend (1m)", timeframe="1m",
            score=score, max_score=W_EMA_TREND,
            direction="BULLISH",
            detail=f"EMA9 {e9:.2f} > EMA21 {e21:.2f} (+{diff:.2f})"
        )
    else:
        pct = min(abs(diff) / e21 * 100, 1.0) if e21 > 0 else 0.0
        score = -(W_EMA_TREND * (0.5 + 0.5 * pct / 0.1))
        score = max(score, -W_EMA_TREND)
        return ScalpScoreFactor(
            name="EMA Trend (1m)", timeframe="1m",
            score=score, max_score=W_EMA_TREND,
            direction="BEARISH",
            detail=f"EMA9 {e9:.2f} < EMA21 {e21:.2f} ({diff:.2f})"
        )


def _vwap_score(snap: IndicatorSnapshot, close: float) -> ScalpScoreFactor:
    """1m price vs VWAP."""
    vwap = snap.trend.vwap
    if vwap is None or vwap <= 0:
        return ScalpScoreFactor(
            name="VWAP Position (1m)", timeframe="1m",
            score=0.0, max_score=W_VWAP,
            direction="NEUTRAL", detail="VWAP unavailable"
        )
    pct_from_vwap = (close - vwap) / vwap * 100
    if pct_from_vwap >= 0:
        score = min(W_VWAP, W_VWAP * (1.0 + pct_from_vwap / 0.2))
        return ScalpScoreFactor(
            name="VWAP Position (1m)", timeframe="1m",
            score=score, max_score=W_VWAP,
            direction="BULLISH",
            detail=f"Price {close:.2f} above VWAP {vwap:.2f} (+{pct_from_vwap:.3f}%)"
        )
    else:
        score = max(-W_VWAP, W_VWAP * (pct_from_vwap / 0.2))
        score = max(score, -W_VWAP)
        return ScalpScoreFactor(
            name="VWAP Position (1m)", timeframe="1m",
            score=score, max_score=W_VWAP,
            direction="BEARISH",
            detail=f"Price {close:.2f} below VWAP {vwap:.2f} ({pct_from_vwap:.3f}%)"
        )


def _rsi_score(snap: IndicatorSnapshot) -> ScalpScoreFactor:
    """1m RSI — context-aware scoring."""
    rsi = snap.momentum.rsi
    if rsi is None:
        return ScalpScoreFactor(
            name="RSI (1m)", timeframe="1m",
            score=0.0, max_score=W_RSI,
            direction="NEUTRAL", detail="RSI unavailable"
        )
    # RSI ranges and their scores
    if rsi <= 30:
        # Oversold → strong BUY lean
        score = W_RSI
        direction = "BULLISH"
        detail = f"RSI {rsi:.1f} — oversold, bullish reversal zone"
    elif rsi <= 45:
        score = W_RSI * 0.6
        direction = "BULLISH"
        detail = f"RSI {rsi:.1f} — below midline, mild bullish"
    elif rsi <= 55:
        score = 0.0
        direction = "NEUTRAL"
        detail = f"RSI {rsi:.1f} — neutral midband"
    elif rsi <= 65:
        score = -W_RSI * 0.4
        direction = "BEARISH"
        detail = f"RSI {rsi:.1f} — above midline, mild bearish"
    elif rsi <= 70:
        score = -W_RSI * 0.7
        direction = "BEARISH"
        detail = f"RSI {rsi:.1f} — approaching overbought"
    else:
        # Overbought → strong SELL lean
        score = -W_RSI
        direction = "BEARISH"
        detail = f"RSI {rsi:.1f} — overbought, bearish reversal zone"
    return ScalpScoreFactor(
        name="RSI (1m)", timeframe="1m",
        score=score, max_score=W_RSI,
        direction=direction, detail=detail
    )


def _macd_score(snap: IndicatorSnapshot) -> ScalpScoreFactor:
    """1m MACD histogram — positive = bullish momentum."""
    hist = snap.momentum.macd_histogram
    if hist is None:
        return ScalpScoreFactor(
            name="MACD (1m)", timeframe="1m",
            score=0.0, max_score=W_MACD,
            direction="NEUTRAL", detail="MACD unavailable"
        )
    if hist > 0:
        score = min(W_MACD, W_MACD * (abs(hist) / 5.0 + 0.5))
        score = min(score, W_MACD)
        direction = "BULLISH"
        detail = f"MACD hist +{hist:.3f} — positive momentum"
    else:
        score = max(-W_MACD, -(W_MACD * (abs(hist) / 5.0 + 0.5)))
        score = max(score, -W_MACD)
        direction = "BEARISH"
        detail = f"MACD hist {hist:.3f} — negative momentum"
    return ScalpScoreFactor(
        name="MACD (1m)", timeframe="1m",
        score=score, max_score=W_MACD,
        direction=direction, detail=detail
    )


def _volume_score(snap: IndicatorSnapshot) -> ScalpScoreFactor:
    """1m relative volume confirmation — volume neutrally boosts conviction."""
    rvol = snap.volume.relative_volume
    if rvol is None:
        return ScalpScoreFactor(
            name="Volume (1m)", timeframe="1m",
            score=0.0, max_score=W_VOLUME,
            direction="NEUTRAL", detail="Volume data unavailable"
        )
    if rvol >= 1.5:
        score = W_VOLUME
        detail = f"RVOL {rvol:.2f}x — above average, high conviction"
    elif rvol >= 0.9:
        score = W_VOLUME * 0.7
        detail = f"RVOL {rvol:.2f}x — normal volume"
    elif rvol >= 0.6:
        score = W_VOLUME * 0.3
        detail = f"RVOL {rvol:.2f}x — below average volume"
    else:
        score = 0.0
        detail = f"RVOL {rvol:.2f}x — very low volume, weak"
    return ScalpScoreFactor(
        name="Volume (1m)", timeframe="1m",
        score=score, max_score=W_VOLUME,
        direction="NEUTRAL", detail=detail
    )


def _context_5m_score(snap_5m: Optional[IndicatorSnapshot]) -> Tuple[ScalpScoreFactor, str]:
    """5m EMA trend context."""
    if snap_5m is None:
        return ScalpScoreFactor(
            name="5m Trend Context", timeframe="5m",
            score=0.0, max_score=W_5M_TREND,
            direction="NEUTRAL", detail="5m data unavailable"
        ), "UNKNOWN"
    e9 = snap_5m.trend.ema_9
    e21 = snap_5m.trend.ema_21
    rsi5 = snap_5m.momentum.rsi
    if e9 is None or e21 is None:
        return ScalpScoreFactor(
            name="5m Trend Context", timeframe="5m",
            score=0.0, max_score=W_5M_TREND,
            direction="NEUTRAL", detail="5m EMA unavailable"
        ), "UNKNOWN"
    if e9 > e21:
        rsi_boost = 0.2 if rsi5 and rsi5 < 55 else 0.0
        score = W_5M_TREND * (0.8 + rsi_boost)
        score = min(score, W_5M_TREND)
        return ScalpScoreFactor(
            name="5m Trend Context", timeframe="5m",
            score=score, max_score=W_5M_TREND,
            direction="BULLISH",
            detail=f"5m EMA9 {e9:.2f} > EMA21 {e21:.2f} — uptrend"
        ), "BULLISH"
    else:
        rsi_boost = 0.2 if rsi5 and rsi5 > 45 else 0.0
        score = -(W_5M_TREND * (0.8 + rsi_boost))
        score = max(score, -W_5M_TREND)
        return ScalpScoreFactor(
            name="5m Trend Context", timeframe="5m",
            score=score, max_score=W_5M_TREND,
            direction="BEARISH",
            detail=f"5m EMA9 {e9:.2f} < EMA21 {e21:.2f} — downtrend"
        ), "BEARISH"


def _context_15m_score(snap_15m: Optional[IndicatorSnapshot]) -> Tuple[ScalpScoreFactor, str]:
    """15m context — only penalises if strongly opposing."""
    if snap_15m is None:
        return ScalpScoreFactor(
            name="15m Context", timeframe="15m",
            score=0.0, max_score=W_15M_CTX,
            direction="NEUTRAL", detail="15m data unavailable"
        ), "UNKNOWN"
    e9 = snap_15m.trend.ema_9
    e21 = snap_15m.trend.ema_21
    rsi15 = snap_15m.momentum.rsi
    if e9 is None or e21 is None:
        return ScalpScoreFactor(
            name="15m Context", timeframe="15m",
            score=0.0, max_score=W_15M_CTX,
            direction="NEUTRAL", detail="15m EMA unavailable"
        ), "UNKNOWN"
    if e9 > e21:
        score = W_15M_CTX * 0.8  # supportive
        direction = "BULLISH"
        detail = f"15m EMA9 {e9:.2f} > EMA21 — macro uptrend supportive"
    else:
        # Opposing context — partial penalty only, not a gate
        score = -(W_15M_CTX * 0.6)
        direction = "BEARISH"
        detail = f"15m EMA9 {e9:.2f} < EMA21 — macro downtrend, mild headwind"
    return ScalpScoreFactor(
        name="15m Context", timeframe="15m",
        score=score, max_score=W_15M_CTX,
        direction=direction, detail=detail
    ), direction


def _build_trade_plan(
    direction: ScalpDirection,
    close: float,
    snap_1m: IndicatorSnapshot,
) -> ScalpTradePlan:
    """Build entry/SL/TP using ATR-based sizing. Analytical only."""
    atr = snap_1m.volatility.atr
    if atr is None or atr <= 0 or direction == ScalpDirection.NO_TRADE:
        return ScalpTradePlan(
            plan_available=False,
            plan_rejection_reason="ATR unavailable or NO_TRADE direction"
        )

    # SCALP risk parameters
    SL_MULT = 1.5   # stop = 1.5 × ATR
    TP1_MULT = 2.0  # 1.25R minimum → use 2.0 ATR for TP1
    TP2_MULT = 3.0  # 2.0R
    TP3_MULT = 4.5  # 3.0R

    sl_dist = atr * SL_MULT
    tp1_dist = atr * TP1_MULT
    tp2_dist = atr * TP2_MULT
    tp3_dist = atr * TP3_MULT

    rr1 = round(tp1_dist / sl_dist, 2)
    rr2 = round(tp2_dist / sl_dist, 2)
    rr3 = round(tp3_dist / sl_dist, 2)

    if direction == ScalpDirection.BUY:
        return ScalpTradePlan(
            entry_price=round(close, 2),
            stop_loss=round(close - sl_dist, 2),
            tp1=round(close + tp1_dist, 2),
            tp2=round(close + tp2_dist, 2),
            tp3=round(close + tp3_dist, 2),
            rr_tp1=rr1, rr_tp2=rr2, rr_tp3=rr3,
            atr_used=round(atr, 4),
            plan_available=True,
        )
    else:  # SELL
        return ScalpTradePlan(
            entry_price=round(close, 2),
            stop_loss=round(close + sl_dist, 2),
            tp1=round(close - tp1_dist, 2),
            tp2=round(close - tp2_dist, 2),
            tp3=round(close - tp3_dist, 2),
            rr_tp1=rr1, rr_tp2=rr2, rr_tp3=rr3,
            atr_used=round(atr, 4),
            plan_available=True,
        )


class ScalpStrategyEngine:
    """
    SCALP_STRATEGY_V1 — deterministic 1m scalping engine.

    Invariants:
    - Does NOT call Phase 5 SignalEngine or Phase 10 TradeDecisionEngine.
    - Does NOT modify any existing Phase 3–10 engine.
    - Confirmed signals come only from closed 1m candles (is_closed=True).
    - Preview signals (is_preview=True) come from the forming candle.
    - Completely deterministic for the same input sequence.
    - Zero network/DB/exchange dependency.
    """

    STRATEGY_ID = "SCALP_STRATEGY_V1"
    VERSION = "1.0.0"

    @classmethod
    def evaluate(
        cls,
        candles_1m: List[Candle],
        candles_5m: Optional[List[Candle]] = None,
        candles_15m: Optional[List[Candle]] = None,
        symbol: str = "BTCUSDT",
        phase5_direction: str = "NEUTRAL",
        is_preview: bool = False,
    ) -> ScalpSignal:
        """
        Evaluate SCALP_STRATEGY_V1 on provided candle sequences.

        Args:
            candles_1m: 1-minute candles (closed + optionally one forming).
            candles_5m: 5-minute candles for context (optional).
            candles_15m: 15-minute candles for context (optional).
            symbol: Market symbol.
            phase5_direction: Phase 5 research signal direction (READ-ONLY display, not a gate).
            is_preview: If True, allow evaluation including forming candle.

        Returns:
            ScalpSignal with BUY / SELL / NO_TRADE decision.
        """
        now_ms = int(time.time() * 1000)

        # ── 1. Compute indicators ────────────────────────────────────────────
        closed_1m = [c for c in candles_1m if c.is_closed]
        if len(closed_1m) < 30:
            return ScalpSignal(
                symbol=symbol,
                direction=ScalpDirection.NO_TRADE,
                score_breakdown=ScalpScoreBreakdown(),
                is_preview=is_preview,
                calculation_timestamp=now_ms,
                reasons=["Insufficient 1m closed candles (need 30+)"],
                phase5_research_direction=phase5_direction,
            )

        # Use closed candles for confirmed; add forming candle for preview
        eval_1m = closed_1m if not is_preview else list(candles_1m)
        snap_1m = IndicatorEngine.calculate_snapshot(
            eval_1m, symbol=symbol, timeframe="1m", is_confirmed=not is_preview
        )

        # Current candle reference
        ref_candle = eval_1m[-1]
        close = ref_candle.close
        candle_ts = ref_candle.timestamp

        # Context timeframes
        snap_5m: Optional[IndicatorSnapshot] = None
        snap_15m: Optional[IndicatorSnapshot] = None
        if candles_5m and len(candles_5m) >= 20:
            closed_5m = [c for c in candles_5m if c.is_closed]
            if closed_5m:
                snap_5m = IndicatorEngine.calculate_snapshot(
                    closed_5m, symbol=symbol, timeframe="5m", is_confirmed=True
                )
        if candles_15m and len(candles_15m) >= 20:
            closed_15m = [c for c in candles_15m if c.is_closed]
            if closed_15m:
                snap_15m = IndicatorEngine.calculate_snapshot(
                    closed_15m, symbol=symbol, timeframe="15m", is_confirmed=True
                )

        # ── 2. Score each factor ─────────────────────────────────────────────
        f_ema   = _ema_trend_score(snap_1m)
        f_vwap  = _vwap_score(snap_1m, close)
        f_rsi   = _rsi_score(snap_1m)
        f_macd  = _macd_score(snap_1m)
        f_vol   = _volume_score(snap_1m)
        f_5m, ctx_5m = _context_5m_score(snap_5m)
        f_15m, ctx_15m = _context_15m_score(snap_15m)

        factors = [f_ema, f_vwap, f_rsi, f_macd, f_vol, f_5m, f_15m]

        bull_total = sum(max(f.score, 0.0) for f in factors)
        bear_total = sum(abs(min(f.score, 0.0)) for f in factors)
        net = bull_total - bear_total   # range ~ -100..+100

        max_possible = sum(f.max_score for f in factors)  # 100
        normalised = round(min(100.0, abs(net) / max_possible * 100), 1)

        breakdown = ScalpScoreBreakdown(
            factors=factors,
            raw_bull_score=round(bull_total, 2),
            raw_bear_score=round(bear_total, 2),
            net_score=round(net, 2),
            normalised_score=normalised,
        )

        # ── 3. Direction decision ────────────────────────────────────────────
        if net >= BUY_THRESHOLD:
            direction = ScalpDirection.BUY
        elif net <= SELL_THRESHOLD:
            direction = ScalpDirection.SELL
        else:
            direction = ScalpDirection.NO_TRADE

        # ── 4. Trade plan ─────────────────────────────────────────────────────
        trade_plan = _build_trade_plan(direction, close, snap_1m)

        # ── 5. Reasons & invalidation ────────────────────────────────────────
        reasons = [f.detail for f in factors if abs(f.score) > 2.0]
        invalidation: List[str] = []
        if direction == ScalpDirection.BUY:
            invalidation = [
                f"EMA 9 crosses below EMA 21 on 1m",
                f"Price breaks below VWAP and stays below",
                f"MACD histogram turns negative",
                f"RSI drops below 35",
            ]
        elif direction == ScalpDirection.SELL:
            invalidation = [
                f"EMA 9 crosses above EMA 21 on 1m",
                f"Price reclaims VWAP",
                f"MACD histogram turns positive",
                f"RSI rises above 65",
            ]

        return ScalpSignal(
            strategy_id=cls.STRATEGY_ID,
            strategy_version=cls.VERSION,
            symbol=symbol,
            primary_timeframe="1m",
            direction=direction,
            score_breakdown=breakdown,
            trade_plan=trade_plan,
            is_preview=is_preview,
            candle_timestamp=candle_ts,
            calculation_timestamp=now_ms,
            reasons=reasons,
            invalidation_conditions=invalidation,
            context_5m_trend=ctx_5m,
            context_15m_trend=ctx_15m,
            phase5_research_direction=phase5_direction,
        )
