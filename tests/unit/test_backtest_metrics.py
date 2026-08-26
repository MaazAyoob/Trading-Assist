import pytest
from app.backtesting.models import SignalOutcome, HorizonOutcome, OutcomeClassificationEnum
from app.backtesting.config import BacktestConfig
from app.backtesting.metrics import MetricsAggregator


def test_metrics_aggregation_directional_symmetry_and_breakdowns():
    # Construct synthetic signal outcomes
    signals = []
    t = 1700000000000

    # 10 Long Signals
    for i in range(10):
        signals.append(
            SignalOutcome(
                signal_id=f"sig_long_{i}",
                symbol="BTCUSDT",
                timeframe="15m",
                signal_timestamp=t + i * 900000,
                signal_direction="LONG_SETUP",
                signal_strength="STRONG" if i % 2 == 0 else "MODERATE",
                signal_score=55.0 + i,
                entry_reference_price=50000.0,
                outcomes={
                    1: HorizonOutcome(horizon=1, future_close=50500.0, forward_return=0.01, mfe=0.015, mae=-0.005, status=OutcomeClassificationEnum.POSITIVE_FORWARD_RETURN),
                    5: HorizonOutcome(horizon=5, future_close=51000.0, forward_return=0.02, mfe=0.03, mae=-0.01, status=OutcomeClassificationEnum.POSITIVE_FORWARD_RETURN),
                },
                regime_at_signal="TRENDING_BULLISH" if i < 6 else "RANGING",
                structure_at_signal="BULLISH",
                volatility_at_signal="NORMAL",
                engine_version="0.5.0",
                config_version="2026-08-24-v1",
            )
        )

    # 10 Short Signals
    for i in range(10):
        signals.append(
            SignalOutcome(
                signal_id=f"sig_short_{i}",
                symbol="BTCUSDT",
                timeframe="15m",
                signal_timestamp=t + (10 + i) * 900000,
                signal_direction="SHORT_SETUP",
                signal_strength="MODERATE",
                signal_score=-55.0 - i,
                entry_reference_price=50000.0,
                outcomes={
                    1: HorizonOutcome(horizon=1, future_close=49500.0, forward_return=0.01, mfe=0.02, mae=-0.005, status=OutcomeClassificationEnum.POSITIVE_FORWARD_RETURN),
                    5: HorizonOutcome(horizon=5, future_close=49000.0, forward_return=0.02, mfe=0.03, mae=-0.01, status=OutcomeClassificationEnum.POSITIVE_FORWARD_RETURN),
                },
                regime_at_signal="TRENDING_BEARISH" if i < 6 else "RANGING",
                structure_at_signal="BEARISH",
                volatility_at_signal="NORMAL",
                engine_version="0.5.0",
                config_version="2026-08-24-v1",
            )
        )

    config = BacktestConfig(symbol="BTCUSDT", timeframe="15m", horizons=[1, 5])
    start_ts = t
    end_ts = t + 20 * 900000

    metrics = MetricsAggregator.aggregate(
        signal_outcomes=signals,
        config=config,
        total_candles=100,
        start_timestamp=start_ts,
        end_timestamp=end_ts,
        wait_signal_count=5,
        neutral_signal_count=15,
    )

    assert metrics.total_signals == 20
    assert metrics.long_signals == 10
    assert metrics.short_signals == 10
    assert metrics.wait_signals == 5
    assert metrics.neutral_signals == 15
    assert metrics.signals_per_day > 0

    # Verify combined horizon metrics
    assert 1 in metrics.horizon_metrics
    assert 5 in metrics.horizon_metrics
    assert metrics.horizon_metrics[1].forward_return_stats.sample_count == 20
    assert metrics.horizon_metrics[1].forward_return_stats.mean == 0.01

    # Verify directional symmetry (Long vs Short)
    assert metrics.long_horizon_metrics[1].forward_return_stats.sample_count == 10
    assert metrics.short_horizon_metrics[1].forward_return_stats.sample_count == 10

    # Verify regime breakdowns
    assert "TRENDING_BULLISH" in metrics.regime_breakdown
    assert metrics.regime_breakdown["TRENDING_BULLISH"].sample_count == 6
    assert "RANGING" in metrics.regime_breakdown
    assert metrics.regime_breakdown["RANGING"].sample_count == 8

    # Verify strength breakdown
    assert "STRONG" in metrics.strength_breakdown
    assert "MODERATE" in metrics.strength_breakdown

    # Verify score breakdown
    assert "50 to 60" in metrics.score_breakdown
