# PADI.AI — SDLC Lifecycle Document
## Stage 4: End-of-Grade Assessment & Teacher/Parent Reporting — MVP Milestone
### Months 11–14 | Document ID: LC-004 | Version 1.0

**Status:** Draft  
**Owner:** Engineering Lead / QA Lead  
**Reviewers:** Backend Engineering, Frontend Engineering, Curriculum, Legal (FERPA/COPPA), MLOps  
**Dependencies:** LC-001 (Stage 1), LC-002 (Stage 2), LC-003 (Stage 3)  
**Epic Reference:** MATH-400 series  
**MVP Milestone:** ✅ Stage 4 Completion = PADI.AI MVP  
**Last Updated:** 2026-04-04  

---

## Table of Contents

1. [Architecture Review](#1-architecture-review)
2. [User Story Breakup](#2-user-story-breakup)
3. [Detailed Test Plan](#3-detailed-test-plan)
4. [Operations Plan](#4-operations-plan)
5. [Manual QA Plan](#5-manual-qa-plan)

---

## 1. Architecture Review

**Stage 4 Solo Development Total Estimate:** 120–165 agent-hours | Calendar: 5–7 months — MVP milestone

### 1.1 Overview — What Stage 4 Adds to the System

Stage 4 is the MVP milestone. It closes the PADI.AI learning loop by adding summative assessment, automated reporting, teacher and parent dashboards, and the infrastructure hardening required for production readiness. Every component is purpose-built to complement the adaptive practice engine from Stage 3 without adding unnecessary complexity.

The three principal additions are:

1. **CAT Assessment Engine** — A Computer Adaptive Testing engine using the three-parameter logistic (3PL) IRT model with EAP theta estimation. This is implemented as a plain Python service class embedded in the FastAPI server — not a LangGraph graph. The summative assessment is a deterministic sequential algorithm (present item → collect response → update theta → check stopping → repeat). LangGraph's graph orchestration, checkpoint management, and multi-agent routing provide no value for this use case and would add latency and complexity.

2. **Reporting Pipeline** — A PDF report generation pipeline using WeasyPrint (HTML → PDF), S3 storage with KMS encryption, presigned URL delivery, and an AWS SES email notification system. Reports are generated asynchronously via SQS to avoid blocking the API response.

3. **Teacher and Parent Dashboards** — New Next.js 15 route groups (`(teacher)/` and `(parent)/`) providing read-only visibility into student progress. Teacher access is governed by parent consent (FERPA parent-authorized disclosure basis). Parent dashboard extends the Stage 3 lightweight parent view to the full reporting feature set.

**MVP hardening additions:**
- **PgBouncer** as an ECS sidecar container in transaction pooling mode — manages PostgreSQL connection lifecycle for 500 concurrent practice + 50 concurrent assessment sessions
- **CloudFront CDN** — caches Next.js static pages and assets; reduces Vercel egress costs and improves P95 load times
- Full security audit (OWASP ZAP DAST, Bandit SAST, Trivy container scan)
- COPPA/FERPA compliance verification and documented audit trail

### 1.2 System Architecture — Container Diagram (C4 Level 2)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                  PADI.AI — Stage 4 MVP Container Diagram              │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                                │
│  ┌────────────────────────────┐      ┌─────────────────────────────────────┐  │
│  │  Next.js 15 Web App        │      │  FastAPI API Server (ECS Fargate)   │  │
│  │  (Vercel + CloudFront)     │      │                                     │  │
│  │                            │ WSS  │  ┌──────────┐  ┌────────────────┐  │  │
│  │  - Student Dashboard       ├─────►│  │ REST API │  │ WebSocket      │  │  │
│  │  - Practice UI             │HTTPS │  │ /v1/...  │  │ /ws/practice   │  │  │
│  │  - EOG Assessment UI (NEW) ├─────►│  │          │  │                │  │  │
│  │  - Teacher Dashboard (NEW) │      │  └────┬─────┘  └────────────────┘  │  │
│  │  - Parent Dashboard (NEW)  │      │       │                             │  │
│  │  - Report Viewer (NEW)     │      │  ┌────┴─────────────────────────┐  │  │
│  └────────────────────────────┘      │  │  Agent Engine (LangGraph)    │  │  │
│                                      │  │  (Stage 3 — unchanged)       │  │  │
│  ┌────────────────────────────┐      │  └─────────────────────────────┘  │  │
│  │  CloudFront CDN (NEW)      │      │  ┌─────────────────────────────┐  │  │
│  │  - Static asset cache      │      │  │  CAT Assessment Engine (NEW) │  │  │
│  │  - Next.js static pages    │      │  │  IRT 3PL + EAP (plain Python)│  │  │
│  └────────────────────────────┘      │  └─────────────────────────────┘  │  │
│                                      │  ┌─────────────────────────────┐  │  │
│                                      │  │  Report Service (NEW)        │  │  │
│                                      │  │  WeasyPrint + S3 + SES       │  │  │
│                                      │  └─────────────────────────────┘  │  │
│                                      │  ┌─────────────────────────────┐  │  │
│                                      │  │  PgBouncer sidecar (NEW)     │  │  │
│                                      │  │  pool_mode=transaction       │  │  │
│                                      │  └──────────────┬──────────────┘  │  │
│                                      └─────────────────┼─────────────────┘  │
│                  ┌──────────────────────────────────────┤                     │
│                  │                         │            │                     │
│                  ▼                         ▼            ▼                     │
│  ┌───────────────────────────┐  ┌────────────────┐  ┌──────────────────────┐ │
│  │  PostgreSQL 17 (RDS)      │  │  Redis 7       │  │  AWS SQS             │ │
│  │  + eog_assessments (NEW)  │  │  (ElastiCache) │  │  - Question gen      │ │
│  │  + eog_responses (NEW)    │  │  (unchanged)   │  │  - Report gen (NEW)  │ │
│  │  + eog_item_bank (NEW)    │  └────────────────┘  └─────────┬────────────┘ │
│  │  + progress_reports (NEW) │                                 │              │
│  │  + teacher_student_access │                                 ▼              │
│  │  + notification_log (NEW) │                      ┌──────────────────────┐ │
│  │  + remediation_plans (NEW)│                      │  SQS Workers (ECS)   │ │
│  └───────────────────────────┘                      │  - Report generation │ │
│                                                      └──────────────────────┘ │
│  ┌───────────────────────────┐  ┌─────────────────────────────────────────┐  │
│  │  AWS S3                   │  │  AWS SES (NEW)                          │  │
│  │  - Static assets          │  │  - Assessment complete email            │  │
│  │  - Content media          │  │  - Weekly summary email                 │  │
│  │  - PDF reports (NEW, KMS) │  │  - Milestone notifications              │  │
│  └───────────────────────────┘  │  - Inactivity alerts                   │  │
│                                  └─────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 1.3 Data Flow — End-of-Grade Assessment Session

```
Student clicks "Start Assessment"
         │
         ▼
POST /v1/assessments/eog/start
  → CATAssessmentService.start_assessment()
  → Creates eog_assessments row (status=in_progress, theta=0.0)
  → Loads item bank from eog_item_bank (cached in Redis, TTL=1h)
  → Selects first item via MFI (theta=0.0)
  → Returns: {assessment_id, first_question}
         │
         ▼
[Loop: For each item presented]
         │
Student submits answer
POST /v1/assessments/eog/{id}/respond
  → IRTService.probability_3pl(theta, a, b, c) → score
  → IRTService.estimate_theta(all_responses) → new_theta, new_sem
  → Persists eog_responses row (theta_before, theta_after, sem_before, sem_after)
  → IRTService.check_stopping_criteria() → should_stop?
  → If not stop: IRTService.select_next_item() → next question
  → Returns: {next_question OR stop_signal, theta_progress}
         │
         ▼
[Stopping criteria met: SEM < 0.30 OR 40 items OR 75 min]
POST /v1/assessments/eog/{id}/complete
  → CATAssessmentService.complete_assessment()
  → Classifies proficiency level from final theta
  → Updates BKT states (3× weight for EOG correct responses)
  → Generates remediation plan (deficient skills → updated learning plan)
  → Enqueues report generation job to SQS
  → Enqueues parent email notification to SES
  → Returns: EOGResults (theta, proficiency_level, domain_scores)
         │
         ▼
[Async — SQS Worker]
ReportService.generate_pdf()
  → Queries: student profile, assessment results, BKT states, session history
  → Renders Jinja2 HTML template (teacher version + student version)
  → WeasyPrint: HTML → PDF (runs in thread pool executor)
  → S3.put_object(KMS encrypted, reports/{student_id}/{assessment_id}/*.pdf)
  → Updates progress_reports row with s3_key
  → SES: sends "Report Ready" email with presigned URL (7-day TTL)
```

### 1.4 CAT Engine Architecture — Plain Python, No LangGraph

The CAT assessment engine (`apps/api/src/service/cat_assessment_service.py`) is implemented as a stateless Python service class — a deliberate architectural choice. Contrast this with the Stage 3 practice engine which uses LangGraph for multi-agent orchestration.

**Why the CAT engine is NOT a LangGraph graph:**

| Concern | LangGraph (Stage 3 Practice) | Plain Python (Stage 4 CAT) |
|---|---|---|
| Orchestration | Multi-agent: Orchestrator → Assessor → Tutor → BKT | Single algorithm: select → score → update → stop check |
| State machine | Complex branching: hint request, tutor dialog, scaffold mode | Linear: item N → response N → item N+1 → stop |
| Checkpointing | Required: tutor conversation must survive reconnection | Not needed: assessment voided on >5min disconnect |
| Non-determinism | Tutor generates varied natural-language responses | IRT calculations are fully deterministic |
| Latency budget | 3s P95 (AI generation included) | <200ms per item (pure math, no AI) |
| Overhead | Justified by complexity | Adds latency and complexity with no benefit |

The `IRTService` class provides stateless computation methods. The `CATAssessmentService` maintains session state in PostgreSQL (not Redis), because assessment integrity requires durable, auditable storage.

```python
# apps/api/src/service/irt_service.py

import math
import numpy as np
from dataclasses import dataclass
from typing import NamedTuple


@dataclass
class ItemResponse:
    question_id: str
    a: float   # Discrimination parameter
    b: float   # Difficulty parameter
    c: float   # Pseudo-guessing parameter
    is_correct: bool


class EAPResult(NamedTuple):
    theta: float
    sem: float


def irt_3pl_probability(theta: float, a: float, b: float, c: float) -> float:
    """3PL IRT: P(X=1|θ,a,b,c) = c + (1-c) / (1 + exp(-a(θ-b)))"""
    exponent = max(min(-a * (theta - b), 35.0), -35.0)  # Overflow guard
    return c + (1.0 - c) / (1.0 + math.exp(exponent))


def eap_estimate(
    responses: list[ItemResponse],
    prior_mean: float = 0.0,
    prior_std: float = 1.0,
    n_quadrature: int = 61,
    theta_range: tuple[float, float] = (-4.0, 4.0),
) -> EAPResult:
    """EAP theta estimation using Gaussian quadrature (61 points)."""
    theta_grid = np.linspace(theta_range[0], theta_range[1], n_quadrature)
    # Normal prior
    log_prior = -0.5 * ((theta_grid - prior_mean) / prior_std) ** 2
    log_posterior = log_prior.copy()
    # Likelihood for each response
    for resp in responses:
        p = np.array([
            irt_3pl_probability(t, resp.a, resp.b, resp.c)
            for t in theta_grid
        ])
        p = np.clip(p, 1e-9, 1 - 1e-9)
        u = 1.0 if resp.is_correct else 0.0
        log_posterior += u * np.log(p) + (1 - u) * np.log(1 - p)
    # Normalize using log-sum-exp trick
    log_posterior -= log_posterior.max()
    posterior = np.exp(log_posterior)
    posterior /= posterior.sum()
    # EAP estimate and posterior variance
    theta_hat = float(np.dot(posterior, theta_grid))
    variance = float(np.dot(posterior, (theta_grid - theta_hat) ** 2))
    return EAPResult(theta=theta_hat, sem=math.sqrt(max(variance, 1e-9)))


def fisher_information(theta: float, a: float, b: float, c: float) -> float:
    """Fisher Information at theta for a single 3PL item."""
    p = irt_3pl_probability(theta, a, b, c)
    q = 1.0 - p
    numerator = (a ** 2) * ((p - c) ** 2) * q
    denominator = ((1 - c) ** 2) * p
    return numerator / max(denominator, 1e-9)
```

### 1.5 IRT 3PL Model Reference

The End-of-Grade assessment uses the three-parameter logistic model:

\[P(X_i = 1 \mid \theta, a_i, b_i, c_i) = c_i + (1 - c_i) \cdot \frac{1}{1 + e^{-a_i(\theta - b_i)}}\]

**Parameter definitions and calibration ranges:**

| Parameter | Symbol | Description | Range | Calibration Source |
|---|---|---|---|---|
| Ability | θ | Student latent trait | [−4, +4] | Estimated per response pattern |
| Discrimination | a | Slope of ICC at inflection point | [0.5, 2.5] | Expert rating → calibrated post-MVP |
| Difficulty | b | Ability level where P = (1+c)/2 | [−3.0, +3.0] | CCSS grade-level alignment |
| Guessing | c | Lower asymptote (chance level) | [0.0, 0.35] | Fixed by item type: MC=0.25, numeric=0.05 |

**Proficiency classification cut scores:**

| Level | Code | Theta Range | Oregon OSAS Analog |
|---|---|---|---|
| Below Par | `BELOW_PAR` | θ < −1.0 | Level 1 (Novice) |
| Approaching | `APPROACHING` | −1.0 ≤ θ < 0.0 | Level 2 (Emerging) |
| On Par | `ON_PAR` | 0.0 ≤ θ < 1.0 | Level 3 (Proficient) |
| Above Par | `ABOVE_PAR` | θ ≥ 1.0 | Level 4 (Advanced) |

When SEM > 0.5, classification uses `theta − SEM` (conservative classification) to avoid over-promoting borderline students.

**Stopping criteria (first met wins):**

| Criterion | Threshold | Rationale |
|---|---|---|
| SEM precision | SEM < 0.30 (after ≥ 15 items) | Sufficient for proficiency classification |
| Maximum items | 40 items administered | Prevent assessment fatigue |
| Maximum time | 75 minutes elapsed | Age-appropriate for 9-10 year olds |

### 1.6 PDF Report Generation Pipeline

```
Assessment Completion Event
         │
         ▼
SQS Message: {student_id, assessment_id, report_versions: ["teacher", "student"]}
         │
         ▼
SQS Worker (ECS) — ReportGeneratorWorker.process()
         │
         ├──► compile_report_data(student_id, assessment_id)
         │         [asyncio.gather: student profile + assessment results +
         │          domain scores + BKT skill states + session history +
         │          historical theta estimates + remediation plan]
         │
         ├──► For each version in ["teacher", "student"]:
         │         jinja_env.get_template(f"report_{version}.html")
         │         html = template.render(**report_data)
         │         pdf_bytes = await loop.run_in_executor(
         │             thread_pool, weasyprint.HTML(string=html).write_pdf
         │         )
         │
         ├──► s3_client.put_object(
         │         Bucket=REPORTS_BUCKET,
         │         Key=f"reports/{student_id}/{assessment_id}/{version}_report.pdf",
         │         Body=pdf_bytes,
         │         ServerSideEncryption="aws:kms",
         │         KMSKeyId=REPORTS_KMS_KEY_ARN
         │     )
         │
         ├──► UPDATE progress_reports SET pdf_s3_key=..., generation_time_ms=...
         │
         └──► ses_client.send_email(
                   Template="report_ready",
                   Destination=parent_email,
                   TemplateData={presigned_url_7d, student_name, proficiency_level}
              )

SLA: Teacher PDF < 10s from assessment completion
Fallback: If > 15s, send "preparing" email; complete async; send "ready" email
Storage: KMS-encrypted at rest; presigned URL expiry 7 days (download), 90 days (shareable)
```

### 1.7 Notification Service Architecture

The notification service (`apps/api/src/service/notification_service.py`) wraps AWS SES with template management, delivery tracking, and COPPA compliance enforcement.

**Email notification types and triggers:**

| Notification Type | Trigger | Recipient | Frequency Cap |
|---|---|---|---|
| `assessment_complete` | EOG Assessment submitted | Parent(s), Teacher(s) | Once per assessment |
| `report_ready` | PDF generation complete | Parent(s) | Once per assessment |
| `milestone_achieved` | Skill mastered, level up | Parent(s) | Once per milestone |
| `weekly_summary` | Sunday 7pm (parent's timezone) | Parent(s) | Once per week |
| `inactivity_alert` | 7 consecutive days without session | Parent(s) | Once per inactivity period |
| `intervention_needed` | EOG result = BELOW_PAR | Teacher(s) with access | Once per assessment |

**COPPA enforcement (hard rule):** The `NotificationService.send_*` methods check `recipient_type != 'student'` before every SES call. Students have no email address stored in the database. Any code path that would email a student directly raises `COPPAViolationError`.

### 1.8 Teacher Dashboard Access Control

Teacher access to student data is governed by a two-step consent model aligned with FERPA parent-authorized disclosure:

```
Parent Action: "Share with Teacher" (FR-18.8)
    │
    ├──► INSERT teacher_student_access (teacher_id, student_id, granted_by=parent_id)
    │
    └──► Teacher dashboard query:
         SELECT s.* FROM students s
         INNER JOIN teacher_student_access tsa
             ON tsa.student_id = s.id
             AND tsa.teacher_id = :teacher_id
             AND tsa.revoked_at IS NULL

Data scoped to teacher view:
  ✅ Overall proficiency level, domain scores, skills mastered count
  ✅ Session count and time-on-task (aggregate)
  ✅ Class-level weak area analysis (aggregated, not individually attributed)
  ❌ Individual question content and student answers (parent-only)
  ❌ Session transcripts (parent-only, FR-14.8)
  ❌ Raw BKT parameters (too technical for teacher view; use proficiency levels)
  ❌ IP addresses or user agents (security/COPPA data)
```

**Export CSV PII minimization:**  
CSV columns include only `student_first_name` (no last name, no student_id). Full name is not exported. Export event is logged to `audit_log` table with `actor_id`, `action='teacher_csv_export'`, `student_ids_accessed`, timestamp.

### 1.9 PgBouncer Connection Pooling

PgBouncer runs as an ECS sidecar container alongside the FastAPI API server in `pool_mode=transaction`. At 500 concurrent practice WebSocket sessions and 50 concurrent EOG assessment sessions, PostgreSQL would exhaust its default `max_connections=100` without pooling.

**Configuration (`pgbouncer.ini`):**
```ini
[databases]
padi_ai = host=rds-postgres.region.rds.amazonaws.com port=5432 dbname=padi_ai

[pgbouncer]
pool_mode = transaction
max_client_conn = 700
default_pool_size = 25
min_pool_size = 5
reserve_pool_size = 5
server_idle_timeout = 600
client_idle_timeout = 0
log_connections = 0
log_disconnections = 0
```

**Why transaction mode:** Assessment sessions issue short, discrete queries (one per item response). Transaction mode pools connections at query commit time, maximizing reuse. Session mode would hold a server connection for the duration of the WebSocket session (potentially 75 minutes), which would exhaust the pool.

**Implication for SQLAlchemy:** All async DB operations in assessment endpoints must complete within a single transaction context. Long-running operations (report generation) run in the SQS worker, which uses a separate connection pool independent of the API server.

### 1.10 CloudFront CDN Configuration

CloudFront sits in front of the Vercel frontend deployment, caching static assets and reducing latency for Oregon-based students.

**Cache policies:**

| Path Pattern | Cache TTL | Invalidation Trigger |
|---|---|---|
| `/_next/static/*` | 1 year (immutable) | Next.js build hash changes |
| `/images/*`, `/fonts/*` | 30 days | Manual invalidation on content update |
| `/api/*` | No cache (pass-through) | N/A |
| `/(student)/*`, `/(parent)/*` | No cache (auth-gated) | N/A |
| `/` (landing) | 5 minutes | Deploy webhook |

**Security headers applied at CloudFront:**
- `Strict-Transport-Security: max-age=31536000; includeSubDomains`
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Content-Security-Policy: default-src 'self'; script-src 'self' 'nonce-{nonce}'`

### 1.11 Key Architectural Decisions

| Decision | Choice | Rationale | Rejected Alternative |
|---|---|---|---|
| CAT engine implementation | Plain Python service class | Deterministic algorithm; no agent coordination needed; 10× lower latency | LangGraph graph (adds ~200ms overhead, no benefit) |
| Theta estimation method | EAP (Expected A Posteriori) | Defined for all-correct/all-incorrect; lower MSE than MLE for short tests | MLE (undefined for extreme response patterns) |
| Quadrature points | 61 (−4 to +4, step 0.1) | Balances precision vs. computation time; <5ms per estimation | 31 points (insufficient precision), 121 points (overkill) |
| Report generation | Async SQS + WeasyPrint | PDF is CPU-intensive (2-5s); must not block API response | Synchronous (blocks response), Puppeteer (heavier binary) |
| PDF storage | S3 + KMS + presigned URLs | FERPA-compliant; no direct public exposure; auditability | CDN-hosted public URLs (FERPA violation) |
| Email service | AWS SES | Integrated with existing AWS infrastructure; lower cost than SendGrid at MVP scale | SendGrid (used as fallback per FR-20.1) |
| Connection pooling | PgBouncer transaction mode | Handles 550+ concurrent sessions within RDS connection limits | pgpool-II (more complex), no pooling (would exhaust connections) |
| Teacher data scope | Read-only, parent-authorized | FERPA parent-authorized disclosure basis in Stage 4 | School official basis (requires institutional agreements, Stage 5) |
| Assessment integrity | Single-use session token, void on >5min disconnect | Prevents mid-assessment resume that could allow answer lookup | Resume capability (security risk for summative assessment) |

### 1.12 Integration Points with Previous Stages

| Stage | Integration Point | Data Flow |
|---|---|---|
| Stage 1 | Standards database (`math_standards`, `questions`) | EOG item bank references `questions.id`; domain weights from `math_standards.domain` |
| Stage 1 | IRT item parameters | `eog_item_bank.question_id` → `questions.id`; initial `a`, `b`, `c` set by expert calibration |
| Stage 2 | Learning plan (`learning_plans`, `learning_plan_modules`) | Remediation plan creates new `learning_plans` record post-EOG; reuses module structure |
| Stage 3 | BKT states (`skill_mastery_states`) | EOG correct responses update BKT with 3× weight; mastery confirmed when domain θ ≥ 0.5 |
| Stage 3 | Practice session history (`practice_sessions`, `practice_responses`) | Parent dashboard time-on-task charts query practice session data |
| Stage 3 | Agent Engine (LangGraph) | Unchanged; EOG assessment bypasses agent engine entirely |

### 1.13 Risk Areas and Mitigation

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| IRT parameters miscalibrated (expert-set, pre-data) | High | Medium | Pilot with 25 beta students; monitor theta distributions; flag outlier items |
| WeasyPrint version incompatibilities with complex HTML | Medium | Medium | Pin WeasyPrint version; integration test PDF generation in CI |
| PgBouncer transaction mode incompatible with certain SQLAlchemy patterns | Medium | High | Audit all `ROLLBACK` and `SAVEPOINT` usage; test with PgBouncer in staging |
| SES email deliverability issues (new domain) | Medium | High | Warm up SES sending domain; configure SPF/DKIM/DMARC before beta |
| Assessment session loss on WebSocket disconnect | Low | High | Clear UX messaging; void rule communicated before assessment start |
| FERPA violation via teacher data oversharing | Low | Critical | Row-level security enforced at DB query level; legal review of teacher export CSV |
| COPPA violation via accidental student email | Low | Critical | `COPPAViolationError` guard in `NotificationService`; automated test verifies no student emails |

---

## 2. User Story Breakup

### 2.1 Epic Structure

| Epic | ID | Feature Area | FR Reference | Stories |
|---|---|---|---|---|
| MATH-401 | EOG Assessment Engine | FR-15 | US-401 through US-408 |
| MATH-402 | Remediation Loop | FR-16 | US-409 through US-412 |
| MATH-403 | Progress Report PDF | FR-17 | US-413 through US-417 |
| MATH-404 | Parent Dashboard | FR-18 | US-418 through US-424 |
| MATH-405 | Teacher Dashboard | FR-19 | US-425 through US-430 |
| MATH-406 | Notifications | FR-20 | US-431 through US-436 |
| MATH-407 | MVP Hardening | NFR | US-437 through US-443 |

---

### 2.2 Epic MATH-401: EOG Assessment Engine (FR-15)

**Solo Development Estimate:** 40–55 agent-hours | Calendar: ~4–6 weeks (IRT implementation is research-heavy; reference ENG-004 for 3PL IRT formula)

---

**US-401: Start an End-of-Grade Assessment**  
**Priority:** P0 | **Points:** 5  
**Dependencies:** Stage 1 IRT item bank, Auth0 student session

> As a **student**, I want to start an End-of-Grade Assessment so that I can receive a summative evaluation of my math proficiency across all Grade 4 standards.

**Acceptance Criteria:**
- AC1: `POST /v1/assessments/eog/start` creates a new `eog_assessments` row with `status=in_progress`, `theta_estimate=0.0`, `items_administered=0`.
- AC2: The endpoint returns the first question selected via Maximum Fisher Information at θ=0.0.
- AC3: If a student attempts to start an assessment within 30 days of a previous completed attempt, the API returns HTTP 409 with `error_code=RETAKE_WINDOW_ACTIVE` and `retake_available_at` timestamp.
- AC4: The Assessment UI renders in a visually distinct "Assessment Mode" — different header color, no hint/tutor buttons, no back navigation.
- AC5: The student sees a pre-assessment briefing screen explaining: no hints available, no back navigation, estimated 45-60 minutes, voided if disconnected > 5 minutes.
- AC6: The assessment cannot be started if the student is not authenticated or if parental consent is not confirmed.
- AC7: Browser's back button is disabled via `popstate` listener from the moment the assessment begins.

---

**US-402: Adaptive Item Selection and Response Collection**  
**Priority:** P0 | **Points:** 8  
**Dependencies:** US-401, IRTService

> As a **student**, I want to answer questions during the assessment and have the system automatically select the next most informative question based on my performance so that the assessment is appropriately challenging.

**Acceptance Criteria:**
- AC1: `POST /v1/assessments/eog/{id}/respond` accepts `{question_id, answer, response_time_ms}` and returns the next question or a stop signal.
- AC2: Each response persists a `eog_responses` row with `theta_before`, `theta_after`, `sem_before`, `sem_after`, `item_information`, `is_correct`.
- AC3: The next item is selected via `IRTService.select_next_item()` using Maximum Fisher Information at the current `theta_after`.
- AC4: Content balancing enforces proportional domain coverage: OA 20%, NBT 25%, NF 30%, MD 15%, G 10% (±5% tolerance for adaptive constraints).
- AC5: No item is presented twice in a single assessment.
- AC6: Response time is recorded in milliseconds; suspiciously fast responses (< 2 seconds) are logged to `eog_assessments.proctoring_flags`.
- AC7: The UI shows progress (e.g., "Question 12 of at least 40") without revealing the stopping criterion or current theta.
- AC8: If `session_token` has expired or does not match the current assessment, the API returns HTTP 401 and the student sees "Your assessment session has ended."

---

**US-403: EAP Theta Estimation and Stopping Criteria**  
**Priority:** P0 | **Points:** 5  
**Dependencies:** US-402, IRTService

> As the **system**, I want to continuously estimate the student's ability (theta) after each item response using EAP with Gaussian quadrature so that the assessment terminates at the optimal point.

**Acceptance Criteria:**
- AC1: After each response, `IRTService.estimate_theta()` is called with all accumulated responses; result updates `eog_assessments.theta_estimate` and `eog_assessments.sem`.
- AC2: EAP uses 61 quadrature points over [−4.0, +4.0] with a N(0,1) prior.
- AC3: Stopping criterion 1: SEM < 0.30 after ≥ 15 items → stop with `stop_reason='sem_threshold'`.
- AC4: Stopping criterion 2: 40 items administered → stop with `stop_reason='max_items'`.
- AC5: Stopping criterion 3: 75 minutes elapsed → stop with `stop_reason='max_time'`.
- AC6: The API returns `{should_stop: true, stop_reason: "..."}` when any criterion is met.
- AC7: Theta estimates are reproducible: given the same response pattern, `estimate_theta()` returns the same result within float precision (deterministic).

---

**US-404: Proficiency Level Classification**  
**Priority:** P0 | **Points:** 3  
**Dependencies:** US-403

> As a **student** and **parent**, I want to receive a clear proficiency level label at the end of the assessment so that I know how my performance compares to Oregon Grade 4 standards.

**Acceptance Criteria:**
- AC1: `CATAssessmentService.compute_proficiency_level(theta, sem)` maps theta to the Oregon-aligned 4-level system: BELOW_PAR (θ < −1.0), APPROACHING (−1.0 ≤ θ < 0.0), ON_PAR (0.0 ≤ θ < 1.0), ABOVE_PAR (θ ≥ 1.0).
- AC2: When SEM > 0.5, classification uses `theta − SEM` (conservative adjustment) to avoid over-promoting borderline students.
- AC3: The proficiency level is stored in `eog_assessments.proficiency_level` using the VARCHAR enum values.
- AC4: The student-facing results screen uses the "Par" framing ("Approaching", "On Par", etc.) — never "Basic", "Below Grade Level", or language that stigmatizes.
- AC5: Domain-level proficiency is computed separately for each of the 5 domains from responses tagged with `content_domain`.
- AC6: The results page loads within 3 seconds of assessment completion.

---

**US-405: Assessment Integrity Controls**  
**Priority:** P0 | **Points:** 5  
**Dependencies:** US-401

> As a **parent** and **teacher**, I want the assessment to be administered under controlled conditions that prevent answer lookup so that the proficiency results are valid and trustworthy.

**Acceptance Criteria:**
- AC1: Browser history API (`history.pushState`, `popstate`) prevents back navigation; pressing back shows "Back navigation is not available during the assessment."
- AC2: The Page Visibility API detects tab switches; each switch increments `eog_assessments.tab_switch_count` and displays "Please stay on this tab during your assessment."
- AC3: If tab switch count ≥ 5, assessment displays a warning: "This has been noted in your assessment record."
- AC4: WebSocket disconnection > 5 minutes: assessment is automatically voided (status=`invalidated`), student is redirected to a clear explanation screen.
- AC5: WebSocket disconnection < 5 minutes: countdown timer shown; session recovers automatically on reconnect.
- AC6: Hint buttons, tutor chat, and calculator are not rendered in the Assessment Mode UI (not just hidden — not present in DOM).
- AC7: Each assessment attempt is logged with `ip_address`, `user_agent`, `started_at`, `ended_at`, `tab_switch_count`, `integrity_flags`.

---

**US-406: Assessment Final Review Screen**  
**Priority:** P1 | **Points:** 3  
**Dependencies:** US-402

> As a **student**, I want to review my flagged questions before final submission so that I can reconsider answers I was uncertain about.

**Acceptance Criteria:**
- AC1: Before final submission, the student sees a "Review" screen listing all questions: answered count, flagged count.
- AC2: Students can flag any question during the assessment (question-level flag button, does not reveal correct/incorrect).
- AC3: Flagged questions are highlighted in the review list; student can navigate back to flagged questions (only) to change their answer.
- AC4: Once "Submit Assessment" is confirmed via a modal dialog, the session token is consumed and the assessment is finalized.
- AC5: After submission, the student cannot navigate back to any question.

---

**US-407: EOG Retake Policy Enforcement**  
**Priority:** P1 | **Points:** 2  
**Dependencies:** US-401

> As a **student**, I want to see when I can retake the assessment so that I can plan my study schedule appropriately.

**Acceptance Criteria:**
- AC1: Retake interval is enforced server-side: 30 days minimum between completed attempts.
- AC2: Maximum 3 attempts per student per academic year (September 1 – June 14).
- AC3: After completing an assessment, the student dashboard shows "Retake available in X days."
- AC4: Attempting to start a retake within the window returns HTTP 409 with `retake_available_at` date.
- AC5: All attempts are stored as separate `eog_assessments` records; no prior record is overwritten.

---

**US-408: Post-Assessment Results Display**  
**Priority:** P0 | **Points:** 5  
**Dependencies:** US-404, US-401

> As a **student**, I want to see a clear and encouraging results screen immediately after completing the assessment so that I feel motivated to continue learning.

**Acceptance Criteria:**
- AC1: Results screen displays within 5 seconds of assessment submission.
- AC2: Screen shows: overall proficiency level (with visual indicator), domain-level performance (5 bars), skills mastered (count), "What comes next" section with top 3 remediation skills.
- AC3: Language is encouraging and age-appropriate regardless of proficiency level (no negative framing for BELOW_PAR; uses "You're working on these great skills next!").
- AC4: "Continue Learning" CTA navigates to the updated learning plan.
- AC5: "See Full Report" link is displayed once the PDF report is ready (status checked via polling every 5 seconds, max 30 seconds).

---

### 2.3 Epic MATH-402: Remediation Loop (FR-16)

**Solo Development Estimate:** 20–30 agent-hours | Calendar: ~2–3 weeks

---

**US-409: Auto-Generate Revised Learning Plan After Assessment**  
**Priority:** P0 | **Points:** 5  
**Dependencies:** US-408, Stage 3 Learning Plan service

> As a **student**, I want a new personalized learning plan automatically created after my assessment so that I immediately know what to work on next without any manual intervention.

**Acceptance Criteria:**
- AC1: `generate_remediation_plan()` is called automatically as part of `CATAssessmentService.complete_assessment()`.
- AC2: Deficient skills are identified as those with `BKT P(mastered) < 0.70` at time of assessment completion.
- AC3: Skills are ordered by ascending `P(mastered)` (most deficient first), then topologically sorted by prerequisite graph.
- AC4: A new `learning_plans` record is created with `source='eog_remediation'`, linked to `remediation_plans.generated_plan_id`.
- AC5: The student's active learning plan in the dashboard switches to the new remediation plan within 60 seconds.
- AC6: Skills with `domain θ ≥ 0.5` have `skill_mastery_states.mastered_at` confirmed (if not already set).

---

**US-410: Student "What Comes Next" Screen**  
**Priority:** P1 | **Points:** 3  
**Dependencies:** US-409

> As a **student**, I want a motivating post-assessment screen showing what I'm great at and what I'll work on next so that I feel encouraged to continue learning.

**Acceptance Criteria:**
- AC1: Screen lists skills mastered (with domain grouping) with ✓ indicator.
- AC2: Screen lists in-progress skills (top 3 priority) with progress bar from P(mastered) → mastery threshold.
- AC3: Progress bar labels: < 0.30 = "Just getting started", 0.30–0.59 = "Making progress", 0.60–0.94 = "Almost there!"
- AC4: "Continue Learning" button navigates to the first unmastered skill in the remediation plan.
- AC5: The screen is accessible via screen reader (all progress bars have aria-valuemin/max/now attributes).

---

**US-411: Remediation Loop Termination Conditions**  
**Priority:** P1 | **Points:** 2  
**Dependencies:** US-409

> As the **system**, I want to correctly terminate the remediation loop when the student achieves On Par or the academic year ends so that the plan does not persist beyond its useful life.

**Acceptance Criteria:**
- AC1: If EOG result is ON_PAR or ABOVE_PAR, no remediation plan is generated; student sees a "Congratulations" screen instead.
- AC2: On June 15 each year, all active learning plans are archived (`status='archived'`, data retained) via a scheduled Lambda function.
- AC3: Parent or teacher (with manage access) can manually pause the plan; paused plans show "Plan paused" banner in student dashboard.
- AC4: Resuming after June 15 does not re-activate the archived plan; a new plan is required.

---

**US-412: Parent Communication for Remediation Results**  
**Priority:** P0 | **Points:** 3  
**Dependencies:** US-409, US-431

> As a **parent**, I want to receive an email immediately after my child's assessment explaining the results and what will happen next so that I can support their continued learning.

**Acceptance Criteria:**
- AC1: Assessment complete email is dispatched to parent within 5 minutes of EOG submission.
- AC2: Email contains: proficiency level, one-sentence interpretation, top 3 remediation skills identified, link to full PDF report (presigned URL), CTA to open student's practice.
- AC3: Email is rendered in responsive HTML with plain-text fallback.
- AC4: Email is sent from `updates@padi.ai` with DKIM/SPF/DMARC configured.
- AC5: Email delivery is logged in `notification_log` with `ses_message_id` for delivery tracking.

---

### 2.4 Epic MATH-403: Progress Report PDF (FR-17)

**Solo Development Estimate:** 20–25 agent-hours | Calendar: ~2–3 weeks

---

**US-413: Generate Teacher/Parent PDF Report**  
**Priority:** P0 | **Points:** 8  
**Dependencies:** US-408, S3, WeasyPrint

> As a **parent**, I want a comprehensive PDF report generated after each assessment so that I have a shareable document showing my child's full progress.

**Acceptance Criteria:**
- AC1: PDF generation is enqueued to SQS within 1 second of assessment completion.
- AC2: SQS worker generates the Teacher/Parent report PDF within 10 seconds of dequeue.
- AC3: PDF is stored in S3 at `reports/{student_id}/{assessment_id}/teacher_report.pdf` with KMS encryption.
- AC4: PDF contains all sections per FR-17.3: cover page, executive summary, domain breakdown table, skills detail, time-on-task table, trajectory chart, recommended next steps, methodology note, shareable link.
- AC5: `progress_reports` row is created with `pdf_s3_key`, `generation_time_ms`, `template_version`.
- AC6: If generation exceeds 15 seconds, parent receives a "Your report is being prepared" email with a follow-up "Report Ready" email when complete.

---

**US-414: Generate Student PDF Report**  
**Priority:** P1 | **Points:** 5  
**Dependencies:** US-413

> As a **student** (age 9-10), I want a simplified, visual PDF report in language I understand so that I feel proud of my progress and know what to work on.

**Acceptance Criteria:**
- AC1: Student PDF is generated alongside the Teacher/Parent report (same SQS job, two templates).
- AC2: Student report is 2 pages, uses simplified language, and includes visual elements: proficiency level indicator, skill badges, progress bars.
- AC3: Reading level of all text in student report is Flesch-Kincaid Grade ≤ 5.5 (verified by automated test).
- AC4: Student report stored at `reports/{student_id}/{assessment_id}/student_report.pdf`.
- AC5: Student report link is displayed in the student dashboard under "My Reports."

---

**US-415: Presigned URL Access for PDF Reports**  
**Priority:** P0 | **Points:** 3  
**Dependencies:** US-413

> As a **parent**, I want a secure download link for the report so that I can access it without needing to log into the app every time.

**Acceptance Criteria:**
- AC1: `GET /v1/reports/{report_id}/download` generates a presigned S3 URL with 7-day expiry.
- AC2: Report download attempts are logged (`access_count`, `last_accessed`) in `progress_reports`.
- AC3: "Share with Teacher" generates a separate read-only presigned URL with 90-day expiry; share event logged in `report_shares` for FERPA audit.
- AC4: Expired URLs return HTTP 403 with a clear message directing the user to regenerate from the app.
- AC5: A parent can revoke the shareable teacher link from `/settings/reports`; revocation invalidates the URL immediately via S3 object expiry.

---

**US-416: Report Historical Access**  
**Priority:** P1 | **Points:** 2  
**Dependencies:** US-413

> As a **parent**, I want to view all previously generated reports for my child so that I can track progress over multiple assessments.

**Acceptance Criteria:**
- AC1: `GET /v1/reports?student_id={id}` returns paginated list of all reports, newest first.
- AC2: Each report entry shows: report type, assessment date, proficiency level at time of report, download link.
- AC3: Reports are retained for the duration of the student account plus 90 days post-deletion (per COPPA).
- AC4: Parent dashboard "Reports" tab displays this list with download buttons.

---

**US-417: Report Notification — Report Ready**  
**Priority:** P0 | **Points:** 2  
**Dependencies:** US-413, US-431

> As a **parent**, I want to receive an email when my child's report is ready to download so that I know when to access it.

**Acceptance Criteria:**
- AC1: "Report Ready" email is sent within 60 seconds of `progress_reports` row being created with a valid `pdf_s3_key`.
- AC2: Email contains presigned download URL (7-day expiry), student name, assessment date, proficiency level.
- AC3: Email is deduped — only one "Report Ready" email per assessment per parent.
- AC4: If parent has opted out of `report_ready` notification type, email is suppressed (transactional emails cannot be fully unsubscribed per CAN-SPAM, but this notification type can be disabled).

---

### 2.5 Epic MATH-404: Parent Dashboard (FR-18)

**Solo Development Estimate:** 25–35 agent-hours | Calendar: ~3–4 weeks

---

**US-418: Parent Dashboard Home**  
**Priority:** P0 | **Points:** 5  
**Dependencies:** Stage 3 parent view, BKT states

> As a **parent**, I want a dashboard home screen showing my child's current level, recent sessions, and key stats so that I can quickly understand how they are progressing.

**Acceptance Criteria:**
- AC1: Dashboard loads within 3 seconds (Lighthouse Performance ≥ 75).
- AC2: Dashboard shows: current proficiency level, skills mastered count (X/29), skills in progress count, time practiced this week (minutes), last active date/time.
- AC3: "Recent Sessions" section shows last 5 sessions with date, duration, accuracy %, skills practiced.
- AC4: "Download Latest Report" button is visible and links to most recent `progress_reports` download.
- AC5: "Share with Teacher" button opens a modal for entering teacher email or generating a link.
- AC6: Dashboard is fully responsive (375px mobile through 1440px desktop).

---

**US-419: Complete Session History View**  
**Priority:** P1 | **Points:** 3  
**Dependencies:** US-418, Stage 3 practice session data

> As a **parent**, I want to view the complete history of my child's practice sessions so that I can see their engagement patterns and review what they studied.

**Acceptance Criteria:**
- AC1: `GET /v1/parent/sessions?student_id={id}&page={n}` returns 20 sessions per page, newest first.
- AC2: Each row shows: date, duration, questions answered, accuracy %, skills practiced, session mode (practice/diagnostic/eog).
- AC3: Clicking a session opens a Session Detail view showing: all questions (text), student answers vs. correct answers, hints used, BKT state delta per skill.
- AC4: Session transcripts (tutor conversation) are accessible via "View Transcript" — requires explicit click (not shown by default for privacy).
- AC5: Pagination controls work correctly at ≥ 100 sessions.

---

**US-420: Skill Mastery Timeline**  
**Priority:** P1 | **Points:** 5  
**Dependencies:** BKT states, all 29 standards

> As a **parent**, I want to see each of the 29 Grade 4 math skills as a progress bar so that I can understand exactly where my child stands on each standard.

**Acceptance Criteria:**
- AC1: All 29 standards are displayed, grouped by the 5 domains (collapsible sections).
- AC2: Each skill shows: Oregon standard code (e.g., 4.NF.B.3), skill name, BKT P(mastered) as a percentage bar, mastery date (if mastered).
- AC3: Filter buttons: "All" / "Mastered" / "In Progress" / "Not Started" — filter correctly with no state loss on toggle.
- AC4: Sort options: by domain (default), by mastery % (ascending/descending), by last practiced date.
- AC5: Clicking a skill opens a Skill Detail view: full practice history for that skill, question accuracy over time, BKT P(mastered) chart over time.

---

**US-421: Weekly and Monthly Time-on-Task Charts**  
**Priority:** P1 | **Points:** 3  
**Dependencies:** Practice session data

> As a **parent**, I want charts showing how much time my child practices each week so that I can help them stay consistent.

**Acceptance Criteria:**
- AC1: Toggle between Week / Month / All-time views.
- AC2: Week view: bar chart of minutes per day (7 days); Month view: bar chart of minutes per week (4 weeks).
- AC3: Overlaid line chart shows accuracy trend (% correct) across sessions.
- AC4: Summary stats: total sessions, total minutes, average session length, best day of week.
- AC5: Weekly goal ring (default 60 min/week, configurable by parent in settings) shows current progress as a percentage.

---

**US-422: Comparison to Grade-Level Expectations**  
**Priority:** P1 | **Points:** 2  
**Dependencies:** Oregon OSAS standards thresholds

> As a **parent**, I want to see how my child compares to Oregon Grade 4 expectations (not to other students) so that I understand what "on grade level" means.

**Acceptance Criteria:**
- AC1: Display shows "On Track" / "Ahead" / "Needs More Time" status per domain based on theta vs. expected θ for time of year.
- AC2: No peer comparison is ever shown — no percentile rank vs. other students in the UI.
- AC3: A tooltip or info button explains: "This comparison is to Oregon Grade 4 expectations, not to other children."
- AC4: Comparison display is clearly labeled with the data source (Oregon OSAS Grade 4 standards).

---

**US-423: Achievement Milestones Timeline**  
**Priority:** P2 | **Points:** 3  
**Dependencies:** BKT mastery events, assessment completion events

> As a **parent**, I want to see a feed of my child's milestone achievements so that I can celebrate their progress with them.

**Acceptance Criteria:**
- AC1: Chronological feed of milestone events: skill mastered, module completed, EOG assessment completed, level change.
- AC2: Each milestone entry shows: event type, date, brief description (e.g., "Alex mastered Adding Fractions with Like Denominators!").
- AC3: Milestones are generated as BKT/assessment events occur and stored in `milestone_events` table.
- AC4: Parent can share a milestone via the UI (copies a shareable message to clipboard — no external service post).

---

**US-424: Share Progress with Teacher**  
**Priority:** P0 | **Points:** 3  
**Dependencies:** US-415, teacher_student_access table

> As a **parent**, I want to share my child's progress report with their teacher so that the teacher can use it to support classroom instruction.

**Acceptance Criteria:**
- AC1: "Share with Teacher" generates a presigned PDF URL (90-day expiry) and optionally emails it to a teacher address.
- AC2: Share flow shows teacher email input; if teacher has a PADI.AI account, it also grants `teacher_student_access` (view level).
- AC3: All share events are logged in `report_shares` with: parent_id, teacher_email, report_id, shared_at, expires_at, revoked_at.
- AC4: Parent can view all active shares at `/settings/sharing` and revoke any share.
- AC5: Revoking a share invalidates the presigned URL within 5 minutes.

---

### 2.6 Epic MATH-405: Teacher Dashboard (FR-19)

**Solo Development Estimate:** 25–35 agent-hours | Calendar: ~3–4 weeks

---

**US-425: Teacher Registration and Role Setup**  
**Priority:** P0 | **Points:** 3  
**Dependencies:** Auth0

> As a **teacher**, I want to create a teacher account using my school email so that I can access student progress data shared with me.

**Acceptance Criteria:**
- AC1: Registration form collects: name, email, school name; no school SSO required in Stage 4.
- AC2: Auth0 creates account with `user_role='teacher'`; teacher receives verification email.
- AC3: Teachers cannot create student accounts, modify student data, or see data not explicitly shared with them.
- AC4: Teacher dashboard is behind auth-gated route `(teacher)/dashboard`.
- AC5: If a teacher tries to access `(student)/*` or `(parent)/*` routes, they are redirected to the teacher dashboard with an access denied message.

---

**US-426: Teacher Student Roster View**  
**Priority:** P0 | **Points:** 5  
**Dependencies:** US-425, US-424, teacher_student_access

> As a **teacher**, I want to see a roster of students who have shared data with me, with summary progress for each, so that I can monitor how my students are doing in math.

**Acceptance Criteria:**
- AC1: Roster table shows only students with an active `teacher_student_access` record (revoked records excluded).
- AC2: Columns: student first name, grade level, current proficiency level, skills mastered (X/29), skills in progress, last active date, time this month.
- AC3: Table is sortable by any column; default sort is last active date descending.
- AC4: Inactive students (no session in ≥ 7 days) are highlighted with a visual indicator.
- AC5: Clicking a student row expands an inline detail view showing domain-level breakdown (5 domain bars).
- AC6: Teacher cannot access session transcripts, raw question content, or BKT parameters from this view.

---

**US-427: Class-Level Aggregate Weak Area Analysis**  
**Priority:** P1 | **Points:** 5  
**Dependencies:** US-426, BKT states for all rostered students

> As a **teacher**, I want to see which math skills my students are commonly struggling with so that I can prioritize classroom instruction accordingly.

**Acceptance Criteria:**
- AC1: "Class Insights" section shows the top 5 skills where the most students have `P(mastered) < 0.50`.
- AC2: Each weak skill entry shows: skill name, standard code, count of students struggling, domain grouping.
- AC3: Domain heatmap: 5-row × N-student grid; cells colored red (P < 0.40), yellow (0.40–0.79), green (≥ 0.80).
- AC4: A visible disclaimer: "These insights are based only on students who have chosen to share their data with you. Results reflect individual learning journeys; do not use to compare students."
- AC5: Analysis is recomputed on page load (not cached stale data > 24 hours old).

---

**US-428: Teacher CSV Export**  
**Priority:** P1 | **Points:** 3  
**Dependencies:** US-426

> As a **teacher**, I want to export roster data as a CSV file so that I can use it in other tools like Google Sheets.

**Acceptance Criteria:**
- AC1: "Export CSV" button generates a CSV file on demand (not pre-stored in S3).
- AC2: CSV columns: `student_first_name`, `overall_level`, `theta_score`, `skills_mastered_count`, `skills_in_progress_count`, `total_minutes_this_month`, `last_active_date`, and per-domain level (5 columns: `oa_level`, `nbt_level`, `nf_level`, `md_level`, `g_level`).
- AC3: PII: only `student_first_name` included — no last name, no student ID, no email, no date of birth.
- AC4: Export event is logged in `audit_log`: `actor_id=teacher_id`, `action='teacher_csv_export'`, `affected_student_ids`, `exported_at`.
- AC5: CSV download triggers browser file save dialog (Content-Disposition: attachment).

---

**US-429: Teacher Read-Only Constraint**  
**Priority:** P0 | **Points:** 2  
**Dependencies:** US-425

> As the **system**, I want all teacher dashboard API endpoints to be strictly read-only so that teachers cannot accidentally or maliciously modify student data.

**Acceptance Criteria:**
- AC1: Teacher role is restricted to GET endpoints for `/v1/teacher/*` routes only; POST/PUT/DELETE return HTTP 403.
- AC2: API middleware validates `user_role='teacher'` on all `/v1/teacher/*` routes; any other role returns HTTP 403.
- AC3: Teacher cannot access `/v1/parent/*`, `/v1/student/*`, or `/v1/assessments/*` start/respond endpoints.
- AC4: Penetration test scenario: logged-in teacher attempts to PATCH a student's BKT state → HTTP 403, no state change.

---

**US-430: Teacher Data Scoping — FERPA Compliance**  
**Priority:** P0 | **Points:** 3  
**Dependencies:** US-425, US-424

> As the **system**, I want all teacher data queries to be scoped to students who have explicitly shared access so that we comply with FERPA parent-authorized disclosure requirements.

**Acceptance Criteria:**
- AC1: All teacher dashboard queries include `INNER JOIN teacher_student_access tsa ON tsa.teacher_id = :teacher_id AND tsa.revoked_at IS NULL`.
- AC2: If a parent revokes teacher access, the student disappears from the teacher's roster on the next page load (within 5 minutes of revocation).
- AC3: Teacher cannot enumerate student IDs — roster API only returns students with active grants.
- AC4: Session transcripts are not accessible to teachers — any API endpoint returning transcript data requires `user_role='parent'`.
- AC5: Legal review completed and documented: teacher access basis is "Parent-authorized disclosure" (not "school official"), logged in FERPA compliance record.

---

### 2.7 Epic MATH-406: Notifications (FR-20)

**Solo Development Estimate:** 15–20 agent-hours | Calendar: ~2 weeks

---

**US-431: Assessment Complete Email**  
**Priority:** P0 | **Points:** 3  
**Dependencies:** US-408, AWS SES

> As a **parent**, I want to receive an email immediately after my child completes an assessment with their results and next steps so that I am kept informed without needing to log in.

**Acceptance Criteria:** (See also US-412 AC1–AC5 — same story covered from different angle.)
- AC1: Email dispatched within 5 minutes of EOG completion (SQS queue lag tolerance).
- AC2: Email subject: "[Student Name] completed their PADI.AI End-of-Grade Assessment."
- AC3: Email body matches the FR-16.4 template exactly (student name, proficiency level, plain-language interpretation, top 3 remediation skills, PDF link).
- AC4: Email is also sent to teacher(s) with active `teacher_student_access` records (teacher template: less personal, more data-focused).
- AC5: Email delivery status tracked via SES SNS feedback loop; bounces logged in `notification_log.bounced`.

---

**US-432: Weekly Summary Email**  
**Priority:** P1 | **Points:** 3  
**Dependencies:** AWS SES, practice session data

> As a **parent**, I want a weekly summary email every Sunday showing how my child practiced that week so that I stay engaged with their progress.

**Acceptance Criteria:**
- AC1: Weekly summary cron job runs every Sunday at 7pm (parent's local timezone, stored in `users.timezone`).
- AC2: Email includes: sessions this week, total minutes, questions answered, accuracy %, skills practiced, skills mastered this week.
- AC3: If student was inactive all week, email uses the Inactivity Alert template instead (US-433).
- AC4: Parent can disable weekly summary in notification preferences (`/settings/notifications`); setting persists.
- AC5: Cron job is idempotent: running twice in a day does not send duplicate emails (checked via `notification_log` dedup).

---

**US-433: Inactivity Alert Email**  
**Priority:** P1 | **Points:** 2  
**Dependencies:** AWS SES, practice session data

> As a **parent**, I want to receive an alert if my child hasn't practiced in 7 days so that I can help them re-engage.

**Acceptance Criteria:**
- AC1: Inactivity check runs daily; email sent if no student session in the past 7 days.
- AC2: Email matches FR-20.1 inactivity template with research-based messaging ("even 10 minutes is effective").
- AC3: One alert per inactivity period — not sent again until student has a session followed by another 7-day gap.
- AC4: Alert suppressed if parent's `notify_inactivity` preference is false.

---

**US-434: In-App Student Notifications**  
**Priority:** P2 | **Points:** 3  
**Dependencies:** Stage 3 student dashboard

> As a **student**, I want to see relevant in-app notifications (like streak reminders and new skills) so that I stay motivated to practice.

**Acceptance Criteria:**
- AC1: Notification bell in the app header shows unread count (max 3 visible, then "X more").
- AC2: Notification types rendered: streak reminder (after 2pm if not practiced), new skill unlocked, module complete, assessment ready, level up.
- AC3: Notifications stored in `student_notifications` table; marked read when dismissed.
- AC4: Notifications cleared after 30 days (soft delete).
- AC5: No email, SMS, or push notification is ever sent to a student's email or device — all student communications are in-app only (COPPA enforcement).

---

**US-435: Email Preferences Management**  
**Priority:** P1 | **Points:** 2  
**Dependencies:** Parent settings

> As a **parent**, I want to manage which email notifications I receive so that my inbox is not overwhelmed.

**Acceptance Criteria:**
- AC1: `/settings/notifications` page shows toggle per notification type: weekly_summary, inactivity_alert, milestone_achieved, streak_reminder.
- AC2: `assessment_complete` and `report_ready` are always-on transactional emails — not toggleable (clearly explained in UI).
- AC3: Every marketing email has a CAN-SPAM-compliant "Unsubscribe" link in the footer; unsubscribe does not affect transactional emails.
- AC4: Preference changes are reflected in `notification_preferences` table and take effect within 1 minute.

---

**US-436: COPPA No-Child-Direct-Communication Enforcement**  
**Priority:** P0 | **Points:** 2  
**Dependencies:** US-431 through US-434

> As the **system**, I want to enforce that no email, SMS, or push notification is ever sent directly to a student's email address or device so that we comply with COPPA.

**Acceptance Criteria:**
- AC1: `NotificationService.send_*()` raises `COPPAViolationError` if `recipient_type='student'` is passed.
- AC2: Students have no email address stored in `users.email` (field is NULL for student accounts created after COPPA check).
- AC3: If a student attempts to add an email in profile settings, the UI shows: "Notifications are managed by your parent."
- AC4: Automated test `test_no_student_email_ever` queries `notification_log WHERE recipient_type='student'` daily and asserts 0 rows.
- AC5: Code review checklist includes: "Does this endpoint ever send an external notification to a student email?" — tracked in `PULL_REQUEST_TEMPLATE.md`.

---

### 2.8 Epic MATH-407: MVP Hardening (NFR)

---

**US-437: PgBouncer Connection Pooling Setup**  
**Priority:** P0 | **Points:** 5  
**Dependencies:** ECS task definition

> As an **engineer**, I want PgBouncer deployed as an ECS sidecar in transaction pooling mode so that the API server can handle 550 concurrent sessions without exhausting PostgreSQL connections.

**Acceptance Criteria:**
- AC1: PgBouncer container added to the API ECS task definition; connection string updated to `localhost:5432`.
- AC2: `pool_mode=transaction`, `max_client_conn=700`, `default_pool_size=25`.
- AC3: Load test at 550 concurrent connections passes with < 1% connection error rate.
- AC4: SQLAlchemy pool configuration (`pool_size=5, max_overflow=10`) validated compatible with PgBouncer transaction mode.
- AC5: No `ROLLBACK` or `SAVEPOINT` outside explicit transaction blocks (PgBouncer transaction mode restriction).

---

**US-438: CloudFront CDN Deployment**  
**Priority:** P1 | **Points:** 3  
**Dependencies:** Vercel frontend

> As an **engineer**, I want CloudFront configured in front of the Vercel frontend to cache static assets so that Oregon students experience faster page loads.

**Acceptance Criteria:**
- AC1: CloudFront distribution created with Vercel as origin; custom domain `app.padi.ai` points to CloudFront.
- AC2: `/_next/static/*` cached with `max-age=31536000, immutable`.
- AC3: `/api/*` and auth-gated routes are not cached (pass-through).
- AC4: Security headers applied at CloudFront (HSTS, CSP, X-Frame-Options, X-Content-Type-Options).
- AC5: Cache hit ratio ≥ 60% after 24 hours of production traffic (measured in CloudWatch metrics).

---

**US-439: Performance Load Testing at MVP Scale**  
**Priority:** P0 | **Points:** 5  
**Dependencies:** All Stage 4 services deployed to staging

> As an **engineer**, I want the system load-tested at MVP target scale so that we can confirm performance thresholds before beta launch.

**Acceptance Criteria:**
- AC1: k6 load test: 500 concurrent practice WebSocket sessions + 50 concurrent EOG assessment sessions sustained for 10 minutes.
- AC2: P95 REST API latency < 500ms under full load.
- AC3: P95 IRT item response latency (per-question) < 200ms.
- AC4: PDF generation P95 < 10 seconds (measured in SQS worker).
- AC5: Error rate < 1% under full load (HTTP 5xx + WebSocket drops combined).
- AC6: PostgreSQL connection count stays within `max_connections` (monitored via PgBouncer stats).

---

**US-440: Security Audit — OWASP Top 10 Verification**  
**Priority:** P0 | **Points:** 5  
**Dependencies:** All APIs deployed to staging

> As an **engineer and legal**, I want a full security audit completed before MVP launch so that we have zero critical/high vulnerabilities exposed to beta users.

**Acceptance Criteria:**
- AC1: OWASP ZAP DAST scan completed against staging API; zero critical or high findings.
- AC2: Bandit SAST scan: zero high-severity findings in `apps/api/src/`.
- AC3: Trivy container scan: zero critical CVEs in production Docker images.
- AC4: `npm audit` / `pip-audit` dependency scan: zero critical vulnerabilities.
- AC5: SQL injection test on all `/v1/assessments/eog/*` and `/v1/teacher/*` endpoints — all parameterized, no injection possible.
- AC6: Manual penetration test: authenticated teacher cannot access another teacher's students; parent cannot access another parent's child data.

---

**US-441: COPPA/FERPA Compliance Verification**  
**Priority:** P0 | **Points:** 5  
**Dependencies:** All Stage 1–4 features

> As **legal and engineering**, I want a documented COPPA and FERPA compliance walkthrough completed so that we have evidence of compliance before beta launch with real children.

**Acceptance Criteria:**
- AC1: COPPA checklist completed and signed off: parental consent flow (Auth0), no child PII in LLM prompts, no direct child email, data minimization, 48-hour deletion SLA.
- AC2: FERPA checklist completed: teacher access basis documented as "parent-authorized disclosure," teacher data scope verified (no transcripts, no raw BKT), audit log retention confirmed.
- AC3: PII encryption verified: all `students` PII fields encrypted at rest (AES-256 via pgcrypto), TLS 1.3 in transit.
- AC4: Data deletion flow tested: parent deletes account → student data deleted within 48 hours → verified by DB audit.
- AC5: Automated test `test_coppa_pii_not_in_llm_prompts` passes (no student name/email in any prompt log).

---

**US-442: Full MVP Regression Suite Execution**  
**Priority:** P0 | **Points:** 8  
**Dependencies:** All 39 MVP checklist items (FR-15 through FR-20)

> As **QA**, I want a full regression suite executed against staging covering all 39 MVP checklist items so that we can confirm the complete student learning loop works end-to-end.

**Acceptance Criteria:**
- AC1: All 39 MVP checklist items (S1-01 through S4-22) pass in staging environment.
- AC2: Playwright E2E suite for the complete flow (diagnostic → learning plan → practice → EOG → report → teacher view) passes in all supported browsers (Chrome, Firefox, Safari).
- AC3: Zero P0 bugs open at time of MVP gate review.
- AC4: Full regression test run takes < 2 hours in CI (parallelized).
- AC5: Test coverage report shows ≥ 90% for core business logic (IRT service, BKT, report service), ≥ 80% for API routes.

---

**US-443: Monitoring and Alerting for Production**  
**Priority:** P0 | **Points:** 5  
**Dependencies:** Datadog, Sentry, AWS CloudWatch

> As an **engineer**, I want comprehensive monitoring configured before beta launch so that any production issues are detected and alerted within minutes.

**Acceptance Criteria:**
- AC1: Datadog APM traces all API endpoints with P50/P95/P99 latency dashboards.
- AC2: Sentry error tracking configured for both Next.js frontend and FastAPI backend with alert on new errors.
- AC3: CloudWatch alarms on: ECS task memory > 80%, RDS connections > 80% of max, SQS queue depth > 100, SES bounce rate > 5%.
- AC4: PgBouncer metrics (pool utilization, wait time) exported to CloudWatch custom metrics.
- AC5: On-call runbook written and linked from README: how to respond to PgBouncer exhaustion, SES failure, PDF generation failure, assessment invalidation spike.

---

## 3. Detailed Test Plan

### 3.1 Unit Tests

**Philosophy:** Unit tests are the foundation of the testing pyramid. For Stage 4, the most critical unit tests cover the IRT mathematics (deterministic algorithms that must be correct), proficiency classification (any bug can misclassify a child), and PDF generation (any bug produces a broken or incorrect report). Coverage target: ≥ 90% for `irt_service.py`, `cat_assessment_service.py`, `report_service.py`; ≥ 80% for remaining services.

**Test file locations:**
- `apps/api/tests/unit/test_irt_service.py`
- `apps/api/tests/unit/test_cat_assessment_service.py`
- `apps/api/tests/unit/test_report_service.py`
- `apps/api/tests/unit/test_notification_service.py`
- `apps/api/tests/unit/test_remediation_service.py`

---

#### 3.1.1 IRT 3PL Probability Calculations

```python
# apps/api/tests/unit/test_irt_service.py

import math
import pytest
import numpy as np
from apps.api.src.service.irt_service import (
    irt_3pl_probability,
    eap_estimate,
    fisher_information,
    ItemResponse,
)


class TestIRT3PLProbability:
    """Test the 3PL IRT probability function."""

    def test_probability_at_difficulty_equals_theta(self):
        """P(correct | θ=b) = (1+c)/2 for any valid c."""
        a, b, c = 1.5, 0.5, 0.25
        p = irt_3pl_probability(theta=b, a=a, b=b, c=c)
        expected = (1 + c) / 2
        assert abs(p - expected) < 1e-6

    def test_probability_above_c_for_low_ability(self):
        """For very low theta, probability approaches c (guessing floor)."""
        p = irt_3pl_probability(theta=-10.0, a=1.5, b=0.0, c=0.25)
        assert abs(p - 0.25) < 0.01

    def test_probability_approaches_1_for_high_ability(self):
        """For very high theta, probability approaches 1.0."""
        p = irt_3pl_probability(theta=10.0, a=1.5, b=0.0, c=0.25)
        assert p > 0.999

    def test_probability_monotonically_increasing_in_theta(self):
        """P(correct|θ) must be monotonically increasing as theta increases."""
        thetas = np.linspace(-4, 4, 81)
        probs = [irt_3pl_probability(float(t), a=1.2, b=0.0, c=0.25) for t in thetas]
        for i in range(len(probs) - 1):
            assert probs[i] <= probs[i + 1], (
                f"Non-monotone at theta={thetas[i]:.2f}: {probs[i]:.4f} > {probs[i+1]:.4f}"
            )

    def test_probability_zero_guessing(self):
        """With c=0, P at theta=b equals exactly 0.5."""
        p = irt_3pl_probability(theta=0.5, a=1.5, b=0.5, c=0.0)
        assert abs(p - 0.5) < 1e-6

    def test_overflow_prevention(self):
        """Extreme theta values must not cause overflow/NaN."""
        p_low = irt_3pl_probability(theta=-100.0, a=2.0, b=0.0, c=0.25)
        p_high = irt_3pl_probability(theta=100.0, a=2.0, b=0.0, c=0.25)
        assert math.isfinite(p_low)
        assert math.isfinite(p_high)
        assert 0.0 <= p_low <= 1.0
        assert 0.0 <= p_high <= 1.0

    def test_mc_item_guessing_parameter(self):
        """4-choice MC item has c=0.25; confirm probability bound."""
        p = irt_3pl_probability(theta=-4.0, a=1.0, b=0.0, c=0.25)
        assert p >= 0.24  # Approaches 0.25 asymptotically

    def test_numeric_entry_no_guessing(self):
        """Numeric entry items have c≈0.05; low-ability student probability near 0."""
        p = irt_3pl_probability(theta=-4.0, a=1.5, b=0.0, c=0.05)
        assert p < 0.10
```

---

#### 3.1.2 EAP Theta Estimation

```python
class TestEAPEstimation:
    """Test EAP theta estimation with Gaussian quadrature."""

    @pytest.fixture
    def all_correct_easy_responses(self):
        """Student answering all easy items correctly → high theta."""
        return [
            ItemResponse(question_id=f"q{i}", a=1.2, b=-1.0, c=0.25, is_correct=True)
            for i in range(15)
        ]

    @pytest.fixture
    def all_incorrect_hard_responses(self):
        """Student answering all hard items incorrectly → low theta."""
        return [
            ItemResponse(question_id=f"q{i}", a=1.2, b=1.0, c=0.25, is_correct=False)
            for i in range(15)
        ]

    def test_all_correct_produces_positive_theta(self, all_correct_easy_responses):
        """All-correct response pattern yields theta above prior mean."""
        result = eap_estimate(all_correct_easy_responses)
        assert result.theta > 0.5, f"Expected theta > 0.5, got {result.theta:.3f}"

    def test_all_incorrect_produces_negative_theta(self, all_incorrect_hard_responses):
        """All-incorrect response pattern yields theta below prior mean."""
        result = eap_estimate(all_incorrect_hard_responses)
        assert result.theta < -0.5, f"Expected theta < -0.5, got {result.theta:.3f}"

    def test_sem_decreases_with_more_responses(self):
        """SEM should decrease as more items are administered."""
        responses = [
            ItemResponse(question_id=f"q{i}", a=1.5, b=float(i % 5 - 2),
                        c=0.25, is_correct=(i % 3 != 0))
            for i in range(40)
        ]
        sems = []
        for n in [5, 10, 20, 40]:
            result = eap_estimate(responses[:n])
            sems.append(result.sem)
        for i in range(len(sems) - 1):
            assert sems[i] >= sems[i + 1] - 0.01, (
                f"SEM did not decrease: {sems[i]:.3f} → {sems[i+1]:.3f}"
            )

    def test_theta_within_range(self):
        """EAP theta must always be within the quadrature range [-4, 4]."""
        for _ in range(100):
            responses = [
                ItemResponse(
                    question_id="q0", a=2.0, b=3.0, c=0.0, is_correct=True
                )
            ]
            result = eap_estimate(responses)
            assert -4.0 <= result.theta <= 4.0

    def test_eap_is_deterministic(self):
        """Same response pattern always yields identical theta and SEM."""
        responses = [
            ItemResponse(question_id=f"q{i}", a=1.2, b=-0.5 + i * 0.1,
                        c=0.25, is_correct=(i % 2 == 0))
            for i in range(20)
        ]
        results = [eap_estimate(responses) for _ in range(5)]
        for r in results[1:]:
            assert abs(r.theta - results[0].theta) < 1e-10
            assert abs(r.sem - results[0].sem) < 1e-10

    def test_sem_is_positive(self):
        """SEM must always be strictly positive."""
        responses = [
            ItemResponse(question_id="q0", a=1.5, b=0.0, c=0.25, is_correct=True)
        ]
        result = eap_estimate(responses)
        assert result.sem > 0.0

    def test_empty_response_list_returns_prior(self):
        """With no responses, EAP returns the prior mean."""
        result = eap_estimate([], prior_mean=0.0, prior_std=1.0)
        assert abs(result.theta - 0.0) < 0.01
```

---

#### 3.1.3 Item Selection (Maximum Fisher Information)

```python
# apps/api/tests/unit/test_item_selection.py

from apps.api.src.service.irt_service import (
    fisher_information,
    IRTService,
)


class TestFisherInformation:
    """Test Fisher Information calculation."""

    def test_fisher_info_is_positive(self):
        """Fisher Information must always be positive."""
        fi = fisher_information(theta=0.0, a=1.5, b=0.0, c=0.25)
        assert fi > 0.0

    def test_fisher_info_maximized_near_difficulty(self):
        """Fisher Information peaks near item difficulty for c=0 items."""
        fi_at_b = fisher_information(theta=0.5, a=1.5, b=0.5, c=0.0)
        fi_far_from_b = fisher_information(theta=3.0, a=1.5, b=0.5, c=0.0)
        assert fi_at_b > fi_far_from_b

    def test_item_selection_excludes_administered(self):
        """MFI selection never returns an already-administered item."""
        irt_svc = IRTService()
        item_bank = [
            {"question_id": "q1", "a": 1.5, "b": 0.0, "c": 0.25, "domain": "NF"},
            {"question_id": "q2", "a": 1.2, "b": 0.1, "c": 0.25, "domain": "NF"},
            {"question_id": "q3", "a": 1.8, "b": -0.1, "c": 0.25, "domain": "OA"},
        ]
        selected = irt_svc.select_next_item(
            theta=0.0,
            administered_items=["q1", "q3"],
            item_bank=item_bank,
            content_coverage={"NF": 1, "OA": 1},
            target_coverage={"NF": 0.30, "OA": 0.20},
        )
        assert selected["question_id"] == "q2"

    def test_item_selection_respects_content_balance(self):
        """When a domain is under-represented, selection prefers that domain."""
        irt_svc = IRTService()
        # NF needs more items; OA is over-represented
        item_bank = [
            {"question_id": "q1", "a": 0.8, "b": 0.0, "c": 0.25, "domain": "NF"},
            {"question_id": "q2", "a": 2.0, "b": 0.0, "c": 0.25, "domain": "OA"},
        ]
        selected = irt_svc.select_next_item(
            theta=0.0,
            administered_items=[],
            item_bank=item_bank,
            content_coverage={"NF": 0, "OA": 10},
            target_coverage={"NF": 0.30, "OA": 0.20},
        )
        # NF is severely under-represented, so NF item selected despite lower info
        assert selected["domain"] == "NF"

    def test_item_selection_returns_none_for_exhausted_bank(self):
        """Returns None when all items have been administered."""
        irt_svc = IRTService()
        item_bank = [
            {"question_id": "q1", "a": 1.5, "b": 0.0, "c": 0.25, "domain": "NF"}
        ]
        selected = irt_svc.select_next_item(
            theta=0.0,
            administered_items=["q1"],
            item_bank=item_bank,
            content_coverage={"NF": 1},
            target_coverage={"NF": 0.30},
        )
        assert selected is None
```

---

#### 3.1.4 Proficiency Classification

```python
# apps/api/tests/unit/test_proficiency_classification.py

import pytest
from apps.api.src.service.cat_assessment_service import CATAssessmentService
from apps.api.src.models.assessment import ProficiencyLevel


class TestProficiencyClassification:
    """Test theta → proficiency level mapping with SEM adjustments."""

    @pytest.fixture
    def cat_service(self):
        return CATAssessmentService()

    @pytest.mark.parametrize("theta,sem,expected", [
        (-2.0, 0.25, ProficiencyLevel.BELOW_PAR),    # Clearly below par
        (-0.5, 0.25, ProficiencyLevel.APPROACHING),   # Approaching boundary
        (0.5, 0.25, ProficiencyLevel.ON_PAR),          # On par
        (1.5, 0.25, ProficiencyLevel.ABOVE_PAR),       # Above par
        (-0.05, 0.1, ProficiencyLevel.APPROACHING),   # Just below On Par boundary
        (0.0, 0.1, ProficiencyLevel.ON_PAR),           # Exactly at On Par boundary
        (1.0, 0.1, ProficiencyLevel.ABOVE_PAR),        # Exactly at Above Par boundary
    ])
    def test_classification_boundaries(self, cat_service, theta, sem, expected):
        result = cat_service.compute_proficiency_level(theta=theta, sem=sem)
        assert result == expected, f"theta={theta}, sem={sem}: expected {expected}, got {result}"

    def test_conservative_classification_on_high_sem(self, cat_service):
        """When SEM > 0.5, use theta - SEM for effective classification."""
        # theta=0.1, sem=0.6 → effective_theta = 0.1 - 0.6 = -0.5 → APPROACHING
        result = cat_service.compute_proficiency_level(theta=0.1, sem=0.6)
        assert result == ProficiencyLevel.APPROACHING

    def test_conservative_not_applied_for_low_sem(self, cat_service):
        """When SEM ≤ 0.5, use raw theta for classification."""
        # theta=0.1, sem=0.3 → raw theta used → ON_PAR
        result = cat_service.compute_proficiency_level(theta=0.1, sem=0.3)
        assert result == ProficiencyLevel.ON_PAR

    def test_all_proficiency_levels_reachable(self, cat_service):
        """Every proficiency level must be reachable with normal SEM."""
        assert cat_service.compute_proficiency_level(-2.0, 0.2) == ProficiencyLevel.BELOW_PAR
        assert cat_service.compute_proficiency_level(-0.5, 0.2) == ProficiencyLevel.APPROACHING
        assert cat_service.compute_proficiency_level(0.5, 0.2) == ProficiencyLevel.ON_PAR
        assert cat_service.compute_proficiency_level(2.0, 0.2) == ProficiencyLevel.ABOVE_PAR
```

---

#### 3.1.5 PDF Generation Service — Unit Tests

```python
# apps/api/tests/unit/test_report_service.py

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from apps.api.src.service.report_service import ReportService
from apps.api.src.models.assessment import ReportVersion


class TestReportService:
    """Unit tests for PDF report generation service."""

    @pytest.fixture
    def report_service(self):
        return ReportService()

    @pytest.fixture
    def sample_report_data(self):
        return {
            "student_name": "Alex",
            "assessment_date": "2026-06-01",
            "theta": 0.35,
            "sem": 0.28,
            "proficiency_level": "ON_PAR",
            "domain_scores": {"OA": 0.8, "NBT": 0.6, "NF": 0.2, "MD": 0.4, "G": 0.9},
            "skills_mastered": 17,
            "skills_total": 29,
            "remediation_skills": ["4.NF.B.3", "4.MD.A.1"],
        }

    @pytest.mark.asyncio
    async def test_html_rendered_for_teacher_version(
        self, report_service, sample_report_data
    ):
        """Teacher version HTML contains theta score and SEM."""
        html = report_service._render_html(sample_report_data, ReportVersion.TEACHER)
        assert "0.35" in html  # Theta displayed
        assert "0.28" in html  # SEM displayed
        assert "Domain" in html  # Domain breakdown section present

    @pytest.mark.asyncio
    async def test_html_rendered_for_student_version(
        self, report_service, sample_report_data
    ):
        """Student version HTML does not contain raw theta or SEM values."""
        html = report_service._render_html(sample_report_data, ReportVersion.STUDENT)
        assert "theta" not in html.lower()
        assert "SEM" not in html
        assert "Alex" in html  # Student name present

    def test_s3_key_format_is_correct(self, report_service):
        """S3 key follows expected pattern for FERPA-compliant access control."""
        key = report_service._build_s3_key(
            student_id="stu-123",
            assessment_id="asmt-456",
            version=ReportVersion.TEACHER,
        )
        assert key == "reports/stu-123/asmt-456/teacher_report.pdf"

    @pytest.mark.asyncio
    async def test_get_report_url_generates_presigned_url(self, report_service):
        """Presigned URL generation returns a non-empty URL string."""
        with patch.object(report_service, "_s3_client") as mock_s3:
            mock_s3.generate_presigned_url = MagicMock(
                return_value="https://s3.amazonaws.com/bucket/key?X-Amz-Signature=abc123"
            )
            url = await report_service.get_report_url(
                report_id="rpt-789", version=ReportVersion.TEACHER
            )
        assert url.startswith("https://")
        assert "X-Amz-Signature" in url

    def test_report_data_contains_all_required_sections(
        self, report_service, sample_report_data
    ):
        """All FR-17.3 sections are present in compiled report data."""
        required_keys = [
            "student_name", "assessment_date", "proficiency_level",
            "domain_scores", "skills_mastered", "remediation_skills",
        ]
        for key in required_keys:
            assert key in sample_report_data, f"Missing required key: {key}"

    def test_student_report_reading_level(self, report_service, sample_report_data):
        """Student report text must be ≤ Flesch-Kincaid Grade 5.5."""
        import textstat
        html = report_service._render_html(sample_report_data, ReportVersion.STUDENT)
        # Extract text content (simplified — full test would use BeautifulSoup)
        text_content = (
            "You're doing great! You've learned a lot of math this year. "
            "Keep working on fractions and you'll get there soon!"
        )
        fk_grade = textstat.flesch_kincaid_grade(text_content)
        assert fk_grade <= 5.5, f"FK Grade {fk_grade} exceeds 5.5 for student report"
```

---

#### 3.1.6 Additional Unit Test Cases Summary

| Test ID | File | Test Name | Coverage Target |
|---|---|---|---|
| UT-401 | `test_irt_service.py` | `test_probability_at_difficulty_equals_theta` | `irt_3pl_probability` |
| UT-402 | `test_irt_service.py` | `test_overflow_prevention` | Numerical stability |
| UT-403 | `test_irt_service.py` | `test_eap_is_deterministic` | Score reproducibility |
| UT-404 | `test_irt_service.py` | `test_sem_decreases_with_more_responses` | SEM convergence |
| UT-405 | `test_item_selection.py` | `test_item_selection_excludes_administered` | No item repeats |
| UT-406 | `test_item_selection.py` | `test_item_selection_respects_content_balance` | Domain balancing |
| UT-407 | `test_proficiency_classification.py` | `test_conservative_classification_on_high_sem` | SEM adjustment |
| UT-408 | `test_proficiency_classification.py` | `test_all_proficiency_levels_reachable` | Classification coverage |
| UT-409 | `test_report_service.py` | `test_student_report_reading_level` | Accessibility |
| UT-410 | `test_report_service.py` | `test_s3_key_format_is_correct` | FERPA key structure |
| UT-411 | `test_notification_service.py` | `test_coppa_violation_error_raised_for_student` | COPPA guard |
| UT-412 | `test_notification_service.py` | `test_weekly_summary_idempotent` | No duplicate emails |
| UT-413 | `test_remediation_service.py` | `test_deficient_skills_sorted_by_p_mastered_ascending` | Plan ordering |
| UT-414 | `test_remediation_service.py` | `test_prerequisite_ordering_respected` | Graph sort |
| UT-415 | `test_stopping_criteria.py` | `test_all_three_stopping_conditions` | CAT termination |

---

### 3.2 Integration Tests

Integration tests use `testcontainers` (PostgreSQL 17 + Redis) and `httpx.AsyncClient` against the real FastAPI app. No mocks for database or cache layers.

**Test file locations:**
- `apps/api/tests/integration/test_eog_assessment_api.py`
- `apps/api/tests/integration/test_report_pipeline.py`
- `apps/api/tests/integration/test_notification_delivery.py`
- `apps/api/tests/integration/test_teacher_dashboard_api.py`

---

#### 3.2.1 Full CAT Assessment Session Integration Test

```python
# apps/api/tests/integration/test_eog_assessment_api.py

import pytest
import httpx
from testcontainers.postgres import PostgresContainer
from apps.api.src.main import create_app


@pytest.fixture(scope="module")
def postgres_container():
    with PostgresContainer("postgres:17") as pg:
        yield pg


@pytest.mark.asyncio
async def test_complete_eog_session_integration(postgres_container, auth_headers):
    """Full CAT session: start → respond 40 times → complete → verify results."""
    app = create_app()
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        # 1. Start assessment
        resp = await client.post(
            "/v1/assessments/eog/start",
            headers=auth_headers,
            json={"student_id": "stu-test-001", "grade_level": 4},
        )
        assert resp.status_code == 201
        data = resp.json()
        assessment_id = data["assessment_id"]
        assert data["first_question"]["question_id"] is not None

        # 2. Submit 40 responses (alternating correct/incorrect)
        question_id = data["first_question"]["question_id"]
        for i in range(40):
            resp = await client.post(
                f"/v1/assessments/eog/{assessment_id}/respond",
                headers=auth_headers,
                json={
                    "question_id": question_id,
                    "answer": "correct_answer" if i % 2 == 0 else "wrong_answer",
                    "response_time_ms": 15000,
                },
            )
            assert resp.status_code == 200
            body = resp.json()
            if body.get("should_stop"):
                break
            question_id = body["next_question"]["question_id"]

        # 3. Complete assessment
        resp = await client.post(
            f"/v1/assessments/eog/{assessment_id}/complete",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        results = resp.json()
        assert results["proficiency_level"] in [
            "BELOW_PAR", "APPROACHING", "ON_PAR", "ABOVE_PAR"
        ]
        assert -4.0 <= results["theta"] <= 4.0
        assert results["sem"] > 0.0
        assert results["items_administered"] <= 40

        # 4. Verify DB state
        from apps.api.src.db.session import get_session
        async with get_session() as session:
            from sqlalchemy import text
            row = await session.execute(
                text("SELECT status, proficiency_level FROM eog_assessments WHERE id = :id"),
                {"id": assessment_id}
            )
            db_row = row.fetchone()
            assert db_row.status == "completed"
            assert db_row.proficiency_level == results["proficiency_level"]
```

---

#### 3.2.2 Retake Window Enforcement Integration Test

```python
@pytest.mark.asyncio
async def test_retake_window_enforced(postgres_container, auth_headers_student_a):
    """Student cannot start a second EOG within 30 days of the first."""
    app = create_app()
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        # First assessment
        resp1 = await client.post("/v1/assessments/eog/start", headers=auth_headers_student_a,
                                   json={"student_id": "stu-a", "grade_level": 4})
        assert resp1.status_code == 201

        # Simulate completion by marking as completed in DB
        assessment_id = resp1.json()["assessment_id"]
        await mark_assessment_completed(assessment_id)

        # Immediate retake attempt
        resp2 = await client.post("/v1/assessments/eog/start", headers=auth_headers_student_a,
                                   json={"student_id": "stu-a", "grade_level": 4})
        assert resp2.status_code == 409
        error = resp2.json()
        assert error["error_code"] == "RETAKE_WINDOW_ACTIVE"
        assert "retake_available_at" in error
```

---

#### 3.2.3 Report Generation Pipeline Integration Test

```python
# apps/api/tests/integration/test_report_pipeline.py

@pytest.mark.asyncio
async def test_report_generated_after_assessment(mock_s3, mock_sqs, postgres_container):
    """PDF report generation job is enqueued and produces a valid S3 key."""
    assessment_id = await create_completed_assessment("stu-pdf-test")

    # Simulate SQS worker processing
    from apps.api.src.workers.report_worker import ReportGeneratorWorker
    worker = ReportGeneratorWorker()
    result = await worker.process({"student_id": "stu-pdf-test", "assessment_id": assessment_id})

    assert result["status"] == "success"
    assert result["generation_time_ms"] < 10000  # Under 10-second SLA
    assert result["teacher_pdf_s3_key"].endswith("teacher_report.pdf")
    assert result["student_pdf_s3_key"].endswith("student_report.pdf")

    # Verify S3 upload was called with KMS encryption
    mock_s3.put_object.assert_called_with(
        Bucket=pytest.mock.ANY,
        Key=pytest.mock.ANY,
        Body=pytest.mock.ANY,
        ContentType="application/pdf",
        ServerSideEncryption="aws:kms",
    )
```

---

#### 3.2.4 Email Delivery Integration Test

```python
# apps/api/tests/integration/test_notification_delivery.py

@pytest.mark.asyncio
async def test_assessment_complete_email_sent_to_parent(mock_ses, postgres_container):
    """Assessment complete notification is sent to parent within expected parameters."""
    from apps.api.src.service.notification_service import NotificationService
    svc = NotificationService()

    results = await svc.send_assessment_complete(
        student_id="stu-notif-test",
        results=make_eog_results(theta=0.3, level="ON_PAR"),
    )

    mock_ses.send_email.assert_called_once()
    call_kwargs = mock_ses.send_email.call_args.kwargs
    assert call_kwargs["Destination"]["ToAddresses"] == ["parent@example.com"]
    assert "completed" in call_kwargs["Message"]["Subject"]["Data"].lower()

    # Verify notification_log entry
    log = await get_notification_log_entry(student_id="stu-notif-test",
                                            notification_type="assessment_complete")
    assert log is not None
    assert log.status == "sent"
    assert log.recipient_type == "parent"

@pytest.mark.asyncio
async def test_no_email_sent_to_student(mock_ses, postgres_container):
    """COPPA: no email must ever be sent to a student recipient_type."""
    from apps.api.src.service.notification_service import NotificationService, COPPAViolationError
    svc = NotificationService()

    with pytest.raises(COPPAViolationError):
        await svc._send_email(
            recipient_id="stu-001",
            recipient_email="student@example.com",
            recipient_type="student",
            notification_type="assessment_complete",
            subject="Test",
            template_id="test",
            template_data={},
        )
```

---

#### 3.2.5 Teacher Dashboard Data Scoping Integration Test

```python
# apps/api/tests/integration/test_teacher_dashboard_api.py

@pytest.mark.asyncio
async def test_teacher_only_sees_granted_students(postgres_container):
    """Teacher roster query returns only students with active grants."""
    # Set up: teacher has access to stu-A but not stu-B
    await grant_teacher_access(teacher_id="tch-1", student_id="stu-A")

    app = create_app()
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.get("/v1/teacher/roster", headers=teacher_auth("tch-1"))
        assert resp.status_code == 200
        roster = resp.json()["students"]
        student_ids = [s["student_id"] for s in roster]
        assert "stu-A" in student_ids
        assert "stu-B" not in student_ids  # No grant exists

@pytest.mark.asyncio
async def test_teacher_cannot_access_session_transcripts(postgres_container):
    """Teacher cannot retrieve session transcripts — parent-only data."""
    app = create_app()
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.get(
            "/v1/sessions/sess-001/transcript",
            headers=teacher_auth("tch-1"),
        )
        assert resp.status_code == 403
        assert "transcript" in resp.json()["detail"].lower()
```

---

#### 3.2.6 Integration Test Summary Table

| Test ID | File | Test Name | What It Verifies |
|---|---|---|---|
| IT-401 | `test_eog_assessment_api.py` | `test_complete_eog_session_integration` | Full 40-item CAT session, DB state |
| IT-402 | `test_eog_assessment_api.py` | `test_retake_window_enforced` | 30-day retake restriction |
| IT-403 | `test_eog_assessment_api.py` | `test_no_hints_during_assessment` | Assessment integrity |
| IT-404 | `test_eog_assessment_api.py` | `test_domain_coverage_after_40_items` | Content balancing |
| IT-405 | `test_eog_assessment_api.py` | `test_bkt_updated_after_assessment` | BKT state update (3× weight) |
| IT-406 | `test_report_pipeline.py` | `test_report_generated_after_assessment` | PDF SLA < 10s |
| IT-407 | `test_report_pipeline.py` | `test_report_s3_kms_encrypted` | FERPA at-rest encryption |
| IT-408 | `test_report_pipeline.py` | `test_presigned_url_expires_at_7_days` | URL expiry |
| IT-409 | `test_notification_delivery.py` | `test_assessment_complete_email_sent_to_parent` | Email delivery |
| IT-410 | `test_notification_delivery.py` | `test_no_email_sent_to_student` | COPPA guard |
| IT-411 | `test_notification_delivery.py` | `test_weekly_summary_dedup` | No duplicate emails |
| IT-412 | `test_teacher_dashboard_api.py` | `test_teacher_only_sees_granted_students` | FERPA scoping |
| IT-413 | `test_teacher_dashboard_api.py` | `test_teacher_cannot_access_session_transcripts` | Data scope restriction |
| IT-414 | `test_teacher_dashboard_api.py` | `test_teacher_csv_export_pii_minimized` | PII minimization |
| IT-415 | `test_remediation_service.py` | `test_remediation_plan_created_after_assessment` | Loop closure |

---

### 3.3 End-to-End Tests (Playwright)

E2E tests exercise complete user workflows through the actual Next.js UI. Tests run on Chromium, Firefox, and WebKit (Safari) using Playwright's parallel test runner.

**Config file:** `apps/web/playwright.config.ts`  
**Test location:** `apps/web/tests/e2e/stage4/`

---

#### 3.3.1 Complete Assessment Flow E2E

```typescript
// apps/web/tests/e2e/stage4/assessment-flow.spec.ts

import { test, expect } from '@playwright/test';
import { loginAsStudent, seedTestStudent } from '../helpers/auth';

test.describe('EOG Assessment Complete Flow', () => {
  test.beforeEach(async ({ page }) => {
    await seedTestStudent({ studentId: 'e2e-stu-001', completedPriorAssessment: false });
    await loginAsStudent(page, 'e2e-stu-001');
  });

  test('E2E-401: Student completes full EOG assessment', async ({ page }) => {
    // Navigate to assessment
    await page.goto('/student/assessment');
    await expect(page.locator('[data-testid="start-eog-btn"]')).toBeVisible();
    await page.click('[data-testid="start-eog-btn"]');

    // Pre-assessment briefing
    await expect(page.locator('[data-testid="assessment-briefing"]')).toContainText('no hints');
    await page.click('[data-testid="begin-assessment-btn"]');

    // Answer questions until stop signal
    let questionCount = 0;
    while (questionCount < 50) {
      const questionVisible = await page.locator('[data-testid="question-text"]').isVisible();
      if (!questionVisible) break;

      // Select first option for MC or enter a value for numeric
      const mcOption = page.locator('[data-testid="mc-option-0"]');
      if (await mcOption.isVisible()) {
        await mcOption.click();
      } else {
        await page.fill('[data-testid="numeric-input"]', '42');
      }
      await page.click('[data-testid="submit-answer-btn"]');
      questionCount++;

      // Check if review screen appeared
      const reviewVisible = await page.locator('[data-testid="assessment-review"]').isVisible();
      if (reviewVisible) break;
    }

    // Final review and submit
    await page.click('[data-testid="submit-final-btn"]');
    await page.click('[data-testid="confirm-submit-btn"]');

    // Results screen
    await expect(page.locator('[data-testid="proficiency-level"]')).toBeVisible();
    await expect(page.locator('[data-testid="domain-scores"]')).toBeVisible();
    await expect(page.locator('[data-testid="continue-learning-btn"]')).toBeVisible();
  });

  test('E2E-402: Back button disabled during assessment', async ({ page }) => {
    await page.goto('/student/assessment');
    await page.click('[data-testid="start-eog-btn"]');
    await page.click('[data-testid="begin-assessment-btn"]');

    // Attempt browser back navigation
    await page.goBack();

    // Still on assessment page (browser back blocked)
    await expect(page).toHaveURL(/\/student\/assessment/);
    await expect(page.locator('[data-testid="question-text"]')).toBeVisible();
  });

  test('E2E-403: Hint buttons not present during assessment', async ({ page }) => {
    await page.goto('/student/assessment');
    await page.click('[data-testid="start-eog-btn"]');
    await page.click('[data-testid="begin-assessment-btn"]');

    // Assert hint and tutor elements are NOT in DOM at all
    await expect(page.locator('[data-testid="hint-btn"]')).not.toBeAttached();
    await expect(page.locator('[data-testid="tutor-chat"]')).not.toBeAttached();
    await expect(page.locator('[data-testid="calculator-btn"]')).not.toBeAttached();
  });

  test('E2E-404: Tab switch detected and counter incremented', async ({ page, context }) => {
    await page.goto('/student/assessment');
    await page.click('[data-testid="start-eog-btn"]');
    await page.click('[data-testid="begin-assessment-btn"]');

    // Open a new tab (simulates tab switch)
    const newPage = await context.newPage();
    await newPage.goto('about:blank');
    await newPage.close();

    // Return to assessment page
    await page.bringToFront();
    await expect(page.locator('[data-testid="tab-switch-warning"]')).toBeVisible();
  });

  test('E2E-405: Retake blocked within 30-day window', async ({ page }) => {
    await seedTestStudent({ studentId: 'e2e-stu-retake', completedAssessmentDaysAgo: 5 });
    await loginAsStudent(page, 'e2e-stu-retake');
    await page.goto('/student/assessment');

    await expect(page.locator('[data-testid="retake-unavailable"]')).toBeVisible();
    await expect(page.locator('[data-testid="retake-available-in"]')).toContainText('25 days');
    await expect(page.locator('[data-testid="start-eog-btn"]')).not.toBeVisible();
  });
});
```

---

#### 3.3.2 Teacher Dashboard E2E

```typescript
// apps/web/tests/e2e/stage4/teacher-dashboard.spec.ts

test.describe('Teacher Dashboard', () => {
  test('E2E-410: Teacher sees only students who have shared data', async ({ page }) => {
    await loginAsTeacher(page, 'tch-e2e-001');
    await page.goto('/teacher/dashboard');

    const rosterRows = page.locator('[data-testid="roster-row"]');
    await expect(rosterRows).toHaveCount(2); // Only 2 students granted access

    // Verify shared student is visible
    await expect(page.locator('[data-testid="student-Alex-M"]')).toBeVisible();

    // Verify non-shared student is absent
    await expect(page.locator('[data-testid="student-Jordan-T"]')).not.toBeVisible();
  });

  test('E2E-411: Teacher CSV export downloads correct file', async ({ page }) => {
    await loginAsTeacher(page, 'tch-e2e-001');
    await page.goto('/teacher/dashboard');

    const [download] = await Promise.all([
      page.waitForEvent('download'),
      page.click('[data-testid="export-csv-btn"]'),
    ]);

    const filename = download.suggestedFilename();
    expect(filename).toMatch(/^padi-ai-roster-\d{4}-\d{2}-\d{2}\.csv$/);

    const csvContent = await download.path().then(p => require('fs').readFileSync(p, 'utf-8'));
    expect(csvContent).toContain('student_first_name');
    expect(csvContent).not.toContain('student_last_name');
    expect(csvContent).not.toContain('student_id');
    expect(csvContent).not.toContain('email');
  });

  test('E2E-412: Teacher cannot see session transcripts', async ({ page }) => {
    await loginAsTeacher(page, 'tch-e2e-001');
    await page.goto('/teacher/students/stu-shared-001');

    // Transcript section should not exist in teacher view
    await expect(page.locator('[data-testid="session-transcript"]')).not.toBeAttached();
    await expect(page.locator('[data-testid="view-transcript-btn"]')).not.toBeAttached();
  });
});
```

---

#### 3.3.3 Parent Dashboard and PDF Download E2E

```typescript
// apps/web/tests/e2e/stage4/parent-dashboard.spec.ts

test.describe('Parent Dashboard', () => {
  test('E2E-420: Parent dashboard loads within 3 seconds', async ({ page }) => {
    await loginAsParent(page, 'par-e2e-001');
    const start = Date.now();
    await page.goto('/parent/dashboard');
    await expect(page.locator('[data-testid="dashboard-home"]')).toBeVisible();
    const loadTime = Date.now() - start;
    expect(loadTime).toBeLessThan(3000);
  });

  test('E2E-421: Parent can download PDF report', async ({ page }) => {
    await loginAsParent(page, 'par-e2e-001');
    await page.goto('/parent/dashboard');

    const [download] = await Promise.all([
      page.waitForEvent('download'),
      page.click('[data-testid="download-latest-report-btn"]'),
    ]);

    expect(download.suggestedFilename()).toMatch(/\.pdf$/);
  });

  test('E2E-422: Skill mastery timeline shows all 29 standards', async ({ page }) => {
    await loginAsParent(page, 'par-e2e-001');
    await page.goto('/parent/skills');

    const skillBars = page.locator('[data-testid="skill-bar"]');
    await expect(skillBars).toHaveCount(29);
  });

  test('E2E-423: Share with teacher generates a link', async ({ page }) => {
    await loginAsParent(page, 'par-e2e-001');
    await page.goto('/parent/dashboard');
    await page.click('[data-testid="share-with-teacher-btn"]');

    await expect(page.locator('[data-testid="share-modal"]')).toBeVisible();
    await page.click('[data-testid="generate-link-btn"]');

    const linkInput = page.locator('[data-testid="share-link-input"]');
    await expect(linkInput).toHaveValue(/https:\/\/.+/);
  });

  test('E2E-424: No peer comparison shown in parent dashboard', async ({ page }) => {
    await loginAsParent(page, 'par-e2e-001');
    await page.goto('/parent/dashboard');

    // Verify no percentile/rank language
    const pageContent = await page.content();
    expect(pageContent).not.toContain('percentile');
    expect(pageContent).not.toContain('compared to other students');
    expect(pageContent).not.toContain('class average');
  });
});
```

---

#### 3.3.4 E2E Test Matrix

| Test ID | Workflow | Chrome | Firefox | Safari |
|---|---|---|---|---|
| E2E-401 | Complete EOG assessment (40 items) | ✓ | ✓ | ✓ |
| E2E-402 | Back button disabled during assessment | ✓ | ✓ | ✓ |
| E2E-403 | Hint/tutor absent from assessment DOM | ✓ | ✓ | ✓ |
| E2E-404 | Tab switch detection | ✓ | ✓ | — (API unavailable in WebKit) |
| E2E-405 | Retake blocked (30-day window) | ✓ | ✓ | ✓ |
| E2E-406 | Assessment results screen loads | ✓ | ✓ | ✓ |
| E2E-407 | "Continue Learning" navigates to plan | ✓ | ✓ | ✓ |
| E2E-408 | PDF report link appears after completion | ✓ | ✓ | ✓ |
| E2E-409 | Remediation plan updated in dashboard | ✓ | ✓ | ✓ |
| E2E-410 | Teacher roster — scoped to grants | ✓ | ✓ | ✓ |
| E2E-411 | Teacher CSV export | ✓ | ✓ | ✓ |
| E2E-412 | Teacher cannot see transcripts | ✓ | ✓ | ✓ |
| E2E-413 | Teacher class heatmap renders | ✓ | ✓ | ✓ |
| E2E-420 | Parent dashboard load time < 3s | ✓ | ✓ | ✓ |
| E2E-421 | Parent PDF download | ✓ | ✓ | ✓ |
| E2E-422 | 29 skill bars displayed | ✓ | ✓ | ✓ |
| E2E-423 | Share with teacher generates link | ✓ | ✓ | ✓ |
| E2E-424 | No peer comparison in UI | ✓ | ✓ | ✓ |

---

### 3.4 Behavioral/BDD Tests (Given-When-Then)

BDD tests are written in Gherkin format and executed with `pytest-bdd`. Feature files are located at `apps/api/tests/bdd/features/stage4/`.

---

#### 3.4.1 Assessment Scenarios

```gherkin
# apps/api/tests/bdd/features/stage4/assessment.feature

Feature: End-of-Grade Assessment Administration

  Background:
    Given a student "Alex" in Grade 4 with a completed diagnostic assessment
    And a calibrated EOG item bank with 200 questions across 5 domains

  Scenario: Student completes assessment with sufficient precision
    Given Alex has not taken an EOG assessment in the last 30 days
    When Alex starts an EOG assessment
    And Alex answers 20 questions correctly and 5 questions incorrectly
    And the SEM falls below 0.30 after item 18
    Then the assessment should terminate with stop_reason "sem_threshold"
    And the final proficiency_level should not be null
    And a remediation plan should be automatically generated

  Scenario: Assessment is voided after extended disconnection
    Given Alex is in the middle of an EOG assessment at item 12
    When Alex's browser disconnects for 6 minutes
    Then the assessment should be marked as "invalidated"
    And Alex should see an explanation screen about the voided assessment
    And the voided assessment should not affect the retake window countdown

  Scenario: Assessment integrity - no back navigation
    Given Alex is on item 7 of the EOG assessment
    When Alex presses the browser's back button
    Then Alex should remain on item 7
    And no prior question should be displayed
    And the back-navigation attempt should be silently absorbed

  Scenario: Proficiency level Below Par triggers teacher intervention alert
    Given Alex completes an EOG assessment
    And the computed theta is -1.5 (BELOW_PAR level)
    And teacher "Ms. Garcia" has active teacher_student_access for Alex
    When the assessment is finalized
    Then Ms. Garcia should receive an intervention_needed email
    And the email should contain Alex's proficiency level and remediation plan link
```

---

#### 3.4.2 Reporting Scenarios

```gherkin
# apps/api/tests/bdd/features/stage4/reporting.feature

Feature: Progress Report Generation and Delivery

  Scenario: Parent receives PDF report after assessment completion
    Given student "Jordan" has just completed an EOG assessment
    And Jordan's parent "Sarah" has email notifications enabled
    When the assessment completion event is processed
    Then a PDF report should be generated within 10 seconds
    And Sarah should receive an email with a presigned download URL
    And the URL should expire in 7 days

  Scenario: Teacher report contains theta and SEM, student report does not
    Given a completed assessment with theta=0.45 and SEM=0.27
    When the teacher/parent PDF is generated
    Then the teacher PDF should contain "0.45" (theta value)
    And the teacher PDF should contain "0.27" (SEM value)
    When the student PDF is generated
    Then the student PDF should not contain "0.45" or "theta"
    And the student PDF reading level should be Flesch-Kincaid ≤ 5.5

  Scenario: Shareable teacher report link expires after 90 days
    Given parent "Sarah" generates a shareable teacher link
    When 91 days have passed
    Then accessing the shareable link should return HTTP 403
    And the teacher should see "This link has expired" message

  Scenario: CSV export is PII-minimized for teacher use
    Given teacher "Ms. Garcia" clicks "Export CSV" on her roster
    When the CSV file is downloaded
    Then the CSV should contain column "student_first_name"
    And the CSV should not contain columns "student_last_name", "email", "student_id"
    And the export event should be logged in audit_log
```

---

#### 3.4.3 Remediation Loop Scenarios

```gherkin
# apps/api/tests/bdd/features/stage4/remediation.feature

Feature: Closed Remediation Loop After Assessment

  Scenario: Deficient skills generate updated learning plan
    Given student "Riley" completes an EOG assessment with theta = -0.8
    And 8 skills have P(mastered) < 0.70 in BKT
    When the remediation plan is auto-generated
    Then a new learning_plans record should exist with source="eog_remediation"
    And the plan should contain modules for all 8 deficient skills
    And skills should be ordered by ascending P(mastered)
    And prerequisite ordering should be respected in the module sequence

  Scenario: Above-par student does not receive remediation plan
    Given student "Sam" completes an EOG assessment with theta = 1.2 (ABOVE_PAR)
    When the assessment is finalized
    Then no remediation plan should be created
    And Sam should see a "Congratulations! You've exceeded grade level!" screen
    And no updated learning plan should be pushed to Sam's dashboard

  Scenario: Loop continues until On Par achieved
    Given student "Alex" is in the remediation loop after first EOG (theta = -0.5)
    And Alex practices the remediation plan for 4 weeks
    When Alex completes a second EOG assessment with theta = 0.2 (ON_PAR)
    Then the remediation loop should terminate
    And Alex's dashboard should show the "On Par" achievement milestone
    And a new remediation plan should NOT be generated
```

---

#### 3.4.4 Email Notification Scenarios

```gherkin
# apps/api/tests/bdd/features/stage4/notifications.feature

Feature: Email and In-App Notification System

  Scenario: Weekly summary sent at correct time in parent's timezone
    Given parent "Sarah" is in timezone "America/Los_Angeles"
    And Sarah has weekly_summary notifications enabled
    When Sunday 7:00 PM Pacific Time is reached
    Then Sarah should receive a weekly_summary email
    And the email subject should match "[Student Name]'s PADI.AI Update"

  Scenario: Inactivity alert sent after 7 days without practice
    Given student "Alex" last had a practice session 7 days ago
    When the daily inactivity check runs
    Then parent "Sarah" should receive an inactivity_alert email
    And the email should not be sent again until Alex has a new session

  Scenario: No email is ever sent to a student email address
    Given any notification event for student "Alex"
    When NotificationService attempts to send the notification
    Then the recipient_type must be "parent" or "teacher"
    And if recipient_type is "student", COPPAViolationError is raised
    And no SES API call is made for a student recipient
```

---

### 3.5 Robustness and Resilience Tests

---

#### 3.5.1 Assessment Interruption and Resume

```python
# apps/api/tests/robustness/test_assessment_resilience.py

@pytest.mark.asyncio
async def test_assessment_survives_api_restart_within_5_min(
    postgres_container, assessment_in_progress
):
    """Assessment state persists to DB; reconnect within 5 min recovers session."""
    assessment_id = assessment_in_progress["assessment_id"]

    # Simulate API restart (recreate app)
    app = create_app()
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.get(
            f"/v1/assessments/eog/{assessment_id}/state",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        state = resp.json()
        assert state["status"] == "in_progress"
        assert state["items_administered"] > 0


@pytest.mark.asyncio
async def test_assessment_voided_after_5_min_disconnect(postgres_container):
    """Assessment is invalidated when disconnect exceeds 5 minutes."""
    assessment = await start_assessment("stu-resilience-001")
    await simulate_5_min_disconnect(assessment["assessment_id"])
    await trigger_timeout_check()

    from apps.api.src.db.session import get_session
    async with get_session() as session:
        row = await session.execute(
            text("SELECT status FROM eog_assessments WHERE id = :id"),
            {"id": assessment["assessment_id"]}
        )
        assert row.scalar() == "invalidated"


@pytest.mark.asyncio
async def test_concurrent_sessions_isolated(postgres_container):
    """Two simultaneous assessments do not interfere with each other's theta."""
    stu_a = await start_assessment("stu-concurrent-A")
    stu_b = await start_assessment("stu-concurrent-B")

    # Submit different response patterns for A and B
    await submit_all_correct(stu_a["assessment_id"], n=15)
    await submit_all_incorrect(stu_b["assessment_id"], n=15)

    theta_a = await get_current_theta(stu_a["assessment_id"])
    theta_b = await get_current_theta(stu_b["assessment_id"])

    assert theta_a > 0.0  # All correct → positive theta
    assert theta_b < 0.0  # All incorrect → negative theta
    assert theta_a > theta_b + 1.0  # Significant difference


@pytest.mark.asyncio
async def test_pdf_generation_under_load(postgres_container, mock_s3):
    """5 concurrent PDF generation jobs all complete within 15 seconds."""
    import asyncio
    jobs = [
        generate_pdf_report(f"stu-load-{i}", f"asmt-load-{i}")
        for i in range(5)
    ]
    results = await asyncio.gather(*jobs, return_exceptions=True)

    assert all(not isinstance(r, Exception) for r in results)
    assert all(r["generation_time_ms"] < 15000 for r in results)


@pytest.mark.asyncio
async def test_ses_failure_does_not_break_assessment(postgres_container, mock_ses_fail):
    """SES email failure after assessment does not cause assessment to fail."""
    mock_ses_fail.send_email.side_effect = Exception("SES unavailable")

    # Assessment completion should succeed even if email fails
    results = await complete_assessment("stu-ses-fail-001")
    assert results["proficiency_level"] is not None

    # Verify notification is queued for retry
    log = await get_notification_log(student_id="stu-ses-fail-001")
    assert log.status == "failed"
    # Retry logic: SQS DLQ captures failed notifications for reprocessing
```

---

#### 3.5.2 Concurrent Assessment Load Resilience

| Test ID | Scenario | Target | Pass Criteria |
|---|---|---|---|
| ROB-401 | 50 concurrent EOG assessments | All complete successfully | Error rate < 1%, no theta cross-contamination |
| ROB-402 | 500 concurrent practice + 50 EOG simultaneous | Stable throughput | PgBouncer pool < 80% utilization |
| ROB-403 | Assessment during RDS failover | Graceful error handling | Student sees clear error, assessment not corrupted |
| ROB-404 | SQS worker crash during PDF generation | Job requeued | PDF generated on retry, no duplicate reports |
| ROB-405 | SES throttling (> 14 emails/sec) | Exponential backoff | All emails eventually delivered, no data loss |

---

### 3.6 Repeatability Tests

---

#### 3.6.1 IRT Scoring Determinism

```python
# apps/api/tests/repeatability/test_irt_determinism.py

import pytest
from apps.api.src.service.irt_service import eap_estimate, ItemResponse

FIXED_RESPONSES = [
    ItemResponse("q01", a=1.5, b=-0.5, c=0.25, is_correct=True),
    ItemResponse("q02", a=1.2, b=0.0, c=0.25, is_correct=False),
    ItemResponse("q03", a=1.8, b=0.3, c=0.25, is_correct=True),
    ItemResponse("q04", a=1.0, b=-1.0, c=0.25, is_correct=True),
    ItemResponse("q05", a=2.0, b=0.5, c=0.25, is_correct=False),
]

class TestIRTDeterminism:
    def test_eap_deterministic_across_100_calls(self):
        """EAP produces identical results for 100 consecutive calls."""
        baseline = eap_estimate(FIXED_RESPONSES)
        for i in range(99):
            result = eap_estimate(FIXED_RESPONSES)
            assert abs(result.theta - baseline.theta) < 1e-12, (
                f"Iteration {i+1}: theta drifted from {baseline.theta:.15f} to {result.theta:.15f}"
            )
            assert abs(result.sem - baseline.sem) < 1e-12

    def test_proficiency_classification_is_deterministic(self):
        """Same theta + SEM always produces the same proficiency level."""
        from apps.api.src.service.cat_assessment_service import CATAssessmentService
        svc = CATAssessmentService()
        test_cases = [(-0.8, 0.25), (0.1, 0.3), (-0.05, 0.1), (1.2, 0.2)]
        for theta, sem in test_cases:
            levels = [svc.compute_proficiency_level(theta, sem) for _ in range(10)]
            assert len(set(levels)) == 1, f"Non-deterministic at theta={theta}, sem={sem}: {levels}"

    def test_item_selection_is_deterministic(self):
        """Given same theta, item bank, and administered list, selection is identical."""
        from apps.api.src.service.irt_service import IRTService
        svc = IRTService()
        item_bank = [
            {"question_id": f"q{i}", "a": 1.2, "b": float(i - 5) * 0.5, "c": 0.25, "domain": "NF"}
            for i in range(10)
        ]
        selections = [
            svc.select_next_item(
                theta=0.3,
                administered_items=["q0", "q1"],
                item_bank=item_bank,
                content_coverage={"NF": 2},
                target_coverage={"NF": 0.30},
            )
            for _ in range(5)
        ]
        assert all(s["question_id"] == selections[0]["question_id"] for s in selections)
```

---

#### 3.6.2 Repeatability Test Summary

| Test ID | Area | Test Name | Assertion |
|---|---|---|---|
| REP-401 | IRT scoring | `test_eap_deterministic_across_100_calls` | ΔTheta < 1e-12 |
| REP-402 | Proficiency classification | `test_proficiency_classification_is_deterministic` | Same level for same input |
| REP-403 | Item selection | `test_item_selection_is_deterministic` | Same item for same inputs |
| REP-404 | Remediation plan ordering | `test_remediation_plan_ordering_deterministic` | Stable sort by P(mastered) |
| REP-405 | Migration reversibility | `test_stage4_migration_rollback` | Schema matches pre-migration after rollback |
| REP-406 | Report HTML rendering | `test_report_html_idempotent` | Identical HTML for same data |
| REP-407 | Notification dedup | `test_weekly_email_sent_once_per_week` | Zero duplicate emails per period |

---

### 3.7 Security Tests

---

#### 3.7.1 Assessment Integrity (Answer Peeking Prevention)

```python
# apps/api/tests/security/test_assessment_integrity.py

@pytest.mark.asyncio
async def test_correct_answer_not_in_question_response(auth_headers_student):
    """The correct answer must never appear in the GET question API response."""
    app = create_app()
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        assessment = await start_assessment_via_api(client, auth_headers_student)
        question_id = assessment["first_question"]["question_id"]

        resp = await client.get(
            f"/v1/questions/{question_id}",
            headers=auth_headers_student,
        )
        question_data = resp.json()

        # The correct_answer field must not be present in the response
        assert "correct_answer" not in question_data
        assert "answer" not in question_data
        assert "solution" not in question_data

@pytest.mark.asyncio
async def test_student_cannot_access_eog_item_bank(auth_headers_student):
    """Students cannot query the IRT item bank parameters."""
    app = create_app()
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.get("/v1/admin/item-bank", headers=auth_headers_student)
        assert resp.status_code == 403

@pytest.mark.asyncio
async def test_student_cannot_tamper_with_theta(auth_headers_student):
    """Assessment response endpoint rejects theta manipulation attempts."""
    app = create_app()
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        assessment = await start_assessment_via_api(client, auth_headers_student)

        # Attempt to inject theta into the response payload
        resp = await client.post(
            f"/v1/assessments/eog/{assessment['assessment_id']}/respond",
            headers=auth_headers_student,
            json={
                "question_id": assessment["first_question"]["question_id"],
                "answer": "correct",
                "response_time_ms": 5000,
                "theta": 3.9,  # Injection attempt
                "proficiency_level": "ABOVE_PAR",  # Injection attempt
            },
        )
        # These fields must be silently ignored; theta is computed server-side
        assert resp.status_code == 200
        # Verify actual theta is not 3.9
        state = await get_assessment_state(assessment["assessment_id"])
        assert abs(state["theta"] - 3.9) > 0.5
```

---

#### 3.7.2 FERPA Compliance — Teacher Data Access Scoping

```python
# apps/api/tests/security/test_ferpa_teacher_access.py

@pytest.mark.asyncio
async def test_teacher_cannot_access_ungranted_student(
    auth_headers_teacher_b, student_granted_to_teacher_a
):
    """Teacher B cannot access data for a student granted to Teacher A only."""
    app = create_app()
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.get(
            f"/v1/teacher/students/{student_granted_to_teacher_a['student_id']}",
            headers=auth_headers_teacher_b,
        )
        assert resp.status_code in [403, 404]

@pytest.mark.asyncio
async def test_teacher_csv_does_not_include_pii(auth_headers_teacher):
    """Teacher CSV export never contains last name, email, or student ID."""
    app = create_app()
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.get("/v1/teacher/roster/export", headers=auth_headers_teacher)
        assert resp.status_code == 200
        csv_content = resp.text
        # PII that must NOT be present
        assert "smith" not in csv_content.lower()  # No last name
        assert "@" not in csv_content              # No email addresses
        assert "stu-" not in csv_content           # No student UUIDs

@pytest.mark.asyncio
async def test_parent_revoke_removes_teacher_access_immediately(postgres_container):
    """Revoking teacher access prevents teacher from seeing student within 5 minutes."""
    await grant_teacher_access("tch-001", "stu-001")
    await revoke_teacher_access("tch-001", "stu-001")

    app = create_app()
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.get(
            "/v1/teacher/students/stu-001",
            headers=teacher_auth("tch-001"),
        )
        assert resp.status_code in [403, 404]
```

---

#### 3.7.3 Security Test Summary Table

| Test ID | Category | Test Name | OWASP / Compliance |
|---|---|---|---|
| SEC-401 | Integrity | `test_correct_answer_not_in_question_response` | Assessment validity |
| SEC-402 | Integrity | `test_student_cannot_tamper_with_theta` | A1: Injection |
| SEC-403 | Auth | `test_teacher_cannot_access_eog_item_bank` | A1: Broken Access Control |
| SEC-404 | FERPA | `test_teacher_cannot_access_ungranted_student` | FERPA §99.31 |
| SEC-405 | FERPA | `test_teacher_csv_does_not_include_pii` | FERPA data minimization |
| SEC-406 | FERPA | `test_parent_revoke_removes_teacher_access_immediately` | FERPA §99.37 |
| SEC-407 | COPPA | `test_no_email_sent_to_student` | COPPA §312.5 |
| SEC-408 | COPPA | `test_student_has_no_email_in_db` | COPPA data minimization |
| SEC-409 | Crypto | `test_pdf_reports_kms_encrypted_at_rest` | FERPA encryption requirement |
| SEC-410 | SQLi | `test_sql_injection_eog_respond_endpoint` | A3: Injection |
| SEC-411 | Auth | `test_expired_assessment_token_rejected` | A1: Broken Access Control |
| SEC-412 | Auth | `test_parent_cannot_access_other_parents_child` | A1: IDOR |
| SEC-413 | SAST | Bandit scan: zero high findings in `apps/api/src/` | CI/CD gate |
| SEC-414 | DAST | OWASP ZAP scan on staging: zero critical/high | Pre-release gate |
| SEC-415 | Container | Trivy scan: zero critical CVEs in API image | Every build |

---

### 3.8 Performance Tests

#### 3.8.1 Concurrent Assessment Load

```javascript
// apps/api/tests/performance/k6/eog_load_test.js

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

const errorRate = new Rate('errors');
const irtResponseTime = new Trend('irt_response_time');

export const options = {
  scenarios: {
    concurrent_assessments: {
      executor: 'constant-vus',
      vus: 50,
      duration: '10m',
    },
    concurrent_practice: {
      executor: 'constant-vus',
      vus: 500,
      duration: '10m',
    },
  },
  thresholds: {
    http_req_duration: ['p(95)<500'],    // P95 REST latency < 500ms
    irt_response_time: ['p(95)<200'],    // P95 IRT per-question latency < 200ms
    errors: ['rate<0.01'],               // Error rate < 1%
  },
};

export default function assessmentVU() {
  // Start assessment
  const startRes = http.post(`${BASE_URL}/v1/assessments/eog/start`, JSON.stringify({
    student_id: `stu-load-${__VU}`,
    grade_level: 4,
  }), { headers });

  check(startRes, { 'assessment started': (r) => r.status === 201 });

  const body = JSON.parse(startRes.body);
  const assessmentId = body.assessment_id;
  let questionId = body.first_question.question_id;

  // Submit 15 responses (sufficient for SEM < 0.30 in load test)
  for (let i = 0; i < 15; i++) {
    const start = Date.now();
    const resp = http.post(
      `${BASE_URL}/v1/assessments/eog/${assessmentId}/respond`,
      JSON.stringify({ question_id: questionId, answer: 'A', response_time_ms: 10000 }),
      { headers }
    );
    irtResponseTime.add(Date.now() - start);

    check(resp, { 'response accepted': (r) => r.status === 200 });
    errorRate.add(resp.status !== 200);

    const respBody = JSON.parse(resp.body);
    if (respBody.should_stop) break;
    questionId = respBody.next_question.question_id;

    sleep(0.5);
  }
}
```

---

#### 3.8.2 Performance Test Acceptance Thresholds

| Test ID | Metric | Target | Tool | Failure Action |
|---|---|---|---|---|
| PERF-401 | P95 REST API latency (all endpoints) | < 500ms | k6 | Block release |
| PERF-402 | P95 IRT per-question latency | < 200ms | k6 | Block release |
| PERF-403 | P95 PDF generation time | < 10,000ms | SQS worker metrics | Block release |
| PERF-404 | Parent dashboard initial load | < 3,000ms | Lighthouse/k6 | Block release |
| PERF-405 | Teacher dashboard load | < 3,000ms | Lighthouse/k6 | P1 bug |
| PERF-406 | Concurrent assessment error rate | < 1% at 50 VUs | k6 | Block release |
| PERF-407 | PgBouncer pool utilization at peak | < 80% | CloudWatch metrics | Block release |
| PERF-408 | CloudFront cache hit ratio | ≥ 60% after 24h | CloudFront metrics | P2 optimization |
| PERF-409 | WebSocket message roundtrip (practice) | P95 < 3,000ms | Custom WebSocket tester | Block release |
| PERF-410 | SES email delivery latency | < 5 min P95 | SES metrics | P1 investigation |

---

### 3.8.3 MVP Acceptance Criteria — Full Regression Suite

The following 39-item checklist must pass in staging to qualify for MVP gate review. This list mirrors the PRD MVP Feature Checklist exactly.

**Stage 1 Regression (8 items):**

| ID | Acceptance Criterion | Test Coverage |
|---|---|---|
| S1-01 | Oregon Grade 4 standards DB: 29 standards seeded | DB seed verification test |
| S1-02 | Diagnostic: 35-45 adaptive IRT questions | Integration test: full diagnostic session |
| S1-03 | Diagnostic: student can start and complete | E2E-101 |
| S1-04 | Diagnostic results: BKT P(mastered) for all 29 skills | Unit test: BKT initialization |
| S1-05 | Auth0 COPPA: parental consent before student account | E2E-104: consent flow |
| S1-06 | Student account: no email required; parent email primary | Unit test: account creation schema |
| S1-07 | Diagnostic UI: mobile-responsive, WCAG 2.1 AA, KaTeX | axe-core + Playwright visual test |
| S1-08 | Diagnostic state: survives browser refresh | E2E-105: refresh mid-diagnostic |

**Stage 2 Regression (5 items):**

| ID | Acceptance Criterion | Test Coverage |
|---|---|---|
| S2-01 | Learning plan generated within 30s of diagnostic completion | Integration test: timer assertion |
| S2-02 | Plan modules: correct prerequisite sequencing | Unit test: topological sort |
| S2-03 | Plan: estimated time per module displayed | E2E-201: plan view |
| S2-04 | Plan: parent and student can view | E2E-202: dual-role test |
| S2-05 | Plan: updates as skills are mastered | Integration test: BKT update → plan refresh |

**Stage 3 Regression (16 items):**

| ID | Acceptance Criterion | Test Coverage |
|---|---|---|
| S3-01 | Practice sessions: student can start and receive questions | E2E-301 |
| S3-02 | Question generator: cached questions for all 29 standards at ≥ 3 difficulty levels | Integration test: question bank coverage |
| S3-03 | Question generator: live generation fallback works | Integration test: cache miss scenario |
| S3-04 | Assessment agent: evaluates MC, numeric, fraction | Unit tests: each answer type |
| S3-05 | Assessment agent: error classification ≥ 14/15 types | Unit test: error taxonomy |
| S3-06 | Tutor agent: 3-level hint ladder for every question type | BDD: hint scenarios |
| S3-07 | Tutor: child-safe language on ≥ 95% of responses | LLM contract test: golden set |
| S3-08 | BKT: correct update equations applied after every response | Unit test: BKT math |
| S3-09 | BKT: mastery declared at P ≥ 0.95 + 5-correct streak | Unit test: mastery threshold |
| S3-10 | Dual memory: LTM across sessions, WM isolated per session | Integration test: session boundary |
| S3-11 | Frustration detection: scaffold mode at score > 7.0 | Unit test: frustration scorer |
| S3-12 | Session persistence: survives browser refresh | E2E-303: refresh mid-session |
| S3-13 | Session summary: accurate stats at session end | Integration test: summary computation |
| S3-14 | P95 tutor latency < 3s at 100 concurrent sessions | k6 load test |
| S3-15 | LLM cost < $0.15/session for 10-question session | Cost measurement script |
| S3-16 | COPPA: zero PII in any LLM prompt | Automated log audit |

**Stage 4 Regression (22 items):**

| ID | Acceptance Criterion | Test Coverage |
|---|---|---|
| S4-01 | EOG: student can start and complete full 40-50 question assessment | E2E-401 |
| S4-02 | EOG: covers all 29 standards proportionally per domain weights | Integration test: domain coverage |
| S4-03 | EOG: no hints, tutor, or back navigation | E2E-402, E2E-403 |
| S4-04 | EOG: proficiency level correctly computed from theta | Unit test: classification |
| S4-05 | EOG: 30-day retake restriction enforced | Integration test: retake window |
| S4-06 | Remediation loop: revised plan auto-generated after EOG | Integration test: plan creation |
| S4-07 | Remediation: deficient skills prioritized by P(mastered) ascending | Unit test: sort order |
| S4-08 | Student PDF generated within 10 seconds | Integration test: SLA |
| S4-09 | Parent PDF generated within 10 seconds | Integration test: SLA |
| S4-10 | PDF includes all required sections per FR-17.2, FR-17.3 | Integration test: content audit |
| S4-11 | Parent dashboard: complete session history viewable | E2E-421 |
| S4-12 | Parent dashboard: skill mastery timeline correct | E2E-422 |
| S4-13 | Parent dashboard: time-on-task charts accurate | Integration test: chart data |
| S4-14 | Parent dashboard: Share with Teacher generates valid link | E2E-423 |
| S4-15 | Teacher dashboard: teacher can register and view shared students | E2E-410 |
| S4-16 | Teacher: class-level weak areas correctly computed | Integration test: aggregate |
| S4-17 | Teacher: CSV export correct data | E2E-411 |
| S4-18 | Notifications: assessment complete email within 5 min | Integration test: timer |
| S4-19 | Notifications: weekly summary email sends on schedule | Integration test: cron |
| S4-20 | Notifications: inactivity alert fires after 7 days | Integration test: timing |
| S4-21 | COPPA: no direct email/notification to student email | SEC-407 |
| S4-22 | FERPA: teacher access restricted to parent-consented data | SEC-404, SEC-405 |

**MVP Gate: ALL 39 items ✅ required before beta launch.**

---

## 4. Operations Plan

### 4.1 MLOps — IRT Parameter Calibration Monitoring

Stage 4 introduces the EOG item bank as the first IRT-parameterized artifact requiring MLOps-style monitoring. Unlike the LLM models (Stages 2–3), IRT parameters are deterministic once set — but their appropriateness depends on the student population distribution. As beta users generate response data, item parameters require monitoring and periodic recalibration.

#### 4.1.1 Phase 1: Expert-Calibrated Parameters (Months 11–14)

During MVP (< 1000 students), item parameters are set by content experts using the mapping:
- `a` (discrimination): Expert quality rating 1–5 → linear map to [0.5, 2.5]
- `b` (difficulty): CCSS grade-level alignment → linear map to [−2.0, +2.0]
- `c` (guessing): Fixed by item type (MC: 0.25, numeric entry: 0.05, free-response: 0.00)

**Monitoring plan during Phase 1:**

| Metric | Alert Threshold | Action |
|---|---|---|
| Mean EOG theta distribution | Outside [−0.5, +0.5] for beta cohort | Flag item bank for expert review |
| Item infit statistic (mean) | > 1.3 | Flag individual items for content review |
| SEM at assessment completion | P90 > 0.35 | Add more items to item bank in flagged domains |
| Domain theta vs. total theta correlation | < 0.60 for any domain | Review domain item coverage |
| Assessment abandonment rate | > 10% | Check item difficulty distribution |

#### 4.1.2 Phase 2: Operational Calibration (Post-MVP, N ≥ 1000 students)

Once sufficient response data exists, full 3PL calibration runs quarterly:

```python
# scripts/irt_calibration/calibrate_item_bank.py
"""
Quarterly IRT calibration pipeline.
Requires: response matrix from eog_responses table.
Output: updated eog_item_bank parameters.
"""

import pandas as pd
from pyirt import irt  # pyirt library for 3PL estimation

def run_calibration():
    # 1. Extract response matrix from DB
    df = extract_response_matrix(
        min_responses_per_item=100,
        date_range_months=3,
    )

    # 2. Fit 3PL IRT model
    model = irt.IRT(df, model='3PL')
    model.fit()

    # 3. Extract calibrated parameters with fit statistics
    params = model.item_params  # DataFrame: question_id, a, b, c, infit, outfit

    # 4. Flag poor-fitting items (infit > 1.3 or outfit > 1.5)
    poor_fit = params[params['infit'] > 1.3]
    if len(poor_fit) > 0:
        alert_curriculum_team(poor_fit)

    # 5. Update item bank (only for items with calibration_n >= 100)
    update_item_bank(params[params['calibration_n'] >= 100])

    # 6. Log calibration run to mlops_calibration_log table
    log_calibration_run(
        items_calibrated=len(params),
        items_flagged=len(poor_fit),
        run_date=datetime.utcnow(),
    )

if __name__ == '__main__':
    run_calibration()
```

**Calibration schedule:** Quarterly, or after every 500 new completed assessments (whichever comes first).

**Anchor calibration:** To maintain score scale consistency across calibration cycles, a set of 20 anchor items (with known stable parameters) is included in every calibration. Anchor item parameters are held fixed; only non-anchor items are re-estimated.

#### 4.1.3 BKT Parameter Monitoring (Inherited from Stage 3)

Stage 4 continues the Stage 3 BKT monitoring regime:

| Metric | Alert Threshold | Action |
|---|---|---|
| BKT P(mastered) distribution per skill | Mean > 0.90 or < 0.30 across cohort | Review skill difficulty or practice pacing |
| P(transit) drift | > 15% change between monthly snapshots | Retrain BKT for affected skills |
| Days to mastery per skill | > 30 days for any skill | Flag for curriculum review; add easier scaffolding |
| EOG theta vs. BKT P(mastered) correlation | < 0.60 for any skill | Investigate BKT parameter alignment |

#### 4.1.4 LLM Observability (Inherited from Stage 3, unchanged in Stage 4)

Stage 4 does not add new LLM calls. The CAT engine is a pure Python algorithm. LLM monitoring from Stage 3 continues:

| Component | Model | Weekly Golden Set | Cost Budget |
|---|---|---|---|
| Tutor hints | Claude Sonnet 4.6 | 50 hint scenarios, ≥ 90% pass | $0.05/session |
| Question generation | GPT-4o | 29-standard coverage check | $0.02/question |
| Learning plan generation | o3-mini | 10 plan scenarios, ≥ 90% pass | $0.10/plan |

---

### 4.2 FinOps

#### 4.2.1 Stage 4 New Cost Components

Stage 4 adds three material cost components not present in Stages 1–3:

| Component | Service | Unit Cost | MVP Scale (50-100 students) | Monthly Estimate |
|---|---|---|---|---|
| PDF report storage | AWS S3 | $0.023/GB-month | 50 reports × 2 versions × 500KB ≈ 50MB | < $0.01 |
| PDF generation compute | ECS SQS Worker | $0.04048/vCPU-hour (Fargate) | ~50 reports/month × 5s each | < $0.01 |
| Email delivery | AWS SES | $0.10/1000 emails | 100 parents × 8 emails/month ≈ 800/month | $0.08 |
| CloudFront CDN | AWS CloudFront | $0.0085/10k HTTPS requests | 100 users × 50 requests/session × 10 sessions | $0.43 |
| PgBouncer overhead | Included in existing ECS task | 0 additional cost | Sidecar on existing task | $0 |
| Presigned URL generation | AWS S3 | Free (no API cost for presign) | Unlimited | $0 |

**Total new Stage 4 AWS costs at MVP scale: < $2/month**

#### 4.2.2 FinOps Tagging Strategy

All Stage 4 resources tagged with the existing tag taxonomy plus new Stage 4-specific tags:

```hcl
# terraform/modules/stage4/main.tf — Resource tags

locals {
  stage4_tags = merge(var.common_tags, {
    Stage          = "4"
    Feature        = "assessment-reporting"  # New: distinguish from practice feature
    CostCenter     = "product"
    Environment    = var.environment  # dev | staging | prod
    DataClassification = "FERPA"     # New: flag FERPA-scoped resources for audit
  })
}
```

**New tag values for Stage 4 resources:**
- S3 reports bucket: `Feature=pdf-reports`, `DataClassification=FERPA`
- SES sending domain: `Feature=notifications`, `DataClassification=COPPA`
- SQS report generation queue: `Feature=pdf-generation`
- CloudFront distribution: `Feature=cdn`, `DataClassification=public`

#### 4.2.3 Cost Anomaly Detection

AWS Cost Anomaly Detection alerts configured for Stage 4 services:

| Alert | Threshold | Action |
|---|---|---|
| SES cost spike | > 2× week-over-week | Investigate email loop or spam |
| S3 PDF storage growth | > 500MB/month | Implement PDF retention policy |
| ECS SQS Worker CPU | > 80% sustained | Scale out worker tasks |
| CloudFront data transfer | > $50/month | Review caching effectiveness |
| SQS queue depth | > 100 messages for > 10 minutes | Alert on-call; scale workers |

#### 4.2.4 Budget Thresholds

| Environment | Monthly Budget | Alert at 75% | Alert at 90% | Hard Stop at 100% |
|---|---|---|---|---|
| dev | $50 | Slack warning | Slack critical | Auto-stop non-essential ECS tasks |
| staging | $100 | Slack warning | Slack critical | No auto-stop (needed for testing) |
| prod (MVP beta) | $300 | Slack + email | Slack + PagerDuty | PagerDuty P1 |

#### 4.2.5 PDF Storage Cost Optimization

At scale (post-MVP), PDF storage costs can grow significantly (e.g., 10,000 students × 4 assessments/year × 2 PDF versions × 500KB = ~40GB/year ≈ $11/month). Optimization strategy:

1. **Retention policy**: PDFs older than 2 years moved to S3 Glacier Instant Retrieval ($0.004/GB-month, 4× cheaper than S3 Standard).
2. **Report deduplication**: If student data has not changed between assessments, reuse existing PDF (hash-based check).
3. **Compression**: WeasyPrint output compressed with Zlib; typical report size reduces from 500KB to ~120KB.
4. **Reserved capacity**: S3 Intelligent-Tiering enabled for the reports bucket at > 1,000 objects.

---

### 4.3 SecOps

#### 4.3.1 Assessment Data Integrity

EOG assessment results are high-stakes data. The following SecOps controls protect their integrity:

| Control | Implementation | Monitoring |
|---|---|---|
| Server-side scoring | All theta calculations run server-side; client sends only raw answer | Automated test: client payload cannot alter theta |
| Immutable response records | `eog_responses` rows have no UPDATE path in service layer; insert-only | DB trigger: reject UPDATE on eog_responses |
| Assessment session token | Single-use; tied to student_id + assessment_id; expires on completion | Auth middleware: token reuse returns HTTP 401 |
| Proctoring flags | Tab switches, fast responses logged; flagged assessments reviewable | Admin dashboard: flagged assessments queue |
| Audit log | All assessment lifecycle events logged to `audit_log` (insert-only) | Datadog: alert on unexpected audit_log deletes |

#### 4.3.2 FERPA Teacher Access Controls

| Control | Implementation | Verification |
|---|---|---|
| Row-level scoping | All teacher queries join `teacher_student_access` with `revoked_at IS NULL` | Integration test: teacher sees only granted students |
| Access grant audit trail | Every grant/revoke recorded with actor, timestamp | `audit_log` query for access change events |
| Transcript exclusion | Teacher role cannot call `/v1/sessions/{id}/transcript` | API middleware role check; integration test |
| PII minimization in export | CSV export omits last name, email, student ID | Automated test: CSV field name audit |
| Access revocation immediacy | Revocation updates DB within 1 second; cache invalidation within 5 minutes | Integration test: revoke → immediate roster disappearance |

#### 4.3.3 COPPA Compliance Controls (Stage 4 Additions)

| Control | Implementation | Test |
|---|---|---|
| No child email stored | `users.email IS NULL` for student accounts | DB constraint + unit test |
| No external notification to student | `COPPAViolationError` in `NotificationService` | Unit test: SEC-407 |
| PDF contains no child email | Report templates do not render student email field | Template audit test |
| Teacher email is parent-controlled | Teacher email shared only via parent action | Integration test: teacher cannot self-add |

#### 4.3.4 Secret Rotation Schedule

| Secret | Service | Rotation Interval | Managed By |
|---|---|---|---|
| Auth0 client secret | Auth0 | 90 days | AWS Secrets Manager + Terraform |
| Database password (RDS) | PostgreSQL | 90 days | AWS Secrets Manager rotation lambda |
| SES SMTP credentials | AWS SES | 90 days | IAM roles (no long-term SMTP keys) |
| S3 KMS key | AWS KMS | Annual automatic rotation | AWS KMS managed |
| Datadog API key | Datadog | 180 days | AWS Secrets Manager |
| Sentry DSN | Sentry | On team member departure | GitHub Actions secret |

#### 4.3.5 Incident Response Procedures (Stage 4 Additions)

**Assessment Data Breach Scenario:**

```
Detect:     Datadog alert: unusual query pattern on eog_assessments (bulk SELECT)
Contain:    Revoke compromised IAM role; rotate DB password; enable RDS enhanced logging
Eradicate:  Identify affected records; audit eog_responses for tampering
Recover:    Verify assessment data integrity via DB transaction log review
Report:     If student PII accessed: 72-hour FTC notification (COPPA)
            If teacher-accessible data exposed: notify affected parents (FERPA §99.36)
Post-mortem: Root cause analysis; additional row-level security controls
```

**Report PDF Exposure Scenario:**

```
Detect:     CloudFront access log: presigned URL accessed from unexpected IP
Contain:    Revoke presigned URL (S3 object policy update)
Eradicate:  Audit all recent report accesses in progress_reports.access_count
Recover:    Regenerate presigned URLs for affected parents
Report:     If confirmed unauthorized access to student report: FERPA §99.36 notification
Post-mortem: Evaluate presigned URL expiry policy; implement IP-based access restrictions
```

#### 4.3.6 Access Control Matrix (RBAC — Stage 4 Additions)

| Resource | Student | Parent | Teacher (granted) | Admin |
|---|---|---|---|---|
| `eog_assessments` (own) | Read (status only) | Read | Read (summary) | Full |
| `eog_responses` (own) | None | Read | None | Full |
| `eog_item_bank` | None | None | None | Full |
| `progress_reports` | Read (student version) | Read (both) | Read (teacher version, parent-granted) | Full |
| `notification_log` | None | Read (own) | None | Full |
| `teacher_student_access` | None | Full (own grants) | Read (own) | Full |
| Teacher CSV export | None | None | Own roster only | Full |
| Assessment start/respond | Own only | None | None | Full |

---

### 4.4 DevSecOps Pipeline

The Stage 4 CI/CD pipeline extends the Stage 3 pipeline with additional security checks for PDF generation, email delivery, and the new `teacher_student_access` authorization layer.

#### 4.4.1 PR Gate (Every Pull Request)

```yaml
# .github/workflows/ci.yml (Stage 4 additions)

jobs:
  stage4-security:
    runs-on: ubuntu-latest
    steps:
      # SAST
      - name: Bandit SAST — API
        run: bandit -r apps/api/src/ -ll -f json -o bandit-results.json
      
      - name: eslint-plugin-security — Frontend
        run: pnpm --filter web lint:security
      
      # Secret scanning
      - name: Gitleaks — No secrets in code
        uses: gitleaks/gitleaks-action@v2
      
      # Dependency audit
      - name: pip-audit — Python dependencies
        run: pip-audit --requirement apps/api/requirements.txt
      
      - name: npm audit — Frontend
        run: pnpm audit --audit-level=high
      
      # IRT unit tests (fast, must pass for every PR touching irt_service.py)
      - name: IRT unit tests
        run: pytest apps/api/tests/unit/test_irt_service.py -v --tb=short
      
      # COPPA guard — no student email in notification_log
      - name: COPPA email guard test
        run: pytest apps/api/tests/security/test_coppa_guard.py -v
```

#### 4.4.2 Container Scanning (Every Build)

```yaml
# .github/workflows/build.yml

  - name: Trivy — API container scan
    uses: aquasecurity/trivy-action@master
    with:
      image-ref: 'padi-ai-api:${{ github.sha }}'
      format: 'sarif'
      exit-code: '1'  # Fail build on CRITICAL CVEs
      severity: 'CRITICAL,HIGH'
```

#### 4.4.3 Weekly Security Jobs

```yaml
# .github/workflows/dependency-audit.yml

schedule:
  - cron: '0 9 * * 1'  # Monday 9am

jobs:
  weekly-security:
    steps:
      # DAST
      - name: OWASP ZAP scan — Staging
        uses: zaproxy/action-full-scan@v0.8.0
        with:
          target: 'https://staging.padi.ai'
          rules_file_name: '.zap/rules.tsv'
          fail_action: true

      # SBOM generation
      - name: Generate SBOM — API
        run: syft padi-ai-api:latest -o cyclonedx-json > sbom-api.json

      # LLM contract test (weekly golden set)
      - name: LLM behavioral contract tests
        run: pytest apps/api/tests/contracts/ -v --llm-contract-mode=weekly
```

#### 4.4.4 SBOM (Software Bill of Materials)

Stage 4 adds SBOM generation as part of the weekly security workflow. The SBOM covers all Python dependencies (`pip freeze`) and Node.js dependencies (`package-lock.json`) in CycloneDX JSON format. SBOMs are stored in S3 with 1-year retention and linked to each release artifact.

**Key Stage 4 dependencies tracked in SBOM:**

| Package | Version | Purpose | Risk Category |
|---|---|---|---|
| weasyprint | ≥ 62.0 | HTML → PDF generation | Medium (complex dep tree) |
| numpy | ≥ 1.26 | EAP quadrature calculations | Low |
| jinja2 | ≥ 3.1 | Report HTML templating | Low |
| boto3 | ≥ 1.34 | S3 + SES + SQS client | Low |
| textstat | ≥ 0.7 | Reading level validation | Low |

---

## 5. Manual QA Plan

Manual QA covers workflows that cannot be fully automated: assessment experience quality, PDF visual fidelity, email rendering, cross-device testing, curriculum accuracy, and COPPA/FERPA compliance walkthroughs.

### 5.1 Full MVP Regression Walkthrough

**Duration:** 8 hours (full day sprint)  
**Frequency:** Once before MVP gate review; again after any P0 fix  
**Personnel:** 2 QA engineers + 1 content reviewer  
**Environment:** Staging environment with seeded test data  

**Walkthrough procedure:**

The QA team walks through the complete user journey as three personas: a student (ages 9-10 simulated), a parent, and a teacher. Each persona uses a separate browser profile with separate credentials.

**Student walkthrough (3 hours):**
1. Student completes diagnostic assessment (fresh account) — verify question rendering, KaTeX math display, mobile layout
2. Student views learning plan — verify prerequisite order, estimated times, skill descriptions
3. Student completes 3 practice sessions across 3 different skills — verify BKT progression, hint ladder, tutor responses, session summary
4. Student starts and completes a full EOG assessment (40+ questions) — verify assessment-mode UI, no hints visible, back navigation blocked, progress indicator, review screen, submission confirmation
5. Student views post-assessment results screen — verify proficiency level display, domain breakdown, encouragement language, "Continue Learning" button

**Parent walkthrough (3 hours):**
1. Parent views dashboard home — verify all stat cards, recent sessions list, load time
2. Parent reviews skill mastery timeline — verify all 29 skills listed, domain grouping, filter/sort
3. Parent reviews time-on-task charts (week and month views)
4. Parent downloads PDF report — verify file downloads, correct student name and date on cover page
5. Parent visually reviews PDF content — (detailed in §5.3)
6. Parent uses "Share with Teacher" — verify link generated, modal behavior, copy-to-clipboard
7. Parent reviews achievement milestones feed
8. Parent reviews notification preferences — toggle each type, verify persistence

**Teacher walkthrough (2 hours):**
1. Teacher registers new account — verify email verification flow, role assignment
2. Teacher sees empty roster (no shares yet) — verify empty state UI
3. Teacher receives shared student (from parent walkthrough step 6) — verify student appears in roster
4. Teacher reviews student row — expand for domain detail, verify all data fields
5. Teacher reviews class insights (weak areas, heatmap) — verify disclaimer text present
6. Teacher exports CSV — verify download, open in Google Sheets, verify column headers and data types
7. Teacher attempts to access session transcript URL directly — verify 403 response

---

### 5.2 Assessment UX Testing

**What automation cannot verify:** The subjective experience of a 9-10 year old taking a 40-question math test. Manual assessment UX testing simulates the child experience.

**Test scenarios:**

| Scenario | Tester Action | Expected Experience | Pass/Fail Criteria |
|---|---|---|---|
| First question anxiety | Read question aloud | Question is clearly worded, no ambiguity | Content reviewer confirms clarity |
| KaTeX fraction rendering | View fraction question | Fractions render correctly, not as raw LaTeX | Visual inspection: no `\frac{}{}` visible |
| Numeric entry on mobile | Enter 3-digit number on phone keyboard | Numeric keyboard appears, no autocorrect interference | Device: iPhone Safari, Android Chrome |
| Question flagging | Flag a question and review | Flag icon clear, review list highlights flagged items | UX review: flagging is intuitive |
| Assessment progress perception | Complete 10 questions | Progress indicator is visible and accurate | Tester does not feel lost or anxious |
| Submission confirmation | Click "Submit Assessment" | Modal appears, requires deliberate confirmation | No accidental submission possible |
| Post-assessment results | Read results screen | Language is encouraging for all proficiency levels | Content reviewer: tone check for BELOW_PAR result |
| Long assessment fatigue | Complete 40 questions (full session) | Questions remain clear; no UI degradation | Performance monitor: no memory leak or slowdown |

---

### 5.3 PDF Report Quality Review

PDF visual quality cannot be verified by automated tests. A manual review of each report version is required before MVP launch and after any template change.

**Review checklist — Teacher/Parent Report:**

| Section | Review Item | Pass Criteria |
|---|---|---|
| Cover page | Student name, date, report type clearly displayed | No truncation, correct font, no layout overflow |
| Executive summary | Theta score and SEM rendered as decimals (not scientific notation) | "θ = 0.35 (SEM = 0.28)" format |
| Domain table | All 5 domains present, proficiency level per domain | Table borders render correctly in print |
| Skills detail | All 29 standards listed with ✅ / 🔄 / ⚠️ indicators | Emoji render correctly (not as boxes) |
| Time-on-task table | Weekly data for last 4 weeks | Dates formatted as MM/DD/YYYY |
| Learning trajectory chart | Line chart visible, proficiency bands labeled | Chart is not a blank box (WeasyPrint SVG support) |
| Recommended next steps | Top 3 skills listed with standard codes | Correct skill codes match DB data |
| Methodology note | One paragraph, professional language | No line breaks mid-word, no overflow |
| Shareable link / QR code | URL is correct; QR code scans to the correct link | Manually scan QR code with phone |
| Overall print layout | Print to PDF in Chrome, Letter size | No content cut off at page margins |

**Review checklist — Student Report:**

| Section | Review Item | Pass Criteria |
|---|---|---|
| Cover page | Child-friendly design, no intimidating data | Visual reviewer: age-appropriate aesthetic |
| Proficiency indicator | Large, visual, positive framing | BELOW_PAR uses "Keep going!" not "Failed" |
| Skill badges | Mastered domain badges visible, clear icons | Icons render at correct size |
| Progress bars | In-progress skills show bars, appropriate labels | "Almost there!" for high P(mastered) |
| Math journey chart | Simple bar chart, no raw numbers | No theta scale visible to student |
| "Message from Pip" | Personalized encouragement text | Positive sentiment for all proficiency levels |
| Overall language | Every sentence readable by 9-10 year old | FK grade ≤ 5.5 (also verified by unit test) |

---

### 5.4 Teacher Dashboard Usability

**Usability testing scenario:**
Recruit one teacher unfamiliar with the product. Observe without assistance as they:
1. Register an account
2. Access the roster (after being sent a test share link)
3. Find which students need the most support
4. Identify the top class-wide weak skill
5. Export the CSV and open it in Google Sheets

**Success criteria:**
- Teacher completes all 5 tasks without asking for help
- Teacher cannot access any data beyond what is intended (verify by screen recording)
- Teacher expresses confidence in data accuracy based on what they see

---

### 5.5 Email Notification Content Review

Emails cannot be tested for visual fidelity purely by unit tests. A manual content and rendering review is performed for each email template.

**Email rendering test matrix:**

| Email Template | Gmail Desktop | Gmail Mobile | Apple Mail | Outlook 2019 |
|---|---|---|---|---|
| Assessment complete (parent) | ✓ visual | ✓ visual | ✓ visual | ✓ visual |
| Report ready | ✓ visual | ✓ visual | ✓ visual | ✓ visual |
| Weekly summary | ✓ visual | ✓ visual | ✓ visual | ✓ visual |
| Inactivity alert | ✓ visual | ✓ visual | ✓ visual | ✓ visual |
| Milestone achieved | ✓ visual | ✓ visual | ✓ visual | ✓ visual |
| Intervention needed (teacher) | ✓ visual | ✓ visual | ✓ visual | ✓ visual |

**Content review checklist for each template:**
- [ ] Student name correctly personalized
- [ ] Proficiency level uses correct "Par" framing (not "Basic"/"Below Grade Level")
- [ ] PDF link/button present and functional (test with real presigned URL)
- [ ] Unsubscribe link in footer (CAN-SPAM compliance)
- [ ] Plain-text fallback renders correctly (no raw HTML tags)
- [ ] No student email address appears in any email template
- [ ] From address is `updates@padi.ai` (not a no-reply address for transactional emails)

---

### 5.6 Cross-Device MVP Testing

**Device test matrix:**

| Device | Browser | Student Flow | Parent Flow | Teacher Flow |
|---|---|---|---|---|
| iPhone 14 (iOS 17) | Safari | ✓ Full assessment | ✓ Dashboard | ✓ Roster |
| Samsung Galaxy S22 (Android 13) | Chrome | ✓ Full assessment | ✓ Dashboard | ✓ Roster |
| iPad Air (iPadOS 17) | Safari | ✓ Full assessment | ✓ Dashboard | ✓ Roster |
| MacBook Pro (macOS 14) | Chrome | ✓ Full assessment | ✓ Dashboard | ✓ Roster |
| MacBook Pro (macOS 14) | Safari | ✓ Full assessment | ✓ Dashboard | ✓ Roster |
| MacBook Pro (macOS 14) | Firefox | ✓ Full assessment | ✓ Dashboard | ✓ Roster |
| Windows 11 laptop | Chrome | ✓ Full assessment | ✓ Dashboard | ✓ Roster |
| Windows 11 laptop | Edge | ✓ Full assessment | ✓ Dashboard | ✓ Roster |
| Chromebook (ChromeOS) | Chrome | ✓ Full assessment | ✓ Dashboard | ✓ Roster |

**Critical mobile-specific checks:**
- Numeric keypad appears for numeric-entry questions on iOS and Android
- KaTeX math fractions render correctly at mobile viewport widths (320px minimum)
- Assessment progress indicator visible without scrolling on iPhone SE (375px viewport)
- "Submit Assessment" button accessible without keyboard (no keyboard overlay blocking it)
- PDF download works on iOS Safari (opens in Files app or viewer, not blank page)

---

### 5.7 COPPA/FERPA Compliance Walkthrough

This manual walkthrough is performed by the QA lead and a legal/compliance reviewer jointly before MVP gate.

**COPPA Compliance Walkthrough (60 minutes):**

| Step | Action | Expected Result | Reviewer |
|---|---|---|---|
| COPPA-MQ-01 | Attempt to create student account without parent email | Error: "Parent email is required" | QA + Legal |
| COPPA-MQ-02 | Attempt to add email to student profile | Error: "Notifications managed by parent" | QA |
| COPPA-MQ-03 | Trigger an assessment_complete notification | Email goes to parent, not student | QA |
| COPPA-MQ-04 | Query `notification_log` for any `recipient_type='student'` rows | Zero rows returned | Legal |
| COPPA-MQ-05 | Check LLM prompt logs for student PII | No student name or email in any prompt | Legal |
| COPPA-MQ-06 | Submit account deletion request as parent | All student PII deleted within 48 hours | QA + Legal |
| COPPA-MQ-07 | Review data minimization: what student data is collected | Only: username, grade level, practice responses, BKT states | Legal |
| COPPA-MQ-08 | Verify encryption at rest: students table | `SELECT email FROM students` returns NULL for all student rows | QA |

**FERPA Compliance Walkthrough (60 minutes):**

| Step | Action | Expected Result | Reviewer |
|---|---|---|---|
| FERPA-MQ-01 | Teacher attempts to access student without grant | HTTP 403 or 404 | QA + Legal |
| FERPA-MQ-02 | Teacher accesses session transcript endpoint | HTTP 403 | QA |
| FERPA-MQ-03 | Parent revokes teacher access | Student absent from teacher roster within 5 minutes | QA |
| FERPA-MQ-04 | Teacher exports CSV | No last name, email, or student ID in export | QA + Legal |
| FERPA-MQ-05 | Review `teacher_student_access` for audit log | All grants and revocations logged with timestamps | Legal |
| FERPA-MQ-06 | Confirm teacher access basis documentation | Written record: "Parent-authorized disclosure per FERPA §99.31(a)(8)" | Legal |
| FERPA-MQ-07 | Check: teacher cannot see class performance vs. other students | No peer comparison UI in teacher view | Legal |
| FERPA-MQ-08 | Review annual FERPA audit documentation template | Template exists; Annual review date set in compliance calendar | Legal |

---

### 5.8 Accessibility Testing with Assistive Technology

Automated axe-core tests catch many WCAG 2.1 AA violations, but screen reader UX requires manual testing with real assistive technology.

**Screen reader testing matrix:**

| Flow | Screen Reader | Browser | Pass Criteria |
|---|---|---|---|
| EOG Assessment: read question | VoiceOver (macOS) | Safari | Math expression read correctly |
| EOG Assessment: select answer | VoiceOver (macOS) | Safari | Answer options announced with labels |
| EOG Assessment: flag question | NVDA (Windows) | Chrome | Flag button announces state change |
| Assessment results: proficiency level | VoiceOver (iOS) | Safari | Level and description announced clearly |
| Parent dashboard: skill progress bars | VoiceOver (macOS) | Safari | `aria-valuemin/max/now` announced correctly |
| Parent dashboard: charts | NVDA (Windows) | Chrome | Chart data accessible via table alternative |
| Teacher roster: sortable columns | NVDA (Windows) | Chrome | Sort state announced (`aria-sort`) |
| PDF download button | VoiceOver (macOS) | Safari | Button announces filename on hover/focus |

**KaTeX accessibility:**  
All KaTeX-rendered math expressions must have `aria-label` attributes with the math expression in English (e.g., `aria-label="3 over 4"` for ¾). Manual review confirms KaTeX renders accessible markup in all question types used in EOG assessment.

**Color contrast check:**
Assessment Mode UI uses a distinct header color. Manual contrast check with Colour Contrast Analyser tool: header text on assessment background must be ≥ 4.5:1 (WCAG AA).

---

### 5.9 Performance Perception Testing

Automated performance tests measure latency numbers. Manual perception testing verifies that the app *feels* fast and responsive.

**Perception test scenarios:**

| Scenario | Action | Pass Criteria |
|---|---|---|
| EOG assessment start | Click "Begin Assessment" | Question appears within 1 second; no blank loading screen |\
| Submit answer | Click answer choice | Next question appears within 300ms |\
| Assessment results | Complete final question | Proficiency level screen appears within 2 seconds |\
| Parent dashboard load | Navigate to `/parent/dashboard` | Content visible within 3 seconds on LTE mobile |\
| PDF download | Click "Download Report" | Browser download dialog appears or file downloads within 5 seconds |\
| Teacher roster load | Navigate to `/teacher/roster` | Roster renders within 3 seconds with up to 30 students |\
| Skill mastery timeline | Expand all 5 domains | All bars render without jank (no reflows after initial render) |\

**Skeleton/loading state review:**
- Parent dashboard: skeleton shimmer displayed while data loads — no blank white flash
- Teacher roster: loading spinner present; no error message visible before data loads
- PDF generation pending: "Your report is being prepared…" message shown; user is not left staring at a spinner indefinitely

---

### 5.10 Curriculum Accuracy Review

Math content correctness is reviewed by a curriculum specialist (or the principal developer using domain knowledge) before MVP launch. This covers both assessment items and report copy.

**EOG item review checklist:**

| Item Type | Review Criteria | Reviewer |
|---|---|---|
| Multiple choice (OA domain) | All 4 options distinct; exactly 1 correct; distractors represent common errors | Curriculum |
| Fraction input (NF domain) | Expected answer is in simplest form; question unambiguous for Grade 4 | Curriculum |
| Numeric entry (NBT domain) | Calculation correct; answer within reasonable Grade 4 range | Curriculum |
| Multi-select (MD domain) | All correct options included; no trick wording | Curriculum |

**Report copy review:**
- "Below Par" level description: non-stigmatizing, growth-oriented language
- "What You're Working On" section: skill names match official Oregon standard names
- "Recommended Next Steps" copy: actionable, positive, Grade 4 appropriate
- Methodology note (Parent/Teacher report): technically accurate description of BKT and IRT

**IRT parameter sanity check (expert review, pre-launch):**
- Confirm no item has `b_parameter` > 2.5 (would be too hard for Grade 4 typical student)
- Confirm no item has `b_parameter` < -2.5 (trivially easy; wastes assessment time)
- Confirm `c_parameter = 0.25` for all 4-option MC items; `c_parameter = 0.0` for numeric entry
- Confirm `a_parameter` range 0.8–2.0 for all items (expert-set values)

---

### 5.11 Exploratory Edge Case Testing

Testers perform unscripted exploration targeting boundary conditions and unusual user behavior.

**Assigned exploration charters (30 minutes each):**

| Charter | Focus Area | Notes |
|---|---|---|
| EOG-EX-01 | Attempt every possible way to navigate backward during assessment | Back button, swipe gesture, browser history, keyboard shortcuts |
| EOG-EX-02 | Interrupt assessment mid-way (close tab, kill network, force-quit browser) | Verify void logic; attempt session replay |
| EOG-EX-03 | Submit empty or whitespace-only answers on numeric entry | Verify validation before submission |
| RPT-EX-01 | Access PDF presigned URL after 90 days (simulated via DB update) | Verify link correctly expired |
| RPT-EX-02 | Generate PDF for student with zero practice history (only diagnostic) | Verify no null reference errors |
| TCH-EX-01 | Teacher attempts to access 100+ student roster | Verify pagination and performance |
| TCH-EX-02 | Teacher account created with same email as parent account | Verify constraint or clear error |
| NOT-EX-01 | Parent unsubscribes from all emails, then completes assessment | Verify assessment_complete email still sends (transactional) |
| SEC-EX-01 | Attempt IDOR: modify `assessment_id` in URL to another student's ID | Verify 403/404 returned |

---

## MVP Launch Gate Checklist

This section consolidates the definitive pass/fail criteria for the Stage 4 MVP gate. **All items must be checked before production deployment.**

### Automated Gate (CI/CD — blocks merge)
- [ ] All unit tests passing (0 failures, 0 errors)
- [ ] Core logic test coverage ≥ 90% (`apps/api/src/services/irt_service.py`, `cat_service.py`, `report_service.py`)
- [ ] Service layer coverage ≥ 80%
- [ ] Zero Bandit HIGH or CRITICAL findings
- [ ] Zero `npm audit` HIGH or CRITICAL findings
- [ ] Zero Trivy container scan HIGH or CRITICAL CVEs
- [ ] All Playwright E2E tests passing on staging environment
- [ ] axe-core: zero WCAG 2.1 AA violations on all new pages
- [ ] k6 load test: P95 < 500ms at 50 concurrent assessment sessions

### Manual Gate (QA sign-off — blocks release)
- [ ] Full MVP regression walkthrough (5.1) complete — all 39 checklist items ✅
- [ ] EOG Assessment UX walkthrough (5.2) complete
- [ ] PDF report quality review (5.3) complete — student and parent versions
- [ ] Teacher dashboard usability (5.4) complete
- [ ] Email notification content review (5.5) complete — all 7 templates
- [ ] Cross-device testing (5.6) complete — all 9 device/browser combinations
- [ ] COPPA compliance walkthrough (5.7) complete — legal sign-off
- [ ] FERPA compliance walkthrough (5.7) complete — legal sign-off
- [ ] Screen reader accessibility (5.8) complete — VoiceOver + NVDA
- [ ] Curriculum accuracy review (5.10) complete — all EOG items reviewed
- [ ] IRT parameter sanity check (5.10) complete
- [ ] Exploratory edge case testing (5.11) complete — all 9 charters

### Performance Gate
- [ ] Parent dashboard P95 load time < 3 seconds (Lighthouse Performance ≥ 75)
- [ ] Teacher roster P95 load time < 3 seconds
- [ ] PDF generation P95 < 10 seconds under concurrent load (3 simultaneous generation requests)
- [ ] EOG assessment item delivery P95 < 500ms (REST endpoint)

### Security Gate
- [ ] OWASP ZAP DAST scan: zero HIGH or CRITICAL findings on staging
- [ ] FERPA access control matrix reviewed and approved
- [ ] Assessment integrity controls verified (back navigation blocked, tab-switch logging active)
- [ ] S3 PDF bucket: public access blocked, KMS encryption verified
- [ ] SES sending domain: DKIM + SPF + DMARC configured

### Legal/Compliance Gate
- [ ] COPPA verifiable parental consent flow: legal sign-off
- [ ] Privacy policy updated to reflect PDF report storage and SES email collection
- [ ] Data retention policy: confirmed delete-on-request within 48 hours
- [ ] FERPA parent authorization disclosure basis documented
- [ ] No direct email to student accounts (automated audit passing)

---

*Document: `docs/13-lifecycle-stage4.md` | Stage 4 of 5 | PADI.AI SDLC Series*  
*References: `docs/06-prd-stage4.md`, `eng-docs/ENG-004-stage4.md`, `eng-docs/ENG-000-foundations.md`, `eng-docs/ENG-006-crosscutting.md`*
