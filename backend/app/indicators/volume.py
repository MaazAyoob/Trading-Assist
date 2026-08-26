import numpy as np


def compute_volume_sma(volumes: np.ndarray, period: int = 20) -> np.ndarray:
    """
    Calculate Simple Moving Average of Volume.
    """
    n = len(volumes)
    vol_sma = np.full(n, np.nan, dtype=np.float64)
    if n < period or period <= 0:
        return vol_sma

    for i in range(period - 1, n):
        vol_sma[i] = np.mean(volumes[i - period + 1 : i + 1])

    return vol_sma


def compute_relative_volume(volumes: np.ndarray, period: int = 20) -> np.ndarray:
    """
    Calculate Relative Volume (RVol) ratio:
    Current Bar Volume relative to the average volume of the preceding 'period' bars.
    Formula: Volume_t / VolumeSMA_{t-1}(period)
    """
    n = len(volumes)
    rel_vol = np.full(n, np.nan, dtype=np.float64)
    vol_sma = compute_volume_sma(volumes, period)

    for i in range(period, n):
        prev_avg = vol_sma[i - 1]
        if not np.isnan(prev_avg) and prev_avg > 0:
            rel_vol[i] = volumes[i] / prev_avg

    return rel_vol


def compute_obv(closes: np.ndarray, volumes: np.ndarray) -> np.ndarray:
    """
    Calculate On-Balance Volume (OBV).
    Formula:
      If Close_t > Close_{t-1}  => OBV_t = OBV_{t-1} + Volume_t
      If Close_t < Close_{t-1}  => OBV_t = OBV_{t-1} - Volume_t
      If Close_t == Close_{t-1} => OBV_t = OBV_{t-1}
    """
    n = len(closes)
    obv = np.zeros(n, dtype=np.float64)
    if n == 0:
        return obv

    obv[0] = volumes[0]
    for i in range(1, n):
        if closes[i] > closes[i - 1]:
            obv[i] = obv[i - 1] + volumes[i]
        elif closes[i] < closes[i - 1]:
            obv[i] = obv[i - 1] - volumes[i]
        else:
            obv[i] = obv[i - 1]

    return obv
