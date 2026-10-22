// Prices are proposals from DESIGN.md §6. Edit here; every page reads from this file.

export type Tier = {
  id: "diagnose" | "build" | "run";
  step: number;
  name: string;
  summary: string;
  price: string;
  priceNote: string;
  outcome: string;
  items: { name: string; detail: string; price?: string; group?: string }[];
};

/** Anchor id for a service row, so other pages can deep-link to it. */
export const serviceId = (name: string) =>
  name
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");

export const buildGroups = ["Leads and sales", "Documents and back office", "AI assistants and training", "Brand and web"] as const;

export const tiers: Tier[] = [
  {
    id: "diagnose",
    step: 1,
    name: "Diagnose",
    summary: "A paid audit of your tools, data and workflows, with a 90-day roadmap ranked by hours saved.",
    price: "$2,500–$6,000",
    priceNote: "Fee credited to your build if you go ahead within 60 days",
    outcome: "You leave with a costed plan, even if you never hire us for the build.",
    items: [
      {
        name: "Automation and AI readiness audit",
        detail: "We map how work moves today, what your tools already do, and where staff re-key, chase or wait.",
        price: "$2,500–$6,000",
      },
      {
        name: "Tech stack and tool-spend audit",
        detail: "Overlapping SaaS, unused seats and duplicate tools, listed with what to cancel and what it saves. It usually pays for itself.",
        price: "from $1,500",
      },
      {
        name: "Customer journey and funnel audit",
        detail: "How leads arrive, where they drop off and how long they wait for a reply.",
        price: "from $1,500",
      },
      {
        name: "Brand and website audit",
        detail: "Messaging clarity, conversion problems, speed, SEO and visibility in AI search answers.",
        price: "from $1,500",
      },
      {
        name: "Data readiness assessment",
        detail: "Whether your CRM, spreadsheets and documents are clean enough for automation and AI to use.",
        price: "from $1,500",
      },
      {
        name: "AI policy and governance starter",
        detail: "A plain-English guide to which AI tools staff can use and how client data stays protected.",
        price: "from $1,500",
      },
    ],
  },
  {
    id: "build",
    step: 2,
    name: "Build",
    summary: "The automation, AI agent, CRM, brand or website the roadmap calls for, scoped at a fixed price.",
    price: "$4,000–$40,000",
    priceNote: "Fixed scope and price, agreed before work starts",
    outcome: "A working system in your own accounts, documented, with your team trained to use it.",
    items: [
      { group: "Leads and sales", name: "Lead capture and instant replies", detail: "Instant replies, qualification questions and booking straight into your calendar.", price: "$8,000–$20,000" },
      { group: "AI assistants and training", name: "Internal AI assistant", detail: "Trained on your SOPs, documents and FAQs, for onboarding and support.", price: "$12,000–$35,000" },
      { group: "Documents and back office", name: "Document automation", detail: "Proposals, quotes, contracts, invoices and reports generated from templates and your data.", price: "$8,000–$25,000" },
      { group: "Documents and back office", name: "Email and inbox automation", detail: "Sorting, drafted replies and follow-ups that go out on time.", price: "$6,000–$15,000" },
      { group: "Documents and back office", name: "Client onboarding automation", detail: "Forms, contracts, welcome sequences and tasks created the moment a client signs.", price: "$6,000–$15,000" },
      { group: "Leads and sales", name: "CRM setup and migration", detail: "HubSpot, GoHighLevel or Pipedrive, set up properly and moved over from what you use now.", price: "$6,000–$20,000" },
      { group: "Documents and back office", name: "Reporting dashboards", detail: "Live numbers from your CRM, ads and accounting tools in one place.", price: "$5,000–$15,000" },
      { group: "AI assistants and training", name: "AI content system", detail: "One video or article turned into social posts and newsletters, in your brand voice.", price: "$6,000–$18,000" },
      { group: "Leads and sales", name: "Marketing automation", detail: "Email and SMS nurture sequences and review requests that run themselves.", price: "$5,000–$15,000" },
      { group: "Brand and web", name: "Brand identity and website", detail: "Identity, social branding and a site built to turn visitors into booked calls.", price: "$12,000–$40,000" },
      { group: "Brand and web", name: "Landing pages and microsites", detail: "For a campaign, an offer or a launch.", price: "$4,000–$9,000" },
      { group: "Leads and sales", name: "Pitch decks and sales collateral", detail: "Designed to match your brand and the way your team sells.", price: "$3,000–$10,000" },
      { group: "AI assistants and training", name: "Staff AI training workshops", detail: "Your team learns ChatGPT, Claude and the tools we built, on their own work.", price: "$2,500 per session" },
    ],
  },
  {
    id: "run",
    step: 3,
    name: "Run",
    summary: "Monitoring, fixes when tools change, new automations each month, and a report on hours saved.",
    price: "from $1,800/mo",
    priceNote: "Month to month after the first three months",
    outcome: "Systems that keep working, and a monthly number you can show your leadership.",
    items: [
      { name: "Maintenance and monitoring", detail: "We watch every automation and fix breaks when an API or tool changes.", price: "All plans" },
      { name: "Monthly optimization", detail: "Better prompts, new automations, and time saved measured against the baseline.", price: "Growth, Scale" },
      { name: "Monthly performance report", detail: "Hours saved, leads handled and revenue influenced, on one page.", price: "All plans" },
      { name: "Website care plan", detail: "Hosting, updates, security and small edits.", price: "Growth, Scale" },
      { name: "Social media and content retainer", detail: "Content produced and posted in your brand voice.", price: "Add-on, quoted" },
      { name: "SEO and AI-search visibility", detail: "So you show up in Google results and in the answers AI assistants give.", price: "Add-on, quoted" },
      { name: "Fractional automation lead", detail: "A named person acting as your in-house automation lead for a set number of hours a month.", price: "from $6,000/mo" },
    ],
  },
];

