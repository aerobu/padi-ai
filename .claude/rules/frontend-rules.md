---
globs: apps/web/**/*.tsx, apps/web/**/*.ts, packages/ui/**/*.tsx, packages/math-renderer/**/*.tsx
---

# Frontend & Design System Rules — PADI.AI

## 🎨 Design Tokens (Mandatory)
- **ALWAYS** use semantic tokens. **NEVER** use raw hex values (#4CAF50) or pixel literals (16px).
- **Colors:** `color-bg-primary`, `color-text-body`, `color-accent-primary`, etc.
- **Spacing:** `space-1` (4px) to `space-13` (96px). All spacing is multiples of 4px.
- **Typography:** `type-body-lg` (18px student), `type-display-md` (24px), `type-math-input` (24px JetBrains Mono).
- **No red for wrong answers:** Use shake animation + neutral feedback. Red is for system errors only.
- **Accessibility:** Student-facing text 18px minimum. Touch targets 48x48px minimum.

## 🏗️ Component Patterns (Atomic Design)
- **Atoms (`packages/ui/`):** Stateless UI primitives (Button, Input, Badge). Use `forwardRef`.
- **Molecules/Organisms (`apps/web/src/components/`):** Composed components.
- **Math Rendering:** Use `@padi/math-renderer` for all math. Use `ssr: false` for dynamic imports.

## ⚙️ Framework & State
- **Next.js 15:** Server Components by default. Use `'use client'` only for interactivity.
- **State:** Zustand for client state. Stores live in `apps/web/src/stores/`.
- **Types:** Use shared types from `@padi/types`. Avoid `any`.
