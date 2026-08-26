import pytest
from app.data.schema import Candle, CandleStateEnum
from app.signals.models import ResearchSignal, SignalDirectionEnum, SignalStrengthEnum, SignalStatusEnum
from app.backtesting.outcomes import OutcomeCalculator
from app.backtesting.models import OutcomeClassificationEnum
from app.backtesting.config import CostModelConfig


def create_mock_candle(timestamp: int, close: float, high: float, low: float):
    return Candle(
        timestamp=timestamp,
        open=close,
        high=high,
        low=low,
        close=close,
        volume=100.0,
        close_time=timestamp + 899999,
        is_closed=True,
        state=CandleStateEnum.CLOSED,
    )


def test_long_forward_returns_and_excursions():
    # Base signal at index 0 (price = 100)
    # Candle 1: close = 102, high = 105, low = 99
    # Candle 2: close = 104, high = 106, low = 101
    # Candle 3: close = 98,  high = 104, low = 95
    candles = [
        create_mock_candle(1000, close=100.0, high=101.0, low=99.0),
        create_mock_candle(2000, close=102.0, high=105.0, low=99.0),
        create_mock_candle(3000, close=104.0, high=106.0, low=101.0),
        create_mock_candle(4000, close=98.0,  high=104.0, low=95.0),
    ]

    mock_signal = ResearchSignal(
        symbol="BTCUSDT",
        timeframe="15m",
        timestamp=1000,
        candle_state=CandleStateEnum.CLOSED,
        is_confirmed=True,
        is_historical=True,
        direction=SignalDirectionEnum.LONG_SETUP,
        strength=SignalStrengthEnum.STRONG,
        status=SignalStatusEnum.VALID,
        score=65.0,
        evidence_groups={},
        score_trace={
            "trend_score": 50, "momentum_score": 50, "structure_score": 50, "volume_score": 50,
            "base_directional_score": 50, "regime_modifier": 1.0, "volatility_modifier": 1.0,
            "context_adjusted_score": 50, "total_conflict_penalty": 0, "net_score": 50
        },
        conflicts=[],
        supporting_evidence=[],
        contradictions=[],
        data_quality_status="HEALTHY",
        disclaimer="Research signal",
        engine_version="0.5.0",
        config_version="2026-08-24-v1",
    )

    outcome = OutcomeCalculator.evaluate_signal_outcomes(
        signal=mock_signal,
        signal_candle_idx=0,
        all_candles=candles,
        horizons=[1, 2, 3],
    )

    # 1C Horizon (Candle 1): close = 102 -> +2.0%, max high = 105 -> +5.0%, min low = 99 -> -1.0%
    out_1 = outcome.outcomes[1]
    assert out_1.forward_return == 0.02
    assert out_1.mfe == 0.05
    assert out_1.mae == -0.01
    assert out_1.status == OutcomeClassificationEnum.POSITIVE_FORWARD_RETURN

    # 2C Horizon (Candles 1-2): close = 104 -> +4.0%, max high = 106 -> +6.0%, min low = 99 -> -1.0%
    out_2 = outcome.outcomes[2]
    assert out_2.forward_return == 0.04
    assert out_2.mfe == 0.06
    assert out_2.mae == -0.01

    # 3C Horizon (Candles 1-3): close = 98 -> -2.0%, max high = 106 -> +6.0%, min low = 95 -> -5.0%
    out_3 = outcome.outcomes[3]
    assert out_3.forward_return == -0.02
    assert out_3.mfe == 0.06
    assert out_3.mae == -0.05
    assert out_3.status == OutcomeClassificationEnum.NEGATIVE_FORWARD_RETURN


def test_short_forward_returns_and_excursions():
    # Base signal at index 0 (price = 100)
    # Candle 1: close = 98, high = 101, low = 96
    # Candle 2: close = 95, high = 99,  low = 92
    candles = [
        create_mock_candle(1000, close=100.0, high=101.0, low=99.0),
        create_mock_candle(2000, close=98.0,  high=101.0, low=96.0),
        create_mock_candle(3000, close=95.0,  high=99.0,  low=92.0),
    ]

    mock_signal = ResearchSignal(
        symbol="BTCUSDT",
        timeframe="15m",
        timestamp=1000,
        candle_state=CandleStateEnum.CLOSED,
        is_confirmed=True,
        is_historical=True,
        direction=SignalDirectionEnum.SHORT_SETUP,
        strength=SignalStrengthEnum.STRONG,
        status=SignalStatusEnum.VALID,
        score=-65.0,
        evidence_groups={},
        score_trace={
            "trend_score": -50, "momentum_score": -50, "structure_score": -50, "volume_score": -50,
            "base_directional_score": -50, "regime_modifier": 1.0, "volatility_modifier": 1.0,
            "context_adjusted_score": -50, "total_conflict_penalty": 0, "net_score": -50
        },
        conflicts=[],
        supporting_evidence=[],
        contradictions=[],
        data_quality_status="HEALTHY",
        disclaimer="Research signal",
        engine_version="0.5.0",
        config_version="2026-08-24-v1",
    )

    outcome = OutcomeCalculator.evaluate_signal_outcomes(
        signal=mock_signal,
        signal_candle_idx=0,
        all_candles=candles,
        horizons=[1, 2],
    )

    # 1C Horizon for SHORT: close dropped from 100 to 98 -> return = +2.0%
    # MFE = (100 - min_low: 96) / 100 = +4.0%
    # MAE = (100 - max_high: 101) / 100 = -1.0%
    out_1 = outcome.outcomes[1]
    assert out_1.forward_return == 0.02
    assert out_1.mfe == 0.04
    assert out_1.mae == -0.01
    assert out_1.status == OutcomeClassificationEnum.POSITIVE_FORWARD_RETURN

    # 2C Horizon for SHORT: close dropped from 100 to 95 -> return = +5.0%
    # MFE = (100 - min_low: 92) / 100 = +8.0%
    # MAE = (100 - max_high: 101) / 100 = -1.0%
    out_2 = outcome.outcomes[2]
    assert out_2.forward_return == 0.05
    assert out_2.mfe == 0.08
    assert out_2.mae == -0.01


