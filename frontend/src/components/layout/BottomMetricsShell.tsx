import React, { useState } from 'react';
import { Activity, Compass, GitBranch, Zap, History, Shield, Database, PlayCircle, Target, FlaskConical, Radio, Layers } from 'lucide-react';
import { useMarketStore } from '../../stores/marketStore';
import { IndicatorPanel } from '../indicators/IndicatorPanel';
import { RegimePanel } from '../regime/RegimePanel';
import { MarketStructurePanel } from '../structure/MarketStructurePanel';
import { SignalResearchPanel } from '../intelligence/SignalResearchPanel';
import { BacktestDashboard } from '../backtesting/BacktestDashboard';
import { ForensicsDashboard } from '../forensics/ForensicsDashboard';
import { StrategyLab } from '../strategy-lab/StrategyLab';
import { ShadowValidationDashboard } from '../shadow/ShadowValidationDashboard';
import { TradeDecisionDetails } from '../trade-decision/TradeDecisionDetails';
import { ProfileMetrics } from '../profiles/ProfileMetrics';
import { ProfileComparison } from '../profiles/ProfileComparison';

type Tab = 'decision' | 'profiles' | 'signal' | 'backtest' | 'forensics' | 'strategylab' | 'shadow' | 'matrix' | 'regime' | 'structure' | 'derivatives';

