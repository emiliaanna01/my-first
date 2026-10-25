// Lift Station 3: a wet well, two VFD pumps (duty/standby), a discharge valve and a level PI loop.
// One step = one simulated second. Everything is deterministic for a given seed so tests can replay it.
(function () {
  const LW = (globalThis.LW = globalThis.LW || {});

  const PLANT = {
    name: 'Lift Station 3',
    wellVolume: 60,          // m3 at 100 % level
    pumpQmax: 320,           // m3/h per pump at 100 % speed, valve open
    minSpeed: 0.25,          // fraction of speed needed to beat the static head
    valveCapacity: 750,      // m3/h through XV-103 fully open
    ambient: 28,             // degC
    ratedCurrent: 98,        // A
    vfdRamp: 2,              // % per second
    lagStart: 88,            // % level: standby pump starts (hardwired)
    lagStop: 55,             // % level: standby pump stops
    ltDeadtime: 15,          // s: ultrasonic transmitter damping + PLC scan + comms
  };

  // Tag catalogue: what the operator, the analytics and the agent all see.
  const TAGS = {
    'LT-101':   { desc: 'Wet well level', unit: '%', lo: 0, hi: 100 },
    'LIC-101.SP': { desc: 'Level controller setpoint', unit: '%', lo: 0, hi: 100 },
    'LIC-101.OP': { desc: 'Level controller output (pump speed demand)', unit: '%', lo: 0, hi: 100 },
    'FT-101':   { desc: 'Inflow to wet well', unit: 'm3/h', lo: 0, hi: 700 },
    'FT-102':   { desc: 'Discharge flow', unit: 'm3/h', lo: 0, hi: 700 },
    'PT-102':   { desc: 'Discharge pressure', unit: 'bar', lo: 0, hi: 6 },
    'XV-103.CMD': { desc: 'Discharge valve command', unit: '%', lo: 0, hi: 100 },
    'XV-103.POS': { desc: 'Discharge valve position feedback', unit: '%', lo: 0, hi: 100 },
    'P-101.SPD': { desc: 'Pump P-101 speed', unit: '%', lo: 0, hi: 100 },
    'P-101.AMP': { desc: 'Pump P-101 motor current', unit: 'A', lo: 0, hi: 120 },
    'P-101.TMP': { desc: 'Pump P-101 motor winding temperature', unit: 'degC', lo: 0, hi: 130 },
    'P-101.VIB': { desc: 'Pump P-101 bearing vibration (RMS velocity)', unit: 'mm/s', lo: 0, hi: 12 },
    'P-102.SPD': { desc: 'Pump P-102 speed', unit: '%', lo: 0, hi: 100 },
    'P-102.AMP': { desc: 'Pump P-102 motor current', unit: 'A', lo: 0, hi: 120 },
    'P-102.TMP': { desc: 'Pump P-102 motor winding temperature', unit: 'degC', lo: 0, hi: 130 },
    'P-102.VIB': { desc: 'Pump P-102 bearing vibration (RMS velocity)', unit: 'mm/s', lo: 0, hi: 12 },
  };

  const SCENARIOS = {
    cavitation:  { title: 'Pump cavitation', equipment: 'P-101', blurb: 'Rags block the duty pump intake. Flow drops, pressure turns noisy, vibration climbs.' },
    drift:       { title: 'Level sensor drift', equipment: 'LT-101', blurb: 'LT-101 slowly reads high. The loop looks perfect while the real level falls.' },
    valveStuck:  { title: 'Stuck discharge valve', equipment: 'XV-103', blurb: 'XV-103 actuator fails at 30 %. More pumping cannot move more water.' },
    badTuning:   { title: 'Loop retuned badly', equipment: 'LIC-101', blurb: 'Someone set LIC-101 to Kp 15, Ti 20 s. The pumps start hunting.' },
    bearing:     { title: 'Bearing wear', equipment: 'P-101', blurb: 'The duty pump bearing degrades over hours. Vibration and temperature creep up.' },
    surge:       { title: 'Storm inflow', equipment: 'FT-101', blurb: 'Rain raises inflow to 2.6x for 45 minutes. A process upset, not a fault.' },
  };

  function rng(seed) {
    let a = seed >>> 0;
    return function () {
      a = (a + 0x6d2b79f5) >>> 0;
      let t = a;
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  function newPump() {
    return { run: false, speed: 0, flow: 0, amp: 0, temp: 45, vib: 0, wear: 0, cav: 0 };
  }

  function create(seed = 7) {
    const s = {
      seed,
      rngState: seed,
      t: 0,
      volume: 0.6 * PLANT.wellVolume,
      inflow: 180,
      surgeT: -1,
      duty: 'P-101',
      pumps: { 'P-101': newPump(), 'P-102': newPump() },
      valve: { cmd: 100, pos: 100, stuck: null },
      pid: { sp: 60, kp: 3.4, ti: 600, mode: 'AUTO', op: 67, pv: 60 },
      lt: { filtered: 60, drift: 0, delay: [] },
      faults: { cavitation: false, drift: false, valveStuck: false, badTuning: false, bearing: false, surge: false },
      meas: {},
    };
    s.pumps['P-101'].run = true;
    s.pumps['P-101'].speed = 67;
    s.pumps['P-101'].temp = 56;
    s._rand = rng(seed);
    // Settle into a realistic steady state before anyone looks at it.
    for (let i = 0; i < 900; i++) step(s);
    s.t = 0;
    return s;
  }

  function noise(s, amp) {
    return (s._rand() * 2 - 1) * amp;
  }

  function step(s) {
    const dt = 1;
    const P = PLANT;
    s.t += dt;

    // Inflow: a compressed daily pattern, noise and an optional storm.
    let qin = 180 + 40 * Math.sin((2 * Math.PI * s.t) / 21600) + noise(s, 6);
    if (s.faults.surge) {
      if (s.surgeT < 0) s.surgeT = 0;
      s.surgeT += dt;
      const ramp = Math.min(1, s.surgeT / 300);
      const decay = s.surgeT > 3000 ? Math.max(0, 1 - (s.surgeT - 3000) / 600) : 1;
      qin *= 1 + 1.6 * ramp * decay;
      if (s.surgeT > 3600) { s.faults.surge = false; s.surgeT = -1; }
    }
    s.inflow = Math.max(0, qin);

    // Level transmitter: true level plus drift, noise and a 5 s filter.
    const trueLevel = (s.volume / P.wellVolume) * 100;
    if (s.faults.drift) s.lt.drift = Math.min(45, s.lt.drift + 0.012 * dt);
    s.lt.delay.push(trueLevel + s.lt.drift + noise(s, 0.12));
    const raw = s.lt.delay.length > P.ltDeadtime ? s.lt.delay.shift() : s.lt.delay[0];
    s.lt.filtered += (raw - s.lt.filtered) * (dt / 5);
    const pv = Math.max(0, Math.min(100, s.lt.filtered));
    s.pid.pv = pv;

    // LIC-101: direct-acting PI (more level, more pumping) with conditional-integration anti-windup.
    if (s.pid.mode === 'AUTO') {
      const err = pv - s.pid.sp;
      const kp = s.pid.kp;
      let op = s.pid.op + kp * (err - (s.pid.lastErr ?? err)) + (kp * dt / s.pid.ti) * err;
      s.pid.lastErr = err;
      s.pid.op = Math.max(0, Math.min(100, op));
    } else {
      s.pid.lastErr = pv - s.pid.sp;
    }

    // Lead/lag: standby pump follows a hardwired level rule on the true float switch.
    const standby = s.duty === 'P-101' ? 'P-102' : 'P-101';
    if (trueLevel > P.lagStart) s.pumps[standby].run = true;
    if (trueLevel < P.lagStop && s.pumps[standby].run && !s.pumps[standby].manual) s.pumps[standby].run = false;

    // Valve: follows command at 5 %/s unless the actuator has failed.
    if (s.faults.valveStuck) {
      if (s.valve.stuck === null) s.valve.stuck = 30;
      s.valve.pos += (s.valve.stuck - s.valve.pos) * 0.3;
    } else {
      s.valve.stuck = null;
      const d = s.valve.cmd - s.valve.pos;
      s.valve.pos += Math.sign(d) * Math.min(Math.abs(d), 5 * dt);
    }
    const valveCap = P.valveCapacity * Math.pow(Math.max(0, s.valve.pos) / 100, 1.5);

    // Pumps.
    let demand = 0;
    const lowLevelCav = Math.max(0, Math.min(1, (8 - trueLevel) / 6));
    for (const id of ['P-101', 'P-102']) {
      const p = s.pumps[id];
      const target = p.run ? s.pid.op : 0;
      const d = target - p.speed;
      p.speed += Math.sign(d) * Math.min(Math.abs(d), P.vfdRamp * dt);
      if (!p.run && p.speed < 0.5) p.speed = 0;
      if (s.faults.bearing && id === s.bearingPump && p.speed > 0) p.wear = Math.min(1, p.wear + dt / 14400);
      let cav = 0;
      if (s.faults.cavitation && id === s.cavPump) cav = 1;
      cav = Math.max(cav, p.speed > 0 ? lowLevelCav : 0);
      p.cav = cav;
      const sp = p.speed / 100;
      p.flowRaw = p.speed > 0 ? P.pumpQmax * Math.max(0, (sp - P.minSpeed) / (1 - P.minSpeed)) * (1 - 0.3 * cav) : 0;
      demand += p.flowRaw;
    }
    const restriction = demand > valveCap && demand > 0 ? valveCap / demand : 1;
    let qout = 0;
    for (const id of ['P-101', 'P-102']) {
      const p = s.pumps[id];
      const sp = p.speed / 100;
      p.flow = p.flowRaw * restriction;
      qout += p.flow;
      if (p.speed > 0) {
        const load = 0.55 + 0.45 * restriction;
        p.amp = 14 + 84 * Math.pow(sp, 3) * load * (1 - 0.18 * p.cav) + noise(s, 0.6 + 4 * p.cav);
        p.vib = 1.5 + 0.7 * sp + 6.6 * p.cav + 6.2 * p.wear + noise(s, 0.08 + 0.9 * p.cav);
      } else {
        p.amp = 0;
        p.vib = Math.max(0, noise(s, 0.03) + 0.05);
      }
      const tss = p.speed > 0 ? P.ambient + 20 + 50 * Math.pow(p.amp / P.ratedCurrent, 2) + 48 * p.wear : P.ambient + 4;
      p.temp += ((tss - p.temp) * dt) / 600;
    }

    // Mass balance on the true volume.
    s.volume += ((s.inflow - qout) * dt) / 3600;
    s.volume = Math.max(0, Math.min(P.wellVolume * 1.02, s.volume));

    // Discharge pressure: pump head, throttling against a restricted valve, cavitation noise.
    const maxSp = Math.max(s.pumps['P-101'].speed, s.pumps['P-102'].speed) / 100;
    const cavMax = Math.max(s.pumps['P-101'].cav, s.pumps['P-102'].cav);
    let pt = 0.6 + 3.4 * maxSp * maxSp * (1 - 0.35 * cavMax) + 1.6 * (1 - restriction) + noise(s, 0.03 + 0.28 * cavMax);
    if (maxSp === 0) pt = 0.6 + noise(s, 0.02);

    s.meas = {
      'LT-101': pv,
      'LIC-101.SP': s.pid.sp,
      'LIC-101.OP': s.pid.op,
      'FT-101': s.inflow + noise(s, 2),
      'FT-102': qout + noise(s, 2),
      'PT-102': Math.max(0, pt),
      'XV-103.CMD': s.valve.cmd,
      'XV-103.POS': s.valve.pos,
    };
    for (const id of ['P-101', 'P-102']) {
      const p = s.pumps[id];
      s.meas[id + '.SPD'] = p.speed;
      s.meas[id + '.AMP'] = Math.max(0, p.amp);
      s.meas[id + '.TMP'] = p.temp;
      s.meas[id + '.VIB'] = Math.max(0, p.vib);
    }
    s.meas['P-101.RUN'] = s.pumps['P-101'].speed > 0 ? 1 : 0;
    s.meas['P-102.RUN'] = s.pumps['P-102'].speed > 0 ? 1 : 0;
    s.meas['LIC-101.MODE'] = s.pid.mode;
    s.meas['DUTY'] = s.duty;
    s.trueLevel = trueLevel;
    return s.meas;
  }

  function setFault(s, name, on) {
    if (!(name in s.faults)) throw new Error('Unknown scenario ' + name);
    s.faults[name] = on;
    if (name === 'badTuning' && on) {
      s.pid.kp = 15;
      s.pid.ti = 20;
      s.pid.sp = Math.min(75, s.pid.sp + 5); // the retune happened alongside a setpoint bump
    }
    if (name === 'surge' && on) s.surgeT = 0;
    if (name === 'cavitation' && on) s.cavPump = s.duty;     // the fault stays with the pump it started on
    if (name === 'bearing' && on) s.bearingPump = s.duty;
    if (!on) clearFaultEffects(s, name);
  }

  function clearFaultEffects(s, name) {
    if (name === 'drift') s.lt.drift = 0;
    if (name === 'bearing') for (const p of Object.values(s.pumps)) p.wear = 0;
    if (name === 'surge') s.surgeT = -1;
  }

  // Operator commands. Returns a short description, or throws with a reason.
  function command(s, action, params = {}) {
    switch (action) {
      case 'set_setpoint': {
        const v = Number(params.value);
        if (!(v >= 20 && v <= 80)) throw new Error('Setpoint must be between 20 and 80 %');
        s.pid.sp = v;
        return `LIC-101 setpoint set to ${v.toFixed(1)} %`;
      }
      case 'set_tuning': {
        const kp = Number(params.kp), ti = Number(params.ti);
        if (!(kp >= 0.1 && kp <= 20)) throw new Error('Kp must be between 0.1 and 20');
        if (!(ti >= 10 && ti <= 3000)) throw new Error('Ti must be between 10 and 3000 s');
        s.pid.kp = kp;
        s.pid.ti = ti;
        s.faults.badTuning = false;
        return `LIC-101 tuning set to Kp ${kp}, Ti ${ti} s`;
      }
      case 'set_mode': {
        if (params.mode !== 'AUTO' && params.mode !== 'MAN') throw new Error('Mode must be AUTO or MAN');
        s.pid.mode = params.mode;
        delete s.pid.lastErr;
        return `LIC-101 switched to ${params.mode}`;
      }
      case 'set_output': {
        const v = Number(params.value);
        if (s.pid.mode !== 'MAN') throw new Error('Put LIC-101 in MAN before setting the output');
        if (!(v >= 0 && v <= 100)) throw new Error('Output must be between 0 and 100 %');
        s.pid.op = v;
        return `LIC-101 output set to ${v.toFixed(0)} %`;
      }
      case 'swap_duty': {
        const old = s.duty;
        const next = old === 'P-101' ? 'P-102' : 'P-101';
        s.duty = next;
        s.pumps[next].run = true;
        s.pumps[next].manual = false;
        s.pumps[old].run = false;
        s.pumps[old].manual = false;
        return `Duty pump changed from ${old} to ${next}`;
      }
      case 'start_pump':
      case 'stop_pump': {
        const p = s.pumps[params.pump];
        if (!p) throw new Error('Pump must be P-101 or P-102');
        const run = action === 'start_pump';
        if (!run && params.pump === s.duty) throw new Error('Swap duty before stopping the duty pump');
        p.run = run;
        p.manual = run;
        return `${params.pump} ${run ? 'started' : 'stopped'}`;
      }
      case 'set_valve': {
        const v = Number(params.value);
        if (!(v >= 0 && v <= 100)) throw new Error('Valve command must be between 0 and 100 %');
        s.valve.cmd = v;
        return `XV-103 commanded to ${v.toFixed(0)} %`;
      }
      default:
        throw new Error('Unknown action ' + action);
    }
  }

  // Repairs land when a work order is completed in the field.
  function repair(s, equipment) {
    const fixed = [];
    for (const [name, sc] of Object.entries(SCENARIOS)) {
      const target = name === 'cavitation' ? s.cavPump : name === 'bearing' ? s.bearingPump : sc.equipment;
      if (target === equipment && s.faults[name] && name !== 'surge' && name !== 'badTuning') {
        s.faults[name] = false;
        clearFaultEffects(s, name);
        fixed.push(sc.title);
      }
    }
    if (equipment === 'P-101' || equipment === 'P-102') {
      s.pumps[equipment].wear = 0;
    }
    return fixed;
  }

  function clone(s) {
    const c = JSON.parse(JSON.stringify(s, (k, v) => (k === '_rand' ? undefined : v)));
    c._rand = rng((s.seed * 31 + Math.floor(s.t)) >>> 0);
    return c;
  }

  LW.PLANT = PLANT;
  LW.TAGS = TAGS;
  LW.SCENARIOS = SCENARIOS;
  LW.Sim = { create, step, setFault, command, repair, clone, rng };
})();
