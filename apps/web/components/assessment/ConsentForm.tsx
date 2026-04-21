"use client";

/**
 * ConsentForm component
 *
 * COPPA compliance requires explicit parental consent with two checkboxes:
 * 1. Parent/guardian attestation
 * 2. Data collection consent
 */

import React, { useState } from "react";
import { apiClient } from "@/lib/api-client";

interface ConsentFormProps {
  onSubmit?: () => void;
  parentId?: string;
  onConsentGranted?: () => void;
  onConsentDenied?: () => void;
  onError?: (error: string) => void;
  consentStatus?: "granted" | "denied" | "pending";
  isLoading?: boolean;
}

export function ConsentForm({
  onSubmit,
  parentId,
  onConsentGranted,
  onConsentDenied,
  onError,
  consentStatus,
  isLoading,
}: ConsentFormProps) {
  const [isParentGuardian, setIsParentGuardian] = useState(false);
  const [dataConsent, setDataConsent] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleSubmit = async () => {
    // Reset any previous errors
    setErrorMessage(null);

    // Validate both checkboxes are checked
    if (!isParentGuardian || !dataConsent) {
      const error = "Please check both boxes to continue";
      setErrorMessage(error);
      onError?.(error);
      return;
    }

    try {
      // Use real initiateConsent method
      await apiClient.initiateConsent({
        student_display_name: "Student",
        acknowledgements: ["data_collection", "data_use"],
      });

      onSubmit?.();
      onConsentGranted?.();
    } catch (error) {
      const errorMsg = "Failed to submit consent. Please try again";
      setErrorMessage(errorMsg);
      onError?.(errorMsg);
    }
  };

  if (consentStatus === "granted") {
    return (
      <div>
        <h2>Consent granted</h2>
        <p>You can now proceed.</p>
      </div>
    );
  }

  if (consentStatus === "denied") {
    return (
      <div>
        <h2>Consent denied</h2>
        <p>Access is not available.</p>
      </div>
    );
  }

  if (consentStatus === "pending") {
    return (
      <div>
        <h2>Consent pending</h2>
        <p>Please wait for confirmation.</p>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div role="status">
        <p>Processing...</p>
      </div>
    );
  }

  return (
    <div>
      <h2>Parental Consent</h2>

      {errorMessage && (
        <div role="alert">{errorMessage}</div>
      )}

      <label className="flex items-start gap-3">
        <input
          type="checkbox"
          checked={isParentGuardian}
          onChange={(e) => setIsParentGuardian(e.target.checked)}
          aria-required="true"
          id="parent-guardian-checkbox"
        />
        <span>
          I am the parent or legal guardian of the child I am enrolling, and I am
          at least 18 years old.
        </span>
      </label>

      <label className="flex items-start gap-3">
        <input
          type="checkbox"
          checked={dataConsent}
          onChange={(e) => setDataConsent(e.target.checked)}
          aria-required="true"
          id="data-consent-checkbox"
        />
        <span>
          I consent to the collection and processing of my child&apos;s first name,
          grade level, and assessment responses for the purpose of providing
          personalized math instruction, as described in the{" "}
          <a href="/privacy" className="underline">
            Privacy Policy
          </a>
          .
        </span>
      </label>

      <div className="mb-4">
        <a href="/terms">Terms of Service</a>
        <a href="/privacy">Privacy Policy</a>
      </div>

      <button
        onClick={handleSubmit}
        disabled={!(isParentGuardian && dataConsent)}
      >
        I Consent
      </button>
    </div>
  );
}
