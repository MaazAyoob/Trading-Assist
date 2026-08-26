import React, { useEffect } from 'react';
import { useMarketStore } from '../../stores/marketStore';
import { Layers, ArrowRight, CheckCircle2, ShieldCheck, Activity } from 'lucide-react';

export const ProfileComparison: React.FC = () => {
  const { symbol, profileComparison, loadProfileComparison, setProfile, selectedProfileId } = useMarketStore();

  useEffect(() => {
    loadProfileComparison();
  }, [symbol]);

  const profiles = profileComparison?.profiles || [];

  return (
    <div className="p-4 bg-slate-950/90 border border-slate-800 rounded-xl space-y-3 font-mono select-none">
      <div className="flex items-center justify-between pb-2 border-b border-slate-800">
        <div>
          <h3 className="text-sm font-bold text-slate-100 font-sans flex items-center gap-1.5">
            <Layers className="w-4 h-4 text-indigo-400" />
            Multi-Profile Analytical Comparison Matrix
          </h3>
          <p className="text-xs text-slate-400 font-sans mt-0.5">
            Objective observed performance characteristics across trading styles without subjective winner declarations.
          </p>
        </div>
        <div className="text-[10px] text-slate-400 bg-slate-900 px-2 py-1 rounded border border-slate-800">
          Target: <strong className="text-slate-200">{symbol}</strong>
        </div>
      </div>

      <div className="overflow-x-auto rounded-lg border border-slate-800">
        <table className="w-full text-left text-xs">
          <thead className="bg-slate-900 text-slate-400 text-[10px] uppercase tracking-wider font-semibold border-b border-slate-800">
            <tr>
              <th className="p-2.5">Trading Profile</th>
              <th className="p-2.5">Primary TF</th>
              <th className="p-2.5">Context TFs</th>
              <th className="p-2.5">Holding Horizon</th>
              <th className="p-2.5">Signals/Day</th>
              <th className="p-2.5">5C Median Return</th>
              <th className="p-2.5">Win Rate</th>
              <th className="p-2.5">Cost Viability (10 bps)</th>
              <th className="p-2.5 text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {profiles.map((p) => {
              const isSelected = p.profile_id === selectedProfileId;
              return (
                <tr key={p.profile_id} className={`transition ${isSelected ? 'bg-indigo-950/30' : 'hover:bg-slate-900/40'}`}>
                  <td className="p-2.5 font-bold text-slate-200 flex items-center gap-1.5">
                    <span>{p.display_name}</span>
                    {isSelected && (
                      <span className="text-[9px] px-1 rounded bg-indigo-600 text-white font-mono">
                        ACTIVE
                      </span>
                    )}
                  </td>
                  <td className="p-2.5 font-mono text-indigo-300 font-bold">
                    {p.primary_timeframe}
                  </td>
                  <td className="p-2.5 text-slate-400 text-[11px]">
                    {p.context_timeframes.join(', ')}
                  </td>
                  <td className="p-2.5 text-slate-300 text-[11px] font-sans">
                    {p.expected_horizon}
                  </td>
                  <td className="p-2.5 font-mono text-emerald-400 font-bold">
                    {p.signals_per_day.toFixed(1)}
                  </td>
                  <td className="p-2.5 font-mono text-slate-200">
                    +{p.median_5c_return_pct.toFixed(2)}%
                  </td>
                  <td className="p-2.5 font-mono text-slate-200">
                    {p.positive_rate_pct.toFixed(1)}%
                  </td>
                  <td className="p-2.5">
                    <span className="text-[10px] px-1.5 py-0.2 rounded font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                      VIABLE
                    </span>
                  </td>
                  <td className="p-2.5 text-right">
                    <button
                      onClick={() => setProfile(p.profile_id)}
                      disabled={isSelected}
                      className={`px-2 py-1 rounded text-[11px] font-medium transition ${
                        isSelected
                          ? 'bg-slate-800 text-slate-500 cursor-default'
                          : 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-sm'
                      }`}
                    >
                      {isSelected ? 'Selected' : 'Activate'}
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
