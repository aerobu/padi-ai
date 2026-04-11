# Engineering Plan — Stage 1: Foundations (Months 1–3)

**Document ID:** ENG-001  
**Version:** 1.0  
**Date:** 2026-04-04  
**Author:** Principal Software Engineer  
**Status:** Draft  

**Scope:** Oregon standards database, COPPA-compliant authentication, seed question bank, and diagnostic assessment engine.

---

## 1. High-Level Architecture

### 1.1 System Context Diagram (C4 Level 1)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        EXTERNAL ACTORS                                  │
│                                                                         │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐                         │
│   │  Parent   │    │ Student  │    │  Admin   │                         │
│   │ (Browser) │    │(Browser) │    │(Browser) │                         │
│   └────┬─────┘    └────┬─────┘    └────┬─────┘                         │
│        │               │               │                                │
└────────┼───────────────┼───────────────┼────────────────────────────────┘
         │ HTTPS         │ HTTPS         │ HTTPS
         ▼               ▼               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                   PADI.AI SYSTEM BOUNDARY                       │
│                                                                         │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                    Next.js Web App (Vercel)                     │   │
│   │   • Parent registration & consent flows                        │   │
│   │   • Student diagnostic assessment UI                           │   │
│   │   • Admin question management                                  │   │
│   │   • Results display                                            │   │
│   └────────────────────────────┬────────────────────────────────────┘   │
│                                │ HTTPS (REST API)                       │
│   ┌────────────────────────────▼────────────────────────────────────┐   │
│   │                  FastAPI API Server (ECS/Fargate)               │   │
│   │   • Auth + COPPA consent management                            │   │
│   │   • Standards CRUD                                             │   │
│   │   • Question bank management                                   │   │
│   │   • Diagnostic assessment engine (CAT + BKT)                   │   │
│   └──────┬─────────────┬───────────────────────────────────────────┘   │
│          │ TCP:5432    │ TCP:6379                                       │
│   ┌──────▼──────┐ ┌───▼────────┐                                       │
│   │ PostgreSQL  │ │   Redis    │                                       │
│   │   17 RDS    │ │ElastiCache │                                       │
│   │ + pgvector  │ │   7.x      │                                       │
│   │ + pgcrypto  │ │            │                                       │
│   └─────────────┘ └────────────┘                                       │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌──────────────┐  ┌───────────────┐  ┌────────────────┐
│    Auth0     │  │   AWS SES     │  │    PostHog     │
│  (Identity)  │  │ (Email Svc)   │  │  (Analytics)   │
│  OAuth 2.0   │  │ SMTP/API      │  │  Event Stream  │
└──────────────┘  └───────────────┘  └────────────────┘
```

**Actor Interactions:**

| Actor | Interaction | Protocol |
|-------|------------|----------|
| Parent | Registers account, provides COPPA consent, creates student profiles, views diagnostic results | HTTPS via browser → Vercel CDN → API |
| Student | Takes diagnostic assessment (read-only: no PII input) | HTTPS via browser → Vercel CDN → API |
| Admin | Manages question bank, views standards, reviews content | HTTPS via browser → Vercel CDN → API |
| Auth0 | Handles OAuth 2.0 token issuance, password hashing, MFA | HTTPS (Auth0 Management API + Authorization Code flow) |
| AWS SES | Sends transactional emails: verification, consent confirmation, results ready | HTTPS (AWS SDK v3) |
| PostHog | Receives frontend analytics events (page views, assessment progress, timing) | HTTPS (PostHog JS SDK) |

### 1.2 Container Diagram (C4 Level 2)

```
┌──────────────────────────────────────────────────────────────────────┐
│                     DEPLOYMENT CONTAINERS                            │
│                                                                      │
│  ┌─────────────────────────────────────┐                             │
│  │   Next.js 15 Web App               │                             │
│  │   ─────────────────────             │                             │
│  │   Host: Vercel Edge Network         │                             │
│  │   Runtime: Node.js 20 (Edge + SSR)  │                             │
│  │   Framework: React 19, App Router   │                             │
│  │                                     │                             │
│  │   Responsibilities:                 │                             │
│  │   • Server-side rendering           │                             │
│  │   • Static page generation          │                             │
│  │   • Auth0 Universal Login redirect  │                             │
│  │   • Client-side assessment UI       │                             │
│  │   • PostHog event emission          │                             │
│  └──────────┬──────────────────────────┘                             │
│             │                                                        │
│             │ HTTPS/JSON (REST)                                      │
│             │ Authorization: Bearer <JWT>                            │
│             ▼                                                        │
│  ┌─────────────────────────────────────┐                             │
│  │   FastAPI API Server                │                             │
│  │   ─────────────────────             │                             │
│  │   Host: AWS ECS Fargate             │                             │
│  │   Runtime: Python 3.12              │                             │
│  │   Framework: FastAPI 0.115+         │                             │
│  │   ORM: SQLAlchemy 2.0 (async)       │                             │
│  │   Port: 8000 (behind ALB:443)       │                             │
│  │                                     │                             │
│  │   Responsibilities:                 │                             │
│  │   • JWT validation (Auth0 JWKS)     │                             │
│  │   • COPPA consent management        │                             │
│  │   • Standards data serving          │                             │
│  │   • Question selection (CAT)        │                             │
│  │   • BKT computation                 │                             │
│  │   • Assessment state management     │                             │
│  └─────┬───────────────┬───────────────┘                             │
│        │               │                                             │
│  TCP:5432        TCP:6379                                            │
│  (asyncpg)       (aioredis)                                          │
│        │               │                                             │
│  ┌─────▼─────┐   ┌─────▼──────┐                                     │
│  │PostgreSQL │   │   Redis    │                                     │
│  │  17 RDS   │   │ElastiCache │                                     │
│  │───────────│   │────────────│                                     │
│  │Multi-AZ   │   │Single-node │                                     │
│  │(prod)     │   │cluster mode│                                     │
│  │           │   │            │                                     │
│  │Extensions:│   │Usage:      │                                     │
│  │• pgvector │   │• Session   │                                     │
│  │• pgcrypto │   │  cache     │                                     │
│  │• ltree    │   │• Rate limit│                                     │
│  │• pg_trgm  │   │  counters  │                                     │
│  └───────────┘   │• Assessment│                                     │
│                  │  state     │                                     │
│                  └────────────┘                                     │
└──────────────────────────────────────────────────────────────────────┘

Data Flows:
  Browser ──HTTPS──▶ Vercel (CDN + SSR)
  Vercel  ──HTTPS──▶ ALB ──HTTP──▶ ECS Fargate (FastAPI :8000)
  FastAPI ──TCP────▶ PostgreSQL RDS :5432 (asyncpg, TLS)
  FastAPI ──TCP────▶ Redis ElastiCache :6379 (TLS in-transit)
  FastAPI ──HTTPS──▶ Auth0 (JWKS endpoint, Management API)
  FastAPI ──HTTPS──▶ AWS SES (SendEmail API)
  Browser ──HTTPS──▶ PostHog Cloud (analytics events)
```

### 1.3 Component Diagram (C4 Level 3) — Backend

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    FastAPI API Server (Internal Components)              │
│                                                                         │
│  ┌─────────────┐  ┌────────────────┐  ┌────────────────┐               │
│  │ Auth Router  │  │Standards Router│  │Assessment      │               │
│  │ /auth/*      │  │ /standards/*   │  │  Router        │               │
│  │              │  │                │  │ /assessments/* │               │
│  └──────┬───┬──┘  └───────┬────────┘  └───┬────────┬───┘               │
│         │   │             │               │        │                    │
│         │   │  ┌──────────┴────┐    ┌─────┘        │                    │
│         │   │  │               │    │              │                    │
│  ┌──────▼───┼──▼───────────────▼────▼──┐           │                    │
│  │     Auth Middleware (JWT)           │           │                    │
│  │  • Validate Auth0 JWT              │           │                    │
│  │  • Extract user claims             │           │                    │
│  │  • Enforce RBAC (parent/admin)     │           │                    │
│  │  • Rate limiting check             │           │                    │
│  └─────────────────────────────────────┘           │                    │
│         │            │                │            │                    │
│  ┌──────┼────────────┼────────────────┼────────────┼──────┐            │
│  │      │  SERVICE LAYER              │            │      │            │
│  │      │                             │            │      │            │
│  │  ┌───▼──────────┐  ┌──────────────▼──┐  ┌──────▼───┐  │            │
│  │  │ Consent      │  │ Assessment     │  │ Question │  │            │
│  │  │ Service      │  │ Service        │  │ Service  │  │            │
│  │  │              │  │                │  │ (Admin)  │  │            │
│  │  │• initiate()  │  │• start_diag() │  │          │  │            │
│  │  │• confirm()   │  │• get_next_q() │  │• create()│  │            │
│  │  │• verify()    │  │• submit()     │  │• update()│  │            │
│  │  │• revoke()    │  │• complete()   │  │• list()  │  │            │
│  │  └──────────────┘  │• calc_bkt()   │  │• import()│  │            │
│  │                    └───────┬────────┘  └──────┬──┘  │            │
│  │                            │                  │      │            │
│  │                    ┌───────▼──────┐           │      │            │
│  │                    │ BKT Service  │           │      │            │
│  │                    │              │           │      │            │
│  │                    │• init_from() │           │      │            │
│  │                    │• update()    │           │      │            │
│  │                    │• mastery_p() │           │      │            │
│  │                    └──────────────┘           │      │            │
│  │                            │                  │      │            │
│  │                    ┌───────▼──────┐           │      │            │
│  │                    │ Question     │           │      │            │
│  │                    │ Selection    │           │      │            │
│  │                    │ Service      │           │      │            │
│  │                    │              │           │      │            │
│  │                    │• select()    │           │      │            │
│  │                    │• estimate_θ()│           │      │            │
│  │                    └──────────────┘           │      │            │
│  └──────────────────────────────────────────────────────┘            │
│         │            │             │             │                    │
│  ┌──────┼────────────┼─────────────┼─────────────┼──────┐            │
│  │      │  REPOSITORY LAYER        │             │      │            │
│  │      │                          │             │      │            │
│  │  ┌───▼──────────┐  ┌───────────▼──┐  ┌───────▼──┐   │            │
│  │  │ Student      │  │ Assessment  │  │Standards│   │            │
│  │  │ Repository   │  │ Repository  │  │  Repo  │   │            │
│  │  └──────────────┘  └─────────────┘  └────────┘   │            │
│  │                                                    │            │
│  │  ┌──────────────┐  ┌─────────────┐                 │            │
│  │  │ Consent      │  │ Question    │                 │            │
│  │  │ Repository   │  │ Repository  │                 │            │
│  │  └──────────────┘  └─────────────┘                 │            │
│  └────────────────────────────────────────────────────┘            │
│                          │                                          │
│              ┌───────────▼───────────┐                               │
│              │   SQLAlchemy 2.0      │                               │
│              │   (async session)     │                               │
│              └───────────┬───────────┘                               │
│                          │ asyncpg                                   │
└──────────────────────────┼──────────────────────────────────────────┘
                           ▼
                    PostgreSQL 17 RDS
```

**Component Dependency Matrix:**

| Component | Depends On |
|-----------|-----------|
| Auth Router | Auth Middleware, Consent Service, Student Repository |
| Standards Router | Auth Middleware, Standards Repository |
| Assessment Router | Auth Middleware, Assessment Service |
| Question Router | Auth Middleware (admin scope), Question Service |
| Assessment Service | BKT Service, Question Selection Service, Assessment Repository, Question Repository |
| BKT Service | pyBKT library (pure computation, no DB dependency) |
| Question Selection Service | Question Repository (pure computation with data input) |
| Consent Service | Consent Repository, Student Repository, AWS SES client |
| All Repositories | SQLAlchemy async session (injected via FastAPI `Depends`) |

### 1.4 Component Diagram — Frontend (Next.js)

```
app/                                    # Next.js App Router
├── layout.tsx                          # Root layout (SC): HTML shell, fonts, PostHog
├── globals.css                         # Tailwind CSS + design tokens
├── providers.tsx                       # Client: Auth0Provider, QueryClientProvider
│
├── (auth)/                             # Route group: unauthenticated pages
│   ├── layout.tsx                      # SC: centered card layout, no nav
│   ├── register/
│   │   └── page.tsx                    # CC: registration form → Auth0 signup
│   ├── verify-email/
│   │   └── page.tsx                    # SC: email verification landing
│   └── login/
│       └── page.tsx                    # CC: login form → Auth0 authorize
│
├── (onboarding)/                       # Route group: post-auth pre-dashboard
│   ├── layout.tsx                      # SC: Auth guard + progress stepper
│   ├── consent/
│   │   └── page.tsx                    # CC: COPPA consent form + e-sign
│   └── create-student/
│       └── page.tsx                    # CC: child profile creation form
│
├── (dashboard)/                        # Route group: authenticated parent
│   ├── layout.tsx                      # SC: Auth guard + sidebar nav + top bar
│   ├── page.tsx                        # SC: Parent home — student cards
│   └── diagnostic/
│       ├── start/
│       │   └── page.tsx               # CC: Assessment launcher (select child)
│       ├── [sessionId]/
│       │   └── page.tsx               # CC: Live assessment (question display)
│       └── results/
│           └── page.tsx               # SC+CC: Results display (charts)
│
├── (admin)/                            # Route group: admin-only
│   ├── layout.tsx                      # SC: Admin auth guard + nav
│   └── questions/
│       └── page.tsx                    # CC: Question CRUD table
│
└── api/                                # Next.js API routes (minimal — proxy only)
    └── auth/
        ├── callback/route.ts          # Auth0 callback handler
        └── logout/route.ts            # Auth0 logout handler

components/                             # Shared UI components
├── ui/                                 # Primitive components (Button, Input, Card, etc.)
│   ├── button.tsx                     # CC: Variants: primary, secondary, ghost, danger
│   ├── input.tsx                      # CC: Form input with label, error, hint
│   ├── card.tsx                       # SC/CC: Container card with header slot
│   ├── modal.tsx                      # CC: Dialog overlay with focus trap
│   ├── progress-bar.tsx               # CC: Animated progress indicator
│   ├── badge.tsx                      # SC: Status/tag badge
│   ├── skeleton.tsx                   # CC: Loading skeleton
│   └── toast.tsx                      # CC: Toast notification system
├── assessment/
│   ├── question-card.tsx              # CC: Renders question with answer options
│   ├── answer-option.tsx              # CC: Individual answer choice (A/B/C/D)
│   ├── timer-display.tsx              # CC: Countdown/elapsed timer
│   ├── progress-tracker.tsx           # CC: Question N of M with domain progress
│   └── results-summary.tsx            # CC: Skills radar chart + category cards
├── layout/
│   ├── sidebar-nav.tsx                # CC: Collapsible navigation sidebar
│   ├── top-bar.tsx                    # CC: User avatar + notifications
│   └── page-header.tsx               # SC: Page title + breadcrumbs
└── forms/
    ├── consent-form.tsx               # CC: COPPA consent with checkboxes
    └── student-form.tsx               # CC: Create/edit student profile

lib/
├── api-client.ts                      # Typed fetch wrapper with interceptors
├── auth.ts                            # Auth0 config + token management
├── constants.ts                       # App-wide constants
└── utils.ts                           # Shared utilities (cn, formatDate, etc.)

stores/                                 # Zustand state management
├── assessment-store.ts                # Live assessment session state
├── auth-store.ts                      # Auth state (user, tokens, role)
└── ui-store.ts                        # UI state (sidebar, modals, toasts)

hooks/
├── use-assessment.ts                  # Assessment query/mutation hooks (SWR)
├── use-auth.ts                        # Auth state + guards
├── use-standards.ts                   # Standards data fetching
└── use-students.ts                    # Student CRUD hooks
```

**Component Details:**

| Page/Component | Type | Data Fetching | Key Props / State |
|---------------|------|---------------|-------------------|
| `(auth)/register/page.tsx` | CC | None (form → Auth0 redirect) | `email, password, confirmPassword` |
| `(auth)/login/page.tsx` | CC | None (form → Auth0 redirect) | `email, password, rememberMe` |
| `(onboarding)/consent/page.tsx` | CC | SWR: `GET /consent/status` | `consentChecks: boolean[], signature: string, agreed: boolean` |
| `(onboarding)/create-student/page.tsx` | CC | SWR mutation: `POST /students` | `displayName, gradeLevel, avatarId` |
| `(dashboard)/page.tsx` | SC | RSC fetch: `GET /students` | Students array from server |
| `diagnostic/start/page.tsx` | CC | SWR: `GET /students` | `selectedStudentId, isStarting` |
| `diagnostic/[sessionId]/page.tsx` | CC | SWR + Zustand | Assessment store (see below) |
| `diagnostic/results/page.tsx` | SC+CC | RSC: `GET /assessments/{id}/results` | Results data from server, chart interactivity client |
| `(admin)/questions/page.tsx` | CC | SWR: paginated `GET /questions` | `filters, page, sortBy, editingQuestion` |

**Zustand Store Definitions:**

