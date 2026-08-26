import pytest
from app.data.binance import BinanceMarketDataProvider
from app.backtesting.engine import BacktestEngine
from app.backtesting.config import BacktestConfig


@pytest.mark.asyncio
async def test_live_binance_dataset_backtest():
    provider = BinanceMarketDataProvider()
    candles = await provider.get_historical_klines(symbol="BTCUSDT", timeframe="15m", limit=120)

    assert len(candles) >= 100
    config = BacktestConfig(symbol="BTCUSDT", timeframe="15m", warmup_bars=50, horizons=[1, 3, 5, 10, 20])

    run = BacktestEngine.run(candles, config=config)

    assert run.status == "COMPLETED"
    assert run.dataset_metadata.candle_count == len(candles)
    assert run.integrity_report.checks_passed is True
    assert run.integrity_report.future_leakage_detected is False

    print(
        f"\n[LIVE BACKTEST TEST] Symbol: {run.symbol} | Candles: {len(candles)} | Signals: {run.metrics.total_signals} | Run ID: {run.run_id}"
    )
