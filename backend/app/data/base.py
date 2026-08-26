from abc import ABC, abstractmethod
from typing import Callable, Awaitable, List, Optional
from app.data.schema import Candle, Ticker, OrderBook, RecentTrade


class MarketDataProvider(ABC):
    """
    Abstract interface for market data providers.
    Decouples strategies and analysis engines from specific crypto exchanges (Binance, Bybit, Coinbase, etc.).
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the provider (e.g., 'binance', 'bybit')"""
        pass

    @abstractmethod
    async def get_historical_klines(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 500,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
    ) -> List[Candle]:
        """
        Fetch historical OHLCV candlestick data.
        Returns candles in ascending chronological order.
        """
        pass

    @abstractmethod
    async def get_ticker(self, symbol: str) -> Ticker:
        """
        Fetch 24h ticker price statistics.
        """
        pass

    @abstractmethod
    async def get_order_book(self, symbol: str, limit: int = 20) -> OrderBook:
        """
        Fetch top bids and asks depth.
        """
        pass

    @abstractmethod
    async def get_recent_trades(self, symbol: str, limit: int = 50) -> List[RecentTrade]:
        """
        Fetch most recent completed trades.
        """
        pass

    @abstractmethod
    async def ping(self) -> bool:
        """
        Health check verifying exchange connectivity.
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """
        Gracefully close HTTP sessions and background streams.
        """
        pass
