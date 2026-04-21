/**
 * COPPA Consent page.
 * Parental consent form for COPPA compliance.
 */

"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { ConsentForm } from "@/components/assessment/ConsentForm";
import { apiClient } from "@/lib/api-client";

export default function ConsentPage() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Get parent ID from localStorage (set after Auth0 login)
  const parentId =
    typeof window !== "undefined"
      ? localStorage.getItem("parent_id") || localStorage.getItem("user_id")
      : "guest-parent";

  const handleConsentGranted = async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Navigate to create student page after consent
      router.push("/onboarding/create-student");
    } catch (err) {
      setError("Failed to process consent. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleConsentDenied = () => {
    setError("Consent is required to use PADI.AI. Please check both boxes.");
  };

  const handleError = (msg: string) => {
    setError(msg);
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6 md:p-8">
      <h1 className="text-2xl font-bold text-slate-900 mb-2">
        Parental Consent Required
      </h1>
      <p className="text-slate-600 mb-6">
        Under the Children&apos;s Online Privacy Protection Act (COPPA), we
        require your consent before collecting any information from students
        under 13 years of age.
      </p>

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-700">{error}</p>
        </div>
      )}

      <ConsentForm
        parentId={parentId}
        onConsentGranted={handleConsentGranted}
        onConsentDenied={handleConsentDenied}
        onError={handleError}
        isLoading={isLoading}
      />

      <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <h3 className="font-semibold text-blue-900 mb-2">
          What information will be collected?
        </h3>
        <ul className="text-sm text-blue-800 space-y-1 list-disc list-inside">
          <li>Student&apos;s name (first name only, no last name)</li>
          <li>Grade level</li>
          <li>Math assessment results</li>
          <li>Learning progress over time</li>
        </ul>
        <p className="text-sm text-blue-800 mt-2">
          No personally identifiable information will be shared with third
          parties without your explicit consent.
        </p>
      </div>
    </div>
  );
}
