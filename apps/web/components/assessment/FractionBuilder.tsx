import React from "react";

/**
 * FractionBuilder component
 *
 * Oregon math standards require students to demonstrate fraction understanding
 * through interactive fraction builder UI.
 */

"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";

interface FractionBuilderProps {
  onValueChange?: (value: { numerator: number; denominator: number }) => void;
  value?: { numerator: number; denominator: number } | null;
  error?: string | null;
  label?: string;
}

export function FractionBuilder({
  onValueChange,
  value,
  error,
  label = "Enter your answer",
}: FractionBuilderProps) {
  const [numerator, setNumerator] = useState<string>(value?.numerator?.toString() ?? "");
  const [denominator, setDenominator] = useState<string>(value?.denominator?.toString() ?? "");

  const handleSubmit = () => {
    const num = parseInt(numerator, 10);
    const denom = parseInt(denominator, 10);

    if (isNaN(num) || isNaN(denom)) return;
    if (denom === 0) return;
    if (num < 0) return;

    onValueChange?.({ numerator: num, denominator: denom });
  };

  const isValid =
    numerator !== "" &&
    denominator !== "" &&
    parseInt(denominator, 10) !== 0 &&
    parseInt(numerator, 10) >= 0;

  return (
    <div>
      <h2 className="text-display-sm text-neutral-900 mb-6">{label}</h2>

      <div className="rounded-xl border border-surface-border bg-white shadow-sm p-6 space-y-5">
        <div>
          <label className="block text-[12px] font-semibold uppercase tracking-[.08em] text-neutral-400 mb-2">
            Numerator
          </label>
          <input
            type="number"
            value={numerator}
            onChange={(e) => setNumerator(e.target.value)}
            min="0"
            className="w-full h-[44px] rounded-md border-[1.5px] border-neutral-200 bg-surface-cream px-3 text-[14px] text-neutral-900 focus:border-green-500 focus:ring-3 focus:ring-green-500/10 outline-none"
          />
        </div>

        <div>
          <label className="block text-[12px] font-semibold uppercase tracking-[.08em] text-neutral-400 mb-2">
            Denominator
          </label>
          <input
            type="number"
            value={denominator}
            onChange={(e) => setDenominator(e.target.value)}
            min="1"
            className="w-full h-[44px] rounded-md border-[1.5px] border-neutral-200 bg-surface-cream px-3 text-[14px] text-neutral-900 focus:border-green-500 focus:ring-3 focus:ring-green-500/10 outline-none"
          />
        </div>

        {error && (
          <div
            role="alert"
            className="p-3 rounded-md bg-status-high-bg border border-status-high-text/20 text-status-high-text text-[14px]"
          >
            {error}
          </div>
        )}

        <button
          onClick={handleSubmit}
          disabled={!isValid}
          className={cn(
            "w-full bg-terra-500 text-white shadow-[0_4px_12px_rgba(191,110,60,.28)] rounded-md h-[44px] font-semibold text-[14px] cursor-pointer transition-all duration-200 active:scale-[.96]",
            "hover:bg-terra-600",
            !isValid && "opacity-50 cursor-not-allowed",
          )}
        >
          Submit
        </button>
      </div>
    </div>
  );
}
