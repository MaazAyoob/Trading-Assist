"""
SCALP_STRATEGY_V2 — Signal Evaluation and Setup Pattern Recognition.
Independent multi-factor evaluator supporting:
  - Setup A: Trend Continuation
  - Setup B: Pullback / Reversion
  - Setup C: Momentum Breakout
"""
from typing import List, Tuple, Optional
from app.data.schema import Candle
from app.indicators.base import IndicatorSnapshot
from app.scalp_v2.config import (
    W_TREND_ALIGNMENT,
    W_VWAP,
    W_MOMENTUM,
    W_RSI,
    W_VOLUME,
    W_5M_CONTEXT,
    W_15M_CONTEXT,
    W_SETUP_BONUS,
    BUY_THRESHOLD,
    SELL_THRESHOLD,
    WATCH_POS_MIN,
    WATCH_POS_MAX,
    WATCH_NEG_MIN,
    WATCH_NEG_MAX,
    STRENGTH_VERY_STRONG_MIN,
    STRENGTH_STRONG_MIN,
    STRENGTH_MODERATE_MIN,
    STRENGTH_WEAK_MIN,
    STRENGTH_WATCH_MIN,
)
from app.scalp_v2.models import (
    ScalpV2Direction,
    ScalpV2SetupType,
    ScalpV2Strength,
    ScalpV2ScoreFactor,
    ScalpV2ScoreBreakdown,
)


def evaluate_trend_factor(snap_1m: IndicatorSnapshot) -> ScalpV2ScoreFactor:
    """1m EMA 9 vs EMA 21 trend alignment."""
    e9 = snap_1m.trend.ema_9
    e21 = snap_1m.trend.ema_21
    if e9 is None or e21 is None:
        return ScalpV2ScoreFactor(
            name="1m EMA Trend",
            timeframe="1m",
            score=0.0,
            max_score=W_TREND_ALIGNMENT,
            direction="NEUTRAL",
            detail="1m EMAs not available",
        )
    diff = e9 - e21
    if diff > 0:
        pct = min((diff / e21) * 100 / 0.08, 1.0) if e21 > 0 else 0.5
        score = W_TREND_ALIGNMENT * (0.6 + 0.4 * pct)
        return ScalpV2ScoreFactor(
            name="1m EMA Trend",
            timeframe="1m",
            score=min(score, W_TREND_ALIGNMENT),
            max_score=W_TREND_ALIGNMENT,
            direction="BULLISH",
            detail=f"EMA9 ({e9:.2f}) > EMA21 ({e21:.2f})",
        )
    else:
        pct = min((abs(diff) / e21) * 100 / 0.08, 1.0) if e21 > 0 else 0.5
        score = -W_TREND_ALIGNMENT * (0.6 + 0.4 * pct)
        return ScalpV2ScoreFactor(
            name="1m EMA Trend",
            timeframe="1m",
            score=max(score, -W_TREND_ALIGNMENT),
            max_score=W_TREND_ALIGNMENT,
            direction="BEARISH",
            detail=f"EMA9 ({e9:.2f}) < EMA21 ({e21:.2f})",
        )


def evaluate_vwap_factor(snap_1m: IndicatorSnapshot, close: float) -> ScalpV2ScoreFactor:
    """1m Price position relative to VWAP."""
    vwap = snap_1m.trend.vwap
    if vwap is None or vwap <= 0:
        return ScalpV2ScoreFactor(
            name="1m VWAP Position",
            timeframe="1m",
            score=0.0,
            max_score=W_VWAP,
            direction="NEUTRAL",
            detail="VWAP unavailable",
        )
    diff_pct = (close - vwap) / vwap * 100
    if diff_pct >= 0:
        score = min(W_VWAP, W_VWAP * (0.7 + 0.3 * min(diff_pct / 0.15, 1.0)))
        return ScalpV2ScoreFactor(
            name="1m VWAP Position",
            timeframe="1m",
            score=score,
            max_score=W_VWAP,
            direction="BULLISH",
            detail=f"Price ${close:.2f} above VWAP ${vwap:.2f} (+{diff_pct:.2f}%)",
        )
    else:
        score = -min(W_VWAP, W_VWAP * (0.7 + 0.3 * min(abs(diff_pct) / 0.15, 1.0)))
        return ScalpV2ScoreFactor(
            name="1m VWAP Position",
            timeframe="1m",
            score=score,
            max_score=W_VWAP,
            direction="BEARISH",
            detail=f"Price ${close:.2f} below VWAP ${vwap:.2f} ({diff_pct:.2f}%)",
        )


