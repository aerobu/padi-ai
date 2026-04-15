/**
 * Progress tracker component for assessment.
 */

"use client";

import React from "react";
import { Card, CardContent } from "@padi/ui/card";

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

  // Get domain colors
  const domainColors: Record<string, string> = {
    "4.NBT": "bg-blue-500",
    "4.NF": "bg-green-500",
    "4.OA": "bg-purple-500",
    "4.MD": "bg-yellow-500",
    "4.G": "bg-pink-500",
  };

  return (
    <div className="space-y-4">
      {/* Main progress bar */}
      <Card className="w-full">
        <CardContent className="p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-slate-700">
              Progress
            </span>
            <span className="text-sm font-semibold text-slate-900">
              {questionsAnswered} / {targetTotal}
            </span>
          </div>
          <div className="w-full bg-slate-200 rounded-full h-3">
            <div
              className="bg-blue-600 h-3 rounded-full transition-all duration-500"
              style={{ width: `${progress}%` }}
            />
          </div>
          <p className="mt-2 text-xs text-slate-500">
            Estimated time remaining: ~{estimatedTimeRemainingMin} minutes
          </p>
        </CardContent>
      </Card>

      {/* Domain coverage */}
      {domainsCovered && Object.keys(domainsCovered).length > 0 && (
        <Card className="w-full">
          <CardContent className="p-4">
            <p className="text-sm font-medium text-slate-700 mb-3">
              Domain Coverage
            </p>
            <div className="flex flex-wrap gap-2">
              {Object.entries(domainsCovered).map(([domain, count]) => (
                <div
                  key={domain}
                  className="flex items-center gap-1 px-2 py-1 rounded-md bg-slate-100"
                >
                  <div
                    className={`w-2 h-2 rounded-full ${
                      domainColors[domain] || "bg-slate-400"
                    }`}
                  />
                  <span className="text-xs text-slate-700">
                    {domain}: {count}
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
