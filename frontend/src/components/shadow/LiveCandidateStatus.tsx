import React from 'react';
import { CandidateLiveMetrics } from '../../types/shadow';
import { Shield, Zap, TrendingUp, Layers, CheckCircle2, Clock, AlertTriangle } from 'lucide-react';

interface Props {
  metrics: Record<string, CandidateLiveMetrics>;
  selectedCandidate: string;
  onSelectCandidate: (candidateId: string) => void;
}

export const LiveCandidateStatus: React.FC<Props> = ({
  metrics,
  selectedCandidate,
  onSelectCandidate,
}) => {
  const getCandidateBadge = (id: string) => {
    switch (id) {
      case 'BASELINE':
        return <span className="px-2 py-0.5 bg-surface-elevated text-text-muted border border-border rounded text-[10px] font-bold">BASELINE (PHASE 5)</span>;
      case 'EXP_A2_PULLBACK_VWAP':
        return <span className="px-2 py-0.5 bg-emerald-950/80 text-emerald-300 border border-emerald-500/40 rounded text-[10px] font-bold">A2 VWAP PULLBACK</span>;
      case 'EXP_E2_EXTENSION_VWAP':
        return <span className="px-2 py-0.5 bg-cyan-950/80 text-cyan-300 border border-cyan-500/40 rounded text-[10px] font-bold">E2 VWAP EXTENSION</span>;
      default:
        return <span className="px-2 py-0.5 bg-surface-elevated text-text-muted rounded text-[10px]">{id}</span>;
    }
  };

  const getSampleBadge = (status: string) => {
    switch (status) {
      case 'ADEQUATE_SAMPLE':
        return <span className="text-[10px] text-emerald-400 font-bold">ADEQUATE (N≥30)</span>;
      case 'SMALL_SAMPLE':
        return <span className="text-[10px] text-amber-400 font-bold">SMALL SAMPLE (10≤N&lt;30)</span>;
      default:
        return <span className="text-[10px] text-rose-400 font-bold">INSUFFICIENT SAMPLE (N&lt;10)</span>;
    }
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
      {Object.entries(metrics).map(([cId, m]) => {
        const isSelected = selectedCandidate === cId;
        return (
          <div
            key={cId}
            onClick={() => onSelectCandidate(cId)}
            className={`p-3.5 bg-surface rounded-lg border transition cursor-pointer flex flex-col justify-between gap-2.5 ${
              isSelected
                ? 'border-accent-cyan shadow-glow-cyan/20 bg-surface-elevated/30'
                : 'border-border hover:border-text-muted/40 hover:bg-surface-elevated/10'
            }`}
          >
            <div className="flex items-center justify-between">
              {getCandidateBadge(cId)}
              {getSampleBadge(m.sample_status)}
            </div>

            <div className="grid grid-cols-3 gap-2 py-1 border-y border-border/40 text-center">
              <div>
                <span className="text-[9px] text-text-muted uppercase">Signals</span>
                <div className="text-sm font-bold text-text-primary mt-0.5">{m.total_signals}</div>
                <div className="text-[9px] text-text-muted">L: {m.long_count} | S: {m.short_count}</div>
              </div>
              <div>
                <span className="text-[9px] text-text-muted uppercase">5C Med Return</span>
                <div className={`text-sm font-bold mt-0.5 ${m.h5_median_raw >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                  {(m.h5_median_raw * 100).toFixed(3)}%
                </div>
                <div className="text-[9px] text-text-muted">Raw Analytical</div>
              </div>
              <div>
                <span className="text-[9px] text-text-muted uppercase">5C Pos Rate</span>
                <div className="text-sm font-bold text-text-primary mt-0.5">{m.h5_positive_rate.toFixed(1)}%</div>
                <div className="text-[9px] text-text-muted">Win Rate</div>
              </div>
            </div>

            <div className="flex items-center justify-between text-[10px] text-text-muted pt-0.5">
              <span className="flex items-center gap-1">
                <Clock className="w-3 h-3 text-accent-gold" />
                <span>Pending: {m.pending_outcomes_count}</span>
              </span>
              <span className="flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                <span>Completed: {m.completed_outcomes_count}</span>
              </span>
              <span>Clustering: {m.adjacent_signal_rate.toFixed(1)}%</span>
            </div>
          </div>
        );
      })}
    </div>
  );
};
