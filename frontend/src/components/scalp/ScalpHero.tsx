import React, { useEffect, useState, useCallback } from 'react';
import {
  TrendingUp, TrendingDown, MinusCircle, Clock, Shield, Zap,
  AlertTriangle, CheckCircle2, Info, RefreshCw, Target, ChevronDown, ChevronUp
} from 'lucide-react';
import { ScalpSignal, ScalpDirection } from '../../types/scalp';
import { fetchScalpSignal } from '../../services/api';
import { useMarketStore } from '../../stores/marketStore';

const REFRESH_INTERVAL_MS = 15_000; // refresh every 15s

export const ScalpHero: React.FC = () => {
  const { symbol } = useMarketStore();
  const [confirmed, setConfirmed] = useState<ScalpSignal | null>(null);
  const [preview, setPreview] = useState<ScalpSignal | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showFactors, setShowFactors] = useState(false);
  const [lastRefresh, setLastRefresh] = useState<number>(Date.now());
  const [refreshAge, setRefreshAge] = useState(0);

  const load = useCallback(async () => {
    try {
      setError(null);
      const res = await fetchScalpSignal(symbol, true);
      setConfirmed(res.confirmed_signal);
      setPreview(res.preview_signal ?? null);
      setLastRefresh(Date.now());
    } catch (e: any) {
      setError(e.message || 'Failed to load scalp signal');
    } finally {
      setIsLoading(false);
    }
  }, [symbol]);

  // Live refresh age counter — ticks every second so UI stays accurate
  useEffect(() => {
    const tick = setInterval(() => {
      setRefreshAge(Math.floor((Date.now() - lastRefresh) / 1000));
    }, 1000);
    return () => clearInterval(tick);
  }, [lastRefresh]);

  useEffect(() => {
    setIsLoading(true);
    load();
    const interval = setInterval(load, REFRESH_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [load]);

  const signal = confirmed;
  const dir: ScalpDirection = signal?.direction ?? 'NO_TRADE';
  const score = signal?.score_breakdown.normalised_score ?? 0;
  const net = signal?.score_breakdown.net_score ?? 0;
  const plan = signal?.trade_plan;

  // Derive actual 1m EMA trend from the EMA factor in the score breakdown
  const ema1mFactor = signal?.score_breakdown.factors.find(f => f.name === 'EMA Trend (1m)');
  const trend1m = ema1mFactor?.direction ?? 'NEUTRAL';

  // ── Direction styling ────────────────────────────────────────────────────
  const dirConfig = {
    BUY: {
      bg: 'bg-emerald-950/60 border-emerald-500/60',
      badge: 'bg-emerald-500 text-white',
      icon: TrendingUp,
      iconColor: 'text-emerald-400',
      label: '🟢 BUY SCALP',
      scoreColor: 'text-emerald-400',
      glow: 'shadow-emerald-500/20',
    },
    SELL: {
      bg: 'bg-rose-950/60 border-rose-500/60',
      badge: 'bg-rose-500 text-white',
      icon: TrendingDown,
      iconColor: 'text-rose-400',
      label: '🔴 SELL SCALP',
      scoreColor: 'text-rose-400',
      glow: 'shadow-rose-500/20',
    },
    NO_TRADE: {
      bg: 'bg-slate-900/80 border-slate-700/60',
      badge: 'bg-amber-500/20 text-amber-300 border border-amber-500/30',
      icon: MinusCircle,
      iconColor: 'text-amber-400',
      label: '🟡 NO TRADE',
      scoreColor: 'text-slate-400',
      glow: 'shadow-slate-700/20',
    },
  }[dir];
  const DirIcon = dirConfig.icon;

  const fmtPrice = (v: number | null | undefined) => v != null ? `$${v.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : 'N/A';
  const fmtRR = (v: number | null | undefined) => v != null ? `${v.toFixed(2)}R` : 'N/A';

  if (isLoading && !signal) {
    return (
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-xl font-mono flex items-center gap-3">
        <RefreshCw className="w-5 h-5 text-indigo-400 animate-spin" />
        <div>
          <div className="text-sm font-bold text-slate-200">SCALP_STRATEGY_V1 — Loading...</div>
          <div className="text-xs text-slate-400">Fetching 1m confirmed candle signal</div>
        </div>
      </div>
    );
  }

  return (
    <div className={`border rounded-xl shadow-2xl ${dirConfig.glow} ${dirConfig.bg} font-mono select-none`}>
      {/* ── Top banner ─────────────────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 px-3 sm:px-4 py-2.5 border-b border-slate-800/80">
        <div className="flex flex-wrap items-center gap-1.5 sm:gap-2">
          <span className="text-[10px] font-bold font-sans uppercase tracking-widest text-slate-400 flex items-center gap-1.5">
            <Zap className="w-3 h-3 text-indigo-400" />
            SCALP_STRATEGY_V1
          </span>
          <span className="text-[9px] px-1.5 py-0.5 rounded bg-indigo-950/60 border border-indigo-700/40 text-indigo-300 font-mono">
            1m Primary · 5m/15m Context
          </span>
          <span className="text-[9px] px-1.5 py-0.5 rounded bg-slate-900 border border-slate-700 text-slate-400 font-mono">
            {symbol}
          </span>
        </div>
        <div className="flex flex-wrap items-center gap-2 text-[9px] sm:text-[10px] font-mono text-slate-400 pt-1 sm:pt-0 border-t sm:border-t-0 border-slate-800/60">
          {signal && !signal.is_preview ? (
            <span className="flex items-center gap-1 text-emerald-300">
              <CheckCircle2 className="w-3 h-3 text-emerald-400" />
              CONFIRMED — CLOSED 1m
            </span>
          ) : (
            <span className="flex items-center gap-1 text-amber-300">
              <Clock className="w-3 h-3 text-amber-400 animate-spin" />
              PREVIEW — FORMING
            </span>
          )}
          <span className="text-slate-600">|</span>
          <span>{refreshAge}s ago</span>
          <button
            onClick={load}
            className="p-1 rounded hover:bg-slate-800 transition"
            title="Refresh scalp signal"
          >
            <RefreshCw className="w-3 h-3 text-slate-400" />
          </button>
          <span className="text-slate-600">|</span>
          <Shield className="w-3 h-3 text-indigo-400" />
          <span className="text-indigo-300 font-bold">SHADOW ONLY</span>
        </div>
      </div>

      {/* ── Main Signal Grid ────────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2.5 p-2.5 sm:p-3">
        {/* Decision badge */}
        <div className="flex flex-col items-center justify-center p-3.5 sm:p-4 rounded-lg bg-slate-950/40 border border-slate-800/80 gap-2.5 sm:gap-3">
          <div className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs sm:text-sm font-black tracking-wide ${dirConfig.badge} shadow-lg`}>
            <DirIcon className="w-4 h-4 sm:w-5 sm:h-5" />
            {dirConfig.label}
          </div>
          {/* Score bar */}
          <div className="w-full max-w-[180px]">
            <div className="flex justify-between text-[10px] text-slate-400 mb-1">
              <span>BEAR</span>
              <span className={`font-bold ${dirConfig.scoreColor}`}>SCORE {score.toFixed(0)}</span>
              <span>BULL</span>
            </div>
            <div className="h-2 rounded-full bg-slate-800 overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-700 ${
                  dir === 'BUY' ? 'bg-emerald-400' : dir === 'SELL' ? 'bg-rose-400' : 'bg-amber-400'
                }`}
                style={{
                  width: `${score}%`,
                  // SELL fills from the right side
                  marginLeft: dir === 'SELL' ? `${100 - score}%` : '0%',
                }}
              />
            </div>
            <div className="text-center text-[10px] font-mono mt-1 text-slate-400">
              Net: {net >= 0 ? '+' : ''}{net.toFixed(1)} / ±100
            </div>
          </div>
        </div>

        {/* Entry / SL / TP */}
        <div className="p-3.5 rounded-lg bg-slate-950/40 border border-slate-800/80 flex flex-col gap-1.5 sm:gap-2">
          <div className="text-[10px] text-slate-400 font-bold uppercase tracking-wider mb-0.5">Trade Plan</div>
          {plan?.plan_available ? (
            <>
              <div className="flex justify-between text-xs">
                <span className="text-slate-400">Entry Ref</span>
                <span className="font-bold text-slate-100">{fmtPrice(plan.entry_price)}</span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-slate-400">Stop Loss</span>
                <span className="font-bold text-rose-400">{fmtPrice(plan.stop_loss)}</span>
              </div>
              <div className="h-px bg-slate-800/80 my-0.5" />
              <div className="flex justify-between text-xs">
                <span className="text-slate-400">TP1</span>
                <span className="font-bold text-emerald-400">{fmtPrice(plan.tp1)}</span>
                <span className="text-slate-500">{fmtRR(plan.rr_tp1)}</span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-slate-400">TP2</span>
                <span className="font-bold text-teal-400">{fmtPrice(plan.tp2)}</span>
                <span className="text-slate-500">{fmtRR(plan.rr_tp2)}</span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-slate-400">TP3</span>
                <span className="font-bold text-indigo-400">{fmtPrice(plan.tp3)}</span>
                <span className="text-slate-500">{fmtRR(plan.rr_tp3)}</span>
              </div>
            </>
          ) : (
            <div className="text-xs text-amber-400 flex items-center gap-1.5 my-auto py-2">
              <AlertTriangle className="w-3.5 h-3.5 shrink-0" />
              <span>TRADE PLAN: NOT AVAILABLE</span>
            </div>
          )}
        </div>

        {/* Timeframe context */}
        <div className="p-3.5 rounded-lg bg-slate-950/40 border border-slate-800/80 flex flex-col gap-1.5 sm:gap-2">
          <div className="text-[10px] text-slate-400 font-bold uppercase tracking-wider mb-0.5">Timeframe Context</div>
          {[
            { tf: '1m', label: 'Primary', trend: trend1m },
            { tf: '5m', label: 'Context', trend: signal?.context_5m_trend ?? 'UNKNOWN' },
            { tf: '15m', label: 'Context', trend: signal?.context_15m_trend ?? 'UNKNOWN' },
          ].map((row) => (
            <div key={row.tf} className="flex items-center justify-between text-xs">
              <div className="flex items-center gap-1.5">
                <span className="font-bold text-indigo-300 font-mono w-8">{row.tf}</span>
                <span className="text-slate-500">{row.label}</span>
              </div>
              <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                row.trend === 'BULLISH' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30' :
                row.trend === 'BEARISH' ? 'bg-rose-500/10 text-rose-400 border border-rose-500/30' :
                'bg-slate-800 text-slate-400 border border-slate-700'
              }`}>
                {row.trend}
              </span>
            </div>
          ))}

          <div className="h-px bg-slate-800/80 my-0.5" />
          <div className="flex items-center justify-between text-xs">
            <span className="text-slate-500 text-[11px]">Phase 5 Context</span>
            <span className="text-[9px] font-mono text-slate-400 bg-slate-900 px-1.5 py-0.5 rounded border border-slate-700">
              {signal?.phase5_research_direction ?? 'NEUTRAL'}
            </span>
          </div>
        </div>

        {/* Reasons */}
        <div className="p-3.5 rounded-lg bg-slate-950/40 border border-slate-800/80 flex flex-col gap-1.5">
          <div className="text-[10px] text-slate-400 font-bold uppercase tracking-wider mb-0.5 flex items-center gap-1.5">
            <Info className="w-3 h-3 text-indigo-400" />
            Signal Rationale
          </div>
          {(signal?.reasons ?? []).slice(0, 4).map((r, i) => (
            <div key={i} className="flex items-start gap-1 text-[10px] text-slate-300 font-sans leading-tight">
              <span className="text-indigo-400 shrink-0">›</span>
              <span className="truncate">{r}</span>
            </div>
          ))}
          {(signal?.reasons ?? []).length === 0 && (
            <span className="text-[10px] text-slate-500 italic">No active signal factors</span>
          )}
          {(signal?.invalidation_conditions ?? []).length > 0 && (
            <>
              <div className="text-[9px] font-bold text-slate-500 uppercase mt-1 tracking-wide">Invalidation</div>
              {(signal?.invalidation_conditions ?? []).slice(0, 2).map((c, i) => (
                <div key={i} className="text-[9px] text-slate-500 flex gap-1 leading-tight">
                  <span className="text-rose-500 shrink-0">✕</span>
                  <span className="truncate">{c}</span>
                </div>
              ))}
            </>
          )}
        </div>
      </div>

      {/* ── Score Breakdown Toggle ──────────────────────────────────────────── */}
      <div className="border-t border-slate-800/80">
        <button
          onClick={() => setShowFactors(!showFactors)}
          className="w-full flex items-center justify-between px-4 py-2 text-[11px] font-mono text-slate-400 hover:text-slate-200 hover:bg-slate-900/40 transition"
        >
          <span className="flex items-center gap-1.5">
            <Target className="w-3 h-3 text-indigo-400" />
            Score Breakdown — {signal?.score_breakdown.factors.length ?? 0} factors
          </span>
          {showFactors ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
        </button>

        {showFactors && (
          <div className="px-4 pb-3 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2 border-t border-slate-800/60">
            {(signal?.score_breakdown.factors ?? []).map((f) => {
              // Guard against divide-by-zero if max_score is somehow 0
              const pct = f.max_score > 0 ? Math.min(Math.abs(f.score) / f.max_score, 1.0) : 0;
              return (
                <div key={f.name} className="bg-slate-900/60 rounded-lg p-2.5 border border-slate-800">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-[10px] font-bold text-slate-300 font-sans">{f.name}</span>
                    <span className={`text-[9px] font-bold px-1 rounded ${
                      f.direction === 'BULLISH' ? 'text-emerald-400' :
                      f.direction === 'BEARISH' ? 'text-rose-400' : 'text-slate-400'
                    }`}>
                      {f.score >= 0 ? '+' : ''}{f.score.toFixed(1)}
                    </span>
                  </div>
                  <div className="h-1.5 rounded-full bg-slate-800 overflow-hidden mb-1">
                    <div
                      className={`h-full rounded-full ${
                        f.direction === 'BULLISH' ? 'bg-emerald-500' :
                        f.direction === 'BEARISH' ? 'bg-rose-500' : 'bg-slate-500'
                      }`}
                      style={{ width: `${Math.min(pct * 100, 100)}%` }}
                    />
                  </div>
                  <div className="text-[9px] text-slate-500 font-sans leading-tight">{f.detail}</div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {error && (
        <div className="px-4 py-2 text-[11px] text-rose-400 border-t border-slate-800/60 flex items-center gap-1.5">
          <AlertTriangle className="w-3.5 h-3.5" />
          {error}
        </div>
      )}
    </div>
  );
};
