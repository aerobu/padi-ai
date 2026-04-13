import type { Config } from 'tailwindcss';
import { colors } from '@padi/config';

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        padiGreen: colors.padiGreen,
        padiBlue: colors.padiBlue,
        error: colors.error,
        warning: colors.warning,
        success: colors.success,
        gray: colors.gray,
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
    },
  },
  plugins: [],
};
export default config;
