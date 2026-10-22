// Sample engagements. They show the kind of work and how results are reported.
// They are not real clients: every page that shows them says so. Replace with real case studies.

export type CaseStudy = {
  slug: string;
  client: string;
  location: string;
  tiers: ("Diagnose" | "Build" | "Run")[];
  practices: string[];
  headline: string;
  summary: string;
  figures: { value: string; label: string }[];
  timeline: string;
  /** What the engagement cost, in the published price ranges. */
  investment: string;
  /** How long until the measured savings covered the cost. */
  payback: string;
  situation: string[];
  built: { name: string; detail: string }[];
  stack: string[];
  running: string;
};

export const caseStudies: CaseStudy[] = [
  {
    slug: "hvac-speed-to-lead",
    client: "Regional HVAC and plumbing company",
    location: "6 locations, Texas",
    tiers: ["Build", "Run"],
    practices: ["Business automation", "AI agents and integrated systems"],
    headline: "Lead replies went from 3 hours 40 minutes to 90 seconds.",
    summary: "An instant reply and booking system for web, phone and after-hours enquiries.",
    figures: [
      { value: "90 s", label: "Average first reply, down from 3 h 40 min" },
      { value: "+38%", label: "Booked service calls in the first quarter" },
      { value: "11 h", label: "Dispatcher time returned each week" },
    ],
    timeline: "5 weeks to launch",
    investment: "$16,000 build, then Growth at $4,200/mo",
    payback: "About 6 weeks",
    situation: [
      "Web forms and missed calls landed in a shared inbox. Dispatchers answered between jobs, so the average enquiry waited almost four hours for a reply.",
      "Call tracking showed nearly a third of those enquiries booked with a competitor before anyone called back.",
    ],
    built: [
      { name: "Instant reply", detail: "Every form, missed call and chat gets a text and an email within two minutes, any hour." },
      { name: "Qualification", detail: "An AI assistant asks three questions (service, urgency, ZIP code) and flags emergencies to the on-call tech." },
      { name: "Booking", detail: "Customers pick a slot that is actually free in the field-service calendar." },
      { name: "CRM logging", detail: "Every conversation is saved to HubSpot with its source, so marketing spend can be judged on booked jobs." },
    ],
    stack: ["HubSpot", "Field-service scheduling", "Twilio SMS", "Claude API"],
    running: "On a Growth retainer: we monitor the flows, tune the assistant's answers monthly and report booked calls by source.",
  },
  {
    slug: "fabrication-quote-automation",
    client: "Metal fabrication shop",
    location: "85 staff, Ohio",
    tiers: ["Diagnose", "Build"],
    practices: ["Business analysis", "Business automation"],
    headline: "Quotes that took three days now go out in four hours.",
    summary: "Drawings in, priced quote out, using the material costs and machine rates already in the ERP.",
    figures: [
      { value: "4 h", label: "Quote turnaround, down from 3 days" },
      { value: "2.1×", label: "Quotes sent per week by the same two estimators" },
      { value: "29%", label: "Quote win rate, up from 22%" },
    ],
    timeline: "2-week audit, 7-week build",
    investment: "$4,500 audit, $22,000 build",
    payback: "About 4 months",
    situation: [
      "Two estimators priced every job by hand in spreadsheets, copying material prices and machine rates out of the ERP.",
      "Buyers who needed an answer the same day went elsewhere, and the audit found 30% of estimator time went on re-keying.",
    ],
    built: [
      { name: "Intake", detail: "One form for drawings, quantities and deadlines, replacing email threads." },
      { name: "Quote engine", detail: "Pulls current material costs and machine-hour rates from the ERP and applies the shop's own margin rules." },
      { name: "Proposal documents", detail: "Branded quote PDFs with terms, ready for e-signature." },
      { name: "Estimator review", detail: "Nothing is sent without an estimator's approval. The system does the arithmetic, people make the call." },
    ],
    stack: ["ERP integration", "Document templates", "E-signature", "Python services"],
    running: "Handed over with runbooks. The shop's own IT contractor maintains it.",
  },
  {
    slug: "3pl-invoice-processing",
    client: "Third-party logistics provider",
    location: "140 staff, Georgia",
    tiers: ["Build", "Run"],
    practices: ["Business automation", "AI agents and integrated systems"],
    headline: "Invoice processing time cut by 70%.",
    summary: "Carrier invoices read, matched to shipments and posted to accounting, with exceptions sent to a person.",
    figures: [
      { value: "−70%", label: "Time to process a carrier invoice" },
      { value: "26 h", label: "Accounts-payable time returned each week" },
      { value: "1.8%", label: "Of carrier spend caught as billing errors" },
    ],
    timeline: "8 weeks to launch",
    investment: "$24,000 build, then Starter at $1,800/mo",
    payback: "About 5 months",
    situation: [
      "Around 2,000 carrier invoices a month arrived as PDFs and were keyed into accounting by hand.",
      "Overcharges were only noticed when a customer complained, months later.",
    ],
    built: [
      { name: "Document reading", detail: "Each invoice is read and its lines extracted, whatever the carrier's layout." },
      { name: "Shipment matching", detail: "Lines are checked against the shipment record: weight, accessorials and agreed rates." },
      { name: "Exception queue", detail: "Anything that does not match goes to a person with the reason shown. Matched invoices post automatically." },
      { name: "Accounting sync", detail: "Approved invoices post to the accounting system with the shipment reference attached." },
    ],
    stack: ["Document AI", "TMS integration", "Accounting API", "Exception dashboard"],
    running: "On a Starter retainer: monitoring, carrier layout updates and a monthly savings report.",
  },
  {
    slug: "clinic-group-tool-audit",
    client: "Physical therapy group",
    location: "9 clinics, North Carolina",
    tiers: ["Diagnose", "Build", "Run"],
    practices: ["Business analysis", "Brand identity and social", "Websites"],
    headline: "$38,400 a year of unused software cut, then one CRM and a new site.",
    summary: "A tool-spend audit paid for the project. The savings funded a CRM migration, a brand refresh and a new website.",
    figures: [
      { value: "$38k", label: "Yearly software spend removed after the audit" },
      { value: "+24%", label: "New patient enquiries in six months" },
      { value: "1", label: "Dashboard replacing four weekly spreadsheets" },
    ],
    timeline: "3-week audit, 10-week build",
    investment: "$3,500 audit, $28,000 build, then Growth",
    payback: "Audit paid back in 5 weeks",
    situation: [
      "Each clinic had picked its own tools over the years: three scheduling add-ons, two email platforms and dozens of unused seats.",
      "Leadership spent Monday mornings merging spreadsheets to see how the week had gone.",
    ],
    built: [
      { name: "Tool-spend audit", detail: "Every subscription listed with its owner, its use and a keep or cancel call." },
      { name: "CRM migration", detail: "Referrals and patient enquiries moved into one HubSpot account with consistent stages." },
      { name: "Brand refresh and website", detail: "A clearer identity and a fast site with online booking per clinic." },
      { name: "Reporting dashboard", detail: "Enquiries, bookings and referral sources by clinic, updated every hour." },
    ],
    stack: ["HubSpot", "Next.js", "Looker Studio", "Booking integration"],
    running: "On a Growth retainer: website care, monthly reporting and new automations as clinics ask for them.",
  },
];

export function getCaseStudy(slug: string) {
  return caseStudies.find((c) => c.slug === slug);
}
