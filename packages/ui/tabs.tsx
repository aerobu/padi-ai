"use client";

import { createContext, useContext, useState, useCallback, type ReactNode } from "react";
import { cn } from "@/lib/utils";

interface TabsContextValue {
  value: string;
  onValueChange: (value: string) => void;
}

const TabsContext = createContext<TabsContextValue | undefined>(undefined);

export function Tabs({
  value,
  onValueChange,
  className,
  children,
}: {
  value: string;
  onValueChange: (value: string) => void;
  className?: string;
  children: ReactNode;
}) {
  return (
    <TabsContext.Provider value={{ value, onValueChange }}>
      <div className={cn("w-full", className)}>{children}</div>
    </TabsContext.Provider>
  );
}

function TabsList({
  className,
  variant = "segment",
  children,
}: {
  variant?: "segment" | "tab-bar";
  className?: string;
  children: ReactNode;
}) {
  const variantStyles = {
    segment: cn(
      "inline-flex gap-1 p-1 rounded-md bg-surface-cream border border-neutral-200",
    ),
    "tab-bar": cn(
      "flex gap-0 border-t border-shell-border bg-shell text-shell-text",
    ),
  };
  return (
    <div
      role="tablist"
      aria-orientation="horizontal"
      className={cn(variantStyles[variant], className)}
    >
      {children}
    </div>
  );
}

function TabsTrigger({
  value,
  className,
  children,
  icon,
  badge,
  ...props
}: {
  value: string;
  className?: string;
  children: ReactNode;
  icon?: ReactNode;
  badge?: ReactNode;
  active?: boolean;
}) {
  const context = useContext(TabsContext);
  if (!context) throw new Error("TabsTrigger must be used within Tabs");
  const { value: currentValue, onValueChange } = context;
  const isActive = currentValue === value;

  return (
    <button
      role="tab"
      aria-selected={isActive}
      onClick={() => onValueChange(value)}
      data-state={isActive ? "active" : "inactive"}
      className={cn(
        // segment styles
        "inline-flex items-center gap-1.5 whitespace-nowrap rounded-md px-3 py-1.5 text-sm font-medium transition-all duration-200 ease-standard cursor-pointer select-none",
        "data-[state=inactive]:text-neutral-600 data-[state=inactive]:hover:bg-neutral-200/50",
        "data-[state=active]:bg-green-600 data-[state=active]:text-white data-[state=active]:font-semibold data-[state=active]:shadow-sm",
        // tab-bar overrides
        "[&:not([role])]:data-[state=inactive]:text-shell-text [&:not([role])]:data-[state=inactive]:hover:text-white data-[state=active]:border-b-2 data-[state=active]:border-terra-500 [&:not([role])]:rounded-none [&:not([role])]:border-b-2",
        "data-[state=inactive]:data-[role=tab-bar]:bg-transparent",
        className,
      )}
      {...props}
    >
      {icon}
      {children}
      {badge}
    </button>
  );
}

function TabsContent({ value, className, children }: {
  value: string;
  className?: string;
  children: ReactNode;
}) {
  const context = useContext(TabsContext);
  if (!context) throw new Error("TabsContent must be used within Tabs");
  const { value: currentValue } = context;
  if (currentValue !== value) return null;
  return (
    <div
      role="tabpanel"
      id={`tab-panel-${value}`}
      className={cn("mt-4", className)}
    >
      {children}
    </div>
  );
}

export { Tabs, TabsList, TabsTrigger, TabsContent };
