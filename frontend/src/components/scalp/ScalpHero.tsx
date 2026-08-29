import React, { useEffect, useState, useCallback, useMemo } from 'react';
import {
  TrendingUp,
  TrendingDown,
  MinusCircle,
  Clock,
  Shield,
  Zap,
  AlertTriangle,
  CheckCircle2,
  Info,
  RefreshCw,
  Target,
  ChevronDown,
  ChevronUp,
  Layers,
  Sparkles,
  Radio,
  BarChart3,
  History,
  GitCompare,
  Eye,
} from 'lucide-react';
import { ScalpSignal, ScalpDirection } from '../../types/scalp';
import {
  ScalpV2Signal,
  ScalpV2Direction,
  HorizonResult,
  ScoreBucketResult,
  SetupQualityResult,
  ScalpV2DiagnosticReport,
  ScoreBucketDiagnostic,
  SetupDiagnostic,
  FactorDiagnostic,
} from '../../types/scalpV2';
import {
  fetchScalpSignal,
  fetchScalpV2Signal,
  fetchScalpV2Stats,
  fetchScalpV2History,
  fetchScalpComparison,
  fetchScalpV2Diagnostics,
} from '../../services/api';
import {
  useMarketStore,
  getScalpStrengthTier,
  getScalpActionGuidance,
} from '../../stores/marketStore';

const REFRESH_INTERVAL_MS = 8_000;

