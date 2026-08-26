import React, { useEffect, useState } from 'react';
import {
  FlaskConical,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  RefreshCw,
  Layers,
  ArrowRight,
  TrendingUp,
  Clock,
  Zap,
  BarChart3,
  ShieldCheck,
  ShieldAlert,
} from 'lucide-react';
import { ExperimentEvaluation, ResearchStatus } from '../../types/strategyLab';
import { fetchStrategyResearchRegistry } from '../../services/api';

export const StrategyLab: React.FC = () => {
  const [registry, setRegistry] = useState<Record<string, ExperimentEvaluation>>({});
  const [selectedExpId, setSelectedExpId] = useState<string>('EXP_F1_COMBINED_CANDIDATE');
  const [subTab, setSubTab] = useState<'comparison' | 'gates' | 'partitions' | 'timing'>('comparison');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadRegistry();
  }, []);

  const loadRegistry = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchStrategyResearchRegistry();
      setRegistry(data);
      if (!data[selectedExpId] && Object.keys(data).length > 0) {
        setSelectedExpId(Object.keys(data)[0]);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load strategy research registry');
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status: ResearchStatus) => {
    switch (status) {
      case 'CANDIDATE_FOR_PAPER_TRADING':
        return <span className="px-2.5 py-1 bg-emerald-950/80 text-emerald-300 border border-emerald-500/50 rounded font-bold text-[10px] tracking-wide">CANDIDATE_FOR_PAPER_TRADING</span>;
      case 'RESEARCH_PROMOTED':
        return <span className="px-2.5 py-1 bg-cyan-950/80 text-cyan-300 border border-cyan-500/50 rounded font-bold text-[10px] tracking-wide">RESEARCH_PROMOTED</span>;
      case 'TEST_EVALUATED':
        return <span className="px-2.5 py-1 bg-purple-950/80 text-purple-300 border border-purple-500/50 rounded font-bold text-[10px] tracking-wide">TEST_EVALUATED</span>;
      case 'VALIDATION_PASSED':
        return <span className="px-2.5 py-1 bg-blue-950/80 text-blue-300 border border-blue-500/50 rounded font-bold text-[10px] tracking-wide">VALIDATION_PASSED</span>;
      case 'VALIDATION_FAILED':
        return <span className="px-2.5 py-1 bg-rose-950/80 text-rose-300 border border-rose-500/50 rounded font-bold text-[10px] tracking-wide">VALIDATION_FAILED</span>;
      case 'REJECTED':
        return <span className="px-2.5 py-1 bg-rose-950/80 text-rose-400 border border-rose-600/50 rounded font-bold text-[10px] tracking-wide">REJECTED</span>;
      default:
        return <span className="px-2.5 py-1 bg-surface-elevated text-text-muted border border-border rounded font-bold text-[10px]">{status}</span>;
    }
  };

  if (loading) {
    return (
      <div className="p-12 flex flex-col items-center justify-center gap-3 text-text-muted">
        <RefreshCw className="w-6 h-6 animate-spin text-accent-cyan" />
        <span className="font-mono text-xs">Loading Phase 8 Strategy Research Laboratory...</span>
      </div>
    );
  }

  if (error || Object.keys(registry).length === 0) {
    return (
      <div className="p-8 text-center bg-surface rounded-lg border border-border">
        <AlertTriangle className="w-8 h-8 text-amber-400 mx-auto mb-2" />
        <div className="text-text-primary font-bold mb-1">NO STRATEGY EXPERIMENTS AVAILABLE</div>
        <div className="text-text-muted text-xs font-mono mb-4">{error || 'No historical experiment registry found.'}</div>
        <button
          onClick={loadRegistry}
          className="px-4 py-1.5 bg-surface-elevated hover:bg-surface-elevated/80 border border-border text-xs font-mono rounded"
        >
          Initialize Research Battery
        </button>
      </div>
    );
  }

  const baseline = registry['BASELINE'];
  const exp = registry[selectedExpId] || registry[Object.keys(registry)[0]];

  return (
    <div className="flex flex-col gap-4 font-mono text-xs text-text-secondary pb-6 select-none">
      {/* Notice Banner */}
      <div className="p-3 bg-indigo-950/20 border border-indigo-500/40 rounded-lg flex items-start gap-2.5">
        <FlaskConical className="w-4 h-4 text-indigo-400 shrink-0 mt-0.5" />
        <div className="text-indigo-200/90 leading-relaxed text-[11px]">
          <span className="font-bold text-indigo-300">Phase 8 Research Laboratory:</span> Controlled hypothesis testing of redesigned entry and filtering mechanisms against the frozen Phase 5 baseline. Historical outcomes do not guarantee live trading profitability. Strategies are evaluated across strict chronological partitions (Train, Validation, and untouched Test).
        </div>
      </div>

      {/* Candidate Experiment Selector Bar */}
      <div className="flex flex-wrap items-center gap-1.5 p-2 bg-surface rounded-lg border border-border">
        <span className="text-[11px] font-bold text-text-muted mr-1 px-1">Candidate:</span>
        {Object.entries(registry).map(([k, v]) => (
          <button
            key={k}
            onClick={() => setSelectedExpId(k)}
            className={`px-2.5 py-1 rounded text-[11px] transition font-bold ${
              selectedExpId === k
                ? 'bg-surface-elevated text-accent-cyan border border-accent-cyan/50 shadow-glow-cyan/20'
                : 'text-text-muted hover:text-text-primary hover:bg-surface-elevated/50 border border-transparent'
            }`}
          >
            {k === 'BASELINE' ? 'PHASE 5 BASELINE' : k.replace('EXP_', '')}
          </button>
        ))}
      </div>

      {/* Selected Experiment Header Card */}
      <div className="p-4 bg-surface rounded-lg border border-border flex flex-col gap-3">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 border-b border-border/60 pb-3">
          <div>
            <div className="text-sm font-bold text-text-primary flex items-center gap-2">
              <span>{exp.experiment_name}</span>
            </div>
            <div className="text-[11px] text-text-muted mt-0.5">{exp.description}</div>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            {getStatusBadge(exp.status)}
            <span className="px-2 py-0.5 bg-surface-elevated border border-border text-[10px] text-text-muted rounded">
              Gates: {exp.gates_passed_count}/{exp.total_gates_count}
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-[11px]">
          <div className="bg-surface-elevated p-2.5 rounded border border-border/60">
            <span className="text-[10px] text-text-muted uppercase font-bold">Hypothesis Tested</span>
            <div className="text-text-secondary mt-1">{exp.hypothesis}</div>
          </div>
          <div className="bg-surface-elevated p-2.5 rounded border border-border/60">
            <span className="text-[10px] text-text-muted uppercase font-bold">Predeclared Parameters</span>
            <div className="text-accent-cyan mt-1 font-mono text-[10px] truncate" title={JSON.stringify(exp.parameters)}>
              {JSON.stringify(exp.parameters)}
            </div>
          </div>
          <div className="bg-surface-elevated p-2.5 rounded border border-border/60">
            <span className="text-[10px] text-text-muted uppercase font-bold">Decision Rationale</span>
            <div className="text-text-secondary mt-1">{exp.decision_rationale}</div>
          </div>
        </div>
      </div>

      {/* Sub-tabs Navigation */}
      <div className="flex items-center gap-1 border-b border-border/80 pb-1">
        <button
          onClick={() => setSubTab('comparison')}
          className={`px-3 py-1 rounded text-xs transition ${subTab === 'comparison' ? 'bg-surface-elevated text-accent-cyan font-bold border border-accent-cyan/40' : 'text-text-muted hover:text-text-primary'}`}
        >
          Baseline vs Candidate Comparison
        </button>
        <button
          onClick={() => setSubTab('gates')}
          className={`px-3 py-1 rounded text-xs transition ${subTab === 'gates' ? 'bg-surface-elevated text-accent-cyan font-bold border border-accent-cyan/40' : 'text-text-muted hover:text-text-primary'}`}
        >
          10-Gate Promotion Checklist
        </button>
        <button
          onClick={() => setSubTab('partitions')}
          className={`px-3 py-1 rounded text-xs transition ${subTab === 'partitions' ? 'bg-surface-elevated text-accent-cyan font-bold border border-accent-cyan/40' : 'text-text-muted hover:text-text-primary'}`}
        >
          Train / Validation / Test Partitions
        </button>
        <button
          onClick={() => setSubTab('timing')}
          className={`px-3 py-1 rounded text-xs transition ${subTab === 'timing' ? 'bg-surface-elevated text-accent-cyan font-bold border border-accent-cyan/40' : 'text-text-muted hover:text-text-primary'}`}
        >
          Pre vs Post Timing & Clustering
        </button>
      </div>

      {/* Sub-Tab 1: Baseline vs Experiment Comparison */}
      {subTab === 'comparison' && baseline && (
        <div className="flex flex-col gap-3">
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-2">
            {/* Metric 1: Signal Count */}
            <div className="bg-surface p-3 rounded-lg border border-border">
              <span className="text-[10px] text-text-muted uppercase">Validation Signals</span>
              <div className="text-text-primary font-bold text-sm mt-0.5">{exp.validation_metrics.signal_count.toLocaleString()}</div>
              <div className="text-[10px] text-text-muted mt-1">Baseline: {baseline.validation_metrics.signal_count.toLocaleString()}</div>
            </div>

            {/* Metric 2: 5C Median Return */}
            <div className="bg-surface p-3 rounded-lg border border-border">
              <span className="text-[10px] text-text-muted uppercase">Val 5C Median Return</span>
              <div className={`font-bold text-sm mt-0.5 ${exp.validation_metrics.h5_median >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                {(exp.validation_metrics.h5_median * 100).toFixed(3)}%
              </div>
              <div className="text-[10px] text-text-muted mt-1">Baseline: {(baseline.validation_metrics.h5_median * 100).toFixed(3)}%</div>
            </div>

            {/* Metric 3: Positive Rate */}
            <div className="bg-surface p-3 rounded-lg border border-border">
              <span className="text-[10px] text-text-muted uppercase">Val 5C Positive Rate</span>
              <div className="text-text-primary font-bold text-sm mt-0.5">{exp.validation_metrics.positive_rate_5c.toFixed(1)}%</div>
              <div className="text-[10px] text-text-muted mt-1">Baseline: {baseline.validation_metrics.positive_rate_5c.toFixed(1)}%</div>
            </div>

            {/* Metric 4: Pre-5C Extension */}
            <div className="bg-surface p-3 rounded-lg border border-border">
              <span className="text-[10px] text-text-muted uppercase">Pre-5C Extension</span>
              <div className="text-text-primary font-bold text-sm mt-0.5">{(exp.validation_metrics.timing.pre_5_median * 100).toFixed(3)}%</div>
              <div className="text-[10px] text-text-muted mt-1">Baseline: {(baseline.validation_metrics.timing.pre_5_median * 100).toFixed(3)}%</div>
            </div>

            {/* Metric 5: Adjacent Clustering */}
            <div className="bg-surface p-3 rounded-lg border border-border">
              <span className="text-[10px] text-text-muted uppercase">Adjacent Bar Clusters</span>
              <div className="text-text-primary font-bold text-sm mt-0.5">{exp.validation_metrics.clustering.adjacent_signal_rate.toFixed(1)}%</div>
              <div className="text-[10px] text-text-muted mt-1">Baseline: {baseline.validation_metrics.clustering.adjacent_signal_rate.toFixed(1)}%</div>
            </div>

            {/* Metric 6: Test 5C Return */}
            <div className="bg-surface p-3 rounded-lg border border-border">
              <span className="text-[10px] text-text-muted uppercase">Test 5C Median Return</span>
              <div className={`font-bold text-sm mt-0.5 ${(exp.test_metrics?.h5_median || 0) >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                {exp.test_metrics ? `${(exp.test_metrics.h5_median * 100).toFixed(3)}%` : 'UNTESTED'}
              </div>
              <div className="text-[10px] text-text-muted mt-1">Baseline: {(baseline.test_metrics?.h5_median ? baseline.test_metrics.h5_median * 100 : 0).toFixed(3)}%</div>
            </div>
          </div>
        </div>
      )}

      {/* Sub-Tab 2: 10-Gate Promotion Checklist */}
      {subTab === 'gates' && (
        <div className="p-4 bg-surface rounded-lg border border-border flex flex-col gap-3">
          <div className="flex items-center justify-between border-b border-border/60 pb-2">
            <span className="font-bold text-text-primary flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-accent-cyan" />
              <span>Objective Promotion Gates Evaluation</span>
            </span>
            <span className="text-text-muted text-[11px]">
              Required: Passes Validation Gates + Untouched Test Generalization
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-[11px]">
              <thead>
                <tr className="border-b border-border/80 text-text-muted text-left">
                  <th className="pb-1.5">Gate ID</th>
                  <th className="pb-1.5">Gate Name & Description</th>
                  <th className="pb-1.5">Required Threshold</th>
                  <th className="pb-1.5">Candidate Measured</th>
                  <th className="pb-1.5 text-center">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/40">
                {exp.promotion_gates.map((g) => (
                  <tr key={g.gate_id} className="py-2">
                    <td className="py-2 font-bold text-accent-cyan">{g.gate_id}</td>
                    <td className="py-2 text-text-primary">
                      <div className="font-bold">{g.gate_name}</div>
                      <div className="text-[10px] text-text-muted">{g.details}</div>
                    </td>
                    <td className="py-2 font-mono text-text-muted">{g.required_criterion}</td>
                    <td className="py-2 font-mono font-bold text-text-primary">{g.measured_value}</td>
                    <td className="py-2 text-center font-bold">
                      {g.passed ? (
                        <span className="px-2 py-0.5 bg-emerald-950 text-emerald-300 border border-emerald-500/40 rounded text-[10px]">PASS</span>
                      ) : (
                        <span className="px-2 py-0.5 bg-rose-950 text-rose-300 border border-rose-500/40 rounded text-[10px]">FAIL</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Sub-Tab 3: Chronological Partitions */}
      {subTab === 'partitions' && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {/* Train */}
          <div className="p-3 bg-surface rounded-lg border border-border flex flex-col gap-2">
            <span className="font-bold text-text-primary border-b border-border/60 pb-1.5 flex items-center justify-between">
              <span>TRAIN (2024 Full Year)</span>
              <span className="text-[10px] text-text-muted">N = {exp.train_metrics.signal_count.toLocaleString()}</span>
            </span>
            <div className="flex flex-col gap-1 text-[11px]">
              <div className="flex justify-between"><span className="text-text-muted">5C Median Return:</span><span className="font-bold text-rose-400">{(exp.train_metrics.h5_median * 100).toFixed(3)}%</span></div>
              <div className="flex justify-between"><span className="text-text-muted">10C Median Return:</span><span className="font-bold text-rose-400">{(exp.train_metrics.h10_median * 100).toFixed(3)}%</span></div>
              <div className="flex justify-between"><span className="text-text-muted">Positive Rate 5C:</span><span className="font-bold text-text-primary">{exp.train_metrics.positive_rate_5c.toFixed(1)}%</span></div>
              <div className="flex justify-between"><span className="text-text-muted">Signals / Day:</span><span className="font-bold text-text-primary">{exp.train_metrics.signals_per_day}</span></div>
              <div className="flex justify-between"><span className="text-text-muted">Adjacent Clustering:</span><span className="font-bold text-text-primary">{exp.train_metrics.clustering.adjacent_signal_rate.toFixed(1)}%</span></div>
            </div>
          </div>

          {/* Validation */}
          <div className="p-3 bg-surface rounded-lg border border-border flex flex-col gap-2">
            <span className="font-bold text-accent-cyan border-b border-border/60 pb-1.5 flex items-center justify-between">
              <span>VALIDATION (2025 H1)</span>
              <span className="text-[10px] text-text-muted">N = {exp.validation_metrics.signal_count.toLocaleString()}</span>
            </span>
            <div className="flex flex-col gap-1 text-[11px]">
              <div className="flex justify-between"><span className="text-text-muted">5C Median Return:</span><span className="font-bold text-rose-400">{(exp.validation_metrics.h5_median * 100).toFixed(3)}%</span></div>
              <div className="flex justify-between"><span className="text-text-muted">10C Median Return:</span><span className="font-bold text-rose-400">{(exp.validation_metrics.h10_median * 100).toFixed(3)}%</span></div>
              <div className="flex justify-between"><span className="text-text-muted">Positive Rate 5C:</span><span className="font-bold text-text-primary">{exp.validation_metrics.positive_rate_5c.toFixed(1)}%</span></div>
              <div className="flex justify-between"><span className="text-text-muted">Signals / Day:</span><span className="font-bold text-text-primary">{exp.validation_metrics.signals_per_day}</span></div>
              <div className="flex justify-between"><span className="text-text-muted">Adjacent Clustering:</span><span className="font-bold text-text-primary">{exp.validation_metrics.clustering.adjacent_signal_rate.toFixed(1)}%</span></div>
            </div>
          </div>

          {/* Test */}
          <div className="p-3 bg-surface rounded-lg border border-border flex flex-col gap-2">
            <span className="font-bold text-purple-400 border-b border-border/60 pb-1.5 flex items-center justify-between">
              <span>UNTOUCHED TEST (2025 H2)</span>
              <span className="text-[10px] text-text-muted">N = {exp.test_metrics?.signal_count.toLocaleString() || 0}</span>
            </span>
            <div className="flex flex-col gap-1 text-[11px]">
              <div className="flex justify-between"><span className="text-text-muted">5C Median Return:</span><span className="font-bold text-rose-400">{exp.test_metrics ? `${(exp.test_metrics.h5_median * 100).toFixed(3)}%` : 'UNTESTED'}</span></div>
              <div className="flex justify-between"><span className="text-text-muted">10C Median Return:</span><span className="font-bold text-rose-400">{exp.test_metrics ? `${(exp.test_metrics.h10_median * 100).toFixed(3)}%` : 'UNTESTED'}</span></div>
              <div className="flex justify-between"><span className="text-text-muted">Positive Rate 5C:</span><span className="font-bold text-text-primary">{exp.test_metrics ? `${exp.test_metrics.positive_rate_5c.toFixed(1)}%` : 'UNTESTED'}</span></div>
              <div className="flex justify-between"><span className="text-text-muted">Signals / Day:</span><span className="font-bold text-text-primary">{exp.test_metrics?.signals_per_day || 0}</span></div>
              <div className="flex justify-between"><span className="text-text-muted">Adjacent Clustering:</span><span className="font-bold text-text-primary">{exp.test_metrics ? `${exp.test_metrics.clustering.adjacent_signal_rate.toFixed(1)}%` : 'UNTESTED'}</span></div>
            </div>
          </div>
        </div>
      )}

      {/* Sub-Tab 4: Pre vs Post Timing */}
      {subTab === 'timing' && (
        <div className="p-4 bg-surface rounded-lg border border-border flex flex-col gap-3">
          <div className="font-bold text-text-primary flex items-center gap-2 border-b border-border/60 pb-2">
            <Clock className="w-4 h-4 text-accent-gold" />
            <span>Pre-Signal Price Movement vs Post-Signal Analytical Follow-Through (Validation)</span>
          </div>

          <table className="w-full text-center text-[11px] mt-1">
            <thead>
              <tr className="border-b border-border/80 text-text-muted">
                <th className="pb-1.5 text-left">Horizon</th>
                <th className="pb-1.5">Pre-Signal Median</th>
                <th className="pb-1.5">Post-Signal Median</th>
                <th className="pb-1.5">Long 5C</th>
                <th className="pb-1.5">Short 5C</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/40">
              <tr>
                <td className="py-2 text-left font-bold">1 Candle (15m)</td>
                <td className="py-2 font-mono text-text-muted">{(exp.validation_metrics.timing.pre_1_median * 100).toFixed(3)}%</td>
                <td className="py-2 font-mono font-bold text-rose-400">{(exp.validation_metrics.h1_median * 100).toFixed(3)}%</td>
                <td className="py-2 font-mono text-text-muted">-</td>
                <td className="py-2 font-mono text-text-muted">-</td>
              </tr>
              <tr>
                <td className="py-2 text-left font-bold">3 Candles (45m)</td>
                <td className="py-2 font-mono text-text-muted">{(exp.validation_metrics.timing.pre_3_median * 100).toFixed(3)}%</td>
                <td className="py-2 font-mono font-bold text-rose-400">{(exp.validation_metrics.h3_median * 100).toFixed(3)}%</td>
                <td className="py-2 font-mono text-text-muted">-</td>
                <td className="py-2 font-mono text-text-muted">-</td>
              </tr>
              <tr>
                <td className="py-2 text-left font-bold">5 Candles (75m)</td>
                <td className="py-2 font-mono text-text-muted">{(exp.validation_metrics.timing.pre_5_median * 100).toFixed(3)}%</td>
                <td className="py-2 font-mono font-bold text-rose-400">{(exp.validation_metrics.h5_median * 100).toFixed(3)}%</td>
                <td className="py-2 font-mono text-rose-400">{(exp.validation_metrics.long_5c_median * 100).toFixed(3)}%</td>
                <td className="py-2 font-mono text-rose-400">{(exp.validation_metrics.short_5c_median * 100).toFixed(3)}%</td>
              </tr>
              <tr>
                <td className="py-2 text-left font-bold">10 Candles (2.5h)</td>
                <td className="py-2 font-mono text-text-muted">{(exp.validation_metrics.timing.pre_10_median * 100).toFixed(3)}%</td>
                <td className="py-2 font-mono font-bold text-rose-400">{(exp.validation_metrics.h10_median * 100).toFixed(3)}%</td>
                <td className="py-2 font-mono text-rose-400">{(exp.validation_metrics.long_10c_median * 100).toFixed(3)}%</td>
                <td className="py-2 font-mono text-rose-400">{(exp.validation_metrics.short_10c_median * 100).toFixed(3)}%</td>
              </tr>
              <tr>
                <td className="py-2 text-left font-bold">20 Candles (5.0h)</td>
                <td className="py-2 font-mono text-text-muted">{(exp.validation_metrics.timing.pre_20_median * 100).toFixed(3)}%</td>
                <td className="py-2 font-mono font-bold text-rose-400">{(exp.validation_metrics.h20_median * 100).toFixed(3)}%</td>
                <td className="py-2 font-mono text-rose-400">{(exp.validation_metrics.long_20c_median * 100).toFixed(3)}%</td>
                <td className="py-2 font-mono text-rose-400">{(exp.validation_metrics.short_20c_median * 100).toFixed(3)}%</td>
              </tr>
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
