/**
 * Assessment results page.
 * Displays complete results after assessment completion.
 */

"use client";

import React, { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { ResultsSummary, AssessmentResultsProps } from "@/components/assessment/results-summary";
import { apiClient } from "@/lib/api-client";

export default function ResultsPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const assessmentId = searchParams.get("assessment");

  const [loading, setLoading] = useState(true);
  const [results, setResults] = useState<AssessmentResultsProps | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (assessmentId) {
      fetchResults(assessmentId);
    }
  }, [assessmentId]);

  const fetchResults = async (id: string) => {
    try {
      setLoading(true);
      const data = await apiClient.getResults(id);
      setResults(data);
    } catch (err) {
      console.error("Error fetching results:", err);
      setError("Failed to load results. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <p className="text-lg font-medium">Loading results...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <p className="text-red-600 mb-4">{error}</p>
          <Button onClick={() => router.push("/dashboard")}>
            Back to Dashboard
          </Button>
        </div>
      </div>
    );
  }

  if (!results) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <p className="text-lg font-medium">No results available.</p>
          <Button className="mt-4" onClick={() => router.push("/dashboard")}>
            Back to Dashboard
          </Button>
        </div>
      </div>
    );
  }

  return <ResultsSummary {...results} />;
}
