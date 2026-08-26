import React from 'react';
import { Shield, AlertTriangle, Clock, ArrowUpRight, ArrowDownRight, MinusCircle, Info, Sparkles, CheckCircle2, XCircle } from 'lucide-react';
import { useMarketStore, formatSymbolPrice, getAlignmentScoreTier } from '../../stores/marketStore';

export const TradeDecisionHero: React.FC = () => {
  const {
    symbol,
    confirmedTradeDecision,
    realtimeTradeDecision,
    selectedStrategyId,
    setSelectedStrategyId,
    multiStrategyDecisions,
    candles,
    isLoading,
  } = useMarketStore();

  const decision = confirmedTradeDecision || realtimeTradeDecision;

  const lastClosedCandle = candles.filter((c) => c.is_closed).pop();
  const lastClosedTime = lastClosedCandle
    ? new Date(lastClosedCandle.timestamp).toLocaleTimeString('en-US', {
        timeZone: 'UTC',
        hour: '2-digit',
        minute: '2-digit',
        hour12: false,
      }) + ' UTC'
    : '—';

  if (!decision && isLoading) {
    return (
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 mb-4 shadow-xl font-mono">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-slate-800 flex items-center justify-center text-indigo-400">
            <Clock className="w-5 h-5 animate-spin" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-slate-200 uppercase tracking-wider">Evaluating Market Decision...</h2>
            <p className="text-xs text-slate-400">Awaiting confirmed analysis across indicators, regime, structure, and strategy filter...</p>
          </div>
        </div>
      </div>
    );
  }

  if (!decision) {
    return (
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 mb-4 shadow-xl font-mono">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-slate-800 flex items-center justify-center text-slate-400">
            <MinusCircle className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-slate-200 uppercase tracking-wider">NO ACTIVE DECISION</h2>
            <p className="text-xs text-slate-400">Awaiting market data stream initialization...</p>
          </div>
        </div>
      </div>
    );
  }

  const isBuy = decision.decision === 'BUY';
  const isSell = decision.decision === 'SELL';
  const isNoTrade = decision.decision === 'NO_TRADE';

  const badgeBg = isBuy
    ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
    : isSell
    ? 'bg-rose-500/10 border-rose-500/30 text-rose-400'
    : 'bg-amber-500/10 border-amber-500/30 text-amber-400';

  // Lifecycle state formatting
  const getStateDisplay = () => {
    if (isNoTrade) return 'NO VALID DIRECTIONAL SETUP';
    if (isBuy) {
      if (decision.state === 'ENTRY_ZONE_ACTIVE') return 'BUY — ENTRY ZONE ACTIVE';
      return 'BUY SETUP — WAITING FOR ENTRY';
    }
    if (isSell) {
      if (decision.state === 'ENTRY_ZONE_ACTIVE') return 'SELL — ENTRY ZONE ACTIVE';
      return 'SELL SETUP — WAITING FOR ENTRY';
    }
    return decision.state.replace(/_/g, ' ');
  };

  const stateBg =
    decision.state === 'ENTRY_ZONE_ACTIVE'
      ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40 animate-pulse'
      : decision.state === 'WAITING_FOR_ENTRY'
      ? 'bg-blue-500/20 text-blue-300 border-blue-500/40'
      : decision.state === 'INVALIDATED'
      ? 'bg-rose-500/20 text-rose-300 border-rose-500/40'
      : decision.state === 'EXPIRED'
      ? 'bg-slate-500/20 text-slate-400 border-slate-500/40'
      : 'bg-slate-800 text-slate-400 border-slate-700';

  const alignmentScore = decision.decision_alignment_score;
  const scoreTier = getAlignmentScoreTier(alignmentScore);

  const formatPrice = (val: number | null | undefined) => formatSymbolPrice(symbol, val);

  return (
    <div className="bg-slate-900/95 border border-slate-800/90 rounded-xl p-3 sm:p-4 mb-3 shadow-2xl backdrop-blur-md font-mono">
      {/* Top Banner: Strategy Selector, Timestamps & Realtime Preview Indicator */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 pb-2.5 sm:pb-3 border-b border-slate-800/80 mb-3">
        {/* Strategy Context Selector Pills */}
        <div className="flex flex-wrap items-center gap-1.5 sm:gap-2 max-w-full">
          <span className="text-[10px] sm:text-[11px] font-semibold tracking-wider uppercase text-slate-400 flex items-center gap-1.5 font-sans">
            <Sparkles className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
            <span className="hidden xs:inline">Strategy Context:</span>
            <span className="xs:hidden">Strategy:</span>
          </span>
          <div className="flex items-center bg-slate-950 p-0.5 rounded-lg border border-slate-800 overflow-x-auto max-w-full scrollbar-none">
            {[
              { id: 'EXP_A2_PULLBACK_VWAP', label: 'A2 Pullback' },
              { id: 'EXP_E2_EXTENSION_VWAP', label: 'E2 Extension' },
              { id: 'PHASE5_BASELINE', label: 'Phase 5 Baseline' },
            ].map((strat) => {
              const active = selectedStrategyId === strat.id;
              const candDecision = multiStrategyDecisions?.candidate_decisions?.[strat.id]?.decision;
              return (
                <button
                  key={strat.id}
                  onClick={() => setSelectedStrategyId(strat.id)}
                  className={`px-2 sm:px-2.5 py-1 text-[11px] sm:text-xs font-medium rounded-md transition-all flex items-center gap-1.5 shrink-0 ${
                    active
                      ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
                  }`}
                >
                  {strat.label}
                  {candDecision && (
                    <span
                      className={`text-[9px] px-1 py-0.2 rounded font-bold uppercase ${
                        candDecision === 'BUY'
                          ? 'bg-emerald-500/20 text-emerald-300'
                          : candDecision === 'SELL'
                          ? 'bg-rose-500/20 text-rose-300'
                          : 'bg-slate-800 text-slate-400'
                      }`}
                    >
                      {candDecision}
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        </div>

        {/* Realtime Forming Preview or Confirmed Closed Candle Badge */}
        <div className="flex items-center gap-2 text-[10px] sm:text-[11px] pt-1 sm:pt-0 border-t sm:border-t-0 border-slate-800/60">
          <div className="font-mono text-slate-400 hidden lg:flex items-center gap-1.5">
            <Clock className="w-3 h-3 text-slate-500" />
            <span>Closed:</span>
            <span className="text-slate-200 font-bold">{lastClosedTime}</span>
          </div>

          {decision.is_preview ? (
            <span className="inline-flex items-center gap-1 px-2 sm:px-2.5 py-0.5 sm:py-1 rounded-md text-[10px] sm:text-[11px] font-semibold bg-slate-800/80 text-slate-300 border border-slate-700/80">
              <Clock className="w-3.5 h-3.5 text-amber-400 animate-spin" />
              PREVIEW
            </span>
          ) : (
            <span className="inline-flex items-center gap-1 px-2 sm:px-2.5 py-0.5 sm:py-1 rounded-md text-[10px] sm:text-[11px] font-semibold bg-emerald-950/40 text-emerald-400 border border-emerald-800/40">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
              CONFIRMED
            </span>
          )}
        </div>
      </div>

      {/* Main Grid: Decision Hero Badge, Entry Zone, Risk/Reward, and Alignment Score */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2.5 sm:gap-3 items-stretch">
        {/* Col 1: Actionable Decision Badge */}
        <div className={`p-3.5 rounded-xl border flex flex-col justify-between ${badgeBg}`}>
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
              Trade Plan Decision
            </span>
            <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold border uppercase tracking-wider ${stateBg}`}>
              {getStateDisplay()}
            </span>
          </div>

          <div className="flex items-center gap-2.5 my-1">
            <div
              className={`w-11 h-11 rounded-xl flex items-center justify-center font-black ${
                isBuy
                  ? 'bg-emerald-500 text-slate-950'
                  : isSell
                  ? 'bg-rose-500 text-white'
                  : 'bg-amber-500/20 text-amber-400 border border-amber-500/40'
              }`}
            >
              {isBuy ? (
                <ArrowUpRight className="w-6 h-6 stroke-[2.5]" />
              ) : isSell ? (
                <ArrowDownRight className="w-6 h-6 stroke-[2.5]" />
              ) : (
                <MinusCircle className="w-5 h-5" />
              )}
            </div>
            <div>
              <div className="text-2xl font-black tracking-tight">{decision.decision}</div>
              <div className="text-xs text-slate-300 font-sans">
                {isNoTrade
                  ? decision.reasons_for_no_trade[0] || 'Research signal is NEUTRAL.'
                  : `${decision.direction} Setup (${decision.entry?.entry_type.replace(/_/g, ' ') || 'MARKET'})`}
              </div>
            </div>
          </div>

          <div className="text-[10px] text-slate-400 flex items-center gap-1.5 mt-2 pt-2 border-t border-slate-800/40 font-sans">
            <Shield className="w-3.5 h-3.5 text-indigo-400" />
            <span>Analytical trade plan only — No execution</span>
          </div>
        </div>

        {/* Col 2: Rule-Based Entry Reference & Zone */}
        <div className="p-3.5 rounded-xl border border-slate-800 bg-slate-950/60 flex flex-col justify-between">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Planned Entry Reference
            </span>
            {!isNoTrade && decision.entry && (
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-indigo-300 font-mono">
                {decision.entry.entry_type}
              </span>
            )}
          </div>

          <div>
            <div className="text-2xl font-black font-mono text-slate-100">
              {isNoTrade ? 'N/A' : decision.entry ? `$${formatPrice(decision.entry.planned_entry_price)}` : '—'}
            </div>
            <div className="text-xs text-slate-400 mt-1 flex items-center justify-between">
              <span>Entry Zone:</span>
              <span className="font-mono text-slate-300 font-medium">
                {isNoTrade
                  ? 'N/A — No directional setup'
                  : decision.entry
                  ? `$${formatPrice(decision.entry.entry_zone_low)} – $${formatPrice(decision.entry.entry_zone_high)}`
                  : 'N/A'}
              </span>
            </div>
          </div>

          <div className="text-[10px] text-slate-500 truncate pt-2 border-t border-slate-800/60 font-sans">
            {isNoTrade ? 'No directional trade plan active' : decision.entry?.formula_description || 'Market Close Equilibrium'}
          </div>
        </div>

        {/* Col 3: Structural Stop Loss & Risk Distance */}
        <div className="p-3.5 rounded-xl border border-slate-800 bg-slate-950/60 flex flex-col justify-between">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Structural Stop Loss
            </span>
            {!isNoTrade && decision.stop_loss && (
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-rose-950/40 text-rose-400 border border-rose-800/40 font-mono">
                -{decision.stop_loss.distance_atr.toFixed(2)} ATR
              </span>
            )}
          </div>

          <div>
            <div className="text-2xl font-black font-mono text-rose-400">
              {isNoTrade ? 'N/A' : decision.stop_loss ? `$${formatPrice(decision.stop_loss.price)}` : '—'}
            </div>
            <div className="text-xs text-slate-400 mt-1 flex items-center justify-between">
              <span>Risk Distance:</span>
              <span className="font-mono text-slate-300 font-medium">
                {isNoTrade ? 'N/A — No trade plan' : decision.stop_loss ? `$${formatPrice(decision.stop_loss.distance)}` : 'N/A'}
              </span>
            </div>
          </div>

          <div className="text-[10px] text-slate-500 truncate pt-2 border-t border-slate-800/60 font-sans">
            {isNoTrade ? 'No directional setup to protect' : decision.stop_loss?.reason || 'Confirmed Swing Anchor'}
          </div>
        </div>

        {/* Col 4: Take Profit Targets & Alignment Score */}
        <div className="p-3.5 rounded-xl border border-slate-800 bg-slate-950/60 flex flex-col justify-between">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Targets & Alignment
            </span>
            <div
              className="group relative cursor-help flex items-center gap-1 text-[11px]"
              title="Deterministic component-alignment score. It is not a probability or forecast accuracy measure."
            >
              <span className="text-slate-400">Score:</span>
              <span className={`font-bold font-mono ${scoreTier.color}`}>
                {alignmentScore !== null && alignmentScore !== undefined ? `${alignmentScore.toFixed(0)}/100` : '—'}
              </span>
              <span className={`text-[9px] px-1 rounded font-bold uppercase ${scoreTier.color} bg-slate-900 border border-slate-800`}>
                {scoreTier.label}
              </span>
              <Info className="w-3 h-3 text-slate-500" />
            </div>
          </div>

          {!isNoTrade && decision.take_profits ? (
            <div className="grid grid-cols-3 gap-1.5 py-0.5">
              <div className="bg-slate-900 p-1.5 rounded-lg border border-slate-800 text-center">
                <div className="text-[9px] text-slate-400 font-semibold uppercase">TP1 ({decision.take_profits.tp1.actual_rr_after_adjustment.toFixed(2)}R)</div>
                <div className="text-xs font-mono font-bold text-emerald-400 truncate">
                  ${formatPrice(decision.take_profits.tp1.adjusted_target)}
                </div>
              </div>
              <div className="bg-slate-900 p-1.5 rounded-lg border border-slate-800 text-center">
                <div className="text-[9px] text-slate-400 font-semibold uppercase">TP2 ({decision.take_profits.tp2.actual_rr_after_adjustment.toFixed(2)}R)</div>
                <div className="text-xs font-mono font-bold text-emerald-400 truncate">
                  ${formatPrice(decision.take_profits.tp2.adjusted_target)}
                </div>
              </div>
              <div className="bg-slate-900 p-1.5 rounded-lg border border-slate-800 text-center">
                <div className="text-[9px] text-slate-400 font-semibold uppercase">TP3 ({decision.take_profits.tp3.actual_rr_after_adjustment.toFixed(2)}R)</div>
                <div className="text-xs font-mono font-bold text-emerald-400 truncate">
                  ${formatPrice(decision.take_profits.tp3.adjusted_target)}
                </div>
              </div>
            </div>
          ) : (
            <div className="py-2 text-center text-xs text-slate-400 font-mono">
              N/A — No trade plan
            </div>
          )}

          <div className="text-[10px] text-slate-500 flex items-center justify-between pt-2 border-t border-slate-800/60">
            <span>R:R Filter:</span>
            <span
              className={`font-semibold font-mono ${
                !isNoTrade && decision.risk_reward?.is_acceptable ? 'text-emerald-400' : 'text-slate-400'
              }`}
            >
              {!isNoTrade && decision.risk_reward?.is_acceptable ? 'PASSED (>= 1.20R)' : 'N/A — No trade plan'}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
