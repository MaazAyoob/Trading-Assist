"""
Phase 8 — Strategy Research REST API Endpoints.
Serves immutable baseline and controlled candidate experiment evaluations.
"""

from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from app.strategy_research.models import (
    ExperimentEvaluation,
    ExperimentComparisonReport,
)
from app.strategy_research.registry import ResearchRegistry
from app.strategy_research.engine import StrategyResearchEngine
from app.backtesting.dataset import DatasetManager
from app.core.logging import logger

router = APIRouter()


def _ensure_experiments_loaded() -> Dict[str, ExperimentEvaluation]:
    exps = ResearchRegistry.get_all_experiments()
    if not exps:
        logger.info("Initializing and executing Phase 8 strategy research battery...")
        dm = DatasetManager()
        try:
            candles, meta = dm.load_processed_dataset("BTCUSDT_15m_1704067200000_1767226499999_0c65f8e3")
        except Exception:
            candles, meta = dm.load_processed_dataset("data/processed/BTCUSDT_15m_1787132700000_1787582699999_d02351a2.json")
        exps = StrategyResearchEngine.run_all_experiments(candles)
        ResearchRegistry.save_all_experiments(exps)
    return exps


@router.get("/registry", response_model=Dict[str, ExperimentEvaluation])
def get_research_registry():
    """Returns all registered experiments, partition metrics, and promotion gate statuses."""
    return _ensure_experiments_loaded()


@router.get("/baseline", response_model=ExperimentEvaluation)
def get_strategy_baseline():
    """Returns the immutable Phase 5 baseline evaluation across Train, Validation, and Test."""
    exps = _ensure_experiments_loaded()
    baseline = exps.get("BASELINE")
    if not baseline:
        raise HTTPException(status_code=404, detail="Baseline evaluation not found.")
    return baseline


@router.get("/experiments", response_model=List[ExperimentEvaluation])
def list_experiments():
    """Returns the list of all candidate experiments."""
    exps = _ensure_experiments_loaded()
    return [v for k, v in exps.items() if k != "BASELINE"]


@router.get("/experiments/{experiment_id}", response_model=ExperimentEvaluation)
def get_experiment_detail(experiment_id: str):
    """Returns comprehensive evaluation details for a specific experiment."""
    exps = _ensure_experiments_loaded()
    exp = exps.get(experiment_id)
    if not exp:
        raise HTTPException(status_code=404, detail=f"Experiment '{experiment_id}' not found.")
    return exp


@router.get("/experiments/{experiment_id}/comparison", response_model=ExperimentComparisonReport)
def get_experiment_comparison(
    experiment_id: str,
    partition: str = Query("VALIDATION", description="Partition to compare: TRAIN, VALIDATION, or TEST"),
):
    """Returns a side-by-side metric comparison between Baseline and Candidate Experiment."""
    _ensure_experiments_loaded()
    comp = ResearchRegistry.generate_comparison(experiment_id, partition.upper())
    if not comp:
        raise HTTPException(status_code=404, detail=f"Comparison for experiment '{experiment_id}' on partition '{partition}' not available.")
    return comp


@router.post("/experiments/run", response_model=Dict[str, ExperimentEvaluation])
def run_all_research_experiments():
    """Triggers execution of the complete Phase 8 research battery on the historical dataset."""
    dm = DatasetManager()
    candles, meta = dm.load_processed_dataset("BTCUSDT_15m_1704067200000_1767226499999_0c65f8e3")
    exps = StrategyResearchEngine.run_all_experiments(candles)
    ResearchRegistry.save_all_experiments(exps)
    return exps
