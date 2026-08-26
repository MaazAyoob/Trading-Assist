import React, { useState } from 'react';
import { Play, Sliders, RefreshCw, AlertCircle } from 'lucide-react';
import { Timeframe } from '../../types/market';

interface BacktestControlsProps {
  symbol: string;
  timeframe: Timeframe;
  onRunBacktest: (params: {
    symbol: string;
    timeframe: Timeframe;
    candle_count: number;
    warmup_bars: number;
    fee_bps: number;
    slippage_bps: number;
  }) => Promise<void>;
  isLoading: boolean;
}

export const BacktestControls: React.FC<BacktestControlsProps> = ({
  symbol,
  timeframe,
  onRunBacktest,
  isLoading,
}) => {
  const [candleCount, setCandleCount] = useState<number>(300);
  const [warmupBars, setWarmupBars] = useState<number>(50);
  const [feeBps, setFeeBps] = useState<number>(0.0);
  const [slippageBps, setSlippageBps] = useState<number>(0.0);
  const [showAdvanced, setShowAdvanced] = useState<boolean>(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onRunBacktest({
      symbol,
      timeframe,
      candle_count: candleCount,
      warmup_bars: warmupBars,
      fee_bps: feeBps,
      slippage_bps: slippageBps,
    });
  };

  return (
    <form onSubmit={handleSubmit} className="bg-surface/50 p-3 rounded-lg border border-border-subtle font-mono text-xs">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3 flex-wrap">
          <div className="flex items-center gap-1.5">
            <span className="text-text-muted">Target:</span>
            <span className="bg-surface-elevated px-2 py-0.5 rounded text-accent-cyan font-bold border border-border-subtle">
              {symbol} · {timeframe}
            </span>
          </div>

          <div className="flex items-center gap-1.5">
            <span className="text-text-muted">Candles:</span>
            <select
              value={candleCount}
              onChange={(e) => setCandleCount(Number(e.target.value))}
              disabled={isLoading}
              className="bg-surface-card border border-border-subtle rounded px-2 py-1 text-text-primary focus:outline-none focus:border-accent-cyan"
            >
              <option value={150}>150 bars</option>
              <option value={300}>300 bars</option>
              <option value={500}>500 bars</option>
              <option value={1000}>1,000 bars</option>
            </select>
          </div>

          <button
            type="button"
            onClick={() => setShowAdvanced(!showAdvanced)}
            className={`flex items-center gap-1 px-2 py-1 rounded border transition text-[11px] ${
              showAdvanced
                ? 'bg-accent-gold/20 border-accent-gold text-accent-gold font-bold'
                : 'bg-surface-elevated/40 border-border-subtle text-text-muted hover:text-text-secondary'
            }`}
          >
            <Sliders className="w-3 h-3" />
            <span>Cost Scenarios</span>
          </button>
        </div>

        <button
          type="submit"
          disabled={isLoading}
          className="flex items-center gap-1.5 px-4 py-1.5 rounded bg-accent-cyan text-black font-bold hover:shadow-glow-cyan transition disabled:opacity-50"
        >
          {isLoading ? (
            <>
              <RefreshCw className="w-3.5 h-3.5 animate-spin" />
              <span>Simulating...</span>
            </>
          ) : (
            <>
              <Play className="w-3.5 h-3.5 fill-current" />
              <span>Run Backtest</span>
            </>
          )}
        </button>
      </div>

      {showAdvanced && (
        <div className="mt-3 pt-3 border-t border-border/40 grid grid-cols-1 sm:grid-cols-3 gap-3 text-[11px]">
          <div>
            <label className="text-text-muted block mb-1">Warmup Bars:</label>
            <input
              type="number"
              min={30}
              max={150}
              value={warmupBars}
              onChange={(e) => setWarmupBars(Number(e.target.value))}
              className="w-full bg-surface-card border border-border-subtle rounded px-2 py-1 text-text-primary focus:outline-none"
            />
          </div>

          <div>
            <label className="text-text-muted block mb-1">Fee (bps):</label>
            <input
              type="number"
              step="0.5"
              min={0}
              value={feeBps}
              onChange={(e) => setFeeBps(Number(e.target.value))}
              className="w-full bg-surface-card border border-border-subtle rounded px-2 py-1 text-text-primary focus:outline-none"
              placeholder="e.g. 10 bps"
            />
          </div>

          <div>
            <label className="text-text-muted block mb-1">Slippage (bps):</label>
            <input
              type="number"
              step="0.5"
              min={0}
              value={slippageBps}
              onChange={(e) => setSlippageBps(Number(e.target.value))}
              className="w-full bg-surface-card border border-border-subtle rounded px-2 py-1 text-text-primary focus:outline-none"
              placeholder="e.g. 5 bps"
            />
          </div>
        </div>
      )}
    </form>
  );
};
