"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@padi/ui/button";
import { Card } from "@padi/ui/card";
import { HeroCard } from "@padi/ui/hero-card";
import { Divider } from "@padi/ui/divider";

export default function DiagnosticStartPage() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const studentId = typeof window !== "undefined" ? localStorage.getItem("student_id") : null;

  const handleStart = async () => {
    if (!studentId) return;
    setIsLoading(true);
    router.push("/diagnostic/active");
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="flex items-center gap-3">
        <button onClick={() => router.push("/dashboard")} className="text-[14px] text-neutral-600 hover:text-neutral-900 no-underline">
          ← Back to Dashboard
        </button>
      </div>

      <h1 className="font-display text-display-md text-neutral-900">Diagnostic Assessment</h1>

      <HeroCard label="Estimated Duration" value="45-60 min" sub="Adaptive difficulty · ~35 questions · All Grade 4 domains" />

      <Card className="p-5">
        <h3 className="text-[14px] font-semibold text-neutral-900 mb-3">What to expect:</h3>
        <ul className="text-[14px] text-neutral-600 leading-relaxed space-y-2">
          <li className="flex gap-2 items-start">
            <span className="text-green-600">✓</span>
            <span>Adaptive difficulty that adjusts to your child's responses</span>
          </li>
          <li className="flex gap-2 items-start">
            <span className="text-green-600">✓</span>
            <span>Covers all major Grade 4 Oregon math standards</span>
          </li>
          <li className="flex gap-2 items-start">
            <span className="text-green-600">✓</span>
            <span>Provides detailed proficiency report across all domains</span>
          </li>
        </ul>
      </Card>

      <Card className="p-5">
        <h3 className="text-[14px] font-semibold text-neutral-900 mb-2">Tips:</h3>
        <ul className="text-[14px] text-neutral-600 leading-relaxed space-y-1.5">
          <li className="flex gap-2 items-start">
            <span className="text-terra-500">⚡</span>
            <span>Find a quiet environment with minimal distractions</span>
          </li>
          <li className="flex gap-2 items-start">
            <span className="text-terra-500">⚡</span>
            <span>Allow enough time to complete in one sitting</span>
          </li>
        </ul>
      </Card>

      <div className="flex gap-3 pt-4">
        <Button size="sm" variant="outline" onClick={() => router.push("/dashboard")}>
          Cancel
        </Button>
        <Button size="lg" variant="primary" onClick={handleStart} disabled={isLoading} className="flex-1">
          {isLoading ? "Starting..." : "Start Assessment"}
        </Button>
      </div>
    </div>
  );
}
