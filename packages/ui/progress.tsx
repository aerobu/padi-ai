"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

const Progress = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & {
    value?: number;
    max?: number;
    color?: "green" | "terra" | "neutral";
    height?: string;
  }
>(
  (
    { className, value = 0, max = 100, color = "green", height = "h-2", ...props },
    ref
  ) => {
    const percentage = Math.min(100, Math.max(0, (value / max) * 100));
    const trackClass = { green: "bg-neutral-200", terra: "bg-terra-100", neutral: "bg-neutral-200" };
    const fillClass = { green: "bg-green-500", terra: "bg-terra-500", neutral: "bg-neutral-300" };
    return (
      <div
        ref={ref}
        role="progressbar"
        aria-valuenow={value}
        aria-valuemin={0}
        aria-valuemax={max}
        className={cn(
          "relative w-full overflow-hidden rounded-full bg-neutral-200 duration-slow ease-standard",
          height,
          className
        )}
        {...props}
      >
        <div
          className={cn(
            "h-full rounded-full duration-slow ease-standard",
            fillClass[color]
          )}
          style={{ width: `${percentage}%` }}
        />
      </div>
    );
  }
);
Progress.displayName = "Progress";

export { Progress };
