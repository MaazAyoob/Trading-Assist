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
  setConnectionState: (state: ConnectionState, message?: string) => void;
  toggleOverlay: (name: keyof ChartOverlaySettings) => void;
  toggleCleanChart: () => void;
  loadHistoricalData: () => Promise<void>;
  loadProfileComparison: () => Promise<void>;
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
        profilesList: profiles || [],
        activeProfileResult: profContext || null,
        quality: indicatorRes?.quality || null,
        indicatorHistory: history || [],
        latencyMs: latency,
        isStale: false,
        isLoading: false,
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
