import React, { useState } from 'react';
import {
  Shield,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  MinusCircle,
  ChevronDown,
  ChevronRight,
  TrendingUp,
  Target,
  ShieldAlert,
  Layers,
  HelpCircle,
  Info,
} from 'lucide-react';
import { useMarketStore, formatSymbolPrice } from '../../stores/marketStore';

export const TradeDecisionDetails: React.FC = () => {
  const { symbol, confirmedTradeDecision, realtimeTradeDecision, multiStrategyDecisions, selectedStrategyId, setSelectedStrategyId } = useMarketStore();
  const [activeTab, setActiveTab] = useState<'audit' | 'invalidation' | 'targets' | 'candidates'>('audit');

  const decision = confirmedTradeDecision || realtimeTradeDecision;
  if (!decision) return null;

  const isNoTrade = decision.decision === 'NO_TRADE';
  const formatPrice = (val: number | null | undefined) => formatSymbolPrice(symbol, val);

  const auditItems = [
    { name: '1. Data Quality Check', data: decision.audit_trace.data_quality_check },
    { name: '2. Research Signal Status', data: decision.audit_trace.signal_check },
    { name: '3. Strategy Context Filter', data: decision.audit_trace.strategy_filter_check },
    { name: '4. Regime Compatibility', data: decision.audit_trace.regime_check },
    { name: '5. Market Structure Direction', data: decision.audit_trace.structure_check },
    { name: '6. Support/Resistance Clearance', data: decision.audit_trace.sr_clearance_check },
    { name: '7. Analytical Entry Plan', data: decision.audit_trace.entry_check },
    { name: '8. Structural Stop Loss Plan', data: decision.audit_trace.stop_check },
    { name: '9. Take Profit Multipliers', data: decision.audit_trace.target_check },
    { name: '10. Risk/Reward Threshold Filter', data: decision.audit_trace.risk_reward_check },
    { name: '11. Decision Alignment Confidence', data: decision.audit_trace.confidence_check },
    { name: 'Final Analytical Decision', data: decision.audit_trace.final_decision },
  ];

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 sm:p-5 mb-4 shadow-xl font-mono">
      {/* Navigation Tabs */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-3 mb-4">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setActiveTab('audit')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors ${
              activeTab === 'audit'
                ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
            }`}
          >
            <Shield className="w-3.5 h-3.5" />
            Decision Audit Trace ({auditItems.filter(i => i.data?.status === 'PASS').length}/12 PASS)
          </button>

          <button
            onClick={() => setActiveTab('targets')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors ${
              activeTab === 'targets'
                ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
            }`}
          >
            <Target className="w-3.5 h-3.5" />
            Targets & Risk Detail
          </button>

          <button
            onClick={() => setActiveTab('invalidation')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors ${
              activeTab === 'invalidation'
                ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
            }`}
          >
            <ShieldAlert className="w-3.5 h-3.5" />
            Invalidation Triggers ({decision.invalidation_conditions.length})
          </button>

          <button
            onClick={() => setActiveTab('candidates')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors ${
              activeTab === 'candidates'
                ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            Multi-Strategy Contexts
          </button>
        </div>

        <div className="text-xs text-slate-500 font-mono">
          Engine: v{decision.decision_engine_version} | Hash: {decision.strategy_config_hash}
        </div>
      </div>

      {/* Tab 1: Audit Trace Table & Diagnostic Summary */}
      {activeTab === 'audit' && (
        <div className="space-y-4">
          {/* Primary Reason Diagnostic Card */}
          {isNoTrade && (
            <div className="p-3.5 bg-amber-950/20 border border-amber-500/30 rounded-xl flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-amber-500/20 flex items-center justify-center text-amber-400">
                  <AlertTriangle className="w-4 h-4" />
                </div>
                <div>
                  <div className="text-[10px] text-amber-400/80 uppercase font-bold tracking-wider">
                    NO_TRADE Primary Diagnostic Reason
                  </div>
                  <div className="text-xs text-amber-200 font-bold mt-0.5">
                    {decision.reasons_for_no_trade[0] || 'Research signal is NEUTRAL.'}
                  </div>
                </div>
              </div>
              <span className="text-[10px] text-slate-400 px-2 py-0.5 rounded bg-slate-900 border border-slate-800">
                Directional Pipeline Paused
              </span>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Supporting Factors */}
            <div className="p-3.5 bg-slate-950/60 rounded-xl border border-slate-800">
              <h4 className="text-xs font-bold uppercase tracking-wider text-emerald-400 flex items-center gap-1.5 mb-2.5">
                <CheckCircle2 className="w-4 h-4" />
                Supporting Analytical Factors
              </h4>
              {decision.supporting_factors.length > 0 ? (
                <ul className="space-y-1.5 text-xs text-slate-300">
                  {decision.supporting_factors.map((f, idx) => (
                    <li key={idx} className="flex items-start gap-2">
                      <span className="text-emerald-500 font-bold">•</span>
                      <span>{f}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <div className="text-xs text-slate-500 italic">No strong directional supporting factors established.</div>
              )}
            </div>

            {/* Conflicting / Rejection Factors */}
            <div className="p-3.5 bg-slate-950/60 rounded-xl border border-slate-800">
              <h4 className="text-xs font-bold uppercase tracking-wider text-amber-400 flex items-center gap-1.5 mb-2.5">
                <AlertTriangle className="w-4 h-4" />
                Conflicting & Deductive Factors
              </h4>
              {decision.reasons_for_no_trade.length > 0 || decision.conflicting_factors.length > 0 ? (
                <ul className="space-y-1.5 text-xs text-slate-300">
                  {decision.reasons_for_no_trade.map((r, idx) => (
                    <li key={`rej-${idx}`} className="flex items-start gap-2 text-rose-300">
                      <span className="text-rose-400 font-bold">•</span>
                      <span>{r}</span>
                    </li>
                  ))}
                  {decision.conflicting_factors.map((f, idx) => (
                    <li key={`conf-${idx}`} className="flex items-start gap-2">
                      <span className="text-amber-400 font-bold">•</span>
                      <span>{f}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <div className="text-xs text-slate-500 italic">Zero analytical conflicts detected across components.</div>
              )}
            </div>
          </div>

          {/* 11-Step Hierarchical Table */}
          <div className="overflow-x-auto rounded-xl border border-slate-800">
            <table className="w-full text-left text-xs border-collapse">
              <thead className="bg-slate-950 text-slate-400 font-semibold border-b border-slate-800 uppercase tracking-wider">
                <tr>
                  <th className="p-2.5 px-3">Hierarchical Step</th>
                  <th className="p-2.5 px-3">Evaluation Status</th>
                  <th className="p-2.5 px-3">Diagnostic Reason & Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 bg-slate-900/40">
                {auditItems.map((item, idx) => {
                  const status = item.data?.status || 'NOT_APPLICABLE';
                  const isPass = status === 'PASS';
                  const isFail = status === 'FAIL';

                  return (
                    <tr key={idx} className="hover:bg-slate-800/30 transition-colors">
                      <td className="p-2.5 px-3 font-semibold text-slate-200 whitespace-nowrap">
                        {item.name}
                      </td>
                      <td className="p-2.5 px-3 whitespace-nowrap">
                        <span
                          className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-bold ${
                            isPass
                              ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                              : isFail
                              ? 'bg-rose-500/15 text-rose-400 border border-rose-500/30'
                              : 'bg-slate-800 text-slate-400 border border-slate-700'
                          }`}
                        >
                          {isPass ? (
                            <CheckCircle2 className="w-3 h-3" />
                          ) : isFail ? (
                            <XCircle className="w-3 h-3" />
                          ) : (
                            <MinusCircle className="w-3 h-3" />
                          )}
                          {status}
                        </span>
                      </td>
                      <td className="p-2.5 px-3 text-slate-300 font-mono text-[11px]">
                        {item.data?.reason || '—'}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 2: Targets & Risk Detail */}
      {activeTab === 'targets' && (
        <div className="space-y-4">
          {isNoTrade ? (
            <div className="p-8 text-center bg-slate-950/40 rounded-xl border border-slate-800 text-slate-400">
              <MinusCircle className="w-8 h-8 mx-auto text-amber-400 mb-2" />
              <div className="text-sm font-bold text-slate-200">No Directional Trade Plan Active</div>
              <div className="text-xs text-slate-500 mt-1">
                Stop loss and take profit targets are not calculated for NO_TRADE decisions.
              </div>
            </div>
          ) : (
            <>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* TP1 Detail */}
                <div className="p-4 bg-slate-950/60 rounded-xl border border-slate-800">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-bold text-slate-400 uppercase">Take Profit 1 (TP1)</span>
                    <span className="text-xs font-bold font-mono px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800">
                      {decision.take_profits ? `${decision.take_profits.tp1.actual_rr_after_adjustment.toFixed(2)}R` : 'N/A'}
                    </span>
                  </div>
                  <div className="text-2xl font-black font-mono text-emerald-400 mb-2">
                    ${formatPrice(decision.take_profits?.tp1.adjusted_target)}
                  </div>
                  <div className="text-xs text-slate-400 space-y-1 pt-2 border-t border-slate-800 font-mono">
                    <div className="flex justify-between">
                      <span>Canonical Base:</span>
                      <span>{decision.take_profits?.tp1.r_multiple_base.toFixed(2)}R</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Structural Level:</span>
                      <span>{decision.take_profits?.tp1.structural_level ? `$${formatPrice(decision.take_profits.tp1.structural_level)}` : 'None'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Adjustment:</span>
                      <span className={decision.take_profits?.tp1.constrained_by_structure ? 'text-amber-400' : 'text-slate-400'}>
                        {decision.take_profits?.tp1.adjustment_reason || 'Canonical'}
                      </span>
                    </div>
                  </div>
                </div>

                {/* TP2 Detail */}
                <div className="p-4 bg-slate-950/60 rounded-xl border border-slate-800">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-bold text-slate-400 uppercase">Take Profit 2 (TP2)</span>
                    <span className="text-xs font-bold font-mono px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800">
                      {decision.take_profits ? `${decision.take_profits.tp2.actual_rr_after_adjustment.toFixed(2)}R` : 'N/A'}
                    </span>
                  </div>
                  <div className="text-2xl font-black font-mono text-emerald-400 mb-2">
                    ${formatPrice(decision.take_profits?.tp2.adjusted_target)}
                  </div>
                  <div className="text-xs text-slate-400 space-y-1 pt-2 border-t border-slate-800 font-mono">
                    <div className="flex justify-between">
                      <span>Canonical Base:</span>
                      <span>{decision.take_profits?.tp2.r_multiple_base.toFixed(2)}R</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Structural Level:</span>
                      <span>{decision.take_profits?.tp2.structural_level ? `$${formatPrice(decision.take_profits.tp2.structural_level)}` : 'None'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Adjustment:</span>
                      <span className={decision.take_profits?.tp2.constrained_by_structure ? 'text-amber-400' : 'text-slate-400'}>
                        {decision.take_profits?.tp2.adjustment_reason || 'Canonical'}
                      </span>
                    </div>
                  </div>
                </div>

                {/* TP3 Detail */}
                <div className="p-4 bg-slate-950/60 rounded-xl border border-slate-800">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-bold text-slate-400 uppercase">Take Profit 3 (TP3)</span>
                    <span className="text-xs font-bold font-mono px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800">
                      {decision.take_profits ? `${decision.take_profits.tp3.actual_rr_after_adjustment.toFixed(2)}R` : 'N/A'}
                    </span>
                  </div>
                  <div className="text-2xl font-black font-mono text-emerald-400 mb-2">
                    ${formatPrice(decision.take_profits?.tp3.adjusted_target)}
                  </div>
                  <div className="text-xs text-slate-400 space-y-1 pt-2 border-t border-slate-800 font-mono">
                    <div className="flex justify-between">
                      <span>Canonical Base:</span>
                      <span>{decision.take_profits?.tp3.r_multiple_base.toFixed(2)}R</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Structural Level:</span>
                      <span>{decision.take_profits?.tp3.structural_level ? `$${formatPrice(decision.take_profits.tp3.structural_level)}` : 'None'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Adjustment:</span>
                      <span className={decision.take_profits?.tp3.constrained_by_structure ? 'text-amber-400' : 'text-slate-400'}>
                        {decision.take_profits?.tp3.adjustment_reason || 'Canonical'}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* R:R Invariant Summary Card */}
              <div className="p-3.5 bg-slate-950/60 rounded-xl border border-slate-800 text-xs text-slate-400 flex flex-wrap items-center justify-between gap-3">
                <div className="flex items-center gap-2">
                  <Info className="w-4 h-4 text-indigo-400" />
                  <span>
                    <strong>Mathematical Invariant:</strong> Planned risk = <code className="text-slate-200">${decision.stop_loss ? formatPrice(decision.stop_loss.distance) : '0'}</code>. Actual R:R is recalculated post structural adjustment (<code className="text-slate-200">actual_rr = abs(target - entry) / risk</code>).
                  </span>
                </div>
                <div className="text-slate-300 font-mono">
                  Minimum Acceptance: TP1 &ge; 1.20R | TP2 &ge; 1.50R | TP3 &ge; 2.00R
                </div>
              </div>
            </>
          )}
        </div>
      )}

      {/* Tab 3: Invalidation Triggers */}
      {activeTab === 'invalidation' && (
        <div className="space-y-3">
          <div className="p-3.5 bg-slate-950/60 rounded-xl border border-slate-800">
            <h4 className="text-xs font-bold uppercase tracking-wider text-rose-400 flex items-center gap-1.5 mb-2.5">
              <ShieldAlert className="w-4 h-4" />
              Active Plan Invalidation Criteria
            </h4>
            <div className="space-y-2">
              {decision.invalidation_conditions.map((cond, idx) => (
                <div key={idx} className="flex items-start gap-2.5 text-xs text-slate-300 bg-slate-900/60 p-2.5 rounded-lg border border-slate-800/80">
                  <span className="text-rose-400 font-bold font-mono">#{idx + 1}</span>
                  <span>{cond}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Tab 4: Multi-Strategy Context Comparisons */}
      {activeTab === 'candidates' && (
        <div className="space-y-3">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {multiStrategyDecisions?.candidate_decisions &&
              Object.entries(multiStrategyDecisions.candidate_decisions).map(([stratId, candPlan]) => {
                const isSelected = selectedStrategyId === stratId;
                const isCandBuy = candPlan.decision === 'BUY';
                const isCandSell = candPlan.decision === 'SELL';

                return (
                  <div
                    key={stratId}
                    onClick={() => setSelectedStrategyId(stratId)}
                    className={`p-3.5 rounded-xl border cursor-pointer transition-all ${
                      isSelected
                        ? 'bg-indigo-950/40 border-indigo-500/60 shadow-lg shadow-indigo-600/20'
                        : 'bg-slate-950/60 border-slate-800 hover:border-slate-700'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-bold text-slate-300 truncate">{stratId}</span>
                      <span
                        className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase ${
                          isCandBuy
                            ? 'bg-emerald-500/20 text-emerald-400'
                            : isCandSell
                            ? 'bg-rose-500/20 text-rose-400'
                            : 'bg-slate-800 text-slate-400'
                        }`}
                      >
                        {candPlan.decision}
                      </span>
                    </div>

                    <div className="text-xs text-slate-400 space-y-1 font-mono">
                      <div className="flex justify-between">
                        <span>Alignment Score:</span>
                        <span className="text-slate-200 font-bold">{candPlan.decision_alignment_score.toFixed(1)}/100</span>
                      </div>
                      <div className="flex justify-between">
                        <span>State:</span>
                        <span className="text-slate-300">{candPlan.state}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Entry Ref:</span>
                        <span>{candPlan.entry ? `$${formatPrice(candPlan.entry.planned_entry_price)}` : 'N/A'}</span>
                      </div>
                    </div>
                  </div>
                );
              })}
          </div>
        </div>
      )}
    </div>
  );
};
