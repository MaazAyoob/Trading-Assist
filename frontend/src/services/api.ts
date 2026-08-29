import {
  Candle,
  Ticker,
  MarketConnectionStatus,
  MarketDataQuality,
  IndicatorSnapshot,
  IndicatorHistoryPoint,
  MarketRegimeSnapshot,
  MarketStructureSnapshot,
  ResearchSignal,
  Timeframe,
} from '../types/market';
import {
  BacktestRun,
  BacktestRunSummaryItem,
  BacktestMetrics,
  SignalOutcome,
} from '../types/backtesting';
import {
  TradePlan,
  MultiStrategyTradeDecisions,
} from '../types/tradeDecision';
import { ScalpResponse } from '../types/scalp';
import {
  ScalpV2Response,
  ScalpV2StatsResponse,
  ScalpV2HistoryItem,
  ScalpComparisonResponse,
  ScalpV2EvaluationReport,
  ScalpV2DiagnosticReport,
} from '../types/scalpV2';

/**
 * Automatically resolve and normalize API base URL.
 * Handles both root URLs (https://trading-assist.onrender.com)
 * and full v1 endpoints (https://trading-assist.onrender.com/api/v1).
 */
export function getApiBaseUrl(): string {
  const raw = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
  const clean = raw.replace(/\/+$/, '');
  return clean.endsWith('/api/v1') ? clean : `${clean}/api/v1`;
}

/**
 * Automatically derive WebSocket base URL from environment or VITE_API_BASE_URL.
 * Converts https:// -> wss:// and http:// -> ws:// seamlessly.
 */
export function getWsBaseUrl(): string {
  if (import.meta.env.VITE_WS_BASE_URL) {
    return import.meta.env.VITE_WS_BASE_URL.replace(/\/+$/, '');
  }
  const rawApi = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
  const cleanApi = rawApi.replace(/\/+$/, '').replace(/\/api\/v1$/, '');
  const wsProtocol = cleanApi.startsWith('https://') ? 'wss://' : 'ws://';
  const host = cleanApi.replace(/^https?:\/\//, '');
  return `${wsProtocol}${host}/ws`;
}

export const API_BASE = getApiBaseUrl();

// Production diagnostics log
if (typeof window !== 'undefined') {
  console.log(`[Trading Platform Config] Active API_BASE: ${API_BASE} | Active WS_BASE: ${getWsBaseUrl()}`);
}

export async function fetchScalpSignal(
  symbol: string = 'BTCUSDT',
  includePreview: boolean = true
): Promise<ScalpResponse> {
  const url = `${API_BASE}/scalp?symbol=${encodeURIComponent(symbol)}&include_preview=${includePreview}`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch scalp signal: ${response.statusText}`);
  }
  return response.json();
}

export async function fetchScalpV2Signal(
  symbol: string = 'BTCUSDT',
  includePreview: boolean = true
): Promise<ScalpV2Response> {
  const url = `${API_BASE}/scalp-v2?symbol=${encodeURIComponent(symbol)}&include_preview=${includePreview}`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch scalp v2 signal: ${response.statusText}`);
  }
  return response.json();
}

export async function fetchScalpV2Stats(
  symbol: string = 'BTCUSDT'
): Promise<ScalpV2StatsResponse> {
  const url = `${API_BASE}/scalp-v2/stats?symbol=${encodeURIComponent(symbol)}`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch scalp v2 stats: ${response.statusText}`);
  }
  return response.json();
}

export async function fetchScalpV2History(
  symbol: string = 'BTCUSDT',
  limit: number = 50
): Promise<ScalpV2HistoryItem[]> {
  const url = `${API_BASE}/scalp-v2/history?symbol=${encodeURIComponent(symbol)}&limit=${limit}`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch scalp v2 history: ${response.statusText}`);
  }
  return response.json();
}

