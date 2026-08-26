from sqlalchemy import Column, Integer, BigInteger, String, Float
from app.db.base import Base


class TickerSnapshotModel(Base):
    __tablename__ = "ticker_snapshots"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, index=True)
    price = Column(Float, nullable=False)
    price_change = Column(Float, default=0.0)
    price_change_percent = Column(Float, default=0.0)
    high_24h = Column(Float, default=0.0)
    low_24h = Column(Float, default=0.0)
    volume_24h = Column(Float, default=0.0)
    quote_volume_24h = Column(Float, default=0.0)
    timestamp = Column(BigInteger, nullable=False, index=True)
