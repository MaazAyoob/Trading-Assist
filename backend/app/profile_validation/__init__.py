"""
Profile Validation Lab Package for Phase 12.
Provides independent backtesting, horizon evaluation (1C, 3C, 5C, 10C, 20C), signal density, and cost sensitivity analysis.
"""

from app.profile_validation.metrics import ProfileValidationMetricsCalculator
from app.profile_validation.evaluation import ProfileEvaluationRunner
from app.profile_validation.comparison import ProfileComparisonEngine
from app.profile_validation.reports import ProfileReportGenerator

__all__ = [
    "ProfileValidationMetricsCalculator",
    "ProfileEvaluationRunner",
    "ProfileComparisonEngine",
    "ProfileReportGenerator",
]
