# Crypto AI Trading Intelligence Platform

A high-performance, deterministic crypto market intelligence and algorithmic trading analysis system built with **FastAPI**, **React + TypeScript**, **TradingView Lightweight Charts**, and **Tailwind CSS**.

---

## 🌟 Key Architecture & Highlights

- **Data Quality & Integrity Layer (`app/data/quality.py`)**:
  - Validates geometric OHLC bounds ($H \ge \max(O,C), L \le \min(O,C)$, positive prices, non-negative volume).
  - Duplicate timestamp suppression, chronological ordering, and interval-aware gap detection (without synthetic data fabrication).
- **Pure Quantitative Indicator Engine (`app/indicators/`)**:
  - **Trend**: EMA (9, 21, 50, 100, 200), Rolling 24h VWAP, ADX with +DI/-DI (Wilder smoothing), Supertrend (10, 3.0).
  - **Momentum**: RSI (14, Wilder RMA), MACD (12, 26, 9), Stochastic RSI (%K, %D), ROC % (12).
  - **Volatility**: ATR (14, Wilder smoothing), Bollinger Bands (20, 2.0 std) with Bandwidth % and %B.
  - **Volume**: Volume SMA (20), Relative Volume (RVol ratio), OBV (On-Balance Volume).
- **Market Regime Engine (`app/regime/`)**:
  - Independent multidimensional classification: Direction, Trend Strength, Volatility State (normalized rolling ATR% percentile), Momentum State, Volume State, and Structure State.
  - Grouped evidence weighting and internal rule consistency `evidence_strength` (0.0 to 100.0).
- **Market Structure Engine (`app/structure/`)**:
  - Causally verified Pivot Swings ($LEFT=3, RIGHT=3$) separating `CONFIRMED` ($T_{N+3}$) from `DEVELOPING` swings.
  - Break of Structure (BOS) requiring confirmed candle CLOSE, duplicate break suppression, and break quality metrics.
  - Change of Character (CHoCH) structural transition state machine.
  - ATR-relative Support & Resistance clustering with lifecycle tracking (`ACTIVE`, `TESTED`, `BROKEN`) and touch strength scoring.
- **Multi-Factor Signal Research Engine (`app/signals/`)**:
  - 4 Directional Evidence Groups (Trend: 30%, Momentum: 20%, Structure: 35%, Volume: 15%) normalized on a $[-100.0, +100.0]$ scale.
  - Contextual Modifiers: Regime compatibility ($0.70\times$ to $1.00\times$) and Volatility quality ($0.60\times$ to $1.00\times$).
  - Conflict Detection & Support/Resistance Proximity filtering (within $0.25\times \text{ATR}$).
  - Fully auditable mathematical score trace: $\text{Base} \times \text{Regime} \times \text{Vol} - \text{Penalties} = \text{Net Score}$.
  - Analytical classifications: `LONG_SETUP`, `SHORT_SETUP`, `NEUTRAL`, `WAIT`.
  - Strictly non-predictive research disclaimer: *"Research signal — not a guaranteed prediction."*
- **Trading Terminal UI**:
  - Real-time Candlestick chart with interactive toggleable overlays (EMA ribbons, VWAP, Bollinger Bands, Supertrend, Swings, S&R Zones, Research Signal Markers ▲/▼).
  - High-density Technical Indicator Matrix, Market Regime Panel, Market Structure Panel, and Multi-Factor Research Signal Panel.
  - Confirmed vs Live Forming view modes.
- **100% Passing Automated Tests**: **70/70** unit, mathematical, immutability, repainting, and live integration tests.

---

## 📁 Repository Structure

```
Trading Bot/
├── frontend/                     # React + Vite + TypeScript + Tailwind
│   ├── src/
│   │   ├── components/
│   │   │   ├── chart/            # TradingView chart with indicator, structure, and signal overlays
│   │   │   ├── indicators/       # Trend, Momentum, Volatility, Volume matrices & DataQuality badge
│   │   │   ├── regime/           # Market Regime Panel, Evidence & Contradictions
│   │   │   ├── structure/        # Market Structure Panel, BOS/CHoCH, S&R clusters
│   │   │   ├── intelligence/     # Multi-Factor Signal Research Panel & Score Trace
│   │   │   ├── layout/           # Header, bottom tabbed metrics shell
│   │   │   └── market/           # Ticker bar, Watchlist
│   │   ├── services/             # REST & Resilient WebSocket client
│   │   ├── stores/               # Zustand market, indicator, regime, structure & signal store
│   │   └── types/                # TypeScript schemas
│   ├── package.json
│   └── vite.config.ts
│
├── backend/                      # Python FastAPI Backend
│   ├── app/
│   │   ├── api/v1/endpoints/     # REST: /indicators, /regime, /structure, /signal, /quality, /ws
│   │   ├── core/                 # Timeframes, config, logging, custom exceptions
│   │   ├── data/                 # MarketDataProvider, Binance provider, Quality validator, WebSocket manager
│   │   ├── indicators/           # Pure technical indicators & non-repainting engine
│   │   ├── regime/               # Multi-dimensional market regime classifier & grouped evidence
│   │   ├── structure/            # Pivot swings, BOS, CHoCH, S&R clustering
│   │   ├── signals/              # Multi-Factor Signal Research Engine & Conflict Detector
│   │   ├── db/                   # Async SQLAlchemy session (SQLite / Postgres)
│   │   ├── models/               # ORM models (Candle, Ticker, Snapshot, Regime, Structure, Signal)
│   │   └── main.py               # FastAPI application with lifespan management
│   ├── requirements.txt
│   └── .env.example
│
├── tests/                        # Pytest test suite (70 tests)
│   ├── unit/                     # Math, indicators, swings, BOS/CHoCH, S&R, regime, signals, APIs
│   └── integration/              # Live Binance public endpoint integration tests
│
├── docs/                         # Documentation (indicators.md, regime.md, structure.md, signals.md)
├── .env.example
└── README.md
```

---

## 🧪 Running Automated Tests

Run the full 70-test suite:
```bash
backend\.venv\Scripts\pytest.exe tests -v -s
```
