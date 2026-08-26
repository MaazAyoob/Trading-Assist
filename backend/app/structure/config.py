from pydantic import BaseModel, Field


class StructureConfig(BaseModel):
    """
    Centralized, versioned configuration for the Market Structure Engine.
    """

    structure_engine_version: str = Field("0.4.0", description="Semantic version of structure engine")
    structure_config_version: str = Field("2026-08-24-v1", description="Structure configuration schema revision")

    # Pivot Swing Window Parameters
    SWING_LEFT: int = Field(3, description="Number of left-side bars required for pivot peak/valley")
    SWING_RIGHT: int = Field(3, description="Number of right-side confirmation bars required")
    EQUAL_TOLERANCE_ATR: float = Field(0.10, description="Tolerance for equal highs/lows in units of ATR")

    # Support / Resistance Clustering Parameters
    SR_CLUSTER_ATR_MULTIPLIER: float = Field(0.75, description="Proximity threshold for clustering swing levels into a single zone")
    SR_MIN_TOUCHES_STRONG: int = Field(3, description="Touch count threshold for STRONG rating")
    SR_MIN_TOUCHES_MODERATE: int = Field(2, description="Touch count threshold for MODERATE rating")

    # Break Quality Parameters
    BREAK_STRONG_ATR_DISTANCE: float = Field(0.5, description="ATR-normalized break distance indicating STRONG break")
    BREAK_STRONG_VOLUME_RATIO: float = Field(1.5, description="Volume ratio indicating institutional participation")
    BREAK_STRONG_BODY_RATIO: float = Field(0.60, description="Minimum body-to-candle ratio indicating conviction")


default_structure_config = StructureConfig()
