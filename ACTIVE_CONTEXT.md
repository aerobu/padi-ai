# Active Project Context

## Current Phase: Stage 3 — Phase 4-A Ready (Assessment Agent)
**Status:** Phases 0, 1, 2-partial, and 3 landed 2026-05-16.
**Up next:** Phase 4-A — implement the real Assessment Agent (15-code
error taxonomy via `LLMClient(purpose=ASSESSMENT)`).

## Latest Reports
- **Phase 0–3 report:** `docs/history/2026-05-16-phase-0-3-report.md`
- **Execution plan (still authoritative):** `docs/history/2026-05-16-execution-plan.md`

## What's Verified Working
- Diagnostic flow: start → answer → complete (Redis state round-trips).
- BKT: stateless, concurrent-safe (50-stream test).
- 4-agent orchestrator (PRD § 3.2 routing) with deterministic stubs.
- WebSocket `/api/v1/sessions/{id}/ws` endpoint with JWT auth.
- Real 2PL IRT in `_select_by_information`.
- 135-question seed bank across all 39 G3/G4 standards.
- KaTeX rendering in QuestionCard.
- Parent + Dashboard pages call live API (zero mock data).
- `apiClient` attaches `Authorization: Bearer` header.
- CI hardened (ruff, mypy, bandit, detect-secrets, type-drift gate,
  forbids direct LLM imports outside `llm_client.py`).

## Test Status
- **92/92 no-DB tests passing** (was 60 pre-session, couldn't even
  collect in CI).
- 7 new test files committed (BKT concurrency, assessment state, IRT
  math, orchestrator round-trip, WS smoke, seed-bank invariants, PII
  redaction).
- Legacy `tests/repositories/*` and `tests/core/test_redis_client.py`
  still red — pre-existing bugs, not introduced.

## Critical Patterns (non-negotiable)
1. **Repository pattern:** All DB access via `src/repositories/`. No raw
   `select()` in routers.
2. **LLM routing:** All LLM calls via `src/clients/llm_client.py`.
   CI gate enforces this.
3. **COPPA:** Local Ollama/Qwen2.5 for student-facing inference.
4. **Pydantic v2** for every request/response model.
5. **`datetime.now(timezone.utc)`** — never `datetime.utcnow()`.
6. **BKT is stateless.** Pass priors through, never cache on the service.

## Backlog (Stage 3 → MVP)
See `docs/history/2026-05-16-phase-0-3-report.md` § 4 for the full
carry-forward list. Highlights:
- **Phase 4-A:** Assessment Agent — real 15-code error taxonomy.
- **Phase 4-B:** Tutor Agent — FK validator + frustration model.
- **Phase 4-C:** Question Generator — cache + live + verification.
- **Phase 4-D:** Progress Tracker LTM writes + session summary.
- **Phase 4-E:** LangGraph swap; frontend `useSession` hook + practice UI.
- **Phase 4-G:** Cost + latency observability (`session_llm_costs`).
- **Phase 4-H:** 100-session load test (<3s P95, <$0.15/session).
