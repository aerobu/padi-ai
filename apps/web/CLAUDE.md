# CLAUDE.md - PADI.AI Frontend Guidance

## 🏗️ Architectural Guardrails (Strict)
1. **Server Components:** Use Server Components by default. Use `'use client'` ONLY for leaf components requiring state or browser APIs.
2. **Shared Components:** Use `@padi/ui` for all primitive UI elements. Do not reinvent buttons, cards, or inputs.
3. **Type Safety:** Use shared types from `@padi/types`. Avoid `any`.
4. **Data Fetching:** Prefer Server Actions or server-side fetch in layouts/pages.

## 📁 Structure
```
apps/web/
├── app/             # App Router pages & layouts
├── components/      # Feature-specific components
├── lib/             # Utilities and API clients
├── stores/          # Zustand/State management
└── providers/       # Context providers
```

## 📋 Common Commands
```bash
pnpm dev             # Run dev server
pnpm test            # Run Vitest
pnpm lint            # Run ESlint
pnpm type-check      # Run TSC
```

## 📖 Pattern: Data Fetching
```typescript
// GOOD: Server-side fetching in Page
export default async function Page() {
  const data = await getStudentData(); // Server-side function
  return <StudentDashboard data={data} />;
}
```
