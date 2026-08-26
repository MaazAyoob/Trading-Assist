"""
Phase 9 — Shadow Validation Research Report Generator.
Formats comprehensive session summaries with strict adherence to causal audit and research conventions.
"""

from typing import Dict, Any
import time

from app.shadow_validation.models import (
    ShadowSession,
    ShadowSignal,
    CandidateLiveMetrics,
    CausalAuditReport,
)


class ShadowReportGenerator:
    """
    Generates structured scientific validation reports for completed or active shadow sessions.
    """

    @classmethod
    def generate_report(
        cls,
        session: ShadowSession,
        signals: list[ShadowSignal],
        metrics_by_candidate: Dict[str, CandidateLiveMetrics],
        audit: CausalAuditReport,
    ) -> Dict[str, Any]:
        report_id = f"REPORT_SHADOW_{session.session_id}"
        created_ts = int(time.time() * 1000)

        # Observed Facts
        observed_facts = [
            f"Session '{session.session_id}' monitored {session.candles_processed_count} closed 15m candles.",
            f"Generated {len(signals)} total shadow signals across Baseline and Phase 8 candidates.",
        ]
        for c_id, m in metrics_by_candidate.items():
            observed_facts.append(
                f"[{c_id}] Produced {m.total_signals} signals ({m.long_count} Long, {m.short_count} Short). "
                f"5C median return: {m.h5_median_raw*100:+.3f}%, Positive rate: {m.h5_positive_rate:.1f}%, "
                f"Adjacent clustering: {m.adjacent_signal_rate:.1f}%, Sample Status: {m.sample_status}."
            )

        # Possible Explanations
        possible_explanations = [
            "Proximity constraints to institutional volume-weighted references (VWAP) continue to reduce entry extension during live market conditions.",
            "Independent episode grouping and cooldown mechanisms reduce repetitive over-triggering across consecutive candles.",
        ]

        # Unproven Hypotheses
        unproven_hypotheses = [
            "Live market volatility shifts between macro trending and high-frequency chop may require larger continuous live sample sizes (N >= 100) to confirm asymptotic return convergence.",
        ]

        return {
            "report_id": report_id,
            "session_id": session.session_id,
            "generated_at_timestamp": created_ts,
            "session_start_time": session.start_time,
            "session_end_time": session.end_time,
            "session_status": session.status.value,
            "final_research_status": session.final_research_status.value,
            "market_data_provider": session.market_data_provider,
            "symbol": session.symbol,
            "timeframe": session.timeframe,
            "configuration_hashes": session.configuration_hashes,
            "candles_processed": session.candles_processed_count,
            "total_signals_recorded": len(signals),
            "candidates_metrics": {k: v.model_dump() for k, v in metrics_by_candidate.items()},
            "causal_audit": audit.model_dump(),
            "summary_observed_facts": observed_facts,
            "summary_possible_explanations": possible_explanations,
            "summary_unproven_hypotheses": unproven_hypotheses,
            "mandatory_disclaimer": "SHADOW VALIDATION ONLY. No real orders, no execution simulation. Historical and live returns are empirical research observations.",
        }
