"""Backtest of the 15-minute ORB strategy on cached 60-day 5-minute Yahoo bars.

Rules (long only):
  opening range = 9:30, 9:35, 9:40 bars; trigger = FIRST 5-min bar closing above the range high;
  it must close 9:50-10:30 (slots 3-11). Entry = trigger close. Stop = range midpoint (rounded down).
  Target = entry + R x risk. Bar by bar: stop checked first (a gap below fills at the open), then
  target. Flat at the 15:50 bar's close (15:55). Size = min($20 / risk, $750 / entry), whole shares.
Filters: price $10-75, range width 0.5-2 %, trigger-bar volume >= range-bar average, SPY above its
  own range high at the trigger bar.
Costs: $0.01 a share on the entry and on any exit that is not the target limit.
"""
import gzip, json, math, os, statistics, sys
from collections import defaultdict
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

NY = ZoneInfo("America/New_York")
D = os.path.dirname(os.path.abspath(__file__)) + "/data"
SKIP_DAYS = {"2026-10-23"}          # today: session not finished
FLAT_SLOT = 76                       # 15:50 bar, closes 15:55
RISK_USD, CAP_USD, COST = 20.0, 750.0, 0.01


def load(sym):
    doc = json.load(gzip.open("%s/%s.json.gz" % (D, sym), "rt"))
    r = doc["chart"]["result"][0]
    q = r["indicators"]["quote"][0]
    days = defaultdict(dict)
    for i, ts in enumerate(r.get("timestamp") or []):
        o, h, l, c, v = (q[k][i] for k in ("open", "high", "low", "close", "volume"))
        if None in (o, h, l, c):
            continue
        t = datetime.fromtimestamp(ts, timezone.utc).astimezone(NY)
        m = (t.hour * 60 + t.minute) - 570
        if m < 0 or m % 5 or m >= 390:
            continue
        d = t.date().isoformat()
        if d in SKIP_DAYS:
            continue
        days[d][m // 5] = (o, h, l, c, v or 0)
    return days


def opening_range(bars):
    if not all(k in bars for k in (0, 1, 2)):
        return None
    hi = max(bars[k][1] for k in (0, 1, 2))
    lo = min(bars[k][2] for k in (0, 1, 2))
    return hi, lo, statistics.mean(bars[k][4] for k in (0, 1, 2))


def signal(bars, spy, last_slot=11):
    """First close above the range high. None if it comes after last_slot or never."""
    orr = opening_range(bars)
    if not orr:
        return None
    hi, lo, vavg = orr
    for k in range(3, FLAT_SLOT):
        if k not in bars:
            continue
        if bars[k][3] > hi:
            if k > last_slot:
                return None
            entry = bars[k][3]
            stop = math.floor((hi + lo) / 2 * 100) / 100
            spy_or = opening_range(spy) if spy else None
            spy_ok = bool(spy_or and k in spy and spy[k][3] > spy_or[0])
            return dict(slot=k, entry=entry, stop=stop, or_hi=hi, or_lo=lo,
                        width=(hi - lo) / hi, vol_ok=bars[k][4] >= vavg, spy_ok=spy_ok,
                        dollar_vol=bars[k][4] * entry)
    return None


def simulate(bars, s, R):
    entry, stop = s["entry"], s["stop"]
    risk = entry - stop
    if risk < 0.0005 * entry:
        return None
    target = round(entry + R * risk + 1e-9, 2)
    shares = min(int(RISK_USD // risk), int(CAP_USD // entry))
    if shares < 1:
        return None
    exit_px, how, exit_slot = None, "flat", None
    for j in range(s["slot"] + 1, FLAT_SLOT + 1):
        if j not in bars:
            continue
        o, h, l, c, _ = bars[j]
        if o <= stop:
            exit_px, how = o, "stop"
        elif l <= stop:
            exit_px, how = stop, "stop"
        elif h >= target:
            exit_px, how = target, "target"
        if exit_px is not None:
            exit_slot = j
            break
        last = (c, j)
    if exit_px is None:
        exit_px, exit_slot = last
    cost = COST * shares * (1 if how == "target" else 2)
    pnl = shares * (exit_px - entry) - cost
    return dict(how=how, r=(exit_px - entry) / risk, r_net=pnl / (shares * risk), pnl=pnl,
                shares=shares, exit_slot=exit_slot, risk_usd=shares * risk)


def stats(trades):
    n = len(trades)
    if not n:
        return dict(n=0)
    wins = [t for t in trades if t["pnl"] > 0]
    gross_w = sum(t["pnl"] for t in wins)
    gross_l = -sum(t["pnl"] for t in trades if t["pnl"] <= 0)
    return dict(n=n, win=len(wins) / n, tgt=sum(t["how"] == "target" for t in trades) / n,
                stp=sum(t["how"] == "stop" for t in trades) / n,
                flat=sum(t["how"] == "flat" for t in trades) / n,
                avg_r=statistics.mean(t["r"] for t in trades),
                avg_r_net=statistics.mean(t["r_net"] for t in trades),
                pf=gross_w / gross_l if gross_l else float("inf"),
                avg_pnl=statistics.mean(t["pnl"] for t in trades),
                tot=sum(t["pnl"] for t in trades))


def row(name, st):
    if not st["n"]:
        return "%-44s %5d" % (name, 0)
    return ("%-44s %5d  %5.1f%%  %5.1f%%  %5.1f%%  %5.1f%%  %+6.3f  %+6.3f  %5.2f  %+6.2f" %
            (name, st["n"], 100 * st["win"], 100 * st["tgt"], 100 * st["stp"], 100 * st["flat"],
             st["avg_r"], st["avg_r_net"], st["pf"], st["avg_pnl"]))


def main():
    picks = [p["symbol"] for p in json.load(open(D + "/picks.json"))["picks"]]
    spy = load("SPY")
    data = {}
    for s in picks:
        try:
            data[s] = load(s)
        except (OSError, KeyError, ValueError):
            pass
    days = sorted(spy)
    print("Data: %d stocks + SPY, %d sessions, %s to %s" % (len(data), len(days), days[0], days[-1]))

    # every signal, every day, with its flags and outcomes at 2R and 1.5R
    sigs = []
    for sym, dd in data.items():
        for d, bars in dd.items():
            for last_slot, tag in ((11, "window"), (71, "any")):
                s = signal(bars, spy.get(d), last_slot)
                if not s:
                    continue
                s.update(sym=sym, day=d, tag=tag,
                         price_ok=10 <= s["entry"] <= 75,
                         width_ok=0.005 <= s["width"] <= 0.02)
                for R in (2.0, 1.5, 1.0):
                    s["res%s" % R] = simulate(bars, s, R)
                sigs.append(s)

    def pick(tag, R, *flags):
        out = []
        for s in sigs:
            if s["tag"] == tag and all(s[f] for f in flags) and s["res%s" % R]:
                out.append(dict(s["res%s" % R], sym=s["sym"], day=s["day"], slot=s["slot"],
                                dv=s["dollar_vol"]))
        return out

    hdr = "%-44s %5s  %6s  %6s  %6s  %6s  %6s  %6s  %5s  %6s" % (
        "every qualifying signal (no portfolio limits)", "n", "win", "target", "stop", "flat",
        "avg R", "net R", "PF", "$/trd")
    print("\n" + hdr + "\n" + "-" * len(hdr))
    print(row("ORB, any time to 3:30, 2R", stats(pick("any", 2.0, "price_ok"))))
    print(row("ORB, 9:50-10:30 window, 2R", stats(pick("window", 2.0, "price_ok"))))
    print(row("  + range width 0.5-2%", stats(pick("window", 2.0, "price_ok", "width_ok"))))
    print(row("  + width + volume", stats(pick("window", 2.0, "price_ok", "width_ok", "vol_ok"))))
    print(row("  + width + volume + SPY  (FULL, 2R)",
              stats(pick("window", 2.0, "price_ok", "width_ok", "vol_ok", "spy_ok"))))
    print(row("  FULL, 1.5R target",
              stats(pick("window", 1.5, "price_ok", "width_ok", "vol_ok", "spy_ok"))))
    print(row("  FULL, 1R target",
              stats(pick("window", 1.0, "price_ok", "width_ok", "vol_ok", "spy_ok"))))
    print(row("  SPY filter only (window, 2R)", stats(pick("window", 2.0, "price_ok", "spy_ok"))))
    print(row("  window, SPY NOT above its range (2R)",
              stats([t for t in pick("window", 2.0, "price_ok")
                     if not next(s for s in sigs if s["tag"] == "window" and s["sym"] == t["sym"]
                                 and s["day"] == t["day"])["spy_ok"]])))

    full = pick("window", 2.0, "price_ok", "width_ok", "vol_ok", "spy_ok")
    half = days[len(days) // 2]
    print(row("  FULL 2R, first half (to %s)" % days[len(days) // 2 - 1],
              stats([t for t in full if t["day"] < half])))
    print(row("  FULL 2R, second half", stats([t for t in full if t["day"] >= half])))

    # the $1,000 account: one position at a time, at most 2 trades a day, no repeat symbol
    for R in (2.0, 1.5):
        cand = defaultdict(list)
        for t in pick("window", R, "price_ok", "width_ok", "vol_ok", "spy_ok"):
            cand[t["day"]].append(t)
        eq, peak, mdd, taken, curve = 1000.0, 1000.0, 0.0, [], []
        for d in days:
            busy_until, n, seen = -1, 0, set()
            for t in sorted(cand.get(d, []), key=lambda t: (t["slot"], -t["dv"])):
                if n >= 2 or t["slot"] <= busy_until or t["sym"] in seen:
                    continue
                taken.append(t); eq += t["pnl"]; n += 1; seen.add(t["sym"])
                busy_until = t["exit_slot"]
                peak = max(peak, eq); mdd = max(mdd, peak - eq)
            curve.append(eq)
        st = stats(taken)
        days_traded = len({t["day"] for t in taken})
        print("\n$1,000 account, FULL rules, %sR target, max 2 trades/day, one at a time:" % R)
        if st["n"]:
            print("  %d trades on %d of %d days | win %.1f%% | target %.1f%% stop %.1f%% flat %.1f%%"
                  % (st["n"], days_traded, len(days), 100 * st["win"], 100 * st["tgt"],
                     100 * st["stp"], 100 * st["flat"]))
            print("  net P&L $%+.2f (%+.1f%% of $1,000) | avg $%+.2f a trade | avg net R %+.3f | PF %.2f"
                  % (st["tot"], st["tot"] / 10, st["avg_pnl"], st["avg_r_net"], st["pf"]))
            print("  max drawdown $%.2f | worst trade $%.2f | best trade $%.2f | avg risk $%.2f"
                  % (mdd, min(t["pnl"] for t in taken), max(t["pnl"] for t in taken),
                     statistics.mean(t["risk_usd"] for t in taken)))
            if R == 2.0:
                json.dump(taken, open(os.path.dirname(D) + "/trades_2R.json", "w"), indent=1)

    s0 = spy[days[0]][min(spy[days[0]])][0]
    s1 = spy[days[-1]][max(spy[days[-1]])][3]
    print("\nBenchmark: SPY %s open %.2f -> %s close %.2f = %+.1f%%" %
          (days[0], s0, days[-1], s1, 100 * (s1 / s0 - 1)))


if __name__ == "__main__":
    main()
