"use client";

import { InputHTMLAttributes, forwardRef } from "react";
import { cn } from "@/lib/utils";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  prefix?: string;
  suffix?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, prefix, suffix, className, ...props }, ref) => {
    return (
      <div className="w-full">
        {label && (
          <label className="block text-[11px] font-semibold uppercase tracking-[.08em] text-neutral-500 mb-[8px]">
            {label}
          </label>
        )}
        <div
          className={cn(
            "flex items-center h-[44px] rounded-md border-[1.5px] bg-surface-cream transition-all duration-200 ease-standard",
            error
              ? "border-error-500"
              : "border-neutral-300 hover:border-neutral-400",
            "focus-within:border-green-500 focus-within:ring-[3px] focus-within:ring-green-500/10",
            className,
          )}
        >
          {prefix && (
            <span className="pl-3 pr-2.5 text-neutral-500 text-[14px] border-r border-neutral-200 h-full flex items-center">
              {prefix}
            </span>
          )}
          <input
            ref={ref}
            className={cn(
              "flex-1 bg-transparent border-none outline-none text-neutral-800 text-[14px] py-0 pl-3 pr-3",
              prefix && "pl-0",
              suffix && "pr-0",
            )}
            {...props}
          />
          {suffix && (
            <span className="pl-2.5 pr-3 text-neutral-500 text-[14px] border-l border-neutral-200 h-full flex items-center">
              {suffix}
            </span>
          )}
        </div>
        {error && <p className="mt-1.5 text-xs text-error-600">{error}</p>}
      </div>
    );
  }
);
Input.displayName = "Input";
