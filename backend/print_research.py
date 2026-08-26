import json

with open("data/research/experiment_registry.json") as f:
    d = json.load(f)

print("=========================================================================================")
print("PHASE 8 — STRATEGY RESEARCH BATTERY DETAILED SUMMARY")
print("=========================================================================================")
for exp_id, exp in d.items():
    print(f"\n[{exp_id}] {exp['experiment_name']}")
    print(f"Status: {exp['status']} | Gates Passed: {exp['gates_passed_count']}/{exp['total_gates_count']}")
    
    vm = exp['validation_metrics']
    tm = exp.get('test_metrics')
    
    print(f"  VALIDATION (2025 H1): N={vm['signal_count']:,} | 5C Med: {vm['h5_median']*100:+.3f}% | 10C Med: {vm['h10_median']*100:+.3f}% | Pos: {vm['positive_rate_5c']:.1f}% | Pre-5C: {vm['timing']['pre_5_median']*100:+.3f}% | Adjacent: {vm['clustering']['adjacent_signal_rate']:.1f}% | Mono: {vm['score_monotonicity_grade']}")
    
    if tm:
        print(f"  FINAL TEST (2025 H2): N={tm['signal_count']:,} | 5C Med: {tm['h5_median']*100:+.3f}% | 10C Med: {tm['h10_median']*100:+.3f}% | Pos: {tm['positive_rate_5c']:.1f}% | Pre-5C: {tm['timing']['pre_5_median']*100:+.3f}% | Adjacent: {tm['clustering']['adjacent_signal_rate']:.1f}% | Mono: {tm['score_monotonicity_grade']}")
    
    print(f"  Decision Rationale: {exp['decision_rationale']}")
