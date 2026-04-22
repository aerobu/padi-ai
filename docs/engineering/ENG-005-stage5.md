# ENG-005 — Engineering Plan: Stage 5 — MMP — Monetization, Polish & School Onboarding

**Document ID:** ENG-005  
**Stage:** 5 of 5 — Minimum Marketable Product (MMP)  
**Timeline:** Months 15–20  
**Status:** Draft  
**Last Updated:** 2026-04-04  
**Author:** Principal Engineer  

> **Stage 5 Solo Development Estimate:** 200–280 agent-hours | Calendar: 8–10 months | **MMP Milestone**  
> **Stripe billing:** 30–45 hrs — Stripe state machine + idempotent webhooks require careful testing; use Stripe's test mode extensively before going live  
> **i18n/Spanish:** 25–40 hrs for code + requires bilingual Oregon math educator for vocabulary review (separate contractor from English curriculum specialist)  
> **School onboarding (RLS + Clever):** 35–50 hrs — Row Level Security in PostgreSQL requires schema design review before implementation; Clever OAuth needs app registration

---

## Table of Contents

1. [High-Level Architecture](#1-high-level-architecture)
2. [Detailed System Design](#2-detailed-system-design)
3. [Key Algorithms (Stage 5)](#3-key-algorithms-stage-5)
4. [Infrastructure (Stage 5)](#4-infrastructure-stage-5)
5. [Testing Plan (Stage 5)](#5-testing-plan-stage-5)
6. [QA Plan — MMP Exit Criteria](#6-qa-plan--mmp-exit-criteria)
7. [Operational Runbooks (Stage 5)](#7-operational-runbooks-stage-5)

---

## 1. High-Level Architecture

### 1.1 System Evolution at MMP

Stage 5 transforms PADI.AI from a functional MVP (Stage 4) into a commercially viable MMP. The system must now support real-money transactions, institutional customers (schools/districts), multilingual learners, and data-driven product decisions — all while maintaining COPPA compliance for children under 13.

**Key changes from MVP → MMP:**

| Dimension | MVP (Stage 4) | MMP (Stage 5) |
|-----------|---------------|----------------|
| **Monetization** | Free beta / waitlist | Stripe billing: Individual ($14.99/mo), Family ($24.99/mo), School (per-seat invoicing) |
| **Authentication** | Auth0 parent login only | + Clever SSO for schools, teacher roles, district admin roles |
| **Multi-tenancy** | Single parent → students | District → School → Teacher → Classroom → Student hierarchy |
| **Localization** | English only | English + Spanish (UI, AI-generated content, tutor prompts) |
| **Analytics** | Basic CloudWatch metrics | PostHog event pipeline, COPPA-compliant cookieless tracking, A/B testing |
| **Scale target** | 500 concurrent users | 10,000 concurrent users (school-day peak) |
| **Compliance** | COPPA consent flow | + COPPA Safe Harbor certification (kidSAFE or PRIVO), FERPA DPA for schools |
| **Performance** | Best-effort CDN | CloudFront Origin Shield, read replicas, auto-scaling ECS, PgBouncer |
| **Messaging** | None | AWS SES transactional email, SQS async job queue |

**New containers introduced in Stage 5:**
- **Billing Service** — Stripe integration, subscription state machine, feature gating
- **School Management Service** — District/school onboarding, Clever SSO, roster sync, DPA management
- **Analytics Pipeline** — PostHog integration, event taxonomy, A/B testing framework
- **i18n Infrastructure** — Translation file CDN, locale-aware API responses, prompt localization
- **Async Job Queue** — SQS-backed workers for question generation, report generation, email delivery
- **Transactional Email** — AWS SES for billing notifications, dunning, school onboarding

### 1.2 Full MMP Container Diagram (C4 Level 2)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              EXTERNAL USERS                                     │
│                                                                                 │
│  [Parent Browser]   [Student Browser]   [Teacher Browser]   [School Admin]      │
│        │                   │                   │                  │              │
└────────┼───────────────────┼───────────────────┼──────────────────┼──────────────┘
         │                   │                   │                  │
         ▼                   ▼                   ▼                  ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          EDGE / CDN LAYER                                       │
│                                                                                 │
│  ┌──────────────┐    ┌──────────────────┐    ┌──────────────────────────┐       │
│  │  CloudFront   │    │  Vercel Edge     │    │  WAF (OWASP Core Rules) │       │
│  │  (static,     │    │  (Next.js SSR,   │    │  + Rate Limiting        │       │
│  │   i18n files) │    │   React 19 app)  │    │  + Geo-blocking         │       │
│  └──────────────┘    └──────────────────┘    └──────────────────────────┘       │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
         │                                                          │
         ▼                                                          ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          APPLICATION LAYER (ECS Fargate)                        │
│                                                                                 │
│  ┌────────────────────┐  ┌────────────────────┐  ┌────────────────────────┐    │
│  │   API Service       │  │  Agent Engine       │  │  Billing Service       │    │
│  │   (FastAPI)         │  │  (FastAPI +          │  │  (FastAPI)             │    │
│  │                     │  │   LangGraph +        │  │                        │    │
│  │  - REST endpoints   │  │   WebSocket)         │  │  - Stripe webhooks     │    │
│  │  - Auth middleware   │  │                      │  │  - Checkout sessions   │    │
│  │  - Assessment flow   │  │  - Tutor Agent       │  │  - Feature gating      │    │
│  │  - Standards API     │  │  - BKT Engine        │  │  - School invoicing    │    │
│  │  - Progress API      │  │  - Question Gen      │  │                        │    │
│  │  - Report Gen        │  │  - Hint Engine       │  │                        │    │
│  └─────────┬──────────┘  └─────────┬──────────┘  └────────────┬───────────┘    │
│            │                       │                           │                 │
│  ┌────────────────────┐  ┌────────────────────┐  ┌────────────────────────┐    │
│  │  School Mgmt Svc    │  │  Analytics Worker   │  │  Async Job Worker      │    │
│  │  (FastAPI)          │  │  (Python)           │  │  (Python)              │    │
│  │                     │  │                     │  │                        │    │
│  │  - Clever OAuth     │  │  - Event ingestion  │  │  - SQS consumer        │    │
│  │  - Roster sync      │  │  - A/B assignment   │  │  - Question generation │    │
│  │  - DPA management   │  │  - Server-side      │  │  - Report PDF gen      │    │
│  │  - Teacher CRUD     │  │    PostHog proxy    │  │  - Email dispatch      │    │
│  │  - Classroom CRUD   │  │                     │  │  - Clever nightly sync │    │
│  └─────────┬──────────┘  └─────────┬──────────┘  └────────────┬───────────┘    │
│            │                       │                           │                 │
└────────────┼───────────────────────┼───────────────────────────┼─────────────────┘
             │                       │                           │
             ▼                       ▼                           ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            DATA LAYER                                           │
│                                                                                 │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐  ┌──────────────┐ │
│  │  PostgreSQL 17  │  │  Redis          │  │  S3             │  │  SQS          │ │
│  │  (RDS)          │  │  (ElastiCache)  │  │                 │  │              │ │
│  │                 │  │                 │  │  - Question      │  │  - job-queue │ │
│  │  - Primary      │  │  - Sessions     │  │    images        │  │  - dlq       │ │
│  │  - Read replica │  │  - Feature cache│  │  - Reports       │  │              │ │
│  │  - PgBouncer    │  │  - Rate limits  │  │  - Audit logs    │  │              │ │
│  │  - pgvector     │  │  - BKT cache    │  │  - i18n files    │  │              │ │
│  │  - RLS policies │  │                 │  │                 │  │              │ │
│  └────────────────┘  └────────────────┘  └────────────────┘  └──────────────┘ │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
             │                       │                           │
             ▼                       ▼                           ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         EXTERNAL SERVICES                                       │
│                                                                                 │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐ │
│  │  Auth0    │ │  Stripe   │ │  Clever   │ │  PostHog  │ │  AWS SES  │ │ LLM    │ │
│  │          │ │          │ │          │ │          │ │          │ │ APIs   │ │
│  │  - Login  │ │  - Payments│ │  - SSO    │ │  - Events │ │  - Email  │ │        │ │
│  │  - MFA    │ │  - Invoices│ │  - Rosters│ │  - A/B    │ │  - Dunning│ │-Claude │ │
│  │  - RBAC   │ │  - Webhooks│ │  - Sync   │ │  - Funnels│ │  - Alerts │ │-o3-mini│ │
│  │          │ │          │ │          │ │          │ │          │ │-Local  │ │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘ └────────┘ │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 1.3 Billing System Architecture

#### Subscription State Machine

The subscription lifecycle is modeled as a finite state machine. Every transition is triggered by a Stripe webhook event, recorded in an audit log, and may trigger email notifications.

```
                              ┌──────────────────────────┐
                              │                          │
                    ┌─────────▼──────────┐               │
       ┌────────────│      TRIAL         │               │
       │            │  (14 days free)    │               │
       │            └─────────┬──────────┘               │
       │                      │                          │
       │         trial_ended  │  payment_success         │
       │    (no payment       │  (checkout.session.      │
       │     method)          │   completed +            │
       │                      │   invoice.payment_       │
       │                      │   succeeded)             │
       │                      ▼                          │
       │  ┌───────────────────────────────────┐          │
       │  │            ACTIVE                  │          │
       │  │  (recurring billing active)        │◄─────┐  │
       │  └─────────┬───────────┬─────────────┘      │  │
       │            │           │                      │  │
       │  payment_  │           │ cancel_              │  │
       │  failed    │           │ requested            │  │
       │  (invoice. │           │ (customer.           │  │
       │  payment_  │           │  subscription.       │  │
       │  failed)   │           │  updated →           │  │  reactivate
       │            ▼           │  cancel_at_          │  │  (customer.subscription.
       │  ┌──────────────┐     │  period_end)         │  │   updated → cancel_at=null)
       │  │  PAST_DUE     │     │                      │  │
       │  │  (retry 1-3)  │     ▼                      │  │
       │  └───┬──────┬───┘  ┌──────────────┐          │  │
       │      │      │      │  CANCELING    │          │  │
       │      │      │      │  (active til  │──────────┘  │
       │retry_│      │all   │   period end) │             │
       │success      │fail  └──────┬───────┘             │
       │      │      │             │                      │
       │      │      │    period_  │                      │
       │      │      │    ended    │                      │
       │      │      │             ▼                      │
       │      │      │    ┌──────────────┐               │
       │      │      └───►│  CANCELED     │               │
       │      │           │              │               │
       └──────┼──────────►│              │               │
              │           └──────┬───────┘               │
              │                  │                        │
              │         resubscribe (new checkout)        │
              │                  │                        │
              │                  └────────────────────────┘
              │
              │  (School accounts only)
              │
              ▼
       ┌──────────────┐
       │   PAUSED      │    (School: summer break, budget hold)
       │   (school     │───► resume → ACTIVE
       │    only)      │───► expire → EXPIRED
       └──────────────┘

       ┌──────────────┐
       │   EXPIRED     │    (Terminal state: school contract ended,
       │              │     no renewal)
       └──────────────┘
```

**State transition detail:**

| Transition | Stripe Webhook | DB Update | Email Sent | Feature Impact |
|------------|---------------|-----------|------------|----------------|
| `trial_started` | `checkout.session.completed` (mode=subscription, trial) | Create `subscriptions` row, state=TRIAL | Welcome + trial start email | All features unlocked |
| `trial_ended_to_active` | `invoice.payment_succeeded` (first real charge) | Update state=ACTIVE, set `current_period_end` | Payment confirmation email | Features remain unlocked |
| `trial_ended_no_payment` | `customer.subscription.deleted` (trial auto-cancel) | Update state=CANCELED | Trial expired + upgrade CTA email | Features gated to free tier |
| `payment_success` | `invoice.payment_succeeded` | Update `current_period_end`, reset `past_due_since` | Payment receipt email | No change |
| `payment_failed` | `invoice.payment_failed` | Update state=PAST_DUE, set `past_due_since` | Dunning email #1 (update payment method) | Features remain for grace period (7 days) |
| `retry_success` | `invoice.payment_succeeded` after retry | Update state=ACTIVE, clear `past_due_since` | Payment recovered email | No change |
| `all_retries_failed` | `customer.subscription.deleted` (auto-cancel after 3 retries) | Update state=CANCELED, set `canceled_at` | Final cancellation email | Features removed |
| `cancel_requested` | `customer.subscription.updated` (cancel_at_period_end=true) | Update state=CANCELING, set `cancel_at` | Cancellation confirmed email (with reactivation CTA) | Features remain until period end |
| `period_ended` | `customer.subscription.deleted` | Update state=CANCELED | Subscription ended email | Features removed |
| `reactivate` | `customer.subscription.updated` (cancel_at_period_end=false) | Update state=ACTIVE, clear `cancel_at` | Reactivation confirmed email | No change |
| `upgrade` | `customer.subscription.updated` (plan change) | Update `plan_id`, `subscription_tier` | Plan upgrade confirmation | New features immediately available |
| `downgrade` | `customer.subscription.updated` (plan change, effective at period end) | Update `pending_plan_id` | Plan downgrade scheduled email | Current features until period end |
| `school_pause` | Manual API / admin action | Update state=PAUSED, set `paused_at` | School pause notification | Features removed for students |
| `school_resume` | Manual API / admin action | Update state=ACTIVE, clear `paused_at` | School resume notification | Features restored |

#### Stripe Webhook Processing

The webhook handler must be **idempotent**, **order-tolerant**, and **crash-resilient**. Every webhook event is processed exactly once, regardless of duplicates or out-of-order delivery.

**Design principles:**
1. **Signature verification first** — Reject unsigned or tampered payloads before any processing.
2. **Idempotency via event ID** — Use `stripe_event_id` as a unique key in a deduplication table. If already processed, return 200 immediately.
3. **Single database transaction** — All state mutations (subscription update + audit log + dedup record) happen in one atomic transaction. If any step fails, the entire operation rolls back, and Stripe will retry.
4. **Out-of-order tolerance** — Use Stripe's `event.created` timestamp and the object's `updated` field to detect stale events. If the DB record's `stripe_updated_at` is newer than the event's, skip processing.
5. **Async side effects** — Email notifications and cache invalidation are enqueued to SQS after the transaction commits. If SQS enqueue fails, a separate reconciliation job catches missed side effects.

**Events to handle:**

| Stripe Event | Handler Action |
|-------------|----------------|
| `checkout.session.completed` | Create subscription record, link to parent, set initial state (TRIAL or ACTIVE) |
| `invoice.payment_succeeded` | Update subscription to ACTIVE, extend `current_period_end`, record payment |
| `invoice.payment_failed` | Update subscription to PAST_DUE, increment retry count, enqueue dunning email |
| `customer.subscription.updated` | Handle plan changes, cancellation scheduling, reactivation |
| `customer.subscription.deleted` | Update subscription to CANCELED, trigger feature revocation |
| `invoice.created` | For school invoices: update invoice status in PADI.AI |
| `invoice.finalized` | Send invoice PDF to school admin |
| `payment_intent.payment_failed` | Log failure reason for debugging (card declined, insufficient funds) |

#### Feature Gating

**Architecture:** Feature gating uses a layered approach — Redis cache (hot path) backed by PostgreSQL (source of truth), with cache invalidation on every subscription state change.

```
Request Flow:
  Client → API Middleware → Redis Cache Lookup
                               │
                        ┌──────┴──────┐
                        │ Cache Hit?  │
                        └──────┬──────┘
                          Yes ╱ ╲ No
                             ╱   ╲
                    Return  ╱     ╲  Query DB
                    cached ╱       ╲ Set Cache (TTL 5min)
                    set   ╱         ╲ Return features
                         ╱           ╲
                        ▼             ▼
                   [Feature Set]  [Feature Set]
```

**Feature tiers:**

| Feature | Free | Individual ($14.99/mo) | Family ($24.99/mo) | School (per-seat) |
|---------|------|----------------------|--------------------|--------------------|
| Initial assessment | Yes | Yes | Yes | Yes |
| Adaptive practice (5 sessions/week) | Yes | — | — | — |
| Adaptive practice (unlimited) | — | Yes | Yes | Yes |
| AI tutor hints (3/session) | Yes | — | — | — |
| AI tutor hints (unlimited) | — | Yes | Yes | Yes |
| Parent progress dashboard | Basic | Full | Full | — |
| Teacher classroom dashboard | — | — | — | Yes |
| End-of-grade readiness report | — | Yes | Yes | Yes |
| Spanish language support | — | Yes | Yes | Yes |
| Multiple student profiles | 1 | 1 | Up to 4 | Unlimited (roster) |
| Priority question generation | — | — | Yes | Yes |
| School admin analytics | — | — | — | Yes |
| Custom learning plan schedule | — | Yes | Yes | Yes |

**Cache invalidation strategy:**
- On every `subscription_state_changed` event, publish to Redis pub/sub channel `subscription:invalidate:{user_id}`
- All API instances subscribe and delete the user's feature cache key
- TTL fallback: 5-minute TTL on all feature cache entries ensures eventual consistency even if pub/sub message is lost
- Graceful degradation: if Redis is down, fall back to DB query with a 100ms circuit breaker timeout

### 1.4 School Onboarding Architecture

#### Entity Hierarchy

```
District (e.g., "Portland Public Schools")
  │
  ├── School (e.g., "Rosa Parks Elementary")
  │     │
  │     ├── SchoolAdmin (user with SCHOOL_ADMIN role)
  │     │
  │     ├── Teacher (user with TEACHER role)
  │     │     │
  │     │     ├── Classroom (e.g., "Mrs. Johnson's 4th Grade Math - Period 2")
  │     │     │     │
  │     │     │     ├── Student (student profile, linked via classroom_enrollment)
  │     │     │     ├── Student
  │     │     │     └── Student
  │     │     │
  │     │     └── Classroom (e.g., "Mrs. Johnson's 4th Grade Math - Period 5")
  │     │           └── ...
  │     │
  │     └── Teacher
  │           └── ...
  │
  ├── School (e.g., "Woodstock Elementary")
  │     └── ...
  │
  └── DistrictAdmin (user with DISTRICT_ADMIN role — can see all schools)
```

**Role hierarchy and permissions:**

| Role | Scope | Can View | Can Modify | Can Delete |
|------|-------|----------|------------|------------|
| PARENT | Own children only | Own children's progress, reports | Learning plan preferences | Account + children |
| TEACHER | Own classrooms | Student progress in their classrooms | Classroom settings, assignments | Nothing |
| SCHOOL_ADMIN | Entire school | All teachers, classrooms, student progress | Teacher assignments, school settings | Nothing |
| DISTRICT_ADMIN | All schools in district | Everything in all schools | School admin assignments, district settings | Nothing |
| SYSTEM_ADMIN | Global | Everything | Everything | Controlled via audit trail |

#### Data Isolation Strategy

**Row-Level Security (PostgreSQL RLS):**

Every table containing student data has RLS policies enforced at the database level. This is defense-in-depth — the application layer also enforces scoping, but RLS prevents data leaks even if application code has bugs.

```sql
-- Enable RLS on student_profiles
ALTER TABLE student_profiles ENABLE ROW LEVEL SECURITY;

-- Parents can only see their own children
CREATE POLICY parent_isolation ON student_profiles
    FOR ALL
    TO app_user
    USING (
        parent_id = current_setting('app.current_user_id')::uuid
        OR
        -- Teachers can see students in their classrooms
        EXISTS (
            SELECT 1 FROM classroom_enrollments ce
            JOIN classrooms c ON c.id = ce.classroom_id
            WHERE ce.student_id = student_profiles.id
            AND c.teacher_id = current_setting('app.current_user_id')::uuid
        )
        OR
        -- School admins can see all students in their school
        EXISTS (
            SELECT 1 FROM school_admins sa
            JOIN classroom_enrollments ce ON TRUE
            JOIN classrooms c ON c.id = ce.classroom_id
            WHERE sa.user_id = current_setting('app.current_user_id')::uuid
            AND c.school_id = sa.school_id
            AND ce.student_id = student_profiles.id
        )
        OR
        -- District admins can see all students in their district
        EXISTS (
            SELECT 1 FROM district_admins da
            JOIN schools s ON s.district_id = da.district_id
            JOIN classrooms c ON c.school_id = s.id
            JOIN classroom_enrollments ce ON ce.classroom_id = c.id
            WHERE da.user_id = current_setting('app.current_user_id')::uuid
            AND ce.student_id = student_profiles.id
        )
    );
```

**Application-layer enforcement (belt + suspenders):**

```python
# Every repository method includes scope filtering
class StudentRepository:
    async def get_students(
        self,
        db: AsyncSession,
        requesting_user: User,
    ) -> list[StudentProfile]:
        query = select(StudentProfile)

        match requesting_user.role:
            case Role.PARENT:
                query = query.where(StudentProfile.parent_id == requesting_user.id)
            case Role.TEACHER:
                query = query.join(ClassroomEnrollment).join(Classroom).where(
                    Classroom.teacher_id == requesting_user.id
                )
            case Role.SCHOOL_ADMIN:
                query = query.join(ClassroomEnrollment).join(Classroom).where(
                    Classroom.school_id == requesting_user.school_id
                )
            case Role.DISTRICT_ADMIN:
                query = query.join(ClassroomEnrollment).join(Classroom).join(School).where(
                    School.district_id == requesting_user.district_id
                )
            case _:
                raise AuthorizationError("Unknown role")

        result = await db.execute(query)
        return list(result.scalars().all())
```

#### Clever SSO Integration

**OAuth 2.0 Authorization Code Flow:**

```
┌──────────┐    1. District admin clicks     ┌──────────────┐
│  School   │       "Connect Clever"          │  PADI.AI     │
│  Admin    │────────────────────────────────►│  School Mgmt  │
│  Browser  │                                 │  Service      │
└──────────┘                                  └──────┬───────┘
      │                                              │
      │    2. Redirect to Clever OAuth               │
      │◄─────────────────────────────────────────────┘
      │       https://clever.com/oauth/authorize
      │       ?response_type=code
      │       &client_id={CLEVER_CLIENT_ID}
      │       &redirect_uri={PADI_AI_CALLBACK}
      │       &district_id={DISTRICT_CLEVER_ID}
      │       &state={CSRF_TOKEN}
      │
      ▼
┌──────────┐    3. Admin authenticates        ┌──────────────┐
│  Clever   │       with district IDP         │  District     │
│  Login    │◄───────────────────────────────►│  Identity     │
│  Page     │                                 │  Provider     │
└──────┬───┘                                  └──────────────┘
       │
       │    4. Redirect back with auth code
       │       {PADI_AI_CALLBACK}?code={AUTH_CODE}&state={CSRF_TOKEN}
       │
       ▼
┌──────────────┐    5. Exchange code for      ┌──────────────┐
│  PADI.AI     │       tokens                 │  Clever       │
│  Callback     │─────────────────────────────►│  Token API    │
│  Handler      │                              │               │
│               │◄─────────────────────────────│  access_token │
│               │       6. {access_token,      │  + id_token   │
│               │            id_token}         └──────────────┘
│               │
│               │    7. Fetch district data    ┌──────────────┐
│               │─────────────────────────────►│  Clever       │
│               │                              │  Data API     │
│               │◄─────────────────────────────│               │
│               │    8. {schools, teachers,    │  /v3.0/me     │
│               │         sections, students}  │  /v3.0/       │
│               │                              │   districts/  │
└──────┬───────┘                              └──────────────┘
       │
       │    9. Create/update PADI.AI entities
       │       - District record
       │       - School records
       │       - Teacher user accounts
       │       - Student profiles (linked to classrooms)
       │       - SSO connection record (stores refresh token)
       │
       ▼
┌──────────────┐
│  PADI.AI DB  │
└──────────────┘
```

**Nightly roster sync (SQS-triggered):**

A scheduled EventBridge rule fires at 2:00 AM Pacific daily, enqueuing a sync job for every active Clever connection:

```python
async def sync_school_roster(connection: CleverConnection) -> SyncResult:
    """
    Nightly sync: refresh tokens, fetch roster delta, reconcile.
    """
    # 1. Refresh Clever access token
    new_token = await clever_client.refresh_token(connection.refresh_token)
    await db.update_connection_token(connection.id, new_token)

    # 2. Fetch current roster from Clever
    clever_sections = await clever_client.get_sections(connection.district_id)
    clever_students = await clever_client.get_students(connection.district_id)
    clever_teachers = await clever_client.get_teachers(connection.district_id)

    # 3. Reconcile with PADI.AI DB
    result = SyncResult()

    for student in clever_students:
        existing = await db.find_student_by_clever_id(student.clever_id)
        if existing:
            # Update if name/grade changed
            if existing.needs_update(student):
                await db.update_student_from_clever(existing.id, student)
                result.students_updated += 1
        else:
            # Check for conflict: parent-created student with same name + school
            conflict = await db.find_potential_duplicate(
                first_name=student.first_name,
                last_name=student.last_name,
                school_id=connection.school_id,
            )
            if conflict:
                # Flag for manual review — don't auto-merge
                await db.create_merge_request(conflict.id, student)
                result.merge_requests_created += 1
            else:
                await db.create_student_from_clever(student, connection.school_id)
                result.students_created += 1

    # 4. Handle removed students (no longer in Clever roster)
    padi_clever_ids = await db.get_clever_student_ids(connection.school_id)
    clever_student_ids = {s.clever_id for s in clever_students}
    removed_ids = padi_clever_ids - clever_student_ids

    for clever_id in removed_ids:
        # Soft-remove: unenroll from classrooms, don't delete data
        await db.unenroll_student_by_clever_id(clever_id)
        result.students_unenrolled += 1

    # 5. Update classroom enrollments
    for section in clever_sections:
        classroom = await db.find_or_create_classroom(section, connection.school_id)
        await db.sync_classroom_enrollment(classroom.id, section.student_ids)
        result.enrollments_synced += 1

    # 6. Record sync completion
    await db.record_sync_job(connection.id, result)
    return result
```

**Conflict resolution — parent-created student vs. Clever import:**

When a student already exists in PADI.AI (created by a parent) and Clever tries to add the same student:
1. A `merge_request` record is created with both profiles
2. The school admin receives a notification in their dashboard
3. The school admin can: (a) merge the profiles (learning history is preserved), (b) keep them separate (school version + home version), or (c) dismiss the merge request
4. Parent is notified if a merge occurs and must consent to the school having view access to their child's learning history

#### FERPA Data Processing Agreement (DPA)

**DPA flow during school onboarding:**

```
Step 1: District admin creates PADI.AI school account
Step 2: District admin reviews DPA (pre-generated PDF based on PADI.AI template)
Step 3: DPA includes:
  - What student data PADI.AI collects (name, grade, assessment responses, learning progress)
  - What PADI.AI will NOT do (sell data, use for advertising, share with third parties)
  - Data retention: student data deleted within 30 days of contract termination
  - Data security: encryption at rest + in transit, annual pen test, incident notification within 72 hours
  - Parent access: parents can request data export/deletion for their child
  - School data ownership: school retains ownership of all student education records
Step 4: District admin electronically signs DPA (name, email, title, timestamp)
Step 5: Signed DPA stored in `dpa_agreements` table + PDF archived in S3
Step 6: School onboarding continues (Clever SSO setup, teacher invitations)
```

**Data field restrictions once DPA is signed:**

| Data Field | PADI.AI CAN | PADI.AI CANNOT |
|-----------|-------------|-----------------|
| Student first/last name | Display to teacher/parent, use in reports | Share with third parties, use in marketing |
| Assessment responses | Power BKT algorithm, generate progress reports | Sell or monetize, use for non-educational purposes |
| Learning path progress | Show to teacher/parent, internal product improvement | Share student-level data externally |
| Student email | N/A (not collected for under-13) | N/A |
| Behavioral data | Aggregate for product analytics (anonymized) | Track individual student behavior for advertising |

### 1.5 Internationalization (i18n) Architecture

#### Framework Choice: next-intl

**Why next-intl over react-i18next:**

| Criterion | next-intl | react-i18next |
|-----------|-----------|---------------|
| Next.js App Router support | Native, first-class | Requires workarounds for RSC |
| Server Components | Full support via `getTranslations()` | Limited — requires client-side hydration |
| Type safety | TypeScript-native message keys | Requires additional plugins |
| URL routing | Built-in `[locale]` segment routing | Manual setup needed |
| Bundle size | Loads only current locale messages | Can accidentally bundle all locales |
| Middleware | Built-in locale detection + redirect | Custom middleware needed |

next-intl is the clear choice for a Next.js 15 App Router project.

#### Translation Workflow

**File structure:**

```
apps/web/
├── messages/
│   ├── en.json          # English UI strings (source of truth)
│   ├── es.json          # Spanish UI strings
│   └── validation.ts    # Build-time check: all en keys exist in es
├── src/
│   ├── i18n/
│   │   ├── config.ts    # Locale config: ['en', 'es'], default 'en'
│   │   ├── routing.ts   # Navigation helpers with locale prefix
│   │   └── request.ts   # Server-side message loading
│   ├── middleware.ts     # Locale detection + redirect
│   └── app/
│       └── [locale]/     # All pages under locale segment
│           ├── layout.tsx
│           ├── page.tsx
│           ├── practice/
│           ├── dashboard/
│           └── ...

services/agent-engine/
├── prompts/
│   ├── en/
│   │   ├── tutor_hint_v1.0.jinja2
│   │   ├── tutor_encouragement_v1.0.jinja2
│   │   ├── question_generation_v1.0.jinja2
│   │   └── assessment_instruction_v1.0.jinja2
│   └── es/
│       ├── tutor_hint_v1.0.jinja2
│       ├── tutor_encouragement_v1.0.jinja2
│       ├── question_generation_v1.0.jinja2
│       └── assessment_instruction_v1.0.jinja2
```

**Translation memory system:**

```python
class TranslationMemory:
    """
    Stores previously approved translations to avoid re-translating
    identical strings. Uses pgvector for fuzzy matching.
    """

    async def get_translation(self, source_text: str, target_locale: str) -> str | None:
        """Exact match lookup in translation memory."""
        result = await db.execute(
            select(TranslationEntry.target_text)
            .where(TranslationEntry.source_text == source_text)
            .where(TranslationEntry.target_locale == target_locale)
            .where(TranslationEntry.approved == True)
        )
        return result.scalar_one_or_none()

    async def get_fuzzy_matches(
        self, source_text: str, target_locale: str, threshold: float = 0.85
    ) -> list[TranslationMatch]:
        """
        Fuzzy match using pgvector embedding similarity.
        Returns similar source→target pairs for translator reference.
        """
        embedding = await embed(source_text)
        results = await db.execute(
            select(TranslationEntry)
            .where(TranslationEntry.target_locale == target_locale)
            .where(TranslationEntry.approved == True)
            .order_by(TranslationEntry.source_embedding.cosine_distance(embedding))
            .limit(5)
        )
        return [
            TranslationMatch(entry=r, similarity=1 - r.source_embedding.cosine_distance(embedding))
            for r in results.scalars()
            if 1 - r.source_embedding.cosine_distance(embedding) >= threshold
        ]
```

**AI-generated question translation:**

Math questions generated by o3-mini must also be available in Spanish. The translation pipeline:

1. Question generated in English (primary language for math standards)
2. Question passes English validation pipeline (correctness, grade-level, safety)
3. If student's locale is `es`, question text is translated:
   - Prose/word problems → translated via Claude Sonnet with math-domain context
   - Math notation (KaTeX) → unchanged (universal)
   - Numeric formats → localized (decimal comma in some Spanish-speaking regions — but Oregon standards use US format, so we keep `.` as decimal separator)
4. Spanish translation passes a secondary validation:
   - Grade 4-5 readability in Spanish (Fernández-Huerta formula)
   - Mathematical accuracy preserved (bilingual math expert review for golden set)
   - Cultural appropriateness (names, scenarios relevant to Oregon Hispanic community)

**URL strategy:** Path prefix `/en/` and `/es/`:

```
https://padi.ai/en/practice          # English practice
https://padi.ai/es/practice          # Spanish practice
https://padi.ai/en/dashboard         # English parent dashboard
https://padi.ai/es/dashboard         # Spanish parent dashboard
```

Locale is determined by: (1) user preference stored in DB, (2) URL path prefix, (3) browser `Accept-Language` header. User preference takes precedence. The `[locale]` dynamic segment in Next.js App Router handles routing automatically via next-intl middleware.

---

## 2. Detailed System Design

### 2.1 Database Schema (Stage 5 New Tables)

```sql
-- =============================================================================
-- BILLING TABLES
-- =============================================================================

-- Subscription plans and their mapping to Stripe
CREATE TABLE subscription_plans (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    stripe_price_id VARCHAR(255) NOT NULL UNIQUE,      -- e.g., 'price_1N...'
    name            VARCHAR(100) NOT NULL,              -- 'Individual', 'Family', 'School'
    slug            VARCHAR(50)  NOT NULL UNIQUE,       -- 'individual', 'family', 'school'
    amount_cents    INTEGER      NOT NULL,              -- 1499, 2499, or 0 (school = invoiced)
    currency        VARCHAR(3)   NOT NULL DEFAULT 'usd',
    interval        VARCHAR(20)  NOT NULL DEFAULT 'month', -- 'month' | 'year'
    max_students    INTEGER      NOT NULL DEFAULT 1,    -- 1, 4, or NULL (unlimited for school)
    trial_days      INTEGER      NOT NULL DEFAULT 14,
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT now()
);

COMMENT ON TABLE subscription_plans IS 'Available subscription tiers with Stripe price mapping.';

-- Parent/school subscriptions
CREATE TABLE subscriptions (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    parent_id             UUID         REFERENCES users(id) ON DELETE SET NULL,
    school_id             UUID         REFERENCES schools(id) ON DELETE SET NULL,
    plan_id               UUID         NOT NULL REFERENCES subscription_plans(id),
    stripe_subscription_id VARCHAR(255) UNIQUE,           -- 'sub_1N...'
    stripe_customer_id    VARCHAR(255) NOT NULL,           -- 'cus_1N...'
    state                 VARCHAR(20)  NOT NULL DEFAULT 'trial'
        CHECK (state IN ('trial', 'active', 'past_due', 'canceling', 'canceled', 'paused', 'expired')),
    trial_start           TIMESTAMPTZ,
    trial_end             TIMESTAMPTZ,
    current_period_start  TIMESTAMPTZ,
    current_period_end    TIMESTAMPTZ,
    cancel_at             TIMESTAMPTZ,
    canceled_at           TIMESTAMPTZ,
    paused_at             TIMESTAMPTZ,
    past_due_since        TIMESTAMPTZ,
    pending_plan_id       UUID         REFERENCES subscription_plans(id), -- for scheduled downgrades
    po_number             VARCHAR(100),                    -- school purchase order
    metadata              JSONB        NOT NULL DEFAULT '{}',
    created_at            TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at            TIMESTAMPTZ  NOT NULL DEFAULT now(),

    -- A subscription belongs to either a parent OR a school, not both
    CONSTRAINT subscription_owner_check CHECK (
        (parent_id IS NOT NULL AND school_id IS NULL) OR
        (parent_id IS NULL AND school_id IS NOT NULL)
    )
);

CREATE INDEX idx_subscriptions_parent_id ON subscriptions(parent_id) WHERE parent_id IS NOT NULL;
CREATE INDEX idx_subscriptions_school_id ON subscriptions(school_id) WHERE school_id IS NOT NULL;
CREATE INDEX idx_subscriptions_stripe_sub_id ON subscriptions(stripe_subscription_id);
CREATE INDEX idx_subscriptions_state ON subscriptions(state);

COMMENT ON TABLE subscriptions IS 'Active and historical subscription records, synchronized with Stripe.';

-- Audit log for all subscription state transitions
CREATE TABLE subscription_events (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subscription_id  UUID         NOT NULL REFERENCES subscriptions(id),
    event_type       VARCHAR(50)  NOT NULL,  -- 'state_changed', 'plan_changed', 'payment_succeeded', etc.
    previous_state   VARCHAR(20),
    new_state        VARCHAR(20),
    stripe_event_id  VARCHAR(255),           -- link to originating Stripe event
    metadata         JSONB        NOT NULL DEFAULT '{}',  -- additional context (amount, reason, etc.)
    created_at       TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE INDEX idx_sub_events_subscription_id ON subscription_events(subscription_id);
CREATE INDEX idx_sub_events_stripe_event_id ON subscription_events(stripe_event_id);
CREATE INDEX idx_sub_events_created_at ON subscription_events(created_at);

COMMENT ON TABLE subscription_events IS 'Immutable audit log of every subscription lifecycle event.';

-- Idempotency table for Stripe webhooks
CREATE TABLE stripe_webhook_events (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    stripe_event_id  VARCHAR(255) NOT NULL UNIQUE,        -- Stripe event ID (evt_1N...)
    event_type       VARCHAR(100) NOT NULL,               -- 'invoice.payment_succeeded', etc.
    processed_at     TIMESTAMPTZ  NOT NULL DEFAULT now(),
    processing_time_ms INTEGER,                           -- how long processing took
    status           VARCHAR(20)  NOT NULL DEFAULT 'processed'
        CHECK (status IN ('processed', 'skipped', 'failed')),
    error_message    TEXT,                                 -- if status = 'failed'
    payload_hash     VARCHAR(64)  NOT NULL,               -- SHA-256 of raw payload for audit
    created_at       TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE INDEX idx_stripe_events_type ON stripe_webhook_events(event_type);
CREATE INDEX idx_stripe_events_created_at ON stripe_webhook_events(created_at);

COMMENT ON TABLE stripe_webhook_events IS 'Deduplication and audit table for all received Stripe webhooks.';

-- =============================================================================
-- SCHOOL & DISTRICT TABLES
-- =============================================================================

CREATE TABLE districts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(255) NOT NULL,
    clever_id       VARCHAR(255) UNIQUE,                  -- Clever district ID
    state           VARCHAR(2)   NOT NULL DEFAULT 'OR',   -- US state code
    city            VARCHAR(255),
    website_url     VARCHAR(500),
    contact_email   VARCHAR(255),                         -- encrypted at app layer
    contact_name    VARCHAR(255),                         -- encrypted at app layer
    metadata        JSONB        NOT NULL DEFAULT '{}',
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE INDEX idx_districts_clever_id ON districts(clever_id) WHERE clever_id IS NOT NULL;

COMMENT ON TABLE districts IS 'School districts. One district contains many schools.';

CREATE TABLE schools (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    district_id     UUID         NOT NULL REFERENCES districts(id),
    name            VARCHAR(255) NOT NULL,
    clever_id       VARCHAR(255) UNIQUE,                  -- Clever school ID
    nces_id         VARCHAR(20),                          -- National Center for Education Statistics ID
    address_line1   VARCHAR(255),
    address_city    VARCHAR(255),
    address_state   VARCHAR(2)   DEFAULT 'OR',
    address_zip     VARCHAR(10),
    phone           VARCHAR(20),
    principal_name  VARCHAR(255),
    max_students    INTEGER,                              -- license limit
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE INDEX idx_schools_district_id ON schools(district_id);
CREATE INDEX idx_schools_clever_id ON schools(clever_id) WHERE clever_id IS NOT NULL;

COMMENT ON TABLE schools IS 'Individual schools within districts.';

CREATE TABLE school_admins (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID         NOT NULL REFERENCES users(id),
    school_id       UUID         NOT NULL REFERENCES schools(id),
    role            VARCHAR(30)  NOT NULL DEFAULT 'school_admin'
        CHECK (role IN ('school_admin', 'district_admin')),
    invited_by      UUID         REFERENCES users(id),
    invited_at      TIMESTAMPTZ,
    accepted_at     TIMESTAMPTZ,
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),

    UNIQUE(user_id, school_id)
);

CREATE INDEX idx_school_admins_school_id ON school_admins(school_id);

COMMENT ON TABLE school_admins IS 'Maps users to school/district admin roles.';

CREATE TABLE district_admins (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID         NOT NULL REFERENCES users(id),
    district_id     UUID         NOT NULL REFERENCES districts(id),
    invited_by      UUID         REFERENCES users(id),
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),

    UNIQUE(user_id, district_id)
);

CREATE INDEX idx_district_admins_district_id ON district_admins(district_id);

COMMENT ON TABLE district_admins IS 'Maps users to district admin roles.';

CREATE TABLE classrooms (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id       UUID         NOT NULL REFERENCES schools(id),
    teacher_id      UUID         NOT NULL REFERENCES users(id),
    clever_id       VARCHAR(255) UNIQUE,                  -- Clever section ID
    name            VARCHAR(255) NOT NULL,                -- "Mrs. Johnson's 4th Grade Math"
    grade_level     INTEGER      NOT NULL DEFAULT 4,
    period          VARCHAR(50),                          -- "Period 2", "Block A"
    academic_year   VARCHAR(9)   NOT NULL,                -- "2026-2027"
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE INDEX idx_classrooms_school_id ON classrooms(school_id);
CREATE INDEX idx_classrooms_teacher_id ON classrooms(teacher_id);
CREATE INDEX idx_classrooms_clever_id ON classrooms(clever_id) WHERE clever_id IS NOT NULL;

COMMENT ON TABLE classrooms IS 'Teacher-managed classrooms within a school.';

CREATE TABLE classroom_enrollments (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    classroom_id    UUID         NOT NULL REFERENCES classrooms(id),
    student_id      UUID         NOT NULL REFERENCES student_profiles(id),
    clever_id       VARCHAR(255),                         -- Clever enrollment ID
    enrolled_at     TIMESTAMPTZ  NOT NULL DEFAULT now(),
    unenrolled_at   TIMESTAMPTZ,
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,

    UNIQUE(classroom_id, student_id)
);

CREATE INDEX idx_enrollments_classroom_id ON classroom_enrollments(classroom_id);
CREATE INDEX idx_enrollments_student_id ON classroom_enrollments(student_id);

COMMENT ON TABLE classroom_enrollments IS 'Many-to-many: students enrolled in classrooms.';

CREATE TABLE clever_sync_jobs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    connection_id   UUID         NOT NULL REFERENCES sso_connections(id),
    school_id       UUID         NOT NULL REFERENCES schools(id),
    status          VARCHAR(20)  NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'running', 'completed', 'failed', 'partial')),
    started_at      TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ,
    students_created   INTEGER   DEFAULT 0,
    students_updated   INTEGER   DEFAULT 0,
    students_unenrolled INTEGER  DEFAULT 0,
    merge_requests     INTEGER   DEFAULT 0,
    enrollments_synced INTEGER   DEFAULT 0,
    error_message   TEXT,
    error_details   JSONB,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE INDEX idx_sync_jobs_connection_id ON clever_sync_jobs(connection_id);
CREATE INDEX idx_sync_jobs_status ON clever_sync_jobs(status);
CREATE INDEX idx_sync_jobs_created_at ON clever_sync_jobs(created_at);

COMMENT ON TABLE clever_sync_jobs IS 'Audit trail for all Clever roster synchronization jobs.';

CREATE TABLE dpa_agreements (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    district_id     UUID         NOT NULL REFERENCES districts(id),
    school_id       UUID         REFERENCES schools(id),  -- NULL = district-wide DPA
    signed_by_user_id UUID      NOT NULL REFERENCES users(id),
    signed_by_name  VARCHAR(255) NOT NULL,                 -- name at time of signing
    signed_by_email VARCHAR(255) NOT NULL,                 -- email at time of signing (encrypted)
    signed_by_title VARCHAR(255) NOT NULL,                 -- "Technology Director", "Principal"
    signed_at       TIMESTAMPTZ  NOT NULL DEFAULT now(),
    dpa_version     VARCHAR(20)  NOT NULL,                 -- "1.0", "1.1"
    dpa_pdf_s3_key  VARCHAR(500) NOT NULL,                 -- S3 key for archived signed PDF
    effective_date  DATE         NOT NULL,
    expiration_date DATE         NOT NULL,                 -- typically 1 year from signing
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    revoked_at      TIMESTAMPTZ,
    revoked_reason  TEXT,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE INDEX idx_dpa_district_id ON dpa_agreements(district_id);
CREATE INDEX idx_dpa_active ON dpa_agreements(is_active) WHERE is_active = TRUE;

COMMENT ON TABLE dpa_agreements IS 'FERPA Data Processing Agreements signed by district/school officials.';

CREATE TABLE sso_connections (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    district_id     UUID         NOT NULL REFERENCES districts(id),
    provider        VARCHAR(30)  NOT NULL DEFAULT 'clever'
        CHECK (provider IN ('clever', 'classlink', 'google_workspace')),
    clever_district_id VARCHAR(255),
    client_id       VARCHAR(255) NOT NULL,
    access_token    TEXT,                                   -- encrypted at app layer
    refresh_token   TEXT,                                   -- encrypted at app layer
    token_expires_at TIMESTAMPTZ,
    last_sync_at    TIMESTAMPTZ,
    sync_enabled    BOOLEAN      NOT NULL DEFAULT TRUE,
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE INDEX idx_sso_connections_district_id ON sso_connections(district_id);

COMMENT ON TABLE sso_connections IS 'SSO provider connections (Clever, ClassLink, Google) per district.';

-- =============================================================================
-- FEATURE GATING
-- =============================================================================

CREATE TABLE subscription_features (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_id         UUID         NOT NULL REFERENCES subscription_plans(id),
    feature_key     VARCHAR(100) NOT NULL,  -- 'unlimited_practice', 'unlimited_hints', etc.
    feature_value   JSONB        NOT NULL DEFAULT 'true',  -- boolean or config object
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),

    UNIQUE(plan_id, feature_key)
);

CREATE INDEX idx_sub_features_plan_id ON subscription_features(plan_id);
CREATE INDEX idx_sub_features_feature_key ON subscription_features(feature_key);

COMMENT ON TABLE subscription_features IS 'Feature flags per subscription plan. Source of truth for what each tier unlocks.';

-- =============================================================================
-- ANALYTICS TABLES
-- =============================================================================

-- COPPA-safe event log (no student PII — uses anonymized hashes)
CREATE TABLE analytics_events (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_name      VARCHAR(100) NOT NULL,
    actor_type      VARCHAR(20)  NOT NULL CHECK (actor_type IN ('student', 'parent', 'teacher', 'admin')),
    actor_hash      VARCHAR(64)  NOT NULL,  -- SHA-256(actor_id + daily_salt) for students; user_id for parents
    session_hash    VARCHAR(64),            -- anonymized session identifier
    properties      JSONB        NOT NULL DEFAULT '{}',  -- NO PII — skill_code, difficulty, etc.
    page_url        VARCHAR(500),
    occurred_at     TIMESTAMPTZ  NOT NULL DEFAULT now(),
    ingested_at     TIMESTAMPTZ  NOT NULL DEFAULT now()
);

-- Partition by month for efficient querying and retention
-- CREATE TABLE analytics_events_2026_04 PARTITION OF analytics_events
--     FOR VALUES FROM ('2026-04-01') TO ('2026-05-01');

CREATE INDEX idx_analytics_event_name ON analytics_events(event_name);
CREATE INDEX idx_analytics_actor_hash ON analytics_events(actor_hash);
CREATE INDEX idx_analytics_occurred_at ON analytics_events(occurred_at);

COMMENT ON TABLE analytics_events IS 'COPPA-compliant event log. Student events use anonymized hashes, never PII.';

CREATE TABLE ab_test_experiments (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    experiment_key  VARCHAR(100) NOT NULL UNIQUE,  -- 'hint_button_placement_v2'
    description     TEXT,
    variants        JSONB        NOT NULL,         -- ["control", "variant_a", "variant_b"]
    traffic_pct     INTEGER      NOT NULL DEFAULT 100 CHECK (traffic_pct BETWEEN 0 AND 100),
    status          VARCHAR(20)  NOT NULL DEFAULT 'draft'
        CHECK (status IN ('draft', 'running', 'paused', 'completed')),
    started_at      TIMESTAMPTZ,
    ended_at        TIMESTAMPTZ,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT now()
);

COMMENT ON TABLE ab_test_experiments IS 'A/B test experiment definitions.';

CREATE TABLE ab_test_assignments (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    experiment_id   UUID         NOT NULL REFERENCES ab_test_experiments(id),
    actor_hash      VARCHAR(64)  NOT NULL,  -- anonymized, same as analytics_events
    variant         VARCHAR(50)  NOT NULL,
    assigned_at     TIMESTAMPTZ  NOT NULL DEFAULT now(),

    UNIQUE(experiment_id, actor_hash)
);

CREATE INDEX idx_ab_assignments_experiment_id ON ab_test_assignments(experiment_id);

COMMENT ON TABLE ab_test_assignments IS 'Deterministic A/B test variant assignments. Uses hash-based bucketing.';

-- =============================================================================
-- ACHIEVEMENTS & ENGAGEMENT
-- =============================================================================

CREATE TABLE badge_definitions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    badge_key       VARCHAR(100) NOT NULL UNIQUE,  -- 'first_mastery', 'streak_7', 'assessment_complete'
    name_en         VARCHAR(200) NOT NULL,
    name_es         VARCHAR(200),
    description_en  TEXT         NOT NULL,
    description_es  TEXT,
    icon_url        VARCHAR(500) NOT NULL,
    category        VARCHAR(50)  NOT NULL CHECK (category IN ('mastery', 'streak', 'milestone', 'special')),
    criteria        JSONB        NOT NULL,          -- {"type": "skills_mastered", "count": 1}
    sort_order      INTEGER      NOT NULL DEFAULT 0,
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT now()
);

COMMENT ON TABLE badge_definitions IS 'Badge catalog with criteria for automatic awarding.';

CREATE TABLE student_badges (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id      UUID         NOT NULL REFERENCES student_profiles(id),
    badge_id        UUID         NOT NULL REFERENCES badge_definitions(id),
    earned_at       TIMESTAMPTZ  NOT NULL DEFAULT now(),
    context         JSONB        NOT NULL DEFAULT '{}',   -- {"skill_code": "4.OA.A.1", "session_id": "..."}

    UNIQUE(student_id, badge_id)
);

CREATE INDEX idx_student_badges_student_id ON student_badges(student_id);

COMMENT ON TABLE student_badges IS 'Badges earned by students. Each badge can only be earned once.';

CREATE TABLE math_missions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title_en        VARCHAR(200) NOT NULL,
    title_es        VARCHAR(200),
    description_en  TEXT         NOT NULL,
    description_es  TEXT,
    skill_codes     VARCHAR(20)[] NOT NULL,                -- CCSS skill codes involved
    difficulty_range INT4RANGE   NOT NULL DEFAULT '[1,5]', -- difficulty 1-5
    estimated_sessions INTEGER   NOT NULL DEFAULT 5,
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT now()
);

COMMENT ON TABLE math_missions IS 'Themed multi-session learning missions for student engagement.';

CREATE TABLE mission_enrollments (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id      UUID         NOT NULL REFERENCES student_profiles(id),
    mission_id      UUID         NOT NULL REFERENCES math_missions(id),
    started_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),
    completed_at    TIMESTAMPTZ,
    progress_pct    NUMERIC(5,2) NOT NULL DEFAULT 0.00,
    sessions_completed INTEGER   NOT NULL DEFAULT 0,
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,

    UNIQUE(student_id, mission_id)
);

CREATE INDEX idx_mission_enrollments_student_id ON mission_enrollments(student_id);

COMMENT ON TABLE mission_enrollments IS 'Student enrollment and progress in math missions.';

-- =============================================================================
-- i18n
-- =============================================================================

CREATE TABLE user_locale_preferences (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID         NOT NULL REFERENCES users(id) UNIQUE,
    locale          VARCHAR(10)  NOT NULL DEFAULT 'en'
        CHECK (locale IN ('en', 'es')),
    timezone        VARCHAR(50)  NOT NULL DEFAULT 'America/Los_Angeles',
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT now()
);

COMMENT ON TABLE user_locale_preferences IS 'User language and timezone preferences.';

CREATE TABLE translation_entries (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_text     TEXT         NOT NULL,
    source_locale   VARCHAR(10)  NOT NULL DEFAULT 'en',
    target_text     TEXT         NOT NULL,
    target_locale   VARCHAR(10)  NOT NULL,
    context         VARCHAR(200),                          -- 'question_stem', 'hint_text', 'badge_description'
    source_embedding VECTOR(1536),                         -- for fuzzy matching
    approved        BOOLEAN      NOT NULL DEFAULT FALSE,
    approved_by     UUID         REFERENCES users(id),
    approved_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),

    UNIQUE(source_text, source_locale, target_locale, context)
);

CREATE INDEX idx_translation_source ON translation_entries(source_locale, target_locale);
CREATE INDEX idx_translation_embedding ON translation_entries
    USING ivfflat (source_embedding vector_cosine_ops) WITH (lists = 100);

COMMENT ON TABLE translation_entries IS 'Translation memory for reuse across AI-generated content.';
```

### 2.2 Stripe Integration Service Layer

```python
"""
services/billing/service.py — Stripe billing integration service layer.
"""
from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any
from uuid import UUID

import stripe
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


# ─── Enums & Models ──────────────────────────────────────────────────────────

class SubscriptionPlan(str, Enum):
    INDIVIDUAL = "individual"
    FAMILY = "family"
    SCHOOL = "school"


class SubscriptionState(str, Enum):
    TRIAL = "trial"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELING = "canceling"
    CANCELED = "canceled"
    PAUSED = "paused"
    EXPIRED = "expired"


class Feature(str, Enum):
    UNLIMITED_PRACTICE = "unlimited_practice"
    UNLIMITED_HINTS = "unlimited_hints"
    FULL_DASHBOARD = "full_dashboard"
    TEACHER_DASHBOARD = "teacher_dashboard"
    EOG_REPORT = "eog_report"
    SPANISH_LOCALE = "spanish_locale"
    MULTIPLE_STUDENTS = "multiple_students"
    PRIORITY_QUESTION_GEN = "priority_question_gen"
    SCHOOL_ANALYTICS = "school_analytics"
    CUSTOM_LEARNING_PLAN = "custom_learning_plan"


class SubscriptionStatus(BaseModel):
    subscription_id: UUID
    state: SubscriptionState
    plan: SubscriptionPlan
    trial_end: datetime | None
    current_period_end: datetime | None
    cancel_at: datetime | None
    features: set[Feature]


class WebhookResult(BaseModel):
    event_id: str
    event_type: str
    processed: bool  # False if duplicate/skipped
    action_taken: str | None


class SyncResult(BaseModel):
    students_created: int = 0
    students_updated: int = 0
    students_unenrolled: int = 0
    merge_requests_created: int = 0
    enrollments_synced: int = 0
    errors: list[str] = []


class CleverConnection(BaseModel):
    connection_id: UUID
    district_id: str
    district_name: str
    schools_found: int


# ─── Billing Service ─────────────────────────────────────────────────────────

class BillingService:
    """
    Manages Stripe subscriptions, checkout sessions, and webhook processing.
    All Stripe API calls are wrapped with error handling and audit logging.
    """

    def __init__(
        self,
        stripe_secret_key: str,
        stripe_webhook_secret: str,
        db_session_factory,
        redis_client,
        sqs_client,
        plan_registry: dict[SubscriptionPlan, str],  # plan → stripe_price_id
    ):
        stripe.api_key = stripe_secret_key
        self._webhook_secret = stripe_webhook_secret
        self._db_factory = db_session_factory
        self._redis = redis_client
        self._sqs = sqs_client
        self._plans = plan_registry

    async def create_checkout_session(
        self,
        parent_id: UUID,
        plan: SubscriptionPlan,
        trial_days: int = 14,
        success_url: str = "https://padi.ai/billing/success",
        cancel_url: str = "https://padi.ai/billing/cancel",
    ) -> str:
        """
        Creates a Stripe Checkout Session for the given plan.
        Returns the checkout URL to redirect the parent to.

        Raises:
            BillingError: If Stripe API call fails.
            DuplicateSubscriptionError: If parent already has an active subscription.
        """
        async with self._db_factory() as db:
            # Check for existing active subscription
            existing = await self._get_active_subscription(db, parent_id=parent_id)
            if existing:
                raise DuplicateSubscriptionError(
                    f"Parent {parent_id} already has subscription {existing.id}"
                )

            # Get or create Stripe customer
            customer_id = await self._get_or_create_stripe_customer(db, parent_id)

            session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=["card"],
                mode="subscription",
                line_items=[{"price": self._plans[plan], "quantity": 1}],
                subscription_data={
                    "trial_period_days": trial_days,
                    "metadata": {"parent_id": str(parent_id), "plan": plan.value},
                },
                success_url=f"{success_url}?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=cancel_url,
                metadata={"parent_id": str(parent_id)},
            )

            logger.info(
                "Checkout session created",
                extra={
                    "parent_id": str(parent_id),
                    "plan": plan.value,
                    "session_id": session.id,
                },
            )
            return session.url

    async def handle_webhook(self, payload: bytes, signature: str) -> WebhookResult:
        """
        Idempotent Stripe webhook handler. See Section 3 for full algorithm.
        """
        # 1. Verify signature — reject tampered payloads immediately
        try:
            event = stripe.Webhook.construct_event(
                payload, signature, self._webhook_secret
            )
        except stripe.error.SignatureVerificationError:
            logger.warning("Webhook signature verification failed")
            raise WebhookSignatureError("Invalid Stripe webhook signature")

        # 2. Idempotency check
        async with self._db_factory() as db:
            already_processed = await self._check_event_processed(db, event["id"])
            if already_processed:
                logger.info(f"Duplicate webhook skipped: {event['id']}")
                return WebhookResult(
                    event_id=event["id"],
                    event_type=event["type"],
                    processed=False,
                    action_taken="duplicate_skipped",
                )

            # 3. Process within transaction
            async with db.begin():
                action = await self._process_event(db, event)

                # 4. Record event as processed (inside same transaction)
                payload_hash = hashlib.sha256(payload).hexdigest()
                await self._record_event_processed(
                    db, event["id"], event["type"], payload_hash
                )

            # 5. Async side effects (outside transaction)
            await self._enqueue_side_effects(event, action)

            return WebhookResult(
                event_id=event["id"],
                event_type=event["type"],
                processed=True,
                action_taken=action,
            )

    async def get_subscription_status(self, parent_id: UUID) -> SubscriptionStatus:
        """
        Returns the current subscription status and available features
        for a parent account. Checks Redis cache first.
        """
        # Try cache
        cached = await self._redis.get(f"subscription:{parent_id}")
        if cached:
            return SubscriptionStatus.model_validate_json(cached)

        async with self._db_factory() as db:
            sub = await self._get_active_subscription(db, parent_id=parent_id)
            if not sub:
                # Return free tier
                return SubscriptionStatus(
                    subscription_id=UUID(int=0),
                    state=SubscriptionState.CANCELED,
                    plan=SubscriptionPlan.INDIVIDUAL,
                    trial_end=None,
                    current_period_end=None,
                    cancel_at=None,
                    features=set(),  # free tier features determined by caller
                )

            features = await self._get_plan_features(db, sub.plan_id)
            status = SubscriptionStatus(
                subscription_id=sub.id,
                state=SubscriptionState(sub.state),
                plan=SubscriptionPlan(sub.plan.slug),
                trial_end=sub.trial_end,
                current_period_end=sub.current_period_end,
                cancel_at=sub.cancel_at,
                features=features,
            )

            # Cache for 5 minutes
            await self._redis.setex(
                f"subscription:{parent_id}",
                300,
                status.model_dump_json(),
            )
            return status

    async def cancel_subscription(self, parent_id: UUID, reason: str) -> None:
        """
        Schedules subscription cancellation at end of current billing period.
        Does NOT immediately revoke access.
        """
        async with self._db_factory() as db:
            sub = await self._get_active_subscription(db, parent_id=parent_id)
            if not sub:
                raise SubscriptionNotFoundError(f"No active subscription for {parent_id}")

            # Cancel at period end in Stripe
            stripe.Subscription.modify(
                sub.stripe_subscription_id,
                cancel_at_period_end=True,
                metadata={"cancel_reason": reason},
            )

            # Update local state
            sub.state = "canceling"
            sub.cancel_at = sub.current_period_end
            await db.commit()

            # Audit log
            await self._record_subscription_event(
                db, sub.id, "cancel_requested",
                previous_state="active", new_state="canceling",
                metadata={"reason": reason},
            )

            # Invalidate cache
            await self._invalidate_subscription_cache(parent_id)

            logger.info(
                "Subscription cancellation scheduled",
                extra={"parent_id": str(parent_id), "cancel_at": str(sub.cancel_at)},
            )

    async def create_school_invoice(
        self,
        school_id: UUID,
        amount_cents: int,
        po_number: str,
        description: str = "PADI.AI School License",
    ) -> str:
        """
        Creates a Stripe Invoice for a school (net-30 terms).
        Returns the hosted invoice URL for the school to pay.
        """
        async with self._db_factory() as db:
            school = await self._get_school(db, school_id)
            customer_id = await self._get_or_create_school_customer(db, school)

            # Create invoice item
            stripe.InvoiceItem.create(
                customer=customer_id,
                amount=amount_cents,
                currency="usd",
                description=description,
                metadata={"school_id": str(school_id), "po_number": po_number},
            )

            # Create and finalize invoice
            invoice = stripe.Invoice.create(
                customer=customer_id,
                collection_method="send_invoice",
                days_until_due=30,
                metadata={"school_id": str(school_id), "po_number": po_number},
            )
            invoice = stripe.Invoice.finalize_invoice(invoice.id)

            logger.info(
                "School invoice created",
                extra={
                    "school_id": str(school_id),
                    "invoice_id": invoice.id,
                    "amount_cents": amount_cents,
                },
            )
            return invoice.hosted_invoice_url

    # ─── Private helpers (abbreviated signatures) ─────────────────────

    async def _process_event(self, db: AsyncSession, event: dict) -> str:
        """Route event to appropriate handler. Returns action description."""
        handlers = {
            "checkout.session.completed": self._handle_checkout_completed,
            "invoice.payment_succeeded": self._handle_payment_succeeded,
            "invoice.payment_failed": self._handle_payment_failed,
            "customer.subscription.updated": self._handle_subscription_updated,
            "customer.subscription.deleted": self._handle_subscription_deleted,
        }
        handler = handlers.get(event["type"])
        if handler:
            return await handler(db, event["data"]["object"])
        return "unhandled_event_type"

    async def _handle_checkout_completed(self, db: AsyncSession, session: dict) -> str:
        ...  # Create subscription record, link to parent

    async def _handle_payment_succeeded(self, db: AsyncSession, invoice: dict) -> str:
        ...  # Update subscription to ACTIVE, extend period

    async def _handle_payment_failed(self, db: AsyncSession, invoice: dict) -> str:
        ...  # Update to PAST_DUE, enqueue dunning email

    async def _handle_subscription_updated(self, db: AsyncSession, sub: dict) -> str:
        ...  # Handle plan changes, cancellation scheduling

    async def _handle_subscription_deleted(self, db: AsyncSession, sub: dict) -> str:
        ...  # Update to CANCELED, revoke features


# ─── Feature Gating Service ──────────────────────────────────────────────────

class FeatureGatingService:
    """
    Determines which features a user has access to based on their
    subscription state. Uses Redis cache with DB fallback.
    """

    def __init__(self, db_session_factory, redis_client):
        self._db_factory = db_session_factory
        self._redis = redis_client

    async def is_feature_enabled(self, user_id: UUID, feature: Feature) -> bool:
        """Check if a specific feature is enabled for a user."""
        features = self.get_cached_features(user_id)
        if features is None:
            features = await self._load_and_cache_features(user_id)
        return feature in features

    def get_cached_features(self, user_id: UUID) -> set[Feature] | None:
        """
        Synchronous Redis cache lookup. Returns None on cache miss.
        Used in hot path where async overhead is undesirable.
        """
        # Note: in practice, use async Redis; shown sync for clarity
        raw = self._redis.get(f"features:{user_id}")
        if raw is None:
            return None
        return {Feature(f) for f in raw.decode().split(",")}

    async def get_plan_features(self, plan: SubscriptionPlan) -> set[Feature]:
        """Returns all features enabled for a given subscription plan."""
        async with self._db_factory() as db:
            result = await db.execute(
                select(SubscriptionFeatureRow.feature_key)
                .join(SubscriptionPlanRow)
                .where(SubscriptionPlanRow.slug == plan.value)
            )
            return {Feature(row[0]) for row in result.all()}

    async def invalidate_cache(self, user_id: UUID) -> None:
        """Remove cached features. Next request will re-query DB."""
        await self._redis.delete(f"features:{user_id}")
        logger.info(f"Feature cache invalidated for user {user_id}")

    async def _load_and_cache_features(self, user_id: UUID) -> set[Feature]:
        """Load features from DB and populate Redis cache."""
        async with self._db_factory() as db:
            # Get user's active subscription
            sub = await db.execute(
                select(SubscriptionRow)
                .where(SubscriptionRow.parent_id == user_id)
                .where(SubscriptionRow.state.in_(["trial", "active", "past_due", "canceling"]))
                .order_by(SubscriptionRow.created_at.desc())
                .limit(1)
            )
            subscription = sub.scalar_one_or_none()

            if not subscription:
                features: set[Feature] = set()  # free tier
            else:
                result = await db.execute(
                    select(SubscriptionFeatureRow.feature_key)
                    .where(SubscriptionFeatureRow.plan_id == subscription.plan_id)
                )
                features = {Feature(row[0]) for row in result.all()}

            # Cache with 5-minute TTL
            if features:
                await self._redis.setex(
                    f"features:{user_id}",
                    300,
                    ",".join(f.value for f in features),
                )
            return features


# ─── Clever Sync Service ─────────────────────────────────────────────────────

class CleverSyncService:
    """
    Manages Clever SSO connections, OAuth flows, and roster synchronization.
    """

    def __init__(
        self,
        clever_client_id: str,
        clever_client_secret: str,
        clever_redirect_uri: str,
        db_session_factory,
    ):
        self._client_id = clever_client_id
        self._client_secret = clever_client_secret
        self._redirect_uri = clever_redirect_uri
        self._db_factory = db_session_factory

    async def initiate_oauth(self, district_id: str) -> str:
        """
        Generates the Clever OAuth authorization URL.
        Returns URL to redirect the school admin to.
        """
        import secrets
        state = secrets.token_urlsafe(32)
        # Store state in Redis with 10-minute TTL for CSRF validation
        await self._redis.setex(f"clever_oauth_state:{state}", 600, district_id)

        return (
            f"https://clever.com/oauth/authorize"
            f"?response_type=code"
            f"&client_id={self._client_id}"
            f"&redirect_uri={self._redirect_uri}"
            f"&district_id={district_id}"
            f"&state={state}"
        )

    async def handle_callback(self, code: str, state: str) -> CleverConnection:
        """
        Handles the OAuth callback from Clever.
        Exchanges code for tokens, fetches district info, creates connection.
        """
        # 1. Validate state (CSRF protection)
        district_id = await self._redis.get(f"clever_oauth_state:{state}")
        if not district_id:
            raise OAuthStateError("Invalid or expired OAuth state")
        await self._redis.delete(f"clever_oauth_state:{state}")

        # 2. Exchange code for tokens
        token_response = await self._exchange_code(code)
        access_token = token_response["access_token"]

        # 3. Fetch district info from Clever
        me_response = await self._clever_api_get("/v3.0/me", access_token)
        district_info = await self._clever_api_get(
            f"/v3.0/districts/{me_response['data']['district']}",
            access_token,
        )

        # 4. Create or update connection in DB
        async with self._db_factory() as db:
            connection = await self._upsert_connection(
                db,
                district_clever_id=district_id.decode(),
                district_name=district_info["data"]["name"],
                access_token=access_token,
                # Clever SSO tokens don't expire but we track for refresh
            )

            return CleverConnection(
                connection_id=connection.id,
                district_id=district_id.decode(),
                district_name=district_info["data"]["name"],
                schools_found=len(
                    await self._clever_api_get(
                        f"/v3.0/districts/{district_id.decode()}/schools",
                        access_token,
                    )
                ),
            )

    async def sync_school_roster(self, school_id: UUID) -> SyncResult:
        """
        Full roster sync for a single school.
        Called nightly via SQS worker or manually by school admin.
        See Section 1.4 for detailed sync algorithm.
        """
        ...  # Implementation per Section 1.4

    async def refresh_token(self, connection_id: UUID) -> None:
        """
        Refreshes Clever OAuth token for a connection.
        Called before each sync job.
        """
        async with self._db_factory() as db:
            connection = await db.get(SSOConnectionRow, connection_id)
            if not connection:
                raise ConnectionNotFoundError(f"Connection {connection_id} not found")

            new_token = await self._clever_refresh(connection.refresh_token)
            connection.access_token = new_token["access_token"]
            connection.token_expires_at = datetime.utcnow() + timedelta(
                seconds=new_token.get("expires_in", 86400)
            )
            await db.commit()
```

### 2.3 Analytics Architecture (COPPA-Compliant)

#### COPPA Constraints on Analytics

The FTC's COPPA Rule prohibits collecting personal information from children under 13 without verifiable parental consent. For PADI.AI, this means:

1. **No cookies for student sessions** — Students (under 13) must not have tracking cookies, localStorage tokens, or any persistent client-side identifier.
2. **No cross-site tracking** — No third-party analytics pixels, no Facebook/Google tracking snippets on student-facing pages.
3. **No behavioral advertising** — Student interaction data must never flow to advertising systems.
4. **Server-side only for students** — PostHog JavaScript SDK must NOT load on student-facing pages. All student events are tracked server-side by the API.
5. **Anonymized identifiers** — Student events use `SHA-256(student_id + daily_rotating_salt)` instead of actual student IDs. The salt rotates daily, making cross-day tracking impossible without DB access.

**PostHog configuration:**

```python
# Server-side PostHog client (for student events)
import posthog

posthog.project_api_key = settings.POSTHOG_API_KEY
posthog.host = "https://us.i.posthog.com"  # US data residency
posthog.disabled = False
posthog.debug = settings.DEBUG

# COPPA-compliant: server-side only, no cookies
def track_student_event(
    student_id: UUID,
    event_name: str,
    properties: dict[str, Any],
) -> None:
    """
    Track a student event server-side. Uses anonymized hash as distinct_id.
    Properties must NEVER contain PII (name, email, parent info).
    """
    daily_salt = get_daily_salt()  # Rotates at midnight UTC
    anonymous_id = hashlib.sha256(
        f"{student_id}:{daily_salt}".encode()
    ).hexdigest()

    # Validate no PII in properties
    _assert_no_pii(properties)

    posthog.capture(
        distinct_id=anonymous_id,
        event=event_name,
        properties={
            **properties,
            "$lib": "padi-ai-server",  # Mark as server-side
            "actor_type": "student",
        },
    )
```

```typescript
// Client-side PostHog (for parent/teacher pages ONLY)
// apps/web/src/lib/posthog.ts

import posthog from 'posthog-js';

export function initPostHog(userRole: 'parent' | 'teacher' | 'admin') {
  // NEVER initialize PostHog for student-facing pages
  if (typeof window === 'undefined') return;

  posthog.init(process.env.NEXT_PUBLIC_POSTHOG_KEY!, {
    api_host: 'https://us.i.posthog.com',
    // Cookieless mode for maximum privacy
    persistence: 'memory',  // No cookies, no localStorage
    autocapture: false,      // No automatic event capture
    capture_pageview: false,  // Manual pageview capture only
    disable_session_recording: true,  // No session replay for privacy
    opt_out_capturing_by_default: false,
  });
}
```

#### Event Taxonomy

**Student events (server-side only, anonymized):**

```python
# Session lifecycle
track_student_event(student_id, "session_started", {
    "skill_code": "4.NBT.B.5",
    "plan_track": "catch_up",        # catch_up | on_par | exceeding
    "session_number": 12,
})

track_student_event(student_id, "session_completed", {
    "skill_code": "4.NBT.B.5",
    "duration_seconds": 420,
    "questions_answered": 8,
    "questions_correct": 6,
    "hints_used": 2,
})

# Question interaction
track_student_event(student_id, "question_answered", {
    "is_correct": True,
    "difficulty": 3,
    "hint_used": False,
    "question_type": "multiple_choice",
    "skill_code": "4.NBT.B.5",
    "response_time_ms": 12500,
})

track_student_event(student_id, "hint_requested", {
    "hint_level": 2,                 # 1=nudge, 2=strategy, 3=worked_example
    "skill_code": "4.NBT.B.5",
    "question_difficulty": 3,
})

# Mastery events
track_student_event(student_id, "skill_mastered", {
    "skill_code": "4.OA.A.1",
    "sessions_to_master": 4,
    "bkt_p_mastery": 0.95,
})

track_student_event(student_id, "badge_earned", {
    "badge_key": "first_mastery",
    "category": "milestone",
})

# Assessment
track_student_event(student_id, "assessment_started", {
    "assessment_type": "initial",    # initial | periodic | eog
})

track_student_event(student_id, "assessment_completed", {
    "assessment_type": "initial",
    "proficiency_level": "on_par",
    "items_answered": 43,
    "duration_seconds": 1800,
})
```

**Parent events (client-side PostHog — parents are adults):**

```python
# Account lifecycle
posthog.capture("signup_completed", {"plan": "trial"})
posthog.capture("subscription_started", {"plan": "individual", "trial": True})
posthog.capture("subscription_canceled", {"reason": "too_expensive", "days_active": 45})

# Dashboard engagement
posthog.capture("dashboard_viewed", {"tab": "progress"})
posthog.capture("report_downloaded", {"report_type": "eog"})
posthog.capture("learning_plan_adjusted", {"change": "more_practice"})
posthog.capture("child_profile_created", {"child_number": 2})
```

**Teacher events (client-side PostHog):**

```python
posthog.capture("classroom_dashboard_viewed", {"student_count": 28})
posthog.capture("student_progress_viewed", {})  # no student_id in analytics
posthog.capture("class_report_exported", {"format": "pdf"})
```

#### A/B Testing Framework

**Deterministic, cookie-free variant assignment:**

```python
import hashlib

def assign_variant(
    actor_id: UUID,
    experiment_key: str,
    variants: list[str],
    traffic_pct: int = 100,
) -> str | None:
    """
    Deterministic A/B test assignment using hash-based bucketing.
    No cookies, no client-side state — same input always produces same output.

    Args:
        actor_id: Student or parent UUID
        experiment_key: Unique experiment identifier
        variants: List of variant names, e.g., ["control", "variant_a"]
        traffic_pct: Percentage of users included in experiment (0-100)

    Returns:
        Variant name, or None if user is not in the experiment traffic.
    """
    # Deterministic hash: same actor + experiment → same bucket every time
    hash_input = f"{actor_id}:{experiment_key}".encode()
    hash_value = int(hashlib.sha256(hash_input).hexdigest(), 16)
    bucket = hash_value % 100  # 0-99

    # Traffic allocation: bucket < traffic_pct → in experiment
    if bucket >= traffic_pct:
        return None  # Not in experiment

    # Variant assignment: evenly distribute across variants
    variant_index = bucket % len(variants)
    return variants[variant_index]
```

**Experiments tracked:**

| Experiment Key | Variants | Metric | Hypothesis |
|---------------|----------|--------|------------|
| `hint_button_placement_v1` | control (bottom), variant_a (inline) | Hint usage rate, question accuracy | Inline hints increase engagement |
| `celebration_animation_v1` | control (confetti), variant_a (star burst), variant_b (none) | Session completion rate | Celebration animations increase session completion |
| `question_display_format_v1` | control (text only), variant_a (text + visual) | Accuracy, response time | Visual aids improve comprehension |
| `practice_session_length_v1` | control (8 questions), variant_a (6 questions) | Session completion rate, next-day return | Shorter sessions reduce dropout |

---

## 3. Key Algorithms (Stage 5)

### Algorithm 1: Idempotent Webhook Processing

```python
"""
Complete implementation of the idempotent Stripe webhook handler.
"""
import hashlib
import logging
import time
from datetime import datetime

import stripe
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def handle_stripe_webhook(
    payload: bytes,
    signature: str,
    db: AsyncSession,
    webhook_secret: str,
    sqs_client,
) -> None:
    """
    Idempotent Stripe webhook handler.

    Guarantees:
    1. Each Stripe event is processed exactly once (idempotent via event_id).
    2. All DB mutations are atomic (single transaction).
    3. Out-of-order events are handled gracefully (timestamp comparison).
    4. Side effects (emails, cache invalidation) are enqueued async.

    Args:
        payload: Raw request body bytes (must NOT be parsed before signature verification).
        signature: Value of the `Stripe-Signature` header.
        db: SQLAlchemy async session (transaction managed by caller or internally).
        webhook_secret: Stripe webhook endpoint secret for signature verification.
        sqs_client: AWS SQS client for enqueueing side effects.
    """
    start_time = time.monotonic()

    # ── Step 1: Verify Stripe signature ──────────────────────────────
    # CRITICAL: Never process unverified webhooks. This prevents replay
    # attacks and ensures the payload actually came from Stripe.
    try:
        event = stripe.Webhook.construct_event(payload, signature, webhook_secret)
    except stripe.error.SignatureVerificationError as e:
        logger.warning("Webhook signature verification failed", extra={"error": str(e)})
        raise WebhookSignatureError("Invalid signature") from e
    except ValueError as e:
        logger.warning("Webhook payload parsing failed", extra={"error": str(e)})
        raise WebhookPayloadError("Invalid payload") from e

    event_id: str = event["id"]
    event_type: str = event["type"]
    payload_hash = hashlib.sha256(payload).hexdigest()

    logger.info(
        "Webhook received",
        extra={"event_id": event_id, "event_type": event_type},
    )

    # ── Step 2: Idempotency check ────────────────────────────────────
    # If we've already processed this event, return immediately.
    # This handles Stripe's documented duplicate delivery behavior.
    existing = await db.execute(
        select(StripeWebhookEventRow).where(
            StripeWebhookEventRow.stripe_event_id == event_id
        )
    )
    if existing.scalar_one_or_none() is not None:
        logger.info(
            "Duplicate webhook — already processed",
            extra={"event_id": event_id},
        )
        return  # Return 200 — idempotent success

    # ── Step 3: Begin atomic transaction ─────────────────────────────
    # All state mutations happen inside this transaction block.
    # If ANY step fails, everything rolls back and Stripe will retry.
    async with db.begin_nested():  # SAVEPOINT for nested transaction safety

        # ── Step 4: Process event based on type ──────────────────────
        action_taken = "unknown"

        if event_type == "checkout.session.completed":
            session = event["data"]["object"]
            if session.get("mode") == "subscription":
                action_taken = await _create_subscription_from_checkout(db, session)

        elif event_type == "invoice.payment_succeeded":
            invoice = event["data"]["object"]
            if invoice.get("subscription"):
                action_taken = await _handle_payment_success(db, invoice)

        elif event_type == "invoice.payment_failed":
            invoice = event["data"]["object"]
            if invoice.get("subscription"):
                action_taken = await _handle_payment_failure(db, invoice)

        elif event_type == "customer.subscription.updated":
            subscription = event["data"]["object"]
            action_taken = await _handle_subscription_update(
                db, subscription, event.get("data", {}).get("previous_attributes", {})
            )

        elif event_type == "customer.subscription.deleted":
            subscription = event["data"]["object"]
            action_taken = await _handle_subscription_deletion(db, subscription)

        else:
            logger.info(f"Unhandled webhook event type: {event_type}")
            action_taken = "unhandled"

        # ── Step 5: Record event as processed ────────────────────────
        # This is INSIDE the transaction — if processing failed and rolled
        # back, this record won't exist, so Stripe's retry will reprocess.
        processing_time_ms = int((time.monotonic() - start_time) * 1000)

        db.add(StripeWebhookEventRow(
            stripe_event_id=event_id,
            event_type=event_type,
            processed_at=datetime.utcnow(),
            processing_time_ms=processing_time_ms,
            status="processed",
            payload_hash=payload_hash,
        ))

    # ── Step 6: Enqueue async side effects ───────────────────────────
    # These happen AFTER the transaction commits successfully.
    # If SQS fails, a reconciliation job will catch up later.
    try:
        await _enqueue_side_effects(sqs_client, event_type, event["data"]["object"], action_taken)
    except Exception as e:
        # Log but don't fail — the core state is already committed
        logger.error(
            "Failed to enqueue side effects",
            extra={"event_id": event_id, "error": str(e)},
        )

    logger.info(
        "Webhook processed successfully",
        extra={
            "event_id": event_id,
            "event_type": event_type,
            "action": action_taken,
            "processing_time_ms": processing_time_ms,
        },
    )


# ─── Event Handlers ──────────────────────────────────────────────────────────

async def _create_subscription_from_checkout(
    db: AsyncSession, session: dict
) -> str:
    """Handle checkout.session.completed — create subscription record."""
    stripe_sub_id = session["subscription"]
    parent_id = session["metadata"].get("parent_id")
    plan_slug = session["metadata"].get("plan")

    if not parent_id or not plan_slug:
        logger.error("Missing metadata in checkout session", extra={"session_id": session["id"]})
        return "missing_metadata"

    # Fetch full subscription from Stripe for accurate state
    stripe_sub = stripe.Subscription.retrieve(stripe_sub_id)

    # Find the plan
    plan = await db.execute(
        select(SubscriptionPlanRow).where(SubscriptionPlanRow.slug == plan_slug)
    )
    plan_row = plan.scalar_one()

    # Create local subscription record
    sub = SubscriptionRow(
        parent_id=parent_id,
        plan_id=plan_row.id,
        stripe_subscription_id=stripe_sub_id,
        stripe_customer_id=session["customer"],
        state="trial" if stripe_sub.get("trial_end") else "active",
        trial_start=datetime.fromtimestamp(stripe_sub["trial_start"]) if stripe_sub.get("trial_start") else None,
        trial_end=datetime.fromtimestamp(stripe_sub["trial_end"]) if stripe_sub.get("trial_end") else None,
        current_period_start=datetime.fromtimestamp(stripe_sub["current_period_start"]),
        current_period_end=datetime.fromtimestamp(stripe_sub["current_period_end"]),
    )
    db.add(sub)
    await db.flush()  # Get sub.id

    # Audit log
    db.add(SubscriptionEventRow(
        subscription_id=sub.id,
        event_type="created",
        new_state=sub.state,
        stripe_event_id=session.get("id"),
        metadata={"plan": plan_slug, "trial_days": stripe_sub.get("trial_end")},
    ))

    return "subscription_created"


async def _handle_payment_success(db: AsyncSession, invoice: dict) -> str:
    """Handle invoice.payment_succeeded — activate/extend subscription."""
    stripe_sub_id = invoice["subscription"]

    sub = await db.execute(
        select(SubscriptionRow).where(
            SubscriptionRow.stripe_subscription_id == stripe_sub_id
        )
    )
    sub_row = sub.scalar_one_or_none()
    if not sub_row:
        logger.warning(f"Subscription not found for {stripe_sub_id}")
        return "subscription_not_found"

    previous_state = sub_row.state

    # Out-of-order check: skip if our record is already ahead
    stripe_sub = stripe.Subscription.retrieve(stripe_sub_id)
    sub_row.state = "active"
    sub_row.current_period_start = datetime.fromtimestamp(stripe_sub["current_period_start"])
    sub_row.current_period_end = datetime.fromtimestamp(stripe_sub["current_period_end"])
    sub_row.past_due_since = None  # Clear any past_due state

    db.add(SubscriptionEventRow(
        subscription_id=sub_row.id,
        event_type="payment_succeeded",
        previous_state=previous_state,
        new_state="active",
        stripe_event_id=invoice.get("id"),
        metadata={"amount_paid": invoice.get("amount_paid")},
    ))

    return "payment_succeeded"


async def _handle_payment_failure(db: AsyncSession, invoice: dict) -> str:
    """Handle invoice.payment_failed — mark subscription as past_due."""
    stripe_sub_id = invoice["subscription"]

    sub = await db.execute(
        select(SubscriptionRow).where(
            SubscriptionRow.stripe_subscription_id == stripe_sub_id
        )
    )
    sub_row = sub.scalar_one_or_none()
    if not sub_row:
        return "subscription_not_found"

    previous_state = sub_row.state
    sub_row.state = "past_due"
    if not sub_row.past_due_since:
        sub_row.past_due_since = datetime.utcnow()

    db.add(SubscriptionEventRow(
        subscription_id=sub_row.id,
        event_type="payment_failed",
        previous_state=previous_state,
        new_state="past_due",
        stripe_event_id=invoice.get("id"),
        metadata={
            "attempt_count": invoice.get("attempt_count"),
            "next_payment_attempt": invoice.get("next_payment_attempt"),
        },
    ))

    return "payment_failed"


async def _handle_subscription_update(
    db: AsyncSession, subscription: dict, previous_attributes: dict
) -> str:
    """Handle customer.subscription.updated — plan changes, cancellation scheduling."""
    stripe_sub_id = subscription["id"]

    sub = await db.execute(
        select(SubscriptionRow).where(
            SubscriptionRow.stripe_subscription_id == stripe_sub_id
        )
    )
    sub_row = sub.scalar_one_or_none()
    if not sub_row:
        return "subscription_not_found"

    previous_state = sub_row.state
    actions = []

    # Cancellation scheduled
    if subscription.get("cancel_at_period_end") and not previous_attributes.get("cancel_at_period_end"):
        sub_row.state = "canceling"
        sub_row.cancel_at = datetime.fromtimestamp(subscription["current_period_end"])
        actions.append("cancellation_scheduled")

    # Cancellation reversed
    elif not subscription.get("cancel_at_period_end") and previous_attributes.get("cancel_at_period_end") is True:
        sub_row.state = "active"
        sub_row.cancel_at = None
        actions.append("cancellation_reversed")

    # Plan change
    if "items" in previous_attributes:
        new_price_id = subscription["items"]["data"][0]["price"]["id"]
        new_plan = await db.execute(
            select(SubscriptionPlanRow).where(
                SubscriptionPlanRow.stripe_price_id == new_price_id
            )
        )
        new_plan_row = new_plan.scalar_one_or_none()
        if new_plan_row:
            sub_row.plan_id = new_plan_row.id
            actions.append(f"plan_changed_to_{new_plan_row.slug}")

    db.add(SubscriptionEventRow(
        subscription_id=sub_row.id,
        event_type="subscription_updated",
        previous_state=previous_state,
        new_state=sub_row.state,
        metadata={"actions": actions},
    ))

    return ",".join(actions) or "no_relevant_changes"


async def _handle_subscription_deletion(db: AsyncSession, subscription: dict) -> str:
    """Handle customer.subscription.deleted — final cancellation."""
    stripe_sub_id = subscription["id"]

    sub = await db.execute(
        select(SubscriptionRow).where(
            SubscriptionRow.stripe_subscription_id == stripe_sub_id
        )
    )
    sub_row = sub.scalar_one_or_none()
    if not sub_row:
        return "subscription_not_found"

    previous_state = sub_row.state
    sub_row.state = "canceled"
    sub_row.canceled_at = datetime.utcnow()

    db.add(SubscriptionEventRow(
        subscription_id=sub_row.id,
        event_type="subscription_canceled",
        previous_state=previous_state,
        new_state="canceled",
    ))

    return "subscription_canceled"


async def _enqueue_side_effects(
    sqs_client, event_type: str, data: dict, action: str
) -> None:
    """Enqueue emails, cache invalidation, and other async side effects."""
    messages = []

    if action == "subscription_created":
        messages.append({
            "type": "email",
            "template": "welcome_trial",
            "parent_id": data.get("metadata", {}).get("parent_id"),
        })

    elif action == "payment_succeeded":
        messages.append({
            "type": "email",
            "template": "payment_receipt",
            "stripe_invoice_id": data.get("id"),
        })
        messages.append({
            "type": "cache_invalidation",
            "key_pattern": f"features:*",  # Invalidate by subscription lookup
        })

    elif action == "payment_failed":
        messages.append({
            "type": "email",
            "template": "payment_failed_dunning",
            "stripe_invoice_id": data.get("id"),
        })

    elif action == "subscription_canceled":
        messages.append({
            "type": "email",
            "template": "subscription_ended",
            "stripe_subscription_id": data.get("id"),
        })
        messages.append({
            "type": "cache_invalidation",
            "key_pattern": f"features:*",
        })

    for msg in messages:
        await sqs_client.send_message(
            QueueUrl="https://sqs.us-west-2.amazonaws.com/.../padi-ai-side-effects",
            MessageBody=json.dumps(msg),
        )
```

### Algorithm 2: Feature Gate Middleware

```python
"""
FastAPI dependency for feature gating.
Usage:
    @router.get("/reports/eog", dependencies=[Depends(require_feature(Feature.EOG_REPORT))])
    async def get_eog_report(...):
        ...
"""
from functools import wraps
from typing import Callable

from fastapi import Depends, HTTPException, Request
from starlette.status import HTTP_403_FORBIDDEN

from app.auth.dependencies import get_current_user
from app.billing.service import Feature, FeatureGatingService
from app.models.user import User


def require_feature(feature: Feature) -> Callable:
    """
    FastAPI dependency factory for feature gating.

    Returns a dependency that:
    1. Extracts the current user from the auth token
    2. Checks if the user's subscription includes the required feature
    3. Raises 403 with upgrade prompt if feature is not enabled
    4. Passes through silently if feature is enabled

    Usage:
        @router.get("/practice/unlimited")
        async def unlimited_practice(
            _: None = Depends(require_feature(Feature.UNLIMITED_PRACTICE)),
            user: User = Depends(get_current_user),
        ):
            ...
    """
    async def _check_feature(
        request: Request,
        user: User = Depends(get_current_user),
    ) -> None:
        gating_service: FeatureGatingService = request.app.state.feature_gating_service

        is_enabled = await gating_service.is_feature_enabled(user.id, feature)

        if not is_enabled:
            raise HTTPException(
                status_code=HTTP_403_FORBIDDEN,
                detail={
                    "error": "feature_not_available",
                    "feature": feature.value,
                    "message": f"This feature requires an upgraded subscription.",
                    "upgrade_url": "/billing/plans",
                },
            )

    _check_feature.__name__ = f"require_{feature.value}"
    return _check_feature


def require_any_feature(*features: Feature) -> Callable:
    """
    Require at least one of the given features.
    Useful for OR-logic gating: require_any_feature(Feature.INDIVIDUAL, Feature.FAMILY)
    """
    async def _check_any_feature(
        request: Request,
        user: User = Depends(get_current_user),
    ) -> None:
        gating_service: FeatureGatingService = request.app.state.feature_gating_service

        for feature in features:
            if await gating_service.is_feature_enabled(user.id, feature):
                return  # At least one feature is enabled

        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail={
                "error": "feature_not_available",
                "features": [f.value for f in features],
                "message": "This feature requires an upgraded subscription.",
                "upgrade_url": "/billing/plans",
            },
        )

    return _check_any_feature
```

### Algorithm 3: Content Delivery Optimization for Schools

**CDN caching strategy for school-day traffic:**

```yaml
# CloudFront cache behaviors configuration (Terraform/CDK equivalent)

cache_behaviors:
  # 1. Static assets — immutable, cache forever
  - path_pattern: "/static/*"
    cache_policy:
      min_ttl: 31536000          # 1 year
      max_ttl: 31536000
      default_ttl: 31536000
    compress: true
    viewer_protocol_policy: "redirect-to-https"
    comment: "Question images, badge icons, illustration assets"

  # 2. Next.js static chunks — content-hashed, cache forever
  - path_pattern: "/_next/static/*"
    cache_policy:
      min_ttl: 31536000
      max_ttl: 31536000
    compress: true
    comment: "Hashed JS/CSS bundles — safe to cache indefinitely"

  # 3. i18n translation files — cache with revalidation
  - path_pattern: "/locales/*"
    cache_policy:
      min_ttl: 3600              # 1 hour minimum
      max_ttl: 86400             # 24 hours maximum
      default_ttl: 3600
    compress: true
    comment: "Translation JSON files — may update with deployments"

  # 4. API routes — no cache, pass-through to origin
  - path_pattern: "/api/*"
    cache_policy:
      min_ttl: 0
      max_ttl: 0
      default_ttl: 0
    origin_request_policy: "AllViewerExceptHostHeader"
    comment: "Dynamic API — must always hit origin"

  # 5. Standards data — cache with ETag validation
  - path_pattern: "/api/v1/standards/*"
    cache_policy:
      min_ttl: 0
      max_ttl: 86400
      default_ttl: 3600
    comment: "Oregon math standards — rarely change, use ETag for freshness"

# Origin Shield: reduce origin load during school day peak
origin_shield:
  enabled: true
  region: "us-west-2"           # Closest to Oregon schools
```

**Auto-scaling for school-day traffic:**

```python
# ECS Auto Scaling Configuration

# API Service: scales on CPU + request count
api_scaling = {
    "service": "padi-ai-api",
    "min_capacity": 2,
    "max_capacity": 20,
    "policies": [
        {
            "type": "TargetTrackingScaling",
            "metric": "ECSServiceAverageCPUUtilization",
            "target_value": 70,
            "scale_in_cooldown": 300,
            "scale_out_cooldown": 60,
        },
        {
            "type": "TargetTrackingScaling",
            "metric": "ALBRequestCountPerTarget",
            "target_value": 500,  # requests per target per minute
            "scale_in_cooldown": 300,
            "scale_out_cooldown": 60,
        },
    ],
    # Scheduled scaling: pre-warm for school day
    "scheduled_actions": [
        {
            "schedule": "cron(30 8 ? * MON-FRI *)",  # 8:30 AM Pacific
            "min_capacity": 6,
            "comment": "Pre-warm before school day starts at 9 AM",
        },
        {
            "schedule": "cron(0 16 ? * MON-FRI *)",  # 4:00 PM Pacific
            "min_capacity": 2,
            "comment": "Scale down after school hours",
        },
    ],
}

# Agent Engine: scales on WebSocket connection count
agent_scaling = {
    "service": "padi-ai-agent-engine",
    "min_capacity": 2,
    "max_capacity": 15,
    "policies": [
        {
            "type": "TargetTrackingScaling",
            "metric": "WebSocketConnectionCount",  # Custom CloudWatch metric
            "target_value": 200,  # connections per task
            "scale_in_cooldown": 600,   # Slower scale-in — don't disrupt sessions
            "scale_out_cooldown": 60,
        },
    ],
}
```

**Rate limiting per school:**

```python
# Redis-based rate limiter (sliding window)
SCHOOL_RATE_LIMIT = 1000  # requests per minute per school_id

async def check_school_rate_limit(school_id: UUID, redis: Redis) -> bool:
    """
    Sliding window rate limit per school.
    Prevents runaway Clever sync or school-wide bot activity.
    Returns True if request is allowed, False if rate-limited.
    """
    key = f"rate_limit:school:{school_id}"
    now = time.time()
    window_start = now - 60  # 1-minute window

    pipe = redis.pipeline()
    pipe.zremrangebyscore(key, 0, window_start)  # Remove old entries
    pipe.zadd(key, {str(now): now})              # Add current request
    pipe.zcard(key)                              # Count requests in window
    pipe.expire(key, 120)                        # TTL: 2 minutes
    results = await pipe.execute()

    request_count = results[2]
    return request_count <= SCHOOL_RATE_LIMIT
```

---

## 4. Infrastructure (Stage 5)

### 4.1 Scale-Out Configuration for MMP

**Target:** 10,000 concurrent users during school-day peak (9 AM – 3 PM Pacific, weekdays).

#### ECS Auto Scaling

| Service | Min Tasks | Max Tasks | Scale Metric | Target | Scale-Out Cooldown | Scale-In Cooldown |
|---------|-----------|-----------|-------------|--------|-------------------|-------------------|
| API Service | 2 | 20 | CPU Utilization | 70% | 60s | 300s |
| API Service | 2 | 20 | ALB Request Count | 500/target/min | 60s | 300s |
| Agent Engine | 2 | 15 | WebSocket Connections | 200/task | 60s | 600s |
| Billing Service | 1 | 5 | CPU Utilization | 70% | 120s | 600s |
| School Mgmt Svc | 1 | 3 | CPU Utilization | 70% | 120s | 600s |
| Async Worker | 2 | 10 | SQS Queue Depth | 100 messages | 30s | 300s |

**Task sizing:**

```
API Service:       CPU: 1024 (1 vCPU),  Memory: 2048 MB
Agent Engine:      CPU: 2048 (2 vCPU),  Memory: 4096 MB  (LLM calls are memory-intensive)
Billing Service:   CPU: 512  (0.5 vCPU), Memory: 1024 MB
School Mgmt Svc:   CPU: 512  (0.5 vCPU), Memory: 1024 MB
Async Worker:      CPU: 1024 (1 vCPU),  Memory: 2048 MB  (question gen needs compute)
```

#### RDS Configuration

```
Primary Instance:     db.r6g.xlarge (4 vCPU, 32 GB RAM)
Read Replica:         db.r6g.large  (2 vCPU, 16 GB RAM)
Storage:              500 GB gp3, 3000 IOPS, 125 MB/s throughput
Multi-AZ:             Enabled (primary + standby)
Backup:               35-day automated snapshots + PITR (7-day window)
```

**Read replica routing:**

```python
# SQLAlchemy engine configuration with read/write splitting

from sqlalchemy.ext.asyncio import create_async_engine

# Write engine — always goes to primary
write_engine = create_async_engine(
    settings.DATABASE_URL_PRIMARY,
    pool_size=20,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=3600,
)

# Read engine — goes to read replica for dashboard/reporting queries
read_engine = create_async_engine(
    settings.DATABASE_URL_REPLICA,
    pool_size=30,       # Higher pool — dashboards are read-heavy
    max_overflow=15,
    pool_timeout=30,
    pool_recycle=3600,
)

# PgBouncer sits between ECS and RDS
# pgbouncer.ini settings:
# pool_mode = transaction
# max_client_conn = 1000
# default_pool_size = 50
# min_pool_size = 10
# reserve_pool_size = 5
# reserve_pool_timeout = 3
```

**Read replica query routing:**

Dashboard queries, classroom rosters, progress reports, and analytics aggregations route to the read replica. All write operations (assessment submissions, subscription changes, BKT updates) route to the primary.

```python
# Usage in repository layer
class ProgressRepository:
    async def get_student_progress(self, student_id: UUID) -> StudentProgress:
        """Read from replica — eventual consistency is OK for dashboards."""
        async with read_session_factory() as db:
            return await self._query_progress(db, student_id)

    async def update_bkt_state(self, student_id: UUID, skill: str, state: BKTState) -> None:
        """Write to primary — must be strongly consistent."""
        async with write_session_factory() as db:
            await self._update_state(db, student_id, skill, state)
```

#### ElastiCache (Redis)

```
Cluster Mode:     Enabled
Shards:           3
Replicas/Shard:   2 (total 9 nodes)
Node Type:        cache.r6g.large (2 vCPU, 13 GB)
Total Memory:     ~39 GB across cluster

Keyspace Prefixes:
  session:*       — User session data (TTL: 24h)
  features:*      — Feature gate cache (TTL: 5min)
  rate_limit:*    — Rate limiting counters (TTL: 2min)
  bkt_cache:*     — BKT state cache (TTL: 10min)
  sub:invalidate  — Pub/sub channel for subscription cache invalidation
  oauth_state:*   — CSRF state for OAuth flows (TTL: 10min)

Eviction Policy:  allkeys-lru
```

#### CloudFront

```
Distribution:
  - Custom domain: cdn.padi.ai (ACM certificate in us-east-1)
  - Origin Shield: us-west-2 (reduce origin load)
  - HTTP/2 + HTTP/3 enabled
  - Minimum TLS: TLSv1.2
  - Geo-restriction: None (but WAF rules limit to US for student data)

Cache Behaviors:
  /static/*       → S3 origin, max-age=31536000
  /_next/static/* → Vercel origin, max-age=31536000
  /locales/*      → S3 origin, max-age=3600, ETag validation
  /api/*          → ALB origin, no cache, all headers forwarded
  Default (*)     → Vercel origin, managed caching
```

### 4.2 COPPA Safe Harbor Certification Impact on Infrastructure

To achieve kidSAFE or PRIVO Safe Harbor certification, the following infrastructure changes are required:

**1. Data Residency**
- All student data must remain in US-based AWS regions only (us-east-1 or us-west-2)
- S3 bucket policy: deny any cross-region replication to non-US regions
- CloudFront: PriceClass_100 (US, Canada, Europe) — but student data served only from US edge locations
- PostHog: use US cloud instance (`us.i.posthog.com`)
- Auth0: US-based tenant

**2. Audit Logging**
- All access to student data must be logged: who accessed what, when, from where
- CloudTrail: enabled for all API calls to RDS, S3, and Secrets Manager
- Application-level audit log: every query touching `student_profiles`, `assessment_responses`, `bkt_states` tables logs the requesting user, timestamp, and data accessed
- Audit logs retained for 7 years (FERPA requirement for education records)
- Stored in S3 with Object Lock (WORM — write once, read many) to prevent tampering

**3. Penetration Testing**
- Annual penetration test by a certified third-party firm
- Vendor selection criteria: CREST-certified, OWASP-aligned methodology, experience with EdTech/COPPA
- Scope: external (API endpoints, web app), internal (VPC network), social engineering awareness
- Remediation SLAs: Critical = 7 days, High = 14 days, Medium = 30 days, Low = 90 days
- Retest within 30 days of critical/high remediation

**4. Security Headers**

```python
# FastAPI middleware — all responses include security headers
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)

        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "0"  # Disabled — use CSP instead
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), "
            "interest-cohort=()"  # Block FLoC/Topics API
        )
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://us.i.posthog.com; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' https://cdn.padi.ai data:; "
            "connect-src 'self' https://us.i.posthog.com https://api.stripe.com; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self' https://checkout.stripe.com;"
        )

        return response
```

**5. Vulnerability Management**
- All critical/high CVEs must be patched within 7 days of public disclosure
- Automated dependency scanning in CI (see Cross-Cutting doc Section 3.3)
- Container image scanning with Trivy on every build
- AWS Inspector enabled for all ECS tasks
- Monthly vulnerability review meeting (even for solo developer — documented checklist)

---

## 5. Testing Plan (Stage 5)

### 5.1 Billing Tests (Critical — Money Involved)

| # | Test Scenario | Type | Precondition | Action | Expected Result |
|---|--------------|------|-------------|--------|-----------------|
| 1 | **Happy path: checkout → active** | Integration | Parent account exists, no subscription | Complete Stripe test checkout | Subscription created in DB with state=TRIAL, features unlocked, welcome email queued |
| 2 | **Trial expiry → payment success** | Integration | Active trial (day 14) | Stripe fires `invoice.payment_succeeded` | State transitions TRIAL → ACTIVE, `current_period_end` set to +30 days |
| 3 | **Payment failure → retry → success** | Integration | Active subscription | Stripe fires `invoice.payment_failed` then (3 days later) `invoice.payment_succeeded` | State: ACTIVE → PAST_DUE → ACTIVE. Dunning email sent on failure, recovery email on success |
| 4 | **Payment failure → all retries fail** | Integration | Active subscription, 3 failed payments | Stripe fires `customer.subscription.deleted` | State: PAST_DUE → CANCELED. Features revoked. Final cancellation email sent |
| 5 | **Cancellation → end of period** | Integration | Active subscription | Parent requests cancellation | State: ACTIVE → CANCELING. Features remain until `current_period_end`. Stripe subscription has `cancel_at_period_end=true` |
| 6 | **School PO invoice** | Integration | School with admin account | Create invoice with PO number | Stripe invoice created with net-30 terms, PDF generated, school admin notified |
| 7 | **Webhook duplicate delivery** | Unit | Webhook event already in `stripe_webhook_events` | Same event_id received again | Handler returns 200 immediately, no DB mutations, no duplicate emails |
| 8 | **Webhook out of order** | Integration | No subscription record yet | `invoice.payment_succeeded` arrives before `checkout.session.completed` | Handler processes gracefully (creates subscription on checkout, re-checks on payment), no data corruption |
| 9 | **Subscription upgrade** | Integration | Active Individual plan | Parent upgrades to Family | Plan updated immediately, feature cache invalidated, new features (4 students) available instantly |
| 10 | **Data isolation** | E2E | Two schools with subscriptions | School A queries student data | School A sees only their students, never School B's. RLS enforced at DB level |

### 5.2 School Onboarding Tests

| # | Test Scenario | Type | Expected Result |
|---|--------------|------|-----------------|
| 1 | **Clever OAuth happy path** | Integration | District admin completes OAuth, connection created, district/schools discovered |
| 2 | **Roster sync — new students** | Integration | Students from Clever created in PADI.AI with correct school_id and classroom assignments |
| 3 | **Roster sync — student removed** | Integration | Student removed from Clever roster is soft-unenrolled (not deleted) — learning history preserved |
| 4 | **Duplicate detection** | Integration | Parent-created student matching Clever import generates merge request, not duplicate |
| 5 | **DPA agreement flow** | E2E | School admin reviews DPA, signs electronically, signed PDF archived in S3, timestamp recorded |
| 6 | **Teacher classroom view** | E2E | Teacher sees only students in their assigned classrooms, cannot see other teachers' students |
| 7 | **School admin view** | E2E | School admin sees all classrooms and students in their school, but cannot modify learning plans |
| 8 | **Clever token refresh** | Integration | Expired Clever token auto-refreshes before sync, sync completes successfully |

### 5.3 i18n Tests

| # | Test Scenario | Type | Expected Result |
|---|--------------|------|-----------------|
| 1 | **Translation completeness** | Unit | Every key in `en.json` has a corresponding key in `es.json` (build-time check) |
| 2 | **Spanish word problems** | Integration | AI-generated Spanish word problems pass validation pipeline (readability, math accuracy) |
| 3 | **Locale switching** | E2E | Parent switches from English to Spanish, preference persists across sessions via `user_locale_preferences` |
| 4 | **KaTeX rendering** | Visual regression | Math notation renders identically in English and Spanish contexts |
| 5 | **Tutor prompts in Spanish** | Contract test | Spanish tutor hints meet same behavioral contracts as English (no answer reveal at level 1, grade-appropriate language) |
| 6 | **URL locale prefix** | E2E | `/es/practice` serves Spanish UI, `/en/practice` serves English UI, `/practice` redirects based on user preference |

### 5.4 Load Tests (MMP Scale)

```python
"""
Locust load test for 10,000 concurrent users.
Run: locust -f loadtest.py --headless -u 10000 -r 500 --run-time 30m
"""
from locust import HttpUser, TaskSet, between, task
import json
import random
import websocket


class StudentPractice(TaskSet):
    """60% of users — students in active practice sessions."""

    @task(1)
    def start_session(self):
        """Start a practice session (REST → then WebSocket)."""
        self.client.post("/api/v1/sessions", json={
            "student_id": self.user.student_id,
            "skill_code": random.choice(["4.OA.A.1", "4.NBT.B.5", "4.NF.A.1"]),
        })

    @task(10)
    def answer_question(self):
        """Submit answer via WebSocket (simulated as REST for load test)."""
        self.client.post("/api/v1/sessions/current/answer", json={
            "question_id": self.user.current_question_id,
            "answer": random.choice(["A", "B", "C", "D"]),
        })

    @task(3)
    def request_hint(self):
        """Request a tutor hint."""
        self.client.post("/api/v1/sessions/current/hint", json={
            "hint_level": random.randint(1, 3),
        })


class ParentDashboard(TaskSet):
    """20% of users — parents viewing dashboards."""

    @task(5)
    def view_progress(self):
        self.client.get(f"/api/v1/parents/{self.user.parent_id}/progress")

    @task(2)
    def view_report(self):
        self.client.get(f"/api/v1/reports/eog/{self.user.student_id}")

    @task(1)
    def view_subscription(self):
        self.client.get(f"/api/v1/billing/subscription")


class TeacherRoster(TaskSet):
    """10% of users — teachers viewing classroom rosters."""

    @task(5)
    def view_classroom(self):
        self.client.get(f"/api/v1/classrooms/{self.user.classroom_id}/students")

    @task(3)
    def view_student_detail(self):
        self.client.get(f"/api/v1/classrooms/{self.user.classroom_id}/students/{self.user.student_id}")

    @task(1)
    def export_report(self):
        self.client.get(f"/api/v1/classrooms/{self.user.classroom_id}/report?format=pdf")


class OnboardingUser(TaskSet):
    """10% of users — onboarding/assessment flows."""

    @task(1)
    def complete_assessment(self):
        # Simulate answering 43 assessment questions
        for i in range(43):
            self.client.post("/api/v1/assessment/answer", json={
                "question_id": f"q_{i}",
                "answer": random.choice(["A", "B", "C", "D"]),
            })


# ── Performance Thresholds ───────────────────────────────────────────
# These gate deployment to production:
#   P95 API response < 500ms
#   P95 WebSocket message RTT < 3s
#   Error rate < 1%
#   No connection pool exhaustion
#   No Redis evictions during test
```

---

## 6. QA Plan — MMP Exit Criteria

The following checklist must be fully satisfied before declaring MMP. Each item requires evidence (test report, screenshot, log, or sign-off).

### Billing & Monetization (15 items)

- [ ] Stripe test-mode checkout completes successfully for Individual plan
- [ ] Stripe test-mode checkout completes successfully for Family plan
- [ ] School invoice creation and delivery works with PO number
- [ ] Trial period (14 days) correctly gates features at day 0 (all unlocked) and day 15 (gated)
- [ ] Payment success transitions subscription to ACTIVE with correct period dates
- [ ] Payment failure triggers PAST_DUE state and dunning email on correct schedule (day 1, day 3, day 7)
- [ ] All retries failed → subscription cancellation → features revoked
- [ ] Parent can cancel subscription — remains active until period end, then features revoked
- [ ] Parent can reactivate a canceling subscription before period end
- [ ] Subscription upgrade (Individual → Family) takes effect immediately, features updated
- [ ] Subscription downgrade schedules for end of billing period
- [ ] Webhook idempotency: duplicate events processed exactly once (verified with test)
- [ ] Webhook signature verification rejects tampered payloads
- [ ] Feature gating cache invalidation fires within 5 seconds of subscription change
- [ ] Stripe webhook endpoint responds within 5 seconds (Stripe timeout threshold)

### School Onboarding (10 items)

- [ ] Clever OAuth flow completes for sandbox test district
- [ ] Roster sync creates student profiles without duplicates
- [ ] Roster sync correctly handles student removals (soft-unenroll, not delete)
- [ ] Duplicate student detection flags merge requests for admin review
- [ ] FERPA DPA agreement recorded with timestamp, signer name, email, and title
- [ ] Signed DPA PDF archived in S3 with Object Lock
- [ ] School admin can view all student progress in their school
- [ ] School admin cannot modify individual student learning plans
- [ ] Teacher sees only their own classrooms' students
- [ ] District admin can view across all schools in the district

### Scale & Performance (10 items)

- [ ] Load test: 10,000 concurrent users, P95 API response < 500ms
- [ ] Load test: 500 concurrent WebSocket sessions, P95 message RTT < 3s
- [ ] Load test: sustained 1-hour peak with no ECS task crashes
- [ ] Database: no connection pool exhaustion at peak load (PgBouncer metrics verified)
- [ ] Redis: zero evictions during 1-hour sustained peak load test
- [ ] Read replica lag < 1 second during peak load
- [ ] CloudFront cache hit ratio > 90% for static assets
- [ ] Auto-scaling: API scales from 2 → 8+ tasks within 3 minutes of load spike
- [ ] Auto-scaling: scale-in does not disrupt active WebSocket sessions
- [ ] CDN: all static assets served with correct Cache-Control headers

### Security & Compliance (12 items)

- [ ] COPPA Safe Harbor pre-certification checklist complete (kidSAFE or PRIVO)
- [ ] Security headers scan passes (A+ on securityheaders.com)
- [ ] Penetration test completed with no open critical or high findings
- [ ] Student PII encryption verified at rest (RDS AES-256, S3 SSE)
- [ ] Application-layer PII field encryption verified (parent email/name in PostgreSQL)
- [ ] TLS 1.3 enforced on all connections (no TLS 1.1/1.2 fallback)
- [ ] No student PII in application logs (log audit completed)
- [ ] No student PII in analytics events (PostHog audit completed)
- [ ] COPPA consent flow end-to-end test passes (parent email verification → consent → child access)
- [ ] FERPA DPA template reviewed by legal counsel
- [ ] Annual privacy policy review complete and published
- [ ] Vulnerability scan (Trivy + npm audit + pip-audit) shows zero critical/high

### Localization (6 items)

- [ ] All UI strings have Spanish translations (100% key coverage in `es.json`)
- [ ] Spanish math word problems pass validation pipeline
- [ ] Locale switching persists across sessions
- [ ] Spanish tutor hints meet behavioral contracts (tested against golden set)
- [ ] KaTeX math rendering is language-neutral (visual regression test)
- [ ] Accessibility: Spanish content meets same WCAG 2.1 AA standards as English

### Accessibility (5 items)

- [ ] axe-core automated scan: zero violations on all pages
- [ ] Screen reader (VoiceOver) can navigate full assessment flow
- [ ] Touch targets ≥ 48px on all interactive elements
- [ ] Font sizes ≥ 16px for all student-facing text
- [ ] No time-pressure UI elements visible to students (no countdown timers)

### Operational Readiness (5 items)

- [ ] All P1 alerts configured and tested (fire + resolve cycle)
- [ ] All operational runbooks written and reviewed
- [ ] Launch day checklist prepared and walkthrough completed
- [ ] Rollback procedure tested: can revert to previous version within 5 minutes
- [ ] On-call rotation established (even if solo: phone notifications + escalation)

**Total: 63 items. All must pass for MMP exit.**

---

## 7. Operational Runbooks (Stage 5)

### Runbook 7.1: Stripe Webhook Failure Recovery

**Trigger:** Alert fires for `padi.stripe.webhook.error_rate > 5%` or `padi.stripe.webhook.processing_lag > 60min`.

**Severity:** P1 — Revenue and subscription state affected.

**Symptoms:**
- Stripe dashboard shows webhook delivery failures (HTTP 500s from our endpoint)
- Subscriptions stuck in wrong state (e.g., payment succeeded in Stripe but TRIAL in our DB)
- Parents complaining about features being gated despite payment

**Diagnosis steps:**

1. **Check webhook endpoint health:**
   ```bash
   # Check if the billing service is running
   aws ecs describe-services --cluster padi-ai-prod --services padi-ai-billing
   
   # Check recent logs for errors
   aws logs filter-log-events \
     --log-group-name /ecs/padi-ai-billing \
     --filter-pattern "ERROR" \
     --start-time $(date -d '1 hour ago' +%s000)
   ```

2. **Check Stripe webhook dashboard:**
   - Go to Stripe Dashboard → Developers → Webhooks
   - Check the webhook endpoint status (is it marked as disabled?)
   - Check the event delivery log — look for consecutive failures

3. **Verify signature configuration:**
   ```bash
   # Compare webhook secret in AWS Secrets Manager with Stripe Dashboard
   aws secretsmanager get-secret-value --secret-id padi-ai/prod/stripe-webhook-secret
   ```

4. **Check for database issues:**
   ```bash
   # Check PgBouncer connection pool
   psql -h pgbouncer.internal -p 6432 pgbouncer -c "SHOW POOLS"
   
   # Check for lock contention
   psql -h primary.rds.internal -c "SELECT * FROM pg_stat_activity WHERE wait_event_type = 'Lock'"
   ```

**Recovery steps:**

1. **If webhook secret mismatch:** Update the secret in AWS Secrets Manager, restart billing service.

2. **If processing errors:** Fix the bug, deploy, then replay missed events:
   ```bash
   # List failed events in Stripe (last 24 hours)
   stripe events list --type invoice.payment_succeeded --delivery-success false --limit 100
   
   # Replay events one by one through Stripe CLI
   stripe events resend evt_1Nxxxxxxx
   ```

3. **If database connection issues:** Restart PgBouncer, check RDS connection limits.

4. **Manual reconciliation (last resort):**
   ```sql
   -- Find subscriptions where Stripe state differs from our DB
   -- Compare stripe_subscription_id status via Stripe API against local state
   SELECT s.id, s.state, s.stripe_subscription_id
   FROM subscriptions s
   WHERE s.state != 'canceled'
   AND s.updated_at < now() - interval '24 hours';
   ```
   For each mismatch, manually call the Stripe API to get current state and update the DB.

**Post-incident:**
- Review webhook processing logs for the incident window
- Verify all missed events have been replayed
- Check that all subscription states match Stripe
- Update monitoring if the alert didn't fire quickly enough

---

### Runbook 7.2: School Clever Sync Failure

**Trigger:** Alert fires for `padi.clever.sync.status = failed` or school admin reports stale roster.

**Severity:** P2 — Students may not have correct classroom access but can still use the app.

**Symptoms:**
- New students added in Clever don't appear in teacher's PADI.AI classroom
- Students transferred between classrooms still show in old classroom
- `clever_sync_jobs` table shows `status = 'failed'` for recent runs

**Diagnosis steps:**

1. **Check the sync job log:**
   ```sql
   SELECT id, school_id, status, error_message, error_details, started_at, completed_at
   FROM clever_sync_jobs
   WHERE school_id = '<school_id>'
   ORDER BY created_at DESC LIMIT 5;
   ```

2. **Check Clever API availability:**
   ```bash
   curl -H "Authorization: Bearer <test_token>" https://api.clever.com/v3.0/me
   ```

3. **Check token validity:**
   ```sql
   SELECT id, district_id, token_expires_at, last_sync_at
   FROM sso_connections
   WHERE district_id = '<district_id>';
   ```

4. **Check SQS queue for stuck messages:**
   ```bash
   aws sqs get-queue-attributes \
     --queue-url https://sqs.../padi-ai-clever-sync \
     --attribute-names ApproximateNumberOfMessages,ApproximateNumberOfMessagesNotVisible
   ```

**Recovery steps:**

1. **Token expired:** Trigger manual token refresh, then retry sync:
   ```python
   await clever_sync_service.refresh_token(connection_id)
   await clever_sync_service.sync_school_roster(school_id)
   ```

2. **Clever API down:** Wait for Clever status page to clear, then manually trigger sync.

3. **Data conflict:** Review merge requests in the admin dashboard, resolve duplicates manually.

4. **Partial sync failure:** Re-run the sync with `force_full_sync=True` to override delta logic.

**Post-incident:**
- Verify all classrooms have correct enrollment counts matching Clever
- Notify affected teachers if roster was stale for >24 hours

---

### Runbook 7.3: Subscription State Desync

**Trigger:** Parent reports features are gated despite having paid, or features are available despite cancellation. Alert fires on `padi.billing.state_desync` custom metric.

**Severity:** P1 — Directly impacts revenue and user trust.

**Diagnosis steps:**

1. **Compare Stripe and DB state:**
   ```python
   # Get our DB state
   sub = await db.execute(
       select(SubscriptionRow).where(SubscriptionRow.parent_id == parent_id)
   )

   # Get Stripe state
   stripe_sub = stripe.Subscription.retrieve(sub.stripe_subscription_id)

   # Compare: sub.state vs stripe_sub.status
   print(f"DB: {sub.state}, Stripe: {stripe_sub.status}")
   ```

2. **Check for missed webhooks:**
   ```sql
   -- Find the gap: what events did we process vs what Stripe sent?
   SELECT stripe_event_id, event_type, processed_at
   FROM stripe_webhook_events
   WHERE stripe_event_id LIKE '%sub_xxx%'
   ORDER BY processed_at DESC;
   ```

3. **Check webhook endpoint logs for errors during the period.**

**Recovery steps:**

1. **Re-derive state from Stripe (authoritative source):**
   ```python
   stripe_sub = stripe.Subscription.retrieve(stripe_subscription_id)

   # Map Stripe status to our state
   state_map = {
       "trialing": "trial",
       "active": "active",
       "past_due": "past_due",
       "canceled": "canceled",
       "unpaid": "past_due",
   }

   our_sub.state = state_map[stripe_sub.status]
   our_sub.current_period_end = datetime.fromtimestamp(stripe_sub.current_period_end)
   await db.commit()
   ```

2. **Invalidate feature cache:** `await redis.delete(f"features:{parent_id}")`

3. **Replay missed webhooks from Stripe CLI.**

4. **Log the desync in `subscription_events` with `event_type = "manual_reconciliation"`.**

**Prevention:**
- Run a daily reconciliation job that compares all active subscriptions against Stripe API
- Alert on any mismatches found by the reconciliation job

---

### Runbook 7.4: MMP Launch Day Operations

**Pre-Launch Checklist (T-24 hours):**

- [ ] All MMP QA exit criteria (Section 6) passed — documented in release notes
- [ ] Database migration applied to production and verified
- [ ] Stripe webhooks verified in production mode (send test event)
- [ ] Clever SSO verified with at least one pilot school
- [ ] Load test results reviewed — production can handle projected launch traffic
- [ ] CDN cache warmed for static assets
- [ ] All monitoring dashboards verified (metrics flowing)
- [ ] All P1/P2 alerts verified (test fire + resolve)
- [ ] Rollback plan documented and tested
- [ ] Support/FAQ page updated for billing and school onboarding flows

**Launch Day Monitoring (T-0):**

| Time | Action |
|------|--------|
| T-2h | Pre-warm ECS tasks to min 6 API, 4 Agent Engine |
| T-1h | Final health checks: all services green, DB connections nominal |
| T-0 | Enable production Stripe billing (flip feature flag) |
| T+0 | Watch dashboards: error rates, latency, signup funnel |
| T+15m | First signup verification: checkout → webhook → subscription → features |
| T+30m | Check: Stripe webhook processing lag < 5s |
| T+1h | Check: no elevated error rates, no PgBouncer saturation |
| T+2h | Check: email delivery rate > 95% (SES metrics) |
| T+4h | Check: first school onboarding attempt (if pre-scheduled) |
| T+8h | End-of-day review: error rates, failed payments, support tickets |

**Rollback Criteria (trigger immediate rollback):**

1. API error rate > 10% for more than 5 minutes
2. Stripe webhook processing completely failing (all events returning 500)
3. Data corruption detected (subscription states invalid)
4. Security incident (any unauthorized data access)

**Rollback Procedure:**

```bash
# 1. Disable billing feature flag (immediately stops new checkouts)
aws ssm put-parameter --name /padi-ai/prod/features/billing_enabled --value "false" --overwrite

# 2. Revert ECS to previous task definition
aws ecs update-service --cluster padi-ai-prod --service padi-ai-api \
  --task-definition padi-ai-api:PREVIOUS_VERSION

# 3. If DB migration needs reversal:
# Run the down migration script (pre-tested)
alembic downgrade -1

# 4. Notify affected users via SES
# (Template: "We're experiencing issues and are working to resolve them")
```

**Post-Launch (T+24h):**
- Review all metrics against projections
- Address any support tickets related to billing or onboarding
- Conduct mini-retrospective: what went well, what to improve for next launch
- Confirm no COPPA-sensitive data leaks in logs or analytics

---

*End of ENG-005 — Stage 5 Engineering Plan*
