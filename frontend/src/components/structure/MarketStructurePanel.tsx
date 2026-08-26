import React, { useState } from 'react';
import { GitBranch, Layers, ArrowUpRight, ArrowDownRight, Shield, Activity, Lock, Eye } from 'lucide-react';
import { useMarketStore } from '../../stores/marketStore';
import { DataQualityBadge } from '../indicators/DataQualityBadge';

export const MarketStructurePanel: React.FC = () => {
  const { symbol, timeframe, confirmedStructure, realtimeStructure, quality } = useMarketStore();
  const [viewMode, setViewMode] = useState<'confirmed' | 'realtime'>('confirmed');

  const activeStruct = viewMode === 'confirmed' ? confirmedStructure : (realtimeStructure || confirmedStructure);

  const getBreakQualityBadge = (q: string) => {
    switch (q) {
      case 'STRONG_BREAK':
        return <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-400 font-bold border border-emerald-500/30">STRONG</span>;
      case 'WEAK_BREAK':
        return <span className="text-[10px] px-1.5 py-0.5 rounded bg-rose-500/20 text-rose-400 font-medium border border-rose-500/30">WEAK</span>;
      default:
        return <span className="text-[10px] px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-400 font-medium border border-blue-500/30">NORMAL</span>;
    }
  };

  const getStrengthBadge = (str: string) => {
    switch (str) {
      case 'STRONG':
        return <span className="text-[10px] px-1.5 py-0.5 rounded bg-purple-500/20 text-purple-300 font-bold border border-purple-500/30">STRONG (3+)</span>;
      case 'MODERATE':
        return <span className="text-[10px] px-1.5 py-0.5 rounded bg-accent-gold/20 text-accent-gold font-medium border border-accent-gold/30">MODERATE (2)</span>;
      default:
        return <span className="text-[10px] px-1.5 py-0.5 rounded bg-surface-elevated text-text-muted font-medium">WEAK (1)</span>;
    }
  };

  const getStatusBadge = (st: string) => {
    switch (st) {
      case 'ACTIVE':
        return <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 font-semibold">ACTIVE</span>;
      case 'TESTED':
        return <span className="text-[10px] px-1.5 py-0.5 rounded bg-accent-cyan/10 text-accent-cyan font-semibold">TESTED</span>;
      case 'BROKEN':
        return <span className="text-[10px] px-1.5 py-0.5 rounded bg-rose-500/10 text-rose-400 font-semibold">BROKEN</span>;
      default:
        return <span className="text-[10px] px-1.5 py-0.5 rounded bg-surface-elevated text-text-muted font-semibold">{st}</span>;
    }
  };

  return (
    <div className="bg-surface-card rounded-lg border border-border flex flex-col overflow-hidden select-none font-mono">
      {/* Header Bar */}
      <div className="h-11 bg-surface px-4 flex flex-wrap items-center justify-between border-b border-border/80 gap-2">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 text-xs font-bold text-text-primary uppercase tracking-wider">
            <GitBranch className="w-4 h-4 text-purple-400" />
            <span>Market Price Action Structure Engine</span>
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
                ? 'bg-purple-500 text-white font-bold shadow-glow-cyan/30'
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
            <span>Live Developing</span>
          </button>
        </div>
      </div>

      {/* Structural Metric Cards */}
      <div className="p-4 grid grid-cols-2 sm:grid-cols-4 gap-3 border-b border-border/60">
        <div className="bg-surface/60 p-2.5 rounded border border-border/40">
          <div className="text-[10px] text-text-muted">STRUCTURAL TREND</div>
          <div className="mt-1 text-xs text-accent-cyan font-bold">
            {activeStruct?.structure_direction || 'UNKNOWN'}
          </div>
        </div>

        <div className="bg-surface/60 p-2.5 rounded border border-border/40">
          <div className="text-[10px] text-text-muted">ACTIVE SWING HIGH</div>
          <div className="mt-1 text-xs text-emerald-400 font-semibold">
            {activeStruct?.active_structural_high ? `$${activeStruct.active_structural_high.price.toLocaleString('en-US')}` : '--'}
          </div>
        </div>

        <div className="bg-surface/60 p-2.5 rounded border border-border/40">
          <div className="text-[10px] text-text-muted">ACTIVE SWING LOW</div>
          <div className="mt-1 text-xs text-rose-400 font-semibold">
            {activeStruct?.active_structural_low ? `$${activeStruct.active_structural_low.price.toLocaleString('en-US')}` : '--'}
          </div>
        </div>

        <div className="bg-surface/60 p-2.5 rounded border border-border/40">
          <div className="text-[10px] text-text-muted">SWINGS TRACKED</div>
          <div className="mt-1 text-xs text-text-primary">
            <span className="font-bold text-accent-gold">{activeStruct?.confirmed_swings.length || 0} Confirmed</span>
            {viewMode === 'realtime' && (
              <span className="text-text-muted text-[10px] ml-1">({activeStruct?.developing_swings.length || 0} Dev)</span>
            )}
          </div>
        </div>
      </div>

      {/* Events and Levels Columns */}
      <div className="p-4 grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Structural Break Events (BOS & CHoCH) */}
        <div className="bg-surface/40 p-3 rounded-lg border border-border-subtle">
          <div className="flex items-center justify-between mb-2.5 border-b border-border/60 pb-1.5">
            <span className="text-xs font-bold text-accent-cyan tracking-wider uppercase">
              Structural Breaks (BOS & CHoCH)
            </span>
            <span className="text-[10px] text-text-muted">
              {((activeStruct?.bos_events.length || 0) + (activeStruct?.choch_events.length || 0))} Confirmed
            </span>
          </div>

          <div className="space-y-2 text-[11px] max-h-56 overflow-y-auto">
            {activeStruct && (activeStruct.bos_events.length > 0 || activeStruct.choch_events.length > 0) ? (
              [...(activeStruct.choch_events || []), ...(activeStruct.bos_events || [])].slice(-6).reverse().map((ev, i) => (
                <div key={i} className="flex items-center justify-between p-2 rounded bg-surface-elevated/40 border border-border/20">
                  <div className="flex items-center gap-2">
                    <span className={`text-[10px] px-1.5 py-0.5 rounded font-bold ${
                      ev.event_type.includes('BULL') ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                    }`}>
                      {ev.event_type.replace('_', ' ')}
                    </span>
                    <span className="text-text-primary">
                      ${ev.broken_level.toLocaleString('en-US')} → Close: ${ev.close_price.toLocaleString('en-US')}
                    </span>
                  </div>

                  <div className="flex items-center gap-2">
                    <span className="text-[10px] text-text-muted">+{ev.atr_normalized_distance.toFixed(1)} ATR</span>
                    {getBreakQualityBadge(ev.break_quality)}
                  </div>
                </div>
              ))
            ) : (
              <div className="text-text-muted py-2">No structural breaks recorded in lookback window.</div>
            )}
          </div>
        </div>

        {/* Support & Resistance Zones */}
        <div className="bg-surface/40 p-3 rounded-lg border border-border-subtle">
          <div className="flex items-center justify-between mb-2.5 border-b border-border/60 pb-1.5">
            <span className="text-xs font-bold text-purple-400 tracking-wider uppercase">
              ATR-Clustered S&R Zones
            </span>
            <span className="text-[10px] text-text-muted">
              {((activeStruct?.support_zones.length || 0) + (activeStruct?.resistance_zones.length || 0))} Zones
            </span>
          </div>

          <div className="space-y-2 text-[11px] max-h-56 overflow-y-auto">
            {activeStruct && (activeStruct.resistance_zones.length > 0 || activeStruct.support_zones.length > 0) ? (
              [...(activeStruct.resistance_zones || []), ...(activeStruct.support_zones || [])].slice(0, 6).map((z, i) => (
                <div key={i} className="flex items-center justify-between p-2 rounded bg-surface-elevated/40 border border-border/20">
                  <div className="flex items-center gap-2">
                    <span className={`text-[10px] px-1.5 py-0.5 rounded font-bold ${
                      z.zone_type === 'RESISTANCE' ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20' : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                    }`}>
                      {z.zone_type}
                    </span>
                    <span className="text-text-primary">
                      ${z.price_low.toFixed(0)} - ${z.price_high.toFixed(0)}
                    </span>
                  </div>

                  <div className="flex items-center gap-2">
                    {getStatusBadge(z.status)}
                    {getStrengthBadge(z.strength)}
                  </div>
                </div>
              ))
            ) : (
              <div className="text-text-muted py-2">No clustered support/resistance zones in view.</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
