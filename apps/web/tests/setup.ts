import '@testing-library/jest-dom';
import { afterEach } from 'vitest';
import { cleanup } from '@testing-library/react';
import { server } from './msw';
import React from 'react';

// Make React globally available for JSX
global.React = React;

// Start MSW server before tests
beforeAll(() => server.listen({ onUnhandledRequest: 'bypass' }));

// Reset server state after each test
afterEach(() => {
  server.resetHandlers();
  cleanup();
});

// Clean up after tests
afterAll(() => server.close());

// Mock Next.js router
vi.mock('next/navigation', () => ({
  useRouter() {
    return {
      push: vi.fn(),
      prefetch: vi.fn(),
      pathname: '/',
      asPath: '/',
      query: {},
    };
  },
  usePathname() {
    return '/';
  },
  useSearchParams() {
    return {
      get: vi.fn(),
      has: vi.fn(),
      getAll: vi.fn(),
      set: vi.fn(),
      delete: vi.fn(),
      keys: vi.fn(),
      values: vi.fn(),
      entries: vi.fn(),
    };
  },
}));

// Mock @auth0/nextjs-auth0
vi.mock('@auth0/nextjs-auth0', () => ({
  Auth0Provider: (props: any) => {
    return { type: 'fragment', children: props.children };
  },
  useAuth0: () => ({
    isAuthenticated: false,
    user: null,
    isLoading: false,
    error: null,
    loginWithRedirect: vi.fn(),
    logout: vi.fn(),
    getAccessToken: vi.fn(),
  }),
}));
