# Engineering Plan — Stage 4: Summative Assessment, Reporting & MVP Hardening

**Document ID:** ENG-004  
**Version:** 1.0  
**Stage:** 4 of 6 — **MVP Milestone**  
**Timeline:** Months 11–14  
**Status:** Draft  
**Last Updated:** 2026-04-04  
**Author:** Principal AI Systems Architect  

> **Stage 4 Solo Development Estimate:** 150–200 agent-hours | Calendar: 5–7 months | **MVP Milestone**  
> **Hardest part:** 3PL IRT implementation + EAP theta estimation (40–55 hrs) — read the academic references in ENG-004 §IRT section before starting; do not estimate this lightly.  
> **Quick win:** PDF report pipeline (WeasyPrint) can be built in 20–25 hrs and provides high parent-visible value early.

---

## Executive Summary

Stage 4 represents the MVP milestone for MathPath Oregon. This stage adds three critical capabilities: (1) a full IRT-based summative end-of-grade (EOG) assessment engine using the 3-Parameter Logistic model with EAP theta estimation, (2) teacher and parent reporting dashboards with PDF report generation, and (3) comprehensive MVP hardening including performance optimization, security audits, COPPA/FERPA compliance verification, and production readiness.

**Key Deliverables:**
- Computer Adaptive Testing (CAT) engine with 3PL IRT model
- EAP theta estimation with Gaussian quadrature (61 quadrature points)
- Maximum Fisher Information item selection with exposure control
- Proficiency classification aligned with Oregon OSAS 4-level system
- Teacher dashboard with per-student and class-level progress views
- Parent dashboard with child-appropriate progress summaries
- PDF report generation (WeasyPrint) with S3 storage and presigned URLs
- Email notification system (AWS SES) for assessment completion and milestones
- Performance hardening for 500 concurrent practice + 50 concurrent assessment sessions
- COPPA/FERPA compliance verification and audit trail

---

## 1. High-Level Architecture

### 1.1 System Evolution (What Changes from Previous Stage)

**Existing (end of Stage 3):**
- Next.js 15 web app on Vercel — student dashboard, practice UI, learning plan view
- FastAPI API server on AWS ECS — REST + WebSocket, embedded Agent Engine with LangGraph
- PostgreSQL 17 on RDS — all data tables through Stage 3
- Redis 7 on ElastiCache — sessions, working memory, BKT cache, LangGraph checkpoints
- SQS + Worker — async question generation
- S3 — static assets, content media

**New in Stage 4:**

| Component | Type | Description |
|-----------|------|-------------|
| CAT Assessment Engine | Python module (embedded in FastAPI) | IRT 3PL adaptive test with EAP scoring |
| IRT Item Bank | PostgreSQL table | Calibrated item parameters (a, b, c) per question |
| Report Generator | FastAPI + WeasyPrint | HTML → PDF report generation pipeline |
| Notification Service | FastAPI + AWS SES | Email notifications for assessments, milestones |
| Teacher Dashboard | Next.js pages | Class roster, per-student progress, assessment results |
| Parent Dashboard | Next.js pages | Child progress summary, assessment reports, milestone feed |
| PDF Storage | S3 bucket | Generated PDF reports with presigned URL access |
| PgBouncer | Sidecar container (ECS) | Connection pooling for PostgreSQL under load |
| CloudFront | CDN | Static asset caching for frontend performance |

**Architectural Decisions:**

1. **CAT Engine is NOT a LangGraph graph.** Unlike the practice engine (Stage 3), the summative assessment is a straightforward sequential algorithm (present item → collect response → update theta → check stopping → repeat). LangGraph's overhead adds no value here. The CAT engine is a plain Python service class.

2. **Reports generated asynchronously.** PDF generation via WeasyPrint is CPU-intensive (2–5 seconds). Reports are generated in a background task (SQS worker) and stored in S3. The API returns a presigned URL when ready.

3. **PgBouncer added as ECS sidecar.** At 500 concurrent WebSocket sessions + 50 concurrent assessments, PostgreSQL connection management becomes critical. PgBouncer in transaction pooling mode keeps connections efficient.

### 1.2 Updated Container Diagram (C4 Level 2)

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                    MathPath Oregon — Stage 4 (MVP)                             │
│                       Container Diagram (C4 L2)                                │
├────────────────────────────────────────────────────────────────────────────────┤
│                                                                                │
│  ┌────────────────────────────┐      ┌──────────────────────────────────────┐  │
│  │    Next.js 15 Web App      │      │     FastAPI API Server (ECS)         │  │
│  │       (Vercel)             │      │                                      │  │
│  │                            │      │  ┌──────────┐  ┌────────────────┐   │  │
│  │  - Student Dashboard       │ WSS  │  │ REST API │  │ WebSocket      │   │  │
│  │  - Practice UI             ├─────►│  │          │  │ /ws/practice   │   │  │
│  │  - Assessment UI (NEW)     │ HTTPS│  │ + assess │  │                │   │  │
│  │  - Teacher Dashboard (NEW) ├─────►│  │ + report │  └────────────────┘   │  │
│  │  - Parent Dashboard (NEW)  │      │  │ + notify │                       │  │
│  │  - Report Viewer (NEW)     │      │  └────┬─────┘                       │  │
│  └─────────────┬──────────────┘      │       │                             │  │
│                │                      │  ┌────┴────────────────────────┐    │  │
│                │ CDN                  │  │      Agent Engine           │    │  │
│                ▼                      │  │   (LangGraph — Stage 3)    │    │  │
│  ┌────────────────────────────┐      │  └─────────────────────────────┘    │  │
│  │       CloudFront (NEW)     │      │  ┌─────────────────────────────┐    │  │
│  │  - Static assets           │      │  │   CAT Assessment Engine     │    │  │
│  │  - Next.js static pages    │      │  │   (IRT 3PL + EAP) (NEW)    │    │  │
│  └────────────────────────────┘      │  └─────────────────────────────┘    │  │
│                                      │  ┌─────────────────────────────┐    │  │
│                                      │  │   PgBouncer (sidecar) (NEW) │    │  │
│                                      │  │   pool_mode=transaction     │    │  │
│                                      │  └──────────────┬──────────────┘    │  │
│                                      └─────────────────┼──────────────────┘  │
│                                                        │                      │
│                  ┌─────────────────────────┬────────────┤                      │
│                  │                         │            │                      │
│                  ▼                         ▼            ▼                      │
│  ┌──────────────────────────┐  ┌──────────────────┐  ┌────────────────────┐  │
│  │   PostgreSQL 17 (RDS)    │  │ Redis 7           │  │  AWS SQS           │  │
│  │                          │  │ (ElastiCache)     │  │                    │  │
│  │  + eog_assessments (NEW) │  │  (unchanged)      │  │  - Question gen    │  │
│  │  + eog_responses (NEW)   │  │                   │  │  - Report gen (NEW)│  │
│  │  + eog_item_bank (NEW)   │  │                   │  │                    │  │
│  │  + progress_reports (NEW)│  │                   │  └────────┬───────────┘  │
│  │  + teacher_access (NEW)  │  │                   │           │              │
│  │  + notification_log (NEW)│  │                   │           ▼              │
│  │  + remediation_plans(NEW)│  │                   │  ┌────────────────────┐  │
│  └──────────────────────────┘  └───────────────────┘  │  SQS Workers (ECS) │  │
│                                                       │  - Question gen     │  │
│  ┌──────────────────────────┐  ┌───────────────────┐  │  - Report gen (NEW)│  │
│  │       AWS S3              │  │   AWS SES (NEW)   │  └────────────────────┘  │
│  │  - Static assets          │  │                   │                          │
│  │  - Content media          │  │  - Assessment     │                          │
│  │  - PDF reports (NEW)      │  │    completion     │                          │
│  │                           │  │  - Weekly summary │                          │
│  └──────────────────────────┘  │  - Milestones     │                          │
│                                └───────────────────┘                          │
└────────────────────────────────────────────────────────────────────────────────┘
```

### 1.5 IRT-Based Summative Assessment Architecture

#### 1.5.1 Three-Parameter Logistic (3PL) IRT Model

The MathPath Oregon EOG assessment uses the 3PL IRT model to estimate student ability and adaptively select items:

**Model Definition:**

\[
P(X_i = 1 \mid \theta, a_i, b_i, c_i) = c_i + (1 - c_i) \cdot \frac{1}{1 + e^{-a_i(\theta - b_i)}}
\]

Where:
- \(\theta\) = student ability (latent trait), typically \(\theta \in [-3, +3]\)
- \(a_i\) = item discrimination — how sharply the item differentiates between ability levels. Higher \(a\) = steeper ICC curve. Range: \(0.5 \leq a \leq 2.5\)
- \(b_i\) = item difficulty — the ability level at which \(P = \frac{1+c}{2}\). Range: \(-3.0 \leq b \leq 3.0\)
- \(c_i\) = pseudo-guessing parameter — lower asymptote, the probability that a very low-ability student guesses correctly. For 4-choice MC: \(c \approx 0.25\). For free-response: \(c \approx 0.0\). Range: \(0.0 \leq c \leq 0.35\)

**Item Information Function:**

\[
I_i(\theta) = \frac{a_i^2 \cdot (P_i(\theta) - c_i)^2}{(1 - c_i)^2 \cdot P_i(\theta) \cdot (1 - P_i(\theta))}
\]

This quantifies how much information item \(i\) provides about ability at a given \(\theta\). Maximum information occurs near \(\theta = b_i\) for items with \(c = 0\), shifted slightly right for items with \(c > 0\).

**Test Information Function:**

\[
I(\theta) = \sum_{i=1}^{n} I_i(\theta)
\]

Total information is the sum of individual item informations for all administered items.

**Standard Error of Measurement:**

\[
SEM(\theta) = \frac{1}{\sqrt{I(\theta)}}
\]

The SEM decreases as more items are administered, providing the stopping criterion.

#### 1.5.2 EAP (Expected A Posteriori) Theta Estimation

We use EAP rather than MLE because:
1. EAP is defined for all response patterns (including all-correct or all-incorrect).
2. EAP incorporates a prior distribution, regularizing estimates especially with few items.
3. EAP has lower MSE than MLE for short tests (< 40 items).

**Algorithm:**

Given responses \(\mathbf{x} = (x_1, x_2, \ldots, x_n)\) to items with parameters \((a_i, b_i, c_i)\), and a prior distribution \(\theta \sim N(\mu_0, \sigma_0^2)\):

\[
\hat{\theta}_{EAP} = \frac{\int_{-\infty}^{\infty} \theta \cdot L(\mathbf{x} \mid \theta) \cdot f(\theta) \, d\theta}{\int_{-\infty}^{\infty} L(\mathbf{x} \mid \theta) \cdot f(\theta) \, d\theta}
\]

Where:
- \(L(\mathbf{x} \mid \theta) = \prod_{i=1}^{n} P_i(\theta)^{x_i} \cdot (1 - P_i(\theta))^{1-x_i}\) is the likelihood
- \(f(\theta)\) is the prior density \(N(\mu_0, \sigma_0^2)\)

The integrals are approximated by Gauss-Hermite quadrature with 61 quadrature points over \([-4, +4]\).

The posterior variance (for SEM computation):

\[
Var(\theta \mid \mathbf{x}) = \frac{\int_{-\infty}^{\infty} (\theta - \hat{\theta}_{EAP})^2 \cdot L(\mathbf{x} \mid \theta) \cdot f(\theta) \, d\theta}{\int_{-\infty}^{\infty} L(\mathbf{x} \mid \theta) \cdot f(\theta) \, d\theta}
\]

\[
SEM = \sqrt{Var(\theta \mid \mathbf{x})}
\]

#### 1.5.3 Maximum Fisher Information Item Selection

At each step, the CAT engine selects the next item that maximizes Fisher Information at the current \(\hat{\theta}_{EAP}\):

\[
i^* = \arg\max_{i \in \text{remaining}} I_i(\hat{\theta}_{EAP})
\]

With constraints:
- **Content balancing**: At least 20% of items from each of the 4 major math domains (Operations & Algebraic Thinking, Number & Operations, Measurement & Data, Geometry).
- **Exposure control**: No item administered to more than 20% of students (Sympson-Hetter method when calibration data available).
- **Item type diversity**: Mix of MC, numeric, and free-response items.

#### 1.5.4 Stopping Criteria

The assessment terminates when ANY of these conditions is met:

| Criterion | Value | Rationale |
|-----------|-------|-----------|
| SEM below threshold | SEM < 0.30 | Sufficient precision for proficiency classification |
| Maximum items | 40 items administered | Prevent fatigue; diminishing information gains |
| Maximum time | 75 minutes elapsed | Age-appropriate time limit |
| Minimum items | ≥ 15 items before SEM stop | Ensure content coverage |

#### 1.5.5 Item Parameter Calibration Plan

**Phase 1: Initial Parameters (Months 11–12)**

Before sufficient real student data exists, item parameters are set by content experts:

| Parameter | Method | Typical Values |
|-----------|--------|----------------|
| \(a\) (discrimination) | Expert rating on 1–5 quality scale, mapped to \([0.5, 2.5]\) | Mean = 1.2, SD = 0.4 |
| \(b\) (difficulty) | Expert rating on grade-level alignment, mapped to \([-2, +2]\) | Based on CCSS skill progression |
| \(c\) (guessing) | Set by item type: MC = 0.25, numeric = 0.05, free-response = 0.0 | Fixed by type |

**Phase 2: Operational Calibration (Post-MVP, after N ≥ 1000 students)**

Once sufficient data exists:
1. Extract response matrices from `eog_responses` table.
2. Fit 3PL IRT model using `pyirt` (Python) or `mirt` (R).
3. Anchor calibration to maintain scale consistency across calibration cycles.
4. Update `eog_item_bank` table with calibrated parameters.
5. Flag items with poor fit (infit/outfit > 1.3) for review.

**Calibration schedule**: Quarterly, or after every 500 new assessments, whichever comes first.

---

## 2. Detailed System Design

### 2.1 Database Schema (Complete DDL)

```sql
-- ============================================================================
-- Stage 4: Summative Assessment & Reporting Tables
-- ============================================================================

