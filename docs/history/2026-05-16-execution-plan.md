# PADI.AI — Code Review Remediation & Stage 3 Execution Plan
**Date:** 2026-05-16
**Author:** Code review pass (Claude Code)
**Status:** Proposed — pending sign-off
**Supersedes claim of completion in:** `docs/history/2026-04-21-stage2-remediation-report.md`

---

## 0. Plan-at-a-Glance

| Phase | Theme | Duration (solo + agents) | Gate |
|---|---|---|---|
| **Phase 0** | Make CI honest | 2 days | Backend tests actually run in CI; mypy fails on bad attrs |
| **Phase 1** | P0 critical bug fixes (C-1…C-12) | 5 days | Diagnostic + practice happy-paths green end-to-end |
| **Phase 2** | True Stage 2 closure | 5 days | Question-gen pipeline produces validated rows; dashboards consume real API |
| **Phase 3** | Stage 3 scaffolding | 5 days | LangGraph orchestrator round-trips one fake question over WebSocket |
| **Phase 4** | Stage 3 agents & IRT | 4–6 weeks | All four agents operational, BKT real-time, frustration model live |
| **Phase 5** | Architecture hygiene | Interleaved | Singletons removed, types generated, observability live |

**Stop-the-line rule:** No Phase N+1 ticket is started until **all Phase N "exit criteria" tests are merged green**.

---

## 1. Working Conventions (apply to every ticket)

1. **Test first.** Every ticket begins with a failing test (red), then the fix (green), then refactor.
2. **Touch only one concern per PR.** If a ticket says "fix C-1", do not also reformat unrelated files.
3. **Repository pattern.** Database access stays in `apps/api/src/repositories/`. Services orchestrate; endpoints validate + delegate. No raw `select()` in routers (current code violates this — fix where touched).
4. **All LLM calls through `llm_client.get_llm_response()`** (or `LLMClient.acomplete(purpose=…)`). No direct `litellm.completion` / `litellm.acompletion` / `anthropic.*` / `openai.*` imports in services. Add a lint rule in Phase 0.
5. **No `datetime.utcnow()`.** Use `datetime.now(timezone.utc)` (utcnow is deprecated in Py 3.12).
6. **No PII in logs.** Log IDs only; never log emails, names, or answer text.
7. **Migration discipline.** Every schema-touching ticket ships an alembic revision + a forward+backward test in `tests/migrations/`.
8. **Definition of Done (DoD) for any ticket:**
   - Failing test exists at PR open
   - All tests pass locally and in CI
   - `ruff check`, `mypy --strict` (on touched files), `bandit -r apps/api/src` (touched files) pass
   - PR description references the ticket ID and lists acceptance criteria
   - No `# type: ignore`, `# noqa`, `# TODO` introduced without a tracked follow-up issue
   - `ACTIVE_CONTEXT.md` updated if phase advances

---

## 2. Phase 0 — Make CI Honest (2 days)

**Why first:** Every other phase's "tests pass" claim is unverifiable until CI installs the real dependencies and enforces type/lint gates.

### P0-T01 — Pin and install real backend deps in CI
**File:** `.github/workflows/ci.yml`, `apps/api/pyproject.toml` (create), `apps/api/requirements.txt`, `apps/api/requirements-dev.txt`
**Steps:**
1. Migrate `apps/api` to a PEP-621 `pyproject.toml` with two extras: `dev` and `test`.
2. Pin `fastapi`, `pydantic>=2.6`, `pydantic-settings`, `sqlalchemy[asyncio]>=2.0`, `asyncpg`, `alembic`, `cryptography`, `pyjwt[crypto]`, `slowapi`, `redis>=5`, `litellm`, `networkx`, `sentry-sdk[fastapi]`, `textstat`, `sentence-transformers`, `pgvector`, `httpx`, `python-multipart`.
3. Dev extras: `pytest`, `pytest-asyncio`, `pytest-cov`, `testcontainers[postgresql]`, `ruff`, `mypy`, `bandit`, `detect-secrets`, `safety`.
4. CI install step: `pip install -e ".[dev]"` (replace current `pip install pytest pytest-asyncio`).
5. CI test step: `pytest -q --strict-markers --strict-config --cov=src --cov-fail-under=70`.

**Acceptance criteria:**
- `gh workflow run ci.yml` collects ≥ 80 tests (no collection errors).
- Coverage threshold enforced.
- Frontend job unchanged (already mostly works).

### P0-T02 — Add real static analysis gates
**File:** `.github/workflows/ci.yml`, `apps/api/pyproject.toml`, `.pre-commit-config.yaml`, `.secrets.baseline`
**Steps:**
1. `ruff` config: `target-version = "py312"`, enable `E,F,I,B,UP,SIM,RUF,ASYNC,S`.
2. `mypy` config: `strict = true` for `apps/api/src/services/**`, `apps/api/src/agents/**`, `apps/api/src/core/**`.
3. `bandit` config: skip `tests/`, fail on `MEDIUM` or higher.
4. `detect-secrets` baseline committed; CI runs `--baseline .secrets.baseline`.
5. Add CI job `lint-backend` that runs all four.
6. Add a `ruff` rule (custom or `RUF` family) that bans `from litellm import completion|acompletion` outside `apps/api/src/clients/llm_client.py`. Use `tool.ruff.lint.per-file-ignores` + a grep step in CI if needed.

