import { create } from 'zustand';
import {
  Candle,
  Ticker,
  ConnectionState,
  Timeframe,
  WebSocketMessage,
  IndicatorSnapshot,
  IndicatorHistoryPoint,
  MarketDataQuality,
  MarketRegimeSnapshot,
  MarketStructureSnapshot,
  ResearchSignal,
  ChartOverlaySettings,
} from '../types/market';
import {
  TradePlan,
  MultiStrategyTradeDecisions,
} from '../types/tradeDecision';
import {
  TradingProfileConfig,
  ProfileAnalysisResult,
  ProfileComparisonReport,
} from '../types/profiles';
import { ScalpSignal, ScalpDirection } from '../types/scalp';
import {
  ScalpV2Signal,
  ScalpV2StatsResponse,
  ScalpV2HistoryItem,
  ScalpComparisonResponse,
  ScalpV2EvaluationReport,
  ScalpV2DiagnosticReport,
} from '../types/scalpV2';
import {
  fetchHistoricalKlines,
  fetchTicker,
  fetchIndicators,
  fetchIndicatorHistory,
  fetchRegime,
  fetchStructure,
  fetchSignal,
  fetchSignalHistory,
  fetchTradeDecision,
  fetchTradeDecisionHistory,
  fetchTradingProfiles,
  fetchProfileContext,
  fetchProfileComparison,
  fetchScalpSignal,
  fetchScalpV2Signal,
  fetchScalpV2Stats,
  fetchScalpV2History,
  fetchScalpComparison,
  fetchScalpV2Evaluation,
  fetchScalpV2Diagnostics,
} from '../services/api';

export function formatSymbolPrice(symbol: string, price: number | null | undefined): string {
  if (price === null || price === undefined || isNaN(price)) return '—';
  const sym = symbol.toUpperCase();
  if (sym.includes('XRP')) return price.toFixed(4);
  if (sym.includes('SOL')) return price.toFixed(3);
  return price.toFixed(2);
}

export function formatPercentage(val: number | null | undefined): string {
  if (val === null || val === undefined || isNaN(val)) return '—';
  const prefix = val >= 0 ? '+' : '';
  return `${prefix}${val.toFixed(2)}%`;
}

export function getAlignmentScoreTier(score: number | null | undefined): { label: string; color: string } {
  if (score === null || score === undefined || isNaN(score)) {
    return { label: 'AWAITING', color: 'text-slate-500' };
  }
  if (score >= 80) return { label: 'VERY HIGH', color: 'text-emerald-400' };
  if (score >= 65) return { label: 'HIGH', color: 'text-teal-400' };
  if (score >= 50) return { label: 'MODERATE', color: 'text-blue-400' };
  if (score >= 35) return { label: 'LOW', color: 'text-amber-400' };
  return { label: 'VERY LOW', color: 'text-slate-400' };
}

export interface ScalpStrengthTier {
  label: string;
  badgeClass: string;
  dotColor: string;
  textColor: string;
  description: string;
}

export function getScalpStrengthTier(
  score: number | null | undefined,
  direction: ScalpDirection | null | undefined
): ScalpStrengthTier {
  if (score === null || score === undefined || isNaN(score) || direction === 'NO_TRADE' || !direction) {
    return {
      label: 'NO TRADE',
      badgeClass: 'bg-slate-800 text-slate-400 border border-slate-700',
      dotColor: 'bg-slate-400',
      textColor: 'text-slate-400',
      description: 'System analytical criteria not met for directional entry.',
    };
  }

  const isBuy = direction === 'BUY';
  const isSell = direction === 'SELL';

  if (score >= 80) {
    return {
      label: 'VERY STRONG',
      badgeClass: isBuy
        ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 shadow-emerald-500/10'
        : 'bg-rose-500/20 text-rose-400 border border-rose-500/40 shadow-rose-500/10',
      dotColor: isBuy ? 'bg-emerald-400' : 'bg-rose-400',
      textColor: isBuy ? 'text-emerald-400' : 'text-rose-400',
      description: 'Exceptionally high multi-factor alignment across indicators and timeframes.',
    };
  }
  if (score >= 65) {
    return {
      label: 'STRONG',
      badgeClass: isBuy
        ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30'
        : 'bg-rose-500/15 text-rose-300 border border-rose-500/30',
      dotColor: isBuy ? 'bg-emerald-400' : 'bg-rose-400',
      textColor: isBuy ? 'text-emerald-400' : 'text-rose-400',
      description: 'Multiple analytical factors currently agree with the directional setup.',
    };
  }
  if (score >= 50) {
    return {
      label: 'MODERATE',
      badgeClass: 'bg-amber-500/15 text-amber-300 border border-amber-500/30',
      dotColor: 'bg-amber-400',
      textColor: 'text-amber-400',
      description: 'Moderate analytical alignment; higher likelihood of whipsaw or chop.',
    };
  }
  if (score >= 35) {
    return {
      label: 'WEAK',
      badgeClass: 'bg-orange-500/15 text-orange-400 border border-orange-500/30',
      dotColor: 'bg-orange-400',
      textColor: 'text-orange-400',
      description: 'Conflicting analytical factors with low directional edge.',
    };
  }
  return {
    label: 'VERY WEAK',
    badgeClass: 'bg-slate-800 text-slate-400 border border-slate-700',
    dotColor: 'bg-slate-500',
    textColor: 'text-slate-400',
    description: 'Sub-threshold alignment score. Insufficient directional evidence.',
  };
}

