# Loopwise: how to show it and sell it

## The pitch in one line

*Loopwise is a copilot for control-room operators: it finds the cause of an alarm in seconds,
tests the fix on a digital twin, and hands the operator a one-click action, without ever touching the plant itself.*

## The problem it solves

- **Alarm floods.** An upset raises 10–50 alarms; the operator has to work out which one matters. ISA-18.2
  rationalisation helps, but someone still has to diagnose.
- **Knowledge walks out the door.** Senior operators and controls engineers retire. Their judgement
  ("a drifting ultrasonic reads high, check the sight gauge") lives in their heads, not in the SCADA.
- **Slow faults hide.** A drifting transmitter or a wearing bearing doesn't trip an alarm until it's expensive.
- **Bad loops cost money quietly.** Surveys of process plants keep finding that a large share of PID loops
  perform poorly. Hunting loops wear actuators and waste energy.

## Who buys

| Buyer | Why they care | How to reach them |
|---|---|---|
| **System integrators** (your best channel) | Sell it as a value-add on SCADA/PLC projects and service contracts | You already speak their language; offer white-label |
| **Water and wastewater utilities** | Many unmanned lift stations, small operator teams, overflow fines | Municipal tenders, regional water associations |
| **Food & beverage, pharma utilities** | Boilers, chillers, CIP, compressed air: same loops, same faults | Plant engineering managers |
| **Building automation / HVAC** | AHU and chiller plant loops hunt constantly | BMS contractors |
| **OEMs** (pump, blower, skid builders) | Ship a "smart" skid with built-in diagnostics | Product managers at local OEMs |

Start with whichever of these you already have contacts in. One reference customer is worth more than any deck.

## What you sell

1. **Demo** (free) – this repo. Show it live in 5 minutes (script in README).
2. **Pilot** (paid, 4–6 weeks) – connect one real unit **read-only**, load the customer's SOPs and alarm list,
   tune the checks to their equipment, run it beside the operators, measure.
3. **Subscription** – per site or per unit, including updates, new checks, and support.
4. **Services** – loop tuning audits, alarm rationalisation, SOP digitisation. The copilot makes these faster for you.

### Suggested pricing to test (adjust to your market)

| Offer | Price idea | Notes |
|---|---|---|
| Pilot, one unit | a fixed fee covering ~10–15 days of your engineering time | Credit it against the first year if they continue |
| Subscription, small site | monthly fee per station / unit | Lift stations, skids |
| Subscription, plant | per plant per year | Priced against one avoided failure or overflow |
| Integrator white-label | revenue share or per-deployment licence | They do the install, you supply the product |

Price on value: one avoided pump rebuild, overflow report or night call-out usually pays for a year.

## What to measure in a pilot

- Time from alarm to diagnosis (before vs. with the copilot).
- Faults caught before an alarm (drift, wear, hunting loops).
- Loops retuned and the reduction in actuator movement or energy.
- Operator rating of each suggestion (accepted / rejected) – the approvals log already records this.

## Taking it from demo to a real plant

| Step | What changes | Effort |
|---|---|---|
| Data in | A small read-only gateway: OPC UA, Modbus TCP, MQTT/Sparkplug B, or a historian CSV export. Map real tags to the tag list in `tools.js` | Days per site |
| Site knowledge | Replace `kb.js` with the customer's SOPs, P&IDs notes, alarm philosophy and datasheets | Days |
| Checks | Keep the generic checks; set thresholds from the customer's normal operation | Days |
| Twin | Replace the lift-station model with a simple model of their unit (mass/energy balance, first-order plus deadtime) | 1–2 weeks |
| Brain | **On-premise LLM** (Ollama or similar on a local server) so no process data leaves the site | Hours |
| Writes | Stay **advisory**: proposals go to the operator, who executes them in the SCADA. Only add write-back later, through the SCADA's own interlocks | Optional |

### Security and safety position (say this early; OT buyers will ask)

- Read-only by default. The copilot cannot write to the control system in the pilot.
- Runs inside the customer's network; the LLM can run locally, so data stays on site (fits IEC 62443 zoning).
- It is decision support, not a safety function. Safety instrumented systems and interlocks stay as they are.
- Every suggestion, approval and rejection is logged.

## Showing it to people

- **LinkedIn / YouTube:** a 60-second screen recording of the drift scenario ("the loop looks perfect, the
  copilot says the sensor is lying") is your strongest hook for automation engineers.
- **Live demo:** keep the built-in reasoner on for reliability; switch to an LLM to show free reasoning.
- **Integrator meetings:** lead with "you can resell this on your next SCADA project".
- **Utilities:** lead with overflow prevention and unmanned stations.

## Roadmap ideas

- Step-test identification so the tuning uses a model fitted from real data, not the datasheet.
- Alarm flood analysis: group cascaded alarms into one incident.
- Energy view: specific energy (kWh/m³) per pump, best duty point.
- Voice / mobile handover for on-call staff.
- Multi-site fleet view for utilities with dozens of stations.
