import React from 'react';
import { TrendIndicators as TrendType } from '../../types/market';

interface Props {
  trend?: TrendType | null;
  isConfirmed?: boolean;
}

export const TrendIndicators: React.FC<Props> = ({ trend, isConfirmed = true }) => {
  const formatPrice = (val?: number | null) =>
    val != null ? `$${val.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : 'Warmup...';

  const formatNum = (val?: number | null) =>
    val != null ? val.toFixed(2) : '--';

  return (
    <div className="bg-surface/60 rounded-lg p-3 border border-border-subtle font-mono text-xs select-none">
      <div className="flex items-center justify-between border-b border-border/60 pb-2 mb-2.5">
        <span className="font-bold text-accent-cyan tracking-wider uppercase text-[11px]">Trend Matrix</span>
        <span className="text-[10px] text-text-muted">EMA / VWAP / ADX / Supertrend</span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
        <div className="bg-surface-elevated/60 p-2 rounded border border-border/40">
          <div className="text-[10px] text-text-muted">EMA 9</div>
          <div className="text-text-primary font-medium mt-0.5">{formatPrice(trend?.ema_9)}</div>
        </div>

        <div className="bg-surface-elevated/60 p-2 rounded border border-border/40">
          <div className="text-[10px] text-text-muted">EMA 21</div>
          <div className="text-text-primary font-medium mt-0.5">{formatPrice(trend?.ema_21)}</div>
        </div>

        <div className="bg-surface-elevated/60 p-2 rounded border border-border/40">
          <div className="text-[10px] text-text-muted">EMA 50</div>
          <div className="text-text-primary font-medium mt-0.5">{formatPrice(trend?.ema_50)}</div>
        </div>

        <div className="bg-surface-elevated/60 p-2 rounded border border-border/40">
          <div className="text-[10px] text-text-muted">EMA 200</div>
          <div className="text-text-primary font-medium mt-0.5">{formatPrice(trend?.ema_200)}</div>
        </div>

        <div className="bg-surface-elevated/60 p-2 rounded border border-border/40">
          <div className="text-[10px] text-text-muted">Rolling 24h VWAP</div>
          <div className="text-accent-gold font-medium mt-0.5">{formatPrice(trend?.vwap)}</div>
        </div>

        <div className="bg-surface-elevated/60 p-2 rounded border border-border/40">
          <div className="text-[10px] text-text-muted">ADX (14)</div>
          <div className="text-accent-cyan font-bold mt-0.5">{formatNum(trend?.adx)}</div>
        </div>

        <div className="bg-surface-elevated/60 p-2 rounded border border-border/40">
          <div className="text-[10px] text-text-muted">+DI / -DI</div>
          <div className="text-text-primary mt-0.5">
            <span className="text-emerald-400">{formatNum(trend?.plus_di)}</span>
            <span className="text-text-muted mx-1">/</span>
            <span className="text-rose-400">{formatNum(trend?.minus_di)}</span>
          </div>
        </div>

        <div className="bg-surface-elevated/60 p-2 rounded border border-border/40">
          <div className="text-[10px] text-text-muted">Supertrend (10, 3.0)</div>
          <div className="text-text-primary mt-0.5 flex items-center justify-between">
            <span>{formatPrice(trend?.supertrend)}</span>
            {trend?.supertrend_direction && (
              <span className={`text-[10px] px-1 rounded font-bold ${
                trend.supertrend_direction === 1 ? 'bg-emerald-500/10 text-emerald-400' : 'bg-rose-500/10 text-rose-400'
              }`}>
                {trend.supertrend_direction === 1 ? '▲ BULL' : '▼ BEAR'}
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
