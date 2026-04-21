# Stage 2 Production Remediation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Take the Stage 2 codebase (built by local Qwen 2.5) from prototype quality to production-readiness by fixing the critical security, COPPA compliance, schema, and test-quality issues surfaced in the 2026-04-20 production-readiness review.

**Architecture:** Execute in four phases, ordered by blast radius: (1) legal/security blockers — secrets, COPPA consent, IDOR, auth callback; (2) correctness — schema/model divergence, broken endpoint, token storage, audit log; (3) test suite repair — fixture plumbing, rewrite fake tests, align schemas; (4) cleanup — docs debris, rate limiting, observability hooks. Each phase must be green before moving to the next.

**Tech Stack:** FastAPI (Python 3.12), SQLAlchemy 2.0 async, Pydantic v2, Auth0, PostgreSQL 17 + pgvector, Redis 7, Next.js 15, React 19, TypeScript, Tailwind, pnpm + Turbo, Alembic, pytest + pytest-asyncio, Vitest + Playwright, LiteLLM (Ollama local + Claude cloud).

**Review artifacts this plan remediates:**
- `STAGE2-TEST-ISSUES.md` (test suite failures)
- 2026-04-20 review covering: backend architecture, test coverage, E2E + security/COPPA, frontend, infrastructure
- Prior plan: `/Users/aerobu/.claude/plans/look-at-stage2-test-issues-md-and-jazzy-pelican.md` (subsumed by Phase 3)

**Non-goals:** Stage 3+ features (LangGraph, multi-agent tutoring). Next.js App Router rewrite. Postgres → MySQL migration. Any work not listed in the tasks below.

---

## Phase 0 — Prep (do once, before any other task)

### Task 0.1: Create worktree and branch

**Files:**
- Worktree: `/Users/aerobu/claude_code_projects/padi_ai-stage2-remediation` (or similar)

- [ ] **Step 1: Confirm current git state is committed**

Run: `git -C /Users/aerobu/claude_code_projects/padi_ai status --short | wc -l`
Expected: `0` (no uncommitted changes). If non-zero, commit or stash before proceeding.

- [ ] **Step 2: Create remediation branch**

```bash
cd /Users/aerobu/claude_code_projects/padi_ai
git checkout -b remediation/stage2-production main
```

- [ ] **Step 3: Verify backend tests run at all**

```bash
cd apps/api
python -m pytest tests/api/test_parent_dashboard.py -v --tb=line
```
Expected: 7 passed. This is our "green baseline" — if it fails we stop here and fix environment before doing any remediation work.

---

## Phase 1 — CRITICAL: Legal & security blockers

Nothing else matters if these ship. Each task stands alone; commit between tasks.

### Task 1.1: Purge secrets from git and rotate

**Files:**
- Delete: `apps/api/.env`
- Modify: `.gitignore`
- Create: `apps/api/.env.local.example` (new reference)

Context: `apps/api/.env` contains `DATABASE_URL=postgresql://padi:padi_secret@...`, `AUTH0_SECRET=placeholder_secret`, and `AUTH0_CLIENT_SECRET=your-client-secret`. Even "placeholder" values indicate the pattern of committing real secrets and must be treated as compromised.

- [ ] **Step 1: Confirm `.env` is tracked**

Run: `git ls-files apps/api/.env`
Expected output: `apps/api/.env`

- [ ] **Step 2: Verify `.gitignore` coverage**

Read `.gitignore`. If it does not already contain the lines below, add them:
```
.env
.env.local
.env.*.local
apps/*/.env
apps/*/.env.local
```

- [ ] **Step 3: Remove `.env` from tracking**

```bash
git rm --cached apps/api/.env
```

- [ ] **Step 4: Rewrite history to purge the file**

Decide with user before running. Options:
- **Keep history, accept leak** (faster): skip this step; rotate credentials and move on.
- **Purge history**: `git filter-repo --path apps/api/.env --invert-paths` (requires pipx install git-filter-repo). Only do this if the repo is private and has no collaborators past `HEAD`.

Record the decision in the commit message.

- [ ] **Step 5: Rotate every credential that ever appeared in `apps/api/.env`**

- Postgres password: update in Postgres, in docker-compose, in any deployed env.
- Auth0 client secret: regenerate in Auth0 dashboard.
- Any other secrets: regenerate.

This is a manual step — record a checklist in `SECURITY-ROTATION-2026-04-20.md` (then delete the file after rotation is complete).

- [ ] **Step 6: Commit the purge**

```bash
git add .gitignore
git commit -m "security: remove committed secrets, update gitignore

Removed apps/api/.env from tracking. All credentials that appeared
in that file have been rotated out-of-band."
```

### Task 1.2: Fix COPPA-inverted consent form

**Files:**
- Modify: `apps/web/components/assessment/ConsentForm.tsx`
- Test: `apps/web/tests/components/ConsentForm.test.tsx` (create if missing)

Context: The current form at `ConsentForm.tsx:115` presents a checkbox reading "I am over 13". The app is for students Grades 1-5 (under 13). COPPA requires the PARENT to confirm they are the parent/guardian of a minor child and explicitly consent to data collection. The current form is legally non-compliant.

- [ ] **Step 1: Read the current component**

```bash
cat apps/web/components/assessment/ConsentForm.tsx
```
Note the props, state shape, and submission handler signature.

- [ ] **Step 2: Write the failing test**

Create `apps/web/tests/components/ConsentForm.test.tsx`:

```tsx
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { ConsentForm } from "@/components/assessment/ConsentForm";

describe("ConsentForm COPPA compliance", () => {
  it("does NOT contain an 'over 13' self-attestation", () => {
    render(<ConsentForm onSubmit={vi.fn()} />);
    expect(screen.queryByText(/over 13/i)).toBeNull();
    expect(screen.queryByText(/am 13/i)).toBeNull();
  });

  it("requires parent/guardian attestation", () => {
    render(<ConsentForm onSubmit={vi.fn()} />);
    expect(
      screen.getByLabelText(/parent or legal guardian/i)
    ).toBeInTheDocument();
  });

  it("requires explicit data-collection consent", () => {
    render(<ConsentForm onSubmit={vi.fn()} />);
    expect(
      screen.getByLabelText(/consent to the collection/i)
    ).toBeInTheDocument();
  });

  it("disables submit until both boxes are checked", () => {
    const onSubmit = vi.fn();
    render(<ConsentForm onSubmit={onSubmit} />);
    const submit = screen.getByRole("button", { name: /consent/i });
    expect(submit).toBeDisabled();

    fireEvent.click(screen.getByLabelText(/parent or legal guardian/i));
    expect(submit).toBeDisabled();

    fireEvent.click(screen.getByLabelText(/consent to the collection/i));
    expect(submit).not.toBeDisabled();
  });
});
```

- [ ] **Step 3: Run the test to verify it fails**

```bash
cd apps/web
pnpm vitest run tests/components/ConsentForm.test.tsx
```
Expected: FAIL.

- [ ] **Step 4: Rewrite the form**

Replace the two checkbox rows in `apps/web/components/assessment/ConsentForm.tsx` with:

```tsx
<label className="flex items-start gap-3">
  <input
    type="checkbox"
    checked={isParentGuardian}
    onChange={(e) => setIsParentGuardian(e.target.checked)}
    aria-required="true"
  />
  <span>
    I am the parent or legal guardian of the child I am enrolling, and I am
    at least 18 years old.
  </span>
</label>

<label className="flex items-start gap-3">
  <input
    type="checkbox"
    checked={dataConsent}
    onChange={(e) => setDataConsent(e.target.checked)}
    aria-required="true"
  />
  <span>
    I consent to the collection and processing of my child's first name,
    grade level, and assessment responses for the purpose of providing
    personalized math instruction, as described in the{" "}
    <a href="/privacy" className="underline">
      Privacy Policy
    </a>
    .
  </span>
</label>
```

