"use client";

import { cn } from "@/lib/utils";

export type BadgeVariant = "low" | "medium" | "high" | "terra" | "default" | "green";

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant;
  size?: "sm" | "md";
  showDot?: boolean;
}

const variantStyles: Record<BadgeVariant, string> = {
  low:    "bg-status-low-bg text-status-low-text",
  medium: "bg-status-med-bg text-status-med-text",
  high:   "bg-status-high-bg text-status-high-text",
  terra:  "bg-terra-500 text-white",
  default: "bg-neutral-200 text-neutral-600",
  green:  "bg-green-600 text-white",
};

const dotColors: Record<BadgeVariant, string> = {
  low:    "bg-status-low-text",
  medium: "bg-status-med-dot",
  high:   "bg-status-high-dot",
  terra:  "bg-white/60",
  default:"bg-neutral-400",
  green:  "bg-white/60",
};

export function Badge({
  variant = "default",
  size = "md",
  showDot = false,
  className,
  children,
  ...props
}: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full font-semibold uppercase tracking-[.06em]",
        variantStyles[variant],
        size === "sm" ? "px-2.5 py-0.5 text-[10px]" : "px-2.5 py-1 text-xs",
        showDot && "before:content-[''] before:rounded-full before:block before:w-[7px] before:h-[7px] before:shrink-0 before:bg-current",
        className,
      )}
      {...props}
    >
      {children}
    </span>
  );
}
