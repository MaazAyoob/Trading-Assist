import React, { useEffect, useState } from 'react';
import {
  AlertTriangle,
  Clock,
  Layers,
  TrendingDown,
  TrendingUp,
  Activity,
  CheckCircle2,
  HelpCircle,
  BarChart3,
  RefreshCw,
  Zap,
  ShieldAlert,
} from 'lucide-react';
import { ForensicsReport } from '../../types/forensics';
import { fetchForensicsSummary } from '../../services/api';

export const ForensicsDashboard: React.FC = () => {
  const [report, setReport] = useState<ForensicsReport | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [subTab, setSubTab] = useState<'diagnosis' | 'timing' | 'factors' | 'partitions'>('diagnosis');

  useEffect(() => {
    loadForensics();
  }, []);

  const loadForensics = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchForensicsSummary();
      setReport(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load forensics report');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="p-12 flex flex-col items-center justify-center gap-3 text-text-muted">
        <RefreshCw className="w-6 h-6 animate-spin text-accent-cyan" />
        <span className="font-mono text-xs">Loading Phase 7 Causal Signal Forensics...</span>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="p-8 text-center bg-rose-950/20 border border-rose-800/40 rounded-lg">
        <AlertTriangle className="w-8 h-8 text-rose-400 mx-auto mb-2" />
        <div className="text-rose-300 font-bold mb-1">NO FORENSICS RUN AVAILABLE</div>
        <div className="text-text-muted text-xs font-mono mb-4">{error || 'No historical forensics dataset found.'}</div>
        <button
          onClick={loadForensics}
          className="px-4 py-1.5 bg-surface-elevated hover:bg-surface-elevated/80 border border-border text-xs font-mono rounded"
        >
          Retry Load
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4 font-mono text-xs text-text-secondary pb-6">
      {/* Notice Banner */}
      <div className="p-3 bg-amber-950/20 border border-amber-500/40 rounded-lg flex items-start gap-2.5">
        <ShieldAlert className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
        <div className="text-amber-200/90 leading-relaxed text-[11px]">
          <span className="font-bold text-amber-300">Phase 7 Diagnostic Notice:</span> Factor contribution describes how the frozen Phase 5 signal score was constructed. It does not establish that any individual factor independently predicts future market returns. Strategy parameters remain 100% frozen.
        </div>
      </div>

      {/* Top Header Card */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-2 bg-surface p-3 rounded-lg border border-border">
        <div>
          <span className="text-[10px] text-text-muted uppercase">Dataset</span>
          <div className="text-text-primary font-bold truncate" title={report.dataset_id}>{report.symbol} {report.timeframe} (2 Yrs)</div>
        </div>
        <div>
          <span className="text-[10px] text-text-muted uppercase">Candles Analyzed</span>
          <div className="text-text-primary font-bold">{report.candle_count.toLocaleString()}</div>
        </div>
        <div>
          <span className="text-[10px] text-text-muted uppercase">Total Signals</span>
          <div className="text-text-primary font-bold">{report.total_signals.toLocaleString()}</div>
        </div>
        <div>
          <span className="text-[10px] text-text-muted uppercase">Long / Short</span>
          <div className="text-text-primary font-bold">
            <span className="text-emerald-400">{report.long_signals.toLocaleString()}</span> / <span className="text-rose-400">{report.short_signals.toLocaleString()}</span>
          </div>
        </div>
        <div>
          <span className="text-[10px] text-text-muted uppercase">Score Monotonicity</span>
          <div className={`font-bold ${report.score_monotonicity_grade === 'INVERSE' ? 'text-rose-400' : 'text-amber-400'}`}>
            {report.score_monotonicity_grade}
          </div>
        </div>
        <div>
          <span className="text-[10px] text-text-muted uppercase">Execution Time</span>
          <div className="text-text-primary font-bold">{report.runtime_seconds}s</div>
        </div>
      </div>

      {/* Sub-tabs Navigation */}
      <div className="flex items-center gap-1 border-b border-border/80 pb-1">
        <button
          onClick={() => setSubTab('diagnosis')}
          className={`px-3 py-1 rounded text-xs transition ${subTab === 'diagnosis' ? 'bg-surface-elevated text-accent-cyan font-bold border border-accent-cyan/40' : 'text-text-muted hover:text-text-primary'}`}
        >
          Research Diagnosis
        </button>
        <button
          onClick={() => setSubTab('timing')}
          className={`px-3 py-1 rounded text-xs transition ${subTab === 'timing' ? 'bg-surface-elevated text-accent-cyan font-bold border border-accent-cyan/40' : 'text-text-muted hover:text-text-primary'}`}
        >
          Signal Timing & Trend-Chasing
        </button>
        <button
          onClick={() => setSubTab('factors')}
          className={`px-3 py-1 rounded text-xs transition ${subTab === 'factors' ? 'bg-surface-elevated text-accent-cyan font-bold border border-accent-cyan/40' : 'text-text-muted hover:text-text-primary'}`}
        >
          Factor Attribution & Calibration
        </button>
        <button
          onClick={() => setSubTab('partitions')}
          className={`px-3 py-1 rounded text-xs transition ${subTab === 'partitions' ? 'bg-surface-elevated text-accent-cyan font-bold border border-accent-cyan/40' : 'text-text-muted hover:text-text-primary'}`}
        >
          Partitions & Stability
        </button>
      </div>

      {/* 1. Research Diagnosis Sub-Tab */}
      {subTab === 'diagnosis' && (
        <div className="flex flex-col gap-4">
          <div className="p-4 bg-surface rounded-lg border border-border flex flex-col gap-2.5">
            <div className="flex items-center gap-2 text-emerald-400 font-bold text-sm">
              <CheckCircle2 className="w-4 h-4" />
              <span>1. OBSERVED FACTS (Empirical Measurements)</span>
            </div>
            <ul className="list-disc list-inside text-text-secondary space-y-1.5 pl-2 text-[11px] leading-relaxed">
              {report.observed_facts.map((fact, idx) => (
                <li key={idx}><span className="text-text-primary">{fact}</span></li>
              ))}
            </ul>
          </div>

          <div className="p-4 bg-surface rounded-lg border border-border flex flex-col gap-2.5">
            <div className="flex items-center gap-2 text-amber-400 font-bold text-sm">
              <AlertTriangle className="w-4 h-4" />
              <span>2. POSSIBLE EXPLANATIONS (Analytical Interpretations)</span>
            </div>
            <ul className="list-disc list-inside text-text-secondary space-y-1.5 pl-2 text-[11px] leading-relaxed">
              {report.possible_explanations.map((exp, idx) => (
                <li key={idx}><span>{exp}</span></li>
              ))}
            </ul>
          </div>

          <div className="p-4 bg-surface rounded-lg border border-border flex flex-col gap-2.5">
            <div className="flex items-center gap-2 text-rose-400 font-bold text-sm">
              <HelpCircle className="w-4 h-4" />
              <span>3. UNPROVEN HYPOTHESES (Requiring Future Experimental Testing)</span>
            </div>
            <ul className="list-disc list-inside text-text-secondary space-y-1.5 pl-2 text-[11px] leading-relaxed">
              {report.unproven_hypotheses.map((hyp, idx) => (
                <li key={idx}><span className="text-rose-200/90">{hyp}</span></li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* 2. Timing & Trend-Chasing Sub-Tab */}
      {subTab === 'timing' && (
        <div className="flex flex-col gap-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {/* Long Timing */}
            <div className="p-3 bg-surface rounded-lg border border-border flex flex-col gap-2">
              <div className="flex items-center justify-between">
                <span className="font-bold text-emerald-400 flex items-center gap-1.5">
                  <TrendingUp className="w-4 h-4" /> LONG SETUP Pre vs Post Timing
                </span>
                <span className="px-2 py-0.5 bg-rose-950/40 text-rose-300 border border-rose-800/40 rounded text-[10px]">
                  {report.timing_long.reversal_vs_continuation_classification}
                </span>
              </div>
              <div className="text-[11px] text-text-muted">{report.timing_long.trend_chasing_diagnostic}</div>
              <table className="w-full mt-2 text-center text-[11px]">
                <thead>
                  <tr className="border-b border-border/80 text-text-muted">
                    <th className="pb-1 text-left">Horizon</th>
                    <th className="pb-1">Pre-Signal Median</th>
                    <th className="pb-1">Post-Signal Median</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/40">
                  {report.timing_long.horizons.map((h) => (
                    <tr key={h}>
                      <td className="py-1 text-left font-bold">{h} candles ({h * 15}m)</td>
                      <td className="py-1 text-emerald-400 font-bold">
                        +{(report.timing_long.pre_signal_median_returns[h] * 100).toFixed(3)}%
                      </td>
                      <td className={`py-1 font-bold ${report.timing_long.post_signal_median_returns[h] >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                        {(report.timing_long.post_signal_median_returns[h] * 100).toFixed(3)}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Short Timing */}
            <div className="p-3 bg-surface rounded-lg border border-border flex flex-col gap-2">
              <div className="flex items-center justify-between">
                <span className="font-bold text-rose-400 flex items-center gap-1.5">
                  <TrendingDown className="w-4 h-4" /> SHORT SETUP Pre vs Post Timing
                </span>
                <span className="px-2 py-0.5 bg-rose-950/40 text-rose-300 border border-rose-800/40 rounded text-[10px]">
                  {report.timing_short.reversal_vs_continuation_classification}
                </span>
              </div>
              <div className="text-[11px] text-text-muted">{report.timing_short.trend_chasing_diagnostic}</div>
              <table className="w-full mt-2 text-center text-[11px]">
                <thead>
                  <tr className="border-b border-border/80 text-text-muted">
                    <th className="pb-1 text-left">Horizon</th>
                    <th className="pb-1">Pre-Signal Median</th>
                    <th className="pb-1">Post-Signal Median</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/40">
                  {report.timing_short.horizons.map((h) => (
                    <tr key={h}>
                      <td className="py-1 text-left font-bold">{h} candles ({h * 15}m)</td>
                      <td className="py-1 text-rose-400 font-bold">
                        {(report.timing_short.pre_signal_median_returns[h] * 100).toFixed(3)}%
                      </td>
                      <td className={`py-1 font-bold ${report.timing_short.post_signal_median_returns[h] >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                        {(report.timing_short.post_signal_median_returns[h] * 100).toFixed(3)}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Clustering & Persistence */}
          <div className="p-4 bg-surface rounded-lg border border-border flex flex-col gap-2">
            <div className="font-bold text-text-primary flex items-center gap-2">
              <Clock className="w-4 h-4 text-purple-400" />
              <span>Signal Clustering & Directional Persistence</span>
            </div>
            <div className="text-[11px] text-amber-300/90">{report.clustering.dependence_warning}</div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-2">
              <div className="bg-surface-elevated p-2 rounded border border-border/60">
                <span className="text-[10px] text-text-muted">Adjacent Bar Clusters (dt=1)</span>
                <div className="text-text-primary font-bold text-sm">{report.clustering.pct_within_1_candle}%</div>
              </div>
              <div className="bg-surface-elevated p-2 rounded border border-border/60">
                <span className="text-[10px] text-text-muted">Clusters within 4 Bars</span>
                <div className="text-text-primary font-bold text-sm">{report.clustering.pct_within_4_candles}%</div>
              </div>
              <div className="bg-surface-elevated p-2 rounded border border-border/60">
                <span className="text-[10px] text-text-muted">Avg Continuous Run Length</span>
                <div className="text-text-primary font-bold text-sm">{report.clustering.long_run_lengths_avg} bars</div>
              </div>
              <div className="bg-surface-elevated p-2 rounded border border-border/60">
                <span className="text-[10px] text-text-muted">Effective Independent Episodes</span>
                <div className="text-accent-cyan font-bold text-sm">~{report.clustering.effective_sample_size_estimate.toLocaleString()}</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 3. Factor Attribution & Score Calibration Sub-Tab */}
      {subTab === 'factors' && (
        <div className="flex flex-col gap-4">
          {/* Factor Monotonicity Table */}
          <div className="p-4 bg-surface rounded-lg border border-border flex flex-col gap-2">
            <div className="font-bold text-text-primary flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-accent-cyan" />
              <span>Individual Factor Monotonicity Evaluations (H=5 Candles)</span>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-center text-[11px] mt-2">
                <thead>
                  <tr className="border-b border-border/80 text-text-muted">
                    <th className="pb-1 text-left">Factor Name</th>
                    <th className="pb-1">Monotonicity Grade</th>
                    <th className="pb-1">Spearman Corr</th>
                    <th className="pb-1 text-right">Criteria & Diagnostic Description</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/40">
                  {report.factor_monotonicity.filter(f => f.horizon === 5).map((fm) => (
                    <tr key={fm.factor_name}>
                      <td className="py-1.5 text-left font-bold text-accent-cyan">{fm.factor_name}</td>
                      <td className="py-1.5 font-bold">
                        <span className={`px-2 py-0.5 rounded text-[10px] ${fm.monotonicity_grade === 'MONOTONIC' ? 'bg-emerald-950 text-emerald-300' : (fm.monotonicity_grade === 'INVERSE' ? 'bg-rose-950 text-rose-300' : 'bg-amber-950 text-amber-300')}`}>
                          {fm.monotonicity_grade}
                        </span>
                      </td>
                      <td className="py-1.5 font-mono">{fm.spearman_correlation.toFixed(3)}</td>
                      <td className="py-1.5 text-right text-text-muted text-[10px]">{fm.criteria_description}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Score Calibration */}
          <div className="p-4 bg-surface rounded-lg border border-border flex flex-col gap-2">
            <div className="font-bold text-text-primary flex items-center gap-2">
              <Zap className="w-4 h-4 text-accent-gold" />
              <span>Score Calibration: Magnitude vs Forward Return (H=5 Horizon)</span>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-center text-[11px] mt-2">
                <thead>
                  <tr className="border-b border-border/80 text-text-muted">
                    <th className="pb-1 text-left">Score Range Bucket</th>
                    <th className="pb-1">Direction</th>
                    <th className="pb-1">Sample Count</th>
                    <th className="pb-1">H5 Median Return</th>
                    <th className="pb-1">Positive Rate</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/40">
                  {report.score_calibration.map((sc) => (
                    <tr key={sc.score_bucket}>
                      <td className="py-1.5 text-left font-bold">{sc.score_bucket}</td>
                      <td className={`py-1.5 font-bold ${sc.direction === 'LONG' ? 'text-emerald-400' : 'text-rose-400'}`}>
                        {sc.direction}
                      </td>
                      <td className="py-1.5 font-mono">{sc.signal_count.toLocaleString()}</td>
                      <td className={`py-1.5 font-bold ${sc.h5_median_return >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                        {(sc.h5_median_return * 100).toFixed(3)}%
                      </td>
                      <td className="py-1.5 font-mono">{sc.h5_positive_rate.toFixed(1)}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* 4. Partitions & Quarterly Stability Sub-Tab */}
      {subTab === 'partitions' && (
        <div className="flex flex-col gap-4">
          <div className="p-4 bg-surface rounded-lg border border-border flex flex-col gap-2">
            <div className="font-bold text-text-primary flex items-center gap-2">
              <Layers className="w-4 h-4 text-purple-400" />
              <span>Out-of-Sample Partition Performance (Train / Validation / Test)</span>
            </div>
            <table className="w-full text-center text-[11px] mt-2">
              <thead>
                <tr className="border-b border-border/80 text-text-muted">
                  <th className="pb-1 text-left">Partition</th>
                  <th className="pb-1">Period</th>
                  <th className="pb-1">Signals</th>
                  <th className="pb-1">H5 Median Return</th>
                  <th className="pb-1">Positive Rate</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/40">
                {report.partitions.map((p) => (
                  <tr key={p.partition_name}>
                    <td className="py-1.5 text-left font-bold text-text-primary">{p.partition_name}</td>
                    <td className="py-1.5 text-text-muted">{p.start_date} → {p.end_date}</td>
                    <td className="py-1.5 font-mono">{p.signal_count.toLocaleString()}</td>
                    <td className="py-1.5 font-bold text-rose-400">{(p.h5_median_return * 100).toFixed(3)}%</td>
                    <td className="py-1.5 font-mono">{p.h5_positive_rate.toFixed(1)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="p-4 bg-surface rounded-lg border border-border flex flex-col gap-2">
            <div className="font-bold text-text-primary flex items-center gap-2">
              <Activity className="w-4 h-4 text-emerald-400" />
              <span>Quarterly Stability Analysis (2024-Q1 → 2025-Q4)</span>
            </div>
            <table className="w-full text-center text-[11px] mt-2">
              <thead>
                <tr className="border-b border-border/80 text-text-muted">
                  <th className="pb-1 text-left">Quarter</th>
                  <th className="pb-1">Signal Count</th>
                  <th className="pb-1">Long / Short</th>
                  <th className="pb-1">H5 Median Return</th>
                  <th className="pb-1">Positive Rate</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/40">
                {report.quarterly.map((q) => (
                  <tr key={q.partition_name}>
                    <td className="py-1.5 text-left font-bold">{q.partition_name}</td>
                    <td className="py-1.5 font-mono">{q.signal_count.toLocaleString()}</td>
                    <td className="py-1.5 font-mono">{q.long_count} / {q.short_count}</td>
                    <td className="py-1.5 font-bold text-rose-400">{(q.h5_median_return * 100).toFixed(3)}%</td>
                    <td className="py-1.5 font-mono">{q.h5_positive_rate.toFixed(1)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
