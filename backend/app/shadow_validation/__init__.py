"""
Phase 9 — Real-Time Shadow / Paper Validation Package.
"""

from app.shadow_validation.models import (
    ShadowSignal,
    HorizonOutcome,
    ShadowSession,
    SessionStatusEnum,
    CandidateLiveMetrics,
    DriftMetricComparison,
    CausalAuditReport,
)
from app.shadow_validation.config import CANDIDATES, HORIZONS
from app.shadow_validation.engine import ShadowValidationEngine
from app.shadow_validation.outcomes import ShadowOutcomeEngine
from app.shadow_validation.statistics import LiveStatisticsAggregator
from app.shadow_validation.drift import DriftMonitor
from app.shadow_validation.alerts import ShadowAlertBus
from app.shadow_validation.registry import ShadowRegistry
from app.shadow_validation.reports import ShadowReportGenerator

__all__ = [
    "ShadowSignal",
    "HorizonOutcome",
    "ShadowSession",
    "SessionStatusEnum",
    "CandidateLiveMetrics",
    "DriftMetricComparison",
    "CausalAuditReport",
    "CANDIDATES",
    "HORIZONS",
    "ShadowValidationEngine",
    "ShadowOutcomeEngine",
    "LiveStatisticsAggregator",
    "DriftMonitor",
    "ShadowAlertBus",
    "ShadowRegistry",
    "ShadowReportGenerator",
]
