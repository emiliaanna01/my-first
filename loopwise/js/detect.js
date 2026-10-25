// History buffer, alarm engine (ISA-18.2 style) and the diagnostic checks the agent relies on.
(function () {
  const LW = (globalThis.LW = globalThis.LW || {});

  // ---------- History ----------
  function createHistory(interval = 2, cap = 3600) {
    return { interval, cap, t: [], v: {}, lastT: -Infinity };
  }

  function record(h, t, meas) {
    if (t - h.lastT < h.interval) return;
    h.lastT = t;
    h.t.push(t);
    for (const [k, val] of Object.entries(meas)) {
      if (typeof val !== 'number') continue;
      (h.v[k] = h.v[k] || []).push(val);
    }
    if (h.t.length > h.cap + 200) {
      const cut = h.t.length - h.cap;
      h.t.splice(0, cut);
      for (const k of Object.keys(h.v)) h.v[k].splice(0, cut);
    }
  }

  function series(h, tag, seconds) {
    const vals = h.v[tag];
    if (!vals || !h.t.length) return { t: [], v: [] };
    const end = h.t[h.t.length - 1];
    let i = h.t.length - 1;
    while (i > 0 && h.t[i - 1] >= end - seconds) i--;
    return { t: h.t.slice(i), v: vals.slice(i) };
  }

  function regress(t, v) {
    const n = t.length;
    if (n < 3) return { slope: 0, intercept: v[0] ?? 0 };
    let st = 0, sv = 0, stt = 0, stv = 0;
    for (let i = 0; i < n; i++) { st += t[i]; sv += v[i]; stt += t[i] * t[i]; stv += t[i] * v[i]; }
    const d = n * stt - st * st;
    const slope = d === 0 ? 0 : (n * stv - st * sv) / d;
    return { slope, intercept: (sv - slope * st) / n };
  }

  function stats(h, tag, seconds) {
    const { t, v } = series(h, tag, seconds);
    if (!v.length) return null;
    let min = Infinity, max = -Infinity, sum = 0;
    for (const x of v) { min = Math.min(min, x); max = Math.max(max, x); sum += x; }
    const mean = sum / v.length;
    const { slope, intercept } = regress(t, v);
    let r2 = 0, d2 = 0;
    for (let i = 0; i < v.length; i++) r2 += (v[i] - (intercept + slope * t[i])) ** 2;
    for (let i = 1; i < v.length; i++) d2 += (v[i] - v[i - 1]) ** 2;
    return {
      n: v.length, min, max, mean, last: v[v.length - 1],
      std: Math.sqrt(r2 / v.length),       // scatter around the trend line
      jitter: v.length > 1 ? Math.sqrt(d2 / (v.length - 1) / 2) : 0, // sample-to-sample noise; ignores slow swings
      slopePerHour: slope * 3600,
      fitLast: intercept + slope * t[t.length - 1], // trend-line value now, steadier than the last sample
    };
  }

  // ---------- Alarms ----------
  const P = { CRITICAL: 1, HIGH: 2, MEDIUM: 3, LOW: 4 };
  const anyRun = (m) => m['P-101.RUN'] || m['P-102.RUN'];

  const ALARM_DEFS = [
    { id: 'LT-101.HH', tag: 'LT-101', pri: P.CRITICAL, msg: 'Wet well level high-high (overflow risk)', on: (m) => m['LT-101'] > 90, off: (m) => m['LT-101'] < 88, delay: 2 },
    { id: 'LT-101.H', tag: 'LT-101', pri: P.HIGH, msg: 'Wet well level high', on: (m) => m['LT-101'] > 80, off: (m) => m['LT-101'] < 78, delay: 5 },
    { id: 'LT-101.L', tag: 'LT-101', pri: P.HIGH, msg: 'Wet well level low', on: (m) => m['LT-101'] < 25, off: (m) => m['LT-101'] > 27, delay: 5 },
    { id: 'LT-101.LL', tag: 'LT-101', pri: P.CRITICAL, msg: 'Wet well level low-low (dry-run risk)', on: (m) => m['LT-101'] < 10, off: (m) => m['LT-101'] > 12, delay: 2 },
    { id: 'PT-102.H', tag: 'PT-102', pri: P.HIGH, msg: 'Discharge pressure high', on: (m) => m['PT-102'] > 4.4, off: (m) => m['PT-102'] < 4.2, delay: 10 },
    { id: 'PT-102.L', tag: 'PT-102', pri: P.MEDIUM, msg: 'Discharge pressure low with pump running', on: (m) => anyRun(m) && m['PT-102'] < 1.2, off: (m) => !anyRun(m) || m['PT-102'] > 1.4, delay: 20 },
    { id: 'XV-103.DISC', tag: 'XV-103.POS', pri: P.HIGH, msg: 'Discharge valve position does not match command', on: (m) => Math.abs(m['XV-103.CMD'] - m['XV-103.POS']) > 10, off: (m) => Math.abs(m['XV-103.CMD'] - m['XV-103.POS']) < 5, delay: 10 },
    { id: 'LIC-101.DEV', tag: 'LIC-101.OP', pri: P.MEDIUM, msg: 'Level controller deviation from setpoint', on: (m) => m['LIC-101.MODE'] === 'AUTO' && Math.abs(m['LT-101'] - m['LIC-101.SP']) > 10, off: (m) => Math.abs(m['LT-101'] - m['LIC-101.SP']) < 7, delay: 120 },
    { id: 'LIC-101.SAT', tag: 'LIC-101.OP', pri: P.MEDIUM, msg: 'Level controller output saturated at 100 %', on: (m) => m['LIC-101.OP'] >= 99.5, off: (m) => m['LIC-101.OP'] < 97, delay: 120 },
  ];
  for (const pump of ['P-101', 'P-102']) {
    ALARM_DEFS.push(
      { id: `${pump}.VIB.H`, tag: `${pump}.VIB`, pri: P.MEDIUM, msg: `${pump} vibration high (ISO 10816 zone C)`, on: (m) => m[`${pump}.VIB`] > 4.5, off: (m) => m[`${pump}.VIB`] < 4.2, delay: 30 },
      { id: `${pump}.VIB.HH`, tag: `${pump}.VIB`, pri: P.HIGH, msg: `${pump} vibration high-high (ISO 10816 zone D)`, on: (m) => m[`${pump}.VIB`] > 7.1, off: (m) => m[`${pump}.VIB`] < 6.8, delay: 10 },
      { id: `${pump}.TMP.H`, tag: `${pump}.TMP`, pri: P.HIGH, msg: `${pump} motor winding temperature high`, on: (m) => m[`${pump}.TMP`] > 95, off: (m) => m[`${pump}.TMP`] < 92, delay: 10 },
      { id: `${pump}.TMP.HH`, tag: `${pump}.TMP`, pri: P.CRITICAL, msg: `${pump} motor winding temperature high-high (trip imminent)`, on: (m) => m[`${pump}.TMP`] > 110, off: (m) => m[`${pump}.TMP`] < 105, delay: 5 },
    );
  }
  ALARM_DEFS.push({ id: 'LAG.RUN', tag: 'DUTY', pri: P.LOW, msg: 'Standby pump running on high level', on: (m) => m['P-101.RUN'] && m['P-102.RUN'], off: (m) => !(m['P-101.RUN'] && m['P-102.RUN']), delay: 5 });

  function createAlarms() {
    return { list: {}, pending: {}, events: [] };
  }

  function logEvent(a, t, kind, text) {
    a.events.push({ t, kind, text });
    if (a.events.length > 500) a.events.shift();
  }

  function evaluate(a, t, m) {
    const raised = [];
    for (const d of ALARM_DEFS) {
      const cur = a.list[d.id];
      const active = cur && cur.active;
      if (!active) {
        if (d.on(m)) {
          a.pending[d.id] = a.pending[d.id] ?? t;
          if (t - a.pending[d.id] >= d.delay) {
            const al = { id: d.id, tag: d.tag, pri: d.pri, msg: d.msg, active: true, acked: false, raisedAt: t, clearedAt: null, value: m[d.tag], count: (cur?.count || 0) + 1 };
            a.list[d.id] = al;
            delete a.pending[d.id];
            raised.push(al);
            logEvent(a, t, 'alarm', `${d.id} ${d.msg}`);
          }
        } else delete a.pending[d.id];
      } else {
        cur.value = m[d.tag];
        if (d.off(m)) {
          cur.active = false;
          cur.clearedAt = t;
          logEvent(a, t, 'rtn', `${d.id} returned to normal`);
          if (cur.acked) delete a.list[d.id];
        }
      }
    }
    return raised;
  }

  function ack(a, t, id) {
    const al = a.list[id];
    if (!al) return;
    al.acked = true;
    logEvent(a, t, 'ack', `${id} acknowledged`);
    if (!al.active) delete a.list[id];
  }

  function activeAlarms(a) {
    return Object.values(a.list).sort((x, y) => x.pri - y.pri || y.raisedAt - x.raisedAt);
  }

  // ---------- Diagnostic checks ----------
  function loopOscillation(h, window = 900) {
    const op = series(h, 'LIC-101.OP', window);
    const lv = series(h, 'LT-101', window);
    if (op.v.length < 60) return null;
    const mean = op.v.reduce((s, x) => s + x, 0) / op.v.length;
    const band = 5;
    let state = 0, crossings = [];
    for (let i = 0; i < op.v.length; i++) {
      const d = op.v[i] - mean;
      const s = d > band ? 1 : d < -band ? -1 : 0;
      if (s !== 0 && s !== state) { if (state !== 0) crossings.push(op.t[i]); state = s; }
    }
    const sorted = [...op.v].sort((x, y) => x - y);
    const pct = (p) => sorted[Math.floor(p * (sorted.length - 1))];
    const lvSorted = [...lv.v].sort((x, y) => x - y);
    const lvPct = (p) => lvSorted[Math.floor(p * (lvSorted.length - 1))];
    const period = crossings.length >= 3 ? (2 * (crossings[crossings.length - 1] - crossings[0])) / (crossings.length - 1) : null;
    return {
      oscillating: crossings.length >= 6,
      cycles: Math.floor(crossings.length / 2),
      periodS: period ? Math.round(period) : null,
      opAmplitude: (pct(0.95) - pct(0.05)) / 2,
      levelAmplitude: (lvPct(0.95) - lvPct(0.05)) / 2,
      windowS: window,
    };
  }

  function massBalance(h, plant, window = 900) {
    const lv = series(h, 'LT-101', window);
    const qi = series(h, 'FT-101', window);
    const qo = series(h, 'FT-102', window);
    if (lv.v.length < 60) return null;
    const overflow = Math.max(...lv.v) > 99;
    let dvFlow = 0;
    for (let i = 1; i < qi.v.length; i++) dvFlow += ((qi.v[i] - qo.v[i]) * (qi.t[i] - qi.t[i - 1])) / 3600;
    // Compare the level change with the flow integral; average the ends to beat transmitter noise.
    const k = Math.min(10, Math.floor(lv.v.length / 4));
    const avg = (arr) => arr.reduce((s, x) => s + x, 0) / arr.length;
    const dLevel = avg(lv.v.slice(-k)) - avg(lv.v.slice(0, k));
    const dvLevel = (dLevel / 100) * plant.wellVolume;
    const residual = dvLevel - dvFlow;
    const spanH = (lv.t[lv.t.length - 1] - lv.t[0]) / 3600;
    return {
      valid: !overflow,
      windowS: window,
      levelChangeM3: dvLevel,
      flowBalanceM3: dvFlow,
      residualM3: residual,
      impliedLevelDriftPctPerHour: spanH > 0 ? (residual / plant.wellVolume) * 100 / spanH : 0,
    };
  }

  function expectedFlow(plant, speedPct) {
    const s = speedPct / 100;
    return speedPct > 0 ? plant.pumpQmax * Math.max(0, (s - plant.minSpeed) / (1 - plant.minSpeed)) : 0;
  }

  function pumpPerformance(h, plant, window = 300) {
    const flow = stats(h, 'FT-102', window);
    if (!flow) return null;
    let expected = 0;
    const running = [];
    for (const id of ['P-101', 'P-102']) {
      const sp = stats(h, id + '.SPD', window);
      if (sp && sp.mean > 1) { running.push(id); expected += expectedFlow(plant, sp.mean); }
    }
    return { running, expectedM3h: expected, measuredM3h: flow.mean, ratio: expected > 20 ? flow.mean / expected : null };
  }

  function etaHours(st, threshold) {
    if (!st || st.slopePerHour <= 0 || st.last >= threshold) return null;
    return (threshold - st.last) / st.slopePerHour;
  }

  function runChecks(h, plant, m) {
    const findings = [];
    const add = (f) => findings.push(f);
    const fmt = (x, d = 1) => (x == null ? 'n/a' : Number(x).toFixed(d));

    const osc = loopOscillation(h);
    if (osc && osc.oscillating) {
      add({ id: 'loop_oscillation', severity: 'warning', equipment: 'LIC-101', title: 'LIC-101 is oscillating',
        detail: `${osc.cycles} cycles in ${osc.windowS / 60} min, period about ${osc.periodS} s, pump speed swinging ±${fmt(osc.opAmplitude, 0)} %, level ±${fmt(osc.levelAmplitude, 2)} %.`, evidence: osc });
    }

    const mb = massBalance(h, plant);
    if (mb && mb.valid && Math.abs(mb.residualM3) > 2.5) {
      add({ id: 'mass_balance', severity: 'warning', equipment: 'LT-101', title: 'Level does not match the flow balance',
        detail: `Over ${mb.windowS / 60} min the flows say the well changed by ${fmt(mb.flowBalanceM3)} m3 but LT-101 says ${fmt(mb.levelChangeM3)} m3. Gap ${fmt(mb.residualM3)} m3 (LT-101 drifting about ${fmt(mb.impliedLevelDriftPctPerHour)} %/h, or a flowmeter is wrong).`, evidence: mb });
    }

    const perf = pumpPerformance(h, plant);
    if (perf && perf.ratio !== null && perf.ratio < 0.85) {
      add({ id: 'pump_underperforming', severity: 'warning', equipment: perf.running.join(', '), title: 'Discharge flow below the pump curve',
        detail: `At the current speed the pump curve predicts ${fmt(perf.expectedM3h, 0)} m3/h but FT-102 reads ${fmt(perf.measuredM3h, 0)} m3/h (${fmt(perf.ratio * 100, 0)} % of expected).`, evidence: perf });
    }

    const pt = stats(h, 'PT-102', 120);
    if (pt && pt.n > 20 && pt.jitter > 0.12) {
      add({ id: 'pressure_noise', severity: 'warning', equipment: 'PT-102', title: 'Discharge pressure is erratic',
        detail: `PT-102 jumps ${fmt(pt.jitter, 2)} bar between samples (normal is about 0.02 bar). Typical of cavitation or air in the line.`, evidence: { jitter: pt.jitter, mean: pt.mean } });
    }

    const disc = Math.abs((m['XV-103.CMD'] ?? 0) - (m['XV-103.POS'] ?? 0));
    if (disc > 10) {
      add({ id: 'valve_discrepancy', severity: 'critical', equipment: 'XV-103', title: 'XV-103 is not following its command',
        detail: `Command ${fmt(m['XV-103.CMD'], 0)} %, position ${fmt(m['XV-103.POS'], 0)} %. The valve is restricting discharge.`, evidence: { cmd: m['XV-103.CMD'], pos: m['XV-103.POS'] } });
    }

    const op = series(h, 'LIC-101.OP', 600);
    if (op.v.length > 30) {
      const sat = op.v.filter((x) => x >= 99.5).length / op.v.length;
      if (sat > 0.5) add({ id: 'output_saturated', severity: 'warning', equipment: 'LIC-101', title: 'Controller has run out of pump capacity',
        detail: `LIC-101 output has been at 100 % for ${fmt(sat * 100, 0)} % of the last 10 min.`, evidence: { fraction: sat } });
    }

    for (const pump of ['P-101', 'P-102']) {
      if (!m[pump + '.RUN']) continue;
      const vib = stats(h, pump + '.VIB', 3600);
      const tmp = stats(h, pump + '.TMP', 3600);
      const spd = stats(h, pump + '.SPD', 3600);
      const ranWholeWindow = spd && spd.min > 1;
      const vibNow = stats(h, pump + '.VIB', 120);
      const erratic = vibNow && vibNow.n > 20 && vibNow.jitter >= 0.3;
      // A wear trend is a smooth ramp: a sudden step (std around the line) is something else.
      if (vib && !erratic && ranWholeWindow && vib.n > 100 && vib.slopePerHour > 0.3 && vib.fitLast > 2.6 && vib.std < 0.4) {
        add({ id: 'vibration_trend', severity: vib.last > 4.5 ? 'warning' : 'info', equipment: pump, title: `${pump} vibration is trending up`,
          detail: `${fmt(vib.last, 2)} mm/s now, rising ${fmt(vib.slopePerHour, 2)} mm/s per hour. Zone C (4.5) in ${fmt(etaHours(vib, 4.5))} h, zone D (7.1) in ${fmt(etaHours(vib, 7.1))} h.`,
          evidence: { now: vib.last, slopePerHour: vib.slopePerHour, etaZoneC_h: etaHours(vib, 4.5), etaZoneD_h: etaHours(vib, 7.1) } });
      }
      if (erratic && vibNow.mean > 4.5) {
        add({ id: 'vibration_erratic', severity: 'warning', equipment: pump, title: `${pump} vibration is high and erratic`,
          detail: `${fmt(vibNow.mean, 2)} mm/s average with ${fmt(vibNow.jitter, 2)} mm/s jumps between samples. Sudden and noisy, so hydraulic rather than mechanical wear.`, evidence: { mean: vibNow.mean, jitter: vibNow.jitter } });
      }
      if (tmp && ranWholeWindow && tmp.n > 100 && tmp.slopePerHour > 2 && tmp.last > 70) {
        add({ id: 'temperature_trend', severity: tmp.last > 95 ? 'warning' : 'info', equipment: pump, title: `${pump} motor temperature is rising`,
          detail: `${fmt(tmp.last)} degC now, rising ${fmt(tmp.slopePerHour)} degC per hour. Alarm (95) in ${fmt(etaHours(tmp, 95))} h, trip (110) in ${fmt(etaHours(tmp, 110))} h.`,
          evidence: { now: tmp.last, slopePerHour: tmp.slopePerHour, etaAlarm_h: etaHours(tmp, 95), etaTrip_h: etaHours(tmp, 110) } });
      }
    }

    const qin = stats(h, 'FT-101', 300);
    const qinBase = stats(h, 'FT-101', 7200);
    if (qin && qinBase && qin.mean > 1.5 * Math.min(qinBase.mean, 220)) {
      add({ id: 'inflow_high', severity: qin.mean > plant.pumpQmax ? 'warning' : 'info', equipment: 'FT-101', title: 'Inflow well above normal',
        detail: `Inflow ${fmt(qin.mean, 0)} m3/h against a normal of about 200 m3/h. One pump moves at most ${plant.pumpQmax} m3/h.`, evidence: { now: qin.mean, normal: 200, singlePumpMax: plant.pumpQmax } });
    }

    const lv = stats(h, 'LT-101', 300);
    if (lv && Math.abs(lv.slopePerHour) > 30) {
      const target = lv.slopePerHour > 0 ? 90 : 10;
      const eta = Math.abs((target - lv.last) / lv.slopePerHour) * 60;
      add({ id: 'level_moving', severity: 'warning', equipment: 'LT-101', title: `Level ${lv.slopePerHour > 0 ? 'rising' : 'falling'} fast`,
        detail: `${fmt(lv.last)} % and moving ${fmt(lv.slopePerHour / 60, 2)} %/min. ${lv.slopePerHour > 0 ? 'High-high (90 %)' : 'Low-low (10 %)'} in about ${fmt(eta, 0)} min.`, evidence: { now: lv.last, ratePerMin: lv.slopePerHour / 60, etaMin: eta } });
    }
    return findings;
  }

  // Rule engine: map findings to likely causes. The agent treats these as candidates to verify.
  function candidateCauses(findings) {
    const has = (id) => findings.find((f) => f.id === id);
    const out = [];
    if (has('valve_discrepancy')) out.push({ cause: 'XV-103 discharge valve stuck or actuator failed', equipment: 'XV-103', confidence: 0.95, sop: 'SOP-VLV-02',
      because: ['valve_discrepancy', has('pump_underperforming') && 'pump_underperforming', has('output_saturated') && 'output_saturated'].filter(Boolean) });
    if (has('pressure_noise') && (has('vibration_erratic') || has('pump_underperforming')) && !has('valve_discrepancy')) {
      const eq = (has('vibration_erratic') || {}).equipment || 'duty pump';
      out.push({ cause: `${eq} cavitating (blocked intake or low suction)`, equipment: eq, confidence: has('vibration_erratic') ? 0.85 : 0.6, sop: 'SOP-PMP-03',
        because: ['pressure_noise', has('vibration_erratic') && 'vibration_erratic', has('pump_underperforming') && 'pump_underperforming'].filter(Boolean) });
    }
    if (has('mass_balance') && !has('valve_discrepancy')) out.push({ cause: 'LT-101 level transmitter drifting', equipment: 'LT-101', confidence: has('loop_oscillation') ? 0.5 : 0.8, sop: 'SOP-INS-01', because: ['mass_balance'] });
    if (has('loop_oscillation') && !has('valve_discrepancy') && !has('pressure_noise')) out.push({ cause: 'LIC-101 tuning too aggressive (loop hunting)', equipment: 'LIC-101', confidence: 0.8, sop: 'SOP-CTL-01', because: ['loop_oscillation'] });
    if (has('vibration_trend') && !has('vibration_erratic')) {
      const f = has('vibration_trend');
      out.push({ cause: `${f.equipment} bearing wear developing`, equipment: f.equipment, confidence: has('temperature_trend') ? 0.85 : 0.65, sop: 'SOP-PMP-05',
        because: ['vibration_trend', has('temperature_trend') && 'temperature_trend'].filter(Boolean) });
    }
    if (has('inflow_high') && !has('valve_discrepancy')) out.push({ cause: 'Hydraulic overload from high inflow (storm or upstream discharge)', equipment: 'FT-101', confidence: 0.85, sop: 'SOP-OPS-04',
      because: ['inflow_high', has('level_moving') && 'level_moving', has('output_saturated') && 'output_saturated'].filter(Boolean) });
    return out.sort((x, y) => y.confidence - x.confidence);
  }

  // SIMC tuning for an integrating level process: Kc = 1 / (k' (tc + theta)), Ti = 4 (tc + theta).
  function recommendTuning(plant, pumpsRunning = 1, tc = 150) {
    const kPrime = ((plant.pumpQmax * pumpsRunning) / (1 - plant.minSpeed) / 100 / 3600 / plant.wellVolume) * 100;
    const theta = plant.ltDeadtime + 5;
    const kp = 1 / (kPrime * (tc + theta));
    const ti = 4 * (tc + theta);
    return {
      method: 'SIMC (Skogestad) for an integrating process',
      model: { integratingGainPctPerSPerPct: kPrime, deadtimeS: theta },
      closedLoopTimeConstantS: tc,
      kp: Math.round(kp * 10) / 10,
      ti: Math.round(ti / 10) * 10,
    };
  }

  LW.History = { create: createHistory, record, series, stats };
  LW.Alarms = { DEFS: ALARM_DEFS, PRIORITY: P, create: createAlarms, evaluate, ack, active: activeAlarms, log: logEvent };
  LW.Detect = { runChecks, candidateCauses, loopOscillation, massBalance, pumpPerformance, recommendTuning, expectedFlow };
})();
