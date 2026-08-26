# Market Structure & Price Action Engine

This document outlines the algorithms, confirmation timing, lifecycle state machines, and mathematical definitions for the **Market Structure Engine** implemented in **Phase 4**.

---

## 1. Pivot Swing Detection & Causal Confirmation Timing

Pivot swings are detected with a configurable left and right confirmation window ($LEFT=3, RIGHT=3$):

```
       [Swing High (Peak)]
             ▲  (Index N, Swing Timestamp = T_N)
            / \
           /   \
 [LEFT=3] /     \ [RIGHT=3 Confirmation Window]
                 \
                  ▼
         [Confirmation Point] (Index N+3, Confirmation Timestamp = T_{N+3})
```

### Rules & Causality Guarantee
1. **Swing High**: Bar $N$ satisfies $\text{High}_N > \text{High}_{N-k}$ for all $1 \le k \le 3$, and $\text{High}_N \ge \text{High}_{N+k} - \epsilon$ for all $1 \le k \le 3$.
2. **Confirmation Timestamp**: The swing occurred at $T_N$, but is marked as `is_confirmed=True` **only at** $T_{N+3}$.
3. **Equal Highs/Lows Tie Handling**: If two bars are within $\text{EQUAL\_TOLERANCE\_ATR} \times \text{ATR}$ (0.10 ATR), the earlier candidate peak takes precedence deterministically.
4. **Developing Swings**: Candidate peaks/valleys inside the latest 3 forming bars are placed into `developing_swings` (`is_confirmed=False`) and excluded from official structural calculations.

---

## 2. Break of Structure (BOS)

A Break of Structure represents continuation in the prevailing trend.

```
       ─── Previous Confirmed Swing High ────────────────────
                       ▲ (Wick crosses: NO BOS)
                      │
                   [Candle CLOSES above Level] ──► Confirmed Bullish BOS!
```

### Deterministic Rules:
1. **Candle CLOSE Required**: Intrabar wick crossings do **not** trigger a confirmed BOS. The candle must close beyond the level ($Close_t > SwingHigh.price$ or $Close_t < SwingLow.price$).
2. **Duplicate Suppression**: Once a specific swing level is broken by a confirmed close, that swing is marked as broken. Consecutive closes above that level do not emit duplicate BOS events.
3. **Break Quality Metrics**:
   - $\text{ATR Normalized Distance} = |Close_t - Level| / ATR_t$
   - $\text{Volume Ratio} = Volume_t / VolumeSMA_t$
   - $\text{Body Ratio} = |Close_t - Open_t| / (High_t - Low_t)$
   - If $\text{ATR Normalized} \ge 0.5$, $\text{Volume Ratio} \ge 1.5$, and $\text{Body Ratio} \ge 0.6 \implies \text{STRONG\_BREAK}$.

---

## 3. Change of Character (CHoCH)

A Change of Character represents a structural trend transition against the prior established sequence:

```
  Bearish Structure:  LH_1 ──► LL_1 ──► LH_2 ──► LL_2
                                         ▲
                                         │  (Confirmed Close ABOVE LH_2)
                                         └──► BULLISH CHoCH Transition Event
```

### Algorithm:
- **Bullish CHoCH**: In an established Lower High / Lower Low sequence, a confirmed candle close above the most recent confirmed Lower High marks a `BULLISH_CHOCH`.
- **Bearish CHoCH**: In an established Higher High / Higher Low sequence, a confirmed candle close below the most recent confirmed Higher Low marks a `BEARISH_CHOCH`.
- **Regime Independence**: A CHoCH event updates structural state (`structure_direction = TRANSITION`), but does **not** arbitrarily force the overall regime direction to reverse without supporting trend and momentum evidence.

---

## 4. ATR-Relative Support & Resistance Clustering

Confirmed swing highs are clustered into Resistance Zones, and confirmed swing lows into Support Zones:

$$\text{Cluster Distance Threshold} \le \text{SR\_CLUSTER\_ATR\_MULTIPLIER} \times \text{ATR} \quad (0.75 \times \text{ATR})$$

### Zone Lifecycle States
- `ACTIVE`: Current price has not breached through the zone boundaries.
- `TESTED`: Price has interacted with the zone multiple times ($\ge 2$ touches).
- `BROKEN`: A confirmed candle close crossed past the outer boundary of the zone.
- `INVALIDATED`: Price has moved far beyond the zone ($> 3 \times \text{ATR}$).

### Zone Strength
- `STRONG`: $\ge 3$ confirmed swing touches in the cluster
- `MODERATE`: $2$ confirmed touches
- `WEAK`: $1$ confirmed touch

---

## 5. API Endpoints

- `GET /api/v1/analysis/structure?symbol=BTCUSDT&timeframe=15m&include_realtime=false`
- `GET /api/v1/analysis/structure/history?symbol=BTCUSDT&timeframe=15m&limit=300`
