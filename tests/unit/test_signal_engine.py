import pytest
from app.data.schema import Candle, CandleStateEnum, MarketDataQuality, QualityStatusEnum
from app.indicators.engine import IndicatorEngine
from app.regime.engine import MarketRegimeEngine
from app.structure.engine import MarketStructureEngine
from app.signals.engine import MultiFactorSignalEngine
from app.signals.models import SignalDirectionEnum, SignalStatusEnum, SignalStrengthEnum


def create_clear_bullish_swings(num_cycles: int = 15):
    """
    Creates a realistic bullish trending sequence with distinct pullbacks,
    Higher Highs, Higher Lows, rising volume, and confirmed Bullish BOS breaks.
    """
    candles = []
    base_price = 50000.0
    t = 1700000000000

    for k in range(num_cycles):
        peak_base = base_price + k * 250.0
        # Rising to Higher High
        for j in range(5):
            close = peak_base + j * 50.0
            spread = close * 0.002
            candles.append(
                Candle(
                    timestamp=t,
                    open=close - spread * 0.5,
                    high=close + spread,
                    low=close - spread,
                    close=close,
                    volume=200.0 + k * 10.0 + j * 20.0,
                    close_time=t + 899999,
                    is_closed=True,
                    state=CandleStateEnum.CLOSED,
                )
            )
            t += 900000
        # Pullback to Higher Low (omit on final cycle so it ends on impulse expansion)
        if k < num_cycles - 1:
            top_close = candles[-1].close
            for j in range(1, 5):
                close = top_close - j * 30.0
                spread = close * 0.002
                candles.append(
                    Candle(
                        timestamp=t,
                        open=close + spread * 0.5,
                        high=close + spread,
                        low=close - spread,
                        close=close,
                        volume=80.0,
                        close_time=t + 899999,
                        is_closed=True,
                        state=CandleStateEnum.CLOSED,
                    )
                )
                t += 900000
    return candles


def create_clear_bearish_swings(num_cycles: int = 15):
    """
    Creates a realistic bearish trending sequence with distinct pullbacks,
    Lower Highs, Lower Lows, distribution volume, and confirmed Bearish BOS breaks.
    """
    candles = []
    base_price = 70000.0
    t = 1700000000000

    for k in range(num_cycles):
        valley_base = base_price - k * 250.0
        # Falling to Lower Low
        for j in range(5):
            close = valley_base - j * 50.0
            spread = close * 0.002
            candles.append(
                Candle(
                    timestamp=t,
                    open=close + spread * 0.5,
                    high=close + spread,
                    low=close - spread,
                    close=close,
                    volume=200.0 + k * 10.0 + j * 20.0,
                    close_time=t + 899999,
                    is_closed=True,
                    state=CandleStateEnum.CLOSED,
                )
            )
            t += 900000
        # Pullback to Lower High (omit on final cycle so it ends on impulse down)
        if k < num_cycles - 1:
            bottom_close = candles[-1].close
            for j in range(1, 5):
                close = bottom_close + j * 30.0
                spread = close * 0.002
                candles.append(
                    Candle(
                        timestamp=t,
                        open=close - spread * 0.5,
                        high=close + spread,
                        low=close - spread,
                        close=close,
                        volume=80.0,
                        close_time=t + 899999,
                        is_closed=True,
                        state=CandleStateEnum.CLOSED,
                    )
                )
                t += 900000
    return candles


def test_strong_bullish_signal_classification():
    candles = create_clear_bullish_swings(15)
    ind = IndicatorEngine.calculate_snapshot(candles, symbol="BTCUSDT", timeframe="15m", is_confirmed=True)
    struct = MarketStructureEngine.evaluate(candles, indicators=ind, is_confirmed=True)
    regime = MarketRegimeEngine.classify(candles=candles, indicators=ind, structure_state=struct.structure_direction, is_confirmed=True)

    signal = MultiFactorSignalEngine.calculate_signal(
        candles=candles,
        indicators=ind,
        regime=regime,
        structure=struct,
        is_confirmed=True,
    )

    assert signal.direction == SignalDirectionEnum.LONG_SETUP
    assert signal.status == SignalStatusEnum.VALID
    assert signal.score >= 45.0
    assert signal.strength in [SignalStrengthEnum.STRONG, SignalStrengthEnum.VERY_STRONG, SignalStrengthEnum.MODERATE]
    assert len(signal.supporting_evidence) > 0
    assert "Research signal" in signal.disclaimer


def test_strong_bearish_signal_classification():
    candles = create_clear_bearish_swings(15)
    ind = IndicatorEngine.calculate_snapshot(candles, symbol="BTCUSDT", timeframe="15m", is_confirmed=True)
    struct = MarketStructureEngine.evaluate(candles, indicators=ind, is_confirmed=True)
    regime = MarketRegimeEngine.classify(candles=candles, indicators=ind, structure_state=struct.structure_direction, is_confirmed=True)

    signal = MultiFactorSignalEngine.calculate_signal(
        candles=candles,
        indicators=ind,
        regime=regime,
        structure=struct,
        is_confirmed=True,
    )

    assert signal.direction == SignalDirectionEnum.SHORT_SETUP
    assert signal.status == SignalStatusEnum.VALID
    assert signal.score <= -45.0
    assert signal.strength in [SignalStrengthEnum.STRONG, SignalStrengthEnum.VERY_STRONG, SignalStrengthEnum.MODERATE]


def test_invalid_data_produces_invalid_status():
    candles = create_clear_bullish_swings(15)
    ind = IndicatorEngine.calculate_snapshot(candles, symbol="BTCUSDT", timeframe="15m", is_confirmed=True)
    struct = MarketStructureEngine.evaluate(candles, indicators=ind, is_confirmed=True)
    regime = MarketRegimeEngine.classify(candles=candles, indicators=ind, structure_state=struct.structure_direction, is_confirmed=True)

    invalid_quality = MarketDataQuality(
        symbol="BTCUSDT",
        timeframe="15m",
        status=QualityStatusEnum.INVALID,
        total_candles=150,
        valid_candles=0,
        gap_count=10,
        duplicate_count=0,
        out_of_order_count=0,
        is_stale=True,
        details=["Corrupted stream"],
    )

    signal = MultiFactorSignalEngine.calculate_signal(
        candles=candles,
        indicators=ind,
        regime=regime,
        structure=struct,
        quality=invalid_quality,
        is_confirmed=True,
    )

    assert signal.status == SignalStatusEnum.INVALID_DATA
    assert signal.direction == SignalDirectionEnum.NEUTRAL
