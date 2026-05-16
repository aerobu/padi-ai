# Active Project Context

## Current Phase: Stage 2 — Remediation Continuing
**Status:** Active (rolled back from "Stage 3 ready" on 2026-05-16)
**Reason:** Code review on 2026-05-16 identified 12 critical (P0) bugs that
would prevent the diagnostic + practice-session flows from running end-to-end.
The Stage 2 remediation report (2026-04-21) overstated completeness.

## Execution Plan
- **Plan document:** `docs/history/2026-05-16-execution-plan.md`
- **Phase 0:** CI hardening (in progress — `feat(ci)` PR)
- **Phase 1:** Fix critical bugs C-1 → C-12 (next)
- **Phase 2:** True Stage 2 closure (seed bank, Q-gen, dashboards)
- **Phase 3:** Stage 3 scaffolding (agent skeleton, WebSocket, IRT)
- **Phase 4:** Stage 3 implementation (5–8 weeks)

## Critical Bug Backlog (P0)
Tracked in `docs/history/2026-05-16-execution-plan.md` § 3.

| ID | Component | Summary |
|----|-----------|---------|
| C-1 | `assessment_service.start_assessment` | `session_id` and `student_id` never persisted to Redis state |
| C-2 | `assessment_service._save_skill_state` | Wrong kwargs (`p_mastery` etc.) — model uses `mastery_prob` |
| C-3 | `student_repository.update_skill_summary` | Reads non-existent `state.p_mastery` attribute |
| C-4 | `bkt_service.BKTService` | Process-wide singleton corrupts state across concurrent students |
| C-5 | `learning_plans.submit_session_answer` | Calls non-existent `PyBKT.from_db_record` / `to_db_record` |
| C-6 | `learning_plans.complete_session` | Reads `practice_session_id` (real col is `session_id`); writes missing `accuracy_percentage` |
| C-7 | `learning_plan_service.generate_learning_plan` | Stores `standard_code` in `PlanModule.standard_id` (FK violation in prod) |
| C-8 | `llm_question_generator` | `standard_code` kwarg mismatch; `self.session` (real attr is `self.db_session`); direct `litellm` import |
| C-9 | `auth.register` / `auth.login` | Wrong variable name `request.x`; non-existent model fields; impersonation via body param |
| C-10 | `assessments.submit_response/complete` | Missing IDOR check (parent ownership) |
| C-11 | `apps/web/lib/api-client.ts` | Never attaches `Authorization` header |
| C-12 | `apps/web/app/(dashboard)/*/page.tsx` | Hard-coded mock data; no API integration |

## Core Documentation
- **Master Index:** `docs/strategy/00-master-index.md`
- **Engineering Foundations:** `docs/engineering/ENG-000-foundations.md`
- **Stage 3 PRD (target):** `docs/specs/05-prd-stage3.md`
- **Code Review:** Conducted 2026-05-16 (in session history)
- **Execution Plan:** `docs/history/2026-05-16-execution-plan.md`

## Critical Patterns (non-negotiable)
1. **Repository pattern:** All DB access via `src/repositories/`. No raw `select()` in routers.
2. **LLM routing:** All LLM calls via `src/clients/llm_client.py`. CI gate enforced.
3. **COPPA:** Local Ollama/Qwen2.5 for all student-facing inference.
4. **Pydantic v2** for every request/response model.
5. **`datetime.now(timezone.utc)`** — never `datetime.utcnow()` (deprecated in 3.12).
