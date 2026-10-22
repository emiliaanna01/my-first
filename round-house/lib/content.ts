/* Site content. Everything a visitor reads lives here, so copy edits never touch layout code. */

export type Bay = { name: string; price: string; desc: string; proofLabel: string; proof: string };
export type Step = { key: "diagnose" | "build" | "run"; name: string; desc: string; price: string; terms: string; outcome: string };
export type Practice = { name: string; desc: string; items: string[] };
export type Term = { name: string; icon: IconName; text: string };
export type Row = [name: string, desc: string, price: string];
export type Plan = { name: string; price: string; pick?: boolean; best: string; items: string[] };
export type BeforeAfter = { before: number; after: number; bl: string; al: string };
export type CaseStudy = {
  slug: string; client: string; where: string; steps: ("Diagnose" | "Build" | "Run")[];
  title: string; summary: string; investment: string; payback: string; timeline: string;
  metric: string; metricCap: string;
  results: { num: string; cap: string; ba?: BeforeAfter }[];
  situation: string[]; built: [string, string][]; runningLabel: string; running: string; tools: string[];
};
export type IconName = "clock" | "doc" | "tag" | "shield" | "key" | "gauge" | "info" | "arrowL" | "arrowR" | "out" | "map" | "wrench" | "pen";

export const EMAIL = "hello@roundhouse.studio";
export const CAL = "https://cal.com/roundhouse/intro";

export const NAV = [
  { href: "/services", label: "Services", key: "services" },
  { href: "/work", label: "Work", key: "work" },
  { href: "/about", label: "About", key: "about" },
  { href: "/contact", label: "Contact", key: "contact" },
] as const;

export const BAYS: Bay[] = [
  { name: "Onboarding", price: "$6,000–$15,000", desc: "Forms, contracts, welcome emails and tasks created the moment a client signs.", proofLabel: "Takes off your team", proof: "Re-keying the same client details into four tools." },
  { name: "Documents", price: "$8,000–$25,000", desc: "Proposals, quotes, contracts, invoices and reports generated from templates and your data.", proofLabel: "Sample result", proof: "Quotes went from <strong>3 days to 4 hours</strong> at a metal fabrication shop." },
  { name: "Inbox", price: "$6,000–$15,000", desc: "Sorting, drafted replies and follow-ups that go out on time.", proofLabel: "Takes off your team", proof: "Hunting for the thread, and replies that slip a day." },
  { name: "Leads", price: "$8,000–$20,000", desc: "A reply within two minutes to every form, missed call and chat, with qualifying questions and a booking link.", proofLabel: "Sample result", proof: "First reply went from <strong>3 h 40 min to 90 s</strong> for an HVAC company." },
  { name: "CRM", price: "$6,000–$20,000", desc: "HubSpot, GoHighLevel or Pipedrive set up properly, and moved over from what you use now.", proofLabel: "Takes off your team", proof: "Spreadsheets nobody trusts and deals nobody owns." },
  { name: "Reporting", price: "$5,000–$15,000", desc: "Live numbers from your CRM, ads and accounting tools in one place.", proofLabel: "Sample result", proof: "<strong>One dashboard</strong> replaced four weekly spreadsheets at a clinic group." },
  { name: "Content", price: "$6,000–$18,000", desc: "One video or article turned into social posts and newsletters, in your brand voice.", proofLabel: "Takes off your team", proof: "Rewriting the same idea for five channels." },
  { name: "Website", price: "$4,000–$40,000", desc: "Fast sites and landing pages that turn visits into booked calls, with a care plan after launch.", proofLabel: "Takes off your team", proof: "A site that looks less reliable than the work you do." },
];

export const STEPS: Step[] = [
  { key: "diagnose", name: "Diagnose", desc: "A paid audit of your tools, data and workflows, with a 90-day roadmap ranked by hours saved.", price: "$2,500–$6,000", terms: "Fee credited to your build if you go ahead within 60 days", outcome: "You leave with a costed plan, even if you never hire us for the build." },
  { key: "build", name: "Build", desc: "The automation, AI agent, CRM, brand or website the roadmap calls for, scoped at a fixed price.", price: "$4,000–$40,000", terms: "Fixed scope and price, agreed before work starts", outcome: "A working system in your own accounts, documented, with your team trained to use it." },
  { key: "run", name: "Run", desc: "Monitoring, fixes when tools change, new automations each month, and a report on hours saved.", price: "from $1,800/mo", terms: "Month to month after the first three months", outcome: "Systems that keep working, and a monthly number you can show your leadership." },
];

