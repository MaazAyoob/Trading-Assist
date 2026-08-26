from typing import List
from pydantic import BaseModel, Field


class RegimeConfig(BaseModel):
    """
    Centralized, versioned configuration for the Market Regime Engine.
    All thresholds for trend, momentum, volatility, volume, and structure are configurable.
    """

    regime_engine_version: str = Field("0.4.0", description="Semantic version of regime engine")
    regime_config_version: str = Field("2026-08-24-v1", description="Configuration schema revision")

    # ADX Trend Strength Thresholds
    ADX_TREND_THRESHOLD: float = Field(25.0, description="Minimum ADX to indicate directional trend")
    ADX_STRONG_TREND_THRESHOLD: float = Field(35.0, description="ADX indicating strong trend")
    ADX_VERY_STRONG_THRESHOLD: float = Field(50.0, description="ADX indicating extreme trend")

    # RSI Momentum Thresholds
    RSI_OVERBOUGHT_THRESHOLD: float = Field(70.0, description="RSI overbought boundary")
    RSI_OVERSOLD_THRESHOLD: float = Field(30.0, description="RSI oversold boundary")
    RSI_BULLISH_BIAS: float = Field(52.0, description="RSI baseline for bullish momentum")
    RSI_BEARISH_BIAS: float = Field(48.0, description="RSI baseline for bearish momentum")

    # Relative Volume Thresholds
    RVOL_HIGH_THRESHOLD: float = Field(1.5, description="Relative Volume indicating expansion")
    RVOL_LOW_THRESHOLD: float = Field(0.7, description="Relative Volume indicating low activity")

    # Rolling Percentile Lookback for Normalized Volatility (ATR / Close)
    VOLATILITY_LOOKBACK_BARS: int = Field(50, description="Bars to compute ATR% historical distribution")
    VOL_PERCENTILE_VERY_LOW: float = Field(0.15, description="Below 15th percentile: VERY_LOW")
    VOL_PERCENTILE_LOW: float = Field(0.35, description="15th-35th percentile: LOW")
    VOL_PERCENTILE_HIGH: float = Field(0.70, description="70th-88th percentile: HIGH")
    VOL_PERCENTILE_EXTREME: float = Field(0.88, description="Above 88th percentile: EXTREME")

    # Evidence Group Weights (for rule agreement classification_strength)
    WEIGHT_TREND: float = Field(0.30, description="Weight for Trend group")
    WEIGHT_MOMENTUM: float = Field(0.20, description="Weight for Momentum group")
    WEIGHT_STRUCTURE: float = Field(0.25, description="Weight for Price Structure group")
    WEIGHT_VOLATILITY: float = Field(0.15, description="Weight for Volatility group")
    WEIGHT_VOLUME: float = Field(0.10, description="Weight for Volume group")


default_regime_config = RegimeConfig()
