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
        // Cast through unknown to bypass readonly array constraint
        display: fontFamily.display as unknown as string[],
        sans: fontFamily.sans as unknown as string[],
        mono: ['JetBrains Mono', 'monospace'],
      },
      fontSize: {
        // Design system typography scale (Section 4.2 of 09-design-system.md)
        'display-lg': ['32px', { lineHeight: '40px', fontWeight: '700' }],
        'display-md': ['24px', { lineHeight: '32px', fontWeight: '700' }],
        'display-sm': ['20px', { lineHeight: '28px', fontWeight: '500' }],
        'body-lg': ['18px', { lineHeight: '28px', fontWeight: '400' }],
        'body-md': ['16px', { lineHeight: '24px', fontWeight: '400' }],
        'label-lg': ['14px', { lineHeight: '20px', fontWeight: '600' }],
        'label-sm': ['12px', { lineHeight: '16px', fontWeight: '500' }],
      },
      boxShadow: {
        // Design system elevation shadows (Section 4.4 of 09-design-system.md)
        'sm': '0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.06)', // elevation-1
        'md': '0 4px 6px rgba(0,0,0,0.07), 0 2px 4px rgba(0,0,0,0.06)', // elevation-2
        'lg': '0 10px 15px rgba(0,0,0,0.07), 0 4px 6px rgba(0,0,0,0.05)', // elevation-3
        'xl': shadows.xl,
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
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [require('tailwindcss-animate'), require('@tailwindcss/typography')],
};
export default config;