-- End-of-Grade Assessment container
CREATE TABLE eog_assessments (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id          UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    grade_level         INT NOT NULL CHECK (grade_level BETWEEN 3 AND 8),
    started_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at        TIMESTAMPTZ,
    theta_estimate      FLOAT,                   -- Final EAP theta
    sem                 FLOAT,                   -- Final SEM
    proficiency_level   VARCHAR(20)              -- See proficiency_levels enum
                        CHECK (proficiency_level IN (
                            'below_par', 'approaching', 'on_par', 'above_par'
                        )),
    items_administered  INT NOT NULL DEFAULT 0,
    total_time_seconds  INT,
    status              VARCHAR(20) NOT NULL DEFAULT 'in_progress'
                        CHECK (status IN (
                            'in_progress', 'completed', 'timed_out', 'abandoned', 'invalidated'
                        )),
    stop_reason         VARCHAR(20)
                        CHECK (stop_reason IN (
                            'sem_threshold', 'max_items', 'max_time', 'student_ended', 'error'
                        )),
    content_domain_coverage JSONB,               -- {"OA": 8, "NF": 6, "MD": 5, "G": 4}
    proctoring_flags    JSONB DEFAULT '[]',      -- Unusual patterns for review
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_eog_assessments_student ON eog_assessments(student_id);
CREATE INDEX idx_eog_assessments_student_grade ON eog_assessments(student_id, grade_level);
CREATE INDEX idx_eog_assessments_status ON eog_assessments(status) WHERE status = 'in_progress';
CREATE INDEX idx_eog_assessments_completed ON eog_assessments(completed_at DESC)
    WHERE status = 'completed';


-- Individual item responses within an assessment
CREATE TABLE eog_responses (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_id       UUID NOT NULL REFERENCES eog_assessments(id) ON DELETE CASCADE,
    question_id         UUID NOT NULL REFERENCES questions(id),
    item_position       INT NOT NULL,            -- Order presented (1-indexed)
    theta_before        FLOAT NOT NULL,          -- Theta estimate before this item
    theta_after         FLOAT NOT NULL,          -- Theta estimate after this item
    sem_before          FLOAT NOT NULL,
    sem_after           FLOAT NOT NULL,
    item_difficulty     FLOAT NOT NULL,          -- b parameter used
    item_discrimination FLOAT NOT NULL,          -- a parameter used
    item_guessing       FLOAT NOT NULL,          -- c parameter used
    item_information    FLOAT NOT NULL,          -- Fisher info at theta_before
    is_correct          BOOLEAN NOT NULL,
    student_answer      TEXT NOT NULL,
    response_time_ms    INT NOT NULL CHECK (response_time_ms >= 0),
    content_domain      VARCHAR(5) NOT NULL,     -- "OA", "NF", "MD", "G"
    skill_code          VARCHAR(20) NOT NULL,
    presented_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    answered_at         TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_eog_responses_assessment ON eog_responses(assessment_id);
CREATE INDEX idx_eog_responses_question ON eog_responses(question_id);
CREATE INDEX idx_eog_responses_position ON eog_responses(assessment_id, item_position);


-- IRT item bank (calibrated item parameters)
CREATE TABLE eog_item_bank (
    question_id         UUID PRIMARY KEY REFERENCES questions(id) ON DELETE CASCADE,
    a_parameter         FLOAT NOT NULL CHECK (a_parameter BETWEEN 0.1 AND 5.0),
    b_parameter         FLOAT NOT NULL CHECK (b_parameter BETWEEN -4.0 AND 4.0),
    c_parameter         FLOAT NOT NULL CHECK (c_parameter BETWEEN 0.0 AND 0.5),
    grade_level         INT NOT NULL CHECK (grade_level BETWEEN 3 AND 8),
    content_domain      VARCHAR(5) NOT NULL CHECK (content_domain IN ('OA', 'NF', 'MD', 'G')),
    calibrated          BOOLEAN NOT NULL DEFAULT FALSE,
    calibration_method  VARCHAR(20) DEFAULT 'expert'
                        CHECK (calibration_method IN ('expert', 'mle', 'bayesian', 'fixed')),
    calibration_n       INT NOT NULL DEFAULT 0,  -- Number of responses used for calibration
    calibration_fit     FLOAT,                   -- Infit statistic (1.0 = perfect)
    last_calibrated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    active              BOOLEAN NOT NULL DEFAULT TRUE,
    exposure_rate       FLOAT NOT NULL DEFAULT 0.0 CHECK (exposure_rate BETWEEN 0.0 AND 1.0),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_eog_item_bank_grade ON eog_item_bank(grade_level) WHERE active = TRUE;
CREATE INDEX idx_eog_item_bank_domain ON eog_item_bank(grade_level, content_domain) WHERE active = TRUE;
CREATE INDEX idx_eog_item_bank_difficulty ON eog_item_bank(b_parameter) WHERE active = TRUE;
CREATE INDEX idx_eog_item_bank_calibrated ON eog_item_bank(calibrated);


-- Progress reports (generated PDFs)
CREATE TABLE progress_reports (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id              UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    assessment_id           UUID REFERENCES eog_assessments(id) ON DELETE SET NULL,
    generated_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    report_type             VARCHAR(30) NOT NULL
                            CHECK (report_type IN (
                                'eog_assessment', 'weekly_progress', 'monthly_progress',
                                'practice_summary', 'remediation_plan'
                            )),
    report_version          VARCHAR(10) NOT NULL DEFAULT 'teacher',
    pdf_s3_key              TEXT NOT NULL,
    pdf_size_bytes          INT,
    student_version_s3_key  TEXT,             -- Simplified version for parents/students
    generation_time_ms      INT,
    template_version        VARCHAR(20) NOT NULL,
    access_count            INT NOT NULL DEFAULT 0,
    last_accessed           TIMESTAMPTZ,
    expires_at              TIMESTAMPTZ,      -- Presigned URL expiry
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_progress_reports_student ON progress_reports(student_id);
CREATE INDEX idx_progress_reports_assessment ON progress_reports(assessment_id);
CREATE INDEX idx_progress_reports_type ON progress_reports(student_id, report_type);


-- Teacher-Student access control
CREATE TABLE teacher_student_access (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    teacher_id  UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    student_id  UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    class_id    UUID REFERENCES classes(id) ON DELETE SET NULL,
    granted_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    granted_by  UUID NOT NULL REFERENCES users(id),
    revoked_at  TIMESTAMPTZ,
    access_type VARCHAR(20) NOT NULL DEFAULT 'view'
                CHECK (access_type IN ('view', 'manage', 'admin')),
    
    CONSTRAINT uq_teacher_student_active UNIQUE (teacher_id, student_id)
        WHERE revoked_at IS NULL  -- Only one active grant per teacher-student pair
);

-- Note: The unique constraint above uses a partial index approach.
-- In practice, implement with a partial unique index:
CREATE UNIQUE INDEX idx_teacher_student_active 
    ON teacher_student_access(teacher_id, student_id) 
    WHERE revoked_at IS NULL;

CREATE INDEX idx_teacher_access_teacher ON teacher_student_access(teacher_id) WHERE revoked_at IS NULL;
CREATE INDEX idx_teacher_access_student ON teacher_student_access(student_id) WHERE revoked_at IS NULL;


-- Notification log
CREATE TABLE notification_log (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recipient_id        UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    recipient_email     VARCHAR(255) NOT NULL,
    recipient_type      VARCHAR(20) NOT NULL
                        CHECK (recipient_type IN ('teacher', 'parent', 'admin')),
    notification_type   VARCHAR(30) NOT NULL
                        CHECK (notification_type IN (
                            'assessment_complete', 'weekly_summary', 'monthly_report',
                            'milestone_achieved', 'intervention_needed',
                            'account_created', 'report_ready'
                        )),
    subject_line        TEXT NOT NULL,
    template_id         VARCHAR(50) NOT NULL,
    template_data       JSONB NOT NULL DEFAULT '{}',
    sent_at             TIMESTAMPTZ,
    delivered_at        TIMESTAMPTZ,
    opened_at           TIMESTAMPTZ,
    clicked_at          TIMESTAMPTZ,
    bounced             BOOLEAN NOT NULL DEFAULT FALSE,
    ses_message_id      VARCHAR(100),
    status              VARCHAR(20) NOT NULL DEFAULT 'pending'
                        CHECK (status IN ('pending', 'sent', 'delivered', 'bounced', 'failed')),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_notification_log_recipient ON notification_log(recipient_id);
CREATE INDEX idx_notification_log_type ON notification_log(notification_type, created_at DESC);
CREATE INDEX idx_notification_log_status ON notification_log(status) WHERE status IN ('pending', 'failed');
CREATE INDEX idx_notification_log_ses ON notification_log(ses_message_id);


-- Remediation plans (generated after assessment identifies deficiencies)
CREATE TABLE remediation_plans (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id          UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    assessment_id       UUID NOT NULL REFERENCES eog_assessments(id) ON DELETE CASCADE,
    deficient_skills    JSONB NOT NULL,          -- [{"skill_code": "3.OA.A.1", "theta_at_skill": -0.5, "target_theta": 0.0}]
    recommended_modules JSONB NOT NULL,          -- [{"module_id": "...", "priority": 1, "estimated_hours": 2.5}]
    generated_plan_id   UUID REFERENCES learning_plans(id) ON DELETE SET NULL,
    teacher_approved    BOOLEAN,
    teacher_notes       TEXT,
    approved_at         TIMESTAMPTZ,
    approved_by         UUID REFERENCES users(id),
    status              VARCHAR(20) NOT NULL DEFAULT 'pending'
                        CHECK (status IN ('pending', 'approved', 'active', 'completed', 'rejected')),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_remediation_plans_student ON remediation_plans(student_id);
CREATE INDEX idx_remediation_plans_assessment ON remediation_plans(assessment_id);
CREATE INDEX idx_remediation_plans_status ON remediation_plans(status);
```

### 2.2 Service Layer Design

```python
# ============================================================================
# Stage 4 — Complete Python Class Interfaces
# ============================================================================

from __future__ import annotations
from uuid import UUID
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional


# --- Enums and Models ---

class ProficiencyLevel(str, Enum):
    BELOW_PAR = "below_par"          # θ < -0.5
    APPROACHING = "approaching"       # -0.5 ≤ θ < 0.0
    ON_PAR = "on_par"                # 0.0 ≤ θ < 0.8
    ABOVE_PAR = "above_par"          # θ ≥ 0.8


class AssessmentStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    TIMED_OUT = "timed_out"
    ABANDONED = "abandoned"
    INVALIDATED = "invalidated"


class ReportVersion(str, Enum):
    TEACHER = "teacher"       # Full detail: theta, SEM, item-level analysis
    PARENT = "parent"         # Simplified: proficiency level, strengths/weaknesses, recommendations
    STUDENT = "student"       # Child-friendly: stars, progress bars, encouragement


class NotificationType(str, Enum):
    ASSESSMENT_COMPLETE = "assessment_complete"
    WEEKLY_SUMMARY = "weekly_summary"
    MONTHLY_REPORT = "monthly_report"
    MILESTONE_ACHIEVED = "milestone_achieved"
    INTERVENTION_NEEDED = "intervention_needed"
    REPORT_READY = "report_ready"


class ItemResponse(BaseModel):
    """A single item response for IRT scoring."""
    question_id: str
    a: float
    b: float
    c: float
    is_correct: bool
    response_time_ms: int


class IRTUpdateResult(BaseModel):
    """Result of processing an item response."""
    theta_before: float
    theta_after: float
    sem_before: float
    sem_after: float
    item_information: float
    is_correct: bool
    should_stop: bool
    stop_reason: str | None = None


class EOGResults(BaseModel):
    """Final assessment results."""
    assessment_id: UUID
    student_id: UUID
    theta_estimate: float
    sem: float
    proficiency_level: ProficiencyLevel
    items_administered: int
    correct_count: int
    total_time_seconds: int
    content_coverage: dict[str, int]   # domain → item count
    stop_reason: str
    strengths: list[str]               # Skill codes with high performance
    weaknesses: list[str]              # Skill codes with low performance


class ProgressReport(BaseModel):
    """Data model for a progress report before PDF generation."""
    report_id: UUID
    student_id: UUID
    student_name: str
    grade_level: int
    assessment_date: datetime
    theta_estimate: float
    sem: float
    proficiency_level: ProficiencyLevel
    proficiency_description: str
    domain_scores: dict[str, dict]     # {"OA": {"theta": 0.3, "items": 8, "correct": 6}}
    skill_mastery: list[dict]          # [{"skill_code": ..., "name": ..., "mastered": True}]
    practice_history: dict             # {"sessions": 15, "total_questions": 200, "avg_correct": 0.72}
    growth_over_time: list[dict]       # [{"date": ..., "theta": ...}] for growth chart
    recommendations: list[str]
    next_steps: list[str]


# --- Service Classes ---

class SummativeAssessmentService:
    """Orchestrates end-of-grade adaptive assessment.
    
    This is a stateful service that manages a single assessment session.
    Unlike the practice engine, this does NOT use LangGraph — it's a
    straightforward CAT algorithm with sequential item selection.
    
    State is persisted in the eog_assessments and eog_responses tables
    between API calls (student answers one item at a time via REST).
    """
    
    def __init__(self, irt_service: IRTService):
        self.irt = irt_service
    
    async def start_eog_assessment(
        self, student_id: UUID, grade_level: int
    ) -> dict:
        """Start a new end-of-grade assessment.
        
        1. Verify student has no active (in_progress) assessment.
        2. Create eog_assessments record with status='in_progress'.
        3. Load item bank for the grade level.
        4. Initialize theta = 0.0 (prior mean), SEM = 1.0.
        5. Select first item using Maximum Fisher Information.
        6. Return assessment_id and first question.
        """
        ...
    
    async def get_next_item(
        self, assessment_id: UUID
    ) -> dict | None:
        """Get the next item for an in-progress assessment.
        
        1. Load assessment state (current theta, SEM, administered items).
        2. Check stopping criteria.
        3. If should stop → return None.
        4. Otherwise, select next item via MFI with content balancing.
        5. Record item presentation in eog_responses.
        6. Return question payload (no correct answer).
        """
        ...
    
    async def submit_response(
        self, assessment_id: UUID, question_id: UUID, answer: str, time_ms: int
    ) -> IRTUpdateResult:
        """Process a student's response to an assessment item.
        
        1. Score the response (correct/incorrect).
        2. Update EAP theta estimate with new response.
        3. Compute new SEM.
        4. Persist to eog_responses (theta_before, theta_after, etc.).
        5. Check stopping criteria.
        6. Return update result with should_stop flag.
        """
        ...
    
    async def complete_assessment(
        self, assessment_id: UUID
    ) -> EOGResults:
        """Finalize a completed assessment.
        
        1. Compute final theta and SEM.
        2. Classify proficiency level.
        3. Identify strengths/weaknesses by content domain.
        4. Update eog_assessments with final results.
        5. Generate remediation plan if below_par or approaching.
        6. Trigger report generation (enqueue to SQS).
        7. Trigger notifications (assessment complete email).
        8. Return EOGResults.
        """
        ...
    
    def compute_proficiency_level(
        self, theta: float, sem: float
    ) -> ProficiencyLevel:
        """Classify proficiency from theta estimate.
        
        Cut scores (see §3.2 for rationale):
        - Below Par:   θ < -0.5
        - Approaching: -0.5 ≤ θ < 0.0
        - On Par:       0.0 ≤ θ < 0.8
        - Above Par:    θ ≥ 0.8
        
        When SEM is high (> 0.5), classify conservatively:
        use theta - SEM for the effective classification theta.
        """
        ...


class IRTService:
    """IRT computation engine.
    
    Stateless service providing IRT calculations:
    - 3PL probability
    - Fisher Information
    - EAP theta estimation
    - Maximum Fisher Information item selection
    - Stopping criteria evaluation
    """
    
    def probability_3pl(
        self, theta: float, a: float, b: float, c: float
    ) -> float:
        """3PL probability of correct response."""
        ...
    
    def fisher_information(
        self, theta: float, a: float, b: float, c: float
    ) -> float:
        """Fisher Information at theta for a single item."""
        ...
    
    def estimate_theta(
        self, responses: list[ItemResponse],
        prior_mean: float = 0.0,
        prior_std: float = 1.0,
    ) -> tuple[float, float]:
        """EAP theta estimation.
        
        Returns (theta_estimate, standard_error_of_measurement).
        See §3.1 for full implementation.
        """
        ...
    
    def select_next_item(
        self,
        theta: float,
        administered_items: list[str],
        item_bank: list[dict],
        content_coverage: dict[str, int],
        target_coverage: dict[str, float],
    ) -> dict | None:
        """Select next item via MFI with content balancing.
        
        1. Exclude administered items.
        2. Check content balance — if any domain is under-represented,
           restrict selection to that domain.
        3. Compute Fisher Information for each candidate.
        4. Select item with maximum information (subject to constraints).
        5. Return item or None if bank exhausted.
        """
        ...
    
    def check_stopping_criteria(
        self,
        theta: float,
        sem: float,
        items_administered: int,
        elapsed_seconds: int,
    ) -> tuple[bool, str | None]:
        """Check whether assessment should terminate.
        
        Returns (should_stop, stop_reason).
        """
        if items_administered >= 15 and sem < 0.30:
            return True, "sem_threshold"
        if items_administered >= 40:
            return True, "max_items"
        if elapsed_seconds >= 75 * 60:
            return True, "max_time"
        return False, None


class ReportService:
    """Report generation and delivery.
    
    Reports are generated asynchronously:
    1. Data assembly (async DB queries)
    2. HTML rendering (Jinja2 template)
    3. PDF conversion (WeasyPrint — CPU-intensive, runs in thread pool)
    4. S3 upload
    5. Presigned URL generation
    """
    
    async def generate_progress_report(
        self, student_id: UUID, assessment_id: UUID,
        version: ReportVersion = ReportVersion.TEACHER,
    ) -> ProgressReport:
        """Assemble all data needed for a progress report.
        
        Queries run in parallel (asyncio.gather):
        - Student profile (name, grade)
        - Assessment results (theta, SEM, proficiency)
        - Domain-level scores
        - Skill mastery details
        - Practice session history
        - Historical theta estimates (for growth chart)
        """
        ...
    
    async def generate_pdf(
        self, report: ProgressReport, version: ReportVersion
    ) -> str:
        """Generate PDF from report data.
        
        Pipeline:
        1. Select Jinja2 template based on version (teacher/parent/student).
        2. Render HTML with report data.
        3. Convert HTML → PDF using WeasyPrint (in thread pool executor).
        4. Upload PDF to S3.
        5. Return S3 key.
        """
        ...
    
    async def get_report_url(
        self, report_id: UUID, version: ReportVersion
    ) -> str:
        """Generate a presigned S3 URL for downloading a report.
        
        URL expires in 7 days. Access is logged.
        """
        ...
    
    async def get_student_reports(
        self, student_id: UUID, limit: int = 10,
    ) -> list[dict]:
        """List available reports for a student.
        
        Used by teacher and parent dashboards.
        """
        ...


class NotificationService:
    """Email notification delivery via AWS SES.
    
    All notifications are logged in notification_log table.
    Uses HTML email templates with SES templates for tracking
    open/click events.
    """
    
    async def send_assessment_complete(
        self, student_id: UUID, results: EOGResults,
    ) -> None:
        """Send assessment completion notification to teacher(s) and parent(s).
        
        1. Look up teacher(s) via teacher_student_access.
        2. Look up parent(s) via student_parent_links.
        3. Render email from template with proficiency level, summary.
        4. Send via SES.
        5. Log to notification_log.
        """
        ...
    
    async def send_weekly_summary(
        self, parent_id: UUID
    ) -> None:
        """Send weekly practice summary to a parent.
        
        Includes: sessions completed, skills mastered, time spent, encouragement.
        Sent every Sunday at 6pm parent's local time.
        """
        ...
    
    async def send_milestone_notification(
        self, student_id: UUID, milestone: dict,
    ) -> None:
        """Send milestone notification (e.g., "Your child mastered multiplication!").
        
        Milestones:
        - First assessment completed
        - Proficiency level improved
        - 10 skills mastered
        - 100 practice questions answered
        """
        ...
    
    async def send_intervention_needed(
        self, student_id: UUID, assessment_id: UUID,
    ) -> None:
        """Alert teacher when assessment shows proficiency below_par.
        
        Includes remediation plan link and suggested actions.
        """
        ...
```

---

## 3. Key Algorithms

### 3.1 Algorithm: EAP Theta Estimation

```python
# services/irt_service.py — EAP estimation

import math
import numpy as np
from dataclasses import dataclass
from typing import NamedTuple


@dataclass
class ItemResponse:
    """A single item response for IRT scoring."""
    question_id: str
    a: float    # Discrimination
    b: float    # Difficulty
    c: float    # Guessing
    is_correct: bool


class EAPResult(NamedTuple):
    theta: float
    sem: float


def irt_3pl_probability(theta: float, a: float, b: float, c: float) -> float:
    """3PL IRT probability: P(X=1|θ,a,b,c) = c + (1-c) / (1 + exp(-a(θ-b)))"""
    exponent = -a * (theta - b)
    exponent = max(min(exponent, 35.0), -35.0)  # Prevent overflow
    return c + (1.0 - c) / (1.0 + math.exp(exponent))


def eap_estimate(
    responses: list[ItemResponse],
    prior_mean: float = 0.0,
    prior_std: float = 1.0,
    n_quadrature: int = 61,
    theta_range: tuple[float, float] = (-4.0, 4.0),
) -> EAPResult:
    """
    Expected A Posteriori (EAP) theta estimation using Gaussian quadrature.
    
    This is the core scoring algorithm for the MathPath Oregon EOG assessment.
    It estimates the student's latent ability (theta) from their pattern of
    correct/incorrect responses, accounting for each item's psychometric
    properties (discrimination, difficulty, guessing).
    
    Algorithm:
    1. Create quadrature grid: 61 evenly spaced points over [-4, +4].
    2. For each quadrature point θ_q:
       a. Compute log-likelihood of the observed response pattern:
          LL(θ_q) = Σ [x_i * log(P_i(θ_q)) + (1-x_i) * log(1 - P_i(θ_q))]
       b. Compute log-prior density: log(N(θ_q | μ_0, σ_0²))
       c. Compute log-posterior (unnormalized): LL(θ_q) + log_prior(θ_q)
    3. Normalize the posterior using the log-sum-exp trick for numerical stability.
    4. Compute EAP estimate: θ̂ = Σ θ_q * w_q * posterior(θ_q)
    5. Compute posterior variance: Var = Σ (θ_q - θ̂)² * w_q * posterior(θ_q)
    6. SEM = √Var
    
    Args:
        responses: List of ItemResponse objects with item parameters and correctness.
        prior_mean: Mean of the normal prior distribution (default 0.0).
        prior_std: Standard deviation of the prior (default 1.0).
        n_quadrature: Number of quadrature points (default 61).
        theta_range: Range for quadrature grid (default [-4, 4]).
    
    Returns:
        EAPResult(theta=θ̂, sem=SEM)
    
    Complexity: O(n_quadrature * n_items) — very fast for typical sizes.
    
    Numerical stability:
    - Uses log-probabilities throughout to prevent underflow.
    - Uses log-sum-exp trick for normalization.
    - Clamps exponents to [-35, 35] to prevent overflow.
    
    Examples:
        >>> responses = [
        ...     ItemResponse("q1", a=1.0, b=0.0, c=0.2, is_correct=True),
        ...     ItemResponse("q2", a=1.2, b=0.5, c=0.2, is_correct=True),
        ...     ItemResponse("q3", a=0.8, b=-0.3, c=0.2, is_correct=False),
        ... ]
        >>> result = eap_estimate(responses)
        >>> -0.5 < result.theta < 1.5  # Reasonable range for 2/3 correct
        True
        >>> result.sem < 1.0  # SEM decreases with more items
        True
    """
    if not responses:
        return EAPResult(theta=prior_mean, sem=prior_std)
    
    # Step 1: Create quadrature grid
    theta_grid = np.linspace(theta_range[0], theta_range[1], n_quadrature)
    delta_theta = theta_grid[1] - theta_grid[0]  # Spacing for numerical integration
    
    # Step 2: Compute log-posterior at each quadrature point
    log_posterior = np.zeros(n_quadrature)
    
    for q in range(n_quadrature):
        theta_q = theta_grid[q]
        
        # Log-prior: N(theta_q | prior_mean, prior_std²)
        z = (theta_q - prior_mean) / prior_std
        log_prior = -0.5 * z * z - math.log(prior_std) - 0.5 * math.log(2 * math.pi)
        
        # Log-likelihood: sum over all items
        log_likelihood = 0.0
        for item in responses:
            p = irt_3pl_probability(theta_q, item.a, item.b, item.c)
            # Clamp to avoid log(0)
            p = max(min(p, 1.0 - 1e-15), 1e-15)
            
            if item.is_correct:
                log_likelihood += math.log(p)
            else:
                log_likelihood += math.log(1.0 - p)
        
        log_posterior[q] = log_likelihood + log_prior
    
    # Step 3: Normalize using log-sum-exp trick
    max_log_post = np.max(log_posterior)
    log_posterior_shifted = log_posterior - max_log_post
    posterior = np.exp(log_posterior_shifted)
    
    # Numerical integration weights (trapezoidal rule)
    weights = np.ones(n_quadrature) * delta_theta
    weights[0] *= 0.5
    weights[-1] *= 0.5
    
    normalizing_constant = np.sum(posterior * weights)
    
    if normalizing_constant < 1e-300:
        # All posterior mass is negligible — return prior
        return EAPResult(theta=prior_mean, sem=prior_std)
    
    normalized_posterior = posterior * weights / normalizing_constant
    
    # Step 4: EAP estimate (posterior mean)
    theta_hat = np.sum(theta_grid * normalized_posterior)
    
    # Step 5: Posterior variance
    variance = np.sum((theta_grid - theta_hat) ** 2 * normalized_posterior)
    
    # Step 6: SEM
    sem = math.sqrt(max(variance, 1e-10))
    
    return EAPResult(theta=float(theta_hat), sem=float(sem))
```

### 3.2 Algorithm: Proficiency Classification

```python
# services/irt_service.py — proficiency classification

from enum import Enum


class ProficiencyLevel(str, Enum):
    BELOW_PAR = "below_par"
    APPROACHING = "approaching"
    ON_PAR = "on_par"
    ABOVE_PAR = "above_par"


# Cut score definitions
# These cut scores partition the theta scale into 4 proficiency levels
# aligned with Oregon OSAS assessment levels (1–4).
#
# Oregon OSAS uses scale scores (e.g., 2200–2800 range), not theta directly.
# Our theta scale is centered at 0 with SD ≈ 1. The cut scores below
# are mapped to approximate the OSAS level distributions:
#
# OSAS Level 1 (Does not yet meet) ↔ Below Par:   ~25% of students
# OSAS Level 2 (Nearly meets)      ↔ Approaching: ~25% of students
# OSAS Level 3 (Meets)             ↔ On Par:      ~30% of students
# OSAS Level 4 (Exceeds)           ↔ Above Par:   ~20% of students
#
# These percentages approximate the actual Oregon statewide distribution
# where ~31.5% of students are proficient (Level 3 or 4) in math.
# Source: Oregon Department of Education, OSAS 2025 results.
#
# Validation plan:
# 1. After 500+ assessments, compare MathPath proficiency distribution
#    to Oregon statewide distribution for the same grade levels.
# 2. Adjust cut scores if distribution deviates by >5 percentage points.
# 3. Conduct criterion validity study: correlate MathPath theta with
#    OSAS scale scores for students who take both assessments.

CUT_SCORES = {
    "below_par_upper": -0.5,      # θ < -0.5 → Below Par
    "approaching_upper": 0.0,      # -0.5 ≤ θ < 0.0 → Approaching
    "on_par_upper": 0.8,           # 0.0 ≤ θ < 0.8 → On Par
    # θ ≥ 0.8 → Above Par
}


def classify_proficiency(
    theta: float,
    sem: float,
    conservative: bool = True,
) -> ProficiencyLevel:
    """
    Classify student proficiency from IRT theta estimate.
    
    Uses a conservative approach when SEM is high:
    if SEM > 0.5, classify using (theta - SEM) instead of theta.
    This prevents over-classification of students with imprecise estimates.
    
    Args:
        theta: EAP theta estimate.
        sem: Standard Error of Measurement.
        conservative: If True, use conservative classification for high SEM.
    
    Returns:
        ProficiencyLevel enum value.
    
    Cut scores:
        Below Par:   θ_eff < -0.5
        Approaching: -0.5 ≤ θ_eff < 0.0
        On Par:       0.0 ≤ θ_eff < 0.8
        Above Par:    θ_eff ≥ 0.8
    
    Where θ_eff = θ - SEM if conservative and SEM > 0.5, else θ.
    
    Examples:
        >>> classify_proficiency(0.5, 0.25)
        ProficiencyLevel.ON_PAR
        
        >>> classify_proficiency(0.5, 0.6, conservative=True)
        ProficiencyLevel.APPROACHING   # Uses 0.5 - 0.6 = -0.1
        
        >>> classify_proficiency(-0.8, 0.2)
        ProficiencyLevel.BELOW_PAR
    """
    # Apply conservative adjustment for imprecise estimates
    if conservative and sem > 0.5:
        theta_eff = theta - sem
    else:
        theta_eff = theta
    
    if theta_eff < CUT_SCORES["below_par_upper"]:
        return ProficiencyLevel.BELOW_PAR
    elif theta_eff < CUT_SCORES["approaching_upper"]:
        return ProficiencyLevel.APPROACHING
    elif theta_eff < CUT_SCORES["on_par_upper"]:
        return ProficiencyLevel.ON_PAR
    else:
        return ProficiencyLevel.ABOVE_PAR


def get_proficiency_description(
    level: ProficiencyLevel, grade_level: int
) -> str:
    """Human-readable description of proficiency level for reports."""
    descriptions = {
        ProficiencyLevel.BELOW_PAR: (
            f"This student is performing below grade {grade_level} expectations "
            f"in mathematics. Significant support and targeted practice are "
            f"recommended to build foundational skills."
        ),
        ProficiencyLevel.APPROACHING: (
            f"This student is approaching grade {grade_level} proficiency in "
            f"mathematics. With continued practice on identified areas, "
            f"the student is on track to reach grade-level expectations."
        ),
        ProficiencyLevel.ON_PAR: (
            f"This student meets grade {grade_level} expectations in mathematics. "
            f"The student demonstrates solid understanding of grade-level concepts "
            f"and is well-prepared for advancement."
        ),
        ProficiencyLevel.ABOVE_PAR: (
            f"This student exceeds grade {grade_level} expectations in mathematics. "
            f"The student demonstrates advanced understanding and may benefit from "
            f"enrichment opportunities and more challenging material."
        ),
    }
    return descriptions[level]
```

### 3.3 Algorithm: PDF Report Generation Pipeline

```python
# services/report_service.py — PDF generation pipeline

import asyncio
import io
import time
import logging
from uuid import UUID, uuid4
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

logger = logging.getLogger(__name__)

# Thread pool for CPU-intensive WeasyPrint rendering
_pdf_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="pdf")


class ReportGenerator:
    """Pipeline for generating progress report PDFs.
    
    Architecture:
    1. Data Assembly (async, parallel DB queries) — ~50ms
    2. HTML Rendering (Jinja2 template) — ~5ms
    3. PDF Conversion (WeasyPrint, in thread pool) — ~2-5 seconds
    4. S3 Upload (async) — ~200ms
    5. Presigned URL Generation — ~10ms
    
    Total target: < 5 seconds end-to-end.
    """
    
    TEMPLATE_DIR = "templates/reports"
    S3_BUCKET = "mathpath-reports"
    URL_EXPIRY_DAYS = 7
    
    def __init__(self):
        self.jinja_env = Environment(
            loader=FileSystemLoader(self.TEMPLATE_DIR),
            autoescape=True,
        )
    
    async def generate_full_report(
        self,
        student_id: UUID,
        assessment_id: UUID,
        version: str = "teacher",
    ) -> dict:
        """Complete report generation pipeline.
        
        Returns:
            {
                "report_id": UUID,
                "pdf_s3_key": str,
                "presigned_url": str,
                "generation_time_ms": int,
            }
        """
        start = time.monotonic()
        report_id = uuid4()
        
        # --- Step 1: Data Assembly (parallel queries) ---
        (
            student,
            assessment,
            domain_scores,
            skill_mastery,
            practice_history,
            growth_data,
        ) = await asyncio.gather(
            self._get_student_profile(student_id),
            self._get_assessment_results(assessment_id),
            self._get_domain_scores(assessment_id),
            self._get_skill_mastery(student_id),
            self._get_practice_history(student_id),
            self._get_growth_data(student_id),
        )
        
        # Build report data model
        report_data = {
            "report_id": str(report_id),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "student_name": student["name"],
            "grade_level": student["grade_level"],
            "assessment_date": assessment["completed_at"],
            "proficiency_level": assessment["proficiency_level"],
            "proficiency_description": get_proficiency_description(
                ProficiencyLevel(assessment["proficiency_level"]),
                student["grade_level"],
            ),
            "theta": round(assessment["theta_estimate"], 2),
            "sem": round(assessment["sem"], 2),
            "items_administered": assessment["items_administered"],
            "correct_count": assessment.get("correct_count", 0),
            "domain_scores": domain_scores,
            "skill_mastery": skill_mastery,
            "practice_history": practice_history,
            "growth_data": growth_data,
            "recommendations": self._generate_recommendations(
                assessment, domain_scores, skill_mastery
            ),
            "version": version,
        }
        
        # --- Step 2: HTML Rendering ---
        template_name = f"report_{version}_v1.0.html"
        template = self.jinja_env.get_template(template_name)
        html_content = template.render(**report_data)
        
        # --- Step 3: PDF Conversion (offloaded to thread pool) ---
        loop = asyncio.get_event_loop()
        pdf_bytes = await loop.run_in_executor(
            _pdf_executor,
            self._render_pdf,
            html_content,
        )
        
        # --- Step 4: S3 Upload ---
        s3_key = f"reports/{student_id}/{report_id}/{version}.pdf"
        await self._upload_to_s3(s3_key, pdf_bytes)
        
        # --- Step 5: Presigned URL ---
        presigned_url = await self._generate_presigned_url(
            s3_key,
            expiry_seconds=self.URL_EXPIRY_DAYS * 86400,
        )
        
        # --- Persist report record ---
        generation_time_ms = int((time.monotonic() - start) * 1000)
        
        await self._save_report_record(
            report_id=report_id,
            student_id=student_id,
            assessment_id=assessment_id,
            report_type="eog_assessment",
            version=version,
            s3_key=s3_key,
            pdf_size=len(pdf_bytes),
            generation_time_ms=generation_time_ms,
        )
        
        return {
            "report_id": str(report_id),
            "pdf_s3_key": s3_key,
            "presigned_url": presigned_url,
            "generation_time_ms": generation_time_ms,
        }
    
    def _render_pdf(self, html_content: str) -> bytes:
        """Synchronous PDF rendering via WeasyPrint.
        
        MUST run in thread pool — WeasyPrint is CPU-bound and blocking.
        Typical render time: 2-5 seconds for a 2-page report.
        """
        html = HTML(string=html_content, base_url=self.TEMPLATE_DIR)
        return html.write_pdf()
    
    async def _upload_to_s3(self, key: str, data: bytes) -> None:
        """Upload PDF bytes to S3."""
        import aioboto3
        session = aioboto3.Session()
        async with session.client("s3") as s3:
            await s3.put_object(
                Bucket=self.S3_BUCKET,
                Key=key,
                Body=data,
                ContentType="application/pdf",
                ServerSideEncryption="AES256",
            )
    
    async def _generate_presigned_url(
        self, key: str, expiry_seconds: int
    ) -> str:
        """Generate presigned S3 URL for PDF download."""
        import aioboto3
        session = aioboto3.Session()
        async with session.client("s3") as s3:
            url = await s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.S3_BUCKET, "Key": key},
                ExpiresIn=expiry_seconds,
            )
            return url
    
    async def _get_student_profile(self, student_id: UUID) -> dict:
        """Query student name, grade level, school."""
        ...
    
    async def _get_assessment_results(self, assessment_id: UUID) -> dict:
        """Query final assessment results."""
        ...
    
    async def _get_domain_scores(self, assessment_id: UUID) -> dict:
        """Compute per-domain theta estimates from item responses.
        
        Groups eog_responses by content_domain and runs EAP estimation
        on each domain subset to get domain-specific ability estimates.
        """
        ...
    
    async def _get_skill_mastery(self, student_id: UUID) -> list[dict]:
        """Get skill-level mastery status from BKT current states."""
        ...
    
    async def _get_practice_history(self, student_id: UUID) -> dict:
        """Aggregate practice session statistics."""
        ...
    
    async def _get_growth_data(self, student_id: UUID) -> list[dict]:
        """Historical theta estimates for growth visualization.
        
        Returns list of {"date": ISO, "theta": float} from past assessments
        and interpolated from BKT mastery trends.
        """
        ...
    
    def _generate_recommendations(
        self, assessment: dict, domain_scores: dict, skill_mastery: list[dict]
    ) -> list[str]:
        """Generate actionable recommendations based on results.
        
        Rules:
        - If domain theta < -0.5: "Focus on [domain name] skills"
        - If specific skill P(mastered) < 0.5: "Practice [skill name]"
        - If growth positive: "Great progress in [area]!"
        - Always include at least one positive recommendation.
        """
        ...
    
    async def _save_report_record(self, **kwargs) -> None:
        """Insert into progress_reports table."""
        ...
```

---

## 4. Infrastructure (Stage 4 — MVP Hardening)

### 4.1 Performance & Scaling Configuration

**MVP Performance Targets:**

| Metric | Target | Measurement |
|--------|--------|-------------|
| Concurrent practice sessions | 500 WebSocket connections | k6 load test |
| Concurrent EOG assessments | 50 simultaneous | k6 load test |
| Practice question delivery | < 2s p95 | CloudWatch custom metric |
| Assessment item delivery | < 1s p95 | CloudWatch custom metric |
| Assessment scoring (EAP) | < 100ms p95 | Application metric |
| Report PDF generation | < 5s per report | SQS processing time |
| Report generation queue | < 5 min end-to-end | SQS age metric |
| API response time (REST) | < 500ms p95 | ALB target response time |
| Error rate | < 1% | CloudWatch error ratio |

#### 4.1.1 ECS Auto-Scaling

```hcl
# terraform/modules/ecs/autoscaling.tf

# API service auto-scaling
resource "aws_appautoscaling_target" "api" {
  max_capacity       = 10
  min_capacity       = 2    # Min 2 for HA (up from 1 in Stage 3)
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.api.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

# Scale out on CPU
resource "aws_appautoscaling_policy" "api_cpu_scale_out" {
  name               = "mathpath-api-cpu-scale-out"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.api.resource_id
  scalable_dimension = aws_appautoscaling_target.api.scalable_dimension
  service_namespace  = aws_appautoscaling_target.api.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value       = 70.0    # Scale out at 70% CPU
    scale_in_cooldown  = 300     # 5 min cooldown before scale in
    scale_out_cooldown = 60      # 1 min cooldown before next scale out
  }
}

# Scale out on memory
resource "aws_appautoscaling_policy" "api_memory_scale_out" {
  name               = "mathpath-api-memory-scale-out"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.api.resource_id
  scalable_dimension = aws_appautoscaling_target.api.scalable_dimension
  service_namespace  = aws_appautoscaling_target.api.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageMemoryUtilization"
    }
    target_value       = 75.0
    scale_in_cooldown  = 300
    scale_out_cooldown = 60
  }
}

# Custom metric: Active WebSocket connections per task
resource "aws_appautoscaling_policy" "api_ws_connections" {
  name               = "mathpath-api-ws-connections"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.api.resource_id
  scalable_dimension = aws_appautoscaling_target.api.scalable_dimension
  service_namespace  = aws_appautoscaling_target.api.service_namespace

  target_tracking_scaling_policy_configuration {
    customized_metric_specification {
      metric_name = "ActiveWebSocketConnections"
      namespace   = "MathPath/API"
      statistic   = "Average"
    }
    target_value       = 250.0   # Target 250 WS connections per task (50% of 500)
    scale_in_cooldown  = 300
    scale_out_cooldown = 60
  }
}

# Report worker auto-scaling
resource "aws_appautoscaling_target" "report_worker" {
  max_capacity       = 5
  min_capacity       = 1
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.report_worker.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "report_worker_queue_depth" {
  name               = "mathpath-report-worker-queue"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.report_worker.resource_id
  scalable_dimension = aws_appautoscaling_target.report_worker.scalable_dimension
  service_namespace  = aws_appautoscaling_target.report_worker.service_namespace

  target_tracking_scaling_policy_configuration {
    customized_metric_specification {
      metric_name = "ApproximateNumberOfMessagesVisible"
      namespace   = "AWS/SQS"
      statistic   = "Average"
      dimensions = {
        QueueName = aws_sqs_queue.report_gen.name
      }
    }
    target_value       = 5.0     # Scale at 5 pending reports per worker
    scale_in_cooldown  = 300
    scale_out_cooldown = 60
  }
}
```

#### 4.1.2 PgBouncer Configuration

```hcl
# terraform/modules/ecs/pgbouncer.tf

# PgBouncer runs as a sidecar container in the API task definition
resource "aws_ecs_task_definition" "api_with_pgbouncer" {
  family                   = "mathpath-api"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 1536   # 1.5 vCPU (1024 API + 512 PgBouncer)
  memory                   = 3072   # 3 GB (2048 API + 1024 PgBouncer)
  
  execution_role_arn = aws_iam_role.ecs_execution.arn
  task_role_arn      = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name  = "api"
      image = "${var.ecr_repo_url}:${var.api_image_tag}"
      cpu   = 1024
      memory = 2048
      
      portMappings = [
        { containerPort = 8000, protocol = "tcp" }
      ]
      
      environment = [
        # Connect to PgBouncer sidecar on localhost:6432
        { name = "DATABASE_URL", value = "postgresql://mathpath:${var.db_password}@localhost:6432/mathpath" },
        { name = "REDIS_URL", value = var.redis_url },
      ]
      
      dependsOn = [
        { containerName = "pgbouncer", condition = "HEALTHY" }
      ]
      
      stopTimeout = 120
    },
    {
      name  = "pgbouncer"
      image = "bitnami/pgbouncer:1.22"
      cpu   = 256
      memory = 512
      
      portMappings = [
        { containerPort = 6432, protocol = "tcp" }
      ]
      
      environment = [
        { name = "POSTGRESQL_HOST", value = var.rds_endpoint },
        { name = "POSTGRESQL_PORT", value = "5432" },
        { name = "POSTGRESQL_DATABASE", value = "mathpath" },
        { name = "POSTGRESQL_USERNAME", value = "mathpath" },
        { name = "PGBOUNCER_POOL_MODE", value = "transaction" },
        { name = "PGBOUNCER_MAX_CLIENT_CONN", value = "500" },
        { name = "PGBOUNCER_DEFAULT_POOL_SIZE", value = "20" },
        { name = "PGBOUNCER_MIN_POOL_SIZE", value = "5" },
        { name = "PGBOUNCER_RESERVE_POOL_SIZE", value = "5" },
        { name = "PGBOUNCER_RESERVE_POOL_TIMEOUT", value = "3" },
        { name = "PGBOUNCER_SERVER_IDLE_TIMEOUT", value = "600" },
        { name = "PGBOUNCER_LOG_CONNECTIONS", value = "0" },
        { name = "PGBOUNCER_LOG_DISCONNECTIONS", value = "0" },
        { name = "PGBOUNCER_STATS_PERIOD", value = "60" },
      ]
      
      secrets = [
        { name = "POSTGRESQL_PASSWORD", valueFrom = "${var.db_password_ssm_arn}" }
      ]
      
      healthCheck = {
        command     = ["CMD-SHELL", "pg_isready -h localhost -p 6432 -U mathpath || exit 1"]
        interval    = 15
        timeout     = 5
        retries     = 3
        startPeriod = 10
      }
    }
  ])
}
```

#### 4.1.3 Redis Configuration

```hcl
# terraform/modules/elasticache/main.tf

