import React, { useState } from 'react';
import { ShieldAlert, Compass, Activity, Layers, BarChart2, CheckCircle2, AlertTriangle, Lock, Eye, ArrowUpRight, ArrowDownRight, Info } from 'lucide-react';
import { useMarketStore } from '../../stores/marketStore';
import { DataQualityBadge } from '../indicators/DataQualityBadge';

export const SignalResearchPanel: React.FC = () => {
  const { symbol, timeframe, confirmedSignal, realtimeSignal, quality } = useMarketStore();
  const [viewMode, setViewMode] = useState<'confirmed' | 'realtime'>('confirmed');

  const activeSignal = viewMode === 'confirmed' ? confirmedSignal : (realtimeSignal || confirmedSignal);

  const getDirectionBadge = (dir?: string) => {
    switch (dir) {
      case 'LONG_SETUP':
        return <span className="bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 px-3 py-1 rounded font-bold text-sm tracking-wider flex items-center gap-1.5"><ArrowUpRight className="w-4 h-4" /> LONG SETUP</span>;
      case 'SHORT_SETUP':
        return <span className="bg-rose-500/20 text-rose-400 border border-rose-500/40 px-3 py-1 rounded font-bold text-sm tracking-wider flex items-center gap-1.5"><ArrowDownRight className="w-4 h-4" /> SHORT SETUP</span>;
      default:
        return <span className="bg-surface-elevated text-text-muted px-3 py-1 rounded font-bold text-sm tracking-wider">NEUTRAL / WAIT</span>;
    }
  };

  const getStrengthBadge = (str?: string) => {
    switch (str) {
      case 'VERY_STRONG':
        return <span className="text-xs px-2 py-0.5 rounded bg-accent-cyan/20 text-accent-cyan font-bold border border-accent-cyan/40">VERY STRONG</span>;
      case 'STRONG':
        return <span className="text-xs px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 font-bold border border-emerald-500/30">STRONG</span>;
      case 'MODERATE':
        return <span className="text-xs px-2 py-0.5 rounded bg-accent-gold/20 text-accent-gold font-medium border border-accent-gold/30">MODERATE</span>;
      case 'WEAK':
        return <span className="text-xs px-2 py-0.5 rounded bg-surface-elevated text-text-secondary">WEAK</span>;
      default:
        return <span className="text-xs px-2 py-0.5 rounded bg-surface-elevated text-text-muted">VERY WEAK</span>;
    }
  };

  const getStatusBadge = (st?: string) => {
    switch (st) {
      case 'VALID':
        return <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 font-bold">VALID</span>;
      case 'WAIT':
        return <span className="text-[10px] px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 font-bold">WAIT</span>;
      case 'INVALID_DATA':
        return <span className="text-[10px] px-2 py-0.5 rounded bg-rose-500/20 text-rose-400 font-bold">INVALID DATA</span>;
      default:
        return <span className="text-[10px] px-2 py-0.5 rounded bg-surface-elevated text-text-muted font-bold">{st || '--'}</span>;
    }
  };

  const getScoreColor = (score?: number) => {
    if (score == null) return 'text-text-muted';
    if (score >= 45) return 'text-emerald-400 font-bold';
    if (score <= -45) return 'text-rose-400 font-bold';
    return 'text-accent-gold font-semibold';
  };

  return (
    <div className="bg-surface-card rounded-lg border border-border flex flex-col overflow-hidden select-none font-mono">
      {/* Top Header Bar */}
      <div className="h-11 bg-surface px-4 flex flex-wrap items-center justify-between border-b border-border/80 gap-2">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 text-xs font-bold text-text-primary uppercase tracking-wider">
            <Activity className="w-4 h-4 text-accent-cyan" />
            <span>Crypto AI Research Engine</span>
          </div>
          <span className="text-[10px] text-text-muted bg-surface-elevated px-2 py-0.5 rounded border border-border-subtle">
            {symbol} · {timeframe}
          </span>
          <DataQualityBadge quality={quality} />
        </div>

        {/* View Mode Toggle */}
        <div className="flex items-center gap-1 bg-surface-card p-1 rounded border border-border-subtle">
          <button
            onClick={() => setViewMode('confirmed')}
            className={`flex items-center gap-1 px-2.5 py-1 text-[11px] font-medium rounded transition ${
              viewMode === 'confirmed'
                ? 'bg-accent-cyan text-black font-bold shadow-glow-cyan/30'
                : 'text-text-secondary hover:text-text-primary'
            }`}
          >
            <Lock className="w-3 h-3" />
            <span>Confirmed (Closed)</span>
          </button>

          <button
            onClick={() => setViewMode('realtime')}
            className={`flex items-center gap-1 px-2.5 py-1 text-[11px] font-medium rounded transition ${
              viewMode === 'realtime'
                ? 'bg-accent-gold text-black font-bold shadow-glow-cyan/30'
                : 'text-text-secondary hover:text-text-primary'
            }`}
          >
            <Eye className="w-3 h-3" />
            <span>Live Forming</span>
          </button>
        </div>
      </div>

      {/* Mandatory Research Disclaimer Banner */}
      <div className="bg-accent-gold/10 border-b border-accent-gold/20 px-4 py-1.5 flex items-center justify-between text-[11px] text-accent-gold">
        <div className="flex items-center gap-1.5">
          <Info className="w-3.5 h-3.5" />
          <span className="font-semibold">{activeSignal?.disclaimer || 'Research signal — not a guaranteed prediction.'}</span>
        </div>
        <span className="text-[10px] text-text-muted hidden sm:inline">Version {activeSignal?.engine_version || '0.5.0'}</span>
      </div>

      {/* Main Signal Status Row */}
      <div className="p-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 border-b border-border/60 bg-surface/30">
        <div className="bg-surface/60 p-3 rounded-lg border border-border/40 flex flex-col justify-between">
          <div className="text-[10px] text-text-muted">RESEARCH CLASSIFICATION</div>
          <div className="mt-2">{getDirectionBadge(activeSignal?.direction)}</div>
        </div>

        <div className="bg-surface/60 p-3 rounded-lg border border-border/40 flex flex-col justify-between">
          <div className="text-[10px] text-text-muted">SIGNAL STRENGTH & STATUS</div>
          <div className="mt-2 flex items-center gap-2">
            {getStrengthBadge(activeSignal?.strength)}
            {getStatusBadge(activeSignal?.status)}
          </div>
        </div>

        <div className="bg-surface/60 p-3 rounded-lg border border-border/40 flex flex-col justify-between">
          <div className="text-[10px] text-text-muted">NET DIRECTIONAL EVIDENCE</div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className={`text-xl ${getScoreColor(activeSignal?.score)}`}>
              {activeSignal?.score != null ? (activeSignal.score > 0 ? `+${activeSignal.score}` : activeSignal.score) : '--'}
            </span>
            <span className="text-text-muted text-[11px]">/ 100</span>
          </div>
        </div>

        <div className="bg-surface/60 p-3 rounded-lg border border-border/40 flex flex-col justify-between">
          <div className="text-[10px] text-text-muted">CONTEXTUAL QUALITY MODIFIERS</div>
          <div className="mt-2 flex items-center gap-3 text-xs">
            <div>
              <span className="text-text-muted text-[10px]">Regime: </span>
              <span className="text-accent-cyan font-bold">{activeSignal?.score_trace ? `${activeSignal.score_trace.regime_modifier}x` : '--'}</span>
            </div>
            <div>
              <span className="text-text-muted text-[10px]">Vol Mod: </span>
              <span className="text-purple-400 font-bold">{activeSignal?.score_trace ? `${activeSignal.score_trace.volatility_modifier}x` : '--'}</span>
            </div>
          </div>
        </div>
      </div>

      {/* 4-Factor Score Breakdown Grid */}
      <div className="p-4 grid grid-cols-2 sm:grid-cols-4 gap-3 border-b border-border/60">
        {/* Trend Group */}
        <div className="bg-surface/50 p-2.5 rounded border border-border-subtle">
          <div className="flex items-center justify-between text-[10px] text-text-muted">
            <span>TREND (30%)</span>
            <span className="text-text-primary font-bold">{activeSignal?.evidence_groups?.TREND?.state || '--'}</span>
          </div>
          <div className="mt-1 text-lg font-bold text-accent-cyan">
            {activeSignal?.evidence_groups?.TREND ? (activeSignal.evidence_groups.TREND.score > 0 ? `+${activeSignal.evidence_groups.TREND.score}` : activeSignal.evidence_groups.TREND.score) : '--'}
          </div>
        </div>

        {/* Momentum Group */}
        <div className="bg-surface/50 p-2.5 rounded border border-border-subtle">
          <div className="flex items-center justify-between text-[10px] text-text-muted">
            <span>MOMENTUM (20%)</span>
            <span className="text-text-primary font-bold">{activeSignal?.evidence_groups?.MOMENTUM?.state || '--'}</span>
          </div>
          <div className="mt-1 text-lg font-bold text-accent-gold">
            {activeSignal?.evidence_groups?.MOMENTUM ? (activeSignal.evidence_groups.MOMENTUM.score > 0 ? `+${activeSignal.evidence_groups.MOMENTUM.score}` : activeSignal.evidence_groups.MOMENTUM.score) : '--'}
          </div>
        </div>

        {/* Structure Group */}
        <div className="bg-surface/50 p-2.5 rounded border border-border-subtle">
          <div className="flex items-center justify-between text-[10px] text-text-muted">
            <span>STRUCTURE (35%)</span>
            <span className="text-text-primary font-bold">{activeSignal?.evidence_groups?.STRUCTURE?.state || '--'}</span>
          </div>
          <div className="mt-1 text-lg font-bold text-purple-400">
            {activeSignal?.evidence_groups?.STRUCTURE ? (activeSignal.evidence_groups.STRUCTURE.score > 0 ? `+${activeSignal.evidence_groups.STRUCTURE.score}` : activeSignal.evidence_groups.STRUCTURE.score) : '--'}
          </div>
        </div>

        {/* Volume Group */}
        <div className="bg-surface/50 p-2.5 rounded border border-border-subtle">
          <div className="flex items-center justify-between text-[10px] text-text-muted">
            <span>VOLUME (15%)</span>
            <span className="text-text-primary font-bold">{activeSignal?.evidence_groups?.VOLUME?.state || '--'}</span>
          </div>
          <div className="mt-1 text-lg font-bold text-emerald-400">
            {activeSignal?.evidence_groups?.VOLUME ? (activeSignal.evidence_groups.VOLUME.score > 0 ? `+${activeSignal.evidence_groups.VOLUME.score}` : activeSignal.evidence_groups.VOLUME.score) : '--'}
          </div>
        </div>
      </div>

      {/* Score Trace Reconstruction Bar */}
      {activeSignal?.score_trace && (
        <div className="bg-surface/30 px-4 py-2 border-b border-border/40 flex flex-wrap items-center justify-between text-[11px] text-text-muted gap-2">
          <div className="flex items-center gap-1.5 flex-wrap">
            <span className="text-text-secondary font-bold">Calculation Trace:</span>
            <span>Base ({activeSignal.score_trace.base_directional_score})</span>
            <span>×</span>
            <span>Regime ({activeSignal.score_trace.regime_modifier})</span>
            <span>×</span>
            <span>Vol ({activeSignal.score_trace.volatility_modifier})</span>
            <span>=</span>
            <span>Adj ({activeSignal.score_trace.context_adjusted_score})</span>
            <span>-</span>
            <span>Penalties ({activeSignal.score_trace.total_conflict_penalty})</span>
            <span>=</span>
            <span className="text-text-primary font-bold">{activeSignal.score_trace.net_score} Net</span>
          </div>
        </div>
      )}

      {/* Evidence and Contradictions Columns */}
      <div className="p-4 grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Supporting Evidence */}
        <div className="bg-surface/40 p-3 rounded-lg border border-border-subtle">
          <div className="flex items-center gap-1.5 text-xs font-bold text-emerald-400 uppercase tracking-wider mb-2.5">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
            <span>Supporting Deterministic Evidence ({activeSignal?.supporting_evidence?.length || 0})</span>
          </div>

          <div className="space-y-1.5 text-[11px] max-h-48 overflow-y-auto">
            {activeSignal && activeSignal.supporting_evidence?.length > 0 ? (
              activeSignal.supporting_evidence.map((ev, i) => (
                <div key={i} className="flex items-start gap-2 p-1.5 rounded bg-surface-elevated/40 border border-border/20">
                  <span className="text-emerald-400 font-bold">✓</span>
                  <span className="text-text-primary">{ev}</span>
                </div>
              ))
            ) : (
              <div className="text-text-muted py-2">No active directional supporting evidence.</div>
            )}
          </div>
        </div>

        {/* Contradictions & Conflicts */}
        <div className="bg-surface/40 p-3 rounded-lg border border-border-subtle">
          <div className="flex items-center gap-1.5 text-xs font-bold text-amber-400 uppercase tracking-wider mb-2.5">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
            <span>Conflicts & Contradictions ({activeSignal?.conflicts?.length || 0})</span>
          </div>

          <div className="space-y-1.5 text-[11px] max-h-48 overflow-y-auto">
            {activeSignal && activeSignal.conflicts?.length > 0 ? (
              activeSignal.conflicts.map((c, i) => (
                <div key={i} className="flex items-start justify-between gap-2 p-1.5 rounded bg-amber-500/5 border border-amber-500/20">
                  <div className="flex items-start gap-1.5">
                    <span className="text-[9px] px-1 rounded bg-amber-500/10 text-amber-400 font-bold border border-amber-500/20">
                      {c.severity}
                    </span>
                    <span className="text-amber-300">{c.explanation}</span>
                  </div>
                  <span className="text-rose-400 text-[10px] whitespace-nowrap">-{c.applied_penalty} pts</span>
                </div>
              ))
            ) : (
              <div className="text-text-muted py-2">No active structural contradictions or proximity penalties.</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
