import numpy as np
from typing import List, Dict, Optional, Tuple
from app.indicators.config import IndicatorConfig


def compute_ema(prices: np.ndarray, period: int) -> np.ndarray:
    """
    Calculate Exponential Moving Average (EMA).
    Returns array of same length with NaN for warmup entries (< period).
    """
    n = len(prices)
    ema = np.full(n, np.nan, dtype=np.float64)
    if n < period or period <= 0:
        return ema

    # Initialize first valid EMA with SMA of first 'period' bars
    sma_init = np.mean(prices[:period])
    ema[period - 1] = sma_init
    alpha = 2.0 / (period + 1.0)

    for i in range(period, n):
        ema[i] = prices[i] * alpha + ema[i - 1] * (1.0 - alpha)

    return ema


def compute_rolling_vwap(
    timestamps_ms: np.ndarray,
    highs: np.ndarray,
    lows: np.ndarray,
    closes: np.ndarray,
    volumes: np.ndarray,
    window_hours: int = 24,
) -> np.ndarray:
    """
    Calculate 24h continuous rolling Volume Weighted Average Price (VWAP) for 24/7 crypto markets.
    Methodology:
    - Typical Price TP = (High + Low + Close) / 3
    - Rolling window lookback: [current_timestamp - 24 * 3600 * 1000, current_timestamp]
    - VWAP = Sum(TP * Volume) / Sum(Volume) over the rolling 24h window
    - If total rolling volume is 0, returns NaN
    """
    n = len(closes)
    vwap = np.full(n, np.nan, dtype=np.float64)
    if n == 0:
        return vwap

    typical_prices = (highs + lows + closes) / 3.0
    tp_vol = typical_prices * volumes
    window_ms = window_hours * 3600 * 1000

    left_idx = 0
    cum_tp_vol = 0.0
    cum_vol = 0.0

    for right_idx in range(n):
        current_ts = timestamps_ms[right_idx]
        threshold_ts = current_ts - window_ms

        # Add current bar to window
        cum_tp_vol += tp_vol[right_idx]
        cum_vol += volumes[right_idx]

        # Slide left pointer to remove bars older than 24h
        while left_idx < right_idx and timestamps_ms[left_idx] < threshold_ts:
            cum_tp_vol -= tp_vol[left_idx]
            cum_vol -= volumes[left_idx]
            left_idx += 1

        if cum_vol > 0:
            vwap[right_idx] = cum_tp_vol / cum_vol
        else:
            vwap[right_idx] = typical_prices[right_idx]

    return vwap


def compute_wilder_rma(values: np.ndarray, period: int) -> np.ndarray:
    """
    Wilder's Running Moving Average (RMA / Modified Moving Average).
    Used in RSI, ATR, and ADX calculations.
    Formula: RMA_t = (RMA_{t-1} * (period - 1) + value_t) / period
    """
    n = len(values)
    rma = np.full(n, np.nan, dtype=np.float64)
    if n < period or period <= 0:
        return rma

    # First value is simple SMA of first 'period' bars
    rma[period - 1] = np.mean(values[:period])
    for i in range(period, n):
        rma[i] = (rma[i - 1] * (period - 1) + values[i]) / period

    return rma


