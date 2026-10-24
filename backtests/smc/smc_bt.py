"""Backtest of the 1H -> 5m SMC strategy (CHoCH, BOS, POI, LTF FVG retest, rejection).

Data: HistData.com 1-minute BID bars, timestamps EST without DST (UTC-5 all year).
Everything is decided on CLOSED bars only; entries fill at the next 5m bar's open;
exits are simulated on 1-minute bars.

Rules as agreed with the user
  1H  swings: fractal pivots, 3 bars each side (known only 3 bars later)
  5m  swings: fractal pivots, 2 bars each side
  break of structure uses the candle CLOSE (body), never a wick
  CHoCH: first close beyond the latest swing against the trend; BOS: close beyond the latest
         swing in the trend direction
  1H POI: after a 1H CHoCH, the FIRST 1H BOS in that direction marks the POI: the unfilled FVG
          in the leg that caused the BOS, closest to price; else the order block (last opposite
          candle at the leg's start)
  POI dies on a 1H close through its far side, on an opposite 1H CHoCH, or after one trade
  5m: after price touches the POI: 5m CHoCH, then 5m BOS, in the trade direction; the 5m FVG
      in the BOS leg must overlap the 1H POI (closest to price if several)
  retest: within 24 five-minute bars of the BOS; rejection candle = wick into the FVG, closes in
          the trade direction and beyond the FVG midpoint
  setup fails if a 5m bar closes beyond the FVG's far side or touches the stop
  entry: next 5m open. SL: FVG far edge - 0.1 x ATR14(5m). TP: nearest unswept 1H swing
         (swing high for longs). Skip unless reward:risk >= 2. No breakeven, no partials.
  costs: spread on entry (bid data: longs buy at bid+spread, shorts exit at ask) and
         $7 per $100k notional round trip
  size: $20 risk a trade (2 % of $1,000), notional capped at 30:1 leverage on $1,000
"""
import csv, io, json, math, os, statistics, sys, zipfile
from collections import defaultdict
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
SPREAD = {"EURUSD": 0.00010, "GBPUSD": 0.00014, "USDJPY": 0.012, "XAUUSD": 0.30}
COMM_PER_USD = 7.0 / 100000
RISK_USD, ACCOUNT, MAX_LEV = 20.0, 1000.0, 30.0
N1H, N5M = 3, 2
RETEST_BARS, ATR_N, BUF_ATR, MIN_RR = 24, 14, 0.1, 2.0
# MODE strict: 5m FVG must overlap the 1H POI (sheet section 1)
#      relaxed: any FVG left by the 5m BOS (sheet section 2)
#      origin: the move that makes the 5m CHoCH starts inside the 1H POI; FVG left by the BOS
MODE = os.environ.get("MODE", "origin")
TP_R = float(os.environ.get("TP_R", "0"))          # 0 = the rule: nearest unswept 1H swing
EST = 5 * 3600


# ------------------------------------------------------------------ data

def load_1m(sym):
    files = sorted(f for f in os.listdir(DATA) if f.startswith(sym + "_") and f.endswith(".zip"))
    t, o, h, l, c = [], [], [], [], []
    for f in files:
        with zipfile.ZipFile(os.path.join(DATA, f)) as z:
            name = next(n for n in z.namelist() if n.endswith(".csv"))
            for row in csv.reader(io.TextIOWrapper(z.open(name)), delimiter=";"):
                d = row[0]
                ts = int(datetime(int(d[:4]), int(d[4:6]), int(d[6:8]), int(d[9:11]), int(d[11:13]),
                                  tzinfo=timezone.utc).timestamp()) + EST
                t.append(ts); o.append(float(row[1])); h.append(float(row[2]))
                l.append(float(row[3])); c.append(float(row[4]))
    return t, o, h, l, c


def resample(m1, sec):
    t, o, h, l, c = m1
    out = ([], [], [], [], [], [])  # t, o, h, l, c, index of first 1m bar
    cur = None
    for i in range(len(t)):
        b = t[i] - t[i] % sec
        if b != cur:
            cur = b
            out[0].append(b); out[1].append(o[i]); out[2].append(h[i]); out[3].append(l[i])
            out[4].append(c[i]); out[5].append(i)
        else:
            if h[i] > out[2][-1]: out[2][-1] = h[i]
            if l[i] < out[3][-1]: out[3][-1] = l[i]
            out[4][-1] = c[i]
    return out


