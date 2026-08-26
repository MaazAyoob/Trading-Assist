from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class DirectionEnum(str, Enum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    RANGE = "RANGE"
    UNCERTAIN = "UNCERTAIN"


class TrendStrengthEnum(str, Enum):
    NONE = "NONE"
    WEAK = "WEAK"
    MODERATE = "MODERATE"
    STRONG = "STRONG"
    VERY_STRONG = "VERY_STRONG"


class VolatilityStateEnum(str, Enum):
    VERY_LOW = "VERY_LOW"
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    EXTREME = "EXTREME"


class MomentumStateEnum(str, Enum):
    VERY_POSITIVE = "VERY_POSITIVE"
    POSITIVE = "POSITIVE"
    NEUTRAL = "NEUTRAL"
    NEGATIVE = "NEGATIVE"
    VERY_NEGATIVE = "VERY_NEGATIVE"


class VolumeStateEnum(str, Enum):
    LOW = "LOW"
    NORMAL = "NORMAL"
    ABOVE_AVERAGE = "ABOVE_AVERAGE"
    HIGH_EXPANSION = "HIGH_EXPANSION"


class StructureStateEnum(str, Enum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    RANGE = "RANGE"
    TRANSITION = "TRANSITION"
    UNKNOWN = "UNKNOWN"


class OverallRegimeEnum(str, Enum):
    TRENDING_BULLISH = "TRENDING_BULLISH"
    TRENDING_BEARISH = "TRENDING_BEARISH"
    RANGING = "RANGING"
    HIGH_VOLATILITY = "HIGH_VOLATILITY"
    LOW_VOLATILITY = "LOW_VOLATILITY"
    TRANSITION = "TRANSITION"
    UNCERTAIN = "UNCERTAIN"


class EvidenceCategoryEnum(str, Enum):
    TREND = "TREND"
    MOMENTUM = "MOMENTUM"
    VOLATILITY = "VOLATILITY"
    VOLUME = "VOLUME"
    STRUCTURE = "STRUCTURE"


class EvidenceItem(BaseModel):
    category: EvidenceCategoryEnum
    description: str
    metric_value: Optional[str] = None
    is_supporting: bool = True


class MarketRegimeSnapshot(BaseModel):
    """
    Standardized, multi-dimensional Market Regime Snapshot.
    Describes current market environment without generating trading signals.
    """

    symbol: str
    timeframe: str
    timestamp: int
    is_confirmed: bool = Field(True, description="True if calculated exclusively from CLOSED historical candles")

    direction: DirectionEnum
    trend_strength: TrendStrengthEnum
    volatility_state: VolatilityStateEnum
    momentum_state: MomentumStateEnum
    volume_state: VolumeStateEnum
    structure_state: StructureStateEnum
    overall_regime: OverallRegimeEnum

    evidence_strength: float = Field(
        ...,
        description="Deterministic rule agreement metric (0.0 to 100.0). NOT a probability of future price movement.",
    )

    evidence: List[EvidenceItem] = Field(default_factory=list)
    contradictions: List[EvidenceItem] = Field(default_factory=list)

    regime_engine_version: str = Field("0.4.0")
    regime_config_version: str = Field("2026-08-24-v1")
