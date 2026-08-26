import React, { useState } from 'react';
import { ListFilter, Search } from 'lucide-react';
import { SignalOutcome } from '../../types/backtesting';

interface SignalOutcomeTableProps {
  signals: SignalOutcome[];
}

export const SignalOutcomeTable: React.FC<SignalOutcomeTableProps> = ({ signals }) => {
  const [filterDirection, setFilterDirection] = useState<'ALL' | 'LONG_SETUP' | 'SHORT_SETUP'>('ALL');
  const [searchTerm, setSearchTerm] = useState<string>('');

  const filteredSignals = signals.filter((s) => {
    if (filterDirection !== 'ALL' && s.signal_direction !== filterDirection) return false;
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      return (
        s.regime_at_signal.toLowerCase().includes(term) ||
        s.structure_at_signal.toLowerCase().includes(term) ||
        s.signal_strength.toLowerCase().includes(term)
      );
    }
    return true;
  });

  const formatPct = (val?: number) => {
    if (val == null) return 'N/A';
    const sign = val > 0 ? '+' : '';
    return `${sign}${(val * 100).toFixed(2)}%`;
  };

  const getReturnClass = (val?: number) => {
    if (val == null) return 'text-text-muted';
    if (val > 0.0005) return 'text-emerald-400 font-bold';
    if (val < -0.0005) return 'text-rose-400 font-bold';
    return 'text-text-secondary';
  };

  const formatTs = (ts: number) => {
    const d = new Date(ts);
    return `${d.getUTCMonth() + 1}/${d.getUTCDate()} ${d.getUTCHours().toString().padStart(2, '0')}:${d.getUTCMinutes().toString().padStart(2, '0')}`;
  };

  return (
    <div className="bg-surface/40 p-4 rounded-lg border border-border-subtle font-mono text-xs select-none space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <ListFilter className="w-4 h-4 text-accent-cyan" />
          <span className="font-bold text-text-primary uppercase tracking-wider">
            Individual Signal Outcome History ({filteredSignals.length} Records)
          </span>
        </div>

        <div className="flex items-center gap-2">
          {/* Search box */}
          <div className="flex items-center gap-1.5 bg-surface-card border border-border-subtle rounded px-2 py-1 text-[11px]">
            <Search className="w-3 h-3 text-text-muted" />
            <input
              type="text"
              placeholder="Filter by regime/structure..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="bg-transparent text-text-primary focus:outline-none text-[11px] w-36"
            />
          </div>

          {/* Direction toggle */}
          <div className="flex items-center gap-1 bg-surface-card p-0.5 rounded border border-border-subtle text-[11px]">
            <button
              onClick={() => setFilterDirection('ALL')}
              className={`px-2 py-0.5 rounded transition ${
                filterDirection === 'ALL' ? 'bg-accent-cyan text-black font-bold' : 'text-text-muted hover:text-text-secondary'
              }`}
            >
              All
            </button>
            <button
              onClick={() => setFilterDirection('LONG_SETUP')}
              className={`px-2 py-0.5 rounded transition ${
                filterDirection === 'LONG_SETUP' ? 'bg-emerald-500/20 text-emerald-400 font-bold' : 'text-text-muted hover:text-text-secondary'
              }`}
            >
              ▲ Long
            </button>
            <button
              onClick={() => setFilterDirection('SHORT_SETUP')}
              className={`px-2 py-0.5 rounded transition ${
                filterDirection === 'SHORT_SETUP' ? 'bg-rose-500/20 text-rose-400 font-bold' : 'text-text-muted hover:text-text-secondary'
              }`}
            >
              ▼ Short
            </button>
          </div>
        </div>
      </div>

      <div className="overflow-x-auto max-h-96">
        <table className="w-full text-left border-collapse text-[11px]">
          <thead className="sticky top-0 bg-surface z-10">
            <tr className="border-b border-border text-text-muted bg-surface/90">
              <th className="py-2 px-2.5">TIME (UTC)</th>
              <th className="py-2 px-2.5">DIRECTION</th>
              <th className="py-2 px-2.5">SCORE</th>
              <th className="py-2 px-2.5">REF PRICE</th>
              <th className="py-2 px-2.5">1C RETURN</th>
              <th className="py-2 px-2.5">3C RETURN</th>
              <th className="py-2 px-2.5">5C RETURN</th>
              <th className="py-2 px-2.5">10C RETURN</th>
              <th className="py-2 px-2.5 text-emerald-400">5C MFE</th>
              <th className="py-2 px-2.5 text-rose-400">5C MAE</th>
              <th className="py-2 px-2.5">REGIME</th>
              <th className="py-2 px-2.5">STRUCTURE</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border/20">
            {filteredSignals.map((s) => {
              const o1 = s.outcomes[1];
              const o3 = s.outcomes[3];
              const o5 = s.outcomes[5];
              const o10 = s.outcomes[10];

              const isLong = s.signal_direction === 'LONG_SETUP';

              return (
                <tr key={s.signal_id} className="hover:bg-surface-elevated/30 transition">
                  <td className="py-2 px-2.5 text-text-muted">{formatTs(s.signal_timestamp)}</td>
                  <td className="py-2 px-2.5">
                    <span className={`px-1.5 py-0.5 rounded font-bold text-[10px] ${
                      isLong ? 'bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/20 text-rose-400'
                    }`}>
                      {isLong ? '▲ LONG' : '▼ SHORT'}
                    </span>
                  </td>
                  <td className="py-2 px-2.5 font-bold text-text-primary">
                    {s.signal_score > 0 ? `+${s.signal_score.toFixed(1)}` : s.signal_score.toFixed(1)}
                  </td>
                  <td className="py-2 px-2.5 text-text-secondary">${s.entry_reference_price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
                  <td className={`py-2 px-2.5 ${getReturnClass(o1?.forward_return)}`}>{formatPct(o1?.forward_return)}</td>
                  <td className={`py-2 px-2.5 ${getReturnClass(o3?.forward_return)}`}>{formatPct(o3?.forward_return)}</td>
                  <td className={`py-2 px-2.5 ${getReturnClass(o5?.forward_return)}`}>{formatPct(o5?.forward_return)}</td>
                  <td className={`py-2 px-2.5 ${getReturnClass(o10?.forward_return)}`}>{formatPct(o10?.forward_return)}</td>
                  <td className="py-2 px-2.5 text-emerald-400">{formatPct(o5?.mfe)}</td>
                  <td className="py-2 px-2.5 text-rose-400">{formatPct(o5?.mae)}</td>
                  <td className="py-2 px-2.5 text-text-muted truncate max-w-[100px]" title={s.regime_at_signal}>{s.regime_at_signal}</td>
                  <td className="py-2 px-2.5 text-text-muted">{s.structure_at_signal}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
