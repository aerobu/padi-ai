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
        padi: {
          teal: colors.teal,
          warm: colors.warm,
          green: colors.green,
          amber: colors.amber,
          neutral: colors.neutral,
        },
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
        ...colors.borderRadius,
      },
    },
  },
  plugins: [],
};
export default config;
