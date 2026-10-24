# Backtests

Not financial advice. Simulations on real historical bars; past results do not predict future ones.

## smc/ — 1H to 5m Smart Money Concepts strategy

Data: HistData.com 1-minute bid bars, Jan 2023 to mid-Oct 2026, for XAUUSD, EURUSD, GBPUSD and USDJPY.
Exits are simulated on 1-minute bars. Costs follow a typical retail ECN account (EURUSD 1.0, GBPUSD 1.4,
USDJPY 1.2 pip spread, gold $0.30, plus $7 per $100k round trip). Risk is $20 a trade, with notional
capped at 30:1 on $1,000.

```bash
python3 backtests/smc/fetch_histdata.py                 # ~53 MB of zips into backtests/smc/data/
MODE=origin  python3 backtests/smc/smc_bt.py            # or MODE=strict / MODE=relaxed, TP_R=2 for a fixed 2R target
python3 backtests/smc/plot_trade.py backtests/smc/trades_origin.json 1 chart.png
```

| version (how the 5m setup relates to the 1H POI) | trades | win | avg R (±95%) | $1,000 account |
|---|---|---|---|---|
| strict: 5m FVG must overlap the 1H POI | 15 | 6.7% | −0.03 (±1.94) | −9.0% |
| origin: the 5m CHoCH move starts inside the POI | 61 | 13.1% | −0.41 (±0.42) | −35.2% |
| relaxed: any FVG left by the 5m BOS | 139 | 15.1% | −0.20 (±0.40) | −12.0% |
| origin, fixed 2R target (sensitivity) | 73 | 21.9% | −0.35 (±0.29) | −49.4% |
| relaxed, fixed 2R target (sensitivity) | 166 | 25.3% | −0.25 (±0.21) | −64.8% |

The full output, with per-instrument, per-year and long/short results and the setup funnel, is in `smc/results/`.

## orb/ — 15-minute opening-range breakout on US stocks

There are 60 days of Yahoo 5-minute bars, for the 300 most traded stocks priced $10–75. The full filter set
gave 289 signals, with an average net R of −0.33.
