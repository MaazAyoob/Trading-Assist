import pytest
import numpy as np
from app.data.schema import Candle, CandleStateEnum, QualityStatusEnum
from app.indicators.base import (
    IndicatorSnapshot,
    TrendIndicators,
    MomentumIndicators,
    VolatilityIndicators,
    VolumeIndicators,
)
from app.regime.config import RegimeConfig
from app.regime.models import (
    DirectionEnum,
    TrendStrengthEnum,
    VolatilityStateEnum,
    MomentumStateEnum,
    VolumeStateEnum,
    StructureStateEnum,
    OverallRegimeEnum,
)
from app.regime.engine import MarketRegimeEngine


def create_mock_candle(ts: int, close: float, volume: float = 100.0) -> Candle:
    return Candle(
        timestamp=ts,
        open=close - 10.0,
        high=close + 20.0,
        low=close - 20.0,
        close=close,
        volume=volume,
        is_closed=True,
        state=CandleStateEnum.CLOSED,
    )


def test_regime_bullish_classification():
    candles = [create_mock_candle(1700000000000 + i * 60000, 60000.0 + i * 50) for i in range(100)]
    snap = IndicatorSnapshot(
        symbol="BTCUSDT",
        timeframe="15m",
        timestamp=1700000000000,
        is_confirmed=True,
        quality_status=QualityStatusEnum.HEALTHY,
        indicator_engine_version="0.3.0",
        indicator_config_version="2026-08-24-v1",
        trend=TrendIndicators(
            ema_9=65000.0,
            ema_21=64000.0,
            ema_50=63000.0,
            ema_100=62000.0,
            ema_200=61000.0,
            vwap=63500.0,
            adx=38.0,
            plus_di=32.0,
            minus_di=14.0,
            supertrend=63800.0,
            supertrend_direction=1,
        ),
        momentum=MomentumIndicators(
            rsi=62.0,
            macd=250.0,
            macd_signal=180.0,
            macd_histogram=70.0,
            stoch_rsi_k=75.0,
            stoch_rsi_d=70.0,
            roc=2.5,
        ),
        volatility=VolatilityIndicators(
            atr=500.0,
            bb_upper=66000.0,
            bb_middle=64500.0,
            bb_lower=63000.0,
            bb_bandwidth=4.6,
            bb_percent_b=0.75,
        ),
        volume=VolumeIndicators(
            volume_sma=100.0,
            relative_volume=1.6,
            obv=5000.0,
        ),
    )

    regime = MarketRegimeEngine.classify(
        candles=candles,
        indicators=snap,
        structure_state=StructureStateEnum.BULLISH,
        is_confirmed=True,
    )

    assert regime.direction == DirectionEnum.BULLISH
    assert regime.trend_strength == TrendStrengthEnum.STRONG
    assert regime.momentum_state == MomentumStateEnum.POSITIVE
    assert regime.volume_state == VolumeStateEnum.ABOVE_AVERAGE
    assert regime.overall_regime == OverallRegimeEnum.TRENDING_BULLISH
    assert regime.evidence_strength > 75.0
    assert len(regime.evidence) > 0


def test_regime_bearish_classification():
    candles = [create_mock_candle(1700000000000 + i * 60000, 60000.0 - i * 50) for i in range(100)]
    snap = IndicatorSnapshot(
        symbol="BTCUSDT",
        timeframe="15m",
        timestamp=1700000000000,
        is_confirmed=True,
        quality_status=QualityStatusEnum.HEALTHY,
        indicator_engine_version="0.3.0",
        indicator_config_version="2026-08-24-v1",
        trend=TrendIndicators(
            ema_9=55000.0,
            ema_21=56000.0,
            ema_50=57000.0,
            ema_100=58000.0,
            ema_200=59000.0,
            vwap=56500.0,
            adx=42.0,
            plus_di=12.0,
            minus_di=35.0,
            supertrend=57500.0,
            supertrend_direction=-1,
        ),
        momentum=MomentumIndicators(
            rsi=38.0,
            macd=-300.0,
            macd_signal=-200.0,
            macd_histogram=-100.0,
            stoch_rsi_k=25.0,
            stoch_rsi_d=30.0,
            roc=-3.2,
        ),
        volatility=VolatilityIndicators(
            atr=600.0,
            bb_upper=58000.0,
            bb_middle=56000.0,
            bb_lower=54000.0,
            bb_bandwidth=7.1,
            bb_percent_b=0.25,
        ),
        volume=VolumeIndicators(
            volume_sma=100.0,
            relative_volume=1.9,
            obv=-8000.0,
        ),
    )

    regime = MarketRegimeEngine.classify(
        candles=candles,
        indicators=snap,
        structure_state=StructureStateEnum.BEARISH,
        is_confirmed=True,
    )

    assert regime.direction == DirectionEnum.BEARISH
    assert regime.trend_strength == TrendStrengthEnum.STRONG
    assert regime.momentum_state == MomentumStateEnum.NEGATIVE
    assert regime.overall_regime == OverallRegimeEnum.TRENDING_BEARISH


def test_regime_ranging_and_low_adx():
    candles = [create_mock_candle(1700000000000 + i * 60000, 50000.0) for i in range(100)]
    snap = IndicatorSnapshot(
        symbol="BTCUSDT",
        timeframe="15m",
        timestamp=1700000000000,
        is_confirmed=True,
        quality_status=QualityStatusEnum.HEALTHY,
        indicator_engine_version="0.3.0",
        indicator_config_version="2026-08-24-v1",
        trend=TrendIndicators(
            ema_9=50005.0,
            ema_21=50002.0,
            ema_50=49998.0,
            vwap=50000.0,
            adx=14.0,  # Weak ADX
            plus_di=20.0,
            minus_di=19.0,
            supertrend=49900.0,
            supertrend_direction=1,
        ),
        momentum=MomentumIndicators(
            rsi=50.5,
            macd=5.0,
            macd_signal=4.0,
            macd_histogram=1.0,
            roc=0.05,
        ),
        volatility=VolatilityIndicators(
            atr=100.0,
            bb_upper=50200.0,
            bb_middle=50000.0,
            bb_lower=49800.0,
            bb_bandwidth=0.8,
        ),
        volume=VolumeIndicators(
            volume_sma=100.0,
            relative_volume=0.8,
            obv=100.0,
        ),
    )

    regime = MarketRegimeEngine.classify(
        candles=candles,
        indicators=snap,
        structure_state=StructureStateEnum.RANGE,
        is_confirmed=True,
    )

    assert regime.direction == DirectionEnum.RANGE
    assert regime.trend_strength == TrendStrengthEnum.NONE
    assert regime.overall_regime in [OverallRegimeEnum.RANGING, OverallRegimeEnum.LOW_VOLATILITY]