export async function fetchScalpComparison(
  symbol: string = 'BTCUSDT'
): Promise<ScalpComparisonResponse> {
  const url = `${API_BASE}/scalp/compare?symbol=${encodeURIComponent(symbol)}`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch scalp comparison: ${response.statusText}`);
  }
  return response.json();
}

export async function fetchScalpV2Evaluation(
  symbol: string = 'BTCUSDT',
  limit: number = 1000
): Promise<ScalpV2EvaluationReport> {
  const url = `${API_BASE}/scalp-v2/evaluation?symbol=${encodeURIComponent(symbol)}&limit=${limit}`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch scalp v2 evaluation: ${response.statusText}`);
  }
  return response.json();
}

export async function fetchScalpV2Diagnostics(
  symbol: string = 'BTCUSDT',
  limit: number = 1000
): Promise<ScalpV2DiagnosticReport> {
  const url = `${API_BASE}/scalp-v2/diagnostics?symbol=${encodeURIComponent(symbol)}&limit=${limit}`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch scalp v2 diagnostics: ${response.statusText}`);
  }
  return response.json();
}


export async function fetchHistoricalKlines(
  symbol: string = 'BTCUSDT',
  timeframe: Timeframe = '15m',
  limit: number = 300
): Promise<Candle[]> {
  const url = `${API_BASE}/market/klines?symbol=${encodeURIComponent(symbol)}&timeframe=${encodeURIComponent(timeframe)}&limit=${limit}`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch historical klines: ${response.statusText}`);
  }
  return response.json();
}

export async function fetchTicker(symbol: string = 'BTCUSDT'): Promise<Ticker> {
  const url = `${API_BASE}/market/ticker?symbol=${encodeURIComponent(symbol)}`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch ticker: ${response.statusText}`);
  }
  return response.json();
}

export async function fetchMarketStatus(
  symbol: string = 'BTCUSDT',
  timeframe: Timeframe = '15m'
): Promise<MarketConnectionStatus> {
  const url = `${API_BASE}/market/status?symbol=${encodeURIComponent(symbol)}&timeframe=${encodeURIComponent(timeframe)}`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch market status: ${response.statusText}`);
  }
  return response.json();
}

export async function fetchIndicators(
  symbol: string = 'BTCUSDT',
  timeframe: Timeframe = '15m',
  includeRealtime: boolean = true
): Promise<{
  symbol: string;
  timeframe: string;
  quality: MarketDataQuality;
  latest_candle: Candle | null;
  confirmed_snapshot: IndicatorSnapshot;
  realtime_snapshot: IndicatorSnapshot | null;
  calculation_timestamp: number;
}> {
  const url = `${API_BASE}/analysis/indicators?symbol=${encodeURIComponent(symbol)}&timeframe=${encodeURIComponent(timeframe)}&include_realtime=${includeRealtime}`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch indicators: ${response.statusText}`);
  }
  return response.json();
}

export async function fetchIndicatorHistory(
  symbol: string = 'BTCUSDT',
  timeframe: Timeframe = '15m',
  limit: number = 300
): Promise<IndicatorHistoryPoint[]> {
  const url = `${API_BASE}/analysis/indicators/history?symbol=${encodeURIComponent(symbol)}&timeframe=${encodeURIComponent(timeframe)}&limit=${limit}`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch indicator history: ${response.statusText}`);
  }
  return response.json();
}

export async function fetchRegime(
  symbol: string = 'BTCUSDT',
  timeframe: Timeframe = '15m',
  includeRealtime: boolean = true
): Promise<{
  symbol: string;
  timeframe: string;
  quality: MarketDataQuality;
  confirmed_snapshot: MarketRegimeSnapshot;
  realtime_snapshot: MarketRegimeSnapshot | null;
  calculation_timestamp: number;
}> {
  const url = `${API_BASE}/analysis/regime?symbol=${encodeURIComponent(symbol)}&timeframe=${encodeURIComponent(timeframe)}&include_realtime=${includeRealtime}`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch regime: ${response.statusText}`);
  }
  return response.json();
}

export async function fetchStructure(
  symbol: string = 'BTCUSDT',
  timeframe: Timeframe = '15m',
  includeRealtime: boolean = true
): Promise<{
  symbol: string;
  timeframe: string;
  quality: MarketDataQuality;
  confirmed_snapshot: MarketStructureSnapshot;
  realtime_snapshot: MarketStructureSnapshot | null;
  calculation_timestamp: number;
}> {
  const url = `${API_BASE}/analysis/structure?symbol=${encodeURIComponent(symbol)}&timeframe=${encodeURIComponent(timeframe)}&include_realtime=${includeRealtime}`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch structure: ${response.statusText}`);
  }
  return response.json();
}