```typescript
// stores/assessment-store.ts
import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

interface Question {
  id: string;
  standardCode: string;
  stem: string;
  options: { key: string; text: string; imageUrl?: string }[];
  difficulty: number;
  domainLabel: string;
}

interface ResponseRecord {
  questionId: string;
  selectedOption: string;
  isCorrect: boolean;
  timeSpentMs: number;
  timestamp: string;
}

interface AssessmentState {
  // Session metadata
  sessionId: string | null;
  assessmentId: string | null;
  studentId: string | null;
  totalQuestions: number;

  // Current question
  currentQuestion: Question | null;
  questionIndex: number;

  // Tracking
  responses: ResponseRecord[];
  questionsAnswered: number;
  startTime: string | null;
  timeElapsedMs: number;

  // UI state
  isPaused: boolean;
  isSubmitting: boolean;
  isComplete: boolean;
  selectedOption: string | null;
  showFeedback: boolean;

  // Actions
  startSession: (params: {
    sessionId: string;
    assessmentId: string;
    studentId: string;
    totalQuestions: number;
  }) => void;
  setCurrentQuestion: (question: Question) => void;
  selectOption: (optionKey: string) => void;
  recordResponse: (response: ResponseRecord) => void;
  setSubmitting: (isSubmitting: boolean) => void;
  pauseSession: () => void;
  resumeSession: () => void;
  completeSession: () => void;
  resetSession: () => void;
  tick: (elapsedMs: number) => void;
}

export const useAssessmentStore = create<AssessmentState>()(
  devtools(
    persist(
      (set, get) => ({
        // Initial state
        sessionId: null,
        assessmentId: null,
        studentId: null,
        totalQuestions: 0,
        currentQuestion: null,
        questionIndex: 0,
        responses: [],
        questionsAnswered: 0,
        startTime: null,
        timeElapsedMs: 0,
        isPaused: false,
        isSubmitting: false,
        isComplete: false,
        selectedOption: null,
        showFeedback: false,

        // Action implementations
        startSession: (params) =>
          set({
            ...params,
            questionIndex: 0,
            responses: [],
            questionsAnswered: 0,
            startTime: new Date().toISOString(),
            timeElapsedMs: 0,
            isPaused: false,
            isSubmitting: false,
            isComplete: false,
            selectedOption: null,
            showFeedback: false,
          }),

        setCurrentQuestion: (question) =>
          set({
            currentQuestion: question,
            selectedOption: null,
            showFeedback: false,
            questionIndex: get().questionIndex + 1,
          }),

        selectOption: (optionKey) =>
          set({ selectedOption: optionKey }),

        recordResponse: (response) =>
          set((state) => ({
            responses: [...state.responses, response],
            questionsAnswered: state.questionsAnswered + 1,
            showFeedback: true,
          })),

        setSubmitting: (isSubmitting) => set({ isSubmitting }),

        pauseSession: () => set({ isPaused: true }),
        resumeSession: () => set({ isPaused: false }),
        completeSession: () => set({ isComplete: true }),

        resetSession: () =>
          set({
            sessionId: null,
            assessmentId: null,
            studentId: null,
            totalQuestions: 0,
            currentQuestion: null,
            questionIndex: 0,
            responses: [],
            questionsAnswered: 0,
            startTime: null,
            timeElapsedMs: 0,
            isPaused: false,
            isSubmitting: false,
            isComplete: false,
            selectedOption: null,
            showFeedback: false,
          }),

        tick: (elapsedMs) =>
          set({ timeElapsedMs: elapsedMs }),
      }),
      {
        name: 'padi-ai-assessment',
        partialize: (state) => ({
          sessionId: state.sessionId,
          assessmentId: state.assessmentId,
          studentId: state.studentId,
          responses: state.responses,
          questionsAnswered: state.questionsAnswered,
          startTime: state.startTime,
          timeElapsedMs: state.timeElapsedMs,
          isPaused: state.isPaused,
        }),
      }
    )
  )
);
```

```typescript
// stores/auth-store.ts
import { create } from 'zustand';

type UserRole = 'parent' | 'admin';

interface AuthUser {
  id: string;
  email: string;
  displayName: string;
  role: UserRole;
  auth0Sub: string;
  emailVerified: boolean;
  consentCompleted: boolean;
  hasStudents: boolean;
}

interface AuthState {
  user: AuthUser | null;
  accessToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;

  setUser: (user: AuthUser | null) => void;
  setAccessToken: (token: string | null) => void;
  setLoading: (loading: boolean) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()((set) => ({
  user: null,
  accessToken: null,
  isAuthenticated: false,
  isLoading: true,

  setUser: (user) =>
    set({ user, isAuthenticated: !!user }),
  setAccessToken: (accessToken) =>
    set({ accessToken }),
  setLoading: (isLoading) =>
    set({ isLoading }),
  logout: () =>
    set({
      user: null,
      accessToken: null,
      isAuthenticated: false,
      isLoading: false,
    }),
}));
```

### 1.5 Data Flow Diagrams

**Flow 1: Parent Registration + COPPA Consent**

```
Step  Actor/Component          Action                                Data
────  ────────────────────    ──────────────────────────            ──────────────────
 1    Parent (Browser)        Fills registration form               email, password
 2    Next.js (CC)            Redirects to Auth0 Universal Login    Auth0 authorize URL
 3    Auth0                   Creates user, sends verification      Auth0 user record
 4    Auth0                   Redirects back with auth code         authorization_code
 5    Next.js (API route)     Exchanges code for tokens             access_token, id_token
 6    Next.js (CC)            Calls POST /auth/register             { auth0Sub, email, displayName }
 7    FastAPI Auth Router     Validates JWT, creates user record    →
 8    FastAPI                 INSERT INTO users                     users row (id, auth0_sub, email_enc)
 9    FastAPI                 Returns { userId, needsConsent: true }
10    Next.js (CC)            Redirects to /onboarding/consent
11    Parent (Browser)        Reads COPPA notice, checks boxes      consent form data
12    Next.js (CC)            Calls POST /consent/initiate          { userId, consentData }
13    FastAPI Consent Svc     INSERT INTO consent_records           consent row (pending)
14    FastAPI                 Calls AWS SES SendEmail               verification email
15    AWS SES                 Delivers email to parent              email with confirm link
16    Parent (Email client)   Clicks confirmation link              token in URL
17    Browser                 GET /consent/confirm?token=xxx
18    Next.js (SC)            Calls POST /consent/confirm           { token }
19    FastAPI Consent Svc     Validates token (HMAC + expiry)       →
20    FastAPI                 UPDATE consent_records SET status='active', confirmed_at=now()
21    FastAPI                 INSERT INTO audit_log                 consent confirmation event
22    FastAPI                 Returns { status: 'active' }
23    Next.js (CC)            Redirects to /onboarding/create-student
```

**Flow 2: Student Takes Diagnostic Assessment**

```
Step  Actor/Component          Action                                Data
────  ────────────────────    ──────────────────────────            ──────────────────
 1    Parent (Browser)        Navigates to /diagnostic/start        →
 2    Parent (Browser)        Selects child, clicks "Start"         studentId
 3    Next.js (CC)            Calls POST /assessments               { studentId, type: 'diagnostic' }
 4    FastAPI Assessment Rtr  Validates: parent owns student, consent active
 5    Assessment Service      Creates assessment record             →
 6    FastAPI                 INSERT INTO assessments                assessment row
 7    FastAPI                 INSERT INTO assessment_sessions        session row
 8    Redis                   SET assessment:{id}:state = initial   CAT state cache
 9    FastAPI                 Returns { assessmentId, sessionId, totalQuestions: 40 }
10    Next.js (CC)            Redirects to /diagnostic/{sessionId}
11    Browser (CC)            Calls GET /assessments/{id}/next-question
12    QuestionSelection Svc   Loads question pool for uncovered standards
13    QuestionSelection Svc   Runs CAT algorithm:
                              • Identify standard with lowest coverage
                              • Estimate θ from prior (initial = 0.0)
                              • Select question with difficulty closest to θ
                              • Apply Fisher information maximization
14    FastAPI                 Returns { question: { id, stem, options, domain } }
15    Student (Browser)       Reads question, selects answer         selectedOption
16    Next.js (CC)            Calls POST /assessments/{id}/responses { questionId, answer, timeMs }
17    Assessment Service      Evaluates correctness against answer key
18    BKT Service             Updates BKT state for the standard:
                              • P(L_t) = P(L_t|obs) using forward algorithm
                              • Cache updated state in Redis
19    QuestionSelection Svc   Updates θ estimate using response
20    FastAPI                 INSERT INTO assessment_responses       response row
21    FastAPI                 Returns { isCorrect, feedback, progress }
22    Next.js (CC)            Displays brief feedback (1.5s)
23    Next.js (CC)            Updates Zustand store (questionsAnswered++)
24    [Repeat steps 11-23 for remaining ~39 questions]
25    Assessment Service      Detects completion (all standards covered, min 35 questions)
26    Next.js (CC)            Calls PUT /assessments/{id}/complete
27    Assessment Service      Finalizes BKT states for all standards
28    Assessment Service      Calculates per-standard mastery P(L)
29    Assessment Service      Classifies: Below Par / On Par / Above Par
30    FastAPI                 INSERT INTO student_skill_states       one row per standard
31    FastAPI                 UPDATE assessments SET status='completed', completed_at=now()
32    FastAPI                 Returns { results: { overallScore, skillStates[], gapAnalysis } }
33    Next.js (CC)            Redirects to /diagnostic/results
34    Next.js (SC)            Server-fetches results, renders summary
35    FastAPI                 Calls AWS SES: "Diagnostic results ready" email to parent
```


---

## 2. Detailed System Design

### 2.1 Database Schema (Complete)

**Migration Strategy:** All schema changes managed via Alembic. Each migration is a single atomic transaction. Down-migrations are always provided.

**Encryption Strategy:** PII fields (parent email, parent name) encrypted at application layer using `pgcrypto` AES-256-CBC with a key from AWS Secrets Manager. Hashed lookup columns enable indexed queries on encrypted data.

