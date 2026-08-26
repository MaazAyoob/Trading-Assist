import React from 'react';
import { Compass } from 'lucide-react';
import { BacktestMetrics } from '../../types/backtesting';

interface MfeMaeChartProps {
  metrics: BacktestMetrics;
}

export const MfeMaeChart: React.FC<MfeMaeChartProps> = ({ metrics }) => {
  const horizons = Object.keys(metrics.horizon_metrics).map(Number).sort((a, b) => a - b);

  const formatPct = (val?: number) => {
    if (val == null) return 'N/A';
    const sign = val > 0 ? '+' : '';
    return `${sign}${(val * 100).toFixed(2)}%`;
  };

  return (
    <div className="bg-surface/40 p-4 rounded-lg border border-border-subtle font-mono text-xs select-none">
      <div className="flex items-center gap-2 mb-3">
        <Compass className="w-4 h-4 text-purple-400" />
        <span className="font-bold text-text-primary uppercase tracking-wider">
          Excursion Profiles (MFE / MAE Analytical Extents)
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse text-[11px]">
          <thead>
            <tr className="border-b border-border/60 text-text-muted bg-surface/60">
              <th className="py-2 px-3">HORIZON</th>
              <th className="py-2 px-3">SAMPLE (N)</th>
              <th className="py-2 px-3 text-emerald-400">MEAN MFE (Max Favorable)</th>
              <th className="py-2 px-3 text-emerald-400">MEDIAN MFE</th>
              <th className="py-2 px-3 text-rose-400">MEAN MAE (Max Adverse)</th>
              <th className="py-2 px-3 text-rose-400">MEDIAN MAE</th>
              <th className="py-2 px-3">MFE/MAE RATIO</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border/30">
            {horizons.map((h) => {
              const hm = metrics.horizon_metrics[h];
              if (!hm) return null;
              const mfe = hm.mfe_stats;
              const mae = hm.mae_stats;

              const ratio =
                mfe.mean != null && mae.mean != null && Math.abs(mae.mean) > 1e-5
                  ? (mfe.mean / Math.abs(mae.mean)).toFixed(2)
                  : 'N/A';

              return (
                <tr key={h} className="hover:bg-surface-elevated/30 transition">
                  <td className="py-2.5 px-3 font-bold text-purple-400">{h} Candle{h > 1 ? 's' : ''}</td>
                  <td className="py-2.5 px-3 text-text-primary">{mfe.sample_count}</td>
                  <td className="py-2.5 px-3 text-emerald-400 font-bold">{formatPct(mfe.mean)}</td>
                  <td className="py-2.5 px-3 text-emerald-400">{formatPct(mfe.median)}</td>
                  <td className="py-2.5 px-3 text-rose-400 font-bold">{formatPct(mae.mean)}</td>
                  <td className="py-2.5 px-3 text-rose-400">{formatPct(mae.median)}</td>
                  <td className="py-2.5 px-3 text-accent-gold font-bold">{ratio}x</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
