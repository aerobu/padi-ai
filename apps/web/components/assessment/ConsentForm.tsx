import { useState } from "react";
import { cn } from "@/lib/utils";
import Link from "next/link";

interface ConsentFormProps {
  parentId?: string;
  onConsentGranted?: () => void;
  onConsentDenied?: () => void;
  onError?: (error: string) => void;
  consentStatus?: "granted" | "denied" | "pending";
  isLoading?: boolean;
  className?: string;
}

export function ConsentForm({
  parentId: _parentId,
  onConsentGranted,
  onConsentDenied,
  onError,
  consentStatus,
  isLoading,
  className,
}: ConsentFormProps) {
  const [isParentGuardian, setIsParentGuardian] = useState(false);
  const [dataConsent, setDataConsent] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleSubmit = async (e?: React.FormEvent) => {
    e?.preventDefault();
    setErrorMessage(null);

    if (!isParentGuardian || !dataConsent) {
      const error = "Please check both boxes to continue";
      setErrorMessage(error);
      onError?.(error);
      return;
    }

    try {
      onConsentGranted?.();
    } catch (error) {
      const errorMsg = "Failed to submit consent. Please try again.";
      setErrorMessage(errorMsg);
      onError?.(errorMsg);
    }
  };

  if (consentStatus === "granted") {
    return (
      <div className="p-4 rounded-md bg-green-50 border border-green-200">
        <h2 className="text-display-sm font-bold text-green-600">Consent granted</h2>
        <p className="mt-2 text-[14px] text-neutral-600">You can now proceed.</p>
      </div>
    );
  }

  if (consentStatus === "denied") {
    return (
      <div className="p-4 rounded-md bg-status-high-bg border border-[#f7e8e8]">
        <h2 className="text-display-sm font-bold text-[#a83030]">Consent denied</h2>
        <p className="mt-2 text-[14px] text-neutral-600">Access is not available.</p>
      </div>
    );
  }

  if (consentStatus === "pending") {
    return (
      <div className="p-4 rounded-md bg-surface-cream border border-surface-border">
        <h2 className="text-display-sm font-bold text-neutral-900">Consent pending</h2>
        <p className="mt-2 text-[14px] text-neutral-600">Please wait for confirmation.</p>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div role="status" className="flex items-center gap-3 p-4 rounded-md bg-surface-cream border border-surface-border">
        <div className="animate-spin rounded-full h-5 w-5 border-2 border-neutral-200 border-t-green-600" />
        <p className="text-[14px] text-neutral-600">Processing...</p>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className={cn("space-y-6", className)}>
      <p className="text-[14px] text-neutral-600 leading-relaxed">
        Please provide the following consent to continue.
      </p>

      {errorMessage && (
        <div
          role="alert"
          className="p-3 rounded-md bg-status-high-bg border border-[#f7e8e8] text-[#a83030] text-[14px]"
        >
          {errorMessage}
        </div>
      )}

      <div className="space-y-4">
        <label className={cn("flex items-start gap-3 cursor-pointer")}>
          <input
            type="checkbox"
            className="mt-1 rounded border-neutral-200"
            checked={isParentGuardian}
            onChange={(e) => setIsParentGuardian(e.target.checked)}
            aria-required="true"
          />
          <span className="text-[14px] text-neutral-700 leading-relaxed">
            I am the parent or legal guardian of the child I am enrolling, and I am
            at least 18 years old.
          </span>
        </label>

        <label className={cn("flex items-start gap-3 cursor-pointer")}>
          <input
            type="checkbox"
            className="mt-1 rounded border-neutral-200"
            checked={dataConsent}
            onChange={(e) => setDataConsent(e.target.checked)}
            aria-required="true"
          />
          <span className="text-[14px] text-neutral-700 leading-relaxed">
            I consent to the collection and processing of my child&apos;s first name,
            grade level, and assessment responses for the purpose of providing
            personalized math instruction, as described in the{" "}
            <a href="/privacy" className="underline text-green-600">
              Privacy Policy
            </a>
            .
          </span>
        </label>
      </div>

      <div className="flex items-center gap-3 text-[14px]">
        <Link href="/terms" className="text-green-600 hover:underline">Terms of Service</Link>
        <span className="text-neutral-300">·</span>
        <a href="/privacy" className="text-terra-500 hover:underline">Privacy Policy</a>
      </div>
    </form>
  );
}
