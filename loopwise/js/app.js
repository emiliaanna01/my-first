// UI glue: runs the station in real time, draws the HMI and drives the copilot console.
(function () {
  const { Tools, Sim, Alarms, Agent, SCENARIOS, Detect, PLANT, History } = LW;
  const $ = (id) => document.getElementById(id);
  const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  const store = {
    get(k, d) { try { const v = localStorage.getItem('loopwise.' + k); return v == null ? d : JSON.parse(v); } catch (e) { return d; } },
    set(k, v) { try { localStorage.setItem('loopwise.' + k, JSON.stringify(v)); } catch (e) { /* storage blocked */ } },
  };

  let env = Tools.createEnv(7);
  let speed = 30, carry = 0;
  let cfg = Object.assign({ provider: 'builtin', baseUrl: '', model: '', key: '' }, store.get('cfg', {}));
  let busy = false, lastAuto = -1e9, autoQueue = null;
  const seenCauses = new Set(), candidateSeen = new Set();
  let chatHistory = [];

  // ---------- Mimic ----------
  const W = { x: 132, y: 92, w: 196, h: 206 };
  function vbox(id, x, y, tag, unit, w = 96) {
    return `<g><rect class="vbox" id="b-${id}" x="${x}" y="${y}" width="${w}" height="36" rx="3"/>
      <text class="tag" x="${x + 6}" y="${y + 12}">${tag}</text>
      <text class="val" id="v-${id}" x="${x + 6}" y="${y + 29}">–</text>
      <text class="unit" x="${x + w - 6}" y="${y + 29}" text-anchor="end">${unit}</text></g>`;
  }
  function pumpGroup(id, cy) {
    const by = cy - 26;
    return `<path class="pipe" id="suc-${id}" d="M330 ${cy} H378"/>
      <path class="pipe" id="dis-${id}" d="M422 ${cy} H480"/>
      <circle class="pump-body" id="pb-${id}" cx="400" cy="${cy}" r="21"/>
      <polygon class="pump-tri" points="392,${cy - 11} 392,${cy + 11} 412,${cy}"/>
      <text class="lbl-big" x="400" y="${cy + 38}" text-anchor="middle">${id}</text>
      <text class="duty" id="duty-${id}" x="400" y="${cy + 50}" text-anchor="middle"></text>
      ${vbox(id + '.SPD', 500, by, 'SPEED', '%', 66)}
      ${vbox(id + '.AMP', 570, by, 'CURRENT', 'A', 66)}
      ${vbox(id + '.VIB', 640, by, 'VIB', 'mm/s', 72)}
      ${vbox(id + '.TMP', 716, by, 'WINDING', '°C', 74)}`;
  }
  function buildMimic() {
    const ticks = [[90, 'HH'], [80, 'H'], [25, 'L'], [10, 'LL']].map(([v, l]) => {
      const y = W.y + W.h * (1 - v / 100);
      return `<line class="tick" x1="${W.x - 8}" x2="${W.x}" y1="${y}" y2="${y}"/><text class="tick-l" x="${W.x - 11}" y="${y + 3}" text-anchor="end">${l}</text>`;
    }).join('');
    $('mimic').innerHTML = `<svg class="mimic" viewBox="0 0 800 330" role="img" aria-label="Lift Station 3 process mimic">
      <text class="lbl" x="10" y="60">FROM SEWER NETWORK</text>
      <path class="pipe flow" d="M10 70 H170 V92"/>
      ${vbox('FT-101', 10, 12, 'FT-101 INFLOW', 'm³/h', 104)}
      <rect class="vessel" x="${W.x - 2}" y="${W.y - 2}" width="${W.w + 4}" height="${W.h + 4}"/>
      <rect class="liquid" id="liquid" x="${W.x}" y="${W.y + W.h / 2}" width="${W.w}" height="${W.h / 2}"/>
      <line class="sp-line" id="spline" x1="${W.x}" x2="${W.x + W.w}" y1="0" y2="0"/>
      ${ticks}
      <text class="lbl-big" x="${W.x + W.w / 2}" y="${W.y + W.h + 22}" text-anchor="middle">WET WELL · 60 m³</text>
      <line class="tick" x1="290" x2="290" y1="54" y2="${W.y - 2}"/>
      ${vbox('LT-101', 236, 18, 'LT-101 LEVEL', '%', 104)}
      ${pumpGroup('P-101', 190)}
      ${pumpGroup('P-102', 270)}
      <path class="pipe" id="hdr" d="M480 270 V120 H770"/>
      <g id="valve"><polygon class="valve" id="valveA" points="540,108 540,132 562,120"/><polygon class="valve" id="valveB" points="584,108 584,132 562,120"/>
        <line class="tick" x1="562" x2="562" y1="120" y2="96"/><rect class="vbox" x="550" y="88" width="24" height="8" rx="1"/></g>
      ${vbox('XV-103.POS', 516, 40, 'XV-103 POSITION', '%', 116)}
      ${vbox('PT-102', 640, 40, 'PT-102', 'bar', 72)}
      ${vbox('FT-102', 640, 130, 'FT-102 DISCHARGE', 'm³/h', 130)}
      <polygon points="770,112 788,120 770,128" fill="var(--equip)"/>
      <text class="lbl" x="788" y="104" text-anchor="end">TO TREATMENT WORKS</text>
    </svg>`;
  }

  const fmtTag = {
    'FT-101': 0, 'FT-102': 0, 'LT-101': 1, 'PT-102': 2, 'XV-103.POS': 0,
    'P-101.SPD': 0, 'P-101.AMP': 0, 'P-101.VIB': 2, 'P-101.TMP': 1, 'P-102.SPD': 0, 'P-102.AMP': 0, 'P-102.VIB': 2, 'P-102.TMP': 1,
  };
  function renderMimic() {
    const m = env.sim.meas;
    for (const [tag, d] of Object.entries(fmtTag)) {
      const el = $('v-' + tag);
      if (el) el.textContent = (m[tag] ?? 0).toFixed(d);
    }
    const lv = Math.max(0, Math.min(100, m['LT-101']));
    const lq = $('liquid');
    lq.setAttribute('y', W.y + W.h * (1 - lv / 100));
    lq.setAttribute('height', W.h * (lv / 100));
    const spy = W.y + W.h * (1 - env.sim.pid.sp / 100);
    $('spline').setAttribute('y1', spy); $('spline').setAttribute('y2', spy);
    let anyFlow = false;
    for (const id of ['P-101', 'P-102']) {
      const run = m[id + '.RUN'];
      anyFlow = anyFlow || run;
      $('pb-' + id).classList.toggle('run', !!run);
      for (const p of ['suc-', 'dis-']) { $(p + id).classList.toggle('flow', !!run); $(p + id).classList.toggle('off', !run); }
      $('duty-' + id).textContent = env.sim.duty === id ? 'DUTY' : 'STANDBY';
    }
    $('hdr').classList.toggle('flow', m['FT-102'] > 5); $('hdr').classList.toggle('off', !(m['FT-102'] > 5));
    const open = m['XV-103.POS'] > 5, fault = Math.abs(m['XV-103.CMD'] - m['XV-103.POS']) > 10;
    for (const v of ['valveA', 'valveB']) { $(v).classList.toggle('open', open); $(v).classList.toggle('fault', fault); }
    // Alarm colour on the value box of the tag in alarm (highest priority wins).
    const worst = {};
    for (const a of Alarms.active(env.alarms)) if (a.active) worst[a.tag] = Math.min(worst[a.tag] || 9, a.pri);
    for (const tag of Object.keys(fmtTag)) {
      const b = $('b-' + tag);
      if (b) b.setAttribute('class', 'vbox' + (worst[tag] && worst[tag] <= 3 ? ' p' + worst[tag] : ''));
    }
    $('clock').textContent = Tools.clock(env.sim.t);
  }

  // ---------- Trends ----------
  function css(name) { return getComputedStyle(document.documentElement).getPropertyValue(name).trim(); }
  function drawTrend(id, lines, lo, hi, refs = []) {
    const cv = $(id);
    const dpr = window.devicePixelRatio || 1;
    const w = cv.clientWidth, h = cv.clientHeight;
    if (!w) return;
    if (cv.width !== Math.round(w * dpr)) { cv.width = Math.round(w * dpr); cv.height = Math.round(h * dpr); }
    const g = cv.getContext('2d');
    g.setTransform(dpr, 0, 0, dpr, 0, 0);
    g.clearRect(0, 0, w, h);
    const padL = 30, padB = 14, span = 1800;
    const end = env.sim.t, start = end - span;
    const X = (t) => padL + ((t - start) / span) * (w - padL - 4);
    const Y = (v) => 4 + (1 - (v - lo) / (hi - lo)) * (h - padB - 6);
    g.font = '10px ' + css('--font-data');
    g.fillStyle = css('--ink-2');
    g.strokeStyle = css('--line');
    g.lineWidth = 1;
    for (let i = 0; i <= 2; i++) {
      const v = lo + ((hi - lo) * i) / 2, y = Y(v);
      g.globalAlpha = 0.6; g.beginPath(); g.moveTo(padL, y); g.lineTo(w - 4, y); g.stroke(); g.globalAlpha = 1;
      g.textAlign = 'right'; g.fillText(String(+v.toFixed(1)), padL - 4, y + 3);
    }
    g.textAlign = 'center';
    for (let m = 0; m <= 30; m += 10) g.fillText(m === 30 ? 'now' : `-${30 - m}m`, Math.min(w - 14, Math.max(padL + 10, X(start + m * 60))), h - 2);
    for (const r of refs) {
      g.strokeStyle = css(r.color); g.setLineDash([3, 3]); g.beginPath(); g.moveTo(padL, Y(r.v)); g.lineTo(w - 4, Y(r.v)); g.stroke(); g.setLineDash([]);
    }
    for (const ln of lines) {
      const s = History.series(env.hist, ln.tag, span);
      if (s.v.length < 2) continue;
      g.strokeStyle = css(ln.color); g.lineWidth = ln.width || 1.6;
      if (ln.dash) g.setLineDash(ln.dash);
      g.beginPath();
      for (let i = 0; i < s.v.length; i++) {
        const x = X(s.t[i]), y = Y(Math.max(lo, Math.min(hi, s.v[i])));
        i ? g.lineTo(x, y) : g.moveTo(x, y);
      }
      g.stroke(); g.setLineDash([]);
      const lx = X(s.t[s.t.length - 1]), lyv = Y(Math.max(lo, Math.min(hi, s.v[s.v.length - 1])));
      g.fillStyle = css(ln.color); g.beginPath(); g.arc(lx, lyv, 2.5, 0, 7); g.fill();
    }
  }
  function renderTrends() {
    const m = env.sim.meas;
    drawTrend('tLT', [{ tag: 'LIC-101.SP', color: '--accent', dash: [5, 4], width: 1.4 }, { tag: 'LT-101', color: '--ink' }], 0, 100, [{ v: 90, color: '--p1' }, { v: 10, color: '--p1' }]);
    drawTrend('tOP', [{ tag: 'LIC-101.OP', color: '--ink' }], 0, 100);
    drawTrend('tPT', [{ tag: 'PT-102', color: '--ink' }], 0, 6, [{ v: 4.4, color: '--p2' }]);
    drawTrend('tVB', [{ tag: 'P-102.VIB', color: '--equip' }, { tag: 'P-101.VIB', color: '--ink' }], 0, 12, [{ v: 4.5, color: '--p3' }, { v: 7.1, color: '--p2' }]);
    $('nLT').textContent = `${m['LT-101'].toFixed(1)} / SP ${env.sim.pid.sp.toFixed(0)}`;
    $('nOP').textContent = m['LIC-101.OP'].toFixed(0);
    $('nPT').textContent = m['PT-102'].toFixed(2);
    $('nVB').textContent = `${m['P-101.VIB'].toFixed(1)} / ${m['P-102.VIB'].toFixed(1)}`;
  }

  // ---------- Alarms ----------
  let alarmSig = '';
  function renderAlarms() {
    const list = Alarms.active(env.alarms);
    const counts = [0, 0, 0, 0, 0];
    for (const a of list) if (a.active) counts[a.pri]++;
    for (let p = 1; p <= 4; p++) $('c' + p).textContent = counts[p];
    const sig = list.map((a) => a.id + a.active + a.acked).join('|');
    if (sig === alarmSig) return;
    alarmSig = sig;
    $('alarmList').innerHTML = list.length ? list.map((a) => `<div class="alarm-row ${a.acked ? '' : 'unack'} ${a.active ? '' : 'rtn'}">
        <span class="glyph p${a.pri}">${a.pri}</span>
        <span class="t mono">${Tools.clock(a.raisedAt)}</span>
        <span class="tagc mono">${esc(a.id)}</span>
        <span class="msg">${esc(a.msg)}${a.active ? '' : ' · returned to normal'}</span>
        <span class="val mono">${typeof a.value === 'number' ? a.value.toFixed(1) : ''}</span>
        ${a.acked ? '<span class="note">ACK</span>' : `<button type="button" class="btn small" data-ack="${esc(a.id)}">Ack</button>`}
      </div>`).join('') : '<div class="alarm-empty">No active alarms.</div>';
  }
  $('alarmList').addEventListener('click', (e) => {
    const id = e.target.closest('[data-ack]')?.dataset.ack;
    if (id) { Alarms.ack(env.alarms, env.sim.t, id); renderAlarms(); }
  });
  $('ackPage').addEventListener('click', () => {
    for (const a of Alarms.active(env.alarms)) if (!a.acked) Alarms.ack(env.alarms, env.sim.t, a.id);
    renderAlarms();
  });

  // ---------- Faceplate ----------
  function renderFace() {
    const s = env.sim, m = s.meas;
    $('fPV').textContent = m['LT-101'].toFixed(1) + ' %';
    $('fSP').textContent = s.pid.sp.toFixed(1) + ' %';
    $('fOPbar').style.width = s.pid.op.toFixed(1) + '%';
    $('fOPbar').title = s.pid.op.toFixed(0) + ' %';
    $('fTune').textContent = `Kp ${s.pid.kp}  ·  Ti ${s.pid.ti} s`;
    $('fDuty').textContent = s.duty;
    for (const b of $('mode').querySelectorAll('button')) b.setAttribute('aria-pressed', String(b.dataset.mode === s.pid.mode));
    const fill = (id, v) => { if (document.activeElement !== $(id)) $(id).value = v; };
    fill('spIn', Math.round(s.pid.sp));
    fill('opIn', Math.round(s.pid.op));
    fill('kpIn', s.pid.kp);
    fill('tiIn', s.pid.ti);
  }
  function operator(action, params) {
    try {
      const text = Sim.command(env.sim, action, params);
      Alarms.log(env.alarms, env.sim.t, 'operator', 'Operator: ' + text);
      faceMsg(text);
    } catch (e) { faceMsg(e.message, true); }
    renderFace();
  }
  function faceMsg(text, err) { const el = $('faceMsg'); el.textContent = text; el.className = 'face-msg' + (err ? ' err' : ''); }
  $('mode').addEventListener('click', (e) => { const m = e.target.dataset.mode; if (m && m !== env.sim.pid.mode) operator('set_mode', { mode: m }); });
  $('swap').addEventListener('click', () => operator('swap_duty', {}));
  $('spForm').addEventListener('submit', (e) => {
    e.preventDefault();
    const sp = Number($('spIn').value);
    if (sp !== Math.round(env.sim.pid.sp)) operator('set_setpoint', { value: sp });
    if (env.sim.pid.mode === 'MAN') operator('set_output', { value: Number($('opIn').value) });
  });
  $('tuneForm').addEventListener('submit', (e) => { e.preventDefault(); operator('set_tuning', { kp: Number($('kpIn').value), ti: Number($('tiIn').value) }); });

  // ---------- Scenarios ----------
  function buildScenarios() {
    $('scen').innerHTML = Object.entries(SCENARIOS).map(([k, s]) => `<button type="button" data-scen="${k}" aria-pressed="false"><b>${esc(s.title)}</b><span>${esc(s.blurb)}</span></button>`).join('');
  }
  function renderScenarios() {
    const on = [];
    for (const b of $('scen').querySelectorAll('button')) {
      const active = !!env.sim.faults[b.dataset.scen];
      b.setAttribute('aria-pressed', String(active));
      if (active) on.push(SCENARIOS[b.dataset.scen].title);
    }
    $('scenNote').textContent = on.length ? 'Active: ' + on.join(', ') + '.' : 'Plant healthy.';
  }
  $('scen').addEventListener('click', (e) => {
    const k = e.target.closest('[data-scen]')?.dataset.scen;
    if (!k) return;
    const on = !env.sim.faults[k];
    Sim.setFault(env.sim, k, on);
    Alarms.log(env.alarms, env.sim.t, 'demo', `Demo scenario ${on ? 'started' : 'stopped'}: ${SCENARIOS[k].title}`);
    renderScenarios();
  });
  $('reset').addEventListener('click', () => {
    env = Tools.createEnv(7 + Math.floor(Math.random() * 1000));
    seenCauses.clear(); candidateSeen.clear(); alarmSig = ''; autoQueue = null; chatHistory = [];
    addNote('Station reset to healthy steady state. Approvals and work orders cleared.');
    renderAll();
  });

  // ---------- Copilot console ----------
  const LABELS = {
    get_plant_snapshot: 'Read all tags', get_tag_history: 'Read trend', get_active_alarms: 'Read alarms', run_diagnostics: 'Run diagnostics',
    search_knowledge_base: 'Search SOPs', recommend_tuning: 'Compute tuning', simulate_what_if: 'Test on digital twin', propose_action: 'Propose action',
    create_work_order: 'Raise work order',
  };
  function md(src) {
    const inline = (s) => esc(s).replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>').replace(/(^|[\s(])\*([^*\s][^*]*?)\*(?=[\s).,;:!?]|$)/g, '$1<em>$2</em>').replace(/`([^`]+)`/g, '<code>$1</code>');
    const special = /^(#{1,4}\s|\||\s*[-*]\s|\s*\d+[.)]\s)/;
    const lines = String(src).split('\n');
    let html = '', i = 0;
    while (i < lines.length) {
      const l = lines[i];
      if (!l.trim()) { i++; continue; }
      if (/^#{1,4}\s/.test(l)) { html += `<h3>${inline(l.replace(/^#+\s/, ''))}</h3>`; i++; continue; }
      if (/^\|/.test(l)) {
        const rows = [];
        while (i < lines.length && /^\|/.test(lines[i])) rows.push(lines[i++]);
        const cells = (r) => r.trim().replace(/^\||\|$/g, '').split('|').map((c) => c.trim());
        const body = rows.filter((r) => !/^\|[\s|:-]+\|?$/.test(r.trim()));
        html += '<div class="tbl"><table>' + body.map((r, k) => '<tr>' + cells(r).map((c) => (k === 0 ? `<th>${inline(c)}</th>` : `<td>${inline(c)}</td>`)).join('') + '</tr>').join('') + '</table></div>';
        continue;
      }
      const list = (re, tag) => {
        const items = [];
        while (i < lines.length && re.test(lines[i])) items.push(lines[i++].replace(re, ''));
        html += `<${tag}>` + items.map((x) => `<li>${inline(x)}</li>`).join('') + `</${tag}>`;
      };
      if (/^\s*[-*]\s/.test(l)) { list(/^\s*[-*]\s/, 'ul'); continue; }
      if (/^\s*\d+[.)]\s/.test(l)) { list(/^\s*\d+[.)]\s/, 'ol'); continue; }
      const p = [];
      while (i < lines.length && lines[i].trim() && !special.test(lines[i])) p.push(lines[i++]);
      html += `<p>${p.map(inline).join('<br>')}</p>`;
    }
    return html;
  }

  const chat = $('pane-chat');
  function scrollChat() { chat.scrollTop = chat.scrollHeight; }
  function addUser(text) {
    const d = document.createElement('div');
    d.className = 'msg user'; d.textContent = text;
    chat.appendChild(d); scrollChat();
  }
  function addNote(text, err) {
    const d = document.createElement('div');
    d.className = 'note' + (err ? ' err' : ''); d.textContent = text;
    chat.appendChild(d); scrollChat();
  }
  function addBot(autoReason) {
    const d = document.createElement('div');
    d.className = 'msg bot';
    d.innerHTML = `<div class="who">Loopwise${autoReason ? `<span class="auto">· auto-investigation: ${esc(autoReason)}</span>` : ''}</div><div class="trace"></div><div class="answer"></div>`;
    chat.appendChild(d); scrollChat();
    const trace = d.querySelector('.trace'), answer = d.querySelector('.answer');
    return {
      event(e) {
        if (e.type === 'tool') {
          const det = document.createElement('details');
          const args = Object.keys(e.args || {}).length ? JSON.stringify(e.args) : '';
          let res = JSON.stringify(e.result, null, 1);
          if (res.length > 4000) res = res.slice(0, 4000) + '\n…';
          det.innerHTML = `<summary><span>${esc(LABELS[e.name] || e.name)}</span><span class="fn">${esc(e.name)}</span><span class="args">${esc(args)}</span></summary><pre>${esc(res)}</pre>`;
          trace.appendChild(det);
          renderSide();
        } else if (e.type === 'thought') {
          const t = document.createElement('div'); t.className = 'thought'; t.textContent = e.text; trace.appendChild(t);
        } else if (e.type === 'answer') {
          answer.innerHTML = md(e.text);
        }
        if (!trace.children.length) trace.hidden = true; else trace.hidden = false;
        scrollChat();
      },
      note(text, err) { const n = document.createElement('div'); n.className = 'note' + (err ? ' err' : ''); n.textContent = text; d.appendChild(n); },
    };
  }

  function setBusy(b) {
    busy = b;
    $('brain').classList.toggle('busy', b);
    $('askBtn').disabled = b;
    $('brainName').textContent = b ? 'Working…' : brainLabel();
  }
  function brainLabel() {
    if (cfg.provider === 'builtin') return 'Built-in reasoner';
    return `${Agent.PROVIDERS[cfg.provider]?.label.replace(/ \(.*\)/, '') || 'LLM'} · ${cfg.model}`;
  }

  async function ask(question, autoReason) {
    if (busy) return;
    setBusy(true);
    if (!autoReason) addUser(question);
    const turn = addBot(autoReason);
    const onEvent = (e) => turn.event(e);
    try {
      if (cfg.provider === 'builtin') {
        await Agent.runBuiltin(env, question, onEvent);
      } else {
        try {
          const text = await Agent.runLLM(env, cfg, chatHistory, question, onEvent);
          chatHistory.push({ role: 'user', content: question }, { role: 'assistant', content: text });
          chatHistory = chatHistory.slice(-8);
        } catch (err) {
          const why = err instanceof TypeError ? 'could not be reached (network or browser security blocked it)' : err.message;
          turn.note(`The model API ${why}. Answering with the built-in reasoner instead.`, true);
          await Agent.runBuiltin(env, question, onEvent);
        }
      }
    } catch (err) {
      turn.note('Something went wrong: ' + err.message, true);
    } finally {
      setBusy(false);
      renderSide();
    }
  }

  $('askForm').addEventListener('submit', (e) => {
    e.preventDefault();
    const q = $('askIn').value.trim();
    if (!q) return;
    $('askIn').value = '';
    ask(q);
  });
  $('prompts').addEventListener('click', (e) => { if (e.target.tagName === 'BUTTON') ask(e.target.textContent); });

  // Auto-investigation: new high-priority alarms, or a new cause the analytics find before any alarm.
  function considerAuto(raised) {
    if (!$('autoInv').checked) return;
    const serious = raised.filter((a) => a.pri <= 2);
    // Wait 90 s of station time after the alarm so the analytics have data to work with.
    if (serious.length && !autoQueue) autoQueue = { at: env.sim.t + 90, reason: `${serious[0].id} ${serious[0].msg}`, q: `New alarm ${serious[0].id} (${serious[0].msg}). What's wrong and what should we do?` };
  }
  function scanCauses() {
    if (env.hist.t.length < 120) return;
    const causes = Detect.candidateCauses(Detect.runChecks(env.hist, PLANT, env.sim.meas));
    const now = new Set(causes.map((c) => c.sop));
    // A cause must show up in two scans in a row before it triggers an investigation.
    for (const c of causes) {
      if (!seenCauses.has(c.sop) && candidateSeen.has(c.sop) && !autoQueue && $('autoInv').checked) autoQueue = { at: env.sim.t, reason: `analytics flagged ${c.cause}`, q: `Analytics flagged: ${c.cause}. Investigate and prepare actions.` };
    }
    for (const s of [...seenCauses]) if (!now.has(s)) seenCauses.delete(s);
    for (const s of now) if (candidateSeen.has(s)) seenCauses.add(s);
    candidateSeen.clear();
    for (const s of now) candidateSeen.add(s);
  }
  function runAuto() {
    if (!autoQueue || busy || !$('autoInv').checked || env.sim.t < autoQueue.at) return;
    const cooldown = cfg.provider === 'builtin' ? 12000 : 60000;
    if (performance.now() - lastAuto < cooldown) return;
    lastAuto = performance.now();
    const job = autoQueue; autoQueue = null;
    ask(job.q, job.reason);
  }
  $('autoInv').addEventListener('change', () => { store.set('auto', $('autoInv').checked); if (!$('autoInv').checked) autoQueue = null; });

  // ---------- Side panes ----------
  function renderSide() {
    const pend = env.approvals.filter((a) => a.status === 'pending');
    const openWO = env.workOrders.filter((w) => w.status === 'open');
    $('bApprovals').textContent = pend.length || '';
    $('bWO').textContent = openWO.length || '';
    $('pane-approvals').innerHTML = env.approvals.length ? env.approvals.slice().reverse().map((a) => `<div class="card">
        <div class="ttl"><b>${esc(Tools.describe(a))}</b><span class="id">${a.id} · ${Tools.clock(a.at)}</span><span class="status ${a.status}">${a.status}</span></div>
        <p>${esc(a.reason)}</p>
        ${a.result ? `<p class="note">${esc(a.result)}</p>` : ''}
        ${a.status === 'pending' ? `<div class="inline"><button type="button" class="btn primary small" data-approve="${a.id}">Approve and execute</button><button type="button" class="btn small" data-reject="${a.id}">Reject</button></div>` : ''}
      </div>`).join('') : '<div class="empty">Nothing waiting. Control changes the copilot suggests appear here, and nothing runs until you approve it.</div>';
    $('pane-workorders').innerHTML = env.workOrders.length ? env.workOrders.slice().reverse().map((w) => `<div class="card">
        <div class="ttl"><span class="prio ${w.priority}">${w.priority}</span><b>${esc(w.equipment)} · ${esc(w.title)}</b><span class="id">${w.id} · ${Tools.clock(w.at)}</span><span class="status ${w.status === 'open' ? 'pending' : 'done'}">${w.status}</span></div>
        <p>${esc(w.description)}</p>
        ${w.status === 'open' ? `<div class="inline"><button type="button" class="btn small" data-complete="${w.id}">Mark completed in the field</button><span class="note">Demo: the technician fixes the fault.</span></div>` : ''}
      </div>`).join('') : '<div class="empty">No work orders. Field jobs the copilot raises (repairs, calibration) appear here.</div>';
    renderLog();
  }
  function renderLog() {
    if ($('pane-log').hidden) return;
    const ev = env.alarms.events.slice(-150).reverse();
    $('pane-log').innerHTML = ev.length ? `<table class="log">${ev.map((e) => `<tr><td>${Tools.clock(e.t)}</td><td class="k">${esc(e.kind)}</td><td>${esc(e.text)}</td></tr>`).join('')}</table>` : '<div class="empty">No events yet.</div>';
  }
  document.querySelector('.copilot').addEventListener('click', (e) => {
    const t = e.target.closest('button');
    if (!t) return;
    if (t.dataset.approve || t.dataset.reject) {
      const a = Tools.decide(env, t.dataset.approve || t.dataset.reject, !!t.dataset.approve);
      if (a) addNote(`${a.id} ${a.status === 'done' ? 'approved: ' + a.result : a.status === 'rejected' ? 'rejected by operator.' : 'failed: ' + a.result}`, a.status === 'failed');
      renderSide(); renderFace();
    }
    if (t.dataset.complete) {
      const r = Tools.completeWorkOrder(env, t.dataset.complete);
      if (r) addNote(`${r.wo.id} completed in the field.${r.fixed.length ? ' Fixed: ' + r.fixed.join(', ') + '.' : ''}`);
      renderSide(); renderScenarios();
    }
    if (t.dataset.tab) {
      for (const b of document.querySelectorAll('.tabs button')) b.setAttribute('aria-selected', String(b === t));
      for (const p of ['chat', 'approvals', 'workorders', 'log']) $('pane-' + p).hidden = p !== t.dataset.tab;
      $('chatInput').hidden = t.dataset.tab !== 'chat';
      renderSide();
    }
  });

  // ---------- Settings ----------
  function fillSettings() {
    $('sProvider').innerHTML = Object.entries(Agent.PROVIDERS).map(([k, p]) => `<option value="${k}">${esc(p.label)}</option>`).join('');
    $('sProvider').value = cfg.provider;
    $('sBase').value = cfg.baseUrl; $('sModel').value = cfg.model; $('sKey').value = cfg.key;
    settingsHelp();
  }
  function settingsHelp() {
    const p = Agent.PROVIDERS[$('sProvider').value];
    const builtin = $('sProvider').value === 'builtin';
    for (const id of ['sBase', 'sModel', 'sKey']) $(id).disabled = builtin;
    $('sHelp').innerHTML = builtin ? 'The built-in reasoner runs the same tools with fixed expert rules. Pick an LLM to let a model reason freely.'
      : p.keyUrl ? `Get a free key at <a href="${p.keyUrl}" target="_blank" rel="noopener">${p.keyUrl.replace('https://', '')}</a>.`
      : $('sProvider').value === 'ollama' ? 'Start Ollama with OLLAMA_ORIGINS=* so the browser can reach it. No key needed.' : 'Any OpenAI-compatible endpoint with tool calling.';
  }
  $('sProvider').addEventListener('change', () => {
    const p = Agent.PROVIDERS[$('sProvider').value];
    if ($('sProvider').value !== 'custom') { $('sBase').value = p.baseUrl; $('sModel').value = p.model; }
    settingsHelp();
  });
  $('openSettings').addEventListener('click', () => { fillSettings(); $('settings').showModal(); });
  $('settings').addEventListener('close', () => {
    if ($('settings').returnValue !== 'save') return;
    cfg = { provider: $('sProvider').value, baseUrl: $('sBase').value.trim(), model: $('sModel').value.trim(), key: $('sKey').value.trim() };
    store.set('cfg', cfg);
    chatHistory = [];
    $('brainName').textContent = brainLabel();
    addNote(`Copilot brain: ${brainLabel()}.`);
  });

  // ---------- Speed and main loop ----------
  $('speed').addEventListener('click', (e) => {
    const b = e.target.closest('[data-speed]');
    if (!b) return;
    speed = Number(b.dataset.speed);
    for (const x of $('speed').querySelectorAll('button')) x.setAttribute('aria-pressed', String(x === b));
  });

  function renderAll() { renderMimic(); renderTrends(); renderAlarms(); renderFace(); renderScenarios(); renderSide(); }

  let frame = 0;
  setInterval(() => {
    carry += speed / 10;
    const steps = Math.floor(carry);
    carry -= steps;
    const raised = [];
    for (let i = 0; i < steps; i++) raised.push(...Tools.tick(env));
    if (raised.length) considerAuto(raised);
    frame++;
    if (steps || frame % 5 === 0) { renderMimic(); renderAlarms(); renderFace(); }
    if (frame % 5 === 0) renderTrends();
    if (frame % 10 === 0) { if (steps) scanCauses(); renderLog(); }
    runAuto();
  }, 100);

  // ---------- Boot ----------
  buildMimic();
  buildScenarios();
  $('autoInv').checked = store.get('auto', true);
  $('brainName').textContent = brainLabel();
  // A short head start so the trends have something to show.
  for (let i = 0; i < 900; i++) Tools.tick(env);
  renderAll();
  addBot(null).event({ type: 'answer', text: `I'm watching **Lift Station 3**: two duty/standby pumps, a 60 m³ wet well and the LIC-101 level loop.\n\n- Start a **demo scenario** on the left. I investigate new alarms by myself, and I catch some faults before any alarm fires.\n- Or ask me anything about the station.\n- Control changes I suggest wait in **Approvals**. Nothing runs until you approve it.\n\n${cfg.provider === 'builtin' ? 'Running on the built-in reasoner. Connect a free LLM in **Settings** to let a model reason over the same tools.' : 'Brain: **' + brainLabel() + '**.'}` });
  window.addEventListener('resize', renderTrends);
})();
