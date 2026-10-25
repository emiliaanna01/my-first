// Two brains behind the same tools:
//  - runLLM: a tool-calling loop against any OpenAI-compatible chat API (Groq, OpenRouter, Gemini, Ollama).
//  - runBuiltin: a deterministic reasoner that needs no key, so the demo works offline and for free.
(function () {
  const LW = (globalThis.LW = globalThis.LW || {});
  const { Tools, PLANT, Detect, History } = LW;

  const PROVIDERS = {
    builtin:    { label: 'Built-in reasoner (no key)', baseUrl: '', model: '' },
    groq:       { label: 'Groq (free tier)', baseUrl: 'https://api.groq.com/openai/v1', model: 'openai/gpt-oss-120b', keyUrl: 'https://console.groq.com/keys' },
    openrouter: { label: 'OpenRouter (free models)', baseUrl: 'https://openrouter.ai/api/v1', model: 'openrouter/free', keyUrl: 'https://openrouter.ai/settings/keys' },
    gemini:     { label: 'Google Gemini (free tier)', baseUrl: 'https://generativelanguage.googleapis.com/v1beta/openai', model: 'gemini-flash-latest', keyUrl: 'https://aistudio.google.com/apikey' },
    ollama:     { label: 'Ollama on this computer', baseUrl: 'http://localhost:11434/v1', model: 'qwen3:8b', keyUrl: '' },
    custom:     { label: 'Custom OpenAI-compatible', baseUrl: '', model: '' },
  };

  const SYSTEM = `You are Loopwise, the operations copilot for ${PLANT.name}, a municipal wastewater lift station. You support the control-room operator.

Rules:
- Ground every claim in tool results. Quote tag names and values with units.
- Investigate before concluding: run_diagnostics, read the history of the tags involved, and search the knowledge base. Cite SOP and document IDs.
- You cannot change the plant. Use propose_action for control changes; an operator approves them. Test a control change with simulate_what_if before proposing it, and report the result.
- Raise create_work_order for field work (repairs, calibration, inspection) with measured values, suspected cause, SOP and parts.
- Never acknowledge, shelve or suppress alarms. If overflow or dry-run is possible, say so first.
- Do not propose actions the evidence says will not help, and explain why.

Answer format (markdown, under 180 words unless asked for a report):
First line: **Normal**, **Attention** or **Action needed**, then one sentence.
**Cause** – your conclusion and confidence.
**Evidence** – 2-4 bullets with values.
**Done for you** – proposals (A-ids, waiting for approval) and work orders (WO-ids).
**Check in the field** – only if needed.
For a shift report use headings: Summary, Process, Alarms and events, Equipment health, Open items, Handover.`;

  // ---------- LLM agent ----------
  async function runLLM(env, cfg, history, question, onEvent, signal) {
    if (!cfg.baseUrl || !cfg.model) throw new Error('Set the API address and model in Settings.');
    const tools = Tools.SPECS.map((s) => ({ type: 'function', function: s }));
    const messages = [{ role: 'system', content: SYSTEM }, ...history.slice(-8), { role: 'user', content: question }];
    for (let round = 0; round < 10; round++) {
      const res = await fetch(cfg.baseUrl.replace(/\/$/, '') + '/chat/completions', {
        method: 'POST', signal,
        headers: { 'Content-Type': 'application/json', ...(cfg.key ? { Authorization: 'Bearer ' + cfg.key } : {}) },
        body: JSON.stringify({ model: cfg.model, messages, tools, tool_choice: 'auto', temperature: 0.2 }),
      });
      if (!res.ok) {
        let detail = '';
        try { detail = (await res.json()).error?.message || ''; } catch (e) { /* not json */ }
        throw new Error(`${res.status} from the model API${detail ? ': ' + detail : ''}`);
      }
      const data = await res.json();
      const msg = data.choices?.[0]?.message;
      if (!msg) throw new Error('The model API returned no message.');
      const calls = msg.tool_calls || [];
      messages.push({ role: 'assistant', content: msg.content || '', ...(calls.length ? { tool_calls: calls } : {}) });
      if (!calls.length) {
        onEvent({ type: 'answer', text: msg.content || '(no answer)' });
        return msg.content || '';
      }
      if (msg.content) onEvent({ type: 'thought', text: msg.content });
      for (const c of calls) {
        let args = {};
        try { args = c.function.arguments ? JSON.parse(c.function.arguments) : {}; } catch (e) { args = {}; }
        const result = Tools.call(env, c.function.name, args);
        onEvent({ type: 'tool', name: c.function.name, args, result });
        let content = JSON.stringify(result);
        if (content.length > 6000) content = content.slice(0, 6000) + '…(truncated)';
        messages.push({ role: 'tool', tool_call_id: c.id, name: c.function.name, content });
      }
    }
    const text = 'I stopped after 10 tool rounds without a conclusion. Ask again with a narrower question.';
    onEvent({ type: 'answer', text });
    return text;
  }

  // ---------- Built-in reasoner ----------
  const wait = (ms) => new Promise((res) => setTimeout(res, ms));

  function intent(q) {
    const s = q.toLowerCase();
    if (/report|handover|hand over|shift|summar/.test(s)) return 'report';
    if (/new alarm|flagged|wrong|why|investigat|diagnos|problem|fault/.test(s)) return 'investigate';
    if (/tun|pid|\bpi\b|oscillat|hunt|\bkp\b|\bti\b|loop/.test(s)) return 'tuning';
    if (/maint|predict|bearing|forecast|remaining|lifetime|wear|vibrat/.test(s)) return 'maintenance';
    if (/\bsop\b|procedure|how do i|how to|what is|what does|standard|iso/.test(s)) return 'kb';
    if (/status|how is|how's|overview|everything ok|all good/.test(s)) return 'status';
    return 'investigate';
  }

  const f1 = (x) => (x == null ? 'n/a' : Number(x).toFixed(1));
  const f0 = (x) => (x == null ? 'n/a' : Number(x).toFixed(0));

  async function runBuiltin(env, question, onEvent, opts = {}) {
    const pause = opts.fast ? 0 : 260;
    const use = async (name, args = {}) => {
      await wait(pause);
      const result = Tools.call(env, name, args);
      onEvent({ type: 'tool', name, args, result });
      return result;
    };
    const say = (text) => { onEvent({ type: 'answer', text }); return text; };
    const think = async (text) => { await wait(pause / 2); onEvent({ type: 'thought', text }); };

    const kind = intent(question);
    if (kind === 'report') return say(await shiftReport(env, use));
    if (kind === 'kb') {
      const res = await use('search_knowledge_base', { query: question });
      if (!Array.isArray(res)) return say('**Normal** – I found nothing in the site documents for that. Try naming the equipment or symptom.');
      const top = res[0];
      return say(`From **${top.id} ${top.title}**:\n\n${top.text}\n\n${res.length > 1 ? 'Also relevant: ' + res.slice(1).map((d) => `${d.id} ${d.title}`).join('; ') : ''}`);
    }

    const alarms = await use('get_active_alarms');
    const diag = await use('run_diagnostics');
    const causes = diag.candidate_causes || [];
    const alarmList = Array.isArray(alarms) ? alarms : [];

    if (kind === 'tuning') return say(await tuningAnswer(env, use, think, diag));
    if (kind === 'maintenance') return say(await maintenanceAnswer(env, use, diag));

    if (!causes.length) {
      const snap = await use('get_plant_snapshot');
      const t = snap.tags;
      const head = alarmList.length ? `**Attention** – ${alarmList.length} alarm(s) shown, but the analytics find no fault behind them.` : '**Normal** – the station is running inside its normal envelope.';
      return say(`${head}\n\n**Evidence**\n- LT-101 ${f1(t['LT-101'].value)} % against setpoint ${f1(snap.controller.sp)} %\n- Inflow ${f0(t['FT-101'].value)} m3/h, discharge ${f0(t['FT-102'].value)} m3/h at ${t['PT-102'].value} bar\n- Duty ${snap.pumps.duty}: vibration ${t[snap.pumps.duty + '.VIB'].value} mm/s, winding ${f1(t[snap.pumps.duty + '.TMP'].value)} degC\n- All ${diag.findings.length === 0 ? '' : 'critical '}checks passed: loop stability, mass balance, pump curve, pressure noise, valve tracking, trends.`);
    }

    if (kind === 'status') {
      const lines = causes.map((c) => `- ${c.cause} (${Math.round(c.confidence * 100)} %)`).join('\n');
      return say(`**Attention** – ${causes.length} issue(s) need a look.\n\n${lines}\n\nAsk *"What's wrong right now?"* and I will investigate and prepare actions.`);
    }

    const top = causes[0];
    await think(`Strongest candidate: ${top.cause}. Checking the trends before I commit to it.`);
    const handler = HANDLERS[top.sop] || generic;
    const body = await handler(env, use, think, top, diag);
    const others = causes.slice(1).filter((c) => c.sop !== top.sop);
    const also = others.length ? `\n\n**Also watching**\n${others.map((c) => `- ${c.cause} (${Math.round(c.confidence * 100)} %, ${c.sop})`).join('\n')}` : '';
    return say(body + also);
  }

  function findingText(diag, id) {
    const f = diag.findings.find((x) => x.id === id);
    return f ? f.detail : null;
  }

  function evidenceList(diag, ids) {
    return ids.map((id) => findingText(diag, id)).filter(Boolean).map((t) => '- ' + t).join('\n');
  }

  function compareLine(w) {
    const a = w.without_actions, b = w.with_actions;
    return `Twin, next ${w.horizon_minutes} min: without action level ${f1(a.level.min)}–${f1(a.level.max)} %, vibration ends at ${a.vibration_end} mm/s; with it level ${f1(b.level.min)}–${f1(b.level.max)} %, vibration ends at ${b.vibration_end} mm/s.`;
  }

  const HANDLERS = {
    'SOP-VLV-02': async (env, use, think, c, diag) => {
      const pos = await use('get_tag_history', { tag: 'XV-103.POS', minutes: 15 });
      const lv = await use('get_tag_history', { tag: 'LT-101', minutes: 15 });
      await use('search_knowledge_base', { query: 'SOP-VLV-02 valve stuck actuator' });
      await think('The valve is the restriction, so starting P-102 would only raise pressure. Field action is the fix.');
      const w = await use('simulate_what_if', { actions: [{ action: 'start_pump', params: { pump: env.sim.duty === 'P-101' ? 'P-102' : 'P-101' } }], minutes: 20 });
      const level = lv.stats.last;
      const wo = await use('create_work_order', { equipment: 'XV-103', priority: level > 80 ? 'P1' : 'P2', title: 'Discharge valve stuck, open by handwheel',
        description: `XV-103 position ${f0(pos.stats.last)} % against command 100 %. Discharge restricted, LT-101 at ${f1(level)} % and rising. Check actuator supply, torque switch and local/remote selector; open by handwheel. SOP-VLV-02.` });
      return `**Action needed** – XV-103 is stuck at ${f0(pos.stats.last)} %, so the station cannot discharge and the level is rising.\n\n**Cause** – Discharge valve actuator failure (${Math.round(c.confidence * 100)} %).\n\n**Evidence**\n${evidenceList(diag, ['valve_discrepancy', 'pump_underperforming', 'level_moving'])}\n\n**Done for you**\n- ${wo.id} ${level > 80 ? 'P1' : 'P2'} raised for a technician to open XV-103 by handwheel (SOP-VLV-02).\n- I did **not** propose starting the standby pump. On the twin it changes nothing: the level reaches ${f1(w.with_actions.level.max)} % within ${w.horizon_minutes} min either way, because the valve is the restriction.\n\n**Check in the field**\n- Actuator power, torque switch trip, local/remote selector.\n- At 90 % call the tanker contractor and inform the network control room.`;
    },

    'SOP-PMP-03': async (env, use, think, c, diag) => {
      const pump = c.equipment.startsWith('P-') ? c.equipment : env.sim.duty;
      await use('get_tag_history', { tag: pump + '.VIB', minutes: 15 });
      await use('get_tag_history', { tag: 'PT-102', minutes: 15 });
      await use('search_knowledge_base', { query: 'SOP-PMP-03 cavitation blocked intake' });
      const w = await use('simulate_what_if', { actions: [{ action: 'swap_duty' }], minutes: 20 });
      const p = await use('propose_action', { action: 'swap_duty', reason: `${pump} is cavitating: erratic pressure and vibration in ISO 10816 zone D. SOP-PMP-03 says swap duty and do not run it for more than 30 min.` });
      const wo = await use('create_work_order', { equipment: pump, priority: 'P2', title: 'Clear pump intake, inspect impeller',
        description: `${pump} cavitating: ${findingText(diag, 'vibration_erratic') || ''} ${findingText(diag, 'pressure_noise') || ''} Lift pump, clear rags from intake and impeller, check impeller wear. SOP-PMP-03.` });
      return `**Action needed** – ${pump} is cavitating. Every minute it runs like this damages the seal and bearings.\n\n**Cause** – Blocked intake or low suction on ${pump} (${Math.round(c.confidence * 100)} %).\n\n**Evidence**\n${evidenceList(diag, ['vibration_erratic', 'pressure_noise', 'pump_underperforming'])}\n\n**Done for you**\n- ${p.id} waiting for your approval: swap duty to the standby pump. ${compareLine(w)}\n- ${wo.id} P2 raised to clear the intake (SOP-PMP-03).\n\n**Check in the field**\n- Listen for gravel noise at ${pump}; confirm the wet well is above 20 %.`;
    },

    'SOP-INS-01': async (env, use, think, c, diag) => {
      await use('get_tag_history', { tag: 'LT-101', minutes: 30 });
      await use('get_tag_history', { tag: 'FT-102', minutes: 30 });
      await use('search_knowledge_base', { query: 'SOP-INS-01 level transmitter drift mass balance' });
      const long = Detect.massBalance(env.hist, PLANT, 3600);
      const offset = long ? (long.residualM3 / PLANT.wellVolume) * 100 : 0;
      const reads = offset > 0 ? 'high' : 'low';
      const sp = env.sim.pid.sp;
      await think(`The flows say the well has ${offset > 0 ? 'lost' : 'gained'} about ${f1(Math.abs(offset))} % that LT-101 did not see. LT-101 reads ${reads}, so the true level is near ${f1(sp - offset)} %.`);
      const newSp = Math.max(20, Math.min(80, Math.round(sp + offset)));
      let line = '';
      if (Math.abs(newSp - sp) >= 2) {
        const w = await use('simulate_what_if', { actions: [{ action: 'set_setpoint', params: { value: newSp } }], minutes: 20 });
        const p = await use('propose_action', { action: 'set_setpoint', params: { value: newSp }, reason: `Stopgap for LT-101 reading about ${f1(Math.abs(offset))} % ${reads}: brings the true level back toward ${f0(sp)} %. Confirm with the sight gauge first (SOP-INS-01).` });
        line = `- ${p.id} waiting for your approval: setpoint ${f0(sp)} → ${newSp} % as a stopgap, only after the sight gauge confirms. Twin: true level ends at ${w.with_actions.true_level_end} % instead of ${w.without_actions.true_level_end} %.\n`;
      }
      const wo = await use('create_work_order', { equipment: 'LT-101', priority: 'P2', title: 'Clean and recalibrate level transmitter',
        description: `LT-101 disagrees with the flow balance by about ${f1(Math.abs(offset))} % (reads ${reads}) and growing ${f1(Math.abs(long?.impliedLevelDriftPctPerHour))} %/h. Check the sensor face for foam or condensation, verify against the dip, recalibrate. SOP-INS-01.` });
      return `**Action needed** – LT-101 is not telling the truth. The loop looks perfect, but the real level is about ${f1(sp - offset)} %, not ${f1(env.sim.meas['LT-101'])} %.\n\n**Cause** – Level transmitter drift (${Math.round(c.confidence * 100)} %). A flowmeter error is the alternative.\n\n**Evidence**\n${evidenceList(diag, ['mass_balance'])}\n- Over the last hour the gap adds up to ${f1(long?.residualM3)} m3 (${f1(offset)} % of the well).\n\n**Done for you**\n${line}- ${wo.id} P2 raised for an instrument technician (SOP-INS-01).\n\n**Check in the field**\n- Read the local sight gauge or dip the well now. If it reads ${reads === 'high' ? 'low' : 'high'}, the ${reads === 'high' ? 'pumps are heading for dry-run' : 'well is heading for overflow'}.`;
    },

    'SOP-CTL-01': async (env, use, think, c, diag) => tuningAnswer(env, use, think, diag),

    'SOP-PMP-05': async (env, use, think, c, diag) => maintenanceAnswer(env, use, diag),

    'SOP-OPS-04': async (env, use, think, c, diag) => {
      const qin = await use('get_tag_history', { tag: 'FT-101', minutes: 30 });
      const lv = await use('get_tag_history', { tag: 'LT-101', minutes: 15 });
      await use('search_knowledge_base', { query: 'SOP-OPS-04 storm high inflow' });
      const standby = env.sim.duty === 'P-101' ? 'P-102' : 'P-101';
      const standbyRunning = env.sim.meas[standby + '.RUN'];
      const actions = [];
      if (!standbyRunning) actions.push({ action: 'start_pump', params: { pump: standby } });
      if (env.sim.pid.sp > 50) actions.push({ action: 'set_setpoint', params: { value: 50 } });
      const lines = [];
      if (actions.length) {
        const w = await use('simulate_what_if', { actions, minutes: 30 });
        for (const a of actions) {
          const p = await use('propose_action', { ...a, reason: a.action === 'start_pump' ? `Inflow ${f0(qin.stats.last)} m3/h exceeds one pump (${PLANT.pumpQmax} m3/h). SOP-OPS-04: start the standby early.` : 'SOP-OPS-04: lower the setpoint to gain buffer volume during the storm.' });
          lines.push(`- ${p.id} waiting for your approval: ${Tools.describe(a)}.`);
        }
        lines.push(`- ${compareLine(w)}`);
      } else lines.push('- Both pumps are already running and the setpoint is already low. Nothing more to change from here.');
      return `**Attention** – Storm inflow. No equipment fault; the station is short of capacity.\n\n**Cause** – Hydraulic overload (${Math.round(c.confidence * 100)} %).\n\n**Evidence**\n${evidenceList(diag, ['inflow_high', 'level_moving', 'output_saturated'])}\n- LT-101 peaked at ${f1(lv.stats.max)} % in the last 15 min.\n\n**Done for you**\n${lines.join('\n')}\n\n**Check in the field**\n- If both pumps reach 100 % and the level still rises, notify the network control room (SOP-OPS-04).`;
    },
  };

  async function generic(env, use, think, c, diag) {
    await use('search_knowledge_base', { query: c.cause });
    return `**Attention** – ${c.cause} (${Math.round(c.confidence * 100)} %).\n\n**Evidence**\n${diag.findings.map((f) => '- ' + f.detail).join('\n')}\n\nSee ${c.sop}.`;
  }

  async function tuningAnswer(env, use, think, diag) {
    const op = await use('get_tag_history', { tag: 'LIC-101.OP', minutes: 15 });
    const osc = Detect.loopOscillation(env.hist);
    const rec = await use('recommend_tuning', { closed_loop_time_constant_s: 150 });
    const cur = rec.current;
    const close = Math.abs(cur.kp - rec.kp) / rec.kp < 0.35 && Math.abs(cur.ti - rec.ti) / rec.ti < 0.5;
    if (!osc?.oscillating && close) {
      return `**Normal** – LIC-101 is stable and its tuning (Kp ${cur.kp}, Ti ${cur.ti} s) is close to the SIMC recommendation (Kp ${rec.kp}, Ti ${rec.ti} s).\n\n**Evidence**\n- Pump speed ${f0(op.stats.min)}–${f0(op.stats.max)} % over 15 min, no sustained oscillation.\n- Model: integrating gain ${rec.model.integratingGainPctPerSPerPct.toFixed(5)} %/s per %, deadtime ${rec.model.deadtimeS} s, target closed-loop time constant ${rec.closedLoopTimeConstantS} s.`;
    }
    await think(`Current Kp ${cur.kp}, Ti ${cur.ti} s. SIMC gives Kp ${rec.kp}, Ti ${rec.ti} s. Testing it on the twin first.`);
    const w = await use('simulate_what_if', { actions: [{ action: 'set_tuning', params: { kp: rec.kp, ti: rec.ti } }], minutes: 30 });
    const p = await use('propose_action', { action: 'set_tuning', params: { kp: rec.kp, ti: rec.ti }, reason: `LIC-101 is ${osc?.oscillating ? 'hunting' : 'off its design tuning'}. SIMC for the integrating level process (SOP-CTL-01), verified on the twin.` });
    await use('search_knowledge_base', { query: 'SOP-CTL-01 level loop tuning' });
    const a = w.without_actions.pump_speed, b = w.with_actions.pump_speed;
    return `**Attention** – LIC-101 is ${osc?.oscillating ? `hunting: pump speed swings ±${f0(osc.opAmplitude)} % every ${osc.periodS} s` : 'tuned far from its design values'}. That wears the VFD, couplings and seals.\n\n**Cause** – Tuning too aggressive for an integrating level process with ${rec.model.deadtimeS} s deadtime (Kp ${cur.kp}, Ti ${cur.ti} s).\n\n**Evidence**\n${osc?.oscillating ? '- ' + findingText(diag, 'loop_oscillation') + '\n' : ''}- SIMC (tc ${rec.closedLoopTimeConstantS} s): Kc = 1 / (k′(tc + θ)) = **${rec.kp}**, Ti = 4(tc + θ) = **${rec.ti} s**.\n- Twin, 30 min: pump speed swing ±${a.swing} % → ±${b.swing} %, level ${f1(w.with_actions.level.min)}–${f1(w.with_actions.level.max)} %.\n\n**Done for you**\n- ${p.id} waiting for your approval: Kp ${rec.kp}, Ti ${rec.ti} s (SOP-CTL-01).`;
  }

  async function maintenanceAnswer(env, use, diag) {
    const rows = [];
    let worst = null;
    const checks = Detect.runChecks(env.hist, PLANT, env.sim.meas);
    for (const pump of ['P-101', 'P-102']) {
      if (!env.sim.meas[pump + '.RUN']) { rows.push(`| ${pump} | standby | – | – | – |`); continue; }
      const vib = await use('get_tag_history', { tag: pump + '.VIB', minutes: 60 });
      const tmp = await use('get_tag_history', { tag: pump + '.TMP', minutes: 60 });
      const f = checks.find((x) => x.id === 'vibration_trend' && x.equipment === pump);
      const ev = f ? f.evidence : null;
      const etaD = ev && ev.etaZoneD_h != null ? `${f1(ev.etaZoneD_h)} h` : vib.stats.last > 7.1 ? 'now' : 'no trend';
      rows.push(`| ${pump} | ${vib.stats.last} mm/s | ${vib.stats.trend_per_hour > 0 ? '+' : ''}${vib.stats.trend_per_hour} mm/s/h | ${f1(tmp.stats.last)} degC | ${etaD} |`);
      if (f) worst = { pump, ev, vib, tmp };
    }
    const table = `| Pump | Vibration | Trend | Winding | Zone D (7.1) in |\n|---|---|---|---|---|\n${rows.join('\n')}`;
    if (!worst) {
      return `**Normal** – no pump shows a wear trend.\n\n${table}\n\nVibration limits per ISO 10816-3: zone C from 4.5 mm/s, zone D from 7.1 mm/s (DOC-STD-10816).`;
    }
    await use('search_knowledge_base', { query: 'SOP-PMP-05 bearing wear vibration trend' });
    const w = await use('simulate_what_if', { actions: [{ action: 'swap_duty' }], minutes: 60 });
    const p = await use('propose_action', { action: 'swap_duty', reason: `${worst.pump} vibration rising ${worst.vib.stats.trend_per_hour} mm/s per hour. Running the healthy pump slows the wear (SOP-PMP-05).` });
    const etaD = worst.ev.etaZoneD_h;
    const wo = await use('create_work_order', { equipment: worst.pump, priority: worst.vib.stats.last > 4.5 ? 'P2' : 'P3', title: 'Replace pump bearings before zone D',
      description: `${worst.pump} vibration ${worst.vib.stats.last} mm/s rising ${worst.vib.stats.trend_per_hour} mm/s/h; winding ${f1(worst.tmp.stats.last)} degC rising. Zone D forecast in ${f1(etaD)} h at current duty. Parts: SKF 6316-2Z/C3 bearing pair, mechanical seal kit. SOP-PMP-05.` });
    return `**Attention** – ${worst.pump} bearing wear is developing. At this rate it reaches ISO 10816 zone D in about **${f1(etaD)} h**.\n\n${table}\n\n**Cause** – Bearing wear: smooth, steady rise in vibration with the winding temperature climbing too. Cavitation would be noisy.\n\n**Done for you**\n- ${p.id} waiting for your approval: make the healthy pump duty. Twin, 60 min: vibration ends at ${w.with_actions.vibration_end} mm/s instead of ${w.without_actions.vibration_end} mm/s.\n- ${wo.id} ${worst.vib.stats.last > 4.5 ? 'P2' : 'P3'} raised with the bearing pair and seal kit, so parts arrive before zone D (SOP-PMP-05).`;
  }

  async function shiftReport(env, use) {
    const snap = await use('get_plant_snapshot');
    const lv = await use('get_tag_history', { tag: 'LT-101', minutes: 120 });
    const qo = await use('get_tag_history', { tag: 'FT-102', minutes: 120 });
    const diag = await use('run_diagnostics');
    const hours = Math.min(2, env.sim.t / 3600);
    const ev = env.alarms.events;
    const alarmsRaised = ev.filter((e) => e.kind === 'alarm');
    const notable = ev.filter((e) => ['operator', 'workorder', 'scenario'].includes(e.kind)).slice(-8);
    const openWO = env.workOrders.filter((w) => w.status === 'open');
    const pending = env.approvals.filter((a) => a.status === 'pending');
    const t = snap.tags;
    return `### Summary
${PLANT.name}, shift 06:00 to ${snap.time}. ${diag.candidate_causes.length ? `**${diag.candidate_causes.length} open issue(s)**: ${diag.candidate_causes.map((c) => c.cause).join('; ')}.` : 'No open process or equipment issues.'}

### Process
- Level ${f1(lv.stats.min)}–${f1(lv.stats.max)} % (mean ${f1(lv.stats.mean)} %), setpoint ${snap.controller.sp} %, LIC-101 in ${snap.controller.mode} (Kp ${snap.controller.kp}, Ti ${snap.controller.ti_s} s).
- Pumped about ${f0(qo.stats.mean * hours)} m3 in the last ${f1(hours)} h (mean ${f0(qo.stats.mean)} m3/h). Inflow now ${f0(t['FT-101'].value)} m3/h.
- Duty pump ${snap.pumps.duty}; P-101 ${snap.pumps['P-101']}, P-102 ${snap.pumps['P-102']}.

### Alarms and events
- ${alarmsRaised.length} alarm(s) raised this shift, ${snap.active_alarms} still active.
${notable.length ? notable.map((e) => `- ${Tools.clock(e.t)} ${e.text}`).join('\n') : '- No operator actions or work orders.'}

### Equipment health
- P-101: ${t['P-101.VIB'].value} mm/s, ${f1(t['P-101.TMP'].value)} degC. P-102: ${t['P-102.VIB'].value} mm/s, ${f1(t['P-102.TMP'].value)} degC.
${diag.findings.length ? diag.findings.map((f) => `- ${f.title}: ${f.detail}`).join('\n') : '- All analytics checks normal.'}

### Open items
${openWO.length ? openWO.map((w) => `- ${w.id} ${w.priority} ${w.equipment}: ${w.title}`).join('\n') : '- No open work orders.'}
${pending.length ? pending.map((a) => `- ${a.id} waiting for approval: ${Tools.describe(a)}`).join('\n') : '- No proposals waiting for approval.'}

### Handover
${diag.candidate_causes.length ? diag.candidate_causes.map((c) => `- Watch: ${c.cause}. Follow ${c.sop}.`).join('\n') : '- Normal operation. No special instructions.'}`;
  }

  LW.Agent = { PROVIDERS, SYSTEM, runLLM, runBuiltin, intent };
})();
