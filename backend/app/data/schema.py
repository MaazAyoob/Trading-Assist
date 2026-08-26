from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class ConnectionStateEnum(str, Enum):
    LIVE = "LIVE"
    RECONNECTING = "RECONNECTING"
    OFFLINE = "OFFLINE"


class CandleStateEnum(str, Enum):
    OPEN = "OPEN"
    UPDATING = "UPDATING"
    CLOSED = "CLOSED"


class QualityStatusEnum(str, Enum):
    HEALTHY = "HEALTHY"
    WARNING = "WARNING"
    INVALID = "INVALID"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    OFFLINE = "OFFLINE"


class Candle(BaseModel):
    timestamp: int = Field(..., description="Start timestamp of the candle in milliseconds (UTC)")
    open: float = Field(..., description="Open price")
    high: float = Field(..., description="Highest price during period")
    low: float = Field(..., description="Lowest price during period")
    close: float = Field(..., description="Close (or current) price")
    volume: float = Field(..., description="Base asset volume")
    close_time: Optional[int] = Field(None, description="End timestamp of candle in milliseconds (UTC)")
    quote_volume: Optional[float] = Field(None, description="Quote asset volume")
    trades_count: Optional[int] = Field(None, description="Number of trades")
    is_closed: bool = Field(True, description="Whether this candle interval is finalized/closed")
    state: CandleStateEnum = Field(CandleStateEnum.CLOSED, description="Candle lifecycle state: OPEN, UPDATING, or CLOSED")


class Ticker(BaseModel):
    symbol: str
    price: float
    price_change: float = 0.0
    price_change_percent: float = 0.0
    high_24h: float = 0.0
    low_24h: float = 0.0
    volume_24h: float = 0.0
    quote_volume_24h: float = 0.0
    timestamp: int


class OrderBookLevel(BaseModel):
    price: float
    quantity: float


class OrderBook(BaseModel):
    symbol: str
    last_update_id: int
    bids: List[OrderBookLevel]
    asks: List[OrderBookLevel]
    timestamp: int


class RecentTrade(BaseModel):
    id: int
    price: float
    qty: float
    time: int
    is_buyer_maker: bool


class MarketConnectionStatus(BaseModel):
    state: ConnectionStateEnum
    symbol: str
    timeframe: str
    last_ping: int
    last_message_time: int
    reconnect_attempts: int = 0
    message: Optional[str] = None


class MarketDataQuality(BaseModel):
    symbol: str
    timeframe: str
    status: QualityStatusEnum
    latest_timestamp: Optional[int] = None
    candle_count: int = 0
    duplicate_count: int = 0
    gap_count: int = 0
    invalid_count: int = 0
    gaps: List[dict] = Field(default_factory=list)
    stale: bool = False
    validation_messages: List[str] = Field(default_factory=list)


class KlineStreamPayload(BaseModel):
    symbol: str
    timeframe: str
    candle: Candle
    candle_state: CandleStateEnum = CandleStateEnum.CLOSED
    ticker: Optional[Ticker] = None
    server_time: int
    indicators: Optional[dict] = None
