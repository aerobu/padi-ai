import Link from 'next/link';
import { Button } from '@padi/ui';

export default function HomePage() {
  return (
    <div className="min-h-screen flex flex-col">
      {/* Navigation */}
      <nav className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <span className="text-2xl font-bold text-padiGreen-600">PADI.AI</span>
            </div>
            <div className="flex items-center gap-4">
              <Link href="/(auth)/login">
                <Button variant="outline">Sign In</Button>
              </Link>
              <Link href="/(auth)/login">
                <Button>Get Started</Button>
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="flex-1">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
          <div className="text-center">
            <h1 className="text-4xl sm:text-5xl font-bold text-gray-900 mb-6">
              Adaptive Math Learning
              <br />
              <span className="text-padiGreen-600">for Oregon Students</span>
            </h1>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto mb-8">
              Personalized AI-powered learning that helps 4th graders master math
              concepts through adaptive practice and intelligent tutoring.
            </p>
            <div className="flex justify-center gap-4">
              <Link href="/(auth)/login">
                <Button size="lg">Start Learning</Button>
              </Link>
              <Link href="/(auth)/login">
                <Button size="lg" variant="outline">Learn More</Button>
              </Link>
            </div>
          </div>

          {/* Features */}
          <div className="mt-24 grid md:grid-cols-3 gap-8">
            <div className="bg-white rounded-lg p-6 shadow border border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Adaptive Learning
              </h3>
              <p className="text-gray-600">
                AI-powered tutoring that adjusts to each student&apos;s needs in real-time.
              </p>
            </div>
            <div className="bg-white rounded-lg p-6 shadow border border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Standards Aligned
              </h3>
              <p className="text-gray-600">
                Content mapped to Oregon math standards for grades 1-5.
              </p>
            </div>
            <div className="bg-white rounded-lg p-6 shadow border border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                COPPA Compliant
              </h3>
              <p className="text-gray-600">
                Privacy-first design with local LLM processing for student data.
              </p>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <p className="text-gray-400">
            &copy; 2026 PADI.AI. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
}
