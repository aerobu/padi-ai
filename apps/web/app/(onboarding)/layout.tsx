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
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-slate-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-slate-200">
        <div className="container mx-auto max-w-4xl px-4 py-4">
          <div className="flex items-center justify-between">
            <Link href="/" className="flex items-center space-x-2">
              <span className="text-xl font-bold text-blue-700">PADI.AI</span>
            </Link>
            <nav className="flex items-center space-x-4">
              <Link
                href="/"
                className="text-sm text-slate-600 hover:text-slate-900"
              >
                Home
              </Link>
            </nav>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="container mx-auto max-w-2xl px-4 py-8">
        {children}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-slate-200 mt-auto">
        <div className="container mx-auto max-w-4xl px-4 py-6">
          <div className="flex items-center justify-between text-sm text-slate-600">
            <span>© 2026 PADI.AI</span>
            <div className="flex space-x-4">
              <Link href="/terms" className="hover:text-slate-900">
                Terms
              </Link>
              <Link href="/privacy" className="hover:text-slate-900">
                Privacy
              </Link>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
