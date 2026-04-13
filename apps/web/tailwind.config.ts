import type { Config } from 'tailwindcss';
import { colors, shadows } from '@padi/config';

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Brand colors from design system
        teal: colors.teal,
        warm: colors.warm,
        green: colors.green,
        amber: colors.amber,
        neutral: colors.neutral,
        // Semantic colors
        error: colors.error,
        warning: colors.warning,
        success: colors.success,
        // Backwards compatibility
        gray: colors.gray,
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      boxShadow: {
        sm: shadows.sm,
        DEFAULT: shadows.DEFAULT,
        md: shadows.md,
        lg: shadows.lg,
        xl: shadows.xl,
      },
      borderRadius: {
        none: '0',
        sm: '0.25rem',
        default: '0.375rem',
        md: '0.5rem',
        lg: '0.75rem',
        xl: '1rem',
        '2xl': '1.5rem',
        full: '9999px',
      },
    },
  },
  plugins: [],
};
export default config;