Update the state variables and the submit button's `disabled={!(isParentGuardian && dataConsent)}` binding accordingly.

- [ ] **Step 5: Run the test to verify it passes**

```bash
pnpm vitest run tests/components/ConsentForm.test.tsx
```
Expected: PASS (all 4 tests).

- [ ] **Step 6: Commit**

```bash
git add apps/web/components/assessment/ConsentForm.tsx apps/web/tests/components/ConsentForm.test.tsx
git commit -m "fix(coppa): replace 'over 13' checkbox with parent/guardian attestation

The prior form asked the user to confirm 'I am over 13' — inverted
for a platform serving children under 13. Replaced with explicit
parent/guardian attestation and data-collection consent per COPPA."
```

### Task 1.3: Fix Auth0 callback `origin` crash

**Files:**
- Modify: `apps/web/app/api/auth/callback/route.ts`
- Test: `apps/web/tests/api/auth-callback.test.ts` (create)

Context: Callback route references `origin` as a variable at lines 16, 20, 24, 69 but never declares it. Every Auth0 redirect crashes. Pattern used elsewhere (`login/route.ts`) is `const origin = request.headers.get('origin') ?? new URL(request.url).origin`.

- [ ] **Step 1: Read the current route**

```bash
cat apps/web/app/api/auth/callback/route.ts
```

- [ ] **Step 2: Write the failing test**

Create `apps/web/tests/api/auth-callback.test.ts`:

```ts
import { describe, it, expect, vi } from "vitest";
import { GET } from "@/app/api/auth/callback/route";

describe("Auth0 callback route", () => {
  it("derives origin from request headers when present", async () => {
    const req = new Request("http://test.local/api/auth/callback?code=x&state=y", {
      headers: { origin: "https://app.example.com" },
    });
    const res = await GET(req);
    // Should redirect (302) or return token response — NOT throw ReferenceError
    expect(res.status).toBeLessThan(500);
  });

  it("falls back to request URL origin when header missing", async () => {
    const req = new Request("http://test.local/api/auth/callback?code=x&state=y");
    const res = await GET(req);
    expect(res.status).toBeLessThan(500);
  });
});
```

Mock Auth0 token exchange with `vi.mock('@/lib/auth0-client', ...)` — see existing test patterns in `apps/web/tests/`.

- [ ] **Step 3: Run the test to verify it fails**

```bash
cd apps/web
pnpm vitest run tests/api/auth-callback.test.ts
```
Expected: FAIL with `ReferenceError: origin is not defined`.

- [ ] **Step 4: Fix the route**

At the top of the `GET` handler in `apps/web/app/api/auth/callback/route.ts`, add:

```ts
const origin =
  request.headers.get("origin") ?? new URL(request.url).origin;
```

Replace the four bare `origin` references (lines 16, 20, 24, 69) with this local constant.

- [ ] **Step 5: Run the test to verify it passes**

```bash
pnpm vitest run tests/api/auth-callback.test.ts
```
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add apps/web/app/api/auth/callback/route.ts apps/web/tests/api/auth-callback.test.ts
git commit -m "fix(auth): derive origin from request in Auth0 callback"
```

### Task 1.4: Add ownership check to `POST /assessments`

**Files:**
- Modify: `apps/api/src/api/v1/endpoints/assessments.py` (around line 102-135)
- Modify: `apps/api/src/services/assessment_service.py` (signature of `start_assessment`)
- Test: `apps/api/tests/api/test_assessments_authz.py` (create)

Context: The POST handler currently calls `service.start_assessment(request.student_id)` without verifying the authenticated user owns the student. IDOR: any parent can start any other parent's student's assessment by guessing the student_id.

- [ ] **Step 1: Write the failing test**

Create `apps/api/tests/api/test_assessments_authz.py`:

```python
import pytest
import pytest_asyncio
from uuid import uuid4
from src.models.models import User, Student

@pytest.mark.asyncio
async def test_start_assessment_forbidden_for_non_owning_parent(
    client, async_db_session
):
    """A parent cannot start an assessment for another parent's student."""
    # Parent A owns Student X
    parent_a = User(
        id="parent-a", auth0_id="auth0|a", role="parent", is_active=True,
        first_name="A", last_name="Parent",
    )
    parent_a.set_email("a@example.com")
    student_x = Student(
        id=str(uuid4()), parent_id="parent-a", grade_level=4,
        display_name="Child X", is_active=True,
    )
    async_db_session.add_all([parent_a, student_x])
    await async_db_session.flush()

    # Parent B is the authenticated caller (default `client` JWT sub = "test-user-id")
    response = await client.post(
        "/api/v1/assessments",
        json={"student_id": student_x.id, "assessment_type": "diagnostic"},
    )

    assert response.status_code == 403, response.text
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
cd apps/api
python -m pytest tests/api/test_assessments_authz.py -v
```
Expected: FAIL (likely 200/201 or 500, not 403).

- [ ] **Step 3: Add ownership check to the endpoint**

Open `apps/api/src/api/v1/endpoints/assessments.py`. In the `POST /assessments` handler (currently around line 102), immediately after `verify_jwt` resolves and before calling the service, add:

```python
from sqlalchemy import select
from src.models.models import Student

result = await db.execute(select(Student).where(Student.id == request.student_id))
student = result.scalar_one_or_none()
if student is None:
    raise HTTPException(status_code=404, detail="Student not found")

user_id = user_payload.get("sub") or user_payload.get("auth0_id")
if student.parent_id != user_id:
    raise HTTPException(status_code=403, detail="Not authorized for this student")
```

- [ ] **Step 4: Run the test to verify it passes**

```bash
python -m pytest tests/api/test_assessments_authz.py -v
```
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add apps/api/src/api/v1/endpoints/assessments.py apps/api/tests/api/test_assessments_authz.py
git commit -m "security(assessments): add parent-ownership check to POST /assessments

Prior code accepted any authenticated parent's request to start an
assessment for any student_id. Added IDOR guard: reject 403 when the
JWT sub does not match student.parent_id."
```

### Task 1.5: Add ownership check to `GET /assessments/{id}/next-question`

**Files:**
- Modify: `apps/api/src/api/v1/endpoints/assessments.py` (around line 138)
- Test: same file as Task 1.4

- [ ] **Step 1: Add failing test to `test_assessments_authz.py`**

Append:

```python
@pytest.mark.asyncio
async def test_next_question_forbidden_for_non_owning_parent(
    client, async_db_session
):
    from src.models.models import Assessment, AssessmentType, AssessmentStatus

    parent_a = User(
        id="parent-a", auth0_id="auth0|a", role="parent", is_active=True,
        first_name="A", last_name="Parent",
    )
    parent_a.set_email("a@example.com")
    student_x = Student(
        id=str(uuid4()), parent_id="parent-a", grade_level=4,
        display_name="Child X", is_active=True,
    )
    assessment = Assessment(
        id=str(uuid4()), student_id=student_x.id,
        assessment_type=AssessmentType.DIAGNOSTIC.value,
        status=AssessmentStatus.IN_PROGRESS.value,
    )
    async_db_session.add_all([parent_a, student_x, assessment])
    await async_db_session.flush()

    response = await client.get(f"/api/v1/assessments/{assessment.id}/next-question")
    assert response.status_code == 403
```

- [ ] **Step 2: Run the test — fails**

```bash
python -m pytest tests/api/test_assessments_authz.py::test_next_question_forbidden_for_non_owning_parent -v
```

