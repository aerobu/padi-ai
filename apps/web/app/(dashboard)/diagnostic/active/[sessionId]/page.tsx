"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { cn } from "@/lib/utils";

export default function AssessmentActivePage() {
  const params = useParams();
  const sessionId = params.sessionId as string;
  const [showFeedback, setShowFeedback] = useState(false);
  const [isCorrect] = useState(true);
  const [answered, setAnswered] = useState(0);
  const total = 35;
  const progress = ((answered) / total) * 100;

  const domains = ["4.NBT", "4.OA", "4.NF", "4.MD", "4.G"];
  const domainColors: Record<string, string> = {
    "4.NBT": "bg-green-500",
    "4.NF": "bg-terra-500",
    "4.OA": "bg-green-600",
    "4.MD": "bg-[#c97a4a]",
    "4.G": "bg-[#c8bfac]",
  };

  const options = [
    { key: "A", text: "An explanation of the mathematical concept" },
    { key: "B", text: "The correct numerical answer with reasoning" },
    { key: "C", text: "A step-by-step procedure with an example" },
    { key: "D", text: "A visual diagram with labeled parts" },
  ];

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Question header */}
      <div className="flex items-center justify-between">
        <h1 className="text-[18px] font-semibold text-neutral-900">Assessment</h1>
        <div className="text-[14px] text-neutral-500">
          Question {answered + 1} of {total}
        </div>
      </div>

      {/* Progress */}
      <div className="rounded-lg border border-surface-border bg-surface-cream p-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-[12px] font-medium text-neutral-600">Progress</span>
          <span className="text-[12px] font-semibold text-neutral-700">{answered} / {total}</span>
        </div>
        <div className="w-full h-2 rounded-full bg-neutral-200">
          <div
            className="h-full rounded-full bg-green-500 transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Domain badges */}
      <div className="flex gap-2 flex-wrap">
        {domains.map((d) => (
          <div key={d} className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-white border border-neutral-200">
            <div className={cn("w-2 h-2 rounded-full", domainColors[d])} />
            <span className="text-[12px] text-neutral-700">{d}: 3</span>
          </div>
        ))}
      </div>

      {/* Question Card */}
      <div className="rounded-xl border border-surface-border bg-white shadow-sm p-6">
        <div className="flex items-center justify-between mb-4">
          <span className="text-[12px] font-semibold uppercase tracking-[.1em] text-neutral-400">Question {answered + 1}</span>
          <span className="text-[12px] font-semibold uppercase tracking-[.06em] text-terra-500 bg-terra-50 px-2.5 py-1 rounded-full">4.OA</span>
        </div>

        <p className="text-body-lg text-neutral-800 mb-6 leading-relaxed">
          Which of the following best describes the relationship between prime numbers and composite numbers?
        </p>

        {/* Options */}
        <div className="space-y-3">
          {options.map((opt) => (
            <button
              key={opt.key}
              className={cn(
                "w-full p-4 text-left rounded-lg border-2 transition-all duration-200 cursor-pointer",
                "border-neutral-200 hover:border-green-500",
                "hover:shadow-sm",
                showFeedback && opt.key === "B" && "border-green-500 bg-green-50",
                showFeedback && opt.key !== "B" && "border-neutral-200",
              )}
              onClick={() => setShowFeedback(true)}
            >
              <span className="font-semibold text-neutral-700 mr-3">{opt.key}.</span>
              <span className="text-neutral-800">{opt.text}</span>
            </button>
          ))}
        </div>

        {/* Feedback */}
        {showFeedback && (
          <div className={cn("mt-4 p-4 rounded-lg", isCorrect ? "bg-green-50 border border-green-200" : "bg-red-50 border border-red-200")}>
            <p className="font-semibold text-neutral-900">{isCorrect ? "Correct!" : "Not quite right."}</p>
            <p className="mt-2 text-[14px] text-neutral-600">
              Prime numbers have exactly two factors (1 and themselves), while composite numbers have more than two factors.
            </p>
          </div>
        )}

        {/* Time */}
        <div className="mt-4 text-[12px] text-neutral-400">
          Time spent: 45s
        </div>
      </div>
    </div>
  );
}
