# Quantitative Technical Indicators & Data Quality Engine

This document details the mathematical formulas, methodologies, warmup rules, and data quality validation pipelines implemented in **Phase 3** of the **Crypto AI Trading Intelligence Platform**.

---

## 1. Centralized Data Quality Validation

Before consuming any candle dataset, the `MarketDataQualityValidator` evaluates the data along a strict sequential validation pipeline:

```
Raw Input Candles
      ↓
[1] Schema & Type Validation (Numeric types, positive timestamps)
      ↓
[2] Geometric OHLC Bounds Check:
    - High >= max(Open, Close)
    - Low <= min(Open, Close)
    - Open > 0, High > 0, Low > 0, Close > 0, Volume >= 0
      ↓
[3] Duplicate Timestamp Suppression (Discards duplicate timestamp bars)
      ↓
[4] Chronological Ordering Check (Ensures t_i > t_{i-1})
      ↓
[5] Gap Detection (Flags delta_t > 1.5 * expected_interval)
      ↓
[6] Staleness Evaluation (Flags delta_now > 2.5 * expected_interval + 60s)
      ↓
Clean Immutable Dataset & Quality Report
```

### Data Quality States
- `HEALTHY`: Clean, ordered, uninterrupted chronological observations with no anomalies.
- `WARNING`: Gaps detected or data slightly delayed, but enough continuous history remains.
- `INVALID`: Fatal geometric anomalies or corrupt timestamp sequences detected.
- `INSUFFICIENT_DATA`: Total valid candle count is below the minimum lookback required.
- `OFFLINE`: No connection or stream initiated.

> [!IMPORTANT]
> **No Silent Data Repair**: The validator never fabricates synthetic candles or interpolates prices. If a gap occurs, `gap_count` is incremented and the engine calculates indicators over the available continuous observations.

---

## 2. Technical Indicator Suite

### A. Trend Indicators

#### 1. Exponential Moving Average (EMA)
- **Periods**: 9, 21, 50, 100, 200
- **Formula**:
  $$\alpha = \frac{2}{N + 1}$$
  $$EMA_t = Close_t \cdot \alpha + EMA_{t-1} \cdot (1 - \alpha)$$
- **Warmup**: First $N$ bars are initialized with the Simple Moving Average ($SMA_N$). Any bar index $< N - 1$ returns `null` (`INSUFFICIENT_DATA`).

#### 2. Rolling 24-Hour VWAP
- **Methodology**: `ROLLING_24H` (Continuous rolling volume-weighted average price tailored for 24/7 crypto markets).
- **Source Price**: Typical Price $TP = \frac{\text{High} + \text{Low} + \text{Close}}{3}$.
- **Formula**:
  $$VWAP_t = \frac{\sum_{i \in \text{window}} TP_i \cdot Volume_i}{\sum_{i \in \text{window}} Volume_i}$$
  $$\text{Window} = [ts_t - 24 \text{ hours}, ts_t]$$