export interface ScalpActionGuidance {
  action: 'TAKE TRADE' | 'WAIT FOR CONFIRMATION' | 'AVOID' | 'NO TRADE';
  badgeClass: string;
  explanation: string;
}

export function getScalpActionGuidance(
  score: number | null | undefined,
  direction: ScalpDirection | null | undefined
): ScalpActionGuidance {
  if (!direction || direction === 'NO_TRADE' || score === null || score === undefined || isNaN(score)) {
    return {
      action: 'NO TRADE',
      badgeClass: 'bg-slate-800 text-slate-300 border-slate-700 hover:bg-slate-700',
      explanation: 'No directional setup currently qualified by the scoring engine.',
    };
  }

  if (score >= 65) {
    return {
      action: 'TAKE TRADE',
      badgeClass: direction === 'BUY'
        ? 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg shadow-emerald-600/30 border-emerald-400/50'
        : 'bg-rose-600 hover:bg-rose-500 text-white shadow-lg shadow-rose-600/30 border-rose-400/50',
      explanation: 'Directional factors pass primary qualification thresholds.',
    };
  }
  if (score >= 50) {
    return {
      action: 'WAIT FOR CONFIRMATION',
      badgeClass: 'bg-amber-600/90 hover:bg-amber-500 text-white shadow-lg shadow-amber-600/25 border-amber-400/50',
      explanation: 'Setup is developing. Wait for candle close confirmation before acting.',
    };
  }
  return {
    action: 'AVOID',
    badgeClass: 'bg-slate-700 hover:bg-slate-600 text-slate-200 border-slate-600',
    explanation: 'Alignment score is weak. Unfavorable risk-to-reward conditions.',
  };
}

interface MarketStoreState {
  symbol: string;
  timeframe: Timeframe;
  connectionState: ConnectionState;
  connectionMessage: string;
  latencyMs: number;
  isStale: boolean;
  candles: Candle[];
  ticker: Ticker | null;
  confirmedSnapshot: IndicatorSnapshot | null;
  realtimeSnapshot: IndicatorSnapshot | null;
  confirmedRegime: MarketRegimeSnapshot | null;
  realtimeRegime: MarketRegimeSnapshot | null;
  confirmedStructure: MarketStructureSnapshot | null;
  realtimeStructure: MarketStructureSnapshot | null;
  confirmedSignal: ResearchSignal | null;
  realtimeSignal: ResearchSignal | null;
  signalHistory: ResearchSignal[];
  
  // Phase 10 Trade Decision State
  confirmedTradeDecision: TradePlan | null;
  realtimeTradeDecision: TradePlan | null;
  multiStrategyDecisions: MultiStrategyTradeDecisions | null;
  selectedStrategyId: string;
  tradeDecisionHistory: TradePlan[];

  // Phase 13A / Phase 12 Scalp Strategy State
  selectedScalpStrategy: 'SCALP_V1' | 'SCALP_V2';
  confirmedScalpSignal: ScalpSignal | null;
  previewScalpSignal: ScalpSignal | null;
  confirmedScalpV2Signal: ScalpV2Signal | null;
  previewScalpV2Signal: ScalpV2Signal | null;
  scalpV2Stats: ScalpV2StatsResponse | null;
  scalpV2History: ScalpV2HistoryItem[];
  scalpComparison: ScalpComparisonResponse | null;
  scalpV2Evaluation: ScalpV2EvaluationReport | null;
  scalpV2Diagnostics: ScalpV2DiagnosticReport | null;
  isScalpLoading: boolean;
  scalpError: string | null;

