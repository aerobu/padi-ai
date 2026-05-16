"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@padi/ui/button";
import { Input } from "@padi/ui/input";
import { Card } from "@padi/ui/card";
import { HeroCard } from "@padi/ui/hero-card";
import { RiskRow } from "@padi/ui/hero-card";
import { Badge } from "@padi/ui/badge";
import { Divider } from "@padi/ui/divider";

export default function ConsentPage() {
  const router = useRouter();
  const [isParent] = useState(false);
  const [dataConsent] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="font-display text-display-md text-neutral-900">Parental Consent Required</h1>
        <p className="mt-2 text-[16px] text-neutral-500 leading-relaxed">
          Under the Children&apos;s Online Privacy Protection Act (COPPA), we require your consent before collecting any information from students under 13 years of age.
        </p>
      </div>

      {/* What will be collected */}
      <div className="rounded-xl border border-surface-border bg-white shadow-sm p-5">
        <h3 className="text-[14px] font-semibold text-neutral-900 mb-3">What information will be collected:</h3>
        <ul className="text-[14px] text-neutral-600 space-y-1.5">
          {[
            "Student first name (no last name collected)",
            "Grade level",
            "Math assessment results",
            "Learning progress over time",
          ].map((item, i) => (
            <li key={i} className="flex gap-2 items-start">
              <span className="text-green-600 mt-0.5">•</span>
              {item}
            </li>
          ))}
        </ul>
      </div>

      {/* Consent checkboxes */}
      <Card className="p-5">
        <h2 className="text-[14px] font-semibold uppercase tracking-[.06em] text-neutral-400 mb-4">
          Parental Consent
        </h2>
        <div className="space-y-3">
          <label className="flex items-start gap-3 cursor-pointer">
            <input type="checkbox" className="mt-0.5 rounded border-neutral-300" />
            <span className="text-[14px] text-neutral-700 leading-relaxed">
              I am the parent or legal guardian of the child I am enrolling, and I am at least 18 years old.
            </span>
          </label>
          <label className="flex items-start gap-3 cursor-pointer">
            <input type="checkbox" className="mt-0.5 rounded border-neutral-300" />
            <span className="text-[14px] text-neutral-700 leading-relaxed">
              I consent to the collection and processing of my child&apos;s first name, grade level, and assessment responses for personalized math instruction, as described in the{" "}
              <a href="/privacy" className="text-green-600 underline">Privacy Policy</a>.
            </span>
          </label>
        </div>
        <Divider />
        <Button
          size="lg"
          disabled={!(isParent && dataConsent)}
          className="w-full mt-4"
          onClick={() => { setIsLoading(true); router.push("/onboarding/create-student"); }}
        >
          {isLoading ? "Processing..." : "I Consent"}
        </Button>
      </Card>

      {/* Risk info */}
      <div className="space-y-3">
        <p className="text-[12px] font-semibold uppercase tracking-[.1em] text-neutral-400">Privacy protections</p>
        <RiskRow title="Data stored locally" description="Student data is stored on secure Oregon-based servers with AES-256 encryption." status="low" />
        <RiskRow title="No third-party sharing" description="No personal information is shared with third parties without explicit parental consent." status="low" />
      </div>

      <Divider />
      <div className="flex gap-3 text-center">
        <a href="/terms" className="text-[14px] text-neutral-500 hover:text-neutral-800">Terms of Service</a>
        <span className="text-neutral-300">·</span>
        <a href="/privacy" className="text-[14px] text-neutral-500 hover:text-neutral-800">Privacy Policy</a>
      </div>
    </div>
  );
}
