import pytest
from app.data.binance import BinanceMarketDataProvider


@pytest.mark.asyncio
async def test_live_binance_ping():
    provider = BinanceMarketDataProvider()
    try:
        is_alive = await provider.ping()
        assert is_alive is True, "Binance public ping should return True"
    finally:
        await provider.close()


@pytest.mark.asyncio
async def test_live_binance_get_btc_klines():
    provider = BinanceMarketDataProvider()
    try:
        candles = await provider.get_historical_klines("BTCUSDT", "15m", limit=10)
        assert len(candles) == 10
        assert candles[0].close > 0
        assert candles[0].timestamp < candles[-1].timestamp
        print(f"\n[LIVE TEST] Successfully fetched {len(candles)} BTC/USDT 15m candles. Latest Close: ${candles[-1].close:,.2f}")
    finally:
        await provider.close()


@pytest.mark.asyncio
async def test_live_binance_get_btc_ticker():
    provider = BinanceMarketDataProvider()
    try:
        ticker = await provider.get_ticker("BTCUSDT")
        assert ticker.symbol == "BTCUSDT"
        assert ticker.price > 0
        print(f"\n[LIVE TEST] Successfully fetched live BTC/USDT Ticker: ${ticker.price:,.2f} ({ticker.price_change_percent:+.2f}%)")
    finally:
        await provider.close()
