"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";

interface SegmentControlProps {
  options: { value: string; label: string }[];
  value: string;
  onChange: (value: string) => void;
  className?: string;
}

export function SegmentControl({ options, value, onChange, className }: SegmentControlProps) {
  return (
    <div className={cn("flex gap-2 flex-wrap", className)}>
      {options.map((opt) => (
        <button
          key={opt.value}
          onClick={() => onChange(opt.value)}
          className={cn(
            "px-3 py-1.5 rounded-md text-[13px] cursor-pointer transition-all duration-200 ease-standard",
            "border border-neutral-300 bg-white text-neutral-600",
            "hover:border-neutral-400 hover:text-neutral-800",
            value === opt.value && "bg-green-600 border-green-600 text-white font-semibold",
          )}
        >
          {opt.label}
        </button>
      ))}
    </div>
  );
}

interface ShellNavProps {
  brand: string;
  links?: { label: string; href: string }[];
  actions?: { label: string; href: string; variant: "cta" }[];
  className?: string;
}

export function ShellNav({ brand, links, actions, className }: ShellNavProps) {
  return (
    <nav className={cn(
      "sticky top-0 z-100 flex items-center h-[56px] px-8 bg-shell border-b border-shell-border text-shell-text",
      "backdrop-blur-sm bg-opacity-90",
      className,
    )}>
      <a href="/" className="flex items-center gap-2 text-white font-bold text-[16px] leading-none tracking-[-.01em] no-underline">
        <span className="text-[16px]">{brand}</span>
      </a>
      {links && links.length > 0 && (
        <nav className="flex gap-6 ml-5">
          {links.map((link) => (
            <a key={link.href} href={link.href} className="text-white/65 text-[14px] no-underline transition-colors duration-200 hover:text-white">
              {link.label}
            </a>
          ))}
        </nav>
      )}
      {actions && actions.length > 0 && (
        <div className="ml-auto flex gap-3">
          {actions.map((action) => (
            <a
              key={action.href}
              href={action.href}
              className={cn(
                "h-[36px] rounded-md px-4 font-semibold text-[14px] text-white cursor-pointer transition-colors duration-200 whitespace-nowrap",
                action.variant === "cta" && "bg-terra-500 hover:bg-terra-600 active:scale-[.96]",
              )}
            >
              {action.label}
            </a>
          ))}
        </div>
      )}
    </nav>
  );
}
