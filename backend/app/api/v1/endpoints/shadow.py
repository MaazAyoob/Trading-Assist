"""
Phase 9 — Shadow Validation REST API Endpoints.
Provides control, telemetry, metrics, and drift analysis for shadow validation sessions.
"""

from typing import List, Dict, Optional, Any
from fastapi import APIRouter, HTTPException, Query

from app.shadow_validation.models import (
    ShadowSession,
    ShadowSignal,
    CandidateLiveMetrics,
    DriftMetricComparison,
    SessionStatusEnum,
)
from app.shadow_validation.registry import ShadowRegistry
from app.shadow_validation.drift import DriftMonitor
from app.shadow_validation.alerts import ShadowAlertBus, ShadowAlert
from app.shadow_validation.config import CANDIDATES

router = APIRouter()


@router.get("/status")
def get_shadow_status():
    """Returns active session status, provenance, and configuration hashes."""
    ShadowRegistry.initialize()
    active = ShadowRegistry.get_active_session()
    return {
        "active_session_id": active.session_id if active else None,
        "is_running": (active.status == SessionStatusEnum.RUNNING) if active else False,
        "session_status": active.status.value if active else "NO_ACTIVE_SESSION",
        "symbol": active.symbol if active else "BTCUSDT",
        "timeframe": active.timeframe if active else "15m",
        "candles_processed": active.candles_processed_count if active else 0,
        "configuration_hashes": active.configuration_hashes if active else {},
    }


@router.get("/sessions", response_model=List[ShadowSession])
def list_shadow_sessions():
    """Returns a list of all historical and active shadow validation sessions."""
    ShadowRegistry.initialize()
    return ShadowRegistry.list_all_sessions()


@router.post("/sessions/start", response_model=ShadowSession)
def start_shadow_session(
    symbol: str = Query("BTCUSDT", description="Market symbol"),
    timeframe: str = Query("15m", description="Candle timeframe"),
):
    """Starts a new real-time shadow validation session."""
    ShadowRegistry.initialize()
    session = ShadowRegistry.start_session(symbol=symbol, timeframe=timeframe)
    ShadowAlertBus.emit_alert(
        session_id=session.session_id,
        alert_type="SESSION_STARTED",
        title="Shadow Session Started",
        message=f"Started shadow validation session for {symbol} {timeframe}.",
        severity="INFO",
    )
    return session


@router.post("/sessions/{session_id}/pause", response_model=ShadowSession)
def pause_shadow_session(session_id: str):
    """Pauses an active shadow validation session."""
    sess = ShadowRegistry.pause_session(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail=f"Active session '{session_id}' not found.")
    ShadowAlertBus.emit_alert(
        session_id=session_id,
        alert_type="SESSION_PAUSED",
        title="Shadow Session Paused",
        message=f"Session {session_id} has been paused.",
        severity="WARNING",
    )
    return sess


@router.post("/sessions/{session_id}/resume", response_model=ShadowSession)
def resume_shadow_session(session_id: str):
    """Resumes a paused shadow validation session."""
    sess = ShadowRegistry.resume_session(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail=f"Paused session '{session_id}' not found.")
    ShadowAlertBus.emit_alert(
        session_id=session_id,
        alert_type="SESSION_RESUMED",
        title="Shadow Session Resumed",
        message=f"Session {session_id} has resumed processing.",
        severity="INFO",
    )
    return sess


@router.post("/sessions/{session_id}/stop", response_model=ShadowSession)
def stop_shadow_session(session_id: str):
    """Stops an active session, finalizes horizons, and exports immutable research artifacts."""
    sess = ShadowRegistry.stop_session(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")
    ShadowAlertBus.emit_alert(
        session_id=session_id,
        alert_type="SESSION_STOPPED",
        title="Shadow Session Concluded",
        message=f"Session {session_id} finalized and exported.",
        severity="INFO",
    )
    return sess


@router.get("/sessions/{session_id}", response_model=ShadowSession)
def get_shadow_session_detail(session_id: str):
    """Returns metadata and candidate metrics for a specific session."""
    sess = ShadowRegistry.load_session(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")
    return sess


@router.get("/sessions/{session_id}/signals", response_model=List[ShadowSignal])
def get_session_signals(
    session_id: str,
    candidate_id: Optional[str] = Query(None, description="Filter by candidate ID"),
    limit: int = Query(200, description="Max signals to return"),
):
    """Returns recorded shadow signal snapshots for a session."""
    signals = ShadowRegistry.get_signals(session_id)
    if candidate_id:
        signals = [s for s in signals if s.candidate_id == candidate_id]
    return signals[-limit:]


@router.get("/sessions/{session_id}/metrics", response_model=Dict[str, CandidateLiveMetrics])
def get_session_metrics(session_id: str):
    """Returns live aggregated statistical metrics for Baseline, A2, and E2."""
    sess = ShadowRegistry.load_session(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")
    return sess.candidates_metrics


@router.get("/sessions/{session_id}/drift", response_model=Dict[str, List[DriftMetricComparison]])
def get_session_drift(session_id: str):
    """Returns observational drift metrics comparing live behavior to Phase 8 historical expectations."""
    sess = ShadowRegistry.load_session(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")

    drift_report = {}
    for c_id, metrics in sess.candidates_metrics.items():
        drift_report[c_id] = DriftMonitor.evaluate_candidate_drift(metrics)
    return drift_report


@router.get("/alerts", response_model=List[ShadowAlert])
def get_shadow_alerts(
    session_id: Optional[str] = Query(None, description="Filter by session ID"),
    limit: int = Query(50, description="Max alerts to retrieve"),
):
    """Returns recent observational notifications from the shadow alert bus."""
    return ShadowAlertBus.get_recent_alerts(session_id=session_id, limit=limit)
