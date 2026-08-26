from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class SwingTypeEnum(str, Enum):
    SWING_HIGH = "SWING_HIGH"
    SWING_LOW = "SWING_LOW"


class StructureEventTypeEnum(str, Enum):
    BULLISH_BOS = "BULLISH_BOS"
    BEARISH_BOS = "BEARISH_BOS"
    BULLISH_CHOCH = "BULLISH_CHOCH"
    BEARISH_CHOCH = "BEARISH_CHOCH"


class BreakQualityEnum(str, Enum):
    WEAK_BREAK = "WEAK_BREAK"
    NORMAL_BREAK = "NORMAL_BREAK"
    STRONG_BREAK = "STRONG_BREAK"


class ZoneTypeEnum(str, Enum):
    SUPPORT = "SUPPORT"
    RESISTANCE = "RESISTANCE"


class ZoneStatusEnum(str, Enum):
    ACTIVE = "ACTIVE"
    TESTED = "TESTED"
    BROKEN = "BROKEN"
    INVALIDATED = "INVALIDATED"


class ZoneStrengthEnum(str, Enum):
    WEAK = "WEAK"
    MODERATE = "MODERATE"
    STRONG = "STRONG"


class SwingPoint(BaseModel):
    id: str
    type: SwingTypeEnum
    price: float
    swing_timestamp: int
    confirmation_timestamp: int
    is_confirmed: bool = True
    volume: float = 0.0
    atr_normalized_magnitude: Optional[float] = None


class StructureEvent(BaseModel):
    event_id: str
    event_type: StructureEventTypeEnum
    broken_swing_id: str
    broken_level: float
    break_timestamp: int
    confirmation_timestamp: int
    close_price: float
    break_distance: float
    atr_normalized_distance: float
    volume_ratio: float
    candle_body_ratio: float
    break_quality: BreakQualityEnum
    is_confirmed: bool = True


class SupportResistanceZone(BaseModel):
    zone_id: str
    zone_type: ZoneTypeEnum
    price_low: float
    price_high: float
    price_center: float
    touch_count: int
    strength: ZoneStrengthEnum
    status: ZoneStatusEnum
    created_timestamp: int
    last_touch_timestamp: int


class MarketStructureSnapshot(BaseModel):
    """
    Complete Market Price Action Structure Snapshot.
    Tracks swings, BOS, CHoCH, and Support/Resistance clusters deterministically.
    """

    symbol: str
    timeframe: str
    timestamp: int
    is_confirmed: bool = True

    structure_direction: str = Field(
        ..., description="Structural trend state: BULLISH (HH/HL), BEARISH (LH/LL), RANGE, TRANSITION, UNKNOWN"
    )

    active_structural_high: Optional[SwingPoint] = None
    active_structural_low: Optional[SwingPoint] = None

    confirmed_swings: List[SwingPoint] = Field(default_factory=list)
    developing_swings: List[SwingPoint] = Field(default_factory=list)

    bos_events: List[StructureEvent] = Field(default_factory=list)
    choch_events: List[StructureEvent] = Field(default_factory=list)

    support_zones: List[SupportResistanceZone] = Field(default_factory=list)
    resistance_zones: List[SupportResistanceZone] = Field(default_factory=list)

    structure_engine_version: str = Field("0.4.0")
    structure_config_version: str = Field("2026-08-24-v1")
