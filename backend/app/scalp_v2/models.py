"""
SCALP_STRATEGY_V2 — Pydantic Models.
Higher-frequency 1-minute BTCUSDT scalping strategy models.
"""
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from app.scalp_v2.version import SCALP_STRATEGY_V2_ID, SCALP_STRATEGY_V2_VERSION


class ScalpV2Direction(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    WATCH = "WATCH"
    NO_TRADE = "NO_TRADE"


class ScalpV2SetupType(str, Enum):
    TREND_CONTINUATION = "TREND_CONTINUATION"
    PULLBACK = "PULLBACK"
    MOMENTUM_BREAKOUT = "MOMENTUM_BREAKOUT"
    NONE = "NONE"


class ScalpV2TradeState(str, Enum):
    NO_TRADE = "NO_TRADE"
    WATCH = "WATCH"
    BUY = "BUY"
    SELL = "SELL"


class ScalpV2Lifecycle(str, Enum):
    WAITING = "WAITING"
    ENTRY_READY = "ENTRY_READY"
    ACTIVE = "ACTIVE"
    INVALIDATED = "INVALIDATED"
    EXPIRED = "EXPIRED"


class ScalpV2Strength(str, Enum):
    VERY_STRONG = "VERY STRONG"
    STRONG = "STRONG"
    MODERATE = "MODERATE"
    WEAK = "WEAK"
    WATCH = "WATCH"
    NO_TRADE = "NO TRADE"


class ScalpV2ScoreFactor(BaseModel):
    name: str
    timeframe: str                      # "1m", "5m", "15m"
    score: float                        # positive = bullish, negative = bearish
    max_score: float
    direction: str                      # "BULLISH", "BEARISH", "NEUTRAL"
    detail: str                         # human-readable factor analysis


class ScalpV2ScoreBreakdown(BaseModel):
    factors: List[ScalpV2ScoreFactor] = Field(default_factory=list)
    raw_bull_score: float = 0.0
    raw_bear_score: float = 0.0
    net_score: float = 0.0              # -100 to +100 range
    normalised_score: float = 0.0       # 0 to 100 displayed alignment score
    setup_bonus: float = 0.0            # up to ±20 for recognized setup patterns


class ScalpV2Entry(BaseModel):
    planned_entry: Optional[float] = None
    entry_zone_low: Optional[float] = None
    entry_zone_high: Optional[float] = None
    reference_price: Optional[float] = None


class ScalpV2StopLoss(BaseModel):
    price: Optional[float] = None
    risk_distance: Optional[float] = None
    risk_distance_atr: Optional[float] = None


class ScalpV2TakeProfits(BaseModel):
    tp1: Optional[float] = None
    tp2: Optional[float] = None
    tp3: Optional[float] = None
    rr_tp1: Optional[float] = None
    rr_tp2: Optional[float] = None
    rr_tp3: Optional[float] = None


class ScalpV2Signal(BaseModel):
    strategy_id: str = SCALP_STRATEGY_V2_ID
    strategy_version: str = SCALP_STRATEGY_V2_VERSION
    symbol: str = "BTCUSDT"
    primary_timeframe: str = "1m"
    direction: ScalpV2Direction = ScalpV2Direction.NO_TRADE
    trade_state: ScalpV2TradeState = ScalpV2TradeState.NO_TRADE
    lifecycle: ScalpV2Lifecycle = ScalpV2Lifecycle.WAITING
    setup_type: ScalpV2SetupType = ScalpV2SetupType.NONE
    score: float = 0.0                  # -100 to +100 net score
    alignment_score: float = 0.0        # 0 to 100 deterministic alignment
    strength: ScalpV2Strength = ScalpV2Strength.NO_TRADE
    is_preview: bool = False
    candle_timestamp: int = 0
    calculation_timestamp: int = 0
    score_breakdown: ScalpV2ScoreBreakdown = Field(default_factory=ScalpV2ScoreBreakdown)
    entry: ScalpV2Entry = Field(default_factory=ScalpV2Entry)
    stop_loss: ScalpV2StopLoss = Field(default_factory=ScalpV2StopLoss)
    take_profits: ScalpV2TakeProfits = Field(default_factory=ScalpV2TakeProfits)
    supporting_factors: List[str] = Field(default_factory=list)
    conflicting_factors: List[str] = Field(default_factory=list)
    invalidation_conditions: List[str] = Field(default_factory=list)
    context_5m_trend: str = "UNKNOWN"
    context_15m_trend: str = "UNKNOWN"


class ScalpV2Response(BaseModel):
    confirmed_signal: ScalpV2Signal
    preview_signal: Optional[ScalpV2Signal] = None
    calculation_timestamp: int


class ScalpV2HistoryItem(BaseModel):
    timestamp: int
    direction: ScalpV2Direction
    score: float
    alignment_score: float
    setup_type: ScalpV2SetupType
    strength: ScalpV2Strength
    entry_price: Optional[float]
    stop_loss: Optional[float]
    tp1: Optional[float]
    lifecycle: ScalpV2Lifecycle


class ScalpV2StatsResponse(BaseModel):
    strategy_id: str = SCALP_STRATEGY_V2_ID
    symbol: str = "BTCUSDT"
    total_candles_evaluated: int = 0
    signals_last_hour: int = 0
    signals_last_4_hours: int = 0
    signals_last_24_hours: int = 0
    buy_count: int = 0
    sell_count: int = 0
    watch_count: int = 0
    no_trade_count: int = 0
    average_score: float = 0.0
    average_abs_score: float = 0.0
    min_score: float = 0.0
    max_score: float = 0.0
    setup_distribution: Dict[str, int] = Field(default_factory=dict)
    calculation_timestamp: int = 0


class ScalpCompareResponse(BaseModel):
    symbol: str = "BTCUSDT"
    timeframe: str = "1m"
    calculation_timestamp: int
    v1: dict
    v2: dict