# ------------------------------------------------------------------ structure

class Structure:
    """Swings, trend, CHoCH and BOS on one timeframe, fed one closed bar at a time."""

    def __init__(self, n):
        self.n = n
        self.o, self.h, self.l, self.c, self.t = [], [], [], [], []
        self.sh = self.sl = None          # [price, idx, broken]
        self.broken = None                # idx of the swing the last event broke
        self.trend = 0
        self.highs, self.lows = [], []    # every confirmed swing: (price, idx)

    def add(self, t, o, h, l, c):
        self.t.append(t); self.o.append(o); self.h.append(h); self.l.append(l); self.c.append(c)
        i, n = len(self.c) - 1, self.n
        p = i - n
        if p >= n:
            hp, lp = self.h[p], self.l[p]
            if all(hp > self.h[k] for k in range(p - n, p + n + 1) if k != p):
                self.sh = [hp, p, False]; self.highs.append((hp, p))
            if all(lp < self.l[k] for k in range(p - n, p + n + 1) if k != p):
                self.sl = [lp, p, False]; self.lows.append((lp, p))
        ev = None
        if self.sh and not self.sh[2] and c > self.sh[0]:
            self.sh[2] = True; self.broken = self.sh[1]
            ev = "CHOCH_UP" if self.trend == -1 else "BOS_UP" if self.trend == 1 else "INIT_UP"
            self.trend = 1
        elif self.sl and not self.sl[2] and c < self.sl[0]:
            self.sl[2] = True; self.broken = self.sl[1]
            ev = "CHOCH_DN" if self.trend == 1 else "BOS_DN" if self.trend == -1 else "INIT_DN"
            self.trend = -1
        return ev

    def leg_start(self, a, b, d):
        rng = range(a, b + 1)
        return min(rng, key=lambda k: self.l[k]) if d == 1 else max(rng, key=lambda k: self.h[k])

    def fvgs(self, a, b, d):
        """Unfilled FVGs created in bars a..b (third candle index), as (bottom, top, idx)."""
        out = []
        for j in range(max(a + 2, 2), b + 1):
            if d == 1 and self.l[j] > self.h[j - 2]:
                bot, top = self.h[j - 2], self.l[j]
                if all(self.l[k] > bot for k in range(j + 1, b + 1)):
                    out.append((bot, top, j))
            if d == -1 and self.h[j] < self.l[j - 2]:
                bot, top = self.h[j], self.l[j - 2]
                if all(self.h[k] < top for k in range(j + 1, b + 1)):
                    out.append((bot, top, j))
        return out

    def order_block(self, leg, b, d):
        for k in range(min(leg + 1, b - 1), max(-1, leg - 6), -1):
            if (d == 1 and self.c[k] < self.o[k]) or (d == -1 and self.c[k] > self.o[k]):
                return (self.l[k], self.h[k], k)
        return None


# ------------------------------------------------------------------ backtest