export const PRACTICES: Practice[] = [
  { name: "Business analysis", desc: "Find where the hours go before anything gets built.", items: ["Process mapping", "Tool-spend audits", "Funnel and data reviews"] },
  { name: "Business automation", desc: "Take the copy-paste, chasing and re-keying off your team.", items: ["Instant lead replies", "Documents and invoices", "Inbox and onboarding"] },
  { name: "AI agents and integrated systems", desc: "Assistants that work inside the tools you already use, connected end to end.", items: ["Knowledge assistants", "CRM and ERP integration", "AI policy and training"] },
  { name: "Brand identity and social", desc: "An identity that looks as reliable as the work you do.", items: ["Logo and identity systems", "Social media branding", "Decks and collateral"] },
  { name: "Websites", desc: "Fast sites, landing pages and care plans that turn visits into calls.", items: ["Company sites", "Campaign microsites", "SEO and AI-search visibility"] },
  { name: "UI and UX", desc: "Screens your staff and customers can use without a manual.", items: ["Dashboards", "Customer portals", "Internal tools"] },
];

export const TERMS: Term[] = [
  { name: "Hours", icon: "clock", text: "9am–6pm Eastern, Monday to Friday. Replies within one business day, faster on a retainer." },
  { name: "Contracts", icon: "doc", text: "Mutual NDA before discovery. Every project runs on a master services agreement and a fixed-price statement of work." },
  { name: "Pricing", icon: "tag", text: "Published ranges for every service. The audit fee is credited to your build if you go ahead within 60 days." },
  { name: "Data security", icon: "shield", text: "We work inside your accounts with the least access the job needs, require MFA, never train AI models on your data, and remove our access at handover." },
  { name: "Ownership", icon: "key", text: "You own the code, automations, prompts and documentation. Nothing is locked to a platform we control." },
  { name: "Measurement", icon: "gauge", text: "We record a baseline before we build and report hours saved, response times and revenue influenced against it." },
];

export const DIAGNOSE: Row[] = [
  ["Automation and AI readiness audit", "We map how work moves today, what your tools already do, and where staff re-key, chase or wait.", "$2,500–$6,000"],
  ["Tech stack and tool-spend audit", "Overlapping SaaS, unused seats and duplicate tools, listed with what to cancel and what it saves. It usually pays for itself.", "from $1,500"],
  ["Customer journey and funnel audit", "How leads arrive, where they drop off and how long they wait for a reply.", "from $1,500"],
  ["Brand and website audit", "Messaging clarity, conversion problems, speed, SEO and visibility in AI search answers.", "from $1,500"],
  ["Data readiness assessment", "Whether your CRM, spreadsheets and documents are clean enough for automation and AI to use.", "from $1,500"],
  ["AI policy and governance starter", "A plain-English guide to which AI tools staff can use and how client data stays protected.", "from $1,500"],
];

export const BUILD: { group: string; rows: Row[] }[] = [
  { group: "Leads and sales", rows: [
    ["Lead capture and instant replies", "Instant replies, qualification questions and booking straight into your calendar.", "$8,000–$20,000"],
    ["CRM setup and migration", "HubSpot, GoHighLevel or Pipedrive, set up properly and moved over from what you use now.", "$6,000–$20,000"],
    ["Marketing automation", "Email and SMS nurture sequences and review requests that run themselves.", "$5,000–$15,000"],
    ["Pitch decks and sales collateral", "Designed to match your brand and the way your team sells.", "$3,000–$10,000"],
  ]},
  { group: "Documents and back office", rows: [
    ["Document automation", "Proposals, quotes, contracts, invoices and reports generated from templates and your data.", "$8,000–$25,000"],
    ["Email and inbox automation", "Sorting, drafted replies and follow-ups that go out on time.", "$6,000–$15,000"],
    ["Client onboarding automation", "Forms, contracts, welcome sequences and tasks created the moment a client signs.", "$6,000–$15,000"],
    ["Reporting dashboards", "Live numbers from your CRM, ads and accounting tools in one place.", "$5,000–$15,000"],
  ]},
  { group: "AI assistants and training", rows: [
    ["Internal AI assistant", "Trained on your SOPs, documents and FAQs, for onboarding and support.", "$12,000–$35,000"],
    ["AI content system", "One video or article turned into social posts and newsletters, in your brand voice.", "$6,000–$18,000"],
    ["Staff AI training workshops", "Your team learns ChatGPT, Claude and the tools we built, on their own work.", "$2,500 per session"],
  ]},
  { group: "Brand and web", rows: [
    ["Brand identity and website", "Identity, social branding and a site built to turn visitors into booked calls.", "$12,000–$40,000"],
    ["Landing pages and microsites", "For a campaign, an offer or a launch.", "$4,000–$9,000"],
  ]},
];

