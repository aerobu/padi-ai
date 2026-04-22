# PADI.AI — SDLC Lifecycle Document
## Stage 5: MMP — Monetization, Polish & School Onboarding (Months 15–20)

**Document ID:** LCD-005  
**Stage:** 5 of 5 — Minimum Marketable Product (MMP)  
**Timeline:** Months 15–20  
**Status:** Draft  
**Last Updated:** 2026-04-04  
**Author:** Engineering Lead  
**Dependencies:** LCD-001 through LCD-004 (Stages 1–4 complete)  
**Source PRD:** `/home/user/workspace/docs/07-prd-stage5.md`  
**Source Engineering:** `/home/user/workspace/eng-docs/ENG-005-stage5.md`  
**Foundations:** `/home/user/workspace/eng-docs/ENG-000-foundations.md`  
**Cross-Cutting:** `/home/user/workspace/eng-docs/ENG-006-crosscutting.md`

---

## Table of Contents

1. [Architecture Review](#1-architecture-review)
2. [User Story Breakup](#2-user-story-breakup)
3. [Detailed Test Plan](#3-detailed-test-plan)
4. [Operations Plan](#4-operations-plan)
5. [Manual QA Plan](#5-manual-qa-plan)

---

## 1. Architecture Review

**Stage 5 Solo Development Total Estimate:** 115–180 agent-hours | Calendar: 8–10 months — MMP milestone

### 1.1 MMP System Context: MVP → MMP Evolution

Stage 5 is the commercial launch milestone. The system evolves from a functional MVP (Stage 4) serving 200 concurrent users to a commercially viable MMP capable of supporting 10,000 concurrent users, real-money transactions, institutional customers, multilingual content delivery, and data-driven product decisions — all while maintaining COPPA Safe Harbor certification for children under 13.

**System transformation summary:**

| Dimension | MVP (Stage 4) | MMP (Stage 5) |
|-----------|---------------|----------------|
| **Monetization** | Free beta | Stripe billing: Individual ($14.99/mo), Family ($24.99/mo), School (per-seat invoicing) |
| **Authentication** | Auth0 parent login | + Clever SSO, Google Workspace for Education, teacher/district admin roles |
| **Multi-tenancy** | Parent → students | District → School → Teacher → Classroom → Student hierarchy |
| **Localization** | English only | English + Spanish (UI, AI content, tutor prompts, emails, PDFs) |
| **Analytics** | Basic CloudWatch | PostHog event pipeline, COPPA-compliant cookieless tracking, A/B testing |
| **Scale** | 200 concurrent | 10,000 concurrent users (school-day peak) |
| **Compliance** | COPPA consent flow | + COPPA Safe Harbor (kidSAFE/PRIVO), FERPA DPA, Student Privacy Pledge |
| **Performance** | Best-effort CDN | CloudFront Origin Shield, read replicas, PgBouncer, auto-scaling ECS |
| **Messaging** | None | AWS SES transactional email, SQS async job queue |
| **Content** | ~500 questions | 10,000+ questions + video micro-lessons |
| **Engagement** | Basic sessions | Pip mascot (Lottie), 20+ badges, Weekly Math Missions, Study Together |

### 1.2 New Services Introduced in Stage 5

Six new containers are introduced alongside the existing API Service and Agent Engine:

| Service | Runtime | Responsibility |
|---------|---------|----------------|
| **Billing Service** | FastAPI (Python 3.12) | Stripe webhook processing, subscription state machine, checkout sessions, feature gating, school invoicing |
| **School Management Service** | FastAPI (Python 3.12) | District/school onboarding, Clever OAuth + nightly roster sync, DPA management, teacher/classroom CRUD |
| **Analytics Pipeline** | Python worker | PostHog event ingestion proxy, COPPA-compliant pseudonymization, A/B assignment engine, server-side analytics |
| **i18n Infrastructure** | Next.js middleware + CDN | Translation file delivery via CloudFront, next-intl locale routing, locale-aware API response shaping |
| **Async Job Queue** | SQS + Python worker | Question batch generation, PDF report generation, transactional email dispatch, nightly Clever sync |
| **Transactional Email** | AWS SES | Billing notifications, dunning sequence, school onboarding invitations, badge unlock parent alerts |

### 1.3 Full MMP Container Architecture (C4 Level 2)

```
┌──────────────────────────────────────────────────────────────────┐
│                         EXTERNAL USERS                           │
│  [Parent Browser]  [Student Browser]  [Teacher]  [School Admin]  │
└─────────────┬───────────────┬──────────────┬──────────┬──────────┘
              │               │              │          │
              ▼               ▼              ▼          ▼
┌──────────────────────────────────────────────────────────────────┐
│                      EDGE / CDN LAYER                            │
│  CloudFront (i18n files, static)  │  Vercel Edge (Next.js 15)   │
│  WAF (OWASP Core Rules, Rate Limiting, Geo-blocking)             │
└─────────────────────────────┬────────────────────────────────────┘
                              │
┌─────────────────────────────▼────────────────────────────────────┐
│                 APPLICATION LAYER (ECS Fargate)                  │
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ API Service  │  │ Agent Engine│  │   Billing Service       │  │
│  │ (FastAPI)    │  │ (FastAPI +  │  │   (FastAPI)             │  │
│  │ Auth middle  │  │  LangGraph) │  │   Stripe webhooks       │  │
│  │ REST endpts  │  │  Tutor Agent│  │   Checkout sessions     │  │
│  │ Progress API │  │  BKT Engine │  │   Feature gating        │  │
│  │ Report Gen   │  │  Hint Engine│  │   School invoicing      │  │
│  └──────┬──────┘  └──────┬──────┘  └────────────┬────────────┘  │
│         │                │                        │               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ School Mgmt │  │ Analytics   │  │   Async Job Worker      │  │
│  │ Service      │  │ Pipeline    │  │   (SQS consumer)        │  │
│  │ Clever OAuth │  │ PostHog     │  │   Question generation   │  │
│  │ Roster sync  │  │ proxy       │  │   PDF generation        │  │
│  │ DPA mgmt     │  │ A/B engine  │  │   Email dispatch        │  │
│  │ Teacher CRUD │  │ Event ingest│  │   Nightly Clever sync   │  │
│  └──────┬──────┘  └──────┬──────┘  └────────────┬────────────┘  │
└─────────┼────────────────┼───────────────────────┼───────────────┘
          │                │                        │
┌─────────▼────────────────▼───────────────────────▼───────────────┐
│                         DATA LAYER                               │
│  PostgreSQL 17 (RDS)     │  Redis (ElastiCache)   │  S3          │
│  - Primary + Read replica│  - Sessions            │  - i18n files│
│  - PgBouncer             │  - Feature cache (5m)  │  - PDFs      │
│  - pgvector              │  - Rate limits         │  - Audit logs│
│  - RLS policies          │  - BKT state cache     │  - DPA PDFs  │
│  SQS (job-queue + DLQ)   │  CloudFront Origin     │  Shield      │
└──────────────────────────────────────────────────────────────────┘
          │                │
┌─────────▼────────────────▼───────────────────────────────────────┐
│                      EXTERNAL SERVICES                           │
│  Auth0 │ Stripe │ Clever │ PostHog │ AWS SES │ Claude/o3-mini    │
└──────────────────────────────────────────────────────────────────┘
```

### 1.4 Billing System Architecture

#### 1.4.1 Subscription State Machine

The subscription lifecycle is a finite state machine driven entirely by Stripe webhook events. Every state transition is persisted atomically with an immutable audit log entry in `subscription_events`.

```
                    ┌──────────────────────────────────┐
                    │              TRIAL               │
                    │  (14-day free; all features)     │
                    └────────┬──────────┬──────────────┘
                             │          │
          invoice.payment_   │          │  customer.subscription.deleted
          succeeded          │          │  (no payment method at trial end)
          (first real charge)│          │
                             ▼          ▼
                    ┌──────────────────────────────────┐
                    │             ACTIVE               │◄──── reactivate
                    │  (recurring billing live)        │
                    └────┬──────────┬──────────────────┘
                         │          │
           invoice.       │          │  cancel_at_period_end=true
           payment_failed │          │
                          ▼          ▼
                  ┌───────────┐  ┌───────────┐
                  │ PAST_DUE  │  │ CANCELING │──► reactivate → ACTIVE
                  │ (retry    │  │ (active   │
                  │  1–3)     │  │  to end)  │
                  └─┬──────┬──┘  └─────┬─────┘
                    │      │           │ period_ended
               retry│      │all        ▼
             success│      │fail  ┌───────────┐
                    │      │      │ CANCELED  │──► resubscribe → TRIAL
                    │      └─────►│           │
                    │             └───────────┘
                    └──────────► ACTIVE

  School-only states:
  ACTIVE ──school_pause──► PAUSED ──resume──► ACTIVE
                                   └─expire──► EXPIRED
```

**State transition table:**

| Transition | Stripe Webhook | DB Action | Email Triggered |
|------------|---------------|-----------|-----------------|
| `trial_started` | `checkout.session.completed` | Create subscription row, state=TRIAL | Welcome + trial start |
| `trial_converted` | `invoice.payment_succeeded` (first charge) | state=ACTIVE, set `current_period_end` | Payment confirmation |
| `trial_expired_no_pay` | `customer.subscription.deleted` | state=CANCELED | Trial expired + upgrade CTA |
| `payment_success` | `invoice.payment_succeeded` | Extend `current_period_end` | Receipt email |
| `payment_failed` | `invoice.payment_failed` | state=PAST_DUE, set `past_due_since` | Dunning #1 |
| `retry_success` | `invoice.payment_succeeded` | state=ACTIVE, clear `past_due_since` | Payment recovered |
| `all_retries_failed` | `customer.subscription.deleted` | state=CANCELED | Final cancellation |
| `cancel_requested` | `customer.subscription.updated` (cancel_at_period_end=true) | state=CANCELING, set `cancel_at` | Cancellation confirmed |
| `period_ended` | `customer.subscription.deleted` | state=CANCELED | Subscription ended |
| `reactivate` | `customer.subscription.updated` (cancel_at_period_end=false) | state=ACTIVE, clear `cancel_at` | Reactivation confirmed |
| `upgrade` | `customer.subscription.updated` | Update `plan_id` | Upgrade confirmed |
| `downgrade` | `customer.subscription.updated` | Set `pending_plan_id` | Downgrade scheduled |
| `school_pause` | Manual admin action | state=PAUSED | School pause alert |
| `school_resume` | Manual admin action | state=ACTIVE | School resume alert |

#### 1.4.2 Stripe Webhook Processing Architecture

Webhook handlers adhere to four invariants: **signature verification first**, **idempotency via `stripe_event_id`**, **single atomic DB transaction**, and **async side effects via SQS**.

```python
# services/billing/webhook_handler.py
@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Idempotency check — return 200 immediately if already processed
    existing = await db.execute(
        select(StripeWebhookEvent).where(
            StripeWebhookEvent.stripe_event_id == event["id"]
        )
    )
    if existing.scalar_one_or_none():
        return {"status": "already_processed"}

    # Single atomic transaction: state update + audit log + dedup record
    async with db.begin():
        await process_stripe_event(event, db)
        await db.execute(
            insert(StripeWebhookEvent).values(
                stripe_event_id=event["id"],
                event_type=event["type"],
                payload_hash=sha256(payload).hexdigest(),
                status="processed",
            )
        )

    # Side effects enqueued AFTER commit (not inside transaction)
    await sqs_client.send_message(
        QueueUrl=settings.JOB_QUEUE_URL,
        MessageBody=json.dumps({"type": "webhook_side_effects", "event_id": event["id"]}),
    )
    return {"status": "ok"}
```

#### 1.4.3 Feature Gating Architecture

Feature access is determined by a two-tier cache: Redis (hot path, 5-minute TTL) backed by PostgreSQL (source of truth). Cache invalidation on every subscription state change via Redis pub/sub.

```
Client Request
    │
    ▼
API Middleware: require_feature("unlimited_practice")
    │
    ▼
Redis Cache: GET feature:{user_id}
    │
    ├─── HIT ──► Return feature set (cached)
    │
    └─── MISS ──► PostgreSQL: JOIN subscriptions + subscription_features
                     │
                     ▼
                  SET feature:{user_id} TTL=300s
                     │
                     ▼
                  Return feature set
```

**Feature tier matrix:**

| Feature | Free | Individual ($14.99) | Family ($24.99) | School (per-seat) |
|---------|------|--------------------|-----------------|--------------------|
| Diagnostic assessment | ✓ | ✓ | ✓ | ✓ |
| Practice (3 sessions/week) | ✓ | — | — | — |
| Practice (unlimited) | — | ✓ | ✓ | ✓ |
| AI tutor hints (3/session) | ✓ | — | — | — |
| AI tutor hints (unlimited) | — | ✓ | ✓ | ✓ |
| Parent dashboard (basic) | ✓ | Full | Full | — |
| Teacher classroom dashboard | — | — | — | ✓ |
| EOG readiness report | — | ✓ | ✓ | ✓ |
| Spanish language support | — | ✓ | ✓ | ✓ |
| Multiple student profiles | 1 | 1 | Up to 4 | Unlimited (roster) |
| School admin analytics | — | — | — | ✓ |
| Priority question generation | — | — | ✓ | ✓ |

### 1.5 School Onboarding Architecture

#### 1.5.1 Multi-Tenant Entity Hierarchy

```
District (e.g., "Portland Public Schools")
  ├── DistrictAdmin (user: DISTRICT_ADMIN role — sees all schools)
  │
  ├── School (e.g., "Rosa Parks Elementary")
  │     ├── SchoolAdmin (user: SCHOOL_ADMIN role)
  │     │
  │     ├── Teacher (user: TEACHER role)
  │     │     ├── Classroom ("Mrs. Johnson's 4th Grade — Period 2")
  │     │     │     ├── Student (via classroom_enrollments)
  │     │     │     └── Student
  │     │     └── Classroom ("Period 5")
  │     │
  │     └── Teacher
  │           └── Classroom
  │
  └── School (e.g., "Woodstock Elementary")
        └── ...
```

**Role permission matrix:**

| Role | Scope | Can View | Can Modify |
|------|-------|----------|------------|
| PARENT | Own children | Child progress, reports | Learning prefs, account |
| TEACHER | Own classrooms | Student progress in classrooms | Classroom settings |
| SCHOOL_ADMIN | Entire school | All teachers, students, analytics | Teacher assignments, school settings |
| DISTRICT_ADMIN | All schools | Everything in district | School admin assignments |
| SYSTEM_ADMIN | Global | Everything | Everything (audited) |

#### 1.5.2 Clever SSO Integration Flow

```
School Admin Browser ──1. Click "Connect Clever"──► PADI.AI School Mgmt Service
                     ◄──2. Redirect to Clever OAuth─────────────────────────────
                     ──3. Authenticate with district IDP──► Clever Login
                     ◄──4. Redirect with auth code──────────────────────────────
PADI.AI Callback ──5. Exchange code for tokens──► Clever Token API
                  ◄──6. {access_token, id_token}────────────────────────────────
                  ──7. Fetch district data (schools, teachers, sections, students)
                       via Clever Data API /v3.0/*
                  ──8. Create/update PADI.AI entities (district, schools, teachers,
                       students, classrooms) in PostgreSQL
                  ──9. Store refresh_token (encrypted via AWS Secrets Manager)
```

**Nightly roster sync:** EventBridge rule fires at 02:00 Pacific, enqueuing `sync_school_roster` job per active Clever connection. Sync reconciles delta: creates new students, updates name/grade changes, soft-unenrolls removed students (no data deletion), and flags parent/school conflicts for manual admin resolution.

**Conflict resolution policy:** When a parent-created student and Clever-imported student share the same name + school, a `merge_request` record is created. The school admin resolves in their dashboard (merge, keep separate, or dismiss). Parent consent required before school gains access to home-created learning history.

#### 1.5.3 FERPA DPA Flow

```
Step 1  District admin completes school profile (name, NCES ID, district, state=OR, billing contact)
Step 2  DPA displayed inline — must scroll to bottom (no click-through bypass)
Step 3  DPA signed: official name, title, typed signature, date captured
Step 4  dpa_agreements record created with SHA-256 content hash + S3-archived PDF
Step 5  DPA PDF emailed to school admin via SES
Step 6  PADI.AI co-signed DPA returned within 2 business days (manual; automated in MMP+)
Step 7  Student data access UNLOCKED — before Step 6, roster import and Clever sync are blocked
```

**FERPA data usage constraints (enforced in application layer + RLS):**

| Data Field | PADI.AI CAN | PADI.AI CANNOT |
|------------|-------------|-----------------|
| Student first/last name | Display to teacher/parent, reports | Share externally, marketing |
| Assessment responses | BKT algorithm, progress reports | Sell, non-educational use |
| Learning path progress | Teacher/parent dashboard, analytics | Student-level external sharing |
| Behavioral data | Aggregate anonymized product analytics | Individual tracking for ads |

#### 1.5.4 Data Isolation via PostgreSQL RLS

Every student-data table carries RLS policies enforced at the database layer (defense-in-depth on top of application-layer scoping):

```sql
-- services/billing/migrations/versions/V005_stage5_rls.sql
ALTER TABLE student_profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY parent_isolation ON student_profiles
    FOR ALL TO app_user
    USING (
        parent_id = current_setting('app.current_user_id')::uuid
        OR EXISTS (
            SELECT 1 FROM classroom_enrollments ce
            JOIN classrooms c ON c.id = ce.classroom_id
            WHERE ce.student_id = student_profiles.id
            AND c.teacher_id = current_setting('app.current_user_id')::uuid
        )
        OR EXISTS (
            SELECT 1 FROM school_admins sa
            JOIN classrooms c ON c.school_id = sa.school_id
            JOIN classroom_enrollments ce ON ce.classroom_id = c.id
            WHERE sa.user_id = current_setting('app.current_user_id')::uuid
            AND ce.student_id = student_profiles.id
        )
        OR EXISTS (
            SELECT 1 FROM district_admins da
            JOIN schools s ON s.district_id = da.district_id
            JOIN classrooms c ON c.school_id = s.id
            JOIN classroom_enrollments ce ON ce.classroom_id = c.id
            WHERE da.user_id = current_setting('app.current_user_id')::uuid
            AND ce.student_id = student_profiles.id
        )
    );
```

### 1.6 Internationalization Architecture

**Framework:** `next-intl` (native Next.js 15 App Router support, type-safe message keys, built-in `[locale]` segment routing, server-component-compatible `getTranslations()`).

**URL strategy:**
```
https://padi.ai/en/practice   → English practice
https://padi.ai/es/practice   → Spanish practice
https://padi.ai/en/dashboard  → English parent dashboard
https://padi.ai/es/dashboard  → Spanish parent dashboard
```

**Locale detection priority:** (1) User preference stored in DB → (2) URL path prefix → (3) `Accept-Language` header.

**Translation file structure:**
```
apps/web/messages/
├── en.json          # English UI strings (source of truth)
├── es.json          # Spanish UI strings
└── validation.ts    # Build-time key parity check (all en keys ∈ es)

services/agent-engine/prompts/
├── en/
│   ├── tutor_hint_v1.0.jinja2
│   ├── tutor_encouragement_v1.0.jinja2
│   └── question_generation_v1.0.jinja2
└── es/
    ├── tutor_hint_v1.0.jinja2        # Spanish system prompt additions
    ├── tutor_encouragement_v1.0.jinja2
    └── question_generation_v1.0.jinja2
```

**AI-generated question translation pipeline:**
1. Question generated in English, validated (correctness, grade-level, safety)
2. Prose/word problems translated via Claude Sonnet with math-domain context prompt
3. KaTeX math notation unchanged (universal across locales)
4. Spanish output validated: Fernández-Huerta readability (Grade 4–5), mathematical accuracy, cultural relevance to Oregon Hispanic community
5. Approved translations stored in `translation_memory` table with pgvector fuzzy matching for reuse

### 1.7 Analytics Pipeline Architecture

```
Student Browser ──(no cookies, memory-only PostHog)──► /ingest proxy (Next.js API route)
                                                           │
                                                           ▼
                                                    Analytics Worker
                                                    (COPPA pseudonymization)
                                                    actor_hash = SHA-256(actor_id + daily_salt)
                                                           │
                                         ┌─────────────────┼─────────────────┐
                                         ▼                 ▼                 ▼
                                    PostHog           analytics_events   ab_test_assignments
                                    (self-hosted       (PostgreSQL)       (PostgreSQL)
                                     or GCP)
```

**COPPA-compliant tracking rules:**
- Student events: session-memory only (no cookies), pseudonymous actor_hash, no PII in event properties
- Parent events: standard analytics (adults, standard consent)
- Analytics data retention: 13-month rolling window
- No cross-device tracking for students
- No third-party data export containing student identifiers

### 1.8 Auto-Scaling Architecture for 10,000 Concurrent Users

**Scaling targets:**
- School-day peak: 10,000 concurrent users (3:00–5:00 PM Pacific)
- P95 API latency < 500ms under full load
- P95 WebSocket (tutor) < 3s
- Error rate < 0.5% at peak
- Uptime SLA: 99.9% (school contract eligible)

**Infrastructure scaling configuration:**

| Component | Baseline | Peak | Scaling Trigger |
|-----------|---------|------|-----------------|
| API Service ECS | 2 tasks (2 vCPU, 4GB) | 20 tasks | CPU > 60% for 2 minutes |
| Agent Engine ECS | 2 tasks (4 vCPU, 8GB) | 16 tasks | Connection count > 200/task |
| Billing Service ECS | 2 tasks (1 vCPU, 2GB) | 4 tasks | CPU > 70% |
| School Mgmt ECS | 1 task (1 vCPU, 2GB) | 4 tasks | CPU > 70% |
| PostgreSQL RDS | db.r6g.large | db.r6g.xlarge | Manually promoted (planned capacity) |
| Read Replica | db.r6g.large | Add second replica | Read query lag > 10ms |
| Redis (ElastiCache) | cache.r6g.large | cache.r6g.xlarge | Memory > 75% |
| PgBouncer | 200 connections/task | Pool per task | Scaled with API tasks |

**CloudFront Origin Shield:** All static assets, i18n translation files, and cacheable API responses (question bank, badge definitions) served from Origin Shield before touching origin servers. Expected cache hit ratio ≥ 85% for static content.

### 1.9 Key Architectural Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Payment processor | Stripe (Stripe Elements, no card data on server) | PCI-DSS SAQ-A compliance; eliminates PCI scope for PADI.AI servers |
| Webhook idempotency mechanism | Unique constraint on `stripe_event_id` in PostgreSQL | Atomic, crash-safe; no distributed lock needed |
| Subscription state machine location | Billing Service only (single source of truth) | Prevents state drift from multiple writers |
| School SSO provider | Clever (primary) + Google Workspace | Clever covers 95% of US K-12; GWS covers Google-native districts |
| i18n framework | next-intl over react-i18next | Native App Router RSC support; tree-shakes unused locales |
| Analytics platform | PostHog (self-hosted) | COPPA-safe: student data never leaves our infrastructure |
| COPPA Safe Harbor program | kidSAFE first, PRIVO post-MMP | 3–6 month timeline fits Month 15–20 window; kidSAFE recognized by FTC |
| Multi-tenancy isolation | PostgreSQL RLS + application-layer filtering | Defense-in-depth: RLS catches application bugs; application logic provides readable access patterns |
| Mascot animation | Lottie JSON (≤200KB total) | Performant; respects `prefers-reduced-motion`; JSON format allows designer iteration |
| Async jobs | SQS with DLQ | Decouples email, PDF gen, question gen from request path; DLQ captures failed jobs |

### 1.10 Integration Points with Previous Stages

| Stage | Integration Point | How Stage 5 Extends |
|-------|-----------------|---------------------|
| Stage 1 (Standards DB) | 29 Oregon standards + 9 prerequisites | School admin dashboard aggregates standard mastery across all classrooms; question bank expansion targets all 29 standards at 150+ questions/skill |
| Stage 2 (Question Gen) | o3-mini question generation pipeline | Async Job Queue handles bulk generation (10,000+ target); translation pipeline adds Spanish variants |
| Stage 3 (AI Tutor) | LangGraph tutor agent | Spanish language prompt variants added; `prefers-reduced-motion` flag passed to Pip animation controller |
| Stage 4 (Assessment + Reporting) | BKT states, EOG assessment, PDF reports | Feature gating restricts EOG to paid tiers; school admin dashboard aggregates BKT states across enrolled students; reports generated in Spanish |

### 1.11 Risk Areas and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Stripe webhook delivery failure causing subscription state drift | Medium | High | Idempotency table + Stripe dashboard reconciliation job (nightly); SQS-backed retry for side effects |
| Clever API rate limiting during large district sync | Medium | Medium | Exponential backoff with jitter; incremental pagination; sync at 02:00 AM off-peak |
| COPPA Safe Harbor certification delayed past Month 20 | Low | High | Start kidSAFE application at Month 15 kickoff; have legal counsel engaged immediately |
| PostgreSQL read replica lag under 10K concurrent user peak | Medium | Medium | PgBouncer connection pooling; Origin Shield cache; feature cache TTL absorbs read spikes |
| Spanish translation quality for math word problems | Medium | Medium | Human translator review for all human-authored content; bilingual math expert review for AI-generated golden set |
| Payment failure dunning causing parent churn | Low | Medium | Stripe Smart Retries; dunning email sequence at days 0/3/7; 7-day grace period preserves student access |
| DPA signing flow legal ambiguity | Low | High | Legal counsel reviews DPA template before Stage 5 launch; school pilot before public launch |

---

## 2. User Story Breakup

Stories are organized by epic, derived from FR-21 through FR-26. Dependencies are noted. Priority scale: P0 = MMP blocker, P1 = MMP required, P2 = MMP preferred, P3 = post-MMP.

### Epic 1: Subscription & Billing (FR-21)

**Solo Development Estimate:** 30–45 agent-hours | Calendar: ~3–5 weeks (state machine + webhooks require careful testing)

---

**MATH-501 — Freemium Feature Gating**  
*As a product owner, I want all app features to be gated by subscription tier so that free users experience value while paid users receive full access.*

**Acceptance Criteria:**
- Free users are limited to 3 practice sessions per week (resets every Monday 00:00 Pacific)
- Free users see only the first 5 skills of their learning plan
- Free users receive 3 AI tutor hints maximum per session (not per week)
- Paid users see no session count limits and access all 29 skills
- Feature gating checks Redis cache first (TTL 5 minutes), then PostgreSQL
- Cache is invalidated within 30 seconds of any subscription state change via Redis pub/sub
- Free users see upgrade prompts at each gated feature (non-blocking modal, dismissible)
- Feature flag `unlimited_practice` resolves correctly for all 7 subscription states (trial, active, past_due, canceling, canceled, paused, expired)
- Graceful degradation: if Redis is unavailable, falls back to DB query within 100ms circuit breaker timeout

**Priority:** P0 | **Points:** 8 | **Dependencies:** None

---

**MATH-502 — Stripe Checkout Session (New Subscriptions)**  
*As a parent, I want to start a subscription by entering my payment details through a secure checkout so that I can unlock premium features for my child.*

**Acceptance Criteria:**
- Stripe Elements checkout embedded at `/settings/billing/upgrade` — no card data transmitted to PADI.AI servers
- Parent selects plan (Individual/Family) and billing period (monthly/annual) before checkout
- 14-day free trial applied automatically for first-time subscribers (`trial_period_days=14`)
- Checkout completion creates subscription record in `subscriptions` table with `state=TRIAL`
- Parent receives welcome email + trial start confirmation within 2 minutes of checkout
- Subscription confirmation page shown in < 3 seconds of Stripe redirect
- Checkout form meets WCAG 2.1 AA (keyboard navigable, error messages associated with inputs)
- Checkout page fully translated in Spanish when locale is `es`
- Stripe customer ID stored on `users.stripe_customer_id` (idempotent: existing customer reused)

**Priority:** P0 | **Points:** 8 | **Dependencies:** MATH-501

---

**MATH-503 — Stripe Webhook State Machine**  
*As the system, I want all Stripe webhook events to reliably drive subscription state transitions so that billing state in PADI.AI always reflects Stripe's source of truth.*

**Acceptance Criteria:**
- All 8 webhook event types handled: `checkout.session.completed`, `invoice.payment_succeeded`, `invoice.payment_failed`, `customer.subscription.updated`, `customer.subscription.deleted`, `invoice.created`, `invoice.finalized`, `payment_intent.payment_failed`
- Webhook signature verified via `stripe.Webhook.construct_event()` before any processing; unsigned requests rejected with HTTP 400
- Idempotency: duplicate `stripe_event_id` returns HTTP 200 immediately without reprocessing
- Out-of-order tolerance: stale events (DB record newer than event's `updated` timestamp) are skipped
- All state mutations (subscription update + audit log + dedup record) execute in single atomic PostgreSQL transaction
- Email notifications and cache invalidation enqueued to SQS after transaction commit (not inside)
- Failed webhook processing: status set to `failed` with error message in `stripe_webhook_events`; Stripe retries within 24 hours
- Webhook endpoint returns HTTP 200 within 5 seconds; heavy processing delegated to async workers
- Every state transition produces an immutable row in `subscription_events` with previous/new state

**Priority:** P0 | **Points:** 13 | **Dependencies:** MATH-502

---

**MATH-504 — Subscription Management UI**  
*As a parent, I want to manage my subscription (upgrade, downgrade, cancel, pause, reactivate) from my account settings so that I have full control over my billing.*

**Acceptance Criteria:**
- `/settings/subscription` displays current tier, billing period, next charge date, and amount
- Upgrade path: Individual → Family prorated immediately; proration amount shown before confirmation
- Downgrade path: Family → Individual scheduled for period end; banner shows effective date
- Cancel: parent chooses "Cancel immediately" or "Cancel at period end"; both confirm via modal with feature-loss warning
- Pause: available once per year for 30 days; sets `subscription.pause_collection` in Stripe; banner shows during pause
- Reactivate: one-click from `/settings/subscription` when in `canceled` state; retains all student progress
- Change billing period: monthly → annual shows proration credit; annual → monthly shows next cycle date
- All actions confirmed via explicit modal with consequences described in plain language
- Subscription portal powered by Stripe Customer Portal for payment method updates (no raw card data in PADI.AI UI)

**Priority:** P1 | **Points:** 8 | **Dependencies:** MATH-503

---

**MATH-505 — Payment Failure & Dunning Sequence**  
*As the system, I want to notify parents of payment failures and retry intelligently so that we recover revenue while minimizing subscription cancellations.*

**Acceptance Criteria:**
- Day 0 (payment_failed webhook): dunning email #1 sent via SES — "Your payment didn't go through — please update your payment method"
- Day 3 (Stripe retry fails): dunning email #2 sent
- Day 7 (Stripe retry fails): dunning email #3 sent + in-app banner shown at every login: "Action needed: Update payment method"
- Day 14 (all retries exhausted): subscription state set to CANCELED; downgrade to free tier; email "Your subscription has ended"
- Grace period: student access to paid features preserved for 7 days from initial failure (not 14 days)
- Student data is NEVER deleted due to payment failure
- Reactivation link included in all dunning emails; one-click reactivation restores previous tier
- In-app banner dismissible but re-shown at next login until resolved
- All dunning emails translated in Spanish when parent locale is `es`
- Stripe Smart Retries used (not fixed schedule); PADI.AI emails align to actual retry events

**Priority:** P0 | **Points:** 5 | **Dependencies:** MATH-503

---

**MATH-506 — School Invoicing**  
*As a school admin, I want to pay by purchase order invoice instead of credit card so that school procurement processes are accommodated.*

**Acceptance Criteria:**
- School accounts can select "Pay by Invoice" at Classroom plan checkout
- Invoice form collects: PO number (optional), billing contact name, billing email, billing address
- Stripe Invoice object generated; invoice PDF emailed to billing contact via SES within 5 minutes
- Payment terms: Net 30 displayed on invoice
- Invoice status tracked in PADI.AI (`pending`, `paid`, `overdue`)
- Renewal invoice sent 45 days before contract expiry via SES
- School admin can download invoice PDF from `/admin/billing` at any time
- `subscriptions.po_number` stored and displayed in school admin billing view
- Annual-only billing for Classroom tier enforced (no monthly school subscriptions)

**Priority:** P1 | **Points:** 5 | **Dependencies:** MATH-503

---

### Epic 2: School & District Onboarding (FR-22)

**Solo Development Estimate:** 35–50 agent-hours | Calendar: ~4–6 weeks (RLS + Clever SSO)

---

**MATH-511 — School Admin Account Type**  
*As a school technology director, I want a dedicated school admin account so that I can manage teachers, students, and billing for my school in one place.*

**Acceptance Criteria:**
- New account type `SCHOOL_ADMIN` in Auth0 with corresponding RBAC role
- School admin can create teacher accounts by email invitation
- School admin can view all classrooms and student progress within their school
- School admin can manage school subscription: seat count, billing contact, invoice download
- School admin CANNOT view individual session transcripts (teacher-only with parent consent)
- School admin CANNOT modify individual student learning plans
- School admin CANNOT access raw BKT parameters (aggregate views only)
- School admin dashboard accessible at `/admin/school` (distinct from parent and teacher dashboards)
- District admin role added: sees all schools within district; cannot see schools outside their district

**Priority:** P0 | **Points:** 8 | **Dependencies:** MATH-506

---

**MATH-512 — FERPA DPA Flow**  
*As a school district official, I want to review and electronically sign a FERPA Data Processing Agreement so that my school's use of PADI.AI is legally compliant.*

**Acceptance Criteria:**
- DPA displayed inline at school onboarding step 2 — must scroll to bottom (progress indicator shown)
- DPA content includes: data categories, use limitations, retention schedule, security measures, subprocessors list, FERPA acknowledgment, privacy officer contact
- Signing captures: official name, title, typed signature, timestamp, IP address
- `dpa_agreements` record created with SHA-256 hash of signed DPA content
- Signed DPA PDF generated (via async job) and emailed to school admin within 10 minutes
- PDF archived in S3 at `s3://padi-ai-dpa/{district_id}/{agreement_id}.pdf`
- Student data access BLOCKED until DPA is fully executed (signed and countersigned)
- DPA version tracked (`dpa_version` field); legal team controls version bumps
- Existing schools notified 60 days before DPA expiration with renewal link

**Priority:** P0 | **Points:** 8 | **Dependencies:** MATH-511

---

**MATH-513 — CSV Roster Import**  
*As a school admin, I want to bulk-import student rosters from a CSV file so that I can onboard an entire school without manual student-by-student entry.*

**Acceptance Criteria:**
- CSV format: `first_name, last_name, grade, teacher_email, student_id_local`
- Upload via `/admin/roster/import`; async processing for files > 100 rows
- Validation: required columns present, grade=4 enforced (v1 supports Grade 4 only), teacher emails valid
- Preview shown before import: "Importing 28 students. 2 new teacher accounts will be invited. Proceed?"
- Import result page: success count, error rows with reason code, downloadable error CSV
- Duplicate `student_id_local` within same school: skip row, report as duplicate
- New teacher accounts: invitation email sent to teacher_email via SES; account created on first login
- Import limited to 1,000 students per upload (larger districts use multi-file or Clever SSO)
- Import is idempotent: re-importing same `student_id_local` updates existing record rather than creating duplicate
- COPPA note included in UI: school import covered by FERPA school official basis; DPA must be signed first (gate enforced)

**Priority:** P0 | **Points:** 8 | **Dependencies:** MATH-512

---

**MATH-514 — Clever SSO Integration**  
*As a district IT administrator, I want to connect PADI.AI to our Clever instance so that teachers and students log in with their existing school credentials and rosters sync automatically.*

**Acceptance Criteria:**
- Clever OAuth 2.0 authorization code flow implemented at `/auth/clever/callback`
- CSRF state token verified on callback; mismatched state rejected
- Auth code exchanged for `access_token` + `id_token` at Clever Token API
- District data fetched via Clever Data API v3.0 (`/v3.0/me`, `/v3.0/districts/*`, `/v3.0/schools/*`, `/v3.0/sections/*`, `/v3.0/students/*`)
- Role mapping: `clever.type = student → STUDENT`, `teacher → TEACHER`, `district_admin → SCHOOL_ADMIN`
- Clever `refresh_token` stored encrypted (AWS KMS) in `sso_connections.refresh_token`
- Nightly sync: EventBridge fires at 02:00 Pacific → SQS job → sync worker per active connection
- Sync creates new students, updates changed records, soft-unenrolls removed students
- Conflict (parent-created + Clever-imported same student): `merge_request` created; school admin resolves via dashboard UI
- Manual on-demand sync available from school admin dashboard
- Sync status and results displayed in `/admin/sso` (students_created, students_updated, merge_requests, errors)

**Priority:** P1 | **Points:** 13 | **Dependencies:** MATH-512

---

**MATH-515 — Google Workspace for Education SSO**  
*As a teacher at a Google Workspace school, I want to log in to PADI.AI using my school Google account so that I don't need a separate password.*

**Acceptance Criteria:**
- Google OAuth 2.0 flow configured with scopes: `email`, `profile` only (no Drive, Classroom API)
- School admin configures Google Workspace domain in `/admin/sso/google` (e.g., `hillcrest.k12.or.us`)
- Only users authenticating from the configured domain are auto-provisioned as school accounts
- Users from unconfigured domains fall through to standard Auth0 login
- First login: student/teacher record created and linked to roster (by student_id_local or email match)
- `Sign in with Google (School)` button shown on login page when school domain is detected via email prefix
- Auto-provisioned accounts inherit role from Clever roster data if both SSO methods active

**Priority:** P1 | **Points:** 5 | **Dependencies:** MATH-514

---

**MATH-516 — School Admin Dashboard**  
*As a school admin, I want a school-wide analytics dashboard so that I can monitor student progress, identify struggling classrooms, and track standards coverage across the school.*

**Acceptance Criteria:**
- Proficiency distribution chart: % of students at each level (Below Par / Approaching / On Par / Above Par)
- Domain heatmap: average domain score per domain across all enrolled students
- Trend comparison: current vs. beginning-of-year diagnostic results
- Active students widget: % of enrolled students with ≥1 session in current week
- Classroom comparison table: teacher name, active student %, avg proficiency, avg skills mastered (per classroom)
- Framing: "each class's learning journey" — no teacher ranking language
- Standards coverage grid: 29 standards × N classrooms — % of students with P(mastered) ≥ 0.80 per cell; red/yellow/green coloring
- Oregon DOE-format report downloadable: per-student (anonymized with local ID) proficiency + practice time; school-wide standard mastery rates
- Dashboard data sourced from read replica (not primary PostgreSQL) to prevent analytics queries impacting learning sessions
- Page load P95 < 2 seconds with 500 enrolled students

**Priority:** P1 | **Points:** 8 | **Dependencies:** MATH-513

---

### Epic 3: Enhanced UX & Engagement (FR-23)

**Solo Development Estimate:** 25–40 agent-hours | Calendar: ~3–5 weeks (math vocabulary requires bilingual curriculum consultant)

---

**MATH-521 — Pip Mascot (Animated)**  
*As a student, I want to interact with a friendly animated mascot named Pip so that practicing math feels encouraging and fun.*

**Acceptance Criteria:**
- Pip implemented as Lottie animations (6 JSON files): `neutral`, `happy`, `thinking`, `encouraging`, `celebrating`, `sad_encouraging`
- Total animation asset size ≤ 200KB
- `prefers-reduced-motion: reduce` detected → static PNG fallback shown for all Pip states
- Pip `happy` animation triggers on correct answer (< 300ms after answer submit)
- Pip `encouraging` triggers on incorrect answer or hint request
- Pip `celebrating` triggers on skill mastery event (P(mastered) crosses 0.80)
- Pip `thinking` shown during question load / BKT computation
- Pip `sad_encouraging` triggers on scaffolded mode activation (3+ consecutive incorrect)
- Pip design: gender-neutral, Oregon-themed (teal/gold, rain hat), no human ethnicity cues
- Pip animations tested across Chrome, Firefox, Safari, Edge (latest 2 versions)
- Pip present in student practice view, onboarding tutorial, session summary

**Priority:** P1 | **Points:** 8 | **Dependencies:** None

---

**MATH-522 — Achievement Badge System (20+ Badges)**  
*As a student, I want to earn achievement badges as I practice and make progress so that I feel recognized for my hard work.*

**Acceptance Criteria:**
- 21 badge definitions seeded in `badge_definitions` table (First Session, Hint Hero, Fast Learner, 3-Day Streak, Week Warrior, Month Maven, Fraction Flyer, Operations Ace, Measurement Master, Number Ninja, Geometry Genius, Oregon Scholar, Assessment Ready, Challenge Accepted, On Par, Above Par, Century Club, Hint Refuser, Challenge Seeker, Session Superstar, Math Mission Complete, Study Partner)
- Badge criteria evaluated as async post-session job (not blocking session completion)
- `student_badges` table stores badge_id, student_id, earned_at, context JSONB (skill_code, session_id)
- Each badge can only be earned once per student (UNIQUE constraint enforced)
- Badge unlock notification shown in-app as animated toast (within 30 seconds of session completion)
- Badge shelf shown on student profile page: all earned badges with unlock date
- 5 most recently earned badges shown on session summary screen
- Parent email notification sent when badge unlocked: "Your child earned: Week Warrior!"
- Badge names and descriptions available in English and Spanish (`name_en`, `name_es`, `description_en`, `description_es`)

**Priority:** P1 | **Points:** 8 | **Dependencies:** MATH-521

---

**MATH-523 — Weekly Math Missions**  
*As a student, I want to take on a weekly Math Mission challenge so that I have a special goal to work toward each week.*

**Acceptance Criteria:**
- Math Mission released every Monday 00:00 Pacific; expires following Sunday 23:59 Pacific
- Mission: 15 curated questions, multiple skills/domains, harder than standard practice
- Oregon context themes used (e.g., "Crater Lake Expedition", "Oregon Tide Pools Adventure")
- No hints available during mission (challenge-only; Pip encourages without hinting)
- Mission completion award: "Math Mission Complete!" badge + double Pip celebration animation
- Homepage widget: mission title + countdown timer showing days/hours remaining
- Mission optional: student advances learning plan regardless of mission participation
- 52 pre-authored missions per grade stored in `math_missions` + `mission_questions` tables
- `student_mission_attempts` records attempt start, current question, and completion status
- Mission abandonment: student can resume from current position within the week

**Priority:** P2 | **Points:** 5 | **Dependencies:** MATH-522

---

**MATH-524 — Study Together Mode**  
*As a parent, I want to practice math with my child in a joint session so that I can support their learning directly on the same device.*

**Acceptance Criteria:**
- "Study Together" accessible from parent dashboard → child profile page
- Parent selects a skill from child's current in-progress skills
- Session uses same adaptive question engine; no Pip hints (parent is hint-giver)
- Session labeled `session_mode = 'study_together'` in `practice_sessions`
- BKT updates normally from study together responses
- Session summary shows "Great time together!" framing with skills practiced and questions answered
- Study Together sessions counted toward child's session total but NOT toward free-tier session cap
- `study_partner` badge unlocked after first completed study together session
- Supports both English and Spanish (locale follows student language preference)

**Priority:** P2 | **Points:** 5 | **Dependencies:** MATH-521

---

**MATH-525 — Handwriting Recognition (Tablet Input)**  
*As a student using an iPad or Android tablet, I want to write my numeric answer by hand instead of typing it so that the experience feels more natural for math.*

**Acceptance Criteria:**
- Canvas draw area replaces numeric keypad on touch devices (detected via `navigator.maxTouchPoints > 1` AND screen width ≤ 1024px)
- Client-side OCR via `tesseract.js` (numeric mode) or `mathpix.js`
- Recognized number shown in "Did you write [X]?" confirmation step before submission
- If recognition confidence < 0.80: "I'm not sure what you wrote — can you use the keypad?" — numeric keypad shown as fallback
- Toggle: student switches between handwriting and keypad mode any time (persists in session)
- Handwriting input respects `prefers-reduced-motion` (canvas clears without animation)
- Handwriting recognition runs entirely client-side (no student handwriting data sent to server)
- OCR library bundle size impact ≤ 500KB gzipped (lazy-loaded; not in initial bundle)
- Accuracy baseline target: ≥ 90% recognition accuracy for single-digit numbers; ≥ 85% for multi-digit (≤6 digits) in controlled testing

**Priority:** P2 | **Points:** 8 | **Dependencies:** None

---

**MATH-526 — Dark Mode & Accessibility Theme**  
*As a student or parent, I want a dark mode and high-contrast accessibility options so that PADI.AI is comfortable to use in different lighting conditions and for users with visual needs.*

**Acceptance Criteria:**
- Dark mode triggered by `prefers-color-scheme: dark` (automatic) or manual toggle in settings
- Dark mode palette: navy/charcoal backgrounds, high-contrast cream text, teal/gold accents at reduced brightness
- KaTeX equations render correctly in dark mode (custom dark-mode CSS overrides)
- Math Mission themes and PDF reports remain in light mode (print-friendly)
- High-contrast mode: black/white, no gradient backgrounds; available in Student Settings → Accessibility Options
- Large text mode: base font size +4px applied globally; no layout breakage verified at all breakpoints
- Theme preference stored per user in DB (`users.theme_preference`)
- All theme variants pass WCAG 2.1 AA (axe-core zero violations in each mode)
- Dark mode tested on: Chrome, Firefox, Safari, Edge (latest 2 versions) + iOS Safari + Android Chrome

**Priority:** P1 | **Points:** 5 | **Dependencies:** None

---

**MATH-527 — Full Spanish Language Support**  
*As a Spanish-speaking parent or student, I want to use PADI.AI entirely in Spanish so that language is not a barrier to accessing math support.*

**Acceptance Criteria:**
- All UI strings (menus, buttons, labels, notifications, error messages) translated to Spanish in `es.json`
- Build-time validation: `validation.ts` fails build if any `en.json` key is missing from `es.json`
- AI Tutor (Pip) responds in Spanish when `student.language_preference = 'es'` (system prompt addition applied)
- Practice questions translated to Spanish; translation stored in `questions.text_es`; served based on locale
- Parent dashboard fully translated (all views, widgets, charts labels)
- All transactional emails have Spanish templates (welcome, dunning, badge unlock, trial reminder)
- Progress report PDFs generated in Spanish when locale is `es`
- Language toggle available in app header: "English / Español"
- Language preference set during parent account setup; student language defaults to parent language; overridable
- URL prefix routing: `/es/practice`, `/es/dashboard` etc. via next-intl middleware

**Priority:** P1 | **Points:** 13 | **Dependencies:** None

---

### Epic 4: Analytics & A/B Testing (FR-24)

**Solo Development Estimate:** 15–25 agent-hours | Calendar: ~2–3 weeks

---

**MATH-531 — PostHog Analytics Integration**  
*As a product team, I want all key user actions tracked in PostHog so that we can measure funnel conversion, retention, and feature engagement.*

**Acceptance Criteria:**
- PostHog initialized with `persistence: 'memory'` (no cookies for student accounts), `autocapture: false`
- All events proxied through `/ingest` Next.js API route (no direct browser-to-PostHog calls)
- Student events pseudonymized: `actor_hash = SHA-256(student_id + daily_salt)` — no student PII in PostHog
- Core student events captured: `student_session_started`, `student_question_answered`, `student_hint_requested`, `student_session_completed`, `student_skill_mastered`, `student_assessment_completed`
- Core parent events captured: `parent_signup_completed`, `parent_subscription_started`, `parent_report_downloaded`, `parent_share_with_teacher`
- Funnel defined in PostHog: Signup → Diagnostic → First Session → D7 Active → Subscription
- Analytics data retained for 13-month rolling window (configured in PostHog data retention settings)
- Zero PII fields in any event properties (verified by automated event schema tests)
- Event ingestion latency < 100ms (async; does not block UI interactions)

**Priority:** P1 | **Points:** 8 | **Dependencies:** None

---

**MATH-532 — A/B Testing Framework**  
*As a product manager, I want a server-side A/B testing framework so that we can run controlled product experiments without cookie-based tracking or COPPA risks.*

**Acceptance Criteria:**
- Variant assignment uses SHA-256 hash: `hash(student_id + test_id) % num_variants` — deterministic, no random assignment
- Assignments stored in `ab_test_assignments` table for backend-driven decisions; PostHog Feature Flags for frontend
- Student retains same variant across sessions (stable assignment from account creation)
- 5 planned experiments seeded: ABT-001 (animations), ABT-002 (hint button color), ABT-003 (session length), ABT-004 (parent onboarding), ABT-005 (trial length)
- Variant exposed in session context; experiment metrics tagged in PostHog events (`abtest_variant` property)
- Experiment can be paused or concluded from admin interface without code deploy
- Statistical significance threshold: p < 0.05 (two-tailed) before concluding winner
- Assignment is COPPA-safe: uses anonymized `actor_hash`, no PII stored in assignment table

**Priority:** P1 | **Points:** 5 | **Dependencies:** MATH-531

---

### Epic 5: COPPA Safe Harbor & Privacy (FR-25)

**Solo Development Estimate:** 10–20 agent-hours + external legal time | Calendar: ~2–4 weeks (certification is process-dependent, not just code)

---

**MATH-541 — COPPA Safe Harbor Certification**  
*As the company, I want COPPA Safe Harbor certification from kidSAFE (or equivalent) so that PADI.AI can be legally marketed to children and schools have third-party privacy assurance.*

**Acceptance Criteria:**
- kidSAFE application submitted by Month 15 Week 2
- Privacy policy written at ≤ 9th grade Flesch-Kincaid reading level
- Privacy Summary page published at `/privacy/summary` in plain language
- Data collection inventory documented (all fields, storage location, justification, retention)
- Parental consent mechanism reviewed and approved by kidSAFE
- Annual privacy audit process agreed to and calendared
- kidSAFE seal displayed on homepage and privacy policy page
- PRIVO application initiated by Month 18 for school/district sales credibility
- Student Privacy Pledge signed (studentprivacypledge.org) — all 10 commitments verifiable in product

**Priority:** P0 | **Points:** 13 | **Dependencies:** None (legal process, not engineering)

---

**MATH-542 — Data Minimization & Privacy Audit**  
*As the privacy officer, I want a formal data minimization audit so that PADI.AI collects only what is necessary for educational function and can demonstrate COPPA compliance.*

**Acceptance Criteria:**
- Data inventory document completed: every data field with where stored, why collected, retention period
- Confirmed NOT collected: student last name, student photos, location data (IP-to-city disabled), contacts, calendar
- Confirmed NOT used: third-party advertising trackers, behavioral profiling for ads
- PostHog confirmed self-hosted (student data never leaves PADI.AI infrastructure)
- Every third-party subprocessor signed a DPA with PADI.AI (AWS, Auth0, Anthropic, OpenAI, Stripe documented)
- Annual privacy review process defined: October audit checklist, output = Privacy Review Report
- Data deletion workflow tested: parent deletion request processed within 48 hours
- IP address retention: session IPs retained 30 days only; EOG assessment IPs 1 year (assessment integrity)

**Priority:** P0 | **Points:** 5 | **Dependencies:** MATH-541

---

### Epic 6: Content Expansion (FR-26)

---

**MATH-551 — 10,000+ Question Bank**  
*As a student, I want access to a large, varied question bank so that practice sessions feel fresh and cover all difficulty levels across every Oregon Grade 4 math standard.*

**Acceptance Criteria:**
- Minimum 150 questions per skill × 29 skills = 4,350 questions at target density
- Total question bank ≥ 10,000 questions at MMP launch
- Per-skill diversity: ≥5 different context themes, ≥3 question types, ≥3 difficulty levels (b = -1.0, 0.0, 1.0)
- ≥20% word problems per skill with Oregon-specific contexts (Crater Lake, Willamette Valley, Oregon Coast)
- Quality pipeline: spec → o3-mini generates 5 variants → human teacher review → automated answer verification → IRT calibration
- Spanish translations available for all questions at launch (AI-translated + human-reviewed)
- Question analytics materialized view (`question_analytics`) refreshed nightly
- Questions flagged for review when: p1_accuracy < 0.20 or > 0.95, hint_rate > 0.80, distractor chosen < 5%
- Async Job Queue handles bulk generation (SQS worker) so question gen doesn't block API response

**Priority:** P1 | **Points:** 13 | **Dependencies:** MATH-527

---

**MATH-552 — Video Micro-Lessons**  
*As a student starting a new module, I want to watch a short concept video so that I understand the mathematical idea before I start practicing questions.*

**Acceptance Criteria:**
- 29 videos (one per module), 2–3 minutes each, screen-capture/animated explainer format
- Videos shown at module start; can be re-watched from module overview page
- Skippable after 15 seconds (skip button appears at 15s)
- Captions required (English); Spanish subtitles provided
- Stage 5 v1: YouTube unlisted with privacy-enhanced embed (`nocookie.com` domain)
- Analytics: `student_video_watched` event with `start`, `complete`, `skip_at_seconds` properties
- Videos respect `prefers-reduced-motion` (video still plays; no app-layer motion effects during video)
- Video player WCAG 2.1 AA: keyboard controls, caption toggle, volume accessible by keyboard

**Priority:** P2 | **Points:** 5 | **Dependencies:** MATH-527

---

## 3. Detailed Test Plan

### 3.1 Unit Tests

**Tooling:** pytest 8.x (Python), Vitest (TypeScript/React). Coverage enforced by GitHub Actions CI gate. **Coverage targets:** ≥90% core business logic (subscription state machine, billing service, feature gating); ≥80% service layer; ≥70% UI components.

#### 3.1.1 Stripe Webhook Handler Unit Tests

**File:** `services/billing/tests/unit/test_webhook_handler.py`

```python
import pytest
import stripe
from unittest.mock import AsyncMock, patch, MagicMock
from billing.webhook_handler import process_stripe_event
from billing.models import SubscriptionState

@pytest.fixture
def mock_db():
    return AsyncMock()

@pytest.fixture
def valid_invoice_succeeded_event():
    return {
        "id": "evt_test_001",
        "type": "invoice.payment_succeeded",
        "created": 1700000000,
        "data": {
            "object": {
                "subscription": "sub_test_123",
                "amount_paid": 1499,
                "currency": "usd",
                "period_end": 1702678400,
            }
        }
    }

class TestWebhookSignatureVerification:
    """UT-BILL-001: Signature verification rejects unsigned payloads."""

    async def test_invalid_signature_raises_400(self, test_client):
        response = await test_client.post(
            "/webhooks/stripe",
            content=b'{"id": "evt_fake"}',
            headers={"stripe-signature": "invalid"},
        )
        assert response.status_code == 400

    async def test_missing_signature_header_raises_400(self, test_client):
        response = await test_client.post(
            "/webhooks/stripe",
            content=b'{"id": "evt_fake"}',
        )
        assert response.status_code == 400

    async def test_valid_signature_accepted(self, test_client, mock_stripe_signature):
        response = await test_client.post(
            "/webhooks/stripe",
            content=mock_stripe_signature.payload,
            headers={"stripe-signature": mock_stripe_signature.header},
        )
        assert response.status_code == 200

class TestWebhookIdempotency:
    """UT-BILL-002: Duplicate events are safely skipped."""

    async def test_duplicate_event_returns_200_without_reprocessing(
        self, mock_db, valid_invoice_succeeded_event
    ):
        # Pre-seed dedup table
        mock_db.get_stripe_event.return_value = MagicMock(stripe_event_id="evt_test_001")

        result = await process_stripe_event(valid_invoice_succeeded_event, mock_db)

        assert result.status == "already_processed"
        mock_db.update_subscription.assert_not_called()

class TestPaymentSucceededHandler:
    """UT-BILL-003: invoice.payment_succeeded transitions to ACTIVE."""

    async def test_first_payment_sets_active_state(
        self, mock_db, valid_invoice_succeeded_event
    ):
        mock_db.get_stripe_event.return_value = None
        mock_db.get_subscription_by_stripe_id.return_value = MagicMock(
            state=SubscriptionState.TRIAL
        )

        await process_stripe_event(valid_invoice_succeeded_event, mock_db)

        mock_db.update_subscription.assert_called_once()
        call_kwargs = mock_db.update_subscription.call_args.kwargs
        assert call_kwargs["state"] == SubscriptionState.ACTIVE

    async def test_past_due_recovery_clears_past_due_since(
        self, mock_db, valid_invoice_succeeded_event
    ):
        mock_db.get_stripe_event.return_value = None
        mock_db.get_subscription_by_stripe_id.return_value = MagicMock(
            state=SubscriptionState.PAST_DUE
        )

        await process_stripe_event(valid_invoice_succeeded_event, mock_db)

        call_kwargs = mock_db.update_subscription.call_args.kwargs
        assert call_kwargs["past_due_since"] is None

class TestPaymentFailedHandler:
    """UT-BILL-004: invoice.payment_failed transitions to PAST_DUE."""

    async def test_payment_failure_sets_past_due(self, mock_db):
        event = {
            "id": "evt_test_002",
            "type": "invoice.payment_failed",
            "data": {"object": {"subscription": "sub_test_123"}},
        }
        mock_db.get_stripe_event.return_value = None
        mock_db.get_subscription_by_stripe_id.return_value = MagicMock(
            state=SubscriptionState.ACTIVE
        )

        await process_stripe_event(event, mock_db)

        call_kwargs = mock_db.update_subscription.call_args.kwargs
        assert call_kwargs["state"] == SubscriptionState.PAST_DUE
        assert call_kwargs["past_due_since"] is not None

class TestStaleEventHandling:
    """UT-BILL-005: Out-of-order events are safely ignored."""

    async def test_stale_event_skipped_when_db_record_newer(
        self, mock_db, valid_invoice_succeeded_event
    ):
        mock_db.get_stripe_event.return_value = None
        mock_db.get_subscription_by_stripe_id.return_value = MagicMock(
            state=SubscriptionState.ACTIVE,
            stripe_updated_at=9999999999,  # DB newer than event
        )

        result = await process_stripe_event(valid_invoice_succeeded_event, mock_db)

        assert result.status == "stale_event_skipped"
```

#### 3.1.2 Subscription State Machine Unit Tests

**File:** `services/billing/tests/unit/test_subscription_state_machine.py`

```python
"""
UT-BILL-006 through UT-BILL-012: Full state machine transition coverage.
"""

class TestSubscriptionStateMachine:

    def test_trial_to_active_on_first_payment(self, state_machine):
        """UT-BILL-006"""
        result = state_machine.transition(
            from_state="trial", event="payment_succeeded", is_first_charge=True
        )
        assert result.new_state == "active"

    def test_active_to_past_due_on_payment_failure(self, state_machine):
        """UT-BILL-007"""
        result = state_machine.transition(from_state="active", event="payment_failed")
        assert result.new_state == "past_due"

    def test_past_due_to_canceled_after_all_retries(self, state_machine):
        """UT-BILL-008"""
        result = state_machine.transition(
            from_state="past_due", event="subscription_deleted", retry_count=3
        )
        assert result.new_state == "canceled"

    def test_canceling_to_canceled_at_period_end(self, state_machine):
        """UT-BILL-009"""
        result = state_machine.transition(from_state="canceling", event="period_ended")
        assert result.new_state == "canceled"

    def test_canceled_to_trial_on_resubscribe(self, state_machine):
        """UT-BILL-010"""
        result = state_machine.transition(from_state="canceled", event="checkout_completed")
        assert result.new_state == "trial"

    def test_invalid_transition_raises_error(self, state_machine):
        """UT-BILL-011: No direct expired → active transition."""
        with pytest.raises(InvalidStateTransitionError):
            state_machine.transition(from_state="expired", event="payment_succeeded")

    def test_active_to_paused_school_only(self, state_machine):
        """UT-BILL-012: School pause only available on school subscriptions."""
        result = state_machine.transition(
            from_state="active", event="school_pause", subscription_type="school"
        )
        assert result.new_state == "paused"

        with pytest.raises(InvalidStateTransitionError):
            state_machine.transition(
                from_state="active", event="school_pause", subscription_type="individual"
            )
```

#### 3.1.3 i18n Rendering Unit Tests

**File:** `apps/web/tests/unit/i18n/i18n-rendering.test.ts`

```typescript
// UT-I18N-001 through UT-I18N-005
import { render, screen } from '@testing-library/react'
import { NextIntlClientProvider } from 'next-intl'
import { PracticeHeader } from '@/components/practice/PracticeHeader'
import enMessages from '@/messages/en.json'
import esMessages from '@/messages/es.json'

describe('i18n rendering', () => {
  it('UT-I18N-001: renders English session header by default', () => {
    render(
      <NextIntlClientProvider locale="en" messages={enMessages}>
        <PracticeHeader sessionNumber={3} />
      </NextIntlClientProvider>
    )
    expect(screen.getByText(/Practice Session/i)).toBeInTheDocument()
  })

  it('UT-I18N-002: renders Spanish session header when locale is es', () => {
    render(
      <NextIntlClientProvider locale="es" messages={esMessages}>
        <PracticeHeader sessionNumber={3} />
      </NextIntlClientProvider>
    )
    expect(screen.getByText(/Sesión de Práctica/i)).toBeInTheDocument()
  })

  it('UT-I18N-003: all en.json keys exist in es.json', () => {
    const enKeys = new Set(Object.keys(flattenKeys(enMessages)))
    const esKeys = new Set(Object.keys(flattenKeys(esMessages)))
    const missingKeys = [...enKeys].filter(k => !esKeys.has(k))
    expect(missingKeys).toHaveLength(0)
  })

  it('UT-I18N-004: KaTeX equation does not change between locales', () => {
    const question = { text_en: 'Solve: $3 \\times 4$', text_es: 'Resuelve: $3 \\times 4$' }
    // Math notation preserved; only prose text changes
    const katexPart = question.text_es.match(/\$.*?\$/)
    expect(katexPart?.[0]).toBe(question.text_en.match(/\$.*?\$/)?.[0])
  })

  it('UT-I18N-005: Spanish tutor prompt includes language instruction', async () => {
    const prompt = await buildTutorPrompt({ locale: 'es', hintLevel: 1 })
    expect(prompt).toContain('LANGUAGE: The student has selected Spanish')
    expect(prompt).toContain('4th-grade reading level in Spanish')
  })
})
```

#### 3.1.4 Clever SSO Token Exchange Unit Tests

**File:** `services/school-mgmt/tests/unit/test_clever_oauth.py`

```python
"""UT-SSO-001 through UT-SSO-005"""

class TestCleverTokenExchange:

    async def test_valid_code_returns_tokens(self, mock_clever_api):
        """UT-SSO-001"""
        mock_clever_api.token_endpoint.return_value = {
            "access_token": "at_test_123",
            "refresh_token": "rt_test_456",
        }
        result = await clever_exchange_code("valid_auth_code_xyz")
        assert result.access_token == "at_test_123"

    async def test_invalid_code_raises_oauth_error(self, mock_clever_api):
        """UT-SSO-002"""
        mock_clever_api.token_endpoint.side_effect = CleverOAuthError("invalid_code")
        with pytest.raises(CleverOAuthError):
            await clever_exchange_code("invalid_code")

    async def test_csrf_state_mismatch_raises_error(self):
        """UT-SSO-003"""
        with pytest.raises(CSRFStateError):
            await clever_callback(code="valid", state="wrong_state", session_state="correct_state")

    async def test_refresh_token_stored_encrypted(self, mock_db, mock_clever_api):
        """UT-SSO-004"""
        mock_clever_api.token_endpoint.return_value = {"access_token": "at", "refresh_token": "rt"}
        await clever_exchange_code("code")
        stored = mock_db.upsert_sso_connection.call_args.kwargs
        # Stored value should not be plaintext refresh token
        assert stored["refresh_token"] != "rt"
        assert stored["refresh_token"].startswith("AQI")  # KMS-encrypted prefix

    async def test_role_mapping_district_admin_to_school_admin(self, mock_clever_api):
        """UT-SSO-005"""
        mock_clever_api.get_user.return_value = {"type": "district_admin", "id": "123"}
        role = map_clever_role_to_padi_ai({"type": "district_admin"})
        assert role == "SCHOOL_ADMIN"
```

#### 3.1.5 Roster Import Parsing Unit Tests

**File:** `services/school-mgmt/tests/unit/test_roster_import.py`

```python
"""UT-ROSTER-001 through UT-ROSTER-007"""

class TestRosterCSVParsing:

    def test_valid_csv_parses_all_rows(self):
        """UT-ROSTER-001"""
        csv_content = "first_name,last_name,grade,teacher_email,student_id_local\n"
        csv_content += "Alex,Martinez,4,jsmith@school.or.us,1001\n"
        csv_content += "Jordan,Thompson,4,jsmith@school.or.us,1002\n"
        result = parse_roster_csv(csv_content)
        assert len(result.students) == 2
        assert result.errors == []

    def test_missing_required_column_raises_validation_error(self):
        """UT-ROSTER-002: Missing grade column"""
        csv_content = "first_name,last_name,teacher_email,student_id_local\nAlex,M,t@s.com,1001\n"
        result = parse_roster_csv(csv_content)
        assert any("grade" in e.reason for e in result.errors)

    def test_non_grade4_student_flagged(self):
        """UT-ROSTER-003: Grade 3 student row is flagged"""
        csv_content = "first_name,last_name,grade,teacher_email,student_id_local\n"
        csv_content += "Sam,Lee,3,t@s.com,1003\n"
        result = parse_roster_csv(csv_content)
        assert any("grade" in e.reason for e in result.errors)

    def test_duplicate_local_id_flagged_not_duplicated(self):
        """UT-ROSTER-004"""
        csv_content = "first_name,last_name,grade,teacher_email,student_id_local\n"
        csv_content += "Alex,M,4,t@s.com,1001\nJordan,T,4,t@s.com,1001\n"
        result = parse_roster_csv(csv_content)
        assert len(result.students) == 1
        assert any("duplicate" in e.reason.lower() for e in result.errors)

    def test_invalid_teacher_email_flags_row_student_still_imported(self):
        """UT-ROSTER-005"""
        csv_content = "first_name,last_name,grade,teacher_email,student_id_local\n"
        csv_content += "Alex,M,4,not-an-email,1001\n"
        result = parse_roster_csv(csv_content)
        assert len(result.students) == 1
        assert result.students[0].teacher_email is None
        assert any("teacher_email" in e.reason for e in result.errors)

    def test_max_1000_rows_enforced(self):
        """UT-ROSTER-006"""
        rows = "first_name,last_name,grade,teacher_email,student_id_local\n"
        rows += "\n".join(f"A{i},B,4,t@s.com,{i}" for i in range(1001))
        result = parse_roster_csv(rows)
        assert result.truncated is True
        assert len(result.students) == 1000

    def test_csv_import_is_idempotent(self, mock_db):
        """UT-ROSTER-007: Re-importing same local ID updates, not duplicates."""
        existing = MagicMock(student_id_local="1001", first_name="Alex")
        mock_db.find_by_local_id.return_value = existing
        result = process_student_row(
            {"first_name": "Alexander", "student_id_local": "1001"}, mock_db
        )
        assert result.action == "updated"
        mock_db.create_student.assert_not_called()
```

#### 3.1.6 Feature Gating Unit Tests

**File:** `services/api/tests/unit/test_feature_gating.py`

```python
"""UT-FEAT-001 through UT-FEAT-006"""

class TestFeatureGating:

    async def test_active_subscription_grants_unlimited_practice(self, mock_redis, mock_db):
        """UT-FEAT-001"""
        mock_redis.get.return_value = None  # Cache miss
        mock_db.get_subscription.return_value = MagicMock(state="active", plan_slug="individual")
        mock_db.get_features.return_value = {"unlimited_practice": True}
        result = await check_feature(user_id="u1", feature="unlimited_practice")
        assert result is True

    async def test_canceled_subscription_denies_premium_feature(self, mock_redis, mock_db):
        """UT-FEAT-002"""
        mock_redis.get.return_value = None
        mock_db.get_subscription.return_value = MagicMock(state="canceled")
        result = await check_feature(user_id="u1", feature="unlimited_practice")
        assert result is False

    async def test_cache_hit_bypasses_db(self, mock_redis, mock_db):
        """UT-FEAT-003"""
        mock_redis.get.return_value = '{"unlimited_practice": true}'
        result = await check_feature(user_id="u1", feature="unlimited_practice")
        mock_db.get_subscription.assert_not_called()
        assert result is True

    async def test_redis_down_falls_back_to_db(self, mock_redis, mock_db):
        """UT-FEAT-004"""
        mock_redis.get.side_effect = RedisConnectionError("Connection refused")
        mock_db.get_subscription.return_value = MagicMock(state="active", plan_slug="individual")
        mock_db.get_features.return_value = {"unlimited_practice": True}
        result = await check_feature(user_id="u1", feature="unlimited_practice")
        assert result is True  # Graceful fallback

    async def test_past_due_still_grants_access_within_grace_period(self, mock_redis, mock_db):
        """UT-FEAT-005"""
        from datetime import datetime, timedelta
        mock_redis.get.return_value = None
        mock_db.get_subscription.return_value = MagicMock(
            state="past_due",
            past_due_since=datetime.utcnow() - timedelta(days=3),  # Within 7-day grace
        )
        result = await check_feature(user_id="u1", feature="unlimited_practice")
        assert result is True

    async def test_cache_invalidated_on_subscription_state_change(self, mock_redis):
        """UT-FEAT-006"""
        await invalidate_feature_cache(user_id="u1")
        mock_redis.delete.assert_called_once_with("feature:u1")
```

### 3.2 Integration Tests

**Tooling:** pytest + testcontainers (PostgreSQL 17, Redis 7 in Docker). Real database operations; no mocks for DB or Redis layers. httpx AsyncClient for API calls.

#### 3.2.1 Full Billing Lifecycle Integration Tests

**File:** `services/billing/tests/integration/test_billing_lifecycle.py`

```python
"""IT-BILL-001 through IT-BILL-008: Full billing lifecycle with real PostgreSQL."""

@pytest.mark.integration
class TestBillingLifecycleIntegration:

    async def test_IT_BILL_001_checkout_creates_trial_subscription(
        self, db_session, stripe_mock
    ):
        """Full checkout → trial subscription creation."""
        parent = await create_test_parent(db_session)
        # Simulate Stripe checkout.session.completed event
        event = build_checkout_completed_event(
            customer_id="cus_test", subscription_id="sub_test", trial=True
        )
        await process_webhook_event(event, db_session)

        sub = await db_session.get_subscription_by_stripe_id("sub_test")
        assert sub.state == "trial"
        assert sub.parent_id == parent.id

    async def test_IT_BILL_002_trial_converts_to_active_on_first_payment(
        self, db_session
    ):
        """First invoice.payment_succeeded converts trial → active."""
        sub = await create_test_subscription(db_session, state="trial")
        event = build_invoice_succeeded_event(sub.stripe_subscription_id, is_first=True)
        await process_webhook_event(event, db_session)

        await db_session.refresh(sub)
        assert sub.state == "active"
        assert sub.current_period_end is not None

    async def test_IT_BILL_003_payment_failure_triggers_dunning_email(
        self, db_session, sqs_mock
    ):
        """invoice.payment_failed → dunning email enqueued in SQS."""
        sub = await create_test_subscription(db_session, state="active")
        event = build_invoice_failed_event(sub.stripe_subscription_id)
        await process_webhook_event(event, db_session)

        await db_session.refresh(sub)
        assert sub.state == "past_due"
        # Email job enqueued to SQS
        assert sqs_mock.send_message.called
        job = json.loads(sqs_mock.send_message.call_args.kwargs["MessageBody"])
        assert job["type"] == "send_dunning_email"
        assert job["dunning_day"] == 0

    async def test_IT_BILL_004_cancel_at_period_end_flow(self, db_session):
        """customer.subscription.updated (cancel_at_period_end) → CANCELING state."""
        sub = await create_test_subscription(db_session, state="active")
        event = build_subscription_updated_event(
            sub.stripe_subscription_id, cancel_at_period_end=True
        )
        await process_webhook_event(event, db_session)

        await db_session.refresh(sub)
        assert sub.state == "canceling"
        assert sub.cancel_at is not None

    async def test_IT_BILL_005_reactivation_clears_cancellation(self, db_session):
        """cancel_at_period_end=false → reactivated to ACTIVE."""
        sub = await create_test_subscription(db_session, state="canceling")
        event = build_subscription_updated_event(
            sub.stripe_subscription_id, cancel_at_period_end=False
        )
        await process_webhook_event(event, db_session)

        await db_session.refresh(sub)
        assert sub.state == "active"
        assert sub.cancel_at is None

    async def test_IT_BILL_006_feature_gating_reflects_subscription_state(
        self, db_session, redis_client
    ):
        """Feature access enabled on active, disabled on canceled."""
        sub = await create_test_subscription(db_session, state="active")
        parent = await db_session.get(User, sub.parent_id)

        # Active: unlimited practice granted
        result = await check_feature(parent.id, "unlimited_practice", redis_client, db_session)
        assert result is True

        # Cancel subscription
        await db_session.execute(
            update(Subscription).where(Subscription.id == sub.id).values(state="canceled")
        )
        await redis_client.delete(f"feature:{parent.id}")  # Clear cache

        # Canceled: unlimited practice denied
        result = await check_feature(parent.id, "unlimited_practice", redis_client, db_session)
        assert result is False

    async def test_IT_BILL_007_duplicate_webhook_idempotent(self, db_session):
        """Same stripe_event_id processed twice results in single DB write."""
        event = build_invoice_succeeded_event("sub_test_007")
        await process_webhook_event(event, db_session)
        count_before = await db_session.scalar(
            select(func.count()).select_from(SubscriptionEvent)
        )
        # Process same event again
        await process_webhook_event(event, db_session)
        count_after = await db_session.scalar(
            select(func.count()).select_from(SubscriptionEvent)
        )
        assert count_before == count_after  # No duplicate events

    async def test_IT_BILL_008_school_invoice_creation(self, db_session, stripe_mock):
        """School invoice: Stripe Invoice object created, PDF S3 key stored."""
        school = await create_test_school(db_session)
        result = await create_school_invoice(
            school_id=school.id,
            po_number="PO-2026-001",
            billing_contact="admin@school.or.us",
            db=db_session,
        )
        assert result.stripe_invoice_id.startswith("in_")
        assert result.po_number == "PO-2026-001"
```

#### 3.2.2 SSO Flow Integration Tests

**File:** `services/school-mgmt/tests/integration/test_sso_flow.py`

```python
"""IT-SSO-001 through IT-SSO-005"""

@pytest.mark.integration
class TestCleverSSOIntegration:

    async def test_IT_SSO_001_clever_callback_creates_school_entities(
        self, db_session, clever_api_mock
    ):
        """Full Clever OAuth callback creates district, school, teachers, students."""
        clever_api_mock.configure(
            district={"id": "d1", "name": "Portland Public"},
            schools=[{"id": "s1", "name": "Rosa Parks Elementary"}],
            teachers=[{"id": "t1", "email": "teacher@school.or.us"}],
            students=[{"id": "st1", "first_name": "Alex", "last_name": "Martinez", "grade": 4}],
        )
        await handle_clever_callback(code="auth_code", state="csrf_valid", db=db_session)

        district = await db_session.query(District).filter_by(clever_id="d1").first()
        assert district.name == "Portland Public"
        student = await db_session.query(StudentProfile).filter_by(clever_id="st1").first()
        assert student.first_name == "Alex"

    async def test_IT_SSO_002_nightly_sync_unenrolls_removed_student(
        self, db_session, clever_api_mock
    ):
        """Student removed from Clever → soft-unenrolled in PADI.AI; data preserved."""
        student = await create_test_clever_student(db_session, clever_id="st2")
        clever_api_mock.configure(students=[])  # Student removed from Clever

        await sync_school_roster(
            connection=await db_session.get(CleverConnection, student.school_id),
            db=db_session,
        )

        enrollment = await db_session.query(ClassroomEnrollment).filter_by(
            student_id=student.id
        ).first()
        assert enrollment.is_active is False
        # Data preserved
        progress = await db_session.query(SkillMasteryState).filter_by(
            student_id=student.id
        ).first()
        assert progress is not None

    async def test_IT_SSO_003_conflict_creates_merge_request(
        self, db_session, clever_api_mock
    ):
        """Parent-created student + Clever import creates merge_request."""
        # Pre-existing parent-created student
        parent_student = await create_test_student(
            db_session, first_name="Alex", last_name="Martinez", school_id="s1"
        )
        clever_api_mock.configure(
            students=[{"id": "st3", "first_name": "Alex", "last_name": "Martinez", "grade": 4}]
        )

        await sync_school_roster(
            connection=await db_session.query(CleverConnection).filter_by(school_id="s1").first(),
            db=db_session,
        )

        merge_req = await db_session.query(MergeRequest).filter_by(
            existing_student_id=parent_student.id
        ).first()
        assert merge_req is not None

    async def test_IT_SSO_004_dpa_blocks_data_access_before_signing(self, db_session):
        """Student data inaccessible until DPA is signed."""
        school = await create_test_school(db_session, dpa_signed=False)
        student = await create_test_student(db_session, school_id=school.id)

        response = await api_client.get(f"/api/v1/schools/{school.id}/students")
        assert response.status_code == 403
        assert "DPA required" in response.json()["detail"]

    async def test_IT_SSO_005_google_workspace_domain_restriction(self, db_session):
        """Google SSO only provisions users from configured school domain."""
        school = await create_test_school(db_session, google_domain="hillcrest.k12.or.us")
        # Valid domain
        result = await handle_google_sso(email="teacher@hillcrest.k12.or.us", db=db_session)
        assert result.user is not None
        # Invalid domain
        result = await handle_google_sso(email="someone@gmail.com", db=db_session)
        assert result.user is None
        assert result.reason == "domain_not_configured"
```

#### 3.2.3 Analytics Event Pipeline Integration Tests

**File:** `services/analytics/tests/integration/test_analytics_pipeline.py`

```python
"""IT-ANALYTICS-001 through IT-ANALYTICS-005"""

@pytest.mark.integration
class TestAnalyticsPipeline:

    async def test_IT_ANALYTICS_001_student_event_pseudonymized(self, db_session):
        """Student events stored with hash, not PII."""
        await ingest_event(
            event_name="student_session_completed",
            actor_type="student",
            actor_id="stu-uuid-123",
            properties={"session_id": "sess-456", "accuracy_pct": 0.75},
            db=db_session,
        )
        event = await db_session.query(AnalyticsEvent).filter_by(
            event_name="student_session_completed"
        ).first()
        assert event.actor_hash != "stu-uuid-123"
        assert "stu-uuid-123" not in str(event.properties)

    async def test_IT_ANALYTICS_002_no_pii_in_event_properties(self, db_session):
        """Event properties JSON contains no PII fields."""
        forbidden_keys = {"name", "email", "first_name", "last_name", "ip_address"}
        events = await db_session.query(AnalyticsEvent).all()
        for event in events:
            prop_keys = set(event.properties.keys())
            assert prop_keys.isdisjoint(forbidden_keys), (
                f"PII found in event {event.event_name}: {prop_keys & forbidden_keys}"
            )

    async def test_IT_ANALYTICS_003_ab_assignment_is_deterministic(self, db_session):
        """Same student always gets same A/B variant."""
        variant1 = await get_variant("student-abc", "ABT-001", db=db_session)
        variant2 = await get_variant("student-abc", "ABT-001", db=db_session)
        assert variant1 == variant2

    async def test_IT_ANALYTICS_004_ab_assignment_covers_all_variants(self, db_session):
        """Hash-based assignment distributes across all variants."""
        variants_seen = set()
        for i in range(200):
            v = await get_variant(f"student-{i:04d}", "ABT-001", db=db_session)
            variants_seen.add(v)
        # ABT-001 has 2 variants (A, B); all should appear in 200 students
        assert len(variants_seen) == 2

    async def test_IT_ANALYTICS_005_event_ingestion_latency_under_100ms(
        self, db_session, benchmark
    ):
        """Event ingestion must not add > 100ms to request path."""
        result = await benchmark(
            ingest_event,
            event_name="student_question_answered",
            actor_type="student",
            actor_id="stu-bench",
            properties={"skill_id": "4.OA.A.1", "is_correct": True},
            db=db_session,
        )
        assert benchmark.stats.mean < 0.1  # < 100ms
```

### 3.3 End-to-End Tests (Playwright)

**File locations:** `apps/web/tests/e2e/`  
**Configuration:** `apps/web/playwright.config.ts`  
**Cross-browser matrix:** Chromium, Firefox, WebKit (latest 2 versions each). Mobile viewports: iPhone 14 (390×844), iPad Pro (1024×1366).

#### 3.3.1 E2E-BILL-001: Full Subscription Purchase Flow

```typescript
// apps/web/tests/e2e/billing/subscription-purchase.spec.ts
import { test, expect } from '@playwright/test'
import { StripeTestHelper } from '../helpers/stripe-test-helper'

test.describe('Subscription Purchase Flow', () => {
  test('E2E-BILL-001: parent completes Individual subscription with 14-day trial', async ({ page }) => {
    await page.goto('/en/settings/billing/upgrade')
    await expect(page.getByText('Choose your plan')).toBeVisible()

    // Select Individual plan
    await page.getByTestId('plan-individual').click()
    await page.getByTestId('billing-monthly').click()
    await page.getByTestId('start-trial').click()

    // Stripe Elements iframe
    const stripeFrame = page.frameLocator('iframe[name^="__privateStripeFrame"]')
    await stripeFrame.getByPlaceholder('Card number').fill('4242424242424242')
    await stripeFrame.getByPlaceholder('MM / YY').fill('12/30')
    await stripeFrame.getByPlaceholder('CVC').fill('123')

    await page.getByTestId('submit-payment').click()

    // Confirmation
    await expect(page.getByText('Your 14-day free trial has started!')).toBeVisible({ timeout: 10000 })
    await expect(page.getByTestId('trial-end-date')).toBeVisible()

    // Feature access confirmed
    await page.goto('/en/practice')
    await expect(page.getByTestId('session-limit-banner')).not.toBeVisible()
  })

  test('E2E-BILL-002: declined card shows error without redirecting', async ({ page }) => {
    await page.goto('/en/settings/billing/upgrade')
    await page.getByTestId('plan-individual').click()
    await page.getByTestId('start-trial').click()

    const stripeFrame = page.frameLocator('iframe[name^="__privateStripeFrame"]')
    await stripeFrame.getByPlaceholder('Card number').fill('4000000000000002') // Declined card
    await stripeFrame.getByPlaceholder('MM / YY').fill('12/30')
    await stripeFrame.getByPlaceholder('CVC').fill('123')

    await page.getByTestId('submit-payment').click()

    await expect(page.getByText(/Your card was declined/i)).toBeVisible()
    await expect(page).toHaveURL(/\/settings\/billing\/upgrade/)
  })
})
```

#### 3.3.2 E2E-SCHOOL-001: School Admin Onboarding Flow

```typescript
// apps/web/tests/e2e/school/school-onboarding.spec.ts
test.describe('School Admin Onboarding', () => {
  test('E2E-SCHOOL-001: school admin completes DPA and imports roster', async ({ page }) => {
    await page.goto('/en/admin/onboard')

    // Step 1: School profile
    await page.getByLabel('School Name').fill('Rosa Parks Elementary')
    await page.getByLabel('NCES ID').fill('410243000123')
    await page.getByTestId('next-step').click()

    // Step 2: DPA - must scroll to bottom
    await expect(page.getByTestId('dpa-sign-button')).toBeDisabled()
    await page.evaluate(() => {
      const dpaContent = document.querySelector('[data-testid="dpa-content"]')
      dpaContent?.scrollTo(0, dpaContent.scrollHeight)
    })
    await expect(page.getByTestId('dpa-sign-button')).toBeEnabled()

    await page.getByLabel('Your full name').fill('Jane Smith')
    await page.getByLabel('Your title').fill('Technology Director')
    await page.getByLabel('Typed signature').fill('Jane Smith')
    await page.getByTestId('dpa-sign-button').click()
    await expect(page.getByText('DPA signed and sent to your email')).toBeVisible()

    // Step 3: Roster import
    await page.getByTestId('next-step').click()
    const [fileChooser] = await Promise.all([
      page.waitForEvent('filechooser'),
      page.getByTestId('roster-upload').click(),
    ])
    await fileChooser.setFiles('./tests/fixtures/sample-roster.csv')
    await expect(page.getByText('Importing 28 students')).toBeVisible()
    await page.getByTestId('confirm-import').click()
    await expect(page.getByText('28 students imported successfully')).toBeVisible({ timeout: 30000 })
  })

  test('E2E-SCHOOL-002: DPA blocks student data before signing', async ({ page }) => {
    await page.goto('/en/admin/school/students')
    await expect(page.getByText('Please sign the FERPA Data Processing Agreement')).toBeVisible()
    await expect(page.getByTestId('student-list')).not.toBeVisible()
  })
})
```

#### 3.3.3 E2E-I18N-001: Spanish Language Mode

```typescript
// apps/web/tests/e2e/i18n/spanish-mode.spec.ts
test.describe('Spanish Language Support', () => {
  test('E2E-I18N-001: student practice session fully in Spanish', async ({ page }) => {
    // Login as Spanish-preference student
    await loginAs(page, 'spanish-student-fixture')
    await page.goto('/es/practice')

    await expect(page).toHaveURL(/\/es\/practice/)
    await expect(page.getByTestId('session-header')).toContainText('Sesión de Práctica')
    await expect(page.getByTestId('hint-button')).toContainText('Pedir una pista')

    // Pip encouragement text in Spanish
    await page.getByTestId('wrong-answer').click()
    await expect(page.getByTestId('pip-message')).toContainText(/[¡Á-Úá-ú]/) // Spanish characters
  })

  test('E2E-I18N-002: language toggle switches locale mid-session', async ({ page }) => {
    await loginAs(page, 'parent-fixture')
    await page.goto('/en/dashboard')
    await page.getByTestId('language-toggle').click()
    await page.getByText('Español').click()
    await expect(page).toHaveURL(/\/es\/dashboard/)
    await expect(page.getByTestId('dashboard-heading')).toContainText(/Panel/)
  })

  test('E2E-I18N-003: Spanish email preference sends Spanish email', async ({ page }) => {
    // Verify email preview endpoint serves Spanish template
    const response = await page.request.get('/api/preview/email/trial-reminder?locale=es')
    const text = await response.text()
    expect(text).toContain('Tu prueba gratuita termina pronto')
  })
})
```

#### 3.3.4 E2E-UX-001: Dark Mode Visual Regression

```typescript
// apps/web/tests/e2e/ux/dark-mode.spec.ts
test.describe('Dark Mode', () => {
  test('E2E-UX-001: dark mode applies correct theme across practice view', async ({ page }) => {
    await page.emulateMedia({ colorScheme: 'dark' })
    await loginAs(page, 'student-fixture')
    await page.goto('/en/practice')

    // Visual regression snapshot
    await expect(page).toHaveScreenshot('practice-dark-mode.png', {
      maxDiffPixelRatio: 0.001,
    })

    // KaTeX equations visible in dark mode
    const katex = page.getByTestId('question-katex')
    await expect(katex).toBeVisible()
    const color = await katex.evaluate(el =>
      window.getComputedStyle(el).color
    )
    // Cream text in dark mode: not black (not #000000)
    expect(color).not.toBe('rgb(0, 0, 0)')
  })

  test('E2E-UX-002: prefers-reduced-motion shows static Pip', async ({ page }) => {
    await page.emulateMedia({ reducedMotion: 'reduce' })
    await loginAs(page, 'student-fixture')
    await page.goto('/en/practice')

    // Lottie animation NOT present; static PNG IS present
    await expect(page.locator('lottie-player')).not.toBeVisible()
    await expect(page.getByTestId('pip-static-image')).toBeVisible()
  })
})
```

#### 3.3.5 E2E-MASCOT-001: Pip Mascot Interactions

```typescript
// apps/web/tests/e2e/ux/pip-mascot.spec.ts
test.describe('Pip Mascot Interactions', () => {
  test('E2E-MASCOT-001: Pip celebrates on correct answer', async ({ page }) => {
    await loginAs(page, 'student-fixture')
    await page.goto('/en/practice')
    await page.getByTestId('correct-answer-option').click()

    const pip = page.getByTestId('pip-mascot')
    await expect(pip).toHaveAttribute('data-state', 'happy')
    // Animation fires within 300ms
    await page.waitForTimeout(300)
    await expect(pip).not.toHaveAttribute('data-state', 'neutral')
  })

  test('E2E-MASCOT-002: Pip encourages on incorrect answer', async ({ page }) => {
    await loginAs(page, 'student-fixture')
    await page.goto('/en/practice')
    await page.getByTestId('wrong-answer-option').click()

    const pip = page.getByTestId('pip-mascot')
    await expect(pip).toHaveAttribute('data-state', 'encouraging')
  })

  test('E2E-MASCOT-003: Pip celebrates mastery with full animation', async ({ page }) => {
    // Simulate mastery event via API fixture
    await page.route('/api/v1/practice/submit', route =>
      route.fulfill({ json: { skills_mastered: ['4.OA.A.1'], bkt_update: 0.85 } })
    )
    await loginAs(page, 'student-fixture')
    await page.goto('/en/practice')
    await page.getByTestId('submit-answer').click()

    await expect(page.getByTestId('mastery-celebration')).toBeVisible({ timeout: 2000 })
    await expect(page.getByTestId('pip-mascot')).toHaveAttribute('data-state', 'celebrating')
  })
})
```

### 3.4 Behavioral / BDD Tests

**Format:** Given-When-Then (behave / Cucumber). Files in `tests/bdd/features/`.

#### 3.4.1 Billing Scenarios

**File:** `tests/bdd/features/billing.feature`

```gherkin
Feature: Subscription Billing Lifecycle
  As a parent, I want subscription billing to work predictably
  so that my access matches what I've paid for.

  Background:
    Given a parent "Sarah Chen" with email "sarah@example.com"
    And no existing subscription

  Scenario: BDD-BILL-001 — Free trial starts on first checkout
    Given Sarah has no payment history
    When she completes checkout for the Individual Monthly plan
    And provides card number "4242424242424242"
    Then her subscription state should be "trial"
    And she should have access to "unlimited_practice"
    And she should receive a "trial_welcome" email within 2 minutes
    And a "14-day free trial" countdown is shown in her account settings

  Scenario: BDD-BILL-002 — Trial converts automatically to active
    Given Sarah is in "trial" state
    When 14 days pass and Stripe charges her card successfully
    And the webhook "invoice.payment_succeeded" is received
    Then her subscription state should be "active"
    And she should receive a "payment_confirmation" email
    And her "current_period_end" should be 30 days from today

  Scenario: BDD-BILL-003 — Trial expires with no payment method
    Given Sarah started a trial without adding a payment method
    When the 14-day trial period ends
    And Stripe sends "customer.subscription.deleted" webhook
    Then her subscription state should be "canceled"
    And her access should be downgraded to "free_tier"
    And she should receive a "trial_expired" email with upgrade CTA

  Scenario: BDD-BILL-004 — Upgrade from Individual to Family
    Given Sarah has an active Individual subscription
    When she upgrades to Family plan via /settings/subscription
    Then the upgrade should take effect immediately (proration applied)
    And her subscription state should remain "active"
    And she should see up to 4 student profiles
    And she should receive an "upgrade_confirmed" email

  Scenario: BDD-BILL-005 — Downgrade scheduled for period end
    Given Sarah has an active Family subscription
    When she requests a downgrade to Individual
    Then a "downgrade_scheduled" confirmation is shown with the effective date
    And her "pending_plan_id" should be set to the Individual plan
    And she retains Family features until the period end date
    And she should receive a "downgrade_scheduled" email

  Scenario: BDD-BILL-006 — Cancel at period end with data retention
    Given Sarah has an active subscription
    When she cancels her subscription choosing "cancel at period end"
    Then her subscription state should become "canceling"
    And she retains full access until the period end date
    And all student progress data is preserved
    And she can reactivate in one click from /settings/subscription

  Scenario: BDD-BILL-007 — Payment failure dunning sequence
    Given Sarah has an active subscription
    When her payment method fails on renewal
    Then on Day 0: subscription becomes "past_due", dunning email #1 sent
    And on Day 3 (retry fails): dunning email #2 sent
    And on Day 7 (retry fails): dunning email #3 sent and in-app banner shown
    And student access is preserved for 7 days from initial failure
    And on Day 14 (all retries exhausted): subscription becomes "canceled"
    And student data is never deleted during this sequence

  Scenario: BDD-BILL-008 — Dunning recovery via payment update
    Given Sarah is in "past_due" state (Day 5)
    When she updates her payment method and payment succeeds
    And Stripe sends "invoice.payment_succeeded" webhook
    Then her subscription state should return to "active"
    And "past_due_since" should be cleared
    And she should receive a "payment_recovered" email
```

#### 3.4.2 School Admin Scenarios

**File:** `tests/bdd/features/school-onboarding.feature`

```gherkin
Feature: School Admin Onboarding
  As a school technology director, I want to onboard my school
  so that my teachers and students can use PADI.AI.

  Scenario: BDD-SCHOOL-001 — FERPA DPA required before roster access
    Given a new school admin "Dr. Patel" at "Woodstock Elementary"
    When Dr. Patel attempts to access the student roster page
    Then she is redirected to the DPA signing page
    And the student roster is not visible until DPA is signed
    And a banner reads "Please sign the FERPA Data Processing Agreement to continue"

  Scenario: BDD-SCHOOL-002 — DPA signing unlocks student data access
    Given Dr. Patel views the DPA inline (scrolled to bottom)
    When she enters her name, title, and typed signature
    And clicks "Sign and Continue"
    Then a dpa_agreements record is created with SHA-256 content hash
    And a signed DPA PDF is emailed to her within 10 minutes
    And the student roster page becomes accessible

  Scenario: BDD-SCHOOL-003 — CSV roster import with error handling
    Given Dr. Patel has signed the DPA
    When she uploads a CSV with 28 valid students and 2 invalid rows
    Then a preview shows "Importing 28 students. 2 rows have errors."
    And on confirmation, 28 students are created in the database
    And a downloadable error CSV identifies the 2 invalid rows with reasons
    And 3 new teacher invitation emails are sent

  Scenario: BDD-SCHOOL-004 — Clever sync adds and removes students
    Given Woodstock Elementary is connected to Clever
    When the nightly sync runs at 02:00 Pacific
    And Clever reports 1 new student, 1 updated student, 1 removed student
    Then 1 new StudentProfile is created
    And 1 StudentProfile's grade is updated
    And 1 StudentProfile is soft-unenrolled (is_active=false, data preserved)
    And a sync result record is written to clever_sync_jobs

  Scenario: BDD-SCHOOL-005 — School admin views standards coverage grid
    Given 30 students are enrolled across 2 classrooms
    When Dr. Patel views the school admin dashboard
    Then a 29 × 2 standards coverage grid is displayed
    And each cell shows % of students with P(mastered) ≥ 0.80
    And cells with < 50% are shown in red
    And cells with 50-79% are shown in yellow
    And cells with ≥ 80% are shown in green
```

#### 3.4.3 Parental Consent for School Accounts

**File:** `tests/bdd/features/parental-consent-school.feature`

```gherkin
Feature: Parental Consent for School Data Sharing
  As a parent of a school-enrolled student, I want control over
  what data my child's school can access.

  Scenario: BDD-CONSENT-001 — School merge request triggers parent notification
    Given "Alex Martinez" exists as a parent-created student
    And Clever imports a student matching Alex's name at the same school
    When the nightly Clever sync runs
    Then a merge_request record is created
    And Dr. Patel (school admin) is notified in her dashboard
    And Alex's parent receives an email: "Your child's school has found a matching account"

  Scenario: BDD-CONSENT-002 — Parent must consent before school sees home history
    Given a merge has been proposed for Alex Martinez
    When Dr. Patel approves the merge from the admin dashboard
    Then Alex's parent receives a consent request email
    And the merge is not completed until the parent approves
    And until consent is given, Dr. Patel sees only school-session data for Alex

  Scenario: BDD-CONSENT-003 — Parent can revoke school data access
    Given Alex's parent previously consented to school data sharing
    When the parent navigates to Settings → Privacy → School Access
    And clicks "Revoke school access to home progress"
    Then the school data access flag is set to false immediately
    And Dr. Patel's dashboard no longer shows home-session data for Alex
    And Alex's parent receives a confirmation email
```

### 3.5 Robustness & Resilience Tests

#### TC-ROB-001: Stripe Webhook Retry Handling

**Scenario:** Stripe retries a webhook event 3 times (simulating intermittent failures).  
**Expected:** First successful delivery processes event; subsequent deliveries return 200 (idempotency) without reprocessing.  
**Implementation:** Use Stripe CLI `stripe trigger` with forced failures on first two deliveries; verify `stripe_webhook_events` table has exactly one processed row.

```python
async def test_webhook_retry_idempotency(stripe_cli, db_session):
    event_id = "evt_rob_001"
    # Simulate 3 deliveries of the same event
    for attempt in range(3):
        await deliver_webhook(event_id=event_id, db=db_session)

    count = await db_session.scalar(
        select(func.count()).select_from(StripeWebhookEvent)
        .where(StripeWebhookEvent.stripe_event_id == event_id)
    )
    assert count == 1  # Exactly one row regardless of retries
```

#### TC-ROB-002: Clever SSO Failure Graceful Degradation

**Scenario:** Clever API returns 503 during nightly roster sync.  
**Expected:** Sync job marked `failed` in `clever_sync_jobs`; school admin notified by email; existing student data unaffected; no partial state mutations committed.  
**Implementation:** Mock Clever API to return 503 midway through student list. Verify:
- `clever_sync_jobs.status = 'failed'`
- `clever_sync_jobs.error_message` contains the HTTP status
- Students created before failure remain; no orphaned records
- SES email enqueued with sync failure notification

#### TC-ROB-003: Payment Failure Recovery — Dunning Flow Completeness

**Scenario:** Simulate full dunning sequence: payment fails → retries at days 3, 7 → all fail → auto-cancel at day 14.  
**Expected:** Each dunning email triggered at correct day; subscription state transitions correct; student access preserved through day 13; canceled on day 14; data never deleted.  
**Implementation:** Time-warp test using `freezegun` or mock timestamps.

```python
from freezegun import freeze_time

async def test_full_dunning_sequence(db_session, sqs_mock):
    sub = await create_test_subscription(db_session, state="active")

    with freeze_time("2026-06-01"):
        await handle_payment_failed(sub.stripe_subscription_id, db=db_session)
        assert (await get_subscription(sub.id, db_session)).state == "past_due"

    with freeze_time("2026-06-04"):
        await handle_payment_failed(sub.stripe_subscription_id, db=db_session)
        dunning_emails = [m for m in sqs_mock.messages if m["type"] == "dunning_email"]
        assert len(dunning_emails) == 2

    with freeze_time("2026-06-15"):
        await handle_subscription_deleted(sub.stripe_subscription_id, db=db_session)
        final_sub = await get_subscription(sub.id, db_session)
        assert final_sub.state == "canceled"
        # Data preserved
        student = await get_student_by_parent(sub.parent_id, db_session)
        assert student is not None
```

#### TC-ROB-004: SSO Token Expiry Handled Transparently

**Scenario:** Clever access token expires mid-session; refresh token used transparently.  
**Expected:** Sync worker detects 401 from Clever API, refreshes token, retries request, continues sync without error.

#### TC-ROB-005: Redis Cache Failure During Feature Check

**Scenario:** Redis ElastiCache is unreachable for 30 seconds.  
**Expected:** Feature gating falls back to PostgreSQL within 100ms circuit breaker timeout; no feature access denied incorrectly; Redis recovery restores caching automatically.

#### TC-ROB-006: Roster Import with 1,000+ Students

**Scenario:** School admin uploads a 1,000-student CSV file.  
**Expected:** Async processing via SQS job (not synchronous API response); preview shown before import; import completes within 5 minutes; import result page shows success/error counts; no timeout on the HTTP request.

```python
@pytest.mark.integration
async def test_large_roster_import_async(db_session, sqs_mock):
    csv_1000 = generate_test_roster_csv(1000)
    response = await api_client.post(
        "/api/v1/admin/roster/import",
        files={"roster": ("roster.csv", csv_1000, "text/csv")},
    )
    assert response.status_code == 202  # Accepted (async)
    job_id = response.json()["job_id"]
    assert sqs_mock.send_message.called

    # Job completes
    await simulate_sqs_worker(job_id)
    status = await api_client.get(f"/api/v1/admin/roster/import/{job_id}/status")
    assert status.json()["status"] == "completed"
    assert status.json()["students_created"] == 1000
```

#### TC-ROB-007: Concurrent Webhook Delivery (Race Condition Prevention)

**Scenario:** Two identical Stripe webhook events delivered simultaneously to two API pods.  
**Expected:** PostgreSQL `UNIQUE` constraint on `stripe_webhook_events.stripe_event_id` ensures exactly one insertion succeeds; the losing race transaction rolls back cleanly without a 500 error.

#### TC-ROB-008: Analytics Pipeline Backpressure

**Scenario:** PostHog self-hosted instance is unavailable for 1 hour.  
**Expected:** Events buffered in application memory (< 1,000 events, 5-minute window); after 5 minutes, events written to `analytics_events` PostgreSQL table as fallback; PostHog recovery triggers batch replay.

### 3.6 Repeatability Tests

#### TC-REP-001: Subscription State Machine Idempotency

**Test:** Apply the same Stripe webhook event 50 times consecutively. Verify: `subscriptions` table has exactly one state (not incremented); `subscription_events` audit log has exactly one row for that event; no duplicate SQS messages enqueued.

#### TC-REP-002: Roster Sync Consistency (Idempotent Re-Runs)

**Test:** Run `sync_school_roster()` for the same Clever connection 3 times with no Clever data changes. Verify: `students_created = 0`, `students_updated = 0`, `students_unenrolled = 0` on the 2nd and 3rd runs; no duplicate `ClassroomEnrollment` rows.

#### TC-REP-003: A/B Test Assignment Stability

**Test:** Generate variant assignment for student UUID "abc-123" for experiment "ABT-001" 1,000 times (across separate function calls). Verify: all 1,000 calls return identical variant; no randomness introduced.

```python
def test_ab_assignment_stable_across_1000_calls():
    results = set()
    for _ in range(1000):
        variant = deterministic_assign("abc-123", "ABT-001", variants=["control", "variant_a"])
        results.add(variant)
    assert len(results) == 1  # Always the same variant
```

#### TC-REP-004: CSV Import Idempotency

**Test:** Import the same 28-student roster CSV file twice. Verify: no duplicate `StudentProfile` rows; second import logs `action=updated` for all rows; teacher invitation emails sent only once (idempotency via `invited_at` check).

#### TC-REP-005: DPA Content Hash Consistency

**Test:** Generate DPA PDF for the same district data 10 times. Verify: SHA-256 content hash is identical each time (deterministic PDF generation); no race condition creates duplicate `dpa_agreements` rows (UNIQUE constraint on `district_id + dpa_version + signed_at`).

#### TC-REP-006: Feature Cache Re-Population Consistency

**Test:** Delete all Redis feature cache entries; make 100 concurrent feature check requests for the same user. Verify: PostgreSQL is queried exactly once (connection pool handles concurrency); all 100 responses return identical feature set; no thundering herd causes incorrect gating decisions.

### 3.7 Security Tests

#### 3.7.1 PCI-DSS Compliance (Stripe Elements)

**TC-SEC-001: No Card Data on PADI.AI Servers**  
Verify: network inspection of checkout form submission shows zero credit card data in any HTTP request body to `*.padi.ai`. All card data flows directly from browser to Stripe via Stripe.js. PADI.AI servers only receive Stripe's `PaymentMethod` token.  
**Tool:** Playwright network interception + payload inspection.

```typescript
test('TC-SEC-001: no card data transmitted to PADI.AI servers', async ({ page }) => {
  const padiAiRequests: string[] = []
  page.on('request', req => {
    if (req.url().includes('padi.ai')) {
      padiAiRequests.push(req.postData() || '')
    }
  })

  await page.goto('/en/settings/billing/upgrade')
  const stripeFrame = page.frameLocator('iframe[name^="__privateStripeFrame"]')
  await stripeFrame.getByPlaceholder('Card number').fill('4242424242424242')
  await page.getByTestId('submit-payment').click()

  // No padi.ai request should contain card-like data
  const cardPattern = /\b4[0-9]{15}\b|\b4[0-9]{12}(?:[0-9]{3})?\b/
  for (const body of padiAiRequests) {
    expect(body).not.toMatch(cardPattern)
  }
})
```

**TC-SEC-002: Stripe Webhook Secret Not Exposed**  
SAST check (Bandit): `STRIPE_WEBHOOK_SECRET` must only appear in `settings.py` and environment configuration; must never appear in logs, responses, or error messages.

**TC-SEC-003: PCI-DSS SAQ-A Self-Assessment Documentation**  
Annual SAQ-A completion verifying: Stripe Elements used (not self-hosted card forms), no card data storage, TLS 1.2+ enforced on all pages with payment UI.

#### 3.7.2 COPPA Safe Harbor Verification

**TC-SEC-004: Student Events Contain Zero PII**  
Automated schema test on all PostHog events: no `name`, `email`, `first_name`, `last_name`, `birth_date`, or `ip_address` field present in event properties.

```python
def test_all_analytics_events_pii_free(db_session):
    forbidden_keys = {"name", "email", "first_name", "last_name", "birth_date",
                      "ip_address", "phone", "address", "ssn"}
    events = db_session.query(AnalyticsEvent).all()
    for event in events:
        present_keys = set(event.properties.keys())
        violations = present_keys & forbidden_keys
        assert not violations, f"PII in event {event.event_name}: {violations}"
```

**TC-SEC-005: No Analytics Cookies for Student Sessions**  
Playwright test: log in as student; verify zero cookies set with `posthog` or `ph_` prefix; verify `sessionStorage` used for PostHog state (not `localStorage` or `document.cookie`).

**TC-SEC-006: Parental Consent Flow Completeness**  
Manual + automated: verify parent must complete consent flow before any student PII is persisted; verify consent record created in `consent_records` table; verify student cannot be created without associated `parent_id` that has an accepted consent record.

**TC-SEC-007: COPPA Safe Harbor Certification Checklist Verification**  
Automated audit: kidSAFE certification requirements mapped to automated checks (privacy policy reading level via Flesch-Kincaid API, data collection inventory completeness, parental consent mechanism tested).

#### 3.7.3 FERPA DPA Compliance

**TC-SEC-008: DPA Content Hash Integrity**  
Verify: `dpa_agreements.dpa_content_hash` matches SHA-256 of the DPA text at time of signing; any modification to the DPA template creates a new version with new hash; old signed DPAs retain their original hash.

**TC-SEC-009: School Data Isolation — Cross-School Access Denied**  
Test: school_admin at "Rosa Parks Elementary" attempts to access students from "Woodstock Elementary" via direct API calls with manipulated `school_id` parameter.  
**Expected:** PostgreSQL RLS policy blocks access; HTTP 403 returned; no data leaked.

```python
@pytest.mark.security
async def test_cross_school_rls_isolation(db_session, api_client):
    school_a = await create_test_school(db_session, name="Rosa Parks")
    school_b = await create_test_school(db_session, name="Woodstock")
    student_b = await create_test_student(db_session, school_id=school_b.id)

    # Authenticate as school_a admin
    token = await get_school_admin_token(school_a.id)
    response = await api_client.get(
        f"/api/v1/students/{student_b.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403
```

**TC-SEC-010: District Admin Cannot Access Other Districts**  
Similar isolation test: district admin for "Portland Public Schools" cannot read schools/students from "Salem-Keizer School District" via manipulated API calls.

#### 3.7.4 OWASP Top 10 Coverage

**TC-SEC-011: SQL Injection (OWASP A03)**  
DAST with OWASP ZAP; all roster import fields, DPA signing form fields, and subscription management inputs tested for SQL injection. SQLAlchemy 2.0 parameterized queries verified via code review.

**TC-SEC-012: Broken Access Control (OWASP A01)**  
Automated Playwright security tests: teacher attempts to access school admin endpoints; parent attempts to access another parent's student data; all should return 403.

**TC-SEC-013: Security Misconfiguration (OWASP A05)**  
Trivy container scan: zero HIGH or CRITICAL CVEs in all production container images. Stripe webhook endpoint has no CORS headers (server-to-server only). Admin endpoints require MFA (Auth0 configuration verified).

**TC-SEC-014: IDOR Prevention on Student Routes**  
Test: authenticated parent substitutes another parent's student UUID in `/api/v1/students/{id}` — must return 403, not the student data. PostgreSQL RLS policy verified to be the enforcement mechanism (not only application-layer).

**TC-SEC-015: Stripe Webhook Replay Attack Prevention**  
Attempt to replay an old Stripe webhook (timestamp > 300 seconds in the past). Verify: `stripe.Webhook.construct_event()` rejects stale signatures with `SignatureVerificationError`; even if replay succeeds (within 300s window), idempotency table prevents double-processing.

### 3.8 Performance Tests

#### 3.8.1 10,000 Concurrent User Load Test

**Tool:** k6  
**File:** `tests/performance/load-test-10k.js`  
**Scenario:** Simulate school-day peak (3:00–5:00 PM Pacific) with 10,000 concurrent users: 70% students in active practice sessions (WebSocket), 20% parents viewing dashboards, 10% school admins viewing analytics.

```javascript
// tests/performance/load-test-10k.js
import http from 'k6/http'
import ws from 'k6/ws'
import { check, sleep } from 'k6'
import { Rate, Trend } from 'k6/metrics'

const errorRate = new Rate('errors')
const apiLatency = new Trend('api_latency_ms')

export const options = {
  stages: [
    { duration: '5m', target: 2000 },   // Ramp up
    { duration: '10m', target: 10000 }, // Full load
    { duration: '5m', target: 10000 },  // Sustain peak
    { duration: '5m', target: 0 },      // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'],   // P95 < 500ms
    errors: ['rate<0.005'],             // Error rate < 0.5%
    'api_latency_ms{endpoint:practice}': ['p(95)<500'],
    'api_latency_ms{endpoint:dashboard}': ['p(95)<2000'],
  },
}

export default function () {
  const userType = Math.random()

  if (userType < 0.70) {
    // Student practice session
    const res = http.get(`${__ENV.BASE_URL}/api/v1/practice/session`)
    check(res, { 'practice session 200': r => r.status === 200 })
    apiLatency.add(res.timings.duration, { endpoint: 'practice' })
    errorRate.add(res.status !== 200)
    sleep(Math.random() * 2)
  } else if (userType < 0.90) {
    // Parent dashboard
    const res = http.get(`${__ENV.BASE_URL}/api/v1/parents/dashboard`)
    check(res, { 'dashboard 200': r => r.status === 200 })
    apiLatency.add(res.timings.duration, { endpoint: 'dashboard' })
    sleep(5)
  } else {
    // School admin analytics
    const res = http.get(`${__ENV.BASE_URL}/api/v1/admin/school/analytics`)
    check(res, { 'analytics 200': r => r.status === 200 })
    sleep(10)
  }
}
```

**Acceptance criteria:**
- P95 API latency < 500ms
- P95 dashboard load < 2,000ms
- Error rate < 0.5%
- Zero 503s during sustained 10-minute peak

#### 3.8.2 Payment Processing Latency

**TC-PERF-002:** Stripe checkout session creation P95 < 2,000ms (Stripe API call included). Tested under concurrent checkout load of 50 simultaneous purchases. Stripe API timeout configured at 10 seconds with circuit breaker.

#### 3.8.3 Roster Import at Scale

**TC-PERF-003:** 1,000-student CSV import completes within 5 minutes. Async SQS job processes students in batches of 50. Database inserts use bulk `INSERT ... ON CONFLICT DO UPDATE` (not row-by-row). Progress visible in UI via polling `/api/v1/admin/roster/import/{job_id}/status`.

#### 3.8.4 Clever Nightly Sync Performance

**TC-PERF-004:** Full district sync (5 schools × 400 students = 2,000 students) completes within 10 minutes at 02:00 AM. Clever API pagination: 500 students per page. Retry budget: 3 retries with exponential backoff (max 30 seconds wait). Target completion before school day begins.

#### 3.8.5 Feature Cache Throughput

**TC-PERF-005:** 10,000 concurrent feature-check requests for 1,000 unique users. P95 feature check < 5ms (Redis cache hit). P95 feature check on cache miss < 50ms (DB fallback). Cache hit ratio > 95% during sustained load.

### 3.9 MMP Acceptance Criteria (Full Regression)

The MMP milestone requires ALL of the following gates to pass before commercial launch:

| Category | Gate | Tool | Threshold |
|----------|------|------|-----------|
| Test coverage (billing service) | Line coverage | pytest-cov | ≥ 90% |
| Test coverage (school mgmt service) | Line coverage | pytest-cov | ≥ 80% |
| Test coverage (UI components) | Line coverage | Vitest + c8 | ≥ 70% |
| LLM behavioral contracts | Golden set pass rate | Custom validators | ≥ 90% |
| Spanish LLM outputs | Golden set pass rate | Custom validators (ES) | ≥ 90% |
| Accessibility | axe-core violations | axe-core + Playwright | 0 violations (all locales) |
| Security | Critical/High findings | Bandit + OWASP ZAP + Trivy | 0 critical, 0 high |
| Performance (peak load) | P95 API latency at 10K users | k6 | < 500ms |
| Performance (error rate) | Error rate at 10K users | k6 | < 0.5% |
| Uptime SLA | 30-day availability | Datadog | ≥ 99.9% |
| Stripe billing | All state transitions tested | Integration tests | 100% pass |
| COPPA compliance | Analytics PII-free | Automated schema test | 0 PII violations |
| FERPA compliance | Cross-school isolation | Security tests | 0 data leaks |
| COPPA Safe Harbor | kidSAFE application | Legal process | Application submitted |
| i18n completeness | Key parity (en ↔ es) | Build-time validation | 0 missing keys |
| Stage 1–5 regression | All prior lifecycle tests | Full test suite | 100% pass |
| Mutation score (billing SM) | Mutation score | mutmut | ≥ 80% |

---

## 4. Operations Plan

### 4.1 MLOps

#### 4.1.1 Spanish AI Content Generation Pipeline

**Model registry entries for Stage 5:**

| Model | Version | Use Case | Registry Key |
|-------|---------|----------|-------------|
| Claude Sonnet 4.6 | `claude-sonnet-4-20250514` | Spanish tutor hints, question translation | `claude-sonnet-v4.6-prod` |
| o3-mini | `o3-mini-2025-01-31` | Question generation (EN + ES) | `o3-mini-prod` |
| Claude Haiku | `claude-haiku-20240307` | Badge unlock messages, short notifications | `claude-haiku-v3-prod` |

**Spanish prompt versioning:**  
All Spanish prompts versioned separately from English equivalents. Version tags: `tutor_hint_es_v1.0`, `tutor_encouragement_es_v1.0`. Stored in `services/agent-engine/prompts/es/`. Changes require:
1. `prompts/es/*.jinja2` PR with A/B test plan
2. Bilingual math educator review (internal contractor)
3. Spanish golden set validation (≥ 90% pass rate)
4. 48-hour shadow deploy (log but don't serve new prompt)
5. Gradual rollout: 5% → 25% → 100% over 3 days

**Spanish output behavioral contracts (new in Stage 5):**

```python
# tests/contracts/test_spanish_hint_contracts.py
class TestSpanishHintContracts:

    async def test_es_hint_in_correct_language(self, tutor_es, sample_context):
        """Spanish hint must be in Spanish (detect via langdetect)."""
        from langdetect import detect
        hint = await tutor_es.generate_hint(sample_context, hint_level=1)
        assert detect(hint.text) == "es", f"Expected Spanish, got {detect(hint.text)}: {hint.text}"

    async def test_es_hint_does_not_leak_english(self, tutor_es, sample_context):
        """Spanish hint must not contain English phrases in the main body."""
        hint = await tutor_es.generate_hint(sample_context, hint_level=1)
        english_phrases = ["Let's try", "Think about", "Remember that", "First, let"]
        for phrase in english_phrases:
            assert phrase.lower() not in hint.text.lower(), (
                f"English phrase '{phrase}' found in Spanish hint: {hint.text}"
            )

    async def test_es_hint_grade_appropriate_spanish_reading_level(
        self, tutor_es, sample_context
    ):
        """Spanish hint must be readable at grade 4–5 (Fernández-Huerta formula)."""
        hint = await tutor_es.generate_hint(sample_context, hint_level=1)
        fh_score = fernandez_huerta_score(hint.text)
        # Fernández-Huerta: higher = easier; 4th grade ≈ 75-85
        assert 65 <= fh_score <= 95, f"Readability {fh_score} outside range: {hint.text}"
```

**LLM cost tracking (Stage 5 additions):**

| Feature | Model | Est. Tokens/Request | Est. Cost/Request | Monthly Budget |
|---------|-------|--------------------|--------------------|----------------|
| Spanish tutor hint | Claude Sonnet 4.6 | 800 tokens | $0.0072 | $1,440 (10K users) |
| Question translation (EN→ES) | Claude Sonnet 4.6 | 400 tokens | $0.0036 | $360 (100K questions) |
| Badge messages | Claude Haiku | 100 tokens | $0.00008 | $24 |
| Question generation (bulk) | o3-mini | 1,500 tokens | $0.0060 | $600 (expansion) |
| **Total LLM budget** | | | | **$2,424/month** |

#### 4.1.2 Mascot Animation Pipeline (MLOps for Assets)

Pip's Lottie animations are not ML models but are versioned and deployed like model artifacts:

**Animation versioning system:**
```
assets/pip/
├── neutral_v1.0.json       (SHA-256 tracked in asset registry)
├── happy_v1.0.json
├── thinking_v1.0.json
├── encouraging_v1.0.json
├── celebrating_v1.0.json
└── sad_encouraging_v1.0.json
```

- Designer submits new animation to PR; automated test verifies JSON schema (valid Lottie format), file size ≤ 33KB per animation, `prefers-reduced-motion` fallback PNG updated
- Animations deployed to CloudFront CDN with long cache headers (`Cache-Control: max-age=31536000`)
- A/B test capability: `MATH-521-A` vs `MATH-521-B` animation variants served via feature flag

#### 4.1.3 Content Quality Monitoring

**Nightly question analytics refresh:**
- `question_analytics` materialized view refreshed via SQS job at 03:00 Pacific
- Questions flagged automatically: `p1_accuracy < 0.20`, `p1_accuracy > 0.95`, `hint_rate > 0.80`, distractor < 5% selection rate
- Flagged questions queued for curriculum team review in Notion
- Weekly report: question quality dashboard showing flagged count by skill

**BKT drift monitoring (inherited from Stage 3, extended for Stage 5):**
- Monitor BKT parameter drift per skill: alert if `p_learn` changes > 20% week-over-week
- School-context BKT: monitor if school students' mastery trajectories diverge significantly from individual-plan students (may indicate school content relevance gap)
- Spanish-language BKT: monitor if Spanish-preference students have systematically different mastery curves (potential translation quality signal)

#### 4.1.4 LLM Behavioral Contract Testing (Weekly Golden Set)

**Extends Stage 3 contracts with Stage 5 additions:**

| Contract | Language | Frequency | Pass Threshold |
|---------|----------|-----------|----------------|
| Hint Level 1 — no answer | EN | Every PR + weekly | 100% |
| Hint Level 1 — no answer | ES | Every PR (prompt changes) + weekly | 100% |
| Hint sentiment positive | EN + ES | Weekly | ≥ 95% |
| Reading level grade 4–5 | EN | Weekly | ≥ 90% |
| Reading level grade 4–5 (Fernández-Huerta) | ES | Weekly | ≥ 90% |
| Badge message uniqueness | EN + ES | Monthly | 100% unique texts |
| Question correctness (o3-mini gen) | EN + ES | Every batch run | 100% |

**Weekly CI job:** `.github/workflows/llm-contract-tests.yml` runs full golden set every Monday 06:00 UTC. Failure triggers Slack alert + blocks the next production deploy until reviewed.

### 4.2 FinOps

#### 4.2.1 Cost Allocation Tagging Strategy

All AWS resources tagged:

| Tag | Values | Purpose |
|-----|--------|---------|
| `Environment` | `production`, `staging`, `dev` | Per-env cost isolation |
| `Service` | `billing-svc`, `school-mgmt-svc`, `analytics-pipeline`, `async-worker`, `agent-engine`, `api-svc` | Per-service breakdown |
| `Stage` | `5` | Track Stage 5 infra additions |
| `Team` | `engineering`, `ml`, `infra` | Team attribution |
| `CostCenter` | `prod-revenue`, `prod-school`, `prod-consumer` | Business unit allocation |

#### 4.2.2 Stripe Fee Tracking

Stripe charges 2.9% + $0.30 per successful card charge. Track net revenue vs. gross:

```python
# services/billing/analytics/stripe_fee_tracker.py
async def calculate_net_revenue(period_start: date, period_end: date) -> RevenueReport:
    """
    Fetch all successful invoices from Stripe and calculate net revenue
    after fees. Stored in billing_revenue_snapshots for FinOps reporting.
    """
    invoices = await stripe.Invoice.list(
        status="paid",
        created={"gte": period_start.timestamp(), "lte": period_end.timestamp()},
    )
    gross_revenue = sum(inv.amount_paid for inv in invoices) / 100  # cents → dollars
    stripe_fees = sum(inv.metadata.get("stripe_fee", 0) for inv in invoices) / 100
    net_revenue = gross_revenue - stripe_fees

    await db.insert(BillingRevenueSnapshot(
        period_start=period_start,
        period_end=period_end,
        gross_revenue_usd=gross_revenue,
        stripe_fees_usd=stripe_fees,
        net_revenue_usd=net_revenue,
        active_subscriptions=await count_active_subscriptions(),
        mrr_usd=await calculate_mrr(),
    ))
    return RevenueReport(gross=gross_revenue, fees=stripe_fees, net=net_revenue)
```

#### 4.2.3 CDN Cost Optimization at Scale

With 10,000 concurrent users, CloudFront costs are significant. Optimization strategy:

| Content Type | Cache TTL | Expected Hit Ratio | Est. Monthly Savings vs. Origin |
|-------------|----------|-------------------|---------------------------------|
| Translation files (i18n) | 1 year (versioned URLs) | 99% | $180 |
| Pip animation JSON | 1 year (versioned URLs) | 99% | $45 |
| Question images (S3) | 30 days | 95% | $320 |
| API responses (cacheable) | 5 minutes (CloudFront + Redis) | 80% | $240 |
| Video micro-lessons (YouTube) | N/A (YouTube CDN) | 100% | $500 offset |

**Origin Shield:** Enable CloudFront Origin Shield for us-west-2 (Oregon region). Adds $0.008/10K requests but reduces origin hits by 60%, saving ~$400/month at peak.

#### 4.2.4 LLM Cost Controls

**Three-tier architecture:**

| Tier | Model | Use When | Cost |
|------|-------|---------|------|
| Fast/Cheap | GPT-4o-mini | Simple badge messages, session summaries | $0.00015/1K tokens |
| Balanced | o3-mini | Question generation, assessment feedback | $0.004/1K tokens |
| Premium | Claude Sonnet 4.6 | Complex tutor hints, Spanish translation | $0.009/1K tokens |

**Cost guardrails:**
- Daily LLM spend alert at $100 (75% of daily budget)
- Automatic fallback: if Claude Sonnet 4.6 latency > 5 seconds, route to o3-mini (cost and latency savings)
- Question generation batch jobs run during off-peak hours (01:00–05:00 AM Pacific) when spot ECS pricing is 40% cheaper

#### 4.2.5 Reserved Instance & Auto-Scaling Cost Model

| Resource | Commitment | Savings vs. On-Demand | Monthly Cost |
|----------|-----------|----------------------|-------------|
| RDS db.r6g.xlarge (primary) | 1-year reserved | 38% | $145 |
| RDS db.r6g.large (read replica) | On-demand (variable) | — | $73 |
| ElastiCache cache.r6g.large | 1-year reserved | 35% | $89 |
| ECS Fargate (API baseline: 2 tasks) | Fargate Savings Plan | 20% | $120 |
| ECS Fargate (auto-scaled: up to 20 tasks) | On-demand | — | Variable |
| **Total monthly infra (baseline)** | | | **~$850** |

**Auto-scaling cost model:** Peak school-day hours (2:30–5:30 PM Pacific) scale to 20 API tasks and 16 agent engine tasks. Expected peak cost: $0.04/task-hour × 36 tasks × 3 hours × 22 school days = $95/month in peak overage.

#### 4.2.6 Budget Thresholds

| Environment | Monthly Budget | Alert at 75% | Alert at 90% | Hard Stop |
|-------------|---------------|-------------|-------------|-----------|
| Production | $2,500 | $1,875 | $2,250 | None (revenue-generating) |
| Staging | $400 | $300 | $360 | $440 |
| Development | $150 | $113 | $135 | $165 |

**FinOps reviews:** Weekly during Stage 5 active development; monthly after MMP launch. AWS Cost Explorer + Datadog cost dashboard used for tracking.

### 4.3 SecOps

#### 4.3.1 Incident Response Procedures

**Severity classification:**

| Severity | Definition | Response Time | Resolution Time |
|----------|-----------|---------------|-----------------|
| P0 | Billing error (overcharge/undercharge), COPPA data breach, complete service outage | 15 minutes | 4 hours |
| P1 | Partial outage, Stripe webhook processing failure, DPA data exposure | 1 hour | 24 hours |
| P2 | Feature degradation, analytics pipeline failure, Clever sync failure | 4 hours | 72 hours |
| P3 | Non-critical bug, UI rendering issue, slow dashboard | Next business day | 2 weeks |

**Incident response workflow:**
1. **Detect:** Datadog alert or PagerDuty page triggers
2. **Contain:** Take affected service offline if breach suspected; revoke compromised tokens; enable maintenance mode
3. **Eradicate:** Root cause identified; patch applied; secrets rotated if compromised
4. **Recover:** Service restored with fix; post-patch monitoring for 24 hours
5. **Post-mortem:** Blameless post-mortem within 72 hours; action items tracked in GitHub Issues

#### 4.3.2 COPPA Breach Notification Plan

Per COPPA 2025 Final Rule (effective June 23, 2025, compliance by April 22, 2026):

- **72-hour FTC notification:** If a data breach involving children's PII is detected, FTC must be notified within 72 hours. Notification template pre-drafted and stored in legal shared drive.
- **Parent notification:** Affected parents notified within 48 hours of breach confirmation via email
- **Incident log:** All potential breaches logged in `security_incidents` table with severity, detection timestamp, containment timestamp, and resolution
- **Data breach coordinator:** Engineering Lead is primary; Legal Counsel is secondary; CEO for media inquiries
- **COPPA 2025 new requirements:** Separate opt-in consent mechanism for any use of children's data beyond core educational function must be implemented before April 22, 2026

#### 4.3.3 Secret Rotation Schedule

| Secret | Location | Rotation Frequency | Responsible Party |
|--------|----------|-------------------|--------------------|
| `STRIPE_SECRET_KEY` | AWS Secrets Manager | 90 days | Platform Engineer |
| `STRIPE_WEBHOOK_SECRET` | AWS Secrets Manager | 90 days (with Stripe re-registration) | Platform Engineer |
| `STRIPE_PUBLISHABLE_KEY` | Environment variable | On rotation | Platform Engineer |
| `CLEVER_CLIENT_SECRET` | AWS Secrets Manager | 90 days (with Clever re-registration) | Platform Engineer |
| `AUTH0_CLIENT_SECRET` | AWS Secrets Manager | 90 days | Platform Engineer |
| `POSTHOG_API_KEY` | AWS Secrets Manager | 90 days | Platform Engineer |
| `CLAUDE_API_KEY` | AWS Secrets Manager | 90 days | ML Lead |
| `OPENAI_API_KEY` | AWS Secrets Manager | 90 days | ML Lead |
| Database passwords | AWS Secrets Manager | 180 days | Platform Engineer |
| JWT signing keys | AWS Secrets Manager | 180 days | Platform Engineer |

**Rotation procedure:** Automated rotation via AWS Lambda + Secrets Manager rotation function. Services use `boto3` to fetch secrets at startup (no hardcoded values). Rotation tested in staging before production.

#### 4.3.4 RBAC Access Control Matrix

| Role | Billing API | School Mgmt API | Analytics API | Admin API | Student API | Parent API |
|------|------------|----------------|--------------|-----------|-------------|------------|
| STUDENT | ✗ | ✗ | Read (own) | ✗ | Read (self) | ✗ |
| PARENT | Read/Write (own) | ✗ | Read (own children) | ✗ | Read/Write (own children) | Read/Write (self) |
| TEACHER | ✗ | Read (own classrooms) | Read (own classrooms) | ✗ | Read (enrolled students) | ✗ |
| SCHOOL_ADMIN | Read/Write (own school) | Read/Write (own school) | Read (own school) | Read (school) | Read (school students) | ✗ |
| DISTRICT_ADMIN | Read (district) | Read/Write (district) | Read (district) | Read (district) | Read (district students) | ✗ |
| SYSTEM_ADMIN | Full | Full | Full | Full | Full | Full |

#### 4.3.5 PCI-DSS Compliance Posture (Stripe Elements — SAQ-A)

PADI.AI uses Stripe Elements exclusively for card data capture. This qualifies for PCI-DSS SAQ-A (minimal scope) because:
- Card data never touches PADI.AI servers
- Stripe handles all PCI-compliant infrastructure
- TLS 1.2+ enforced on all payment pages (HSTS enabled)

**Annual SAQ-A tasks:**
- Complete and submit SAQ-A self-assessment questionnaire
- Verify Stripe's PCI compliance certificate (updated annually)
- Verify no PAN, CVV, or track data in PADI.AI logs (automated log scan)
- Confirm Stripe Elements JavaScript loaded from `js.stripe.com` (not self-hosted)

#### 4.3.6 Audit Log Retention and Review

| Log Type | Retention | Review Frequency | Tool |
|----------|----------|------------------|------|
| `subscription_events` | Indefinite (immutable) | On-demand + weekly automated anomaly detection | PostgreSQL + Datadog |
| `stripe_webhook_events` | 2 years | Weekly: failed events reviewed | PostgreSQL |
| `dpa_agreements` | 7 years (legal requirement) | Annual: expiry review | PostgreSQL + S3 |
| `clever_sync_jobs` | 1 year | Daily: failed syncs reviewed | PostgreSQL |
| `security_incidents` | Indefinite | On-demand + quarterly review | PostgreSQL |
| CloudTrail (AWS) | 1 year | On-demand | S3 + Athena |
| Auth0 audit logs | 90 days | On-demand | Auth0 dashboard |

### 4.4 DevSecOps Pipeline

#### 4.4.1 CI/CD Security Gates

Every pull request triggers (`.github/workflows/ci.yml`):

```yaml
# .github/workflows/ci.yml (Stage 5 additions)
security-scan:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4

    # Python SAST
    - name: Bandit SAST (Python)
      run: |
        pip install bandit
        bandit -r services/ -ll --format json -o bandit-report.json
        # Fail on HIGH or CRITICAL
        python -c "
        import json, sys
        report = json.load(open('bandit-report.json'))
        high_critical = [i for i in report['results']
                         if i['issue_severity'] in ['HIGH', 'CRITICAL']]
        if high_critical:
            print(f'FAIL: {len(high_critical)} HIGH/CRITICAL findings')
            sys.exit(1)
        "

    # TypeScript SAST
    - name: ESLint Security Plugin
      run: |
        cd apps/web
        npx eslint --plugin security --ext .ts,.tsx src/ --format json > eslint-security.json

    # Container scanning (every build)
    - name: Trivy Container Scan
      uses: aquasecurity/trivy-action@master
      with:
        image-ref: padi-ai/billing-service:${{ github.sha }}
        format: sarif
        severity: HIGH,CRITICAL
        exit-code: 1

    # Dependency audit
    - name: Python Dependency Audit
      run: pip-audit --requirement requirements.txt --format json

    - name: npm Dependency Audit
      run: cd apps/web && npm audit --audit-level=high
```

#### 4.4.2 Weekly Security Jobs

```yaml
# .github/workflows/dast-weekly.yml
dast:
  schedule: [cron: '0 4 * * MON']  # Mondays 04:00 UTC
  steps:
    - name: OWASP ZAP Full Scan
      uses: zaproxy/action-full-scan@v0.9.0
      with:
        target: 'https://staging.padi.ai'
        rules_file_name: '.zap/rules.tsv'
        cmd_options: '-a'

# .github/workflows/dependency-audit.yml
audit:
  schedule: [cron: '0 3 * * MON']  # Mondays 03:00 UTC
  steps:
    - name: Trivy filesystem scan (all services)
      run: trivy fs --severity HIGH,CRITICAL .
    - name: Generate SBOM
      run: trivy sbom --format cyclonedx -o sbom.json .
    - name: Upload SBOM to S3
      run: aws s3 cp sbom.json s3://padi-ai-sbom/$(date +%Y-%m-%d)-sbom.json
```

#### 4.4.3 SBOM (Software Bill of Materials)

Generated weekly via Trivy in CycloneDX format; stored in S3 at `s3://padi-ai-sbom/`. Required for:
- School district procurement offices (some districts require SBOM)
- Supply chain security incident response (identify affected packages rapidly)
- COPPA Safe Harbor audit evidence

#### 4.4.4 Stripe-Specific Security Controls

- **Webhook endpoint:** No CORS headers (server-to-server only); no authentication beyond Stripe signature verification
- **Checkout session creation:** Rate-limited to 10 requests/minute per user (Redis rate limiter)
- **Customer portal:** Authenticated session required; portal session expires in 5 minutes
- **Stripe publishable key:** In client-side code is acceptable (read-only, no secret capability)
- **Stripe secret key:** Never logged, never in responses, rotated every 90 days, stored in AWS Secrets Manager only

---

## 5. Manual QA Plan

Manual QA covers scenarios where automation is insufficient: subjective quality assessment, real-device hardware testing, native speaker review, and regulatory compliance walkthrough.

### 5.1 Payment Flow Walkthrough

**Tester:** QA Lead + Finance representative  
**Environment:** Staging with Stripe test mode  
**Frequency:** Once before MMP launch; after any billing-related code change

| Step | Action | Expected Result | Pass Criteria |
|------|--------|-----------------|---------------|
| 1 | Navigate to `/en/settings/billing/upgrade` as new parent | Plan selection page shown | Page loads < 2s; plans clearly differentiated |
| 2 | Select Individual Monthly; click "Start Free Trial" | Stripe Elements checkout shown | No card data fields except Stripe iframe |
| 3 | Enter test card `4242 4242 4242 4242`, 12/30, CVC 123 | Card accepted indicator shown | Stripe validation inline |
| 4 | Submit checkout | Trial confirmation page shown | "14-day free trial" + end date prominently shown |
| 5 | Navigate to `/en/practice` | No session limit banner | Unlimited access confirmed |
| 6 | Upgrade from Individual to Family | Proration amount shown before confirmation | Proration math verified manually |
| 7 | Attempt Family → Individual downgrade | "Effective at period end" warning shown | Current family features retained |
| 8 | Cancel at period end | Features remain until end date | Student progress visible and intact |
| 9 | Attempt reactivation after cancellation | One-click reactivation works | All prior progress retained |
| 10 | Simulate payment failure (`4000 0000 0000 0341`) | Dunning email received within 5 minutes | Email content reviewed for tone and accuracy |
| 11 | School invoice flow: select "Pay by Invoice" | PO number field shown; invoice emailed | Invoice PDF opened and verified for accuracy |
| 12 | Test subscription in Spanish locale (`/es/`) | All billing UI in Spanish | Native Spanish speaker reviews translation |

### 5.2 School Admin Onboarding Experience

**Tester:** QA Lead + mock school admin (non-engineer)  
**Environment:** Staging  
**Frequency:** Once before MMP launch; after any onboarding flow change

| Step | Action | Expected Result | Pass Criteria |
|------|--------|-----------------|---------------|
| 1 | School admin creates account via invitation link | Account created; school profile setup starts | Clear onboarding flow; no dead ends |
| 2 | Complete school profile form | Form validates correctly | NCES ID validation; ZIP code format enforced |
| 3 | Read DPA — attempt to sign without scrolling | Sign button disabled | Cannot bypass DPA scroll requirement |
| 4 | Scroll to bottom; sign DPA | Signature accepted; email received within 10 min | DPA PDF opened; content verified |
| 5 | Upload sample roster CSV (provided fixture) | Preview shown: 28 students, 2 teachers | Preview matches expected counts |
| 6 | Confirm import | 28 students created; 2 teacher invites sent | Admin can see students in dashboard |
| 7 | View school admin dashboard | Proficiency distribution + standards grid visible | Data loads correctly; chart labels readable |
| 8 | View classroom comparison table | One row per classroom with metrics | Verify "learning journey" framing (no ranking language) |
| 9 | Set up Clever SSO (using test Clever sandbox) | OAuth flow completes; 5 test students synced | Students appear in dashboard after sync |
| 10 | View Oregon DOE compliance report | PDF downloadable; student data anonymized | Report format verified against ODE conventions |
| 11 | Attempt access as teacher (vs. school admin) | Teacher sees only own classrooms | Role enforcement verified at UI level |

### 5.3 Spanish Language Content Review (Native Speaker)

**Tester:** Native Spanish speaker (bilingual educator or professional translator)  
**Scope:** Full Spanish UI + sample tutor interactions + email templates  
**Frequency:** Before MMP launch; quarterly thereafter

**Review checklist:**

| Area | Specific Checks | Quality Bar |
|------|----------------|-------------|
| UI strings (menus, buttons) | Correct Spanish grammar; no literal English translations; natural phrasing | Zero grammatical errors |
| Math terminology | Correct Spanish math terms (e.g., "fracción" not "fracción de número", "denominador" spelled correctly) | 100% math terms correct |
| Pip tutor responses (10 sample interactions) | Friendly, encouraging tone in Mexican/Pacific Northwest Spanish; appropriate for 9–10-year-old | No awkward literal translations |
| Error messages | Helpful and non-alarming; clear instructions | Clear to a non-technical Spanish speaker |
| Dunning emails | Professional, empathetic tone; clear action steps | Passes bilingual parent review |
| Badge unlock messages | Celebratory, age-appropriate | Suitable for a 4th grader |
| Math Mission descriptions | Oregon context feels authentic; no culturally jarring elements | Oregon Hispanic community familiar and comfortable |
| Word problem translations | Mathematical accuracy preserved; no ambiguity from translation | Bilingual math educator verification |

### 5.4 Mascot Interaction Quality (Pip)

**Tester:** QA Lead + child usability tester (9–10-year-old, parental consent obtained)  
**Environment:** Staging on iPad and desktop Chrome  
**Frequency:** Before MMP launch

| Interaction | Device | Test Action | Pass Criteria |
|------------|--------|-------------|---------------|
| Pip neutral/idle | iPad | Let practice session idle for 10 seconds | Subtle breathing motion visible; not distracting |
| Pip happy (correct) | Desktop | Answer question correctly | Happy animation triggers ≤ 300ms; feels rewarding |
| Pip encouraging (wrong) | iPad | Answer question incorrectly | Encouraging animation plays; message visible; not shaming |
| Pip thinking | Desktop | Wait for question to load | Chin-tap gesture during BKT computation |
| Pip celebrating (mastery) | Desktop | Trigger mastery event | Full spin + confetti; feels celebratory (child tester reacts positively) |
| Pip sad_encouraging | iPad | Answer 3+ questions incorrectly in a row | Recovery animation ("We'll get through this!") — not discouraging |
| Reduced motion (desktop) | Desktop | Enable `prefers-reduced-motion` | Static PNG shows; no animation; Pip still present |
| Reduced motion (iOS) | iPhone | Enable Reduce Motion in iOS Settings | Same static image; no Lottie playback |
| Animation asset size | DevTools | Network tab: total Pip assets | ≤ 200KB total before compression |
| Cross-browser | Firefox | Run all 6 states | All animations play correctly |

### 5.5 Handwriting Recognition Accuracy

**Tester:** QA Lead  
**Devices:** iPad Pro (Apple Pencil), iPad Air (finger), Samsung Galaxy Tab S8 (S Pen)  
**Frequency:** Before MMP launch; after any OCR library update

| Test Input | Writing Style | Expected Recognition | Pass Criteria |
|-----------|--------------|---------------------|---------------|
| Single digit: `7` | Clear handwriting | `7` | ≥ 90% recognition |
| Single digit: `1` | Ambiguous (could be `l`) | `1` | ≥ 85% |
| Two-digit: `42` | Normal handwriting | `42` | ≥ 85% |
| Three-digit: `375` | Clear handwriting | `375` | ≥ 85% |
| Four-digit: `1,024` | With comma | `1024` (stripped) | ≥ 80% |
| Low confidence: scribble | Messy | < 0.80 confidence | Keypad fallback shown |
| Erasure (finger smear) | After erasure | Fresh recognition | Canvas clears correctly |
| Decimal: `3.5` | With decimal point | `3.5` | ≥ 80% |
| Negative: `-12` | With minus sign | `-12` | ≥ 75% |
| Toggle to keypad | During handwriting | Keypad shown | Instant switch, no data loss |

**Accept/reject threshold:** If recognition accuracy falls below 85% for simple digits on iPad Pro with Apple Pencil, OCR library replaced or confidence threshold tuned before launch.

### 5.6 COPPA Safe Harbor Compliance Checklist

**Tester:** Legal Counsel + Engineering Lead  
**Frequency:** Before MMP launch (initial); annually  
**Reference:** kidSAFE certification requirements + COPPA 2025 Final Rule

| Requirement | Status | Evidence | Notes |
|------------|--------|---------|-------|
| Privacy policy at accessible reading level (≤ 9th grade FK) | Verify | Flesch-Kincaid score computed | Run before MMP launch |
| Privacy Summary page published at `/privacy/summary` | Verify | URL accessible unauthenticated | Review for plain language |
| Verifiable parental consent before student PII collected | Verify | Consent record in DB before student creation | Manual walkthrough of consent flow |
| No analytics cookies for student accounts | Verify | Browser DevTools: zero posthog/ph_ cookies | Test on Chrome, Firefox, Safari |
| Student analytics pseudonymized (no PII in events) | Verify | Automated test TC-SEC-004 passes | Review 20 random events |
| No third-party advertising on student-facing pages | Verify | Network tab: no ad tracker calls | Test all student-facing routes |
| PostHog self-hosted (student data not sent to PostHog cloud) | Verify | PostHog endpoint config | Check `api_host` in posthog.init |
| Data deletion within 48 hours of request | Verify | Deletion workflow tested | E2E deletion walkthrough |
| Student Privacy Pledge signed | Verify | Pledge certificate | Organizational commitment |
| kidSAFE application submitted | Verify | Application acknowledgment | Legal process |
| Annual privacy audit scheduled | Calendar | October 2026 | Calendar invitation created |

### 5.7 Dark Mode Visual QA

**Tester:** QA Lead + Frontend Engineer  
**Devices:** MacBook Pro (Safari), Windows Chrome, iPhone 15 (iOS Safari), iPad Pro  
**Frequency:** Before MMP launch; after any design system changes

| View | Dark Mode Check | Pass Criteria |
|------|----------------|---------------|
| Student practice session | Background dark; text cream; math equations visible | No white flash on page load; all text readable |
| Parent dashboard | Charts readable in dark palette; card borders visible | Color encoding preserved (red/yellow/green) |
| KaTeX equation rendering | Math symbols clearly visible | Equations not invisible against dark background |
| Pip animations | Mascot visible against dark background | Pip edges distinct; not washed out |
| Badge display | Badge colors distinguishable | No badge lost in dark background |
| Stripe checkout | Stripe Elements dark mode (configured) | Card input fields readable |
| School admin dashboard | Standards coverage grid color coding intact | Red/yellow/green cells still distinct |
| Math Mission countdown timer | Timer readable | Countdown numbers high contrast |
| Error states | Error messages legible | Red error text meets WCAG 4.5:1 contrast in dark mode |
| High-contrast mode | Black/white only; no gradients | Verified with axe-core + manual inspection |

**Automated complement:** Playwright visual regression snapshot comparison (`dark-mode.png` baseline) for all major views. Any pixel diff > 0.1% triggers manual review.

### 5.8 MMP Launch Readiness Checklist

This checklist must be 100% complete before any public marketing or school sales activity begins.

#### Legal & Compliance
- [ ] COPPA Safe Harbor application submitted to kidSAFE (or equivalent) — Month 15
- [ ] Student Privacy Pledge signed and published
- [ ] Privacy policy at ≤ 9th grade Flesch-Kincaid level — verified
- [ ] Privacy Summary page live at `/privacy/summary`
- [ ] FERPA DPA template reviewed by legal counsel
- [ ] FERPA DPA template includes all required disclosures (subprocessors, retention, deletion, security)
- [ ] PCI-DSS SAQ-A completed for current year
- [ ] Data minimization audit document finalized

#### Billing & Payments
- [ ] Stripe live mode keys configured (not test mode)
- [ ] All 5 Stripe Products/Prices created in live mode
- [ ] Stripe webhook endpoint registered with live mode secret
- [ ] Webhook endpoint tested with `stripe listen` in production
- [ ] All billing lifecycle scenarios tested in staging with Stripe test clock
- [ ] Dunning email sequence tested end-to-end
- [ ] School invoice flow tested (PDF generation, Net 30 terms)
- [ ] Subscription portal configured in Stripe Dashboard (for payment method updates)

#### School Onboarding
- [ ] DPA PDF generation tested and legal-approved
- [ ] CSV roster import tested with 1,000-student file
- [ ] Clever OAuth app registered with Clever and approved
- [ ] Nightly sync tested against Clever sandbox
- [ ] Google Workspace SSO tested against Google Workspace test tenant
- [ ] School admin dashboard load tested (500 students)

#### Engagement & UX
- [ ] All 6 Pip Lottie animations finalized and ≤ 200KB total
- [ ] Static PNG fallbacks created for all 6 Pip states
- [ ] All 21 badge icons designed and uploaded to CDN
- [ ] 52 Math Mission question sets authored and validated
- [ ] Video micro-lessons (29 videos) uploaded to YouTube (unlisted, privacy-enhanced)
- [ ] Handwriting recognition accuracy ≥ 85% on iPad Pro (Apple Pencil)

#### Internationalization
- [ ] All UI strings translated to Spanish — `es.json` key parity verified by build
- [ ] Spanish tutor prompts reviewed by bilingual math educator
- [ ] All transactional email templates in Spanish
- [ ] Progress report PDF generation tested in Spanish
- [ ] Spanish badge names and descriptions reviewed by native speaker

#### Content
- [ ] Question bank ≥ 10,000 questions verified (SELECT COUNT(*) FROM practice_questions)
- [ ] All 29 skills with ≥ 50 questions at minimum
- [ ] Spanish translations for all questions verified (SELECT COUNT(*) WHERE text_es IS NOT NULL = COUNT(*))
- [ ] Question analytics flagging pipeline operational (nightly refresh confirmed)

#### Performance
- [ ] k6 load test at 10,000 concurrent users — all thresholds pass
- [ ] Auto-scaling policy tested (ECS scales from 2 to 20 API tasks under load)
- [ ] CloudFront Origin Shield enabled for us-west-2
- [ ] PgBouncer configured for connection pooling
- [ ] Read replica configured and load balancing verified
- [ ] 99.9% uptime SLA monitoring configured in Datadog

#### Security
- [ ] All Bandit HIGH/CRITICAL findings resolved (CI gate passing)
- [ ] OWASP ZAP DAST run against staging — zero HIGH/CRITICAL findings
- [ ] Trivy container scan — zero HIGH/CRITICAL CVEs in all images
- [ ] Cross-school RLS isolation tests passing
- [ ] COPPA analytics PII-free tests passing
- [ ] Stripe card data isolation tests passing
- [ ] Secret rotation procedure documented and tested in staging
- [ ] SBOM generated and stored in S3

#### Operations
- [ ] Datadog dashboards configured: billing metrics, school onboarding metrics, error rates, LLM costs
- [ ] PagerDuty escalation policy updated for Stage 5 services
- [ ] Runbooks written for: payment webhook failure, Clever sync failure, subscription state drift, DPA expiry
- [ ] FinOps budget alerts configured in AWS for production, staging, dev
- [ ] On-call rotation includes Stage 5 service owners

#### Launch Communication
- [ ] App Store listing prepared (if mobile app)
- [ ] School/district sales deck ready (referencing FERPA DPA and COPPA Safe Harbor)
- [ ] Press release drafted for MMP announcement
- [ ] Support documentation updated (billing FAQ, school onboarding guide, Spanish support guide)

---

*Document Status: Complete*  
*Next Review: Month 17 mid-point checkpoint (Month 17, Week 2)*  
*Owner: Engineering Lead*  
*Distribution: Engineering, Product, Legal, QA, Design, Operations*
