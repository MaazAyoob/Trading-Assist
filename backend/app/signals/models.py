from enum import Enum
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from app.data.schema import CandleStateEnum, MarketDataQuality
from app.signals.version import SIGNAL_ENGINE_VERSION, SIGNAL_CONFIG_VERSION


class SignalDirectionEnum(str, Enum):
    LONG_SETUP = "LONG_SETUP"
    SHORT_SETUP = "SHORT_SETUP"
    NEUTRAL = "NEUTRAL"


class SignalStrengthEnum(str, Enum):
    VERY_WEAK = "VERY_WEAK"
    WEAK = "WEAK"
    MODERATE = "MODERATE"
    STRONG = "STRONG"
    VERY_STRONG = "VERY_STRONG"


class SignalStatusEnum(str, Enum):
    VALID = "VALID"
    WAIT = "WAIT"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    CONFLICTED = "CONFLICTED"
    INVALID_DATA = "INVALID_DATA"


class ConflictSeverityEnum(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class EvidenceComponent(BaseModel):
    name: str
    raw_value: str
    contribution: float = Field(..., description="Signed numeric contribution (-max to +max)")
    direction: str = Field(..., description="BULLISH, BEARISH, or NEUTRAL")
    explanation: str


class EvidenceGroupScore(BaseModel):
    group_name: str
    score: float = Field(..., description="Normalized score on [-100, +100] scale")
    weight: float
    weighted_contribution: float
    state: str
    components: List[EvidenceComponent] = Field(default_factory=list)


class ConflictItem(BaseModel):
    conflict_id: str
    category: str
    severity: ConflictSeverityEnum
    raw_penalty: float
    applied_penalty: float
    explanation: str
    affected_groups: List[str] = Field(default_factory=list)


class ScoreTrace(BaseModel):
    """
    Complete mathematical reconstruction trace for auditable scoring.
    base_directional_score -> context_adjusted_score -> net_score.
    """

    trend_score: float
    momentum_score: float
    structure_score: float
    volume_score: float
    base_directional_score: float
    regime_modifier: float
    volatility_modifier: float
    context_adjusted_score: float
    total_conflict_penalty: float
    net_score: float


class ResearchSignal(BaseModel):
    """
    Deterministic Multi-Factor Research Signal Object.
    Contains mathematical score breakdown, grouped evidence, conflicts, and trace.
    Strictly descriptive analysis — NOT a guaranteed prediction or execution order.
    """

    symbol: str
    timeframe: str
    timestamp: int
    candle_state: CandleStateEnum
    is_confirmed: bool = Field(True, description="True if calculated strictly from CLOSED candles")
    is_historical: bool = Field(True, description="True if official immutable historical record")

    direction: SignalDirectionEnum
    strength: SignalStrengthEnum
    status: SignalStatusEnum
    score: float = Field(..., description="Final net evidence score on [-100.0, +100.0] scale")

    evidence_groups: Dict[str, EvidenceGroupScore]
    score_trace: ScoreTrace
    conflicts: List[ConflictItem] = Field(default_factory=list)
    supporting_evidence: List[str] = Field(default_factory=list)
    contradictions: List[str] = Field(default_factory=list)

    data_quality_status: str = Field("HEALTHY")
    disclaimer: str = Field("Research signal — not a guaranteed prediction.")

    engine_version: str = Field(SIGNAL_ENGINE_VERSION)
    config_version: str = Field(SIGNAL_CONFIG_VERSION)
