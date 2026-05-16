"use client";

import Link from "next/link";
import { Button } from "@padi/ui/button";
import { useRouter } from "next/navigation";

export default function LoginPage() {
  const router = useRouter();
  const handleLogin = () => router.push("/api/auth/login");

  return (
    <div className="min-h-screen bg-page flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        {/* Brand */}
        <div className="text-center mb-8">
          <div className="inline-flex h-12 w-12 rounded-xl bg-green-600 items-center justify-center text-white mb-4">
            <svg width="24" height="24" viewBox="0 0 16 16" fill="none">
              <path d="M3 12L8 3l5 9" stroke="white" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
              <circle cx="8" cy="8" r="2" fill="rgba(255,255,255,.3)" />
            </svg>
          </div>
          <h1 className="font-display text-2xl text-neutral-900">Welcome to PADI.AI</h1>
          <p className="mt-2 text-body-md text-neutral-500">
            Sign in to continue your adaptive math learning journey
          </p>
        </div>

        <div className="rounded-xl border border-surface-border bg-white shadow-sm p-6">
          <Button onClick={handleLogin} className="w-full" size="lg" variant="primary">
            Continue with Auth0
          </Button>

          <div className="mt-6 text-center">
            <p className="text-[14px] text-neutral-500 mb-2">
              By continuing, you agree to our
            </p>
            <div className="flex gap-3 justify-center text-[14px]">
              <Link href="/terms" className="text-green-600 hover:underline">Terms of Service</Link>
              <span className="text-neutral-400">and</span>
              <Link href="/privacy" className="text-terra-500 hover:underline">Privacy Policy</Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
