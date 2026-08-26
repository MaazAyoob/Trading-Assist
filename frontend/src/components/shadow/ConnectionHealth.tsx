import React from 'react';
import { Activity, ShieldCheck, Clock, Database, Radio } from 'lucide-react';
import { ShadowSession } from '../../types/shadow';

interface Props {
  session: ShadowSession | null;
}

export const ConnectionHealth: React.FC<Props> = ({ session }) => {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-2.5">
      <div className="bg-surface p-3 rounded-lg border border-border flex items-center gap-2.5">
        <Radio className="w-5 h-5 text-emerald-400 shrink-0 animate-pulse" />
        <div>
          <span className="text-[10px] text-text-muted uppercase">Feed Connection</span>
          <div className="text-text-primary font-bold text-xs">Binance Public WS</div>
        </div>
      </div>

      <div className="bg-surface p-3 rounded-lg border border-border flex items-center gap-2.5">
        <Activity className="w-5 h-5 text-accent-cyan shrink-0" />
        <div>
          <span className="text-[10px] text-text-muted uppercase">15m Candles Processed</span>
          <div className="text-text-primary font-bold text-xs">{session?.candles_processed_count || 0} Closed</div>
        </div>
      </div>

      <div className="bg-surface p-3 rounded-lg border border-border flex items-center gap-2.5">
        <ShieldCheck className="w-5 h-5 text-indigo-400 shrink-0" />
        <div>
          <span className="text-[10px] text-text-muted uppercase">Config Provenance</span>
          <div className="text-text-primary font-bold text-xs font-mono">Immutable Hashes Active</div>
        </div>
      </div>

      <div className="bg-surface p-3 rounded-lg border border-border flex items-center gap-2.5">
        <Clock className="w-5 h-5 text-accent-gold shrink-0" />
        <div>
          <span className="text-[10px] text-text-muted uppercase">Session Status</span>
          <div className="text-emerald-400 font-bold text-xs">{session?.status || 'NO_SESSION'}</div>
        </div>
      </div>
    </div>
  );
};