export async function fetchSignal(
  symbol: string = 'BTCUSDT',
  timeframe: Timeframe = '15m',
  includeRealtime: boolean = true
): Promise<{
  symbol: string;
  timeframe: string;
  quality: MarketDataQuality;
  confirmed_signal: ResearchSignal;
  realtime_signal: ResearchSignal | null;
  calculation_timestamp: number;
}> {
  const url = `${API_BASE}/analysis/signal?symbol=${encodeURIComponent(symbol)}&timeframe=${encodeURIComponent(timeframe)}&include_realtime=${includeRealtime}`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch research signal: ${response.statusText}`);
  }
  return response.json();
}

export async function fetchSignalHistory(
  symbol: string = 'BTCUSDT',
  timeframe: Timeframe = '15m',
  limit: number = 50
): Promise<ResearchSignal[]> {
  const url = `${API_BASE}/analysis/signal/history?symbol=${encodeURIComponent(symbol)}&timeframe=${encodeURIComponent(timeframe)}&limit=${limit}`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch signal history: ${response.statusText}`);
  }
  return response.json();
}

export async function fetchSignalExplain(
  symbol: string = 'BTCUSDT',
  timeframe: Timeframe = '15m',
  timestamp?: number
): Promise<ResearchSignal> {
  const tsParam = timestamp ? `&timestamp=${timestamp}` : '';
  const url = `${API_BASE}/analysis/signal/explain?symbol=${encodeURIComponent(symbol)}&timeframe=${encodeURIComponent(timeframe)}${tsParam}`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch signal explanation: ${response.statusText}`);
  }
  return response.json();
}

export async function fetchDataQuality(
  symbol: string = 'BTCUSDT',
  timeframe: Timeframe = '15m'
): Promise<MarketDataQuality> {
  const url = `${API_BASE}/analysis/quality?symbol=${encodeURIComponent(symbol)}&timeframe=${encodeURIComponent(timeframe)}`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch data quality: ${response.statusText}`);
  }
  return response.json();
}

// ==========================================
// Phase 6 Backtesting API Methods
// ==========================================

export async function runBacktest(params: {
  symbol?: string;
  timeframe?: Timeframe;
  candle_count?: number;
  warmup_bars?: number;
  horizons?: number[];
  fee_bps?: number;
  slippage_bps?: number;
}): Promise<BacktestRun> {
  const url = `${API_BASE}/backtesting/run`;
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      symbol: params.symbol || 'BTCUSDT',
      timeframe: params.timeframe || '15m',
      candle_count: params.candle_count || 300,
      warmup_bars: params.warmup_bars || 50,
      horizons: params.horizons || [1, 3, 5, 10, 20],
      fee_bps: params.fee_bps || 0.0,
      slippage_bps: params.slippage_bps || 0.0,
    }),
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(err.detail || `Backtest failed: ${response.statusText}`);
  }
  return response.json();
}

export async function fetchBacktestRuns(
  symbol?: string,
  timeframe?: string,
  limit: number = 20
): Promise<BacktestRunSummaryItem[]> {
  let url = `${API_BASE}/backtesting/runs?limit=${limit}`;
  if (symbol) url += `&symbol=${encodeURIComponent(symbol)}`;
  if (timeframe) url += `&timeframe=${encodeURIComponent(timeframe)}`;

  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch backtest runs: ${response.statusText}`);
  }
  return response.json();
}

export async function fetchBacktestRun(runId: string): Promise<BacktestRun> {
  const url = `${API_BASE}/backtesting/runs/${encodeURIComponent(runId)}`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch backtest run: ${response.statusText}`);
  }
  return response.json();
}

