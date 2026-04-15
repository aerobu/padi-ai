// Test setup file - excluded from type checking
// vitest globals are available through config.globals: true
import '@testing-library/jest-dom/vitest';
import { afterEach, vi } from 'vitest';
import { cleanup } from '@testing-library/react';
import { server } from './msw';

// Import React for JSX support (React 17+ auto-import)
import 'react';

// Reset server state after each test
afterEach(() => {
  server.resetHandlers();
  cleanup();
});

// Clean up after tests
afterEach(() => {
  server.close();
});
