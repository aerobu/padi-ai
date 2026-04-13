import { defineConfig } from 'vitest/config';
import path from 'path';

export default defineConfig({
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./tests/setup.ts'],
    include: ['tests/**/*.test.tsx', 'tests/**/*.test.ts'],
    coverage: {
      provider: 'istanbul',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        '.next/',
        'tests/',
        '**/*.d.ts',
        'src/**/*.{test,spec}.ts*',
      ],
    },
    resolve: {
      alias: [
        { find: '@padi/ui', replacement: path.resolve(__dirname, '../packages/ui') },
        { find: '@padi/config', replacement: path.resolve(__dirname, '../packages/config') },
        { find: '@padi/types', replacement: path.resolve(__dirname, '../packages/types') },
      ],
    },
  },
});