resource "aws_elasticache_replication_group" "redis" {
  replication_group_id       = "mathpath-redis"
  description                = "MathPath Redis cluster"
  node_type                  = "cache.t4g.medium"   # 2 vCPU, 3.09 GB
  num_cache_clusters         = 2                      # Primary + 1 replica
  automatic_failover_enabled = true
  multi_az_enabled           = true
  
  engine         = "redis"
  engine_version = "7.1"
  port           = 6379
  
  parameter_group_name = aws_elasticache_parameter_group.redis.name
  subnet_group_name    = aws_elasticache_subnet_group.redis.name
  security_group_ids   = [aws_security_group.redis.id]
  
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  
  snapshot_retention_limit = 7
  snapshot_window          = "03:00-04:00"
  maintenance_window       = "sun:04:00-sun:05:00"
}

resource "aws_elasticache_parameter_group" "redis" {
  name   = "mathpath-redis-params"
  family = "redis7"
  
  parameter {
    name  = "maxmemory-policy"
    value = "allkeys-lru"          # LRU eviction for working memory
  }
  
  # Max memory is set by node type (3.09 GB for t4g.medium)
  # Working memory keys have TTLs, so LRU eviction is a safety net
}
```

#### 4.1.4 CloudFront Configuration

```hcl
# terraform/modules/cloudfront/main.tf