**Acceptance criteria:**
- CI fails on a deliberately-introduced direct `litellm.acompletion` call.
- `mypy --strict apps/api/src/services/llm_question_generator.py` currently fails with ≥10 errors (proves it's actually checking).

### P0-T03 — Tighten test fixtures so they don't mask bugs
**File:** `apps/api/tests/conftest.py`
**Steps:**
1. Replace blanket `mock_redis_client` with a dict-backed in-memory mock so `save_assessment_state` → `get_assessment_state` actually round-trips.
2. Remove `mock_redis_client` from `autouse=True`. Tests opt in explicitly.
3. Add a session-scoped `real_redis` fixture using `testcontainers[redis]` for integration tests.
4. Add a `caplog`-style helper that asserts no log line contains `@` (email leakage canary).

**Acceptance criteria:**
- At least one test in `tests/api/test_assessments_endpoint.py` exercises a full start→answer→complete flow against the in-memory Redis mock.
- That test FAILS today against current code (proves C-1 is exposed) — and is parked as `xfail(strict=True)` until P1-T01 lands.

### P0-T04 — Update `ACTIVE_CONTEXT.md` and create a tracking issue per critical bug
**File:** `ACTIVE_CONTEXT.md`, GitHub Issues
**Steps:**
1. Reset `Current Phase` to "Stage 2 — Remediation Continuing".
2. Open issues `PADI-C-01` through `PADI-C-12` (mirroring the review table). Link them in `ACTIVE_CONTEXT.md`.
3. Add a "Known false claims to retract" section pointing at the Stage 2 remediation report.

**Phase 0 exit criteria:**
- CI green on `main` with the real dependency list.
- `ruff`, `mypy --strict`, `bandit`, `detect-secrets` all gating.
- 12 critical-bug issues exist and are labeled `P0`.

---

## 3. Phase 1 — P0 Critical Bug Fixes (5 days)

> Order matters: C-2/C-3 (field names) unblock C-1 (Redis state). C-4 (BKT singleton) is foundational for every other bug fix touching mastery. Do them in the order below.

### P1-T01 (C-2, C-3) — Align `StudentSkillState` field access with the model
**Files:** `apps/api/src/services/assessment_service.py`, `apps/api/src/repositories/student_repository.py`, `apps/api/src/api/v1/endpoints/parent.py`
**Steps:**
1. Add a failing unit test: create a `StudentSkillState` row, call `_save_skill_state`, fetch back, assert `mastery_prob == expected`.
2. In `assessment_service._save_skill_state`, rename kwargs: `p_mastery → mastery_prob`, `p_guess → guess_prob`, `p_slip → slip_prob`, `p_learning → learning_rate`.
3. In `student_repository.update_skill_summary`, replace `state.p_mastery` with `state.mastery_prob`.
4. In `parent.py`, the response already uses `mastery_prob` (correct) — keep.
5. Add a centralized helper `bkt_state_from_row(row) -> BKTState` and `bkt_state_to_row(row, state)` in `services/bkt_service.py` so this mapping lives in one place forever.

**Acceptance criteria:**
- New unit test passes.
- `grep -rn 'state.p_mastery\|p_mastery=' apps/api/src` returns zero hits (except `BKTState` dataclass).
- `mypy --strict` passes on touched files.

### P1-T02 (C-1) — Persist `session_id` and `student_id` in Redis assessment state
**File:** `apps/api/src/services/assessment_service.py`, `apps/api/src/core/redis_client.py`
**Steps:**
1. Define a Pydantic v2 `AssessmentRedisState` model in `apps/api/src/schemas/internal/assessment_state.py` with required fields: `assessment_id`, `session_id`, `student_id`, `theta: float`, `covered_standards: dict[str, int]`, `questions_answered: int`, `bkt_states: dict[str, dict]`.
2. `RedisClient.save_assessment_state(state: AssessmentRedisState)` validates and serializes.
3. `RedisClient.get_assessment_state(assessment_id) -> AssessmentRedisState | None` deserializes back.
4. `assessment_service.start_assessment` constructs the model with `session_id=session.id, student_id=student_id`.
5. All downstream calls use `state.session_id`, `state.student_id` (no `.get(…)` defaults).
6. Failing → passing E2E test: `test_assessment_full_loop` does start → next_question → submit_response → complete and asserts `status == "completed"`.

**Acceptance criteria:**
- E2E happy path test passes against in-memory Redis mock.
- 100% coverage on `assessment_state.py`.
- C-1 issue closed.

### P1-T03 (C-4) — Make BKT stateless
**Files:** `apps/api/src/services/bkt_impl.py`, `apps/api/src/services/bkt_service.py`, callers
**Steps:**
1. Delete `BKTService._bkt_instances` cache and `get_or_create_bkt`.
2. New signature: `BKTService.update(prior: BKTState, is_correct: bool) -> BKTState`. Pure function. No process state.
3. Caller (`assessment_service.submit_response`) loads `BKTState` from `StudentSkillState` row, calls `update`, writes back to row. Atomic per request.
4. Add `tests/services/test_bkt_concurrency.py` that spawns 50 asyncio tasks doing independent BKT updates on the same skill and asserts each task's result is independent of the others.

**Acceptance criteria:**
- Concurrency test green.
- `grep -rn '_bkt_instances\|_bkt_service\b' apps/api/src` returns zero hits.
- Bench: `pytest tests/services/test_bkt_concurrency.py -k 50tasks --benchmark` < 200ms.

### P1-T04 (C-5) — Implement `PyBKT.from_db_record` / `to_db_record`
**Files:** `apps/api/src/services/bkt_impl.py`, `apps/api/src/api/v1/endpoints/learning_plans.py`
**Steps:**
1. Add classmethod `BKTState.from_row(row: StudentSkillState) -> BKTState` and method `apply_to_row(self, row: StudentSkillState) -> None`. (Prefer this over methods on `PyBKT`.)
2. Replace `PyBKT.from_db_record` / `to_db_record` usage in `submit_session_answer` with the new helpers.
3. Delete the stale `PyBKT` alias once nothing imports it.

**Acceptance criteria:**
- `tests/api/test_practice_session_flow.py::test_answer_updates_bkt` passes (currently xfailed).

### P1-T05 (C-6) — Fix `complete_session` model mismatches
**Files:** `apps/api/src/api/v1/endpoints/learning_plans.py`, `apps/api/src/models/models.py`, `apps/api/alembic/versions/006_practice_session_accuracy.py`
**Steps:**
1. Alembic migration 006: add `accuracy_percentage Float NULL` to `practice_sessions`.
2. In `learning_plans.complete_session`, change `PracticeSessionQuestion.practice_session_id` → `PracticeSessionQuestion.session_id`.
3. Replace `session.accuracy_percentage = …` with the real column post-migration.
4. Load `plan.modules` with `selectinload(LearningPlan.modules)` to avoid lazy-load.
5. Add migration test `tests/migrations/test_006_practice_session_accuracy.py` (forward + backward).

**Acceptance criteria:**
- `test_practice_sessions.py::test_complete_session_marks_accuracy` passes (currently xfailed; un-xfail it).

### P1-T06 (C-7) — `PlanModule.standard_id` stores Standard UUID, not code
**Files:** `apps/api/src/services/learning_plan_service.py`, `apps/api/src/api/v1/endpoints/learning_plans.py`, plus migration if backfill needed.
**Steps:**
1. Modify `_generate_module_sequence` to return `{"standard_id": <uuid>, "standard_code": <code>, …}`.
2. `LearningPlanService.generate_learning_plan` populates `PlanModule.standard_id = module_def["standard_id"]`.
3. Endpoint responses surface `standard_code` by joining to `Standard` via `selectinload`.
4. Backfill migration: for any existing `plan_modules.standard_id` that matches `standards.standard_code`, rewrite to `standards.id`.
5. Integration test: with UUID-id standards (not the test fixture's id==code) the full plan-generation flow works.

**Acceptance criteria:**
- New fixture `seed_grade_4_standards_uuid` (UUID ids) used by `tests/api/test_learning_plans_endpoint.py::test_generate_with_uuid_ids` passes.

### P1-T07 (C-8) — Fix `LLMQuestionGenerator` field names and self-ref
**Files:** `apps/api/src/services/llm_question_generator.py`, `apps/api/src/repositories/generation_job_repository.py`
**Steps:**
1. Change `GenerationJob(standard_code=…)` → `GenerationJob(standard_id=<uuid_resolved_from_code>)`. Add a lookup step in `create_generation_job` mirroring the one in `_promote_to_questions_table`.
2. Replace every `GeneratedQuestion.standard_code` reference with `GeneratedQuestion.standard_id`.
3. Replace `self.session` with `self.db_session` in `_promote_to_questions_table`.
4. Route LLM calls through `LLMClient.acomplete(purpose=LLMPurpose.QUESTION_GENERATION)` instead of `litellm.acompletion`. Same for `_verify_with_claude` (purpose=ADMIN).
5. Move `SentenceTransformer` to `apps/api/src/services/embedding_service.py` as a singleton; inject into `LLMQuestionGenerator`.
6. Delete `validation_details` kwarg in `QuestionValidationResult` (column doesn't exist).
7. Add `tests/services/test_llm_question_generator.py` with a recorded fixture (use `vcrpy` or hand-rolled mocks) that runs an end-to-end mock generation and asserts one row reaches the `questions` table.

**Acceptance criteria:**
- One full mock generation cycle promotes ≥ 1 row into `questions`.
- `grep -rn 'litellm\.\(a\)\?completion' apps/api/src` returns zero hits outside `clients/llm_client.py`.

### P1-T08 (C-9) — Fix auth endpoints
**Files:** `apps/api/src/api/v1/endpoints/auth.py`, `apps/api/src/models/models.py`
**Steps:**
1. In `register()`, rename every `request.<attr>` → `request_data.<attr>`. Add a regression test that POSTs valid JSON and asserts 201.
2. In `login()`, remove `auth0_sub` from request body. Make the endpoint require a valid JWT and read `sub` from the payload (`Depends(verify_jwt)`).
3. Remove `last_login_at`, `login_count`, `consent_confirmed_at` accesses, OR add columns + migration `007_user_login_tracking.py` if these are actually wanted (the model in PRD Stage 1 § FR-1 does call out tracking — add them).
4. Add `last_login_at` and `login_count` columns to `users` if going the additive route. Use `consented_at` (existing column) for the consent check.
5. Add `tests/api/test_auth_endpoint.py` covering both endpoints + an impersonation test asserting that a request with another user's `sub` in body but valid JWT for user A acts as user A.

**Acceptance criteria:**
- Impersonation test passes (auth0_sub from body is ignored).
- Register/login happy paths return 2xx.

### P1-T09 (C-10) — Close IDOR holes on submit_response / complete_assessment
**File:** `apps/api/src/api/v1/endpoints/assessments.py`
**Steps:**
1. Extract a `require_assessment_owned_by_user(assessment_id, user_payload, deps)` helper that returns the `Assessment` if the JWT subject owns the student.
2. Apply on `submit_response`, `complete_assessment`, and any other assessment endpoint missing the check.
3. Pass `student_id=assessment.student_id` (not `user_id`) into the service.
4. Add `tests/api/test_assessments_authz.py::test_submit_response_idor` and `…::test_complete_assessment_idor` (asserting 403).

**Acceptance criteria:**
- New IDOR tests pass.
- Other authz tests unchanged.

### P1-T10 (C-11) — Make `apiClient` actually authenticate
**Files:** `apps/web/lib/api-client.ts`, `apps/web/app/api/auth/callback/route.ts`, `apps/web/lib/auth-token.ts` (new)
**Steps:**
1. After Auth0 callback, store the access token in an httpOnly cookie (server-side set) **and** also expose a typed `getAccessToken()` server action / client helper for the SPA to pull when needed.
2. `ApiClient.request` reads the token (via `next/headers` on server components, via `fetch('/api/auth/token')` returning the JWT for client components — or use a cookie that the backend can read).
3. **Pick one auth mode:** either (a) Authorization Bearer header (backend currently expects this) or (b) cookie auth with CSRF token + backend `HTTPBearer` swap to cookie-aware dep. Recommend **(a) Bearer header** because backend is already there.
4. Add MSW handlers asserting requests carry `Authorization: Bearer <token>`.

**Acceptance criteria:**
- `tests/lib/api-client.test.ts` asserts header presence on every request.
- E2E `parent-journey.spec.ts` reaches a protected endpoint without 401.

### P1-T11 (C-12) — Replace mock data on Parent + Dashboard pages
**Files:** `apps/web/app/(dashboard)/dashboard/page.tsx`, `apps/web/app/(dashboard)/parent/page.tsx`, `apps/web/lib/api-client.ts`
**Steps:**
1. Add `apiClient.getParentDashboard(userId)`, `getDetailedReport(userId)`, `getLearningPlan(studentId)`, `getStudentBadges(studentId)`, `getStudentStreak(studentId)` methods.
2. Convert both pages to server components that `await apiClient.…` and render real data. Keep loading + error states.
3. Remove every literal "Jordan Smith" / "25%" string.
4. Add a Vitest test for each page that mocks the API and asserts correct render.

**Acceptance criteria:**
- `grep -rn 'Jordan Smith\|24%\|25%' apps/web` returns zero hits.
- Both page tests green.

**Phase 1 exit criteria:**
- All twelve P0 issues closed.
- One green end-to-end test covering: register → consent → create student → start diagnostic → answer 35 questions → complete → view results → generate learning plan → start practice session → submit answer → complete session.
- CI coverage ≥ 75%.

---

## 4. Phase 2 — True Stage 2 Closure (5 days)

### P2-T01 — Expand seed question bank to 132+
**Files:** `apps/api/scripts/seed_questions.py`, supporting JSON
**Steps:**
1. Move the question literals into `apps/api/scripts/seed_data/grade4_questions.json` (one file per standard).
2. Curriculum specialist (or LLM-with-human-review using `LLMQuestionGenerator` against test env) produces ≥ 3 questions per Grade-4 standard (≥ 87) and ≥ 5 per Grade-3 prerequisite standard (≥ 45). Target: 132.
3. Each question is validated by the same pipeline as generated questions (no skipping).
4. Seed idempotent (re-runs safe). Add `--dry-run` and `--standard <code>` flags.

**Acceptance criteria:**
- `python -m scripts.seed_questions` ends with `questions` count ≥ 132.
- Every question has `is_active=True`, ≥ 1 option marked `is_correct=True`, ≥ 3 distractors.

### P2-T02 — Wire question-gen pipeline missing validation steps
**Files:** `apps/api/src/services/llm_question_generator.py`
**Steps:**
1. Use `_execute_solution_code` result to assert generated answer matches independent solve. If mismatch, mark `solution_execution_passed=False`.
2. Implement `_check_difficulty_alignment` using a simple regression (word count + reading level + operation depth → expected difficulty bucket). Mark `difficulty_alignment_passed`.
3. Make `solution_execution_passed AND age_appropriateness_passed AND dedup_passed AND math_correctness_passed AND difficulty_alignment_passed` the gate for `overall_passed`.
4. Test: hand-craft three failing questions (one per failure mode) and assert each lands in the review queue, not the questions table.

**Acceptance criteria:**
- Five-step validation real, not stubbed.
- `tests/services/test_llm_question_generator.py::test_validation_gates` green.

### P2-T03 — Drop singleton service holders that close DB sessions
**Files:** `assessment_service.py`, `learning_plan_service.py`, `llm_question_generator.py`, callers
**Steps:**
1. Delete the bottom-of-file `_service = None` + `get_*_service(...)` singletons.
2. Replace with FastAPI dependency factories that return per-request instances.
3. Update tests that previously poked the singleton.

**Acceptance criteria:**
- `grep -n '_assessment_service\|_learning_plan_service\|_generator\b' apps/api/src` returns zero hits.

### P2-T04 — Fix `LearningPlan.completed_modules / completed_lessons / overall_progress`
**Files:** `apps/api/src/services/learning_plan_service.py`
**Steps:**
1. In `update_module_progress`, after marking a module completed, increment plan counters and recompute `overall_progress = completed_modules / total_modules`.
2. In `complete_session` (after the fix in P1-T05), increment `LearningPlan.completed_lessons`.
3. Add invariant test: progressing every module to completion sets `plan.status="completed"`, `overall_progress=1.0`.

**Acceptance criteria:**
- New invariant test passes.
- Parent dashboard now shows real progress.

### P2-T05 — Generate `packages/types` from FastAPI OpenAPI
**Files:** `packages/types/`, `package.json` (root), CI
**Steps:**
1. Add `pnpm gen:types` script: starts the API in OpenAPI export mode (`uvicorn src.main:app --no-lifespan` + `curl /api/openapi.json` is OK), pipes through `openapi-typescript` → writes `packages/types/src/api.ts`.
2. Keep a small `packages/types/src/domain.ts` for hand-curated cross-cutting types.
3. CI step: re-run `pnpm gen:types` and `git diff --exit-code`. Drift fails the build.

**Acceptance criteria:**
- `packages/types/index.ts` is auto-generated and committed.
- CI fails when backend Pydantic schema changes without a regen.

### P2-T06 — Replace mock dashboard data with live API (final pass)
**Files:** `apps/web/app/(dashboard)/parent/page.tsx`, `apps/web/app/(dashboard)/dashboard/page.tsx`, related components
**Note:** P1-T11 stubs this. P2-T06 finishes it with:
1. Real loading skeletons (replace the synthetic spinner).
2. Real error boundaries with retry.
3. Empty-state UI (no learning plan yet → prompt to start diagnostic).
4. Tablet-first layout audit per `docs/engineering/09-design-system.md` § 9.

**Acceptance criteria:**
- Lighthouse mobile ≥ 90 on the parent dashboard.
- Playwright `parent-journey.spec.ts` reaches the dashboard with seeded data.

### P2-T07 — Add `bandit` / SAST for student-data endpoints
**Files:** CI, `apps/api/.bandit.yaml`
**Steps:**
1. Configure `bandit` to fail on `B105`, `B106`, `B107`, `B201`, `B301-B411` (SQL/exec/yaml/etc.) anywhere in `apps/api/src/api/`.
2. Add a custom check: any function decorated `@router.<verb>` without `Depends(verify_jwt)` and not in an explicit allowlist (`/health`, `/auth/login`, `/auth/register`, marketing) fails CI.

**Acceptance criteria:**
- Deliberately removing `Depends(verify_jwt)` from `parent.get_parent_dashboard` fails CI.

### P2-T08 — Logging policy
**Files:** `apps/api/src/core/logging.py` (new), all services
**Steps:**
1. Centralize structured JSON logging with a redaction filter that strips `email`, `display_name`, `student_answer`, `question_text` keys.
2. Replace `logger.info(f"...{email}...")` patterns with `logger.info("...", extra={"event": "...", "ids": {…}})`.
3. Add `tests/core/test_logging_redaction.py` that asserts no `@` in any emitted log.

**Acceptance criteria:**
- Log-redaction test passes for every endpoint exercise in the E2E suite.

**Phase 2 exit criteria:**
- ≥ 132 seed questions in DB; mock data nowhere in `apps/web`.
- Question-generation pipeline produces 1 validated row end-to-end against mocks.
- `packages/types` regenerated and CI-gated.
- ACTIVE_CONTEXT.md: "Stage 2 complete — for real this time."

---

## 5. Phase 3 — Stage 3 Scaffolding (5 days)

### P3-T01 — Agent skeleton & `SessionState`
**Files:** `apps/api/src/agents/__init__.py`, `state.py`, `orchestrator.py`, `assessment_agent.py`, `tutor_agent.py`, `qgen_agent.py`, `progress_tracker.py`
**Steps:**
1. Copy the `SessionState` TypedDict from PRD Stage 3 § 3.2 verbatim.
2. Build a `langgraph.graph.StateGraph(SessionState)` with the four nodes and the routing functions from PRD Stage 3 § 3.2.
3. Each agent is initially a no-op that mutates state with a hardcoded response. Tutor & Assessment route through `llm_client` even if the prompt is empty — proves wiring.
4. Add `tests/agents/test_orchestrator_smoke.py` that runs one cycle and asserts state transitions.

**Acceptance criteria:**
- Orchestrator round-trips a question with all four nodes hit.
- Zero direct LLM imports in agent files.

### P3-T02 — WebSocket session endpoint
**Files:** `apps/api/src/api/v1/endpoints/practice_ws.py`, router
**Steps:**
1. `WS /api/v1/sessions/{session_id}/ws` — auth via JWT in query (`?token=`) or first ws frame.
2. On connect: load `SessionState` from Postgres LTM + Redis WM; send first question.
3. On message: feed into orchestrator; emit either next question, hint, or session-complete frame.
4. Heartbeat ping every 30s; auto-disconnect after 30 min idle.
5. Test with `httpx-ws` or `websockets` client lib.

**Acceptance criteria:**
- Smoke test: connect → answer → receive next question → disconnect cleanly.

### P3-T03 — Promote `difficulty` to IRT `difficulty_b`
**Files:** `models.py`, `alembic/versions/008_irt_b_param.py`, `question_selection_service.py`
**Steps:**
1. Add `Question.difficulty_b: Float NULL` and `Question.discrimination_a: Float DEFAULT 1.0`.
2. Backfill: `difficulty_b = (difficulty - 3) * 0.6` (maps 1..5 → -1.2..+1.2).
3. New `IRTService` (`apps/api/src/services/irt_service.py`) with 2PL information function: `I(θ, a, b) = a² * P(θ) * (1 - P(θ))` where `P(θ) = 1 / (1 + exp(-a(θ - b)))`.
4. Replace `_select_by_information` with a real maximum-information selector.
5. Add MLE θ update: Newton-Raphson on observed responses; cap at θ ∈ [-3, 3].
6. Unit tests on the IRT math (compare to a reference implementation like `catsim`).

**Acceptance criteria:**
- `tests/services/test_irt.py::test_information_max_at_theta_eq_b` passes.
- CAT diagnostic now selects question with `|θ - b|` minimized.

### P3-T04 — KaTeX in frontend
**Files:** `apps/web/package.json`, `apps/web/components/assessment/question-card.tsx`
**Steps:**
1. Add `katex` and `react-katex`.
2. Render `question.stem` through KaTeX if it contains `$…$` or `\(…\)` markers.
3. Render multiple-choice options through KaTeX too.
4. Test: a fraction question (`\frac{3}{4}`) renders as a stacked fraction.

**Acceptance criteria:**
- Visual regression test (Playwright screenshot diff) on three math-heavy questions.

### P3-T05 — `EmbeddingService` singleton + KaTeX hook for Tutor stubs
**Files:** `apps/api/src/services/embedding_service.py`, `apps/api/src/agents/tutor_agent.py`
**Steps:**
1. Lazy-load `SentenceTransformer('all-MiniLM-L6-v2')` once at first request; cache on the module.
2. Tutor agent stub returns a deterministic, KaTeX-safe hint for now (real LLM in Phase 4).

**Acceptance criteria:**
- Benchmarks show second-call dedup at < 50 ms (vs. current several-second cold start).

**Phase 3 exit criteria:**
- A demo where: open WebSocket → orchestrator picks a question (real IRT) → student answers → BKT updates → orchestrator emits next question. No real LLM yet.
- CI green.

---

## 6. Phase 4 — Stage 3 Implementation (4–6 weeks)

This is the bulk of net-new feature work. Each agent gets its own sprint slice.

### P4-A — Assessment Agent (week 1)
**Spec:** PRD Stage 3 § 3.2 Assessment Agent
- Implement `assess(student_answer, question_context, attempt_number) -> AssessmentResult` using `llm_client.acomplete(purpose=ASSESSMENT)`.
- Implement the 15-code error taxonomy (`ERR-OA-01` through `ERR-GUESS`) as a Pydantic enum.
- Output Pydantic schema with strict JSON-only mode (`response_format={"type": "json_object"}` via LiteLLM).
- Tests: 30+ canned `(student_answer, question, expected_error_code)` triplets covering each error type. Aim for ≥ 90% agreement.

### P4-B — Tutor Agent (week 1–2)
**Spec:** PRD Stage 3 § 3.2 Tutor Agent
- Three-level hint ladder. Pull `hint_1/hint_2/hint_3` from `practice_questions` if present; else generate via LLM.
- `validate_tutor_response(response)` post-processor enforces FK grade ≤ 5.5, word count ≤ 75, banned-phrase scan.
- Retry on validation failure (max 2). Fallback to canned response if still failing.
- Frustration model: implement `compute_frustration_score(state)` from PRD; switch `session_mode = "scaffolded"` at threshold 7.0.
- Tests: canned conversation transcripts assert no banned phrase and correct hint level per attempt.

### P4-C — Question Generator Agent (week 2)
**Spec:** PRD Stage 3 § 3.2 Question Generator
- Cache lookup against `questions` table with `difficulty_b BETWEEN θ-0.5 AND θ+0.5` and excluding session history.
- Fallback to live generation via `LLMClient.acomplete(purpose=QUESTION_GENERATION)`.
- Answer-verification pass: independent solve + equivalence check.
- Context-theme rotation per session (Oregon wildlife, food, sports, …).
- Tests: a session of 10 questions has ≤ 1 repeat of `context_theme` (PRD § 3.2 "Context Diversity Rules").

### P4-D — Progress Tracker (week 3)
**Spec:** PRD Stage 3 § 3.2 Progress Tracker
- BKT update per response (already implemented in P1-T03, this is the agent wrapper).
- Mastery declaration when `p_mastered ≥ 0.95 AND correct_streak ≥ 5 AND attempt_count ≥ 5 AND ≥ 3 hard problems`.
- Long-term memory writes (`StudentLongTermMemory` schema from PRD).
- Session summary generation (PRD § 3.2).
- Tests: simulate a 50-response stream, assert mastery declared at the right step.

### P4-E — Orchestrator routing & WebSocket frontend (week 3–4)
- Wire conditional edges per PRD § 3.2 routing functions.
- Frontend WebSocket client (`apps/web/lib/session-client.ts`); React hook `useSession(sessionId)`.
- Practice session UI components (PRD § 3.3 FR-11): question display, hint button + bubble, mascot Pip placeholders, progress bar, pause/resume, session summary screen.
- Playwright E2E: full 10-question session including a hint exchange and a mastery-unlock event.

### P4-F — Mastery progress visualization (week 4, parallel)
Per `ACTIVE_CONTEXT.md`'s already-listed Stage 3 immediate task #2.
- Parent dashboard: mastery gauges per skill (before vs. after).
- "You mastered X" celebration component.
- Skill-level history sparkline.

### P4-G — Cost + latency observability (week 5)
- Per-session cost ledger in Postgres (`session_llm_costs` table). PRD success criteria: < $0.15/session.
- P95 tutor latency tracked via Sentry transactions + a custom histogram.
- Alert: cost > $0.25/session, or P95 > 5s.

### P4-H — Load test 100 concurrent sessions (week 6)
- `locust` script that runs 100 parallel sessions, asserts P95 < 3 s and zero 5xx.
- Tune Ollama config (concurrency, GPU sharing) if needed.

**Phase 4 exit criteria (Stage 3 gate per PRD § 3.1 success criteria):**
- All four agents operational and integrated.
- ≥ 90% hint correctness on test set.
- ≥ 85% frustration detection on simulated scenarios.
- P95 tutor latency < 3 s under 100 concurrent sessions.
- LLM cost per session < $0.15.
- COPPA-compliant: no PII in prompt logs.

---

## 7. Phase 5 — Architecture & Hygiene (interleaved)

These are not blocking, but must land before Stage 4 (MVP). Sprinkle one per Phase-4 sprint.

| # | Ticket | Notes |
|---|---|---|
| H-01 | Replace `Vector = lambda dim: ARRAY(Float)` fallback with hard pgvector requirement | Drop the optional-import dance; CI containers always have pgvector |
| H-02 | Add `kid`-based key versioning to `EncryptionService` | Store `key_id` on each ciphertext; rotate without re-encrypt-all |
| H-03 | CORS: tighten in non-dev (`allow_origins` from `Settings.CORS_ORIGINS` only) | Already configurable; verify prod sets it |
| H-04 | Move `Padi Design System.pdf` + uploads/ out of `main` | Use GitHub Releases or `git-lfs` |
| H-05 | Remove all `datetime.utcnow()` | Replace with `datetime.now(timezone.utc)` |
| H-06 | Convert `from enum import Enum` for SQLAlchemy columns to `SQLEnum` with `native_enum=False` | Avoids the `Enum` vs `.value` confusion in `parent.py` |
| H-07 | Document the `LearningPlanTrack` ⇄ `plan_type` schema decision | PRD says `track`; types had `plan_type`. Pick one and update both |
| H-08 | Wire Unleash feature flags client | PRD non-negotiable #8; currently env-var-only |
| H-09 | Sentry transactions + custom spans on every agent node | Required for the P95 SLO |
| H-10 | PostHog analytics (Stage 5 prep) | COPPA-safe, cookieless, opt-in only |
| H-11 | Generate API SDK for `apps/web` automatically | `openapi-typescript-codegen` next to P2-T05 |
| H-12 | Dockerfile audit (multi-stage, non-root user, distroless) | Already partially done per remediation report |
| H-13 | Terraform skeleton for ECS/Fargate per ENG-000 ADR-3 | Currently only Vercel deploys |
| H-14 | Backup/restore runbook for Postgres + Redis | Required for Stage 4 |

---

## 8. Risk Register & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Hidden runtime bugs we haven't found yet | High | High | Phase 0 CI hardening; Phase 1 E2E happy-path test |
| Ollama too slow on solo-dev hardware for Phase 4 load tests | Medium | Medium | Use smaller model (qwen2.5:7b) in dev; full model only in load env |
| pyBKT/IRT calibration data won't exist until pilot | High | Medium | Use defaults (Corbett & Anderson 1994 params); add recalibration job for post-pilot |
| LLM cost overruns during Q-gen pipeline development | Medium | Low | Cap `OPENAI_API_KEY` org budget at $50; use Claude Haiku-tier in CI |
| Schema migrations conflict between active branches | Medium | Medium | One alembic revision per ticket; merge daily; `alembic merge` only with reviewer |
| Stage 3 PRD scope drift (it's the biggest stage) | High | High | Strict gate at end of Phase 3; no "while we're here" features in Phase 4 |
| COPPA DPA not signed in time to use cloud LLMs | Medium | High | Default is Ollama anyway; cloud switch is config-only (ADR-009 already specified) |

---

## 9. Communication Cadence

- **Daily:** Update the running ticket's PR description with progress checkboxes.
- **End of phase:** Update `ACTIVE_CONTEXT.md` (single source of truth for current phase).
- **End of phase:** Append a short report to `docs/history/YYYY-MM-DD-<phase>-report.md`. Honest count of passing/failing tests. Never round up.
- **On any P0 discovery during a later phase:** Stop. Add a `PADI-P0-<n>` issue. Decide whether to (a) hotfix and continue or (b) pause the phase. Don't accumulate.

---

## 10. Acceptance Summary (read this before merging Phase N → Phase N+1)

**Phase 0 done when:**
- [ ] CI installs full dep tree; backend tests run.
- [ ] `ruff`, `mypy --strict`, `bandit`, `detect-secrets` gating.
- [ ] 12 P0 issues open and tracked.

**Phase 1 done when:**
- [ ] All twelve C-1…C-12 issues closed with linked PRs.
- [ ] End-to-end test: parent registers → consents → creates student → completes 35-question diagnostic → plan generates → practice session start/answer/complete works.
- [ ] CI coverage ≥ 75%.

**Phase 2 done when:**
- [ ] ≥ 132 seed questions in the DB.
- [ ] Q-gen pipeline produces ≥ 1 validated row end-to-end (mocked LLM).
- [ ] `packages/types` auto-generated and drift-gated.
- [ ] Parent + Dashboard pages render real data (zero literal mock strings in `apps/web/app`).
- [ ] CI coverage ≥ 80%.

**Phase 3 done when:**
- [ ] LangGraph orchestrator with four nodes round-trips one question over WebSocket.
- [ ] Real IRT selection (b-param) live; CAT diagnostic uses θ on (-3, +3).
- [ ] KaTeX renders fractions in the practice UI.

**Phase 4 done when:**
- [ ] PRD Stage 3 § 3.1 "Success Criteria (Stage 3 Go/No-Go)" checklist all green.
- [ ] Load test: 100 concurrent sessions, P95 < 3 s, no 5xx, cost/session < $0.15.

**Phase 5:** Continuous; review at end of each Phase-4 sprint.

---

## 11. Estimated Calendar (solo + Claude Code agents @ 25–35 hrs/week)

| Phase | Hours | Wall-clock |
|---|---|---|
| Phase 0 | 12–16 | 2–3 days |
| Phase 1 | 40–55 | 7–10 days |
| Phase 2 | 35–50 | 7–10 days |
| Phase 3 | 35–50 | 7–10 days |
| Phase 4 | 180–260 | 5–8 weeks |
| Phase 5 (interleaved) | 30–50 | n/a |
| **Total to Stage 3 done** | **~330–480 hrs** | **~9–13 weeks** |

This is in line with `docs/strategy/00-master-index.md` "Solo Realistic" estimate of Stage 3 = 6–8 months total only if we count Phases 0–2 (remediation) as still part of Stage 2 — which they honestly are.

---

## 12. First Pull Request to Open

`feat(ci): install full dependency tree; gate ruff/mypy/bandit/detect-secrets (P0-T01, P0-T02)`

This single PR is the unlock for everything else. Until it lands, every other "tests pass" claim is unverifiable.
