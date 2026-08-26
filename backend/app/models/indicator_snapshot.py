from sqlalchemy import Column, Integer, BigInteger, String, JSON, Index
from app.db.base import Base


class IndicatorSnapshotModel(Base):
    """
    Persistent storage model for confirmed candle-close indicator snapshots.
    Guarantees:
    - Only confirmed closed candles are persisted.
    - Exactly one snapshot per closed candle, engine version, and config version.
    """
    __tablename__ = "indicator_snapshots"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, index=True)
    timeframe = Column(String(10), nullable=False, index=True)
    timestamp = Column(BigInteger, nullable=False, index=True)
    quality_status = Column(String(20), nullable=False, default="HEALTHY")
    indicator_engine_version = Column(String(20), nullable=False)
    indicator_config_version = Column(String(50), nullable=False)

    trend = Column(JSON, nullable=False)
    momentum = Column(JSON, nullable=False)
    volatility = Column(JSON, nullable=False)
    volume = Column(JSON, nullable=False)

    __table_args__ = (
        Index(
            "ix_snap_sym_tf_ts_ver",
            "symbol",
            "timeframe",
            "timestamp",
            "indicator_engine_version",
            "indicator_config_version",
            unique=True,
        ),
    )
