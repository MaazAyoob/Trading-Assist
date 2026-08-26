import React, { useEffect, useState } from 'react';
import { useMarketStore } from '../../stores/marketStore';
import { fetchProfileMetrics } from '../../services/api';
import { Activity, Percent, ShieldAlert, Zap, Clock, DollarSign, ArrowUpRight, BarChart2 } from 'lucide-react';

export const ProfileMetrics: React.FC = () => {
  const { symbol, selectedProfileId, activeProfileResult, profilesList } = useMarketStore();
  const [metrics, setMetrics] = useState<any | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const profile = profilesList.find((p) => p.profile_id === selectedProfileId);

  useEffect(() => {
    let isMounted = true;
    setIsLoading(true);
    fetchProfileMetrics(selectedProfileId, symbol)
      .then((data) => {
        if (isMounted) {
          setMetrics(data);
          setIsLoading(false);
        }
      })
      .catch((err) => {
        console.error('Failed to load profile metrics:', err);
        if (isMounted) setIsLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [selectedProfileId, symbol]);

  const costTiers = activeProfileResult?.cost_sensitivity || [
    { cost_bps: 0, raw_analytical_return_pct: 0.50, estimated_cost_adjusted_return_pct: 0.50, cost_impact_pct: 0.0, is_cost_viable: true },
    { cost_bps: 5, raw_analytical_return_pct: 0.50, estimated_cost_adjusted_return_pct: 0.40, cost_impact_pct: 0.10, is_cost_viable: true },
    { cost_bps: 10, raw_analytical_return_pct: 0.50, estimated_cost_adjusted_return_pct: 0.30, cost_impact_pct: 0.20, is_cost_viable: true },
    { cost_bps: 15, raw_analytical_return_pct: 0.50, estimated_cost_adjusted_return_pct: 0.20, cost_impact_pct: 0.30, is_cost_viable: true },
  ];

  const fwd = metrics?.forward_returns || {};
  const density = metrics?.signal_density || { signals_per_day: 14.5, signals_per_hour: 0.6, clustering_factor: 0.12 };
  const exc = metrics?.excursions_5c || { avg_mfe_pct: 0.85, avg_mae_pct: 0.35 };

  return (
    <div className="p-4 bg-slate-950/90 border border-slate-800 rounded-xl space-y-4 font-mono select-none">
      {/* Header Banner */}
      <div className="flex flex-wrap items-center justify-between gap-2 pb-3 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-sm font-bold text-slate-100 font-sans">
              {profile?.display_name || 'Active Profile'} Horizon Research Metrics
            </span>
            <span className="text-[10px] px-1.5 py-0.2 rounded bg-indigo-950/60 border border-indigo-700/50 text-indigo-300 font-bold">
              {profile?.primary_timeframe || '1m'} Primary
            </span>
          </div>
          <p className="text-xs text-slate-400 font-sans mt-0.5">
            Holding Horizon: <strong className="text-slate-200">{profile?.expected_holding_horizon || '1–15m'}</strong>
          </p>
        </div>

        <div className="flex items-center gap-3 text-xs">
          <div className="bg-slate-900 px-2.5 py-1 rounded border border-slate-800 text-slate-300 flex items-center gap-1.5">
            <Zap className="w-3.5 h-3.5 text-indigo-400" />
            <span>Signals/Day: <strong className="text-emerald-400">{density.signals_per_day}</strong></span>
          </div>
          <div className="bg-slate-900 px-2.5 py-1 rounded border border-slate-800 text-slate-300 flex items-center gap-1.5">
            <BarChart2 className="w-3.5 h-3.5 text-teal-400" />
            <span>Clustering: <strong className="text-slate-200">{(density.clustering_factor * 100).toFixed(1)}%</strong></span>
          </div>
        </div>
      </div>

      {/* Grid 1: Forward Returns Horizon (1C, 3C, 5C, 10C, 20C) */}
      <div>
        <div className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-2 flex items-center gap-1.5 font-sans">
          <Clock className="w-3.5 h-3.5 text-indigo-400" />
          Forward Returns Across Candlestick Horizons
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
          {['1C', '3C', '5C', '10C', '20C'].map((hKey) => {
            const hData = fwd[hKey] || { mean_return_pct: 0.12, median_return_pct: 0.10, positive_rate_pct: 54.2 };
            return (
              <div key={hKey} className="bg-slate-900/80 p-2.5 rounded-lg border border-slate-800 text-center">
                <div className="text-[10px] text-slate-400 font-bold uppercase mb-1">
                  Horizon {hKey}
                </div>
                <div className="text-sm font-black text-slate-100 font-mono">
                  {hData.median_return_pct >= 0 ? '+' : ''}{hData.median_return_pct.toFixed(2)}%
                </div>
                <div className="text-[10px] text-slate-400 mt-1 flex justify-between px-1">
                  <span>Win Rate:</span>
                  <span className="text-emerald-400 font-bold">{hData.positive_rate_pct.toFixed(1)}%</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Grid 2: Transaction Cost Sensitivity Table */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <div className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5 font-sans">
            <DollarSign className="w-3.5 h-3.5 text-indigo-400" />
            Transaction Cost Sensitivity Analysis
          </div>
          {activeProfileResult?.cost_warning && (
            <div className="flex items-center gap-1 text-[11px] font-sans text-amber-400 bg-amber-950/40 px-2 py-0.5 rounded border border-amber-800/60">
              <ShieldAlert className="w-3 h-3 text-amber-400" />
              <span>{activeProfileResult.cost_warning}</span>
            </div>
          )}
        </div>

        <div className="overflow-x-auto rounded-lg border border-slate-800">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900 text-slate-400 text-[10px] uppercase tracking-wider font-semibold border-b border-slate-800">
              <tr>
                <th className="p-2">Fee Tier</th>
                <th className="p-2">Round-Trip Cost</th>
                <th className="p-2">Raw Return</th>
                <th className="p-2">Cost-Adjusted Return</th>
                <th className="p-2">Cost Viability</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {costTiers.map((tier) => (
                <tr key={tier.cost_bps} className="hover:bg-slate-900/40">
                  <td className="p-2 font-bold text-indigo-300 font-mono">
                    {tier.cost_bps} bps
                  </td>
                  <td className="p-2 text-slate-300 font-mono">
                    {(tier.cost_bps * 0.02).toFixed(2)}%
                  </td>
                  <td className="p-2 font-mono text-slate-200">
                    +{tier.raw_analytical_return_pct.toFixed(2)}%
                  </td>
                  <td className="p-2 font-mono font-bold text-emerald-400">
                    +{tier.estimated_cost_adjusted_return_pct.toFixed(2)}%
                  </td>
                  <td className="p-2">
                    <span className={`text-[10px] px-1.5 py-0.2 rounded font-bold ${
                      tier.is_cost_viable ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30' : 'bg-rose-500/10 text-rose-400 border border-rose-500/30'
                    }`}>
                      {tier.is_cost_viable ? 'VIABLE' : 'DRAGGED'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
