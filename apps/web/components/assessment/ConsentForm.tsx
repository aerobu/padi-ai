import React from "react";

/**
 * ConsentForm component
 *
 * COPPA compliance requires explicit parental consent with two checkboxes.
 */

"use client";

import { useState } from "react";

interface ConsentFormProps {
  parentId: string;
  onConsentGranted: () => void;
  onConsentDenied: () => void;
  onError?: (error: string) => void;
  consentStatus?: "granted" | "denied" | "pending";
  isLoading?: boolean;
}

export function ConsentForm({
  parentId,
  onConsentGranted,
  onConsentDenied,
  onError,
  consentStatus,
  isLoading,
}: ConsentFormProps) {
  const [ageCheckbox, setAgeCheckbox] = useState(false);
  const [consentCheckbox, setConsentCheckbox] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleSubmit = async () => {
    // Reset any previous errors
    setErrorMessage(null);

    // Validate both checkboxes are checked
    if (!ageCheckbox || !consentCheckbox) {
      const error = "Please check both boxes to continue";
      setErrorMessage(error);
      onError?.(error);
      return;
    }

    try {
      // API call to submit consent
      await apiClient.post("/api/v1/coppa/consent", {
        parent_id: parentId,
        consent_status: "granted",
      });

      onConsentGranted();
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

      <div className="mb-4">
        <label>
          <input
            type="checkbox"
            checked={ageCheckbox}
            onChange={(e) => {
              setAgeCheckbox(e.target.checked);
              setErrorMessage(null);
            }}
          />
          I am over 13 or have parental permission
        </label>
      </div>

      <div className="mb-4">
        <label>
          <input
            type="checkbox"
            checked={consentCheckbox}
            onChange={(e) => {
              setConsentCheckbox(e.target.checked);
              setErrorMessage(null);
            }}
          />
          I agree to the terms
        </label>
      </div>

      <div className="mb-4">
        <a href="/terms">Terms of Service</a>
        <a href="/privacy">Privacy Policy</a>
      </div>

      <button onClick={handleSubmit}>Submit</button>
    </div>
  );
}

// Simple API client for the component
const apiClient = {
  post: async (endpoint: string, data: any) => {
    return { success: true, data };
  },
};
