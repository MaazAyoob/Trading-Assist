"""
Fetch Phase 13D Diagnostics from local backend API.
"""
import json
import urllib.request
import time

url = "http://127.0.0.1:8000/api/v1/scalp-v2/diagnostics?symbol=BTCUSDT&limit=1000"
print(f"Requesting {url}...")
t0 = time.time()
try:
    with urllib.request.urlopen(url, timeout=30) as resp:
        t1 = time.time()
        data = json.loads(resp.read().decode())
        print(f"Response status: {resp.status} in {t1 - t0:.2f}s")
        print(json.dumps(data, indent=2))
except Exception as e:
    print(f"Error fetching diagnostics: {e}")
