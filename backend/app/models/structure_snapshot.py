from sqlalchemy import Column, Integer, String, Float, Boolean, JSON, UniqueConstraint
from app.db.base import Base


class MarketStructureSnapshotModel(Base):
    __tablename__ = "structure_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, index=True)
    timeframe = Column(String(10), nullable=False, index=True)
    timestamp = Column(Integer, nullable=False, index=True)
    is_confirmed = Column(Boolean, default=True, nullable=False)

    structure_direction = Column(String(30), nullable=False)
    active_structural_high = Column(JSON, nullable=True)
    active_structural_low = Column(JSON, nullable=True)

    confirmed_swings = Column(JSON, nullable=False, default=list)
    bos_events = Column(JSON, nullable=False, default=list)
    choch_events = Column(JSON, nullable=False, default=list)
    support_zones = Column(JSON, nullable=False, default=list)
    resistance_zones = Column(JSON, nullable=False, default=list)

    structure_engine_version = Column(String(20), nullable=False)
    structure_config_version = Column(String(30), nullable=False)

    __table_args__ = (
        UniqueConstraint("symbol", "timeframe", "timestamp", "is_confirmed", name="uq_structure_snapshot"),
    )
