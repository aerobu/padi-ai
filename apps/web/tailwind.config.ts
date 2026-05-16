import type { Config } from 'tailwindcss';
import { colors, shadows, fontDisplay, fontSans, radius, spacing, shell, page, surface, status, dataViz } from '@padi/config';

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        green: colors.green,
        terra: colors.terra,
        neutral: colors.neutral,
        shell: {
          DEFAULT: shell.bg,
          deep: shell.bgDeep,
          border: shell.border,
        },
        page: {
          DEFAULT: page.bg,
          alt: page.bgAlt,
        },
        surface: {
          white: surface.white,
          cream: surface.cream,
          border: surface.border,
        },
        status: {
          low:    status.low,
          med:    status.medium,
          high:   status.high,
        },
        data: {
          principal: dataViz.principal,
          interest:  dataViz.interest,
          neutral:   dataViz.neutral,
        },
        teal:  colors.green,
        warm:  colors.terra,
        gray:  colors.neutral,
        error: {
          50:  '#fef2f2', 100: '#fee2e2', 200: '#fecaca', 300: '#fca5a5',
          400: '#f87171', 500: '#ef4444', 600: '#dc2626', 700: '#b91c1c',
          800: '#991b1b', 900: '#7f1d1d',
        },
        warning: {
          50:  '#fffbeb', 100: '#fef3c7', 200: '#fde68a', 300: '#fcd34d',
          400: '#fbbf24', 500: '#f59e0b', 600: '#d97706', 700: '#b45309',
          800: '#92400e', 900: '#78350f',
        },
        success: {
          50:  '#f0fdf4', 100: '#dcfce7', 200: '#bbf7d0', 300: '#86efac',
          400: '#4ade80', 500: '#22c55e', 600: '#16a34a', 700: '#15803d',
          800: '#166534', 900: '#14532d',
        },
      },
      fontFamily: {
        display: [fontDisplay, 'Georgia', 'serif'] as unknown as string[],
        sans:    [fontSans, 'system-ui', '-apple-system', 'sans-serif'] as unknown as string[],
        mono:    ['JetBrains Mono', 'ui-monospace', 'monospace'] as unknown as string[],
      },
      fontSize: {
        'hero':       ['52px', { lineHeight: '1.1' }],
        'display-lg': ['36px', { lineHeight: '1.15' }],
        'display-md': ['24px', { lineHeight: '1.25' }],
        'display-sm': ['18px', { lineHeight: '1.35' }],
        'body-lg':    ['16px', { lineHeight: '1.6' }],
        'body-md':    ['14px', { lineHeight: '1.55' }],
        'body-sm':    ['12px', { lineHeight: '1.5' }],
        'label-lg':   ['14px', { lineHeight: '1' }],
        'label-sm':   ['11px', { lineHeight: '1' }],
        'kpi':        ['32px', { lineHeight: '1' }],
        'kpi-lg':     ['48px', { lineHeight: '1' }],
      },
      boxShadow: {
        'xs':  shadows.xs,
        'sm':  shadows.sm,
        'md':  shadows.md,
        'lg':  shadows.lg,
        'xl':  shadows.xl,
        'green': shadows.green,
      },
      borderRadius: {
        sm:  radius.sm,
        md:  radius.md,
        lg:  radius.lg,
        xl:  radius.xl,
        '2xl': radius.xl2,
        full: radius.full,
      },
      spacing: {
        '1':  spacing[1],
        '2':  spacing[2],
        '3':  spacing[3],
        '4':  spacing[4],
        '5':  spacing[5],
        '6':  spacing[6],
        '7':  spacing[7],
        '8':  spacing[8],
        '9':  spacing[9],
        '10': spacing[10],
        '11': spacing[11],
        '12': spacing[12],
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-out forwards',
        'scale-in': 'scaleIn 0.12s ease-out forwards',
      },
      keyframes: {
        fadeIn: {
          '0%':  { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        scaleIn: {
          '0%':  { opacity: '0', transform: 'scale(0.96)' },
          '100%': { opacity: '1', transform: 'scale(1)' },
        },
      },
      transitionDuration: {
        'fast': '120ms',
        'med':  '200ms',
        'slow': '300ms',
      },
    },
  },
  plugins: [require('tailwindcss-animate'), require('@tailwindcss/typography')],
};

export default config;
