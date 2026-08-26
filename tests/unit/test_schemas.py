import pytest
from app.data.schema import Candle, Ticker, OrderBook, OrderBookLevel, ConnectionStateEnum


def test_candle_schema_valid():
    candle = Candle(
        timestamp=1700000000000,
        open=50000.0,
        high=51000.0,
        low=49500.0,
        close=50800.0,
        volume=120.5,
        close_time=1700000899999,
        quote_volume=6000000.0,
        trades_count=1500,
        is_closed=True,
    )
    assert candle.close == 50800.0
    assert candle.high >= candle.open
    assert candle.is_closed is True


def test_ticker_schema_valid():
    ticker = Ticker(
        symbol="BTCUSDT",
        price=65432.10,
        price_change=1200.5,
        price_change_percent=2.34,
        high_24h=66000.0,
        low_24h=63900.0,
        volume_24h=25400.12,
        quote_volume_24h=1650000000.0,
        timestamp=1700000000000,
    )
    assert ticker.symbol == "BTCUSDT"
    assert ticker.price == 65432.10
    assert ticker.price_change_percent == 2.34


def test_orderbook_schema_valid():
    book = OrderBook(
        symbol="BTCUSDT",
        last_update_id=123456,
        bids=[OrderBookLevel(price=65000.0, quantity=1.5)],
        asks=[OrderBookLevel(price=65001.0, quantity=2.0)],
        timestamp=1700000000000,
    )
    assert len(book.bids) == 1
    assert len(book.asks) == 1
    assert book.bids[0].price == 65000.0