export const RUN: Row[] = [
  ["Maintenance and monitoring", "We watch every automation and fix breaks when an API or tool changes.", "All plans"],
  ["Monthly optimization", "Better prompts, new automations, and time saved measured against the baseline.", "Growth, Scale"],
  ["Monthly performance report", "Hours saved, leads handled and revenue influenced, on one page.", "All plans"],
  ["Website care plan", "Hosting, updates, security and small edits.", "Growth, Scale"],
  ["Social media and content retainer", "Content produced and posted in your brand voice.", "Add-on, quoted"],
  ["SEO and AI-search visibility", "So you show up in Google results and in the answers AI assistants give.", "Add-on, quoted"],
  ["Fractional automation lead", "A named person acting as your in-house automation lead for a set number of hours a month.", "from $6,000/mo"],
];

export const PLANS: Plan[] = [
  { name: "Starter", price: "$1,800", best: "One or two systems that need to keep running.", items: ["Monitoring for up to 5 automations", "Fixes within one business day", "4 hours of small changes a month", "Monthly report on hours saved"] },
  { name: "Growth", price: "$4,200", pick: true, best: "Teams adding automation every month.", items: ["Everything in Starter, for up to 15 automations", "Two new automations or improvements a month", "Prompt and agent tuning", "Website care plan", "Same-day response during US hours"] },
  { name: "Scale", price: "$8,500", best: "Companies that want an automation lead without the hire.", items: ["Everything in Growth, with no automation cap", "A named automation lead, 20 hours a month", "Quarterly roadmap session with your leadership", "4-hour response during US hours"] },
];

export const FAQ: [string, string][] = [
  ["Why should we pay for an audit first?", "Because most automation projects fail on scope, not code. The audit tells you what is worth automating, in what order and what each step will save. If you build with us within 60 days, the audit fee comes off the build price."],
  ["Do you work US hours?", "Yes. We are available 9am to 6pm Eastern, Monday to Friday, for calls, reviews and support. Retainer clients get a response time written into their agreement."],
  ["Will you sign our NDA, or do you have one?", "Either. We sign a mutual NDA before any discovery call that involves your data, and every project runs under a master services agreement and a statement of work with a fixed scope and price."],
  ["How do you handle our data?", "We work inside your accounts with the least access the job needs, and remove that access at handover. Client data is never used to train AI models, we choose AI providers that delete your data after each request where they offer it, and we require MFA on every account we touch."],
  ["Who owns what you build?", "You do. The code, automations, prompts, documentation and accounts are yours. Nothing is locked into a platform we control."],
  ["Which tools do you work with?", "Whatever you already run, where we can. That usually means HubSpot, GoHighLevel, Pipedrive, Google Workspace, Microsoft 365, QuickBooks, Slack, field-service and ERP systems, plus Claude and OpenAI models for the AI parts."],
  ["What happens if an automation breaks?", "On a Run retainer we are watching it and fix it, usually before you notice. Without a retainer, every build comes with 30 days of fixes and a runbook your own team or IT contractor can follow."],
  ["Can you work with our in-house team?", "Yes. Many clients have an ops or IT person who owns the systems after launch. We build with them, document everything and run a training session before handover."],
];

export const TOOLS: string[] = ["HubSpot", "GoHighLevel", "Pipedrive", "Google Workspace", "Microsoft 365", "QuickBooks", "Slack", "Twilio", "Field-service systems", "ERP systems", "Claude", "OpenAI", "Looker Studio", "Next.js"];

