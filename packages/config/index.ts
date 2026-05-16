// Color tokens from Solosail design system (May 2026)
// Primary brand = forest green, Accent = terracotta, Neutral = warm gray

// ── GREEN (Primary Brand) ──

export const green = {
  50:  '#eef5f1',
  100: '#d3e7db',
  200: '#a8cebc',
  300: '#7ab59d',
  400: '#559c80',
  500: '#3d7a62',
  600: '#2d5f4a',
  700: '#234a39',
  800: '#1a3629',
  900: '#112419',
} as const;

// ── TERRACOTTA (Accent) ──

export const terra = {
  50:  '#fbf2ec',
  100: '#f5dece',
  200: '#eabfa4',
  300: '#dc9f7a',
  400: '#cc8055',
  500: '#bf6e3c',
  600: '#a85e2f',
  700: '#8c4d22',
  800: '#6e3c18',
  900: '#502c10',
} as const;

// ── NEUTRAL (Warm Gray) ──

export const neutral = {
  0:   '#ffffff',
  50:  '#fafaf9',
  100: '#f5f1ea',
  200: '#e8e2d8',
  300: '#d5cfc4',
  400: '#b0a898',
  500: '#8a8276',
  600: '#635d54',
  700: '#46413a',
  800: '#2c2820',
  900: '#1a1612',
} as const;

// ── SHELL / CHROME ──

export const shell = {
  bg:     '#1c1008',
  bgDeep: '#130b04',
  border: '#2e1d0e',
} as const;

// ── PAGE / SURFACE ──

export const page = {
  bg:    '#ede8df',     // warm cream
  bgAlt: '#f5f1ea',     // lighter cream
} as const;

export const surface = {
  white:  '#ffffff',
  cream:  '#f9f5ef',
  border: '#e8e2d8',
} as const;

// ── SEMANTIC / STATUS ──

export const status = {
  low:    { bg: '#1f3d2a', text: '#7ecb9a', dot: '#7ecb9a' },
  medium: { bg: '#f9f3e3', text: '#a87c2a', dot: '#d4a843' },
  high:   { bg: '#f7e8e8', text: '#a83030', dot: '#d44a4a' },
} as const;

export const dataViz = {
  principal: '#3d7a62',
  interest:  '#c97a4a',
  neutral:   '#c8bfac',
};

// ── SHADOWS ──

export const shadows = {
  xs:   '0 1px 2px rgba(26,14,0,0.06)',
  sm:   '0 1px 4px rgba(26,14,0,0.08), 0 1px 2px rgba(26,14,0,0.05)',
  md:   '0 4px 12px rgba(26,14,0,0.10), 0 2px 4px rgba(26,14,0,0.06)',
  lg:   '0 10px 24px rgba(26,14,0,0.12), 0 4px 8px rgba(26,14,0,0.07)',
  xl:   '0 20px 48px rgba(26,14,0,0.16)',
  green:'0 8px 24px -4px rgba(45,95,74,0.40)',
} as const;

// ── RADIUS ──

export const radius = {
  sm:  '6px',
  md:  '10px',
  lg:  '14px',
  xl:  '18px',
  xl2: '24px',
  full:'9999px',
} as const;

// ── SPACING (4px base) ──

export const spacing = {
  0:  '0',
  1:  '4px',
  2:  '8px',
  3:  '12px',
  4:  '16px',
  5:  '20px',
  6:  '24px',
  7:  '32px',
  8:  '40px',
  9:  '48px',
  10: '56px',
  11: '64px',
  12: '80px',
} as const;

// ── MOTOR ──

export const motion = {
  easeStandard: 'cubic-bezier(0.4, 0, 0.2, 1)',
  easeOut:      'cubic-bezier(0, 0, 0.2, 1)',
  durFast:  '120ms',
  durMed:   '200ms',
  durSlow:  '300ms',
} as const;

// ── TYPOGRAPHY ──

export const fontDisplay = "'Playfair Display', Georgia, serif";
export const fontSans     = "'Inter', system-ui, -apple-system, sans-serif";
export const fontMono     = "'JetBrains Mono', ui-monospace, monospace";

export const typeScale = {
  hero:       { weight: 800, size: '52px', line: '1.1' } as const,
  displayLg:  { weight: 700, size: '36px', line: '1.15' } as const,
  displayMd:  { weight: 700, size: '24px', line: '1.25' } as const,
  displaySm:  { weight: 600, size: '18px', line: '1.35' } as const,
  bodyLg:     { weight: 400, size: '16px', line: '1.6' } as const,
  bodyMd:     { weight: 400, size: '14px', line: '1.55' } as const,
  bodySm:     { weight: 400, size: '12px', line: '1.5' } as const,
  labelLg:    { weight: 600, size: '14px', line: '1' } as const,
  labelSm:    { weight: 600, size: '11px', line: '1' } as const,
  kpi:        { weight: 700, size: '32px', line: '1' } as const,
  kpiLg:      { weight: 700, size: '48px', line: '1' } as const,
  mono:       { weight: 500, size: '14px', line: '1.5' } as const,
} as const;

// ── BACKWARDS COMPATIBILITY ──

export const colors = {
  teal:  green,
  warm:  terra,
  green,
  terra,
  neutral,
  gray:  neutral,
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
} as const;

// ── APP CONFIG ──

export const APP_CONFIG = {
  name: 'PADI.AI',
  shortName: 'PADI',
  version: '0.1.0',
  description: 'Adaptive Math Learning Platform',
} as const;

export const isDevelopment = process.env.NODE_ENV === 'development';
export const isProduction = process.env.NODE_ENV === 'production';
export const isTest = process.env.NODE_ENV === 'test';

export const API_CONFIG = {
  timeout: 30000,
  retries: 3,
} as const;

export const FEATURE_FLAGS = {
  darkMode: true,
  newDashboard: false,
  betaFeatures: false,
} as const;
