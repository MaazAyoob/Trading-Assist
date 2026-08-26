import json

with open("data/runs/run_BTCUSDT_15m_1787588425_af330e.json") as f:
    data = json.load(f)

m = data["metrics"]
meta = data["dataset_metadata"]

print("=" * 80)
print("              PHASE 6.1 — HISTORICAL 2-YEAR VALIDATION REPORT")
print("=" * 80)
print("Run ID:             ", data["run_id"])
print("Symbol / Timeframe: ", data["symbol"], data["timeframe"])
print("Dataset ID:         ", meta["dataset_id"])
print("Dataset Version:    ", meta.get("dataset_version", "v1.0"))
print("SHA-256 Hash:       ", meta["sha256_hash"])
print(f"Candle Count:        {m['total_candles']:,} candles (2 Years)")
print(f"Execution Time:      {data['runtime_seconds']}s ({data['candles_per_second']} candles/s)")
print("Start Timestamp:    ", meta["start_timestamp"])
print("End Timestamp:      ", meta["end_timestamp"])
print(f"Gaps / Duplicates:   {meta.get('gap_count', 0)} gaps, {meta.get('duplicate_count', 0)} duplicates, {meta.get('invalid_count', 0)} invalid")
print("Quality Status:     ", meta.get("quality_status", "HEALTHY"))
print()
print("-" * 80)
print("1. SIGNAL DISTRIBUTION")
print("-" * 80)
tot = m["total_signals"]
long_cnt = m["long_signals"]
short_cnt = m["short_signals"]
wait_cnt = m.get("wait_signals", 0)
neutral_cnt = m.get("neutral_signals", 0)
print(f"Total Valid Signals: {tot:,} ({m['signals_per_day']} / day, {m['signals_per_week']} / week)")
print(f"  LONG Signals:      {long_cnt:,} ({long_cnt/tot*100:.1f}%)")
print(f"  SHORT Signals:     {short_cnt:,} ({short_cnt/tot*100:.1f}%)")
print(f"  WAIT Signals:      {wait_cnt:,}")
print(f"  NEUTRAL Signals:   {neutral_cnt:,}")
print()
print("-" * 80)
print("2. FORWARD RETURN DISTRIBUTIONS (Across Horizons: 1, 3, 5, 10, 20 Candles)")
print("-" * 80)
print(f"{'Horizon':<10} | {'Long Median':<12} | {'Short Median':<12} | {'Combined Median':<16} | {'Long Pos%':<10} | {'Short Pos%':<10}")
print("-" * 80)
for h in ["1", "3", "5", "10", "20"]:
    if h in m["horizon_metrics"]:
        hm = m["horizon_metrics"][h]
        lhm = m["long_horizon_metrics"].get(h, {})
        shm = m["short_horizon_metrics"].get(h, {})
        l_med = lhm.get("forward_return_stats", {}).get("median", 0) * 100
        s_med = shm.get("forward_return_stats", {}).get("median", 0) * 100
        c_med = hm.get("forward_return_stats", {}).get("median", 0) * 100
        l_pos = lhm.get("positive_ratio", 0) * 100
        s_pos = shm.get("positive_ratio", 0) * 100
        print(f"{h+' bars':<10} | {l_med:>+10.3f}% | {s_med:>+10.3f}% | {c_med:>+14.3f}% | {l_pos:>9.1f}% | {s_pos:>9.1f}%")

print()
print("-" * 80)
print("3. MAXIMUM FAVORABLE / ADVERSE EXCURSION (MFE / MAE)")
print("-" * 80)
print(f"{'Horizon':<10} | {'Long MFE':<12} | {'Long MAE':<12} | {'Short MFE':<12} | {'Short MAE':<12}")
print("-" * 80)
for h in ["1", "3", "5", "10", "20"]:
    if h in m["horizon_metrics"]:
        lhm = m["long_horizon_metrics"].get(h, {})
        shm = m["short_horizon_metrics"].get(h, {})
        l_mfe = lhm.get("mfe_stats", {}).get("median", 0) * 100
        l_mae = lhm.get("mae_stats", {}).get("median", 0) * 100
        s_mfe = shm.get("mfe_stats", {}).get("median", 0) * 100
        s_mae = shm.get("mae_stats", {}).get("median", 0) * 100
        print(f"{h+' bars':<10} | {l_mfe:>10.3f}% | {l_mae:>10.3f}% | {s_mfe:>11.3f}% | {s_mae:>11.3f}%")

print()
print("-" * 80)
print("4. MOVING BLOCK BOOTSTRAP CONFIDENCE INTERVALS (95% CI)")
print("-" * 80)
for h in ["1", "3", "5", "10", "20"]:
    if h in m["horizon_metrics"]:
        st = m["horizon_metrics"][h]["forward_return_stats"]
        mean = st.get("mean", 0) * 100
        norm_lo = (st.get("ci_lower_normal") or 0) * 100
        norm_hi = (st.get("ci_upper_normal") or 0) * 100
        b_lo = (st.get("block_bootstrap_mean_ci_lower") or 0) * 100
        b_hi = (st.get("block_bootstrap_mean_ci_upper") or 0) * 100
        print(f"H={h:<2} bars (n={st['sample_count']:,}): Mean={mean:>+.4f}% | Normal CI=[{norm_lo:>+.3f}%, {norm_hi:>+.3f}%] | Block Bootstrap CI=[{b_lo:>+.3f}%, {b_hi:>+.3f}%] | {st.get('sample_warning','VALID')}")

print()
print("-" * 80)
print("5. SUBPERIOD (QUARTERLY) STABILITY")
print("-" * 80)
for k, sp in sorted(m.get("subperiod_breakdown", {}).items()):
    h5_med = sp["horizon_metrics"].get("5", {}).get("forward_return_stats", {}).get("median", 0) * 100
    pos_r = sp["horizon_metrics"].get("5", {}).get("positive_ratio", 0) * 100
    print(f"  {k}: {sp['sample_count']:>5} signals | H5 Median Return: {h5_med:>+6.3f}% | Positive Rate: {pos_r:>5.1f}%")

print()
print("-" * 80)
print("6. SCORE RANGE BREAKDOWN (H5 Horizon)")
print("-" * 80)
for k, sc in sorted(m.get("score_breakdown", {}).items()):
    h5_med = sc["horizon_metrics"].get("5", {}).get("forward_return_stats", {}).get("median", 0) * 100
    pos_r = sc["horizon_metrics"].get("5", {}).get("positive_ratio", 0) * 100
    print(f"  Score [{k}]: {sc['sample_count']:>5} signals | H5 Median: {h5_med:>+6.3f}% | Positive Rate: {pos_r:>5.1f}%")

print()
print("-" * 80)
print("7. REGIME BREAKDOWN (H5 Horizon)")
print("-" * 80)
for k, rg in sorted(m.get("regime_breakdown", {}).items()):
    h5_med = rg["horizon_metrics"].get("5", {}).get("forward_return_stats", {}).get("median", 0) * 100
    pos_r = rg["horizon_metrics"].get("5", {}).get("positive_ratio", 0) * 100
    print(f"  Regime {k:<18}: {rg['sample_count']:>5} signals | H5 Median: {h5_med:>+6.3f}% | Positive Rate: {pos_r:>5.1f}%")
