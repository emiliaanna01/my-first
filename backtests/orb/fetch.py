"""Fetch data for the ORB backtest.

1. Daily spark (3 months) for the whole universe -> pick liquid stocks priced $10-75
   (price = median close over the window, so the pick is not just today's price).
2. 60 days of 5-minute v8 bars for the picks + SPY, cached as JSON.
"""
import gzip, importlib.util, json, os, statistics, sys, time

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
SCAN = os.path.join(ROOT, ".claude/skills/trader-scanner/scan.py")
OUT = os.path.dirname(os.path.abspath(__file__)) + "/data"
spec = importlib.util.spec_from_file_location("scan", SCAN)
scan = importlib.util.module_from_spec(spec); spec.loader.exec_module(scan)

N_PICK = int(sys.argv[1]) if len(sys.argv) > 1 else 300
os.makedirs(OUT, exist_ok=True)

syms = [l.split("|")[0] for l in open(os.path.join(ROOT, "trader/universe.txt")) if l.strip()]
daily = {}
for i in range(0, len(syms), 20):
    chunk = syms[i:i + 20]
    try:
        daily.update(scan.parse_spark(scan.yahoo_get(scan.spark_path(chunk, "3mo", "1d")),
                                      {scan.to_yahoo(s): s for s in chunk}))
    except scan.ScanError as e:
        print("spark fail", chunk[0], e, file=sys.stderr)
    time.sleep(0.3)
    if i % 1000 == 0:
        print("spark", i, len(syms), file=sys.stderr)

rows = []
for s, ser in daily.items():
    c = [x for x in ser["c"] if x]
    if len(c) < 40:
        continue
    med = statistics.median(c)
    # spark daily has no volume column; today's volume from meta ranks liquidity
    vol = ser["meta"].get("regularMarketVolume") or 0
    if 10 <= med <= 75:
        rows.append((med * vol, s, med, vol))
print("priced $10-75 with data:", len(rows), file=sys.stderr)
rows.sort(reverse=True)
picks = [r[1] for r in rows[:N_PICK]]
json.dump({"picks": [{"symbol": r[1], "median_close": r[2], "median_volume": r[3]} for r in rows[:N_PICK]]},
          open(OUT + "/picks.json", "w"), indent=1)

for k, s in enumerate(["SPY"] + picks):
    p = "%s/%s.json.gz" % (OUT, s)
    if os.path.exists(p):
        continue
    try:
        txt = scan.yahoo_get(scan.chart_path(s, "60d", "5m"))
        scan.parse_chart(txt, s)
        with gzip.open(p, "wt") as fh:
            fh.write(txt)
    except scan.ScanError as e:
        print("chart fail", s, e, file=sys.stderr)
    time.sleep(0.4)
    if k % 50 == 0:
        print("chart", k, len(picks) + 1, file=sys.stderr)
print("done", file=sys.stderr)
