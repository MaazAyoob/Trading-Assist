"""
Phase 7 — Signal Forensics & Factor Attribution API Endpoints.
Serves deterministic historical forensics, timing metrics, and factor attributions.
"""

import os
import json
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from app.forensics.models import (
    ForensicsReport,
    FactorPerformanceBin,
    FactorMonotonicityEvaluation,
    SignalTimingForensics,
    SignalClusteringForensics,
    RegimeForensicsRecord,
    StructureForensicsRecord,
    ConflictForensicsRecord,
    ScoreCalibrationRecord,
)
from app.forensics.engine import SignalForensicsEngine
from app.backtesting.dataset import DatasetManager
from app.core.logging import logger

router = APIRouter()

# In-memory cache for forensics report
_CACHED_FORENSICS: Optional[ForensicsReport] = None


def get_forensics_report() -> ForensicsReport:
    global _CACHED_FORENSICS
    if _CACHED_FORENSICS is not None:
        return _CACHED_FORENSICS

    # Check if a serialized forensics report exists on disk
    report_path = "data/runs/forensics_report_BTCUSDT_15m.json"
    if os.path.exists(report_path):
        try:
            with open(report_path, "r") as f:
                data = json.load(f)
                _CACHED_FORENSICS = ForensicsReport(**data)
                return _CACHED_FORENSICS
        except Exception as e:
            logger.warning(f"Failed to load cached forensics report: {e}")

    # Generate from historical dataset
    dm = DatasetManager()
    dataset_file = "BTCUSDT_15m_1704067200000_1767226499999_0c65f8e3"
    try:
        candles, meta = dm.load_processed_dataset(dataset_file)
    except Exception:
        # Fallback to standard 500 candle dataset if 70k file not found
        candles, meta = dm.load_processed_dataset("data/processed/BTCUSDT_15m_1787132700000_1787582699999_d02351a2.json")

    report = SignalForensicsEngine.analyze(candles, dataset_metadata=meta)

    # Persist report cache
    try:
        os.makedirs("data/runs", exist_ok=True)
        with open(report_path, "w") as f:
            json.dump(report.model_dump(), f)
    except Exception as e:
        logger.warning(f"Could not persist forensics report cache: {e}")

    _CACHED_FORENSICS = report
    return _CACHED_FORENSICS


@router.get("/summary", response_model=ForensicsReport)
def get_forensics_summary(report: ForensicsReport = Depends(get_forensics_report)):
    """Returns the complete Phase 7 Forensic Research Report and 3-part diagnosis."""
    return report


@router.get("/factors", response_model=List[FactorPerformanceBin])
def get_factor_attribution(report: ForensicsReport = Depends(get_forensics_report)):
    """Returns forward return outcomes conditioned on isolated factor score bins."""
    return report.factor_performance


@router.get("/timing")
def get_signal_timing(report: ForensicsReport = Depends(get_forensics_report)):
    """Returns Pre-signal vs Post-signal return timing and trend-chasing metrics."""
    return {
        "timing_long": report.timing_long,
        "timing_short": report.timing_short,
        "timing_combined": report.timing_combined,
        "clustering": report.clustering,
    }


@router.get("/regimes", response_model=List[RegimeForensicsRecord])
def get_regime_forensics(report: ForensicsReport = Depends(get_forensics_report)):
    """Returns signal outcomes conditioned on market regime at signal time."""
    return report.regime_forensics


@router.get("/structure")
def get_structure_forensics(report: ForensicsReport = Depends(get_forensics_report)):
    """Returns signal outcomes conditioned on BOS/CHoCH structural events and S/R distance."""
    return {
        "structural_events": report.structure_forensics,
        "sr_distance_breakdown": report.sr_distance_forensics,
    }


@router.get("/conflicts", response_model=List[ConflictForensicsRecord])
def get_conflict_forensics(report: ForensicsReport = Depends(get_forensics_report)):
    """Returns empirical effectiveness metrics for all active conflict penalty rules."""
    return report.conflict_forensics


@router.get("/score")
def get_score_calibration(report: ForensicsReport = Depends(get_forensics_report)):
    """Returns score magnitude vs return calibration bins and mathematical monotonicity grade."""
    return {
        "score_calibration": report.score_calibration,
        "score_monotonicity_grade": report.score_monotonicity_grade,
        "score_monotonicity_criteria": report.score_monotonicity_criteria,
        "factor_monotonicity": report.factor_monotonicity,
    }