def run(sym, m1, log_examples=False):
    t1, o1, h1, l1, c1 = m1
    m5 = resample(m1, 300)
    T, O, H, L, C, FIRST = m5
    spread = SPREAD[sym]
    S1, S5 = Structure(N1H), Structure(N5M)
    cur_hour, hb = None, None
    poi = None
    pending = None                        # (direction, 1H CHoCH index)
    funnel = defaultdict(int)
    trades, busy_until = [], -1
    tr = []                               # 5m true ranges
    sig = None                            # rejection seen at bar i -> enter at i+1

    def close_hour():
        nonlocal poi, pending
        ev = S1.add(*hb)
        j = len(S1.c) - 1
        if poi:
            bot, top = poi["zone"]
            if (poi["dir"] == 1 and S1.c[j] < bot) or (poi["dir"] == -1 and S1.c[j] > top):
                funnel["poi_invalidated_close"] += 1; poi = None
        if ev in ("CHOCH_UP", "CHOCH_DN"):
            d = 1 if ev == "CHOCH_UP" else -1
            if poi and poi["dir"] != d:
                funnel["poi_invalidated_choch"] += 1; poi = None
            pending = (d, j)
        elif ev in ("BOS_UP", "BOS_DN") and pending and pending[0] == (1 if ev == "BOS_UP" else -1):
            d, ch = pending
            pending = None                # only the FIRST BOS after the CHoCH
            leg = S1.leg_start(ch, j, d)
            f = S1.fvgs(leg, j, d)
            if f:
                zone = max(f, key=lambda z: z[1]) if d == 1 else min(f, key=lambda z: z[0])
                kind = "FVG"
            else:
                zone, kind = S1.order_block(leg, j, d), "OB"
            if zone:
                funnel["poi_" + kind] += 1
                poi = dict(dir=d, zone=(zone[0], zone[1]), kind=kind, t=S1.t[j], touched=False,
                           state="WAIT_CHOCH")

    for i in range(len(T)):
        hour = T[i] - T[i] % 3600
        if hour != cur_hour:
            if hb is not None:
                close_hour()
            cur_hour, hb = hour, [hour, O[i], H[i], L[i], C[i]]
        else:
            hb[2] = max(hb[2], H[i]); hb[3] = min(hb[3], L[i]); hb[4] = C[i]

        # enter on this bar's open if the previous bar was a rejection
        if sig and i > busy_until:
            res = enter(sym, sig, i, m5, m1, S1, hb, spread, funnel)
            if res:
                trades.append(res); busy_until = res["exit_bar5"]
                if poi is sig["poi"]:
                    poi = None            # one trade per POI
        sig = None

        prev_c = C[i - 1] if i else C[i]
        tr.append(max(H[i] - L[i], abs(H[i] - prev_c), abs(L[i] - prev_c)))
        ev = S5.add(T[i], O[i], H[i], L[i], C[i])
        if not poi:
            continue
        d, (bot, top) = poi["dir"], poi["zone"]
        if not poi["touched"]:
            if (d == 1 and L[i] <= top) or (d == -1 and H[i] >= bot):
                poi["touched"] = True; funnel["poi_touched"] += 1
            else:
                continue
        st = poi["state"]
        up, dn = ("CHOCH_UP", "BOS_UP"), ("CHOCH_DN", "BOS_DN")
        mine, other = (up, dn) if d == 1 else (dn, up)
        if st == "WAIT_CHOCH":
            if ev == mine[0]:
                org = S5.leg_start(S5.broken, i, d)   # the low (high) the CHoCH move started from
                inside = (S5.l[org] <= top) if d == 1 else (S5.h[org] >= bot)
                if MODE != "origin" or inside:
                    poi.update(state="WAIT_BOS", ltf_choch=org if MODE == "origin" else i)
                    funnel["ltf_choch"] += 1
        elif st == "WAIT_BOS":
            if ev == other[0]:
                poi["state"] = "WAIT_CHOCH"
            elif ev == mine[1]:
                funnel["ltf_bos"] += 1
                leg = S5.leg_start(poi["ltf_choch"], i, d)
                f = [z for z in S5.fvgs(leg, i, d) if MODE != "strict" or (z[0] <= top and z[1] >= bot)]
                if f:
                    z = max(f, key=lambda z: z[1]) if d == 1 else min(f, key=lambda z: z[0])
                    atr = statistics.mean(tr[-ATR_N:])
                    stop = z[0] - BUF_ATR * atr if d == 1 else z[1] + BUF_ATR * atr
                    poi.update(state="WAIT_RETEST", fvg=z, fvg_t=S5.t[z[2] - 2], bos=i, stop=stop)
                    funnel["ltf_fvg_in_poi"] += 1
        elif st == "WAIT_RETEST":
            fb, ft = poi["fvg"][0], poi["fvg"][1]
            mid = (fb + ft) / 2
            if i - poi["bos"] > RETEST_BARS:
                poi["state"] = "WAIT_CHOCH"; funnel["retest_timeout"] += 1
            elif (d == 1 and (L[i] <= poi["stop"] or C[i] < fb)) or \
                 (d == -1 and (H[i] >= poi["stop"] or C[i] > ft)):
                poi["state"] = "WAIT_CHOCH"; funnel["fvg_failed"] += 1
            elif (d == 1 and L[i] <= ft and C[i] > O[i] and C[i] > mid) or \
                 (d == -1 and H[i] >= fb and C[i] < O[i] and C[i] < mid):
                funnel["rejection"] += 1
                sig = dict(dir=d, stop=poi["stop"], fvg=poi["fvg"], poi=poi, zone=poi["zone"],
                           kind=poi["kind"], bar=i, poi_t=poi["t"], fvg_t=poi["fvg_t"])
                poi["state"] = "WAIT_CHOCH"   # if the trade is skipped, look for the next one
    return trades, funnel


