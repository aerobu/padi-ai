// Test setup file - excluded from type checking
// vitest globals are available through config.globals: true
import '@testing-library/jest-dom/vitest';
import { afterEach, vi } from 'vitest';
import { cleanup } from '@testing-library/react';
import { server } from './msw';

import * as React from 'react';
(globalThis as any).React = React;

// Mock localStorage for zustand persistence
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value.toString();
    },
    removeItem: (key: string) => {
      delete store[key];
    },
    clear: () => {
      store = {};
    },
  };
})();

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

// Reset server state after each test
afterEach(() => {
  server.resetHandlers();
  cleanup();
});

// Clean up after tests
afterEach(() => {
  server.close();
});