export async function fetchForensicsSummary(): Promise<any> {
  const url = `${API_BASE}/analysis/forensics/summary`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch forensics summary: ${response.statusText}`);
  }
  return response.json();
}

export async function fetchStrategyResearchRegistry(): Promise<Record<string, any>> {
  const url = `${API_BASE}/strategy-research/registry`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch research registry: ${response.statusText}`);
  }
  return response.json();
}

export async function fetchStrategyResearchComparison(expId: string, partition: string = 'VALIDATION'): Promise<any> {
  const url = `${API_BASE}/strategy-research/experiments/${encodeURIComponent(expId)}/comparison?partition=${encodeURIComponent(partition)}`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch research comparison: ${response.statusText}`);
  }
  return response.json();
}

export async function fetchShadowStatus(): Promise<any> {
  const url = `${API_BASE}/shadow/status`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch shadow status: ${response.statusText}`);
  }
  return response.json();
}

export async function fetchShadowSessions(): Promise<any[]> {
  const url = `${API_BASE}/shadow/sessions`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch shadow sessions: ${response.statusText}`);
  }
  return response.json();
}

export async function startShadowSession(symbol: string = 'BTCUSDT', timeframe: string = '15m'): Promise<any> {
  const url = `${API_BASE}/shadow/sessions/start?symbol=${encodeURIComponent(symbol)}&timeframe=${encodeURIComponent(timeframe)}`;
  const response = await fetch(url, { method: 'POST' });
  if (!response.ok) {
    throw new Error(`Failed to start shadow session: ${response.statusText}`);
  }
  return response.json();
}

export async function pauseShadowSession(sessionId: string): Promise<any> {
  const url = `${API_BASE}/shadow/sessions/${encodeURIComponent(sessionId)}/pause`;
  const response = await fetch(url, { method: 'POST' });
  if (!response.ok) {
    throw new Error(`Failed to pause shadow session: ${response.statusText}`);
  }
  return response.json();
}

export async function resumeShadowSession(sessionId: string): Promise<any> {
  const url = `${API_BASE}/shadow/sessions/${encodeURIComponent(sessionId)}/resume`;
  const response = await fetch(url, { method: 'POST' });
  if (!response.ok) {
    throw new Error(`Failed to resume shadow session: ${response.statusText}`);
  }
  return response.json();
}

export async function stopShadowSession(sessionId: string): Promise<any> {
  const url = `${API_BASE}/shadow/sessions/${encodeURIComponent(sessionId)}/stop`;
  const response = await fetch(url, { method: 'POST' });
  if (!response.ok) {
    throw new Error(`Failed to stop shadow session: ${response.statusText}`);
  }
  return response.json();
}

export async function fetchShadowSignals(sessionId: string, candidateId?: string): Promise<any[]> {
  let url = `${API_BASE}/shadow/sessions/${encodeURIComponent(sessionId)}/signals?limit=200`;
  if (candidateId) {
    url += `&candidate_id=${encodeURIComponent(candidateId)}`;
  }
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch shadow signals: ${response.statusText}`);
  }
  return response.json();
}

export async function fetchShadowDrift(sessionId: string): Promise<Record<string, any[]>> {
  const url = `${API_BASE}/shadow/sessions/${encodeURIComponent(sessionId)}/drift`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch shadow drift: ${response.statusText}`);
  }
  return response.json();
}

export async function fetchShadowAlerts(sessionId?: string): Promise<any[]> {
  let url = `${API_BASE}/shadow/alerts?limit=50`;
  if (sessionId) {
    url += `&session_id=${encodeURIComponent(sessionId)}`;
  }
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch shadow alerts: ${response.statusText}`);
  }
  return response.json();
}

export async function fetchBacktestMetrics(runId: string): Promise<BacktestMetrics> {
  const url = `${API_BASE}/backtesting/runs/${encodeURIComponent(runId)}/metrics`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch backtest metrics: ${response.statusText}`);
  }
  return response.json();
}

export async function fetchBacktestSignals(runId: string, limit: number = 100): Promise<SignalOutcome[]> {
  const url = `${API_BASE}/backtesting/runs/${encodeURIComponent(runId)}/signals?limit=${limit}`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch backtest signals: ${response.statusText}`);
  }
  return response.json();
}

