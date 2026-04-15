import { defineConfig } from 'vitest/config';
import path from 'path';

export default defineConfig({
  test: {
    environment: 'happy-dom',
    setupFiles: ['./tests/setup.ts'],
    include: ['tests/**/*.{test,spec}.{js,mjs,cjs,ts,mts,cts,jsx,tsx}'],
    css: true,
    coverage: {
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'tests/**',
        '**/*.d.ts',
        'vitest.config.ts',
        'next.config.js',
      ],
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, '.'),
      '@padi/ui': path.resolve(__dirname, '../../packages/ui'),
      '@padi/assessment': path.resolve(__dirname, './components/assessment'),
      '@/stores': path.resolve(__dirname, './stores'),
    },
  },
});