def enter(sym, s, i, m5, m1, S1, hb, spread, funnel):
    T, O, H, L, C, FIRST = m5
    t1, o1, h1, l1, c1 = m1
    d, stop = s["dir"], s["stop"]
    entry = O[i] + spread if d == 1 else O[i]          # long buys the ask, short sells the bid
    if (d == 1 and entry <= stop) or (d == -1 and entry >= stop):
        funnel["skip_gap_past_stop"] += 1; return None
    # nearest unswept 1H swing beyond the entry (completed hours + the current hour so far)
    tp = None
    if d == 1:
        for price, idx in reversed(S1.highs[-300:]):
            if price > entry and max(S1.h[idx + 1:] + [hb[2]]) < price:
                tp = price if tp is None else min(tp, price)
    else:
        for price, idx in reversed(S1.lows[-300:]):
            if price < entry and min(S1.l[idx + 1:] + [hb[3]]) > price:
                tp = price if tp is None else max(tp, price)
    if TP_R:                              # sensitivity test only: fixed R multiple target
        tp = entry + d * TP_R * abs(entry - stop)
    if tp is None:
        funnel["skip_no_target"] += 1; return None
    risk = abs(entry - stop)
    rr = abs(tp - entry) / risk
    if rr < MIN_RR:
        funnel["skip_rr"] += 1; return None
    usd = (lambda px: 1 / px) if sym == "USDJPY" else (lambda px: 1.0)   # quote -> USD per unit
    units = RISK_USD / (risk * usd(entry))
    notional = units * (1 if sym == "USDJPY" else entry)
    if notional > MAX_LEV * ACCOUNT:
        units *= MAX_LEV * ACCOUNT / notional; notional = MAX_LEV * ACCOUNT
    # walk 1-minute bars from the entry bar
    k, how, exit_px = FIRST[i], None, None
    while k < len(t1):
        if d == 1:
            if o1[k] <= stop: how, exit_px = "stop", o1[k]
            elif l1[k] <= stop: how, exit_px = "stop", stop
            elif h1[k] >= tp: how, exit_px = "target", max(tp, o1[k]) if o1[k] >= tp else tp
        else:
            ask_o, ask_h, ask_l = o1[k] + spread, h1[k] + spread, l1[k] + spread
            if ask_o >= stop: how, exit_px = "stop", ask_o
            elif ask_h >= stop: how, exit_px = "stop", stop
            elif ask_l <= tp: how, exit_px = "target", min(tp, ask_o) if ask_o <= tp else tp
        if how:
            break
        k += 1
    if not how:
        how, exit_px, k = "open_at_end", (c1[-1] if d == 1 else c1[-1] + spread), len(t1) - 1
    move = (exit_px - entry) * d
    pnl = units * move * usd(exit_px) - COMM_PER_USD * notional
    exit_bar5 = i
    while exit_bar5 + 1 < len(T) and FIRST[exit_bar5 + 1] <= k:
        exit_bar5 += 1
    funnel["trades"] += 1
    return dict(sym=sym, dir="long" if d == 1 else "short", entry_t=T[i], exit_t=t1[k],
                entry=entry, stop=stop, target=tp, rr_planned=rr, how=how, exit=exit_px,
                r=move / risk, pnl=pnl, units=units, notional=notional, exit_bar5=exit_bar5,
                poi_kind=s["kind"], poi_zone=s["zone"], fvg=s["fvg"][:2], signal_t=T[s["bar"]],
                poi_t=s["poi_t"], fvg_t=s["fvg_t"])


