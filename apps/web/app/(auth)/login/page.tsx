'use client';

import { Button } from '@padi/ui';
import { useRouter } from 'next/navigation';

export default function LoginPage() {
  const router = useRouter();

  const handleLogin = () => {
    // Redirect to Auth0 login API route
    router.push('/api/auth/login');
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-neutral-50">
      <div className="max-w-md w-full space-y-8 p-8 bg-white rounded-lg shadow-md border border-neutral-200">
        <div className="text-center">
          <h2 className="text-3xl font-bold text-neutral-800">
            Welcome to PADI.AI
          </h2>
          <p className="mt-2 text-neutral-600">
            Sign in to continue your adaptive math learning journey
          </p>
        </div>

        <div className="mt-8">
          <Button onClick={handleLogin} className="w-full">
            Continue with Auth0
          </Button>

          <div className="mt-6 text-center text-sm text-neutral-500">
            <p>By continuing, you agree to our</p>
            <a href="/terms" className="text-teal-600 hover:underline">
              Terms of Service
            </a>
            <span className="mx-1">and</span>
            <a href="/privacy" className="text-teal-600 hover:underline">
              Privacy Policy
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
