import type { MetadataRoute } from "next";
import { CASES, SITE } from "@/lib/content";

export default function sitemap(): MetadataRoute.Sitemap {
  const now = new Date();
  return ["", "/services", "/work", "/about", "/contact", ...CASES.map((c) => `/work/${c.slug}`)].map((p) => ({
    url: `${SITE.url}${p}`,
    lastModified: now,
    changeFrequency: "monthly",
    priority: p === "" ? 1 : 0.7,
  }));
}