def evaluate_momentum_factor(snap_1m: IndicatorSnapshot) -> ScalpV2ScoreFactor:
    """1m MACD Histogram & Momentum direction."""
    hist = snap_1m.momentum.macd_histogram
    macd_line = snap_1m.momentum.macd
    sig_line = snap_1m.momentum.macd_signal
    if hist is None:
        return ScalpV2ScoreFactor(
            name="1m MACD Momentum",
            timeframe="1m",
            score=0.0,
            max_score=W_MOMENTUM,
            direction="NEUTRAL",
            detail="MACD unavailable",
        )
    if hist > 0:
        crossover_bonus = 0.2 if (macd_line and sig_line and macd_line > sig_line) else 0.0
        score = min(W_MOMENTUM, W_MOMENTUM * (0.6 + crossover_bonus))
        return ScalpV2ScoreFactor(
            name="1m MACD Momentum",
            timeframe="1m",
            score=score,
            max_score=W_MOMENTUM,
            direction="BULLISH",
            detail=f"MACD histogram positive ({hist:+.3f})",
        )
    elif hist < 0:
        crossover_penalty = 0.2 if (macd_line and sig_line and macd_line < sig_line) else 0.0
        score = -min(W_MOMENTUM, W_MOMENTUM * (0.6 + crossover_penalty))
        return ScalpV2ScoreFactor(
            name="1m MACD Momentum",
            timeframe="1m",
            score=score,
            max_score=W_MOMENTUM,
            direction="BEARISH",
            detail=f"MACD histogram negative ({hist:+.3f})",
        )
    return ScalpV2ScoreFactor(
        name="1m MACD Momentum",
        timeframe="1m",
        score=0.0,
        max_score=W_MOMENTUM,
        direction="NEUTRAL",
        detail="MACD histogram flat",
    )


def evaluate_rsi_factor(snap_1m: IndicatorSnapshot) -> ScalpV2ScoreFactor:
    """1m RSI oscillator momentum."""
    rsi = snap_1m.momentum.rsi
    if rsi is None:
        return ScalpV2ScoreFactor(
            name="1m RSI",
            timeframe="1m",
            score=0.0,
            max_score=W_RSI,
            direction="NEUTRAL",
            detail="RSI unavailable",
        )
    if 50.0 <= rsi <= 75.0:
        # Bullish momentum zone
        score = W_RSI * (0.5 + 0.5 * (rsi - 50.0) / 25.0)
        return ScalpV2ScoreFactor(
            name="1m RSI",
            timeframe="1m",
            score=min(score, W_RSI),
            max_score=W_RSI,
            direction="BULLISH",
            detail=f"RSI bullish momentum ({rsi:.1f})",
        )
    elif 25.0 <= rsi < 50.0:
        # Bearish momentum zone
        score = -W_RSI * (0.5 + 0.5 * (50.0 - rsi) / 25.0)
        return ScalpV2ScoreFactor(
            name="1m RSI",
            timeframe="1m",
            score=max(score, -W_RSI),
            max_score=W_RSI,
            direction="BEARISH",
            detail=f"RSI bearish momentum ({rsi:.1f})",
        )
    elif rsi < 25.0:
        # Strong bearish momentum (oversold territory)
        return ScalpV2ScoreFactor(
            name="1m RSI",
            timeframe="1m",
            score=-W_RSI * 0.7,
            max_score=W_RSI,
            direction="BEARISH",
            detail=f"RSI strong bearish momentum (oversold {rsi:.1f})",
        )
    else:  # rsi > 75.0
        # Strong bullish momentum (overbought territory)
        return ScalpV2ScoreFactor(
            name="1m RSI",
            timeframe="1m",
            score=W_RSI * 0.7,
            max_score=W_RSI,
            direction="BULLISH",
            detail=f"RSI strong bullish momentum (overbought {rsi:.1f})",
        )


