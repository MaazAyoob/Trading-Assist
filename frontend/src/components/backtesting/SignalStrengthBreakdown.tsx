import React from 'react';
import { Target, Zap } from 'lucide-react';
import { BacktestMetrics } from '../../types/backtesting';

interface SignalStrengthBreakdownProps {
  metrics: BacktestMetrics;
}

export const SignalStrengthBreakdown: React.FC<SignalStrengthBreakdownProps> = ({ metrics }) => {
  const strengthKeys = Object.keys(metrics.strength_breakdown);
  const scoreKeys = Object.keys(metrics.score_breakdown);

  const formatPct = (val?: number) => {
    if (val == null) return 'N/A';
    const sign = val > 0 ? '+' : '';
    return `${sign}${(val * 100).toFixed(2)}%`;
  };

  const getReturnColor = (val?: number) => {
    if (val == null) return 'text-text-muted';
    if (val > 0.0005) return 'text-emerald-400 font-bold';
    if (val < -0.0005) return 'text-rose-400 font-bold';
    return 'text-text-secondary';
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 font-mono text-xs select-none">
      {/* Strength Tier Breakdown */}
      <div className="bg-surface/40 p-4 rounded-lg border border-border-subtle">
        <div className="flex items-center gap-2 mb-3">
          <Zap className="w-4 h-4 text-accent-cyan" />
          <span className="font-bold text-text-primary uppercase tracking-wider">
            Performance Sliced by Signal Strength
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-[11px]">
            <thead>
              <tr className="border-b border-border/60 text-text-muted bg-surface/60">
                <th className="py-2 px-3">STRENGTH</th>
                <th className="py-2 px-3">SAMPLE (N)</th>
                <th className="py-2 px-3">1C RETURN</th>
                <th className="py-2 px-3">3C RETURN</th>
                <th className="py-2 px-3">5C RETURN</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/30">
              {strengthKeys.map((st) => {
                const b = metrics.strength_breakdown[st];
                const h1 = b.horizon_metrics[1]?.forward_return_stats;
                const h3 = b.horizon_metrics[3]?.forward_return_stats;
                const h5 = b.horizon_metrics[5]?.forward_return_stats;

                return (
                  <tr key={st} className="hover:bg-surface-elevated/30 transition">
                    <td className="py-2 px-3 font-bold text-text-primary">{st}</td>
                    <td className="py-2 px-3 text-text-secondary">{b.sample_count}</td>
                    <td className={`py-2 px-3 ${getReturnColor(h1?.mean)}`}>{formatPct(h1?.mean)}</td>
                    <td className={`py-2 px-3 ${getReturnColor(h3?.mean)}`}>{formatPct(h3?.mean)}</td>
                    <td className={`py-2 px-3 ${getReturnColor(h5?.mean)}`}>{formatPct(h5?.mean)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Score Range Band Breakdown */}
      <div className="bg-surface/40 p-4 rounded-lg border border-border-subtle">
        <div className="flex items-center gap-2 mb-3">
          <Target className="w-4 h-4 text-purple-400" />
          <span className="font-bold text-text-primary uppercase tracking-wider">
            Performance Sliced by Absolute Score Bands
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-[11px]">
            <thead>
              <tr className="border-b border-border/60 text-text-muted bg-surface/60">
                <th className="py-2 px-3">SCORE BAND</th>
                <th className="py-2 px-3">SAMPLE (N)</th>
                <th className="py-2 px-3">1C RETURN</th>
                <th className="py-2 px-3">3C RETURN</th>
                <th className="py-2 px-3">5C RETURN</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/30">
              {scoreKeys.map((sb) => {
                const b = metrics.score_breakdown[sb];
                const h1 = b.horizon_metrics[1]?.forward_return_stats;
                const h3 = b.horizon_metrics[3]?.forward_return_stats;
                const h5 = b.horizon_metrics[5]?.forward_return_stats;

                return (
                  <tr key={sb} className="hover:bg-surface-elevated/30 transition">
                    <td className="py-2 px-3 font-bold text-text-primary">{sb}</td>
                    <td className="py-2 px-3 text-text-secondary">{b.sample_count}</td>
                    <td className={`py-2 px-3 ${getReturnColor(h1?.mean)}`}>{formatPct(h1?.mean)}</td>
                    <td className={`py-2 px-3 ${getReturnColor(h3?.mean)}`}>{formatPct(h3?.mean)}</td>
                    <td className={`py-2 px-3 ${getReturnColor(h5?.mean)}`}>{formatPct(h5?.mean)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
