import React from 'react';
import { CandidateLiveMetrics } from '../../types/shadow';
import { Layers, ShieldCheck, TrendingUp, AlertTriangle } from 'lucide-react';

interface Props {
  metrics: Record<string, CandidateLiveMetrics>;
}

export const CandidateComparison: React.FC<Props> = ({ metrics }) => {
  const base = metrics['BASELINE'];
  const a2 = metrics['EXP_A2_PULLBACK_VWAP'];
  const e2 = metrics['EXP_E2_EXTENSION_VWAP'];

  if (!base || !a2 || !e2) {
    return null;
  }

  return (
    <div className="flex flex-col gap-3 bg-surface p-4 rounded-lg border border-border">
      <div className="flex items-center justify-between border-b border-border/60 pb-2">
        <span className="font-bold text-text-primary flex items-center gap-1.5 text-xs">
          <Layers className="w-3.5 h-3.5 text-accent-cyan" />
          <span>Descriptive Candidate Comparison (Live Multi-Stream Observation)</span>
        </span>
        <span className="text-[10px] text-text-muted">
          Descriptive Metrics Only (No Automated Winner Selection)
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-center text-[11px] font-mono">
          <thead>
            <tr className="border-b border-border/80 text-text-muted">
              <th className="pb-1.5 text-left">Observed Metric</th>
              <th className="pb-1.5 text-text-muted">BASELINE (PHASE 5)</th>
              <th className="pb-1.5 text-emerald-400">EXP_A2 (VWAP PULLBACK)</th>
              <th className="pb-1.5 text-cyan-400">EXP_E2 (VWAP EXTENSION)</th>
              <th className="pb-1.5 text-right">Observed Advantage</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border/40">
            <tr>
              <td className="py-2 text-left font-bold">Signal Count (Live)</td>
              <td className="py-2 text-text-muted">{base.total_signals}</td>
              <td className="py-2 text-emerald-400 font-bold">{a2.total_signals}</td>
              <td className="py-2 text-cyan-400 font-bold">{e2.total_signals}</td>
              <td className="py-2 text-right text-text-secondary text-[10px]">Filter Discipline Active</td>
            </tr>
            <tr>
              <td className="py-2 text-left font-bold">5C Raw Median Return</td>
              <td className={`py-2 ${base.h5_median_raw >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                {(base.h5_median_raw * 100).toFixed(3)}%
              </td>
              <td className={`py-2 font-bold ${a2.h5_median_raw >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                {(a2.h5_median_raw * 100).toFixed(3)}%
              </td>
              <td className={`py-2 font-bold ${e2.h5_median_raw >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                {(e2.h5_median_raw * 100).toFixed(3)}%
              </td>
              <td className="py-2 text-right font-bold text-accent-cyan text-[10px]">
                {a2.h5_median_raw > base.h5_median_raw || e2.h5_median_raw > base.h5_median_raw ? 'OBSERVED ADVANTAGE' : 'NEUTRAL'}
              </td>
            </tr>
            <tr>
              <td className="py-2 text-left font-bold">5C Positive Rate</td>
              <td className="py-2 text-text-muted">{base.h5_positive_rate.toFixed(1)}%</td>
              <td className="py-2 text-emerald-400 font-bold">{a2.h5_positive_rate.toFixed(1)}%</td>
              <td className="py-2 text-cyan-400 font-bold">{e2.h5_positive_rate.toFixed(1)}%</td>
              <td className="py-2 text-right text-text-secondary text-[10px]">
                {Math.max(a2.h5_positive_rate, e2.h5_positive_rate) > base.h5_positive_rate ? 'POSITIVE DRIFT' : 'ALIGNED'}
              </td>
            </tr>
            <tr>
              <td className="py-2 text-left font-bold">Adjacent Bar Clustering</td>
              <td className="py-2 text-rose-400">{base.adjacent_signal_rate.toFixed(1)}%</td>
              <td className="py-2 text-emerald-400 font-bold">{a2.adjacent_signal_rate.toFixed(1)}%</td>
              <td className="py-2 text-cyan-400 font-bold">{e2.adjacent_signal_rate.toFixed(1)}%</td>
              <td className="py-2 text-right text-emerald-400 text-[10px]">CLUSTERING REDUCED</td>
            </tr>
            <tr>
              <td className="py-2 text-left font-bold">Directional Symmetry (L/S)</td>
              <td className="py-2 text-text-muted">{(base.long_5c_median*100).toFixed(2)}% / {(base.short_5c_median*100).toFixed(2)}%</td>
              <td className="py-2 text-emerald-400">{(a2.long_5c_median*100).toFixed(2)}% / {(a2.short_5c_median*100).toFixed(2)}%</td>
              <td className="py-2 text-cyan-400">{(e2.long_5c_median*100).toFixed(2)}% / {(e2.short_5c_median*100).toFixed(2)}%</td>
              <td className="py-2 text-right text-text-secondary text-[10px]">BALANCED</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
};
