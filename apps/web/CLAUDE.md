# CLAUDE.md - PADI.AI Frontend Guidance

## Tech Stack

- **Framework:** Next.js 15 (App Router)
- **React:** 19
- **TypeScript:** 5.x
- **Styling:** Tailwind CSS
- **Auth:** @auth0/nextjs-auth0
- **UI:** @padi/ui (shared components)

## Project Structure

```
apps/web/
├── app/
│   ├── (auth)/              # Auth route group
│   │   └── login/
│   │       ├── page.tsx     # Login page
│   │       └── layout.tsx
│   ├── (public)/            # Public route group
│   │   ├── page.tsx         # Homepage
│   │   └── globals.css
│   ├── layout.tsx           # Root layout
│   └── providers/
│       └── auth0.tsx        # Auth0 provider
├── components/              # Local components
├── providers/               # React context providers
└── public/                  # Static assets
```

## Route Groups

- `(auth)` - Routes requiring authentication
- `(public)` - Public routes without auth

## Auth Pattern

```typescript
'use client';

import { useAuth0 } from '@auth0/nextjs/auth0';

export function StudentDashboard() {
  const { isAuthenticated, user, isLoading } = useAuth0();

  if (isLoading) return <div>Loading...</div>;
  if (!isAuthenticated) return <div>Please sign in</div>;

  return (
    <div>
      <h1>Welcome, {user?.name}</h1>
      {/* Dashboard content */}
    </div>
  );
}
```

## Protected Routes (Middleware)

See `apps/web/middleware.ts` pattern:
```typescript
import { NextResponse } from 'next/server';
import { auth } from '@/auth';

export async function middleware(request: Request) {
  const session = await auth();

  if (!session) {
    return NextResponse.redirect(new URL('/login', request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/dashboard/:path*'],
};
```

## Server Components (Default)

Next.js 15 defaults to Server Components. Use `'use client'` only for interactivity:

```typescript
// Default: Server Component
export default function Page() {
  return <div>Server-rendered content</div>;
}

// Client Component (for interactivity)
'use client';
export default function Button() {
  const [count, setCount] = useState(0);
  return <button onClick={() => setCount(c => c + 1)}>{count}</button>;
}
```

## API Client Pattern

```typescript
// app/lib/api.ts
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL;

export async function fetchStudentData(studentId: string) {
  const token = await getToken({ req });

  const response = await fetch(`${API_BASE_URL}/api/v1/students/${studentId}`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error('Failed to fetch student data');
  }

  return response.json();
}
```

## UI Components

```typescript
import { Button, Card, Badge } from '@padi/ui';

export function StudentCard({ student }) {
  return (
    <Card title={student.name}>
      <p>Grade {student.gradeLevel}</p>
      <Badge variant="success">Active</Badge>
      <Button>View Progress</Button>
    </Card>
  );
}
```

## Tailwind with PADI Colors

```typescript
// Always use design system colors
<div className="text-padiGreen-600 bg-padiBlue-50 border-gray-200">
```

## Environment Variables

```typescript
// Client-side (prefixed with NEXT_PUBLIC_)
const apiUrl = process.env.NEXT_PUBLIC_API_BASE_URL;

// Server-side (no prefix)
const auth0Secret = process.env.AUTH0_SECRET;
```

## References

- Next.js 15: https://nextjs.org/docs
- React 19: https://react.dev/
- Tailwind CSS: https://tailwindcss.com/docs
- @auth0/nextjs-auth0: https://github.com/auth0/nextjs-auth0
