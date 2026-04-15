/**
 * Assessment results summary component.
 */

"use client";

import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@padi/ui/card";
import { Badge } from "@padi/ui/badge";
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
  gapAnalysis = {},
}: AssessmentResultsProps) {
  const router = useRouter();

  // Safe access to gapAnalysis arrays
  const getGapArray = (key: keyof GapAnalysis) => gapAnalysis?.[key] ?? [];

  const getScoreColor = (score: number): string => {
    if (score >= 0.8) return "text-green-600";
    if (score >= 0.6) return "text-yellow-600";
    return "text-red-600";
  };

  const getClassificationBadge = (classification: string) => {
    switch (classification) {
      case "above_par":
        return <Badge className="bg-green-100 text-green-800">Above Par</Badge>;
      case "on_par":
        return <Badge className="bg-yellow-100 text-yellow-800">On Par</Badge>;
      default:
        return <Badge className="bg-red-100 text-red-800">Below Par</Badge>;
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Overall score */}
      <Card>
        <CardHeader>
          <CardTitle className="text-2xl">Assessment Results</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-600">Overall Score</p>
              <p className={`text-4xl font-bold ${getScoreColor(overallScore)}`}>
                {Math.round(overallScore * 100)}%
              </p>
            </div>
            <div className="text-right">
              <p className="text-sm text-slate-600">Classification</p>
              {getClassificationBadge(overallClassification)}
            </div>
          </div>
          <p className="mt-4 text-sm text-slate-600">
            You answered {totalCorrect} out of {totalQuestions} questions correctly.
          </p>
        </CardContent>
      </Card>

      {/* Domain breakdown */}
      <Card>
        <CardHeader>
          <CardTitle>Domain Breakdown</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {domainResults.map((domain) => (
              <div
                key={domain.domain_code}
                className="flex items-center justify-between p-3 rounded-lg bg-slate-50"
              >
                <div>
                  <p className="font-medium text-slate-900">{domain.domain_name}</p>
                  <p className="text-sm text-slate-600">
                    {domain.correct_count}/{domain.questions_count} correct
                  </p>
                </div>
                <div className="text-right">
                  <p className={`font-semibold ${getScoreColor(domain.score)}`}>
                    {Math.round(domain.score * 100)}%
                  </p>
                  {getClassificationBadge(domain.classification)}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Gap analysis */}
      <Card>
        <CardHeader>
          <CardTitle>Next Steps</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {getGapArray('needs_work').length > 0 && (
            <div>
              <p className="font-medium text-red-700 mb-2">Focus On:</p>
              <div className="flex flex-wrap gap-2">
                {getGapArray('needs_work').map((code) => (
                  <Badge key={code} variant="outline" className="text-red-700 border-red-300">
                    {code}
                  </Badge>
                ))}
              </div>
            </div>
          )}
          {getGapArray('on_track').length > 0 && (
            <div>
              <p className="font-medium text-yellow-700 mb-2">Keep Practicing:</p>
              <div className="flex flex-wrap gap-2">
                {getGapArray('on_track').map((code) => (
                  <Badge key={code} variant="outline" className="text-yellow-700 border-yellow-300">
                    {code}
                  </Badge>
                ))}
              </div>
            </div>
          )}
          {getGapArray('strengths').length > 0 && (
            <div>
              <p className="font-medium text-green-700 mb-2">Strengths:</p>
              <div className="flex flex-wrap gap-2">
                {getGapArray('strengths').map((code) => (
                  <Badge key={code} variant="outline" className="text-green-700 border-green-300">
                    {code}
                  </Badge>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Action buttons */}
      <div className="flex gap-4 justify-center">
        <Button onClick={() => router.push("/dashboard")}>Back to Dashboard</Button>
        <Button variant="outline" onClick={() => window.print()}>
          Print Results
        </Button>
      </div>
    </div>
  );
}
