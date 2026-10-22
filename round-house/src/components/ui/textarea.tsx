import * as React from "react";

import { cn } from "@/lib/utils";

function Textarea({ className, ...props }: React.ComponentProps<"textarea">) {
  return (
    <textarea
      data-slot="textarea"
      className={cn(
        "field-sizing-content min-h-32 w-full rounded-sm border border-input bg-panel px-3.5 py-3 text-base text-ink placeholder:text-steel/80 transition-[border-color,box-shadow] outline-none",
        "focus-visible:border-ink focus-visible:shadow-[inset_0_0_0_1px_var(--ink)] focus-visible:outline-none",
        "aria-invalid:border-alarm aria-invalid:shadow-[inset_0_0_0_1px_var(--alarm)]",
        "disabled:cursor-not-allowed disabled:opacity-50",
        className,
      )}
      {...props}
    />
  );
}

export { Textarea };
