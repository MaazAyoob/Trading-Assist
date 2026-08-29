import React from 'react';
import {
  useMarketStore,
  formatSymbolPrice,
  formatPercentage,
  getScalpStrengthTier,
} from '../../stores/marketStore';
import { Layers, Activity } from 'lucide-react';

interface WatchlistItem {
  symbol: string;
  name: string;
  basePrice: number;
}

const WATCHLIST: WatchlistItem[] = [
  { symbol: 'BTCUSDT', name: 'Bitcoin', basePrice: 65000 },
  { symbol: 'ETHUSDT', name: 'Ethereum', basePrice: 2800 },
  { symbol: 'SOLUSDT', name: 'Solana', basePrice: 150 },
  { symbol: 'BNBUSDT', name: 'BNB', basePrice: 580 },
  { symbol: 'XRPUSDT', name: 'XRP', basePrice: 0.58 },
];

export const Watchlist: React.FC = () => {
  const {
    symbol,
    setSymbol,
    ticker,
    candles,
    confirmedTradeDecision,
    confirmedScalpSignal,
    confirmedScalpV2Signal,
    selectedScalpStrategy,
    selectedProfileId,
    timeframe,
  } = useMarketStore();

  const isScalpProfile = selectedProfileId === 'SCALP_1M_V1' || timeframe === '1m';

  return (
    <div className="w-full lg:w-60 bg-slate-900/95 rounded-xl border border-slate-800/90 flex flex-col overflow-hidden select-none shadow-xl font-mono">
      <div className="h-9 sm:h-10 bg-slate-950 px-3 flex items-center justify-between border-b border-slate-800">
        <div className="flex items-center gap-1.5 text-xs font-bold text-slate-200 uppercase tracking-wider">
          <Layers className="w-3.5 h-3.5 text-indigo-400" />
          <span>Watchlist</span>
        </div>
        <span className="text-[10px] font-mono text-slate-400 bg-slate-900 px-1.5 py-0.5 rounded border border-slate-800">
          SPOT
        </span>
      </div>

      {/* Mobile: Horizontal scroll strip / Desktop: Vertical list */}
      <div className="p-1.5 sm:p-2 flex flex-row lg:flex-col gap-1.5 overflow-x-auto lg:overflow-y-auto scrollbar-none max-w-full">
        {WATCHLIST.map((item) => {
          const isSelected = symbol === item.symbol;
          const isCurrentActive = isSelected && ticker;
          const price = isCurrentActive
            ? ticker.price
            : isSelected && candles.length > 0
            ? candles[candles.length - 1].close
            : item.basePrice;
          const change = isCurrentActive ? ticker.price_change_percent : 0;
          const isPositive = change >= 0;

          // Scalp Analysis status for active BTCUSDT
          let statusText = 'NOT ANALYZED';
          let statusBadgeClass = 'text-slate-500 font-normal';
          let extraTag = '--';

          if (isSelected) {
            if (isScalpProfile) {
              if (selectedScalpStrategy === 'SCALP_V2' && confirmedScalpV2Signal) {
                const tier = getScalpStrengthTier(
                  confirmedScalpV2Signal.alignment_score,
                  confirmedScalpV2Signal.direction as any
                );
                statusText = `${confirmedScalpV2Signal.direction} · ${tier.label}`;
                statusBadgeClass =
                  confirmedScalpV2Signal.direction === 'BUY'
                    ? 'text-emerald-400 font-bold'
                    : confirmedScalpV2Signal.direction === 'SELL'
                    ? 'text-rose-400 font-bold'
                    : 'text-amber-400 font-bold';
                extraTag = 'V2 SCALP';
              } else if (confirmedScalpSignal) {
                const tier = getScalpStrengthTier(
                  confirmedScalpSignal.score_breakdown.normalised_score,
                  confirmedScalpSignal.direction
                );
                statusText = `${confirmedScalpSignal.direction} · ${tier.label}`;
                statusBadgeClass =
                  confirmedScalpSignal.direction === 'BUY'
                    ? 'text-emerald-400 font-bold'
                    : confirmedScalpSignal.direction === 'SELL'
                    ? 'text-rose-400 font-bold'
                    : 'text-amber-400 font-bold';
                extraTag = 'V1 SCALP';
              }
            } else if (confirmedTradeDecision) {
              statusText = confirmedTradeDecision.decision;
              statusBadgeClass =
                confirmedTradeDecision.decision === 'BUY'
                  ? 'text-emerald-400 font-bold'
                  : confirmedTradeDecision.decision === 'SELL'
                  ? 'text-rose-400 font-bold'
                  : 'text-amber-400 font-bold';
              extraTag = timeframe;
            } else {
              statusText = 'ANALYZING...';
              statusBadgeClass = 'text-indigo-300 font-bold';
              extraTag = timeframe;
            }
          }

          return (
            <button
              key={item.symbol}
              onClick={() => setSymbol(item.symbol)}
              className={`p-2 sm:p-2.5 rounded-lg text-left transition-all border shrink-0 min-w-[150px] sm:min-w-[170px] lg:min-w-0 min-h-[44px] ${
                isSelected
                  ? 'bg-slate-950 border-indigo-500/60 shadow-lg shadow-indigo-600/15'
                  : 'bg-slate-900/40 border-transparent hover:border-slate-800 hover:bg-slate-900'
              }`}
            >
              <div className="flex items-center justify-between gap-1">
                <span className="font-mono text-xs font-bold text-slate-100">
                  {item.symbol.replace('USDT', '')}
                  <span className="text-[10px] text-slate-500 font-normal">/USDT</span>
                </span>
                <span
                  className={`text-[10px] font-mono font-bold px-1 rounded ${
                    isPositive ? 'text-emerald-400 bg-emerald-500/10' : 'text-rose-400 bg-rose-500/10'
                  }`}
                >
                  {formatPercentage(change)}
                </span>
              </div>

              <div className="flex items-center justify-between mt-1 gap-1">
                <span className="text-[10px] text-slate-400 font-sans truncate">{item.name}</span>
                <span className="font-mono text-xs font-bold text-slate-200">
                  ${formatSymbolPrice(item.symbol, price)}
                </span>
              </div>

              {/* Analysis Pipeline Status */}
              <div className="mt-1.5 pt-1.5 border-t border-slate-800/60 flex items-center justify-between text-[9px] font-mono">
                {isSelected ? (
                  <div className="flex items-center gap-1.5 w-full justify-between">
                    <span className={`flex items-center gap-1 truncate ${statusBadgeClass}`}>
                      <Activity className="w-2.5 h-2.5 shrink-0 animate-pulse" />
                      <span className="truncate">{statusText}</span>
                    </span>
                    <span className="text-slate-400 text-[8px] bg-slate-900 px-1 rounded border border-slate-800 shrink-0">
                      {extraTag}
                    </span>
                  </div>
                ) : (
                  <div className="flex items-center justify-between w-full">
                    <span className="text-slate-500 font-normal">NOT ANALYZED</span>
                    <span className="text-[8px] text-slate-600">--</span>
                  </div>
                )}
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
};
