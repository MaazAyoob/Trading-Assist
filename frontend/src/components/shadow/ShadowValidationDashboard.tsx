import React, { useEffect, useState } from 'react';
import {
  Shield,
  ShieldCheck,
  ShieldAlert,
  Play,
  Pause,
  Square,
  RefreshCw,
  Layers,
  TrendingUp,
  Radio,
  Zap,
  Clock,
  Compass,
  AlertTriangle,
} from 'lucide-react';
import {
  ShadowSession,
  ShadowSignal,
  CandidateLiveMetrics,
  DriftMetricComparison,
} from '../../types/shadow';
import {
  fetchShadowStatus,
  fetchShadowSessions,
  startShadowSession,
  pauseShadowSession,
  resumeShadowSession,
  stopShadowSession,
  fetchShadowSignals,
  fetchShadowDrift,
} from '../../services/api';
import { ConnectionHealth } from './ConnectionHealth';
import { LiveCandidateStatus } from './LiveCandidateStatus';
import { ShadowSignalFeed } from './ShadowSignalFeed';
import { LiveOutcomeTracker } from './LiveOutcomeTracker';
import { CandidateComparison } from './CandidateComparison';

export const ShadowValidationDashboard: React.FC = () => {
  const [activeSession, setActiveSession] = useState<ShadowSession | null>(null);
  const [sessionsList, setSessionsList] = useState<ShadowSession[]>([]);
  const [signals, setSignals] = useState<ShadowSignal[]>([]);
  const [driftReport, setDriftReport] = useState<Record<string, DriftMetricComparison[]>>({});
  const [selectedCandidate, setSelectedCandidate] = useState<string>('EXP_A2_PULLBACK_VWAP');
  const [activeSubTab, setActiveSubTab] = useState<'feed' | 'outcomes' | 'comparison' | 'drift'>('feed');
  const [loading, setLoading] = useState<boolean>(true);
  const [actionLoading, setActionLoading] = useState<boolean>(false);

  useEffect(() => {
    loadDashboard();
    const interval = setInterval(loadDashboard, 15000);
    return () => clearInterval(interval);
  }, []);

  const loadDashboard = async () => {
    try {
      const sessList = await fetchShadowSessions();
      setSessionsList(sessList);

      const active = sessList.find((s) => s.status === 'RUNNING' || s.status === 'PAUSED');
      if (active) {
        setActiveSession(active);
        const sigs = await fetchShadowSignals(active.session_id);
        setSignals(sigs);
        const drift = await fetchShadowDrift(active.session_id);
        setDriftReport(drift);
      } else if (sessList.length > 0) {
        // Show most recent stopped session
        setActiveSession(sessList[0]);
        const sigs = await fetchShadowSignals(sessList[0].session_id);
        setSignals(sigs);
        const drift = await fetchShadowDrift(sessList[0].session_id);
        setDriftReport(drift);
      }
    } catch (e) {
      console.error('Failed to load shadow dashboard:', e);
    } finally {
      setLoading(false);
    }
  };

  const handleStart = async () => {
    setActionLoading(true);
    try {
      await startShadowSession('BTCUSDT', '15m');
      await loadDashboard();
    } catch (e) {
      console.error('Failed to start session:', e);
    } finally {
      setActionLoading(false);
    }
  };

  const handlePause = async () => {
    if (!activeSession) return;
    setActionLoading(true);
    try {
      await pauseShadowSession(activeSession.session_id);
      await loadDashboard();
    } catch (e) {
      console.error('Failed to pause session:', e);
    } finally {
      setActionLoading(false);
    }
  };

  const handleResume = async () => {
    if (!activeSession) return;
    setActionLoading(true);
    try {
      await resumeShadowSession(activeSession.session_id);
      await loadDashboard();
    } catch (e) {
      console.error('Failed to resume session:', e);
    } finally {
      setActionLoading(false);
    }
  };

  const handleStop = async () => {
    if (!activeSession) return;
    setActionLoading(true);
    try {
      await stopShadowSession(activeSession.session_id);
      await loadDashboard();
    } catch (e) {
      console.error('Failed to stop session:', e);
    } finally {
      setActionLoading(false);
    }
  };

  if (loading && !activeSession) {
    return (
      <div className="p-12 flex flex-col items-center justify-center gap-3 text-text-muted">
        <RefreshCw className="w-6 h-6 animate-spin text-accent-cyan" />
        <span className="font-mono text-xs">Connecting to Phase 9 Real-Time Shadow Engine...</span>
      </div>
    );
  }

  const currentMetrics = activeSession?.candidates_metrics || {};
  const activeMetrics = currentMetrics[selectedCandidate] || currentMetrics['EXP_A2_PULLBACK_VWAP'] || Object.values(currentMetrics)[0];

  return (
    <div className="flex flex-col gap-4 font-mono text-xs text-text-secondary pb-6 select-none">
      {/* Safety & Anti-Execution Notice */}
      <div className="p-3 bg-rose-950/20 border border-rose-500/40 rounded-lg flex items-start gap-2.5">
        <ShieldAlert className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
        <div className="text-rose-200/90 leading-relaxed text-[11px]">
          <span className="font-bold text-rose-300">SHADOW VALIDATION ONLY — NO REAL ORDERS ARE BEING PLACED.</span> Zero execution, no exchange trading keys required. Historical and live forward returns are empirical research measurements, not guaranteed predictions.
        </div>
      </div>

      {/* Session Controls & Provenance Header */}
      <div className="p-3 bg-surface rounded-lg border border-border flex flex-col md:flex-row md:items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <Radio className="w-4 h-4 text-accent-cyan animate-pulse shrink-0" />
          <div>
            <div className="text-text-primary font-bold text-xs flex items-center gap-2">
              <span>Session: {activeSession?.session_id || 'NO_ACTIVE_SESSION'}</span>
              <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                activeSession?.status === 'RUNNING' ? 'bg-emerald-950 text-emerald-300 border border-emerald-500/40' :
                activeSession?.status === 'PAUSED' ? 'bg-amber-950 text-amber-300 border border-amber-500/40' :
                'bg-surface-elevated text-text-muted border border-border'
              }`}>
                {activeSession?.status || 'INACTIVE'}
              </span>
            </div>
            <div className="text-[10px] text-text-muted mt-0.5">
              Provider: {activeSession?.market_data_provider || 'Binance WS'} | Symbol: {activeSession?.symbol || 'BTCUSDT'} ({activeSession?.timeframe || '15m'})
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2">
          {(!activeSession || activeSession.status === 'STOPPED') && (
            <button
              onClick={handleStart}
              disabled={actionLoading}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded text-xs transition"
            >
              <Play className="w-3.5 h-3.5" />
              <span>Start Validation Session</span>
            </button>
          )}

          {activeSession?.status === 'RUNNING' && (
            <>
              <button
                onClick={handlePause}
                disabled={actionLoading}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-amber-600 hover:bg-amber-500 text-white font-bold rounded text-xs transition"
              >
                <Pause className="w-3.5 h-3.5" />
                <span>Pause</span>
              </button>
              <button
                onClick={handleStop}
                disabled={actionLoading}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-rose-600 hover:bg-rose-500 text-white font-bold rounded text-xs transition"
              >
                <Square className="w-3.5 h-3.5" />
                <span>Stop & Export</span>
              </button>
            </>
          )}

          {activeSession?.status === 'PAUSED' && (
            <>
              <button
                onClick={handleResume}
                disabled={actionLoading}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded text-xs transition"
              >
                <Play className="w-3.5 h-3.5" />
                <span>Resume</span>
              </button>
              <button
                onClick={handleStop}
                disabled={actionLoading}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-rose-600 hover:bg-rose-500 text-white font-bold rounded text-xs transition"
              >
                <Square className="w-3.5 h-3.5" />
                <span>Stop & Export</span>
              </button>
            </>
          )}
        </div>
      </div>

      {/* Connection & Telemetry Status */}
      <ConnectionHealth session={activeSession} />

      {/* 3-Candidate Live Overview Cards */}
      <LiveCandidateStatus
        metrics={currentMetrics}
        selectedCandidate={selectedCandidate}
        onSelectCandidate={setSelectedCandidate}
      />

      {/* Sub-Tabs Navigation */}
      <div className="flex items-center gap-1 border-b border-border/80 pb-1">
        <button
          onClick={() => setActiveSubTab('feed')}
          className={`px-3 py-1 rounded text-xs transition ${activeSubTab === 'feed' ? 'bg-surface-elevated text-accent-cyan font-bold border border-accent-cyan/40' : 'text-text-muted hover:text-text-primary'}`}
        >
          Live Signal Feed ({signals.length})
        </button>
        <button
          onClick={() => setActiveSubTab('outcomes')}
          className={`px-3 py-1 rounded text-xs transition ${activeSubTab === 'outcomes' ? 'bg-surface-elevated text-accent-cyan font-bold border border-accent-cyan/40' : 'text-text-muted hover:text-text-primary'}`}
        >
          Forward Outcomes Tracker
        </button>
        <button
          onClick={() => setActiveSubTab('comparison')}
          className={`px-3 py-1 rounded text-xs transition ${activeSubTab === 'comparison' ? 'bg-surface-elevated text-accent-cyan font-bold border border-accent-cyan/40' : 'text-text-muted hover:text-text-primary'}`}
        >
          Baseline vs Candidate Comparison
        </button>
        <button
          onClick={() => setActiveSubTab('drift')}
          className={`px-3 py-1 rounded text-xs transition ${activeSubTab === 'drift' ? 'bg-surface-elevated text-accent-cyan font-bold border border-accent-cyan/40' : 'text-text-muted hover:text-text-primary'}`}
        >
          Historical vs Live Drift
        </button>
      </div>

      {/* Sub-Tab 1: Live Signal Feed */}
      {activeSubTab === 'feed' && (
        <ShadowSignalFeed signals={signals} selectedCandidate={selectedCandidate} />
      )}

      {/* Sub-Tab 2: Forward Outcomes Tracker */}
      {activeSubTab === 'outcomes' && activeMetrics && (
        <LiveOutcomeTracker metrics={activeMetrics} />
      )}

      {/* Sub-Tab 3: Candidate Comparison */}
      {activeSubTab === 'comparison' && (
        <CandidateComparison metrics={currentMetrics} />
      )}

      {/* Sub-Tab 4: Historical vs Live Drift */}
      {activeSubTab === 'drift' && (
        <div className="flex flex-col gap-3 bg-surface p-4 rounded-lg border border-border">
          <div className="flex items-center justify-between border-b border-border/60 pb-2">
            <span className="font-bold text-text-primary flex items-center gap-1.5 text-xs">
              <Compass className="w-3.5 h-3.5 text-purple-400" />
              <span>Observational Drift Monitoring ({selectedCandidate})</span>
            </span>
            <span className="text-[10px] text-text-muted">
              Live vs Phase 8 Validation & Untouched Test
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-[11px] font-mono">
              <thead>
                <tr className="border-b border-border/80 text-text-muted">
                  <th className="pb-1.5">Metric</th>
                  <th className="pb-1.5">Hist. Validation</th>
                  <th className="pb-1.5">Hist. Test</th>
                  <th className="pb-1.5">Live Observed</th>
                  <th className="pb-1.5">Drift Delta</th>
                  <th className="pb-1.5 text-center">Drift Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/40">
                {(driftReport[selectedCandidate] || []).map((d) => (
                  <tr key={d.metric_name} className="py-2">
                    <td className="py-2 font-bold text-text-primary">{d.metric_name}</td>
                    <td className="py-2 font-mono text-text-muted">
                      {d.metric_name.includes('%') ? `${d.historical_validation.toFixed(1)}%` : `${(d.historical_validation * 100).toFixed(3)}%`}
                    </td>
                    <td className="py-2 font-mono text-text-muted">
                      {d.metric_name.includes('%') ? `${d.historical_test.toFixed(1)}%` : `${(d.historical_test * 100).toFixed(3)}%`}
                    </td>
                    <td className="py-2 font-mono font-bold text-text-primary">
                      {d.metric_name.includes('%') ? `${d.live_observed.toFixed(1)}%` : `${(d.live_observed * 100).toFixed(3)}%`}
                    </td>
                    <td className="py-2 font-mono text-accent-cyan">
                      {d.metric_name.includes('%')
                        ? `${d.drift_delta >= 0 ? '+' : ''}${d.drift_delta.toFixed(1)}%`
                        : `${d.drift_delta >= 0 ? '+' : ''}${(d.drift_delta * 100).toFixed(3)}%`}
                    </td>
                    <td className="py-2 text-center font-bold">
                      <span className={`px-2 py-0.5 rounded text-[10px] ${
                        d.drift_status === 'ALIGNED' ? 'bg-emerald-950 text-emerald-300 border border-emerald-500/40' :
                        d.drift_status === 'MILD_DRIFT' ? 'bg-amber-950 text-amber-300 border border-amber-500/40' :
                        d.drift_status === 'SIGNIFICANT_DRIFT' ? 'bg-rose-950 text-rose-300 border border-rose-500/40' :
                        'bg-surface-elevated text-text-muted'
                      }`}>
                        {d.drift_status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
