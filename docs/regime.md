# Market Regime Classification Engine

This document details the architecture, formulas, multidimensional taxonomy, and evidence synthesis implemented in **Phase 4** of the **Crypto AI Trading Intelligence Platform**.

---

## 1. Architecture & Core Philosophy

The `MarketRegimeEngine` is a deterministic, pure mathematical classifier. It maps technical indicator outputs and price action structure into independent environmental dimensions.

> [!IMPORTANT]
> **Strict Descriptive Boundary**: Market regime states (e.g. `TRENDING_BULLISH`, `RANGING`) describe current market characteristics and rule agreement. They do **not** represent trade recommendations, entry signals, price targets, or probabilistic forecasts.

```
Technical Indicator Snapshot + Confirmed Structure State
                             │
                             ▼
 ┌────────────────────────────────────────────────────────┐
 │                 MarketRegimeEngine                     │
 ├────────────────────────────┬───────────────────────────┤
 │ 1. Direction               │ BULLISH / BEARISH / RANGE │
 │ 2. Trend Strength          │ NONE / WEAK / MODERATE... │
 │ 3. Volatility State        │ VERY_LOW / NORMAL / HIGH..│
 │ 4. Momentum State          │ POSITIVE / NEGATIVE...    │
 │ 5. Volume State            │ LOW / NORMAL / EXPANSION  │
 │ 6. Price Structure State   │ BULLISH / BEARISH / RANGE │
 ├────────────────────────────┴───────────────────────────┤
 │ 7. Grouped Evidence & Contradictions                   │
 │ 8. Evidence Strength Metric (0.0 to 100.0)             │
 └────────────────────────────┬───────────────────────────┘
                             │
                             ▼
               MarketRegimeSnapshot (Immutable)
```

---

## 2. Independent Environmental Dimensions

### A. Direction (`direction`)
- `BULLISH`: Positive EMA alignment ($EMA_9 > EMA_{21} > EMA_{50}$), bullish Supertrend, $+DI > -DI$, and price above Rolling 24h VWAP.
- `BEARISH`: Inverted EMA alignment ($EMA_9 < EMA_{21} < EMA_{50}$), bearish Supertrend, $-DI > +DI$, and price below Rolling 24h VWAP.
- `RANGE`: ADX $< \text{ADX\_TREND\_THRESHOLD}$ (25.0), flat/converged EMAs.
- `UNCERTAIN`: Conflicting trend-family signals.

### B. Trend Strength (`trend_strength`)
Evaluated via ADX, EMA separation, and Supertrend persistence:
- `NONE`: $ADX < 15.0$
- `WEAK`: $15.0 \le ADX < 25.0$
- `MODERATE`: $25.0 \le ADX < 35.0$
- `STRONG`: $35.0 \le ADX < 50.0$
- `VERY_STRONG`: $ADX \ge 50.0$

### C. Volatility State (`volatility_state`)
Uses normalized ATR relative to price ($ATR\% = ATR / Close \times 100$) evaluated against its rolling historical percentile distribution (50 bars lookback):
- `VERY_LOW`: $\le 15\text{th}$ percentile (Range compression)
- `LOW`: $15\text{th} - 35\text{th}$ percentile
- `NORMAL`: $35\text{th} - 70\text{th}$ percentile
- `HIGH`: $70\text{th} - 88\text{th}$ percentile
- `EXTREME`: $\ge 88\text{th}$ percentile (Severe expansion / shock volatility)

### D. Momentum State (`momentum_state`)
- `VERY_POSITIVE`: RSI $\ge 70.0$ (Overbought condition highlighted as potential exhaustion contradiction)
- `POSITIVE`: RSI $\ge 52.0$ with MACD Histogram $> 0$
- `NEUTRAL`: RSI between $48.0$ and $52.0$ or divergent MACD
- `NEGATIVE`: RSI $\le 48.0$ with MACD Histogram $< 0$
- `VERY_NEGATIVE`: RSI $\le 30.0$ (Oversold condition highlighted as contradiction)

### E. Volume State (`volume_state`)
- `LOW`: $RVol \le 0.70$
- `NORMAL`: $0.70 < RVol < 1.50$
- `ABOVE_AVERAGE`: $1.50 \le RVol < 2.00$
- `HIGH_EXPANSION`: $RVol \ge 2.00$ (Heavy volume participation)

### F. Overall Synthesized Regime (`overall_regime`)
- `TRENDING_BULLISH`: `direction == BULLISH` and `trend_strength >= MODERATE`
- `TRENDING_BEARISH`: `direction == BEARISH` and `trend_strength >= MODERATE`
- `HIGH_VOLATILITY`: `volatility_state == EXTREME`
- `LOW_VOLATILITY`: `volatility_state == VERY_LOW` and `trend_strength <= WEAK`
- `RANGING`: `direction == RANGE` or `trend_strength == NONE`
- `TRANSITION`: `structure_state == TRANSITION`
- `UNCERTAIN`: Mixed, unconfirmed environment

---

## 3. Grouped Evidence & Rule Agreement

To prevent five correlated indicators (e.g. 5 EMAs) from dominating the classification, evidence is grouped into 5 weighted families:
- **Trend Group** (Weight: 30%): EMA stack, Supertrend, +DI/-DI, VWAP
- **Momentum Group** (Weight: 20%): RSI, MACD, StochRSI, ROC
- **Structure Group** (Weight: 25%): Confirmed Higher Highs / Lows, BOS, CHoCH
- **Volatility Group** (Weight: 15%): Normalized ATR% percentile, Bollinger bandwidth
- **Volume Group** (Weight: 10%): Relative volume (RVol)

$$\text{evidence\_strength} = \sum_{g} \text{score}_g \cdot \text{weight}_g \times 100.0$$

> [!NOTE]
> `evidence_strength` is a measure of internal rule consistency (0.0 to 100.0). It is **never** presented as a win probability.

---

## 4. API Endpoints

- `GET /api/v1/analysis/regime?symbol=BTCUSDT&timeframe=15m&include_realtime=false`
- `GET /api/v1/analysis/regime/history?symbol=BTCUSDT&timeframe=15m&limit=50`