- [ ] **Step 3: Add ownership check**

In the handler for `GET /assessments/{assessment_id}/next-question`, after loading the `Assessment`, add:

```python
student_result = await db.execute(
    select(Student).where(Student.id == assessment.student_id)
)
student = student_result.scalar_one_or_none()
user_id = user_payload.get("sub") or user_payload.get("auth0_id")
if student is None or student.parent_id != user_id:
    raise HTTPException(status_code=403, detail="Not authorized for this assessment")
```

- [ ] **Step 4: Run the test — passes**

- [ ] **Step 5: Commit**

```bash
git commit -am "security(assessments): add ownership guard to next-question endpoint"
```

### Task 1.6: Add ownership check to `POST /sessions/{id}/answer`

**Files:**
- Modify: `apps/api/src/api/v1/endpoints/learning_plans.py` (the session-answer handler ~line 553)
- Test: `apps/api/tests/api/test_practice_session_authz.py` (create)

Note: This endpoint is currently also broken (Task 2.1). For this task, add the ownership check stub. Task 2.1 will rewrite the rest of the body.

- [ ] **Step 1: Write the failing test**

`apps/api/tests/api/test_practice_session_authz.py`:

```python
import pytest
from uuid import uuid4
from src.models.models import (
    User, Student, LearningPlan, PlanModule, PlanLesson, PracticeSession
)

@pytest.mark.asyncio
async def test_session_answer_forbidden_for_non_owner(client, async_db_session):
    parent_a = User(
        id="parent-a", auth0_id="auth0|a", role="parent", is_active=True,
        first_name="A", last_name="Parent",
    )
    parent_a.set_email("a@example.com")
    student_x = Student(
        id=str(uuid4()), parent_id="parent-a", grade_level=4,
        display_name="Child X", is_active=True,
    )
    plan = LearningPlan(id=str(uuid4()), student_id=student_x.id, track="on_track", status="active")
    module = PlanModule(id=str(uuid4()), plan_id=plan.id, standard_id="4.NBT.A.1", sequence_order=1)
    lesson = PlanLesson(id=str(uuid4()), module_id=module.id, sequence_order=1)
    session = PracticeSession(
        id=str(uuid4()), lesson_id=lesson.id, student_id=student_x.id,
        standard_code="4.NBT.A.1", question_count=5,
    )
    async_db_session.add_all([parent_a, student_x, plan, module, lesson, session])
    await async_db_session.flush()

    response = await client.post(
        f"/api/v1/sessions/{session.id}/answer",
        json={"answer": "4", "time_spent_ms": 1000},
    )
    assert response.status_code == 403
```

- [ ] **Step 2: Run — fails**

- [ ] **Step 3: Add ownership check**

This ties into the endpoint rewrite in Task 2.1. For now, replace the entire handler body's ownership traversal (currently using nonexistent `Lesson`/`Module`) with the correct walk using `PlanLesson` → `PlanModule` → `LearningPlan` → `Student`:

```python
# after loading session
lesson = (await db.execute(
    select(PlanLesson).where(PlanLesson.id == session.lesson_id)
)).scalar_one_or_none()
if lesson is None:
    raise HTTPException(404, "Lesson not found")

module = (await db.execute(
    select(PlanModule).where(PlanModule.id == lesson.module_id)
)).scalar_one_or_none()
if module is None:
    raise HTTPException(404, "Module not found")

plan = (await db.execute(
    select(LearningPlan).where(LearningPlan.id == module.plan_id)
)).scalar_one_or_none()
if plan is None:
    raise HTTPException(404, "Plan not found")

student = (await db.execute(
    select(Student).where(Student.id == plan.student_id)
)).scalar_one_or_none()
user_id = user_payload.get("sub") or user_payload.get("auth0_id")
if student is None or student.parent_id != user_id:
    raise HTTPException(403, "Not authorized for this session")
```

- [ ] **Step 4: Run — passes**

- [ ] **Step 5: Commit**

```bash
git commit -am "security(practice): add ownership guard to session-answer endpoint

Also replace references to nonexistent Lesson/Module classes with
PlanLesson/PlanModule. The rest of the handler body is rewritten in
Task 2.1."
```

### Task 1.7: Replace default encryption passphrase with fail-fast config

**Files:**
- Modify: `apps/api/src/core/config.py` (around line 72)
- Test: `apps/api/tests/core/test_config_secrets.py` (create)

Context: Default value `"your-secure-passphrase-32-chars-min-required"` would silently be used in production if the env var is not set, encrypting all student PII with a known-weak key.

- [ ] **Step 1: Write the failing test**

```python
import pytest
from pydantic import ValidationError

def test_config_rejects_default_encryption_passphrase(monkeypatch):
    monkeypatch.delenv("ENCRYPTION_KEY_PASSPHRASE", raising=False)
    from src.core.config import Settings
    with pytest.raises(ValidationError):
        Settings()

def test_config_accepts_strong_passphrase(monkeypatch):
    monkeypatch.setenv(
        "ENCRYPTION_KEY_PASSPHRASE",
        "x" * 32
    )
    from src.core.config import Settings
    s = Settings()
    assert len(s.ENCRYPTION_KEY_PASSPHRASE) >= 32
```

- [ ] **Step 2: Run — fails**

- [ ] **Step 3: Modify config**

In `apps/api/src/core/config.py`, change the field to be required with no default:

```python
ENCRYPTION_KEY_PASSPHRASE: str = Field(
    ...,  # required, no default
    min_length=32,
    description="Key-derivation passphrase for PII encryption. MUST come from a secrets manager; no default permitted.",
)
```

- [ ] **Step 4: Update `conftest.py` to supply a test passphrase**

In `apps/api/tests/conftest.py`, near the other `os.environ[...]` lines at module top, add:

```python
os.environ.setdefault("ENCRYPTION_KEY_PASSPHRASE", "test-passphrase-32-characters-long-ok")
```

- [ ] **Step 5: Update `.env.example` to document the requirement**

Add a comment next to the passphrase entry: `# REQUIRED. Must be ≥32 chars. No default in code — app will fail to start without it.`

- [ ] **Step 6: Run — passes**

- [ ] **Step 7: Commit**

```bash
git commit -am "security(config): require ENCRYPTION_KEY_PASSPHRASE with no default

Removes the hardcoded default that would silently encrypt PII with a
known value in production. Settings() now raises ValidationError if
the env var is missing or shorter than 32 chars."
```

---

## Phase 2 — HIGH: Correctness & production-readiness

### Task 2.1: Fix the session-answer endpoint body (uses nonexistent fields)

**Files:**
- Modify: `apps/api/src/api/v1/endpoints/learning_plans.py:553-709`
- Test: `apps/api/tests/api/test_practice_session_flow.py` (create)

Context: After Task 1.6 the ownership traversal is correct, but the endpoint still references `session.question_ids` and `session.current_question_index` (neither exists on the `PracticeSession` model) and creates a `PracticeSessionQuestion` with the wrong column names (`practice_session_id`, `selected_answer` instead of `session_id`, `student_answer`).

- [ ] **Step 1: Read the real models**

```bash
grep -n "class PracticeSession" apps/api/src/models/models.py
grep -n "class PracticeSessionQuestion" apps/api/src/models/models.py
```
Note the actual column names: `session_id`, `student_answer`, `sequence`, `answered_at`, `time_spent_ms`.

- [ ] **Step 2: Write the failing test**

`apps/api/tests/api/test_practice_session_flow.py`:

```python
import pytest
from uuid import uuid4
from datetime import datetime
from src.models.models import (
    User, Student, LearningPlan, PlanModule, PlanLesson,
    PracticeSession, PracticeSessionQuestion, GeneratedQuestion,
)

@pytest.mark.asyncio
async def test_submit_correct_answer_updates_row_and_returns_progress(
    client, async_db_session
):
    # Auth: default `client` fixture uses sub="test-user-id"
    parent = User(
        id="test-user-id", auth0_id="auth0|test", role="parent", is_active=True,
        first_name="T", last_name="U",
    )
    parent.set_email("t@u.com")
    student = Student(
        id=str(uuid4()), parent_id="test-user-id", grade_level=4,
        display_name="S", is_active=True,
    )
    plan = LearningPlan(id=str(uuid4()), student_id=student.id, track="on_track", status="active")
    module = PlanModule(id=str(uuid4()), plan_id=plan.id, standard_id="4.NBT.A.1", sequence_order=1)
    lesson = PlanLesson(id=str(uuid4()), module_id=module.id, sequence_order=1)
    session = PracticeSession(
        id=str(uuid4()), lesson_id=lesson.id, student_id=student.id,
        standard_code="4.NBT.A.1", question_count=2,
    )
    q1 = GeneratedQuestion(
        id=str(uuid4()), standard_id="4.NBT.A.1",
        question_text="2+2?", correct_answer="4", difficulty=1,
    )
    psq1 = PracticeSessionQuestion(
        id=str(uuid4()), session_id=session.id, question_id=q1.id,
        sequence=0, difficulty=1,
    )
    async_db_session.add_all([parent, student, plan, module, lesson, session, q1, psq1])
    await async_db_session.flush()

    response = await client.post(
        f"/api/v1/sessions/{session.id}/answer",
        json={"answer": "4", "time_spent_ms": 1500},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["correct"] is True
    assert data["progress"]["current_question"] == 1
    assert data["progress"]["total_questions"] == 2
```

- [ ] **Step 3: Run — fails**

- [ ] **Step 4: Rewrite the handler body**

Replace the "find next question" block (currently `session.question_ids[session.current_question_index]`) with a query for the next unanswered `PracticeSessionQuestion`:

```python
next_psq = (await db.execute(
    select(PracticeSessionQuestion)
    .where(
        PracticeSessionQuestion.session_id == session_id,
        PracticeSessionQuestion.student_answer.is_(None),
    )
    .order_by(PracticeSessionQuestion.sequence.asc())
    .limit(1)
)).scalar_one_or_none()

if next_psq is None:
    raise HTTPException(409, "Session has no unanswered questions remaining")

question = (await db.execute(
    select(GeneratedQuestion).where(GeneratedQuestion.id == next_psq.question_id)
)).scalar_one_or_none()
if question is None:
    raise HTTPException(404, "Question not found")

is_correct = request.answer.strip().lower() == question.correct_answer.strip().lower()

next_psq.student_answer = request.answer
next_psq.is_correct = is_correct
next_psq.time_spent_ms = request.time_spent_ms
next_psq.answered_at = datetime.utcnow()
# BKT update block (keep existing logic — it already uses correct models)
```

And the return block:

```python
answered_count = (await db.execute(
    select(func.count()).select_from(PracticeSessionQuestion)
    .where(
        PracticeSessionQuestion.session_id == session_id,
        PracticeSessionQuestion.student_answer.is_not(None),
    )
)).scalar_one()

return SessionAnswerResponse(
    correct=is_correct,
    correct_answer=question.correct_answer,
    explanation=question.explanation,
    progress={
        "current_question": answered_count,
        "total_questions": session.question_count,
    },
)
```