```sql
-- =============================================================================
-- PADI.AI — Stage 1 Database Schema
-- PostgreSQL 17 with extensions: pgcrypto, pgvector, ltree, pg_trgm
-- =============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pgvector";
CREATE EXTENSION IF NOT EXISTS "ltree";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- =============================================================================
-- TRIGGER FUNCTION: Auto-update updated_at timestamp
-- =============================================================================
CREATE OR REPLACE FUNCTION trigger_set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- TRIGGER FUNCTION: Audit log insertion
-- =============================================================================
CREATE OR REPLACE FUNCTION trigger_audit_log()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO audit_log (
        id, table_name, record_id, action,
        old_data, new_data, performed_by, performed_at
    ) VALUES (
        gen_random_uuid(),
        TG_TABLE_NAME,
        COALESCE(NEW.id, OLD.id),
        TG_OP,
        CASE WHEN TG_OP IN ('UPDATE', 'DELETE') THEN to_jsonb(OLD) ELSE NULL END,
        CASE WHEN TG_OP IN ('INSERT', 'UPDATE') THEN to_jsonb(NEW) ELSE NULL END,
        current_setting('app.current_user_id', true)::uuid,
        CURRENT_TIMESTAMP
    );
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- TABLE: audit_log
-- Purpose: Immutable audit trail for COPPA compliance and data governance
-- =============================================================================
CREATE TABLE audit_log (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    table_name      VARCHAR(64) NOT NULL,
    record_id       UUID NOT NULL,
    action          VARCHAR(10) NOT NULL CHECK (action IN ('INSERT', 'UPDATE', 'DELETE')),
    old_data        JSONB,
    new_data        JSONB,
    performed_by    UUID,           -- NULL for system actions
    performed_at    TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ip_address      INET,
    user_agent      TEXT
);

-- Audit log is append-only; index for lookups by record
CREATE INDEX idx_audit_log_table_record ON audit_log (table_name, record_id);
CREATE INDEX idx_audit_log_performed_at ON audit_log (performed_at);
-- Partition audit_log by month for manageability (applied in Alembic migration)
-- CREATE TABLE audit_log ... PARTITION BY RANGE (performed_at);

-- =============================================================================
-- TABLE: users (Parents / Admins)
-- PII fields encrypted with pgcrypto AES-256; hashed columns for lookups
-- =============================================================================
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    auth0_sub       VARCHAR(128) NOT NULL UNIQUE,
    
    -- Encrypted PII fields (AES-256-CBC via application layer)
    email_encrypted BYTEA NOT NULL,
    email_hash      VARCHAR(64) NOT NULL UNIQUE,  -- SHA-256 hash for lookups
    name_encrypted  BYTEA,
    
    -- Non-PII fields
    display_name    VARCHAR(100) NOT NULL,
    role            VARCHAR(20) NOT NULL DEFAULT 'parent'
                    CHECK (role IN ('parent', 'admin')),
    email_verified  BOOLEAN NOT NULL DEFAULT FALSE,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    
    -- Metadata
    last_login_at   TIMESTAMPTZ,
    login_count     INTEGER NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Lookup by Auth0 subject (every authenticated request)
CREATE UNIQUE INDEX idx_users_auth0_sub ON users (auth0_sub);
-- Lookup by email hash (registration uniqueness check)
CREATE UNIQUE INDEX idx_users_email_hash ON users (email_hash);
-- Filter active users
CREATE INDEX idx_users_role_active ON users (role) WHERE is_active = TRUE;

CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

CREATE TRIGGER trg_users_audit
    AFTER INSERT OR UPDATE OR DELETE ON users
    FOR EACH ROW EXECUTE FUNCTION trigger_audit_log();

-- =============================================================================
-- TABLE: students
-- Child profiles linked to parent. No direct PII stored.
-- =============================================================================
CREATE TABLE students (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    parent_id       UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    display_name    VARCHAR(50) NOT NULL,    -- Nickname/alias only, no real name
    avatar_id       VARCHAR(20) NOT NULL DEFAULT 'avatar_default',
    grade_level     SMALLINT NOT NULL DEFAULT 4
                    CHECK (grade_level BETWEEN 3 AND 5),  -- 4th graders, allow ±1
    birth_year      SMALLINT,                -- Optional, year only (COPPA minimal)
    
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- A parent can have multiple children but display names must be unique per parent
    CONSTRAINT uq_student_parent_name UNIQUE (parent_id, display_name)
);

-- Parent → children lookups (dashboard load)
CREATE INDEX idx_students_parent_id ON students (parent_id) WHERE is_active = TRUE;

CREATE TRIGGER trg_students_updated_at
    BEFORE UPDATE ON students
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

CREATE TRIGGER trg_students_audit
    AFTER INSERT OR UPDATE OR DELETE ON students
    FOR EACH ROW EXECUTE FUNCTION trigger_audit_log();

-- =============================================================================
-- TABLE: consent_records
-- COPPA verifiable parental consent. Immutable once confirmed.
-- =============================================================================
CREATE TABLE consent_records (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    parent_id           UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    student_id          UUID REFERENCES students(id) ON DELETE SET NULL,
    
    -- Consent details
    consent_type        VARCHAR(30) NOT NULL DEFAULT 'coppa_verifiable'
                        CHECK (consent_type IN ('coppa_verifiable', 'coppa_school', 'data_processing')),
    status              VARCHAR(20) NOT NULL DEFAULT 'pending'
                        CHECK (status IN ('pending', 'active', 'revoked', 'expired')),
    consent_version     VARCHAR(20) NOT NULL DEFAULT '1.0',  -- Track policy version
    
    -- Verification
    verification_method VARCHAR(30) NOT NULL DEFAULT 'email_plus'
                        CHECK (verification_method IN ('email_plus', 'credit_card', 'phone', 'video')),
    verification_token  VARCHAR(256),           -- HMAC token for email confirmation
    token_expires_at    TIMESTAMPTZ,
    
    -- Consent payload
    consent_text_hash   VARCHAR(64) NOT NULL,   -- SHA-256 of consent text shown
    ip_address          INET NOT NULL,
    user_agent          TEXT NOT NULL,
    
    -- Timestamps
    initiated_at        TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    confirmed_at        TIMESTAMPTZ,
    revoked_at          TIMESTAMPTZ,
    expires_at          TIMESTAMPTZ,            -- Annual renewal for COPPA
    
    created_at          TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Lookup active consent for a parent
CREATE INDEX idx_consent_parent_status ON consent_records (parent_id, status);
-- Token lookup for email confirmation
CREATE INDEX idx_consent_token ON consent_records (verification_token)
    WHERE status = 'pending' AND token_expires_at > CURRENT_TIMESTAMP;
-- Expiring consent monitoring
CREATE INDEX idx_consent_expiry ON consent_records (expires_at)
    WHERE status = 'active';

CREATE TRIGGER trg_consent_updated_at
    BEFORE UPDATE ON consent_records
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

CREATE TRIGGER trg_consent_audit
    AFTER INSERT OR UPDATE OR DELETE ON consent_records
    FOR EACH ROW EXECUTE FUNCTION trigger_audit_log();

-- =============================================================================
-- TABLE: standards
-- Oregon 2021 CCSSM Grade 4 mathematics standards
-- =============================================================================
CREATE TABLE standards (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    code            VARCHAR(20) NOT NULL UNIQUE,    -- e.g., '4.OA.A.1'
    domain          VARCHAR(10) NOT NULL,            -- e.g., '4.OA'
    cluster         VARCHAR(10) NOT NULL,            -- e.g., '4.OA.A'
    
    title           TEXT NOT NULL,                   -- Short title
    description     TEXT NOT NULL,                   -- Full standard description
    
    grade_level     SMALLINT NOT NULL DEFAULT 4,
    
    -- Metadata for assessment engine
    cognitive_level VARCHAR(20) NOT NULL DEFAULT 'understand'
                    CHECK (cognitive_level IN ('remember', 'understand', 'apply', 'analyze')),
    estimated_difficulty NUMERIC(3,2) NOT NULL DEFAULT 0.50
                    CHECK (estimated_difficulty BETWEEN 0.0 AND 1.0),
    
    -- BKT default parameters for this standard
    bkt_p_l0       NUMERIC(5,4) NOT NULL DEFAULT 0.1000,  -- P(L0): prior knowledge
    bkt_p_transit  NUMERIC(5,4) NOT NULL DEFAULT 0.1000,  -- P(T): learn rate
    bkt_p_slip     NUMERIC(5,4) NOT NULL DEFAULT 0.0500,  -- P(S): slip rate
    bkt_p_guess    NUMERIC(5,4) NOT NULL DEFAULT 0.2500,  -- P(G): guess rate
    
    -- Ordering and hierarchy
    sort_order      INTEGER NOT NULL DEFAULT 0,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    
    -- Embeddings for semantic search (Stage 2 will use these)
    description_embedding VECTOR(1536),
    
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Primary lookup by code
CREATE UNIQUE INDEX idx_standards_code ON standards (code);
-- Filter by domain for assessment question pools
CREATE INDEX idx_standards_domain_active ON standards (domain, is_active)
    WHERE is_active = TRUE;
-- Grade + domain for API queries
CREATE INDEX idx_standards_grade_domain ON standards (grade_level, domain);
-- Vector similarity search (Stage 2)
CREATE INDEX idx_standards_embedding ON standards
    USING ivfflat (description_embedding vector_cosine_ops) WITH (lists = 10);

CREATE TRIGGER trg_standards_updated_at
    BEFORE UPDATE ON standards
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

-- =============================================================================
-- TABLE: prerequisite_relationships
-- Directed edges: prerequisite_code → standard_code
-- =============================================================================
CREATE TABLE prerequisite_relationships (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    standard_code       VARCHAR(20) NOT NULL REFERENCES standards(code),
    prerequisite_code   VARCHAR(20) NOT NULL REFERENCES standards(code),
    
    relationship_type   VARCHAR(20) NOT NULL DEFAULT 'prerequisite'
                        CHECK (relationship_type IN ('prerequisite', 'corequisite', 'builds_on')),
    strength            NUMERIC(3,2) NOT NULL DEFAULT 1.0
                        CHECK (strength BETWEEN 0.0 AND 1.0),
    
    created_at          TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Prevent duplicate edges and self-references
    CONSTRAINT uq_prereq_pair UNIQUE (standard_code, prerequisite_code),
    CONSTRAINT chk_no_self_ref CHECK (standard_code <> prerequisite_code)
);

-- Lookup prerequisites for a given standard
CREATE INDEX idx_prereqs_standard ON prerequisite_relationships (standard_code);
-- Reverse lookup: what depends on this standard?
CREATE INDEX idx_prereqs_prereq ON prerequisite_relationships (prerequisite_code);

-- =============================================================================
-- TABLE: questions
-- Seed question bank for diagnostic assessment
-- =============================================================================
CREATE TABLE questions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Classification
    standard_code   VARCHAR(20) NOT NULL REFERENCES standards(code),
    difficulty      SMALLINT NOT NULL CHECK (difficulty BETWEEN 1 AND 5),
                    -- 1=very easy, 2=easy, 3=medium, 4=hard, 5=very hard
    
    -- IRT parameters (calibrated or estimated)
    irt_difficulty  NUMERIC(5,3) NOT NULL DEFAULT 0.000,  -- b parameter (-3.0 to 3.0)
    irt_discrimination NUMERIC(5,3) NOT NULL DEFAULT 1.000,  -- a parameter (0.2 to 3.0)
    irt_guessing    NUMERIC(5,4) NOT NULL DEFAULT 0.2500,  -- c parameter (0.0 to 0.5)
    
    -- Question content
    question_type   VARCHAR(20) NOT NULL DEFAULT 'multiple_choice'
                    CHECK (question_type IN ('multiple_choice', 'numeric_input', 'drag_drop')),
    stem            TEXT NOT NULL,               -- Question text (supports Markdown + LaTeX)
    stem_image_url  TEXT,                        -- Optional illustration
    
    -- Answer options (JSONB array for flexibility)
    options         JSONB NOT NULL DEFAULT '[]',
    -- Format: [{"key": "A", "text": "42", "image_url": null}, ...]
    
    correct_answer  VARCHAR(10) NOT NULL,        -- 'A', 'B', 'C', 'D' or numeric value
    
    -- Explanation shown after answer
    explanation     TEXT,
    explanation_image_url TEXT,
    
    -- Metadata
    source          VARCHAR(30) NOT NULL DEFAULT 'seed'
                    CHECK (source IN ('seed', 'ai_generated', 'imported', 'teacher_submitted')),
    status          VARCHAR(20) NOT NULL DEFAULT 'active'
                    CHECK (status IN ('draft', 'review', 'active', 'retired')),
    
    -- Quality tracking
    times_shown     INTEGER NOT NULL DEFAULT 0,
    times_correct   INTEGER NOT NULL DEFAULT 0,
    observed_difficulty NUMERIC(5,4),  -- times_correct / times_shown (updated async)
    
    -- Content embedding for dedup (Stage 2)
    content_embedding VECTOR(1536),
    
    -- Provenance
    created_by      UUID REFERENCES users(id),
    reviewed_by     UUID REFERENCES users(id),
    reviewed_at     TIMESTAMPTZ,
    
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Primary query: questions by standard and difficulty for CAT engine
CREATE INDEX idx_questions_standard_diff ON questions (standard_code, difficulty)
    WHERE status = 'active';
-- Question pool loading: all active questions for assessment
CREATE INDEX idx_questions_active ON questions (status, standard_code)
    WHERE status = 'active';
-- IRT parameter range queries for CAT item selection
CREATE INDEX idx_questions_irt ON questions (irt_difficulty, irt_discrimination)
    WHERE status = 'active';
-- Dedup search using vector similarity (Stage 2)
CREATE INDEX idx_questions_embedding ON questions
    USING ivfflat (content_embedding vector_cosine_ops) WITH (lists = 50);
-- Full-text search on question stems (admin search)
CREATE INDEX idx_questions_stem_trgm ON questions USING gin (stem gin_trgm_ops);

CREATE TRIGGER trg_questions_updated_at
    BEFORE UPDATE ON questions
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

CREATE TRIGGER trg_questions_audit
    AFTER INSERT OR UPDATE OR DELETE ON questions
    FOR EACH ROW EXECUTE FUNCTION trigger_audit_log();

-- =============================================================================
-- TABLE: assessments
-- Assessment instances (diagnostic, practice, etc.)
-- =============================================================================
CREATE TABLE assessments (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id      UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    
    assessment_type VARCHAR(20) NOT NULL DEFAULT 'diagnostic'
                    CHECK (assessment_type IN ('diagnostic', 'practice', 'post_unit')),
    status          VARCHAR(20) NOT NULL DEFAULT 'created'
                    CHECK (status IN ('created', 'in_progress', 'paused', 'completed', 'abandoned')),
    
    -- Configuration
    target_question_count SMALLINT NOT NULL DEFAULT 40,
    min_question_count    SMALLINT NOT NULL DEFAULT 35,
    max_question_count    SMALLINT NOT NULL DEFAULT 50,
    time_limit_minutes    SMALLINT,              -- NULL = no time limit for diagnostic
    
    -- Results (populated on completion)
    total_questions INTEGER,
    total_correct   INTEGER,
    overall_score   NUMERIC(5,4),               -- 0.0 to 1.0
    results_summary JSONB,                      -- { "byDomain": {...}, "gapAnalysis": {...} }
    
    -- Timestamps
    started_at      TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ,
    abandoned_at    TIMESTAMPTZ,
    
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Student's assessments ordered by recency
CREATE INDEX idx_assessments_student ON assessments (student_id, created_at DESC);
-- Filter by status for cleanup jobs
CREATE INDEX idx_assessments_status ON assessments (status)
    WHERE status IN ('in_progress', 'paused');

CREATE TRIGGER trg_assessments_updated_at
    BEFORE UPDATE ON assessments
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

CREATE TRIGGER trg_assessments_audit
    AFTER INSERT OR UPDATE OR DELETE ON assessments
    FOR EACH ROW EXECUTE FUNCTION trigger_audit_log();

-- =============================================================================
-- TABLE: assessment_sessions
-- Browser sessions within an assessment (handles pause/resume)
-- =============================================================================
CREATE TABLE assessment_sessions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_id   UUID NOT NULL REFERENCES assessments(id) ON DELETE CASCADE,
    
    session_number  SMALLINT NOT NULL DEFAULT 1,
    status          VARCHAR(20) NOT NULL DEFAULT 'active'
                    CHECK (status IN ('active', 'paused', 'completed')),
    
    started_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ended_at        TIMESTAMPTZ,
    duration_ms     BIGINT,                     -- Total active time in this session
    
    -- Client metadata for session integrity
    client_ip       INET,
    user_agent      TEXT,
    
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Active session lookup
CREATE INDEX idx_sessions_assessment ON assessment_sessions (assessment_id, session_number);

CREATE TRIGGER trg_sessions_updated_at
    BEFORE UPDATE ON assessment_sessions
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

-- =============================================================================
-- TABLE: assessment_responses
-- Individual question responses within an assessment
-- PARTITIONED by month (assessment_responses will grow largest)
-- =============================================================================
CREATE TABLE assessment_responses (
    id              UUID NOT NULL DEFAULT gen_random_uuid(),
    assessment_id   UUID NOT NULL,  -- FK enforced per partition via trigger
    session_id      UUID NOT NULL,
    question_id     UUID NOT NULL,
    
    -- Response data
    selected_answer VARCHAR(10) NOT NULL,
    is_correct      BOOLEAN NOT NULL,
    
    -- Timing
    time_spent_ms   INTEGER NOT NULL CHECK (time_spent_ms >= 0),
    presented_at    TIMESTAMPTZ NOT NULL,
    answered_at     TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Context for CAT analysis
    question_number SMALLINT NOT NULL,           -- Position in assessment (1-indexed)
    ability_estimate_before NUMERIC(5,3),        -- θ before this response
    ability_estimate_after  NUMERIC(5,3),        -- θ after this response
    standard_code   VARCHAR(20) NOT NULL,        -- Denormalized for fast aggregation
    
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (id, created_at)
) PARTITION BY RANGE (created_at);

-- Create partitions for next 12 months (managed by pg_partman or Alembic)
CREATE TABLE assessment_responses_2026_04 PARTITION OF assessment_responses
    FOR VALUES FROM ('2026-04-01') TO ('2026-05-01');
CREATE TABLE assessment_responses_2026_05 PARTITION OF assessment_responses
    FOR VALUES FROM ('2026-05-01') TO ('2026-06-01');
CREATE TABLE assessment_responses_2026_06 PARTITION OF assessment_responses
    FOR VALUES FROM ('2026-06-01') TO ('2026-07-01');
CREATE TABLE assessment_responses_2026_07 PARTITION OF assessment_responses
    FOR VALUES FROM ('2026-07-01') TO ('2026-08-01');
CREATE TABLE assessment_responses_2026_08 PARTITION OF assessment_responses
    FOR VALUES FROM ('2026-08-01') TO ('2026-09-01');
CREATE TABLE assessment_responses_2026_09 PARTITION OF assessment_responses
    FOR VALUES FROM ('2026-09-01') TO ('2026-10-01');

-- Query pattern: all responses for a single assessment
CREATE INDEX idx_responses_assessment ON assessment_responses (assessment_id, question_number);
-- Aggregation: correct rate by standard
CREATE INDEX idx_responses_standard_correct ON assessment_responses (standard_code, is_correct);
-- Question analytics: response distribution per question
CREATE INDEX idx_responses_question ON assessment_responses (question_id, is_correct);

-- NOTE: Foreign key constraints cannot reference partitioned tables directly.
-- Referential integrity for assessment_id → assessments.id is enforced via
-- application-layer validation + a CHECK trigger:
CREATE OR REPLACE FUNCTION check_response_refs()
RETURNS TRIGGER AS $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM assessments WHERE id = NEW.assessment_id) THEN
        RAISE EXCEPTION 'assessment_id % does not exist', NEW.assessment_id;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM questions WHERE id = NEW.question_id) THEN
        RAISE EXCEPTION 'question_id % does not exist', NEW.question_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_responses_check_refs
    BEFORE INSERT ON assessment_responses
    FOR EACH ROW EXECUTE FUNCTION check_response_refs();

-- =============================================================================
-- TABLE: student_skill_states
-- BKT mastery states per student per standard (updated after each response)
-- =============================================================================
CREATE TABLE student_skill_states (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id      UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    standard_code   VARCHAR(20) NOT NULL REFERENCES standards(code),
    
    -- BKT state
    p_mastery       NUMERIC(5,4) NOT NULL DEFAULT 0.1000,  -- P(L_t): current mastery probability
    p_transit       NUMERIC(5,4) NOT NULL DEFAULT 0.1000,  -- P(T): learned per standard
    p_slip          NUMERIC(5,4) NOT NULL DEFAULT 0.0500,  -- P(S): per standard
    p_guess         NUMERIC(5,4) NOT NULL DEFAULT 0.2500,  -- P(G): per standard
    
    -- Derived classification
    mastery_level   VARCHAR(20) NOT NULL DEFAULT 'not_assessed'
                    CHECK (mastery_level IN (
                        'not_assessed', 'below_par', 'approaching', 'on_par', 'above_par', 'mastered'
                    )),
    
    -- Statistics
    total_attempts  INTEGER NOT NULL DEFAULT 0,
    total_correct   INTEGER NOT NULL DEFAULT 0,
    streak_current  INTEGER NOT NULL DEFAULT 0,
    streak_longest  INTEGER NOT NULL DEFAULT 0,
    
    -- Source assessment
    last_assessment_id UUID REFERENCES assessments(id),
    last_updated_from  VARCHAR(20) NOT NULL DEFAULT 'diagnostic'
                       CHECK (last_updated_from IN ('diagnostic', 'practice', 'post_unit')),
    
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- One state per student per standard
    CONSTRAINT uq_skill_state UNIQUE (student_id, standard_code)
);

-- Dashboard load: all skill states for a student
CREATE INDEX idx_skill_states_student ON student_skill_states (student_id);
-- Gap analysis: find students below par on specific standards
CREATE INDEX idx_skill_states_mastery ON student_skill_states (standard_code, mastery_level)
    WHERE mastery_level IN ('below_par', 'approaching');

CREATE TRIGGER trg_skill_states_updated_at
    BEFORE UPDATE ON student_skill_states
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

-- =============================================================================
-- ROW-LEVEL SECURITY POLICIES
-- Multi-tenant isolation: parents can only access their own data and their children's data
-- =============================================================================

-- Enable RLS on all user-facing tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE students ENABLE ROW LEVEL SECURITY;
ALTER TABLE consent_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE assessments ENABLE ROW LEVEL SECURITY;
ALTER TABLE assessment_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE student_skill_states ENABLE ROW LEVEL SECURITY;

-- Users: can only see own record
CREATE POLICY users_own_record ON users
    FOR ALL
    USING (id = current_setting('app.current_user_id', true)::uuid);

-- Students: parent can see their own children
CREATE POLICY students_parent_children ON students
    FOR ALL
    USING (parent_id = current_setting('app.current_user_id', true)::uuid);

-- Consent: parent can see their own consent records
CREATE POLICY consent_own_records ON consent_records
    FOR ALL
    USING (parent_id = current_setting('app.current_user_id', true)::uuid);

-- Assessments: parent can see assessments for their children
CREATE POLICY assessments_parent_children ON assessments
    FOR ALL
    USING (
        student_id IN (
            SELECT id FROM students
            WHERE parent_id = current_setting('app.current_user_id', true)::uuid
        )
    );

-- Skill states: parent can see states for their children
CREATE POLICY skill_states_parent_children ON student_skill_states
    FOR ALL
    USING (
        student_id IN (
            SELECT id FROM students
            WHERE parent_id = current_setting('app.current_user_id', true)::uuid
        )
    );

-- Admin bypass: admins can see all records
CREATE POLICY admin_full_access ON users
    FOR ALL
    USING (current_setting('app.current_user_role', true) = 'admin');
CREATE POLICY admin_full_access_students ON students
    FOR ALL
    USING (current_setting('app.current_user_role', true) = 'admin');
CREATE POLICY admin_full_access_consent ON consent_records
    FOR ALL
    USING (current_setting('app.current_user_role', true) = 'admin');
CREATE POLICY admin_full_access_assessments ON assessments
    FOR ALL
    USING (current_setting('app.current_user_role', true) = 'admin');
CREATE POLICY admin_full_access_skill_states ON student_skill_states
    FOR ALL
    USING (current_setting('app.current_user_role', true) = 'admin');
```

**Partitioning Strategy for `assessment_responses`:**

| Aspect | Decision |
|--------|----------|
| Partition Key | `created_at` (TIMESTAMPTZ) |
| Partition Interval | Monthly |
| Rationale | Responses are write-heavy, time-series data. Monthly partitions enable efficient pruning (COPPA deletion by date range), parallel vacuuming, and targeted index rebuilds. |
| Partition Management | Automated via `pg_partman` extension or Alembic migration creating next 6 months of partitions, with a cron job creating future partitions. |
| Estimated Growth | ~200 students × 40 responses × 4 assessments/year = ~32K rows/month initially. Partition pruning provides negligible benefit at this scale but establishes the pattern for 10K+ student growth. |
| Archive Strategy | Partitions older than 24 months detached and moved to cold storage (S3 via `pg_dump`). |


### 2.2 API Design (OpenAPI-level Detail)

**Base URL:** `https://api.padi-ai.com/v1`  
**Auth:** All endpoints require `Authorization: Bearer <JWT>` unless marked `[Public]`.  
**Rate Limiting:** Implemented via Redis sliding window. Limits noted per endpoint.  
**Content Type:** `application/json` for all requests and responses.

---

#### POST /auth/register

**Auth:** `[Public]` — called after Auth0 signup redirect  
**Rate Limit:** 5 req/min per IP  
**Purpose:** Create PADI.AI user record linked to Auth0 identity.

```python
# Request
class RegisterRequest(BaseModel):
    auth0_sub: str = Field(..., min_length=10, max_length=128, pattern=r'^auth0\|[a-f0-9]+$')
    email: EmailStr
    display_name: str = Field(..., min_length=2, max_length=100, pattern=r'^[a-zA-Z\s\-\']+$')

# Response (201 Created)
class RegisterResponse(BaseModel):
    user_id: UUID
    email: str
    display_name: str
    role: Literal['parent']
    needs_consent: bool  # Always True for new parents
    created_at: datetime

# Error Responses:
# 409 Conflict:    {"detail": "User with this email already exists"}
# 422 Validation:  {"detail": [{"loc": [...], "msg": "...", "type": "..."}]}
# 429 Rate Limit:  {"detail": "Rate limit exceeded. Retry after {n} seconds"}
```

