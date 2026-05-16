/**
 * ResultsSummary component for displaying assessment results.
 */

"use client";

import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@padi/ui/card";
import { Badge, type BadgeVariant } from "@padi/ui/badge";
import { Button } from "@padi/ui/button";
import { useRouter } from "next/navigation";

export interface DomainResult {
  domain_code: string;
  domain_name: string;
  questions_count: number;
  correct_count: number;
  score: number;
  classification: "below_par" | "on_par" | "above_par";
}

export interface SkillStateResult {
  standard_code: string;
  standard_title: string;
  p_mastery: number;
  mastery_level: "low" | "medium" | "high";
  questions_attempted: number;
  questions_correct: number;
}

export interface GapAnalysis {
  strengths: string[];
  on_track: string[];
  needs_work: string[];
  recommended_focus_order: string[];
}

export interface AssessmentResultsProps {
  overallScore: number;
  totalQuestions: number;
  totalCorrect: number;
  overallClassification: "below_par" | "on_par" | "above_par";
  domainResults: DomainResult[];
  skillStates: SkillStateResult[];
  gapAnalysis?: GapAnalysis | null;
}

export function ResultsSummary({
  overallScore,
  totalQuestions,
  totalCorrect,
  overallClassification,
  domainResults,
  skillStates,
  gapAnalysis = {
    strengths: [],
    on_track: [],
    needs_work: [],
    recommended_focus_order: [],
  } as GapAnalysis,
}: AssessmentResultsProps) {
  const router = useRouter();

  // Safe access to gapAnalysis arrays
  const getGapArray = (key: keyof GapAnalysis) => gapAnalysis?.[key] ?? [];

  const getScoreColor = (score: number): string => {
    if (score >= 0.8) return "text-green-600";
    if (score >= 0.6) return "text-terra-500";
    return "text-[#a83030]";
  };

  const getBadgeVariant = (classification: string): BadgeVariant => {
    switch (classification) {
      case "above_par":
        return "green";
      case "on_par":
        return "terra";
      default:
        return "high";
    }
  };

  return (
    <div className="max-w-[896px] mx-auto space-y-8">
      {/* Overall score */}
      <Card className="p-6">
        <CardHeader>
          <CardTitle className="text-display-md">Assessment Results</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-[14px] text-neutral-500 mb-2">Overall Score</p>
              <p className={`text-kpi font-bold ${getScoreColor(overallScore)}`}>
                {Math.round(overallScore * 100)}%
              </p>
            </div>
            <div className="text-right">
              <p className="text-[14px] text-neutral-500 mb-2">Classification</p>
              <Badge variant={getBadgeVariant(overallClassification)} showDot>
                {overallClassification.replace("_", " ").toUpperCase()}
              </Badge>
            </div>
          </div>
          <p className="mt-5 text-[14px] text-neutral-500">
            You answered <span className="font-semibold text-neutral-900">{totalCorrect}</span> out of <span className="font-semibold text-neutral-900">{totalQuestions}</span> questions correctly.
          </p>
        </CardContent>
      </Card>

      {/* Domain breakdown */}
      <Card className="p-6">
        <CardHeader>
          <CardTitle>Domain Breakdown</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {domainResults.map((domain) => (
            <div
              key={domain.domain_code}
              className="rounded-lg bg-surface-cream border border-surface-border p-4 flex items-center justify-between"
            >
              <div>
                <p className="font-semibold text-neutral-900">{domain.domain_name}</p>
                <p className="text-[14px] text-neutral-500">
                  <span className="font-semibold text-neutral-900">{domain.correct_count}</span>/<span className="font-semibold text-neutral-900">{domain.questions_count}</span> correct
                </p>
              </div>
              <div className="text-right flex items-center gap-3">
                <p className={`font-semibold text-[22px] tabular-nums ${getScoreColor(domain.score)}`}>
                  {Math.round(domain.score * 100)}%
                </p>
                <Badge variant={getBadgeVariant(domain.classification)} showDot>
                  {domain.classification.replace("_", " ").toUpperCase()}
                </Badge>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>

      {/* Gap analysis */}
      <Card className="p-6">
        <CardHeader>
          <CardTitle>Next Steps</CardTitle>
        </CardHeader>
        <CardContent className="space-y-5">
          {getGapArray("needs_work").length > 0 && (
            <div>
              <p className="text-[12px] font-semibold uppercase tracking-[.08em] text-[#a83030] mb-3">
                Focus On
              </p>
              <div className="flex gap-2">
                {getGapArray("needs_work").map((code) => (
                  <Badge key={code} variant="high" showDot>
                    {code}
                  </Badge>
                ))}
              </div>
            </div>
          )}
          {getGapArray("on_track").length > 0 && (
            <div>
              <p className="text-[12px] font-semibold uppercase tracking-[.08em] text-[#a87c2a] mb-3">
                Keep Practicing
              </p>
              <div className="flex gap-2">
                {getGapArray("on_track").map((code) => (
                  <Badge key={code} variant="terra" showDot>
                    {code}
                  </Badge>
                ))}
              </div>
            </div>
          )}
          {getGapArray("strengths").length > 0 && (
            <div>
              <p className="text-[12px] font-semibold uppercase tracking-[.08em] text-green-600 mb-3">
                Strengths
              </p>
              <div className="flex gap-2">
                {getGapArray("strengths").map((code) => (
                  <Badge key={code} variant="green" showDot>
                    {code}
                  </Badge>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Action buttons */}
      <div className="flex gap-4 pt-4">
        <Button onClick={() => router.push("/dashboard")} size="lg">
          Back to Dashboard
        </Button>
        <Button size="lg" variant="outline" onClick={() => window.print()}>
          Print Results
        </Button>
      </div>
    </div>
  );
}
