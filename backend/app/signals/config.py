from pydantic import BaseModel, Field
from app.signals.version import SIGNAL_ENGINE_VERSION, SIGNAL_CONFIG_VERSION


class SignalConfig(BaseModel):
    """
    Centralized, versioned configuration for the Multi-Factor Signal Research Engine.
    All weights, modifiers, penalties, and thresholds are fully configurable.
    """

    engine_version: str = Field(SIGNAL_ENGINE_VERSION)
    config_version: str = Field(SIGNAL_CONFIG_VERSION)
    research_mode: bool = Field(True, description="Strict research mode flag; zero live execution")

    # Directional Group Weights (Total = 1.00)
    WEIGHT_TREND: float = Field(0.30, description="Base weight for Trend evidence group")
    WEIGHT_MOMENTUM: float = Field(0.20, description="Base weight for Momentum evidence group")
    WEIGHT_STRUCTURE: float = Field(0.35, description="Base weight for Price Structure evidence group")
    WEIGHT_VOLUME: float = Field(0.15, description="Base weight for Volume evidence group")

    # Volatility Contextual Modifiers (Multiplicative quality scale 0.0 to 1.0)
    VOL_MOD_NORMAL: float = Field(1.00, description="Normal volatility quality modifier")
    VOL_MOD_LOW: float = Field(0.95, description="Low volatility quality modifier")
    VOL_MOD_VERY_LOW: float = Field(0.85, description="Very low volatility quality modifier (compression)")
    VOL_MOD_HIGH: float = Field(0.85, description="High volatility quality modifier")
    VOL_MOD_EXTREME: float = Field(0.60, description="Extreme volatility quality modifier (shock risk)")

    # Regime Compatibility Modifiers
    REGIME_MOD_COMPATIBLE: float = Field(1.00, description="Regime aligned with setup direction")
    REGIME_MOD_NEUTRAL: float = Field(0.85, description="Regime ranging or transition")
    REGIME_MOD_OPPOSING: float = Field(0.75, description="Regime opposing setup direction")
    REGIME_MOD_UNCERTAIN: float = Field(0.70, description="Regime state uncertain")

    # Setup Classification Score Thresholds
    SCORE_LONG_THRESHOLD: float = Field(45.0, description="Minimum net score for LONG_SETUP")
    SCORE_SHORT_THRESHOLD: float = Field(-45.0, description="Maximum net score for SHORT_SETUP")
    SCORE_NEUTRAL_BAND: float = Field(30.0, description="Score magnitude boundary below which setup is NEUTRAL")

    # Minimum Independent Agreement Gates
    MIN_TREND_AGREEMENT: float = Field(30.0, description="Minimum Trend score required for directional setup")
    MIN_STRUCTURE_AGREEMENT: float = Field(30.0, description="Minimum Structure score required for directional setup")

    # Proximity & Conflict Thresholds
    SR_PROXIMITY_ATR_MULTIPLIER: float = Field(0.25, description="Distance to opposing S/R zone (in ATR) that triggers proximity penalty")
    PENALTY_LOW: float = Field(5.0, description="Penalty deduction for LOW severity conflict")
    PENALTY_MEDIUM: float = Field(15.0, description="Penalty deduction for MEDIUM severity conflict")
    PENALTY_HIGH: float = Field(25.0, description="Penalty deduction for HIGH severity conflict")


default_signal_config = SignalConfig()
