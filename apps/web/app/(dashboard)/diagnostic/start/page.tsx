/**
 * Diagnostic Assessment Start page.
 * Initiates a new diagnostic assessment.
 */

"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@padi/ui";
import { apiClient } from "@/lib/api-client";

export default function DiagnosticStartPage() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Get student ID from localStorage
  const studentId =
    typeof window !== "undefined"
      ? localStorage.getItem("student_id")
      : null;

  const handleStartAssessment = async () => {
    if (!studentId) {
      setError("Please create a student profile first.");
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      // Start assessment
      const response = await apiClient.startAssessment(studentId);

      // Store session ID
      if (typeof window !== "undefined") {
        localStorage.setItem("assessment_session_id", response.session_id);
        localStorage.setItem("assessment_id", response.assessment_id);
      }

      // Navigate to active assessment
      router.push(`/diagnostic/active/${response.session_id}`);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to start assessment"
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-slate-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-slate-200">
        <div className="container mx-auto max-w-4xl px-4 py-4">
          <div className="flex items-center space-x-2">
            <a href="/dashboard" className="text-sm text-blue-600 hover:underline">
              ← Back to Dashboard
            </a>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="container mx-auto max-w-4xl px-4 py-8">
        <div className="bg-white rounded-lg shadow-md p-6 md:p-8">
          <h1 className="text-2xl font-bold text-slate-900 mb-4">
            Diagnostic Assessment
          </h1>

          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-700">{error}</p>
            </div>
          )}

          <div className="space-y-4 mb-6">
            <p className="text-slate-700">
              This adaptive diagnostic assessment will evaluate your child&apos;s
              math skills across the Grade 4 Oregon math standards.
            </p>

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h3 className="font-semibold text-blue-900 mb-2">
                Assessment Details:
              </h3>
              <ul className="text-sm text-blue-800 space-y-1 list-disc list-inside">
                <li>Approximately 35-45 questions</li>
                <li>Adaptive difficulty based on responses</li>
                <li>Estimated time: 45-60 minutes</li>
                <li>Covers all major Grade 4 math domains</li>
                <li>Provides detailed skill proficiency report</li>
              </ul>
            </div>

            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <p className="text-sm text-yellow-800">
                <strong>Note:</strong> Make sure your child is in a quiet
                environment and has enough time to complete the assessment in one
                sitting.
              </p>
            </div>
          </div>

          <div className="flex justify-end space-x-4">
            <Button variant="outline" onClick={() => router.push("/dashboard")}>
              Cancel
            </Button>
            <Button
              onClick={handleStartAssessment}
              disabled={isLoading}
              size="lg"
            >
              {isLoading ? "Starting..." : "Start Assessment"}
            </Button>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-slate-200 mt-auto">
        <div className="container mx-auto max-w-4xl px-4 py-6">
          <div className="flex items-center justify-between text-sm text-slate-600">
            <span>© 2026 PADI.AI</span>
            <div className="flex space-x-4">
              <span className="hover:text-slate-900">Terms</span>
              <span className="hover:text-slate-900">Privacy</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
