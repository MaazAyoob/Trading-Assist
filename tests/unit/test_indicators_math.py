import numpy as np
import pytest
from app.indicators.trend import (
    compute_ema,
    compute_wilder_rma,
    compute_rolling_vwap,
    compute_adx,
    compute_supertrend,
)
from app.indicators.momentum import compute_rsi, compute_macd, compute_stoch_rsi, compute_roc
from app.indicators.volatility import compute_atr, compute_bollinger_bands
from app.indicators.volume import compute_volume_sma, compute_relative_volume, compute_obv


def test_ema_math_reference():
    # 5-period EMA on simple known series [10, 11, 12, 13, 14, 15]
    # alpha = 2 / (5 + 1) = 1/3
    # SMA(first 5) = (10+11+12+13+14)/5 = 12.0
    # EMA_6 = 15 * (1/3) + 12.0 * (2/3) = 5.0 + 8.0 = 13.0
    prices = np.array([10.0, 11.0, 12.0, 13.0, 14.0, 15.0])
    ema = compute_ema(prices, 5)

    assert np.isnan(ema[0])
    assert np.isnan(ema[3])
    assert np.isclose(ema[4], 12.0)
    assert np.isclose(ema[5], 13.0)


def test_wilder_rma_math():
    # RMA on [10, 20, 30, 40] with period=3
    # SMA(3) = 20.0
    # RMA_4 = (20.0 * 2 + 40) / 3 = 80 / 3 = 26.666667
    vals = np.array([10.0, 20.0, 30.0, 40.0])
    rma = compute_wilder_rma(vals, 3)
    assert np.isnan(rma[0])
    assert np.isnan(rma[1])
    assert np.isclose(rma[2], 20.0)
    assert np.isclose(rma[3], 80.0 / 3.0)


def test_rsi_monotonically_rising():
    # Strictly rising prices should yield RSI = 100
    prices = np.linspace(100.0, 200.0, 30)
    rsi = compute_rsi(prices, 14)
    assert np.isnan(rsi[13])
    assert np.isclose(rsi[-1], 100.0)


def test_rsi_monotonically_falling():
    # Strictly falling prices should yield RSI = 0
    prices = np.linspace(200.0, 100.0, 30)
    rsi = compute_rsi(prices, 14)
    assert np.isclose(rsi[-1], 0.0)


def test_macd_formula_consistency():
    # Verify MACD Line = EMA(fast) - EMA(slow) and Hist = MACD - Signal
    prices = np.sin(np.linspace(0, 10, 100)) * 50 + 1000
    macd_line, sig_line, hist = compute_macd(prices, fast=12, slow=26, signal=9)

    for i in range(len(prices)):
        if not np.isnan(macd_line[i]) and not np.isnan(sig_line[i]) and not np.isnan(hist[i]):
            assert np.isclose(hist[i], macd_line[i] - sig_line[i])


def test_atr_true_range():
    # 2 candles:
    # C1: H=110, L=90, C=100
    # C2: H=125, L=105, C=120
    # TR2 = max(125-105=20, |125-100|=25, |105-100|=5) = 25
    highs = np.array([110.0, 125.0])
    lows = np.array([90.0, 105.0])
    closes = np.array([100.0, 120.0])
    atr = compute_atr(highs, lows, closes, 2)
    # ATR(2) is mean of TR1 (20) and TR2 (25) = 22.5
    assert np.isclose(atr[1], 22.5)


def test_bollinger_bands_math():
    # Constant series: prices = 100 -> std = 0 -> Upper = Middle = Lower = 100, Bandwidth = 0, %B = 0.5
    prices = np.full(30, 100.0)
    upper, middle, lower, bandwidth, pb = compute_bollinger_bands(prices, period=20, std_multiplier=2.0)

    assert np.isclose(middle[-1], 100.0)
    assert np.isclose(upper[-1], 100.0)
    assert np.isclose(lower[-1], 100.0)
    assert np.isclose(bandwidth[-1], 0.0)
    assert np.isclose(pb[-1], 0.5)


def test_supertrend_reference():
    # Deterministic sequence testing bull/bear transitions
    n = 30
    highs = np.linspace(100, 130, n)
    lows = np.linspace(95, 125, n)
    closes = np.linspace(98, 128, n)

    st, direction = compute_supertrend(highs, lows, closes, period=10, multiplier=3.0)
    # With strictly upward trend, direction should be +1 (Bullish) and supertrend < closes
    assert direction[-1] == 1
    assert st[-1] < closes[-1]


def test_rolling_vwap_math():
    # 2 bars within same 24h window:
    # B1: TP = (100+90+95)/3 = 95, Vol = 10 -> TP*Vol = 950
    # B2: TP = (110+100+105)/3 = 105, Vol = 10 -> TP*Vol = 1050
    # VWAP = (950 + 1050) / 20 = 100.0
    ts = np.array([1700000000000, 1700000900000])
    highs = np.array([100.0, 110.0])
    lows = np.array([90.0, 100.0])
    closes = np.array([95.0, 105.0])
    volumes = np.array([10.0, 10.0])

    vwap = compute_rolling_vwap(ts, highs, lows, closes, volumes, window_hours=24)
    assert np.isclose(vwap[0], 95.0)
    assert np.isclose(vwap[1], 100.0)


def test_obv_math():
    closes = np.array([100.0, 105.0, 102.0, 102.0])
    vols = np.array([10.0, 20.0, 15.0, 5.0])
    # OBV:
    # t0: 10
    # t1: close up -> 10 + 20 = 30
    # t2: close down -> 30 - 15 = 15
    # t3: close equal -> 15
    obv = compute_obv(closes, vols)
    assert np.isclose(obv[0], 10.0)
    assert np.isclose(obv[1], 30.0)
    assert np.isclose(obv[2], 15.0)
    assert np.isclose(obv[3], 15.0)


def test_relative_volume_math():
    # 20 bars of vol=10, 21st bar vol=30
    # SMA(20) at index 20 = 10.0 -> RelVol = 30 / 10 = 3.0
    vols = np.full(21, 10.0)
    vols[-1] = 30.0
    rel_vol = compute_relative_volume(vols, period=20)
    assert np.isclose(rel_vol[-1], 3.0)


def test_roc_math():
    # 13 bars: first bar = 100, last bar = 110 -> period=12 ROC = (110 - 100)/100 * 100 = 10.0%
    closes = np.full(13, 100.0)
    closes[-1] = 110.0
    roc = compute_roc(closes, period=12)
    assert np.isclose(roc[-1], 10.0)
