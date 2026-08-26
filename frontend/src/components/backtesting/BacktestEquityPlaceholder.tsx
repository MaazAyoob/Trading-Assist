import React from 'react';
import { AlertTriangle, Lock } from 'lucide-react';

export const BacktestEquityPlaceholder: React.FC = () => {
  return (
    <div className="bg-surface/30 border border-border-subtle/60 rounded-lg p-4 font-mono text-xs text-text-muted flex items-start gap-3">
      <div className="p-2 rounded bg-surface-card border border-border-subtle shrink-0">
        <Lock className="w-5 h-5 text-accent-gold" />
      </div>
      <div className="space-y-1">
        <div className="flex items-center gap-2">
          <span className="font-bold text-text-primary uppercase tracking-wider">
            Execution Simulation & Equity Curves Disabled (Phase 6 Analytical Scope)
          </span>
          <span className="bg-accent-gold/20 text-accent-gold text-[10px] px-2 py-0.5 rounded font-bold">
            RESEARCH ONLY
          </span>
        </div>
        <p className="text-[11px] leading-relaxed text-text-secondary">
          Phase 6 evaluates the historical predictive behavior of the multi-factor signal engine via <strong>causal forward-return distributions, excursions (MFE/MAE), and statistical confidence intervals</strong>.
          An equity curve requires order fill models, stop-loss triggers, take-profit exits, and position sizing, which are intentionally out of scope for the signal research validation phase.
        </p>
      </div>
    </div>
  );
};
