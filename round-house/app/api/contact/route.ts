import { NextResponse } from "next/server";

/* Contact form endpoint. Set ONE of these in Vercel (Project → Settings → Environment Variables):
     FORM_ENDPOINT    a Formspree, Basin or similar URL that accepts JSON (NEXT_PUBLIC_FORM_ENDPOINT also works)
   or
     RESEND_API_KEY   a Resend API key
     CONTACT_TO       where enquiries go, e.g. hello@roundhouse.studio
     CONTACT_FROM     a verified sender, e.g. "Round House site <site@roundhouse.studio>"
   With neither it answers 501, and the form offers the visitor a ready-to-send copy instead. */

export const runtime = "nodejs";

const STARTS = ["Diagnose", "Build", "Run", "Not sure yet"];
const BUDGETS = ["Not sure yet", "Under $5,000", "$5,000–$15,000", "$15,000–$40,000", "$40,000 or more"];
const clean = (v: unknown, max: number) => (typeof v === "string" ? v.replace(/[\u0000-\u0008\u000b-\u001f]/g, "").trim().slice(0, max) : "");

export async function POST(req: Request) {
  let body: Record<string, unknown>;
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ ok: false, error: "The form could not be read. Try again." }, { status: 400 });
  }

  // Honeypot: people never see this field, bots fill it in.
  if (clean(body.website, 200)) return NextResponse.json({ ok: true });

  const name = clean(body.name, 120);
  const email = clean(body.email, 200);
  const company = clean(body.company, 160);
  const start = STARTS.includes(String(body.start)) ? String(body.start) : "Not sure yet";
  const budget = BUDGETS.includes(String(body.budget)) ? String(body.budget) : "Not sure yet";
  const message = clean(body.message, 1200);

  const errors: Record<string, string> = {};
  if (name.length < 2) errors.name = "Enter your name so we know who to reply to.";
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email)) errors.email = "Enter a work email like name@company.com.";
  if (message.length < 10) errors.message = "Tell us in a sentence or two what slows your team down.";
  if (Object.keys(errors).length) return NextResponse.json({ ok: false, errors }, { status: 422 });

  // Option 1: a form service (Formspree, Basin and similar) that accepts JSON posts.
  const endpoint = process.env.FORM_ENDPOINT || process.env.NEXT_PUBLIC_FORM_ENDPOINT;
  if (endpoint) {
    const res = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify({ name, email, company, start, budget, message, _replyto: email, _subject: `Enquiry from ${name}${company ? `, ${company}` : ""}` }),
    }).catch(() => null);
    if (!res || !res.ok) return NextResponse.json({ ok: false, error: "send_failed" }, { status: 502 });
    return NextResponse.json({ ok: true });
  }

  // Option 2: email through Resend.
  const key = process.env.RESEND_API_KEY;
  const to = process.env.CONTACT_TO;
  const from = process.env.CONTACT_FROM;
  if (!key || !to || !from) return NextResponse.json({ ok: false, error: "not_configured" }, { status: 501 });

  const text = [
    `Name: ${name}`,
    `Work email: ${email}`,
    company ? `Company: ${company}` : null,
    `Where they want to start: ${start}`,
    `Budget: ${budget}`,
    "",
    "What slows their team down:",
    message,
  ].filter((l) => l !== null).join("\n");

  const res = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: { Authorization: `Bearer ${key}`, "Content-Type": "application/json" },
    body: JSON.stringify({ from, to: [to], reply_to: email, subject: `Enquiry from ${name}${company ? `, ${company}` : ""}`, text }),
  });
  if (!res.ok) return NextResponse.json({ ok: false, error: "send_failed" }, { status: 502 });
  return NextResponse.json({ ok: true });
}