resource "aws_cloudfront_distribution" "frontend" {
  enabled         = true
  is_ipv6_enabled = true
  comment         = "MathPath Oregon frontend CDN"
  
  # Origin: Vercel deployment
  origin {
    domain_name = "mathpath-app.vercel.app"
    origin_id   = "vercel"
    
    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "https-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }
  
  # Origin: S3 for PDF reports
  origin {
    domain_name = aws_s3_bucket.reports.bucket_regional_domain_name
    origin_id   = "s3-reports"
    
    s3_origin_config {
      origin_access_identity = aws_cloudfront_origin_access_identity.s3.cloudfront_access_identity_path
    }
  }
  
  # Default behavior: Vercel (frontend)
  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "vercel"
    
    forwarded_values {
      query_string = true
      cookies {
        forward = "none"
      }
    }
    
    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 86400     # 1 day for static assets
    max_ttl                = 2592000   # 30 days
    compress               = true
  }
  
  # Cache behavior: Static assets (long TTL)
  ordered_cache_behavior {
    path_pattern     = "/_next/static/*"
    allowed_methods  = ["GET", "HEAD"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "vercel"
    
    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }
    
    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 2592000   # 30 days (immutable hashed filenames)
    default_ttl            = 2592000
    max_ttl                = 31536000  # 1 year
    compress               = true
  }
  
  # Cache behavior: API routes (NO caching)
  ordered_cache_behavior {
    path_pattern     = "/api/*"
    allowed_methods  = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "vercel"
    
    forwarded_values {
      query_string = true
      headers      = ["Authorization", "Origin"]
      cookies {
        forward = "all"
      }
    }
    
    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 0
    max_ttl                = 0
    compress               = true
  }
  
  restrictions {
    geo_restriction {
      restriction_type = "whitelist"
      locations        = ["US"]  # Oregon-focused, US only for MVP
    }
  }
  
  viewer_certificate {
    acm_certificate_arn      = var.acm_certificate_arn
    ssl_support_method       = "sni-only"
    minimum_protocol_version = "TLSv1.2_2021"
  }
}
```

### 4.2 AWS SES Configuration for Notifications

```hcl
# terraform/modules/ses/main.tf

