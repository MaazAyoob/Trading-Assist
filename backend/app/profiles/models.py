"""
Pydantic data models for Phase 12 Trading Profiles & Multi-Timeframe Orchestration.
"""

from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from app.data.schema import Candle, MarketDataQuality
from app.indicators.base import IndicatorSnapshot
from app.regime.models import MarketRegimeSnapshot
from app.structure.models import MarketStructureSnapshot
from app.signals.models import ResearchSignal
from app.trade_decision.models import TradePlan


class ProfileEnum(str, Enum):
    SCALP = "SCALP"
    INTRADAY = "INTRADAY"
    TRADING = "TRADING"
    SWING = "SWING"
    POSITION = "POSITION"


class ProfileLifecycleStatus(str, Enum):
    RESEARCH = "RESEARCH"
    VALIDATING = "VALIDATING"
    OBSERVATION = "OBSERVATION"
    APPROVED_FOR_ANALYTICAL_USE = "APPROVED_FOR_ANALYTICAL_USE"


class ProfileStateEnum(str, Enum):
    NO_TRADE = "NO_TRADE"
    WATCH = "WATCH"
    SETUP = "SETUP"
    ENTRY_READY = "ENTRY_READY"
    INVALIDATED = "INVALIDATED"
    EXPIRED = "EXPIRED"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


class TradingProfileConfig(BaseModel):
    """
    Static, predefined configuration for a trading profile.
    Immutable definition containing timeframe hierarchy and policy requirements.
    """
    profile_id: str
    display_name: str
    description: str
    profile_type: ProfileEnum
    primary_timeframe: str
    context_timeframes: List[str]
    expected_holding_horizon: str
    minimum_data_requirements: int = Field(default=60, description="Minimum closed candles required")
    volatility_policy: str
    structure_requirement: str
    signal_evaluation_behavior: str
    entry_planning_context: str
    research_validation_requirements: str
    cost_sensitivity_bps: List[int] = Field(default_factory=lambda: [0, 5, 10, 15])
    status: ProfileLifecycleStatus = ProfileLifecycleStatus.APPROVED_FOR_ANALYTICAL_USE
    config_hash: str


class MultiTimeframeContext(BaseModel):
    """
    Synchronized multi-timeframe analytical context.
    Guarantees strict causal time alignment (context timestamps <= primary timestamp).
    """
    symbol: str
    primary_timeframe: str
    analytical_timestamp: int
    primary_candle: Candle
    context_timeframes: List[str]
    
    # Per-timeframe analytical states
    context_candles: Dict[str, Candle] = Field(default_factory=dict)
    context_indicators: Dict[str, IndicatorSnapshot] = Field(default_factory=dict)
    context_regimes: Dict[str, MarketRegimeSnapshot] = Field(default_factory=dict)
    context_structures: Dict[str, MarketStructureSnapshot] = Field(default_factory=dict)
    context_signals: Dict[str, ResearchSignal] = Field(default_factory=dict)
    context_qualities: Dict[str, MarketDataQuality] = Field(default_factory=dict)
    
    is_causally_valid: bool = True
    validation_messages: List[str] = Field(default_factory=list)


class CostSensitivityTier(BaseModel):
    """Transaction cost sensitivity evaluation tier."""
    cost_bps: int
    raw_analytical_return_pct: float
    estimated_cost_adjusted_return_pct: float
    cost_impact_pct: float
    is_cost_viable: bool
    warning_flag: Optional[str] = None


class ProfileAnalysisResult(BaseModel):
    """Authoritative analytical result for a trading profile."""
    profile_id: str
    symbol: str
    primary_timeframe: str
    context_timeframes: List[str]
    profile_state: ProfileStateEnum
    state_description: str
    
    # Linked Phase 10 Trade Plan
    trade_plan: Optional[TradePlan] = None
    
    # Multi-timeframe confirmation status
    context_confirmed: Dict[str, bool] = Field(default_factory=dict)
    alignment_score: float = Field(ge=0.0, le=100.0)
    score_tier: str
    
    # Cost sensitivity analysis
    cost_sensitivity: List[CostSensitivityTier] = Field(default_factory=list)
    cost_warning: Optional[str] = None
    
    analytical_timestamp: int
    is_preview: bool = False
    reasons: List[str] = Field(default_factory=list)


class ProfileComparisonItem(BaseModel):
    profile_id: str
    display_name: str
    primary_timeframe: str
    context_timeframes: List[str]
    expected_horizon: str
    signals_per_day: float
    clustering_factor: float
    median_5c_return_pct: float
    positive_rate_pct: float
    avg_mfe_pct: float
    avg_mae_pct: float
    cost_viable_10bps: bool
    status: str


class ProfileComparisonReport(BaseModel):
    generated_timestamp: int
    symbol: str
    profiles: List[ProfileComparisonItem]
