"""Chart one backtest trade: 5m candles, 1H POI, 5m FVG, entry, stop, target."""
import json, os, sys
from datetime import datetime, timezone
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import smc_bt

trades_file, idx, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
t = json.load(open(trades_file))[idx]
m1 = smc_bt.load_1m(t["sym"])
T, O, H, L, C, _ = smc_bt.resample(m1, 300)
start = min(t["poi_t"], t["signal_t"] - 6 * 3600)
end = max(t["exit_t"], t["entry_t"]) + 2 * 3600
if end - start > 4 * 86400:
    start = t["signal_t"] - 2 * 86400
idx_range = [i for i in range(len(T)) if start <= T[i] <= end]
fig, ax = plt.subplots(figsize=(14, 6.5))
x0 = idx_range[0]
for i in idx_range:
    col = "#26a69a" if C[i] >= O[i] else "#ef5350"
    ax.vlines(i - x0, L[i], H[i], color=col, lw=0.6)
    ax.add_patch(Rectangle((i - x0 - 0.35, min(O[i], C[i])), 0.7, abs(C[i] - O[i]) or 1e-9, color=col))
pos = lambda ts: next((i - x0 for i in idx_range if T[i] >= ts), len(idx_range))
xe, xx, xs, xp = pos(t["entry_t"]), pos(t["exit_t"]), pos(t["signal_t"]), pos(t["poi_t"])
ax.axhspan(*t["poi_zone"], color="#5c6bc0", alpha=0.15, label="1H POI (%s)" % t["poi_kind"])
xf = pos(t["fvg_t"])
ax.add_patch(Rectangle((xf, t["fvg"][0]), (xx - xf) + 5, t["fvg"][1] - t["fvg"][0],
                       color="#ffa726", alpha=0.35, label="5m FVG"))
ax.hlines(t["entry"], xe, xx, color="black", lw=1.2, label="entry %.5g" % t["entry"])
ax.hlines(t["stop"], xe, xx, color="#d32f2f", lw=1.2, ls="--", label="stop %.5g" % t["stop"])
ax.hlines(t["target"], xe, xx, color="#2e7d32", lw=1.2, ls="--", label="target %.5g" % t["target"])
ax.axvline(xp, color="#5c6bc0", lw=0.8, ls=":")
ax.axvline(xs, color="#ffa726", lw=0.8, ls=":")
ticks = list(range(0, len(idx_range), max(1, len(idx_range) // 10)))
ax.set_xticks(ticks)
ax.set_xticklabels([datetime.fromtimestamp(T[x0 + k], timezone.utc).strftime("%m-%d %H:%M") for k in ticks],
                   fontsize=8)
ax.set_title("%s %s  %s UTC  -> %s, %+.2fR (planned %.1fR)" % (
    t["sym"], t["dir"], datetime.fromtimestamp(t["entry_t"], timezone.utc).strftime("%Y-%m-%d %H:%M"),
    t["how"], t["r"], t["rr_planned"]))
ax.legend(loc="best", fontsize=8)
ax.grid(alpha=0.2)
fig.tight_layout()
fig.savefig(out, dpi=110)
print(out)
