import React, { useState } from 'react';
import { ShadowSignal } from '../../types/shadow';
import { Zap, Eye, Shield, CheckCircle2, Clock, AlertTriangle, ArrowUpRight, ArrowDownRight } from 'lucide-react';

interface Props {
  signals: ShadowSignal[];
  selectedCandidate: string;
}

export const ShadowSignalFeed: React.FC<Props> = ({ signals, selectedCandidate }) => {
  const [inspectedSignal, setInspectedSignal] = useState<ShadowSignal | null>(null);

  const filtered = selectedCandidate === 'ALL'
    ? signals
    : signals.filter((s) => s.candidate_id === selectedCandidate);

  return (
    <div className="flex flex-col gap-3 bg-surface p-4 rounded-lg border border-border">
      <div className="flex items-center justify-between border-b border-border/60 pb-2">
        <span className="font-bold text-text-primary flex items-center gap-1.5 text-xs">
          <Zap className="w-3.5 h-3.5 text-accent-cyan" />
          <span>Live Shadow Signal Stream ({filtered.length} recorded)</span>
        </span>
        <span className="text-[10px] text-text-muted">
          Immutable Snapshots (Closed 15m Candles Only)
        </span>
      </div>

      {filtered.length === 0 ? (
        <div className="py-8 text-center text-text-muted text-xs font-mono">
          No confirmed shadow signals generated for this candidate stream yet.
        </div>
      ) : (
        <div className="overflow-x-auto max-h-[360px] overflow-y-auto">
          <table className="w-full text-left text-[11px] font-mono">
            <thead>
              <tr className="border-b border-border/80 text-text-muted sticky top-0 bg-surface">
                <th className="pb-1.5">Timestamp</th>
                <th className="pb-1.5">Candidate</th>
                <th className="pb-1.5">Direction</th>
                <th className="pb-1.5">Entry Price</th>
                <th className="pb-1.5">Score</th>
                <th className="pb-1.5">VWAP Dist</th>
                <th className="pb-1.5">Regime</th>
                <th className="pb-1.5">5C Status</th>
                <th className="pb-1.5 text-right">Inspect</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/40">
              {filtered.slice().reverse().map((sig) => {
                const isLong = sig.direction === 'LONG_SETUP';
                const h5 = sig.outcomes[5];
                return (
                  <tr key={sig.signal_id} className="hover:bg-surface-elevated/40 transition">
                    <td className="py-2 text-text-muted">{new Date(sig.candle_close_time).toLocaleTimeString()}</td>
                    <td className="py-2 font-bold text-accent-cyan">{sig.candidate_id.replace('EXP_', '')}</td>
                    <td className="py-2">
                      <span className={`inline-flex items-center gap-1 font-bold ${isLong ? 'text-emerald-400' : 'text-rose-400'}`}>
                        {isLong ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
                        <span>{sig.direction.replace('_SETUP', '')}</span>
                      </span>
                    </td>
                    <td className="py-2 text-text-primary font-bold">${sig.entry_reference_price.toLocaleString()}</td>
                    <td className="py-2 text-accent-gold">{sig.signal_score.toFixed(1)}</td>
                    <td className="py-2 text-text-muted">{sig.vwap_distance_atr ? `${sig.vwap_distance_atr.toFixed(2)} ATR` : '-'}</td>
                    <td className="py-2 text-text-secondary text-[10px]">{sig.regime}</td>
                    <td className="py-2">
                      {h5?.status === 'COMPLETE' ? (
                        <span className={`font-bold ${(h5.raw_analytical_return || 0) >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                          {((h5.raw_analytical_return || 0) * 100).toFixed(3)}%
                        </span>
                      ) : (
                        <span className="text-text-muted text-[10px]">{h5?.status || 'PENDING'}</span>
                      )}
                    </td>
                    <td className="py-2 text-right">
                      <button
                        onClick={() => setInspectedSignal(sig)}
                        className="px-2 py-0.5 bg-surface-elevated hover:bg-accent-cyan/20 text-accent-cyan border border-border rounded text-[10px]"
                      >
                        Inspect
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Snapshot Inspect Modal Drawer */}
      {inspectedSignal && (
        <div className="fixed inset-0 bg-background/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-surface border border-border rounded-lg max-w-xl w-full p-5 flex flex-col gap-3 shadow-xl font-mono text-xs">
            <div className="flex items-center justify-between border-b border-border/80 pb-2">
              <span className="font-bold text-text-primary">Immutable Signal Snapshot: {inspectedSignal.signal_id}</span>
              <button onClick={() => setInspectedSignal(null)} className="text-text-muted hover:text-text-primary font-bold">✕</button>
            </div>

            <div className="grid grid-cols-2 gap-3 text-[11px]">
              <div><span className="text-text-muted">Candidate Stream:</span> <span className="font-bold text-accent-cyan">{inspectedSignal.candidate_id}</span></div>
              <div><span className="text-text-muted">Causal Timestamp:</span> {new Date(inspectedSignal.causal_timestamp).toISOString()}</div>
              <div><span className="text-text-muted">Entry Price:</span> <span className="font-bold">${inspectedSignal.entry_reference_price.toLocaleString()}</span></div>
              <div><span className="text-text-muted">Direction / Score:</span> <span className="font-bold">{inspectedSignal.direction} ({inspectedSignal.signal_score})</span></div>
              <div><span className="text-text-muted">VWAP / Distance:</span> ${inspectedSignal.vwap_price?.toFixed(1) || '-'} ({inspectedSignal.vwap_distance_atr || '-'} ATR)</div>
              <div><span className="text-text-muted">Processing Latency:</span> {inspectedSignal.processing_latency_ms} ms</div>
              <div><span className="text-text-muted">Regime / Volatility:</span> {inspectedSignal.regime} / {inspectedSignal.volatility_state}</div>
              <div><span className="text-text-muted">Config Hash:</span> <span className="font-mono text-[9px] truncate">{inspectedSignal.strategy_config_hash.slice(0, 16)}...</span></div>
            </div>

            <div className="border-t border-border/60 pt-2 flex justify-end">
              <button
                onClick={() => setInspectedSignal(null)}
                className="px-3 py-1 bg-surface-elevated border border-border text-xs rounded hover:bg-surface-elevated/80"
              >
                Close Snapshot
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