resource "aws_ses_domain_identity" "main" {
  domain = "mathpath.org"
}

resource "aws_ses_domain_dkim" "main" {
  domain = aws_ses_domain_identity.main.domain
}

# Email templates
resource "aws_ses_template" "assessment_complete" {
  name    = "mathpath-assessment-complete"
  subject = "{{student_name}}'s Math Assessment Results Are Ready"
  html    = file("${path.module}/templates/assessment_complete.html")
  text    = file("${path.module}/templates/assessment_complete.txt")
}

resource "aws_ses_template" "weekly_summary" {
  name    = "mathpath-weekly-summary"
  subject = "{{student_name}}'s Weekly Math Progress"
  html    = file("${path.module}/templates/weekly_summary.html")
  text    = file("${path.module}/templates/weekly_summary.txt")
}

resource "aws_ses_template" "milestone_achieved" {
  name    = "mathpath-milestone"
  subject = "Celebration! {{student_name}} reached a new milestone!"
  html    = file("${path.module}/templates/milestone.html")
  text    = file("${path.module}/templates/milestone.txt")
}

# SES event destination for tracking opens/clicks
resource "aws_ses_configuration_set" "main" {
  name = "mathpath-notifications"
}

resource "aws_ses_event_destination" "sns" {
  name                   = "mathpath-ses-events"
  configuration_set_name = aws_ses_configuration_set.main.name
  enabled                = true
  matching_types         = ["bounce", "complaint", "delivery", "open", "click"]
  
  sns_destination {
    topic_arn = aws_sns_topic.ses_events.arn
  }
}

