"use client";

import { cn } from "@/lib/utils";

interface HeroCardProps {
  label: string;
  value: string;
  sub?: string;
  className?: string;
}

export function HeroCard({ label, value, sub, className }: HeroCardProps) {
  return (
    <div className={cn("rounded-xl p-6 bg-green-600 text-white shadow-green", className)}>
      <p className="text-[10px] font-semibold uppercase tracking-[.12em] text-white/65 mb-2">{label}</p>
      <p className="text-[38px] font-bold tabular-nums leading-none tracking-[-.02em]">{value}</p>
      {sub && <p className="mt-1 text-[12px] text-white/55">{sub}</p>}
    </div>
  );
}

interface RiskRowProps {
  title: string;
  description: string;
  status: "low" | "medium" | "high";
  className?: string;
}

export function RiskRow({ title, description, status, className }: RiskRowProps) {
  const dotColors = { low: "bg-[#4aad6e]", medium: "border-status-med-dot", high: "bg-[#d44a4a]" };
  return (
    <div className={cn(
      "flex items-center p-4 rounded-lg bg-white border border-neutral-100 gap-3 shadow-sm hover:shadow-md transition-shadow duration-200 ease-standard",
      className,
    )}>
      <div className={cn("w-[10px] h-[10px] rounded-full shrink-0", dotColors[status])} />
      <div className="flex-1">
        <p className="font-semibold text-[13px] text-neutral-900 mb-[4px]">{title}</p>
        <p className="text-[12px] leading-[1.4] text-neutral-500">{description}</p>
      </div>
    </div>
  );
}