def compute_adx(
    highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int = 14
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Calculate Average Directional Index (ADX) along with +DI and -DI using Wilder's smoothing.
    Returns (adx, plus_di, minus_di).
    """
    n = len(closes)
    adx = np.full(n, np.nan, dtype=np.float64)
    plus_di = np.full(n, np.nan, dtype=np.float64)
    minus_di = np.full(n, np.nan, dtype=np.float64)

    if n < (period * 2):
        return adx, plus_di, minus_di

    # Compute True Range and Directional Movements
    tr = np.zeros(n, dtype=np.float64)
    plus_dm = np.zeros(n, dtype=np.float64)
    minus_dm = np.zeros(n, dtype=np.float64)

    tr[0] = highs[0] - lows[0]
    for i in range(1, n):
        hl = highs[i] - lows[i]
        h_pc = abs(highs[i] - closes[i - 1])
        l_pc = abs(lows[i] - closes[i - 1])
        tr[i] = max(hl, h_pc, l_pc)

        up_move = highs[i] - highs[i - 1]
        down_move = lows[i - 1] - lows[i]

        if up_move > down_move and up_move > 0:
            plus_dm[i] = up_move
        if down_move > up_move and down_move > 0:
            minus_dm[i] = down_move

    # Smooth TR, +DM, -DM using Wilder RMA
    tr_smooth = compute_wilder_rma(tr, period)
    plus_dm_smooth = compute_wilder_rma(plus_dm, period)
    minus_dm_smooth = compute_wilder_rma(minus_dm, period)

    dx = np.full(n, np.nan, dtype=np.float64)

    for i in range(period - 1, n):
        if tr_smooth[i] > 0:
            plus_di[i] = (plus_dm_smooth[i] / tr_smooth[i]) * 100.0
            minus_di[i] = (minus_dm_smooth[i] / tr_smooth[i]) * 100.0
            di_sum = plus_di[i] + minus_di[i]
            if di_sum > 0:
                dx[i] = (abs(plus_di[i] - minus_di[i]) / di_sum) * 100.0

    # ADX is Wilder RMA of DX (requires another 'period' bars)
    valid_dx_start = period - 1
    if n - valid_dx_start >= period:
        dx_subset = dx[valid_dx_start:]
        adx_subset = compute_wilder_rma(dx_subset, period)
        adx[valid_dx_start:] = adx_subset

    return adx, plus_di, minus_di


def compute_supertrend(
    highs: np.ndarray,
    lows: np.ndarray,
    closes: np.ndarray,
    period: int = 10,
    multiplier: float = 3.0,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Calculate Supertrend boundary and direction (+1: Bullish / -1: Bearish).
    Methodology:
    - True Range smoothed via Wilder RMA(period) to yield ATR
    - Basic Upper = (High + Low) / 2 + multiplier * ATR
    - Basic Lower = (High + Low) / 2 - multiplier * ATR
    - Final Upper/Lower bands persist based on previous Close & previous Final Bands
    - Direction switches on candle Close crossing the active band
    """
    n = len(closes)
    supertrend = np.full(n, np.nan, dtype=np.float64)
    direction = np.full(n, np.nan, dtype=np.float64)

    if n < period:
        return supertrend, direction

    # 1. Compute True Range
    tr = np.zeros(n, dtype=np.float64)
    tr[0] = highs[0] - lows[0]
    for i in range(1, n):
        hl = highs[i] - lows[i]
        h_pc = abs(highs[i] - closes[i - 1])
        l_pc = abs(lows[i] - closes[i - 1])
        tr[i] = max(hl, h_pc, l_pc)

    atr = compute_wilder_rma(tr, period)

    hl2 = (highs + lows) / 2.0
    basic_upper = hl2 + multiplier * atr
    basic_lower = hl2 - multiplier * atr

    final_upper = np.zeros(n, dtype=np.float64)
    final_lower = np.zeros(n, dtype=np.float64)
    trend = np.zeros(n, dtype=np.int32)

    # Initialize at period - 1
    start_idx = period - 1
    final_upper[start_idx] = basic_upper[start_idx]
    final_lower[start_idx] = basic_lower[start_idx]
    trend[start_idx] = 1 if closes[start_idx] >= basic_lower[start_idx] else -1
    supertrend[start_idx] = final_lower[start_idx] if trend[start_idx] == 1 else final_upper[start_idx]
    direction[start_idx] = trend[start_idx]

    for i in range(start_idx + 1, n):
        # Final Upper Band
        if basic_upper[i] < final_upper[i - 1] or closes[i - 1] > final_upper[i - 1]:
            final_upper[i] = basic_upper[i]
        else:
            final_upper[i] = final_upper[i - 1]

        # Final Lower Band
        if basic_lower[i] > final_lower[i - 1] or closes[i - 1] < final_lower[i - 1]:
            final_lower[i] = basic_lower[i]
        else:
            final_lower[i] = final_lower[i - 1]

        # Trend State Transition
        if trend[i - 1] == 1:
            if closes[i] < final_lower[i]:
                trend[i] = -1
                supertrend[i] = final_upper[i]
            else:
                trend[i] = 1
                supertrend[i] = final_lower[i]
        else:
            if closes[i] > final_upper[i]:
                trend[i] = 1
                supertrend[i] = final_lower[i]
            else:
                trend[i] = -1
                supertrend[i] = final_upper[i]

        direction[i] = trend[i]

    return supertrend, direction
