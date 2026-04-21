"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

interface ProgressProps {
  value?: number;
  max?: number;
  className?: string;
  indicatorClassName?: string;
  height?: string;
  children?: React.ReactNode;
}

const Progress = React.forwardRef<HTMLDivElement, ProgressProps>(
  ({ value = 0, max = 100, className, indicatorClassName, height = "h-2", children, ...props }, ref) => {
    const percentage = Math.min(100, Math.max(0, (value / max) * 100));

    return (
      <div
        ref={ref}
        role="progressbar"
        aria-valuenow={value}
        aria-valuemin={0}
        aria-valuemax={max}
        className={cn("relative w-full overflow-hidden rounded-full bg-gray-200", height, className)}
        {...props}
      >
        <div
          className={cn(
            "absolute left-0 top-0 h-full transition-all duration-300 ease-in-out",
            "bg-blue-600 dark:bg-blue-500",
            indicatorClassName
          )}
          style={{ width: `${percentage}%` }}
        />
        {children}
      </div>
    );
  }
);

Progress.displayName = "Progress";

export { Progress };
export type { ProgressProps };
