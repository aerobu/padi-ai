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
        {/* Hero Gradient Background */}
        <div className="absolute inset-0 bg-gradient-to-br from-neutral-50 via-teal-50/30 to-warm-50/40 z-0" />

        {/* Decorative gradient orbs */}
        <div className="absolute top-0 right-0 -translate-y-1/4 translate-x-1/4 w-96 h-96 bg-teal-200/30 rounded-full blur-3xl animate-float" />
        <div className="absolute bottom-0 left-0 translate-y-1/4 -translate-x-1/4 w-80 h-80 bg-warm-200/30 rounded-full blur-3xl animate-float-delayed" />

        {/* Geometric pattern overlay */}
        <div
          className="absolute inset-0 opacity-[0.03] z-0"
          style={{
            backgroundImage: `radial-gradient(circle at 1px 1px, currentColor 1px, transparent 0)`,
            backgroundSize: '32px 32px',
            color: 'var(--tw-colors-neutral-900)',
          }}
        />

        <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 lg:py-32">
          <div className="max-w-4xl mx-auto text-center">
            {/* Hero badge with warm accent */}
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/80 backdrop-blur-sm border border-teal-200/50 shadow-sm mb-8 animate-fade-in">
              <span className="w-2 h-2 rounded-full bg-warm-500 animate-pulse" />
              <span className="text-sm font-medium text-neutral-700">
                Built for Oregon Students
              </span>
            </div>

            {/* Main Headline with gradient text */}
            <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold mb-8 leading-[1.1] animate-fade-in-delayed">
              <span className="text-neutral-900 block">Adaptive Math</span>
              <span className="block bg-gradient-to-r from-teal-600 via-teal-500 to-warm-500 bg-clip-text text-transparent">
                Learning That Grows
              </span>
              <span className="text-neutral-900 block mt-4">
                With Every Student
              </span>
            </h1>

            {/* Subheadline */}
            <p className="text-xl sm:text-2xl text-neutral-600 max-w-2xl mx-auto mb-12 leading-relaxed animate-fade-in-delayed-2">
              Personalized AI-powered tutoring that adapts to each 4th grader&apos;s
              learning style, building confidence through smart practice and
              intelligent guidance.
            </p>

            {/* CTA Buttons with visual hierarchy */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center animate-fade-in-delayed-3">
              <Link href="/(auth)/login">
                <Button
                  size="lg"
                  className="w-full sm:w-auto px-8 py-4 text-lg shadow-xl shadow-teal-500/25 hover:shadow-2xl hover:shadow-teal-500/30 transition-all duration-300 hover:-translate-y-0.5"
                >
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
                <Button
                  size="lg"
                  variant="outline"
                  className="w-full sm:w-auto px-8 py-4 text-lg border-neutral-300 hover:border-teal-400 hover:bg-teal-50/50 transition-all duration-300"
                >
                  See How It Works
                </Button>
              </Link>
            </div>
          </div>

          {/* Features Grid with elevated cards */}
          <div className="mt-32 grid md:grid-cols-3 gap-8">
            {/* Feature 1: Adaptive Learning */}
            <div
              className="group relative bg-white rounded-2xl p-8 border border-neutral-200/60 shadow-sm hover:shadow-xl hover:shadow-neutral-200/50 hover:border-teal-200/60 transition-all duration-500 overflow-hidden"
              style={{ animationDelay: '0.1s' }}
            >
              {/* Accent bar */}
              <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-teal-500 via-teal-400 to-warm-400 transform -translate-y-full group-hover:translate-y-0 transition-transform duration-500" />

              {/* Feature icon with gradient background */}
              <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-teal-50 to-teal-100 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-500">
                <svg
                  className="w-7 h-7 text-teal-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox=" 0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={1.5}
                    d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                  />
                </svg>
              </div>

              <h3 className="text-2xl font-bold text-neutral-900 mb-3 group-hover:text-teal-700 transition-colors duration-300">
                Adaptive Learning
              </h3>
              <p className="text-neutral-600 leading-relaxed">
                AI-powered tutoring that adjusts difficulty in real-time, ensuring
                every student works at just the right challenge level—never too
                easy, never too hard.
              </p>
            </div>

            {/* Feature 2: Standards Aligned */}
            <div
              className="group relative bg-white rounded-2xl p-8 border border-neutral-200/60 shadow-sm hover:shadow-xl hover:shadow-neutral-200/50 hover:border-teal-200/60 transition-all duration-500 overflow-hidden"
              style={{ animationDelay: '0.2s' }}
            >
              {/* Accent bar */}
              <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-teal-500 via-teal-400 to-warm-400 transform -translate-y-full group-hover:translate-y-0 transition-transform duration-500" />

              {/* Feature icon */}
              <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-warm-50 to-warm-100 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-500">
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

              <h3 className="text-2xl font-bold text-neutral-900 mb-3 group-hover:text-warm-700 transition-colors duration-300">
                Oregon Standards
              </h3>
              <p className="text-neutral-600 leading-relaxed">
                Fully aligned with Oregon math standards for grades 1-5. Every
                lesson maps directly to classroom learning objectives, supporting
                both independent practice and in-class instruction.
              </p>
            </div>

            {/* Feature 3: COPPA Compliant */}
            <div
              className="group relative bg-white rounded-2xl p-8 border border-neutral-200/60 shadow-sm hover:shadow-xl hover:shadow-neutral-200/50 hover:border-teal-200/60 transition-all duration-500 overflow-hidden"
              style={{ animationDelay: '0.3s' }}
            >
              {/* Accent bar */}
              <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-teal-500 via-teal-400 to-warm-400 transform -translate-y-full group-hover:translate-y-0 transition-transform duration-500" />

              {/* Feature icon */}
              <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-teal-50 to-warm-50 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-500">
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

              <h3 className="text-2xl font-bold text-neutral-900 mb-3 group-hover:text-teal-700 transition-colors duration-300">
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
          <div className="mt-24 pt-16 border-t border-neutral-200/60">
            <p className="text-sm font-medium text-neutral-500 mb-8">
              Trusted by educators across Oregon
            </p>
            <div className="flex flex-wrap justify-center items-center gap-12 opacity-60">
              {/* Placeholder school logos - using text for now */}
              <span className="text-lg font-semibold text-neutral-400">Salem-Keizer</span>
              <span className="text-lg font-semibold text-neutral-400">Portland Public</span>
              <span className="text-lg font-semibold text-neutral-400">Beaverton</span>
              <span className="text-lg font-semibold text-neutral-400">Lake Oswego</span>
              <span className="text-lg font-semibold text-neutral-400">Tigard-Tualatin</span>
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

      {/* Custom styles for animations */}
      <style jsx global>{`
        @keyframes float {
          0%,
          100% {
            transform: translate(0, 0) rotate(0deg);
          }
          33% {
            transform: translate(20px, -20px) rotate(5deg);
          }
          66% {
            transform: translate(-10px, 10px) rotate(-3deg);
          }
        }

        @keyframes fade-in {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        .animate-float {
          animation: float 8s ease-in-out infinite;
        }

        .animate-float-delayed {
          animation: float 10s ease-in-out infinite 2s;
        }

        .animate-fade-in {
          animation: fade-in 0.8s ease-out forwards;
        }

        .animate-fade-in-delayed {
          animation: fade-in 0.8s ease-out 0.2s forwards;
          opacity: 0;
        }

        .animate-fade-in-delayed-2 {
          animation: fade-in 0.8s ease-out 0.4s forwards;
          opacity: 0;
        }

        .animate-fade-in-delayed-3 {
          animation: fade-in 0.8s ease-out 0.6s forwards;
          opacity: 0;
        }
      `}</style>
    </div>
  );
}
