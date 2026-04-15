import React from "react";

/**
 * FractionBuilder component
 *
 * Oregon math standards require students to demonstrate fraction understanding
 * through interactive fraction builder UI.
 */

"use client";

import { useState } from "react";

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
      <h2>{label}</h2>

      <div className="mb-2">
        <label>Numerator</label>
        <input
          type="number"
          value={numerator}
          onChange={(e) => setNumerator(e.target.value)}
          min="0"
        />
      </div>

      <div className="mb-2">
        <label>Denominator</label>
        <input
          type="number"
          value={denominator}
          onChange={(e) => setDenominator(e.target.value)}
          min="1"
        />
      </div>

      {error && <p role="alert">{error}</p>}

      <button disabled={!isValid} onClick={handleSubmit}>
        Submit
      </button>
    </div>
  );
}
