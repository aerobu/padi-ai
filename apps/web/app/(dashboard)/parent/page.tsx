"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@padi/ui/card";
import { Button } from "@padi/ui/button";
import { Badge } from "@padi/ui/badge";
import { Progress } from "@padi/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@padi/ui/tabs";

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
  catch_up: {
    label: "Catch Up",
    description: "Focusing on foundational skills before moving to grade-level content",
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

export default function ParentDashboard() {
  const router = useRouter();

  const [students, setStudents] = useState<Student[]>([]);
  const [selectedStudentId, setSelectedStudentId] = useState<string | null>(null);
  const [plans, setPlans] = useState<Record<string, LearningPlan>>({});
  const [activities, setActivities] = useState<ActivityLog[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const token = localStorage.getItem("auth_token");
      if (!token) {
        router.push("/login");
        return;
      }

      // Fetch students (parent's children)
      const studentsResponse = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/v1/students`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      const studentsData = await studentsResponse.json();
      setStudents(studentsData.students || []);

      if (studentsData.students?.length > 0) {
        setSelectedStudentId(studentsData.students[0].id);
        fetchPlan(studentsData.students[0].id);
      }

      // Fetch recent activities
      const activitiesResponse = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/v1/activities/recent`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      const activitiesData = await activitiesResponse.json();
      setActivities(activitiesData.activities || []);
    } catch (error) {
      console.error("Error fetching dashboard data:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchPlan = async (studentId: string) => {
    try {
      const token = localStorage.getItem("auth_token");
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/v1/learning-plans/${studentId}`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      if (response.ok) {
        const data = await response.json();
        setPlans((prev) => ({ ...prev, [studentId]: data.plan }));
      }
    } catch (error) {
      console.error("Error fetching learning plan:", error);
    }
  };

  const selectedStudent = students.find((s) => s.id === selectedStudentId);
  const currentPlan = selectedStudentId ? plans[selectedStudentId] : null;

  const progressPercentage = currentPlan
    ? (currentPlan.completed_modules / currentPlan.total_modules) * 100
    : 0;

  const estimatedWeeks = currentPlan
    ? Math.round(currentPlan.estimated_total_minutes / (20 * 3 * 5))
    : 0;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-muted-foreground">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Parent Dashboard</h1>
        {students.length > 1 && (
          <select
            value={selectedStudentId || ""}
            onChange={(e) => {
              setSelectedStudentId(e.target.value);
              fetchPlan(e.target.value);
            }}
            className="p-2 border rounded-md"
          >
            {students.map((student) => (
              <option key={student.id} value={student.id}>
                {student.display_name} - Grade {student.grade_level}
              </option>
            ))}
          </select>
        )}
      </div>

      {selectedStudent && (
        <>
          {/* Student Header */}
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-4">
                <div className="w-16 h-16 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-2xl font-bold">
                  {selectedStudent.display_name.charAt(0)}
                </div>
                <div>
                  <h2 className="text-2xl font-semibold">{selectedStudent.display_name}</h2>
                  <p className="text-muted-foreground">Grade {selectedStudent.grade_level}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Tabs defaultValue="overview" className="space-y-6">
            <TabsList>
              <TabsTrigger value="overview">Overview</TabsTrigger>
              <TabsTrigger value="plan">Learning Plan</TabsTrigger>
              <TabsTrigger value="activity">Activity</TabsTrigger>
            </TabsList>

            <TabsContent value="overview" className="space-y-6">
              {/* Stats Cards */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-sm font-medium text-muted-foreground">
                      Learning Plan
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    {currentPlan ? (
                      <>
                        <p className="text-2xl font-bold">{Math.round(progressPercentage)}%</p>
                        <p className="text-sm text-muted-foreground">
                          {currentPlan.completed_modules}/{currentPlan.total_modules} modules
                        </p>
                      </>
                    ) : (
                      <p className="text-muted-foreground">No plan yet</p>
                    )}
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-sm font-medium text-muted-foreground">
                      Time to Mastery
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    {currentPlan ? (
                      <>
                        <p className="text-2xl font-bold">{estimatedWeeks}</p>
                        <p className="text-sm text-muted-foreground">weeks at 20 min/day</p>
                      </>
                    ) : (
                      <p className="text-muted-foreground">-</p>
                    )}
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-sm font-medium text-muted-foreground">
                      Track
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    {currentPlan ? (
                      <Badge
                        className={
                          currentPlan.track === "catch_up"
                            ? "bg-red-100 text-red-800"
                            : currentPlan.track === "accelerate"
                            ? "bg-purple-100 text-purple-800"
                            : "bg-green-100 text-green-800"
                        }
                      >
                        {trackLabels[currentPlan.track].label}
                      </Badge>
                    ) : (
                      <p className="text-muted-foreground">-</p>
                    )}
                  </CardContent>
                </Card>
              </div>

              {/* Progress Card */}
              {currentPlan && (
                <Card>
                  <CardHeader>
                    <CardTitle>Overall Progress</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <Progress value={progressPercentage} className="h-4" />
                    <p className="text-sm text-muted-foreground text-center">
                      {currentPlan.completed_lessons} of {currentPlan.total_lessons} lessons completed
                    </p>
                  </CardContent>
                </Card>
              )}
            </TabsContent>

            <TabsContent value="plan" className="space-y-4">
              {currentPlan ? (
                <>
                  <Card>
                    <CardHeader>
                      <CardTitle>Current Track</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-muted-foreground">
                        {trackLabels[currentPlan.track].description}
                      </p>
                    </CardContent>
                  </Card>

                  {currentPlan.modules && currentPlan.modules.length > 0 && (
                    <div className="space-y-2">
                      <h3 className="text-lg font-semibold">Modules</h3>
                      {currentPlan.modules.map((module) => (
                        <Card key={module.id}>
                          <CardContent className="p-4">
                            <div className="flex items-center justify-between mb-2">
                              <span className="font-medium">{module.standard_code}</span>
                              <Badge
                                className={
                                  module.status === "completed"
                                    ? "bg-green-100 text-green-800"
                                    : module.status === "available"
                                    ? "bg-blue-100 text-blue-800"
                                    : "bg-gray-100 text-gray-600"
                                }
                              >
                                {module.status}
                              </Badge>
                            </div>
                            <Progress
                              value={
                                (module.completed_lessons / module.lesson_count) * 100
                              }
                              className="h-2"
                            />
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                  )}

                  <Button asChild className="w-full mt-4">
                    <Link href={`/dashboard/learning-plan/${selectedStudent.id}`}>
                      View Full Learning Plan
                    </Link>
                  </Button>
                </>
              ) : (
                <Card>
                  <CardContent className="pt-6 text-center">
                    <p className="text-muted-foreground mb-4">
                      No learning plan yet. Start a diagnostic assessment to create one.
                    </p>
                    <Button asChild>
                      <Link href={`/diagnostic/start/${selectedStudent.id}`}>
                        Start Assessment
                      </Link>
                    </Button>
                  </CardContent>
                </Card>
              )}
            </TabsContent>

            <TabsContent value="activity" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Recent Activity</CardTitle>
                </CardHeader>
                <CardContent>
                  {activities.length > 0 ? (
                    <div className="space-y-4">
                      {activities.map((activity) => (
                        <div key={activity.id} className="flex items-start gap-4 pb-4 border-b last:border-0">
                          <div className="w-2 h-2 rounded-full bg-primary mt-2"></div>
                          <div className="flex-1">
                            <p className="font-medium">{activity.action}</p>
                            <p className="text-sm text-muted-foreground">
                              {activity.details}
                            </p>
                            <p className="text-xs text-muted-foreground mt-1">
                              {new Date(activity.timestamp).toLocaleString()}
                            </p>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-muted-foreground text-center">
                      No recent activity
                    </p>
                  )}
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </>
      )}
    </div>
  );
}
