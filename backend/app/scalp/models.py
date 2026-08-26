"""
SCALP_STRATEGY_V1 — Pydantic models.

Independent of Phase 5 Signal Engine. Does NOT modify any existing models.
"""
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


SCALP_STRATEGY_VERSION = "1.0.0"
SCALP_STRATEGY_ID = "SCALP_STRATEGY_V1"


class ScalpDirection(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    NO_TRADE = "NO_TRADE"


class ScalpScoreFactor(BaseModel):
    name: str
    timeframe: str                   # "1m", "5m", "15m"
    score: float                     # positive = bullish contribution, negative = bearish
    max_score: float
    direction: str                   # "BULLISH", "BEARISH", "NEUTRAL"
    detail: str                      # human-readable explanation


class ScalpScoreBreakdown(BaseModel):
    factors: List[ScalpScoreFactor] = Field(default_factory=list)
    raw_bull_score: float = 0.0      # sum of positive contributions (0-100)
    raw_bear_score: float = 0.0      # sum of negative contributions (0-100, positive number)
    net_score: float = 0.0           # bull - bear, on -100..+100 scale
    normalised_score: float = 0.0    # 0-100 displayed score (abs net mapped)


class ScalpTradePlan(BaseModel):
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    tp1: Optional[float] = None
    tp2: Optional[float] = None
    tp3: Optional[float] = None
    rr_tp1: Optional[float] = None
    rr_tp2: Optional[float] = None
    rr_tp3: Optional[float] = None
    atr_used: Optional[float] = None
    plan_available: bool = False
    plan_rejection_reason: Optional[str] = None


class ScalpSignal(BaseModel):
    strategy_id: str = SCALP_STRATEGY_ID
    strategy_version: str = SCALP_STRATEGY_VERSION
    symbol: str
    primary_timeframe: str = "1m"
    direction: ScalpDirection = ScalpDirection.NO_TRADE
    score_breakdown: ScalpScoreBreakdown
    trade_plan: ScalpTradePlan = Field(default_factory=ScalpTradePlan)
    is_preview: bool = False            # True = forming 1m candle, not confirmed
    candle_timestamp: int = 0           # ms timestamp of the 1m candle that produced this signal
    calculation_timestamp: int = 0      # ms timestamp of computation
    reasons: List[str] = Field(default_factory=list)
    invalidation_conditions: List[str] = Field(default_factory=list)
    # Context summaries
    context_5m_trend: str = "UNKNOWN"   # "BULLISH" | "BEARISH" | "NEUTRAL" | "UNKNOWN"
    context_15m_trend: str = "UNKNOWN"
    phase5_research_direction: str = "NEUTRAL"  # read-only display, not used as gate
