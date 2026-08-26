import React, { useState, useEffect } from 'react';
import { Play, RotateCcw, AlertTriangle, CheckCircle2, History } from 'lucide-react';
import { Timeframe } from '../../types/market';
import { BacktestRun, BacktestRunSummaryItem } from '../../types/backtesting';
import { runBacktest, fetchBacktestRuns, fetchBacktestRun } from '../../services/api';

import { BacktestControls } from './BacktestControls';
import { BacktestSummary } from './BacktestSummary';
import { ForwardReturnChart } from './ForwardReturnChart';
import { MfeMaeChart } from './MfeMaeChart';
import { RegimeBreakdown } from './RegimeBreakdown';
import { SignalStrengthBreakdown } from './SignalStrengthBreakdown';
import { SignalOutcomeTable } from './SignalOutcomeTable';
import { BacktestEquityPlaceholder } from './BacktestEquityPlaceholder';

interface BacktestDashboardProps {
  symbol: string;
  timeframe: Timeframe;
}

export const BacktestDashboard: React.FC<BacktestDashboardProps> = ({
  symbol,
  timeframe,
}) => {
  const [currentRun, setCurrentRun] = useState<BacktestRun | null>(null);
  const [previousRuns, setPreviousRuns] = useState<BacktestRunSummaryItem[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'returns' | 'excursions' | 'regime' | 'strength' | 'signals'>('returns');

  // Load previous runs on mount
  useEffect(() => {
    loadPreviousRuns();
  }, [symbol, timeframe]);

  const loadPreviousRuns = async () => {
    try {
      const runs = await fetchBacktestRuns(symbol, timeframe, 10);
      setPreviousRuns(runs);
      if (runs.length > 0 && !currentRun) {
        loadSpecificRun(runs[0].run_id);
      }
    } catch (err: any) {
      console.warn('Could not load previous backtest runs:', err);
    }
  };

  const loadSpecificRun = async (runId: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const run = await fetchBacktestRun(runId);
      setCurrentRun(run);
    } catch (err: any) {
      setError(err.message || `Failed to load run ${runId}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRunBacktest = async (params: {
    symbol: string;
    timeframe: Timeframe;
    candle_count: number;
    warmup_bars: number;
    fee_bps: number;
    slippage_bps: number;
  }) => {
    setIsLoading(true);
    setError(null);
    try {
      const run = await runBacktest(params);
      setCurrentRun(run);
      loadPreviousRuns();
    } catch (err: any) {
      setError(err.message || 'Backtest execution failed.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="p-4 space-y-4 font-mono text-xs text-text-primary max-w-7xl mx-auto">
      {/* Top Header & Run Controls */}
      <div className="flex flex-wrap items-center justify-between gap-3 bg-surface/30 p-3 rounded-lg border border-border-subtle">
        <div>
          <h2 className="text-sm font-bold tracking-wider text-accent-cyan uppercase flex items-center gap-2">
            <span>Phase 6 · Multi-Factor Backtesting & Validation Engine</span>
          </h2>
          <p className="text-[11px] text-text-muted mt-0.5">
            Strictly Causal Historical Forward Returns & Excursions (Non-Fabricated Real Dataset)
          </p>
        </div>

        {/* Previous Run Selector */}
        {previousRuns.length > 0 && (
          <div className="flex items-center gap-1.5 text-[11px]">
            <History className="w-3.5 h-3.5 text-text-muted" />
            <span className="text-text-muted">Previous Runs:</span>
            <select
              value={currentRun?.run_id || ''}
              onChange={(e) => loadSpecificRun(e.target.value)}
              disabled={isLoading}
              className="bg-surface-card border border-border-subtle rounded px-2 py-1 text-text-primary text-[11px] focus:outline-none focus:border-accent-cyan"
            >
              {previousRuns.map((r) => (
                <option key={r.run_id} value={r.run_id}>
                  {r.run_id} ({r.candle_count} bars, {r.signal_count} sigs)
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Interactive Controls Form */}
      <BacktestControls
        symbol={symbol}
        timeframe={timeframe}
        onRunBacktest={handleRunBacktest}
        isLoading={isLoading}
      />

      {/* Error Display */}
      {error && (
        <div className="bg-rose-500/10 border border-rose-500/30 p-3 rounded-lg flex items-center gap-2 text-rose-400">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Active Run Content */}
      {currentRun ? (
        <div className="space-y-4">
          {/* Summary Cards */}
          <BacktestSummary run={currentRun} />

          {/* Sub-view Navigation Tabs */}
          <div className="flex items-center gap-1 border-b border-border/40 pb-2 text-[11px]">
            <button
              onClick={() => setActiveTab('returns')}
              className={`px-3 py-1 rounded transition font-bold ${
                activeTab === 'returns'
                  ? 'bg-accent-cyan text-black shadow-glow-cyan'
                  : 'text-text-secondary hover:text-text-primary bg-surface/40'
              }`}
            >
              1. Forward Returns (1C-20C)
            </button>
            <button
              onClick={() => setActiveTab('excursions')}
              className={`px-3 py-1 rounded transition font-bold ${
                activeTab === 'excursions'
                  ? 'bg-purple-500 text-white'
                  : 'text-text-secondary hover:text-text-primary bg-surface/40'
              }`}
            >
              2. MFE / MAE Excursions
            </button>
            <button
              onClick={() => setActiveTab('regime')}
              className={`px-3 py-1 rounded transition font-bold ${
                activeTab === 'regime'
                  ? 'bg-accent-gold text-black'
                  : 'text-text-secondary hover:text-text-primary bg-surface/40'
              }`}
            >
              3. Regime Slices
            </button>
            <button
              onClick={() => setActiveTab('strength')}
              className={`px-3 py-1 rounded transition font-bold ${
                activeTab === 'strength'
                  ? 'bg-emerald-500 text-black'
                  : 'text-text-secondary hover:text-text-primary bg-surface/40'
              }`}
            >
              4. Strength & Score Bands
            </button>
            <button
              onClick={() => setActiveTab('signals')}
              className={`px-3 py-1 rounded transition font-bold ${
                activeTab === 'signals'
                  ? 'bg-surface-elevated text-text-primary border border-border'
                  : 'text-text-secondary hover:text-text-primary bg-surface/40'
              }`}
            >
              5. Signal Log ({currentRun.signal_outcomes.length})
            </button>
          </div>

          {/* Active Tab Component */}
          {activeTab === 'returns' && <ForwardReturnChart metrics={currentRun.metrics} />}
          {activeTab === 'excursions' && <MfeMaeChart metrics={currentRun.metrics} />}
          {activeTab === 'regime' && <RegimeBreakdown metrics={currentRun.metrics} />}
          {activeTab === 'strength' && <SignalStrengthBreakdown metrics={currentRun.metrics} />}
          {activeTab === 'signals' && <SignalOutcomeTable signals={currentRun.signal_outcomes} />}

          {/* Equity Curve Placeholder Notice */}
          <BacktestEquityPlaceholder />
        </div>
      ) : (
        !isLoading && (
          <div className="bg-surface/20 border border-dashed border-border/40 p-8 rounded-lg text-center space-y-2">
            <p className="text-text-secondary font-bold">No Backtest Run Loaded</p>
            <p className="text-text-muted text-[11px]">
              Click <strong>"Run Backtest"</strong> above to execute a real causal simulation over historical BTC/USDT data.
            </p>
          </div>
        )
      )}
    </div>
  );
};