# IAM policy for ECS to send via SES
resource "aws_iam_role_policy" "ecs_ses" {
  name = "mathpath-ecs-ses"
  role = aws_iam_role.ecs_task.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ses:SendEmail",
          "ses:SendTemplatedEmail",
          "ses:SendBulkTemplatedEmail"
        ]
        Resource = "*"
        Condition = {
          StringEquals = {
            "ses:FromAddress" = "notifications@mathpath.org"
          }
        }
      }
    ]
  })
}
```

---

## 5. Testing Plan

### 5.1 IRT Algorithm Tests

```python
# tests/unit/test_irt.py

import pytest
import math
import numpy as np
from services.irt_service import (
    eap_estimate,
    irt_3pl_probability,
    fisher_information,
    classify_proficiency,
    ItemResponse,
    ProficiencyLevel,
)


class TestIRT3PLProbability:
    
    def test_probability_at_difficulty_equals_midpoint(self):
        """When theta = b and c = 0, P should be 0.5."""
        p = irt_3pl_probability(theta=1.0, a=1.0, b=1.0, c=0.0)
        assert abs(p - 0.5) < 0.001
    
    def test_probability_increases_with_theta(self):
        """P should increase as theta increases."""
        p1 = irt_3pl_probability(theta=0.0, a=1.0, b=0.5, c=0.2)
        p2 = irt_3pl_probability(theta=1.0, a=1.0, b=0.5, c=0.2)
        assert p2 > p1
    
    def test_probability_lower_bound_is_c(self):
        """For very low theta, P should approach c."""
        p = irt_3pl_probability(theta=-10.0, a=1.0, b=0.0, c=0.25)
        assert abs(p - 0.25) < 0.01
    
    def test_probability_upper_bound_is_one(self):
        """For very high theta, P should approach 1.0."""
        p = irt_3pl_probability(theta=10.0, a=1.0, b=0.0, c=0.25)
        assert abs(p - 1.0) < 0.01
    
    def test_higher_discrimination_steeper_curve(self):
        """Higher a should make the curve steeper around b."""
        # At theta slightly above b, high-a item should have higher P
        p_low_a = irt_3pl_probability(theta=0.5, a=0.5, b=0.0, c=0.0)
        p_high_a = irt_3pl_probability(theta=0.5, a=2.0, b=0.0, c=0.0)
        assert p_high_a > p_low_a


class TestEAPEstimation:
    
    def test_empty_responses_returns_prior(self):
        """With no responses, EAP should return the prior."""
        result = eap_estimate([], prior_mean=0.0, prior_std=1.0)
        assert abs(result.theta - 0.0) < 0.01
        assert abs(result.sem - 1.0) < 0.01
    
    def test_eap_increases_with_correct_responses(self):
        """EAP theta should increase when adding correct responses to easy items."""
        responses_1 = [
            ItemResponse("q1", a=1.0, b=-1.0, c=0.2, is_correct=True),
        ]
        responses_5 = [
            ItemResponse(f"q{i}", a=1.0, b=-1.0 + 0.5*i, c=0.2, is_correct=True)
            for i in range(5)
        ]
        
        result_1 = eap_estimate(responses_1)
        result_5 = eap_estimate(responses_5)
        
        assert result_5.theta > result_1.theta
    
    def test_eap_estimation_accuracy(self):
        """EAP estimate should be within 0.3 of true theta for 30 items.
        
        This is a simulation test: generate responses from a known true theta,
        then verify the EAP estimate is close.
        """
        true_theta = 0.5
        np.random.seed(42)
        
        # Generate 30 items with varied difficulty
        items = []
        for i in range(30):
            a = 1.0 + np.random.uniform(-0.3, 0.3)
            b = -2.0 + i * (4.0 / 29)  # Spread from -2 to +2
            c = 0.2
            p = irt_3pl_probability(true_theta, a, b, c)
            correct = np.random.random() < p
            items.append(ItemResponse(f"q{i}", a=a, b=b, c=c, is_correct=correct))
        
        result = eap_estimate(items)
        
        assert abs(result.theta - true_theta) < 0.3, \
            f"EAP estimate {result.theta:.3f} too far from true theta {true_theta}"
        assert result.sem < 0.5, \
            f"SEM {result.sem:.3f} too high for 30 items"
    
    def test_sem_decreases_with_more_items(self):
        """SEM should decrease as more items are administered."""
        base_responses = [
            ItemResponse(f"q{i}", a=1.2, b=-1.0 + 0.2*i, c=0.2, is_correct=(i % 3 != 0))
            for i in range(5)
        ]
        
        sem_5 = eap_estimate(base_responses[:5]).sem
        
        extended = base_responses + [
            ItemResponse(f"q{5+i}", a=1.2, b=0.0 + 0.2*i, c=0.2, is_correct=(i % 2 == 0))
            for i in range(15)
        ]
        sem_20 = eap_estimate(extended).sem
        
        assert sem_20 < sem_5
    
    def test_all_correct_gives_high_theta(self):
        """All correct responses should give a high theta estimate."""
        responses = [
            ItemResponse(f"q{i}", a=1.0, b=-1.0 + 0.3*i, c=0.2, is_correct=True)
            for i in range(20)
        ]
        result = eap_estimate(responses)
        assert result.theta > 1.0
    
    def test_all_incorrect_gives_low_theta(self):
        """All incorrect responses should give a low theta estimate."""
        responses = [
            ItemResponse(f"q{i}", a=1.0, b=-1.0 + 0.3*i, c=0.2, is_correct=False)
            for i in range(20)
        ]
        result = eap_estimate(responses)
        assert result.theta < -1.0


class TestMaximumFisherInformationSelection:
    
    def test_selects_item_near_theta(self):
        """MFI should select items with difficulty near current theta."""
        from services.irt_service import select_next_item, IRTItem
        
        items = [
            IRTItem("q1", a=1.0, b=-2.0, c=0.2),
            IRTItem("q2", a=1.0, b=0.0, c=0.2),   # Closest to theta=0
            IRTItem("q3", a=1.0, b=2.0, c=0.2),
        ]
        
        selected = select_next_item(
            theta=0.0,
            item_bank=items,
            excluded_ids=set(),
        )
        
        # Should select q2 (b=0.0, closest to theta=0.0)
        assert selected.question_id == "q2"
    
    def test_prefers_high_discrimination(self):
        """Among items with same difficulty, should prefer higher discrimination."""
        from services.irt_service import select_next_item, IRTItem
        
        items = [
            IRTItem("q1", a=0.5, b=0.0, c=0.2),
            IRTItem("q2", a=2.0, b=0.0, c=0.2),   # Higher discrimination
        ]
        
        selected = select_next_item(
            theta=0.0,
            item_bank=items,
            excluded_ids=set(),
        )
        
        assert selected.question_id == "q2"
    
    def test_excludes_administered_items(self):
        """Should not select items already administered."""
        from services.irt_service import select_next_item, IRTItem
        
        items = [
            IRTItem("q1", a=2.0, b=0.0, c=0.2),   # Best item, but excluded
            IRTItem("q2", a=1.0, b=0.0, c=0.2),
        ]
        
        selected = select_next_item(
            theta=0.0,
            item_bank=items,
            excluded_ids={"q1"},
        )
        
        assert selected.question_id == "q2"


