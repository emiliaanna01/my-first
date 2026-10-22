/* US Eastern office hours: 9am to 6pm, Monday to Friday. */
const DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
const SHORT = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

export function easternNow(date = new Date()) {
  const parts: Record<string, string> = {};
  new Intl.DateTimeFormat("en-US", { timeZone: "America/New_York", weekday: "short", hour: "numeric", minute: "2-digit", hourCycle: "h23" })
    .formatToParts(date)
    .forEach((p) => { parts[p.type] = p.value; });
  const day = SHORT.indexOf(parts.weekday);
  const hour = parseInt(parts.hour, 10) % 24;
  const time = `${((hour + 11) % 12) + 1}:${parts.minute} ${hour < 12 ? "am" : "pm"}`;
  return { day, hour, time };
}

export function officeStatus(date = new Date()) {
  const { day, hour, time } = easternNow(date);
  const weekday = day >= 1 && day <= 5;
  const open = weekday && hour >= 9 && hour < 18;
  if (open) return { open, text: `Open now. It is ${time} in New York` };
  let next: string;
  if (weekday && hour < 9) next = "today";
  else {
    let d = (day + 1) % 7;
    while (d === 0 || d === 6) d = (d + 1) % 7;
    next = d === (day + 1) % 7 ? "tomorrow" : DAYS[d];
  }
  return { open, text: `Closed now. Back at 9am ET ${next}` };
}
