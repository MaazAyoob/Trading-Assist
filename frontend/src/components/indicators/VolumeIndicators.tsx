import React from 'react';
import { VolumeIndicators as VolumeType } from '../../types/market';

interface Props {
  volume?: VolumeType | null;
}

export const VolumeIndicators: React.FC<Props> = ({ volume }) => {
  const formatNum = (val?: number | null, decimals = 2) =>
    val != null ? val.toLocaleString('en-US', { minimumFractionDigits: decimals, maximumFractionDigits: decimals }) : '--';

  const relVol = volume?.relative_volume;
  const isHighVolume = relVol != null && relVol >= 1.5;

  return (
    <div className="bg-surface/60 rounded-lg p-3 border border-border-subtle font-mono text-xs select-none">
      <div className="flex items-center justify-between border-b border-border/60 pb-2 mb-2.5">
        <span className="font-bold text-accent-gold tracking-wider uppercase text-[11px]">Volume Matrix</span>
        <span className="text-[10px] text-text-muted">Volume SMA / RVol / OBV</span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5">
        <div className="bg-surface-elevated/60 p-2 rounded border border-border/40">
          <div className="text-[10px] text-text-muted">Volume SMA (20)</div>
          <div className="text-text-primary font-medium mt-0.5">{formatNum(volume?.volume_sma)}</div>
        </div>

        <div className="bg-surface-elevated/60 p-2 rounded border border-border/40">
          <div className="text-[10px] text-text-muted flex justify-between">
            <span>Relative Volume (RVol)</span>
            {isHighVolume && <span className="text-emerald-400 font-bold">EXPANDED</span>}
          </div>
          <div className="text-accent-gold font-bold mt-0.5">{formatNum(relVol)}x</div>
        </div>

        <div className="bg-surface-elevated/60 p-2 rounded border border-border/40">
          <div className="text-[10px] text-text-muted">On-Balance Volume (OBV)</div>
          <div className="text-text-primary font-medium mt-0.5">{formatNum(volume?.obv, 0)}</div>
        </div>
      </div>
    </div>
  );
};