class TestStoppingCriteria:
    
    def test_stops_on_sem_threshold(self):
        """Assessment stops when SEM < 0.30 and >= 15 items."""
        from services.irt_service import IRTService
        irt = IRTService()
        
        should_stop, reason = irt.check_stopping_criteria(
            theta=0.5, sem=0.28, items_administered=20, elapsed_seconds=1800
        )
        assert should_stop is True
        assert reason == "sem_threshold"
    
    def test_does_not_stop_before_minimum_items(self):
        """Should not stop for SEM before 15 items."""
        from services.irt_service import IRTService
        irt = IRTService()
        
        should_stop, _ = irt.check_stopping_criteria(
            theta=0.5, sem=0.25, items_administered=10, elapsed_seconds=600
        )
        assert should_stop is False
    
    def test_stops_at_max_items(self):
        """Assessment stops at 40 items regardless of SEM."""
        from services.irt_service import IRTService
        irt = IRTService()
        
        should_stop, reason = irt.check_stopping_criteria(
            theta=0.5, sem=0.50, items_administered=40, elapsed_seconds=3000
        )
        assert should_stop is True
        assert reason == "max_items"
    
    def test_stops_at_max_time(self):
        """Assessment stops at 75 minutes."""
        from services.irt_service import IRTService
        irt = IRTService()
        
        should_stop, reason = irt.check_stopping_criteria(
            theta=0.5, sem=0.40, items_administered=25, elapsed_seconds=75 * 60
        )
        assert should_stop is True
        assert reason == "max_time"


class TestProficiencyClassification:
    
    def test_below_par(self):
        assert classify_proficiency(-1.0, 0.25) == ProficiencyLevel.BELOW_PAR
    
    def test_approaching(self):
        assert classify_proficiency(-0.3, 0.25) == ProficiencyLevel.APPROACHING
    
    def test_on_par(self):
        assert classify_proficiency(0.5, 0.25) == ProficiencyLevel.ON_PAR
    
    def test_above_par(self):
        assert classify_proficiency(1.0, 0.25) == ProficiencyLevel.ABOVE_PAR
    
    def test_conservative_classification_with_high_sem(self):
        """With high SEM, conservative classification should lower effective theta."""
        # theta=0.5 is normally ON_PAR, but with SEM=0.6:
        # effective theta = 0.5 - 0.6 = -0.1 → APPROACHING
        result = classify_proficiency(0.5, 0.6, conservative=True)
        assert result == ProficiencyLevel.APPROACHING
    
    def test_boundary_below_par_approaching(self):
        """Exactly at -0.5 should be APPROACHING (not BELOW_PAR)."""
        assert classify_proficiency(-0.5, 0.2) == ProficiencyLevel.APPROACHING
```

### 5.2 Report Generation Tests

```python
# tests/unit/test_report_generation.py

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4


class TestReportDataAssembly:
    """Test report data assembly with mocked DB queries."""
    
    @pytest.mark.asyncio
    @patch("services.report_service.ReportGenerator._get_student_profile")
    @patch("services.report_service.ReportGenerator._get_assessment_results")
    @patch("services.report_service.ReportGenerator._get_domain_scores")
    @patch("services.report_service.ReportGenerator._get_skill_mastery")
    @patch("services.report_service.ReportGenerator._get_practice_history")
    @patch("services.report_service.ReportGenerator._get_growth_data")
    async def test_all_queries_run_in_parallel(
        self, mock_growth, mock_practice, mock_skills, mock_domains,
        mock_assessment, mock_student,
    ):
        """All 6 data queries should execute concurrently via asyncio.gather."""
        # Configure mocks
        mock_student.return_value = {"name": "Alice", "grade_level": 4}
        mock_assessment.return_value = {
            "completed_at": "2026-04-01", "proficiency_level": "on_par",
            "theta_estimate": 0.5, "sem": 0.25, "items_administered": 25,
        }
        mock_domains.return_value = {"OA": {"theta": 0.6, "items": 8, "correct": 6}}
        mock_skills.return_value = []
        mock_practice.return_value = {"sessions": 10, "total_questions": 100}
        mock_growth.return_value = []
        
        from services.report_service import ReportGenerator
        gen = ReportGenerator()
        
        # This should work without error
        report = await gen.generate_full_report(
            student_id=uuid4(), assessment_id=uuid4(), version="teacher",
        )
        
        # Verify all queries were called
        mock_student.assert_called_once()
        mock_assessment.assert_called_once()
        mock_domains.assert_called_once()
        mock_skills.assert_called_once()
        mock_practice.assert_called_once()
        mock_growth.assert_called_once()


