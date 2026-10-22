// Every value marked PLACEHOLDER is listed in PLACEHOLDERS.md. Replace before launch.

export const site = {
  name: "Round House",
  url: process.env.NEXT_PUBLIC_SITE_URL ?? "https://round-house.vercel.app",
  description:
    "Round House automates the work that slows US businesses down, from the factory floor to the front office. Audits, automation, AI agents, CRM, brand and web, with clear prices.",
  email: "hello@roundhouse.studio", // PLACEHOLDER
  bookingUrl: "https://cal.com/roundhouse/intro", // PLACEHOLDER
  hours: {
    label: "9am–6pm ET, Monday to Friday",
    short: "9am–6pm ET",
    timeZone: "America/New_York",
    open: 9,
    close: 18,
  },
  updated: "October 2026",
  // Formspree, Basin or similar. When unset, the contact form opens a pre-filled email instead.
  formEndpoint: process.env.NEXT_PUBLIC_FORM_ENDPOINT ?? "",
} as const;

export const nav = [
  { href: "/services", label: "Services" },
  { href: "/work", label: "Work" },
  { href: "/about", label: "About" },
  { href: "/contact", label: "Contact" },
] as const;
