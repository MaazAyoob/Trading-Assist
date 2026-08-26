import React from 'react';
import { CandidateLiveMetrics } from '../../types/shadow';
import { Clock, TrendingUp, CheckCircle2, AlertTriangle, ShieldCheck } from 'lucide-react';

interface Props {
  metrics: CandidateLiveMetrics;
}

export const LiveOutcomeTracker: React.FC<Props> = ({ metrics }) => {
  return (
    <div className="flex flex-col gap-3 bg-surface p-4 rounded-lg border border-border">
      <div className="flex items-center justify-between border-b border-border/60 pb-2">
        <span className="font-bold text-text-primary flex items-center gap-1.5 text-xs">
          <TrendingUp className="w-3.5 h-3.5 text-accent-gold" />
          <span>Forward Outcome Performance Breakdown ({metrics.candidate_name})</span>
        </span>
        <span className="text-[10px] text-text-muted">
          Cost-Adjusted Analytical Returns (Not Execution Simulation)
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-center text-[11px] font-mono">
          <thead>
            <tr className="border-b border-border/80 text-text-muted">
              <th className="pb-1.5 text-left">Horizon</th>
              <th className="pb-1.5">Raw Median</th>
              <th className="pb-1.5">Cost Adj (5 bps)</th>
              <th className="pb-1.5">Cost Adj (10 bps)</th>
              <th className="pb-1.5">Positive Rate</th>
              <th className="pb-1.5">MFE (Peak)</th>
              <th className="pb-1.5">MAE (Drawdown)</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border/40">
            <tr>
              <td className="py-2 text-left font-bold">1 Candle (15m)</td>
              <td className={`py-2 font-bold ${metrics.h1_median_raw >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                {(metrics.h1_median_raw * 100).toFixed(3)}%
              </td>
              <td className="py-2 text-text-secondary">{((metrics.h1_median_raw - 0.0005) * 100).toFixed(3)}%</td>
              <td className="py-2 text-text-secondary">{((metrics.h1_median_raw - 0.0010) * 100).toFixed(3)}%</td>
              <td className="py-2 text-text-muted">-</td>
              <td className="py-2 text-text-muted">-</td>
              <td className="py-2 text-text-muted">-</td>
            </tr>
            <tr>
              <td className="py-2 text-left font-bold">3 Candles (45m)</td>
              <td className={`py-2 font-bold ${metrics.h3_median_raw >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                {(metrics.h3_median_raw * 100).toFixed(3)}%
              </td>
              <td className="py-2 text-text-secondary">{((metrics.h3_median_raw - 0.0005) * 100).toFixed(3)}%</td>
              <td className="py-2 text-text-secondary">{((metrics.h3_median_raw - 0.0010) * 100).toFixed(3)}%</td>
              <td className="py-2 text-text-muted">-</td>
              <td className="py-2 text-text-muted">-</td>
              <td className="py-2 text-text-muted">-</td>
            </tr>
            <tr className="bg-surface-elevated/20">
              <td className="py-2 text-left font-bold text-accent-cyan">5 Candles (75m) [Primary]</td>
              <td className={`py-2 font-bold ${metrics.h5_median_raw >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                {(metrics.h5_median_raw * 100).toFixed(3)}%
              </td>
              <td className="py-2 text-text-primary font-bold">{(metrics.h5_median_cost_5bps * 100).toFixed(3)}%</td>
              <td className="py-2 text-text-primary font-bold">{(metrics.h5_median_cost_10bps * 100).toFixed(3)}%</td>
              <td className="py-2 text-text-primary font-bold">{metrics.h5_positive_rate.toFixed(1)}%</td>
              <td className="py-2 text-emerald-400">{(metrics.h5_mfe_median * 100).toFixed(3)}%</td>
              <td className="py-2 text-rose-400">{(metrics.h5_mae_median * 100).toFixed(3)}%</td>
            </tr>
            <tr>
              <td className="py-2 text-left font-bold">10 Candles (2.5h)</td>
              <td className={`py-2 font-bold ${metrics.h10_median_raw >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                {(metrics.h10_median_raw * 100).toFixed(3)}%
              </td>
              <td className="py-2 text-text-secondary">{((metrics.h10_median_raw - 0.0005) * 100).toFixed(3)}%</td>
              <td className="py-2 text-text-secondary">{((metrics.h10_median_raw - 0.0010) * 100).toFixed(3)}%</td>
              <td className="py-2 text-text-primary">{metrics.h10_positive_rate.toFixed(1)}%</td>
              <td className="py-2 text-text-muted">-</td>
              <td className="py-2 text-text-muted">-</td>
            </tr>
            <tr>
              <td className="py-2 text-left font-bold">20 Candles (5.0h)</td>
              <td className={`py-2 font-bold ${metrics.h20_median_raw >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                {(metrics.h20_median_raw * 100).toFixed(3)}%
              </td>
              <td className="py-2 text-text-secondary">{((metrics.h20_median_raw - 0.0005) * 100).toFixed(3)}%</td>
              <td className="py-2 text-text-secondary">{((metrics.h20_median_raw - 0.0010) * 100).toFixed(3)}%</td>
              <td className="py-2 text-text-muted">-</td>
              <td className="py-2 text-text-muted">-</td>
              <td className="py-2 text-text-muted">-</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
};
