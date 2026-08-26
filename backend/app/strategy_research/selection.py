"""
Phase 8 — Strategy Promotion Gates & Selection Engine.
Applies 10 explicit mathematical criteria to determine promotion lifecycle status.
"""

from typing import List, Tuple, Optional
from app.strategy_research.models import (
    PartitionPerformanceMetrics,
    PromotionGateResult,
    ResearchStatusEnum,
)


class StrategySelectionEngine:
    """
    Evaluates candidate experiments against strict, objective promotion gates.
    """

    @classmethod
    def evaluate_gates(
        cls,
        candidate_val: PartitionPerformanceMetrics,
        baseline_val: PartitionPerformanceMetrics,
        candidate_test: Optional[PartitionPerformanceMetrics] = None,
        baseline_test: Optional[PartitionPerformanceMetrics] = None,
    ) -> Tuple[List[PromotionGateResult], ResearchStatusEnum, str]:
        gates: List[PromotionGateResult] = []

        # Gate 1: 5C Outcome Improvement on Validation
        g1_pass = candidate_val.h5_median > baseline_val.h5_median
        gates.append(PromotionGateResult(
            gate_id="GATE_1_5C_OUTCOME",
            gate_name="Validation 5C Median Return Improvement",
            required_criterion=f"> Baseline ({baseline_val.h5_median * 100:+.3f}%)",
            measured_value=f"{candidate_val.h5_median * 100:+.3f}%",
            passed=g1_pass,
            details="Candidate 5-candle median forward return on validation exceeds baseline.",
        ))

        # Gate 2: Positive Outcome Rate Improvement
        g2_pass = candidate_val.positive_rate_5c > baseline_val.positive_rate_5c
        gates.append(PromotionGateResult(
            gate_id="GATE_2_POS_RATE",
            gate_name="Validation 5C Positive Outcome Rate",
            required_criterion=f"> Baseline ({baseline_val.positive_rate_5c:.1f}%)",
            measured_value=f"{candidate_val.positive_rate_5c:.1f}%",
            passed=g2_pass,
            details="Percentage of signals with positive forward return exceeds baseline.",
        ))

        # Gate 3: Trend-Chasing Reduction (Pre-5C Extension)
        g3_pass = candidate_val.timing.pre_5_median < baseline_val.timing.pre_5_median or candidate_val.timing.timing_diagnostic == "REDUCED_EXTENSION"
        gates.append(PromotionGateResult(
            gate_id="GATE_3_TIMING_EXTENSION",
            gate_name="Pre-Signal Price Extension Reduction",
            required_criterion=f"< Baseline Pre-5C ({baseline_val.timing.pre_5_median * 100:+.3f}%)",
            measured_value=f"{candidate_val.timing.pre_5_median * 100:+.3f}%",
            passed=g3_pass,
            details="Candidate reduces premature entry at extreme price extensions.",
        ))

        # Gate 4: Signal Clustering Reduction
        g4_pass = candidate_val.clustering.adjacent_signal_rate < baseline_val.clustering.adjacent_signal_rate
        gates.append(PromotionGateResult(
            gate_id="GATE_4_CLUSTERING",
            gate_name="Adjacent Bar Clustering Reduction",
            required_criterion=f"< Baseline ({baseline_val.clustering.adjacent_signal_rate:.1f}%)",
            measured_value=f"{candidate_val.clustering.adjacent_signal_rate:.1f}%",
            passed=g4_pass,
            details="Percentage of signals triggering on immediately adjacent bars is reduced.",
        ))

        # Gate 5: Score Monotonicity Improvement
        g5_pass = (candidate_val.score_monotonicity_grade != "INVERSE") or (candidate_val.score_spearman_corr > baseline_val.score_spearman_corr)
        gates.append(PromotionGateResult(
            gate_id="GATE_5_SCORE_MONOTONICITY",
            gate_name="Score Calibration & Monotonicity",
            required_criterion="Not INVERSE or Spearman correlation > Baseline",
            measured_value=f"{candidate_val.score_monotonicity_grade} (r={candidate_val.score_spearman_corr:+.3f})",
            passed=g5_pass,
            details="Score magnitude Ordering improves over inverse calibration.",
        ))

        # Gate 6: Adequate Sample Size
        g6_pass = candidate_val.signal_count >= 30
        gates.append(PromotionGateResult(
            gate_id="GATE_6_SAMPLE_SIZE",
            gate_name="Validation Sample Size Adequacy",
            required_criterion="N >= 30 (VALID sample)",
            measured_value=f"N = {candidate_val.signal_count}",
            passed=g6_pass,
            details="Sufficient sample size to prevent micro-sample spurious conclusions.",
        ))

        # Gate 7: Directional Symmetry
        min_dir = min(candidate_val.long_5c_median, candidate_val.short_5c_median)
        g7_pass = min_dir >= -0.0015
        gates.append(PromotionGateResult(
            gate_id="GATE_7_DIRECTIONAL_SYMMETRY",
            gate_name="Directional Symmetry (Long vs Short)",
            required_criterion="Min(Long_5C, Short_5C) >= -0.150%",
            measured_value=f"Long: {candidate_val.long_5c_median*100:+.3f}%, Short: {candidate_val.short_5c_median*100:+.3f}%",
            passed=g7_pass,
            details="Neither Long nor Short setups experience catastrophic failure.",
        ))

        # Gate 8: Regime Breadth
        regime_cnt = len(candidate_val.regime_breakdown)
        g8_pass = regime_cnt >= 2
        gates.append(PromotionGateResult(
            gate_id="GATE_8_REGIME_BREADTH",
            gate_name="Market Regime Robustness",
            required_criterion="Active in >= 2 distinct regimes",
            measured_value=f"{regime_cnt} regimes active",
            passed=g8_pass,
            details="Strategy operates across multiple market conditions.",
        ))

        # Gate 9: Validation Survival (Core validation gates 1-8 pass rate >= 75%)
        val_pass_count = sum(1 for g in gates if g.passed)
        g9_pass = (val_pass_count >= 6)
        gates.append(PromotionGateResult(
            gate_id="GATE_9_VALIDATION_SURVIVAL",
            gate_name="Validation Multi-Dimensional Survival",
            required_criterion="Passes >= 6 of 8 validation gates",
            measured_value=f"{val_pass_count}/8 passed",
            passed=g9_pass,
            details="Demonstrates comprehensive multi-dimensional improvement on validation.",
        ))

        # Gate 10: Untouched Final Test Set Generalization
        if candidate_test is not None and baseline_test is not None:
            g10_pass = (candidate_test.h5_median > baseline_test.h5_median) and (candidate_test.signal_count >= 15)
            test_val_str = f"Test 5C: {candidate_test.h5_median*100:+.3f}% (Baseline: {baseline_test.h5_median*100:+.3f}%)"
        else:
            g10_pass = False
            test_val_str = "TEST_SET_NOT_YET_EVALUATED"

        gates.append(PromotionGateResult(
            gate_id="GATE_10_TEST_GENERALIZATION",
            gate_name="Untouched Final Test Generalization",
            required_criterion="Test 5C Median > Baseline Test 5C (Post-freeze)",
            measured_value=test_val_str,
            passed=g10_pass,
            details="Evaluated exactly once after candidate parameters are frozen.",
        ))

        # Determine overall research status
        total_passed = sum(1 for g in gates if g.passed)

        if not g9_pass:
            status = ResearchStatusEnum.VALIDATION_FAILED
            rationale = f"Validation failed ({val_pass_count}/8 gates passed). Candidate rejected."
        elif candidate_test is None:
            status = ResearchStatusEnum.VALIDATION_PASSED
            rationale = "Validation passed. Candidate configuration frozen. Awaiting untouched final Test evaluation."
        else:
            if g10_pass and total_passed >= 9:
                status = ResearchStatusEnum.CANDIDATE_FOR_PAPER_TRADING
                rationale = (
                    f"Passed {total_passed}/10 promotion gates across Validation and untouched Test. "
                    f"Designated CANDIDATE_FOR_PAPER_TRADING for future paper trading evaluation."
                )
            elif g10_pass:
                status = ResearchStatusEnum.RESEARCH_PROMOTED
                rationale = f"Passed {total_passed}/10 promotion gates including Test Generalization."
            else:
                status = ResearchStatusEnum.TEST_EVALUATED
                rationale = f"Evaluated on untouched Test set ({total_passed}/10 gates passed). Test generalization was insufficient."

        return gates, status, rationale
