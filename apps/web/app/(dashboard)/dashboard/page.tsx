"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { Card, CardContent, CardHeader, CardTitle } from "@padi/ui/card";
import { Button } from "@padi/ui/button";
import { Badge } from "@padi/ui/badge";
import { Progress } from "@padi/ui/progress";
import { HeroCard } from "@padi/ui/hero-card";
import { Divider } from "@padi/ui/divider";

import { apiClient, ApiRequestError } from "@/lib/api-client";

interface PlanModuleSummary {
  id: string;
  standard_id: string;
  standard_code: string;
  status: string;
  completed_lessons: number;
  lesson_count: number;
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
  estimated_completion_date: string | null;
  modules: PlanModuleSummary[];
}

interface Student {
  id: string;
  display_name: string;
  grade_level: number;
  avatar_id?: string;
}

const trackLabels: Record<
  string,
  { label: string; description: string }
> = {
  catch_up: {
    label: "Catch Up",
    description: "Focusing on foundational skills before grade-level content",
  },
  on_track: {
    label: "On Track",
    description: "Making steady progress through the curriculum",
  },
  accelerate: {
    label: "Accelerate",
    description: "Ready for advanced challenges and enrichment",
  },
};

export default function StudentDashboardPage() {
  const router = useRouter();
  const [students, setStudents] = useState<Student[]>([]);
  const [selectedStudent, setSelectedStudent] = useState<Student | null>(null);
  const [plan, setPlan] = useState<LearningPlan | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const list = (await apiClient.listStudents()) as Student[];
        if (cancelled) return;
        setStudents(list);
        const first = list[0] ?? null;
        setSelectedStudent(first);
        if (first) {
          try {
            const planResp = (await apiClient.getLearningPlan(first.id)) as {
              plan: LearningPlan;
            };
            if (!cancelled) setPlan(planResp.plan);
          } catch (e) {
            if (e instanceof ApiRequestError && e.status === 404) {
              setPlan(null); // no plan yet — show empty state
            } else {
              throw e;
            }
          }
        }
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : "Failed to load dashboard");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-2 border-neutral-200 border-t-green-600 mx-auto" />
          <p className="mt-4 text-[14px] text-neutral-500">Loading dashboard…</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <Card className="p-6">
        <CardHeader>
          <CardTitle>Couldn&apos;t load your dashboard</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-[14px] text-neutral-500">{error}</p>
          <Button onClick={() => router.refresh()}>Try again</Button>
        </CardContent>
      </Card>
    );
  }

  if (!selectedStudent) {
    return (
      <Card className="p-6">
        <CardHeader>
          <CardTitle>Welcome to PADI.AI</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-[14px] text-neutral-500">
            Let&apos;s set up your first student to get started.
          </p>
          <Button asChild>
            <Link href="/create-student">Add a student</Link>
          </Button>
        </CardContent>
      </Card>
    );
  }

  const trackInfo = plan ? trackLabels[plan.track] : null;
  const progressPercentage = plan
    ? plan.total_modules
      ? (plan.completed_modules / plan.total_modules) * 100
      : 0
    : 0;
  const estimatedWeeks = plan
    ? Math.max(1, Math.round(plan.estimated_total_minutes / (20 * 3 * 5)))
    : 0;

  return (
    <div className="space-y-6">
      <HeroCard
        label={`${selectedStudent.display_name} · Grade ${selectedStudent.grade_level}`}
        value={trackInfo ? trackInfo.label : "Not started"}
        sub={
          trackInfo
            ? trackInfo.description
            : "Start a diagnostic to see your personalized plan"
        }
      />

      {plan ? (
        <>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card className="p-6">
              <CardHeader>
                <CardTitle className="text-[12px] font-semibold uppercase tracking-[.06em] text-neutral-400">
                  Learning Plan Progress
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <p className="text-[22px] font-bold tabular-nums text-green-600">
                    {Math.round(progressPercentage)}%
                  </p>
                  <p className="text-[14px] text-neutral-500">
                    {plan.completed_modules} of {plan.total_modules} modules
                  </p>
                  <Progress
                    value={progressPercentage}
                    className="h-2"
                    color="green"
                  />
                </div>
              </CardContent>
            </Card>

            <Card className="p-6">
              <CardHeader>
                <CardTitle className="text-[12px] font-semibold uppercase tracking-[.06em] text-neutral-400">
                  Time to Mastery
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-[22px] font-bold tabular-nums text-green-600">
                  {estimatedWeeks}
                </p>
                <p className="text-[14px] text-neutral-500 mt-1">
                  weeks at 20 min/day
                </p>
              </CardContent>
            </Card>

            <Card className="p-6">
              <CardHeader>
                <CardTitle className="text-[12px] font-semibold uppercase tracking-[.06em] text-neutral-400">
                  Current Track
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {trackInfo && (
                  <Badge variant="green" showDot>
                    {trackInfo.label}
                  </Badge>
                )}
                <p className="text-[14px] text-neutral-500">
                  {trackInfo?.description}
                </p>
              </CardContent>
            </Card>
          </div>

          <Card className="p-6">
            <CardHeader>
              <CardTitle>Overall Progress</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <Progress
                value={progressPercentage}
                className="h-3"
                color="green"
              />
              <p className="text-[14px] text-neutral-500 text-center">
                {plan.completed_lessons} of {plan.total_lessons} lessons completed
              </p>
            </CardContent>
          </Card>

          <div className="space-y-4">
            <h2 className="text-display-sm text-neutral-900">Modules</h2>
            {plan.modules.map((m) => (
              <Card
                key={m.id}
                className={m.status === "available" ? "ring-2 ring-green-500" : ""}
              >
                <CardContent className="p-5">
                  <div className="flex items-center justify-between mb-4">
                    <span className="font-semibold text-neutral-900">
                      {m.standard_code}
                    </span>
                    <Badge
                      variant={
                        m.status === "completed"
                          ? "green"
                          : m.status === "in_progress"
                          ? "terra"
                          : "default"
                      }
                      showDot
                    >
                      {m.status.replace("_", " ")}
                    </Badge>
                  </div>
                  <Progress
                    value={
                      m.lesson_count
                        ? (m.completed_lessons / m.lesson_count) * 100
                        : 0
                    }
                    color={m.status === "completed" ? "green" : "neutral"}
                    className="h-2"
                  />
                </CardContent>
              </Card>
            ))}
          </div>

          <Divider />
          <div className="flex gap-4">
            <Button asChild size="lg">
              <Link href={`/dashboard/learning-plan/${selectedStudent.id}`}>
                View Full Learning Plan
              </Link>
            </Button>
            <Button asChild size="lg" variant="outline">
              <Link href="/diagnostic/start">Start Practice</Link>
            </Button>
          </div>
        </>
      ) : (
        <Card className="p-6">
          <CardHeader>
            <CardTitle>No learning plan yet</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-[14px] text-neutral-500">
              Take the diagnostic assessment to generate a personalized plan.
            </p>
            <Button asChild size="lg">
              <Link href="/diagnostic/start">Start Diagnostic</Link>
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
