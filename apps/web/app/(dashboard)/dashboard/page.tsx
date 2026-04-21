/**
 * Parent Dashboard.
 * Main landing page after login.
 */

"use client";

import React from "react";
import { useRouter } from "next/navigation";
import { Button } from "@padi/ui";

export default function DashboardPage() {
  const router = useRouter();

  // Get user info from localStorage
  const userId =
    typeof window !== "undefined"
      ? localStorage.getItem("user_id") || localStorage.getItem("parent_id")
      : null;

  const hasStudent =
    typeof window !== "undefined" ? localStorage.getItem("student_id") : null;

  const handleStartAssessment = () => {
    if (!hasStudent) {
      router.push("/onboarding/create-student");
    } else {
      router.push("/diagnostic/start");
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-slate-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-slate-200">
        <div className="container mx-auto max-w-6xl px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <span className="text-xl font-bold text-blue-700">PADI.AI</span>
              <span className="text-sm text-slate-500">| Parent Dashboard</span>
            </div>
            <Button variant="outline" onClick={() => router.push("/")}>
              Logout
            </Button>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="container mx-auto max-w-6xl px-4 py-8">
        {/* Welcome Section */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <h1 className="text-2xl font-bold text-slate-900 mb-2">
            Welcome to PADI.AI!
          </h1>
          <p className="text-slate-600">
            Adaptive Math Learning for Oregon Elementary Students
          </p>
        </div>

        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-sm font-medium text-slate-500 mb-1">
              Students
            </h3>
            <p className="text-3xl font-bold text-slate-900">
              {hasStudent ? "1" : "0"}
            </p>
          </div>
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-sm font-medium text-slate-500 mb-1">
              Assessments
            </h3>
            <p className="text-3xl font-bold text-slate-900">0</p>
          </div>
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-sm font-medium text-slate-500 mb-1">
              Average Score
            </h3>
            <p className="text-3xl font-bold text-slate-900">N/A</p>
          </div>
        </div>

        {/* Actions */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-lg font-semibold text-slate-900 mb-4">
            Quick Actions
          </h2>
          <div className="flex flex-wrap gap-4">
            <Button onClick={handleStartAssessment} size="lg">
              {hasStudent ? "Start Assessment" : "Create Student Profile"}
            </Button>
            <Button variant="outline" onClick={() => router.push("/diagnostic/results")}>
              View Results
            </Button>
          </div>
        </div>

        {/* Getting Started Guide */}
        <div className="mt-8 bg-blue-50 rounded-lg shadow-md p-6">
          <h2 className="text-lg font-semibold text-blue-900 mb-4">
            Getting Started
          </h2>
          <ol className="space-y-3 text-blue-800">
            <li className="flex items-start">
              <span className="font-semibold mr-2">1.</span>
              <span>Create your child&apos;s profile (if you haven&apos;t already)</span>
            </li>
            <li className="flex items-start">
              <span className="font-semibold mr-2">2.</span>
              <span>
                Start the diagnostic assessment (takes ~45 minutes)
              </span>
            </li>
            <li className="flex items-start">
              <span className="font-semibold mr-2">3.</span>
              <span>
                Receive detailed results showing your child&apos;s math proficiency
                across all Grade 4 domains
              </span>
            </li>
            <li className="flex items-start">
              <span className="font-semibold mr-2">4.</span>
              <span>
                Get personalized learning recommendations based on the results
              </span>
            </li>
          </ol>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-slate-200 mt-auto">
        <div className="container mx-auto max-w-6xl px-4 py-6">
          <div className="flex items-center justify-between text-sm text-slate-600">
            <span>© 2026 PADI.AI</span>
            <div className="flex space-x-4">
              <span className="hover:text-slate-900">Terms</span>
              <span className="hover:text-slate-900">Privacy</span>
              <span className="hover:text-slate-900">Support</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