  // Phase 12 Trading Profiles State
  selectedProfileId: string;
  profilesList: TradingProfileConfig[];
  activeProfileResult: ProfileAnalysisResult | null;
  profileComparison: ProfileComparisonReport | null;

  quality: MarketDataQuality | null;
  indicatorHistory: IndicatorHistoryPoint[];
  chartOverlays: ChartOverlaySettings;
  cleanChart: boolean;
  isLoading: boolean;
  error: string | null;
  lastUpdated: number;

  setSymbol: (symbol: string) => void;
  setTimeframe: (timeframe: Timeframe) => void;
  setProfile: (profileId: string) => void;
  setSelectedStrategyId: (strategyId: string) => void;
  setSelectedScalpStrategy: (strategy: 'SCALP_V1' | 'SCALP_V2') => void;
  setConnectionState: (state: ConnectionState, message?: string) => void;
  toggleOverlay: (name: keyof ChartOverlaySettings) => void;
  toggleCleanChart: () => void;
  loadHistoricalData: () => Promise<void>;
  loadProfileComparison: () => Promise<void>;
  loadScalpSignal: () => Promise<void>;
  loadScalpV2Signal: () => Promise<void>;
  loadScalpV2Stats: () => Promise<void>;
  loadScalpV2History: () => Promise<void>;
  loadScalpComparison: () => Promise<void>;
  loadScalpV2Evaluation: () => Promise<void>;
  loadScalpV2Diagnostics: () => Promise<void>;
  setScalpSignal: (confirmed: ScalpSignal | null, preview: ScalpSignal | null) => void;
  setScalpV2Signal: (confirmed: ScalpV2Signal | null, preview: ScalpV2Signal | null) => void;
  handleWebSocketMessage: (msg: WebSocketMessage) => void;
}