// ==========================================
// Phase 10 Trade Decision API Methods
// ==========================================

export async function fetchTradeDecision(
  symbol: string = 'BTCUSDT',
  timeframe: Timeframe = '15m',
  includeRealtime: boolean = true,
  strategyContextId: string = 'EXP_A2_PULLBACK_VWAP'
): Promise<{
  symbol: string;
  timeframe: string;
  quality: MarketDataQuality;
  confirmed_decision: TradePlan;
  realtime_decision: TradePlan | null;
  multi_strategy_decisions: MultiStrategyTradeDecisions;
  calculation_timestamp: number;
}> {
  const url = `${API_BASE}/trade-decision?symbol=${encodeURIComponent(symbol)}&timeframe=${encodeURIComponent(timeframe)}&include_realtime=${includeRealtime}&strategy_context_id=${encodeURIComponent(strategyContextId)}`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch trade decision: ${response.statusText}`);
  }
  return response.json();
}

export async function fetchTradeDecisionHistory(
  symbol: string = 'BTCUSDT',
  timeframe: Timeframe = '15m',
  strategyContextId: string = 'EXP_A2_PULLBACK_VWAP',
  limit: number = 50
): Promise<TradePlan[]> {
  const url = `${API_BASE}/trade-decision/history?symbol=${encodeURIComponent(symbol)}&timeframe=${encodeURIComponent(timeframe)}&strategy_context_id=${encodeURIComponent(strategyContextId)}&limit=${limit}`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch trade decision history: ${response.statusText}`);
  }
  return response.json();
}

export async function fetchTradeDecisionExplain(
  symbol: string = 'BTCUSDT',
  timeframe: Timeframe = '15m',
  strategyContextId: string = 'EXP_A2_PULLBACK_VWAP',
  timestamp?: number
): Promise<TradePlan> {
  const tsParam = timestamp ? `&timestamp=${timestamp}` : '';
  const url = `${API_BASE}/trade-decision/explain?symbol=${encodeURIComponent(symbol)}&timeframe=${encodeURIComponent(timeframe)}&strategy_context_id=${encodeURIComponent(strategyContextId)}${tsParam}`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch trade decision explanation: ${response.statusText}`);
  }
  return response.json();
}

// ----------------------------------------------------
// Phase 12: Trading Profiles API
// ----------------------------------------------------
export async function fetchTradingProfiles(): Promise<any[]> {
  const response = await fetch(`${API_BASE}/profiles`);
  if (!response.ok) {
    throw new Error(`Failed to fetch trading profiles: ${response.statusText}`);
  }
  return response.json();
}

export async function fetchProfileContext(
  profileId: string = 'SCALP_1M_V1',
  symbol: string = 'BTCUSDT',
  strategyId: string = 'EXP_A2_PULLBACK_VWAP'
): Promise<any> {
  const response = await fetch(
    `${API_BASE}/profiles/${encodeURIComponent(profileId)}/context?symbol=${encodeURIComponent(symbol)}&strategy_id=${encodeURIComponent(strategyId)}`
  );
  if (!response.ok) {
    throw new Error(`Failed to fetch profile context: ${response.statusText}`);
  }
  return response.json();
}

export async function fetchProfileMetrics(
  profileId: string = 'SCALP_1M_V1',
  symbol: string = 'BTCUSDT'
): Promise<any> {
  const response = await fetch(
    `${API_BASE}/profiles/${encodeURIComponent(profileId)}/metrics?symbol=${encodeURIComponent(symbol)}`
  );
  if (!response.ok) {
    throw new Error(`Failed to fetch profile metrics: ${response.statusText}`);
  }
  return response.json();
}

export async function fetchProfileComparison(
  symbol: string = 'BTCUSDT'
): Promise<any> {
  const response = await fetch(
    `${API_BASE}/profiles/compare?symbol=${encodeURIComponent(symbol)}`
  );
  if (!response.ok) {
    throw new Error(`Failed to fetch profile comparison: ${response.statusText}`);
  }
  return response.json();
}

