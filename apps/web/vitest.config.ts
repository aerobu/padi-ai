import { defineConfig } from 'vitest/config';
import path from 'path';

export default defineConfig({
  test: {
    globals: true,
    environment: 'happy-dom',
    setupFiles: ['./tests/setup.ts'],
    include: ['tests/**/*.{test,spec}.{js,mjs,cjs,ts,mts,cts,jsx,tsx}'],
    exclude: [
      '**/node_modules/**',
      '**/dist/**',
      '**/cypress/**',
      '**/.{idea,git,cache,output,temp}/**',
      '**/{karma,rollup,webpack,vite,vitest,jest,ava,babel,nyc,cypress,tsup,build}.config.*',
      '**/*.spec.ts',
    ],
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
      '@padi/config': path.resolve(__dirname, '../../packages/config'),
      '@padi/types': path.resolve(__dirname, '../../packages/types'),
      '@padi/assessment': path.resolve(__dirname, './components/assessment'),
      '@/stores': path.resolve(__dirname, './stores'),
    },
  },
});