#### 3. Average Directional Index (ADX) & Directional Movement
- **Period**: 14 (Wilder's RMA smoothing)
- **Formula**:
  - $+DM = \text{High}_t - \text{High}_{t-1} \text{ if } (> \text{Low}_{t-1} - \text{Low}_t \text{ and } > 0) \text{ else } 0$
  - $-DM = \text{Low}_{t-1} - \text{Low}_t \text{ if } (> \text{High}_t - \text{High}_{t-1} \text{ and } > 0) \text{ else } 0$
  - $TR = \max(\text{High}_t - \text{Low}_t, |\text{High}_t - \text{Close}_{t-1}|, |\text{Low}_t - \text{Close}_{t-1}|)$
  - $+DI = \frac{\text{RMA}(+DM, 14)}{\text{RMA}(TR, 14)} \cdot 100$
  - $-DI = \frac{\text{RMA}(-DM, 14)}{\text{RMA}(TR, 14)} \cdot 100$
  - $DX = \frac{|+DI - -DI|}{+DI + -DI} \cdot 100$
  - $ADX = \text{RMA}(DX, 14)$
- **Warmup**: Requires at least $2 \times \text{period} = 28$ bars.

#### 4. Supertrend
- **Period**: 10 | **Multiplier**: 3.0
- **Formula**:
  - $ATR = \text{WilderRMA}(TR, 10)$
  - $\text{Basic Upper} = \frac{\text{High} + \text{Low}}{2} + 3.0 \cdot ATR$
  - $\text{Basic Lower} = \frac{\text{High} + \text{Low}}{2} - 3.0 \cdot ATR$
  - $\text{Final Upper}_t = \text{Basic Upper}_t \text{ if } (\text{Basic Upper}_t < \text{Final Upper}_{t-1} \text{ or } \text{Close}_{t-1} > \text{Final Upper}_{t-1}) \text{ else } \text{Final Upper}_{t-1}$
  - $\text{Final Lower}_t = \text{Basic Lower}_t \text{ if } (\text{Basic Lower}_t > \text{Final Lower}_{t-1} \text{ or } \text{Close}_{t-1} < \text{Final Lower}_{t-1}) \text{ else } \text{Final Lower}_{t-1}$
  - Direction switches to $+1$ (Bullish) when $\text{Close}_t > \text{Final Upper}_{t-1}$, and $-1$ (Bearish) when $\text{Close}_t < \text{Final Lower}_{t-1}$.

---

### B. Momentum Indicators

#### 1. Relative Strength Index (RSI)
- **Period**: 14
- **Methodology**: Standard Wilder's Running Moving Average (RMA).
- **Formula**:
  $$RS = \frac{\text{RMA}(\text{Gains}, 14)}{\text{RMA}(\text{Losses}, 14)}$$
  $$RSI = 100 - \frac{100}{1 + RS}$$

#### 2. MACD (Moving Average Convergence Divergence)
- **Fast**: 12 | **Slow**: 26 | **Signal**: 9
- **Formula**:
  $$\text{MACD Line} = EMA_{12}(\text{Close}) - EMA_{26}(\text{Close})$$
  $$\text{Signal Line} = EMA_9(\text{MACD Line})$$
  $$\text{Histogram} = \text{MACD Line} - \text{Signal Line}$$

#### 3. Stochastic RSI
- **Period**: 14 | **%K Smoothing**: 3 | **%D Smoothing**: 3
- **Formula**:
  $$\text{StochRSI}_{\text{raw}} = \frac{RSI_t - \min_{14}(RSI)}{\max_{14}(RSI) - \min_{14}(RSI)} \cdot 100$$
  $$\%K = SMA_3(\text{StochRSI}_{\text{raw}})$$
  $$\%D = SMA_3(\%K)$$

#### 4. Rate of Change (ROC)
- **Period**: 12
- **Formula**:
  $$ROC_t = \frac{\text{Close}_t - \text{Close}_{t-12}}{\text{Close}_{t-12}} \cdot 100$$

---

### C. Volatility Indicators

#### 1. Average True Range (ATR)
- **Period**: 14 (Wilder smoothing of True Range)
- **Formula**:
  $$TR_t = \max(\text{High}_t - \text{Low}_t, |\text{High}_t - \text{Close}_{t-1}|, |\text{Low}_t - \text{Close}_{t-1}|)$$
  $$ATR_t = \text{WilderRMA}(TR, 14)$$

#### 2. Bollinger Bands
- **Period**: 20 | **Standard Deviations**: 2.0
- **Formula**:
  $$\text{Middle} = SMA_{20}(\text{Close})$$
  $$\text{Upper} = \text{Middle} + 2 \cdot \sigma_{20}$$
  $$\text{Lower} = \text{Middle} - 2 \cdot \sigma_{20}$$
  $$\text{Bandwidth} = \frac{\text{Upper} - \text{Lower}}{\text{Middle}} \cdot 100$$
  $$\%B = \frac{\text{Close} - \text{Lower}}{\text{Upper} - \text{Lower}}$$

---

### D. Volume Indicators

#### 1. Volume SMA
- **Period**: 20
- **Formula**: $SMA_{20}(\text{Volume})$

#### 2. Relative Volume (RVol)
- **Formula**:
  $$\text{RVol}_t = \frac{\text{Volume}_t}{SMA_{20}(\text{Volume})_{t-1}}$$
- Measures current bar volume against established 20-period baseline volume.

#### 3. On-Balance Volume (OBV)
- **Formula**:
  $$OBV_t = OBV_{t-1} + \begin{cases} \text{Volume}_t & \text{if } \text{Close}_t > \text{Close}_{t-1} \\ -\text{Volume}_t & \text{if } \text{Close}_t < \text{Close}_{t-1} \\ 0 & \text{if } \text{Close}_t = \text{Close}_{t-1} \end{cases}$$

---

## 3. Realtime vs Confirmed Separation & Non-Repainting Guarantee

```
  Candle Ticks (WebSocket)
          │
          ▼
   [Candle is OPEN / UPDATING]
          │
          ├─────────────────────────► Realtime Indicators (Live Overlays / UI)
          ▼                           (Explicitly unconfirmed)
  [Candle CLOSES (x=True)]
          │
          ▼
  Confirmed Indicators Calculated ──► Immutable Snapshot (Database / Backtester)
                                      (Never modified by future candles)
```

1. **Confirmed State**: Calculated strictly over completed (`CLOSED`) intervals. Persisted to database and used for backtesting and future signal evaluation.
2. **Realtime State**: Calculated including the currently forming bar for immediate chart visualization and live monitoring.
3. **Immutability Guarantee**: `IndicatorEngine` never mutates the input dataset, and historical confirmed snapshots never repaint.

---

## 4. API Endpoints

### 1. `GET /api/v1/analysis/indicators`
**Query Parameters**:
- `symbol` (e.g. `BTCUSDT`)
- `timeframe` (`1m`, `5m`, `15m`, `1h`, `4h`, `1d`)
- `limit` (lookback candle count, default: 300)
- `include_realtime` (`true` or `false`, default: `false`)

**Example Real Response (`BTCUSDT` 15m)**:
```json
{
  "symbol": "BTCUSDT",
  "timeframe": "15m",
  "quality": {
    "symbol": "BTCUSDT",
    "timeframe": "15m",
    "status": "HEALTHY",
    "latest_timestamp": 1787578200000,
    "candle_count": 300,
    "duplicate_count": 0,
    "gap_count": 0,
    "invalid_count": 0,
    "stale": false,
    "validation_messages": []
  },
  "confirmed_snapshot": {
    "symbol": "BTCUSDT",
    "timeframe": "15m",
    "timestamp": 1787578200000,
    "is_confirmed": true,
    "quality_status": "HEALTHY",
    "indicator_engine_version": "0.3.0",
    "indicator_config_version": "2026-08-24-v1",
    "trend": {
      "ema_9": 78652.46,
      "ema_21": 78230.01,
      "ema_50": 77804.97,
      "ema_100": 77552.61,
      "ema_200": 77458.68,
      "vwap": 77692.97,
      "adx": 26.70,
      "plus_di": 29.78,
      "minus_di": 16.46,
      "supertrend": 78023.73,
      "supertrend_direction": 1
    },
    "momentum": {
      "rsi": 59.08,
      "macd": 411.09,
      "macd_signal": 326.86,
      "macd_histogram": 84.23,
      "stoch_rsi_k": 64.15,
      "stoch_rsi_d": 82.82,
      "roc": 1.14
    },
    "volatility": {
      "atr": 369.02,
      "bb_upper": 79353.17,
      "bb_middle": 78092.29,
      "bb_lower": 76831.41,
      "bb_bandwidth": 3.23,
      "bb_percent_b": 0.705
    },
    "volume": {
      "volume_sma": 360.41,
      "relative_volume": 2.39,
      "obv": -4460.10
    }
  },
  "calculation_timestamp": 1787578737898
}
```

### 2. `GET /api/v1/analysis/indicators/history`
Returns bar-aligned historical indicator values (`ema_9`, `ema_21`, `ema_50`, `ema_200`, `vwap`, `bb_upper`, `bb_middle`, `bb_lower`, `supertrend`, `rsi`, `macd`, `macd_signal`, `macd_histogram`) formatted for TradingView chart overlays.

### 3. `GET /api/v1/analysis/quality`
Returns `MarketDataQuality` report evaluating candle continuity, gaps, ordering, and staleness.
