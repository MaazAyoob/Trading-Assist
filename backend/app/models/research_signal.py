from sqlalchemy import Column, Integer, String, Float, Boolean, JSON, UniqueConstraint
from app.db.base import Base


class ResearchSignalModel(Base):
    __tablename__ = "research_signals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, index=True)
    timeframe = Column(String(10), nullable=False, index=True)
    timestamp = Column(Integer, nullable=False, index=True)  # Candle open timestamp in ms
    is_confirmed = Column(Boolean, default=True, nullable=False)

    direction = Column(String(30), nullable=False)
    strength = Column(String(30), nullable=False)
    status = Column(String(30), nullable=False)
    score = Column(Float, nullable=False)

    evidence_groups = Column(JSON, nullable=False, default=dict)
    score_trace = Column(JSON, nullable=False, default=dict)
    conflicts = Column(JSON, nullable=False, default=list)
    supporting_evidence = Column(JSON, nullable=False, default=list)
    contradictions = Column(JSON, nullable=False, default=list)

    data_quality_status = Column(String(30), nullable=False, default="HEALTHY")
    engine_version = Column(String(20), nullable=False)
    config_version = Column(String(30), nullable=False)

    __table_args__ = (
        UniqueConstraint("symbol", "timeframe", "timestamp", "engine_version", "config_version", name="uq_research_signal"),
    )
