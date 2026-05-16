/**
 * Onboarding layout.
 * Shared layout for onboarding pages (consent, create-student).
 */

import Link from "next/link";

export default function OnboardingLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-page">
      {/* Shell Nav */}
        <nav className="sticky top-0 z-100 flex items-center h-[56px] px-8 bg-shell border-b border-shell-border text-white">
        <Link href="/" className="flex items-center gap-2 no-underline">
          <span className="h-7 w-7 rounded-md bg-green-600 flex items-center justify-center text-white">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M3 12L8 3l5 9" stroke="white" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
              <circle cx="8" cy="8" r="2" fill="rgba(255,255,255,.3)" />
            </svg>
          </span>
          <span className="font-bold text-[16px] tracking-[-.01em]">PADI.AI</span>
        </Link>
        <div className="ml-auto flex gap-3">
          <Link href="/dashboard" className="h-[36px] rounded-md px-4 font-semibold text-[14px] text-white cursor-pointer transition-colors duration-200 whitespace-nowrap bg-terra-500 hover:bg-terra-600 active:scale-[.96]">
            Dashboard
          </Link>
        </div>
      </nav>

      {/* Main content */}
      <main className="max-w-[600px] mx-auto px-6 py-8">
        {children}
      </main>

      {/* Footer */}
      <footer className="bg-shell text-white border-t border-shell-border">
        <div className="max-w-[600px] mx-auto px-6 py-6 flex items-center justify-between">
          <span className="text-[14px] text-white/65">© 2026 PADI.AI</span>
          <div className="flex gap-6">
            <Link href="/terms" className="text-[14px] text-white/65 hover:text-white transition-colors">Terms</Link>
            <Link href="/privacy" className="text-[14px] text-white/65 hover:text-white transition-colors">Privacy</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