export const retainers = [
  {
    name: "Starter",
    price: "$1,800",
    for: "One or two systems that need to keep running",
    includes: [
      "Monitoring for up to 5 automations",
      "Fixes within one business day",
      "4 hours of small changes a month",
      "Monthly report on hours saved",
    ],
  },
  {
    name: "Growth",
    price: "$4,200",
    for: "Teams adding automation every month",
    includes: [
      "Everything in Starter, for up to 15 automations",
      "Two new automations or improvements a month",
      "Prompt and agent tuning",
      "Website care plan",
      "Same-day response during US hours",
    ],
  },
  {
    name: "Scale",
    price: "$8,500",
    for: "Companies that want an automation lead without the hire",
    includes: [
      "Everything in Growth, with no automation cap",
      "A named automation lead, 20 hours a month",
      "Quarterly roadmap session with your leadership",
      "4-hour response during US hours",
    ],
  },
] as const;

export const practices = [
  {
    name: "Business analysis",
    line: "Find where the hours go before anything gets built.",
    examples: ["Process mapping", "Tool-spend audits", "Funnel and data reviews"],
  },
  {
    name: "Business automation",
    line: "Take the copy-paste, chasing and re-keying off your team.",
    examples: ["Instant lead replies", "Documents and invoices", "Inbox and onboarding"],
  },
  {
    name: "AI agents and integrated systems",
    line: "Assistants that work inside the tools you already use, connected end to end.",
    examples: ["Knowledge assistants", "CRM and ERP integration", "AI policy and training"],
  },
  {
    name: "Brand identity and social",
    line: "An identity that looks as reliable as the work you do.",
    examples: ["Logo and identity systems", "Social media branding", "Decks and collateral"],
  },
  {
    name: "Websites",
    line: "Fast sites, landing pages and care plans that turn visits into calls.",
    examples: ["Company sites", "Campaign microsites", "SEO and AI-search visibility"],
  },
  {
    name: "UI and UX",
    line: "Screens your staff and customers can use without a manual.",
    examples: ["Dashboards", "Customer portals", "Internal tools"],
  },
] as const;

/** The eight bays of the roundhouse schematic. Order is left to right around the ring. */
export const bays = [
  { id: "onboarding", service: "Client onboarding automation", name: "Onboarding", outcome: "New clients get contracts, forms and a welcome sequence the moment they sign." },
  { id: "documents", service: "Document automation", name: "Documents", outcome: "Quotes, proposals and reports assemble themselves from your data." },
  { id: "inbox", service: "Email and inbox automation", name: "Inbox", outcome: "Email gets sorted, drafted and followed up before your team opens it." },
  { id: "leads", service: "Lead capture and instant replies", name: "Leads", outcome: "Every enquiry gets a reply in under two minutes, day or night." },
  { id: "crm", service: "CRM setup and migration", name: "CRM", outcome: "One clean CRM, moved over from the spreadsheets and the old system." },
  { id: "reporting", service: "Reporting dashboards", name: "Reporting", outcome: "One dashboard from your CRM, ads and books, updated every hour." },
  { id: "content", service: "AI content system", name: "Content", outcome: "One video becomes a week of posts and a newsletter, in your voice." },
  { id: "website", service: "Brand identity and website", name: "Website", outcome: "A fast site that turns visitors into booked calls." },
] as const;
