"use client";

import * as React from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { NativeSelect } from "@/components/ui/native-select";
import { Textarea } from "@/components/ui/textarea";
import { site } from "@/content/site";

type Fields = { name: string; email: string; company: string; interest: string | null; budget: string; message: string };
type Errors = Partial<Record<keyof Fields, string>>;

const interests = [
  { value: "diagnose", label: "Diagnose: an audit and roadmap" },
  { value: "build", label: "Build: a specific project" },
  { value: "run", label: "Run: support for systems we or others built" },
  { value: "unsure", label: "Not sure yet" },
];
const budgets = ["Under $5,000", "$5,000–$15,000", "$15,000–$40,000", "$40,000 or more", "Monthly retainer", "Not sure yet"];

const noop = () => () => {};

function validate(f: Fields): Errors {
  const e: Errors = {};
  if (!f.name.trim()) e.name = "Enter your name.";
  if (!f.email.trim()) e.email = "Enter your work email.";
  else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(f.email.trim())) e.email = "Enter an email address like name@company.com.";
  if (f.message.trim().length < 10) e.message = "Tell us in a sentence or two what you want to fix.";
  return e;
}

export function ContactForm() {
  const [fields, setFields] = React.useState<Fields>({ name: "", email: "", company: "", interest: null, budget: "", message: "" });
  const [errors, setErrors] = React.useState<Errors>({});
  const [status, setStatus] = React.useState<"idle" | "sending" | "sent" | "mailto" | "failed">("idle");
  const refs = React.useRef<Partial<Record<keyof Fields, HTMLElement | null>>>({});

  // Links like /contact?interest=run preselect the step until the visitor picks one.
  const search = React.useSyncExternalStore(noop, () => window.location.search, () => "");
  const fromUrl = new URLSearchParams(search).get("interest");
  const interest = fields.interest ?? (interests.some((i) => i.value === fromUrl) ? fromUrl! : "unsure");

  const set = (k: keyof Fields) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    setFields((f) => ({ ...f, [k]: e.target.value }));
    if (errors[k]) setErrors((er) => ({ ...er, [k]: undefined }));
  };

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const found = validate(fields);
    setErrors(found);
    const first = (Object.keys(found) as (keyof Fields)[])[0];
    if (first) {
      refs.current[first]?.focus();
      return;
    }

    const interestLabel = interests.find((i) => i.value === interest)?.label ?? interest;

    if (!site.formEndpoint) {
      // No form backend configured yet: hand the message to the visitor's email app, so nothing is lost.
      const body = [
        fields.message,
        "",
        `Name: ${fields.name}`,
        `Company: ${fields.company || "-"}`,
        `Interested in: ${interestLabel}`,
        `Budget: ${fields.budget || "-"}`,
      ].join("\n");
      window.location.href = `mailto:${site.email}?subject=${encodeURIComponent(`Project enquiry from ${fields.name}`)}&body=${encodeURIComponent(body)}`;
      setStatus("mailto");
      return;
    }

    setStatus("sending");
    try {
      const res = await fetch(site.formEndpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({ ...fields, interest: interestLabel }),
      });
      setStatus(res.ok ? "sent" : "failed");
    } catch {
      setStatus("failed");
    }
  };

  if (status === "sent") {
    return (
      <div role="status" className="border-t-[3px] border-run bg-panel p-6 md:p-8">
        <h2 className="t-h3">Message sent</h2>
        <p className="mt-3 max-w-[48ch]">
          Thanks, {fields.name.split(" ")[0]}. We reply within one business day, 9am–6pm ET. If it is urgent, book a call
          directly.
        </p>
        <Button asChild className="mt-6">
          <a href={site.bookingUrl}>Book a 30-minute call</a>
        </Button>
      </div>
    );
  }

  const errorId = (k: keyof Fields) => (errors[k] ? `${k}-error` : undefined);
  const fieldError = (k: keyof Fields) =>
    errors[k] ? (
      <p id={`${k}-error`} className="t-small mt-2 text-alarm">
        {errors[k]}
      </p>
    ) : null;

  return (
    <form noValidate onSubmit={onSubmit} className="grid gap-6" aria-describedby="form-note">
      <div className="grid gap-6 sm:grid-cols-2">
        <div>
          <Label htmlFor="name">Name</Label>
          <Input
            id="name"
            name="name"
            autoComplete="name"
            className="mt-2"
            value={fields.name}
            onChange={set("name")}
            aria-invalid={!!errors.name}
            aria-describedby={errorId("name")}
            ref={(el) => {
              refs.current.name = el;
            }}
          />
          {fieldError("name")}
        </div>
        <div>
          <Label htmlFor="email">Work email</Label>
          <Input
            id="email"
            name="email"
            type="email"
            inputMode="email"
            autoComplete="email"
            className="mt-2"
            value={fields.email}
            onChange={set("email")}
            aria-invalid={!!errors.email}
            aria-describedby={errorId("email")}
            ref={(el) => {
              refs.current.email = el;
            }}
          />
          {fieldError("email")}
        </div>
      </div>
      <div>
        <Label htmlFor="company">
          Company <span className="font-normal text-steel">(optional)</span>
        </Label>
        <Input id="company" name="company" autoComplete="organization" className="mt-2" value={fields.company} onChange={set("company")} />
      </div>
      <div className="grid gap-6 sm:grid-cols-2">
        <div>
          <Label htmlFor="interest">Where you want to start</Label>
          <NativeSelect id="interest" name="interest" className="mt-2" value={interest} onChange={set("interest")}>
            {interests.map((i) => (
              <option key={i.value} value={i.value}>
                {i.label}
              </option>
            ))}
          </NativeSelect>
        </div>
        <div>
          <Label htmlFor="budget">
            Budget in USD <span className="font-normal text-steel">(optional)</span>
          </Label>
          <NativeSelect id="budget" name="budget" className="mt-2" value={fields.budget} onChange={set("budget")}>
            <option value="">Choose a range</option>
            {budgets.map((b) => (
              <option key={b} value={b}>
                {b}
              </option>
            ))}
          </NativeSelect>
        </div>
      </div>
      <div>
        <Label htmlFor="message">What slows your team down?</Label>
        <p id="message-hint" className="t-small mt-1.5 text-steel">
          A sentence or two is plenty, for example: &ldquo;Quotes take three days and we lose jobs while we wait.&rdquo;
        </p>
        <Textarea
          id="message"
          name="message"
          className="mt-2"
          rows={5}
          value={fields.message}
          onChange={set("message")}
          aria-invalid={!!errors.message}
          aria-describedby={["message-hint", errorId("message")].filter(Boolean).join(" ")}
          ref={(el) => {
            refs.current.message = el;
          }}
        />
        {fieldError("message")}
      </div>
      <div className="flex flex-wrap items-center gap-x-5 gap-y-3">
        <Button type="submit" size="lg" disabled={status === "sending"}>
          {status === "sending" ? "Sending message" : "Send message"}
        </Button>
        <p id="form-note" className="t-small max-w-[40ch] text-steel">
          We reply within one business day. Your details are used only to answer you.
        </p>
      </div>
      <div aria-live="polite">
        {status === "mailto" && (
          <p className="border-l-[3px] border-run pl-4">
            Your email app should open with the message ready to send. If it does not, email{" "}
            <a className="underline underline-offset-4" href={`mailto:${site.email}`}>
              {site.email}
            </a>
            .
          </p>
        )}
        {status === "failed" && (
          <p className="border-l-[3px] border-alarm pl-4 text-alarm">
            The message did not send. Check your connection and try again, or email{" "}
            <a className="underline underline-offset-4" href={`mailto:${site.email}`}>
              {site.email}
            </a>
            .
          </p>
        )}
      </div>
    </form>
  );
}