**Side Effects:**
- INSERT into `users` table (email encrypted, hash stored)
- INSERT into `audit_log`
- PostHog event: `user_registered`

---

#### POST /auth/verify-email

**Auth:** `[Public]` — called from email verification link  
**Rate Limit:** 10 req/min per IP

```python
class VerifyEmailRequest(BaseModel):
    token: str = Field(..., min_length=32, max_length=256)

class VerifyEmailResponse(BaseModel):
    verified: bool
    user_id: UUID

# Errors:
# 400 Bad Request: {"detail": "Invalid or expired verification token"}
# 410 Gone:        {"detail": "Token already used"}
```

**Side Effects:**
- UPDATE `users` SET `email_verified = TRUE`
- INSERT into `audit_log`

---

#### POST /auth/login

**Auth:** `[Public]` — called after Auth0 login redirect  
**Rate Limit:** 10 req/min per IP

```python
class LoginRequest(BaseModel):
    auth0_sub: str = Field(..., min_length=10, max_length=128)

class LoginResponse(BaseModel):
    user_id: UUID
    display_name: str
    role: Literal['parent', 'admin']
    email_verified: bool
    consent_completed: bool
    has_students: bool
    access_token: str
    refresh_token: str
    expires_in: int  # seconds

# Errors:
# 401 Unauthorized: {"detail": "Auth0 token validation failed"}
# 403 Forbidden:    {"detail": "Account deactivated"}
# 404 Not Found:    {"detail": "No PADI.AI account for this Auth0 identity"}
```

**Side Effects:**
- UPDATE `users` SET `last_login_at = now(), login_count = login_count + 1`
- SET Redis session: `session:{user_id}` with TTL

---

#### POST /auth/refresh

**Auth:** Bearer refresh token  
**Rate Limit:** 5 req/min per user

```python
class RefreshRequest(BaseModel):
    refresh_token: str

class RefreshResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int

# Errors:
# 401 Unauthorized: {"detail": "Invalid or expired refresh token"}
```

**Side Effects:**
- Rotate refresh token in Redis (old token invalidated)

---

#### POST /auth/logout

**Auth:** Bearer JWT (any valid token)  
**Rate Limit:** 10 req/min per user

```python
class LogoutResponse(BaseModel):
    logged_out: bool

# Always returns 200 (idempotent)
```

**Side Effects:**
- DELETE Redis session: `session:{user_id}`
- Add access token to Redis denylist with remaining TTL

---

#### POST /consent/initiate

**Auth:** Bearer JWT (parent scope)  
**Rate Limit:** 3 req/min per user

```python
class ConsentInitiateRequest(BaseModel):
    consent_type: Literal['coppa_verifiable'] = 'coppa_verifiable'
    student_display_name: str = Field(..., min_length=1, max_length=50)
    acknowledgements: list[str] = Field(..., min_length=4, max_length=10)
    # Each string is a consent clause ID that was checked:
    # ["data_collection", "data_use", "third_party_disclosure", "parental_rights"]
    ip_address: str  # Injected server-side, not from client

class ConsentInitiateResponse(BaseModel):
    consent_id: UUID
    status: Literal['pending']
    verification_method: Literal['email_plus']
    email_sent_to: str  # Masked email: p***@gmail.com
    expires_at: datetime  # Token valid for 48 hours

# Errors:
# 400 Bad Request:  {"detail": "Active consent already exists for this parent"}
# 422 Validation:   {"detail": "All acknowledgement clauses must be accepted"}
```

**Side Effects:**
- INSERT into `consent_records` with `status='pending'`
- Generate HMAC verification token (SHA-256, 48-hour expiry)
- Call AWS SES: send verification email with confirmation link
- INSERT into `audit_log`

---

#### POST /consent/confirm

**Auth:** `[Public]` — called from email link  
**Rate Limit:** 5 req/min per IP

```python
class ConsentConfirmRequest(BaseModel):
    token: str = Field(..., min_length=64, max_length=256)

class ConsentConfirmResponse(BaseModel):
    consent_id: UUID
    status: Literal['active']
    confirmed_at: datetime
    expires_at: datetime  # 1 year from confirmation

# Errors:
# 400 Bad Request: {"detail": "Invalid or expired consent token"}
# 410 Gone:        {"detail": "Consent already confirmed or revoked"}
```

**Side Effects:**
- UPDATE `consent_records` SET `status='active', confirmed_at=now(), expires_at=now()+1year`
- INSERT into `audit_log` (consent confirmation event)
- Call AWS SES: send confirmation receipt email

---

#### GET /consent/status

**Auth:** Bearer JWT (parent scope)  
**Rate Limit:** 30 req/min per user

```python
class ConsentStatusResponse(BaseModel):
    has_active_consent: bool
    consent_records: list[ConsentRecordSummary]

class ConsentRecordSummary(BaseModel):
    consent_id: UUID
    consent_type: str
    status: Literal['pending', 'active', 'revoked', 'expired']
    consent_version: str
    initiated_at: datetime
    confirmed_at: datetime | None
    expires_at: datetime | None
```

---

#### POST /students

**Auth:** Bearer JWT (parent scope)  
**Rate Limit:** 5 req/min per user  
**Prerequisite:** Active COPPA consent

```python
class CreateStudentRequest(BaseModel):
    display_name: str = Field(..., min_length=1, max_length=50, pattern=r'^[a-zA-Z0-9\s\-]+$')
    grade_level: int = Field(default=4, ge=3, le=5)
    avatar_id: str = Field(default='avatar_default', pattern=r'^avatar_[a-z_]+$')
    birth_year: int | None = Field(default=None, ge=2012, le=2020)

class CreateStudentResponse(BaseModel):
    student_id: UUID
    display_name: str
    grade_level: int
    avatar_id: str
    created_at: datetime

# Errors:
# 403 Forbidden:   {"detail": "Active COPPA consent required before creating student profile"}
# 409 Conflict:    {"detail": "Student with this display name already exists for your account"}
# 422 Validation:  Standard Pydantic validation errors
```

**Side Effects:**
- Verify active consent exists for parent
- INSERT into `students`
- INSERT into `audit_log`

---

#### GET /students/{id}

**Auth:** Bearer JWT (parent scope — must own student)  
**Rate Limit:** 30 req/min per user

```python
class StudentDetailResponse(BaseModel):
    student_id: UUID
    display_name: str
    grade_level: int
    avatar_id: str
    birth_year: int | None
    is_active: bool
    created_at: datetime
    latest_assessment: AssessmentSummary | None
    skill_summary: SkillSummary | None

class AssessmentSummary(BaseModel):
    assessment_id: UUID
    assessment_type: str
    status: str
    overall_score: float | None
    completed_at: datetime | None

class SkillSummary(BaseModel):
    total_standards: int
    mastered: int
    on_par: int
    below_par: int
    not_assessed: int

# Errors:
# 404 Not Found:   {"detail": "Student not found"}
# 403 Forbidden:   {"detail": "Access denied"}
```

---

#### PUT /students/{id}

**Auth:** Bearer JWT (parent scope — must own student)  
**Rate Limit:** 10 req/min per user

```python
class UpdateStudentRequest(BaseModel):
    display_name: str | None = Field(None, min_length=1, max_length=50)
    avatar_id: str | None = None
    grade_level: int | None = Field(None, ge=3, le=5)

class UpdateStudentResponse(BaseModel):
    student_id: UUID
    display_name: str
    grade_level: int
    avatar_id: str
    updated_at: datetime

# Errors:
# 404 Not Found, 403 Forbidden, 422 Validation
```

---

#### GET /standards

**Auth:** Bearer JWT (any authenticated user)  
**Rate Limit:** 60 req/min per user

```python
class StandardsQueryParams(BaseModel):
    grade: int = Field(default=4, ge=3, le=5)
    domain: str | None = Field(None, pattern=r'^4\.(OA|NBT|NF|GM|DR)$')
    cluster: str | None = None
    include_prerequisites: bool = False

class StandardListResponse(BaseModel):
    standards: list[StandardItem]
    total: int

class StandardItem(BaseModel):
    code: str
    domain: str
    cluster: str
    title: str
    description: str
    cognitive_level: str
    estimated_difficulty: float
    prerequisites: list[str] | None = None  # Only if include_prerequisites=True
```

---

#### GET /standards/{code}

**Auth:** Bearer JWT (any authenticated user)  
**Rate Limit:** 60 req/min per user

```python
class StandardDetailResponse(BaseModel):
    code: str
    domain: str
    cluster: str
    title: str
    description: str
    cognitive_level: str
    estimated_difficulty: float
    bkt_defaults: BKTDefaults
    prerequisites: list[PrerequisiteRelation]
    dependent_standards: list[str]
    question_count: int

class BKTDefaults(BaseModel):
    p_l0: float
    p_transit: float
    p_slip: float
    p_guess: float

class PrerequisiteRelation(BaseModel):
    prerequisite_code: str
    relationship_type: str
    strength: float

# Errors:
# 404 Not Found: {"detail": "Standard '4.XX.Y.Z' not found"}
```

---

#### POST /assessments

**Auth:** Bearer JWT (parent scope)  
**Rate Limit:** 3 req/min per user  
**Purpose:** Start a new diagnostic assessment for a student.

```python
class CreateAssessmentRequest(BaseModel):
    student_id: UUID
    assessment_type: Literal['diagnostic'] = 'diagnostic'

class CreateAssessmentResponse(BaseModel):
    assessment_id: UUID
    session_id: UUID
    student_id: UUID
    assessment_type: str
    target_question_count: int
    status: Literal['in_progress']
    started_at: datetime

# Errors:
# 400 Bad Request: {"detail": "Student already has an active diagnostic assessment"}
# 403 Forbidden:   {"detail": "Access denied — student does not belong to your account"}
# 403 Forbidden:   {"detail": "Active COPPA consent required"}
# 409 Conflict:    {"detail": "Diagnostic already completed for this student. Use POST /assessments with type='practice'"}
```

**Side Effects:**
- INSERT into `assessments` with `status='in_progress'`
- INSERT into `assessment_sessions`
- SET Redis: `assessment:{id}:state` = `{ theta: 0.0, covered_standards: [], question_ids_used: [] }`
- Load full question pool into Redis cache: `assessment:{id}:pool`

---

#### GET /assessments/{id}/next-question

**Auth:** Bearer JWT (parent scope — must own student)  
**Rate Limit:** 60 req/min per user (high for rapid question advancement)

```python
class NextQuestionResponse(BaseModel):
    question: QuestionPresentation | None  # None if assessment should end
    progress: AssessmentProgress
    should_end: bool
    end_reason: str | None  # 'all_standards_covered', 'max_questions_reached', 'time_expired'

class QuestionPresentation(BaseModel):
    question_id: UUID
    question_number: int
    standard_domain: str      # "Operations & Algebraic Thinking" (human-readable)
    stem: str
    stem_image_url: str | None
    options: list[OptionPresentation]
    question_type: str

class OptionPresentation(BaseModel):
    key: str              # 'A', 'B', 'C', 'D'
    text: str
    image_url: str | None

class AssessmentProgress(BaseModel):
    questions_answered: int
    target_total: int
    domains_covered: dict[str, int]  # { "4.OA": 5, "4.NBT": 3, ... }
    estimated_time_remaining_min: int

# Errors:
# 404 Not Found:   {"detail": "Assessment not found"}
# 409 Conflict:    {"detail": "Assessment already completed"}
# 403 Forbidden:   {"detail": "Access denied"}
```

**Side Effects:**
- Read CAT state from Redis
- Execute question selection algorithm
- Cache selected question ID in Redis to prevent re-selection

---

#### POST /assessments/{id}/responses

**Auth:** Bearer JWT (parent scope — must own student)  
**Rate Limit:** 30 req/min per user

```python
class SubmitResponseRequest(BaseModel):
    question_id: UUID
    selected_answer: str = Field(..., pattern=r'^[A-D]$|^\d+(\.\d+)?$')
    time_spent_ms: int = Field(..., ge=0, le=600000)  # Max 10 min per question
    client_timestamp: datetime  # For drift detection

class SubmitResponseResponse(BaseModel):
    is_correct: bool
    correct_answer: str
    explanation: str | None
    progress: AssessmentProgress
    # No detailed BKT state exposed to client (prevent gaming)

# Errors:
# 400 Bad Request: {"detail": "Question ID does not match current question"}
# 409 Conflict:    {"detail": "Response already submitted for this question"}
# 422 Validation:  Standard errors
```

**Side Effects:**
- Evaluate correctness (compare against `questions.correct_answer`)
- INSERT into `assessment_responses` (partitioned table)
- BKT state update in Redis: `assessment:{id}:bkt:{standard_code}`
- Update ability estimate θ in Redis
- Update `questions.times_shown` and `times_correct` (async, non-blocking)

---

#### PUT /assessments/{id}/complete

**Auth:** Bearer JWT (parent scope — must own student)  
**Rate Limit:** 5 req/min per user

```python
class CompleteAssessmentResponse(BaseModel):
    assessment_id: UUID
    status: Literal['completed']
    total_questions: int
    total_correct: int
    overall_score: float
    duration_minutes: float
    completed_at: datetime
    results_url: str  # /diagnostic/results?assessment={id}

# Errors:
# 400 Bad Request: {"detail": "Minimum 35 questions required; only 28 answered"}
# 409 Conflict:    {"detail": "Assessment already completed"}
```

**Side Effects:**
- Finalize BKT states from Redis → write to `student_skill_states` table
- UPDATE `assessments` SET `status='completed', completed_at=now(), overall_score=..., results_summary=...`
- UPDATE `assessment_sessions` SET `status='completed', ended_at=now()`
- DELETE Redis keys: `assessment:{id}:*`
- Send "results ready" email via AWS SES
- PostHog event: `assessment_completed`

---

#### GET /assessments/{id}/results

**Auth:** Bearer JWT (parent scope — must own student)  
**Rate Limit:** 30 req/min per user

```python
class AssessmentResultsResponse(BaseModel):
    assessment_id: UUID
    student_name: str
    assessment_type: str
    completed_at: datetime
    duration_minutes: float

    # Overall
    overall_score: float           # 0.0 to 1.0
    total_questions: int
    total_correct: int
    overall_classification: Literal['below_par', 'on_par', 'above_par']

    # Per-domain breakdown
    domain_results: list[DomainResult]

    # Per-standard detail
    skill_states: list[SkillStateResult]

    # Gap analysis
    gap_analysis: GapAnalysis

class DomainResult(BaseModel):
    domain_code: str               # '4.OA'
    domain_name: str               # 'Operations & Algebraic Thinking'
    questions_count: int
    correct_count: int
    score: float
    classification: str

class SkillStateResult(BaseModel):
    standard_code: str
    standard_title: str
    p_mastery: float
    mastery_level: str
    questions_attempted: int
    questions_correct: int

class GapAnalysis(BaseModel):
    strengths: list[str]           # Standard codes where P(L) >= 0.80
    on_track: list[str]            # 0.60 <= P(L) < 0.80
    needs_work: list[str]          # P(L) < 0.60
    recommended_focus_order: list[str]  # Ordered by priority (prerequisite-aware)

# Errors:
# 404 Not Found:   {"detail": "Assessment not found or not completed"}
# 403 Forbidden:   {"detail": "Access denied"}
```


### 2.3 Service Layer Design

**Dependency Injection Pattern:** All services receive dependencies via constructor injection. FastAPI's `Depends()` system wires them at startup. Each service is stateless; all mutable state lives in PostgreSQL or Redis.

