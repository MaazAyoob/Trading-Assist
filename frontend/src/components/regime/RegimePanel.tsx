import React, { useState } from 'react';
import { Compass, CheckCircle2, AlertTriangle, ShieldAlert, Lock, Eye } from 'lucide-react';
import { useMarketStore } from '../../stores/marketStore';
import { DataQualityBadge } from '../indicators/DataQualityBadge';

export const RegimePanel: React.FC = () => {
  const { symbol, timeframe, confirmedRegime, realtimeRegime, quality } = useMarketStore();
  const [viewMode, setViewMode] = useState<'confirmed' | 'realtime'>('confirmed');

  const activeRegime = viewMode === 'confirmed' ? confirmedRegime : (realtimeRegime || confirmedRegime);

  const getDirectionBadge = (dir?: string) => {
    switch (dir) {
      case 'BULLISH':
        return <span className="bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 px-2 py-0.5 rounded font-bold">▲ BULLISH</span>;
      case 'BEARISH':
        return <span className="bg-rose-500/20 text-rose-400 border border-rose-500/40 px-2 py-0.5 rounded font-bold">▼ BEARISH</span>;
      case 'RANGE':
        return <span className="bg-blue-500/20 text-blue-400 border border-blue-500/40 px-2 py-0.5 rounded font-bold">↔ RANGE</span>;
      default:
        return <span className="bg-surface-elevated text-text-muted px-2 py-0.5 rounded font-bold">UNCERTAIN</span>;
    }
  };

  const getTrendStrengthColor = (str?: string) => {
    switch (str) {
      case 'VERY_STRONG':
      case 'STRONG':
        return 'text-accent-cyan font-bold';
      case 'MODERATE':
        return 'text-accent-gold font-semibold';
      case 'WEAK':
        return 'text-text-secondary';
      default:
        return 'text-text-muted';
    }
  };

  const getVolColor = (vol?: string) => {
    switch (vol) {
      case 'EXTREME':
        return 'text-rose-400 font-bold';
      case 'HIGH':
        return 'text-amber-400 font-semibold';
      case 'NORMAL':
        return 'text-emerald-400 font-semibold';
      default:
        return 'text-blue-400';
    }
  };

  return (
    <div className="bg-surface-card rounded-lg border border-border flex flex-col overflow-hidden select-none font-mono">
      {/* Header Bar */}
      <div className="h-11 bg-surface px-4 flex flex-wrap items-center justify-between border-b border-border/80 gap-2">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 text-xs font-bold text-text-primary uppercase tracking-wider">
            <Compass className="w-4 h-4 text-accent-cyan" />
            <span>Market Regime Environment</span>
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

      {/* Snapshot Metadata Subheader */}
      <div className="bg-surface/40 px-4 py-1.5 border-b border-border/40 flex items-center justify-between text-[11px] text-text-muted">
        <div>
          <span>Regime Environment: </span>
          <span className="text-text-primary font-bold">{activeRegime?.overall_regime || 'INITIALIZING'}</span>
        </div>
        <div>
          <span>Evidence Agreement: </span>
          <span className="text-accent-cyan font-bold">{activeRegime?.evidence_strength || 0}%</span>
          <span className="text-text-muted text-[10px] ml-1">(Rule consistency, non-predictive)</span>
        </div>
      </div>

      {/* Dimensional Attribute Grid */}
      <div className="p-4 grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 border-b border-border/60">
        <div className="bg-surface/60 p-2.5 rounded border border-border/40">
          <div className="text-[10px] text-text-muted">DIRECTION</div>
          <div className="mt-1">{getDirectionBadge(activeRegime?.direction)}</div>
        </div>

        <div className="bg-surface/60 p-2.5 rounded border border-border/40">
          <div className="text-[10px] text-text-muted">TREND STRENGTH</div>
          <div className={`mt-1 text-xs ${getTrendStrengthColor(activeRegime?.trend_strength)}`}>
            {activeRegime?.trend_strength || '--'}
          </div>
        </div>

        <div className="bg-surface/60 p-2.5 rounded border border-border/40">
          <div className="text-[10px] text-text-muted">VOLATILITY REGIME</div>
          <div className={`mt-1 text-xs ${getVolColor(activeRegime?.volatility_state)}`}>
            {activeRegime?.volatility_state || '--'}
          </div>
        </div>

        <div className="bg-surface/60 p-2.5 rounded border border-border/40">
          <div className="text-[10px] text-text-muted">MOMENTUM STATE</div>
          <div className="mt-1 text-xs text-text-primary font-semibold">
            {activeRegime?.momentum_state || '--'}
          </div>
        </div>

        <div className="bg-surface/60 p-2.5 rounded border border-border/40">
          <div className="text-[10px] text-text-muted">VOLUME STATE</div>
          <div className="mt-1 text-xs text-accent-gold font-semibold">
            {activeRegime?.volume_state || '--'}
          </div>
        </div>

        <div className="bg-surface/60 p-2.5 rounded border border-border/40">
          <div className="text-[10px] text-text-muted">PRICE STRUCTURE</div>
          <div className="mt-1 text-xs text-purple-400 font-semibold">
            {activeRegime?.structure_state || '--'}
          </div>
        </div>
      </div>

      {/* Evidence & Contradictions Breakdown */}
      <div className="p-4 grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Supporting Evidence */}
        <div className="bg-surface/40 p-3 rounded-lg border border-border-subtle">
          <div className="flex items-center gap-1.5 text-xs font-bold text-emerald-400 uppercase tracking-wider mb-2.5">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
            <span>Supporting Deterministic Evidence ({activeRegime?.evidence.length || 0})</span>
          </div>

          <div className="space-y-1.5 text-[11px] max-h-48 overflow-y-auto">
            {activeRegime && activeRegime.evidence.length > 0 ? (
              activeRegime.evidence.map((ev, i) => (
                <div key={i} className="flex items-start justify-between gap-2 p-1.5 rounded bg-surface-elevated/40 border border-border/20">
                  <div className="flex items-center gap-1.5">
                    <span className="text-[9px] px-1 rounded bg-emerald-500/10 text-emerald-400 font-bold border border-emerald-500/20">
                      {ev.category}
                    </span>
                    <span className="text-text-primary">{ev.description}</span>
                  </div>
                  {ev.metric_value && (
                    <span className="text-text-muted text-[10px] whitespace-nowrap">{ev.metric_value}</span>
                  )}
                </div>
              ))
            ) : (
              <div className="text-text-muted py-2">No active supporting evidence.</div>
            )}
          </div>
        </div>

        {/* Contradictions & Warnings */}
        <div className="bg-surface/40 p-3 rounded-lg border border-border-subtle">
          <div className="flex items-center gap-1.5 text-xs font-bold text-amber-400 uppercase tracking-wider mb-2.5">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
            <span>Structural Contradictions & Warnings ({activeRegime?.contradictions.length || 0})</span>
          </div>

          <div className="space-y-1.5 text-[11px] max-h-48 overflow-y-auto">
            {activeRegime && activeRegime.contradictions.length > 0 ? (
              activeRegime.contradictions.map((ct, i) => (
                <div key={i} className="flex items-start justify-between gap-2 p-1.5 rounded bg-amber-500/5 border border-amber-500/20">
                  <div className="flex items-center gap-1.5">
                    <span className="text-[9px] px-1 rounded bg-amber-500/10 text-amber-400 font-bold border border-amber-500/20">
                      {ct.category}
                    </span>
                    <span className="text-amber-300">{ct.description}</span>
                  </div>
                  {ct.metric_value && (
                    <span className="text-text-muted text-[10px] whitespace-nowrap">{ct.metric_value}</span>
                  )}
                </div>
              ))
            ) : (
              <div className="text-text-muted py-2">No active structural contradictions. Clean alignment.</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