# ------------------------------------------------------------------ report

def stats(tr):
    if not tr:
        return dict(n=0)
    w = [t for t in tr if t["pnl"] > 0]
    gl = -sum(t["pnl"] for t in tr if t["pnl"] <= 0)
    rs = [t["r"] for t in tr]
    return dict(n=len(tr), win=len(w) / len(tr), avg_r=statistics.mean(rs),
                se=statistics.stdev(rs) / math.sqrt(len(rs)) if len(rs) > 1 else 0,
                pf=sum(t["pnl"] for t in w) / gl if gl else float("inf"),
                pnl=sum(t["pnl"] for t in tr), rr=statistics.mean(t["rr_planned"] for t in tr))


def line(name, s):
    if not s["n"]:
        return "%-22s %5d" % (name, 0)
    return "%-22s %5d  %5.1f%%  %+6.3f ±%5.3f  %5.2f  %5.1f  %+9.2f" % (
        name, s["n"], 100 * s["win"], s["avg_r"], 2 * s["se"], s["pf"], s["rr"], s["pnl"])


def main():
    syms = sys.argv[1:] or ["XAUUSD", "EURUSD", "GBPUSD", "USDJPY"]
    allt, funnels = [], {}
    for sym in syms:
        m1 = load_1m(sym)
        print("%s: %d one-minute bars, %s to %s" % (sym, len(m1[0]),
              datetime.fromtimestamp(m1[0][0], timezone.utc).date(),
              datetime.fromtimestamp(m1[0][-1], timezone.utc).date()), flush=True)
        tr, fn = run(sym, m1)
        allt += tr; funnels[sym] = dict(fn)
    tag = "_" + MODE + ("_tp%gR" % TP_R if TP_R else "")
    json.dump(allt, open(os.path.join(HERE, "trades%s.json" % tag), "w"), indent=1)
    json.dump(funnels, open(os.path.join(HERE, "funnel%s.json" % tag), "w"), indent=1)

    hdr = "%-22s %5s  %6s  %14s  %5s  %5s  %9s" % ("", "n", "win", "avg R ±95%", "PF", "RRpl", "P&L $")
    print("\n" + hdr + "\n" + "-" * len(hdr))
    print(line("ALL", stats(allt)))
    for sym in syms:
        print(line(sym, stats([t for t in allt if t["sym"] == sym])))
    for d in ("long", "short"):
        print(line(d, stats([t for t in allt if t["dir"] == d])))
    for y in sorted({datetime.fromtimestamp(t["entry_t"], timezone.utc).year for t in allt}):
        print(line(str(y), stats([t for t in allt if datetime.fromtimestamp(t["entry_t"], timezone.utc).year == y])))
    for k in ("FVG", "OB"):
        print(line("1H POI = " + k, stats([t for t in allt if t["poi_kind"] == k])))
    print("\nexits:", dict(sorted(defaultdict(int, {h: sum(t["how"] == h for t in allt)
                                                   for h in {t["how"] for t in allt}}).items())))
    eq, peak, mdd = ACCOUNT, ACCOUNT, 0
    for t in sorted(allt, key=lambda t: t["exit_t"]):
        eq += t["pnl"]; peak = max(peak, eq); mdd = max(mdd, peak - eq)
    print("$1,000 account at $20 risk a trade: final $%.2f (%+.1f%%), max drawdown $%.2f"
          % (eq, 100 * (eq / ACCOUNT - 1), mdd))
    print("\nfunnel:")
    keys = ["poi_FVG", "poi_OB", "poi_touched", "ltf_choch", "ltf_bos", "ltf_fvg_in_poi", "retest_timeout",
            "fvg_failed", "rejection", "skip_no_target", "skip_rr", "skip_gap_past_stop", "trades",
            "poi_invalidated_close", "poi_invalidated_choch"]
    print("%-22s" % "" + "".join("%9s" % s for s in syms))
    for k in keys:
        print("%-22s" % k + "".join("%9d" % funnels[s].get(k, 0) for s in syms))


if __name__ == "__main__":
    main()
