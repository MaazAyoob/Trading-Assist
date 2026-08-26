import React, { useState } from 'react';
import { TrendingUp, BarChart2 } from 'lucide-react';
import { BacktestMetrics } from '../../types/backtesting';

interface ForwardReturnChartProps {
  metrics: BacktestMetrics;
}

export const ForwardReturnChart: React.FC<ForwardReturnChartProps> = ({ metrics }) => {
  const [symmetryView, setSymmetryView] = useState<'all' | 'long' | 'short'>('all');

  const getActiveHorizonMetrics = () => {
    switch (symmetryView) {
      case 'long':
        return metrics.long_horizon_metrics;
      case 'short':
        return metrics.short_horizon_metrics;
      case 'all':
      default:
        return metrics.horizon_metrics;
    }
  };

  const activeMetrics = getActiveHorizonMetrics();
  const horizons = Object.keys(activeMetrics).map(Number).sort((a, b) => a - b);

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
      <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
        <div className="flex items-center gap-2">
          <TrendingUp className="w-4 h-4 text-accent-cyan" />
          <span className="font-bold text-text-primary uppercase tracking-wider">
            Forward-Return Analytical Distributions
          </span>
        </div>

        {/* Directional Symmetry Toggle */}
        <div className="flex items-center gap-1 bg-surface-card p-0.5 rounded border border-border-subtle text-[11px]">
          <button
            onClick={() => setSymmetryView('all')}
            className={`px-2.5 py-0.5 rounded transition ${
              symmetryView === 'all'
                ? 'bg-accent-cyan text-black font-bold'
                : 'text-text-secondary hover:text-text-primary'
            }`}
          >
            Combined (All)
          </button>
          <button
            onClick={() => setSymmetryView('long')}
            className={`px-2.5 py-0.5 rounded transition ${
              symmetryView === 'long'
                ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 font-bold'
                : 'text-text-secondary hover:text-text-primary'
            }`}
          >
            ▲ Long Only
          </button>
          <button
            onClick={() => setSymmetryView('short')}
            className={`px-2.5 py-0.5 rounded transition ${
              symmetryView === 'short'
                ? 'bg-rose-500/20 text-rose-400 border border-rose-500/40 font-bold'
                : 'text-text-secondary hover:text-text-primary'
            }`}
          >
            ▼ Short Only
          </button>
        </div>
      </div>

      {/* Horizon Distribution Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse text-[11px]">
          <thead>
            <tr className="border-b border-border/60 text-text-muted bg-surface/60">
              <th className="py-2 px-3">HORIZON</th>
              <th className="py-2 px-3">SAMPLE (N)</th>
              <th className="py-2 px-3">MEAN RETURN</th>
              <th className="py-2 px-3">MEDIAN RETURN</th>
              <th className="py-2 px-3">95% BOOTSTRAP CI</th>
              <th className="py-2 px-3">STD DEV</th>
              <th className="py-2 px-3">POSITIVE RATIO</th>
              <th className="py-2 px-3">INSUFFICIENT</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border/30">
            {horizons.map((h) => {
              const hm = activeMetrics[h];
              if (!hm) return null;
              const s = hm.forward_return_stats;

              return (
                <tr key={h} className="hover:bg-surface-elevated/30 transition">
                  <td className="py-2.5 px-3 font-bold text-accent-cyan">{h} Candle{h > 1 ? 's' : ''}</td>
                  <td className="py-2.5 px-3 text-text-primary">{s.sample_count}</td>
                  <td className={`py-2.5 px-3 ${getReturnColor(s.mean)}`}>{formatPct(s.mean)}</td>
                  <td className={`py-2.5 px-3 ${getReturnColor(s.median)}`}>{formatPct(s.median)}</td>
                  <td className="py-2.5 px-3 text-text-muted">
                    {s.bootstrap_mean_ci_lower != null && s.bootstrap_mean_ci_upper != null ? (
                      <span>
                        [{formatPct(s.bootstrap_mean_ci_lower)}, {formatPct(s.bootstrap_mean_ci_upper)}]
                      </span>
                    ) : (
                      <span className="text-text-muted italic">{s.status}</span>
                    )}
                  </td>
                  <td className="py-2.5 px-3 text-text-muted">{s.std_dev != null ? `${(s.std_dev * 100).toFixed(2)}%` : 'N/A'}</td>
                  <td className="py-2.5 px-3">
                    <span className="text-text-primary font-bold">{(hm.positive_ratio * 100).toFixed(1)}%</span>{' '}
                    <span className="text-[10px] text-text-muted">({hm.positive_count}/{s.sample_count})</span>
                  </td>
                  <td className="py-2.5 px-3 text-text-muted">{hm.insufficient_horizon_count}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
