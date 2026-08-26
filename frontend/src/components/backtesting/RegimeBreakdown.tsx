import React from 'react';
import { Layers } from 'lucide-react';
import { BacktestMetrics } from '../../types/backtesting';

interface RegimeBreakdownProps {
  metrics: BacktestMetrics;
}

export const RegimeBreakdown: React.FC<RegimeBreakdownProps> = ({ metrics }) => {
  const regimes = Object.keys(metrics.regime_breakdown);

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
    <div className="bg-surface/40 p-4 rounded-lg border border-border-subtle font-mono text-xs select-none">
      <div className="flex items-center gap-2 mb-3">
        <Layers className="w-4 h-4 text-accent-gold" />
        <span className="font-bold text-text-primary uppercase tracking-wider">
          Conditional Performance Sliced by Market Regime (at Signal Time)
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse text-[11px]">
          <thead>
            <tr className="border-b border-border/60 text-text-muted bg-surface/60">
              <th className="py-2 px-3">MARKET REGIME</th>
              <th className="py-2 px-3">SAMPLE (N)</th>
              <th className="py-2 px-3">1C MEAN RETURN</th>
              <th className="py-2 px-3">3C MEAN RETURN</th>
              <th className="py-2 px-3">5C MEAN RETURN</th>
              <th className="py-2 px-3">10C MEAN RETURN</th>
              <th className="py-2 px-3">5C MEAN MFE</th>
              <th className="py-2 px-3">5C MEAN MAE</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border/30">
            {regimes.map((reg) => {
              const b = metrics.regime_breakdown[reg];
              const h1 = b.horizon_metrics[1]?.forward_return_stats;
              const h3 = b.horizon_metrics[3]?.forward_return_stats;
              const h5 = b.horizon_metrics[5]?.forward_return_stats;
              const h10 = b.horizon_metrics[10]?.forward_return_stats;
              const h5_mfe = b.horizon_metrics[5]?.mfe_stats;
              const h5_mae = b.horizon_metrics[5]?.mae_stats;

              return (
                <tr key={reg} className="hover:bg-surface-elevated/30 transition">
                  <td className="py-2.5 px-3 font-bold text-text-primary">{reg}</td>
                  <td className="py-2.5 px-3 text-text-secondary">{b.sample_count}</td>
                  <td className={`py-2.5 px-3 ${getReturnColor(h1?.mean)}`}>{formatPct(h1?.mean)}</td>
                  <td className={`py-2.5 px-3 ${getReturnColor(h3?.mean)}`}>{formatPct(h3?.mean)}</td>
                  <td className={`py-2.5 px-3 ${getReturnColor(h5?.mean)}`}>{formatPct(h5?.mean)}</td>
                  <td className={`py-2.5 px-3 ${getReturnColor(h10?.mean)}`}>{formatPct(h10?.mean)}</td>
                  <td className="py-2.5 px-3 text-emerald-400">{formatPct(h5_mfe?.mean)}</td>
                  <td className="py-2.5 px-3 text-rose-400">{formatPct(h5_mae?.mean)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