class TestPDFGeneration:
    """Integration tests for PDF generation."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_teacher_report_pdf_generated(self):
        """Full PDF generation against test DB, verify file is created."""
        # This test requires a test database with seeded data
        from services.report_service import ReportGenerator
        gen = ReportGenerator()
        
        result = await gen.generate_full_report(
            student_id=TEST_STUDENT_ID,
            assessment_id=TEST_ASSESSMENT_ID,
            version="teacher",
        )
        
        assert result["pdf_s3_key"].endswith(".pdf")
        assert result["generation_time_ms"] < 10000  # < 10s
        assert result["presigned_url"].startswith("https://")
    
    @pytest.mark.integration
    def test_pdf_visual_regression(self):
        """Snapshot first page of rendered PDF for visual regression.
        
        Uses pdf2image to convert page 1 to PNG, then compares
        against a baseline image using pixelmatch.
        """
        from pdf2image import convert_from_bytes
        from PIL import Image
        import io
        
        # Generate a report PDF with known data
        html_content = render_test_report()
        from weasyprint import HTML
        pdf_bytes = HTML(string=html_content).write_pdf()
        
        # Convert first page to image
        images = convert_from_bytes(pdf_bytes, first_page=1, last_page=1, dpi=150)
        actual_image = images[0]
        
        # Load baseline
        baseline_path = "tests/fixtures/report_baseline_page1.png"
        
        try:
            baseline = Image.open(baseline_path)
            
            # Compare using pixel diff
            actual_pixels = list(actual_image.getdata())
            baseline_pixels = list(baseline.getdata())
            
            if len(actual_pixels) == len(baseline_pixels):
                diff_count = sum(
                    1 for a, b in zip(actual_pixels, baseline_pixels)
                    if abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(a[2] - b[2]) > 30
                )
                diff_pct = diff_count / len(actual_pixels) * 100
                assert diff_pct < 5.0, f"Visual regression: {diff_pct:.1f}% pixels differ"
            else:
                pytest.fail("Image dimensions changed — update baseline")
        
        except FileNotFoundError:
            # No baseline yet — save current as baseline
            actual_image.save(baseline_path)
            pytest.skip("Baseline created — re-run to compare")
```

---

## 6. QA Plan

### 6.1 Stage 4 QA Checklist (MVP Exit Criteria)

This is the **go/no-go gate** for MVP launch. All items must pass.

#### Assessment Integrity (8 items)
- [ ] **AI-01**: Assessment starts with theta=0.0 and SEM=1.0 as prior.
- [ ] **AI-02**: Each item response correctly updates theta via EAP estimation (verified with known test vectors).
- [ ] **AI-03**: SEM monotonically decreases as items are administered (with well-targeted items).
- [ ] **AI-04**: Assessment terminates when SEM < 0.30 (after ≥ 15 items).
- [ ] **AI-05**: Assessment terminates at 40 items if SEM threshold not reached.
- [ ] **AI-06**: Assessment terminates at 75 minutes.
- [ ] **AI-07**: Content balancing: each domain has ≥ 15% representation in administered items.
- [ ] **AI-08**: No assessment item is repeated within the same assessment.

#### IRT Scoring Accuracy (6 items)
- [ ] **IS-01**: EAP estimate within 0.3 of true theta on simulated data (30 items, 100 simulations).
- [ ] **IS-02**: Proficiency classification matches expected level for known theta values at all cut points.
- [ ] **IS-03**: Conservative classification activates when SEM > 0.5.
- [ ] **IS-04**: All 4 proficiency levels are reachable (verified with constructed response patterns).
- [ ] **IS-05**: Item information values are positive and finite for all items in the bank.
- [ ] **IS-06**: Theta estimates are bounded within [-4, +4] for all possible response patterns.

#### Report Generation (5 items)
- [ ] **RG-01**: Teacher report PDF renders correctly with all sections (profile, scores, domains, skills, recommendations).
- [ ] **RG-02**: Parent report uses simplified language, no theta values or technical terms.
- [ ] **RG-03**: Student report uses child-friendly language and encouraging tone.
- [ ] **RG-04**: PDF generation completes in < 5 seconds.
- [ ] **RG-05**: Presigned S3 URL grants access for 7 days and then expires.

#### Teacher Dashboard (6 items)
- [ ] **TD-01**: Teacher sees only students they have access to (teacher_student_access enforced).
- [ ] **TD-02**: Class-level proficiency distribution chart renders correctly.
- [ ] **TD-03**: Per-student drill-down shows assessment history, skill mastery, and practice stats.
- [ ] **TD-04**: Teacher can download PDF reports for any authorized student.
- [ ] **TD-05**: Remediation plan view shows deficient skills and recommended modules.
- [ ] **TD-06**: Teacher cannot access students from other classes/schools.

#### Parent Dashboard (5 items)
- [ ] **PD-01**: Parent sees only their linked children.
- [ ] **PD-02**: Progress summary shows proficiency level, recent practice, and milestones.
- [ ] **PD-03**: Parent can download child-version or parent-version report.
- [ ] **PD-04**: No internal identifiers (UUIDs, theta values) exposed in parent UI.
- [ ] **PD-05**: Parent dashboard loads in < 3 seconds.

#### Notification Delivery (5 items)
- [ ] **ND-01**: Assessment completion email sent to teacher and parent within 5 minutes.
- [ ] **ND-02**: Email contains correct student name, proficiency level, and report link.
- [ ] **ND-03**: Weekly summary email sent every Sunday at 6pm parent's local time.
- [ ] **ND-04**: Milestone notifications fire for: first assessment, proficiency improvement, 10 skills mastered.
- [ ] **ND-05**: Unsubscribe link in all emails is functional (sets notification preferences).

#### Performance Under Load (5 items)
- [ ] **PL-01**: System handles 500 concurrent practice sessions (k6 load test passes all thresholds).
- [ ] **PL-02**: System handles 50 concurrent EOG assessments with < 1s item delivery.
- [ ] **PL-03**: Report generation queue processes backlog within 5 minutes (50 reports queued).
- [ ] **PL-04**: PgBouncer maintains connection pool under load (no connection timeouts).
- [ ] **PL-05**: Redis memory usage stays below 80% of allocated memory under peak load.

#### COPPA/FERPA Compliance (7 items)
- [ ] **CF-01**: No student PII in client-side logs, analytics, or error tracking.
- [ ] **CF-02**: All student data encrypted at rest (RDS encryption, S3 SSE).
- [ ] **CF-03**: All student data encrypted in transit (TLS 1.2+).
- [ ] **CF-04**: Student accounts created only through teacher/parent-initiated flow (no direct child sign-up).
- [ ] **CF-05**: Data access audit log captures all report downloads with user ID and timestamp.
- [ ] **CF-06**: No student data shared with third-party analytics (no external SDKs on student-facing pages).
- [ ] **CF-07**: Parental consent status tracked per student; data processing halted if consent revoked.

#### Security (5 items)
- [ ] **SE-01**: All API endpoints require authentication (verified by penetration test).
- [ ] **SE-02**: JWT tokens expire within 1 hour; refresh tokens within 30 days.
- [ ] **SE-03**: SQL injection scan clean (sqlmap or similar against all endpoints).
- [ ] **SE-04**: XSS scan clean on all user-facing inputs.
- [ ] **SE-05**: Dependency vulnerability scan clean (no critical/high CVEs in production dependencies).

#### Data Integrity (3 items)
- [ ] **DI-01**: All eog_responses FK to valid eog_assessments.
- [ ] **DI-02**: All progress_reports have valid S3 keys (PDF exists and is accessible).
- [ ] **DI-03**: Remediation plans reference valid deficient skills and learning plan modules.

**Total: 55 items.**

---

## 7. Operational Runbooks

### 7.1 Runbook: Production Readiness Checklist

**Run before MVP launch. Every item must be checked off.**

#### Infrastructure & Monitoring
- [ ] All CloudWatch alarms configured and tested (manually triggered):
  - [ ] ECS CPU > 80%
  - [ ] ECS Memory > 85%
  - [ ] RDS CPU > 70%
  - [ ] RDS connection count > 80% of max
  - [ ] Redis memory > 75%
  - [ ] ALB 5xx error rate > 1%
  - [ ] ALB response time p95 > 2s
  - [ ] SQS DLQ message count > 0
  - [ ] WebSocket connection count > 600
- [ ] PagerDuty/OpsGenie integration tested (alert → page on-call engineer)
- [ ] RDS automated backups configured (daily, 7-day retention)
- [ ] RDS point-in-time recovery tested (restore from 1 hour ago, verify data)
- [ ] Redis cluster failover tested (kill primary, verify replica promotion)
- [ ] ECS deployment strategy set to rolling update with health checks
- [ ] ECS task deregistration delay set to 120s for WebSocket draining

#### Application
- [ ] All environment variables set in production ECS task definition
- [ ] API keys rotated and stored in SSM Parameter Store (not env vars)
- [ ] Database migrations run successfully against production schema
- [ ] Seed data loaded (BKT parameters, item bank, SES templates)
- [ ] Health check endpoint (`/health`) returns 200 with component status
- [ ] Structured logging configured (JSON format, CloudWatch Logs)
- [ ] Request tracing enabled (X-Ray or OpenTelemetry)
- [ ] Feature flags system operational (Redis-backed)

#### Security
- [ ] HTTPS enforced everywhere (HSTS headers set)
- [ ] CORS configured to allow only mathpath.org origins
- [ ] Rate limiting configured on all public endpoints
- [ ] WAF rules active on ALB (SQL injection, XSS, rate limiting)
- [ ] Penetration test completed with no critical findings
- [ ] Dependency scan clean (Snyk or Dependabot)

#### Compliance
- [ ] COPPA consent flow reviewed by legal counsel
- [ ] Privacy policy published and linked from all pages
- [ ] Terms of service published
- [ ] Data processing agreement template ready for school districts
- [ ] Data retention policy documented (what data, how long, deletion process)
- [ ] FERPA-compliant data handling verified by compliance officer

#### Performance
- [ ] Load test passed: 500 concurrent practice sessions
- [ ] Load test passed: 50 concurrent EOG assessments
- [ ] Report generation queue: 50 reports processed in < 5 minutes
- [ ] Frontend Core Web Vitals: LCP < 2.5s, FID < 100ms, CLS < 0.1

#### Operations
- [ ] All operational runbooks written and reviewed
- [ ] On-call rotation established (minimum 2 engineers)
- [ ] Incident response playbook documented
- [ ] Rollback procedure tested (deploy previous version via ECS)
- [ ] Database rollback procedure tested (apply down migration)

### 7.2 Runbook: Responding to a FERPA/COPPA Complaint

**Trigger:** Received complaint from parent, school, or regulatory body regarding data privacy.

**Severity Classification:**

| Severity | Definition | Response SLA |
|----------|-----------|-------------|
| Critical | Data breach involving student PII | Notify legal within 1 hour; remediate immediately |
| High | Unauthorized access to student records | Acknowledge within 4 hours; investigate within 24 hours |
| Medium | Alleged policy violation (no data exposure) | Acknowledge within 24 hours; investigate within 72 hours |
| Low | General inquiry about data practices | Respond within 5 business days |

**Steps:**

1. **Acknowledge receipt** (within SLA for severity):
   - Log the complaint in the compliance incident tracker.
   - Send acknowledgment to the complainant with a case number.
   - Assign a compliance lead and engineering lead.

2. **Assess scope and severity:**
   - What specific data is in question?
   - Which student(s) affected?
   - What regulation is alleged to be violated?
   - Is there evidence of actual unauthorized data access?
   
   ```sql
   -- Identify all data for the student in question
   SELECT 'practice_sessions' as table_name, COUNT(*) FROM practice_sessions WHERE student_id = $ID
   UNION ALL
   SELECT 'eog_assessments', COUNT(*) FROM eog_assessments WHERE student_id = $ID
   UNION ALL
   SELECT 'agent_interaction_logs', COUNT(*) FROM agent_interaction_logs 
     WHERE session_id IN (SELECT session_id FROM practice_sessions WHERE student_id = $ID)
   UNION ALL
   SELECT 'progress_reports', COUNT(*) FROM progress_reports WHERE student_id = $ID
   UNION ALL
   SELECT 'notification_log', COUNT(*) FROM notification_log WHERE recipient_id = $ID;
   ```

3. **Investigate access history:**
   ```sql
   -- Check who accessed this student's data
   SELECT u.email, u.role, tsa.access_type, tsa.granted_at
   FROM teacher_student_access tsa
   JOIN users u ON u.id = tsa.teacher_id
   WHERE tsa.student_id = $ID;
   
   -- Check report downloads
   SELECT pr.report_type, pr.access_count, pr.last_accessed
   FROM progress_reports pr
   WHERE pr.student_id = $ID;
   ```

4. **Legal review:**
   - Forward findings to legal counsel within 4 hours of classification.
   - For data breaches: engage breach notification counsel.
   - For COPPA: verify consent status for the student.
   - For FERPA: verify the school's authorization of MathPath as a school official.

5. **Remediate if required:**
   - **Data deletion request**: Execute data deletion across all tables:
     ```sql
     -- DANGER: Complete student data deletion
     -- Must be approved by compliance lead AND engineering lead
     BEGIN;
     
     -- Delete in dependency order
     DELETE FROM hint_interactions WHERE session_question_id IN (
       SELECT id FROM session_questions WHERE session_id IN (
         SELECT session_id FROM practice_sessions WHERE student_id = $ID
       )
     );
     DELETE FROM session_responses WHERE session_question_id IN (
       SELECT id FROM session_questions WHERE session_id IN (
         SELECT session_id FROM practice_sessions WHERE student_id = $ID
       )
     );
     DELETE FROM session_questions WHERE session_id IN (
       SELECT session_id FROM practice_sessions WHERE student_id = $ID
     );
     DELETE FROM agent_interaction_logs WHERE session_id IN (
       SELECT session_id FROM practice_sessions WHERE student_id = $ID
     );
     DELETE FROM practice_sessions WHERE student_id = $ID;
     DELETE FROM bkt_state_history WHERE student_id = $ID;
     DELETE FROM student_long_term_memory WHERE student_id = $ID;
     DELETE FROM eog_responses WHERE assessment_id IN (
       SELECT id FROM eog_assessments WHERE student_id = $ID
     );
     DELETE FROM remediation_plans WHERE student_id = $ID;
     DELETE FROM eog_assessments WHERE student_id = $ID;
     DELETE FROM progress_reports WHERE student_id = $ID;
     DELETE FROM teacher_student_access WHERE student_id = $ID;
     DELETE FROM notification_log WHERE recipient_id = $ID;
     DELETE FROM students WHERE id = $ID;
     
     COMMIT;
     ```
   - Delete S3 objects (PDF reports):
     ```bash
     aws s3 rm "s3://mathpath-reports/reports/$STUDENT_ID/" --recursive
     ```
   - Clear Redis cache:
     ```bash
     redis-cli -h $REDIS_HOST --scan --pattern "*$STUDENT_ID*" | \
       xargs -r redis-cli -h $REDIS_HOST DEL
     ```

6. **For data breaches specifically:**
   - Assess whether breach notification is required:
     - COPPA: Notify FTC if children's data exposed.
     - State laws: Oregon's breach notification law (ORS 646A.604) requires notification within 45 days.
   - Prepare breach notification letter (legal counsel leads).
   - Notify affected schools/parents.
   - Document root cause and remediation in incident report.

7. **Respond to complainant:**
   - Provide written response within the SLA.
   - Include: summary of investigation, findings, actions taken, preventive measures.
   - For FERPA: document that MathPath operates under the school official exception.
   - For COPPA: document that consent was obtained through the school.

8. **Post-incident:**
   - Conduct blameless retrospective.
   - Update data handling procedures if gaps identified.
   - Update privacy training materials.
   - Implement technical controls to prevent recurrence.
   - File incident report with compliance record.

---

## Appendix A: Report Template Structure

### Teacher Report (report_teacher_v1.0.html)

```
Page 1:
┌──────────────────────────────────────────────┐
│  MATHPATH OREGON — Assessment Report         │
│  Student: [Name]       Grade: [N]            │
│  Assessment Date: [Date]                     │
│  ─────────────────────────────────────────── │
│                                              │
│  PROFICIENCY LEVEL: [Level]                  │
│  ████████████░░░░░░ [Visual bar]             │
│                                              │
│  θ estimate: [X.XX]   SEM: [X.XX]           │
│  Items: [N]   Time: [MM:SS]                 │
│  ─────────────────────────────────────────── │
│                                              │
│  DOMAIN BREAKDOWN                            │
│  ┌─────────────────────────────────────────┐ │
│  │ OA: Operations & Algebraic Thinking     │ │
│  │ ████████░░ 72% correct (8 items)       │ │
│  │                                         │ │
│  │ NF: Number & Operations (Fractions)     │ │
│  │ █████░░░░░ 50% correct (6 items)       │ │
│  │                                         │ │
│  │ MD: Measurement & Data                  │ │
│  │ ██████████ 90% correct (5 items)       │ │
│  │                                         │ │
│  │ G: Geometry                             │ │
│  │ ██████░░░░ 60% correct (4 items)       │ │
│  └─────────────────────────────────────────┘ │
└──────────────────────────────────────────────┘

Page 2:
┌──────────────────────────────────────────────┐
│  SKILL MASTERY DETAIL                        │
│  ┌─────────────────────┬────────┬──────────┐ │
│  │ Skill               │ Status │ P(master)│ │
│  ├─────────────────────┼────────┼──────────┤ │
│  │ 3.OA.A.1 Interpret  │   ✓    │  0.97    │ │
│  │ 3.OA.A.2 Divide     │   ✓    │  0.95    │ │
│  │ 3.NF.A.1 Understand │   ~    │  0.72    │ │
│  │ 3.MD.A.1 Tell time  │   ✓    │  0.98    │ │
│  │ ...                 │        │          │ │
│  └─────────────────────┴────────┴──────────┘ │
│                                              │
│  GROWTH OVER TIME                            │
│  [Line chart: theta over assessment dates]   │
│                                              │
│  PRACTICE HISTORY                            │
│  Sessions: [N]   Questions: [N]              │
│  Avg correct rate: [N]%                      │
│  ─────────────────────────────────────────── │
│                                              │
│  RECOMMENDATIONS                             │
│  1. Focus practice on fractions (3.NF.A)     │
│  2. Continue strong work in measurement      │
│  3. Consider geometry enrichment activities   │
│                                              │
│  Generated: [timestamp] | MathPath Oregon    │
└──────────────────────────────────────────────┘
```

### Parent Report (report_parent_v1.0.html)

Simplified version:
- No theta values or SEM
- Uses "Your child is performing at/above/below grade level" language
- Visual progress bars (stars, not numbers)
- Encouragement-first tone
- Specific activity suggestions parents can do at home

### Student Report (report_student_v1.0.html)

Child-friendly version:
- "Great job!" emphasis
- Shows mastered skills as collected achievements
- Uses characters/illustrations
- No proficiency level labels — uses growth mindset framing
- "You're getting better at…" and "Next, you'll learn…"