def evaluate_volume_factor(snap_1m: IndicatorSnapshot) -> ScalpV2ScoreFactor:
    """1m Relative volume confirmation."""
    rvol = snap_1m.volume.relative_volume if snap_1m.volume else None
    if rvol is None:
        return ScalpV2ScoreFactor(
            name="1m Volume",
            timeframe="1m",
            score=0.0,
            max_score=W_VOLUME,
            direction="NEUTRAL",
            detail="Volume unavailable",
        )
    if rvol >= 1.0:
        score = min(W_VOLUME, W_VOLUME * (0.6 + 0.4 * min((rvol - 1.0) / 1.5, 1.0)))
        return ScalpV2ScoreFactor(
            name="1m Volume",
            timeframe="1m",
            score=score,
            max_score=W_VOLUME,
            direction="BULLISH",
            detail=f"Elevated volume ({rvol:.2f}x relative)",
        )
    elif rvol >= 0.7:
        return ScalpV2ScoreFactor(
            name="1m Volume",
            timeframe="1m",
            score=W_VOLUME * 0.4,
            max_score=W_VOLUME,
            direction="NEUTRAL",
            detail=f"Adequate volume ({rvol:.2f}x relative)",
        )
    else:
        return ScalpV2ScoreFactor(
            name="1m Volume",
            timeframe="1m",
            score=-W_VOLUME * 0.3,
            max_score=W_VOLUME,
            direction="NEUTRAL",
            detail=f"Low liquidity/volume ({rvol:.2f}x relative)",
        )


def evaluate_5m_context(snap_5m: Optional[IndicatorSnapshot]) -> Tuple[ScalpV2ScoreFactor, str]:
    """5m Trend Context."""
    if snap_5m is None or snap_5m.trend.ema_9 is None or snap_5m.trend.ema_21 is None:
        return (
            ScalpV2ScoreFactor(
                name="5m Context Trend",
                timeframe="5m",
                score=0.0,
                max_score=W_5M_CONTEXT,
                direction="NEUTRAL",
                detail="5m Context unavailable",
            ),
            "NEUTRAL",
        )
    e9 = snap_5m.trend.ema_9
    e21 = snap_5m.trend.ema_21
    if e9 > e21:
        return (
            ScalpV2ScoreFactor(
                name="5m Context Trend",
                timeframe="5m",
                score=W_5M_CONTEXT,
                max_score=W_5M_CONTEXT,
                direction="BULLISH",
                detail=f"5m Bullish alignment (EMA9 {e9:.2f} > EMA21 {e21:.2f})",
            ),
            "BULLISH",
        )
    else:
        return (
            ScalpV2ScoreFactor(
                name="5m Context Trend",
                timeframe="5m",
                score=-W_5M_CONTEXT,
                max_score=W_5M_CONTEXT,
                direction="BEARISH",
                detail=f"5m Bearish alignment (EMA9 {e9:.2f} < EMA21 {e21:.2f})",
            ),
            "BEARISH",
        )


def evaluate_15m_context(snap_15m: Optional[IndicatorSnapshot]) -> Tuple[ScalpV2ScoreFactor, str]:
    """15m Broader Context."""
    if snap_15m is None or snap_15m.trend.ema_9 is None or snap_15m.trend.ema_21 is None:
        return (
            ScalpV2ScoreFactor(
                name="15m Higher Context",
                timeframe="15m",
                score=0.0,
                max_score=W_15M_CONTEXT,
                direction="NEUTRAL",
                detail="15m Context unavailable",
            ),
            "NEUTRAL",
        )
    e9 = snap_15m.trend.ema_9
    e21 = snap_15m.trend.ema_21
    if e9 > e21:
        return (
            ScalpV2ScoreFactor(
                name="15m Higher Context",
                timeframe="15m",
                score=W_15M_CONTEXT,
                max_score=W_15M_CONTEXT,
                direction="BULLISH",
                detail=f"15m Bullish context (EMA9 > EMA21)",
            ),
            "BULLISH",
        )
    else:
        return (
            ScalpV2ScoreFactor(
                name="15m Higher Context",
                timeframe="15m",
                score=-W_15M_CONTEXT,
                max_score=W_15M_CONTEXT,
                direction="BEARISH",
                detail=f"15m Bearish context (EMA9 < EMA21)",
            ),
            "BEARISH",
        )


