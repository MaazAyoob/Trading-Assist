import json

with open("data/runs/forensics_report_BTCUSDT_15m.json") as f:
    d = json.load(f)

print("=== PHASE 7 FORENSICS SUMMARY ===")
print("Symbol:", d["symbol"], d["timeframe"])
print("Dataset Hash:", d["dataset_sha256"])
print("Candles:", d["candle_count"], "Signals:", d["total_signals"], "Long:", d["long_signals"], "Short:", d["short_signals"])
print("\n--- TIMING (LONG) ---")
for h in [1, 3, 5, 10, 20]:
    pre = d["timing_long"]["pre_signal_median_returns"][str(h)] * 100
    post = d["timing_long"]["post_signal_median_returns"][str(h)] * 100
    print(f"{h}C: Pre = {pre:+.3f}%, Post = {post:+.3f}%")
print("Diagnostic:", d["timing_long"]["trend_chasing_diagnostic"])

print("\n--- TIMING (SHORT) ---")
for h in [1, 3, 5, 10, 20]:
    pre = d["timing_short"]["pre_signal_median_returns"][str(h)] * 100
    post = d["timing_short"]["post_signal_median_returns"][str(h)] * 100
    print(f"{h}C: Pre = {pre:+.3f}%, Post = {post:+.3f}%")
print("Diagnostic:", d["timing_short"]["trend_chasing_diagnostic"])

print("\n--- CLUSTERING ---")
print("Within 1 bar:", d["clustering"]["pct_within_1_candle"], "%")
print("Within 4 bars:", d["clustering"]["pct_within_4_candles"], "%")
print("Avg Long Run Length:", d["clustering"]["long_run_lengths_avg"], "bars")
print("Avg Short Run Length:", d["clustering"]["short_run_lengths_avg"], "bars")
print("Effective Independent Episodes:", d["clustering"]["effective_sample_size_estimate"])

print("\n--- SCORE CALIBRATION (H5) ---")
for b in d["score_calibration"]:
    print(f"{b['score_bucket']:<15} | Dir: {b['direction']:<5} | N: {b['signal_count']:<5} | H5 Med: {b['h5_median_return']*100:+.3f}% | Pos: {b['h5_positive_rate']:.1f}%")
print("Monotonicity Grade:", d["score_monotonicity_grade"])

print("\n--- FACTOR MONOTONICITY (H5) ---")
for fm in d["factor_monotonicity"]:
    if fm["horizon"] == 5:
        print(f"{fm['factor_name']:<12} | Grade: {fm['monotonicity_grade']:<16} | Corr: {fm['spearman_correlation']:+.3f}")

print("\n--- PARTITIONS ---")
for p in d["partitions"]:
    print(f"{p['partition_name']:<25} | N: {p['signal_count']:<5} | H5 Med: {p['h5_median_return']*100:+.3f}% | Pos: {p['h5_positive_rate']:.1f}%")

print("\n--- QUARTERLY ---")
for q in d["quarterly"]:
    print(f"{q['partition_name']:<10} | N: {q['signal_count']:<5} | Long/Short: {q['long_count']}/{q['short_count']} | H5 Med: {q['h5_median_return']*100:+.3f}% | Pos: {q['h5_positive_rate']:.1f}%")
