import type { Config } from 'tailwindcss';
import { colors, shadows, fontFamily } from '@padi/config';

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
        display: fontFamily.display,
        sans: fontFamily.sans,
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
      animation: {
        'fade-in': 'fadeIn 0.8s ease-out forwards',
        'fade-in-delayed': 'fadeIn 0.8s ease-out 0.2s forwards',
        'fade-in-delayed-2': 'fadeIn 0.8s ease-out 0.4s forwards',
        'fade-in-delayed-3': 'fadeIn 0.8s ease-out 0.6s forwards',
        float: 'float 8s ease-in-out infinite',
        'float-delayed': 'float 10s ease-in-out infinite 2s',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        float: {
          '0%, 100%': { transform: 'translate(0, 0) rotate(0deg)' },
          '33%': { transform: 'translate(20px, -20px) rotate(5deg)' },
          '66%': { transform: 'translate(-10px, 10px) rotate(-3deg)' },
        },
      },
    },
  },
  plugins: [require('tailwindcss-animate'), require('@tailwindcss/typography')],
};
export default config;
