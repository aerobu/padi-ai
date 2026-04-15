import Link from 'next/link';
import { Button } from '@padi/ui';

export default function HomePage() {
  return (
    <div className="min-h-screen flex flex-col font-sans">
      {/* Navigation */}
      <nav className="bg-white/90 backdrop-blur-md border-b border-neutral-200/60 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-20">
            <div className="flex items-center gap-3">
              {/* Logo with geometric dot accent */}
              <div className="flex items-center gap-2">
                <span className="text-3xl font-bold bg-gradient-to-r from-teal-600 to-teal-500 bg-clip-text text-transparent tracking-tight">
                  PADI.AI
                </span>
                <span className="w-2.5 h-2.5 rounded-full bg-teal-500 animate-pulse" />
              </div>
            </div>
            <div className="flex items-center gap-4">
              <Link href="/(auth)/login">
                <Button variant="outline" size="lg">
                  Sign In
                </Button>
              </Link>
              <Link href="/(auth)/login">
                <Button size="lg" className="shadow-lg shadow-teal-500/20">
                  Get Started
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="flex-1 relative overflow-hidden">
        {/* Subtle gradient background - calm, academic aesthetic */}
        <div className="absolute inset-0 bg-gradient-to-br from-neutral-50 via-neutral-50 to-teal-50/20 z-0" />

        {/* Minimal dot pattern - subtle texture, not decorative */}
        <div
          className="absolute inset-0 opacity-[0.02] z-0"
          style={{
            backgroundImage: `radial-gradient(circle at 1px 1px, currentColor 1px, transparent 0)`,
            backgroundSize: '40px 40px',
            color: 'var(--tw-colors-neutral-900)',
          }}
        />

        <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 lg:py-32">
          <div className="max-w-4xl mx-auto text-center">
            {/* Hero badge with warm accent */}
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/80 backdrop-blur-sm border border-teal-200/50 shadow-sm mb-8">
              <span className="w-2 h-2 rounded-full bg-warm-500" />
              <span className="text-label-sm font-medium text-neutral-700">
                Built for Oregon Students
              </span>
            </div>

            {/* Main Headline - Design system typography (Section 4.2) */}
            <h1 className="mb-8 leading-tight">
              <span className="block text-display-md text-neutral-800">Adaptive Math</span>
              <span className="block text-display-lg text-teal-600">
                Learning That Grows
              </span>
              <span className="block text-display-md text-neutral-800">
                With Every Student
              </span>
            </h1>

            {/* Subheadline */}
            <p className="text-body-lg text-neutral-600 max-w-2xl mx-auto mb-12 leading-relaxed">
              Personalized AI-powered tutoring that adapts to each 4th grader&apos;s
              learning style, building confidence through smart practice and
              intelligent guidance.
            </p>

            {/* CTA Buttons with visual hierarchy */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
              <Link href="/(auth)/login">
                <Button size="lg" className="w-full sm:w-auto">
                  <span>Start Learning Free</span>
                  <svg
                    className="w-5 h-5 ml-2"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M13 7l5 5m0 0l-5 5m5-5H6"
                    />
                  </svg>
                </Button>
              </Link>
              <Link href="/(auth)/login">
                <Button size="lg" variant="outline" className="w-full sm:w-auto">
                  See How It Works
                </Button>
              </Link>
            </div>
          </div>

          {/* Features Grid - Design system elevation (Section 4.4) */}
          <div className="mt-32 grid md:grid-cols-3 gap-8">
            {/* Feature 1: Adaptive Learning */}
            <div className="group bg-white rounded-xl p-8 border border-neutral-200/60 shadow-sm hover:shadow-md transition-all duration-300">
              {/* Feature icon */}
              <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-teal-50 to-teal-100 flex items-center justify-center mb-6 group-hover:scale-105 transition-transform duration-300">
                <svg
                  className="w-7 h-7 text-teal-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={1.5}
                    d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                  />
                </svg>
              </div>

              <h3 className="text-body-lg font-bold text-neutral-900 mb-3 group-hover:text-teal-700 transition-colors duration-300">
                Adaptive Learning
              </h3>
              <p className="text-neutral-600 leading-relaxed">
                AI-powered tutoring that adjusts difficulty in real-time, ensuring
                every student works at just the right challenge level—never too
                easy, never too hard.
              </p>
            </div>

            {/* Feature 2: Standards Aligned */}
            <div className="group bg-white rounded-xl p-8 border border-neutral-200/60 shadow-sm hover:shadow-md transition-all duration-300">
              {/* Feature icon */}
              <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-warm-50 to-warm-100 flex items-center justify-center mb-6 group-hover:scale-105 transition-transform duration-300">
                <svg
                  className="w-7 h-7 text-warm-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={1.5}
                    d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
              </div>

              <h3 className="text-body-lg font-bold text-neutral-900 mb-3 group-hover:text-warm-700 transition-colors duration-300">
                Oregon Standards
              </h3>
              <p className="text-neutral-600 leading-relaxed">
                Fully aligned with Oregon math standards for grades 1-5. Every
                lesson maps directly to classroom learning objectives, supporting
                both independent practice and in-class instruction.
              </p>
            </div>

            {/* Feature 3: COPPA Compliant */}
            <div className="group bg-white rounded-xl p-8 border border-neutral-200/60 shadow-sm hover:shadow-md transition-all duration-300">
              {/* Feature icon */}
              <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-teal-50 to-warm-50 flex items-center justify-center mb-6 group-hover:scale-105 transition-transform duration-300">
                <svg
                  className="w-7 h-7 text-teal-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={1.5}
                    d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
                  />
                </svg>
              </div>

              <h3 className="text-body-lg font-bold text-neutral-900 mb-3 group-hover:text-teal-700 transition-colors duration-300">
                COPPA Compliant
              </h3>
              <p className="text-neutral-600 leading-relaxed">
                Privacy-first design with local LLM processing. Student data never
                leaves Oregon servers, and no personal information is collected
                or sold to third parties.
              </p>
            </div>
          </div>

          {/* Social proof / Trust indicators */}
          <div className="mt-32 pt-16 border-t border-neutral-200/60">
            <p className="text-label-sm font-medium text-neutral-500 mb-8">
              Trusted by educators across Oregon
            </p>
            <div className="flex flex-wrap justify-center items-center gap-x-12 gap-y-4 opacity-60">
              {/* Placeholder school logos - using text for now */}
              <span className="text-body-md font-semibold text-neutral-400">Salem-Keizer</span>
              <span className="text-body-md font-semibold text-neutral-400">Portland Public</span>
              <span className="text-body-md font-semibold text-neutral-400">Beaverton</span>
              <span className="text-body-md font-semibold text-neutral-400">Lake Oswego</span>
              <span className="text-body-md font-semibold text-neutral-400">Tigard-Tualatin</span>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-neutral-900 text-white relative overflow-hidden">
        {/* Subtle gradient */}
        <div className="absolute inset-0 bg-gradient-to-t from-teal-900/20 to-transparent" />

        <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="flex flex-col md:flex-row justify-between items-center gap-6">
            <div className="flex items-center gap-2">
              <span className="text-2xl font-bold bg-gradient-to-r from-teal-400 to-teal-300 bg-clip-text text-transparent">
                PADI.AI
              </span>
            </div>

            <div className="flex items-center gap-8 text-sm text-neutral-400">
              <Link
                href="/privacy"
                className="hover:text-teal-400 transition-colors duration-300"
              >
                Privacy Policy
              </Link>
              <Link
                href="/terms"
                className="hover:text-teal-400 transition-colors duration-300"
              >
                Terms of Service
              </Link>
              <Link
                href="/contact"
                className="hover:text-teal-400 transition-colors duration-300"
              >
                Contact
              </Link>
            </div>

            <p className="text-sm text-neutral-500">
              &copy; 2026 PADI.AI. All rights reserved.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