def detect_setup_type(
    candles_1m: List[Candle],
    snap_1m: IndicatorSnapshot,
    snap_5m: Optional[IndicatorSnapshot],
) -> Tuple[ScalpV2SetupType, float, List[str]]:
    """
    Detect Setup A (Trend Continuation), Setup B (Pullback / Reversion),
    or Setup C (Momentum Breakout) and compute setup bonus.
    """
    if len(candles_1m) < 10:
        return ScalpV2SetupType.NONE, 0.0, []

    current = candles_1m[-1]
    prev_candles = candles_1m[-10:-1]
    close = current.close
    e9 = snap_1m.trend.ema_9
    e21 = snap_1m.trend.ema_21
    vwap = snap_1m.trend.vwap or close
    rsi = snap_1m.momentum.rsi or 50.0
    hist = snap_1m.momentum.macd_histogram or 0.0
    rvol = snap_1m.volume.relative_volume if snap_1m.volume else 1.0

    five_m_bull = snap_5m and snap_5m.trend.ema_9 and snap_5m.trend.ema_21 and snap_5m.trend.ema_9 > snap_5m.trend.ema_21
    five_m_bear = snap_5m and snap_5m.trend.ema_9 and snap_5m.trend.ema_21 and snap_5m.trend.ema_9 < snap_5m.trend.ema_21

    recent_high = max(c.high for c in prev_candles)
    recent_low = min(c.low for c in prev_candles)
    recent_closes = [c.close for c in prev_candles]

    reasons: List[str] = []

    # ── 1. Check Setup C: Momentum Breakout ──────────────────────────────────
    if close > recent_high and (hist > 0 or rvol >= 0.9) and not five_m_bear:
        reasons.append("Breakout: Close above 10-candle local resistance")
        if rvol >= 1.0:
            reasons.append(f"Volume expansion ({rvol:.1f}x)")
        return ScalpV2SetupType.MOMENTUM_BREAKOUT, W_SETUP_BONUS, reasons

    if close < recent_low and (hist < 0 or rvol >= 0.9) and not five_m_bull:
        reasons.append("Breakout: Close below 10-candle local support")
        if rvol >= 1.0:
            reasons.append(f"Volume expansion ({rvol:.1f}x)")
        return ScalpV2SetupType.MOMENTUM_BREAKOUT, -W_SETUP_BONUS, reasons

    # ── 2. Check Setup B: Pullback / Reversion ───────────────────────────────
    # Bullish pullback: 5m bullish, price pulled into EMA21/VWAP zone, RSI recovering, candle bullish
    if (
        five_m_bull
        and e21 is not None
        and current.low <= max(e21, vwap) * 1.003
        and close >= min(e21, vwap) * 0.997
        and rsi <= 72.0
        and close >= current.open
    ):
        reasons.append("Pullback: Price retested EMA21/VWAP support in 5m uptrend")
        reasons.append(f"RSI recovery momentum ({rsi:.1f})")
        return ScalpV2SetupType.PULLBACK, W_SETUP_BONUS, reasons

    # Bearish pullback: 5m bearish, price pulled up into EMA21/VWAP zone, RSI recovering down, candle bearish
    if (
        five_m_bear
        and e21 is not None
        and current.high >= min(e21, vwap) * 0.997
        and close <= max(e21, vwap) * 1.003
        and rsi >= 28.0
        and close <= current.open
    ):
        reasons.append("Pullback: Price retested EMA21/VWAP resistance in 5m downtrend")
        reasons.append(f"RSI rejection momentum ({rsi:.1f})")
        return ScalpV2SetupType.PULLBACK, -W_SETUP_BONUS, reasons

    # ── 3. Check Setup A: Trend Continuation ─────────────────────────────────
    if (
        e9 is not None
        and e21 is not None
        and (e9 - e21) / e21 >= 0.0001
        and close >= vwap
        and (five_m_bull or snap_5m is None)
        and rsi < 80.0
        and hist >= -0.1
        and close >= current.open
    ):
        reasons.append("Continuation: 1m EMA alignment + price above VWAP")
        return ScalpV2SetupType.TREND_CONTINUATION, W_SETUP_BONUS * 0.75, reasons

    if (
        e9 is not None
        and e21 is not None
        and (e21 - e9) / e21 >= 0.0001
        and close <= vwap
        and (five_m_bear or snap_5m is None)
        and rsi > 20.0
        and hist <= 0.1
        and close <= current.open
    ):
        reasons.append("Continuation: 1m EMA alignment + price below VWAP")
        return ScalpV2SetupType.TREND_CONTINUATION, -W_SETUP_BONUS * 0.75, reasons

    return ScalpV2SetupType.NONE, 0.0, []


