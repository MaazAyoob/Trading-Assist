import React from 'react';
import { MomentumIndicators as MomentumType } from '../../types/market';

interface Props {
  momentum?: MomentumType | null;
}

export const MomentumIndicators: React.FC<Props> = ({ momentum }) => {
  const formatNum = (val?: number | null, decimals = 2) =>
    val != null ? val.toFixed(decimals) : '--';

  const rsiVal = momentum?.rsi;
  const isRsiOverbought = rsiVal != null && rsiVal >= 70;
  const isRsiOversold = rsiVal != null && rsiVal <= 30;

  return (
    <div className="bg-surface/60 rounded-lg p-3 border border-border-subtle font-mono text-xs select-none">
      <div className="flex items-center justify-between border-b border-border/60 pb-2 mb-2.5">
        <span className="font-bold text-accent-green tracking-wider uppercase text-[11px]">Momentum Matrix</span>
        <span className="text-[10px] text-text-muted">RSI / MACD / StochRSI / ROC</span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
        <div className="bg-surface-elevated/60 p-2 rounded border border-border/40">
          <div className="text-[10px] text-text-muted flex justify-between">
            <span>RSI (14)</span>
            {isRsiOverbought && <span className="text-amber-400 font-bold">OB (70+)</span>}
            {isRsiOversold && <span className="text-emerald-400 font-bold">OS (30-)</span>}
          </div>
          <div className="text-accent-green font-bold text-sm mt-0.5">{formatNum(rsiVal, 1)}</div>
          {/* Visual Mini Slider */}
          <div className="w-full bg-surface-card h-1 rounded-full mt-1.5 overflow-hidden">
            <div
              className="bg-accent-green h-full rounded-full transition-all duration-300"
              style={{ width: `${Math.min(100, Math.max(0, rsiVal || 50))}%` }}
            />
          </div>
        </div>

        <div className="bg-surface-elevated/60 p-2 rounded border border-border/40">
          <div className="text-[10px] text-text-muted">MACD (12, 26)</div>
          <div className="text-text-primary font-medium mt-0.5">{formatNum(momentum?.macd)}</div>
        </div>

        <div className="bg-surface-elevated/60 p-2 rounded border border-border/40">
          <div className="text-[10px] text-text-muted">MACD Signal (9)</div>
          <div className="text-text-secondary font-medium mt-0.5">{formatNum(momentum?.macd_signal)}</div>
        </div>

        <div className="bg-surface-elevated/60 p-2 rounded border border-border/40">
          <div className="text-[10px] text-text-muted">MACD Histogram</div>
          <div
            className={`font-bold mt-0.5 ${
              (momentum?.macd_histogram || 0) >= 0 ? 'text-emerald-400' : 'text-rose-400'
            }`}
          >
            {formatNum(momentum?.macd_histogram)}
          </div>
        </div>

        <div className="bg-surface-elevated/60 p-2 rounded border border-border/40">
          <div className="text-[10px] text-text-muted">Stoch RSI %K / %D</div>
          <div className="text-text-primary mt-0.5">
            <span className="text-accent-cyan font-semibold">{formatNum(momentum?.stoch_rsi_k, 1)}</span>
            <span className="text-text-muted mx-1">/</span>
            <span className="text-text-secondary">{formatNum(momentum?.stoch_rsi_d, 1)}</span>
          </div>
        </div>

        <div className="bg-surface-elevated/60 p-2 rounded border border-border/40">
          <div className="text-[10px] text-text-muted">ROC % (12)</div>
          <div
            className={`font-bold mt-0.5 ${
              (momentum?.roc || 0) >= 0 ? 'text-emerald-400' : 'text-rose-400'
            }`}
          >
            {(momentum?.roc || 0) >= 0 ? '+' : ''}
            {formatNum(momentum?.roc)}%
          </div>
        </div>
      </div>
    </div>
  );
};