export const CASES: CaseStudy[] = [
  {
    slug: "hvac-speed-to-lead",
    client: "Regional HVAC and plumbing company", where: "6 locations, Texas", steps: ["Build", "Run"],
    title: "Lead replies went from 3 hours 40 minutes to 90 seconds.",
    summary: "An instant reply and booking system for web, phone and after-hours enquiries.",
    investment: "$16,000 build, then Growth at $4,200/mo", payback: "About 6 weeks", timeline: "5 weeks to launch",
    metric: "90 s", metricCap: "Average first reply, down from 3 h 40 min",
    results: [
      { num: "90 s", cap: "Average first reply, down from 3 h 40 min.", ba: { before: 220, after: 1.5, bl: "3 h 40 min", al: "90 s" } },
      { num: "+38%", cap: "Booked service calls in the first quarter.", ba: { before: 100, after: 138, bl: "Baseline", al: "+38%" } },
      { num: "11 h", cap: "Dispatcher time returned each week." },
    ],
    situation: ["Web forms and missed calls landed in a shared inbox, and dispatchers answered them between jobs. Enquiries waited nearly four hours for a reply.", "Call tracking showed that nearly a third of those leads booked with a competitor before anyone called back."],
    built: [
      ["Instant reply", "A text and an email within two minutes of any form, missed call or chat, at any hour."],
      ["Qualification", "An AI assistant asks about the service, urgency and ZIP code, and flags emergencies to the on-call tech."],
      ["Booking", "Customers choose a slot that is actually open in the field-service calendar."],
      ["CRM logging", "Every conversation is saved to HubSpot with its source, so marketing spend can be measured by booked jobs."],
    ],
    runningLabel: "Running it",
    running: "The Growth retainer covers monitoring the flows, monthly tuning of the assistant's answers, and a monthly report of booked calls by source.",
    tools: ["HubSpot", "Field-service scheduling", "Twilio SMS", "Claude API"],
  },
  {
    slug: "fabrication-quote-automation",
    client: "Metal fabrication shop", where: "85 staff, Ohio", steps: ["Diagnose", "Build"],
    title: "Quotes that took three days now go out in four hours.",
    summary: "Drawings in, priced quote out, using the material costs and machine rates already in the ERP.",
    investment: "$4,500 audit, $22,000 build", payback: "About 4 months", timeline: "2-week audit, 7-week build",
    metric: "4 h", metricCap: "Quote turnaround, down from 3 days",
    results: [
      { num: "4 h", cap: "Quote turnaround, down from 3 days.", ba: { before: 72, after: 4, bl: "3 days", al: "4 h" } },
      { num: "2.1×", cap: "Quotes sent per week by the same two estimators.", ba: { before: 1, after: 2.1, bl: "1.0×", al: "2.1×" } },
      { num: "29%", cap: "Quote win rate, up from 22%.", ba: { before: 22, after: 29, bl: "22%", al: "29%" } },
    ],
    situation: ["Two estimators priced every job by hand in spreadsheets, copying material prices and machine rates out of the ERP. Buyers who needed a same-day answer went elsewhere.", "The audit found that 30% of estimator time went to re-keying data that already existed."],
    built: [
      ["Intake", "One form for drawings, quantities and deadlines, in place of long email threads."],
      ["Quote engine", "Pulls current material costs and machine-hour rates from the ERP and applies the shop's margin rules."],
      ["Proposal documents", "Branded quote PDFs with terms, ready for e-signature."],
      ["Estimator review", "Nothing goes out without an estimator's approval."],
    ],
    runningLabel: "Handover",
    running: "Delivered with runbooks. The shop's own IT contractor maintains it.",
    tools: ["ERP integration", "Document templates", "E-signature", "Python services"],
  },
  {
    slug: "3pl-invoice-processing",
    client: "Third-party logistics provider", where: "140 staff, Georgia", steps: ["Build", "Run"],
    title: "Invoice processing time cut by 70%.",
    summary: "Carrier invoices read, matched to shipments and posted to accounting, with exceptions sent to a person.",
    investment: "$24,000 build, then Starter at $1,800/mo", payback: "About 5 months", timeline: "8 weeks to launch",
    metric: "−70%", metricCap: "Time to process a carrier invoice",
    results: [
      { num: "−70%", cap: "Time to process a carrier invoice.", ba: { before: 100, after: 30, bl: "Before", al: "After" } },
      { num: "26 h", cap: "Accounts-payable time returned each week." },
      { num: "1.8%", cap: "Of carrier spend caught as billing errors." },
    ],
    situation: ["About 2,000 carrier invoices a month arrived as PDFs and were keyed into accounting by hand.", "Overcharges usually surfaced months later, after a customer complained."],
    built: [
      ["Document reading", "Extracts invoice lines from any carrier's layout."],
      ["Shipment matching", "Checks weight, accessorials and agreed rates against the shipment record."],
      ["Exception queue", "Sends mismatches to a person with the reason shown. Matched invoices post automatically."],
      ["Accounting sync", "Posts approved invoices with the shipment reference attached."],
    ],
    runningLabel: "Running it",
    running: "A Starter retainer covers monitoring, carrier layout updates and a monthly savings report.",
    tools: ["Document AI", "TMS integration", "Accounting API", "Exception dashboard"],
  },
  {
    slug: "clinic-group-tool-audit",
    client: "Physical therapy group", where: "9 clinics, North Carolina", steps: ["Diagnose", "Build", "Run"],
    title: "$38,400 a year of unused software cut, then one CRM and a new site.",
    summary: "A tool-spend audit paid for the project. The savings funded a CRM migration, a brand refresh and a new website.",
    investment: "$3,500 audit, $28,000 build, then Growth", payback: "Audit paid back in 5 weeks", timeline: "3-week audit, 10-week build",
    metric: "$38k", metricCap: "Yearly software spend removed after the audit",
    results: [
      { num: "$38k", cap: "Yearly software spend removed after the audit." },
      { num: "+24%", cap: "New patient enquiries within six months.", ba: { before: 100, after: 124, bl: "Baseline", al: "+24%" } },
      { num: "1", cap: "Dashboard in place of four weekly spreadsheets.", ba: { before: 4, after: 1, bl: "4 sheets", al: "1 view" } },
    ],
    situation: ["Each clinic had chosen its own tools over the years: three scheduling add-ons, two email platforms and dozens of unused seats.", "Leadership spent Monday mornings merging spreadsheets to see how the week had gone."],
    built: [
      ["Tool-spend audit", "Every subscription listed with its owner, its use and a keep or cancel recommendation."],
      ["CRM migration", "Referrals and enquiries moved into one HubSpot account with consistent stages."],
      ["Brand refresh and website", "A new identity and a fast site with online booking for each clinic."],
      ["Reporting dashboard", "Enquiries, bookings and referral sources by clinic, updated hourly."],
    ],
    runningLabel: "Running it",
    running: "A Growth retainer covers website care, monthly reporting and new automations as clinics ask for them.",
    tools: ["HubSpot", "Next.js", "Looker Studio", "Booking integration"],
  },
];

