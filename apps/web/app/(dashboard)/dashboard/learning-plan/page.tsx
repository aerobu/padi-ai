"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@padi/ui/card";
import { Button } from "@padi/ui/button";
import { Badge } from "@padi/ui/badge";
import { Progress } from "@padi/ui/progress";

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

const trackLabels: Record<string, { label: string; color: string }> = {
  catch_up: { label: "Catch Up", color: "bg-red-100 text-red-800" },
  on_track: { label: "On Track", color: "bg-green-100 text-green-800" },
  accelerate: { label: "Accelerate", color: "bg-purple-100 text-purple-800" },
};

const moduleStatusColors: Record<string, string> = {
  locked: "bg-gray-100 text-gray-600",
  available: "bg-blue-100 text-blue-800",
  in_progress: "bg-yellow-100 text-yellow-800",
  completed: "bg-green-100 text-green-800",
};

export default function LearningPlanPage() {
  const params = useParams();
  const router = useRouter();
  const studentId = params.studentId as string;

  const [plan, setPlan] = useState<LearningPlan | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchLearningPlan();
  }, [studentId]);

  const fetchLearningPlan = async () => {
    try {
      setLoading(true);
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/v1/learning-plans/${studentId}`,
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem("auth_token")}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error("Failed to fetch learning plan");
      }

      const data = await response.json();
      setPlan(data.plan);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  const progressPercentage = plan
    ? (plan.completed_modules / plan.total_modules) * 100
    : 0;

  const estimatedWeeks = plan
    ? Math.round(plan.estimated_total_minutes / (20 * 3 * 5))
    : 0;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-muted-foreground">Loading learning plan...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center text-destructive">
          <p className="text-lg font-semibold">Error</p>
          <p className="text-muted-foreground">{error}</p>
          <Button onClick={fetchLearningPlan} className="mt-4">
            Try Again
          </Button>
        </div>
      </div>
    );
  }

  if (!plan) {
    return (
      <Card>
        <CardContent className="pt-6 text-center">
          <p className="text-muted-foreground">No learning plan found.</p>
          <Button asChild className="mt-4">
            <Link href={`/diagnostic/start/${studentId}`}>
              Start Diagnostic Assessment
            </Link>
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Your Learning Plan</h1>
          <p className="text-muted-foreground">
            Personalized path to math mastery
          </p>
        </div>
        <Badge className={trackLabels[plan.track].color}>
          {trackLabels[plan.track].label} Track
        </Badge>
      </div>

      {/* Progress Card */}
      <Card>
        <CardHeader>
          <CardTitle>Your Progress</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">
                {plan.completed_modules} of {plan.total_modules} modules completed
              </p>
              <p className="text-sm text-muted-foreground mt-1">
                Estimated completion: {estimatedWeeks} weeks
              </p>
            </div>
            <div className="text-right">
              <p className="text-2xl font-bold">{Math.round(progressPercentage)}%</p>
            </div>
          </div>
          <Progress value={progressPercentage} className="h-3" />
        </CardContent>
      </Card>

      {/* Modules */}
      <div className="space-y-4">
        <h2 className="text-2xl font-semibold">Modules</h2>
        {plan.modules.map((module) => (
          <Card key={module.id} className={module.status === "available" ? "ring-2 ring-primary" : ""}>
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div
                    className={`w-10 h-10 rounded-full flex items-center justify-center font-bold ${
                      module.status === "completed"
                        ? "bg-green-500 text-white"
                        : module.status === "available"
                        ? "bg-primary text-primary-foreground"
                        : "bg-gray-200 text-gray-600"
                    }`}
                  >
                    {module.sequence_order}
                  </div>
                  <div>
                    <h3 className="font-semibold text-lg">
                      {module.standard_code}
                    </h3>
                    <p className="text-sm text-muted-foreground">
                      {module.lessons?.length || 0} lessons, {module.estimated_minutes} min
                    </p>
                  </div>
                </div>
                <Badge className={moduleStatusColors[module.status]}>
                  {module.status.replace("_", " ").toUpperCase()}
                </Badge>
              </div>

              {/* Module Progress */}
              <div className="mb-4">
                <div className="flex items-center justify-between text-sm mb-1">
                  <span className="text-muted-foreground">Progress</span>
                  <span>
                    {module.completed_lessons} / {module.lesson_count}
                  </span>
                </div>
                <Progress
                  value={
                    (module.completed_lessons / module.lesson_count) * 100
                  }
                  className="h-2"
                />
              </div>

              {/* Lessons */}
              {module.lessons && module.lessons.length > 0 && (
                <div className="flex gap-2 mb-4">
                  {module.lessons.map((lesson) => (
                    <Badge
                      key={lesson.id}
                      variant={
                        lesson.status === "completed"
                          ? "default"
                          : lesson.status === "available"
                          ? "secondary"
                          : "outline"
                      }
                      className={
                        lesson.status === "completed"
                          ? "bg-green-100 text-green-800"
                          : lesson.status === "available"
                          ? "bg-blue-100 text-blue-800"
                          : ""
                      }
                    >
                      {lesson.lesson_type}
                    </Badge>
                  ))}
                </div>
              )}

              {/* Action Button */}
              {module.status === "available" && (
                <Button
                  onClick={() =>
                    router.push(`/diagnostic/active/${studentId}/practice?module=${module.id}`)
                  }
                  className="w-full"
                >
                  Start Lesson
                </Button>
              )}

              {module.status === "in_progress" && (
                <Button
                  variant="outline"
                  onClick={() =>
                    router.push(`/diagnostic/active/${studentId}/practice?module=${module.id}`)
                  }
                  className="w-full"
                >
                  Continue
                </Button>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
