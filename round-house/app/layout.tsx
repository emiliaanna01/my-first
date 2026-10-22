import type { Metadata, Viewport } from "next";
import { Big_Shoulders, Hanken_Grotesk } from "next/font/google";
import { Footer } from "@/components/Footer";
import { Header } from "@/components/Header";
import { Mark } from "@/components/Mark";
import { SiteMotion } from "@/components/SiteMotion";
import { SITE } from "@/lib/content";
import "./globals.css";

// next/font downloads these at build time and serves them from this site, so visitors never call Google.
// Big Shoulders has an optical-size axis: the browser picks its display cut for large headlines.
const display = Big_Shoulders({
  subsets: ["latin"],
  axes: ["opsz"],
  variable: "--font-display-face",
  display: "swap",
  fallback: ["Arial Narrow", "Roboto Condensed", "sans-serif"],
});
const body = Hanken_Grotesk({
  subsets: ["latin"],
  variable: "--font-body-face",
  display: "swap",
  fallback: ["Helvetica Neue", "Arial", "sans-serif"],
});

export const metadata: Metadata = {
  metadataBase: new URL(SITE.url),
  title: { default: "Round House: automation, AI and web for US businesses", template: "%s | Round House" },
  description: SITE.description,
  applicationName: SITE.name,
  openGraph: {
    type: "website",
    locale: "en_US",
    siteName: SITE.name,
    title: "Round House: we automate the work that slows you down",
    description: SITE.description,
    url: SITE.url,
  },
  twitter: { card: "summary_large_image", title: "Round House: we automate the work that slows you down", description: SITE.description },
  alternates: { canonical: "/" },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#e6e9e4" },
    { media: "(prefers-color-scheme: dark)", color: "#0d1611" },
  ],
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${display.variable} ${body.variable}`}>
      <body>
        <Header />
        {children}
        <Footer />
        <div className="curtain" aria-hidden="true"><Mark className="curtain-mark" /></div>
        <SiteMotion />
      </body>
    </html>
  );
}
