import math
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from app.data.schema import QualityStatusEnum


def safe_float(val: Any) -> Optional[float]:
    """
    Sanitize float values.
    Converts NaN, Infinity, -Infinity, None, or unparseable values to None.
    Never emits NaN or Infinity into JSON responses.
    """
    if val is None:
        return None
    try:
        f = float(val)
        if math.isnan(f) or math.isinf(f):
            return None
        return round(f, 6)
    except (ValueError, TypeError):
        return None


class TrendIndicators(BaseModel):
    ema_9: Optional[float] = Field(None, description="9-period EMA")
    ema_21: Optional[float] = Field(None, description="21-period EMA")
    ema_50: Optional[float] = Field(None, description="50-period EMA")
    ema_100: Optional[float] = Field(None, description="100-period EMA")
    ema_200: Optional[float] = Field(None, description="200-period EMA")
    vwap: Optional[float] = Field(None, description="24h Rolling Volume Weighted Average Price")
    adx: Optional[float] = Field(None, description="Average Directional Index")
    plus_di: Optional[float] = Field(None, description="Positive Directional Indicator (+DI)")
    minus_di: Optional[float] = Field(None, description="Negative Directional Indicator (-DI)")
    supertrend: Optional[float] = Field(None, description="Supertrend boundary level")
    supertrend_direction: Optional[int] = Field(None, description="Supertrend direction (+1 for Bullish, -1 for Bearish)")


class MomentumIndicators(BaseModel):
    rsi: Optional[float] = Field(None, description="14-period RSI (Wilder)")
    macd: Optional[float] = Field(None, description="MACD line (12, 26)")
    macd_signal: Optional[float] = Field(None, description="MACD signal line (9 EMA)")
    macd_histogram: Optional[float] = Field(None, description="MACD histogram (MACD - Signal)")
    stoch_rsi_k: Optional[float] = Field(None, description="Stochastic RSI %K line")
    stoch_rsi_d: Optional[float] = Field(None, description="Stochastic RSI %D line")
    roc: Optional[float] = Field(None, description="Rate of Change (12-period %)")


class VolatilityIndicators(BaseModel):
    atr: Optional[float] = Field(None, description="Average True Range (14-period Wilder)")
    bb_upper: Optional[float] = Field(None, description="Bollinger Upper Band (20, 2.0 std)")
    bb_middle: Optional[float] = Field(None, description="Bollinger Middle SMA (20)")
    bb_lower: Optional[float] = Field(None, description="Bollinger Lower Band (20, 2.0 std)")
    bb_bandwidth: Optional[float] = Field(None, description="Bollinger Bandwidth %: (Upper - Lower) / Middle * 100")
    bb_percent_b: Optional[float] = Field(None, description="Bollinger %B: (Close - Lower) / (Upper - Lower)")


class VolumeIndicators(BaseModel):
    volume_sma: Optional[float] = Field(None, description="20-period Volume Simple Moving Average")
    relative_volume: Optional[float] = Field(None, description="Relative Volume ratio (Current / Volume SMA)")
    obv: Optional[float] = Field(None, description="On-Balance Volume cumulative metric")


class IndicatorSnapshot(BaseModel):
    """
    Standardized, self-contained indicator measurement snapshot for a specific symbol, timeframe, and timestamp.
    """

    symbol: str
    timeframe: str
    timestamp: int
    is_confirmed: bool = Field(True, description="True if calculated exclusively from CLOSED historical candles")
    quality_status: QualityStatusEnum = Field(QualityStatusEnum.HEALTHY)
    indicator_engine_version: str = Field("0.3.0")
    indicator_config_version: str = Field("2026-08-24-v1")

    trend: TrendIndicators
    momentum: MomentumIndicators
    volatility: VolatilityIndicators
    volume: VolumeIndicators


class IndicatorHistoryPoint(BaseModel):
    """A single historical timestamp's calculated indicator readings for chart overlays."""
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    is_closed: bool

    # Trend
    ema_9: Optional[float] = None
    ema_21: Optional[float] = None
    ema_50: Optional[float] = None
    ema_200: Optional[float] = None
    vwap: Optional[float] = None
    supertrend: Optional[float] = None
    supertrend_direction: Optional[int] = None

    # Volatility
    bb_upper: Optional[float] = None
    bb_middle: Optional[float] = None
    bb_lower: Optional[float] = None

    # Momentum
    rsi: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_histogram: Optional[float] = None
