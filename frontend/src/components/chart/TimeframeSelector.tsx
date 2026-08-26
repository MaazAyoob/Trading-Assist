import React from 'react';
import { Timeframe } from '../../types/market';
import { useMarketStore } from '../../stores/marketStore';

const TIMEFRAMES: Timeframe[] = ['1m', '5m', '15m', '1h', '4h', '1d'];

export const TimeframeSelector: React.FC = () => {
  const { timeframe, setTimeframe, isLoading } = useMarketStore();

  return (
    <div className="flex items-center gap-1 bg-surface-card p-1 rounded-md border border-border-subtle select-none">
      <span className="text-[11px] font-mono text-text-muted px-2 hidden sm:inline">Interval:</span>
      {TIMEFRAMES.map((tf) => {
        const isActive = timeframe === tf;
        return (
          <button
            key={tf}
            onClick={() => setTimeframe(tf)}
            disabled={isLoading && isActive}
            className={`px-2 sm:px-2.5 py-1 text-xs font-mono font-medium rounded transition-all min-h-[30px] flex items-center justify-center shrink-0 ${
              isActive
                ? 'bg-accent-cyan text-black font-bold shadow-glow-cyan/40'
                : 'text-text-secondary hover:text-text-primary hover:bg-surface-elevated'
            }`}
          >
            {tf}
          </button>
        );
      })}
    </div>
  );
};
