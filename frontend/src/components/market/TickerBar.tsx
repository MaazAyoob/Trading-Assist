import React from 'react';
import { ArrowUpRight, ArrowDownRight, TrendingUp, BarChart2 } from 'lucide-react';
import { useMarketStore } from '../../stores/marketStore';

export const TickerBar: React.FC = () => {
  const { symbol, timeframe, ticker, candles } = useMarketStore();

  const currentPrice = ticker?.price ?? (candles.length > 0 ? candles[candles.length - 1].close : 0);
  const changePercent = ticker?.price_change_percent ?? 0;
  const changeAmount = ticker?.price_change ?? 0;
  const isPositive = changePercent >= 0;

  const high24h = ticker?.high_24h ?? 0;
  const low24h = ticker?.low_24h ?? 0;
  const volume24h = ticker?.volume_24h ?? 0;
  const quoteVolume24h = ticker?.quote_volume_24h ?? 0;

  return (
    <div className="bg-surface-elevated border-b border-border px-3 sm:px-4 py-2 sm:py-2.5 flex flex-wrap items-center justify-between gap-2.5 sm:gap-4 select-none">
      {/* Symbol & Main Price */}
      <div className="flex flex-wrap items-center gap-2.5 sm:gap-4">
        <div className="flex items-center gap-1.5 sm:gap-2">
          <div className="bg-accent-cyan/10 border border-accent-cyan/30 text-accent-cyan font-mono font-bold text-xs sm:text-sm px-2 py-0.5 sm:px-2.5 sm:py-1 rounded">
            {symbol.replace('USDT', '/USDT')}
          </div>
          <span className="text-[10px] sm:text-xs text-text-muted font-mono uppercase bg-surface-card px-1.5 py-0.5 sm:px-2 sm:py-1 rounded border border-border-subtle">
            SPOT
          </span>
        </div>

        <div className="flex items-baseline gap-2">
          <span className="text-xl sm:text-2xl font-bold font-mono tracking-tight text-text-primary">
            ${currentPrice > 0 ? currentPrice.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '---.--'}
          </span>
          <div
            className={`flex items-center text-[10px] sm:text-xs font-mono font-semibold px-1.5 sm:px-2 py-0.5 rounded ${
              isPositive
                ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
            }`}
          >
            {isPositive ? (
              <ArrowUpRight className="w-3 h-3 sm:w-3.5 sm:h-3.5 mr-0.5" />
            ) : (
              <ArrowDownRight className="w-3 h-3 sm:w-3.5 sm:h-3.5 mr-0.5" />
            )}
            <span>
              {isPositive ? '+' : ''}
              {changePercent.toFixed(2)}%
              <span className="hidden xs:inline"> (${Math.abs(changeAmount).toFixed(2)})</span>
            </span>
          </div>
        </div>
      </div>

      {/* 24h Metrics */}
      <div className="flex items-center gap-3 sm:gap-6 text-xs font-mono overflow-x-auto scrollbar-none py-0.5 max-w-full">
        <div>
          <div className="text-[9px] sm:text-[10px] uppercase text-text-muted flex items-center gap-1">
            <span>24h High</span>
          </div>
          <div className="text-text-primary font-medium text-[11px] sm:text-xs mt-0.5">
            ${high24h > 0 ? high24h.toLocaleString('en-US', { minimumFractionDigits: 2 }) : '---'}
          </div>
        </div>

        <div className="border-l border-border/60 pl-3 sm:pl-4">
          <div className="text-[9px] sm:text-[10px] uppercase text-text-muted flex items-center gap-1">
            <span>24h Low</span>
          </div>
          <div className="text-text-primary font-medium text-[11px] sm:text-xs mt-0.5">
            ${low24h > 0 ? low24h.toLocaleString('en-US', { minimumFractionDigits: 2 }) : '---'}
          </div>
        </div>

        <div className="border-l border-border/60 pl-3 sm:pl-4 hidden sm:block">
          <div className="text-[9px] sm:text-[10px] uppercase text-text-muted flex items-center gap-1">
            <BarChart2 className="w-3 h-3 text-text-muted" />
            <span>24h Vol ({symbol.replace('USDT', '')})</span>
          </div>
          <div className="text-text-primary font-medium text-[11px] sm:text-xs mt-0.5">
            {volume24h > 0 ? volume24h.toLocaleString('en-US', { maximumFractionDigits: 2 }) : '---'}
          </div>
        </div>

        <div className="border-l border-border/60 pl-3 sm:pl-4 hidden md:block">
          <div className="text-[9px] sm:text-[10px] uppercase text-text-muted">
            <span>24h Turnover (USDT)</span>
          </div>
          <div className="text-text-primary font-medium text-[11px] sm:text-xs mt-0.5">
            ${quoteVolume24h > 0 ? (quoteVolume24h / 1_000_000).toFixed(2) + 'M' : '---'}
          </div>
        </div>

        <div className="border-l border-border/60 pl-3 sm:pl-4 hidden lg:block">
          <div className="text-[9px] sm:text-[10px] uppercase text-text-muted">Active Timeframe</div>
          <div className="text-accent-cyan font-bold text-[11px] sm:text-xs mt-0.5">{timeframe}</div>
        </div>
      </div>
    </div>
  );
};