```python
# ─────────────────────────────────────────────────────────────────────
# services/assessment_service.py
# ─────────────────────────────────────────────────────────────────────
from uuid import UUID
from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assessment import Assessment, AssessmentSession, AssessmentResponse
from app.models.question import Question
from app.models.student import StudentSkillState
from app.schemas.assessment import (
    AssessmentResults, ResponseResult, AssessmentProgress,
    NextQuestionPayload, DomainResult, GapAnalysis, SkillStateResult,
)
from app.services.bkt_service import BKTService, BKTState
from app.services.question_selection_service import QuestionSelectionService
from app.repositories.assessment_repository import AssessmentRepository
from app.repositories.question_repository import QuestionRepository
from app.repositories.student_repository import StudentRepository
from app.repositories.standards_repository import StandardsRepository
from app.core.redis_client import RedisClient


class AssessmentService:
    """Orchestrates diagnostic assessment lifecycle: creation, question serving, 
    response processing, and results computation."""

    def __init__(
        self,
        db: AsyncSession,
        redis: RedisClient,
        assessment_repo: AssessmentRepository,
        question_repo: QuestionRepository,
        student_repo: StudentRepository,
        standards_repo: StandardsRepository,
        bkt_service: BKTService,
        question_selection: QuestionSelectionService,
    ):
        self._db = db
        self._redis = redis
        self._assessment_repo = assessment_repo
        self._question_repo = question_repo
        self._student_repo = student_repo
        self._standards_repo = standards_repo
        self._bkt = bkt_service
        self._selection = question_selection

    async def start_diagnostic(
        self,
        student_id: UUID,
        parent_id: UUID,
    ) -> tuple[Assessment, AssessmentSession]:
        """Create a new diagnostic assessment and initialize CAT state.
        
        Raises:
            PermissionError: Parent does not own student
            ConsentError: No active COPPA consent
            ConflictError: Active assessment already exists
        """
        ...

    async def get_next_question(
        self,
        assessment_id: UUID,
    ) -> NextQuestionPayload:
        """Run CAT algorithm to select the optimal next question.
        
        Returns NextQuestionPayload with question=None and should_end=True
        when assessment completion criteria are met:
        - All standards have ≥2 questions answered
        - Total questions ≥ min_question_count (35)
        - OR total questions ≥ max_question_count (50)
        """
        ...

    async def submit_response(
        self,
        assessment_id: UUID,
        question_id: UUID,
        selected_answer: str,
        time_spent_ms: int,
    ) -> ResponseResult:
        """Process a student's answer: evaluate, update BKT, update θ.
        
        Returns correctness, explanation, and updated progress.
        """
        ...

    async def complete_assessment(
        self,
        assessment_id: UUID,
    ) -> AssessmentResults:
        """Finalize assessment: compute BKT states, classify mastery, 
        persist to student_skill_states, generate gap analysis.
        
        Raises:
            ValidationError: Fewer than min_question_count responses
        """
        ...

    async def _calculate_skill_states(
        self,
        assessment_id: UUID,
        responses: list[AssessmentResponse],
    ) -> dict[str, SkillStateResult]:
        """Aggregate responses by standard → run BKT → classify mastery levels.
        
        Classification thresholds:
            P(L) >= 0.90 → 'mastered'
            P(L) >= 0.80 → 'above_par'
            P(L) >= 0.60 → 'on_par'
            P(L) >= 0.40 → 'approaching'
            P(L) <  0.40 → 'below_par'
        """
        ...

    async def _generate_gap_analysis(
        self,
        skill_states: dict[str, SkillStateResult],
    ) -> GapAnalysis:
        """Partition skills into strengths/on_track/needs_work.
        Order needs_work by prerequisite dependencies (topological sort).
        """
        ...


# ─────────────────────────────────────────────────────────────────────
# services/bkt_service.py
# ─────────────────────────────────────────────────────────────────────
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class BKTState:
    """Immutable BKT state for a single skill."""
    p_mastery: float      # P(L_t): probability student has learned the skill
    p_transit: float      # P(T): probability of learning on each opportunity
    p_slip: float         # P(S): probability of incorrect despite knowing
    p_guess: float        # P(G): probability of correct despite not knowing
    observations: int     # Number of observations incorporated
    correct_count: int    # Number of correct observations


class BKTService:
    """Bayesian Knowledge Tracing computation engine.
    
    Stateless service — all state passed as parameters.
    Uses the standard BKT Hidden Markov Model:
    
    P(L_t | obs=correct) = P(L_t) * (1 - P(S)) / P(correct)
    P(L_t | obs=incorrect) = P(L_t) * P(S) / P(incorrect)
    P(L_{t+1}) = P(L_t | obs) + (1 - P(L_t | obs)) * P(T)
    """

    def initialize_from_diagnostic(
        self,
        responses_by_standard: dict[str, list[tuple[bool, float]]],
        standard_defaults: dict[str, dict[str, float]],
    ) -> dict[str, BKTState]:
        """Initialize BKT states from a batch of diagnostic responses.
        
        Args:
            responses_by_standard: { standard_code: [(is_correct, irt_difficulty), ...] }
            standard_defaults: { standard_code: { p_l0, p_transit, p_slip, p_guess } }
        
        Returns:
            { standard_code: BKTState }
        
        Algorithm:
            For each standard:
            1. Start with P(L0) from standard defaults
            2. Process each response chronologically via forward algorithm
            3. Return final P(L_t) as mastery estimate
        """
        ...

    def update_state(self, current_state: BKTState, is_correct: bool) -> BKTState:
        """Update BKT state with a single new observation.
        
        Implements the standard BKT update equations:
        1. Compute P(correct) = P(L) * (1 - P(S)) + (1 - P(L)) * P(G)
        2. Compute posterior P(L|obs) using Bayes' rule
        3. Apply learning transition: P(L_{t+1}) = P(L|obs) + (1 - P(L|obs)) * P(T)
        
        Returns new immutable BKTState.
        """
        ...

    def get_mastery_probability(self, state: BKTState) -> float:
        """Return current mastery probability P(L_t)."""
        return state.p_mastery

    def classify_mastery(self, state: BKTState) -> str:
        """Classify mastery level from P(L_t).
        
        Returns: 'mastered' | 'above_par' | 'on_par' | 'approaching' | 'below_par'
        """
        p = state.p_mastery
        if p >= 0.90:
            return 'mastered'
        elif p >= 0.80:
            return 'above_par'
        elif p >= 0.60:
            return 'on_par'
        elif p >= 0.40:
            return 'approaching'
        else:
            return 'below_par'

    def estimate_p_l0_from_accuracy(
        self,
        correct: int,
        total: int,
        default_p_guess: float = 0.25,
    ) -> float:
        """Estimate initial mastery P(L0) from raw accuracy.
        
        Used when initializing BKT from a cold start (no prior data).
        Adjusts for guessing on multiple-choice (4 options → P(G) = 0.25):
        
        P(L0) = max(0.01, (accuracy - P(G)) / (1 - P(G)))
        Clamped to [0.01, 0.99]
        """
        if total == 0:
            return 0.10  # Default prior
        accuracy = correct / total
        p_l0 = max(0.01, (accuracy - default_p_guess) / (1 - default_p_guess))
        return min(0.99, max(0.01, p_l0))


# ─────────────────────────────────────────────────────────────────────
# services/question_selection_service.py
# ─────────────────────────────────────────────────────────────────────
from dataclasses import dataclass
import math
from typing import Optional


@dataclass
class CATState:
    """Mutable CAT state for an in-progress assessment."""
    theta: float                           # Current ability estimate
    theta_se: float                        # Standard error of theta
    covered_standards: dict[str, int]      # { standard_code: questions_asked }
    used_question_ids: set[str]            # Prevent re-selection
    responses: list[tuple[str, bool, float]]  # (question_id, is_correct, irt_b)


class QuestionSelectionService:
    """Computerized Adaptive Testing item selection engine.
    
    Implements a content-balanced maximum Fisher information algorithm:
    1. Content balancing: select the standard with lowest coverage
    2. Within standard: select item maximizing Fisher information at current θ
    3. Exposure control: Sympson-Hetter method to prevent overexposure
    """

    MIN_QUESTIONS_PER_STANDARD: int = 2
    TARGET_QUESTIONS_PER_STANDARD: int = 4
    THETA_INITIAL: float = 0.0
    THETA_SE_INITIAL: float = 1.5

    def select_next_question(
        self,
        cat_state: CATState,
        question_pool: list['Question'],
        all_standards: list[str],
    ) -> Optional['Question']:
        """Select the optimal next question using CAT algorithm.
        
        Args:
            cat_state: Current adaptive testing state
            question_pool: Available (unused) questions
            all_standards: All standard codes to cover
        
        Returns:
            Selected Question, or None if all standards sufficiently covered
        
        Algorithm: See Section 3, Algorithm 1.
        """
        ...

    def estimate_ability(
        self,
        responses: list[tuple[bool, float, float]],
    ) -> tuple[float, float]:
        """Estimate ability (θ) using Maximum Likelihood Estimation (MLE).
        
        Args:
            responses: [(is_correct, irt_difficulty_b, irt_discrimination_a), ...]
        
        Returns:
            (theta_estimate, standard_error)
        
        Uses Newton-Raphson iteration on the 3PL likelihood.
        Bounded to [-4.0, 4.0] to prevent divergence.
        """
        ...

    def fisher_information(
        self,
        theta: float,
        a: float,
        b: float,
        c: float,
    ) -> float:
        """Compute Fisher information for a 3PL IRT item at given θ.
        
        I(θ) = a² * (P - c)² / ((1 - c)² * P * (1 - P))
        where P = c + (1-c) / (1 + exp(-a(θ-b)))
        """
        ...

    def check_completion_criteria(
        self,
        cat_state: CATState,
        all_standards: list[str],
        min_questions: int = 35,
        max_questions: int = 50,
    ) -> tuple[bool, Optional[str]]:
        """Check if assessment should terminate.
        
        Returns (should_end, reason):
        - ('all_standards_covered', True) when all standards have ≥ MIN_QUESTIONS_PER_STANDARD
          and total ≥ min_questions
        - ('max_questions_reached', True) when total ≥ max_questions
        - ('theta_converged', True) when SE(θ) < 0.3 and total ≥ min_questions
        - (None, False) otherwise
        """
        ...
```

### 2.4 Frontend Architecture

(Covered in Section 1.4 above — includes complete page tree, component details, and Zustand store definitions.)

---

## 3. Key Algorithms (Pseudocode + Implementation Notes)

### Algorithm 1: CAT Question Selection (Computerized Adaptive Testing)

```
FUNCTION select_next_question(cat_state, question_pool, all_standards):
    """Content-balanced maximum Fisher information item selection."""
    
    # ─── Step 1: Content Balancing ───────────────────────────────
    # Find the standard with the lowest question coverage
    coverage = {}
    FOR EACH standard IN all_standards:
        coverage[standard] = cat_state.covered_standards.get(standard, 0)
    
    # Sort standards by coverage (ascending), break ties by domain order
    sorted_standards = SORT(all_standards, key=lambda s: (coverage[s], s))
    
    # Filter to standards below target coverage
    underserved = [s for s in sorted_standards 
                   if coverage[s] < TARGET_QUESTIONS_PER_STANDARD]
    
    IF underserved is empty:
        # All standards at target → select from any standard below max
        underserved = [s for s in sorted_standards 
                       if coverage[s] < MAX_QUESTIONS_PER_STANDARD]
    
    IF underserved is empty:
        RETURN None  # Assessment should end
    
    # ─── Step 2: Candidate Question Filtering ────────────────────
    # Get unused questions for the most underserved standard
    target_standard = underserved[0]
    
    candidates = FILTER(question_pool, WHERE:
        question.standard_code == target_standard
        AND question.id NOT IN cat_state.used_question_ids
        AND question.status == 'active'
    )
    
    IF candidates is empty:
        # Fallback: try next underserved standard
        FOR EACH standard IN underserved[1:]:
            candidates = FILTER(question_pool, ..same criteria for standard..)
            IF candidates is not empty:
                target_standard = standard
                BREAK
    
    IF candidates is empty:
        RETURN None  # No available questions
    
    # ─── Step 3: Fisher Information Maximization ─────────────────
    θ = cat_state.theta
    best_question = None
    best_info = -infinity
    
    FOR EACH question IN candidates:
        a = question.irt_discrimination  # default 1.0
        b = question.irt_difficulty
        c = question.irt_guessing        # default 0.25
        
        # 3PL probability of correct response
        P = c + (1 - c) / (1 + exp(-a * (θ - b)))
        
        # Fisher information at current θ
        I = (a ** 2) * ((P - c) ** 2) / (((1 - c) ** 2) * P * (1 - P))
        
        # ─── Step 3a: Difficulty Window Filter ───────────────
        # Prefer items within ±1.5 logits of θ for efficiency
        IF abs(b - θ) > 1.5:
            I = I * 0.5  # Penalty for far-from-ability items
        
        # ─── Step 3b: Exposure Control (Sympson-Hetter) ──────
        # Reduce information for overexposed items
        exposure_rate = question.times_shown / max(1, total_pool_presentations)
        IF exposure_rate > 0.25:  # Exposure cap at 25%
            I = I * (0.25 / exposure_rate)
        
        IF I > best_info:
            best_info = I
            best_question = question
    
    # ─── Step 4: Fallback ────────────────────────────────────────
    IF best_question is None:
        # Select random unused question from target standard
        best_question = RANDOM_CHOICE(candidates)
    
    RETURN best_question

COMPLEXITY: O(S * Q) where S = standards count, Q = questions per standard
EXPECTED: O(28 * 15) = O(420) — sub-millisecond
```

### Algorithm 2: BKT Initialization from Diagnostic Responses

```
FUNCTION initialize_bkt_from_diagnostic(responses, standard_defaults):
    """Process diagnostic responses to initialize BKT states per standard.
    
    Args:
        responses: list of (standard_code, is_correct, irt_difficulty) tuples
                   in chronological order
        standard_defaults: { standard_code: { p_l0, p_transit, p_slip, p_guess } }
    
    Returns:
        { standard_code: BKTState }
    """
    
    # ─── Step 1: Group responses by standard ──────────────────────
    by_standard = GROUP_BY(responses, key=lambda r: r.standard_code)
    
    result = {}
    
    FOR EACH standard_code, standard_responses IN by_standard:
        # ─── Step 2: Load default parameters ─────────────────────
        defaults = standard_defaults.get(standard_code, DEFAULT_BKT_PARAMS)
        P_L = defaults.p_l0        # Prior: P(L₀) — typically 0.10
        P_T = defaults.p_transit   # Learn rate: P(T) — typically 0.10
        P_S = defaults.p_slip      # Slip: P(S) — typically 0.05
        P_G = defaults.p_guess     # Guess: P(G) — typically 0.25
        
        correct_count = 0
        total_count = 0
        
        # ─── Step 3: Forward algorithm — sequential BKT updates ──
        FOR EACH (_, is_correct, _) IN standard_responses:
            total_count += 1
            IF is_correct:
                correct_count += 1
            
            # Step 3a: Compute P(correct | state)
            p_correct = P_L * (1 - P_S) + (1 - P_L) * P_G
            p_incorrect = 1 - p_correct
            
            # Step 3b: Posterior update P(L | observation) via Bayes
            IF is_correct:
                P_L_given_obs = (P_L * (1 - P_S)) / p_correct
            ELSE:
                P_L_given_obs = (P_L * P_S) / p_incorrect
            
            # Step 3c: Learning transition
            # P(L_{t+1}) = P(L|obs) + (1 - P(L|obs)) * P(T)
            P_L = P_L_given_obs + (1 - P_L_given_obs) * P_T
            
            # Step 3d: Clamp to prevent numerical extremes
            P_L = CLAMP(P_L, 0.001, 0.999)
        
        # ─── Step 4: Store final state ───────────────────────────
        result[standard_code] = BKTState(
            p_mastery=P_L,
            p_transit=P_T,
            p_slip=P_S,
            p_guess=P_G,
            observations=total_count,
            correct_count=correct_count,
        )
    
    RETURN result

DEFAULT_BKT_PARAMS = {
    'p_l0': 0.10,
    'p_transit': 0.10,
    'p_slip': 0.05,
    'p_guess': 0.25,
}

NOTES:
- For standards with 0 responses (not covered in diagnostic), 
  BKT state is initialized with P(L) = p_l0 and mastery_level = 'not_assessed'
- The forget parameter P(F) is set to 0.0 for diagnostic (single session)
- For future practice sessions, P(F) can be set to 0.01-0.05 to model decay
```

### Algorithm 3: Gap Analysis Score Calculation

```
FUNCTION compute_gap_analysis(skill_states, prerequisite_graph):
    """Compute gap analysis from BKT skill states.
    
    Args:
        skill_states: { standard_code: BKTState }
        prerequisite_graph: { standard_code: [prerequisite_codes] }
    
    Returns:
        GapAnalysis with classified skills and prioritized remediation order
    """
    
    # ─── Step 1: Classify each skill ─────────────────────────────
    strengths = []      # P(L) >= 0.80
    on_track = []       # 0.60 <= P(L) < 0.80
    needs_work = []     # P(L) < 0.60
    
    FOR EACH code, state IN skill_states:
        p = state.p_mastery
        IF p >= 0.80:
            strengths.append(code)
        ELIF p >= 0.60:
            on_track.append(code)
        ELSE:
            needs_work.append(code)
    
    # ─── Step 2: Domain-level aggregation ─────────────────────────
    domain_scores = {}
    FOR EACH code, state IN skill_states:
        domain = extract_domain(code)  # e.g., '4.OA' from '4.OA.A.1'
        IF domain NOT IN domain_scores:
            domain_scores[domain] = { 'total_p': 0, 'count': 0 }
        domain_scores[domain]['total_p'] += state.p_mastery
        domain_scores[domain]['count'] += 1
    
    domain_classifications = {}
    FOR EACH domain, scores IN domain_scores:
        avg_p = scores['total_p'] / scores['count']
        IF avg_p >= 0.80:
            domain_classifications[domain] = 'above_par'
        ELIF avg_p >= 0.60:
            domain_classifications[domain] = 'on_par'
        ELSE:
            domain_classifications[domain] = 'below_par'
    
    # ─── Step 3: Prioritized remediation order ────────────────────
    # Use topological sort respecting prerequisites
    # Priority: skills that are prerequisites for many other weak skills first
    
    remediation_graph = SUBGRAPH(prerequisite_graph, nodes=needs_work)
    
    # Compute "downstream impact" for each weak skill
    impact_scores = {}
    FOR EACH skill IN needs_work:
        # Count how many other weak skills depend on this one
        dependents = TRANSITIVE_DEPENDENTS(prerequisite_graph, skill)
        weak_dependents = INTERSECT(dependents, needs_work)
        impact_scores[skill] = len(weak_dependents)
    
    # Sort: highest impact first, then lowest P(L) (most in need)
    recommended_order = SORT(needs_work, key=lambda s: (
        -impact_scores[s],                    # Most impactful first
        skill_states[s].p_mastery,            # Then weakest first
    ))
    
    RETURN GapAnalysis(
        strengths=strengths,
        on_track=on_track,
        needs_work=needs_work,
        domain_classifications=domain_classifications,
        recommended_focus_order=recommended_order,
    )
```


---

## 4. Infrastructure & Deployment

### 4.1 Terraform Module Structure (Stage 1)

```
infrastructure/terraform/
├── environments/
│   ├── dev/
│   │   ├── main.tf              # Module instantiation with dev params
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   └── terraform.tfvars     # Dev-specific: single-AZ, small instances
│   ├── staging/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   └── terraform.tfvars     # Staging: mirrors prod topology, smaller instances
│   └── prod/
│       ├── main.tf
│       ├── variables.tf
│       ├── outputs.tf
│       └── terraform.tfvars     # Prod: Multi-AZ, autoscaling, backups
├── modules/
│   ├── networking/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── database/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── cache/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── ecs/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── cdn/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   └── secrets/
│       ├── main.tf
│       ├── variables.tf
│       └── outputs.tf
├── backend.tf                   # S3 + DynamoDB remote state
└── versions.tf                  # Terraform + provider version pins
```

**Module Details:**

