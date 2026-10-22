import type { Metadata, Viewport } from "next";
import localFont from "next/font/local";

import { SiteFooter } from "@/components/site-footer";
import { SiteHeader } from "@/components/site-header";
import { site } from "@/content/site";
import "./globals.css";

// Archivo variable (Omnibus-Type, OFL): weight 100–900 and width 62–125%, self-hosted.
const archivo = localFont({
  src: "./fonts/archivo.woff2",
  variable: "--font-archivo",
  weight: "100 900",
  display: "swap",
  declarations: [{ prop: "font-stretch", value: "62% 125%" }],
});

export const metadata: Metadata = {
  metadataBase: new URL(site.url),
  title: {
    default: "Round House: automation, AI and web for US businesses",
    template: "%s | Round House",
  },
  description: site.description,
  openGraph: {
    type: "website",
    siteName: site.name,
    title: "Round House: we automate the work that slows you down",
    description: site.description,
    url: "/",
    locale: "en_US",
  },
  twitter: { card: "summary_large_image" },
  alternates: { canonical: "/" },
};

export const viewport: Viewport = {
  themeColor: "#e8ebe9",
  colorScheme: "light",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en-US" className={archivo.variable}>
      <body className="flex min-h-dvh flex-col">
        <noscript>
          <style>{`.rh-armed .rh-draw{stroke-dasharray:none!important;stroke-dashoffset:0!important}.rh-armed .rh-fade{opacity:1!important}`}</style>
        </noscript>
        <a
          href="#main"
          className="fixed top-3 left-3 z-50 -translate-y-24 rounded-sm bg-ink px-4 py-3 font-semibold text-plant focus:translate-y-0"
        >
          Skip to content
        </a>
        <SiteHeader />
        <main id="main" className="flex-1">
          {children}
        </main>
        <SiteFooter />
      </body>
    </html>
  );
}
