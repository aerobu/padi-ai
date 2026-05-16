"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { cn } from "@/lib/utils";
import { Card, CardContent, CardHeader, CardTitle } from "@padi/ui/card";
import { Button } from "@padi/ui/button";
import { Badge } from "@padi/ui/badge";
import { Progress } from "@padi/ui/progress";
import { HeroCard } from "@padi/ui/hero-card";
import { Divider } from "@padi/ui/divider";
import Link from "next/link";

interface Student {
  id: string;
  display_name: string;
  grade_level: number;
  avatar_id: string;
}

interface LearningPlan {
  id: string;
  student_id: string;
  track: "catch_up" | "on_track" | "accelerate";
  status: string;
  total_modules: number;
  completed_modules: number;
  total_lessons: number;
  completed_lessons: number;
  estimated_total_minutes: number;
  estimated_completion_date: string;
  created_at: string;
  modules: Array<{
    id: string;
    standard_code: string;
    status: string;
    completed_lessons: number;
    lesson_count: number;
  }>;
}

interface ActivityLog {
  id: string;
  student_id: string;
  action: string;
  timestamp: string;
  details: string;
}

const trackLabels: Record<string, { label: string; description: string }> = {
  catch_up: { label: "Catch Up", description: "Focusing on foundational skills before moving to grade-level content" },
  on_track: { label: "On Track", description: "Making steady progress through the curriculum" },
  accelerate: { label: "Accelerate", description: "Ready for advanced challenges and enrichment" },
};

export default function ParentDashboard() {
  const router = useRouter();
  const [selectedStudentId] = useState<string | null>("demo-student");
  const [currentPlan] = useState<LearningPlan | null>({
    id: "demo",
    student_id: "demo-student",
    track: "on_track",
    status: "active",
    total_modules: 12,
    completed_modules: 3,
    total_lessons: 48,
    completed_lessons: 2,
    estimated_total_minutes: 3600,
    estimated_completion_date: "2026-08-15",
    created_at: "2026-04-01",
    modules: [
      { id: "1", standard_code: "4.NBT", status: "completed", completed_lessons: 4, lesson_count: 4 },
      { id: "2", standard_code: "4.OA", status: "completed", completed_lessons: 3, lesson_count: 3 },
      { id: "3", standard_code: "4.NF", status: "in_progress", completed_lessons: 2, lesson_count: 5 },
      { id: "4", standard_code: "4.MD", status: "available", completed_lessons: 0, lesson_count: 4 },
      { id: "5", standard_code: "4.G", status: "available", completed_lessons: 0, lesson_count: 3 },
    ],
  });
  const [loading] = useState(false);

  const progressPercentage = currentPlan ? (currentPlan.completed_modules / currentPlan.total_modules) * 100 : 0;
  const estimatedWeeks = currentPlan ? Math.round(currentPlan.estimated_total_minutes / (20 * 3 * 5)) : 0;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-2 border-neutral-200 border-t-green-600 mx-auto" />
          <p className="mt-4 text-[14px] text-neutral-500">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Student Header */}
      <HeroCard label="Jordan Smith · Grade 4" value="On Track" sub="Making steady progress through the curriculum" />

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="p-6">
          <CardHeader>
            <CardTitle className="text-[12px] font-semibold uppercase tracking-[.06em] text-neutral-400">Learning Plan Progress</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <p className="text-[22px] font-bold tabular-nums text-green-600">25%</p>
              <p className="text-[14px] text-neutral-500">{currentPlan?.completed_modules} of {currentPlan?.total_modules} modules</p>
              <Progress value={progressPercentage} className="h-2" color="green" />
            </div>
          </CardContent>
        </Card>

        <Card className="p-6">
          <CardHeader>
            <CardTitle className="text-[12px] font-semibold uppercase tracking-[.06em] text-neutral-400">Time to Mastery</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-[22px] font-bold tabular-nums text-green-600">{estimatedWeeks}</p>
            <p className="text-[14px] text-neutral-500 mt-1">weeks at 20 min/day</p>
          </CardContent>
        </Card>

        <Card className="p-6">
          <CardHeader>
            <CardTitle className="text-[12px] font-semibold uppercase tracking-[.06em] text-neutral-400">Current Track</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {currentPlan && (
              <Badge variant="green" showDot>{trackLabels[currentPlan.track].label}</Badge>
            )}
            <p className="text-[14px] text-neutral-500">{trackLabels[currentPlan?.track || "on_track"].description}</p>
          </CardContent>
        </Card>
      </div>

      {/* Overall Progress */}
      <Card className="p-6">
        <CardHeader>
          <CardTitle>Overall Progress</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {currentPlan && (
            <>
              <Progress value={progressPercentage} className="h-3" color="green" />
              <p className="text-[14px] text-neutral-500 text-center">
                {currentPlan.completed_lessons} of {currentPlan.total_lessons} lessons completed
              </p>
            </>
          )}
        </CardContent>
      </Card>

      {/* Module Cards */}
      <div className="space-y-4">
        <h2 className="text-display-sm text-neutral-900">Modules</h2>
        {currentPlan?.modules.map((module) => (
          <Card key={module.id} className={module.status === "available" ? "ring-2 ring-green-500" : ""}>
            <CardContent className="p-5">
              <div className="flex items-center justify-between mb-4">
                <span className="font-semibold text-neutral-900">{module.standard_code}</span>
                <Badge
                  variant={
                    module.status === "completed" ? "green" :
                    module.status === "in_progress" ? "terra" :
                    "default"
                  }
                  showDot
                >
                  {module.status}
                </Badge>
              </div>
              <Progress
                value={(module.completed_lessons / module.lesson_count) * 100}
                color={module.status === "completed" ? "green" : "neutral"}
                className="h-2"
              />
            </CardContent>
          </Card>
        ))}
      </div>

      <Divider />
      <div className="flex gap-4">
        {currentPlan && (
          <Button asChild size="lg">
            <Link href={`/dashboard/learning-plan/${selectedStudentId}`}>
              View Full Learning Plan
            </Link>
          </Button>
        )}
        <Button asChild size="lg" variant="outline">
          <Link href="/diagnostic/start">Start Assessment</Link>
        </Button>
      </div>
    </div>
  );
}