#### networking module
```hcl
# Key Resources:
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true
}

resource "aws_subnet" "public" {
  count             = 2  # Multi-AZ
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.${count.index + 1}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true
}

resource "aws_subnet" "private" {
  count             = 2  # Multi-AZ
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.${count.index + 10}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]
}

resource "aws_internet_gateway" "igw" { vpc_id = aws_vpc.main.id }

resource "aws_nat_gateway" "nat" {
  count         = var.environment == "prod" ? 2 : 1  # HA for prod
  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index].id
}

# Security Groups
resource "aws_security_group" "alb" {
  # Ingress: 443 from 0.0.0.0/0
  # Egress:  8000 to ecs-tasks SG
}

resource "aws_security_group" "ecs_tasks" {
  # Ingress: 8000 from ALB SG
  # Egress:  5432 to RDS SG, 6379 to Redis SG, 443 to 0.0.0.0/0 (external APIs)
}

resource "aws_security_group" "rds" {
  # Ingress: 5432 from ecs-tasks SG only
  # Egress:  none
}

resource "aws_security_group" "redis" {
  # Ingress: 6379 from ecs-tasks SG only
  # Egress:  none
}
```

#### database module
```hcl
resource "aws_db_instance" "postgres" {
  identifier        = "padi-ai-${var.environment}"
  engine            = "postgres"
  engine_version    = "17.2"
  instance_class    = var.environment == "prod" ? "db.r6g.large" : "db.t4g.medium"
  allocated_storage = 50
  max_allocated_storage = 200  # Autoscaling
  storage_encrypted = true
  kms_key_id        = var.kms_key_arn
  
  multi_az          = var.environment == "prod"
  
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [var.rds_security_group_id]
  
  backup_retention_period = var.environment == "prod" ? 30 : 7
  backup_window           = "03:00-04:00"
  maintenance_window      = "sun:04:00-sun:05:00"
  
  performance_insights_enabled = true
  monitoring_interval          = 60
  
  deletion_protection = var.environment == "prod"
  skip_final_snapshot = var.environment != "prod"
}

resource "aws_db_parameter_group" "postgres17" {
  family = "postgres17"
  
  parameter {
    name  = "shared_preload_libraries"
    value = "pg_stat_statements,pgvector"
  }
  parameter {
    name  = "log_min_duration_statement"
    value = "1000"  # Log slow queries > 1s
  }
  parameter {
    name  = "rds.force_ssl"
    value = "1"
  }
}

resource "aws_db_subnet_group" "main" {
  subnet_ids = var.private_subnet_ids
}
```

#### cache module
```hcl
resource "aws_elasticache_replication_group" "redis" {
  replication_group_id = "padi-ai-${var.environment}"
  description          = "PADI.AI Redis cache"
  engine               = "redis"
  engine_version       = "7.1"
  node_type            = var.environment == "prod" ? "cache.r6g.large" : "cache.t4g.medium"
  
  num_cache_clusters   = var.environment == "prod" ? 2 : 1
  
  subnet_group_name    = aws_elasticache_subnet_group.main.name
  security_group_ids   = [var.redis_security_group_id]
  
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  
  snapshot_retention_limit = var.environment == "prod" ? 7 : 1
  
  parameter_group_name = aws_elasticache_parameter_group.redis7.name
}

resource "aws_elasticache_parameter_group" "redis7" {
  family = "redis7"
  
  parameter {
    name  = "maxmemory-policy"
    value = "allkeys-lru"
  }
}
```

#### ecs module
```hcl
resource "aws_ecs_cluster" "main" {
  name = "padi-ai-${var.environment}"
  
  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

resource "aws_ecs_task_definition" "api" {
  family                   = "padi-ai-api-${var.environment}"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.environment == "prod" ? 1024 : 512
  memory                   = var.environment == "prod" ? 2048 : 1024
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn
  
  container_definitions = jsonencode([{
    name  = "padi-ai-api"
    image = "${var.ecr_repository_url}:${var.image_tag}"
    portMappings = [{ containerPort = 8000, protocol = "tcp" }]
    environment = [
      { name = "ENVIRONMENT", value = var.environment }
    ]
    secrets = [
      { name = "DATABASE_URL", valueFrom = "${var.secrets_arn}:DATABASE_URL::" },
      { name = "REDIS_URL",    valueFrom = "${var.secrets_arn}:REDIS_URL::" },
      # ... all secrets from Secrets Manager
    ]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = "/ecs/padi-ai-api-${var.environment}"
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "api"
      }
    }
    healthCheck = {
      command     = ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"]
      interval    = 30
      timeout     = 5
      retries     = 3
      startPeriod = 60
    }
  }])
}

resource "aws_ecs_service" "api" {
  name            = "padi-ai-api"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.api.arn
  desired_count   = var.environment == "prod" ? 2 : 1
  launch_type     = "FARGATE"
  
  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [var.ecs_security_group_id]
    assign_public_ip = false
  }
  
  load_balancer {
    target_group_arn = aws_lb_target_group.api.arn
    container_name   = "padi-ai-api"
    container_port   = 8000
  }
  
  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }
}

resource "aws_lb" "api" {
  name               = "padi-ai-alb-${var.environment}"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [var.alb_security_group_id]
  subnets            = var.public_subnet_ids
}

resource "aws_lb_target_group" "api" {
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"
  
  health_check {
    path                = "/health"
    healthy_threshold   = 2
    unhealthy_threshold = 3
    interval            = 30
    timeout             = 5
  }
}

resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.api.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-2021-06"
  certificate_arn   = var.acm_certificate_arn
  
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.api.arn
  }
}

resource "aws_appautoscaling_target" "ecs" {
  max_capacity       = var.environment == "prod" ? 10 : 2
  min_capacity       = var.environment == "prod" ? 2 : 1
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.api.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "cpu" {
  name               = "cpu-autoscaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ecs.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs.scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs.service_namespace
  
  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value       = 60.0
    scale_in_cooldown  = 300
    scale_out_cooldown = 60
  }
}
```

#### secrets module
```hcl
resource "aws_secretsmanager_secret" "app" {
  name       = "padi-ai/${var.environment}/app"
  kms_key_id = aws_kms_key.app.arn
}

resource "aws_kms_key" "app" {
  description             = "PADI.AI ${var.environment} encryption key"
  deletion_window_in_days = 30
  enable_key_rotation     = true
}

resource "aws_kms_alias" "app" {
  name          = "alias/padi-ai-${var.environment}"
  target_key_id = aws_kms_key.app.key_id
}
```

---

**Docker Compose for Local Development:**

```yaml
# docker/docker-compose.dev.yml
version: '3.9'

services:
  postgres:
    image: pgvector/pgvector:pg17
    container_name: padi-ai-postgres
    environment:
      POSTGRES_DB: padi_ai_dev
      POSTGRES_USER: padi-ai
      POSTGRES_PASSWORD: devpassword123
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init-scripts:/docker-entrypoint-initdb.d
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U padi-ai -d padi_ai_dev"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: padi-ai-redis
    ports:
      - "6379:6379"
    command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  localstack:
    image: localstack/localstack:latest
    container_name: padi-ai-localstack
    ports:
      - "4566:4566"    # LocalStack gateway
    environment:
      SERVICES: ses,secretsmanager,kms
      DEFAULT_REGION: us-west-2
      DEBUG: 0
    volumes:
      - localstack_data:/var/lib/localstack
      - ./localstack-init:/etc/localstack/init/ready.d

  api:
    build:
      context: ../backend
      dockerfile: Dockerfile.dev
    container_name: padi-ai-api
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql+asyncpg://padi:devpassword123@postgres:5432/padi_ai_dev
      REDIS_URL: redis://redis:6379/0
      AUTH0_DOMAIN: dev-padi.us.auth0.com
      AUTH0_API_AUDIENCE: https://api.padi-ai.dev
      AWS_ENDPOINT_URL: http://localstack:4566
      AWS_REGION: us-west-2
      AWS_ACCESS_KEY_ID: test
      AWS_SECRET_ACCESS_KEY: test
      ENVIRONMENT: development
      LOG_LEVEL: DEBUG
      CORS_ALLOWED_ORIGINS: http://localhost:3000
    volumes:
      - ../backend:/app
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      localstack:
        condition: service_started
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

volumes:
  postgres_data:
  localstack_data:
```

### 4.2 Environment Variable Reference

#### FastAPI API Server — `.env.example`

```bash
# ============================================================
# PADI.AI — API Server Environment Variables
# Copy to .env and fill in values
# ============================================================

# ─── Database ─────────────────────────────────────────────────
DATABASE_URL=postgresql+asyncpg://padi:password@localhost:5432/padi_ai_dev
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10
DATABASE_POOL_TIMEOUT=30

# ─── Redis ────────────────────────────────────────────────────
REDIS_URL=redis://localhost:6379/0
REDIS_MAX_CONNECTIONS=50

# ─── Auth0 ────────────────────────────────────────────────────
AUTH0_DOMAIN=dev-padi.us.auth0.com
AUTH0_API_AUDIENCE=https://api.padi-ai.dev
AUTH0_CLIENT_ID=your_client_id
AUTH0_CLIENT_SECRET=your_client_secret
AUTH0_MANAGEMENT_API_TOKEN=  # For user management (admin only)

# ─── AWS ──────────────────────────────────────────────────────
AWS_REGION=us-west-2
AWS_ACCESS_KEY_ID=  # Leave blank for IAM role (ECS)
AWS_SECRET_ACCESS_KEY=
AWS_SES_FROM_EMAIL=noreply@padi-ai.com
AWS_SES_CONFIGURATION_SET=padi-ai-emails
AWS_ENDPOINT_URL=  # Set to http://localhost:4566 for LocalStack

# ─── Security ─────────────────────────────────────────────────
SECRET_KEY=your-256-bit-secret-key-here-min-32-chars
ENCRYPTION_KEY=your-256-bit-aes-key-for-pii-fields
JWT_ALGORITHM=RS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
JWT_REFRESH_TOKEN_EXPIRE_DAYS=30

# ─── Application ──────────────────────────────────────────────
ENVIRONMENT=development
LOG_LEVEL=DEBUG
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001
SENTRY_DSN=https://xxx@sentry.io/yyy
SENTRY_ENVIRONMENT=development
SENTRY_TRACES_SAMPLE_RATE=1.0

# ─── Rate Limiting ────────────────────────────────────────────
RATE_LIMIT_DEFAULT=100/minute
RATE_LIMIT_AUTH=10/minute
RATE_LIMIT_ASSESSMENT=60/minute

# ─── Assessment Engine ────────────────────────────────────────
DIAGNOSTIC_MIN_QUESTIONS=35
DIAGNOSTIC_TARGET_QUESTIONS=40
DIAGNOSTIC_MAX_QUESTIONS=50
BKT_MASTERY_THRESHOLD=0.90
CAT_THETA_CONVERGENCE_SE=0.30
```

#### Next.js Web App — `.env.local.example`

```bash
# ============================================================
# PADI.AI — Next.js Frontend Environment Variables
# Copy to .env.local and fill in values
# ============================================================

# ─── API ──────────────────────────────────────────────────────
NEXT_PUBLIC_API_URL=http://localhost:8000/v1
API_SERVER_URL=http://localhost:8000/v1   # Server-side only (RSC)

# ─── Auth0 ────────────────────────────────────────────────────
NEXT_PUBLIC_AUTH0_DOMAIN=dev-padi.us.auth0.com
NEXT_PUBLIC_AUTH0_CLIENT_ID=your_client_id
AUTH0_CLIENT_SECRET=your_client_secret
AUTH0_BASE_URL=http://localhost:3000
AUTH0_ISSUER_BASE_URL=https://dev-padi.us.auth0.com

# ─── Analytics ────────────────────────────────────────────────
NEXT_PUBLIC_POSTHOG_KEY=phc_xxx
NEXT_PUBLIC_POSTHOG_HOST=https://us.i.posthog.com

# ─── Monitoring ───────────────────────────────────────────────
NEXT_PUBLIC_SENTRY_DSN=https://xxx@sentry.io/yyy
SENTRY_AUTH_TOKEN=  # For source map uploads during build

# ─── Feature Flags ────────────────────────────────────────────
NEXT_PUBLIC_ENABLE_ANALYTICS=true
NEXT_PUBLIC_ENABLE_ASSESSMENT_TIMER=true
```

### 4.3 GitHub Actions CI/CD Pipeline

```yaml
# .github/workflows/ci-cd.yml
name: CI/CD Pipeline

on:
  push:
    branches: [develop, staging, main]
  pull_request:
    branches: [develop, staging, main]

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

env:
  AWS_REGION: us-west-2
  ECR_REPOSITORY: padi-ai-api
  ECS_CLUSTER: padi-ai
  ECS_SERVICE: padi-ai-api
  PYTHON_VERSION: "3.12"
  NODE_VERSION: "20"

jobs:
  # ─────────────────────────────────────────────────────────────
  lint-backend:
    name: Lint Backend (Python)
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements-dev.txt

      - name: Run ruff linter
        run: |
          cd backend
          ruff check . --output-format=github

      - name: Run ruff formatter check
        run: |
          cd backend
          ruff format --check .

      - name: Run mypy type checking
        run: |
          cd backend
          mypy app/ --strict --ignore-missing-imports

  # ─────────────────────────────────────────────────────────────
  lint-frontend:
    name: Lint Frontend (TypeScript)
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'pnpm'

      - name: Install dependencies
        run: |
          cd frontend
          corepack enable
          pnpm install --frozen-lockfile

      - name: Run ESLint
        run: |
          cd frontend
          pnpm lint

      - name: Run TypeScript type check
        run: |
          cd frontend
          pnpm tsc --noEmit

      - name: Run Prettier check
        run: |
          cd frontend
          pnpm prettier --check .

  # ─────────────────────────────────────────────────────────────
  test-backend:
    name: Test Backend (Python + PostgreSQL)
    runs-on: ubuntu-latest
    needs: [lint-backend]
    services:
      postgres:
        image: pgvector/pgvector:pg17
        env:
          POSTGRES_DB: padi_ai_test
          POSTGRES_USER: padi-ai
          POSTGRES_PASSWORD: testpassword
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt -r requirements-dev.txt

      - name: Run database migrations
        run: |
          cd backend
          alembic upgrade head
        env:
          DATABASE_URL: postgresql+asyncpg://padi:testpassword@localhost:5432/padi_ai_test

      - name: Run pytest with coverage
        run: |
          cd backend
          pytest tests/ \
            --cov=app \
            --cov-report=xml:coverage.xml \
            --cov-report=term-missing \
            --cov-fail-under=85 \
            -v \
            --timeout=60
        env:
          DATABASE_URL: postgresql+asyncpg://padi:testpassword@localhost:5432/padi_ai_test
          REDIS_URL: redis://localhost:6379/0
          ENVIRONMENT: test
          SECRET_KEY: test-secret-key-min-32-characters-long
          ENCRYPTION_KEY: test-encryption-key-32-chars-long

      - name: Upload coverage report
        uses: codecov/codecov-action@v4
        with:
          file: backend/coverage.xml
          flags: backend

  # ─────────────────────────────────────────────────────────────
  test-frontend:
    name: Test Frontend (Jest + RTL)
    runs-on: ubuntu-latest
    needs: [lint-frontend]
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'pnpm'

      - name: Install dependencies
        run: |
          cd frontend
          corepack enable
          pnpm install --frozen-lockfile

      - name: Run Jest tests with coverage
        run: |
          cd frontend
          pnpm test -- --coverage --ci --watchAll=false

      - name: Upload coverage report
        uses: codecov/codecov-action@v4
        with:
          file: frontend/coverage/lcov.info
          flags: frontend

  # ─────────────────────────────────────────────────────────────
  security-scan:
    name: Security Scan
    runs-on: ubuntu-latest
    needs: [lint-backend, lint-frontend]
    steps:
      - uses: actions/checkout@v4

      - name: Run Trivy vulnerability scanner (backend)
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: 'backend'
          format: 'sarif'
          output: 'trivy-backend.sarif'
          severity: 'CRITICAL,HIGH'

      - name: Run Trivy vulnerability scanner (frontend)
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: 'frontend'
          format: 'sarif'
          output: 'trivy-frontend.sarif'
          severity: 'CRITICAL,HIGH'

      - name: Run Bandit (Python security linter)
        run: |
          pip install bandit
          cd backend
          bandit -r app/ -f json -o bandit-report.json -ll || true

      - name: Upload SARIF results
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: trivy-backend.sarif
        if: always()

  # ─────────────────────────────────────────────────────────────
  build-and-push:
    name: Build & Push Docker Image
    runs-on: ubuntu-latest
    needs: [test-backend, test-frontend, security-scan]
    if: github.event_name == 'push'
    permissions:
      id-token: write
      contents: read
    outputs:
      image_tag: ${{ steps.meta.outputs.tags }}
    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_DEPLOY_ROLE_ARN }}
          aws-region: ${{ env.AWS_REGION }}

      - name: Login to ECR
        id: ecr-login
        uses: aws-actions/amazon-ecr-login@v2

      - name: Build and push Docker image
        id: meta
        run: |
          IMAGE_TAG="${{ github.sha }}"
          FULL_TAG="${{ steps.ecr-login.outputs.registry }}/${{ env.ECR_REPOSITORY }}:${IMAGE_TAG}"
          docker build -t ${FULL_TAG} -f backend/Dockerfile backend/
          docker push ${FULL_TAG}
          echo "tags=${FULL_TAG}" >> $GITHUB_OUTPUT

  # ─────────────────────────────────────────────────────────────
  deploy-staging:
    name: Deploy to Staging
    runs-on: ubuntu-latest
    needs: [build-and-push]
    if: github.ref == 'refs/heads/staging' || github.ref == 'refs/heads/develop'
    environment: staging
    steps:
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_DEPLOY_ROLE_ARN }}
          aws-region: ${{ env.AWS_REGION }}

      - name: Update ECS service (rolling deployment)
        run: |
          aws ecs update-service \
            --cluster padi-ai-staging \
            --service padi-ai-api \
            --force-new-deployment \
            --task-definition padi-ai-api-staging

      - name: Wait for deployment stability
        run: |
          aws ecs wait services-stable \
            --cluster padi-ai-staging \
            --services padi-ai-api \
            --timeout 600

      - name: Run smoke tests
        run: |
          curl -f https://api-staging.padi-ai.com/health || exit 1

  # ─────────────────────────────────────────────────────────────
  deploy-prod:
    name: Deploy to Production (Blue-Green)
    runs-on: ubuntu-latest
    needs: [build-and-push, deploy-staging]
    if: github.ref == 'refs/heads/main'
    environment: production
    steps:
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_DEPLOY_ROLE_ARN }}
          aws-region: ${{ env.AWS_REGION }}

      - name: Deploy with CodeDeploy (Blue-Green)
        run: |
          aws deploy create-deployment \
            --application-name padi-ai-prod \
            --deployment-group-name padi-ai-api-prod \
            --revision revisionType=AppSpecContent,content='{"version":0.0,"Resources":[{"TargetService":{"Type":"AWS::ECS::Service","Properties":{"TaskDefinition":"arn:aws:ecs:${{ env.AWS_REGION }}:${{ secrets.AWS_ACCOUNT_ID }}:task-definition/padi-ai-api-prod","LoadBalancerInfo":{"ContainerName":"padi-ai-api","ContainerPort":8000}}}}]}' \
            --deployment-config-name CodeDeployDefault.ECSLinear10PercentEvery1Minutes

      - name: Wait for deployment completion
        run: |
          DEPLOY_ID=$(aws deploy list-deployments \
            --application-name padi-ai-prod \
            --deployment-group-name padi-ai-api-prod \
            --query 'deployments[0]' --output text)
          aws deploy wait deployment-successful --deployment-id ${DEPLOY_ID}

      - name: Run production smoke tests
        run: |
          curl -f https://api.padi-ai.com/health || exit 1
          curl -f https://api.padi-ai.com/v1/standards?grade=4 || exit 1
```


