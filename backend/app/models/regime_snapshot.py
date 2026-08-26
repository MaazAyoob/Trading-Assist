from sqlalchemy import Column, Integer, String, Float, Boolean, JSON, UniqueConstraint
from app.db.base import Base


class MarketRegimeSnapshotModel(Base):
    __tablename__ = "regime_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, index=True)
    timeframe = Column(String(10), nullable=False, index=True)
    timestamp = Column(Integer, nullable=False, index=True)  # Candle open timestamp in ms
    is_confirmed = Column(Boolean, default=True, nullable=False)

    direction = Column(String(30), nullable=False)
    trend_strength = Column(String(30), nullable=False)
    volatility_state = Column(String(30), nullable=False)
    momentum_state = Column(String(30), nullable=False)
    volume_state = Column(String(30), nullable=False)
    structure_state = Column(String(30), nullable=False)
    overall_regime = Column(String(40), nullable=False)

    evidence_strength = Column(Float, nullable=False)
    evidence = Column(JSON, nullable=False, default=list)
    contradictions = Column(JSON, nullable=False, default=list)

    regime_engine_version = Column(String(20), nullable=False)
    regime_config_version = Column(String(30), nullable=False)

    __table_args__ = (
        UniqueConstraint("symbol", "timeframe", "timestamp", "is_confirmed", name="uq_regime_snapshot"),
    )
