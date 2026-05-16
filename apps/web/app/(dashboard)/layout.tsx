"use client";

import { useState } from "react";
import { useTheme } from "@/providers/ThemeProvider";
import { cn } from "@/lib/utils";

function ShellNav() {
  const { theme, toggleTheme } = useTheme();
  const dark = theme === "dark";
  return (
    <nav
      className={cn(
        "sticky top-0 z-100 flex items-center h-[56px] px-8 bg-shell border-b border-shell-border text-white",
        dark && "bg-white border-neutral-200 text-neutral-800",
      )}
    >
      <a href="/dashboard" className="flex items-center gap-2 no-underline">
        <span className="h-7 w-7 rounded-md bg-green-600 flex items-center justify-center text-white">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path d="M3 12L8 3l5 9" stroke="white" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
            <circle cx="8" cy="8" r="2" fill="rgba(255,255,255,.3)" />
          </svg>
        </span>
        <span className="font-bold text-[16px] tracking-[-.01em]">PADI.AI</span>
      </a>
      <nav className="flex gap-6 ml-6">
        {[
          { label: "Dashboard", href: "/dashboard" },
          { label: "Assessment", href: "/diagnostic/start" },
          { label: "Results", href: "/diagnostic/results" },
        ].map((l) => (
          <a
            key={l.href}
            href={l.href}
            className={cn(
              "text-[14px] no-underline transition-colors duration-200",
              dark ? "text-neutral-600 hover:text-neutral-900" : "text-white/65 hover:text-white",
            )}
          >
            {l.label}
          </a>
        ))}
      </nav>
      <div className="ml-auto flex items-center gap-3">
        <button
          onClick={toggleTheme}
          className={cn(
            "h-[36px] rounded-md px-4 font-semibold text-[14px] cursor-pointer transition-colors duration-200",
            "bg-green-600 text-white hover:bg-green-700 active:scale-[.96]",
            dark && "bg-neutral-200 text-neutral-700 hover:bg-neutral-300",
          )}
        >
          {theme === "light" ? "Light" : "Dark"}
        </button>
      </div>
    </nav>
  );
}

function Footer() {
  return (
    <footer className="bg-shell text-white border-t border-shell-border">
      <div className="max-w-7xl mx-auto px-8 py-6 flex items-center justify-between text-sm">
        <span>© 2026 PADI.AI</span>
        <div className="flex gap-6">
          <a href="/privacy" className="text-white/65 hover:text-white transition-colors">Privacy</a>
          <a href="/terms" className="text-white/65 hover:text-white transition-colors">Terms</a>
        </div>
      </div>
    </footer>
  );
}

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { theme } = useTheme();
  return (
    <div className="min-h-screen bg-page">
      <ShellNav />
      <main className="max-w-7xl mx-auto px-6 py-8">
        {children}
      </main>
      {theme !== "dark" && <Footer />}
    </div>
  );
}