export const useMarketStore = create<MarketStoreState>((set, get) => ({
  symbol: 'BTCUSDT',
  timeframe: '1m',
  connectionState: 'OFFLINE',
  connectionMessage: 'Initializing...',
  latencyMs: 12,
  isStale: false,
  candles: [],
  ticker: null,
  confirmedSnapshot: null,
  realtimeSnapshot: null,
  confirmedRegime: null,
  realtimeRegime: null,
  confirmedStructure: null,
  realtimeStructure: null,
  confirmedSignal: null,
  realtimeSignal: null,
  signalHistory: [],
  
  // Phase 10
  confirmedTradeDecision: null,
  realtimeTradeDecision: null,
  multiStrategyDecisions: null,
  selectedStrategyId: 'EXP_A2_PULLBACK_VWAP',
  tradeDecisionHistory: [],

  // Phase 13A & 13B Scalp Strategy State
  selectedScalpStrategy: 'SCALP_V2',
  confirmedScalpSignal: null,
  previewScalpSignal: null,
  confirmedScalpV2Signal: null,
  previewScalpV2Signal: null,
  scalpV2Stats: null,
  scalpV2History: [],
  scalpComparison: null,
  scalpV2Evaluation: null,
  scalpV2Diagnostics: null,
  isScalpLoading: false,
  scalpError: null,

  // Phase 12
  selectedProfileId: 'SCALP_1M_V1',
  profilesList: [],
  activeProfileResult: null,
  profileComparison: null,

  quality: null,
  indicatorHistory: [],
  chartOverlays: {
    ema9: true,
    ema21: true,
    ema50: false,
    ema200: false,
    vwap: true,
    bollinger: false,
    supertrend: false,
    swings: true,
    bos: true,
    zones: true,
    signalMarkers: true,
    tradePlan: true,
  },
  cleanChart: false,
  isLoading: false,
  error: null,
  lastUpdated: Date.now(),

  setSymbol: (symbol: string) => {
    if (get().symbol !== symbol) {
      set({
        symbol,
        candles: [],
        ticker: null,
        confirmedSnapshot: null,
        realtimeSnapshot: null,
        confirmedRegime: null,
        realtimeRegime: null,
        confirmedStructure: null,
        realtimeStructure: null,
        confirmedSignal: null,
        realtimeSignal: null,
        signalHistory: [],
        confirmedTradeDecision: null,
        realtimeTradeDecision: null,
        multiStrategyDecisions: null,
        tradeDecisionHistory: [],
        confirmedScalpSignal: null,
        previewScalpSignal: null,
        activeProfileResult: null,
        isLoading: true,
      });
      get().loadHistoricalData();
    }
  },

  setTimeframe: (timeframe: Timeframe) => {
    if (get().timeframe !== timeframe) {
      // Map timeframe to profile
      let targetProfile = 'TRADING_15M_V1';
      if (timeframe === '1m') targetProfile = 'SCALP_1M_V1';
      else if (timeframe === '5m') targetProfile = 'INTRADAY_5M_V1';
      else if (timeframe === '15m') targetProfile = 'TRADING_15M_V1';
      else if (timeframe === '4h') targetProfile = 'SWING_4H_V1';
      else if (timeframe === '1d') targetProfile = 'POSITION_1D_V1';

      set({
        timeframe,
        selectedProfileId: targetProfile,
        candles: [],
        confirmedSnapshot: null,
        realtimeSnapshot: null,
        confirmedRegime: null,
        realtimeRegime: null,
        confirmedStructure: null,
        realtimeStructure: null,
        confirmedSignal: null,
        realtimeSignal: null,
        signalHistory: [],
        confirmedTradeDecision: null,
        realtimeTradeDecision: null,
        multiStrategyDecisions: null,
        tradeDecisionHistory: [],
        confirmedScalpSignal: null,
        previewScalpSignal: null,
        activeProfileResult: null,
        isLoading: true,
      });
      get().loadHistoricalData();
    }
  },

  setProfile: (profileId: string) => {
    if (get().selectedProfileId !== profileId) {
      let targetTf: Timeframe = '15m';
      if (profileId === 'SCALP_1M_V1') targetTf = '1m';
      else if (profileId === 'INTRADAY_5M_V1') targetTf = '5m';
      else if (profileId === 'TRADING_15M_V1') targetTf = '15m';
      else if (profileId === 'SWING_4H_V1') targetTf = '4h';
      else if (profileId === 'POSITION_1D_V1') targetTf = '1d';

      // Immediate wipe of state to prevent stale leakage on profile switch
      set({
        selectedProfileId: profileId,
        timeframe: targetTf,
        candles: [],
        confirmedSnapshot: null,
        realtimeSnapshot: null,
        confirmedRegime: null,
        realtimeRegime: null,
        confirmedStructure: null,
        realtimeStructure: null,
        confirmedSignal: null,
        realtimeSignal: null,
        signalHistory: [],
        confirmedTradeDecision: null,
        realtimeTradeDecision: null,
        multiStrategyDecisions: null,
        tradeDecisionHistory: [],
        confirmedScalpSignal: null,
        previewScalpSignal: null,
        activeProfileResult: null,
        isLoading: true,
      });
      get().loadHistoricalData();
    }
  },

  setSelectedStrategyId: (strategyId: string) => {
    if (get().selectedStrategyId !== strategyId) {
      set({ selectedStrategyId: strategyId });
      const multi = get().multiStrategyDecisions;
      if (multi && multi.candidate_decisions && multi.candidate_decisions[strategyId]) {
        set({ confirmedTradeDecision: multi.candidate_decisions[strategyId] });
      } else {
        get().loadHistoricalData();
      }
    }
  },

  setConnectionState: (state: ConnectionState, message?: string) => {
    set({
      connectionState: state,
      connectionMessage: message || (state === 'LIVE' ? 'Connected' : state),
      isStale: state === 'OFFLINE' || state === 'RECONNECTING',
    });
  },

  toggleOverlay: (name: keyof ChartOverlaySettings) => {
    set((state) => ({
      chartOverlays: {
        ...state.chartOverlays,
        [name]: !state.chartOverlays[name],
      },
    }));
  },

  toggleCleanChart: () => {
    set((state) => ({ cleanChart: !state.cleanChart }));
  },

  setSelectedScalpStrategy: (strategy: 'SCALP_V1' | 'SCALP_V2') => {
    if (get().selectedScalpStrategy !== strategy) {
      set({ selectedScalpStrategy: strategy });
      get().loadHistoricalData();
    }
  },

  setScalpSignal: (confirmed: ScalpSignal | null, preview: ScalpSignal | null) => {
    set({
      confirmedScalpSignal: confirmed,
      previewScalpSignal: preview,
      isScalpLoading: false,
      scalpError: null,
    });
  },

  setScalpV2Signal: (confirmed: ScalpV2Signal | null, preview: ScalpV2Signal | null) => {
    set({
      confirmedScalpV2Signal: confirmed,
      previewScalpV2Signal: preview,
      isScalpLoading: false,
      scalpError: null,
    });
  },

  loadScalpSignal: async () => {
    const { symbol } = get();
    set({ isScalpLoading: true, scalpError: null });
    try {
      const res = await fetchScalpSignal(symbol, true);
      set({
        confirmedScalpSignal: res.confirmed_signal,
        previewScalpSignal: res.preview_signal ?? null,
        isScalpLoading: false,
        scalpError: null,
      });
    } catch (err: any) {
      set({ scalpError: err.message || 'Failed to fetch Scalp V1 signal', isScalpLoading: false });
    }
  },

  loadScalpV2Signal: async () => {
    const { symbol } = get();
    set({ isScalpLoading: true, scalpError: null });
    try {
      const res = await fetchScalpV2Signal(symbol, true);
      set({
        confirmedScalpV2Signal: res.confirmed_signal,
        previewScalpV2Signal: res.preview_signal,
        isScalpLoading: false,
      });
    } catch (err: any) {
      set({ scalpError: err.message || 'Failed to fetch Scalp V2 signal', isScalpLoading: false });
    }
  },

  loadScalpV2Stats: async () => {
    const { symbol } = get();
    try {
      const stats = await fetchScalpV2Stats(symbol);
      set({ scalpV2Stats: stats });
    } catch (err) {
      console.error('Error loading Scalp V2 stats:', err);
    }
  },

  loadScalpV2History: async () => {
    const { symbol } = get();
    try {
      const history = await fetchScalpV2History(symbol, 50);
      set({ scalpV2History: history });
    } catch (err) {
      console.error('Error loading Scalp V2 history:', err);
    }
  },

  loadScalpComparison: async () => {
    const { symbol } = get();
    try {
      const comp = await fetchScalpComparison(symbol);
      set({ scalpComparison: comp });
    } catch (err) {
      console.error('Error loading Scalp comparison:', err);
    }
  },

  loadScalpV2Evaluation: async () => {
    const { symbol } = get();
    try {
      const report = await fetchScalpV2Evaluation(symbol, 1000);
      set({ scalpV2Evaluation: report });
    } catch (err) {
      console.error('Error loading Scalp V2 evaluation report:', err);
    }
  },

  loadScalpV2Diagnostics: async () => {
    const { symbol } = get();
    try {
      const diag = await fetchScalpV2Diagnostics(symbol, 1000);
      set({ scalpV2Diagnostics: diag });
    } catch (err) {
      console.error('Error loading Scalp V2 diagnostics:', err);
    }
  },

  loadHistoricalData: async () => {
    const { symbol, timeframe, selectedStrategyId, selectedProfileId } = get();
    const startTime = Date.now();
    set({ isLoading: true, error: null });
    try {
      const [
        candles,
        ticker,
        indicatorRes,
        history,
        regimeRes,
        structureRes,
        signalRes,
        sigHistory,
        decisionRes,
        decHistory,
        profiles,
        profContext,
        scalpRes,
        scalpV2Res,
        scalpV2StatsRes,
        scalpV2HistoryRes,
        scalpV2EvalRes,
        scalpV2DiagRes,
      ] = await Promise.all([
        fetchHistoricalKlines(symbol, timeframe, 300),
        fetchTicker(symbol).catch(() => null),
        fetchIndicators(symbol, timeframe, true).catch(() => null),
        fetchIndicatorHistory(symbol, timeframe, 300).catch(() => []),
        fetchRegime(symbol, timeframe, true).catch(() => null),
        fetchStructure(symbol, timeframe, true).catch(() => null),
        fetchSignal(symbol, timeframe, true).catch(() => null),
        fetchSignalHistory(symbol, timeframe, 50).catch(() => []),
        fetchTradeDecision(symbol, timeframe, true, selectedStrategyId).catch(() => null),
        fetchTradeDecisionHistory(symbol, timeframe, selectedStrategyId, 50).catch(() => []),
        fetchTradingProfiles().catch(() => []),
        fetchProfileContext(selectedProfileId, symbol, selectedStrategyId).catch(() => null),
        fetchScalpSignal(symbol, true).catch(() => null),
        fetchScalpV2Signal(symbol, true).catch(() => null),
        fetchScalpV2Stats(symbol).catch(() => null),
        fetchScalpV2History(symbol, 50).catch(() => []),
        fetchScalpV2Evaluation(symbol, 1000).catch(() => null),
        fetchScalpV2Diagnostics(symbol, 1000).catch(() => null),
      ]);

      const latency = Math.max(5, Math.min(250, Date.now() - startTime));

      set({
        candles,
        ticker: ticker || get().ticker,
        confirmedSnapshot: indicatorRes?.confirmed_snapshot || null,
        realtimeSnapshot: indicatorRes?.realtime_snapshot || null,
        confirmedRegime: regimeRes?.confirmed_snapshot || null,
        realtimeRegime: regimeRes?.realtime_snapshot || null,
        confirmedStructure: structureRes?.confirmed_snapshot || null,
        realtimeStructure: structureRes?.realtime_snapshot || null,
        confirmedSignal: signalRes?.confirmed_signal || null,
        realtimeSignal: signalRes?.realtime_signal || null,
        signalHistory: sigHistory || [],
        confirmedTradeDecision: decisionRes?.confirmed_decision || null,
        realtimeTradeDecision: decisionRes?.realtime_decision || null,
        multiStrategyDecisions: decisionRes?.multi_strategy_decisions || null,
        tradeDecisionHistory: decHistory || [],
        confirmedScalpSignal: scalpRes?.confirmed_signal || null,
        previewScalpSignal: scalpRes?.preview_signal || null,
        confirmedScalpV2Signal: scalpV2Res?.confirmed_signal || null,
        previewScalpV2Signal: scalpV2Res?.preview_signal || null,
        scalpV2Stats: scalpV2StatsRes || null,
        scalpV2History: scalpV2HistoryRes || [],
        scalpV2Evaluation: scalpV2EvalRes || null,
        scalpV2Diagnostics: scalpV2DiagRes || null,
        profilesList: profiles || [],
        activeProfileResult: profContext || null,
        quality: indicatorRes?.quality || null,
        indicatorHistory: history || [],
        latencyMs: latency,
        isStale: false,
        isLoading: false,
        isScalpLoading: false,
        lastUpdated: Date.now(),
      });
    } catch (err: any) {
      console.error('Error loading historical market data:', err);
      set({
        error: err.message || 'Failed to load historical data',
        isStale: true,
        isLoading: false,
      });
    }
  },

  loadProfileComparison: async () => {
    const { symbol } = get();
    try {
      const comp = await fetchProfileComparison(symbol);
      set({ profileComparison: comp });
    } catch (err) {
      console.error('Error loading profile comparison:', err);
    }
  },

  handleWebSocketMessage: (msg: WebSocketMessage) => {
    const { symbol, timeframe, candles } = get();

    if (msg.symbol !== symbol || msg.timeframe !== timeframe) {
      return;
    }

    if (msg.ticker) {
      set({ ticker: msg.ticker, lastUpdated: Date.now(), isStale: false });
    }

    if (msg.indicators) {
      set({
        realtimeSnapshot: msg.indicators.realtime || get().realtimeSnapshot,
        confirmedSnapshot: msg.indicators.confirmed || get().confirmedSnapshot,
      });
    }

    if (msg.regime) {
      set({
        realtimeRegime: msg.regime.realtime || get().realtimeRegime,
        confirmedRegime: msg.regime.confirmed || get().confirmedRegime,
      });
    }

    if (msg.structure) {
      set({
        realtimeStructure: msg.structure.realtime || get().realtimeStructure,
        confirmedStructure: msg.structure.confirmed || get().confirmedStructure,
      });
    }

    if (msg.signal) {
      set({
        realtimeSignal: msg.signal.realtime || get().realtimeSignal,
        confirmedSignal: msg.signal.confirmed || get().confirmedSignal,
      });
    }

    if (msg.trade_decision) {
      set({
        realtimeTradeDecision: msg.trade_decision.realtime || get().realtimeTradeDecision,
        confirmedTradeDecision: msg.trade_decision.confirmed || get().confirmedTradeDecision,
      });
    }

    if (msg.candle) {
      const incomingCandle = msg.candle;
      const updatedCandles = [...candles];

      if (updatedCandles.length === 0) {
        set({ candles: [incomingCandle], lastUpdated: Date.now(), isStale: false });
        return;
      }

      const lastIdx = updatedCandles.length - 1;
      const lastCandle = updatedCandles[lastIdx];

      if (lastCandle.timestamp === incomingCandle.timestamp) {
        updatedCandles[lastIdx] = incomingCandle;
      } else if (incomingCandle.timestamp > lastCandle.timestamp) {
        updatedCandles.push(incomingCandle);
        if (updatedCandles.length > 500) {
          updatedCandles.shift();
        }
      }

      set({ candles: updatedCandles, lastUpdated: Date.now(), isStale: false });
    }
  },
}));
