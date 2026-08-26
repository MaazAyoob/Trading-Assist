import numpy as np
from typing import Tuple
from app.indicators.trend import compute_ema, compute_wilder_rma


def compute_rsi(closes: np.ndarray, period: int = 14) -> np.ndarray:
    """
    Calculate Relative Strength Index (RSI) using standard Wilder's smoothing (RMA).
    Formula:
      Change = Close_t - Close_{t-1}
      Gain = max(Change, 0), Loss = max(-Change, 0)
      AvgGain = WilderRMA(Gain, period), AvgLoss = WilderRMA(Loss, period)
      RS = AvgGain / AvgLoss
      RSI = 100 - (100 / (1 + RS))
    """
    n = len(closes)
    rsi = np.full(n, np.nan, dtype=np.float64)
    if n <= period or period <= 0:
        return rsi

    deltas = np.diff(closes)
    gains = np.where(deltas > 0, deltas, 0.0)
    losses = np.where(deltas < 0, -deltas, 0.0)

    # Pad with 0 for index alignment with closes
    gains_padded = np.insert(gains, 0, 0.0)
    losses_padded = np.insert(losses, 0, 0.0)

    avg_gain = compute_wilder_rma(gains_padded, period)
    avg_loss = compute_wilder_rma(losses_padded, period)

    for i in range(period, n):
        ag = avg_gain[i]
        al = avg_loss[i]

        if np.isnan(ag) or np.isnan(al):
            continue

        if al == 0.0:
            rsi[i] = 100.0 if ag > 0 else 50.0
        elif ag == 0.0:
            rsi[i] = 0.0
        else:
            rs = ag / al
            rsi[i] = 100.0 - (100.0 / (1.0 + rs))

    return rsi


def compute_macd(
    closes: np.ndarray, fast: int = 12, slow: int = 26, signal: int = 9
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Calculate MACD Line, Signal Line, and MACD Histogram.
    - MACD Line = EMA(fast) - EMA(slow)
    - Signal Line = EMA(MACD Line, signal)
    - Histogram = MACD Line - Signal Line
    """
    n = len(closes)
    macd_line = np.full(n, np.nan, dtype=np.float64)
    signal_line = np.full(n, np.nan, dtype=np.float64)
    histogram = np.full(n, np.nan, dtype=np.float64)

    if n < slow:
        return macd_line, signal_line, histogram

    ema_fast = compute_ema(closes, fast)
    ema_slow = compute_ema(closes, slow)

    # MACD Line exists where slow EMA is valid
    for i in range(slow - 1, n):
        if not np.isnan(ema_fast[i]) and not np.isnan(ema_slow[i]):
            macd_line[i] = ema_fast[i] - ema_slow[i]

    # Signal Line is EMA of MACD Line
    valid_macd_indices = [i for i in range(n) if not np.isnan(macd_line[i])]
    if len(valid_macd_indices) >= signal:
        macd_valid_vals = macd_line[valid_macd_indices]
        sig_valid = compute_ema(macd_valid_vals, signal)
        for idx, orig_idx in enumerate(valid_macd_indices):
            signal_line[orig_idx] = sig_valid[idx]
            if not np.isnan(macd_line[orig_idx]) and not np.isnan(signal_line[orig_idx]):
                histogram[orig_idx] = macd_line[orig_idx] - signal_line[orig_idx]

    return macd_line, signal_line, histogram


def compute_stoch_rsi(
    closes: np.ndarray, period: int = 14, k_period: int = 3, d_period: int = 3
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Calculate Stochastic RSI (%K and %D).
    Formula:
      StochRSI = (RSI - min(RSI, period)) / (max(RSI, period) - min(RSI, period)) * 100
      %K = SMA(StochRSI, k_period)
      %D = SMA(%K, d_period)
    """
    n = len(closes)
    stoch_k = np.full(n, np.nan, dtype=np.float64)
    stoch_d = np.full(n, np.nan, dtype=np.float64)

    rsi = compute_rsi(closes, period)
    stoch_raw = np.full(n, np.nan, dtype=np.float64)

    for i in range(period + period - 1, n):
        rsi_window = rsi[i - period + 1 : i + 1]
        if np.any(np.isnan(rsi_window)):
            continue
        min_rsi = np.min(rsi_window)
        max_rsi = np.max(rsi_window)
        if max_rsi > min_rsi:
            stoch_raw[i] = ((rsi[i] - min_rsi) / (max_rsi - min_rsi)) * 100.0
        else:
            stoch_raw[i] = 50.0

    # %K is SMA of stoch_raw
    for i in range(k_period - 1, n):
        window = stoch_raw[i - k_period + 1 : i + 1]
        if not np.any(np.isnan(window)):
            stoch_k[i] = np.mean(window)

    # %D is SMA of %K
    for i in range(d_period - 1, n):
        window = stoch_k[i - d_period + 1 : i + 1]
        if not np.any(np.isnan(window)):
            stoch_d[i] = np.mean(window)

    return stoch_k, stoch_d


def compute_roc(closes: np.ndarray, period: int = 12) -> np.ndarray:
    """
    Calculate Rate of Change (ROC %).
    Formula: ((Close_t - Close_{t-period}) / Close_{t-period}) * 100
    """
    n = len(closes)
    roc = np.full(n, np.nan, dtype=np.float64)
    if n <= period or period <= 0:
        return roc

    for i in range(period, n):
        prev = closes[i - period]
        if prev > 0:
            roc[i] = ((closes[i] - prev) / prev) * 100.0

    return roc
