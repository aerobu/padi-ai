import Link from "next/link";
import { Button } from "@padi/ui/button";
import { cn } from "@/lib/utils";

export default function HomePage() {
  return (
    <div className="min-h-screen bg-page font-sans">
      {/* Shell Nav */}
      <nav className="sticky top-0 z-100 flex items-center h-[56px] px-8 bg-shell border-b border-shell-border text-white backdrcrop-blur-sm">
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
          <Link href="/(auth)/login">
            <Button size="sm" variant="outline" className="text-white border-white/30 hover:bg-white/10">
              Sign In
            </Button>
          </Link>
          <Link href="/(auth)/login">
            <Button size="sm" variant="primary">
              Get Started
            </Button>
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <main className="relative overflow-hidden">
        <div
          className="relative z-10 max-w-5xl mx-auto px-6 pb-20 pt-20 text-center"
          style={{
            background: "radial-gradient(ellipse at 80% 50%, rgba(61,122,98,.15) 0%, transparent 60%), radial-gradient(ellipse at 20% 80%, rgba(191,110,60,.1) 0%, transparent 50%)",
          }}
        >
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-white/60 backdrop-blur-sm border border-green-200/50 shadow-sm mb-8">
            <span className="w-2 h-2 rounded-full bg-green-500" />
            <span className="text-label-sm text-neutral-700">Built for Oregon Students</span>
          </div>

          <h1 className="text-display-md text-neutral-900 mb-4 leading-tight">
            Adaptive Math
          </h1>
          <h1 className="text-display-lg text-green-600 mb-4">
            Learning That Grows
          </h1>
          <h1 className="text-display-md text-neutral-900 mb-8 leading-tight">
            With Every Student
          </h1>

          <p className="text-body-lg text-neutral-600 max-w-2xl mx-auto mb-12 leading-relaxed">
            Personalized AI-powered tutoring that adapts to each 4th grader&apos;s
            learning style, building confidence through smart practice and
            intelligent guidance.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
            <Link href="/(auth)/login">
              <Button size="lg">
                Start Learning Free
                <svg className="w-5 h-5 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                </svg>
              </Button>
            </Link>
            <Link href="/(auth)/login">
              <Button size="lg" variant="outline">
                See How It Works
              </Button>
            </Link>
          </div>
        </div>
      </main>

      {/* Features */}
      <section className="max-w-5xl mx-auto px-6 pb-20">
        <div className="grid md:grid-cols-3 gap-6">
          {[
            {
              title: "Adaptive Learning",
              desc: "AI-powered tutoring that adjusts difficulty in real-time, ensuring every student works at just the right challenge level.",
              icon: (
                <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              ),
              bg: "bg-green-50",
            },
            {
              title: "Oregon Standards",
              desc: "Fully aligned with Oregon math standards for grades 1-5. Every lesson maps directly to classroom learning objectives.",
              icon: (
                <svg className="w-6 h-6 text-terra-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              ),
              bg: "bg-terra-50",
            },
            {
              title: "COPPA Compliant",
              desc: "Privacy-first design with local LLM processing. Student data never leaves Oregon servers.",
              icon: (
                <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
              ),
              bg: "bg-green-50",
            },
          ].map((f, i) => (
            <div
              key={i}
              className="rounded-xl border border-surface-border bg-white shadow-sm p-6 hover:shadow-md transition-shadow duration-200"
            >
              <div className={cn("w-12 h-12 rounded-lg flex items-center justify-center mb-4", f.bg)}>
                {f.icon}
              </div>
              <h3 className="text-display-sm text-neutral-900 mb-2">{f.title}</h3>
              <p className="text-body-md text-neutral-500 leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Trust */}
      <section className="max-w-5xl mx-auto px-6 pb-20 border-t border-neutral-200">
        <p className="text-label-sm font-medium text-neutral-500 mb-8 text-center mt-12">
          Trusted by educators across Oregon
        </p>
        <div className="flex flex-wrap justify-center items-center gap-x-10 gap-y-3 opacity-60">
          {["Salem-Keizer", "Portland Public", "Beaverton", "Lake Oswego", "Tigard-Tualatin"].map((s) => (
            <span key={s} className="text-body-md font-semibold text-neutral-400">{s}</span>
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-shell text-white border-t border-shell-border">
        <div className="max-w-7xl mx-auto px-8 py-8 flex items-center justify-between text-sm">
          <span>© 2026 PADI.AI</span>
          <div className="flex gap-6">
            <Link href="/privacy" className="text-white/65 hover:text-white transition-colors">Privacy</Link>
            <Link href="/terms" className="text-white/65 hover:text-white transition-colors">Terms</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