Also delete the `from src.models.models import Lesson` and `from src.models.models import Module` lines (they don't exist). Add `PlanLesson`, `PlanModule` imports if not already present.

- [ ] **Step 5: Run — passes**

- [ ] **Step 6: Commit**

```bash
git commit -am "fix(practice): rewrite session-answer endpoint against real schema

The handler referenced session.question_ids and current_question_index,
neither of which exist on PracticeSession. It also imported Lesson and
Module classes that do not exist (the real names are PlanLesson and
PlanModule). Rewrote to:
 - Walk ownership via PlanLesson → PlanModule → LearningPlan → Student
 - Select next unanswered PracticeSessionQuestion by sequence
 - Update that row in place with student_answer, is_correct, time_spent_ms
 - Compute progress as answered_count / question_count"
```

### Task 2.2: Fix Student schema/model divergence

**Files:**
- Read: `apps/api/alembic/versions/001_initial_schema.py` (current first_name/last_name schema)
- Read: `apps/api/src/models/models.py` (Student model uses display_name)
- Create: `apps/api/alembic/versions/004_student_display_name.py`

Context: Migration `001` creates `students.first_name` and `students.last_name` columns. ORM model has `display_name` only. In production you'd get `UndefinedColumn` the first time anything queries Student.display_name.

- [ ] **Step 1: Confirm the divergence**

```bash
grep -n "display_name\|first_name\|last_name" apps/api/alembic/versions/001_initial_schema.py apps/api/src/models/models.py
```

- [ ] **Step 2: Decide direction**

The COPPA-minimization argument favors `display_name` (less PII). Confirm with the user before migrating. Record decision in the task commit.

- [ ] **Step 3: Write the migration**

Create `apps/api/alembic/versions/004_student_display_name.py`:

```python
"""Drop students.first_name/last_name; add display_name

Revision ID: 004
Revises: 003
Create Date: 2026-04-20
"""
from alembic import op
import sqlalchemy as sa

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade():
    # 1. Add display_name nullable
    op.add_column("students", sa.Column("display_name", sa.String(50), nullable=True))
    # 2. Backfill from first_name (best-effort, COPPA-minimal)
    op.execute("UPDATE students SET display_name = COALESCE(first_name, 'Student')")
    # 3. Make non-nullable
    op.alter_column("students", "display_name", nullable=False)
    # 4. Drop plaintext PII columns
    op.drop_column("students", "first_name")
    op.drop_column("students", "last_name")


def downgrade():
    op.add_column("students", sa.Column("first_name", sa.String(100), nullable=True))
    op.add_column("students", sa.Column("last_name", sa.String(100), nullable=True))
    op.drop_column("students", "display_name")
```

- [ ] **Step 4: Run migration locally against testcontainers**

```bash
cd apps/api
alembic upgrade head
```
Expected: migration applies cleanly.

- [ ] **Step 5: Run the full test suite — nothing regresses**

```bash
python -m pytest tests/ -x --tb=short
```

- [ ] **Step 6: Commit**

```bash
git add apps/api/alembic/versions/004_student_display_name.py
git commit -m "migration: consolidate students.first_name/last_name → display_name

COPPA minimization: we only need a display name, not legal name parts.
Backfills display_name from first_name where present, drops the legacy
PII columns."
```

### Task 2.3: Align frontend token storage with httpOnly cookie

**Files:**
- Modify: `apps/web/lib/api-client.ts`
- Test: `apps/web/tests/lib/api-client.test.ts`

Context: Callback writes token to httpOnly cookie; client reads from `localStorage`. Result: every API request is unauthenticated. Fix by switching API client to `credentials: "include"` and removing the `getHeaders()` Bearer injection (or proxy through a server action).

- [ ] **Step 1: Write the failing test**

```ts
import { describe, it, expect, vi, beforeEach } from "vitest";
import { apiClient } from "@/lib/api-client";

describe("apiClient auth", () => {
  beforeEach(() => {
    global.fetch = vi.fn(async () =>
      new Response(JSON.stringify({ ok: true }), { status: 200 })
    ) as unknown as typeof fetch;
  });

  it("sends credentials so httpOnly auth cookie is included", async () => {
    await apiClient.request("/health");
    const call = (global.fetch as unknown as { mock: { calls: [unknown, RequestInit][] } }).mock.calls[0];
    expect(call[1].credentials).toBe("include");
  });

  it("does NOT read token from localStorage", async () => {
    const spy = vi.spyOn(Storage.prototype, "getItem");
    await apiClient.request("/health");
    expect(spy).not.toHaveBeenCalledWith("auth_token");
  });
});
```

- [ ] **Step 2: Run — fails**

- [ ] **Step 3: Update the client**

In `apps/web/lib/api-client.ts`, replace:

```ts
private getHeaders() {
  const token = typeof window !== "undefined"
    ? localStorage.getItem("auth_token") : null;
  return token ? { Authorization: `Bearer ${token}` } : {};
}
```

with an empty-by-default header set and add `credentials: "include"` to every `fetch` call inside `request()`:

```ts
async request(path: string, init: RequestInit = {}) {
  const res = await fetch(`${this.baseUrl}${path}`, {
    ...init,
    credentials: "include",
    headers: { "Content-Type": "application/json", ...init.headers },
  });
  if (res.status === 401) {
    if (typeof window !== "undefined") window.location.assign("/login");
    throw new Error("Unauthenticated");
  }
  if (!res.ok) throw new Error(`API ${res.status}: ${await res.text()}`);
  return res.json();
}
```

Also update the backend: in `apps/api/src/main.py`, ensure CORS middleware has `allow_credentials=True` and tight `allow_origins` (no `"*"` alongside credentials).

- [ ] **Step 4: Run — passes**

- [ ] **Step 5: Smoke test end-to-end in dev**

```bash
pnpm docker:up
pnpm dev
```

Open `http://localhost:3000`, click Login, complete Auth0 flow, open dev tools → Application → Cookies. Confirm the auth cookie is present. Navigate to parent dashboard; it should load without 401s.

- [ ] **Step 6: Commit**

```bash
git commit -am "fix(web): use httpOnly cookie via credentials: include for API auth

The callback writes an httpOnly cookie; the client was reading
localStorage, so every authenticated request failed silently. Switch
to credentials:'include' and drop the Bearer header path. Also tightens
CORS to allow_credentials=True with an explicit origin list."
```

### Task 2.4: Add audit log table and wire sensitive actions

**Files:**
- Create: `apps/api/alembic/versions/005_audit_log.py`
- Create: `apps/api/src/services/audit_service.py`
- Modify: `apps/api/src/api/v1/endpoints/consent.py` (call audit on grant/revoke)
- Modify: `apps/api/src/api/v1/endpoints/students.py` (call audit on create)
- Modify: `apps/api/src/api/v1/endpoints/assessments.py` (call audit on start/complete)
- Test: `apps/api/tests/services/test_audit_service.py`

- [ ] **Step 1: Write migration**

```python
"""Add audit_log table
Revision ID: 005
Revises: 004
"""
from alembic import op
import sqlalchemy as sa

revision = "005"
down_revision = "004"

def upgrade():
    op.create_table(
        "audit_log",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("actor_user_id", sa.String, nullable=False, index=True),
        sa.Column("action", sa.String, nullable=False, index=True),
        sa.Column("resource_type", sa.String, nullable=False),
        sa.Column("resource_id", sa.String, nullable=False),
        sa.Column("ip_address", sa.String, nullable=True),
        sa.Column("user_agent", sa.Text, nullable=True),
        sa.Column("metadata_json", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), index=True),
    )

def downgrade():
    op.drop_table("audit_log")
```

- [ ] **Step 2: Add ORM model**

Append to `apps/api/src/models/models.py`:

```python
class AuditLog(Base):
    __tablename__ = "audit_log"
    id = Column(String, primary_key=True)
    actor_user_id = Column(String, nullable=False, index=True)
    action = Column(String, nullable=False, index=True)
    resource_type = Column(String, nullable=False)
    resource_id = Column(String, nullable=False)
    ip_address = Column(String, nullable=True)
    user_agent = Column(Text, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
```

- [ ] **Step 3: Write the failing service test**

```python
import pytest
from uuid import uuid4
from src.services.audit_service import AuditService
from src.models.models import AuditLog
from sqlalchemy import select

@pytest.mark.asyncio
async def test_audit_service_records_event(async_db_session):
    svc = AuditService(async_db_session)
    await svc.record(
        actor_user_id="u1", action="consent.granted",
        resource_type="consent", resource_id="c1",
        ip_address="10.0.0.1", user_agent="pytest",
    )
    await async_db_session.flush()
    rows = (await async_db_session.execute(select(AuditLog))).scalars().all()
    assert len(rows) == 1
    assert rows[0].action == "consent.granted"
    assert rows[0].ip_address == "10.0.0.1"
```

- [ ] **Step 4: Run — fails (no service yet)**

- [ ] **Step 5: Implement the service**

`apps/api/src/services/audit_service.py`:

```python
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.models import AuditLog

class AuditService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def record(
        self, *, actor_user_id: str, action: str,
        resource_type: str, resource_id: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
        metadata: dict | None = None,
    ) -> None:
        self.db.add(AuditLog(
            id=str(uuid4()),
            actor_user_id=actor_user_id, action=action,
            resource_type=resource_type, resource_id=resource_id,
            ip_address=ip_address, user_agent=user_agent,
            metadata_json=metadata,
        ))
```

- [ ] **Step 6: Run — passes**

- [ ] **Step 7: Wire into sensitive endpoints**

In each of `consent.py`, `students.py`, `assessments.py`:
- Accept `request: Request` as handler arg (if not already).
- After the action succeeds but before commit, call:

```python
await AuditService(db).record(
    actor_user_id=user_id, action="consent.granted",
    resource_type="consent", resource_id=consent_record.id,
    ip_address=request.client.host if request.client else None,
    user_agent=request.headers.get("user-agent"),
)
```

Action strings to use:
- `consent.initiated`, `consent.granted`, `consent.revoked`
- `student.created`, `student.updated`
- `assessment.started`, `assessment.completed`

- [ ] **Step 8: Add one end-to-end test that verifies the audit row appears**

```python
@pytest.mark.asyncio
async def test_consent_grant_writes_audit_row(client, async_db_session, ...):
    # ... call grant endpoint
    rows = (await async_db_session.execute(
        select(AuditLog).where(AuditLog.action == "consent.granted")
    )).scalars().all()
    assert len(rows) == 1
```

- [ ] **Step 9: Commit**

```bash
git add apps/api/alembic/versions/005_audit_log.py apps/api/src/models/models.py \
        apps/api/src/services/audit_service.py apps/api/src/api/v1/endpoints/consent.py \
        apps/api/src/api/v1/endpoints/students.py apps/api/src/api/v1/endpoints/assessments.py \
        apps/api/tests/services/test_audit_service.py
git commit -m "feat(audit): record consent + student + assessment lifecycle events

Adds audit_log table, AuditService, and instruments consent grant/revoke,
student creation, and assessment start/complete endpoints. Required for
COPPA audit-trail compliance."
```

### Task 2.5: Fix `alembic.ini` hardcoded SQLite URL

**Files:**
- Modify: `apps/api/alembic.ini`
- Modify: `apps/api/alembic/env.py`

Context: `alembic.ini:7` sets `sqlalchemy.url = sqlite:///./padi.db`. This ignores `DATABASE_URL` entirely; migrations against prod Postgres would silently write to a local SQLite file.

- [ ] **Step 1: Remove hardcoded URL from `alembic.ini`**

Change line 7 to:
```ini
sqlalchemy.url =
```
(empty — will be filled by `env.py`)

- [ ] **Step 2: Make `env.py` read from settings**

At the top of `apps/api/alembic/env.py`, add:

```python
import os
from src.core.config import get_settings

settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
```

- [ ] **Step 3: Test against real Postgres (docker)**

```bash
cd apps/api
pnpm docker:up
DATABASE_URL=postgresql+asyncpg://padi:padi_secret@localhost:5432/padi alembic upgrade head
```
Expected: applies all migrations against Postgres.

- [ ] **Step 4: Commit**

```bash
git commit -am "fix(alembic): read DATABASE_URL at runtime instead of hardcoded sqlite

alembic.ini pinned sqlite:///./padi.db, silently bypassing the configured
database in every environment. env.py now sources the URL from Settings."
```

---

## Phase 3 — MEDIUM: Test suite repair

This phase subsumes the prior plan at `/Users/aerobu/.claude/plans/look-at-stage2-test-issues-md-and-jazzy-pelican.md`.

### Task 3.1: Repair `conftest.py` fixture plumbing

**Files:**
- Modify: `apps/api/tests/conftest.py`

- [ ] **Step 1: Delete broken sync fixtures**

Remove:
- `engine(test_settings)` (lines ~60-76) — depends on undefined `test_settings`
- `test_engine(engine)` (lines ~79-86)
- `session(test_engine)` (lines ~89-99)
- Duplicate sync `test_parent` (lines ~340-356)
- Duplicate sync `test_student` (lines ~359-374)

- [ ] **Step 2: Rewrite `auth_headers`, `admin_auth_headers`, `different_user_headers`**

Each should install a `verify_jwt` override AND return the header dict:

```python
@pytest.fixture
def auth_headers():
    app.dependency_overrides[verify_jwt] = _override_verify_jwt({
        "sub": "test-parent-id", "email": "p@example.com",
        "email_verified": True, "role": "parent",
    })
    yield {"Authorization": "Bearer test-token"}
    app.dependency_overrides.pop(verify_jwt, None)

@pytest.fixture
def admin_auth_headers():
    app.dependency_overrides[verify_jwt] = _override_verify_jwt({
        "sub": "admin-user-id", "role": "admin",
    })
    yield {"Authorization": "Bearer admin-token"}
    app.dependency_overrides.pop(verify_jwt, None)

@pytest.fixture
def different_user_headers():
    app.dependency_overrides[verify_jwt] = _override_verify_jwt({
        "sub": "other-user-id", "role": "parent",
    })
    yield {"Authorization": "Bearer other-token"}
    app.dependency_overrides.pop(verify_jwt, None)
```

- [ ] **Step 3: Align `client` fixture sub with `test-parent-id`**

In the `client` fixture (line ~509), change the override payload `"sub"` from `"test-user-id"` to `"test-parent-id"` so it matches the `test_parent_for_student` fixture's parent id.

- [ ] **Step 4: Run the collect-only sanity check**

```bash
cd apps/api
python -m pytest tests/ --collect-only -q 2>&1 | tail -20
```
Expected: no collection errors about missing `test_settings`.

- [ ] **Step 5: Commit**

```bash
git commit -am "test(conftest): purge broken sync fixtures, make auth headers install JWT overrides

- Delete engine/test_engine/session (depended on undefined test_settings)
- Delete duplicate sync test_parent/test_student
- auth_headers/admin_auth_headers/different_user_headers now each install
  the verify_jwt override and yield the header dict, so tests that use
  them actually authenticate
- Align default client fixture sub with test_parent_for_student.id"
```

### Task 3.2: Fix `test_practice_sessions.py`

**Files:**
- Modify: `apps/api/tests/api/test_practice_sessions.py`

- [ ] **Step 1: Remove all `current_question_index=...` kwargs**

Lines 122, 229, 374, 495. These are the tests the endpoint fix in Task 2.1 already makes real.

- [ ] **Step 2: For each test that needs "current question" state, create `PracticeSessionQuestion` rows with `sequence=0..N-1`**

Pattern:
```python
psqs = [
    PracticeSessionQuestion(
        id=str(uuid4()), session_id=session.id,
        question_id=questions[i].id, sequence=i, difficulty=1,
    ) for i in range(len(questions))
]
async_db_session.add_all(psqs)
```

For the "all answered" test (line 495), populate every row with `student_answer`, `is_correct`, `answered_at`.

- [ ] **Step 3: Replace the custom `test_client` fixture with the shared async `client` fixture**

Delete lines 13-25 entirely. Update every test signature from `(self, test_client, ...)` to `(self, client, ...)` and every `test_client.post(...)` to `await client.post(...)`.

- [ ] **Step 4: Run the file**

```bash
python -m pytest tests/api/test_practice_sessions.py -v
```
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git commit -am "test(practice): align with real PracticeSession schema

- Drop current_question_index kwargs (no such column)
- Create PracticeSessionQuestion rows with sequence numbers
- Use shared async client fixture instead of local patch-based one"
```

### Task 3.3: Fix `test_learning_plans_endpoint.py`

**Files:**
- Modify: `apps/api/tests/api/test_learning_plans_endpoint.py`
- Maybe create: `apps/api/tests/api/fixtures/learning_plan_seed.py`

- [ ] **Step 1: Run the file to see current failures**

```bash
python -m pytest tests/api/test_learning_plans_endpoint.py -v --tb=short
```

- [ ] **Step 2: For tests that need a parent with id `"test-parent-id"`, use the existing `test_parent_for_student` fixture or rely on the updated `auth_headers` from Task 3.1**

No code change needed if fixtures now align — just remove any test-local setup that re-creates parents with different ids.

- [ ] **Step 3: For `test_generate_learning_plan_success`, seed at least one `Standard` row so the generator has something to build modules from**

Add a new fixture:

```python
@pytest_asyncio.fixture
async def seed_grade_4_standards(async_db_session):
    from src.models.models import Standard
    standards = [
        Standard(id="4.NBT.A.1", standard_code="4.NBT.A.1", grade_level=4,
                 domain="NBT", title="Place value", description="..."),
        Standard(id="4.NBT.B.5", standard_code="4.NBT.B.5", grade_level=4,
                 domain="NBT", title="Multi-digit mult", description="..."),
        Standard(id="4.OA.A.1", standard_code="4.OA.A.1", grade_level=4,
                 domain="OA", title="Multiplicative compare", description="..."),
    ]
    async_db_session.add_all(standards)
    await async_db_session.flush()
    return standards
```

Inject it into the success test.

- [ ] **Step 4: For `test_generate_learning_plan_no_assessment`, use a student fixture that does NOT depend on `test_assessment`**

Add:
```python
@pytest_asyncio.fixture
async def test_student_without_assessment(async_db_session, test_parent_for_student):
    from src.models.models import Student
    from uuid import uuid4
    s = Student(id=str(uuid4()), parent_id="test-parent-id",
                grade_level=4, display_name="S", is_active=True)
    async_db_session.add(s)
    await async_db_session.flush()
    return s
```

Use it in the no-assessment test.

- [ ] **Step 5: Run — all pass**

- [ ] **Step 6: Commit**

```bash
git commit -am "test(learning-plans): align fixtures with default parent id and seed standards"
```

### Task 3.4: Rewrite the four fake endpoint test files as real integration tests

**Files:**
- Rewrite: `apps/api/tests/api/test_assessments_endpoint.py`
- Rewrite: `apps/api/tests/api/test_consent_endpoint.py`
- Rewrite: `apps/api/tests/api/test_standards_endpoint.py`
- Rewrite: `apps/api/tests/api/test_students_endpoint.py`

Context: These currently only do raw SQL inserts and assertions. They're labeled "endpoint" tests but never call an endpoint. Rewrite each to use the shared `client` fixture and exercise real HTTP.

- [ ] **Step 1: `test_consent_endpoint.py` — smallest, start here**

Replace the file with tests for each endpoint in `consent.py`:

```python
import pytest
import pytest_asyncio
from uuid import uuid4

@pytest.mark.asyncio
class TestConsentInitiate:
    async def test_initiate_returns_201_with_token(self, client, test_parent_for_student):
        response = await client.post(
            "/api/v1/consent/initiate",
            json={
                "student_display_name": "Alex",
                "acknowledgements": ["a", "b", "c", "d"],
            },
        )
        assert response.status_code == 201
        assert "verification_token" in response.json()

    async def test_initiate_rejects_empty_acknowledgements(self, client, test_parent_for_student):
        response = await client.post(
            "/api/v1/consent/initiate",
            json={"student_display_name": "Alex", "acknowledgements": []},
        )
        assert response.status_code == 422

@pytest.mark.asyncio
class TestConsentConfirm:
    async def test_confirm_with_valid_token(self, client, test_parent_for_student):
        init = await client.post(
            "/api/v1/consent/initiate",
            json={"student_display_name": "Alex", "acknowledgements": ["a","b","c","d"]},
        )
        token = init.json()["verification_token"]
        response = await client.post(f"/api/v1/consent/confirm?token={token}")
        assert response.status_code == 200

    async def test_confirm_rejects_invalid_token(self, client):
        response = await client.post("/api/v1/consent/confirm?token=bogus")
        assert response.status_code == 400

@pytest.mark.asyncio
class TestConsentGet:
    async def test_get_returns_active_consent(self, client, test_parent_for_student):
        init = await client.post(
            "/api/v1/consent/initiate",
            json={"student_display_name": "Alex", "acknowledgements": ["a","b","c","d"]},
        )
        token = init.json()["verification_token"]
        await client.post(f"/api/v1/consent/confirm?token={token}")

        response = await client.get("/api/v1/consent")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ("granted", "active")
        assert data["student_display_name"] == "Alex"
```

If the exact response-field names differ, adjust by reading `consent.py`'s Pydantic response schema — do not guess.

- [ ] **Step 2: `test_standards_endpoint.py` — second smallest**

```python
import pytest

@pytest.mark.asyncio
async def test_list_standards_by_grade(client, seed_grade_4_standards):
    response = await client.get("/api/v1/standards?grade_level=4")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 3
    assert all(s["grade_level"] == 4 for s in data)

@pytest.mark.asyncio
async def test_get_standard_by_code(client, seed_grade_4_standards):
    response = await client.get("/api/v1/standards/4.NBT.A.1")
    assert response.status_code == 200
    assert response.json()["standard_code"] == "4.NBT.A.1"

@pytest.mark.asyncio
async def test_get_nonexistent_standard_404(client):
    response = await client.get("/api/v1/standards/9.ZZ.Z.9")
    assert response.status_code == 404
```

- [ ] **Step 3: `test_students_endpoint.py`**

Cover: POST /students (requires consent gate), GET /students/{id}, PUT /students/{id}, GET /students (list for parent). Include one test that verifies POST is blocked without an active consent record (403).

- [ ] **Step 4: `test_assessments_endpoint.py`**

Cover: POST /assessments (with ownership — reuse Task 1.4 test patterns), GET /assessments/{id}, GET /assessments/{id}/next-question, POST /assessments/{id}/responses, PUT /assessments/{id}/complete.

- [ ] **Step 5: Run each file after writing**

```bash
python -m pytest tests/api/test_consent_endpoint.py -v
python -m pytest tests/api/test_standards_endpoint.py -v
python -m pytest tests/api/test_students_endpoint.py -v
python -m pytest tests/api/test_assessments_endpoint.py -v
```

- [ ] **Step 6: Commit after each file passes**

```bash
git commit -am "test(consent): rewrite as real API integration tests"
# etc per file
```

### Task 3.5: Replace blanket `except Exception` in endpoints

**Files:**
- Modify: every file in `apps/api/src/api/v1/endpoints/` with `except Exception as e: raise HTTPException(500, detail=str(e))`

- [ ] **Step 1: Find offenders**

```bash
grep -rn "except Exception" apps/api/src/api/v1/endpoints/
```

- [ ] **Step 2: For each, narrow to specific types**

Pattern:
```python
# Bad:
except Exception as e:
    logger.error(f"Error: {e}")
    raise HTTPException(500, detail=str(e))

# Good:
except HTTPException:
    raise
except ValueError as e:
    raise HTTPException(400, detail=str(e))
except IntegrityError as e:
    logger.exception("DB integrity error")
    raise HTTPException(409, detail="Conflict")
# (no catch-all — unexpected errors bubble up; FastAPI returns a 500 without leaking str(e))
```

- [ ] **Step 3: Run the suite — nothing regresses**

```bash
python -m pytest tests/ -x --tb=line
```

- [ ] **Step 4: Commit**

```bash
git commit -am "fix(api): narrow exception handlers, stop leaking str(e) in 500 bodies"
```

---

## Phase 4 — LOW: Cleanup & ops hygiene

### Task 4.1: Archive AI-generated markdown cruft

**Files:**
- Create: `docs/archive/ai-planning/` (directory)
- Move: ~30 top-level `.md` files

- [ ] **Step 1: List candidates**

```bash
ls /Users/aerobu/claude_code_projects/padi_ai/*.md
```

Cruft to archive (AI implementation logs + redundant summaries):
- `IMPLEMENTATION-SUMMARY.md`
- `P3-IMPLEMENTATION-LOG.md`
- `PARENT-DASHBOARD-422-FIX-FINAL-REPORT.md`
- `PARENT-DASHBOARD-422-FIX-IMPLEMENTATION-GUIDE.md`
- `PARENT-DASHBOARD-422-FIX-IMPLEMENTATION-REPORT.md`
- `STAGE1-FIX-GUIDE.md`
- `STAGE1-FIXES-SUMMARY.md`
- `STAGE1-VERIFICATION-COMPLETE.md`
- `STAGE1_COMPLETION_SUMMARY.md`
- `STAGE1_P0_TESTS_IMPLEMENTED.md`
- `STAGE1_SUMMARY.md`
- `STAGE1_TESTING_COMPLETION_SUMMARY.md`
- `STAGE1_TESTING_SUMMARY.md`
- `STAGE1_TESTING_WRAP_UP.md`
- `STAGE2-HANDOFF-GUIDE.md`
- `STAGE2-P3-IMPLEMENTATION-SUMMARY.md`
- `STAGE2-TEST-ISSUES.md`
- `FINAL_TESTING_IMPLEMENTATION_SUMMARY.md`

Keep at root:
- `README.md`, `CONTRIBUTING.md`, `CLAUDE.md`

Move to `docs/specs/` (don't archive):
- `ENG-*.md`, `00-master-index.md` through `17-*.md`, `adaptive-math-app-viability.md`

- [ ] **Step 2: Move files**

```bash
cd /Users/aerobu/claude_code_projects/padi_ai
mkdir -p docs/archive/ai-planning docs/specs
git mv IMPLEMENTATION-SUMMARY.md P3-IMPLEMENTATION-LOG.md \
       PARENT-DASHBOARD-422-*.md STAGE1-*.md STAGE1_*.md STAGE2-*.md \
       FINAL_TESTING_IMPLEMENTATION_SUMMARY.md \
       docs/archive/ai-planning/
git mv ENG-*.md 0*-*.md 1*-*.md adaptive-math-app-viability.md docs/specs/
```

- [ ] **Step 3: Commit**

```bash
git commit -m "docs: archive ~18 AI-generated implementation logs, move specs to docs/specs/

Top level was cluttered with near-duplicate summaries and fix reports.
Moved specs to docs/specs/, implementation logs to docs/archive/ai-planning/."
```

### Task 4.2: Add rate limiting middleware

**Files:**
- Modify: `apps/api/pyproject.toml` (add `slowapi>=0.1.9`)
- Modify: `apps/api/src/main.py`

- [ ] **Step 1: Add dep**

```bash
cd apps/api
# add slowapi to pyproject.toml dependencies, then
pip install slowapi
```

- [ ] **Step 2: Wire middleware**

In `apps/api/src/main.py`:

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
```

- [ ] **Step 3: Apply decorator to sensitive endpoints**

On `POST /assessments`, `POST /consent/initiate`, `POST /auth/register`:
```python
@limiter.limit("10/minute")
```

- [ ] **Step 4: Add a test**

```python
@pytest.mark.asyncio
async def test_rate_limit_on_assessments(client, test_parent_for_student, test_student):
    for _ in range(10):
        await client.post("/api/v1/assessments", json={"student_id": test_student.id})
    response = await client.post("/api/v1/assessments", json={"student_id": test_student.id})
    assert response.status_code == 429
```

- [ ] **Step 5: Run — passes**

- [ ] **Step 6: Commit**

```bash
git commit -am "feat(api): add slowapi rate limiting on sensitive POST endpoints"
```

### Task 4.3: Add security headers middleware

**Files:**
- Modify: `apps/api/src/main.py`

- [ ] **Step 1: Add middleware**

```python
@app.middleware("http")
async def security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    if not request.url.hostname in ("localhost", "127.0.0.1"):
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response
```

- [ ] **Step 2: Test**

```python
@pytest.mark.asyncio
async def test_security_headers_present(client):
    response = await client.get("/api/v1/health")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
```

- [ ] **Step 3: Commit**

```bash
git commit -am "feat(api): add standard security headers (nosniff, deny-frame, HSTS, referrer)"
```

### Task 4.4: Replace manual OAuth with `@auth0/nextjs-auth0`

**Files:**
- Delete: `apps/web/app/api/auth/callback/route.ts`, `apps/web/app/api/auth/login/route.ts`
- Create: `apps/web/app/api/auth/[auth0]/route.ts`
- Modify: `apps/web/lib/auth.ts`, middleware, etc.

Follow the official `@auth0/nextjs-auth0` v3 App Router integration docs. This supersedes the Task 1.3 fix and the Task 2.3 cookie work (the SDK handles both correctly).

- [ ] **Step 1: Install and configure**

Already in `package.json`. Add required env vars per SDK docs.

- [ ] **Step 2: Create catch-all route**

```ts
import { handleAuth } from "@auth0/nextjs-auth0";
export const GET = handleAuth();
```

- [ ] **Step 3: Wrap layouts with `UserProvider`**, etc.

- [ ] **Step 4: Delete the hand-rolled routes**

- [ ] **Step 5: Run E2E**

Full auth flow: sign up → Auth0 → callback → parent dashboard.

- [ ] **Step 6: Commit**

```bash
git commit -m "refactor(auth): replace manual OAuth flow with @auth0/nextjs-auth0 SDK"
```

### Task 4.5: Add observability hooks (Sentry backend + frontend)

**Files:**
- Modify: `apps/api/pyproject.toml` (add `sentry-sdk`)
- Modify: `apps/api/src/main.py`
- Modify: `apps/web/package.json` (add `@sentry/nextjs`)
- Create: `apps/web/sentry.client.config.ts`, `sentry.server.config.ts`

Gate behind `SENTRY_DSN` env var so dev/test still run silently.

- [ ] **Step 1: Backend init**

```python
if settings.SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        integrations=[FastApiIntegration()],
        traces_sample_rate=0.1,
        environment=settings.ENVIRONMENT,
    )
```

- [ ] **Step 2: Frontend init per Sentry Next.js guide**

- [ ] **Step 3: Commit**

```bash
git commit -am "feat(observability): wire Sentry on api + web behind SENTRY_DSN env var"
```

### Task 4.6: Delete `apps/api/Dockerfile` Poetry mismatch or add `poetry.lock`

**Files:**
- Either modify `apps/api/Dockerfile` to use pip+pyproject, or run `poetry lock` and commit.

Pick the simpler option (pip+pyproject, since that's what CI uses):

- [ ] **Step 1: Rewrite Dockerfile**

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e .
COPY src/ src/
COPY alembic/ alembic/
COPY alembic.ini .
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s CMD curl -f http://localhost:8000/health || exit 1
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 2: Build locally**

```bash
cd apps/api
docker build -t padi-api:dev .
```

- [ ] **Step 3: Commit**

```bash
git commit -am "build(api): align Dockerfile with pip+pyproject (drop Poetry mismatch)"
```

---

## Final verification

After every phase, and once more at the end:

- [ ] **Backend full suite**
  ```bash
  cd apps/api && python -m pytest tests/ -v --tb=short
  ```
  Target: 0 errors, 0 failures.

- [ ] **Backend type check**
  ```bash
  mypy src --ignore-missing-imports
  ```

- [ ] **Backend lint**
  ```bash
  ruff check src/
  black src/ --check
  ```

- [ ] **Frontend unit + integration**
  ```bash
  cd apps/web && pnpm test
  ```

- [ ] **Frontend type check**
  ```bash
  pnpm type-check
  ```

- [ ] **Frontend E2E (pick one critical flow)**
  ```bash
  pnpm playwright test tests/e2e/consent-flow.spec.ts
  ```

- [ ] **End-to-end smoke manually in browser**
  1. `pnpm docker:up && pnpm dev`
  2. Sign up as a parent via Auth0
  3. Grant consent
  4. Create a student
  5. Start a diagnostic; answer 2-3 questions
  6. Reload mid-session; verify session resumes or shows a clear "resume" prompt
  7. Complete the diagnostic
  8. Generate a learning plan
  9. Open a practice session; submit an answer
  10. Visit the parent dashboard; verify student + plan appear

- [ ] **COPPA control-surface check**
  - `.env` is not tracked (`git ls-files apps/api/.env` empty)
  - Consent form uses parent/guardian attestation (no "over 13")
  - Audit log rows exist for the operations performed in the smoke test
  - JWT ownership checks reject cross-parent access (verify with curl + a forged-sub token — see `tests/api/test_assessments_authz.py`)
  - All `LLMPurpose.STUDENT_TUTORING` / `ASSESSMENT` routes resolve to `ollama/*` only (grep `llm_client.py`)

---

## Execution order & batching

Tasks within a phase are mostly independent. Recommended order:

**Phase 1 (parallelizable after 0.1):** 1.1 → 1.2, 1.3, 1.4, 1.5, 1.6, 1.7 can run as parallel subagents.

**Phase 2 (must be serialized — each touches shared files):** 2.1 → 2.2 → 2.3 → 2.4 → 2.5.

**Phase 3 (parallelizable after 3.1):** 3.1 first (others depend on it), then 3.2, 3.3, 3.4, 3.5 in parallel.

**Phase 4:** 4.1 can run anytime. 4.2-4.6 are independent.

Do not skip ahead. Phase 1 is non-negotiable before any deploy. Phase 2 before any user testing. Phase 3 before any claim of test coverage. Phase 4 before MMP.

---

## Dependencies on external decisions

These tasks require a user decision before execution:

- **Task 1.1 Step 4**: keep-history vs purge-history for `.env` leak.
- **Task 2.2 Step 2**: confirm `display_name` is the target (rather than keeping `first_name`/`last_name` and updating the model).
- **Task 4.4**: confirm switching to `@auth0/nextjs-auth0` is OK (it is the recommended path, but invalidates some work in 1.3 and 2.3 — if the user prefers to defer, skip 4.4).