export const ScalpHero: React.FC = () => {
  const {
    symbol,
    connectionState,
    selectedScalpStrategy,
    setSelectedScalpStrategy,
    confirmedScalpSignal,
    previewScalpSignal,
    confirmedScalpV2Signal,
    previewScalpV2Signal,
    scalpV2Stats,
    scalpV2History,
    scalpComparison,
    scalpV2Evaluation,
    scalpV2Diagnostics,
    setScalpSignal,
    setScalpV2Signal,
    loadScalpV2Stats,
    loadScalpV2History,
    loadScalpComparison,
    loadScalpV2Evaluation,
    loadScalpV2Diagnostics,
  } = useMarketStore();

  const [showPreview, setShowPreview] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [showFactors, setShowFactors] = useState<boolean>(() => {
    if (typeof window !== 'undefined') return window.innerWidth >= 1024;
    return false;
  });
  const [showStatsModal, setShowStatsModal] = useState<boolean>(false);
  const [showHistoryModal, setShowHistoryModal] = useState<boolean>(false);
  const [showCompareModal, setShowCompareModal] = useState<boolean>(false);
  const [lastRefresh, setLastRefresh] = useState<number>(Date.now());
  const [refreshAge, setRefreshAge] = useState<number>(0);

  const isV2 = selectedScalpStrategy === 'SCALP_V2';

  const loadData = useCallback(async () => {
    try {
      setError(null);
      if (isV2) {
        const res = await fetchScalpV2Signal(symbol, true);
        setScalpV2Signal(res.confirmed_signal, res.preview_signal ?? null);
        loadScalpV2Stats();
        loadScalpV2Evaluation();
        loadScalpV2Diagnostics();
      } else {
        const res = await fetchScalpSignal(symbol, true);
        setScalpSignal(res.confirmed_signal, res.preview_signal ?? null);
      }
      setLastRefresh(Date.now());
    } catch (e: any) {
      setError(e.message || 'Failed to load scalp signal');
    } finally {
      setIsLoading(false);
    }
  }, [symbol, isV2, setScalpSignal, setScalpV2Signal, loadScalpV2Stats, loadScalpV2Evaluation, loadScalpV2Diagnostics]);

  useEffect(() => {
    const tick = setInterval(() => {
      setRefreshAge(Math.floor((Date.now() - lastRefresh) / 1000));
    }, 1000);
    return () => clearInterval(tick);
  }, [lastRefresh]);

  useEffect(() => {
    setIsLoading(true);
    loadData();
    const interval = setInterval(loadData, REFRESH_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [loadData]);

  // Active V1 or V2 signal
  const activeV1Signal: ScalpSignal | null = showPreview && previewScalpSignal ? previewScalpSignal : confirmedScalpSignal;
  const activeV2Signal: ScalpV2Signal | null = showPreview && previewScalpV2Signal ? previewScalpV2Signal : confirmedScalpV2Signal;

  const isPreview = isV2 ? (activeV2Signal?.is_preview ?? false) : (activeV1Signal?.is_preview ?? false);

  // Direction, scores, setup type
  const dir = isV2 ? (activeV2Signal?.direction ?? 'NO_TRADE') : (activeV1Signal?.direction ?? 'NO_TRADE');
  const score = isV2 ? (activeV2Signal?.alignment_score ?? null) : (activeV1Signal?.score_breakdown?.normalised_score ?? null);
  const netScore = isV2 ? (activeV2Signal?.score ?? 0) : (activeV1Signal?.score_breakdown?.net_score ?? 0);
  const setupType = isV2 ? (activeV2Signal?.setup_type ?? 'NONE') : 'V1_MULTI_FACTOR';

  // Entry, SL, TP
  const plannedEntry = isV2 ? activeV2Signal?.entry?.planned_entry : activeV1Signal?.trade_plan?.entry_price;
  const entryLow = isV2 ? activeV2Signal?.entry?.entry_zone_low : activeV1Signal?.trade_plan?.entry_price;
  const entryHigh = isV2 ? activeV2Signal?.entry?.entry_zone_high : activeV1Signal?.trade_plan?.entry_price;
  const stopLoss = isV2 ? activeV2Signal?.stop_loss?.price : activeV1Signal?.trade_plan?.stop_loss;
  const riskDist = isV2
    ? activeV2Signal?.stop_loss?.risk_distance
    : (activeV1Signal?.trade_plan?.entry_price && activeV1Signal?.trade_plan?.stop_loss
        ? Math.abs(activeV1Signal.trade_plan.entry_price - activeV1Signal.trade_plan.stop_loss)
        : null);
  const riskAtr = isV2
    ? activeV2Signal?.stop_loss?.risk_distance_atr
    : (riskDist && activeV1Signal?.trade_plan?.atr_used
        ? riskDist / activeV1Signal.trade_plan.atr_used
        : 1.0);
  const tp1 = isV2 ? activeV2Signal?.take_profits?.tp1 : activeV1Signal?.trade_plan?.tp1;
  const tp2 = isV2 ? activeV2Signal?.take_profits?.tp2 : activeV1Signal?.trade_plan?.tp2;
  const tp3 = isV2 ? activeV2Signal?.take_profits?.tp3 : activeV1Signal?.trade_plan?.tp3;
  const rr1 = isV2 ? (activeV2Signal?.take_profits?.rr_tp1 ?? 1.0) : (activeV1Signal?.trade_plan?.rr_tp1 ?? 1.25);
  const rr2 = isV2 ? (activeV2Signal?.take_profits?.rr_tp2 ?? 1.5) : (activeV1Signal?.trade_plan?.rr_tp2 ?? 2.0);
  const rr3 = isV2 ? (activeV2Signal?.take_profits?.rr_tp3 ?? 2.0) : (activeV1Signal?.trade_plan?.rr_tp3 ?? 3.0);

  const supportingFactors = isV2 ? (activeV2Signal?.supporting_factors ?? []) : (activeV1Signal?.reasons ?? []);
  const conflictingFactors = isV2 ? (activeV2Signal?.conflicting_factors ?? []) : [];
  const invalidationConditions = isV2 ? (activeV2Signal?.invalidation_conditions ?? []) : (activeV1Signal?.invalidation_conditions ?? []);

  const strengthTier = useMemo(() => getScalpStrengthTier(score, dir as any), [score, dir]);
  const actionGuidance = useMemo(() => getScalpActionGuidance(score, dir as any), [score, dir]);

  return (
    <section aria-label="Scalp Signal Intelligence Terminal" className="relative w-full rounded-2xl bg-gradient-to-b from-slate-900 via-slate-900/95 to-slate-950 border border-slate-800 shadow-2xl overflow-hidden transition-all">
      {/* Background ambient glow */}
      <div className={`absolute top-0 right-1/4 w-96 h-96 rounded-full blur-3xl pointer-events-none opacity-20 transition-colors duration-700 ${
        dir === 'BUY' ? 'bg-emerald-500' : dir === 'SELL' ? 'bg-rose-500' : 'bg-blue-500'
      }`} />

      {/* TOP TERMINAL HEADER & STRATEGY SELECTOR */}
      <div className="relative z-10 px-4 sm:px-6 py-3 border-b border-slate-800/80 bg-slate-950/60 backdrop-blur-md flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse shadow-sm shadow-emerald-400/50" />
            <span className="text-xs font-black uppercase tracking-widest text-slate-200">
              {symbol}
            </span>
          </div>

          <span className="text-slate-600">|</span>

          {/* Strategy Selector Toggle */}
          <div className="flex items-center bg-slate-900 rounded-lg p-0.5 border border-slate-800">
            <button
              onClick={() => setSelectedScalpStrategy('SCALP_V2')}
              className={`px-2.5 py-1 text-xs font-bold rounded-md transition-all ${
                isV2
                  ? 'bg-sky-500 text-white shadow-md shadow-sky-500/20'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              SCALP V2 (HF)
            </button>
            <button
              onClick={() => setSelectedScalpStrategy('SCALP_V1')}
              className={`px-2.5 py-1 text-xs font-bold rounded-md transition-all ${
                !isV2
                  ? 'bg-slate-700 text-white shadow-md'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              SCALP V1
            </button>
          </div>

          <span className="text-slate-600">|</span>

          {/* Setup Type Pill (V2 Only) */}
          {isV2 && (
            <span className={`text-[11px] font-bold px-2 py-0.5 rounded-md border ${
              setupType === 'TREND_CONTINUATION'
                ? 'bg-blue-500/10 text-blue-400 border-blue-500/30'
                : setupType === 'PULLBACK'
                ? 'bg-purple-500/10 text-purple-400 border-purple-500/30'
                : setupType === 'MOMENTUM_BREAKOUT'
                ? 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                : 'bg-slate-800/80 text-slate-400 border-slate-700'
            }`}>
              SETUP: {setupType.replace('_', ' ')}
            </span>
          )}
        </div>

        {/* Right Tools: Preview Toggle, Stats, History, Compare */}
        <div className="flex items-center gap-2">
          {/* Confirmed vs Preview Toggle */}
          <div className="flex items-center bg-slate-900/90 rounded-lg p-0.5 border border-slate-800 text-[11px]">
            <button
              onClick={() => setShowPreview(false)}
              className={`px-2 py-0.5 rounded font-medium transition-all ${
                !showPreview
                  ? 'bg-slate-700 text-white'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              ✓ Confirmed
            </button>
            <button
              onClick={() => setShowPreview(true)}
              className={`px-2 py-0.5 rounded font-medium transition-all flex items-center gap-1 ${
                showPreview
                  ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Eye className="w-3 h-3" /> Preview
            </button>
          </div>

          {/* Diagnostic & Research Buttons */}
          {isV2 && (
            <>
              <button
                onClick={() => {
                  loadScalpV2Stats();
                  setShowStatsModal(true);
                }}
                className="p-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-800 text-slate-300 hover:text-white border border-slate-700 transition"
                title="Frequency Statistics"
              >
                <BarChart3 className="w-4 h-4" />
              </button>

              <button
                onClick={() => {
                  loadScalpV2History();
                  setShowHistoryModal(true);
                }}
                className="p-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-800 text-slate-300 hover:text-white border border-slate-700 transition"
                title="Recent Signal History"
              >
                <History className="w-4 h-4" />
              </button>
            </>
          )}

          <button
            onClick={() => {
              loadScalpComparison();
              setShowCompareModal(true);
            }}
            className="p-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-800 text-slate-300 hover:text-white border border-slate-700 transition"
            title="Compare V1 vs V2"
          >
            <GitCompare className="w-4 h-4" />
          </button>

          <button
            onClick={loadData}
            disabled={isLoading}
            className="p-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-800 text-slate-300 hover:text-white border border-slate-700 transition disabled:opacity-50"
            title="Refresh Signal"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin text-sky-400' : ''}`} />
          </button>
        </div>
      </div>

      {/* MAIN HERO CONTENT GRID */}
      <div className="p-4 sm:p-6 space-y-6">
        {/* ROW 1: DIRECTION BADGE & SCORE & ACTION */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-4 items-stretch">
          {/* DIRECTION HERO BADGE */}
          <div className="md:col-span-5 flex flex-col justify-between p-4 rounded-xl bg-slate-950/80 border border-slate-800/80">
            <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
              <span className="font-semibold tracking-wide uppercase">Directional Bias</span>
              <span className="text-[11px] text-slate-400">{refreshAge}s ago</span>
            </div>

            <div className="flex items-center gap-3 my-2">
              <div className={`p-3 rounded-xl border ${
                dir === 'BUY'
                  ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40 shadow-lg shadow-emerald-500/10'
                  : dir === 'SELL'
                  ? 'bg-rose-500/20 text-rose-400 border-rose-500/40 shadow-lg shadow-rose-500/10'
                  : dir === 'WATCH'
                  ? 'bg-amber-500/20 text-amber-400 border-amber-500/40'
                  : 'bg-slate-800/60 text-slate-400 border-slate-700'
              }`}>
                {dir === 'BUY' && <TrendingUp className="w-7 h-7" />}
                {dir === 'SELL' && <TrendingDown className="w-7 h-7" />}
                {dir === 'WATCH' && <AlertTriangle className="w-7 h-7" />}
                {dir === 'NO_TRADE' && <MinusCircle className="w-7 h-7" />}
              </div>

              <div>
                <h2 className={`text-2xl font-black tracking-tight ${
                  dir === 'BUY' ? 'text-emerald-400' : dir === 'SELL' ? 'text-rose-400' : dir === 'WATCH' ? 'text-amber-400' : 'text-slate-300'
                }`}>
                  {dir === 'BUY' ? 'BUY SCALP' : dir === 'SELL' ? 'SELL SCALP' : dir === 'WATCH' ? 'WATCH / CHOP' : 'NO TRADE'}
                </h2>
                <div className="flex items-center gap-2 mt-1">
                  <span className={`text-[11px] font-bold px-2 py-0.5 rounded border ${strengthTier.badgeClass}`}>
                    {strengthTier.label}
                  </span>
                  <span className="text-xs text-slate-400 font-mono">
                    Score: {score !== null ? `${score.toFixed(0)}/100` : '—'}
                  </span>
                </div>
              </div>
            </div>

            <div className="text-[11px] text-slate-400 mt-2">
              {strengthTier.description}
            </div>
          </div>

          {/* ACTION GUIDANCE BANNER */}
          <div className="md:col-span-4 flex flex-col justify-between p-4 rounded-xl bg-slate-950/80 border border-slate-800/80">
            <div className="text-xs text-slate-400 font-semibold tracking-wide uppercase">
              Action Recommendation
            </div>

            <div className="my-2">
              <div className={`px-4 py-2.5 rounded-xl border text-center font-black tracking-wide text-sm ${actionGuidance.badgeClass}`}>
                {actionGuidance.action}
              </div>
            </div>

            <div className="text-[11px] text-slate-400">
              {actionGuidance.explanation}
            </div>
          </div>

          {/* TIME CONTEXT & NET METRICS */}
          <div className="md:col-span-3 flex flex-col justify-between p-4 rounded-xl bg-slate-950/80 border border-slate-800/80">
            <div className="text-xs text-slate-400 font-semibold tracking-wide uppercase">
              Timeframe Context
            </div>

            <div className="grid grid-cols-3 gap-2 my-2 text-center text-xs">
              <div className="p-2 rounded-lg bg-slate-900 border border-slate-800">
                <div className="text-[10px] text-slate-400 font-bold">1M SCALP</div>
                <div className={`font-black mt-0.5 ${dir === 'BUY' ? 'text-emerald-400' : dir === 'SELL' ? 'text-rose-400' : 'text-slate-400'}`}>
                  {dir === 'BUY' ? '▲ BULL' : dir === 'SELL' ? '▼ BEAR' : '—'}
                </div>
              </div>

              <div className="p-2 rounded-lg bg-slate-900 border border-slate-800">
                <div className="text-[10px] text-slate-400 font-bold">5M TREND</div>
                <div className={`font-black mt-0.5 ${
                  (isV2 ? activeV2Signal?.context_5m_trend : activeV1Signal?.context_5m_trend) === 'BULLISH'
                    ? 'text-emerald-400'
                    : (isV2 ? activeV2Signal?.context_5m_trend : activeV1Signal?.context_5m_trend) === 'BEARISH'
                    ? 'text-rose-400'
                    : 'text-slate-400'
                }`}>
                  {(isV2 ? activeV2Signal?.context_5m_trend : activeV1Signal?.context_5m_trend) === 'BULLISH' ? '▲ BULL' : (isV2 ? activeV2Signal?.context_5m_trend : activeV1Signal?.context_5m_trend) === 'BEARISH' ? '▼ BEAR' : 'NEUT'}
                </div>
              </div>

              <div className="p-2 rounded-lg bg-slate-900 border border-slate-800">
                <div className="text-[10px] text-slate-400 font-bold">15M CTX</div>
                <div className={`font-black mt-0.5 ${
                  (isV2 ? activeV2Signal?.context_15m_trend : activeV1Signal?.context_15m_trend) === 'BULLISH'
                    ? 'text-emerald-400'
                    : (isV2 ? activeV2Signal?.context_15m_trend : activeV1Signal?.context_15m_trend) === 'BEARISH'
                    ? 'text-rose-400'
                    : 'text-slate-400'
                }`}>
                  {(isV2 ? activeV2Signal?.context_15m_trend : activeV1Signal?.context_15m_trend) === 'BULLISH' ? '▲ BULL' : (isV2 ? activeV2Signal?.context_15m_trend : activeV1Signal?.context_15m_trend) === 'BEARISH' ? '▼ BEAR' : 'NEUT'}
                </div>
              </div>
            </div>

            <div className="text-[10px] text-slate-400 text-center font-mono">
              Net Bias: {netScore >= 0 ? `+${netScore.toFixed(1)}` : netScore.toFixed(1)} / ±100
            </div>
          </div>
        </div>

        {/* ROW 2: TRADE PLAN CARD & RISK-REWARD LADDER */}
        {dir !== 'NO_TRADE' && plannedEntry ? (
          <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800/80 space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
                <Target className="w-4 h-4 text-sky-400" />
                1M Scalp Trade Plan (Analytical Reference)
              </span>
              <span className="text-[11px] font-mono text-slate-400">
                Risk: ${riskDist?.toFixed(2) ?? '—'} ({riskAtr?.toFixed(1) ?? '1.0'}x ATR)
              </span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 text-center">
              {/* ENTRY */}
              <div className="p-2.5 rounded-lg bg-sky-950/30 border border-sky-500/30">
                <div className="text-[10px] text-sky-400 font-bold uppercase tracking-wider">Entry Price</div>
                <div className="text-base font-black font-mono text-sky-200 mt-0.5">
                  ${plannedEntry.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </div>
                {entryLow && entryHigh && (
                  <div className="text-[9px] text-sky-400/80 font-mono mt-0.5">
                    Zone: ${entryLow.toFixed(0)} - ${entryHigh.toFixed(0)}
                  </div>
                )}
              </div>

              {/* STOP LOSS */}
              <div className="p-2.5 rounded-lg bg-rose-950/30 border border-rose-500/30">
                <div className="text-[10px] text-rose-400 font-bold uppercase tracking-wider">Stop Loss</div>
                <div className="text-base font-black font-mono text-rose-200 mt-0.5">
                  ${stopLoss?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) ?? '—'}
                </div>
                <div className="text-[9px] text-rose-400/80 font-mono mt-0.5">
                  -{riskDist?.toFixed(1) ?? '—'} (1.0R)
                </div>
              </div>

              {/* TP1 */}
              <div className="p-2.5 rounded-lg bg-emerald-950/30 border border-emerald-500/30">
                <div className="text-[10px] text-emerald-400 font-bold uppercase tracking-wider">TP 1 ({rr1.toFixed(1)}R)</div>
                <div className="text-base font-black font-mono text-emerald-200 mt-0.5">
                  ${tp1?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) ?? '—'}
                </div>
                <div className="text-[9px] text-emerald-400/80 font-mono mt-0.5">
                  +${((tp1 ?? 0) - plannedEntry).toFixed(1)}
                </div>
              </div>

              {/* TP2 */}
              <div className="p-2.5 rounded-lg bg-emerald-950/40 border border-emerald-500/40">
                <div className="text-[10px] text-emerald-300 font-bold uppercase tracking-wider">TP 2 ({rr2.toFixed(1)}R)</div>
                <div className="text-base font-black font-mono text-emerald-100 mt-0.5">
                  ${tp2?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) ?? '—'}
                </div>
                <div className="text-[9px] text-emerald-400/80 font-mono mt-0.5">
                  +${((tp2 ?? 0) - plannedEntry).toFixed(1)}
                </div>
              </div>

              {/* TP3 */}
              <div className="p-2.5 rounded-lg bg-emerald-900/40 border border-emerald-400/50">
                <div className="text-[10px] text-emerald-200 font-bold uppercase tracking-wider">TP 3 ({rr3.toFixed(1)}R)</div>
                <div className="text-base font-black font-mono text-emerald-50 mt-0.5">
                  ${tp3?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) ?? '—'}
                </div>
                <div className="text-[9px] text-emerald-300/80 font-mono mt-0.5">
                  +${((tp3 ?? 0) - plannedEntry).toFixed(1)}
                </div>
              </div>
            </div>
          </div>
        ) : null}

        {/* ROW 3: WHY THIS TRADE & INVALIDATION CONDITIONS */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* SUPPORTING REASONS */}
          <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800/80">
            <div className="text-xs font-bold uppercase tracking-wider text-slate-300 mb-2 flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              Supporting Factors
            </div>
            {supportingFactors.length > 0 ? (
              <ul className="space-y-1.5 text-xs text-slate-300">
                {supportingFactors.map((r, idx) => (
                  <li key={idx} className="flex items-start gap-2">
                    <span className="text-emerald-400 font-bold">✓</span>
                    <span>{r}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <div className="text-xs text-slate-400 italic">No clear supporting edge at this moment.</div>
            )}
          </div>

          {/* CONFLICTING / INVALIDATION */}
          <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800/80">
            <div className="text-xs font-bold uppercase tracking-wider text-slate-300 mb-2 flex items-center gap-1.5">
              <AlertTriangle className="w-4 h-4 text-amber-400" />
              Invalidation & Headwinds
            </div>
            {invalidationConditions.length > 0 || conflictingFactors.length > 0 ? (
              <ul className="space-y-1.5 text-xs text-slate-300">
                {conflictingFactors.map((c, idx) => (
                  <li key={`conf-${idx}`} className="flex items-start gap-2 text-amber-300/90">
                    <span className="text-amber-400 font-bold">⚠</span>
                    <span>{c}</span>
                  </li>
                ))}
                {invalidationConditions.map((inv, idx) => (
                  <li key={`inv-${idx}`} className="flex items-start gap-2 text-rose-300/90">
                    <span className="text-rose-400 font-bold">✕</span>
                    <span>{inv}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <div className="text-xs text-slate-400 italic">No active structural invalidation.</div>
            )}
          </div>
        </div>

        {/* ROW 4: HISTORICAL PROBABILITY RESERVED PANEL */}
        <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/60 flex items-start gap-3 text-xs text-slate-400">
          <Info className="w-4 h-4 text-sky-400 mt-0.5 shrink-0" />
          <div>
            <span className="font-bold text-slate-300 uppercase tracking-wide">Historical Probability: Not Available Yet</span>
            <p className="mt-0.5 text-[11px] text-slate-400">
              Statistical probability will be displayed only after recorded historical calibration.
              Current score is a deterministic indicator alignment score, not a win percentage.
            </p>
          </div>
        </div>
      </div>

      {/* STATS MODAL (FREQUENCY MONITOR & PHASE 13D DEEP DIAGNOSTICS) */}
      {showStatsModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-3xl w-full p-6 shadow-2xl space-y-5 max-h-[92vh] overflow-y-auto">
            {/* MODAL HEADER */}
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <h3 className="text-base font-black text-white flex items-center gap-2">
                  <BarChart3 className="w-5 h-5 text-sky-400" />
                  SCALP V2 Calibration & Signal Timing Diagnostics
                </h3>
                <span className="text-[10px] text-sky-400 font-mono">PHASE 13D FORENSICS & SHADOW CALIBRATION</span>
              </div>
              <button onClick={() => setShowStatsModal(false)} className="text-slate-400 hover:text-white font-bold text-lg">✕</button>
            </div>

            {/* 1. OVERVIEW TILES */}
            {scalpV2Diagnostics && (
              <div className="space-y-4">
                <div className="p-3.5 bg-slate-950 rounded-xl border border-slate-800 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
                      <Sparkles className="w-3.5 h-3.5 text-sky-400" />
                      1. V2 Signal Quality Overview
                    </span>
                    <span className="text-[10px] font-mono bg-sky-950/60 text-sky-300 px-2 py-0.5 rounded border border-sky-800/50">
                      HISTORICAL RESEARCH
                    </span>
                  </div>

                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-center text-xs">
                    <div className="p-2.5 bg-slate-900/90 rounded-lg border border-slate-800">
                      <div className="text-[10px] text-slate-400 uppercase font-bold">Total Signals</div>
                      <div className="text-lg font-black text-slate-100 font-mono mt-0.5">{scalpV2Diagnostics.total_signals}</div>
                      <div className="text-[9px] text-slate-400 font-mono">{scalpV2Diagnostics.clustering_analysis.signals_per_hour}/h ({scalpV2Diagnostics.dataset_duration_hours}h)</div>
                    </div>
                    <div className="p-2.5 bg-slate-900/90 rounded-lg border border-slate-800">
                      <div className="text-[10px] text-slate-400 uppercase font-bold">BUY / SELL</div>
                      <div className="text-sm font-black font-mono mt-1 text-emerald-400">
                        {scalpV2Diagnostics.direction_analysis.BUY?.sample_size_n ?? 0}B <span className="text-slate-500">/</span> <span className="text-rose-400">{scalpV2Diagnostics.direction_analysis.SELL?.sample_size_n ?? 0}S</span>
                      </div>
                      <div className="text-[9px] text-slate-400 font-mono">WATCH: {scalpV2Diagnostics.dataset_candles - (scalpV2Diagnostics.direction_analysis.BUY?.sample_size_n ?? 0) - (scalpV2Diagnostics.direction_analysis.SELL?.sample_size_n ?? 0)}</div>
                    </div>
                    <div className="p-2.5 bg-slate-900/90 rounded-lg border border-slate-800">
                      <div className="text-[10px] text-slate-400 uppercase font-bold">TP1 Hit Rates</div>
                      <div className="text-xs font-black font-mono mt-1 text-sky-300">
                        1C: {scalpV2Diagnostics.timing_analysis.tp1_within_1c > 0 ? ((scalpV2Diagnostics.timing_analysis.tp1_within_1c / scalpV2Diagnostics.total_signals) * 100).toFixed(1) : 0}% | 20C: {scalpV2Diagnostics.timing_analysis.tp1_within_20c > 0 ? ((scalpV2Diagnostics.timing_analysis.tp1_within_20c / scalpV2Diagnostics.total_signals) * 100).toFixed(1) : 0}%
                      </div>
                      <div className="text-[9px] text-slate-400 font-mono">5C: {scalpV2Diagnostics.timing_analysis.tp1_within_5c > 0 ? ((scalpV2Diagnostics.timing_analysis.tp1_within_5c / scalpV2Diagnostics.total_signals) * 100).toFixed(1) : 0}%</div>
                    </div>
                    <div className="p-2.5 bg-slate-900/90 rounded-lg border border-slate-800">
                      <div className="text-[10px] text-slate-400 uppercase font-bold">Score Behavior</div>
                      <div className={`text-xs font-black mt-1 ${scalpV2Diagnostics.score_monotonicity.status === 'MONOTONIC' ? 'text-emerald-400' : 'text-amber-400'}`}>
                        {scalpV2Diagnostics.score_monotonicity.status}
                      </div>
                      <div className="text-[9px] text-slate-400 font-mono">Coverage: {((scalpV2Diagnostics.classified_signals / Math.max(1, scalpV2Diagnostics.total_signals)) * 100).toFixed(0)}% ({scalpV2Diagnostics.unclassified_signals} unclass.)</div>
                    </div>
                  </div>
                </div>

                {/* 2. SETUP ACCOUNTING & RECONCILIATION */}
                <div className="p-3.5 bg-slate-950 rounded-xl border border-slate-800 space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-bold text-slate-300 uppercase tracking-wider">2. Setup Accounting & Reconciliation</span>
                    <span className="text-[10px] font-mono text-emerald-400 bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-800/50">
                      RECONCILED (100%)
                    </span>
                  </div>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
                    <div className="p-2 bg-slate-900 rounded-lg border border-slate-800 flex justify-between">
                      <span className="text-slate-400">Continuation:</span>
                      <span className="font-mono text-slate-200">{scalpV2Diagnostics.setup_accounting.trend_continuation_count}</span>
                    </div>
                    <div className="p-2 bg-slate-900 rounded-lg border border-slate-800 flex justify-between">
                      <span className="text-slate-400">Pullback:</span>
                      <span className="font-mono text-slate-200">{scalpV2Diagnostics.setup_accounting.pullback_count}</span>
                    </div>
                    <div className="p-2 bg-slate-900 rounded-lg border border-slate-800 flex justify-between">
                      <span className="text-slate-400">Breakout:</span>
                      <span className="font-mono text-slate-200">{scalpV2Diagnostics.setup_accounting.momentum_breakout_count}</span>
                    </div>
                    <div className="p-2 bg-slate-900 rounded-lg border border-slate-800 flex justify-between">
                      <span className="text-purple-400">Unclassified:</span>
                      <span className="font-mono font-bold text-purple-300">{scalpV2Diagnostics.setup_accounting.unclassified_count}</span>
                    </div>
                  </div>
                  <div className="text-[10px] text-slate-400 font-mono">
                    Unclassified diagnostic breakdown: NO_SETUP_MATCH ({scalpV2Diagnostics.setup_accounting.unclassified_reasons.NO_SETUP_MATCH ?? 0}), MULTIPLE_MATCHES ({scalpV2Diagnostics.setup_accounting.unclassified_reasons.MULTIPLE_SETUP_MATCHES ?? 0})
                  </div>
                </div>

                {/* 3. SCORE CALIBRATION & MONOTONICITY */}
                <div className="p-3.5 bg-slate-950 rounded-xl border border-slate-800 space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-bold text-slate-300 uppercase tracking-wider">3. Score Calibration & Monotonicity</span>
                    <span className={`text-[10px] font-mono px-2 py-0.5 rounded border ${scalpV2Diagnostics.score_monotonicity.status === 'MONOTONIC' ? 'text-emerald-400 border-emerald-800' : 'text-rose-400 border-rose-800 bg-rose-950/40'}`}>
                      {scalpV2Diagnostics.score_monotonicity.status}
                    </span>
                  </div>
                  <div className="overflow-x-auto rounded-lg border border-slate-800 bg-slate-900">
                    <table className="w-full text-xs text-left">
                      <thead className="bg-slate-950 text-[10px] text-slate-400 uppercase font-mono border-b border-slate-800">
                        <tr>
                          <th className="p-2">Score Bucket</th>
                          <th className="p-2">N (Sample)</th>
                          <th className="p-2">BUY / SELL</th>
                          <th className="p-2 text-sky-400">1C TP1</th>
                          <th className="p-2 text-sky-400">5C TP1</th>
                          <th className="p-2 text-sky-400">20C TP1</th>
                          <th className="p-2 text-rose-400">20C SL</th>
                          <th className="p-2">Neither</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800/60 font-mono text-[11px]">
                        {scalpV2Diagnostics.score_analysis.map((b: ScoreBucketDiagnostic) => (
                          <tr key={b.bucket_label} className="hover:bg-slate-800/30">
                            <td className="p-2 text-slate-200 font-bold">{b.bucket_label}</td>
                            <td className="p-2 text-slate-300">{b.sample_size_n}</td>
                            <td className="p-2 text-slate-400">{b.buy_count}B / {b.sell_count}S</td>
                            <td className="p-2 text-sky-300 font-bold">{b.tp1_hit_rate_1c.toFixed(1)}%</td>
                            <td className="p-2 text-sky-300 font-bold">{b.tp1_hit_rate_5c.toFixed(1)}%</td>
                            <td className="p-2 text-sky-300 font-bold">{b.tp1_hit_rate_20c.toFixed(1)}%</td>
                            <td className="p-2 text-rose-400">{b.sl_rate_20c.toFixed(1)}%</td>
                            <td className="p-2 text-slate-400">{b.neither_rate_20c.toFixed(1)}%</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  {scalpV2Diagnostics.score_monotonicity.anomaly_detected && (
                    <div className="p-2 rounded bg-amber-950/30 border border-amber-800/50 text-[10px] text-amber-300 font-mono">
                      ⚠ {scalpV2Diagnostics.score_monotonicity.details}
                    </div>
                  )}
                </div>

                {/* 4. BUY VS SELL COMPARISON */}
                <div className="p-3.5 bg-slate-950 rounded-xl border border-slate-800 space-y-2">
                  <span className="text-xs font-bold text-slate-300 uppercase tracking-wider">4. BUY vs SELL Directional Asymmetry</span>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                    {Object.entries(scalpV2Diagnostics.direction_analysis).map(([k, d]) => (
                      <div key={k} className="p-3 bg-slate-900 rounded-lg border border-slate-800 space-y-1">
                        <div className="flex justify-between items-center">
                          <span className={`font-black ${k === 'BUY' ? 'text-emerald-400' : 'text-rose-400'}`}>{k} SIGNALS</span>
                          <span className="font-mono text-[10px] text-slate-400">N = {d.sample_size_n}</span>
                        </div>
                        <div className="flex justify-between text-slate-400 text-[11px] font-mono pt-1">
                          <span>20C TP1 Hit Rate:</span>
                          <span className="font-bold text-sky-300">{d.tp1_hit_rate_20c.toFixed(1)}%</span>
                        </div>
                        <div className="flex justify-between text-slate-400 text-[11px] font-mono">
                          <span>20C SL Rate:</span>
                          <span className="font-bold text-rose-400">{d.sl_rate_20c.toFixed(1)}%</span>
                        </div>
                        <div className="flex justify-between text-slate-400 text-[11px] font-mono">
                          <span>Avg Deterministic Score:</span>
                          <span className="font-bold text-slate-200">{d.avg_score.toFixed(1)}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* 5. TIMING FORENSICS & ENTRY TIMING */}
                <div className="p-3.5 bg-slate-950 rounded-xl border border-slate-800 space-y-3">
                  <span className="text-xs font-bold text-slate-300 uppercase tracking-wider">5. Signal Timing & Execution Lag Forensics</span>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-center text-xs">
                    <div className="p-2 bg-slate-900 rounded-lg border border-slate-800">
                      <div className="text-[10px] text-slate-400 font-bold">TP1 within 1C</div>
                      <div className="text-base font-black text-sky-300 mt-0.5">{scalpV2Diagnostics.timing_analysis.tp1_within_1c}</div>
                      <div className="text-[9px] text-slate-500 font-mono">{((scalpV2Diagnostics.timing_analysis.tp1_within_1c / scalpV2Diagnostics.total_signals) * 100).toFixed(1)}% immediate</div>
                    </div>
                    <div className="p-2 bg-slate-900 rounded-lg border border-slate-800">
                      <div className="text-[10px] text-slate-400 font-bold">TP1 within 5C</div>
                      <div className="text-base font-black text-sky-300 mt-0.5">{scalpV2Diagnostics.timing_analysis.tp1_within_5c}</div>
                      <div className="text-[9px] text-slate-500 font-mono">{((scalpV2Diagnostics.timing_analysis.tp1_within_5c / scalpV2Diagnostics.total_signals) * 100).toFixed(1)}% within 5m</div>
                    </div>
                    <div className="p-2 bg-slate-900 rounded-lg border border-slate-800">
                      <div className="text-[10px] text-slate-400 font-bold">Avg Candles to TP1</div>
                      <div className="text-base font-black text-emerald-400 mt-0.5">{scalpV2Diagnostics.timing_analysis.avg_candles_to_tp1 ?? '—'}</div>
                      <div className="text-[9px] text-slate-500 font-mono">Median: {scalpV2Diagnostics.timing_analysis.median_candles_to_tp1 ?? '—'}m</div>
                    </div>
                    <div className="p-2 bg-slate-900 rounded-lg border border-slate-800">
                      <div className="text-[10px] text-slate-400 font-bold">Avg Candles to SL</div>
                      <div className="text-base font-black text-rose-400 mt-0.5">{scalpV2Diagnostics.timing_analysis.avg_candles_to_sl ?? '—'}</div>
                      <div className="text-[9px] text-slate-500 font-mono">Median: {scalpV2Diagnostics.timing_analysis.median_candles_to_sl ?? '—'}m</div>
                    </div>
                  </div>
                  <div className="p-2.5 bg-slate-900 rounded-lg border border-slate-800 text-xs flex justify-between font-mono">
                    <span className="text-slate-400">Entry Classification:</span>
                    <span>
                      <strong className="text-emerald-400">{scalpV2Diagnostics.entry_timing.timely_count} Timely</strong> / <strong className="text-amber-400">{scalpV2Diagnostics.entry_timing.early_count} Early</strong> / <strong className="text-rose-400">{scalpV2Diagnostics.entry_timing.late_count} Late</strong> / <strong className="text-slate-500">{scalpV2Diagnostics.entry_timing.undetermined_count} Undetermined</strong>
                    </span>
                  </div>
                </div>

                {/* 6. FACTOR CONTRIBUTION & PREDICTIVE VALUE */}
                <div className="p-3.5 bg-slate-950 rounded-xl border border-slate-800 space-y-2">
                  <span className="text-xs font-bold text-slate-300 uppercase tracking-wider">6. Factor Influence Analysis</span>
                  <div className="overflow-x-auto rounded-lg border border-slate-800 bg-slate-900">
                    <table className="w-full text-xs text-left">
                      <thead className="bg-slate-950 text-[10px] text-slate-400 uppercase font-mono border-b border-slate-800">
                        <tr>
                          <th className="p-2">Factor</th>
                          <th className="p-2">Avg Weight</th>
                          <th className="p-2 text-emerald-400">Strong Pos Hit Rate</th>
                          <th className="p-2 text-slate-400">Neutral Hit Rate</th>
                          <th className="p-2 text-rose-400">Strong Neg Hit Rate</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800/60 font-mono text-[11px]">
                        {scalpV2Diagnostics.factor_analysis.map((f: FactorDiagnostic) => (
                          <tr key={f.factor_name} className="hover:bg-slate-800/30">
                            <td className="p-2 text-slate-200 font-bold">{f.factor_name}</td>
                            <td className="p-2 text-slate-400">{f.avg_contribution.toFixed(1)}</td>
                            <td className="p-2 text-emerald-300 font-bold">{f.tp1_hit_rate_strongly_positive !== null ? `${f.tp1_hit_rate_strongly_positive.toFixed(1)}% (N=${f.strongly_pos_n})` : '—'}</td>
                            <td className="p-2 text-slate-400">{f.tp1_hit_rate_neutral !== null ? `${f.tp1_hit_rate_neutral.toFixed(1)}% (N=${f.neutral_n})` : '—'}</td>
                            <td className="p-2 text-rose-400">{f.tp1_hit_rate_strongly_negative !== null ? `${f.tp1_hit_rate_strongly_negative.toFixed(1)}% (N=${f.strongly_neg_n})` : '—'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* 7. CLUSTERING & FLIPS */}
                <div className="p-3.5 bg-slate-950 rounded-xl border border-slate-800 space-y-2">
                  <span className="text-xs font-bold text-slate-300 uppercase tracking-wider">7. Signal Clustering & Rapid Direction Reversals</span>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-center text-xs font-mono">
                    <div className="p-2 bg-slate-900 rounded-lg border border-slate-800">
                      <div className="text-[10px] text-slate-400 font-bold">Max in 5m Window</div>
                      <div className="text-base font-black text-amber-300 mt-0.5">{scalpV2Diagnostics.clustering_analysis.max_signals_in_rolling_5m}</div>
                    </div>
                    <div className="p-2 bg-slate-900 rounded-lg border border-slate-800">
                      <div className="text-[10px] text-slate-400 font-bold">Max in 15m Window</div>
                      <div className="text-base font-black text-amber-300 mt-0.5">{scalpV2Diagnostics.clustering_analysis.max_signals_in_rolling_15m}</div>
                    </div>
                    <div className="p-2 bg-slate-900 rounded-lg border border-slate-800">
                      <div className="text-[10px] text-slate-400 font-bold">Direction Flips</div>
                      <div className="text-base font-black text-sky-300 mt-0.5">{scalpV2Diagnostics.flip_analysis.flips_total}</div>
                      <div className="text-[9px] text-slate-500 font-mono">{scalpV2Diagnostics.flip_analysis.flips_per_hour}/h</div>
                    </div>
                    <div className="p-2 bg-slate-900 rounded-lg border border-slate-800">
                      <div className="text-[10px] text-slate-400 font-bold">Same-Dir Clusters</div>
                      <div className="text-base font-black text-purple-300 mt-0.5">{scalpV2Diagnostics.clustering_analysis.same_direction_clusters_count}</div>
                    </div>
                  </div>
                </div>

                {/* 8. WARNINGS & RECOMMENDED NEXT INVESTIGATION */}
                <div className="p-3.5 bg-slate-950 rounded-xl border border-slate-800 space-y-2">
                  <span className="text-xs font-bold text-slate-300 uppercase tracking-wider">8. Recommended Next Investigation</span>
                  <div className="flex flex-wrap gap-1.5">
                    {scalpV2Diagnostics.recommended_next_investigation.map((rec, idx) => (
                      <span key={idx} className="px-2 py-1 rounded bg-sky-950 border border-sky-800 text-sky-300 text-xs font-mono font-bold">
                        {rec}
                      </span>
                    ))}
                  </div>
                  {scalpV2Diagnostics.warnings.length > 0 && (
                    <ul className="space-y-1 text-xs text-amber-300/90 font-mono pt-1">
                      {scalpV2Diagnostics.warnings.map((w, idx) => (
                        <li key={idx} className="flex items-start gap-1.5">
                          <span className="text-amber-400 font-bold shrink-0">⚠</span>
                          <span>{w}</span>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>

                {/* 9. STRICT DISCLAIMER */}
                <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 text-[10px] text-slate-400 text-center italic">
                  {scalpV2Diagnostics.disclaimer}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* HISTORY MODAL */}
      {showHistoryModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-2xl w-full p-6 shadow-2xl space-y-4 max-h-[85vh] flex flex-col">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-base font-black text-white flex items-center gap-2">
                <History className="w-5 h-5 text-sky-400" />
                SCALP V2 Recent Signal History (Latest 50)
              </h3>
              <button onClick={() => setShowHistoryModal(false)} className="text-slate-400 hover:text-white font-bold">✕</button>
            </div>

            <div className="overflow-y-auto flex-1 space-y-2 pr-1">
              {scalpV2History.length > 0 ? (
                scalpV2History.map((item, idx) => (
                  <div key={idx} className="p-3 bg-slate-950 rounded-xl border border-slate-800 flex items-center justify-between text-xs">
                    <div className="flex items-center gap-3">
                      <span className={`font-black px-2 py-0.5 rounded ${
                        item.direction === 'BUY' ? 'bg-emerald-500/20 text-emerald-400' : item.direction === 'SELL' ? 'bg-rose-500/20 text-rose-400' : 'bg-slate-800 text-slate-400'
                      }`}>
                        {item.direction}
                      </span>
                      <div>
                        <div className="font-bold text-slate-200">{item.setup_type.replace('_', ' ')}</div>
                        <div className="text-[10px] text-slate-400 font-mono">{new Date(item.timestamp).toLocaleTimeString()}</div>
                      </div>
                    </div>

                    <div className="text-right font-mono">
                      <div className="text-slate-300">Entry: ${item.entry_price?.toFixed(1) ?? '—'}</div>
                      <div className="text-[10px] text-slate-400">SL: ${item.stop_loss?.toFixed(1) ?? '—'} | TP1: ${item.tp1?.toFixed(1) ?? '—'}</div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-xs text-slate-400 text-center py-8">No recorded signals yet in memory buffer.</div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* COMPARE MODAL */}
      {showCompareModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-2xl w-full p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-base font-black text-white flex items-center gap-2">
                <GitCompare className="w-5 h-5 text-sky-400" />
                SCALP Strategy Comparison — V1 vs V2 Side-by-Side
              </h3>
              <button onClick={() => setShowCompareModal(false)} className="text-slate-400 hover:text-white font-bold">✕</button>
            </div>

            <div className="grid grid-cols-2 gap-4">
              {/* V1 COLUMN */}
              <div className="p-4 bg-slate-950 rounded-xl border border-slate-800 space-y-3">
                <div className="font-black text-slate-200 text-sm border-b border-slate-800 pb-2">SCALP V1 (Baseline)</div>
                <div className="text-xs space-y-1.5">
                  <div className="flex justify-between"><span className="text-slate-400">Direction:</span> <span className="font-bold text-slate-200">{confirmedScalpSignal?.direction ?? 'NO_TRADE'}</span></div>
                  <div className="flex justify-between"><span className="text-slate-400">Alignment Score:</span> <span className="font-mono text-slate-200">{confirmedScalpSignal?.score_breakdown?.normalised_score?.toFixed(0) ?? '—'}/100</span></div>
                  <div className="flex justify-between"><span className="text-slate-400">Design Model:</span> <span className="text-slate-300">Strict Multi-Factor</span></div>
                  <div className="flex justify-between"><span className="text-slate-400">TP1 / TP2 / TP3:</span> <span className="font-mono text-slate-300">1.25R / 2.0R / 3.0R</span></div>
                </div>
              </div>

              {/* V2 COLUMN */}
              <div className="p-4 bg-slate-950 rounded-xl border border-sky-500/30 space-y-3">
                <div className="font-black text-sky-400 text-sm border-b border-slate-800 pb-2">SCALP V2 (Higher Frequency)</div>
                <div className="text-xs space-y-1.5">
                  <div className="flex justify-between"><span className="text-slate-400">Direction:</span> <span className="font-bold text-sky-300">{confirmedScalpV2Signal?.direction ?? 'NO_TRADE'}</span></div>
                  <div className="flex justify-between"><span className="text-slate-400">Alignment Score:</span> <span className="font-mono text-sky-300">{confirmedScalpV2Signal?.alignment_score?.toFixed(0) ?? '—'}/100</span></div>
                  <div className="flex justify-between"><span className="text-slate-400">Setup Pattern:</span> <span className="text-purple-400 font-bold">{confirmedScalpV2Signal?.setup_type.replace('_', ' ') ?? 'NONE'}</span></div>
                  <div className="flex justify-between"><span className="text-slate-400">TP1 / TP2 / TP3:</span> <span className="font-mono text-slate-300">1.0R / 1.5R / 2.0R</span></div>
                </div>
              </div>
            </div>

            <div className="text-[11px] text-slate-400 text-center italic">
              Objective side-by-side research comparison. No subjective winner declared.
            </div>
          </div>
        </div>
      )}
    </section>
  );
};
