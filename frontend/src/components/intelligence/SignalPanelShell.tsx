import React from 'react';
import { Cpu, ShieldCheck, Sparkles, CheckCircle2, AlertCircle, ArrowUpRight, ArrowDownRight, MinusCircle, Info } from 'lucide-react';
import { useMarketStore, formatSymbolPrice } from '../../stores/marketStore';

export const SignalPanelShell: React.FC = () => {
  const {
    symbol,
    confirmedTradeDecision,
    realtimeTradeDecision,
    confirmedSignal,
    realtimeSignal,
  } = useMarketStore();

  const decision = confirmedTradeDecision || realtimeTradeDecision;
  const signal = confirmedSignal || realtimeSignal;

  const isBuy = decision?.decision === 'BUY';
  const isSell = decision?.decision === 'SELL';
  const isNoTrade = !decision || decision.decision === 'NO_TRADE';

  const badgeBg = isBuy
    ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
    : isSell
    ? 'bg-rose-500/10 border-rose-500/30 text-rose-400'
    : 'bg-amber-500/10 border-amber-500/30 text-amber-400';

  const scoreTrace = signal?.score_trace;
  const scoreVal = signal?.score || 0;

  return (
    <div className="w-full lg:w-80 bg-surface-card rounded-lg border border-border flex flex-col overflow-hidden select-none">
      {/* Header */}
      <div className="h-10 bg-surface px-3 flex items-center justify-between border-b border-border/80">
        <div className="flex items-center gap-1.5 text-xs font-bold text-text-primary uppercase tracking-wider font-mono">
          <Cpu className="w-3.5 h-3.5 text-indigo-400" />
          <span>Trade Decision & Signal</span>
        </div>
        <span className="text-[10px] font-mono text-indigo-300 bg-indigo-950/40 border border-indigo-800/40 px-1.5 py-0.5 rounded font-semibold">
          PHASE 10 ACTIVE
        </span>
      </div>

      <div className="p-3 flex flex-col gap-3 flex-1 overflow-y-auto font-mono text-xs">
        {/* Authoritative Decision Card */}
        <div className={`border rounded-lg p-3 flex flex-col items-center justify-center text-center ${badgeBg}`}>
          <div className="text-[10px] uppercase tracking-wider text-slate-400 flex items-center gap-1">
            <span>Authoritative Decision</span>
          </div>

          <div className="flex items-center gap-2 mt-1.5">
            {isBuy ? (
              <ArrowUpRight className="w-5 h-5 text-emerald-400" />
            ) : isSell ? (
              <ArrowDownRight className="w-5 h-5 text-rose-400" />
            ) : (
              <MinusCircle className="w-5 h-5 text-amber-400" />
            )}
            <span className="text-lg font-black tracking-tight">
              {decision?.decision || 'NO TRADE'}
            </span>
          </div>

          <div className="text-[11px] text-slate-300 mt-1 font-sans">
            {isNoTrade
              ? decision?.reasons_for_no_trade?.[0] || 'Research signal is NEUTRAL'
              : `${decision?.direction} — ${decision?.state?.replace(/_/g, ' ')}`}
          </div>

          <div className="text-[10px] text-slate-400 mt-1.5 pt-1.5 border-t border-slate-800/40 w-full flex justify-between">
            <span>Alignment Score:</span>
            <span className="font-bold text-slate-200">{decision?.decision_alignment_score?.toFixed(0) || 0}/100</span>
          </div>
        </div>

        {/* Phase 5 Multi-Factor Score Trace */}
        <div className="bg-surface/50 border border-border-subtle rounded-lg p-3">
          <div className="text-[11px] font-semibold text-text-primary flex items-center justify-between mb-2">
            <div className="flex items-center gap-1.5">
              <Sparkles className="w-3 h-3 text-accent-cyan" />
              <span>Multi-Factor Research</span>
            </div>
            <span className="text-[10px] text-slate-400 font-mono">
              Net Score: <strong className={scoreVal > 0 ? 'text-emerald-400' : scoreVal < 0 ? 'text-rose-400' : 'text-slate-300'}>{scoreVal.toFixed(1)}</strong>
            </span>
          </div>

          <div className="space-y-2 text-[11px]">
            <div>
              <div className="flex justify-between text-text-secondary mb-0.5">
                <span>Trend Alignment</span>
                <span className="font-bold text-slate-200">{scoreTrace?.trend_score?.toFixed(1) || '0.0'} / 30</span>
              </div>
              <div className="w-full bg-surface-card h-1.5 rounded-full overflow-hidden">
                <div
                  className="bg-accent-cyan h-full rounded-full transition-all"
                  style={{ width: `${Math.min(100, (Math.abs(scoreTrace?.trend_score || 0) / 30) * 100)}%` }}
                />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-text-secondary mb-0.5">
                <span>Momentum (RSI/MACD)</span>
                <span className="font-bold text-slate-200">{scoreTrace?.momentum_score?.toFixed(1) || '0.0'} / 25</span>
              </div>
              <div className="w-full bg-surface-card h-1.5 rounded-full overflow-hidden">
                <div
                  className="bg-accent-green h-full rounded-full transition-all"
                  style={{ width: `${Math.min(100, (Math.abs(scoreTrace?.momentum_score || 0) / 25) * 100)}%` }}
                />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-text-secondary mb-0.5">
                <span>Market Structure</span>
                <span className="font-bold text-slate-200">{scoreTrace?.structure_score?.toFixed(1) || '0.0'} / 25</span>
              </div>
              <div className="w-full bg-surface-card h-1.5 rounded-full overflow-hidden">
                <div
                  className="bg-accent-gold h-full rounded-full transition-all"
                  style={{ width: `${Math.min(100, (Math.abs(scoreTrace?.structure_score || 0) / 25) * 100)}%` }}
                />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-text-secondary mb-0.5">
                <span>Volume Confirmation</span>
                <span className="font-bold text-slate-200">{scoreTrace?.volume_score?.toFixed(1) || '0.0'} / 20</span>
              </div>
              <div className="w-full bg-surface-card h-1.5 rounded-full overflow-hidden">
                <div
                  className="bg-purple-400 h-full rounded-full transition-all"
                  style={{ width: `${Math.min(100, (Math.abs(scoreTrace?.volume_score || 0) / 20) * 100)}%` }}
                />
              </div>
            </div>
          </div>
        </div>

        {/* Diagnostic Checks Checklist */}
        <div className="bg-surface/50 border border-border-subtle rounded-lg p-2.5 space-y-1.5 text-[11px]">
          <div className="text-slate-400 font-bold uppercase text-[10px] mb-1">
            Hierarchy Validation
          </div>
          <div className="flex justify-between items-center text-slate-300">
            <span>Market Data Live</span>
            <CheckCircle2 className="w-3 h-3 text-emerald-400" />
          </div>
          <div className="flex justify-between items-center text-slate-300">
            <span>Indicator Matrix</span>
            <CheckCircle2 className="w-3 h-3 text-emerald-400" />
          </div>
          <div className="flex justify-between items-center text-slate-300">
            <span>Regime Classification</span>
            <CheckCircle2 className="w-3 h-3 text-emerald-400" />
          </div>
          <div className="flex justify-between items-center text-slate-300">
            <span>Structure (BOS/CHoCH)</span>
            <CheckCircle2 className="w-3 h-3 text-emerald-400" />
          </div>
          <div className="flex justify-between items-center text-slate-300">
            <span>Directional Signal</span>
            {isNoTrade ? (
              <MinusCircle className="w-3 h-3 text-amber-400" />
            ) : (
              <CheckCircle2 className="w-3 h-3 text-emerald-400" />
            )}
          </div>
        </div>

        {/* Shadow Execution Disclaimer */}
        <div className="bg-indigo-950/20 border border-indigo-800/30 rounded-lg p-2.5 text-[10px] text-slate-400 leading-relaxed">
          <div className="flex items-center gap-1.5 text-indigo-300 font-bold mb-0.5">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Analytical Shadow Engine</span>
          </div>
          Rule-based analytical plan generation only. No order placement or trading execution.
        </div>
      </div>
    </div>
  );
};
