"""
SCALP_STRATEGY_V2 — Configuration and Parameters.
All weights, thresholds, and R:R parameters are fully configurable.
"""

# ── Factor Scoring Weights (Sum of base factors = 90.0, with setup bonus up to 20.0, bounded at ±100) ──
W_TREND_ALIGNMENT = 20.0   # 1m EMA 9 vs EMA 21 alignment
W_VWAP            = 15.0   # 1m Price vs VWAP position
W_MOMENTUM        = 15.0   # 1m MACD histogram & crossover
W_RSI             = 10.0   # 1m RSI oscillator momentum
W_VOLUME          = 10.0   # 1m Volume & relative volume
W_5M_CONTEXT      = 15.0   # 5m Trend alignment
W_15M_CONTEXT     = 5.0    # 15m Broader context
W_SETUP_BONUS     = 20.0   # Bonus reward for recognized setup pattern (Continuation / Pullback / Breakout)

# ── Signal Thresholds (V2 Higher-Frequency Scalp Thresholds) ───────────────────
BUY_THRESHOLD     = 35.0   # Net score >= +35
SELL_THRESHOLD    = -35.0  # Net score <= -35

WATCH_POS_MIN     = 20.0   # +20 to +34.99
WATCH_POS_MAX     = 34.99

WATCH_NEG_MIN     = -34.99 # -34.99 to -20
WATCH_NEG_MAX     = -20.0

NO_TRADE_MIN      = -19.99
NO_TRADE_MAX      = 19.99

# ── Strength Classification Bounds ───────────────────────────────────────────
STRENGTH_VERY_STRONG_MIN = 80.0
STRENGTH_STRONG_MIN      = 65.0
STRENGTH_MODERATE_MIN    = 50.0
STRENGTH_WEAK_MIN        = 35.0
STRENGTH_WATCH_MIN       = 20.0

# ── Duplicate Protection & Cooldown ───────────────────────────────────────────
MAX_COOLDOWN_CANDLES     = 2   # Max 2 closed 1m candles before a re-qualification can occur

# ── Trade Plan Defaults ────────────────────────────────────────────────────────
TP1_R_MULTIPLE           = 1.0
TP2_R_MULTIPLE           = 1.5
TP3_R_MULTIPLE           = 2.0

SL_ATR_MULTIPLIER        = 1.0
ENTRY_ZONE_ATR_FRACTION  = 0.25   # Entry zone width ±0.25 ATR
MAX_HISTORY_BUFFER_SIZE  = 100    # In-memory history buffer size
