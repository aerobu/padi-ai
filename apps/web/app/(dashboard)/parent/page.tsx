"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { Button } from "@padi/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@padi/ui/card";
import { Progress } from "@padi/ui/progress";
import { Badge } from "@padi/ui/badge";

import { apiClient, ApiRequestError } from "@/lib/api-client";

interface ChildSummary {
  child_id: string;
  name: string;
  grade: number;
  track: string | null;
  plan_start: string | null;
  estimated_completion: string | null;
  overall_progress: number;
  modules_completed: number;
  total_modules: number;
}

interface DashboardResponse {
  children: ChildSummary[];
}

const trackLabels: Record<string, string> = {
  catch_up: "Catch Up",
  on_track: "On Track",
  accelerate: "Accelerate",
};

function loadUserIdFromCookie(): string | null {
  if (typeof document === "undefined") return null;
  const match = document.cookie.match(/padi_user_id=([^;]+)/);
  return match ? decodeURIComponent(match[1]) : null;
}

export default function ParentDashboardPage() {
  const router = useRouter();
  const [children, setChildren] = useState<ChildSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const userId = loadUserIdFromCookie();
      if (!userId) {
        setError("Sign in to view your dashboard.");
        setLoading(false);
        return;
      }
      try {
        const data = (await apiClient.getParentDashboard(userId)) as DashboardResponse;
        if (!cancelled) setChildren(data.children ?? []);
      } catch (e) {
        if (!cancelled) {
          if (e instanceof ApiRequestError && e.status === 401) {
            router.push("/login");
            return;
          }
          setError(e instanceof Error ? e.message : "Failed to load dashboard");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [router]);

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

  if (children.length === 0) {
    return (
      <Card className="p-6">
        <CardHeader>
          <CardTitle>No children yet</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-[14px] text-neutral-500">
            Add a child profile to start tracking their progress.
          </p>
          <Button onClick={() => router.push("/create-student")}>
            Add a child
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-display-md text-neutral-900">
            Parent Dashboard
          </h1>
          <p className="text-body-md text-neutral-500 mt-1">
            Welcome back! Here&apos;s how your children are progressing.
          </p>
        </div>
      </div>

      <div className="space-y-4">
        {children.map((child) => (
          <Card key={child.child_id} className="p-6">
            <CardContent className="space-y-4 p-0">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-[18px] font-semibold text-neutral-900">
                    {child.name}
                  </h2>
                  <p className="text-[14px] text-neutral-500">
                    Grade {child.grade}
                    {child.track ? ` · ${trackLabels[child.track] ?? child.track}` : ""}
                  </p>
                </div>
                {child.track && (
                  <Badge variant="green" showDot>
                    {trackLabels[child.track] ?? child.track}
                  </Badge>
                )}
              </div>

              {child.total_modules > 0 ? (
                <>
                  <Progress
                    value={child.overall_progress * 100}
                    className="h-2"
                    color="green"
                  />
                  <p className="text-[14px] text-neutral-500">
                    {child.modules_completed} of {child.total_modules} modules
                    completed
                  </p>
                </>
              ) : (
                <p className="text-[14px] text-neutral-500">
                  No learning plan yet — start the diagnostic to generate one.
                </p>
              )}

              <div className="flex gap-3">
                <Button
                  size="sm"
                  onClick={() =>
                    router.push(`/dashboard/learning-plan/${child.child_id}`)
                  }
                >
                  View plan
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => router.push("/diagnostic/start")}
                >
                  Start practice
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
