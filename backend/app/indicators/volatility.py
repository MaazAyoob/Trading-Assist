import numpy as np
from typing import Tuple
from app.indicators.trend import compute_wilder_rma


def compute_atr(
    highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int = 14
) -> np.ndarray:
    """
    Calculate Average True Range (ATR) using standard Wilder's smoothing.
    Formula:
      TR_t = max(High_t - Low_t, |High_t - Close_{t-1}|, |Low_t - Close_{t-1}|)
      ATR_t = WilderRMA(TR, period)
    """
    n = len(closes)
    atr = np.full(n, np.nan, dtype=np.float64)
    if n < period or period <= 0:
        return atr

    tr = np.zeros(n, dtype=np.float64)
    tr[0] = highs[0] - lows[0]
    for i in range(1, n):
        hl = highs[i] - lows[i]
        h_pc = abs(highs[i] - closes[i - 1])
        l_pc = abs(lows[i] - closes[i - 1])
        tr[i] = max(hl, h_pc, l_pc)

    return compute_wilder_rma(tr, period)


def compute_bollinger_bands(
    closes: np.ndarray, period: int = 20, std_multiplier: float = 2.0
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Calculate Bollinger Bands:
    - Middle Band: 20 SMA
    - Upper Band: Middle + (std_multiplier * rolling standard deviation)
    - Lower Band: Middle - (std_multiplier * rolling standard deviation)
    - Bandwidth: (Upper - Lower) / Middle * 100 (%)
    - %B: (Close - Lower) / (Upper - Lower)
    """
    n = len(closes)
    upper = np.full(n, np.nan, dtype=np.float64)
    middle = np.full(n, np.nan, dtype=np.float64)
    lower = np.full(n, np.nan, dtype=np.float64)
    bandwidth = np.full(n, np.nan, dtype=np.float64)
    percent_b = np.full(n, np.nan, dtype=np.float64)

    if n < period or period <= 0:
        return upper, middle, lower, bandwidth, percent_b

    for i in range(period - 1, n):
        window = closes[i - period + 1 : i + 1]
        m = np.mean(window)
        s = np.std(window, ddof=0)

        u = m + std_multiplier * s
        l = m - std_multiplier * s

        middle[i] = m
        upper[i] = u
        lower[i] = l

        if m > 0:
            bandwidth[i] = ((u - l) / m) * 100.0

        denom = u - l
        if denom > 0:
            percent_b[i] = (closes[i] - l) / denom
        else:
            percent_b[i] = 0.5

    return upper, middle, lower, bandwidth, percent_b
