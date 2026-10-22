"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { Wordmark } from "@/components/logo";
import { Button } from "@/components/ui/button";
import { nav } from "@/content/site";
import { cn } from "@/lib/utils";

export function SiteHeader() {
  const pathname = usePathname();
  const [menuOpen, setMenuOpen] = React.useState(false);
  const menuId = React.useId();

  // Close the phone menu on Escape; menu links close it on click.
  React.useEffect(() => {
    if (!menuOpen) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setMenuOpen(false);
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [menuOpen]);

  const isCurrent = (href: string) => pathname === href || pathname.startsWith(href + "/");

  return (
    <header className="sticky top-0 z-40 border-b border-rule/70 bg-plant/92 backdrop-blur-sm supports-[backdrop-filter]:bg-plant/85">
      <div className="shell flex h-[72px] items-center justify-between gap-6">
        <Link href="/" className="-m-2 rounded-sm p-2" aria-label="Round House, home">
          <Wordmark />
        </Link>

        <nav aria-label="Main" className="hidden md:block">
          <ul className="flex items-center gap-1">
            {nav.map((item) => (
              <li key={item.href}>
                <Link
                  href={item.href}
                  aria-current={isCurrent(item.href) ? "page" : undefined}
                  className={cn(
                    "relative inline-flex min-h-11 items-center rounded-sm px-3.5 text-[15px] font-medium text-ink/80 transition-colors hover:text-ink",
                    "aria-[current=page]:text-ink aria-[current=page]:after:absolute aria-[current=page]:after:inset-x-3.5 aria-[current=page]:after:bottom-2 aria-[current=page]:after:h-0.5 aria-[current=page]:after:bg-ink",
                  )}
                >
                  {item.label}
                </Link>
              </li>
            ))}
          </ul>
        </nav>

        <div className="flex items-center gap-2">
          <Button asChild size="sm" className="hidden sm:inline-flex">
            <Link href="/contact">Book a call</Link>
          </Button>
          <button
            type="button"
            className="inline-flex min-h-11 items-center gap-2 rounded-sm border border-ink px-3.5 text-[15px] font-semibold md:hidden"
            aria-expanded={menuOpen}
            aria-controls={menuId}
            onClick={() => setMenuOpen((v) => !v)}
          >
            {menuOpen ? "Close" : "Menu"}
          </button>
        </div>
      </div>

      <div id={menuId} hidden={!menuOpen} className="border-t border-rule bg-plant md:hidden">
        <nav aria-label="Main" className="shell pt-2 pb-6">
          <ul>
            {nav.map((item) => (
              <li key={item.href} className="border-b border-rule">
                <Link
                  href={item.href}
                  aria-current={isCurrent(item.href) ? "page" : undefined}
                  onClick={() => setMenuOpen(false)}
                  className="t-h3 flex min-h-14 items-center aria-[current=page]:underline aria-[current=page]:underline-offset-4"
                >
                  {item.label}
                </Link>
              </li>
            ))}
          </ul>
          <Button asChild className="mt-6 w-full">
            <Link href="/contact" onClick={() => setMenuOpen(false)}>
              Book a 30-minute call
            </Link>
          </Button>
        </nav>
      </div>
    </header>
  );
}
