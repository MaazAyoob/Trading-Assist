from typing import List
from pydantic import BaseModel, Field


class IndicatorConfig(BaseModel):
    """
    Centralized, serializable, versioned configuration for the quantitative technical indicator suite.
    Parameters are never hardcoded inside calculation routines.
    """

    indicator_engine_version: str = Field("0.3.0", description="Semantic version of indicator engine")
    indicator_config_version: str = Field("2026-08-24-v1", description="Configuration schema revision")

    # Trend Indicator Parameters
    EMA_PERIODS: List[int] = Field(default_factory=lambda: [9, 21, 50, 100, 200])
    VWAP_METHOD: str = Field("ROLLING_24H", description="Methodology: ROLLING_24H (24h continuous crypto lookback)")
    VWAP_WINDOW_HOURS: int = Field(24, description="Lookback duration for 24h rolling VWAP")
    ADX_PERIOD: int = Field(14, description="ADX / +DI / -DI period (Wilder smoothing)")
    SUPERTREND_PERIOD: int = Field(10, description="Supertrend ATR period")
    SUPERTREND_MULTIPLIER: float = Field(3.0, description="Supertrend ATR multiplier band")

    # Momentum Indicator Parameters
    RSI_PERIOD: int = Field(14, description="RSI lookback period (Wilder smoothing)")
    MACD_FAST: int = Field(12, description="MACD fast EMA period")
    MACD_SLOW: int = Field(26, description="MACD slow EMA period")
    MACD_SIGNAL: int = Field(9, description="MACD signal line EMA period")
    STOCH_RSI_PERIOD: int = Field(14, description="Stochastic RSI base period")
    STOCH_RSI_K: int = Field(3, description="StochRSI %K smoothing period")
    STOCH_RSI_D: int = Field(3, description="StochRSI %D smoothing period")
    ROC_PERIOD: int = Field(12, description="Rate of Change period")

    # Volatility Indicator Parameters
    ATR_PERIOD: int = Field(14, description="ATR period (Wilder True Range smoothing)")
    BB_PERIOD: int = Field(20, description="Bollinger Bands SMA period")
    BB_STD: float = Field(2.0, description="Bollinger Bands standard deviation multiplier")

    # Volume Indicator Parameters
    VOLUME_SMA_PERIOD: int = Field(20, description="Volume simple moving average period")


default_indicator_config = IndicatorConfig()
