import pytest
from app.data.schema import Candle, CandleStateEnum
from app.indicators.engine import IndicatorEngine
from app.regime.models import MarketRegimeSnapshot, DirectionEnum, OverallRegimeEnum, VolatilityStateEnum
from app.structure.engine import MarketStructureEngine
from app.signals.evidence import EvidenceExtractor
from app.signals.config import default_signal_config


def create_sample_candles(count: int = 100, trend: str = "bullish"):
    candles = []
    base_price = 50000.0
    for i in range(count):
        if trend == "bullish":
            close = base_price + i * 50.0
        elif trend == "bearish":
            close = base_price - i * 50.0
        else:
            close = base_price + (10.0 if i % 2 == 0 else -10.0)
        c = Candle(
            timestamp=1700000000000 + i * 900000,
            open=close - 10.0,
            high=close + 20.0,
            low=close - 20.0,
            close=close,
            volume=100.0 + (i * 2.0 if trend == "bullish" else 0.0),
            close_time=1700000000000 + i * 900000 + 899999,
            is_closed=True,
            state=CandleStateEnum.CLOSED,
        )
        candles.append(c)
    return candles


def test_trend_evidence_normalization_and_caps():
    candles = create_sample_candles(100, trend="bullish")
    ind = IndicatorEngine.calculate_snapshot(candles, symbol="BTCUSDT", timeframe="15m", is_confirmed=True)
    trend_group = EvidenceExtractor.extract_trend_evidence(ind, candles, default_signal_config)

    assert -100.0 <= trend_group.score <= 100.0
    assert trend_group.state in ["BULLISH", "BEARISH", "NEUTRAL"]
    assert len(trend_group.components) == 4

    # Verify EMA structure sub-component cap (40.0)
    ema_comp = next(c for c in trend_group.components if c.name == "EMA_STRUCTURE")
    assert abs(ema_comp.contribution) <= 40.0


def test_rsi_context_aware_logic():
    candles = create_sample_candles(100, trend="bullish")
    ind = IndicatorEngine.calculate_snapshot(candles, symbol="BTCUSDT", timeframe="15m", is_confirmed=True)

    # Bullish regime with elevated RSI (>70)
    regime = MarketRegimeSnapshot(
        symbol="BTCUSDT",
        timeframe="15m",
        timestamp=candles[-1].timestamp,
        candle_state=CandleStateEnum.CLOSED,
        is_confirmed=True,
        direction=DirectionEnum.BULLISH,
        trend_strength="STRONG",
        volatility_state=VolatilityStateEnum.NORMAL,
        momentum_state="POSITIVE",
        volume_state="NORMAL",
        structure_state="BULLISH",
        overall_regime=OverallRegimeEnum.TRENDING_BULLISH,
        evidence_strength=85.0,
        evidence=[],
        contradictions=[],
    )

    mom_group = EvidenceExtractor.extract_momentum_evidence(ind, regime, default_signal_config)
    rsi_comp = next(c for c in mom_group.components if c.name == "RSI_MOMENTUM")

    # In a strong bullish regime, elevated RSI is positive momentum continuation (not short)
    assert rsi_comp.direction == "BULLISH"
    assert rsi_comp.contribution > 0


def test_volume_neutrality_without_structure():
    candles = create_sample_candles(100, trend="ranging")
    ind = IndicatorEngine.calculate_snapshot(candles, symbol="BTCUSDT", timeframe="15m", is_confirmed=True)
    struct = MarketStructureEngine.evaluate(candles, indicators=ind, is_confirmed=True)
    struct.structure_direction = "RANGE"

    vol_group = EvidenceExtractor.extract_volume_evidence(ind, struct, default_signal_config)
    rvol_comp = next(c for c in vol_group.components if c.name == "RELATIVE_VOLUME")

    # Without confirmed directional structure, volume does not fabricate direction
    assert rvol_comp.direction == "NEUTRAL"
    assert rvol_comp.contribution == 0.0
