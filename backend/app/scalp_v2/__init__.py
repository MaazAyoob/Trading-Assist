"""
SCALP_STRATEGY_V2 Package.
"""
from app.scalp_v2.version import SCALP_STRATEGY_V2_ID, SCALP_STRATEGY_V2_VERSION
from app.scalp_v2.models import (
    ScalpV2Direction,
    ScalpV2SetupType,
    ScalpV2TradeState,
    ScalpV2Lifecycle,
    ScalpV2Strength,
    ScalpV2Signal,
    ScalpV2Response,
    ScalpV2StatsResponse,
    ScalpCompareResponse,
)
from app.scalp_v2.engine import ScalpV2StrategyEngine
from app.scalp_v2.evaluation import (
    ScalpV2EvaluationReport,
    HorizonResult,
    SetupQualityResult,
    ScoreBucketResult,
    SignalFrequencyComparison,
    run_scalp_v2_historical_evaluation,
)
from app.scalp_v2.diagnostics import (
    ScalpV2DiagnosticEngine,
    ScalpV2DiagnosticReport,
    ScoreBucketDiagnostic,
    ScoreMonotonicityReport,
    DirectionDiagnostic,
    SetupDiagnostic,
    TimingDistribution,
    EntryTimingDiagnostic,
    FactorDiagnostic,
    ClusteringDiagnostic,
    FlipDiagnostic,
    SetupAccountingReport,
)

__all__ = [
    "SCALP_STRATEGY_V2_ID",
    "SCALP_STRATEGY_V2_VERSION",
    "ScalpV2Direction",
    "ScalpV2SetupType",
    "ScalpV2TradeState",
    "ScalpV2Lifecycle",
    "ScalpV2Strength",
    "ScalpV2Signal",
    "ScalpV2Response",
    "ScalpV2StatsResponse",
    "ScalpCompareResponse",
    "ScalpV2StrategyEngine",
    "ScalpV2EvaluationReport",
    "HorizonResult",
    "SetupQualityResult",
    "ScoreBucketResult",
    "SignalFrequencyComparison",
    "run_scalp_v2_historical_evaluation",
    "ScalpV2DiagnosticEngine",
    "ScalpV2DiagnosticReport",
    "ScoreBucketDiagnostic",
    "ScoreMonotonicityReport",
    "DirectionDiagnostic",
    "SetupDiagnostic",
    "TimingDistribution",
    "EntryTimingDiagnostic",
    "FactorDiagnostic",
    "ClusteringDiagnostic",
    "FlipDiagnostic",
    "SetupAccountingReport",
]