---

## 5. Testing Plan (Stage 1)

### 5.1 Unit Test Coverage Requirements

| Module | Coverage Target | Key Test Cases |
|--------|----------------|----------------|
| `BKTService` | 95% | BKT update with correct response increases P(L); incorrect response decreases P(L); guess parameter prevents P(L) dropping to 0; slip parameter prevents P(L) reaching 1.0; boundary clamping at 0.001/0.999; bulk initialization from multiple responses; mastery classification thresholds match spec; edge case: all correct → mastered; edge case: all incorrect → below_par |
| `AssessmentService` | 90% | Start diagnostic creates correct records; get_next_question returns valid question; submit_response evaluates correctly; complete_assessment finalizes BKT states; completion criteria enforced (min 35 questions); pause/resume preserves state; cannot start duplicate diagnostic; parent ownership verified |
| `QuestionSelectionService` | 90% | Selects from lowest-coverage standard first; Fisher information maximization picks optimal item; exposure control reduces overused items; θ estimation converges with sufficient responses; handles empty question pool gracefully; handles all questions used; difficulty window filter applied; fallback to random when all items equal |
| `ConsentService` | 100% | Token generation produces valid HMAC; token validation succeeds with correct token; expired token rejected; already-used token rejected; consent confirmation sets status='active'; revocation sets status='revoked'; email sent on initiation; confirmation email sent; COPPA text hash stored correctly; IP and user agent captured |
| `StandardsRepository` | 80% | Returns all grade 4 standards; filters by domain correctly; includes prerequisites when requested; standard detail includes BKT defaults; unknown code returns None; search by partial code works |
| `QuestionRepository` | 85% | CRUD operations work correctly; filter by standard+difficulty; filter by status; IRT parameter range queries; question pool loading with exclusion list; times_shown/times_correct increment; pagination works |
| `AssessmentRepository` | 85% | Create assessment with session; find active assessment for student; update assessment status; get responses for assessment; persist skill states; partition-aware inserts for responses |
| `StudentRepository` | 85% | Create student with parent reference; update student; delete cascades correctly; find by parent_id; unique display name per parent enforced |
| `AuthMiddleware` | 90% | Valid JWT passes through; expired JWT returns 401; invalid signature returns 401; missing token returns 401; correct user_id extracted from claims; role-based access enforced; rate limiting applied per endpoint |
| `EncryptionService` | 100% | AES-256 encrypt then decrypt returns original; different keys produce different ciphertext; hash is deterministic for same input; hash is one-way (cannot reverse); empty string handled; Unicode handled |

### 5.2 Integration Test Scenarios

**IT-01: Parent Registration End-to-End**
- **Setup:** Empty database
- **Action:** `POST /auth/register` with valid data → `POST /auth/verify-email` with valid token → `POST /auth/login`
- **Expected:** User created, email_verified=True, login returns valid tokens, consent_completed=false
- **Teardown:** Delete user record

**IT-02: COPPA Consent Flow**
- **Setup:** Verified parent user exists, no consent records
- **Action:** `POST /consent/initiate` → extract token from mock SES → `POST /consent/confirm` with token → `GET /consent/status`
- **Expected:** Consent record transitions: pending → active. Status endpoint shows has_active_consent=true. Audit log entries created for both initiate and confirm.
- **Teardown:** Delete consent records

**IT-03: Student Creation with Consent Check**
- **Setup:** Parent with active consent
- **Action:** `POST /students` with valid data
- **Expected:** Student created, linked to parent, returned with correct fields
- **Teardown:** Delete student

**IT-04: Student Creation Without Consent Rejected**
- **Setup:** Parent exists but no active consent (only expired consent record)
- **Action:** `POST /students` with valid data
- **Expected:** 403 Forbidden with message "Active COPPA consent required"
- **Teardown:** None

**IT-05: Start Diagnostic Assessment**
- **Setup:** Parent with consent, student created, question bank seeded (≥4 questions per standard)
- **Action:** `POST /assessments` with student_id
- **Expected:** Assessment created with status='in_progress', session created, Redis state initialized with θ=0.0
- **Teardown:** Delete assessment + session + Redis keys

**IT-06: Full Diagnostic Assessment Flow (35 Questions)**
- **Setup:** Parent, student, consent, full question bank (150+ questions)
- **Action:** `POST /assessments` → loop 35x: `GET /next-question` → `POST /responses` → `PUT /complete`
- **Expected:** Each question targets lowest-coverage standard. Responses stored correctly. BKT states computed and persisted. Gap analysis generated. Overall score matches manual calculation. Results endpoint returns complete data.
- **Teardown:** Clean all assessment data

**IT-07: Assessment Pause and Resume**
- **Setup:** Active assessment with 10 responses
- **Action:** Close browser → new session → `GET /next-question` (should resume from question 11)
- **Expected:** Previous responses preserved in DB. New session created. Question selection continues from correct state. Total progress correct.
- **Teardown:** Clean assessment data

**IT-08: Concurrent Assessment Prevention**
- **Setup:** Student with active in-progress assessment
- **Action:** `POST /assessments` with same student_id
- **Expected:** 400 Bad Request "Student already has an active diagnostic assessment"
- **Teardown:** Complete or abandon first assessment

**IT-09: RLS Parent Isolation**
- **Setup:** Two parents, each with one student
- **Action:** Parent A tries to access Parent B's student via `GET /students/{parentB_studentId}`
- **Expected:** 404 Not Found (RLS hides the record entirely)
- **Teardown:** None

**IT-10: Standards API with Prerequisites**
- **Setup:** Full standards table with prerequisite relationships
- **Action:** `GET /standards?grade=4&domain=4.NF&include_prerequisites=true`
- **Expected:** Returns all 4.NF standards with prerequisite codes. Prerequisite codes reference valid standards. Response validates against Pydantic schema.
- **Teardown:** None (read-only)

### 5.3 E2E Test Scenarios (Playwright)

**E2E-01: New Parent Registration to Dashboard**
```typescript
test('new parent can register and reach dashboard', async ({ page }) => {
  // Navigate to registration
  await page.goto('/register');
  await expect(page.getByRole('heading', { name: /create your account/i })).toBeVisible();
  
  // Fill registration form
  await page.fill('[name="email"]', 'test-parent@example.com');
  await page.fill('[name="password"]', 'SecureP@ssw0rd!');
  await page.fill('[name="confirmPassword"]', 'SecureP@ssw0rd!');
  await page.fill('[name="displayName"]', 'Test Parent');
  await page.click('button[type="submit"]');
  
  // Should redirect to Auth0, then back to verify-email page
  await page.waitForURL('**/verify-email**');
  await expect(page.getByText(/check your email/i)).toBeVisible();
  
  // Simulate email verification (test helper)
  await page.goto('/verify-email?token=test-verification-token');
  await page.waitForURL('**/consent**');
  
  // COPPA Consent flow
  await expect(page.getByText(/parental consent/i)).toBeVisible();
  await page.check('#consent-data-collection');
  await page.check('#consent-data-use');
  await page.check('#consent-third-party');
  await page.check('#consent-parental-rights');
  await page.fill('[name="signature"]', 'Test Parent');
  await page.click('button:has-text("Submit Consent")');
  
  // Wait for consent email confirmation (simulated)
  await page.waitForURL('**/create-student**');
  
  // Create student profile
  await page.fill('[name="displayName"]', 'Timmy');
  await page.click('[data-avatar="avatar_robot"]');
  await page.click('button:has-text("Create Profile")');
  
  // Should arrive at parent dashboard
  await page.waitForURL('**/dashboard**');
  await expect(page.getByText('Timmy')).toBeVisible();
  await expect(page.getByRole('button', { name: /start diagnostic/i })).toBeVisible();
});
```

**E2E-02: Complete Diagnostic Assessment (Abbreviated)**
```typescript
test('student can complete diagnostic assessment', async ({ page }) => {
  // Login as test parent (pre-seeded with consent + student)
  await page.goto('/login');
  await page.fill('[name="email"]', 'seeded-parent@test.com');
  await page.fill('[name="password"]', 'TestP@ss123!');
  await page.click('button[type="submit"]');
  await page.waitForURL('**/dashboard**');
  
  // Start diagnostic for seeded student
  await page.click('button:has-text("Start Diagnostic")');
  await page.waitForURL('**/diagnostic/start**');
  await page.click('[data-student-id]');  // Select first student
  await page.click('button:has-text("Begin Assessment")');
  
  // Should be on assessment page
  await page.waitForURL(/\/diagnostic\/[a-f0-9-]+/);
  
  // Answer 35 questions (select random valid options)
  for (let i = 0; i < 35; i++) {
    await expect(page.locator('[data-testid="question-stem"]')).toBeVisible();
    await expect(page.locator('[data-testid="progress-indicator"]')).toContainText(`${i + 1}`);
    
    // Select first option (for test speed)
    await page.click('[data-testid="option-A"]');
    await page.click('button:has-text("Submit Answer")');
    
    // Wait for feedback display
    await page.waitForSelector('[data-testid="feedback"]', { timeout: 3000 });
    
    // Advance to next question (if not last)
    if (i < 34) {
      await page.click('button:has-text("Next Question")');
    }
  }
  
  // Assessment completion
  await page.click('button:has-text("Complete Assessment")');
  await page.waitForURL('**/diagnostic/results**');
  
  // Verify results display
  await expect(page.getByText(/diagnostic results/i)).toBeVisible();
  await expect(page.locator('[data-testid="overall-score"]')).toBeVisible();
  await expect(page.locator('[data-testid="domain-breakdown"]')).toBeVisible();
  await expect(page.locator('[data-testid="gap-analysis"]')).toBeVisible();
});
```

**E2E-03: Assessment Pause and Resume**
```typescript
test('assessment can be paused and resumed', async ({ page }) => {
  // Login and start assessment (helper)
  await loginAndStartAssessment(page);
  
  // Answer 5 questions
  for (let i = 0; i < 5; i++) {
    await page.click('[data-testid="option-B"]');
    await page.click('button:has-text("Submit Answer")');
    await page.waitForSelector('[data-testid="feedback"]');
    await page.click('button:has-text("Next Question")');
  }
  
  // Verify progress shows 5/40
  await expect(page.locator('[data-testid="progress-indicator"]')).toContainText('6');
  
  // Navigate away (simulate pause)
  await page.goto('/dashboard');
  
  // Resume assessment
  await page.click('button:has-text("Resume Assessment")');
  await page.waitForURL(/\/diagnostic\/[a-f0-9-]+/);
  
  // Should show question 6 (progress preserved)
  await expect(page.locator('[data-testid="progress-indicator"]')).toContainText('6');
  await expect(page.locator('[data-testid="question-stem"]')).toBeVisible();
});
```

**E2E-04: Admin Question Management**
```typescript
test('admin can create and edit questions', async ({ page }) => {
  // Login as admin
  await page.goto('/login');
  await page.fill('[name="email"]', 'admin@padi-ai.com');
  await page.fill('[name="password"]', 'AdminP@ss123!');
  await page.click('button[type="submit"]');
  
  // Navigate to question management
  await page.goto('/admin/questions');
  await expect(page.getByRole('heading', { name: /question bank/i })).toBeVisible();
  
  // Create new question
  await page.click('button:has-text("Add Question")');
  await page.selectOption('[name="standardCode"]', '4.OA.A.1');
  await page.selectOption('[name="difficulty"]', '3');
  await page.fill('[name="stem"]', 'What is 7 × 8?');
  await page.fill('[name="optionA"]', '54');
  await page.fill('[name="optionB"]', '56');
  await page.fill('[name="optionC"]', '48');
  await page.fill('[name="optionD"]', '64');
  await page.selectOption('[name="correctAnswer"]', 'B');
  await page.fill('[name="explanation"]', '7 × 8 = 56');
  await page.click('button:has-text("Save Question")');
  
  // Verify question appears in list
  await expect(page.getByText('What is 7 × 8?')).toBeVisible();
  
  // Edit question
  await page.click('[data-testid="edit-question-btn"]:first-child');
  await page.fill('[name="explanation"]', '7 × 8 = 56. You can also think of it as 7 × 4 × 2 = 28 × 2 = 56.');
  await page.click('button:has-text("Update Question")');
  
  await expect(page.getByText('Question updated')).toBeVisible();
});
```

**E2E-05: Accessibility — Keyboard-Only Assessment Navigation**
```typescript
test('assessment can be completed with keyboard only', async ({ page }) => {
  await loginAndStartAssessment(page);
  
  // Tab to first option
  await page.keyboard.press('Tab');
  await page.keyboard.press('Tab'); // Skip progress bar
  
  // Select option with keyboard
  await page.keyboard.press('Space'); // Select option A
  await expect(page.locator('[data-testid="option-A"]')).toHaveAttribute('aria-checked', 'true');
  
  // Tab to submit button and press Enter
  await page.keyboard.press('Tab');
  await page.keyboard.press('Tab');
  await page.keyboard.press('Tab');
  await page.keyboard.press('Enter'); // Submit
  
  // Feedback should be visible and focusable
  await expect(page.locator('[data-testid="feedback"]')).toBeVisible();
  await expect(page.locator('[data-testid="feedback"]')).toBeFocused();
  
  // Tab to "Next Question" and press Enter
  await page.keyboard.press('Tab');
  await page.keyboard.press('Enter');
  
  // Next question should be displayed
  await expect(page.locator('[data-testid="question-stem"]')).toBeVisible();
});
```

### 5.4 Performance Tests

**Load Test: 100 Concurrent Diagnostic Sessions (k6)**

```javascript
// tests/performance/diagnostic_load_test.js
import http from 'k6/http';
import { check, sleep } from 'k6';
import { SharedArray } from 'k6/data';

export const options = {
  scenarios: {
    diagnostic_sessions: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '30s', target: 50 },   // Ramp to 50
        { duration: '2m', target: 100 },   // Hold at 100
        { duration: '30s', target: 0 },    // Ramp down
      ],
      gracefulRampDown: '30s',
    },
  },
  thresholds: {
    http_req_duration: ['p(95)<500', 'p(99)<1000'],   // 95th < 500ms
    http_req_failed: ['rate<0.01'],                     // <1% error rate
    'http_req_duration{endpoint:next_question}': ['p(95)<200'],  // Question selection < 200ms
    'http_req_duration{endpoint:submit_response}': ['p(95)<300'], // Response processing < 300ms
  },
};

const BASE_URL = __ENV.API_URL || 'https://api-staging.padi-ai.com/v1';

export default function () {
  const token = getAuthToken(); // Pre-generated test tokens
  const headers = { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' };

  // Start assessment
  const startRes = http.post(`${BASE_URL}/assessments`, 
    JSON.stringify({ student_id: getRandomStudentId() }), 
    { headers, tags: { endpoint: 'start_assessment' } }
  );
  check(startRes, { 'assessment started': (r) => r.status === 201 });
  
  const assessmentId = startRes.json('assessment_id');
  
  // Answer 40 questions
  for (let i = 0; i < 40; i++) {
    // Get next question
    const qRes = http.get(`${BASE_URL}/assessments/${assessmentId}/next-question`,
      { headers, tags: { endpoint: 'next_question' } }
    );
    check(qRes, { 'got question': (r) => r.status === 200 });
    
    if (qRes.json('should_end')) break;
    
    const questionId = qRes.json('question.question_id');
    
    // Submit response
    const respRes = http.post(`${BASE_URL}/assessments/${assessmentId}/responses`,
      JSON.stringify({
        question_id: questionId,
        selected_answer: ['A', 'B', 'C', 'D'][Math.floor(Math.random() * 4)],
        time_spent_ms: Math.floor(Math.random() * 30000) + 5000,
        client_timestamp: new Date().toISOString(),
      }),
      { headers, tags: { endpoint: 'submit_response' } }
    );
    check(respRes, { 'response accepted': (r) => r.status === 200 });
    
    sleep(1); // Simulate student thinking time
  }
  
  // Complete assessment
  const completeRes = http.put(`${BASE_URL}/assessments/${assessmentId}/complete`,
    null, { headers, tags: { endpoint: 'complete_assessment' } }
  );
  check(completeRes, { 'assessment completed': (r) => r.status === 200 });
}
```

