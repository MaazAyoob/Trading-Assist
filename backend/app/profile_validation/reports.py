"""
Profile Report Generator for Phase 12.
"""

from typing import Dict, Any
from app.profiles.models import ProfileComparisonReport


class ProfileReportGenerator:
    @staticmethod
    def generate_text_summary(report: ProfileComparisonReport) -> str:
        lines = [
            "=" * 60,
            f"MULTI-PROFILE COMPARISON REPORT — {report.symbol}",
            "=" * 60,
            f"{'Profile':<18} | {'Primary':<7} | {'Signals/Day':<12} | {'Pos Rate':<10} | {'Status':<15}",
            "-" * 60,
        ]

        for p in report.profiles:
            lines.append(
                f"{p.display_name:<18} | {p.primary_timeframe:<7} | {p.signals_per_day:<12.1f} | {p.positive_rate_pct:<9.1f}% | {p.status:<15}"
            )

        lines.append("=" * 60)
        lines.append("Note: Research observations only. Zero automated execution or guarantees.")
        return "\n".join(lines)
