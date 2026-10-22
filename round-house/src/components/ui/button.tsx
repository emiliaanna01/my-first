import * as React from "react";
import { Slot } from "radix-ui";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex shrink-0 items-center justify-center gap-2 whitespace-nowrap rounded-sm font-semibold transition-[background-color,border-color,color,transform] duration-150 active:translate-y-px disabled:pointer-events-none disabled:opacity-50 cursor-pointer [&_svg]:pointer-events-none [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        // Signal yellow: the one colour that means "act here".
        default: "bg-signal text-ink border border-signal hover:bg-signal-press hover:border-signal-press",
        outline: "border border-ink text-ink bg-transparent hover:bg-ink hover:text-plant",
        inverse: "border border-plant text-plant bg-transparent hover:bg-plant hover:text-ink",
        link: "text-ink underline underline-offset-4 decoration-1 hover:decoration-2 px-0",
      },
      size: {
        default: "min-h-12 px-[22px] text-base",
        sm: "min-h-10 px-4 text-[15px]",
        lg: "min-h-14 px-7 text-[17px]",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  },
);

function Button({
  className,
  variant,
  size,
  asChild = false,
  ...props
}: React.ComponentProps<"button"> &
  VariantProps<typeof buttonVariants> & {
    asChild?: boolean;
  }) {
  const Comp = asChild ? Slot.Root : "button";

  return <Comp data-slot="button" className={cn(buttonVariants({ variant, size, className }))} {...props} />;
}

export { Button, buttonVariants };
