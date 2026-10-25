// Site knowledge base: SOPs, equipment data and standards the agent can search and cite.
// A real deployment loads the customer's own manuals here; these are written for Lift Station 3.
(function () {
  const LW = (globalThis.LW = globalThis.LW || {});

  const DOCS = [
    {
      id: 'DOC-STN-00', title: 'Lift Station 3 overview', tags: ['station', 'overview', 'process', 'design', 'capacity'],
      body: `Wet well 60 m3 (0-100 % on LT-101, ultrasonic, 15 s effective deadtime including damping and PLC scan).
Two identical submersible pumps P-101 and P-102 on VFDs, duty/standby. Each pump: 55 kW, rated 98 A, 320 m3/h at 100 % speed with the valve open; below 25 % speed it cannot beat the static head.
Discharge valve XV-103 (motorised, position feedback). Discharge flow FT-102 (magflow), inflow FT-101, discharge pressure PT-102.
Control: LIC-101 holds the level at setpoint by modulating the duty pump speed (direct acting PI). Normal setpoint 60 %, normal tuning Kp 3.4, Ti 600 s.
Hardwired lead/lag: the standby pump starts above 88 % true level (float) and stops below 55 %.
Normal inflow 140-220 m3/h with a daily pattern. Station capacity with both pumps: about 640 m3/h.`,
    },
    {
      id: 'DOC-ALM-00', title: 'Alarm philosophy (ISA-18.2)', tags: ['alarm', 'priority', 'isa-18.2', 'response', 'acknowledge'],
      body: `Priority 1 Critical: respond within 5 minutes; safety, environmental release or equipment destruction is imminent (LT-101 HH/LL, motor temperature HH).
Priority 2 High: respond within 15 minutes; loss of capacity or equipment damage likely (level H/L, pressure H, valve discrepancy, vibration HH, temperature H).
Priority 3 Medium: respond within 60 minutes; degraded operation (pressure L, vibration H, controller deviation or saturation).
Priority 4 Low: awareness only (standby pump running).
Operators acknowledge alarms; the copilot never acknowledges or shelves alarms on its own.`,
    },
    {
      id: 'SOP-PMP-03', title: 'Pump cavitation or blocked intake', tags: ['cavitation', 'pump', 'vibration', 'pressure', 'noise', 'rags', 'blockage', 'suction', 'flow low'],
      body: `Symptoms: discharge pressure erratic, vibration high and noisy (often over 7 mm/s), flow well below the pump curve for the speed, current lower than normal and unsteady. Gravel-like noise at the pump.
Likely causes: rags or debris at the intake (most common in wastewater), level too low (vortexing), worn impeller.
Immediate actions:
1. Swap duty to the standby pump to protect the bearings and seal.
2. Confirm wet well level is above 20 %; if low, raise the LIC-101 setpoint.
3. Do not run a cavitating pump for more than 30 minutes.
Maintenance: lift the pump, clear the intake and impeller, inspect impeller wear. Create a work order priority 2 (within 24 h).`,
    },
    {
      id: 'SOP-PMP-05', title: 'Bearing wear and rising vibration trend', tags: ['bearing', 'vibration', 'trend', 'temperature', 'predictive', 'maintenance', 'iso 10816'],
      body: `A steady upward vibration trend with a smooth signal, usually with rising winding temperature, points to bearing wear or misalignment.
Plan by the ISO 10816 zone forecast: in zone B (under 4.5 mm/s) schedule inspection; in zone C (4.5-7.1) plan a bearing change within 7 days and limit running hours; in zone D (over 7.1) stop the pump at the next opportunity.
Actions: make the healthy pump duty to slow the wear, raise a work order with the time-to-zone-D forecast, order bearings (SKF 6316-2Z/C3 pair and the mechanical seal kit) so parts arrive before zone D.
Do not grease a submersible pump bearing in the field.`,
    },
    {
      id: 'SOP-INS-01', title: 'Level transmitter drift (LT-101)', tags: ['level', 'transmitter', 'drift', 'calibration', 'ultrasonic', 'mass balance', 'lt-101', 'sensor'],
      body: `Ultrasonic transmitters drift with foam, condensation on the face or a fouled target.
Detection: compare the level change with the flow balance (inflow minus discharge). A growing gap while the controller looks perfectly at setpoint means the transmitter is lying, and the real level is moving away.
Danger: if LT-101 reads high, the true level falls and the pumps can run dry (cavitation and seal damage); if it reads low, the well can overflow.
Actions:
1. Read the local sight gauge or dip the well to get the true level.
2. If confirmed, compensate as a stopgap: when LT-101 reads high, raise the setpoint by the measured error so the true level returns to normal (when it reads low, lower it). The drift keeps growing, so recheck every hour, or put LIC-101 in MAN at a safe speed.
3. Raise a priority 2 work order for an instrument technician to clean and recalibrate LT-101.`,
    },
    {
      id: 'SOP-VLV-02', title: 'Discharge valve not following command (XV-103)', tags: ['valve', 'stuck', 'actuator', 'discrepancy', 'xv-103', 'position', 'pressure high'],
      body: `Symptoms: XV-103 position differs from command, discharge pressure high, flow low, the controller output saturates and the level rises.
Starting the standby pump does not help: the valve is the restriction, so more pumps only raise pressure.
Actions:
1. Dispatch a technician immediately (priority 1 if the level is above 80 %). Check actuator power, torque switch trip and the local/remote selector.
2. The actuator has a manual handwheel: open the valve by hand.
3. If the level reaches 90 %, call the tanker contractor and inform the upstream network (possible overflow report to the regulator).`,
    },
    {
      id: 'SOP-CTL-01', title: 'Level loop tuning (LIC-101)', tags: ['tuning', 'pid', 'pi', 'oscillation', 'hunting', 'kp', 'ti', 'simc', 'controller', 'lic-101'],
      body: `LIC-101 is an integrating process: with flows unbalanced the level ramps. Tune it as averaging level control: smooth pump speed matters more than holding the level exactly.
Model: integrating gain k' = Qmax per pump / 0.75 / 100 / 3600 / 60 m3 x 100 = 0.00198 %/s per % output (one pump). Deadtime theta about 20 s (15 s transmitter + 5 s filter).
SIMC rules: Kc = 1 / (k' (tc + theta)), Ti = 4 (tc + theta). With tc 150 s: Kc about 3.0, Ti about 680 s.
Symptoms of over-tight tuning: pump speed swinging 40-100 % every 2-3 minutes, level oscillating a few percent, extra motor heating and wear on VFDs and couplings.
Always simulate a tuning change before applying it, and apply it in AUTO with the level near setpoint.`,
    },
    {
      id: 'SOP-OPS-04', title: 'High inflow / storm event', tags: ['storm', 'inflow', 'rain', 'surge', 'overload', 'capacity', 'high level', 'lag'],
      body: `During storms inflow can exceed one pump's 320 m3/h. The standby pump starts automatically at 88 %.
Actions:
1. Start the standby pump early (above 75 %) rather than waiting for the float, to keep margin.
2. Lower the LIC-101 setpoint to 45-50 % before a forecast storm to gain buffer volume (about 6 m3 per 10 %).
3. If both pumps are at 100 % and the level still rises, notify the network control room and prepare the overflow procedure.
After the event, return to one duty pump and the normal setpoint.`,
    },
    {
      id: 'DOC-STD-10816', title: 'ISO 10816-3 vibration zones (group 2, flexible mount)', tags: ['iso 10816', 'vibration', 'zone', 'limits', 'mm/s'],
      body: `RMS velocity 10-1000 Hz. Zone A/B boundary 2.3 mm/s, B/C 4.5 mm/s, C/D 7.1 mm/s.
Zone A: newly commissioned. Zone B: unrestricted long-term operation. Zone C: not suitable for long-term continuous operation, plan repair. Zone D: severe enough to cause damage.
Alarm settings at this site: H at 4.5 (zone C), HH at 7.1 (zone D).`,
    },
    {
      id: 'DOC-CMMS-01', title: 'Work order priorities', tags: ['work order', 'cmms', 'maintenance', 'priority', 'dispatch'],
      body: `P1 emergency: dispatch now, call-out allowed. P2 urgent: within 24 hours. P3 planned: within 7 days. P4 routine: next scheduled visit.
A work order names the equipment tag, the symptom with measured values, the suspected cause, the SOP and parts needed.`,
    },
  ];

  function tokens(s) {
    return String(s).toLowerCase().replace(/[^a-z0-9.\- ]+/g, ' ').split(/\s+/).filter((w) => w.length > 1);
  }

  function search(query, limit = 3) {
    const q = tokens(query);
    const scored = DOCS.map((d) => {
      const title = d.title.toLowerCase(), tagStr = d.tags.join(' '), body = d.body.toLowerCase();
      let score = 0;
      for (const w of q) {
        if (d.id.toLowerCase() === w) score += 10;
        if (title.includes(w)) score += 3;
        if (tagStr.includes(w)) score += 2;
        if (body.includes(w)) score += 1;
      }
      return { d, score };
    }).filter((x) => x.score > 0);
    scored.sort((a, b) => b.score - a.score);
    return scored.slice(0, limit).map(({ d, score }) => ({ id: d.id, title: d.title, score, text: d.body }));
  }

  function get(id) {
    return DOCS.find((d) => d.id === id) || null;
  }

  LW.KB = { DOCS, search, get };
})();
