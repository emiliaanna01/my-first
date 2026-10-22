"use client";
import { useEffect, useRef, useState } from "react";
import { EMAIL } from "@/lib/content";
import { gsap, prefersReducedMotion } from "@/lib/gsap";

const STARTS: [string, string][] = [["Diagnose", "An audit and roadmap"], ["Build", "A specific project"], ["Run", "Support for existing systems"], ["Not sure yet", "We will help you pick"]];
const BUDGETS: [string, string][] = [["Not sure yet", "Not sure yet"], ["Under $5,000", "Under $5k"], ["$5,000–$15,000", "$5k–$15k"], ["$15,000–$40,000", "$15k–$40k"], ["$40,000 or more", "$40k+"]];
const slug = (s: string) => s.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "");

type Field = "name" | "email" | "message";
const RULES: Record<Field, [(v: string) => boolean, string]> = {
  name: [(v) => v.trim().length > 1, "Enter your name so we know who to reply to."],
  email: [(v) => /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(v.trim()), "Enter a work email like name@company.com."],
  message: [(v) => v.trim().length >= 10, "Tell us in a sentence or two what slows your team down."],
};

type Sent = { mode: "sent" } | { mode: "draft"; body: string; mailto: string };

export function ContactForm() {
  const [values, setValues] = useState({ name: "", email: "", company: "", start: "Not sure yet", budget: "Not sure yet", message: "", website: "" });
  const [errors, setErrors] = useState<Partial<Record<Field, string>>>({});
  const [busy, setBusy] = useState(false);
  const [failure, setFailure] = useState("");
  const [sent, setSent] = useState<Sent | null>(null);
  const [copyLabel, setCopyLabel] = useState("Copy message");
  const form = useRef<HTMLFormElement>(null);
  const done = useRef<HTMLDivElement>(null);
  const pre = useRef<HTMLPreElement>(null);

  // /contact?interest=run preselects where to start.
  useEffect(() => {
    const interest = new URLSearchParams(window.location.search).get("interest");
    const match = STARTS.find(([v]) => v.toLowerCase() === interest?.toLowerCase());
    if (match) setValues((v) => ({ ...v, start: match[0] }));
  }, []);

  useEffect(() => {
    if (!sent || !done.current) return;
    done.current.focus();
    if (prefersReducedMotion()) return;
    gsap.from(done.current.children, { y: 24, opacity: 0, duration: 0.7, ease: "power3.out", stagger: 0.06 });
    gsap.from(done.current.querySelector(".sent-signal"), { scale: 0, rotation: -90, transformOrigin: "50% 50%", duration: 0.9, ease: "back.out(2)" });
    gsap.fromTo(done.current.querySelector(".sent-signal path"), { strokeDasharray: 40, strokeDashoffset: 40 }, { strokeDashoffset: 0, duration: 0.6, delay: 0.35 });
  }, [sent]);

  const set = (k: keyof typeof values) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const v = e.target.value;
    setValues((s) => ({ ...s, [k]: v }));
    if (k in RULES && errors[k as Field]) check(k as Field, v);
  };
  const check = (k: Field, v: string) => {
    const [ok, text] = RULES[k];
    const good = ok(v);
    setErrors((e) => ({ ...e, [k]: good ? undefined : text }));
    return good;
  };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFailure("");
    const bad = (Object.keys(RULES) as Field[]).filter((k) => !check(k, values[k]));
    if (bad.length) {
      document.getElementById(`f-${bad[0] === "message" ? "msg" : bad[0]}`)?.focus();
      if (!prefersReducedMotion() && form.current) {
        gsap.fromTo(bad.map((k) => document.getElementById(`f-${k === "message" ? "msg" : k}`)!.closest(".field")), { x: -6 }, { x: 0, duration: 0.5, ease: "elastic.out(1, 0.3)" });
      }
      return;
    }
    setBusy(true);
    try {
      const res = await fetch("/api/contact", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(values) });
      if (res.ok) return setSent({ mode: "sent" });
      if (res.status === 422) {
        const data = await res.json();
        setErrors(data.errors ?? {});
        return;
      }
      if (res.status === 501) return setSent(draft());
      setFailure(`We could not send that just now. Email us at ${EMAIL}, or try again in a minute.`);
    } catch {
      setFailure(`We could not reach the server. Check your connection, or email us at ${EMAIL}.`);
    } finally {
      setBusy(false);
    }
  };

  const draft = (): Sent => {
    const body = [
      `Name: ${values.name}`,
      `Work email: ${values.email}`,
      values.company ? `Company: ${values.company}` : null,
      `Where we want to start: ${values.start}`,
      `Budget: ${values.budget}`,
      "",
      "What slows our team down:",
      values.message.trim(),
    ].filter((l) => l !== null).join("\n");
    const subject = `Enquiry from ${values.name}${values.company ? `, ${values.company}` : ""}`;
    return { mode: "draft", body, mailto: `mailto:${EMAIL}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}` };
  };

  const copyDraft = () => {
    if (!sent || sent.mode !== "draft") return;
    const fallback = () => {
      if (pre.current) {
        const r = document.createRange();
        r.selectNodeContents(pre.current);
        const s = window.getSelection();
        s?.removeAllRanges();
        s?.addRange(r);
      }
      setCopyLabel("Selected. Press Ctrl+C");
    };
    try { navigator.clipboard.writeText(sent.body).then(() => setCopyLabel("Copied"), fallback); } catch { fallback(); }
    window.setTimeout(() => setCopyLabel("Copy message"), 2200);
  };

  if (sent) {
    return (
      <div className="sent" ref={done} tabIndex={-1}>
        <svg className="sent-signal" viewBox="0 0 64 64" aria-hidden="true"><circle cx="32" cy="32" r="30" /><path d="M20 33l8 8 16-17" /></svg>
        {sent.mode === "sent" ? (
          <>
            <h2>Message sent</h2>
            <p className="small" style={{ maxWidth: "52ch" }}>Thanks, {values.name.split(" ")[0]}. We reply within one business day, 9am–6pm ET, usually with a few questions or a time for a call.</p>
          </>
        ) : (
          <>
            <h2>Your message is ready</h2>
            <p className="small" style={{ maxWidth: "52ch" }}>The form is not connected to email yet. Copy the message below into an email to {EMAIL}, or open it in your mail app.</p>
            <pre ref={pre}>{sent.body}</pre>
            <div className="sent-actions">
              <button className="btn" type="button" onClick={copyDraft}>{copyLabel}</button>
              <a className="ulink" href={sent.mailto}>Open in your mail app</a>
              <button className="ulink" type="button" onClick={() => setSent(null)} style={{ backgroundColor: "transparent", border: 0, cursor: "pointer", padding: "0 0 2px" }}>Edit the message</button>
            </div>
          </>
        )}
      </div>
    );
  }

  const fieldClass = (k: Field) => `field${errors[k] ? " has-error" : ""}`;
  return (
    <form className="form" id="contact-form" noValidate onSubmit={submit} ref={form}>
      <div style={{ display: "grid", gap: 8 }}>
        <h2 className="h3">Or send the details</h2>
        <p className="small">We reply within one business day. Your details are used only to answer you.</p>
      </div>
      <div className="form-row form-row--2">
        <div>
          <div className={fieldClass("name")}>
            <input id="f-name" name="name" type="text" autoComplete="name" placeholder=" " required value={values.name} onChange={set("name")} onBlur={(e) => e.target.value && check("name", e.target.value)} aria-invalid={!!errors.name} aria-errormessage={errors.name ? "f-name-err" : undefined} />
            <label htmlFor="f-name">Name</label>
          </div>
          {errors.name && <p className="err" id="f-name-err">{errors.name}</p>}
        </div>
        <div>
          <div className={fieldClass("email")}>
            <input id="f-email" name="email" type="email" autoComplete="email" placeholder=" " required value={values.email} onChange={set("email")} onBlur={(e) => e.target.value && check("email", e.target.value)} aria-invalid={!!errors.email} aria-errormessage={errors.email ? "f-email-err" : undefined} />
            <label htmlFor="f-email">Work email</label>
          </div>
          {errors.email && <p className="err" id="f-email-err">{errors.email}</p>}
        </div>
      </div>
      <div className="field">
        <input id="f-company" name="company" type="text" autoComplete="organization" placeholder=" " value={values.company} onChange={set("company")} />
        <label htmlFor="f-company">Company <span className="opt">(optional)</span></label>
      </div>
      <div className="hp" aria-hidden="true">
        <label htmlFor="f-website">Website</label>
        <input id="f-website" name="website" type="text" tabIndex={-1} autoComplete="off" value={values.website} onChange={set("website")} />
      </div>
      <fieldset>
        <legend>Where do you want to start?</legend>
        <div className="seg">
          {STARTS.map(([v, sub]) => (
            <span key={v} style={{ display: "contents" }}>
              <input type="radio" id={`start-${slug(v)}`} name="start" value={v} checked={values.start === v} onChange={() => setValues((s) => ({ ...s, start: v }))} />
              <label htmlFor={`start-${slug(v)}`}>{v}<small>{sub}</small></label>
            </span>
          ))}
        </div>
      </fieldset>
      <fieldset>
        <legend>Budget in USD <span className="small" style={{ fontWeight: 400 }}>(optional)</span></legend>
        <div className="seg">
          {BUDGETS.map(([v, l]) => (
            <span key={v} style={{ display: "contents" }}>
              <input type="radio" id={`budget-${slug(v)}`} name="budget" value={v} checked={values.budget === v} onChange={() => setValues((s) => ({ ...s, budget: v }))} />
              <label htmlFor={`budget-${slug(v)}`}>{l}</label>
            </span>
          ))}
        </div>
      </fieldset>
      <div>
        <div className={fieldClass("message")}>
          <textarea id="f-msg" name="message" placeholder=" " maxLength={1200} required aria-describedby="f-msg-hint" value={values.message} onChange={set("message")} onBlur={(e) => e.target.value && check("message", e.target.value)} aria-invalid={!!errors.message} aria-errormessage={errors.message ? "f-msg-err" : undefined} />
          <label htmlFor="f-msg">What slows your team down?</label>
        </div>
        <div className="field-meta">
          <span id="f-msg-hint">A sentence or two is plenty. For example: “Quotes take three days and we lose jobs while we wait.”</span>
          <span className="num">{values.message.length} / 1200</span>
        </div>
        {errors.message && <p className="err" id="f-msg-err">{errors.message}</p>}
      </div>
      <div className="form-foot">
        <button className="btn" type="submit" data-magnetic="" disabled={busy}>{busy ? "Sending…" : "Send message"}</button>
        <span className="small">Replies 9am–6pm ET, Monday to Friday.</span>
      </div>
      {failure && <p className="form-status" role="alert">{failure}</p>}
    </form>
  );
}
