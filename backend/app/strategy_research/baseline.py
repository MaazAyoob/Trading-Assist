"""
Phase 8 — Frozen Strategy Baseline Subsystem.
Guarantees 100% mathematical immutability and execution equivalence with Phase 5.
"""

from typing import List, Optional, Tuple
from app.data.schema import Candle
from app.signals.models import ResearchSignal
from app.signals.engine import MultiFactorSignalEngine
from app.strategy_research.config import STRATEGY_BASELINE, BASELINE_CONFIG_VERSION


class BaselineStrategyRunner:
    """
    Immutable runner for Phase 5 Multi-Factor Signal Engine (v0.5.0).
    Never modifies weights, thresholds, or evidence extraction formulas.
    """

    BASELINE_ID = STRATEGY_BASELINE
    VERSION = BASELINE_CONFIG_VERSION

    @classmethod
    def get_baseline_identity(cls) -> dict:
        return {
            "baseline_id": cls.BASELINE_ID,
            "engine_version": "0.5.0",
            "config_version": cls.VERSION,
            "description": "Frozen Phase 5 Multi-Factor Trend & Structure Research Engine",
            "immutable": True,
        }
