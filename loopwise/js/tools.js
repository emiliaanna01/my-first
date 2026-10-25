// The agent's tools. Both the LLM agent and the built-in reasoner call these, so the trace looks the same.
// Read tools are free to call. Nothing here changes the plant: actions are only *proposed* for an operator.
(function () {
  const LW = (globalThis.LW = globalThis.LW || {});
  const { Sim, History, Alarms, Detect, KB, TAGS, PLANT } = LW;

  const r = (x, d = 2) => (typeof x === 'number' ? Math.round(x * 10 ** d) / 10 ** d : x);

  function clock(t) {
    const s = Math.floor(6 * 3600 + t) % 86400; // the shift starts at 06:00
    return [s / 3600, (s % 3600) / 60, s % 60].map((x) => String(Math.floor(x)).padStart(2, '0')).join(':');
  }

  function createEnv(seed = 7) {
    const env = { sim: Sim.create(seed), hist: History.create(), alarms: Alarms.create(), approvals: [], workOrders: [], nextId: 1 };
    History.record(env.hist, env.sim.t, env.sim.meas);
    return env;
  }

  // One simulated second: step the plant, record history, evaluate alarms. Returns newly raised alarms.
  function tick(env) {
    const m = Sim.step(env.sim);
    History.record(env.hist, env.sim.t, m);
    return Alarms.evaluate(env.alarms, env.sim.t, m);
  }

  const ACTIONS = {
    set_setpoint: 'Change LIC-101 setpoint. params: { value: 20-80 (%) }',
    set_tuning: 'Change LIC-101 PI tuning. params: { kp: 0.1-20, ti: 10-3000 (s) }',
    set_mode: 'Switch LIC-101 between AUTO and MAN. params: { mode: "AUTO"|"MAN" }',
    set_output: 'Set LIC-101 output in MAN. params: { value: 0-100 (%) }',
    swap_duty: 'Make the standby pump duty and stop the old duty pump. params: {}',
    start_pump: 'Start a pump alongside the duty pump. params: { pump: "P-101"|"P-102" }',
    stop_pump: 'Stop the non-duty pump. params: { pump }',
    set_valve: 'Command XV-103 position. params: { value: 0-100 (%) }',
  };

  const SPECS = [
    { name: 'get_plant_snapshot', description: 'Current value of every tag, controller settings, duty pump and alarm count.', parameters: { type: 'object', properties: {} } },
    { name: 'get_tag_history', description: 'Statistics and a downsampled trend for one tag over the last N minutes (max 120).',
      parameters: { type: 'object', properties: { tag: { type: 'string', enum: Object.keys(TAGS) }, minutes: { type: 'number' } }, required: ['tag'] } },
    { name: 'get_active_alarms', description: 'Active and unacknowledged alarms with ISA-18.2 priority (1 critical to 4 low).', parameters: { type: 'object', properties: {} } },
    { name: 'run_diagnostics', description: 'Run the analytics checks (loop oscillation, mass balance, pump curve, pressure noise, valve discrepancy, vibration and temperature trends with time-to-limit, inflow). Returns findings and rule-engine candidate causes to verify.',
      parameters: { type: 'object', properties: {} } },
    { name: 'search_knowledge_base', description: 'Search site SOPs, equipment data and standards. Cite the returned document IDs.',
      parameters: { type: 'object', properties: { query: { type: 'string' } }, required: ['query'] } },
    { name: 'recommend_tuning', description: 'Compute SIMC PI tuning for LIC-101 from the station model. Returns Kp, Ti and the model used.',
      parameters: { type: 'object', properties: { closed_loop_time_constant_s: { type: 'number', description: 'Desired closed-loop time constant, 60-600 s (default 150)' } } } },
    { name: 'simulate_what_if', description: 'Run the digital twin forward from the current state with and without the given actions, and compare level, pump speed swing, vibration, temperature and alarms.',
      parameters: { type: 'object', properties: {
        actions: { type: 'array', items: { type: 'object', properties: { action: { type: 'string', enum: Object.keys(ACTIONS) }, params: { type: 'object' } }, required: ['action'] } },
        minutes: { type: 'number', description: 'Horizon, 5-120 (default 30)' } }, required: ['actions'] } },
    { name: 'propose_action', description: 'Queue a control action for the operator to approve. It is NOT executed until a person approves it. Actions: ' + Object.entries(ACTIONS).map(([k, v]) => `${k}: ${v}`).join('; '),
      parameters: { type: 'object', properties: { action: { type: 'string', enum: Object.keys(ACTIONS) }, params: { type: 'object' }, reason: { type: 'string' } }, required: ['action', 'reason'] } },
    { name: 'create_work_order', description: 'Raise a maintenance work order in the CMMS for field work the control system cannot do.',
      parameters: { type: 'object', properties: {
        equipment: { type: 'string', description: 'Tag, e.g. P-101, LT-101, XV-103' }, priority: { type: 'string', enum: ['P1', 'P2', 'P3', 'P4'] },
        title: { type: 'string' }, description: { type: 'string', description: 'Symptom with measured values, suspected cause, SOP and parts' } },
        required: ['equipment', 'priority', 'title', 'description'] } },
  ];

  function snapshot(env) {
    const m = env.sim.meas;
    const tags = {};
    for (const [k, def] of Object.entries(TAGS)) tags[k] = { value: r(m[k]), unit: def.unit, desc: def.desc };
    return {
      station: PLANT.name, time: clock(env.sim.t), tags,
      pumps: { duty: env.sim.duty, 'P-101': m['P-101.RUN'] ? 'running' : 'stopped', 'P-102': m['P-102.RUN'] ? 'running' : 'stopped' },
      controller: { tag: 'LIC-101', mode: env.sim.pid.mode, sp: r(env.sim.pid.sp), kp: env.sim.pid.kp, ti_s: env.sim.pid.ti },
      active_alarms: Alarms.active(env.alarms).filter((a) => a.active).length,
      pending_approvals: env.approvals.filter((a) => a.status === 'pending').length,
    };
  }

  function tagHistory(env, { tag, minutes = 30 }) {
    if (!TAGS[tag]) return { error: `Unknown tag ${tag}. Known tags: ${Object.keys(TAGS).join(', ')}` };
    const secs = Math.max(1, Math.min(120, Number(minutes) || 30)) * 60;
    const st = History.stats(env.hist, tag, secs);
    const s = History.series(env.hist, tag, secs);
    const step = Math.max(1, Math.floor(s.v.length / 16));
    const points = [];
    for (let i = 0; i < s.v.length; i += step) points.push([clock(s.t[i]), r(s.v[i])]);
    return { tag, unit: TAGS[tag].unit, minutes: secs / 60, stats: st && { min: r(st.min), max: r(st.max), mean: r(st.mean), last: r(st.last), trend_per_hour: r(st.slopePerHour), noise: r(st.jitter, 3) }, points };
  }

  function activeAlarms(env) {
    const pri = { 1: 'critical', 2: 'high', 3: 'medium', 4: 'low' };
    return Alarms.active(env.alarms).map((a) => ({ id: a.id, priority: `${a.pri} ${pri[a.pri]}`, message: a.msg, state: a.active ? (a.acked ? 'active, acknowledged' : 'active, unacknowledged') : 'cleared, unacknowledged', since: clock(a.raisedAt), value: r(a.value) }));
  }

  function diagnostics(env) {
    const findings = Detect.runChecks(env.hist, PLANT, env.sim.meas);
    return {
      findings: findings.map((f) => ({ id: f.id, severity: f.severity, equipment: f.equipment, title: f.title, detail: f.detail })),
      candidate_causes: Detect.candidateCauses(findings).map((c) => ({ cause: c.cause, equipment: c.equipment, confidence: c.confidence, sop: c.sop, based_on: c.because })),
      note: findings.length ? 'Candidate causes come from rules. Verify them against tag history before concluding.' : 'All checks normal.',
    };
  }

  function tuning(env, args = {}) {
    const tc = Math.max(60, Math.min(600, Number(args.closed_loop_time_constant_s) || 150));
    const running = (env.sim.meas['P-101.RUN'] || 0) + (env.sim.meas['P-102.RUN'] || 0) || 1;
    const t = Detect.recommendTuning(PLANT, 1, tc);
    return { ...t, current: { kp: env.sim.pid.kp, ti: env.sim.pid.ti }, pumps_running: running,
      note: 'Tuned for one pump. With two pumps the process gain doubles, which these settings tolerate.' };
  }

  function summarise(sim, hist, alarms) {
    const lv = History.stats(hist, 'LT-101', 1e9), op = History.stats(hist, 'LIC-101.OP', 1e9);
    const osc = Detect.loopOscillation(hist, Math.min(900, hist.t[hist.t.length - 1] - hist.t[0]));
    const vib = Math.max(History.stats(hist, 'P-101.VIB', 1e9).max, History.stats(hist, 'P-102.VIB', 1e9).max);
    const tmp = Math.max(History.stats(hist, 'P-101.TMP', 1e9).max, History.stats(hist, 'P-102.TMP', 1e9).max);
    return {
      level: { min: r(lv.min, 1), max: r(lv.max, 1), end: r(lv.last, 1) },
      true_level_end: r(sim.trueLevel, 1),
      pump_speed: { min: r(op.min, 0), max: r(op.max, 0), swing: osc ? r(osc.opAmplitude, 0) : null, oscillating: osc ? osc.oscillating : false },
      max_vibration: r(vib), max_motor_temp: r(tmp, 1),
      vibration_end: r(Math.max(sim.meas['P-101.VIB'], sim.meas['P-102.VIB'])),
      alarms_raised: [...new Set(alarms.events.filter((e) => e.kind === 'alarm').map((e) => e.text.split(' ')[0]))],
    };
  }

  function whatIf(env, { actions = [], minutes = 30 }) {
    const secs = Math.max(5, Math.min(120, Number(minutes) || 30)) * 60;
    const run = (apply) => {
      const s = Sim.clone(env.sim);
      const h = History.create(2, 4000), a = Alarms.create();
      const applied = [];
      if (apply) for (const act of actions) {
        try { applied.push(Sim.command(s, act.action, act.params || {})); }
        catch (e) { return { error: `${act.action}: ${e.message}` }; }
      }
      for (let i = 0; i < secs; i++) {
        const m = Sim.step(s);
        History.record(h, s.t, m);
        Alarms.evaluate(a, s.t, m);
      }
      return { applied, ...summarise(s, h, a) };
    };
    const withActions = run(true);
    if (withActions.error) return { error: withActions.error };
    return { horizon_minutes: secs / 60, without_actions: run(false), with_actions: withActions,
      note: 'Digital twin of the station with current faults included. The twin cannot see faults it has not been told about.' };
  }

  function propose(env, { action, params = {}, reason = '' }) {
    if (!ACTIONS[action]) return { error: `Unknown action. Use one of ${Object.keys(ACTIONS).join(', ')}` };
    try { Sim.command(Sim.clone(env.sim), action, params); }       // dry run for limits and interlocks
    catch (e) { return { error: `Rejected by guardrails: ${e.message}` }; }
    const dup = env.approvals.find((a) => a.status === 'pending' && a.action === action && JSON.stringify(a.params) === JSON.stringify(params));
    if (dup) return { id: dup.id, status: 'already pending', note: 'The same action is already waiting for the operator.' };
    const item = { id: 'A-' + env.nextId++, action, params, reason, status: 'pending', at: env.sim.t };
    env.approvals.push(item);
    Alarms.log(env.alarms, env.sim.t, 'agent', `Copilot proposed ${describe(item)}`);
    return { id: item.id, status: 'pending operator approval', note: 'Tell the operator what you proposed and why. Do not say it has been done.' };
  }

  function describe(a) {
    const p = a.params || {};
    switch (a.action) {
      case 'set_setpoint': return `LIC-101 setpoint → ${p.value} %`;
      case 'set_tuning': return `LIC-101 tuning → Kp ${p.kp}, Ti ${p.ti} s`;
      case 'set_mode': return `LIC-101 → ${p.mode}`;
      case 'set_output': return `LIC-101 output → ${p.value} %`;
      case 'swap_duty': return 'Swap duty pump';
      case 'start_pump': return `Start ${p.pump}`;
      case 'stop_pump': return `Stop ${p.pump}`;
      case 'set_valve': return `XV-103 → ${p.value} %`;
      default: return a.action;
    }
  }

  function workOrder(env, { equipment, priority = 'P3', title, description }) {
    if (!equipment || !title) return { error: 'equipment and title are required' };
    const open = env.workOrders.find((w) => w.status === 'open' && w.equipment === equipment);
    if (open) return { id: open.id, status: 'already open', note: `Work order ${open.id} is already open for ${equipment}.` };
    const wo = { id: 'WO-' + (24100 + env.nextId++), equipment, priority, title, description: description || '', status: 'open', at: env.sim.t };
    env.workOrders.push(wo);
    Alarms.log(env.alarms, env.sim.t, 'workorder', `${wo.id} raised: ${priority} ${equipment} ${title}`);
    return { id: wo.id, status: 'open' };
  }

  function call(env, name, args = {}) {
    switch (name) {
      case 'get_plant_snapshot': return snapshot(env);
      case 'get_tag_history': return tagHistory(env, args);
      case 'get_active_alarms': { const a = activeAlarms(env); return a.length ? a : { alarms: 'none' }; }
      case 'run_diagnostics': return diagnostics(env);
      case 'search_knowledge_base': { const res = KB.search(args.query || ''); return res.length ? res : { results: 'nothing found' }; }
      case 'recommend_tuning': return tuning(env, args);
      case 'simulate_what_if': return whatIf(env, args);
      case 'propose_action': return propose(env, args);
      case 'create_work_order': return workOrder(env, args);
      default: return { error: `Unknown tool ${name}` };
    }
  }

  // Operator decisions on the copilot's proposals and work orders.
  function decide(env, id, approve) {
    const a = env.approvals.find((x) => x.id === id && x.status === 'pending');
    if (!a) return null;
    if (!approve) {
      a.status = 'rejected';
      Alarms.log(env.alarms, env.sim.t, 'operator', `Operator rejected ${a.id}: ${describe(a)}`);
      return a;
    }
    try {
      a.result = Sim.command(env.sim, a.action, a.params);
      a.status = 'done';
      Alarms.log(env.alarms, env.sim.t, 'operator', `Operator approved ${a.id}: ${a.result}`);
    } catch (e) {
      a.status = 'failed';
      a.result = e.message;
      Alarms.log(env.alarms, env.sim.t, 'operator', `${a.id} failed: ${e.message}`);
    }
    return a;
  }

  function completeWorkOrder(env, id) {
    const w = env.workOrders.find((x) => x.id === id && x.status === 'open');
    if (!w) return null;
    w.status = 'done';
    const fixed = Sim.repair(env.sim, w.equipment);
    Alarms.log(env.alarms, env.sim.t, 'workorder', `${w.id} completed in the field${fixed.length ? ': ' + fixed.join(', ') + ' fixed' : ''}`);
    return { wo: w, fixed };
  }

  LW.Tools = { SPECS, ACTIONS, createEnv, tick, call, describe, decide, completeWorkOrder, clock, snapshot };
})();
