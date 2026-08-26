"""
Backtesting & Validation Engine package exports.
"""

from app.backtesting.version import BACKTEST_ENGINE_VERSION, BACKTEST_CONFIG_VERSION
from app.backtesting.config import BacktestConfig, CostModelConfig, SplitConfig
from app.backtesting.models import (
    BacktestRun,
    DatasetMetadata,
    SignalOutcome,
    HorizonOutcome,
    BacktestMetrics,
    HorizonMetrics,
    ConditionalBreakdown,
    DistributionStats,
    IntegrityReport,
    OutcomeClassificationEnum,
)
from app.backtesting.dataset import DatasetManager
from app.backtesting.downloader import BinanceHistoricalDownloader
from app.backtesting.outcomes import OutcomeCalculator
from app.backtesting.statistics import StatisticalEngine
from app.backtesting.metrics import MetricsAggregator
from app.backtesting.validation import DatasetSplitter, WalkForwardManager
from app.backtesting.reports import ReportGenerator
from app.backtesting.engine import BacktestEngine

__all__ = [
    "BACKTEST_ENGINE_VERSION",
    "BACKTEST_CONFIG_VERSION",
    "BacktestConfig",
    "CostModelConfig",
    "SplitConfig",
    "BacktestRun",
    "DatasetMetadata",
    "SignalOutcome",
    "HorizonOutcome",
    "BacktestMetrics",
    "HorizonMetrics",
    "ConditionalBreakdown",
    "DistributionStats",
    "IntegrityReport",
    "OutcomeClassificationEnum",
    "DatasetManager",
    "BinanceHistoricalDownloader",
    "OutcomeCalculator",
    "StatisticalEngine",
    "MetricsAggregator",
    "DatasetSplitter",
    "WalkForwardManager",
    "ReportGenerator",
    "BacktestEngine",
]
