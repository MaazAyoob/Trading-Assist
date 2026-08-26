"""
SQLAlchemy ORM models for backtesting run records and signal outcomes.
Completely isolated from live production research signals.
"""

from sqlalchemy import Column, String, Integer, Float, Boolean, Text, BigInteger, Index, JSON
from app.db.session import Base


class BacktestRunModel(Base):
    """
    Persisted historical backtest run record.
    """
    __tablename__ = "backtest_runs"

    run_id = Column(String(128), primary_key=True, index=True)
    symbol = Column(String(32), nullable=False, index=True)
    timeframe = Column(String(16), nullable=False, index=True)
    start_timestamp = Column(BigInteger, nullable=False)
    end_timestamp = Column(BigInteger, nullable=False)
    candle_count = Column(Integer, nullable=False)
    signal_count = Column(Integer, nullable=False)
    dataset_hash = Column(String(64), nullable=False)
    
    # Engine versions
    backtest_engine_version = Column(String(32), nullable=False)
    backtest_config_version = Column(String(32), nullable=False)
    signal_engine_version = Column(String(32), nullable=False)
    
    # Serialized payloads
    config_json = Column(JSON, nullable=False)
    metrics_json = Column(JSON, nullable=False)
    integrity_json = Column(JSON, nullable=False)
    dataset_metadata_json = Column(JSON, nullable=False)
    
    status = Column(String(32), default="COMPLETED")
    created_timestamp = Column(BigInteger, nullable=False)

    __table_args__ = (
        Index("ix_backtest_runs_lookup", "symbol", "timeframe", "created_timestamp"),
    )


class BacktestSignalOutcomeModel(Base):
    """
    Persisted signal outcome record belonging to a specific BacktestRun.
    """
    __tablename__ = "backtest_signal_outcomes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String(128), nullable=False, index=True)
    signal_id = Column(String(128), nullable=False)
    symbol = Column(String(32), nullable=False)
    timeframe = Column(String(16), nullable=False)
    signal_timestamp = Column(BigInteger, nullable=False, index=True)
    signal_direction = Column(String(32), nullable=False)
    signal_strength = Column(String(32), nullable=False)
    signal_score = Column(Float, nullable=False)
    entry_reference_price = Column(Float, nullable=False)
    
    # Serialized horizon outcomes dictionary {1: {...}, 3: {...}, ...}
    outcomes_json = Column(JSON, nullable=False)
    
    regime_at_signal = Column(String(64), nullable=False)
    structure_at_signal = Column(String(64), nullable=False)
    volatility_at_signal = Column(String(64), nullable=False)

    __table_args__ = (
        Index("ix_backtest_signal_run", "run_id", "signal_timestamp"),
    )
