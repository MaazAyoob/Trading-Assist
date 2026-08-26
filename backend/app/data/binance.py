import time
from typing import List, Optional
import httpx
from app.core.config import settings
from app.core.logging import logger
from app.core.errors import MarketDataException, SymbolNotFoundException
from app.data.base import MarketDataProvider
from app.data.schema import Candle, Ticker, OrderBook, OrderBookLevel, RecentTrade


class BinanceMarketDataProvider(MarketDataProvider):
    """
    Binance public market data provider implementation.
    Fetches real-time and historical spot data for BTC/USDT and other crypto pairs.
    """

    def __init__(self, base_url: Optional[str] = None):
        self._base_url = base_url or settings.BINANCE_REST_BASE_URL
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def provider_name(self) -> str:
        return "binance"

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                timeout=httpx.Timeout(10.0, connect=5.0),
                headers={"User-Agent": "CryptoAITradingPlatform/1.0"},
            )
        return self._client

    async def ping(self) -> bool:
        try:
            client = await self._get_client()
            res = await client.get("/api/v3/ping")
            return res.status_code == 200
        except Exception as e:
            logger.warning(f"Binance ping failed: {e}")
            return False

    async def get_historical_klines(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 500,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
    ) -> List[Candle]:
        """
        Fetch historical Kline/Candlestick data from Binance.
        Binance Kline array format:
        [
          0: Open time,
          1: Open,
          2: High,
          3: Low,
          4: Close,
          5: Volume,
          6: Close time,
          7: Quote asset volume,
          8: Number of trades,
          9: Taker buy base asset volume,
          10: Taker buy quote asset volume,
          11: Ignore
        ]
        """
        client = await self._get_client()
        params = {
            "symbol": symbol.upper(),
            "interval": timeframe,
            "limit": min(limit, 1000),
        }
        if start_time is not None:
            params["startTime"] = start_time
        if end_time is not None:
            params["endTime"] = end_time

        try:
            response = await client.get("/api/v3/klines", params=params)
            if response.status_code == 400 and "Invalid symbol" in response.text:
                raise SymbolNotFoundException(symbol)
            response.raise_for_status()
            raw_klines = response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch Binance klines for {symbol} {timeframe}: {e}")
            raise MarketDataException(f"Binance API error fetching historical klines: {str(e)}")

        candles: List[Candle] = []
        for row in raw_klines:
            try:
                candles.append(
                    Candle(
                        timestamp=int(row[0]),
                        open=float(row[1]),
                        high=float(row[2]),
                        low=float(row[3]),
                        close=float(row[4]),
                        volume=float(row[5]),
                        close_time=int(row[6]),
                        quote_volume=float(row[7]),
                        trades_count=int(row[8]),
                        is_closed=True,
                    )
                )
            except (ValueError, IndexError) as parse_err:
                logger.warning(f"Skipping malformed kline row {row}: {parse_err}")
                continue

        return candles

    async def get_ticker(self, symbol: str) -> Ticker:
        client = await self._get_client()
        try:
            response = await client.get("/api/v3/ticker/24hr", params={"symbol": symbol.upper()})
            if response.status_code == 400 and "Invalid symbol" in response.text:
                raise SymbolNotFoundException(symbol)
            response.raise_for_status()
            data = response.json()

            return Ticker(
                symbol=data["symbol"],
                price=float(data["lastPrice"]),
                price_change=float(data["priceChange"]),
                price_change_percent=float(data["priceChangePercent"]),
                high_24h=float(data["highPrice"]),
                low_24h=float(data["lowPrice"]),
                volume_24h=float(data["volume"]),
                quote_volume_24h=float(data["quoteVolume"]),
                timestamp=int(data.get("closeTime", time.time() * 1000)),
            )
        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch Binance ticker for {symbol}: {e}")
            raise MarketDataException(f"Binance API error fetching 24hr ticker: {str(e)}")

    async def get_order_book(self, symbol: str, limit: int = 20) -> OrderBook:
        client = await self._get_client()
        try:
            response = await client.get(
                "/api/v3/depth", params={"symbol": symbol.upper(), "limit": limit}
            )
            response.raise_for_status()
            data = response.json()

            bids = [OrderBookLevel(price=float(b[0]), quantity=float(b[1])) for b in data["bids"]]
            asks = [OrderBookLevel(price=float(a[0]), quantity=float(a[1])) for a in data["asks"]]

            return OrderBook(
                symbol=symbol.upper(),
                last_update_id=data["lastUpdateId"],
                bids=bids,
                asks=asks,
                timestamp=int(time.time() * 1000),
            )
        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch Binance order book for {symbol}: {e}")
            raise MarketDataException(f"Binance API error fetching order book: {str(e)}")

    async def get_recent_trades(self, symbol: str, limit: int = 50) -> List[RecentTrade]:
        client = await self._get_client()
        try:
            response = await client.get(
                "/api/v3/trades", params={"symbol": symbol.upper(), "limit": limit}
            )
            response.raise_for_status()
            data = response.json()

            return [
                RecentTrade(
                    id=trade["id"],
                    price=float(trade["price"]),
                    qty=float(trade["qty"]),
                    time=trade["time"],
                    is_buyer_maker=trade["isBuyerMaker"],
                )
                for trade in data
            ]
        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch Binance recent trades for {symbol}: {e}")
            raise MarketDataException(f"Binance API error fetching trades: {str(e)}")

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            logger.info("Closed BinanceMarketDataProvider HTTP client.")
