"use client";

import { useRouter } from "next/navigation";
import { cn } from "@/lib/utils";
import { Button } from "@padi/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@padi/ui/card";
import { Progress } from "@padi/ui/progress";
import { Badge } from "@padi/ui/badge";

const trackLabels: Record<string, { label: string }> = {
  catch_up: { label: "Catch Up" },
  on_track: { label: "On Track" },
  accelerate: { label: "Accelerate" },
};

export default function ParentDashboard() {
  const router = useRouter();
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-display-md text-neutral-900">Parent Dashboard</h1>
          <p className="text-body-md text-neutral-500 mt-1">Welcome back! Here&apos;s your child&apos;s progress overview.</p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" size="sm" onClick={() => router.push("/api/auth/login")}>
            Logout
          </Button>
        </div>
      </div>

      {/* Student Header */}
      <Card variant="hero" className="p-6 flex items-center gap-4">
        <div className="w-16 h-16 rounded-full bg-white/10 flex items-center justify-center text-[32px] font-bold text-white">
          J
        </div>
        <div>
          <h2 className="text-[24px] font-bold text-white">Jordan Smith</h2>
          <p className="text-[14px] text-white/55">Grade 4 · On Track</p>
        </div>
      </Card>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="p-6">
          <CardHeader>
            <CardTitle className="text-sm font-medium text-neutral-500">Learning Plan Progress</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <p className="text-kpi text-green-600">24%</p>
              <p className="text-[14px] text-neutral-500">3 of 12 modules completed</p>
              <Progress value={24} className="h-2" />
            </div>
          </CardContent>
        </Card>

        <Card className="p-6">
          <CardHeader>
            <CardTitle className="text-sm font-medium text-neutral-500">Time to Mastery</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-[22px] font-bold text-green-600">9</p>
            <p className="text-[14px] text-neutral-500 mt-1">weeks at 20 min/day practice</p>
          </CardContent>
        </Card>

        <Card className="p-6">
          <CardHeader>
            <CardTitle className="text-sm font-medium text-neutral-500">Current Track</CardTitle>
          </CardHeader>
          <CardContent>
            <Badge variant="green" showDot>On Track</Badge>
            <p className="text-[14px] text-neutral-500 mt-2">Making steady progress through the curriculum</p>
          </CardContent>
        </Card>
      </div>

      {/* Overall Progress */}
      <Card className="p-6">
        <CardHeader>
          <CardTitle>Overall Learning Progress</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <Progress value={24} className="h-3" />
          <p className="text-[14px] text-neutral-500 text-center">
            3 of 12 modules · 2 of 48 lessons completed
          </p>
        </CardContent>
      </Card>

      {/* Modules */}
      <div className="space-y-4">
        <h2 className="font-display text-display-sm text-neutral-900">Learning Modules</h2>
        {[
          { code: "4.NBT", name: "Place Value", status: "completed", progress: 100, lessons: "Instruction · Practice · Review" },
          { code: "4.OA", name: "Algebraic Thinking", status: "completed", progress: 100, lessons: "Instruction · Practice" },
          { code: "4.NF", name: "Fractions", status: "in_progress", progress: 45, lessons: "Instruction · Practice" },
          { code: "4.MD", name: "Measurement", status: "available", progress: 0, lessons: "Instruction · Practice · Review · Assessment" },
          { code: "4.G", name: "Geometry", status: "available", progress: 0, lessons: "Instruction · Practice" },
        ].map((mod) => (
          <Card key={mod.code} className={mod.status === "available" ? "ring-2 ring-green-500" : ""}>
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
                    {mod.code.split(".")[0]}
                  </div>
                  <div>
                    <h3 className="font-semibold text-neutral-900">{mod.code}</h3>
                    <p className="text-[14px] text-neutral-500">{mod.name}</p>
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
                value={mod.progress}
                color={mod.status === "completed" ? "green" : mod.status === "in_progress" ? "terra" : "neutral"}
                className="h-2 mb-3"
              />

              <div className="flex gap-1.5 flex-wrap">
                {mod.lessons.split(" · ").map((lesson, i) => (
                  <Badge key={i} variant={i % 2 === 0 ? "default" : "terra"} size="sm" showDot>
                    {lesson}
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Quick Actions */}
      <div className="flex gap-4 pt-4">
        <Button size="lg" className="w-full sm:w-auto" onClick={() => router.push("/diagnostic/start")}>
          Start Assessment
        </Button>
        <Button variant="outline" size="lg" className="w-full sm:w-auto" onClick={() => router.push("/diagnostic/results")}>
          View Results
        </Button>
      </div>
    </div>
  );
}