def evaluate_scalp_v2_signal(
    candles_1m: List[Candle],
    snap_1m: IndicatorSnapshot,
    snap_5m: Optional[IndicatorSnapshot],
    snap_15m: Optional[IndicatorSnapshot],
    symbol: str = "BTCUSDT",
    is_preview: bool = False,
) -> Tuple[ScalpV2Direction, ScalpV2Strength, ScalpV2SetupType, float, float, ScalpV2ScoreBreakdown, List[str], List[str], str, str]:
    """
    Compute V2 score, direction, strength, and setup classification.
    """
    close = candles_1m[-1].close if candles_1m else 0.0

    # Base factor calculations
    f_trend = evaluate_trend_factor(snap_1m)
    f_vwap = evaluate_vwap_factor(snap_1m, close)
    f_mom = evaluate_momentum_factor(snap_1m)
    f_rsi = evaluate_rsi_factor(snap_1m)
    f_vol = evaluate_volume_factor(snap_1m)
    f_5m, trend_5m = evaluate_5m_context(snap_5m)
    f_15m, trend_15m = evaluate_15m_context(snap_15m)

    # Setup bonus detection
    setup_type, setup_bonus, setup_reasons = detect_setup_type(candles_1m, snap_1m, snap_5m)

    f_setup = ScalpV2ScoreFactor(
        name="Setup Pattern Bonus",
        timeframe="1m",
        score=setup_bonus,
        max_score=W_SETUP_BONUS,
        direction="BULLISH" if setup_bonus > 0 else "BEARISH" if setup_bonus < 0 else "NEUTRAL",
        detail=f"Recognized Setup: {setup_type.value}" if setup_type != ScalpV2SetupType.NONE else "No distinct pattern",
    )

    factors = [f_trend, f_vwap, f_mom, f_rsi, f_vol, f_5m, f_15m, f_setup]

    raw_bull = sum(f.score for f in factors if f.score > 0)
    raw_bear = sum(abs(f.score) for f in factors if f.score < 0)

    # Net score bounded between -100.0 and +100.0
    net_score = max(-100.0, min(100.0, sum(f.score for f in factors)))
    alignment_score = abs(net_score)

    breakdown = ScalpV2ScoreBreakdown(
        factors=factors,
        raw_bull_score=round(raw_bull, 2),
        raw_bear_score=round(raw_bear, 2),
        net_score=round(net_score, 2),
        normalised_score=round(alignment_score, 2),
        setup_bonus=round(setup_bonus, 2),
    )

    # Direction Classification
    if net_score >= BUY_THRESHOLD:
        direction = ScalpV2Direction.BUY
    elif net_score <= SELL_THRESHOLD:
        direction = ScalpV2Direction.SELL
    elif (WATCH_POS_MIN <= net_score <= WATCH_POS_MAX) or (WATCH_NEG_MIN <= net_score <= WATCH_NEG_MAX):
        direction = ScalpV2Direction.WATCH
    else:
        direction = ScalpV2Direction.NO_TRADE

    # Strength Classification
    if alignment_score >= STRENGTH_VERY_STRONG_MIN:
        strength = ScalpV2Strength.VERY_STRONG
    elif alignment_score >= STRENGTH_STRONG_MIN:
        strength = ScalpV2Strength.STRONG
    elif alignment_score >= STRENGTH_MODERATE_MIN:
        strength = ScalpV2Strength.MODERATE
    elif alignment_score >= STRENGTH_WEAK_MIN:
        strength = ScalpV2Strength.WEAK
    elif alignment_score >= STRENGTH_WATCH_MIN:
        strength = ScalpV2Strength.WATCH
    else:
        strength = ScalpV2Strength.NO_TRADE

    # Supporting & Conflicting Reasons
    supporting: List[str] = list(setup_reasons)
    conflicting: List[str] = []

    for f in factors:
        if f.name == "Setup Pattern Bonus":
            continue
        if direction in (ScalpV2Direction.BUY, ScalpV2Direction.WATCH) and net_score >= 0:
            if f.score > 0:
                supporting.append(f.detail)
            elif f.score < 0:
                conflicting.append(f.detail)
        elif direction in (ScalpV2Direction.SELL, ScalpV2Direction.WATCH) and net_score < 0:
            if f.score < 0:
                supporting.append(f.detail)
            elif f.score > 0:
                conflicting.append(f.detail)
        else:
            if abs(f.score) > 0:
                conflicting.append(f.detail)

    return (
        direction,
        strength,
        setup_type,
        net_score,
        alignment_score,
        breakdown,
        supporting[:5],
        conflicting[:4],
        trend_5m,
        trend_15m,
    )
