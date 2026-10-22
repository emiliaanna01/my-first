import * as React from "react";

import { cn } from "@/lib/utils";

/** A real <select>: keyboard, screen-reader and mobile-picker behaviour come free. */
function NativeSelect({ className, ...props }: React.ComponentProps<"select">) {
  return (
    <select
      data-slot="native-select"
      className={cn(
        "rh-select min-h-12 w-full rounded-sm border border-input bg-panel px-3.5 text-base text-ink outline-none cursor-pointer",
        "focus-visible:border-ink focus-visible:shadow-[inset_0_0_0_1px_var(--ink)] focus-visible:outline-none",
        "aria-invalid:border-alarm aria-invalid:shadow-[inset_0_0_0_1px_var(--alarm)]",
        className,
      )}
      {...props}
    />
  );
}

export { NativeSelect };
