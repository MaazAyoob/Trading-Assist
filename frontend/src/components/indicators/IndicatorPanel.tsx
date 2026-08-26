import React, { useState } from 'react';
import { Activity, Lock, Eye } from 'lucide-react';
import { useMarketStore } from '../../stores/marketStore';
import { TrendIndicators } from './TrendIndicators';
import { MomentumIndicators } from './MomentumIndicators';
import { VolatilityIndicators } from './VolatilityIndicators';
import { VolumeIndicators } from './VolumeIndicators';
import { DataQualityBadge } from './DataQualityBadge';

export const IndicatorPanel: React.FC = () => {
  const { symbol, timeframe, confirmedSnapshot, realtimeSnapshot, quality } = useMarketStore();
  const [viewMode, setViewMode] = useState<'confirmed' | 'realtime'>('confirmed');

  const activeSnapshot = viewMode === 'confirmed' ? confirmedSnapshot : (realtimeSnapshot || confirmedSnapshot);

  return (
    <div className="bg-surface-card rounded-lg border border-border flex flex-col overflow-hidden select-none">
      {/* Header Bar */}
      <div className="h-11 bg-surface px-4 flex flex-wrap items-center justify-between border-b border-border/80 gap-2">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 text-xs font-bold text-text-primary uppercase tracking-wider font-mono">
            <Activity className="w-4 h-4 text-accent-cyan" />
            <span>Technical Indicator Suite</span>
          </div>
          <span className="text-[10px] font-mono text-text-muted bg-surface-elevated px-2 py-0.5 rounded border border-border-subtle">
            {symbol} · {timeframe}
          </span>
          <DataQualityBadge quality={quality} />
        </div>

        {/* View Mode Toggle: Confirmed vs Realtime */}
        <div className="flex items-center gap-1 bg-surface-card p-1 rounded border border-border-subtle">
          <button
            onClick={() => setViewMode('confirmed')}
            className={`flex items-center gap-1 px-2.5 py-1 text-[11px] font-mono font-medium rounded transition ${
              viewMode === 'confirmed'
                ? 'bg-accent-cyan text-black font-bold shadow-glow-cyan/30'
                : 'text-text-secondary hover:text-text-primary'
            }`}
          >
            <Lock className="w-3 h-3" />
            <span>Confirmed Only (Closed)</span>
          </button>

          <button
            onClick={() => setViewMode('realtime')}
            className={`flex items-center gap-1 px-2.5 py-1 text-[11px] font-mono font-medium rounded transition ${
              viewMode === 'realtime'
                ? 'bg-accent-gold text-black font-bold shadow-glow-cyan/30'
                : 'text-text-secondary hover:text-text-primary'
            }`}
          >
            <Eye className="w-3 h-3" />
            <span>Live Forming (Realtime)</span>
          </button>
        </div>
      </div>

      {/* Snapshot Metadata Warning Pill */}
      <div className="bg-surface/40 px-4 py-1.5 border-b border-border/40 flex items-center justify-between text-[11px] font-mono text-text-muted">
        <div>
          <span>Status: </span>
          <span className={viewMode === 'confirmed' ? 'text-accent-cyan font-semibold' : 'text-accent-gold font-semibold'}>
            {viewMode === 'confirmed' ? '● IMMUTABLE CONFIRMED OBSERVATION' : '○ REALTIME UNCONFIRMED TICK'}
          </span>
        </div>
        <div>
          <span>Engine: v{activeSnapshot?.engine_version || '0.3.0'} · Config: {activeSnapshot?.config_version || '2026-08-24-v1'}</span>
        </div>
      </div>

      {/* Indicator Matrices */}
      <div className="p-4 grid grid-cols-1 md:grid-cols-2 gap-3 overflow-y-auto">
        <TrendIndicators trend={activeSnapshot?.trend} isConfirmed={viewMode === 'confirmed'} />
        <MomentumIndicators momentum={activeSnapshot?.momentum} />
        <VolatilityIndicators volatility={activeSnapshot?.volatility} />
        <VolumeIndicators volume={activeSnapshot?.volume} />
      </div>
    </div>
  );
};