def test_incomplete_horizon_at_end_of_dataset():
    candles = [
        create_mock_candle(1000, close=100.0, high=101.0, low=99.0),
        create_mock_candle(2000, close=102.0, high=103.0, low=101.0),
    ]

    mock_signal = ResearchSignal(
        symbol="BTCUSDT",
        timeframe="15m",
        timestamp=1000,
        candle_state=CandleStateEnum.CLOSED,
        is_confirmed=True,
        is_historical=True,
        direction=SignalDirectionEnum.LONG_SETUP,
        strength=SignalStrengthEnum.MODERATE,
        status=SignalStatusEnum.VALID,
        score=50.0,
        evidence_groups={},
        score_trace={
            "trend_score": 50, "momentum_score": 50, "structure_score": 50, "volume_score": 50,
            "base_directional_score": 50, "regime_modifier": 1.0, "volatility_modifier": 1.0,
            "context_adjusted_score": 50, "total_conflict_penalty": 0, "net_score": 50
        },
        conflicts=[],
        supporting_evidence=[],
        contradictions=[],
        data_quality_status="HEALTHY",
        disclaimer="Research signal",
        engine_version="0.5.0",
        config_version="2026-08-24-v1",
    )

    outcome = OutcomeCalculator.evaluate_signal_outcomes(
        signal=mock_signal,
        signal_candle_idx=0,
        all_candles=candles,
        horizons=[1, 5, 20],
    )

    assert outcome.outcomes[1].status == OutcomeClassificationEnum.POSITIVE_FORWARD_RETURN
    assert outcome.outcomes[5].status == OutcomeClassificationEnum.INSUFFICIENT_HORIZON
    assert outcome.outcomes[5].forward_return is None
    assert outcome.outcomes[20].status == OutcomeClassificationEnum.INSUFFICIENT_HORIZON


def test_optional_cost_model_adjustment():
    candles = [
        create_mock_candle(1000, close=100.0, high=101.0, low=99.0),
        create_mock_candle(2000, close=102.0, high=103.0, low=101.0),
    ]

    mock_signal = ResearchSignal(
        symbol="BTCUSDT",
        timeframe="15m",
        timestamp=1000,
        candle_state=CandleStateEnum.CLOSED,
        is_confirmed=True,
        is_historical=True,
        direction=SignalDirectionEnum.LONG_SETUP,
        strength=SignalStrengthEnum.MODERATE,
        status=SignalStatusEnum.VALID,
        score=50.0,
        evidence_groups={},
        score_trace={
            "trend_score": 50, "momentum_score": 50, "structure_score": 50, "volume_score": 50,
            "base_directional_score": 50, "regime_modifier": 1.0, "volatility_modifier": 1.0,
            "context_adjusted_score": 50, "total_conflict_penalty": 0, "net_score": 50
        },
        conflicts=[],
        supporting_evidence=[],
        contradictions=[],
        data_quality_status="HEALTHY",
        disclaimer="Research signal",
        engine_version="0.5.0",
        config_version="2026-08-24-v1",
    )

    cost_cfg = CostModelConfig(enabled=True, fee_bps=10.0, slippage_bps=5.0, is_round_trip=True)
    # Total round trip = 2 * (10 + 5) / 10000 = 0.0030 (0.30%)

    outcome = OutcomeCalculator.evaluate_signal_outcomes(
        signal=mock_signal,
        signal_candle_idx=0,
        all_candles=candles,
        horizons=[1],
        cost_model=cost_cfg,
    )

    out_1 = outcome.outcomes[1]
    assert out_1.forward_return == 0.02
    assert out_1.estimated_net_forward_return == 0.017  # 0.02 - 0.003
