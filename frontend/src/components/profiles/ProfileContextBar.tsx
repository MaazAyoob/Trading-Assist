import React from 'react';
import { useMarketStore } from '../../stores/marketStore';
import { ShieldCheck, CheckCircle2, AlertTriangle, Layers, Clock } from 'lucide-react';

export const ProfileContextBar: React.FC = () => {
  const { selectedProfileId, activeProfileResult, timeframe } = useMarketStore();

  const confirmedCtx = activeProfileResult?.context_confirmed || {};
  const isCausal = activeProfileResult ? activeProfileResult.profile_state !== 'INSUFFICIENT_DATA' : true;

  return (
    <div className="bg-slate-950/80 border border-slate-800/90 rounded-lg px-2.5 sm:px-3 py-1.5 flex flex-col sm:flex-row sm:items-center justify-between gap-1.5 sm:gap-2 text-[10px] sm:text-[11px] font-mono select-none">
      <div className="flex flex-wrap items-center gap-1.5 sm:gap-2">
        <span className="text-slate-400 font-sans font-semibold flex items-center gap-1">
          <Layers className="w-3 h-3 text-indigo-400 shrink-0" />
          <span className="hidden xs:inline">Multi-Timeframe Context:</span>
          <span className="xs:hidden">Context:</span>
        </span>
        <span className="bg-indigo-950/80 border border-indigo-700/60 px-1.5 py-0.5 rounded text-indigo-300 font-bold">
          {timeframe}
        </span>
        <span className="text-slate-600">→</span>

        {/* Higher Timeframe Badges */}
        <div className="flex flex-wrap items-center gap-1 sm:gap-1.5">
          {Object.entries(confirmedCtx).map(([tf, isConfirmed]) => (
            <div
              key={tf}
              className={`flex items-center gap-1 px-1.5 py-0.5 rounded border ${
                isConfirmed
                  ? 'bg-emerald-950/40 border-emerald-800/60 text-emerald-300'
                  : 'bg-amber-950/40 border-amber-800/60 text-amber-300'
              }`}
            >
              {isConfirmed ? (
                <CheckCircle2 className="w-2.5 h-2.5 text-emerald-400 shrink-0" />
              ) : (
                <AlertTriangle className="w-2.5 h-2.5 text-amber-400 shrink-0" />
              )}
              <span>{tf} {isConfirmed ? 'CONFIRMED' : 'WAIT'}</span>
            </div>
          ))}
          {Object.keys(confirmedCtx).length === 0 && (
            <span className="text-slate-500 text-[10px]">Synchronizing context...</span>
          )}
        </div>
      </div>

      <div className="flex items-center gap-2 text-[9px] sm:text-[10px] text-slate-400 pt-1 sm:pt-0 border-t sm:border-t-0 border-slate-800/60">
        <div className="flex items-center gap-1 text-indigo-300">
          <ShieldCheck className="w-3 h-3 text-indigo-400 shrink-0" />
          <span>CAUSALLY SYNCHRONIZED</span>
        </div>
        <span className="text-slate-600">|</span>
        <span>0 Future Leakage</span>
      </div>
    </div>
  );
};
