"use client";

import { useRouter } from "next/navigation";
import { Button } from "@padi/ui/button";
import { Badge } from "@padi/ui/badge";
import { Progress } from "@padi/ui/progress";
import { HeroCard } from "@padi/ui/hero-card";
import { cn } from "@/lib/utils";

export default function ResultsPage() {
  const router = useRouter();

  const domains = [
    { code: "4.NBT", name: "Place Value", score: 0.92, classification: "above_par" },
    { code: "4.OA", name: "Algebraic Thinking", score: 0.78, classification: "on_par" },
    { code: "4.NF", name: "Fractions", score: 0.55, classification: "below_par" },
    { code: "4.MD", name: "Measurement", score: 0.65, classification: "on_par" },
    { code: "4.G", name: "Geometry", score: 0.45, classification: "below_par" },
  ];

  const overallScore = 0.68;
  const classification = "on_par";

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Overall score */}
      <HeroCard label="Overall Assessment Score" value={`${Math.round(overallScore * 100)}%`} sub={`${classification === "on_par" ? "On Par" : classification === "above_par" ? "Above Par" : "Below Par"} · 24 of 35 questions correct`} />

      {/* Domain breakdown */}
      <div className="rounded-xl border border-surface-border bg-white shadow-sm p-6">
        <h2 className="text-[14px] font-semibold uppercase tracking-[.06em] text-neutral-400 mb-4">Domain Breakdown</h2>
        <div className="space-y-3">
          {domains.map((d) => (
            <div key={d.code} className="flex items-center justify-between p-3 rounded-lg bg-surface-cream">
              <div>
                <p className="font-semibold text-neutral-900">{d.code}</p>
                <p className="text-[14px] text-neutral-500">{d.name}</p>
              </div>
              <div className="text-right w-32">
                <p className={cn("font-bold text-[22px]", d.score >= 0.8 ? "text-green-600" : d.score >= 0.6 ? "text-terra-500" : "text-red-600")}>
                  {Math.round(d.score * 100)}%
                </p>
              </div>
              <Badge
                variant={d.classification === "above_par" ? "green" : d.classification === "on_par" ? "terra" : "high"}
              >
                {d.classification.replace("_", " ").toUpperCase()}
              </Badge>
            </div>
          ))}
        </div>
      </div>

      {/* Skills */}
      <div className="rounded-xl border border-surface-border bg-white shadow-sm p-6">
        <h2 className="text-[14px] font-semibold uppercase tracking-[.06em] text-neutral-400 mb-4">Skill States</h2>
        <div className="space-y-3">
          {[
            { code: "4.NBT.1", title: "Recognize place value", mastery: 0.92 },
            { code: "4.NBT.2", title: "Read/write large numbers", mastery: 0.88 },
            { code: "4.OA.1", title: "Interpret multiplication", mastery: 0.75 },
            { code: "4.NF.1", title: "Equivalent fractions", mastery: 0.45 },
            { code: "4.MD.1", title: "Convert measurements", mastery: 0.62 },
            { code: "4.G.1", title: "Identify geometric lines", mastery: 0.38 },
          ].map((s) => (
            <div key={s.code} className="flex items-center gap-4">
              <div className="w-20 shrink-0">
                <p className="text-[12px] font-semibold text-neutral-900">{s.code}</p>
                <p className="text-[12px] text-neutral-500">{s.title}</p>
              </div>
              <div className="flex-1">
                <Progress value={s.mastery * 100} color={s.mastery >= 0.8 ? "green" : s.mastery >= 0.6 ? "terra" : "neutral"} className="h-2" />
              </div>
              <span className="text-[12px] font-semibold text-neutral-700 w-8 text-right tabular-nums">{Math.round(s.mastery * 100)}%</span>
            </div>
          ))}
        </div>
      </div>

      {/* Next steps */}
      <div className="rounded-xl border border-surface-border bg-white shadow-sm p-6">
        <h2 className="text-[14px] font-semibold uppercase tracking-[.06em] text-neutral-400 mb-4">Recommended Focus</h2>
        <div className="space-y-3">
          <div>
            <p className="text-[12px] font-semibold text-red-600 mb-2">Priority Areas:</p>
            <div className="flex gap-2">
              {["4.G.1", "4.NF.1"].map((c) => (
                <Badge key={c} variant="high" showDot>{c}</Badge>
              ))}
            </div>
          </div>
          <div>
            <p className="text-[12px] font-semibold text-terra-500 mb-2">Building On:</p>
            <div className="flex gap-2">
              {["4.OA.1", "4.MD.1"].map((c) => (
                <Badge key={c} variant="terra" showDot>{c}</Badge>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="flex gap-3 pt-4">
        <Button size="lg" className="flex-1" onClick={() => router.push("/dashboard")}>
          Back to Dashboard
        </Button>
        <Button size="lg" variant="outline" onClick={() => window.print()}>
          Print Results
        </Button>
      </div>
    </div>
  );
}
