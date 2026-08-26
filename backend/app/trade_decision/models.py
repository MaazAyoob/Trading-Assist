"""
Phase 10 — Trade Decision Engine Data Models & Schemas.
Deterministic, auditable, fully JSON-serializable analytical models.
Strictly analytical research — NOT an execution order or guaranteed prediction.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.trade_decision.version import TRADE_DECISION_ENGINE_VERSION, TRADE_DECISION_CONFIG_VERSION


class TradeDecisionEnum(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    NO_TRADE = "NO_TRADE"


class TradePlanState(str, Enum):
    NO_TRADE = "NO_TRADE"
    WAITING_FOR_ENTRY = "WAITING_FOR_ENTRY"
    ENTRY_ZONE_ACTIVE = "ENTRY_ZONE_ACTIVE"
    INVALIDATED = "INVALIDATED"
    EXPIRED = "EXPIRED"


class DecisionStatusEnum(str, Enum):
    VALID = "VALID"
    WAITING = "WAITING"
    INVALID = "INVALID"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


class EntryTypeEnum(str, Enum):
    MARKET_REFERENCE = "MARKET_REFERENCE"
    PULLBACK_ZONE = "PULLBACK_ZONE"
    BREAKOUT_REFERENCE = "BREAKOUT_REFERENCE"


class ConfidenceGradeEnum(str, Enum):
    VERY_HIGH = "VERY_HIGH"    # 90-100
    HIGH = "HIGH"              # 75-89
    MODERATE = "MODERATE"      # 60-74
    LOW = "LOW"                # 40-59
    VERY_LOW = "VERY_LOW"      # 0-39


class AuditCheckStatusEnum(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class AuditCheckItem(BaseModel):
    check_name: str
    status: AuditCheckStatusEnum
    reason: str
    details: Dict[str, Any] = Field(default_factory=dict)


class DecisionAuditTrace(BaseModel):
    data_quality_check: AuditCheckItem
    signal_check: AuditCheckItem
    strategy_filter_check: AuditCheckItem
    regime_check: AuditCheckItem
    structure_check: AuditCheckItem
    sr_clearance_check: AuditCheckItem
    entry_check: AuditCheckItem
    stop_check: AuditCheckItem
    target_check: AuditCheckItem
    risk_reward_check: AuditCheckItem
    confidence_check: AuditCheckItem
    final_decision: AuditCheckItem


class EntryPlan(BaseModel):
    reference_price: float = Field(..., description="Current closed-candle reference price")
    planned_entry_price: float = Field(..., description="Deterministic price used for all SL/TP/RR calculations")
    entry_type: EntryTypeEnum
    entry_zone_low: float
    entry_zone_high: float
    formula_description: str


class StopLossPlan(BaseModel):
    price: float
    distance: float = Field(..., description="Absolute distance from planned_entry_price")
    distance_atr: float = Field(..., description="Distance in ATR units")
    reason: str
    structural_reference_level: Optional[float] = None
    atr_buffer_used: float


class TargetLevelDetail(BaseModel):
    original_target: float
    adjusted_target: float
    structural_level: Optional[float] = None
    adjustment_reason: str
    r_multiple_base: float
    actual_rr_after_adjustment: float
    distance: float
    constrained_by_structure: bool


class TakeProfitPlan(BaseModel):
    tp1: TargetLevelDetail
    tp2: TargetLevelDetail
    tp3: TargetLevelDetail


class RiskRewardSummary(BaseModel):
    tp1_rr: float
    tp2_rr: float
    tp3_rr: float
    risk_distance: float
    is_acceptable: bool
    rejection_reason: Optional[str] = None


class DecisionContext(BaseModel):
    signal_score: float
    regime: str
    trend_strength: str
    structure: str
    volatility: str
    momentum: str
    volume: str


class TradePlan(BaseModel):
    decision: TradeDecisionEnum
    direction: str = Field(..., description="LONG, SHORT, or NEUTRAL")
    state: TradePlanState
    status: DecisionStatusEnum

    decision_alignment_score: float = Field(..., ge=0.0, le=100.0, description="Internal alignment score (0-100). Not a probability.")
    confidence_grade: ConfidenceGradeEnum

    strategy_context_id: str = Field("PHASE5_BASELINE", description="Explicit strategy context: EXP_A2_PULLBACK_VWAP, EXP_E2_EXTENSION_VWAP, PHASE5_BASELINE")
    strategy_context_version: str = Field("1.0.0")
    strategy_config_hash: str = Field("N/A")

    symbol: str
    timeframe: str

    decision_candle_open_time: int
    decision_candle_close_time: int
    calculated_at: int
    market_data_last_updated_at: int

    created_at: int
    valid_until: int
    max_valid_candles: int
    bars_since_creation: int

    is_confirmed: bool = Field(True, description="True if computed strictly from closed candles")
    is_preview: bool = Field(False, description="True if realtime forming preview (not confirmed)")

    entry: Optional[EntryPlan] = None
    stop_loss: Optional[StopLossPlan] = None
    take_profits: Optional[TakeProfitPlan] = None
    risk_reward: Optional[RiskRewardSummary] = None

    context: DecisionContext
    supporting_factors: List[str] = Field(default_factory=list)
    conflicting_factors: List[str] = Field(default_factory=list)
    reasons_for_no_trade: List[str] = Field(default_factory=list)
    invalidation_conditions: List[str] = Field(default_factory=list)

    audit_trace: DecisionAuditTrace

    disclaimer: str = Field("ANALYTICAL TRADE PLAN — NOT A GUARANTEED PREDICTION")
    engine_version: str = Field(TRADE_DECISION_ENGINE_VERSION)
    config_version: str = Field(TRADE_DECISION_CONFIG_VERSION)


class MultiStrategyTradeDecisions(BaseModel):
    symbol: str
    timeframe: str
    timestamp: int
    selected_strategy_id: str
    primary_decision: TradePlan
    candidate_decisions: Dict[str, TradePlan] = Field(default_factory=dict)