**BKT Benchmark Test:**

```python
# tests/performance/test_bkt_benchmark.py
import pytest
from app.services.bkt_service import BKTService, BKTState
import random


@pytest.fixture
def bkt_service():
    return BKTService()


@pytest.fixture
def initial_state():
    return BKTState(
        p_mastery=0.10,
        p_transit=0.10,
        p_slip=0.05,
        p_guess=0.25,
        observations=0,
        correct_count=0,
    )


def test_bkt_10k_updates_under_5_seconds(benchmark, bkt_service, initial_state):
    """10,000 BKT state updates must complete in < 5 seconds."""
    
    # Generate random response sequence
    random.seed(42)
    responses = [random.random() > 0.5 for _ in range(10_000)]
    
    def run_updates():
        state = initial_state
        for is_correct in responses:
            state = bkt_service.update_state(state, is_correct)
        return state
    
    result = benchmark.pedantic(run_updates, iterations=5, rounds=3)
    
    # Verify final state is valid
    assert 0.0 < result.p_mastery < 1.0
    assert result.observations == 10_000
    
    # Assert timing: benchmark.stats['mean'] should be < 5.0
    assert benchmark.stats['mean'] < 5.0, (
        f"BKT 10K updates took {benchmark.stats['mean']:.2f}s, exceeding 5s limit"
    )


def test_cat_selection_100_questions_under_100ms(benchmark, bkt_service):
    """Question selection for pool of 500 questions must complete in < 100ms."""
    from app.services.question_selection_service import QuestionSelectionService, CATState
    from tests.factories import QuestionFactory
    
    selection_service = QuestionSelectionService()
    
    # Create pool of 500 questions across 28 standards
    question_pool = [QuestionFactory.create() for _ in range(500)]
    all_standards = list(set(q.standard_code for q in question_pool))
    
    cat_state = CATState(
        theta=0.0,
        theta_se=1.5,
        covered_standards={},
        used_question_ids=set(),
        responses=[],
    )
    
    def select_question():
        return selection_service.select_next_question(cat_state, question_pool, all_standards)
    
    result = benchmark.pedantic(select_question, iterations=100, rounds=5)
    
    assert result is not None
    assert benchmark.stats['mean'] < 0.1, (
        f"CAT selection took {benchmark.stats['mean']*1000:.1f}ms, exceeding 100ms limit"
    )
```


---

## 6. QA Plan

### 6.1 QA Checklist (Stage 1 Exit Criteria)

#### Functional QA

- [ ] Parent can complete registration via Auth0 Universal Login without assistance
- [ ] Email verification link arrives within 2 minutes and correctly verifies account
- [ ] COPPA consent form displays all 4 required acknowledgement clauses
- [ ] COPPA consent cannot be submitted without all checkboxes checked
- [ ] Consent verification email arrives and confirmation link activates consent
- [ ] Consent record captures IP address, user agent, and timestamp
- [ ] Consent confirmation sends receipt email to parent
- [ ] Parent cannot create student profile without active COPPA consent
- [ ] Child profile creation works with valid display name, avatar selection
- [ ] Duplicate child display names for same parent are rejected with clear message
- [ ] Parent dashboard shows all their children with status cards
- [ ] Diagnostic assessment can be started for a child
- [ ] Only one active diagnostic per student at a time (duplicate prevented)
- [ ] Diagnostic presents between 35 and 50 questions
- [ ] Questions cover all 5 Oregon 4th-grade domains (4.OA, 4.NBT, 4.NF, 4.GM, 4.DR)
- [ ] Each standard receives ≥2 questions during diagnostic
- [ ] Questions are presented in adaptive order (not sequential by standard)
- [ ] Answer options are rendered correctly (including any LaTeX/images)
- [ ] Submitting an answer shows correctness feedback for 1.5 seconds
- [ ] Progress bar updates correctly after each question
- [ ] Session can be paused by navigating away without data loss
- [ ] Session can be resumed from the correct question after pause
- [ ] Assessment completes and shows results summary
- [ ] Results display per-domain breakdown (4.OA, 4.NBT, 4.NF, 4.GM, 4.DR)
- [ ] Results display per-standard mastery classification
- [ ] Gap analysis correctly identifies strengths, on-track, and needs-work skills
- [ ] Recommended focus order respects prerequisite dependencies
- [ ] "Results ready" email sent to parent after assessment completion
- [ ] Admin can log in and access question management interface
- [ ] Admin can create, edit, and retire questions
- [ ] Admin question search filters by standard and difficulty
- [ ] Parent cannot access admin routes (returns 403 or redirect)
- [ ] Logout invalidates session and redirects to login

#### Performance QA

- [ ] Assessment page loads in < 2s on simulated 4G (Chrome DevTools throttling)
- [ ] Question selection API responds in < 200ms (p95) with 500-question pool
- [ ] Response submission API responds in < 300ms (p95)
- [ ] Assessment results page loads in < 3s including chart rendering
- [ ] 100 concurrent diagnostic sessions maintain < 500ms p95 latency
- [ ] PostgreSQL query performance: no query exceeds 100ms (check pg_stat_statements)
- [ ] Redis operations complete in < 10ms for all assessment state reads/writes
- [ ] Frontend bundle size < 200KB gzipped (initial load)

#### Security QA

- [ ] COPPA consent records include timestamp, IP, user agent, and policy version hash
- [ ] Student records contain no direct PII (no real names, no email addresses)
- [ ] Parent email is encrypted at rest in database (verify ciphertext in DB)
- [ ] Email hash allows lookup without decryption
- [ ] JWT access tokens expire after 60 minutes
- [ ] JWT refresh tokens expire after 30 days
- [ ] Expired JWT returns 401 with no sensitive information in error body
- [ ] SQL injection attempt on any endpoint returns 422, no raw SQL error exposed
- [ ] XSS payload in question stem is sanitized on display
- [ ] CORS only allows configured origins (not wildcard)
- [ ] Rate limiting blocks brute-force login attempts (>10/min)
- [ ] Rate limiting blocks assessment endpoint abuse (>60/min)
- [ ] RLS prevents parent A from accessing parent B's student data
- [ ] RLS prevents parent A from accessing parent B's assessment data
- [ ] API responses do not include internal IDs, stack traces, or DB schema details in errors
- [ ] All database connections use TLS
- [ ] Redis connections use TLS in-transit encryption
- [ ] No PII appears in application logs (verify CloudWatch log groups)
- [ ] Secrets Manager rotation is configured for database credentials

#### Accessibility QA

- [ ] All images have descriptive alt text
- [ ] All form inputs have associated `<label>` elements
- [ ] All interactive elements have visible focus indicators
- [ ] Keyboard navigation works through entire assessment flow (Tab, Enter, Space)
- [ ] Screen reader announces question stem, options, and feedback correctly
- [ ] Color is never the sole indicator of correctness (icon + text + color)
- [ ] WCAG AA contrast ratios met for all text (4.5:1 body, 3:1 large)
- [ ] Assessment timer (if displayed) has aria-live="polite" for screen readers
- [ ] No content relies on hover-only interactions
- [ ] Skip navigation link present on all pages

### 6.3 Bug Triage Severity Levels

| Severity | Definition | Example (PADI.AI) | Response SLA | Escalation |
|----------|-----------|---------------------|-------------|------------|
| **P0 — Critical** | System down, data loss, or COPPA/legal violation. Affects all users. | COPPA consent bypass discovered; student PII exposed in logs; database corruption; production 5xx for all users | **Acknowledge: 15 min**. Fix or mitigate: 4 hours. Postmortem: 24 hours. | Immediate page to on-call + engineering lead. CEO notification for COPPA issues. |
| **P1 — High** | Core feature broken for subset of users. Data integrity risk. | Assessment cannot complete (stuck at question 35); BKT calculations produce NaN; parent cannot register; emails not sending | **Acknowledge: 1 hour**. Fix: 24 hours. | Engineering lead + PM notified. Hotfix branch if needed. |
| **P2 — Medium** | Feature works but degraded. Workaround available. | Assessment progress bar shows wrong count; question images slow to load; admin search returns incomplete results; occasional 500 on refresh | **Acknowledge: 4 hours**. Fix: next sprint. | Added to sprint backlog. PM prioritizes. |
| **P3 — Low** | Cosmetic, minor UX, or edge case. | Tooltip text truncated on mobile; avatar selection border inconsistent; typo in consent form footer; extra whitespace in results summary | **Acknowledge: 1 business day**. Fix: backlog (within 2 sprints). | Logged in issue tracker. No escalation. |

---

## 7. Operational Runbooks

### Runbook 1: Database Migration Procedure

**Trigger:** New Alembic migration to apply (schema change, index addition, data migration).

| Step | Action | Command / Detail | Rollback |
|------|--------|-----------------|----------|
| 1 | **Create RDS snapshot** | `aws rds create-db-snapshot --db-instance-identifier padi-ai-prod --db-snapshot-identifier pre-migration-$(date +%Y%m%d-%H%M)` | N/A |
| 2 | **Wait for snapshot completion** | `aws rds wait db-snapshot-available --db-snapshot-identifier pre-migration-...` | N/A |
| 3 | **Apply migration to staging** | SSH into staging bastion → `cd /app && alembic upgrade head` | `alembic downgrade -1` on staging |
| 4 | **Run integration tests on staging** | `pytest tests/integration/ -v --timeout=120` | If tests fail: rollback staging and abort |
| 5 | **Verify staging data integrity** | Manual spot-check: query key tables, verify row counts, check constraints | Abort if anomalies found |
| 6 | **Schedule maintenance window** | Post in #engineering Slack: "DB migration starting at HH:MM UTC. Expected duration: X min." | N/A |
| 7 | **Apply migration to production** | Via bastion: `alembic upgrade head` on prod connection | `alembic downgrade -1` within 30 min |
| 8 | **Verify production** | Query `alembic_version` table. Run health check: `curl https://api.padi-ai.com/health`. Verify API responses for key endpoints. | Restore from snapshot if downgrade fails |
| 9 | **Monitor for 30 minutes** | Watch CloudWatch metrics: error rate, latency, DB connections. Check Sentry for new errors. | Trigger Runbook 5 (DB Restore) if needed |
| 10 | **Announce completion** | Post in #engineering: "Migration complete. All clear." | N/A |

### Runbook 2: Roll Back a Production Deployment

**Trigger:** P0/P1 bug discovered after production deployment. Error rate spike, latency spike, or functional regression.

| Step | Action | Command / Detail |
|------|--------|-----------------|
| 1 | **Identify the issue** | Check Sentry for new errors. Check CloudWatch ALB 5xx metrics. Check ECS deployment events. |
| 2 | **Determine rollback scope** | If API only: rollback ECS task definition. If DB migration involved: see Runbook 1 rollback. If frontend: rollback Vercel deployment. |
| 3 | **Rollback ECS task definition** | `aws ecs update-service --cluster padi-ai-prod --service padi-ai-api --task-definition padi-ai-api-prod:PREVIOUS_REVISION --force-new-deployment` |
| 4 | **Wait for rollback deployment** | `aws ecs wait services-stable --cluster padi-ai-prod --services padi-ai-api` |
| 5 | **Verify rollback** | `curl https://api.padi-ai.com/health` — verify version header matches previous release. Run smoke tests. |
| 6 | **Rollback Vercel (if needed)** | Vercel Dashboard → Deployments → find previous stable deployment → Promote to Production |
| 7 | **Communicate** | Post in #engineering and #incidents: "Production rollback complete. Investigating root cause." |
| 8 | **Trigger postmortem** | Create postmortem document from template. Schedule review meeting within 48 hours. |

### Runbook 3: LLM API Key Rotation

**Trigger:** Scheduled quarterly rotation, suspected compromise, or key approaching expiration.

| Step | Action | Command / Detail |
|------|--------|-----------------|
| 1 | **Generate new API key** | OpenAI: dashboard.openai.com → API Keys → Create new. Anthropic: console.anthropic.com → API Keys → Create new. |
| 2 | **Update AWS Secrets Manager** | `aws secretsmanager update-secret --secret-id padi-ai/prod/app --secret-string '{"OPENAI_API_KEY":"sk-new-key...", ...}'` |
| 3 | **Restart ECS tasks** (rolling) | `aws ecs update-service --cluster padi-ai-prod --service padi-ai-api --force-new-deployment` |
| 4 | **Wait for new tasks healthy** | `aws ecs wait services-stable --cluster padi-ai-prod --services padi-ai-api` |
| 5 | **Verify new key works** | Trigger a test API call (Stage 2: generate a test question). Check CloudWatch logs for successful LLM API calls. |
| 6 | **Revoke old API key** | OpenAI/Anthropic dashboard: delete old key. Do NOT revoke before new tasks are confirmed healthy. |
| 7 | **Update staging/dev** | Repeat steps 2-5 for staging and dev environments. |
| 8 | **Document rotation** | Log in #security channel: date, reason, old key suffix (last 4 chars), new key suffix. |

### Runbook 4: COPPA Data Deletion Request

**Trigger:** Parent requests deletion of their child's data (COPPA right to delete). Must be completed within 48 hours of verified request.

| Step | Action | Detail |
|------|--------|--------|
| 1 | **Receive request** | Via email to privacy@padi-ai.com, or in-app settings. Log request in issue tracker with timestamp. |
| 2 | **Verify parent identity** | Require parent to authenticate via Auth0. If via email: send verification link. Confirm `parent_id` matches the requesting email. |
| 3 | **Identify all student data** | Query: `SELECT id FROM students WHERE parent_id = :parent_id` → list all student_ids. |
| 4 | **Export data (parent copy)** | Generate JSON export of child's assessment results (if parent requests). Send via secure link (24-hour expiry). |
| 5 | **Delete student data** (in order) | Execute in a single transaction: |
| 5a | | `DELETE FROM student_skill_states WHERE student_id IN (:student_ids)` |
| 5b | | `DELETE FROM assessment_responses WHERE assessment_id IN (SELECT id FROM assessments WHERE student_id IN (:student_ids))` |
| 5c | | `DELETE FROM assessment_sessions WHERE assessment_id IN (SELECT id FROM assessments WHERE student_id IN (:student_ids))` |
| 5d | | `DELETE FROM assessments WHERE student_id IN (:student_ids)` |
| 5e | | `DELETE FROM students WHERE id IN (:student_ids)` (cascade) |
| 6 | **Delete consent records** | `DELETE FROM consent_records WHERE parent_id = :parent_id` |
| 7 | **Delete parent account** (if requested) | `DELETE FROM users WHERE id = :parent_id` |
| 8 | **Purge Redis cache** | `redis-cli KEYS "assessment:*" | xargs redis-cli DEL` (for relevant keys). `redis-cli DEL "session:{user_id}"` |
| 9 | **Create deletion audit record** | INSERT into `audit_log`: action='COPPA_DELETION', record_id=parent_id, new_data=JSON with list of deleted record counts. This audit record is retained for compliance (records that deletion occurred, not the deleted data). |
| 10 | **Send confirmation** | Email parent: "Your child's data has been permanently deleted from PADI.AI as of [date]. Deletion reference: [audit_id]." |
| 11 | **Verify deletion** | Run verification queries to confirm zero rows remain for the parent_id and student_ids in all tables (except audit_log). |

### Runbook 5: Production Database Restore from Backup

**Trigger:** Data corruption, accidental deletion, or failed migration that cannot be rolled back.

| Step | Action | Command / Detail |
|------|--------|-----------------|
| 1 | **Identify recovery point** | Determine the last known good timestamp. Check RDS automated backups and manual snapshots. `aws rds describe-db-snapshots --db-instance-identifier padi-ai-prod --query 'sort_by(DBSnapshots, &SnapshotCreateTime)[-5:].[DBSnapshotIdentifier,SnapshotCreateTime]'` |
| 2 | **Put application in maintenance mode** | Update ALB listener rule to return 503 with maintenance page. OR: set ECS desired count to 0. Communicate in #incidents. |
| 3 | **Restore RDS to point-in-time** | `aws rds restore-db-instance-to-point-in-time --source-db-instance-identifier padi-ai-prod --target-db-instance-identifier padi-ai-prod-restored --restore-time "2026-04-04T18:00:00Z" --db-subnet-group-name padi-ai-prod --vpc-security-group-ids sg-xxx` |
| 4 | **Wait for restore** | `aws rds wait db-instance-available --db-instance-identifier padi-ai-prod-restored` (may take 15-60 min) |
| 5 | **Verify restored data** | Connect to restored instance via bastion. Spot-check: row counts, recent timestamps, data integrity. |
| 6 | **Update connection strings** | Update Secrets Manager: `aws secretsmanager update-secret --secret-id padi-ai/prod/app --secret-string '{"DATABASE_URL":"...new-endpoint..."}'` |
| 7 | **Restart ECS tasks** | `aws ecs update-service --cluster padi-ai-prod --service padi-ai-api --force-new-deployment` |
| 8 | **Verify application** | Health check. Run smoke tests. Verify key API endpoints return expected data. |
| 9 | **Rename instances** | Rename old corrupt instance: `aws rds modify-db-instance --db-instance-identifier padi-ai-prod --new-db-instance-identifier padi-ai-prod-corrupt`. Rename restored: `...padi-ai-prod-restored ... --new-db-instance-identifier padi-ai-prod` |
| 10 | **Resume traffic** | Restore ALB listener rule. Set ECS desired count to normal. |
| 11 | **Delete corrupt instance** (after verification period) | Keep for 72 hours for investigation, then: `aws rds delete-db-instance --db-instance-identifier padi-ai-prod-corrupt --skip-final-snapshot` |
| 12 | **Postmortem** | Trigger incident postmortem. Document: what went wrong, data loss window, recovery time, prevention measures. |

