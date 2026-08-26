import pytest
import httpx
from app.data.binance import BinanceMarketDataProvider
from app.core.errors import SymbolNotFoundException


@pytest.mark.asyncio
async def test_binance_provider_mock_klines(monkeypatch):
    provider = BinanceMarketDataProvider()

    # Mock raw response from Binance klines
    fake_kline_data = [
        [1700000000000, "50000.0", "51000.0", "49500.0", "50500.0", "100.5", 1700000899999, "5050000.0", 300, "50.0", "2525000.0", "0"],
        [1700000900000, "50500.0", "52000.0", "50400.0", "51800.0", "150.2", 1700001799999, "7780000.0", 450, "80.0", "4144000.0", "0"],
    ]

    class MockResponse:
        status_code = 200
        text = "[]"
        def raise_for_status(self): pass
        def json(self): return fake_kline_data

    class MockClient:
        is_closed = False
        async def get(self, url, params=None):
            return MockResponse()
        async def aclose(self): pass

    async def mock_get_client(self):
        return MockClient()

    monkeypatch.setattr(provider, "_get_client", mock_get_client.__get__(provider))

    candles = await provider.get_historical_klines("BTCUSDT", "15m", limit=2)
    assert len(candles) == 2
    assert candles[0].open == 50000.0
    assert candles[0].close == 50500.0
    assert candles[1].close == 51800.0
    assert candles[0].is_closed is True


@pytest.mark.asyncio
async def test_binance_provider_invalid_symbol(monkeypatch):
    provider = BinanceMarketDataProvider()

    class Mock400Response:
        status_code = 400
        text = '{"code":-1121,"msg":"Invalid symbol."}'
        def raise_for_status(self):
            raise httpx.HTTPStatusError("Invalid symbol", request=None, response=self)

    class MockClient:
        is_closed = False
        async def get(self, url, params=None):
            return Mock400Response()
        async def aclose(self): pass

    async def mock_get_client(self):
        return MockClient()

    monkeypatch.setattr(provider, "_get_client", mock_get_client.__get__(provider))

    with pytest.raises(SymbolNotFoundException):
        await provider.get_ticker("INVALID_XYZ")
