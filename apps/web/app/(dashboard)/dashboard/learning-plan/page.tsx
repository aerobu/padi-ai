"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { cn } from "@/lib/utils";
import { Card, CardContent, CardHeader, CardTitle } from "@padi/ui/card";
import { Button } from "@padi/ui/button";
import { Badge } from "@padi/ui/badge";
import { Progress } from "@padi/ui/progress";
import { HeroCard } from "@padi/ui/hero-card";
import { Divider } from "@padi/ui/divider";

interface Module {
  id: string;
  standard_code: string;
  module_name: string;
  sequence_order: number;
  status: "locked" | "available" | "in_progress" | "completed";
  lesson_count: number;
  completed_lessons: number;
  estimated_minutes: number;
  entry_p_mastery: number;
  exit_p_mastery: number;
  lessons?: Lesson[];
}

interface Lesson {
  id: string;
  sequence_order: number;
  lesson_type: "instruction" | "practice" | "review" | "assessment";
  title: string;
  status: "locked" | "available" | "in_progress" | "completed";
  question_count: number;
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
  modules: Module[];
}

const trackLabels: Record<string, { label: string; badge: string }> = {
  catch_up: { label: "Catch Up", badge: "terra" },
  on_track: { label: "On Track", badge: "green" },
  accelerate: { label: "Accelerate", badge: "green" },
};

export default function LearningPlanPage() {
  const params = useParams();
  const studentId = params.studentId as string;
  const [plan, setPlan] = useState<LearningPlan | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setPlan({
      id: "demo",
      student_id: studentId,
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
        { id: "1", standard_code: "4.NBT", module_name: "Place Value", sequence_order: 1, status: "completed", lesson_count: 4, completed_lessons: 4, estimated_minutes: 180, entry_p_mastery: 0, exit_p_mastery: 0.9, lessons: [{ id: "1a", sequence_order: 1, lesson_type: "instruction", title: "Intro", status: "completed", question_count: 0 }] },
        { id: "2", standard_code: "4.OA", module_name: "Algebraic Thinking", sequence_order: 2, status: "completed", lesson_count: 3, completed_lessons: 3, estimated_minutes: 120, entry_p_mastery: 0, exit_p_mastery: 0.85, lessons: [] },
        { id: "3", standard_code: "4.NF", module_name: "Fractions", sequence_order: 3, status: "in_progress", lesson_count: 5, completed_lessons: 2, estimated_minutes: 240, entry_p_mastery: 0.3, exit_p_mastery: 0.8, lessons: [] },
        { id: "4", standard_code: "4.MD", module_name: "Measurement", sequence_order: 4, status: "available", lesson_count: 4, completed_lessons: 0, estimated_minutes: 200, entry_p_mastery: 0.1, exit_p_mastery: 0.8, lessons: [] },
        { id: "5", standard_code: "4.G", module_name: "Geometry", sequence_order: 5, status: "available", lesson_count: 3, completed_lessons: 0, estimated_minutes: 150, entry_p_mastery: 0.2, exit_p_mastery: 0.8, lessons: [] },
      ],
    });
    setLoading(false);
  }, [studentId]);

  const progressPercentage = plan ? (plan.completed_modules / plan.total_modules) * 100 : 0;
  const estimatedWeeks = plan ? Math.round(plan.estimated_total_minutes / (20 * 3 * 5)) : 0;
  const trackInfo = trackLabels[plan?.track || "on_track"];

  if (loading) {
    return (
      <div className="flex items-center justify-center" style={{ minHeight: "48vh" }}>
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-2 border-neutral-200 border-t-green-600 mx-auto" />
          <p className="mt-4 text-[14px] text-neutral-500">Loading...</p>
        </div>
      </div>
    );
  }

  if (!plan) {
    return (
      <Card className="p-6 text-center">
        <p className="text-[14px] text-neutral-500">No learning plan found.</p>
        <Button asChild className="mt-4">
          <Link href="/diagnostic/start">Start Assessment</Link>
        </Button>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="font-display text-display-md text-neutral-900">Learning Plan</h1>
          <p className="text-[16px] text-neutral-500 mt-1">Personalized path to math mastery</p>
        </div>
        <Badge variant={trackInfo.badge as any} showDot>{trackInfo.label} Track</Badge>
      </div>

      {/* Overall Progress */}
      <HeroCard label="Overall Progress" value={`${Math.round(progressPercentage)}%`} sub={`${plan.completed_modules} of ${plan.total_modules} modules · ${estimatedWeeks} weeks remaining`} />

      {/* Module Cards */}
      <div className="space-y-4">
        <h2 className="text-display-sm text-neutral-900">Modules</h2>
        {plan.modules.map((mod) => (
          <Card key={mod.id} className={mod.status === "available" ? "ring-2 ring-green-500" : ""}>
            <CardContent className="p-5">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div
                    className={cn(
                      "w-10 h-10 rounded-full flex items-center justify-center font-bold text-[14px]",
                      mod.status === "completed" ? "bg-green-600 text-white" :
                      mod.status === "in_progress" ? "bg-terra-500 text-white" :
                      "bg-neutral-200 text-neutral-600",
                    )}
                  >
                    {mod.sequence_order}
                  </div>
                  <div>
                    <h3 className="font-semibold text-neutral-900">{mod.standard_code}</h3>
                    <p className="text-[14px] text-neutral-500">{mod.lesson_count} lessons · {mod.estimated_minutes} min</p>
                  </div>
                </div>
                <Badge
                  variant={
                    mod.status === "completed" ? "green" :
                    mod.status === "in_progress" ? "terra" :
                    "default"
                  }
                  showDot
                >
                  {mod.status.replace("_", " ").toUpperCase()}
                </Badge>
              </div>

              <Progress
                value={mod.status === "completed" ? 100 : (mod.completed_lessons / mod.lesson_count) * 100}
                color={mod.status === "completed" ? "green" : "neutral"}
                className="h-2 mb-3"
              />

              {mod.lessons && mod.lessons.length > 0 && (
                <div className="flex gap-1.5">
                  {mod.lessons.map((lesson) => (
                    <Badge key={lesson.id} variant={lesson.status === "completed" ? "green" : "default"} size="sm" showDot>
                      {lesson.lesson_type}
                    </Badge>
                  ))}
                </div>
              )}

              <Divider />
              <div className="flex gap-3">
                {mod.status === "available" && (
                  <Button size="sm" className="flex-1">
                    Start Lesson
                  </Button>
                )}
                {mod.status === "in_progress" && (
                  <Button size="sm" variant="outline" className="flex-1">
                    Continue
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
