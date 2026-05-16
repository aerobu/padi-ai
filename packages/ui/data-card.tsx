"use client";

import { cn } from "@/lib/utils";

interface DataCardProps {
  label: string;
  value: string;
  color?: "green" | "terra" | undefined;
  className?: string;
}

export function DataCard({ label, value, color, className }: DataCardProps) {
  const colorClass = color === "green" ? "text-green-600" : color === "terra" ? "text-terra-500" : "";
  return (
    <div className={cn("rounded-lg border border-surface-border bg-surface-cream p-4", className)}>
      <p className="text-[10px] font-semibold uppercase tracking-[.1em] text-neutral-500 mb-1">{label}</p>
      <p className={cn("text-[22px] font-bold tabular-nums", colorClass)}>{value}</p>
    </div>
  );
}

interface DataTableProps {
  columns: string[];
  rows: string[][];
  valueColumns?: number[];
  principalColumns?: number[];
  interestColumns?: number[];
  className?: string;
}

export function DataTable({ columns, rows, valueColumns = [], principalColumns = [], interestColumns = [] }: DataTableProps) {
  return (
    <div className={cn("rounded-xl border border-surface-border bg-white shadow-sm overflow-hidden", "data-table")}>
      <table className="w-full text-[13px] font-normal text-neutral-700">
        <thead>
          <tr className="border-b border-neutral-200">
            {columns.map((col, i) => (
              <th key={i} className="text-left p-3 text-[10px] font-semibold uppercase tracking-[.1em] text-neutral-400">
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, ri) => (
            <tr key={ri} className="border-b border-neutral-100 last:border-none hover:bg-neutral-50/50">
              {row.map((cell, ci) => {
                const isValue = valueColumns.includes(ci);
                const isPrincipal = principalColumns.includes(ci);
                const isInterest = interestColumns.includes(ci);
                const isLast = ri === rows.length - 1;
                return (
                  <td key={ci} className={cn("p-3 tabular-nums",
                    isValue && "font-semibold text-neutral-900",
                    isPrincipal && "font-semibold text-green-600",
                    isInterest && "font-semibold text-terra-500",
                    isLast && "border-t-2 border-neutral-200 font-bold text-neutral-900",
                  )}>{cell}</td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

interface LineItemRowProps {
  items: { label: string; value: string; dotColor?: string }[];
  totalLabel: string;
  totalValue: string;
  className?: string;
}

export function LineItemRow({ items, totalLabel, totalValue, className }: LineItemRowProps) {
  return (
    <div className={cn("flex flex-col", className)}>
      {items.map((item, i) => (
        <div key={i} className="flex items-center justify-between gap-4 py-2 text-neutral-700 border-b border-neutral-100 last:border-none">
          <span className="flex items-center gap-2 text-[13px]">
            {item.dotColor && (
              <span className="w-2 h-2 rounded-full shrink-0" style={{ background: item.dotColor }} />
            )}
            {item.label}
          </span>
          <span className="font-semibold text-neutral-900 tabular-nums">{item.value}</span>
        </div>
      ))}
      <div className="flex items-center justify-between gap-4 pt-4 border-t-2 border-neutral-200 font-bold text-neutral-900">
        <span>{totalLabel}</span>
        <span className="tabular-nums">{totalValue}</span>
      </div>
    </div>
  );
}
