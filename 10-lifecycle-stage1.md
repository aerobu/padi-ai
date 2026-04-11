# PADI.AI — SDLC Lifecycle Document
## Stage 1: Standards Database & Diagnostic Assessment Engine
### Months 1–3 | Document ID: LC-001 | Version 1.0 | Status: Approved

---

## Table of Contents

1. [Architecture Review](#1-architecture-review)
   - 1.1 Component Overview
   - 1.2 System Context & Data Flow
   - 1.3 Key Architectural Decisions
   - 1.4 Integration Points
   - 1.5 Risk Areas & Mitigation
   - 1.6 Performance & Scalability Considerations
2. [User Story Breakup](#2-user-story-breakup)
   - Epic 1: Parent Account & COPPA Compliance
   - Epic 2: Oregon Standards Database
   - Epic 3: Seed Question Bank
   - Epic 4: Diagnostic Assessment Engine
   - Epic 5: Results & Gap Analysis Display
3. [Detailed Test Plan](#3-detailed-test-plan)
   - 3.1 Unit Tests
   - 3.2 Integration Tests
   - 3.3 End-to-End Tests (Playwright)
   - 3.4 Behavioral / BDD Tests
   - 3.5 Robustness & Resilience Tests
   - 3.6 Repeatability Tests
   - 3.7 Security Tests
   - 3.8 Baseline Acceptance Criteria
4. [Operations Plan](#4-operations-plan)
   - 4.1 MLOps
   - 4.2 FinOps
   - 4.3 SecOps
   - 4.4 DevSecOps Pipeline
5. [Manual QA Plan](#5-manual-qa-plan)

---

## 1. Architecture Review

### 1.1 Component Overview

Stage 1 establishes the entire foundational layer of PADI.AI. All five subsequent stages depend on the accuracy and stability of the components delivered here. The architecture spans three tiers: a Next.js 15 frontend on Vercel, a FastAPI backend on AWS ECS Fargate, and a PostgreSQL 17 + Redis data tier on AWS RDS and ElastiCache.

#### Backend Components (apps/api/src/)

| Component | Location | Responsibility |
|-----------|----------|----------------|
| Auth Router | `api/v1/auth.py` | JWT validation via Auth0 JWKS, registration webhook, token refresh |
| Consent Service | `service/consent_service.py` | COPPA consent initiation, email-plus confirmation, revocation |
| Standards Router | `api/v1/standards.py` | CRUD for Oregon math standards, prerequisite graph queries |
| Standards Repository | `repository/standards_repo.py` | SQLAlchemy async queries against `standards` and `prerequisite_relationships` |
| Question Service | `service/question_service.py` | Admin-facing question CRUD, bulk import, validation workflow |
| Question Repository | `repository/question_repo.py` | Question pool queries, availability checks, statistics updates |
| Assessment Router | `api/v1/assessments.py` | Start/resume/complete diagnostic, next-question endpoint |
| Assessment Service | `service/assessment_service.py` | CAT orchestration, response recording, completion detection |
| BKT Service | `service/bkt_service.py` | pyBKT wrapper: state initialization, update, mastery probability |
| Question Selection Service | `service/question_selection_service.py` | CAT difficulty-adaptive selection, fallback logic |
| Student Repository | `repository/student_repo.py` | Child profile CRUD, ownership validation |
| Consent Repository | `repository/consent_repo.py` | Consent record persistence (append-only) |

#### Frontend Components (apps/web/src/)

| Component | Location | Type | Responsibility |
|-----------|----------|------|----------------|
| Registration Page | `app/(auth)/register/page.tsx` | CC | Email/password form → Auth0 Universal Login redirect |
| Login Page | `app/(auth)/login/page.tsx` | CC | Auth0 authorize flow |
| Consent Page | `app/(onboarding)/consent/page.tsx` | CC | COPPA consent multi-step form |
| Create Student Page | `app/(onboarding)/create-student/page.tsx` | CC | Child profile form |
| Parent Dashboard | `app/(dashboard)/page.tsx` | SC | Student card grid, diagnostic status, quick actions |
| Assessment Launcher | `app/(dashboard)/diagnostic/start/page.tsx` | CC | Child selector, pre-assessment briefing |
| Assessment Session | `app/(dashboard)/diagnostic/[sessionId]/page.tsx` | CC | Live question display, CAT integration |
| Results Display | `app/(dashboard)/diagnostic/results/page.tsx` | SC+CC | Skill breakdown charts, gap analysis |
| Admin Questions | `app/(admin)/questions/page.tsx` | CC | Question CRUD, review queue |
| Assessment Store | `stores/assessment-store.ts` | Zustand | Live session state, pause/resume, option selection |
| Auth Store | `stores/auth-store.ts` | Zustand | JWT, user role, consent status |
| KaTeX Components | `packages/math-renderer/src/` | Library | MathDisplay, FractionBuilder, NumberLine |

#### Infrastructure Components

| Component | AWS Service | Configuration |
|-----------|-------------|---------------|
| API Container | ECS Fargate | Python 3.12, FastAPI 0.115+, 1 vCPU/2GB, auto-scale 1–10 tasks |
| Primary Database | RDS PostgreSQL 17 | db.t4g.medium, Multi-AZ (prod), extensions: pgvector, pgcrypto, ltree, pg_trgm |
| Cache | ElastiCache Redis 7 | cache.t4g.small, single-node, TLS in-transit |
| Static Assets | S3 + CloudFront | Question images, PNG format, CloudFront CDN |
| Email | AWS SES | Transactional: verification, consent confirmation, results notification |
| Secret Storage | AWS Secrets Manager | Auth0 client secret, DB credentials, SES SMTP credentials |
| Frontend CDN | Vercel Edge Network | Next.js 15, Node.js 20 Edge runtime, automatic HTTPS |
| Auth | Auth0 | COPPA-compliant tenant, OAuth 2.0 Authorization Code flow, JWKS endpoint |

### 1.2 System Context & Data Flow

#### C4 Level 1 — System Context

```
┌─────────────────────────────────────────────────────────────┐
│                      EXTERNAL ACTORS                         │
│                                                              │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│   │  Parent   │    │ Student  │    │  Admin   │              │
│   │ (Browser) │    │(Browser) │    │(Browser) │              │
│   └────┬──────┘    └────┬─────┘    └────┬─────┘              │
│        │ HTTPS          │ HTTPS         │ HTTPS               │
└────────┼────────────────┼───────────────┼────────────────────┘
         ▼                ▼               ▼
┌─────────────────────────────────────────────────────────────┐
│               PADI.AI SYSTEM BOUNDARY               │
│                                                              │
│   Next.js 15 (Vercel) ──HTTPS/REST──▶ FastAPI (ECS)         │
│                                             │                │
│                              ┌──────────────┼──────────┐     │
│                              ▼              ▼          ▼     │
│                           Postgres       Redis     S3/CDN    │
│                           17 RDS      ElastiCache           │
└──────────────────┬──────────────────────────────────────────┘
                   │
     ┌─────────────┼────────────┐
     ▼             ▼            ▼
  Auth0         AWS SES      PostHog
 (Identity)    (Email)    (Analytics)
```

#### Data Flow 1 — Parent Registration & COPPA Consent

```
Step  Actor              Action                            Notes
────  ─────────────────  ────────────────────────────────  ────────────────────────
 1    Parent             Fills register form               email, password, name
 2    Next.js (CC)       Redirects → Auth0 Universal Login Auth0 authorize URL
 3    Auth0              Creates user, sends verification  Auth0 user record
 4    Auth0              Redirects with auth code          authorization_code
 5    Next.js API route  Exchanges code → tokens           access_token, id_token
 6    Next.js (CC)       POST /auth/register               { auth0Sub, email, name }
 7    FastAPI            INSERT INTO users                 email_encrypted, email_hash
 8    FastAPI            Returns { userId, needsConsent }
 9    Next.js (CC)       Redirects → /onboarding/consent
10    Parent             Reads policy, checks two boxes    consent form data
11    Next.js (CC)       POST /consent/initiate            { userId, consentData }
12    FastAPI            INSERT INTO consent_records       status='pending'
13    FastAPI            AWS SES: send confirmation email
14    Parent             Clicks confirmation link           token in URL
15    FastAPI            Validates HMAC token              expiry check
16    FastAPI            UPDATE consent_records            status='active'
17    FastAPI            INSERT INTO audit_log             consent_confirmed event
18    Next.js            Redirects → /onboarding/create-student
```

#### Data Flow 2 — Diagnostic Assessment Session

```
Step  Actor              Action                            Notes
────  ─────────────────  ────────────────────────────────  ────────────────────────
 1    Parent             POST /assessments                 { studentId, type:'diagnostic' }
 2    FastAPI            Validates ownership + consent
 3    FastAPI            INSERT INTO assessments           status='in_progress'
 4    FastAPI            SET Redis: assessment:{id}:state  initial CAT state, TTL 7d
 5    Browser (CC)       GET /assessments/{id}/next-question
 6    QSS               Identifies lowest-coverage standard
 7    QSS               Selects difficulty-2 question     first question per skill
 8    FastAPI            Returns { question: { id, stem, options, domain } }
 9    Student            Selects answer
10    Browser (CC)       POST /assessments/{id}/responses  { questionId, answer, timeMs }
11    FastAPI            Validates answer (server-side)
12    BKT Service        Updates P(mastered) for standard  forward algorithm
13    FastAPI            UPDATE Redis: CAT state           new difficulty, answered set
14    FastAPI            INSERT INTO assessment_responses   is_correct, time_taken
15    [Repeat steps 5–14 for ~38 remaining questions]
16    FastAPI            Detects completion (all standards covered, ≥35 questions)
17    FastAPI            Calculates per-skill accuracy
18    FastAPI            Classifies Below/On/Above Par
19    FastAPI            INSERT INTO student_skill_states   one row per standard
20    FastAPI            UPDATE assessments: status='completed'
21    FastAPI            Publishes diagnostic_completed     Redis Streams
22    FastAPI            AWS SES: results ready email
```

#### Data Flow 3 — Results Display

```
Step  Actor              Action                            Notes
────  ─────────────────  ────────────────────────────────  ────────────────────────
 1    Parent             Navigates to /diagnostic/results
 2    Next.js (SC)       RSC: GET /assessments/{id}/results
 3    FastAPI            Queries student_skill_states       joins standards table
 4    FastAPI            Queries assessment_responses       for accuracy stats
 5    FastAPI            Builds gap analysis (prereq graph)
 6    FastAPI            Returns results payload
 7    Next.js (SC)       Server-renders summary section     no client JS needed
 8    Next.js (CC)       Client: renders bar charts         Recharts / SVG
 9    Parent             Clicks "Download PDF"
10    FastAPI            Server-generates PDF (WeasyPrint)  < 10 seconds
11    FastAPI            Returns PDF stream
```

### 1.3 Key Architectural Decisions

#### ADR-001: Monorepo (pnpm workspaces + Turborepo)
**Decision:** Single repository for all TypeScript packages and Python services.
**Rationale:** Stage 1 has three separately deployable units (Next.js, FastAPI, BKT Engine) that share types, configuration, and migrations. A monorepo eliminates version drift between `packages/types/` and `apps/api/src/models/`, enables a single CI pipeline, and allows Turborepo to cache build artifacts across packages. The 5-stage development arc will add 4–6 more services; cross-service refactors are far simpler in a monorepo.
**Trade-off:** Larger clone size; mitigated by sparse checkout in CI. Python services opt-out of Turborepo task graph and use Makefile targets instead.

#### ADR-002: FastAPI over Django REST Framework
**Decision:** FastAPI 0.115+ with async SQLAlchemy 2.0 (asyncpg driver).
**Rationale:** The diagnostic assessment endpoint serves a tight latency budget (next-question < 500ms p95). Full async I/O from the HTTP layer through the ORM to PostgreSQL eliminates thread-pool blocking. FastAPI's native Pydantic v2 integration provides schema validation at zero extra cost. Django REST Framework's synchronous ORM would require `sync_to_async` wrappers and a thread pool, adding complexity and latency.
**Trade-off:** Less built-in admin interface; compensated by a custom `/admin` route group in Next.js for question management.

#### ADR-003: Auth0 for Authentication (COPPA-Compliant Tenant)
**Decision:** Auth0 handles all identity concerns; FastAPI validates JWTs via JWKS endpoint.
**Rationale:** COPPA compliance demands verifiable parental consent before any child data is collected. Auth0's COPPA-specific tenant configuration (disabled social logins for children, locked-down scopes, restricted data residency) reduces custom compliance work. Building equivalent functionality home-rolled (bcrypt storage, PKCE, JWKS rotation, MFA, breach detection) would take 4–6 weeks and require ongoing security maintenance.
**Trade-off:** Auth0 pricing increases with user count; acceptable for Stage 1 (≤1,000 MAU). Revisit at Stage 5 when billing is introduced.

#### ADR-004: pyBKT for Bayesian Knowledge Tracing
**Decision:** Use the `pyBKT` library (Python) for BKT parameter estimation and state updates.
**Rationale:** pyBKT is the reference implementation of Yudelson et al.'s BKT with EM training and Brute-Force/Conjugate-Gradient fitting. For Stage 1, default BKT parameters (P_L0, P_T, P_S, P_G) are seeded from educational research baselines and will be calibrated in Stage 3 once sufficient response data accumulates. pyBKT runs in-process within the FastAPI service (no separate service call), keeping the architecture simple.
**Dependency risk:** pyBKT is a research library with irregular releases. It is pinned (`pyBKT==1.4.1`) and vendored in `services/bkt-engine/`. Any upstream breaking change is caught by the weekly dependency audit workflow.

#### ADR-005: PostgreSQL 17 with pgvector + pgcrypto
**Decision:** Single PostgreSQL cluster with pgvector for Stage 2+ semantic search and pgcrypto for PII encryption.
**Rationale:** Stage 1 does not use vector similarity, but the `standards.description_embedding` column is provisioned now so the `ivfflat` index can be built with real data before Stage 2 needs it. Building the index on an empty column at Stage 2 launch avoids a blocking index-build on a live table. pgcrypto AES-256-CBC handles column-level encryption for `email_encrypted` and `name_encrypted`, keeping PII out of application logs and backups.
**Trade-off:** pgvector adds ~50MB to the pg extensions; negligible. The embedding column is NULL for all Stage 1 rows.

#### ADR-006: Redis for Assessment State (TTL-Based Checkpoint)
**Decision:** Assessment CAT state is double-written: to PostgreSQL (durable) and Redis (fast-read).
**Rationale:** The next-question endpoint must return in < 500ms p95. Loading and updating the full assessment state JSON from PostgreSQL on every question submission adds ~10–20ms of I/O. Redis serves the state from memory in < 1ms. PostgreSQL remains the system of record; Redis is invalidated on a 7-day TTL (assessment lifetime). If Redis is unavailable, the API falls back to PostgreSQL without client impact.
**Failure mode:** Redis ElastiCache single-node (Stage 1) has no automatic failover. On Redis outage, assessment state reads fall through to PostgreSQL. This degrades performance but does not cause data loss.

#### ADR-007: CAT Lite (1-Parameter Logistic) for Stage 1
**Decision:** Use simplified 1PL IRT (item difficulty only) for diagnostic CAT, deferring 3PL calibration to Stage 3.
**Rationale:** Full 3-parameter IRT requires response calibration data from ≥300 students per item. Stage 1 launches with zero historical data. A deterministic difficulty-ladder approach (correct → +1 difficulty, incorrect → −1) produces a serviceable adaptive experience without calibration data, and the responses collected in Stage 1 will feed Stage 3's full IRT calibration. Item `irt_difficulty` columns are seeded with expert estimates and treated as placeholders.

#### ADR-008: Vercel for Frontend Hosting
**Decision:** Next.js 15 deployed to Vercel Edge Network; no API calls routed through Next.js to avoid cold starts.
**Rationale:** Vercel provides zero-config Next.js deployment, automatic preview environments per PR, and global CDN distribution. The App Router's React Server Components (RSC) allow server-side data fetching with no client bundle overhead for static sections (standards list, completed results). The frontend does not run a BFF layer; all `/api/v1/*` calls go directly to the FastAPI service behind the ALB.
**Trade-off:** Vercel's free tier is insufficient for production; the Pro plan ($20/month) is required for teams and advanced analytics.

### 1.4 Integration Points

| Integration | Direction | Protocol | Auth | Stage 1 Usage |
|------------|-----------|----------|------|---------------|
| Auth0 | FastAPI ← Auth0 | HTTPS JWKS | RS256 JWT | Validate every authenticated request; webhook on user creation |
| Auth0 | Browser → Auth0 | HTTPS redirect | OAuth 2.0 PKCE | Register, login, Universal Login |
| AWS SES | FastAPI → SES | HTTPS AWS SDK v3 | IAM role | Verification email, consent confirmation, results notification |
| PostHog | Browser → PostHog | HTTPS SDK | API key (client-safe) | Page views, assessment start/complete, timing events |
| PostgreSQL 17 | FastAPI → RDS | TCP/TLS asyncpg | DB password (Secrets Manager) | All persistent data: users, students, assessments, standards, questions |
| Redis 7 | FastAPI → ElastiCache | TCP/TLS aioredis | AUTH token | Assessment CAT state, rate limit counters, session cache |
| S3 + CloudFront | FastAPI → S3 (write), Browser → CloudFront (read) | HTTPS | IAM role (write), signed URLs (read) | Question images for geometry questions (4.GM domain) |
| AWS Secrets Manager | FastAPI → Secrets Manager | HTTPS AWS SDK | IAM role | DB creds, Auth0 client secret, SES credentials |

**Integration points not yet active in Stage 1 (provisioned but dormant):**
- `services/bkt-engine/` standalone service — BKT logic runs in-process within FastAPI in Stage 1; standalone service is wired in Stage 3.
- `services/agent-engine/` — LangGraph agents are not invoked in Stage 1.
- Stripe — no payment integration until Stage 5.
- Redis Streams — `diagnostic_completed` event is published but no consumer exists until Stage 2's learning plan generator subscribes.

### 1.5 Risk Areas & Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| COPPA consent flow defect causes PII collection before consent | Low | Critical | Middleware-level guard on every authenticated endpoint checks `consent.status = 'active'` before permitting student data writes. E2E test suite covers the full consent funnel with negative paths. Zero-defect P0 surface. |
| BKT initial parameters miscalibrated, producing inaccurate proficiency classifications | Medium | High | Stage 1 uses conservative defaults (P_L0=0.1/0.4/0.75 based on diagnostic accuracy buckets). A 50-student pilot cohort validates agreement with teacher reports (≥85% target). P(mastered) displayed as classification bands, not raw values, reducing sensitivity to parameter error. |
| Question pool too small for full CAT coverage (pool exhaustion mid-assessment) | Medium | Medium | Minimum 3 validated questions per standard ensures 3-question stopping rule can always be satisfied. `select_next_question()` has explicit fallback cascade through adjacent difficulties. `QuestionPoolExhaustedError` triggers a graceful fallback: serve a difficulty-3 question from any remaining standard to maintain assessment flow. |
| Redis single-node outage during active assessment | Low | Medium | Double-write to PostgreSQL on every response. Redis read failure falls through to PostgreSQL via `async with timeout(50ms)` guard. Degraded performance (latency +15ms) but no data loss and no user-facing error. |
| KaTeX rendering failure on older iOS Safari | Medium | Medium | KaTeX 0.16 targets Safari 14+. CI browser matrix includes iOS Safari 16 (Playwright device emulation). LaTeX syntax is validated at question-import time against the KaTeX supported-commands list. Fallback: raw LaTeX text with a muted `[Math]` label if KaTeX fails to load. |
| Alembic migration failure in production (downtime) | Low | High | All migrations are transactional (single atomic `BEGIN … COMMIT`). Down-migrations always provided and tested. Blue-green deployment: migration runs before traffic is switched to new containers. Alembic is gated in the CI pipeline; failing migrations block deploy. |
| Auth0 service outage (login unavailable) | Very Low | High | 99.99% SLA from Auth0. Degraded-mode plan: freeze login, show maintenance page, no data loss possible since PII is at rest. No fallback auth provider in Stage 1 (cost/complexity vs. risk accepted). |
| Data breach involving children's PII (COPPA 72-hour notification) | Very Low | Critical | PII fields AES-256 encrypted at rest. No PII in logs. Network: VPC private subnets, security groups. SAST/DAST/SCA in every PR. Incident response runbook at `docs/runbooks/incident-response.md` defines the 72-hour FTC notification SLA. |

### 1.6 Performance & Scalability Considerations

#### Latency Targets and Budgets

| Endpoint | p50 Target | p95 Target | Method |
|---------|-----------|-----------|--------|
| `GET /assessments/{id}/next-question` | < 50ms | < 200ms | Redis cache hit; PostgreSQL fallback < 500ms |
| `POST /assessments/{id}/responses` | < 100ms | < 350ms | Async DB write + Redis update + BKT computation |
| `GET /assessments/{id}/results` | < 500ms | < 1500ms | Multi-table join on completion; results cached after first fetch |
| `GET /standards` | < 20ms | < 80ms | PostgreSQL read with CDN-cached response (1-hour TTL) |
| Assessment page initial load (Next.js) | < 800ms | < 2000ms | SSR + KaTeX bundle; question pre-fetched after load |
| PDF report generation | < 5s | < 10s | WeasyPrint server-side; no caching (fresh data required) |

#### Concurrency Model

- ECS Fargate auto-scales from 1 to 10 tasks based on CPU utilization (scale-out at 70%). Each task handles approximately 100 concurrent requests.
- PostgreSQL: PgBouncer connection pooler, pool size 100, transaction-mode pooling. RDS db.t4g.medium supports 170 max_connections; PgBouncer keeps actual connections at ≤100.
- Redis: Single-node ElastiCache cache.t4g.small (6.38GB memory). Assessment state average payload ≈ 8KB per session × 1,000 concurrent sessions = 8MB. Well within capacity.
- Pre-fetching: After question N is delivered, the browser fires a background `GET /assessments/{id}/next-question-preview` that loads question N+1 into the Zustand store. This makes the transition appear instantaneous (sub-100ms perceived latency).

#### Load Test Baseline (Month 3, Pre-Launch)

k6 scenario targeting 1,000 concurrent diagnostic sessions:
```
Target: 1,000 virtual users, each simulating a full 40-question diagnostic
Duration: 60 minutes
Ramp: 0 → 1,000 VUs over 10 minutes, hold 40 minutes, ramp down 10 minutes
Success criteria:
  - p95 response time < 500ms for /next-question
  - p95 response time < 500ms for /responses
  - Error rate < 0.1%
  - Zero HTTP 5xx responses
```

#### Database Scalability

- Stage 1 does not require read replicas for query load; one replica is provisioned for reporting queries (results display) to avoid read contention on the write primary.
- The `assessment_responses` table will have approximately 40 rows × 1,000 students = 40,000 rows at the end of Stage 1. This is negligible. Partitioning is not required until Stage 3 (1M+ rows expected).
- `standards` (38 rows) and `questions` (142+ rows) are tiny tables; all queries are index-scanned.

---

## 2. User Story Breakup

Stories are derived from PRD functional requirements FR-1 through FR-5. Priority levels: **P0** (must-ship for launch), **P1** (high importance, ship in Stage 1), **P2** (important, can slip to Month 3 buffer), **P3** (nice-to-have, defer if needed).

Story points use a modified Fibonacci scale: 1, 2, 3, 5, 8, 13.

---

### Epic 1: Parent Account & COPPA Compliance
**Source:** FR-1 | **Total Points:** 55

| ID | Title | Priority | Points |
|----|-------|----------|--------|
| US-1.1 | Parent email registration | P0 | 5 |
| US-1.2 | Email verification flow | P0 | 3 |
| US-1.3 | COPPA consent multi-step form | P0 | 13 |
| US-1.4 | Privacy policy versioning & re-acceptance | P1 | 5 |
| US-1.5 | Child profile creation | P0 | 5 |
| US-1.6 | Parent account dashboard | P0 | 5 |
| US-1.7 | Data deletion request (COPPA right-to-delete) | P0 | 8 |
| US-1.8 | Password policy enforcement & HIBP check | P1 | 3 |
| US-1.9 | Session management & token rotation | P0 | 5 |
| US-1.10 | Account lockout after failed attempts | P1 | 3 |

---

**US-1.1 — Parent Email Registration**

> As a **parent**, I want to **create an account with my email address and password** so that **I can access PADI.AI on behalf of my child**.

**Acceptance Criteria:**

1. Given I navigate to `/register`, when I submit a valid form (legal first name, last name, email, password ≥8 chars with uppercase, lowercase, digit, password confirmation matches), then I am redirected to an email verification holding screen and receive a verification email within 60 seconds.
2. Given I submit a duplicate email address, when the form is submitted, then I see the error: "An account with this email already exists. Sign in instead?" and the form is not submitted.
3. Given I submit a password shorter than 8 characters, when the form is submitted, then I see an inline validation error below the password field before the form is submitted to the server.
4. Given I submit the form, then the page clearly states (above the fold) "This service is for children under 13 and requires parental consent" before form submission.
5. Given the email verification link is not clicked within 24 hours, then the account status is `VERIFICATION_EXPIRED` and I can request a fresh link.
6. Given a valid form is submitted, then no password is stored in plaintext in any log, database field, or error message.
7. Given I am on a screen ≥320px wide, when the registration form renders, then all form fields and submit button are visible without horizontal scrolling.

**Dependencies:** Auth0 tenant configured; AWS SES verified sender domain.

---

**US-1.2 — Email Verification Flow**

> As a **parent**, I want to **verify my email address by clicking a link** so that **PADI.AI can confirm I control this email before storing any child data**.

**Acceptance Criteria:**

1. Given I click the verification link in my email, when the link is valid (not expired, not previously used), then my account status changes from `PENDING_VERIFICATION` to `ACTIVE` and I am redirected to the consent flow.
2. Given I click the verification link a second time after it has already been consumed, when I arrive at the verification endpoint, then I receive HTTP 410 and see a message: "This link has already been used. Need a new one?" with a resend option.
3. Given the link has expired (>24 hours), when I click it, then I see: "This link has expired. Request a new verification email." with a one-click resend.
4. Given I request a resend, when a new link is issued, then the previous link is immediately invalidated.
5. Given the verification link contains an invalid JWT (tampered or unsigned), when I access the endpoint, then HTTP 400 is returned and no account state change occurs.

**Dependencies:** US-1.1 complete; AWS SES configured.

---

**US-1.3 — COPPA Consent Multi-Step Form**

> As a **parent**, I want to **provide verifiable parental consent through a clearly explained, multi-step process** so that **my child can legally use PADI.AI and I understand exactly what data is collected and how it is used**.

**Acceptance Criteria:**

1. Given I have verified my email, when I navigate to `/onboarding/consent`, then I see a plain-language privacy summary above the full Privacy Policy and Terms of Service (which are linked and openable in-place).
2. Given the consent form is displayed, then I see two separate checkboxes: (a) "I have read and agree to the Privacy Policy" and (b) "I provide verifiable parental consent for my child to use PADI.AI." Neither checkbox is pre-checked.
3. Given I click "Submit Consent" without checking both boxes, when the form is validated, then I see an error: "Please check both boxes to continue." The form is not submitted.
4. Given I submit valid consent, when the consent is recorded, then a confirmation email is sent within 60 seconds informing me of a 24-hour revocation window.
5. Given the consent is recorded, then the `consent_records` table stores: consent_type, privacy_policy_version, tos_version, consented=true, consented_at (ISO 8601 UTC), ip_address_hash (SHA-256), user_agent, consent_text_hash (SHA-256 of shown text).
6. Given my consent is recorded, when an admin queries the audit log, then every state change to the consent record appears as an immutable audit entry.
7. Given I later request account deletion, when my account data is purged, then my `consent_records` row is NOT deleted (legal retention requirement).
8. Given the Privacy Policy is updated, when I next log in, then I am gated on a re-acceptance screen before accessing the dashboard.

**Dependencies:** US-1.1, US-1.2; privacy policy and ToS documents authored; AWS SES configured.

---

**US-1.4 — Privacy Policy Versioning & Re-Acceptance**

> As a **parent**, I want to **be notified and prompted when the Privacy Policy changes** so that **I can make an informed decision about continued use of PADI.AI**.

**Acceptance Criteria:**

1. Given a new policy version is published, when I log in, then I am redirected to a "Policy Update" screen before the dashboard loads.
2. Given the policy update screen, when I accept the new policy, then my `users.privacy_policy_version` is updated and I continue to the dashboard.
3. Given I decline to accept the updated policy, then I am logged out and my account is moved to `CONSENT_DECLINED` status, with an email sent explaining how to re-accept or delete my account.
4. Given the policy version in `consent_records` is audited, then the specific version string accepted at each consent event is queryable.

**Dependencies:** US-1.3 complete; policy version management in configuration.

---

**US-1.5 — Child Profile Creation**

> As a **parent**, I want to **create a profile for my child** so that **PADI.AI can track their diagnostic results and future learning progress separately from my account**.

**Acceptance Criteria:**

1. Given I have completed consent, when I submit the child profile form with a display name (1–50 chars, no SQL injection/XSS chars) and grade level (pre-set Grade 4), then a `students` record is created with a UUIDv4 `id` and I am redirected to the parent dashboard.
2. Given I attempt to create more than 5 child profiles under one account, when I click "Add Child," then I see: "You've reached the limit of 5 child profiles per account."
3. Given I enter a display name that contains special characters (`<`, `>`, `"`, `'`, `;`), when the form is submitted, then the server sanitizes these characters and stores the cleaned name; no XSS payload is executable.
4. Given the child profile is created, then `display_name` is the only name-like field stored in the `students` table; no last name or full name is stored.
5. Given the child profile is created, then I can select an avatar from 12 pre-built options; no image upload is permitted.
6. Given I enter the child's birth month and year, when the profile is saved, then the raw date is not stored; only the computed grade appropriateness flag is retained.

**Dependencies:** US-1.3 complete.

---

**US-1.6 — Parent Account Dashboard**

> As a **parent**, I want to **see all my children's diagnostic statuses at a glance** so that **I can quickly identify which children have completed or need to start the diagnostic**.

**Acceptance Criteria:**

1. Given I am logged in with active consent and have created at least one child profile, when I navigate to `/dashboard`, then I see a card for each child showing: display name, avatar, grade, diagnostic status (Not Started / In Progress / Completed), and last-updated date.
2. Given a child's diagnostic status is "Completed," when I click "View Full Report," then I navigate to the results screen for that child's most recent assessment.
3. Given a child's diagnostic status is "Not Started," when I click "Start Diagnostic," then I navigate to the assessment launcher for that child.
4. Given a child's diagnostic status is "In Progress," when the card renders, then a "Continue" button is shown (not "Start Diagnostic").
5. Given there are no children on my account, when I access the dashboard, then I see an onboarding prompt: "Let's set up your first child's profile."
6. Given my notification badge shows unread results, when I view the dashboard, then the badge count decrements as I view each child's results.

**Dependencies:** US-1.5 complete.

---

**US-1.7 — Data Deletion Request (COPPA Right-to-Delete)**

> As a **parent**, I want to **permanently delete my account and all associated child data** so that **I can exercise my COPPA data rights and remove my family's information from PADI.AI**.

**Acceptance Criteria:**

1. Given I am on the Account Settings page, when I click "Delete My Account," then I see a confirmation dialog requiring me to type "DELETE" in a text field and re-enter my password before proceeding.
2. Given I confirm the deletion, when the request is processed, then: all child profiles are marked `is_active = FALSE`, all assessment responses queued for deletion within 30 days, and I receive a confirmation email with a deletion reference number within 5 minutes.
3. Given the deletion is confirmed, then consent records are NOT deleted; only the `parent_id` reference is nulled out (legal retention requirement).
4. Given I request deletion of a single child's data, when the request is processed, then only that child's `students` row and related assessments, responses, and skill states are queued for deletion; other children's data is unaffected.
5. Given my account is deleted, when a support staff member queries the audit log, then all deletion events are visible in the immutable audit trail.
6. Given I request a data export before deletion, when the export is generated, then I receive a ZIP file containing: diagnostic results (JSON), skill states (JSON), and a PDF summary.

**Dependencies:** US-1.6; audit log infrastructure; SES email.

---

**US-1.8 — Password Policy & HIBP Check**

> As a **parent**, I want to **be warned if my chosen password appears in known data breaches** so that **I can select a more secure password to protect my account**.

**Acceptance Criteria:**

1. Given I enter a password during registration, when the password is submitted, then the server checks the HaveIBeenPwned API using the k-anonymity model (first 5 characters of SHA-1 hash).
2. Given my password appears in the HIBP database, when the check completes, then I see a warning: "This password has appeared in a known data breach. We recommend choosing a different password." Account creation is NOT blocked.
3. Given the HIBP API is unreachable, when the check times out (>1 second), then registration proceeds normally; the HIBP check is non-blocking.
4. Given a password is submitted, then the plaintext password is never sent to the HIBP API (only the SHA-1 hash prefix is sent).

**Dependencies:** US-1.1; HIBP API access.

---

**US-1.9 — Session Management & Token Rotation**

> As a **parent**, I want to **my session to remain secure and automatically refresh** so that **I do not need to log in repeatedly during normal use while my session cannot be hijacked from a stolen token**.

**Acceptance Criteria:**

1. Given I am logged in, when my JWT access token expires (15-minute TTL), then a new access token is transparently issued using my refresh token without requiring re-login.
2. Given a refresh token is used, when a new access token is issued, then the previous refresh token is immediately invalidated (refresh token rotation).
3. Given I log out explicitly, when my session ends, then all active refresh tokens for my account are invalidated in Redis.
4. Given I have been inactive for 30 minutes (parent session), when I attempt an API call, then I am redirected to the login page.
5. Given my child is taking the diagnostic, when the student session token is issued, then it is scoped only to the assessment flow and cannot access account settings, billing, or other children's data.
6. Given a student assessment session is active, when the session is inactive for 60 minutes, then the session expires but assessment state is preserved in PostgreSQL for resumption on next login.

**Dependencies:** US-1.1; Auth0 configured with 15-minute access token TTL.

---

**US-1.10 — Account Lockout After Failed Attempts**

> As a **platform operator**, I want to **temporarily lock accounts after repeated failed login attempts** so that **brute-force credential attacks are mitigated**.

**Acceptance Criteria:**

1. Given a parent account exists, when 5 consecutive failed login attempts occur (incorrect password), then the account is locked for 15 minutes and I receive an email notification.
2. Given the account is locked, when I attempt to log in during the lockout window, then I see: "Your account is temporarily locked. Please try again in X minutes or reset your password."
3. Given the lockout window expires, when I attempt to log in with the correct password, then the lock is lifted and I am logged in.
4. Given I request an email-based account unlock, when the email is sent, then it contains a one-time unlock link (valid 30 minutes).
5. Given rate limiting is enabled, when more than 100 API requests per minute arrive from a single IP, then HTTP 429 is returned for all subsequent requests until the window resets.

**Dependencies:** US-1.1; Redis for rate limit counters.

---

### Epic 2: Oregon Standards Database
**Source:** FR-2 | **Total Points:** 34

| ID | Title | Priority | Points |
|----|-------|----------|--------|
| US-2.1 | Standards schema and seed data (38 standards) | P0 | 8 |
| US-2.2 | Prerequisite relationship graph | P0 | 5 |
| US-2.3 | Standards API endpoints | P0 | 3 |
| US-2.4 | Full-text search and filtering | P1 | 5 |
| US-2.5 | Admin standards editor with two-person approval | P1 | 8 |
| US-2.6 | Standards versioning and audit log | P1 | 5 |

---

**US-2.1 — Standards Schema and Seed Data**

> As a **developer**, I want to **the complete Oregon Grade 4 and Grade 3 prerequisite math standards seeded into the database** so that **the diagnostic engine has an accurate, authoritative reference for all 38 standards**.

**Acceptance Criteria:**

1. Given the Alembic migration runs against a fresh PostgreSQL 17 instance, when `alembic upgrade head` completes, then the `standards` table contains exactly 29 Grade 4 standards and 9 Grade 3 prerequisite standards.
2. Given the standards are seeded, then each row contains a non-null value for: code (unique, format `[grade].[domain].[cluster].[number]`), domain, cluster, description (≥50 characters), dok_level (1–4), grade_level, and is_active=true.
3. Given I query `SELECT code FROM standards WHERE grade_level = 4 AND is_active = TRUE`, when the result returns, then all 29 codes from FR-2.2 are present and no additional codes exist.
4. Given I query `SELECT code FROM standards WHERE grade_level = 3 AND is_active = TRUE`, when the result returns, then all 9 codes from FR-2.3 are present.
5. Given the `standards` table is queried for DOK level distribution, then at least: 5 standards at DOK 1, 20 standards at DOK 2, 5 standards at DOK 3.

**Dependencies:** PostgreSQL 17 provisioned; pgcrypto, pgvector extensions enabled.

---

**US-2.2 — Prerequisite Relationship Graph**

> As a **diagnostic engine**, I want to **the prerequisite dependency relationships between standards to be modeled as a directed graph** so that **the CAT engine can sequence questions in a prerequisite-first order and the results display can prioritize foundational gaps**.

**Acceptance Criteria:**

1. Given the prerequisite seed migration runs, when I query `SELECT COUNT(*) FROM prerequisite_relationships`, then I get at least 22 rows matching the edges defined in FR-2.4.
2. Given I query prerequisites for `4.OA.A.1`, when the result returns, then `3.OA.C.7` appears as a prerequisite.
3. Given I query prerequisites for `4.NF.A.2`, when the result returns, then both `4.NF.A.1` and `3.NF.A.3` appear as prerequisites.
4. Given the graph is traversed using a topological sort, when starting from any Grade 4 standard, then no cycle is detected.
5. Given the `GET /standards/prerequisites/{code}` API is called with code `4.NBT.B.5`, then the response includes `3.OA.C.7` and `3.NBT.A.3`.

**Dependencies:** US-2.1 complete.

---

**US-2.3 — Standards API Endpoints**

> As a **frontend developer**, I want to **access Oregon math standards via a typed REST API** so that **the diagnostic engine and admin UI can query standards by grade, domain, and code without hardcoded data**.

**Acceptance Criteria:**

1. `GET /api/v1/standards` returns HTTP 200 with a JSON array of all active standards, each containing: id, code, domain, cluster, description, dok_level, grade_level, is_active.
2. `GET /api/v1/standards?grade=4&domain=4.NF` returns only the 7 Grade 4 NF standards.
3. `GET /api/v1/standards/{code}` with code `4.OA.A.1` returns the single standard object or HTTP 404 for unknown codes.
4. `GET /api/v1/standards/prerequisites/{code}` returns the direct prerequisites for a given standard code.
5. All endpoints return responses within 100ms p95 on a warm instance.
6. Unauthenticated requests to standards endpoints return HTTP 401.

**Dependencies:** US-2.1, US-2.2 complete.

---

**US-2.4 — Full-Text Search and Filtering**

> As an **admin**, I want to **search and filter standards by keyword, domain, and DOK level** so that **I can quickly locate specific standards when managing the question bank**.

**Acceptance Criteria:**

1. Given I call `GET /api/v1/standards?q=fraction+equivalence`, when the results return, then all standards whose `description` or `title` contains "fraction" and "equivalence" are returned (PostgreSQL `tsvector` full-text search).
2. Given I call `GET /api/v1/standards?dok_level=3`, when the results return, then only standards with `dok_level = 3` are included.
3. Given I call `GET /api/v1/standards?is_prerequisite=true`, when the results return, then only the 9 Grade 3 prerequisite standards are included.
4. Given I call `GET /api/v1/standards?include_inactive=true`, when the results return, then both active and inactive standards are included.
5. The full-text search uses a GIN index on `to_tsvector('english', description || ' ' || title)` for sub-50ms query times.

**Dependencies:** US-2.3 complete.

---

**US-2.5 — Admin Standards Editor**

> As an **admin**, I want to **edit standards in a web interface with a two-person approval rule** so that **no single administrator can unilaterally alter an educational standard that affects all student diagnostics**.

**Acceptance Criteria:**

1. Given I am logged in as an admin, when I access `/admin/standards`, then I see a list of all standards with columns: code, domain, grade, DOK level, active status, last modified.
2. Given I click "Edit" on a standard, when I modify the description and click "Save Draft," then the change is saved as a pending edit requiring a second admin's approval.
3. Given a second admin reviews and approves the pending edit, when the approval is confirmed, then the `standards` row is updated and an audit log entry records: changed_by, change_type=UPDATE, old_values (JSONB), new_values (JSONB), change_reason.
4. Given I attempt to approve my own edit, when I click "Approve," then I see: "You cannot approve your own edit." and the action is blocked.
5. Given I deactivate a standard, when `is_active` is set to FALSE, then the standard disappears from all student-facing queries but remains in the database with its historical data intact.

**Dependencies:** US-2.3; admin role configured in Auth0.

---

**US-2.6 — Standards Versioning & Audit Log**

> As a **compliance officer**, I want to **standards changes to be immutably recorded with full before/after state** so that **I can reconstruct the exact standard text that was in use during any diagnostic session**.

**Acceptance Criteria:**

1. Given any INSERT, UPDATE, or DELETE on the `standards` table, when the operation completes, then a row is inserted into `standards_audit_log` with: standard_id, changed_by, change_type, old_values, new_values, changed_at, change_reason.
2. Given I query the audit log for a standard's history, when results return, then I can reconstruct the full state of that standard at any point in time.
3. Given a new Oregon standards revision is published (e.g., `OAS-2025`), when new standard rows are inserted with the new `version_tag`, then old rows remain with their original `version_tag` and `is_active = FALSE`.
4. Given I attempt to delete an audit log entry, when the delete is attempted by any admin, then it is rejected (the audit log table has no DELETE privilege for any application role).

**Dependencies:** US-2.5; audit trigger function deployed.

---

### Epic 3: Seed Question Bank
**Source:** FR-3 | **Total Points:** 47

| ID | Title | Priority | Points |
|----|-------|----------|--------|
| US-3.1 | Question schema and seed import | P0 | 8 |
| US-3.2 | Multiple choice answer validation | P0 | 5 |
| US-3.3 | Numeric and fraction answer validation | P0 | 5 |
| US-3.4 | KaTeX math rendering in questions | P0 | 5 |
| US-3.5 | Question image support (S3/CloudFront) | P1 | 5 |
| US-3.6 | Admin question management UI | P1 | 8 |
| US-3.7 | Human review workflow | P0 | 5 |
| US-3.8 | Bulk import via JSON | P1 | 6 |

---

**US-3.1 — Question Schema and Seed Import**

> As a **diagnostic engine**, I want to **at least 142 validated questions seeded in the database (5 per Grade 3 standard, 3 per Grade 4 standard plus buffer)** so that **the CAT algorithm always has a non-empty question pool for every assessed standard**.

**Acceptance Criteria:**

1. Given the seed import script runs, when `SELECT COUNT(*) FROM questions WHERE status = 'active'` is executed, then the count is ≥ 142.
2. Given the seed is complete, when `SELECT standard_code, COUNT(*) FROM questions WHERE status = 'active' GROUP BY standard_code`, then every standard code in the `standards` table has ≥ 3 associated questions; every Grade 3 prerequisite standard has ≥ 5 associated questions.
3. Given the seed is complete, when the difficulty distribution is queried per standard, then at least 1 question at difficulty 2, 1 at difficulty 3, and 1 at difficulty 4 exists per standard with ≥ 3 questions.
4. Given a question row is inspected, then `correct_answer` is a non-null value that validates correctly against its `question_type` constraints (MC: option key `A`–`D`; numeric: parseable number string).
5. Given `SELECT COUNT(*) FROM questions WHERE status = 'active' AND standard_code IS NOT NULL` and `SELECT COUNT(*) FROM questions WHERE status = 'active' AND standard_code NOT IN (SELECT code FROM standards)`, then the second query returns 0 (no orphaned questions).

**Dependencies:** US-2.1 complete; question content authored and reviewed.

---

**US-3.2 — Multiple Choice Answer Validation**

> As a **student taking the diagnostic**, I want to **multiple choice questions to tell me if I was right or wrong accurately** so that **my proficiency assessment reflects my actual knowledge, not answer validation bugs**.

**Acceptance Criteria:**

1. Given I submit answer `"B"` for a multiple-choice question where option B is correct, when the server validates the response, then `is_correct = TRUE` is stored.
2. Given I submit answer `"A"` for a multiple-choice question where option B is correct, when the server validates the response, then `is_correct = FALSE` is stored.
3. Given answer options are displayed to the student, when the question card renders, then the order is randomized using the seed `assessment_id + question_id` (deterministic for replay/review).
4. Given the correct answer is never sent to the browser before submission, when I inspect the network response for `GET /next-question`, then the `correct_answer` field is absent from the response payload.
5. Given a multiple-choice question has exactly 4 options (A, B, C, D), when I inspect `questions.options`, then the JSONB array has exactly 4 elements with `is_correct = true` on exactly one.

**Dependencies:** US-3.1 complete.

---

**US-3.3 — Numeric and Fraction Answer Validation**

> As a **student**, I want to **numeric and fraction answers to accept equivalent forms** so that **I am not marked wrong for writing `1/2` instead of `0.5` when both represent the same value**.

**Acceptance Criteria:**

1. Given the correct answer is `"1/2"` and I submit `"2/4"`, when the server validates using fraction reduction, then `is_correct = TRUE`.
2. Given the correct answer is `"3.75"` and I submit `"3.750"`, when validated with `numeric_tolerance = 0.001`, then `is_correct = TRUE`.
3. Given the correct answer is `"1.5"` and I submit `"3/2"`, when both are in `correct_answer_alt`, then `is_correct = TRUE`.
4. Given I submit a numeric answer with leading zeros (e.g., `"007"`), when normalized, then the comparison treats it as `7`.
5. Given the correct answer is a whole number and I submit a decimal representation (e.g., `"4.0"` for `"4"`), when validated, then `is_correct = TRUE`.
6. Given I submit text in a numeric field (e.g., `"abc"`), when the server validates, then HTTP 422 is returned with a validation error and the response is not stored.

**Dependencies:** US-3.1 complete.

---

**US-3.4 — KaTeX Math Rendering**

> As a **student**, I want to **mathematical expressions to render as properly formatted math** so that **I can read fractions, multiplication symbols, and equations clearly without confusion**.

**Acceptance Criteria:**

1. Given a question `stem` contains KaTeX markup `\(\frac{3}{4}\)`, when the question card renders in the browser, then a visually formatted fraction (3 over 4) is displayed, not raw LaTeX text.
2. Given KaTeX renders, then the render is synchronous — no flash of unrendered LaTeX text during question display.
3. Given a math expression has a screen reader aria-label (e.g., `aria-label="3 fourths"`), when NVDA reads the question aloud, then the aria-label text is spoken, not the LaTeX markup.
4. Given KaTeX renders on iOS Safari 16, Chrome 114, and Firefox 115 (tested in Playwright browser matrix), then all three produce visually identical output with no missing symbols.
5. Given a KaTeX expression is malformed (e.g., unclosed `\frac`), when the question import runs, then a validation error is thrown and the question is NOT imported.

**Dependencies:** US-3.1; `packages/math-renderer/` built.

---

**US-3.5 — Question Image Support**

> As a **student**, I want to **geometry questions to display clear, labeled diagrams** so that **I can interpret angle, shape, and symmetry questions without needing to visualize abstractions mentally**.

**Acceptance Criteria:**

1. Given a question has `has_image = TRUE`, when the question card renders, then the image is loaded from CloudFront CDN within 1 second on a 10Mbps connection.
2. Given a question image fails to load (CloudFront 5xx), when the broken image handler fires, then a fallback message "Diagram unavailable — ask your teacher for help" is shown; the question can still be answered.
3. Given a question image is stored, then: PNG format, minimum 800×600px, maximum 1200×900px, white background, ≤500KB.
4. Given all 4.GM.C.7 (protractor) questions, 4.GM.A.3 (symmetry) questions, and 4.GM.A.1 (angle/line identification) questions are seeded, then each has a non-null `stem_image_url`.
5. Given an image is uploaded, then a descriptive alt text is stored in the database and rendered on the `<img>` element.

**Dependencies:** US-3.1; S3 bucket and CloudFront distribution provisioned.

---

**US-3.6 — Admin Question Management UI**

> As an **admin**, I want to **manage questions through a web interface with filtering, preview, and bulk actions** so that **I can efficiently review and maintain question quality without direct database access**.

**Acceptance Criteria:**

1. Given I navigate to `/admin/questions`, then I see a paginated table (50/page) with columns: standard_code, difficulty, question_type, validation_status, avg_correct_rate, times_used, last_modified.
2. Given I filter by `standard_code = "4.NF.A.1"`, when the filter is applied, then only questions for standard 4.NF.A.1 are shown.
3. Given I click "Preview" on a question, when the preview modal opens, then KaTeX math in the stem and options is rendered exactly as students see it.
4. Given a question has `avg_correct_rate > 0.92` or `avg_correct_rate < 0.25`, when it appears in the question list, then it has a yellow flag icon indicating it needs review.
5. Given I select 5 questions using checkboxes, when I choose "Deactivate Selected" from the bulk actions menu, then all 5 questions have `status = 'retired'` and disappear from student-facing queries.

**Dependencies:** US-3.1; admin auth configured.

---

**US-3.7 — Human Review Workflow**

> As a **content reviewer (Oregon-licensed math teacher)**, I want to **approve or reject questions through the admin interface** so that **only mathematically accurate, grade-appropriate, bias-free questions reach students**.

**Acceptance Criteria:**

1. Given a new question is imported with `status = 'draft'`, then it appears in the "Pending Review" queue in the admin interface.
2. Given I open a pending question for review, when I check: grade-appropriateness, mathematical accuracy, standard alignment, distractor quality, language clarity, and absence of bias — and approve, then `status` is set to `'active'`, `validated_by` is set to my admin name, and `validation_date` is set to today.
3. Given I reject a question and enter a rejection reason (required, ≥20 characters), when the rejection is saved, then the question remains in `status = 'draft'` with the rejection note stored.
4. Given `SELECT COUNT(*) FROM questions WHERE status = 'draft'` at launch, then the count is 0 — all seed questions must be validated before launch.
5. Given I attempt to use an unvalidated question in the diagnostic, when the question selection service runs, then `WHERE status = 'active'` filters prevent `status = 'draft'` questions from being served.

**Dependencies:** US-3.6 complete.

---

**US-3.8 — Bulk Import via JSON**

> As a **content team member**, I want to **import questions in bulk via a structured JSON file** so that **I can add large batches of questions without manually entering each one through the admin UI**.

**Acceptance Criteria:**

1. Given I POST a valid JSON payload to `/api/v1/admin/questions/import`, when all questions pass validation, then all are inserted in a single transaction and the response includes `{ inserted: N, failed: 0 }`.
2. Given I POST a JSON payload where one question has an invalid `question_type`, when validation runs, then NO questions are inserted (all-or-nothing transaction) and the response includes the line-by-line error: `{ "line": 7, "field": "question_type", "error": "must be one of: multiple_choice, numeric_input, drag_drop" }`.
3. Given I POST a question referencing a `standard_code` not in the `standards` table, when validation runs, then a foreign key error is returned for that specific line.
4. Given I POST a question without a `correct_answer` field, when validation runs, then a validation error is returned: `{ "field": "correct_answer", "error": "required" }`.
5. Given a successful import, then all imported questions have `status = 'draft'` (not `'active'`) until reviewed.

**Dependencies:** US-3.7; admin auth.

---

### Epic 4: Diagnostic Assessment Engine
**Source:** FR-4 | **Total Points:** 63

| ID | Title | Priority | Points |
|----|-------|----------|--------|
| US-4.1 | Assessment session creation | P0 | 5 |
| US-4.2 | CAT question selection algorithm | P0 | 13 |
| US-4.3 | Answer submission and response recording | P0 | 5 |
| US-4.4 | BKT state initialization from diagnostic | P0 | 8 |
| US-4.5 | Pause and resume assessment | P0 | 8 |
| US-4.6 | Question display UI (accessibility, KaTeX, progress) | P0 | 8 |
| US-4.7 | Assessment completion and scoring | P0 | 8 |
| US-4.8 | Anti-gaming measures | P1 | 5 |
| US-4.9 | Completion screen and parent notification | P1 | 3 |

---

**US-4.1 — Assessment Session Creation**

> As a **parent**, I want to **start a diagnostic assessment for my child with one click** so that **my child can begin being assessed without technical setup**.

**Acceptance Criteria:**

1. Given I am logged in with active consent and a child profile exists, when I click "Start Diagnostic" for a child with status `NOT_STARTED`, then `POST /assessments` creates an assessment record with `status = 'in_progress'` and I am redirected to `/diagnostic/{sessionId}`.
2. Given a child already has an assessment with `status = 'in_progress'`, when I click the dashboard, then a "Continue" button is shown instead of "Start Diagnostic."
3. Given I click "Continue," when the session resumes, then the question displayed is the next unanswered question (not the first question from scratch).
4. Given the assessment is created, when Redis is checked, then `assessment:{id}:state` key exists with the initial CAT state payload and a 7-day TTL.
5. Given I attempt to start a diagnostic for a child that does not belong to my account, when the API validates ownership, then HTTP 403 is returned.

**Dependencies:** US-1.5, US-3.7 complete.

---

**US-4.2 — CAT Question Selection Algorithm**

> As a **student**, I want to **the assessment to adapt the difficulty of questions based on my answers** so that **the assessment is neither too easy (boring) nor too hard (discouraging) and accurately reflects my knowledge level**.

**Acceptance Criteria:**

1. Given the first question for any standard is served, then it has `difficulty = 2` (the CAT starting point).
2. Given I answer a difficulty-2 question correctly, when the next question for that standard is selected, then it has `difficulty = 3` (or the maximum available at difficulty 3, falling back to 4 or 2 if none exists at 3).
3. Given I answer a difficulty-3 question incorrectly, when the next question for that standard is selected, then it has `difficulty = 2` (capped at floor 1).
4. Given 3 questions have been served for a standard and all 3 were answered correctly, when the termination condition is evaluated, then no further questions are served for that standard (`done = TRUE` in skill state).
5. Given a standard has no questions at the target difficulty, when the selection service runs, then the fallback cascade `[difficulty+1, difficulty-1, 3, 2, 4, 1]` is tried in order until a valid question is found.
6. Given `QuestionPoolExhaustedError` is raised (no questions found after all fallbacks), when the error is caught, then the student receives a question from any other unfinished standard (graceful degradation; assessment continues).
7. Given all standards are complete and the assessment has ≥ 35 questions served, when the next question is requested, then the assessment is marked complete.

**Dependencies:** US-4.1, US-3.7 complete.

---

**US-4.3 — Answer Submission and Response Recording**

> As a **student**, I want to **submit my answer to each question and have it recorded accurately** so that **my diagnostic results reflect what I actually answered**.

**Acceptance Criteria:**

1. Given I submit answer `"B"` to a multiple-choice question, when `POST /assessments/{id}/responses` is called, then the response is stored in `assessment_responses` with: question_id, answer_given=`"B"`, is_correct (boolean), time_taken_seconds, difficulty_at_time.
2. Given I submit an answer, then the `correct_answer` from the questions table is never included in the HTTP response body returned to the browser.
3. Given I submit an answer, then the assessment CAT state in Redis is updated atomically (using a Redis transaction or MULTI/EXEC) before the HTTP response is returned.
4. Given a network timeout occurs during submission, when I retry the same answer submission with the same `question_id`, then the server is idempotent — no duplicate response is stored.
5. Given all answers are submitted, when `SELECT COUNT(*) FROM assessment_responses WHERE assessment_id = :id` is queried, then the count matches the number of questions in `assessments.state_snapshot.questions_served`.

**Dependencies:** US-4.2 complete.

---

**US-4.4 — BKT State Initialization from Diagnostic**

> As a **learning plan engine (Stage 2)**, I want to **each student's BKT skill state to be initialized from their diagnostic results** so that **the learning plan is seeded with accurate mastery probabilities rather than uninformed priors**.

**Acceptance Criteria:**

1. Given a diagnostic completes and skill accuracy for `3.OA.C.7` is 0.33 (1/3 correct), when BKT initialization runs, then `p_l0 = 0.10` is stored in `student_skill_states` for that standard.
2. Given a diagnostic completes and skill accuracy for `4.NBT.B.5` is 0.67 (2/3 correct), when BKT initialization runs, then `p_l0 = 0.40` (on-par threshold) is stored.
3. Given a diagnostic completes and skill accuracy for `3.NF.A.1` is 1.00 (all correct), when BKT initialization runs, then `p_l0 = 0.75` is stored.
4. Given a standard was assessed with only 1 question (pool exhaustion), when the skill state is written, then `low_confidence = TRUE` is flagged in the `student_skill_states` record.
5. Given BKT initialization completes, when `SELECT COUNT(*) FROM student_skill_states WHERE assessment_id = :id`, then the count equals the number of unique standards assessed.
6. Given BKT initialization completes, then `p_t = 0.10`, `p_s = 0.10`, `p_g = 0.20` (Stage 1 defaults) are stored for all skills (calibration happens in Stage 3).

**Dependencies:** US-4.3 complete; `services/bkt-engine/` integrated.

---

**US-4.5 — Pause and Resume Assessment**

> As a **student (or parent on behalf)**, I want to **pause the diagnostic and resume later without losing progress** so that **a bathroom break, meal, or end-of-day interruption does not require restarting the full assessment**.

**Acceptance Criteria:**

1. Given I click "Save and continue later" during an active assessment, when the action is confirmed, then: the current state is checkpointed to PostgreSQL (`assessments.state_snapshot` updated), the student is shown a "See you later!" screen, and the parent dashboard shows "In Progress."
2. Given I close the browser tab mid-assessment without clicking "Save," when I return and log in, then the parent dashboard shows "In Progress" with a "Continue" button and the assessment resumes from the last submitted response.
3. Given I resume an assessment, when the session rehydrates, then the first question served is the next unfinished standard's first unanswered question — not question 1.
4. Given the session expired from inactivity (>60 minutes), when I return, then the state is restored from PostgreSQL (Redis TTL may have expired but PostgreSQL is always the durable fallback).
5. Given the assessment state checkpoint, when the `state_snapshot` JSONB is parsed, then it contains: current_question_index, all questions_served IDs, all responses with is_correct and time_taken, and skill_states per standard.

**Dependencies:** US-4.3 complete.

---

**US-4.6 — Question Display UI (Accessibility, KaTeX, Progress)**

> As a **student**, I want to **questions to be clearly displayed with large text, visual progress, and full keyboard navigability** so that **I can focus on the math rather than the interface**.

**Acceptance Criteria:**

1. Given a question card is displayed, then question text is ≥ 18px, answer option text is ≥ 16px, and all interactive tap targets are ≥ 48×48px.
2. Given the student is on question 15 of an approximately 40-question assessment, when the progress bar renders, then it shows approximately 37.5% filled with label "Question 15 of ~40."
3. Given the student is on question 15, when the domain progress indicator renders, then each domain icon is shown with fill proportional to how many questions from that domain have been answered.
4. Given the student has been on a question for > 3 minutes without interaction, when the timer triggers, then a gentle overlay message appears: "Take your time! When you're ready, tap an answer to continue."
5. Given all answer inputs, when tested with keyboard navigation, then Tab moves between answer options, arrow keys select within a group, and Enter confirms selection.
6. Given the high-contrast mode toggle is activated, when the assessment renders, then the color scheme meets WCAG 2.1 AAA (black background, white text, yellow highlights).
7. Given `prefers-reduced-motion` is set in the OS, when question transitions and the confetti completion animation render, then all motion is suppressed.

**Dependencies:** US-4.1, US-3.4 complete.

---

**US-4.7 — Assessment Completion and Scoring**

> As a **system**, I want to **accurately compute per-skill accuracy, classify proficiency levels, and trigger downstream events upon diagnostic completion** so that **the results display and future Stage 2 learning plan generation receive correct inputs**.

**Acceptance Criteria:**

1. Given all standards have been assessed and ≥ 35 questions served, when the final response is submitted, then `POST /assessments/{id}/complete` runs the scoring pipeline within 2 seconds.
2. Given scoring runs, when a standard has 3/3 correct responses, then accuracy = 1.0, classification = `'Above Par'`, and `p_l0 = 0.75` is initialized.
3. Given scoring runs, when a standard has 1/3 correct responses, then accuracy = 0.33, classification = `'Below Par'`, and `p_l0 = 0.10` is initialized.
4. Given the overall proficiency level is computed, when it is the mode of per-skill classifications with ties broken conservatively (Below Par > On Par > Above Par), then the computed level matches the expected level for a test fixture with known responses.
5. Given the assessment is complete, when Redis Streams is checked, then a `diagnostic_completed` event with `{ assessment_id, student_id, overall_level }` has been published.
6. Given the assessment is complete, when the parent's email account is checked, then a "Results are ready" notification email is delivered within 5 minutes.

**Dependencies:** US-4.4 complete; AWS SES configured; Redis Streams configured.

---

**US-4.8 — Anti-Gaming Measures**

> As a **platform operator**, I want to **detect and flag suspicious answer patterns** so that **diagnostic results reflect genuine knowledge rather than click-through responses**.

**Acceptance Criteria:**

1. Given a student answers all questions in under 5 seconds each (total session time < 3 minutes for 40 questions), when the assessment completes, then `assessments.flagged_for_review = TRUE` is set.
2. Given back-navigation is attempted (browser back button or keyboard shortcut), when the assessment page intercepts the event, then back navigation is prevented and a modal asks: "Are you sure you want to leave? Your progress will be saved."
3. Given a student navigates away during the assessment, when the session ends, then no ability to view correct answers before the assessment resumes exists (assessment state contains only submitted responses, not upcoming questions).
4. Given the server receives an answer submission, when `is_correct` is computed, then it is computed server-side from the database; the client-submitted `is_correct` field (if present) is ignored.
5. Given session tokens are scoped to a single assessment, when I attempt to use a student session token to call a parent account endpoint, then HTTP 403 is returned.

**Dependencies:** US-4.3 complete.

---

**US-4.9 — Completion Screen and Parent Notification**

> As a **student**, I want to **see a celebratory completion screen after finishing the diagnostic** so that **I feel rewarded for completing the assessment and motivated to continue with PADI.AI**.

**Acceptance Criteria:**

1. Given the final answer is submitted and scoring completes, when the completion screen renders, then a confetti animation plays for 2 seconds (unless `prefers-reduced-motion` is set).
2. Given the completion screen renders, then the message reads: "Amazing work, [first name]! Your results are ready." (using the child's `display_name`).
3. Given the student is on the completion screen, when they click "See My Results," then they are navigated to the student-facing results summary page.
4. Given the assessment completes, when the parent's email is checked, then the notification contains a direct link to the parent results screen (`/diagnostic/results?assessmentId={id}`).
5. Given the student-facing results screen renders, then no numeric percentages are shown — only visual bars and level labels (Below Par / On Par / Above Par).

**Dependencies:** US-4.7 complete.

---

### Epic 5: Results & Gap Analysis Display
**Source:** FR-5 | **Total Points:** 38

| ID | Title | Priority | Points |
|----|-------|----------|--------|
| US-5.1 | Student-facing results summary | P0 | 8 |
| US-5.2 | Parent-facing detailed results | P0 | 8 |
| US-5.3 | Skill-by-skill proficiency visualization | P0 | 8 |
| US-5.4 | Gap summary and priority list | P0 | 5 |
| US-5.5 | PDF/print export | P1 | 9 |

---

**US-5.1 — Student-Facing Results Summary**

> As a **student**, I want to **see an encouraging, easy-to-understand summary of my diagnostic results** so that **I feel good about the effort I made and understand what PADI.AI will help me with next**.

**Acceptance Criteria:**

1. Given the results screen loads, then the header uses one of three themed icons: mountain peak (Above Par), hiking path (On Par), climbing figure (Below Par), corresponding to the student's overall classification.
2. Given the results render, then 14 horizontal progress bars are shown: 9 for Grade 3 prerequisite skills and 5 for Grade 4 domain averages.
3. Given a skill is "Below Par," then its bar is orange; "On Par" bars are blue; "Above Par" bars are green.
4. Given skill names render, then child-friendly labels are used (e.g., "Multiplication Facts" not "3.OA.C.7"); a code-to-label mapping is maintained in `lib/constants.ts`.
5. Given the results page renders, then zero numeric accuracy percentages are visible to the student (only bars and level labels).
6. Given the bars animate on mount, when the animation plays, then bars fill from left over 800ms with ease-in-out timing and the animation is suppressed if `prefers-reduced-motion: reduce`.

**Dependencies:** US-4.7 complete.

---

**US-5.2 — Parent-Facing Detailed Results**

> As a **parent**, I want to **see a detailed, plain-language report of my child's diagnostic results** so that **I understand their strengths, gaps, and what PADI.AI will do to help, without needing to understand educational jargon**.

**Acceptance Criteria:**

1. Given the parent results page loads, then it has 6 sections: (1) Summary, (2) Prerequisite Skills table, (3) Grade 4 Domain Preview chart, (4) What This Means, (5) What PADI.AI Will Do, (6) Tips for Parents.
2. Given the Prerequisite Skills table renders, then columns are: Skill Name, Standard Code, Result (colored badge), Questions Answered, Accuracy %.
3. Given I click on a skill bar in the parent view, when the detail panel opens, then it shows: skill description, questions answered, which questions were correct/incorrect (colored circles, no question content visible), and a disabled "Practice this skill" link.
4. Given a skill has no "Below Par" classifications, when the gap summary renders, then the message reads: "Great news! Your child is on track with all foundational skills for 4th grade math."
5. Given the overall proficiency level is "Below Par," when the parent view renders, then the percentage display shows e.g., "5 of 9 prerequisite skills: Below Par."
6. Given results are shown, then all comparisons are criterion-referenced against grade-level expectations — no percentile ranks, no peer comparisons, no class averages.

**Dependencies:** US-5.1 complete.

---

**US-5.3 — Skill-by-Skill Proficiency Visualization**

> As a **parent or student**, I want to **interactive charts that show proficiency by skill and domain** so that **I can visually compare performance across areas and identify patterns**.

**Acceptance Criteria:**

1. Given the results page renders, then bar charts are implemented in React using SVG (custom component or recharts); no third-party charting library with a > 50KB bundle is in the critical render path.
2. Given bars are grouped by domain, then section headers ("Operations & Algebraic Thinking," "Number & Operations in Base Ten," etc.) separate the domains visually.
3. Given a bar animation completes, then each bar shows its color, fill width proportional to mastery, and (parent view only) an accuracy percentage label on the right.
4. Given the assessment results API returns domain averages, when Grade 4 domains are rendered in the parent view, then a donut chart shows approximate readiness per domain with a legend.
5. Given I resize the browser from desktop (1440px) to mobile (375px), when the chart layout adjusts, then bars remain readable with labels not overlapping.

**Dependencies:** US-5.2 complete.

---

**US-5.4 — Gap Summary and Priority List**

> As a **parent**, I want to **see a prioritized list of the skills my child most needs to work on** so that **I know where to focus attention and can understand which gaps are most foundational**.

**Acceptance Criteria:**

1. Given the gap summary renders, then "Below Par" skills are listed in prerequisite-graph priority order (most foundational skills first, using topological sort of `prerequisite_relationships`).
2. Given each gap skill is listed, then it shows: skill name, standard code, accuracy %, and a one-sentence description of what the skill involves.
3. Given there are no "Below Par" skills, when the gap section renders, then the message "Great news! Your child is on track with all foundational skills for 4th grade math." is displayed.
4. Given a gap skill is a Grade 3 prerequisite, when it appears in the list, then it is clearly labeled as a "Foundation skill" to distinguish from Grade 4 content.
5. Given the prerequisite graph is queried, when gap skills are ordered, then a skill that is a prerequisite to 5 other skills appears before a skill that is a prerequisite to 1 other skill.

**Dependencies:** US-5.2, US-2.2 complete.

---

**US-5.5 — PDF/Print Export**

> As a **parent**, I want to **download a PDF of my child's diagnostic results** so that **I can share them with a teacher, keep a record, or review them offline**.

**Acceptance Criteria:**

1. Given I click "Download Report (PDF)," when the server generates the PDF, then I receive a valid PDF file within 10 seconds with HTTP 200.
2. Given the PDF is generated, then it contains: PADI.AI branding header, student first name only (not last), date completed, overall level, per-skill breakdown table with accuracy percentages, gap summary, and What Comes Next section.
3. Given the PDF metadata is inspected, then the `Author` and `Creator` metadata fields contain "PADI.AI" — not the student's full name or date of birth.
4. Given I download the PDF twice, then both downloads contain the same data (idempotent generation from the same assessment record).
5. Given the PDF is opened with a screen reader (e.g., Adobe Acrobat Reader with accessibility mode), then section headings are tagged and the skill table is properly structured for AT navigation.

**Dependencies:** US-5.2; WeasyPrint or Puppeteer configured in FastAPI container.

---

## 3. Detailed Test Plan

### 3.1 Unit Tests

**Framework:** pytest 8.x for Python (apps/api, services/bkt-engine); Vitest 1.x + React Testing Library 14 for TypeScript (apps/web, packages/)
**Coverage Targets:** Core business logic ≥90%; API service/repository layer ≥80%; UI components ≥70%
**Mock Strategy:** All external services (Auth0, SES, Redis, PostgreSQL) are mocked at the service boundary. pytest `AsyncMock` for async services; `httpx.AsyncClient` with ASGI transport for FastAPI route tests.

**Test Locations:**
- Python unit tests: `apps/api/tests/unit/`
- BKT unit tests: `services/bkt-engine/tests/unit/`
- TypeScript unit tests: `apps/web/tests/unit/`
- Math renderer tests: `packages/math-renderer/src/**/*.test.tsx`

---

#### 3.1.1 BKT Service Unit Tests (`services/bkt-engine/tests/unit/test_tracker.py`)

| Test ID | Test Name | What It Verifies |
|---------|-----------|-----------------|
| BKT-U-001 | `test_initialize_below_par_accuracy` | P_L0 = 0.10 when accuracy < 0.60 |
| BKT-U-002 | `test_initialize_on_par_accuracy` | P_L0 = 0.40 when 0.60 ≤ accuracy < 0.80 |
| BKT-U-003 | `test_initialize_above_par_accuracy` | P_L0 = 0.75 when accuracy ≥ 0.80 |
| BKT-U-004 | `test_initialize_single_response_low_confidence` | `low_confidence = TRUE` when only 1 response in pool |
| BKT-U-005 | `test_initialize_all_skills_in_diagnostic` | All 38 standards get skill state rows after full diagnostic |
| BKT-U-006 | `test_default_bkt_parameters` | p_t=0.10, p_s=0.10, p_g=0.20 on init |
| BKT-U-007 | `test_mastery_probability_zero_responses` | Returns None (not 0.0) for unassessed standard |
| BKT-U-008 | `test_p_l0_boundary_exactly_060` | Accuracy of 0.60 maps to on-par bucket (inclusive lower bound) |
| BKT-U-009 | `test_p_l0_boundary_exactly_080` | Accuracy of 0.80 maps to above-par bucket (inclusive lower bound) |
| BKT-U-010 | `test_initialize_returns_all_assessed_standards` | Output dict keys match exactly the input standard codes |

**Example — BKT-U-001:**
```python
# services/bkt-engine/tests/unit/test_tracker.py

import pytest
from services.bkt_engine.engine.tracker import initialize_bkt_state_from_diagnostic

class TestBKTInitialization:
    def test_initialize_below_par_accuracy(self):
        """P_L0 should be 0.10 when diagnostic accuracy is below 60%."""
        diagnostic_results = {
            "3.OA.C.7": [False, False, True],  # accuracy = 0.333
        }
        states = initialize_bkt_state_from_diagnostic("student-uuid", diagnostic_results)
        assert states["3.OA.C.7"]["p_l0"] == pytest.approx(0.10, abs=0.001)
        assert states["3.OA.C.7"]["p_mastered"] == pytest.approx(0.10, abs=0.001)
        assert states["3.OA.C.7"]["initialized_from"] == "diagnostic"
        assert states["3.OA.C.7"]["response_count"] == 3

    def test_initialize_p_l0_boundary_exactly_060(self):
        """Accuracy of exactly 0.60 should map to the on-par bucket (inclusive)."""
        diagnostic_results = {"4.NBT.B.4": [True, True, False, True, False]}  # 3/5 = 0.60
        states = initialize_bkt_state_from_diagnostic("student-uuid", diagnostic_results)
        assert states["4.NBT.B.4"]["p_l0"] == pytest.approx(0.40, abs=0.001)

    def test_initialize_single_response_low_confidence_flag(self):
        """Single response should set low_confidence = True on the state."""
        diagnostic_results = {"4.OA.A.1": [True]}  # only 1 question answered
        states = initialize_bkt_state_from_diagnostic("student-uuid", diagnostic_results)
        assert states["4.OA.A.1"]["low_confidence"] is True

    def test_default_bkt_parameters_are_stage1_values(self):
        """Stage 1 default BKT parameters must match documented values."""
        diagnostic_results = {"3.NF.A.1": [True, False, True]}
        states = initialize_bkt_state_from_diagnostic("student-uuid", diagnostic_results)
        s = states["3.NF.A.1"]
        assert s["p_t"] == pytest.approx(0.10)
        assert s["p_s"] == pytest.approx(0.10)
        assert s["p_g"] == pytest.approx(0.20)
```

---

#### 3.1.2 Question Selection Service Unit Tests (`apps/api/tests/unit/test_question_selection_service.py`)

| Test ID | Test Name | What It Verifies |
|---------|-----------|-----------------|
| QSS-U-001 | `test_first_question_is_difficulty_2` | CAT always starts each standard at difficulty 2 |
| QSS-U-002 | `test_correct_answer_increases_difficulty` | Correct → target difficulty increments by 1 |
| QSS-U-003 | `test_incorrect_answer_decreases_difficulty` | Incorrect → target difficulty decrements by 1 |
| QSS-U-004 | `test_difficulty_capped_at_4` | Correct answer at difficulty 4 → next target is 4 (not 5) |
| QSS-U-005 | `test_difficulty_floored_at_1` | Incorrect answer at difficulty 1 → next target is 1 (not 0) |
| QSS-U-006 | `test_fallback_cascade_on_exhausted_pool` | Falls back through `[d+1, d-1, 3, 2, 4, 1]` when target empty |
| QSS-U-007 | `test_excludes_already_answered_questions` | `answered_question_ids` list is honored in query |
| QSS-U-008 | `test_termination_all_correct` | Returns `done=True` after 3 consecutive correct answers |
| QSS-U-009 | `test_termination_all_incorrect` | Returns `done=True` after 3 consecutive incorrect answers |
| QSS-U-010 | `test_pool_exhausted_raises_error` | `QuestionPoolExhaustedError` raised when all questions answered |

**Example — QSS-U-006:**
```python
# apps/api/tests/unit/test_question_selection_service.py

import pytest
from unittest.mock import AsyncMock, patch
from apps.api.src.service.question_selection_service import select_next_question
from apps.api.src.core.exceptions import QuestionPoolExhaustedError

@pytest.mark.asyncio
async def test_fallback_cascade_uses_adjacent_difficulty():
    """When target difficulty has no available questions, use the cascade."""
    # Mock: difficulty 3 is empty; difficulty 4 has one question
    mock_repo = AsyncMock()
    mock_repo.get_questions_by_difficulty.side_effect = [
        [],           # target difficulty=3: empty
        [{"id": "q-uuid-001", "difficulty": 4}],  # fallback d+1=4: found
    ]
    with patch("apps.api.src.service.question_selection_service.question_repo", mock_repo):
        selected_id = await select_next_question(
            student_id="student-uuid",
            standard_code="4.NF.A.1",
            current_difficulty=3,
            answered_question_ids=["q-uuid-002", "q-uuid-003"],
        )
    assert selected_id == "q-uuid-001"
    assert mock_repo.get_questions_by_difficulty.call_count == 2

@pytest.mark.asyncio
async def test_pool_exhausted_raises_error():
    """QuestionPoolExhaustedError raised when all fallbacks also empty."""
    mock_repo = AsyncMock()
    mock_repo.get_questions_by_difficulty.return_value = []
    with patch("apps.api.src.service.question_selection_service.question_repo", mock_repo):
        with pytest.raises(QuestionPoolExhaustedError, match="4.GM.A.1"):
            await select_next_question(
                student_id="student-uuid",
                standard_code="4.GM.A.1",
                current_difficulty=2,
                answered_question_ids=["q-001", "q-002", "q-003", "q-004", "q-005"],
            )
```

---

#### 3.1.3 Consent Service Unit Tests (`apps/api/tests/unit/test_consent_service.py`)

| Test ID | Test Name | What It Verifies |
|---------|-----------|-----------------|
| CON-U-001 | `test_consent_initiate_creates_pending_record` | Consent record created with status='pending' |
| CON-U-002 | `test_consent_confirm_with_valid_token` | Valid HMAC token confirms consent; status='active' |
| CON-U-003 | `test_consent_confirm_with_expired_token` | Expired token rejected; status unchanged |
| CON-U-004 | `test_consent_confirm_with_tampered_token` | HMAC mismatch rejected; returns HTTP 400 |
| CON-U-005 | `test_consent_record_never_deleted` | Consent records survive user deletion workflow |
| CON-U-006 | `test_consent_ip_hash_is_sha256` | ip_address_hash is 64-char hex (SHA-256) |
| CON-U-007 | `test_consent_stores_policy_version` | privacy_policy_version and tos_version captured |
| CON-U-008 | `test_consent_text_hash_matches_shown_text` | consent_text_hash is SHA-256 of the displayed consent text |
| CON-U-009 | `test_revocation_within_24h_window` | Revocation within 24h sets status='revoked' |
| CON-U-010 | `test_ses_email_sent_on_initiate` | AWS SES send is called once with the parent's email on initiate |

---

#### 3.1.4 Scoring Engine Unit Tests (`apps/api/tests/unit/test_scoring_engine.py`)

| Test ID | Test Name | What It Verifies |
|---------|-----------|-----------------|
| SCR-U-001 | `test_accuracy_all_correct` | 3/3 correct → accuracy=1.0, Above Par |
| SCR-U-002 | `test_accuracy_two_of_three` | 2/3 correct → accuracy=0.667, On Par |
| SCR-U-003 | `test_accuracy_zero_correct` | 0/3 correct → accuracy=0.0, Below Par |
| SCR-U-004 | `test_overall_level_mode_below_par` | Mode calculation with Below Par majority |
| SCR-U-005 | `test_overall_level_tie_broken_conservatively` | Tie between On Par and Above Par → On Par |
| SCR-U-006 | `test_overall_level_tie_below_on` | Tie between Below Par and On Par → Below Par |
| SCR-U-007 | `test_unassessed_standard_returns_none` | Standard not assessed → accuracy=None, not 0.0 |
| SCR-U-008 | `test_accuracy_boundary_exactly_060` | 0.60 accuracy → On Par classification |
| SCR-U-009 | `test_accuracy_boundary_exactly_080` | 0.80 accuracy → Above Par classification |
| SCR-U-010 | `test_scoring_pipeline_fires_redis_event` | `diagnostic_completed` event published to Redis Streams on completion |

---

#### 3.1.5 Frontend Component Unit Tests (`apps/web/tests/unit/`)

| Test ID | File | What It Verifies |
|---------|------|-----------------|
| UI-U-001 | `consent-form.test.tsx` | Checkboxes unchecked by default; submit blocked if not both checked |
| UI-U-002 | `consent-form.test.tsx` | Error shown when submitting with one unchecked box |
| UI-U-003 | `question-card.test.tsx` | KaTeX render output contains expected math elements (no raw LaTeX) |
| UI-U-004 | `answer-option.test.tsx` | Option highlight updates on selection; previous selection deselected |
| UI-U-005 | `progress-tracker.test.tsx` | Progress bar width is proportional to questionsAnswered/totalQuestions |
| UI-U-006 | `assessment-store.test.ts` | `selectOption` action updates `selectedOption` state |
| UI-U-007 | `assessment-store.test.ts` | `recordResponse` appends to `responses` array and increments count |
| UI-U-008 | `assessment-store.test.ts` | `pauseSession` sets `isPaused = true` |
| UI-U-009 | `results-summary.test.tsx` | Below Par bar has correct CSS color class (orange) |
| UI-U-010 | `fraction-builder.test.tsx` | `2/4` input renders as equivalent to `1/2` on reduction preview |

---

### 3.2 Integration Tests

**Framework:** pytest with `testcontainers-python` (PostgreSQL 17 container); `httpx.AsyncClient` with FastAPI ASGI transport; Redis container via `testcontainers`.
**Strategy:** Integration tests run against real containers (no mocks for DB or Redis). External services (Auth0, SES) are mocked at the HTTP client level using `respx`.
**Location:** `apps/api/tests/integration/`

---

#### 3.2.1 API Endpoint Integration Tests

| Test ID | Endpoint | Scenario | Expected Outcome |
|---------|----------|----------|-----------------|
| INT-001 | `POST /auth/register` | Valid new registration | 201 + user record in DB; email verification token created |
| INT-002 | `POST /auth/register` | Duplicate email | 409 with error message |
| INT-003 | `POST /consent/initiate` | Valid consent form submission | 201; consent record with status='pending'; SES mock called |
| INT-004 | `POST /consent/confirm` | Valid token, within expiry | 200; consent status='active' in DB; audit log entry written |
| INT-005 | `POST /consent/confirm` | Expired token (>24h) | 410 Gone; consent status unchanged |
| INT-006 | `GET /standards` | Authenticated parent | 200 + array of 38 standards |
| INT-007 | `GET /standards?grade=3` | Filter by grade | 200 + exactly 9 standards |
| INT-008 | `POST /assessments` | Valid start; student owned by parent | 201; assessment in DB; Redis state key created |
| INT-009 | `POST /assessments` | Student not owned by authenticated parent | 403 |
| INT-010 | `GET /assessments/{id}/next-question` | Valid active session | 200 + question object; `correct_answer` absent from response |
| INT-011 | `POST /assessments/{id}/responses` | Valid answer submission | 200; response recorded in DB; Redis state updated |
| INT-012 | `POST /assessments/{id}/responses` | Duplicate submission (same question_id) | 200 idempotent; no duplicate row in DB |
| INT-013 | `PUT /assessments/{id}/complete` | All standards done | 200; assessment status='completed'; skill states written; Redis event published |
| INT-014 | `GET /assessments/{id}/results` | Completed assessment | 200 + full results payload including gap analysis |
| INT-015 | `GET /students/{id}/diagnostic-report.pdf` | Completed assessment | 200 Content-Type: application/pdf; file ≥ 50KB |

**Example — INT-008 + INT-011:**
```python
# apps/api/tests/integration/test_assessment_flow.py

import pytest
from httpx import AsyncClient
from apps.api.src.main import app

@pytest.mark.asyncio
async def test_full_assessment_session_creation_and_response(
    authenticated_parent_client,  # fixture: AsyncClient with valid JWT
    seeded_student,                # fixture: student owned by authenticated parent
    seeded_question_bank,          # fixture: 142 active questions loaded
    redis_client,                  # fixture: real Redis container client
):
    """Integration: create assessment, submit first response, verify state."""
    # 1. Start assessment
    resp = await authenticated_parent_client.post(
        "/api/v1/assessments",
        json={"student_id": seeded_student.id, "type": "diagnostic"},
    )
    assert resp.status_code == 201
    assessment_id = resp.json()["assessment_id"]

    # 2. Verify Redis state was created
    redis_key = f"assessment:{assessment_id}:state"
    state = await redis_client.get(redis_key)
    assert state is not None

    # 3. Get first question
    resp = await authenticated_parent_client.get(
        f"/api/v1/assessments/{assessment_id}/next-question"
    )
    assert resp.status_code == 200
    question = resp.json()["question"]
    assert "correct_answer" not in question  # must not leak answer

    # 4. Submit response
    resp = await authenticated_parent_client.post(
        f"/api/v1/assessments/{assessment_id}/responses",
        json={
            "question_id": question["id"],
            "answer": "A",
            "time_ms": 12000,
        },
    )
    assert resp.status_code == 200
    assert "is_correct" in resp.json()

    # 5. Verify response recorded in DB
    # (using db fixture to query assessment_responses directly)
    ...
```

---

#### 3.2.2 Database Migration Tests

| Test ID | Test Name | What It Verifies |
|---------|-----------|-----------------|
| MIG-001 | `test_upgrade_head_from_empty` | `alembic upgrade head` on empty DB succeeds; all tables created |
| MIG-002 | `test_downgrade_base` | `alembic downgrade base` succeeds; all tables dropped cleanly |
| MIG-003 | `test_seed_standards_count` | Post-migration seed: 38 standards rows present |
| MIG-004 | `test_seed_prerequisites_count` | Post-migration seed: ≥22 prerequisite relationship rows |
| MIG-005 | `test_no_cycles_in_prerequisite_graph` | Recursive CTE topological sort: no cycles detected |
| MIG-006 | `test_audit_triggers_fire_on_insert` | INSERT into standards table creates audit_log row |
| MIG-007 | `test_pgcrypto_extension_enabled` | `SELECT * FROM pg_extension WHERE extname = 'pgcrypto'` returns row |
| MIG-008 | `test_pgvector_extension_enabled` | pgvector extension present; VECTOR(1536) column exists on standards |

---

#### 3.2.3 Redis Cache Behavior Tests

| Test ID | Test Name | What It Verifies |
|---------|-----------|-----------------|
| RED-001 | `test_assessment_state_ttl_is_7_days` | Redis key TTL ≈ 604800 seconds on creation |
| RED-002 | `test_state_fallback_to_postgres_on_redis_miss` | Redis key deleted → API falls back to PostgreSQL; still returns 200 |
| RED-003 | `test_atomic_state_update_on_response_submit` | Redis MULTI/EXEC ensures no partial state writes |
| RED-004 | `test_rate_limit_counter_increments` | 100 requests within 60s: counter = 100; 101st returns 429 |
| RED-005 | `test_session_token_invalidation_on_logout` | After logout, refresh token Redis key is deleted; reuse returns 401 |

---

### 3.3 End-to-End Tests (Playwright)

**Framework:** Playwright 1.45+ (TypeScript)
**Browser Matrix:**

| Browser | Version | Device | Mode |
|---------|---------|--------|------|
| Chromium | Latest | Desktop (1280×800) | Default |
| Chromium | Latest | iPad (810×1080) | Portrait |
| WebKit (Safari) | Latest | Desktop | Default |
| Firefox | Latest | Desktop | Default |
| Chromium | Latest | iPhone SE (375×667) | Mobile |

**Location:** `apps/web/tests/e2e/`
**Visual Regression:** Playwright `toHaveScreenshot()` with 1px diff threshold; baselines stored in `apps/web/tests/e2e/snapshots/`.

---

#### 3.3.1 Critical Path: COPPA Registration & Consent

**File:** `apps/web/tests/e2e/auth/registration-consent.spec.ts`

| Test ID | Test Name | What It Verifies |
|---------|-----------|-----------------|
| E2E-001 | `registration_happy_path` | Full flow: register → verify email → consent → create student → dashboard |
| E2E-002 | `consent_checkboxes_not_prechecked` | Both consent checkboxes have `checked = false` on page load |
| E2E-003 | `consent_submit_blocked_without_both_boxes` | Submit with one unchecked → error visible, no navigation |
| E2E-004 | `duplicate_email_shows_error` | Existing email → error message visible in DOM |
| E2E-005 | `verification_link_expired_shows_resend` | Expired token URL → "Request new link" UI visible |

**Example — E2E-001:**
```typescript
// apps/web/tests/e2e/auth/registration-consent.spec.ts

import { test, expect } from '@playwright/test';
import { generateTestEmail } from '../../helpers/email';
import { interceptVerificationEmail } from '../../helpers/ses-mock';

test('full registration and consent flow', async ({ page }) => {
  const email = generateTestEmail();

  // Step 1: Register
  await page.goto('/register');
  await page.getByLabel('First Name').fill('Maria');
  await page.getByLabel('Last Name').fill('Garcia');
  await page.getByLabel('Email').fill(email);
  await page.getByLabel('Password').fill('Secure!Pass1');
  await page.getByLabel('Confirm Password').fill('Secure!Pass1');
  await page.getByRole('button', { name: 'Create Account' }).click();

  // Step 2: Email verification holding page
  await expect(page.getByText('Check your email')).toBeVisible();

  // Step 3: Simulate email verification (test SES mock intercepts link)
  const verificationLink = await interceptVerificationEmail(email);
  await page.goto(verificationLink);
  await expect(page).toHaveURL(/onboarding\/consent/);

  // Step 4: Consent form - checkboxes not pre-checked
  const policyCheckbox = page.getByLabel('I have read and agree to the Privacy Policy');
  const consentCheckbox = page.getByLabel('I provide verifiable parental consent');
  await expect(policyCheckbox).not.toBeChecked();
  await expect(consentCheckbox).not.toBeChecked();

  // Step 5: Accept consent
  await policyCheckbox.check();
  await consentCheckbox.check();
  await page.getByRole('button', { name: 'Submit Consent' }).click();

  // Step 6: Create child profile
  await expect(page).toHaveURL(/onboarding\/create-student/);
  await page.getByLabel('Child\'s First Name').fill('Jayden');
  await page.getByRole('button', { name: /Avatar 3/ }).click();
  await page.getByRole('button', { name: 'Create Profile' }).click();

  // Step 7: Dashboard with child card
  await expect(page).toHaveURL('/dashboard');
  await expect(page.getByText('Jayden')).toBeVisible();
  await expect(page.getByText('Not Started')).toBeVisible();
});

test('consent checkboxes are not pre-checked on page load', async ({ page }) => {
  // Pre-condition: verified user, not yet consented
  await page.goto('/onboarding/consent', { ...authenticatedPreConsentContext });
  const boxes = page.getByRole('checkbox');
  await expect(boxes.nth(0)).not.toBeChecked();
  await expect(boxes.nth(1)).not.toBeChecked();
});
```

---

#### 3.3.2 Critical Path: Diagnostic Assessment

**File:** `apps/web/tests/e2e/assessment/diagnostic.spec.ts`

| Test ID | Test Name | What It Verifies |
|---------|-----------|-----------------|
| E2E-010 | `diagnostic_start_to_first_question` | Start → first question card visible with KaTeX rendered |
| E2E-011 | `answer_multiple_choice_and_advance` | Select option B → next question displayed within 500ms |
| E2E-012 | `progress_bar_increments` | Progress bar increases after each submitted answer |
| E2E-013 | `pause_and_resume_assessment` | Save progress → logout → login → Continue → same question index |
| E2E-014 | `back_navigation_blocked` | Browser back button during assessment → warning modal shown |
| E2E-015 | `completion_screen_renders` | Final answer submitted → confetti + "Amazing work!" message |
| E2E-016 | `correct_answer_not_in_dom` | DevTools search for correct answer in network responses: absent |
| E2E-017 | `keyboard_navigation_selects_option` | Tab to option B → arrow key to C → Enter → option C selected |

**Example — E2E-013:**
```typescript
// apps/web/tests/e2e/assessment/diagnostic.spec.ts

test('pause and resume assessment preserves question index', async ({ page, context }) => {
  // Start assessment and answer 5 questions
  await page.goto('/diagnostic/start');
  await page.getByRole('button', { name: 'Start Diagnostic for Jayden' }).click();
  
  for (let i = 0; i < 5; i++) {
    await page.getByRole('button', { name: /^A\b/ }).click();  // Select option A
    await page.getByRole('button', { name: 'Submit' }).click();
    await page.waitForTimeout(200);  // Allow question transition
  }
  
  // Capture current question index from progress bar
  const progressText = await page.getByTestId('progress-text').textContent();
  expect(progressText).toContain('Question 6');  // 5 answered, on question 6

  // Pause
  await page.getByRole('button', { name: 'Save my progress' }).click();
  await expect(page.getByText('See you later!')).toBeVisible();

  // Log out
  await page.getByRole('button', { name: 'Log out' }).click();

  // Re-login and navigate to dashboard
  // (login helpers omitted for brevity)
  await page.getByText('Continue').click();

  // Verify we resume at question 6, not question 1
  await expect(page.getByTestId('progress-text')).toContainText('Question 6');
});
```

---

#### 3.3.3 Critical Path: Results Display

**File:** `apps/web/tests/e2e/results/results-display.spec.ts`

| Test ID | Test Name | What It Verifies |
|---------|-----------|-----------------|
| E2E-020 | `parent_results_loads_after_completion` | Navigate to results → all 6 sections visible |
| E2E-021 | `student_results_no_percentages` | Student view has no numeric % values in DOM |
| E2E-022 | `bar_charts_animate_on_mount` | Bars have non-zero width after 1 second (animation complete) |
| E2E-023 | `pdf_download_initiates` | Click "Download PDF" → response has Content-Type: application/pdf |
| E2E-024 | `gap_list_shows_below_par_skills` | All Below Par skills appear in "Skills to Focus On" section |
| E2E-025 | `visual_regression_results_page` | Screenshot matches baseline within 1px threshold |

---

#### 3.3.4 Visual Regression Tests

**File:** `apps/web/tests/e2e/visual/visual-regression.spec.ts`

| Test ID | Baseline Name | What It Captures |
|---------|--------------|-----------------|
| VR-001 | `registration-page.png` | Registration form, all inputs, CTA button |
| VR-002 | `consent-form-unchecked.png` | Consent form with both checkboxes unchecked |
| VR-003 | `assessment-question-mc.png` | Multiple choice question with KaTeX math |
| VR-004 | `assessment-question-fraction.png` | Fraction input fields with live preview |
| VR-005 | `results-parent-summary.png` | Full parent results page (desktop 1440px) |
| VR-006 | `results-student-summary.png` | Student-facing results page (iPad 810px) |
| VR-007 | `admin-question-list.png` | Admin question management table |

---

### 3.4 Behavioral / BDD Tests

**Framework:** `behave` (Python) for backend user journeys; Playwright's `test.step` for frontend journeys.
**Location:** `apps/api/tests/bdd/features/` (`.feature` files); `apps/api/tests/bdd/steps/` (step implementations)

---

#### Feature: COPPA Parental Consent

```gherkin
# apps/api/tests/bdd/features/coppa_consent.feature

Feature: COPPA Verifiable Parental Consent
  As the legal compliance team
  I want parental consent to be properly collected and stored
  So that we comply with COPPA 16 CFR Part 312

  Background:
    Given the application is running with COPPA enforcement enabled
    And a parent named "Maria Garcia" has verified their email "maria@example.com"

  Scenario: Successful email-plus consent flow
    When Maria submits the consent form with both checkboxes checked
    And the consent text hash is computed from the displayed consent text
    Then a consent record is created with status "pending"
    And the consent_text_hash matches SHA-256 of the displayed consent text
    And a confirmation email is sent to "maria@example.com" within 60 seconds
    When Maria clicks the confirmation link in her email
    Then the consent record status changes to "active"
    And the confirmed_at timestamp is recorded
    And an audit log entry is written with change_type "UPDATE"

  Scenario: Consent form submitted without both checkboxes
    When Maria submits the consent form with only the privacy policy checkbox checked
    Then the consent form is NOT submitted to the server
    And an error message "Please check both boxes to continue" is visible
    And no consent record is created in the database

  Scenario: Consent record survives account deletion
    Given Maria has active consent and a child profile named "Jayden"
    When Maria requests account deletion and confirms with "DELETE" and her password
    Then Maria's user account is marked deleted
    And Jayden's student record is marked deleted
    And Maria's consent record remains in the database with consented=true
    And the consent_records row is NOT deleted

  Scenario: Pre-checked checkboxes are rejected
    When the consent page renders
    Then both consent checkboxes have attribute "checked" equal to false
    And no JavaScript can set them to checked before user interaction
```

---

#### Feature: Adaptive Diagnostic Assessment

```gherkin
# apps/api/tests/bdd/features/diagnostic_assessment.feature

Feature: Adaptive CAT Diagnostic Assessment
  As a student taking the diagnostic
  I want questions to adapt to my ability level
  So that the assessment efficiently determines my knowledge state

  Background:
    Given the question bank has at least 142 validated questions
    And a student "Jayden" is linked to a parent with active consent
    And a diagnostic assessment has been started for Jayden

  Scenario: CAT starts each standard at difficulty 2
    When the first question for standard "3.OA.C.7" is requested
    Then the question returned has difficulty_level equal to 2

  Scenario: Correct answer escalates difficulty
    Given Jayden has been served a difficulty-2 question for "4.NBT.B.5"
    When Jayden submits the correct answer
    Then the next question for "4.NBT.B.5" targets difficulty 3

  Scenario: Incorrect answer de-escalates difficulty
    Given Jayden has been served a difficulty-3 question for "4.NF.A.1"
    When Jayden submits an incorrect answer
    Then the next question for "4.NF.A.1" targets difficulty 2

  Scenario: Standard terminates after 3 all-correct responses
    Given Jayden has answered 3 questions for "3.OA.C.7" all correctly
    When the next question is requested
    Then "3.OA.C.7" has status "done" in the CAT state
    And the next question served is for a different standard

  Scenario: Assessment completes with BKT initialization
    Given Jayden has answered at least 35 questions covering all 38 standards
    When Jayden submits the final answer
    Then the assessment status is set to "completed"
    And exactly 38 rows exist in student_skill_states for Jayden's assessment
    And a "diagnostic_completed" event is published to Redis Streams
    And a notification email is sent to Jayden's parent within 5 minutes

  Scenario: No PII in question content
    When all questions in the seed bank are inspected
    Then no question stem or answer option contains a student's real name
    And no question references a specific school address or identifier
```

---

#### Feature: COPPA-Safe Results Display

```gherkin
# apps/api/tests/bdd/features/results_display.feature

Feature: Results and Gap Analysis Display
  As a parent
  I want to view my child's diagnostic results
  So that I understand their math proficiency and what PADI.AI will do

  Background:
    Given Jayden has completed the diagnostic assessment
    And the scoring pipeline has run

  Scenario: Parent views detailed results
    When Maria navigates to the parent results page
    Then she sees Jayden's overall proficiency level (Below Par, On Par, or Above Par)
    And she sees a table of 9 prerequisite skills with accuracy percentages
    And she sees 5 Grade 4 domain bars with proficiency levels
    And she sees a "Skills to Focus On" section with any Below Par skills listed
    And the comparison is against grade-level expectations, not other students

  Scenario: Student view shows no numeric percentages
    When Jayden navigates to the student results page
    Then he sees visual bars for each skill
    And NO element in the page DOM contains a numeric accuracy percentage
    And he sees encouraging language matching his overall proficiency level

  Scenario: Gap list ordered by prerequisite depth
    Given Jayden has Below Par classifications for "3.OA.C.7" and "4.NF.A.1"
    When the gap summary renders
    Then "3.OA.C.7" appears before "4.NF.A.1" in the list
    Because "3.OA.C.7" is a prerequisite to more Grade 4 standards
```

---

### 3.5 Robustness & Resilience Tests

**Framework:** pytest for Python; k6 for load testing; Playwright for browser-level failure scenarios.

---

#### 3.5.1 Error Handling Tests

| Test ID | Scenario | Expected Behavior |
|---------|----------|------------------|
| ROB-001 | `POST /assessments/{id}/responses` with missing `question_id` | HTTP 422; Pydantic validation error returned; no DB write |
| ROB-002 | `POST /assessments/{id}/responses` for a completed assessment | HTTP 409 Conflict; response body: "Assessment already completed" |
| ROB-003 | `GET /assessments/{id}/next-question` when pool is exhausted | HTTP 200; graceful fallback question from adjacent standard; never HTTP 500 |
| ROB-004 | `GET /assessments/{id}/results` for in-progress assessment | HTTP 409 Conflict; results not available until completion |
| ROB-005 | Invalid JWT on any authenticated endpoint | HTTP 401; body: `{"error": "invalid_token"}` |
| ROB-006 | AWS SES unavailable during consent confirmation | Consent record created (DB write succeeds); HTTP 202 returned; email retry queued |
| ROB-007 | PostgreSQL connection pool exhausted | HTTP 503; retry-after header set; no data corruption |
| ROB-008 | Request body exceeds 1MB limit | HTTP 413 Content Too Large; descriptive error message |
| ROB-009 | Concurrent answer submissions for same question_id | Idempotency: exactly 1 response row; no duplicate; second call returns 200 with original result |
| ROB-010 | PDF generation timeout (>10s) | HTTP 504 Gateway Timeout; parent sees "Report temporarily unavailable, try again" |

---

#### 3.5.2 Network Failure Simulation

```python
# apps/api/tests/integration/test_resilience.py

import pytest
from unittest.mock import patch, AsyncMock
import asyncio

@pytest.mark.asyncio
async def test_redis_unavailable_falls_back_to_postgres(
    authenticated_client, active_assessment_id, db_session
):
    """When Redis is unavailable, the API falls back to PostgreSQL for state."""
    with patch("apps.api.src.clients.redis_client.get", side_effect=ConnectionError("Redis down")):
        response = await authenticated_client.get(
            f"/api/v1/assessments/{active_assessment_id}/next-question"
        )
    # Should still succeed via PostgreSQL fallback
    assert response.status_code == 200
    assert "question" in response.json()

@pytest.mark.asyncio
async def test_ses_failure_does_not_block_consent(
    authenticated_client, verified_user_id
):
    """SES failure during consent should not prevent the consent record from being created."""
    with patch(
        "apps.api.src.clients.ses_client.send_email",
        new_callable=AsyncMock,
        side_effect=Exception("SES: connection refused")
    ):
        response = await authenticated_client.post(
            "/api/v1/consent/initiate",
            json={"user_id": verified_user_id, "consent_data": {...}}
        )
    # Consent record should be created even if email fails
    assert response.status_code == 202  # Accepted, but email delivery may be delayed
    # DB should have consent record with status='pending'
    # ...

@pytest.mark.asyncio
async def test_concurrent_assessment_responses_are_idempotent(
    authenticated_client, active_assessment, active_question_id
):
    """Concurrent submissions of the same question_id should produce exactly 1 DB row."""
    import asyncio
    submit_tasks = [
        authenticated_client.post(
            f"/api/v1/assessments/{active_assessment.id}/responses",
            json={"question_id": active_question_id, "answer": "B", "time_ms": 5000}
        )
        for _ in range(5)  # 5 concurrent identical submissions
    ]
    responses = await asyncio.gather(*submit_tasks, return_exceptions=True)
    successes = [r for r in responses if not isinstance(r, Exception) and r.status_code == 200]
    assert len(successes) >= 1  # At least one succeeds
    # Verify only 1 row in DB
    # ...
```

---

#### 3.5.3 Load Tests (k6)

**File:** `infrastructure/k6/diagnostic_load_test.js`

```javascript
// infrastructure/k6/diagnostic_load_test.js
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

const errorRate = new Rate('errors');

export const options = {
  stages: [
    { duration: '10m', target: 1000 },  // Ramp to 1000 VUs
    { duration: '40m', target: 1000 },  // Hold
    { duration: '10m', target: 0 },     // Ramp down
  ],
  thresholds: {
    'http_req_duration{name:next_question}': ['p(95)<500'],
    'http_req_duration{name:submit_response}': ['p(95)<500'],
    'errors': ['rate<0.001'],
    'http_req_failed': ['rate<0.001'],
  },
};

export default function () {
  const headers = { Authorization: `Bearer ${__ENV.TEST_JWT}` };

  // Get next question
  const nextQ = http.get(`${__ENV.API_URL}/assessments/${__ENV.ASSESSMENT_ID}/next-question`, {
    headers,
    tags: { name: 'next_question' },
  });
  check(nextQ, {
    'next_question status 200': (r) => r.status === 200,
    'correct_answer absent': (r) => !JSON.parse(r.body).question?.correct_answer,
  });
  errorRate.add(nextQ.status !== 200);

  sleep(Math.random() * 30 + 5);  // Simulate 5–35s think time

  // Submit response
  const submitR = http.post(
    `${__ENV.API_URL}/assessments/${__ENV.ASSESSMENT_ID}/responses`,
    JSON.stringify({ question_id: JSON.parse(nextQ.body).question?.id, answer: 'A', time_ms: 15000 }),
    { headers: { ...headers, 'Content-Type': 'application/json' }, tags: { name: 'submit_response' } },
  );
  check(submitR, { 'submit status 200': (r) => r.status === 200 });
  errorRate.add(submitR.status !== 200);

  sleep(1);
}
```

---

### 3.6 Repeatability Tests

---

#### 3.6.1 Idempotency Tests

| Test ID | Scenario | Expected Behavior |
|---------|----------|------------------|
| REP-001 | `POST /auth/register` called twice with same email | Second call returns 409; exactly 1 user row in DB |
| REP-002 | `POST /consent/confirm` called twice with same token | Second call returns 410 Gone; consent status remains 'active' from first call |
| REP-003 | `POST /assessments/{id}/responses` with same question_id twice | Second call returns 200 with original `is_correct`; exactly 1 response row in DB |
| REP-004 | `PUT /assessments/{id}/complete` called twice | Second call returns 200; scoring pipeline runs only once; student_skill_states count unchanged |
| REP-005 | Alembic `upgrade head` on already-migrated DB | Succeeds without error; no duplicate schema changes applied |

---

#### 3.6.2 CAT Determinism Tests

```python
# apps/api/tests/unit/test_repeatability.py

import pytest
from apps.api.src.service.question_selection_service import select_next_question

@pytest.mark.asyncio
async def test_cat_selection_is_deterministic_given_same_seed(
    question_pool_fixture,
):
    """
    Given the same assessment_id + standard_code seed, the same question
    should be selected on repeated calls (randomization is seeded).
    """
    # Same inputs, called twice
    q1 = await select_next_question(
        student_id="fixed-student-uuid",
        standard_code="4.NF.A.1",
        current_difficulty=2,
        answered_question_ids=[],
        random_seed="fixed-assessment-uuid::4.NF.A.1",
    )
    q2 = await select_next_question(
        student_id="fixed-student-uuid",
        standard_code="4.NF.A.1",
        current_difficulty=2,
        answered_question_ids=[],
        random_seed="fixed-assessment-uuid::4.NF.A.1",
    )
    assert q1 == q2  # Deterministic: same question on replay

@pytest.mark.asyncio
async def test_scoring_engine_produces_same_result_on_replay(
    completed_assessment_fixture,
):
    """
    Re-running the scoring engine against the same response set should
    produce identical per-skill accuracy and proficiency classifications.
    """
    from apps.api.src.service.assessment_service import calculate_results
    result1 = await calculate_results(completed_assessment_fixture)
    result2 = await calculate_results(completed_assessment_fixture)
    assert result1.overall_level == result2.overall_level
    for code in result1.skill_states:
        assert result1.skill_states[code].accuracy == pytest.approx(
            result2.skill_states[code].accuracy, abs=0.0001
        )
```

---

#### 3.6.3 Migration Reversibility Tests

| Test ID | Test Name | What It Verifies |
|---------|-----------|-----------------|
| REV-001 | `test_migrate_up_down_up` | `upgrade head` → `downgrade base` → `upgrade head` succeeds without error |
| REV-002 | `test_data_survives_up_down_up` | Seed data loaded → migrate down → migrate up → seed data intact |
| REV-003 | `test_down_migration_provided` | Every migration file in `alembic/versions/` has a non-trivial `downgrade()` function |

---

### 3.7 Security Tests

---

#### 3.7.1 SAST — Bandit (Python) and eslint-plugin-security (TypeScript)

**Run:** Every PR via `.github/workflows/ci.yml`

```yaml
# .github/workflows/ci.yml (security job excerpt)
  security-sast:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Bandit (Python SAST)
        run: |
          pip install bandit[toml]
          bandit -r apps/api/src services/bkt-engine/src -c pyproject.toml \
            --severity-level medium --confidence-level medium \
            --exit-zero  # Report in CI; fail only on HIGH
          bandit -r apps/api/src services/bkt-engine/src -c pyproject.toml \
            --severity-level high --exit-code 1  # Fail on HIGH+
      - name: Run ESLint security plugin (TypeScript)
        run: |
          pnpm --filter @padi-ai/web run lint:security
          # Uses eslint-plugin-security rules: detect-object-injection,
          # detect-non-literal-regexp, detect-possible-timing-attacks
```

**Bandit rules enforced (HIGH/MEDIUM):**

| Rule ID | Rule Name | Relevance |
|---------|-----------|----------|
| B101 | assert_used | No `assert` in production code paths |
| B104 | hardcoded_bind_all_interfaces | No `0.0.0.0` binding in non-test code |
| B105 | hardcoded_password_string | No hardcoded credentials |
| B106 | hardcoded_password_funcarg | No default password arguments |
| B201 | flask_debug_true | (N/A — FastAPI; catch similar patterns) |
| B301 | pickle | No pickle deserialization of untrusted data |
| B320 | xml_bad_cElementTree | No unsafe XML parsing |
| B501 | request_with_no_cert_validation | All HTTPS requests verify SSL |
| B506 | yaml_load | Use `yaml.safe_load` only |
| B601 | paramiko_calls | Paramiko with policy enforcement |

---

#### 3.7.2 DAST — OWASP ZAP (Weekly Automated Scan)

**Run:** Weekly via `.github/workflows/dependency-audit.yml` against staging environment.

```yaml
# .github/workflows/dependency-audit.yml (ZAP job excerpt)
  owasp-zap-scan:
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - name: ZAP API Scan
        uses: zaproxy/action-api-scan@v0.7.0
        with:
          target: 'https://staging-api.padi.ai/api/v1/openapi.json'
          rules_file_name: '.zap/rules.tsv'
          cmd_options: '-a -j -m 10 -T 60'
      - name: ZAP Baseline Scan (Frontend)
        uses: zaproxy/action-baseline@v0.12.0
        with:
          target: 'https://staging.padi.ai'
          rules_file_name: '.zap/baseline-rules.tsv'
```

**OWASP Top 10 Coverage for Stage 1:**

| OWASP Category | Test Coverage |
|---------------|---------------|
| A01 Broken Access Control | Auth middleware tests (INT-009); student ownership validation; admin-only route group |
| A02 Cryptographic Failures | pgcrypto AES-256 verification; TLS 1.3 header checks; no plaintext PII in logs |
| A03 Injection | Input sanitization tests; SQLAlchemy ORM (no raw SQL); Pydantic v2 validation |
| A04 Insecure Design | COPPA consent gate at middleware level; rate limiting; session scoping |
| A05 Security Misconfiguration | Bandit B104/B105; CORS strict allowlist; HSTS header verification |
| A06 Vulnerable Components | Trivy container scan; Dependabot; weekly `pip-audit` |
| A07 Auth & Session Mgmt | JWT validation tests; refresh token rotation; account lockout (US-1.10) |
| A08 Data Integrity Failures | Consent HMAC token validation; response idempotency; audit log immutability |
| A09 Logging & Monitoring | PII-in-logs check (Bandit custom rule); Sentry error tracking; audit log coverage |
| A10 SSRF | No user-supplied URLs fetched by server; S3 URLs validated against allowlist |

---

#### 3.7.3 COPPA-Specific Security Tests

| Test ID | Test Name | What It Verifies |
|---------|-----------|-----------------|
| SEC-COP-001 | `test_no_student_data_before_consent` | `POST /students` without active consent → HTTP 403 |
| SEC-COP-002 | `test_no_assessment_before_consent` | `POST /assessments` without active consent → HTTP 403 |
| SEC-COP-003 | `test_pii_not_in_logs` | Response logs for assessment endpoints contain `[STUDENT]` not child names |
| SEC-COP-004 | `test_consent_record_permanent` | `consent_records` table has `DELETE` privilege revoked for `app_role` |
| SEC-COP-005 | `test_ip_hash_not_raw_ip` | `consent_records.ip_address` is 64-char hex (SHA-256), not raw IP string |
| SEC-COP-006 | `test_data_deletion_removes_student_data` | Account deletion: student rows, assessment_responses, skill_states all deleted; consent row remains |
| SEC-COP-007 | `test_child_session_scope` | Student session token cannot call parent-scoped endpoints (GET /users/me, POST /students) |
| SEC-COP-008 | `test_no_third_party_pii_in_posthog` | PostHog events do not include `student_id`, `display_name`, or `email` fields |

**Example — SEC-COP-007:**
```python
# apps/api/tests/security/test_coppa_compliance.py

@pytest.mark.asyncio
async def test_child_session_token_cannot_access_parent_endpoints(
    student_session_client,  # fixture: AsyncClient with student-scoped JWT
):
    """Child session tokens must not access parent account endpoints."""
    # Parent endpoint — should be forbidden to child session
    response = await student_session_client.get("/api/v1/users/me")
    assert response.status_code == 403

    response = await student_session_client.post(
        "/api/v1/students",
        json={"display_name": "NewChild", "grade_level": 4, "avatar_id": "avatar_1"}
    )
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_no_pii_in_application_logs(
    authenticated_client, caplog, seeded_student_with_completed_assessment
):
    """Application logs must not contain student display names or email addresses."""
    import re
    student_name = "Jayden"
    parent_email = "maria@example.com"
    
    with caplog.at_level("DEBUG"):
        await authenticated_client.get(
            f"/api/v1/assessments/{seeded_student_with_completed_assessment.assessment_id}/results"
        )
    
    log_text = "\n".join(caplog.messages)
    assert student_name not in log_text, f"Student name '{student_name}' found in logs"
    assert parent_email not in log_text, f"Parent email found in logs"
    assert re.search(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}', log_text) is None
```

---

#### 3.7.4 SCA — Trivy Container Scanning

**Run:** Every container build in CI via GitHub Actions.

```yaml
# .github/workflows/ci.yml (container scan job)
  container-scan:
    runs-on: ubuntu-latest
    needs: build
    steps:
      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: '${{ env.ECR_REGISTRY }}/padi-ai-api:${{ github.sha }}'
          format: 'sarif'
          output: 'trivy-results.sarif'
          severity: 'CRITICAL,HIGH'
          exit-code: '1'  # Fail on CRITICAL or HIGH
      - name: Upload Trivy results to GitHub Security
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: 'trivy-results.sarif'
```

---

#### 3.7.5 PII Encryption Validation Tests

| Test ID | Test Name | What It Verifies |
|---------|-----------|-----------------|
| SEC-ENC-001 | `test_email_stored_encrypted` | Direct DB query: `users.email_encrypted` column is BYTEA (not plain text) |
| SEC-ENC-002 | `test_email_hash_is_sha256_length` | `users.email_hash` is exactly 64 hex characters |
| SEC-ENC-003 | `test_name_stored_encrypted` | `users.name_encrypted` column is BYTEA |
| SEC-ENC-004 | `test_decrypted_email_matches_input` | Decrypt `email_encrypted` via pgcrypto → matches original registration email |
| SEC-ENC-005 | `test_tls_13_enforced` | HTTPS response headers include `Strict-Transport-Security: max-age=31536000` |

---

### 3.8 Baseline Acceptance Criteria

All criteria must be met before Stage 1 is declared complete and ready for the 50-student pilot cohort.

#### Performance Gates

| Metric | Target | Measurement Tool |
|--------|--------|-----------------|
| Assessment next-question p95 latency | < 500ms | k6 load test at 1,000 VUs |
| Assessment response submission p95 | < 500ms | k6 load test |
| API error rate under load | < 0.1% | k6 |
| Assessment page initial load p95 | < 2,000ms | Playwright timing |
| PDF generation p95 | < 10,000ms | Integration test |
| Diagnostic results calculation | < 2,000ms | Integration test (timing assertion) |

#### Test Coverage Gates

| Layer | Target | Tool |
|-------|--------|------|
| Core business logic (BKT, scoring, CAT) | ≥ 90% line coverage | pytest-cov |
| API service and repository layer | ≥ 80% line coverage | pytest-cov |
| UI components | ≥ 70% line coverage | Vitest c8 |
| Mutation score (core algorithms) | ≥ 80% | mutmut |

#### Accessibility Gate

| Criterion | Tool | Threshold |
|-----------|------|-----------|
| axe-core automated scan (all pages) | Playwright + axe-core | Zero violations (Level AA) |
| Manual screen reader test (VoiceOver iOS) | Human tester | All form fields labeled; math expressions spoken |
| Color contrast | axe-core | Minimum 4.5:1 body text, 3:1 large text |

#### Security Gate

| Criterion | Threshold |
|-----------|-----------|
| Bandit HIGH/CRITICAL findings | Zero |
| Trivy CRITICAL/HIGH CVEs in container image | Zero |
| OWASP ZAP CRITICAL/HIGH alerts | Zero |
| COPPA-specific test suite pass rate | 100% |

#### Functional Gate

| Criterion | Target |
|-----------|--------|
| Seed question bank validated | 142 questions, all status='active' |
| Standards database completeness | 38 standards, all active |
| COPPA audit pre-launch legal review | Pass |
| Diagnostic accuracy vs. teacher report (pilot) | ≥ 85% agreement |

---

## 4. Operations Plan

### 4.1 MLOps

Stage 1 uses no generative AI (LLM calls are deferred to Stage 2). The MLOps scope here is limited to Bayesian Knowledge Tracing (BKT) parameter monitoring infrastructure — establishing observability now so Stage 3 calibration has historical data.

#### BKT Parameter Registry (Stage 1 Baseline)

Stage 1 BKT parameters are fixed, not learned. They are stored in `services/bkt-engine/tests/fixtures/skill_params.json` and versioned in Git. No runtime calibration occurs in Stage 1.

```json
// services/bkt-engine/tests/fixtures/skill_params.json (excerpt)
{
  "version": "1.0.0-stage1-defaults",
  "effective_date": "2026-06-01",
  "calibration_method": "expert_prior",
  "parameters": {
    "3.OA.C.7": { "p_l0": 0.10, "p_t": 0.10, "p_s": 0.10, "p_g": 0.20 },
    "4.NF.A.1": { "p_l0": 0.10, "p_t": 0.10, "p_s": 0.10, "p_g": 0.20 }
  }
}
```

#### BKT Monitoring Setup (Infrastructure-Only in Stage 1)

Although Stage 1 does not calibrate BKT parameters, the monitoring infrastructure is provisioned now to collect data for Stage 3 calibration:

**Metrics to collect from Day 1 (logged to Datadog):**

| Metric | Collection Point | Datadog Metric Name |
|--------|-----------------|---------------------|
| Per-skill diagnostic accuracy | Assessment completion | `bkt.diagnostic.skill_accuracy{standard_code}` |
| Initial P(mastered) assigned | BKT initialization | `bkt.init.p_mastered{standard_code}` |
| Low-confidence flag rate | BKT initialization | `bkt.init.low_confidence_rate{standard_code}` |
| Overall proficiency distribution | Assessment completion | `bkt.proficiency.distribution{level}` |
| Teacher agreement rate (pilot) | Manual survey input | `bkt.teacher_agreement_rate` |

**Datadog Dashboard:** A "BKT Health — Stage 1" dashboard is provisioned with these metrics visualized as time series. The dashboard is reviewed weekly during the 50-student pilot.

**Drift Detection (Passive in Stage 1):** A weekly GitHub Actions job (`llm-contract-tests.yml`) is repurposed for BKT parameter monitoring — it queries the `student_skill_states` table and produces a distribution report. If average P(mastered) for any standard deviates by > 0.20 from the expert prior, an alert is sent to the engineering Slack channel.

```python
# .github/workflows/bkt-monitoring.yml (cron job, weekly)
# Queries student_skill_states aggregate stats and reports to Datadog
import datadog
from apps.api.src.db.session import get_db_session

async def report_bkt_metrics():
    async with get_db_session() as session:
        rows = await session.execute(
            """
            SELECT standard_code,
                   AVG(p_mastered)      AS avg_p_mastered,
                   COUNT(*)             AS student_count,
                   SUM(CASE WHEN low_confidence THEN 1 ELSE 0 END) AS low_confidence_count
            FROM student_skill_states
            WHERE created_at > NOW() - INTERVAL '7 days'
            GROUP BY standard_code
            """
        )
        for row in rows:
            datadog.api.Metric.send(
                metric="bkt.weekly.avg_p_mastered",
                points=[(time.time(), float(row.avg_p_mastered))],
                tags=[f"standard:{row.standard_code}"],
            )
```

#### Model Version Registry

| Model | Version | Status | Notes |
|-------|---------|--------|-------|
| BKT Parameters | `v1.0.0-stage1-defaults` | Active | Expert-prior defaults; no EM training |
| CAT Difficulty Ladder | `v1.0.0-cat-lite` | Active | 1PL IRT equivalent; Stage 1 only |

No LLM prompt versioning is required in Stage 1 (no LLM calls).

---

### 4.2 FinOps

#### AWS Cost Allocation Tagging Strategy

All AWS resources created by Terraform for Stage 1 carry these mandatory tags:

```hcl
# infrastructure/terraform/modules/base_tags.tf
locals {
  base_tags = {
    Project     = "padi-ai"
    Stage       = "1"            # 1–5 across dev lifecycle
    Environment = var.environment  # "dev", "staging", "production"
    Team        = "engineering"
    CostCenter  = "stage1-foundation"
    ManagedBy   = "terraform"
  }
}
```

Feature-level cost allocation (for future LLM spend in Stage 2+):

| Tag Key | Values | Purpose |
|---------|--------|---------|
| `Feature` | `auth`, `assessment`, `standards`, `reporting` | Per-feature cost breakdown |
| `Environment` | `dev`, `staging`, `production` | Environment cost segregation |
| `Stage` | `1` through `5` | Lifecycle stage attribution |

#### Monthly Budget Thresholds (Stage 1)

| Environment | Service | Monthly Budget | Alert at 75% | Alert at 90% | Alert at 100% |
|------------|---------|---------------|-------------|-------------|--------------|
| Production | ECS Fargate | $150 | $112 | $135 | $150 |
| Production | RDS PostgreSQL 17 (db.t4g.medium, Multi-AZ) | $200 | $150 | $180 | $200 |
| Production | ElastiCache Redis (cache.t4g.small) | $30 | $22 | $27 | $30 |
| Production | S3 + CloudFront | $15 | $11 | $13 | $15 |
| Production | SES (transactional email) | $10 | $7 | $9 | $10 |
| Production | Secrets Manager | $5 | — | — | $5 |
| Production | Auth0 (Developer Plan) | $23 | — | — | $23 |
| **Production Total** | | **$433/mo** | $302 | $364 | $433 |
| Staging | All services | $80 | $60 | $72 | $80 |
| Development | All services | $40 | $30 | $36 | $40 |

**AWS Budget Alert Configuration:**
```hcl
# infrastructure/terraform/modules/monitoring/budgets.tf
resource "aws_budgets_budget" "stage1_production" {
  name         = "padi-ai-stage1-production"
  budget_type  = "COST"
  limit_amount = "433"
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  notification {
    comparison_operator = "GREATER_THAN"
    threshold           = 75
    threshold_type      = "PERCENTAGE"
    notification_type   = "ACTUAL"
    subscriber_email_addresses = ["eng-lead@padi.ai", "ops@padi.ai"]
  }

  notification {
    comparison_operator = "GREATER_THAN"
    threshold           = 90
    threshold_type      = "PERCENTAGE"
    notification_type   = "ACTUAL"
    subscriber_email_addresses = ["eng-lead@padi.ai"]
  }
}
```

#### Cost Anomaly Detection

AWS Cost Anomaly Detection is configured with a `DAILY` threshold: any day where spend exceeds 150% of the 7-day rolling average triggers an SNS alert to `#ops-alerts` in Slack.

#### Resource Right-Sizing

Stage 1 launches with minimum viable capacity. Auto-scaling policies prevent over-provisioning:

| Resource | Initial Size | Scale-Out Trigger | Max Size |
|---------|-------------|------------------|---------|
| ECS Fargate Tasks | 1 task (1 vCPU, 2GB) | CPU > 70% for 3 minutes | 10 tasks |
| RDS | db.t4g.medium | Manual resize at >80% CPU sustained | db.t4g.large (Month 3+ if needed) |
| ElastiCache | cache.t4g.small | Manual resize at >80% memory | cache.t4g.medium |

**FinOps Review Cadence:**
- Weekly review during active development (Months 1–3): 10-minute agenda item in Monday engineering sync.
- Monthly review in steady state (post-Stage 1 launch).
- Review checklist: compare actual vs. budget; identify top 3 cost drivers; check for idle resources; verify tagging compliance.

---

### 4.3 SecOps

#### COPPA Incident Response Plan (72-Hour FTC Notification)

A data breach involving children's personal information under COPPA requires FTC notification within 72 hours. The incident response runbook at `docs/runbooks/incident-response.md` defines:

**Phase 1 — Detect (0–1h):**
- Datadog alerting on anomalous query patterns (bulk SELECT on `students` or `assessment_responses`)
- Sentry error spike alerts (5xx errors, unusual volume)
- AWS GuardDuty: unusual API calls, network anomalies
- Manual report from user via privacy@padi.ai

**Phase 2 — Contain (1–4h):**
1. Engineering on-call (PagerDuty) acknowledges within 15 minutes.
2. Isolate affected ECS task(s): revoke IAM role, remove from target group.
3. Rotate Auth0 client secret and DB credentials immediately.
4. Preserve forensic evidence: snapshot RDS, export CloudTrail logs.
5. Notify engineering lead and legal counsel.

**Phase 3 — Eradicate (4–24h):**
1. Identify breach vector (DAST, code review, log analysis).
2. Deploy patch to staging; validate with security tests.
3. Assess scope: which student records were accessed/exfiltrated?

**Phase 4 — Recover (24–48h):**
1. Deploy patched containers to production.
2. Force re-authentication for all users (revoke all refresh tokens in Redis).
3. Notify affected parents by email with specific information: what data, when, remediation steps.

**Phase 5 — FTC Notification (≤72h from detection):**
1. Legal counsel drafts FTC notification per 16 CFR Part 312.
2. Notification sent to: FTC (online complaint form), affected parents, state AGs if required.
3. Notification must include: description of incident, types of data, number of children affected, steps taken, contact information.

**Phase 6 — Post-Mortem (within 1 week):**
- Blameless post-mortem document in `docs/runbooks/incident-postmortem-{date}.md`.
- Corrective actions tracked in GitHub Issues with P0 priority.

---

#### Secret Rotation Schedule

| Secret | Location | Rotation Frequency | Rotation Method |
|--------|----------|-------------------|-----------------|
| Auth0 Client Secret | AWS Secrets Manager | Every 90 days | Manual via Auth0 dashboard + `infrastructure/scripts/rotate-secrets.sh` |
| PostgreSQL master password | AWS Secrets Manager | Every 90 days | AWS RDS password rotation (automated) |
| SES SMTP credentials | AWS Secrets Manager | Every 90 days | AWS IAM key rotation |
| JWT signing key (Auth0 JWKS) | Auth0 managed | Automatic (Auth0 policy) | Auth0 auto-rotation; FastAPI validates against JWKS endpoint |
| Redis AUTH token | AWS Secrets Manager | Every 90 days | Manual + ECS task re-deploy |

**Rotation Monitoring:** A GitHub Actions cron job runs weekly and checks the `UpdatedAt` timestamp of each secret in Secrets Manager. If any secret is >80 days old, a Slack alert is sent to `#security-alerts`.

---

#### RBAC Access Control Matrix

| Role | Standards (Read) | Standards (Write) | Questions (Read) | Questions (Write/Approve) | Assessments (Read own) | Assessments (Read all) | Consent (Read) | Users (Read) | Users (Delete) | Audit Log (Read) |
|------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Unauthenticated | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Parent | ✓ | ✗ | ✗ | ✗ | ✓ | ✗ | Own only | Own only | Own only | ✗ |
| Student (session-scoped) | ✓ | ✗ | ✗ | ✗ | Own session | ✗ | ✗ | ✗ | ✗ | ✗ |
| Admin | ✓ | Draft | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ |
| Platform Operator (DB) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

**RBAC Implementation:** Auth0 `app_metadata.role` field (`"parent"` or `"admin"`) is included in the JWT `id_token`. FastAPI middleware reads this claim and enforces role checks via a `require_role(["admin"])` dependency injected into admin-only routes.

---

#### Audit Log Retention Policy

| Log Type | Location | Retention | Deletion Policy |
|---------|----------|-----------|----------------|
| `audit_log` table (DB) | PostgreSQL 17 RDS | Indefinite | Never deleted (append-only, no DELETE privilege for app role) |
| `consent_records` table | PostgreSQL 17 RDS | Indefinite | Never deleted (legal requirement) |
| CloudTrail logs | S3 (versioned bucket) | 7 years | Lifecycle policy: transition to Glacier after 90 days |
| Application logs (ECS) | CloudWatch Logs | 90 days | Automatic expiry |
| VPC Flow Logs | CloudWatch Logs | 30 days | Automatic expiry |
| Auth0 logs | Auth0 tenant | 30 days (free tier) | Exported to S3 via Auth0 Log Streams for longer retention |

**Quarterly Audit Log Review:** Every quarter, the engineering lead reviews a sample of 50 audit log entries across all tables to verify log completeness and that no PII appears in log fields where it should not.

---

#### Vulnerability Management SLA

| Severity | Resolution SLA | Notification |
|---------|---------------|-------------|
| Critical (CVSS 9.0–10.0) | 24 hours | Immediate PagerDuty + Slack |
| High (CVSS 7.0–8.9) | 72 hours | Slack `#security-alerts` |
| Medium (CVSS 4.0–6.9) | 14 days | GitHub Issue (P1) |
| Low (CVSS 0.1–3.9) | 90 days | GitHub Issue (P2) |
| Informational | Next sprint | GitHub Issue (P3) |

**Vulnerability Discovery Sources:** Trivy (CI), OWASP ZAP (weekly), Bandit (every PR), Dependabot (daily), GitHub Security Advisories (automated), manual penetration test (quarterly).

---

### 4.4 DevSecOps Pipeline

#### Full CI Pipeline (`.github/workflows/ci.yml`)

```
PR Opened / Push to PR branch
  │
  ├── 1. Lint & Format
  │     ├── ruff check apps/api/src services/ (Python)
  │     ├── mypy --strict apps/api/src services/ (Python type checking)
  │     ├── ESLint (TypeScript, with eslint-plugin-security)
  │     └── Prettier check (formatting)
  │
  ├── 2. Unit Tests
  │     ├── pytest apps/api/tests/unit/ (Python, with coverage)
  │     ├── pytest services/bkt-engine/tests/unit/ (BKT unit tests)
  │     └── vitest run apps/web/tests/unit/ packages/ (TypeScript)
  │
  ├── 3. SAST
  │     ├── bandit -r apps/api/src services/ --severity high --exit-code 1
  │     └── ESLint security rules (eslint-plugin-security)
  │
  ├── 4. Build
  │     ├── Docker build: infrastructure/docker/api.Dockerfile
  │     └── Next.js build: pnpm turbo run build --filter=@padi-ai/web
  │
  ├── 5. Container Scan
  │     └── trivy image --severity CRITICAL,HIGH --exit-code 1
  │
  ├── 6. Integration Tests (testcontainers)
  │     └── pytest apps/api/tests/integration/ (with PostgreSQL + Redis containers)
  │
  └── 7. Coverage Gate
        ├── pytest-cov: fail if core logic < 90%
        └── vitest --coverage: fail if UI < 70%
```

**Merge to `main` (`.github/workflows/deploy-staging.yml`):**
```
After CI passes on PR:
  ├── Deploy to staging (ECS task definition update)
  ├── Run Alembic migration on staging DB
  ├── Run Playwright E2E tests against staging
  └── Notify `#deployments` Slack channel
```

**Weekly Scheduled Jobs:**
```
.github/workflows/dependency-audit.yml (every Monday 03:00 UTC):
  ├── pip-audit (Python dependencies)
  ├── pnpm audit (Node.js dependencies)
  ├── OWASP ZAP scan against staging
  ├── Trivy filesystem scan (non-container)
  └── SBOM generation (Syft → SPDX JSON → S3)
```

#### SBOM Generation

Every weekly run and every production release generates a Software Bill of Materials:
```bash
# infrastructure/scripts/generate-sbom.sh
syft apps/api --output spdx-json=sbom-api-$(date +%Y%m%d).spdx.json
syft apps/web --output spdx-json=sbom-web-$(date +%Y%m%d).spdx.json
aws s3 cp sbom-api-*.spdx.json s3://padi-ai-sbom/stage1/
aws s3 cp sbom-web-*.spdx.json s3://padi-ai-sbom/stage1/
```

SBOMs are retained for 7 years (same as CloudTrail logs) for supply-chain accountability.

---

## 5. Manual QA Plan

Manual QA covers tests that cannot be reliably automated or that require human judgment. All manual QA is performed on real devices before Stage 1 launch and at the end of each development sprint.

---

### 5.1 COPPA Consent Flow Walkthrough (Zero-Defect Surface)

**Tester:** QA Engineer + Legal Representative
**Frequency:** Every sprint that touches auth or consent code; full walkthrough pre-launch
**Devices:** iPhone 15 (iOS 17), iPad 10th gen (iPadOS 17), Chromebook (Chrome OS)

**Walkthrough Script:**

| Step | Action | Pass Criteria | Fail Criteria |
|------|--------|--------------|--------------|
| 1 | Navigate to `/register` on each device | Registration form loads; above-the-fold text mentions children under 13 | Form loads without COPPA notice; form is below the fold on mobile |
| 2 | Submit form with valid data | Verification email received within 60 seconds | Email not received; email goes to spam; verification link fails |
| 3 | Navigate to consent page after email verification | Consent page loads with full Privacy Policy text visible (scrollable), not a link that requires opening a new window | Policy is hidden behind a link; policy text is truncated |
| 4 | Inspect both checkboxes before touching them | Both checkboxes are visually unchecked; no pre-selection state | Either checkbox appears checked; checkboxes look checked but attribute is unchecked (accessible state mismatch) |
| 5 | Attempt to submit with only one checkbox checked | Error message visible: "Please check both boxes to continue." No navigation occurs | Form submits; navigation occurs; no error shown |
| 6 | Check both boxes and submit | Confirmation email received within 60 seconds explaining 24-hour revocation window | Email not sent; email lacks revocation instructions |
| 7 | Click revocation link within 24 hours | Consent status is revoked; parent cannot create student profile; must re-consent | Revocation link does not work; revocation allows continued access |
| 8 | Re-consent after revocation | Re-consent flow works; second consent record created in DB | Re-consent not possible; only one consent record exists in DB |
| 9 | Request account deletion | "DELETE" + password dialog appears; upon confirmation, deletion email received | Deletion proceeds without confirmation; email not sent |
| 10 | Verify consent record exists after deletion | Query `consent_records` table (via admin DB access): row for deleted user still present | Consent record deleted along with user account |

**Legal Sign-Off Requirement:** The legal representative must sign off on steps 3, 5, 6, 7, and 10 before Stage 1 launch. Sign-off documented in `docs/legal-signoffs/stage1-coppa-consent-{date}.md`.

---

### 5.2 Accessibility Testing with Assistive Technology

**Tester:** QA Engineer with assistive technology expertise
**Tools:** VoiceOver (iOS 17, iPadOS 17), NVDA 2024 (Windows 11), TalkBack (Android 14)
**Frequency:** Pre-launch full audit; regression test for any assessment UI changes

**Screen Reader Test Matrix:**

| Flow | Screen Reader | OS | Pass Criteria |
|------|-------------|-----|--------------|
| Registration form | VoiceOver | iPadOS 17 | All form fields announced with label; error messages announced on validation failure |
| Consent form checkboxes | VoiceOver | iPadOS 17 | Checkbox role announced; checked/unchecked state announced on interaction |
| Assessment question (multiple choice) | NVDA | Windows 11 | Question text read in full; math expression aria-label spoken (e.g., "3 fourths"); option labels A, B, C, D announced; selected state announced |
| Fraction input | VoiceOver | iPadOS 17 | Numerator field: "numerator, required, text field"; denominator field: "denominator, required, text field" |
| Progress bar | VoiceOver | iPadOS 17 | "Question 12 of approximately 40" announced; domain progress dots announced |
| Results page | NVDA | Windows 11 | Section headings announced; bar chart values communicated via aria-label; skill names read, not standard codes |
| Parent dashboard | VoiceOver | iPadOS 17 | Child card status announced: "Jayden, Grade 4, Diagnostic: Not Started" |

**Math Expression Spoken Form Requirements:**

| KaTeX Expression | Required aria-label |
|-----------------|-------------------|
| `\frac{3}{4}` | "3 fourths" |
| `8 \times 7` | "8 times 7" |
| `24 \div 6` | "24 divided by 6" |
| `35 = 5 \times 7` | "35 equals 5 times 7" |
| `3\frac{1}{2}` | "3 and 1 half" |

---

### 5.3 Cross-Device Manual Testing Matrix

**Frequency:** Full matrix at sprint end; targeted device tests for UI changes

| Device | OS | Browser | Viewport | Priority Test Areas |
|--------|-----|---------|----------|-------------------|
| iPad 10th gen | iPadOS 17 | Safari | 1080×1668 portrait | Assessment question display, fraction input, results bars |
| iPad 10th gen | iPadOS 17 | Chrome | 1080×1668 portrait | KaTeX rendering, consent form |
| iPhone 15 | iOS 17 | Safari | 390×844 | Registration form, dashboard card layout, question tap targets |
| iPhone SE (3rd gen) | iOS 16 | Safari | 375×667 | Minimum screen width: all elements visible, no horizontal scroll |
| Chromebook (school-issued) | Chrome OS 122 | Chrome | 1366×768 | Full assessment flow; keyboard navigation |
| MacBook Air | macOS Sonoma | Safari | 1440×900 | Admin question management, PDF download |
| MacBook Air | macOS Sonoma | Chrome | 1440×900 | Registration, full assessment, results |
| MacBook Air | macOS Sonoma | Firefox | 1440×900 | KaTeX rendering, assessment |
| Surface Pro | Windows 11 | Edge | 1368×912 | Results display, PDF download |
| Android tablet (Pixel Tablet) | Android 14 | Chrome | 1280×800 | Assessment question display |

**Manual Test Checklist Per Device:**

- [ ] Registration form: All fields visible without horizontal scroll; submit button accessible
- [ ] Consent form: Both checkboxes visible and independently tappable (no overlapping hit areas)
- [ ] Assessment question: KaTeX renders correctly; answer options have ≥48px tap targets
- [ ] Assessment question: Fraction input fields are clearly separated numerator/denominator
- [ ] Progress bar: Readable without zooming
- [ ] Completion screen: Confetti animation renders (or is suppressed by prefers-reduced-motion)
- [ ] Results page: All 14 skill bars visible; bar animations play
- [ ] Parent dashboard: Child card status badge readable; CTA buttons clearly labeled

---

### 5.4 Curriculum Content Accuracy Review

**Reviewers:** Two Oregon-licensed math teachers (grades 3–6), independent of content authors
**Frequency:** One-time pre-launch review of all 142 seed questions; periodic review of new additions

**Review Criteria per Question:**

| Criterion | Pass | Fail |
|-----------|------|------|
| Mathematical accuracy | Answer is definitively correct; no ambiguity | Correct answer is wrong or ambiguous |
| Standard alignment | Question directly assesses the stated standard | Question assesses a different standard |
| Grade appropriateness | Language and context appropriate for 9–10 year olds | Vocabulary or context beyond Grade 4 reading level |
| Distractor quality | Each wrong answer corresponds to a documented misconception | Wrong answers are random, not plausible |
| Language clarity | Question reads clearly in one interpretation | Question is ambiguous or could be misread |
| Bias and fairness | Question does not disadvantage any demographic group | Cultural references unfamiliar to many Oregon students; gendered or stereotyped contexts |
| KaTeX accuracy | Math expressions render correctly and are conventionally notated | Math notation is non-standard or incorrect |

**Known High-Risk Question Types for Review:**
- Division-with-remainder word problems (FR-4.8: distractor quality is critical)
- Fraction comparison questions (multiple valid comparison methods)
- DOK-3 multi-step word problems (must not accidentally require DOK-4 reasoning)
- Geometry questions with protractor images (image accuracy is critical)

**Review Log:** Each reviewed question is logged in the admin interface with reviewer name, review date, pass/fail, and any notes. All 142 questions must have `is_validated = TRUE` and a named reviewer before launch.

---

### 5.5 Exploratory Testing

**Tester:** QA Engineer (unfamiliar with the codebase to maximize discovery)
**Session Duration:** 4 hours per session; 2 sessions pre-launch
**Method:** Charter-based exploratory testing. Each charter is a focused area with a goal and time box.

**Charter 1 — Child-Appropriate Language (1 hour):**
Goal: Verify all student-facing copy is age-appropriate (ages 9–10), encouraging, and non-judgmental.
- Read every screen in the student flow (assessment, completion, results) aloud as a 9-year-old would.
- Flag any: technical jargon, adult tone, negative language, confusing instructions.
- Check: the "encouraging copy" for each proficiency level (Below Par, On Par, Above Par) avoids words like "failing," "wrong," "behind."
- Check: the completion screen message names the student correctly using `display_name` (not email or ID).

**Charter 2 — Session Edge Cases (1 hour):**
Goal: Discover unexpected behavior at session boundaries.
- Start an assessment, close the browser tab mid-question, reopen on a different browser, attempt to resume.
- Start an assessment, let it sit idle for 65 minutes, attempt to submit an answer.
- Start an assessment on iPad, switch to iPhone, attempt to continue the same session.
- Open the assessment in two browser tabs simultaneously, answer in both; verify only one response is recorded.

**Charter 3 — Consent Flow Boundary Testing (1 hour):**
Goal: Find edge cases in the COPPA consent flow.
- Navigate directly to `/dashboard` as an unverified user (before email verification).
- Navigate directly to `/dashboard` as a verified-but-not-consented user.
- Navigate directly to `/onboarding/consent` with an already-active consent.
- Attempt to use browser back button after consent to "unconsent."
- Test consent with a VPN-assigned IP address (verify IP is still hashed correctly).

**Charter 4 — Admin Question Management (1 hour):**
Goal: Verify admin UI handles edge cases gracefully.
- Import a JSON file with 200 questions (performance test).
- Import a JSON file with one invalid question in the middle of 50 valid ones.
- Attempt to approve a question you authored (two-person rule).
- Deactivate a question that is currently in an in-progress assessment.
- Search for questions with special characters in the query (e.g., `'`, `"`, `<script>`).

**Defect Tracking:** All exploratory test findings are logged in GitHub Issues with label `qa-exploratory`, severity classification, and reproduction steps. P0 defects block launch.

---

### 5.6 Performance Perception Testing

**Purpose:** Verify that the application "feels fast" to parents and students beyond raw latency numbers.
**Method:** Moderated usability session with 3–5 pilot participants (parents of 4th graders).

**Perception Thresholds:**
- Question transition: Must feel "instant" (< 300ms perceived) when the next question appears after submission. The pre-fetch strategy should make transitions appear sub-200ms.
- Dashboard load: First meaningful paint should appear within 1 second on a typical home Wi-Fi connection (50Mbps down).
- Assessment start: From "Start Diagnostic" click to first question visible: < 2 seconds.
- PDF download start: Download dialog should appear within 3 seconds of clicking "Download PDF."

**Perception Test Method:**
1. Record a screen capture of a usability session with a parent participant.
2. Review the recording: note moments where the participant pauses, looks confused, or comments on speed.
3. Any moment where the participant waits > 2 seconds for feedback is flagged for investigation.

**Loading States Verification:**
- [ ] Dashboard: Skeleton cards shown during data fetch (no blank screen)
- [ ] Assessment: "Loading next question..." indicator appears before question transition
- [ ] Results: Skeleton bars shown while skill state data loads
- [ ] PDF: "Generating report..." progress indicator shown; button disabled during generation

---

*End of PADI.AI Stage 1 SDLC Lifecycle Document*

---

**Document Control**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-04-04 | Engineering Lead | Initial release |

**Review Sign-offs Required:**
- [ ] Engineering Lead — Architecture Review (Section 1)
- [ ] Product Manager — User Stories (Section 2)
- [ ] QA Lead — Test Plan (Section 3)
- [ ] DevOps Engineer — Operations Plan (Section 4)
- [ ] Legal Counsel — COPPA sections (3.7.3, 4.3, 5.1)

**Related Documents:**
- PRD Stage 1: `/home/user/workspace/docs/03-prd-stage1.md`
- Engineering Plan Stage 1: `/home/user/workspace/eng-docs/ENG-001-stage1.md`
- Engineering Foundations: `/home/user/workspace/eng-docs/ENG-000-foundations.md`
- Design System: `/home/user/workspace/docs/09-design-system.md`
