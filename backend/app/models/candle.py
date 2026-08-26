from sqlalchemy import Column, Integer, BigInteger, String, Float, Boolean, Index
from app.db.base import Base


class CandleModel(Base):
    __tablename__ = "candles"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, index=True)
    timeframe = Column(String(10), nullable=False, index=True)
    timestamp = Column(BigInteger, nullable=False, index=True)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    quote_volume = Column(Float, nullable=True)
    trades_count = Column(Integer, nullable=True)
    is_closed = Column(Boolean, default=True)

    __table_args__ = (
        Index("ix_candle_symbol_tf_ts", "symbol", "timeframe", "timestamp", unique=True),
    )