export const SECURITY: string[] = [
  "Least-privilege access through your own accounts, never shared passwords",
  "MFA required on every account we use",
  "Client data is never used to train AI models",
  "AI providers that delete your data after each request, where they offer it",
  "Data stays in your systems. We do not copy it to ours",
  "Access removed and confirmed in writing at handover",
];

export const STORY: [title: string, rail: string, us: string][] = [
  ["Roll in", "An engine rolls off the main line and onto the turntable.", "Work comes in: a lead, a quote request, a carrier invoice."],
  ["Turn to the right bay", "The bridge turns until its rails line up with the stall that has the right tools.", "We find where the work stalls. That is the audit."],
  ["Inspect and repair", "Inside the stall, crews inspect the engine and fix what slows it down.", "We rebuild the part that costs you hours, at a fixed price."],
  ["Back out on the right track", "The engine turns again and leaves on the track it needs.", "We keep it running, with monitoring and a monthly report."],
];

export const PRINCIPLES: [string, string][] = [
  ["Outcome before tool", "We start from the hours, the response time or the revenue you want to change. The software comes second."],
  ["Measure before and after", "A baseline goes in writing before we build, so the result is a number, not an opinion."],
  ["Build in your stack", "We use the CRM, accounts and tools you already pay for wherever we can, so nothing new has to be adopted."],
  ["Leave it documented", "Every system ships with a runbook and a training session. Your team can own it without us."],
];

export const ROLES: [IconName, string, string][] = [
  ["map", "Systems lead", "Runs the audit, maps your processes and owns the roadmap. Your main contact from first call to handover."],
  ["wrench", "Automation engineer", "Builds and tests the integrations, agents and dashboards, and writes the runbooks."],
  ["pen", "Brand and web designer", "Designs the identity, website and collateral, so what customers see matches how you operate."],
];

/** Bay angles on the turntable drawing, in degrees clockwise from north. */
export const BAY_ANGLES = BAYS.map((_, i) => -122.5 + 35 * i);

export const SITE = {
  name: "Round House",
  url: (process.env.NEXT_PUBLIC_SITE_URL || "https://round-house.vercel.app").replace(/\/$/, ""),
  description: "Round House automates the work that slows US businesses down, from the factory floor to the front office. Audits, automation, AI agents, CRM, brand and web, with clear prices.",
  revision: "October 2026, revision D",
};
