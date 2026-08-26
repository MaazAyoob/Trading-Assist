from typing import List, Optional
from fastapi import APIRouter, Query, Depends
from app.core.config import settings
from app.core.errors import TimeframeNotSupportedException, SymbolNotFoundException
from app.data.base import MarketDataProvider
from app.data.binance import BinanceMarketDataProvider
from app.data.ws_manager import ws_manager
from app.data.schema import Candle, Ticker, OrderBook, RecentTrade, MarketConnectionStatus

router = APIRouter()

# Dependency injection for market data provider
def get_market_provider() -> MarketDataProvider:
    return BinanceMarketDataProvider()


@router.get("/klines", response_model=List[Candle], summary="Get historical OHLCV candles")
async def get_klines(
    symbol: str = Query(default=settings.DEFAULT_SYMBOL, description="Trading pair symbol (e.g., BTCUSDT)"),
    timeframe: str = Query(default="15m", description="Candle interval (1m, 5m, 15m, 1h, 4h, 1d)"),
    limit: int = Query(default=200, ge=10, le=1000, description="Number of candles to return"),
    start_time: Optional[int] = Query(default=None, description="Start timestamp in ms"),
    end_time: Optional[int] = Query(default=None, description="End timestamp in ms"),
    provider: MarketDataProvider = Depends(get_market_provider),
):
    if timeframe not in settings.SUPPORTED_TIMEFRAMES:
        raise TimeframeNotSupportedException(timeframe)
    
    symbol = symbol.upper()
    candles = await provider.get_historical_klines(
        symbol=symbol,
        timeframe=timeframe,
        limit=limit,
        start_time=start_time,
        end_time=end_time,
    )
    return candles


@router.get("/ticker", response_model=Ticker, summary="Get 24h ticker statistics")
async def get_ticker(
    symbol: str = Query(default=settings.DEFAULT_SYMBOL, description="Trading pair symbol"),
    provider: MarketDataProvider = Depends(get_market_provider),
):
    symbol = symbol.upper()
    # Check if we have an in-memory realtime ticker first
    cached = ws_manager.get_latest_ticker(symbol)
    if cached:
        return cached
    return await provider.get_ticker(symbol)


@router.get("/orderbook", response_model=OrderBook, summary="Get order book depth")
async def get_orderbook(
    symbol: str = Query(default=settings.DEFAULT_SYMBOL, description="Trading pair symbol"),
    limit: int = Query(default=20, ge=5, le=100, description="Depth limit"),
    provider: MarketDataProvider = Depends(get_market_provider),
):
    return await provider.get_order_book(symbol=symbol.upper(), limit=limit)


@router.get("/trades", response_model=List[RecentTrade], summary="Get recent executed trades")
async def get_trades(
    symbol: str = Query(default=settings.DEFAULT_SYMBOL, description="Trading pair symbol"),
    limit: int = Query(default=50, ge=10, le=500, description="Trade limit"),
    provider: MarketDataProvider = Depends(get_market_provider),
):
    return await provider.get_recent_trades(symbol=symbol.upper(), limit=limit)


@router.get("/status", response_model=MarketConnectionStatus, summary="Get live market connection status")
async def get_market_status(
    symbol: str = Query(default=settings.DEFAULT_SYMBOL),
    timeframe: str = Query(default="15m"),
):
    return ws_manager.get_status(symbol=symbol.upper(), timeframe=timeframe)


@router.get("/symbols", summary="Get supported trading symbols and timeframes")
async def get_symbols_config():
    return {
        "default_symbol": settings.DEFAULT_SYMBOL,
        "supported_symbols": settings.SUPPORTED_SYMBOLS,
        "supported_timeframes": settings.SUPPORTED_TIMEFRAMES,
    }
