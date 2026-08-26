import pytest
from app.data.schema import Candle, CandleStateEnum
from app.indicators.engine import IndicatorEngine
from app.regime.engine import MarketRegimeEngine
from app.structure.engine import MarketStructureEngine
from app.signals.engine import MultiFactorSignalEngine


def create_candles(count: int = 150):
    candles = []
    base_price = 50000.0
    for i in range(count):
        close = base_price + i * 30.0
        c = Candle(
            timestamp=1700000000000 + i * 900000,
            open=close - 10.0,
            high=close + 20.0,
            low=close - 20.0,
            close=close,
            volume=120.0,
            close_time=1700000000000 + i * 900000 + 899999,
            is_closed=True,
            state=CandleStateEnum.CLOSED,
        )
        candles.append(c)
    return candles


def test_signal_determinism():
    candles = create_candles(150)
    ind1 = IndicatorEngine.calculate_snapshot(candles, symbol="BTCUSDT", timeframe="15m", is_confirmed=True)
    struct1 = MarketStructureEngine.evaluate(candles, indicators=ind1, is_confirmed=True)
    regime1 = MarketRegimeEngine.classify(candles=candles, indicators=ind1, structure_state=struct1.structure_direction, is_confirmed=True)
    sig1 = MultiFactorSignalEngine.calculate_signal(candles, ind1, regime1, struct1, is_confirmed=True)

    ind2 = IndicatorEngine.calculate_snapshot(candles, symbol="BTCUSDT", timeframe="15m", is_confirmed=True)
    struct2 = MarketStructureEngine.evaluate(candles, indicators=ind2, is_confirmed=True)
    regime2 = MarketRegimeEngine.classify(candles=candles, indicators=ind2, structure_state=struct2.structure_direction, is_confirmed=True)
    sig2 = MultiFactorSignalEngine.calculate_signal(candles, ind2, regime2, struct2, is_confirmed=True)

    assert sig1.model_dump() == sig2.model_dump()


def test_signal_non_repainting():
    candles_base = create_candles(150)
    ind_base = IndicatorEngine.calculate_snapshot(candles_base, symbol="BTCUSDT", timeframe="15m", is_confirmed=True)
    struct_base = MarketStructureEngine.evaluate(candles_base, indicators=ind_base, is_confirmed=True)
    regime_base = MarketRegimeEngine.classify(candles=candles_base, indicators=ind_base, structure_state=struct_base.structure_direction, is_confirmed=True)
    sig_at_150 = MultiFactorSignalEngine.calculate_signal(candles_base, ind_base, regime_base, struct_base, is_confirmed=True)

    # Append 5 new future candles
    extended_candles = list(candles_base)
    for j in range(5):
        close = extended_candles[-1].close - 100.0  # Sharp reversal in future bars
        c = Candle(
            timestamp=extended_candles[-1].timestamp + 900000,
            open=close + 10.0,
            high=close + 20.0,
            low=close - 20.0,
            close=close,
            volume=200.0,
            close_time=extended_candles[-1].timestamp + 900000 + 899999,
            is_closed=True,
            state=CandleStateEnum.CLOSED,
        )
        extended_candles.append(c)

    # Re-evaluate snapshot strictly at candle 150
    ind_recalc = IndicatorEngine.calculate_snapshot(extended_candles[:150], symbol="BTCUSDT", timeframe="15m", is_confirmed=True)
    struct_recalc = MarketStructureEngine.evaluate(extended_candles[:150], indicators=ind_recalc, is_confirmed=True)
    regime_recalc = MarketRegimeEngine.classify(candles=extended_candles[:150], indicators=ind_recalc, structure_state=struct_recalc.structure_direction, is_confirmed=True)
    sig_recalc = MultiFactorSignalEngine.calculate_signal(extended_candles[:150], ind_recalc, regime_recalc, struct_recalc, is_confirmed=True)

    assert sig_at_150.direction == sig_recalc.direction
    assert sig_at_150.score == sig_recalc.score
    assert sig_at_150.score_trace.model_dump() == sig_recalc.score_trace.model_dump()


def test_score_trace_reconstruction():
    candles = create_candles(150)
    ind = IndicatorEngine.calculate_snapshot(candles, symbol="BTCUSDT", timeframe="15m", is_confirmed=True)
    struct = MarketStructureEngine.evaluate(candles, indicators=ind, is_confirmed=True)
    regime = MarketRegimeEngine.classify(candles=candles, indicators=ind, structure_state=struct.structure_direction, is_confirmed=True)
    signal = MultiFactorSignalEngine.calculate_signal(candles, ind, regime, struct, is_confirmed=True)

    trace = signal.score_trace
    # Verify exact mathematical trace conservation
    reconstructed_base = (
        trace.trend_score * 0.30
        + trace.momentum_score * 0.20
        + trace.structure_score * 0.35
        + trace.volume_score * 0.15
    )
    assert abs(reconstructed_base - trace.base_directional_score) <= 0.5
    reconstructed_adj = trace.base_directional_score * trace.regime_modifier * trace.volatility_modifier
    assert abs(reconstructed_adj - trace.context_adjusted_score) <= 0.5
