import React from 'react';
import { VolatilityIndicators as VolatilityType } from '../../types/market';

interface Props {
  volatility?: VolatilityType | null;
}

export const VolatilityIndicators: React.FC<Props> = ({ volatility }) => {
  const formatPrice = (val?: number | null) =>
    val != null ? `$${val.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '--';

  const formatNum = (val?: number | null, decimals = 2) =>
    val != null ? val.toFixed(decimals) : '--';

  return (
    <div className="bg-surface/60 rounded-lg p-3 border border-border-subtle font-mono text-xs select-none">
      <div className="flex items-center justify-between border-b border-border/60 pb-2 mb-2.5">
        <span className="font-bold text-purple-400 tracking-wider uppercase text-[11px]">Volatility Matrix</span>
        <span className="text-[10px] text-text-muted">ATR / Bollinger Bands</span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
        <div className="bg-surface-elevated/60 p-2 rounded border border-border/40">
          <div className="text-[10px] text-text-muted">ATR (14)</div>
          <div className="text-purple-400 font-bold mt-0.5">{formatPrice(volatility?.atr)}</div>
        </div>

        <div className="bg-surface-elevated/60 p-2 rounded border border-border/40">
          <div className="text-[10px] text-text-muted">BB Upper (20, 2σ)</div>
          <div className="text-text-primary font-medium mt-0.5">{formatPrice(volatility?.bb_upper)}</div>
        </div>

        <div className="bg-surface-elevated/60 p-2 rounded border border-border/40">
          <div className="text-[10px] text-text-muted">BB Middle SMA</div>
          <div className="text-text-secondary font-medium mt-0.5">{formatPrice(volatility?.bb_middle)}</div>
        </div>

        <div className="bg-surface-elevated/60 p-2 rounded border border-border/40">
          <div className="text-[10px] text-text-muted">BB Lower (20, 2σ)</div>
          <div className="text-text-primary font-medium mt-0.5">{formatPrice(volatility?.bb_lower)}</div>
        </div>

        <div className="bg-surface-elevated/60 p-2 rounded border border-border/40">
          <div className="text-[10px] text-text-muted">BB Bandwidth %</div>
          <div className="text-accent-cyan font-semibold mt-0.5">{formatNum(volatility?.bb_bandwidth)}%</div>
        </div>

        <div className="bg-surface-elevated/60 p-2 rounded border border-border/40">
          <div className="text-[10px] text-text-muted">BB %B Oscillator</div>
          <div className="text-text-primary font-semibold mt-0.5">{formatNum(volatility?.bb_percent_b, 3)}</div>
        </div>
      </div>
    </div>
  );
};
