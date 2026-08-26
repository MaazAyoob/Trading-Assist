"""
Phase 9 — Local Shadow Alert Bus.
Dispatches observational notifications for shadow signal events and data quality warnings.
"""

from typing import List, Dict, Optional
import time
from pydantic import BaseModel, Field


class ShadowAlert(BaseModel):
    alert_id: str
    session_id: str
    timestamp: int
    alert_type: str  # "SIGNAL_GENERATED", "OUTCOME_COMPLETED", "DATA_QUALITY_WARNING", "CONNECTION_WARNING"
    candidate_id: Optional[str] = None
    severity: str = "INFO"  # "INFO", "WARNING", "CRITICAL"
    title: str
    message: str


class ShadowAlertBus:
    """
    In-memory FIFO alert event bus for active shadow validation sessions.
    """
    _ALERTS: List[ShadowAlert] = []
    MAX_ALERTS = 200

    @classmethod
    def emit_alert(
        cls,
        session_id: str,
        alert_type: str,
        title: str,
        message: str,
        candidate_id: Optional[str] = None,
        severity: str = "INFO",
    ):
        alert = ShadowAlert(
            alert_id=f"ALT_{int(time.time() * 1000)}_{len(cls._ALERTS)}",
            session_id=session_id,
            timestamp=int(time.time() * 1000),
            alert_type=alert_type,
            candidate_id=candidate_id,
            severity=severity,
            title=title,
            message=message,
        )
        cls._ALERTS.append(alert)
        if len(cls._ALERTS) > cls.MAX_ALERTS:
            cls._ALERTS.pop(0)

    @classmethod
    def get_recent_alerts(cls, session_id: Optional[str] = None, limit: int = 50) -> List[ShadowAlert]:
        if session_id:
            filtered = [a for a in cls._ALERTS if a.session_id == session_id]
            return filtered[-limit:]
        return cls._ALERTS[-limit:]