export const BottomMetricsShell: React.FC = () => {
  const [activeTab, setActiveTab] = useState<Tab>('decision');
  const { symbol, timeframe } = useMarketStore();

  return (
    <div className="bg-surface-card rounded-lg border border-border flex flex-col overflow-hidden select-none">
      {/* Tab Navigation */}
      <div className="min-h-[40px] h-auto bg-surface px-2 py-1 flex items-center gap-1 border-b border-border/80 overflow-x-auto scrollbar-none">
        <button
          onClick={() => setActiveTab('decision')}
          className={`flex items-center gap-1.5 px-2.5 sm:px-3 py-1.5 rounded text-[11px] sm:text-xs font-mono font-medium transition shrink-0 ${
            activeTab === 'decision'
              ? 'bg-indigo-600 text-white font-bold shadow-lg shadow-indigo-600/30'
              : 'text-text-secondary hover:text-text-primary hover:bg-surface-elevated/50'
          }`}
        >
          <Target className="w-3.5 h-3.5" />
          <span>Decision & Audit</span>
        </button>

        <button
          onClick={() => setActiveTab('profiles')}
          className={`flex items-center gap-1.5 px-2.5 sm:px-3 py-1.5 rounded text-[11px] sm:text-xs font-mono font-medium transition shrink-0 ${
            activeTab === 'profiles'
              ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/40 font-bold shadow-glow-indigo/20'
              : 'text-text-secondary hover:text-text-primary hover:bg-surface-elevated/50'
          }`}
        >
          <Layers className="w-3.5 h-3.5 text-indigo-400" />
          <span>Profiles & Horizons</span>
        </button>

        <button
          onClick={() => setActiveTab('signal')}
          className={`flex items-center gap-1.5 px-2.5 sm:px-3 py-1.5 rounded text-[11px] sm:text-xs font-mono font-medium transition shrink-0 ${
            activeTab === 'signal'
              ? 'bg-surface-elevated text-accent-cyan border border-accent-cyan/40 font-bold shadow-glow-cyan/20'
              : 'text-text-secondary hover:text-text-primary hover:bg-surface-elevated/50'
          }`}
        >
          <Zap className="w-3.5 h-3.5 text-accent-cyan" />
          <span>Research Signals</span>
        </button>

        <button
          onClick={() => setActiveTab('backtest')}
          className={`flex items-center gap-1.5 px-2.5 sm:px-3 py-1.5 rounded text-[11px] sm:text-xs font-mono font-medium transition shrink-0 ${
            activeTab === 'backtest'
              ? 'bg-surface-elevated text-emerald-400 border border-emerald-500/40 font-bold'
              : 'text-text-secondary hover:text-text-primary hover:bg-surface-elevated/50'
          }`}
        >
          <PlayCircle className="w-3.5 h-3.5 text-emerald-400" />
          <span>Backtest</span>
        </button>

        <button
          onClick={() => setActiveTab('forensics')}
          className={`flex items-center gap-1.5 px-2.5 sm:px-3 py-1.5 rounded text-[11px] sm:text-xs font-mono font-medium transition shrink-0 ${
            activeTab === 'forensics'
              ? 'bg-surface-elevated text-purple-300 border border-purple-500/40 font-bold shadow-glow-purple/20'
              : 'text-text-secondary hover:text-text-primary hover:bg-surface-elevated/50'
          }`}
        >
          <Compass className="w-3.5 h-3.5 text-purple-400" />
          <span>Forensics</span>
        </button>

        <button
          onClick={() => setActiveTab('strategylab')}
          className={`flex items-center gap-1.5 px-2.5 sm:px-3 py-1.5 rounded text-[11px] sm:text-xs font-mono font-medium transition shrink-0 ${
            activeTab === 'strategylab'
              ? 'bg-surface-elevated text-indigo-300 border border-indigo-500/40 font-bold shadow-glow-cyan/20'
              : 'text-text-secondary hover:text-text-primary hover:bg-surface-elevated/50'
          }`}
        >
          <FlaskConical className="w-3.5 h-3.5 text-indigo-400" />
          <span>Strategy Lab</span>
        </button>

        <button
          onClick={() => setActiveTab('shadow')}
          className={`flex items-center gap-1.5 px-2.5 sm:px-3 py-1.5 rounded text-[11px] sm:text-xs font-mono font-medium transition shrink-0 ${
            activeTab === 'shadow'
              ? 'bg-surface-elevated text-amber-300 border border-amber-500/40 font-bold shadow-glow-gold/20'
              : 'text-text-secondary hover:text-text-primary hover:bg-surface-elevated/50'
          }`}
        >
          <Radio className="w-3.5 h-3.5 text-amber-400" />
          <span>Shadow</span>
        </button>

        <button
          onClick={() => setActiveTab('matrix')}
          className={`flex items-center gap-1.5 px-2.5 sm:px-3 py-1.5 rounded text-[11px] sm:text-xs font-mono font-medium transition shrink-0 ${
            activeTab === 'matrix'
              ? 'bg-surface-elevated text-accent-cyan border border-accent-cyan/30'
              : 'text-text-secondary hover:text-text-primary hover:bg-surface-elevated/50'
          }`}
        >
          <Activity className="w-3.5 h-3.5" />
          <span>Indicators</span>
        </button>

        <button
          onClick={() => setActiveTab('regime')}
          className={`flex items-center gap-1.5 px-2.5 sm:px-3 py-1.5 rounded text-[11px] sm:text-xs font-mono font-medium transition shrink-0 ${
            activeTab === 'regime'
              ? 'bg-surface-elevated text-accent-gold border border-accent-gold/30'
              : 'text-text-secondary hover:text-text-primary hover:bg-surface-elevated/50'
          }`}
        >
          <Compass className="w-3.5 h-3.5" />
          <span>Regime</span>
        </button>

        <button
          onClick={() => setActiveTab('structure')}
          className={`flex items-center gap-1.5 px-2.5 sm:px-3 py-1.5 rounded text-[11px] sm:text-xs font-mono font-medium transition shrink-0 ${
            activeTab === 'structure'
              ? 'bg-surface-elevated text-purple-400 border border-purple-400/30'
              : 'text-text-secondary hover:text-text-primary hover:bg-surface-elevated/50'
          }`}
        >
          <GitBranch className="w-3.5 h-3.5" />
          <span>Structure</span>
        </button>

        <button
          onClick={() => setActiveTab('derivatives')}
          className={`flex items-center gap-1.5 px-2.5 sm:px-3 py-1.5 rounded text-[11px] sm:text-xs font-mono font-medium transition shrink-0 ${
            activeTab === 'derivatives'
              ? 'bg-surface-elevated text-text-primary border border-border-subtle'
              : 'text-text-secondary hover:text-text-primary hover:bg-surface-elevated/50'
          }`}
        >
          <Database className="w-3.5 h-3.5" />
          <span>Derivatives</span>
        </button>
      </div>

      {/* Tab Content */}
      <div className="p-2 sm:p-3 font-mono text-xs text-text-secondary overflow-x-auto">
        {activeTab === 'decision' && <TradeDecisionDetails />}

        {activeTab === 'profiles' && (
          <div className="space-y-4">
            <ProfileMetrics />
            <ProfileComparison />
          </div>
        )}

        {activeTab === 'signal' && <SignalResearchPanel />}

        {activeTab === 'backtest' && <BacktestDashboard symbol={symbol} timeframe={timeframe} />}

        {activeTab === 'forensics' && <ForensicsDashboard />}

        {activeTab === 'strategylab' && <StrategyLab />}

        {activeTab === 'shadow' && <ShadowValidationDashboard />}

        {activeTab === 'matrix' && <IndicatorPanel />}

        {activeTab === 'regime' && <RegimePanel />}

        {activeTab === 'structure' && <MarketStructurePanel />}

        {activeTab === 'derivatives' && (
          <div className="p-8 text-center text-text-muted">
            <span className="text-purple-400 font-semibold">Derivatives Pipeline</span>: Funding rates, Open Interest, and Liquidations will be integrated in Phase 11.
          </div>
        )}
      </div>
    </div>
  );
};
