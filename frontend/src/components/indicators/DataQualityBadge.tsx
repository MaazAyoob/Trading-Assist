import React from 'react';
import { ShieldCheck, AlertTriangle, AlertOctagon, HelpCircle } from 'lucide-react';
import { MarketDataQuality } from '../../types/market';

interface DataQualityBadgeProps {
  quality: MarketDataQuality | null;
}

export const DataQualityBadge: React.FC<DataQualityBadgeProps> = ({ quality }) => {
  if (!quality) {
    return (
      <div className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-surface-elevated text-text-muted text-[10px] font-mono border border-border-subtle">
        <HelpCircle className="w-3 h-3" />
        <span>Quality: Checking...</span>
      </div>
    );
  }

  const getBadge = () => {
    switch (quality.status) {
      case 'HEALTHY':
        return (
          <div className="flex items-center gap-1.5 px-2.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 text-[10px] font-mono border border-emerald-500/30">
            <ShieldCheck className="w-3 h-3 text-emerald-400" />
            <span className="font-bold">DATA HEALTHY</span>
            <span className="text-text-muted hidden sm:inline">({quality.total_candles} bars)</span>
          </div>
        );
      case 'WARNING':
        return (
          <div className="flex items-center gap-1.5 px-2.5 py-0.5 rounded bg-amber-500/10 text-amber-400 text-[10px] font-mono border border-amber-500/30" title={(quality.details || []).join('; ')}>
            <AlertTriangle className="w-3 h-3 text-amber-400" />
            <span className="font-bold">DATA WARNING</span>
            {quality.gap_count > 0 && <span className="text-amber-300">[{quality.gap_count} gaps]</span>}
            {quality.is_stale && <span className="text-amber-300">[STALE]</span>}
          </div>
        );
      case 'INVALID':
        return (
          <div className="flex items-center gap-1.5 px-2.5 py-0.5 rounded bg-rose-500/10 text-rose-400 text-[10px] font-mono border border-rose-500/30" title={(quality.details || []).join('; ')}>
            <AlertOctagon className="w-3 h-3 text-rose-400" />
            <span className="font-bold">DATA INVALID</span>
          </div>
        );
      case 'INSUFFICIENT_DATA':
      default:
        return (
          <div className="flex items-center gap-1.5 px-2.5 py-0.5 rounded bg-blue-500/10 text-blue-400 text-[10px] font-mono border border-blue-500/30">
            <HelpCircle className="w-3 h-3 text-blue-400" />
            <span className="font-bold">INSUFFICIENT DATA</span>
          </div>
        );
    }
  };

  return <div className="inline-flex">{getBadge()}</div>;
};
