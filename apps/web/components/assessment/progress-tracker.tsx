"use client";

import { Card, CardContent } from "@padi/ui/card";
import { Progress } from "@padi/ui/progress";
import { cn } from "@/lib/utils";

interface ProgressTrackerProps {
  questionsAnswered: number;
  targetTotal: number;
  domainsCovered?: Record<string, number> | null;
  estimatedTimeRemainingMin: number;
}

export function ProgressTracker({
  questionsAnswered,
  targetTotal,
  domainsCovered,
  estimatedTimeRemainingMin,
}: ProgressTrackerProps) {
  const progress = (questionsAnswered / targetTotal) * 100;

  const domainColors: Record<string, string> = {
    "4.NBT": "bg-green-500",
    "4.NF": "bg-terra-500",
    "4.OA": "bg-green-600",
    "4.MD": "bg-[#c97a4a]",
    "4.G": "bg-[#c8bfac]",
  };

  return (
    <div className="space-y-6">
      <Card className="w-full">
        <CardContent className="p-4">
          <div className="flex items-center justify-between mb-3">
            <span className="text-[12px] font-semibold text-neutral-500 uppercase tracking-[.08em]">Progress</span>
            <span className="text-[12px] font-semibold text-neutral-900 tabular-nums">{questionsAnswered} / {targetTotal}</span>
          </div>
          <Progress value={progress} color="green" className="h-2" />
        </CardContent>
      </Card>

      {domainsCovered && Object.keys(domainsCovered).length > 0 && (
        <Card className="w-full">
          <CardContent className="p-4">
            <p className="text-[12px] font-semibold text-neutral-400 mb-3 uppercase tracking-[.08em]">Domain Coverage</p>
            <div className="flex flex-wrap gap-2">
              {Object.entries(domainsCovered).map(([domain, count]) => (
                <div key={domain} className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-surface-cream border border-surface-border">
                  <div className={cn("w-2 h-2 rounded-full", domainColors[domain] || "bg-neutral-300")} />
                  <span className="text-[12px] text-neutral-700">{domain}: {count}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
