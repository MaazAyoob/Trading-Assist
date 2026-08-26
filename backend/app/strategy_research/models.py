"""
Phase 8 — Strategy Research & Redesign Domain Models.
Defines schemas for hypothesis tracking, partitions, metrics, and promotion status lifecycle.
"""

from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class ResearchStatusEnum(str, Enum):
    DRAFT = "DRAFT"
    RUNNING = "RUNNING"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    VALIDATION_PASSED = "VALIDATION_PASSED"
    TEST_EVALUATED = "TEST_EVALUATED"
    RESEARCH_PROMOTED = "RESEARCH_PROMOTED"
    CANDIDATE_FOR_PAPER_TRADING = "CANDIDATE_FOR_PAPER_TRADING"
    REJECTED = "REJECTED"


class PartitionTimingMetrics(BaseModel):
    """Timing metrics: Pre-signal vs Post-signal return distributions."""
    pre_1_median: float = 0.0
    pre_3_median: float = 0.0
    pre_5_median: float = 0.0
    pre_10_median: float = 0.0
    pre_20_median: float = 0.0
    post_1_median: float = 0.0
    post_3_median: float = 0.0
    post_5_median: float = 0.0
    post_10_median: float = 0.0
    post_20_median: float = 0.0
    pre_vs_post_5c_corr: float = 0.0
    trend_chasing_flag: bool = False
    timing_diagnostic: str = ""


class PartitionClusteringMetrics(BaseModel):
    """Clustering frequency and directional persistence."""
    adjacent_signal_rate: float = 0.0
    signals_within_2_bars: float = 0.0
    signals_within_4_bars: float = 0.0
    signals_within_8_bars: float = 0.0
    independent_episodes_count: int = 0
    avg_episode_length_bars: float = 0.0
    max_episode_length_bars: int = 0


class PartitionPerformanceMetrics(BaseModel):
    """Complete statistical outcome record for a chronological dataset partition."""
    partition_name: str
    start_timestamp: int
    end_timestamp: int
    candle_count: int
    signal_count: int
    long_count: int
    short_count: int
    signals_per_day: float
    signals_per_100_candles: float

    # Forward return distributions (Analytical without lookahead)
    h1_median: float = 0.0
    h1_mean: float = 0.0
    h3_median: float = 0.0
    h3_mean: float = 0.0
    h5_median: float = 0.0
    h5_mean: float = 0.0
    h10_median: float = 0.0
    h10_mean: float = 0.0
    h20_median: float = 0.0
    h20_mean: float = 0.0

    # Directional symmetry
    long_5c_median: float = 0.0
    short_5c_median: float = 0.0
    long_10c_median: float = 0.0
    short_10c_median: float = 0.0
    long_20c_median: float = 0.0
    short_20c_median: float = 0.0

    positive_rate_5c: float = 0.0
    positive_rate_10c: float = 0.0
    mfe_5c_median: float = 0.0
    mae_5c_median: float = 0.0

    # Cost sensitivity (0 bps, 5 bps, 10 bps)
    h5_median_cost_0bps: float = 0.0
    h5_median_cost_5bps: float = 0.0
    h5_median_cost_10bps: float = 0.0

    timing: PartitionTimingMetrics = Field(default_factory=PartitionTimingMetrics)
    clustering: PartitionClusteringMetrics = Field(default_factory=PartitionClusteringMetrics)
    score_monotonicity_grade: str = "NON_MONOTONIC"
    score_spearman_corr: float = 0.0
    regime_breakdown: Dict[str, Dict[str, float]] = Field(default_factory=dict)
    sample_warning: str = "VALID"


class PromotionGateResult(BaseModel):
    """Result of an individual objective promotion gate check."""
    gate_id: str
    gate_name: str
    required_criterion: str
    measured_value: str
    passed: bool
    details: str


class ExperimentEvaluation(BaseModel):
    """Full evaluation record of an experiment across all chronological partitions."""
    experiment_id: str
    experiment_name: str
    description: str
    hypothesis: str
    parameters: Dict[str, Any]
    engine_version: str
    dataset_hash: str
    created_timestamp: int
    status: ResearchStatusEnum

    # Partition outcomes
    train_metrics: PartitionPerformanceMetrics
    validation_metrics: PartitionPerformanceMetrics
    test_metrics: Optional[PartitionPerformanceMetrics] = None
    quarterly_metrics: List[PartitionPerformanceMetrics] = Field(default_factory=list)

    # Gate checklist
    promotion_gates: List[PromotionGateResult] = Field(default_factory=list)
    gates_passed_count: int = 0
    total_gates_count: int = 10
    final_decision: str = "PENDING"
    decision_rationale: str = ""


class BaselineComparisonItem(BaseModel):
    """Side-by-side metric comparison between Baseline and Candidate Experiment."""
    metric_name: str
    baseline_val: str
    candidate_val: str
    delta_str: str
    improved: bool
    description: str


class ExperimentComparisonReport(BaseModel):
    """Structured Baseline vs Experiment comparison payload."""
    experiment_id: str
    experiment_name: str
    baseline_id: str = "PHASE5_V0.5.0"
    status: ResearchStatusEnum
    partition_evaluated: str
    comparisons: List[BaselineComparisonItem]
    promotion_status: str
    summary_observed_facts: List[str]
    summary_possible_explanations: List[str]
    summary_unproven_hypotheses: List[str]
