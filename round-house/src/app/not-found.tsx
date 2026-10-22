import Link from "next/link";

import { Button } from "@/components/ui/button";

export default function NotFound() {
  return (
    <section className="shell drafting">
      <div className="relative py-24 md:py-36">
        <p className="t-small text-steel">Error 404</p>
        <h1 className="t-h1 mt-3 max-w-[16ch]">This track does not lead anywhere</h1>
        <p className="t-lead mt-6 max-w-[44ch]">The page may have moved. Start from the home page or see what we do.</p>
        <div className="mt-10 flex flex-wrap gap-3">
          <Button asChild size="lg">
            <Link href="/">Go to the home page</Link>
          </Button>
          <Button asChild size="lg" variant="outline">
            <Link href="/services">See services and prices</Link>
          </Button>
        </div>
      </div>
    </section>
  );
}
