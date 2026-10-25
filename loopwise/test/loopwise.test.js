// Run with: node --test loopwise/test/*.test.js
const test = require('node:test');
const assert = require('node:assert');
for (const f of ['sim', 'detect', 'kb', 'tools', 'agent']) require(`../js/${f}.js`);
const { Sim, Tools, Agent, Detect, PLANT } = globalThis.LW;

function station(fault, seconds, warm = 1800) {
  const env = Tools.createEnv(7);
  for (let i = 0; i < warm; i++) Tools.tick(env);
  if (fault) Sim.setFault(env.sim, fault, true);
  for (let i = 0; i < seconds; i++) Tools.tick(env);
  return env;
}
const topCause = (env) => Tools.call(env, 'run_diagnostics').candidate_causes[0];

test('a healthy station raises no alarms and no findings over 3 hours', () => {
  const env = station(null, 3 * 3600);
  assert.deepStrictEqual(Tools.call(env, 'get_active_alarms'), { alarms: 'none' });
  assert.strictEqual(Tools.call(env, 'run_diagnostics').findings.length, 0);
});

const cases = [
  ['cavitation', 300, 'SOP-PMP-03'],
  ['drift', 900, 'SOP-INS-01'],
  ['valveStuck', 300, 'SOP-VLV-02'],
  ['badTuning', 900, 'SOP-CTL-01'],
  ['bearing', 3600, 'SOP-PMP-05'],
  ['surge', 600, 'SOP-OPS-04'],
];
for (const [fault, secs, sop] of cases) {
  test(`${fault}: the top candidate cause points to ${sop}`, () => {
    assert.strictEqual(topCause(station(fault, secs)).sop, sop);
  });
}

test('cavitation is not mistaken for bearing wear right after the alarm', () => {
  const env = station('cavitation', 90);
  const causes = Tools.call(env, 'run_diagnostics').candidate_causes.map((c) => c.sop);
  assert.ok(!causes.includes('SOP-PMP-05'), causes.join(','));
});

test('drift is caught before any alarm fires', () => {
  const env = station('drift', 600);
  assert.deepStrictEqual(Tools.call(env, 'get_active_alarms'), { alarms: 'none' });
  assert.strictEqual(topCause(env).sop, 'SOP-INS-01');
});

test('SIMC tuning stops the hunting on the twin', () => {
  const env = station('badTuning', 900);
  const rec = Detect.recommendTuning(PLANT);
  const w = Tools.call(env, 'simulate_what_if', { actions: [{ action: 'set_tuning', params: { kp: rec.kp, ti: rec.ti } }], minutes: 30 });
  assert.ok(w.without_actions.pump_speed.oscillating);
  assert.ok(!w.with_actions.pump_speed.oscillating);
});

test('proposals are guarded, wait for approval, and execute only when approved', () => {
  const env = station(null, 60);
  assert.match(Tools.call(env, 'propose_action', { action: 'set_setpoint', params: { value: 95 }, reason: 'x' }).error, /guardrails/);
  const p = Tools.call(env, 'propose_action', { action: 'set_setpoint', params: { value: 50 }, reason: 'buffer' });
  assert.strictEqual(env.sim.pid.sp, 60, 'nothing changes before approval');
  Tools.decide(env, p.id, true);
  assert.strictEqual(env.sim.pid.sp, 50);
});

test('completing a work order repairs the equipment in the field', () => {
  const env = station('cavitation', 120);
  const wo = Tools.call(env, 'create_work_order', { equipment: 'P-101', priority: 'P2', title: 'Clear intake', description: '' });
  Tools.completeWorkOrder(env, wo.id);
  assert.strictEqual(env.sim.faults.cavitation, false);
});

test('built-in reasoner answers an alarm question with an investigation, not a forecast', async () => {
  const env = station('cavitation', 300);
  const text = await Agent.runBuiltin(env, 'New alarm P-101.VIB.HH (P-101 vibration high-high). What is wrong?', () => {}, { fast: true });
  assert.match(text, /cavitating/);
  assert.ok(env.approvals.some((a) => a.action === 'swap_duty' && a.status === 'pending'));
});

test('LLM loop executes tool calls and returns the final answer', async () => {
  const env = station(null, 60);
  const replies = [
    { choices: [{ message: { content: null, tool_calls: [{ id: 'c1', type: 'function', function: { name: 'run_diagnostics', arguments: '{}' } }] } }] },
    { choices: [{ message: { content: '**Normal** – all checks passed.' } }] },
  ];
  const sent = [];
  globalThis.fetch = async (url, init) => { sent.push(JSON.parse(init.body)); return { ok: true, json: async () => replies.shift() }; };
  const events = [];
  const text = await Agent.runLLM(env, { baseUrl: 'https://example.test/v1', model: 'm', key: 'k' }, [], 'Status?', (e) => events.push(e));
  assert.strictEqual(text, '**Normal** – all checks passed.');
  assert.ok(events.some((e) => e.type === 'tool' && e.name === 'run_diagnostics'));
  assert.strictEqual(sent[1].messages.at(-1).role, 'tool');
  assert.ok(sent[0].tools.length >= 9);
});
