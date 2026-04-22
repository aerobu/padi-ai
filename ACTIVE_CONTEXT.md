# Active Project Context

## Current Phase: Stage 3 - Adaptive Practice & Tutoring
**Status:** Ready to Start
**Previous Phase:** Stage 2 Production Remediation (Completed 2026-04-21)

## Core Documentation
- **Master Index:** `docs/strategy/00-master-index.md`
- **Active PRD:** `docs/specs/05-prd-stage3.md`
- **Engineering Foundations:** `docs/engineering/ENG-000-foundations.md`
- **Latest Technical Report:** `docs/history/2026-04-21-stage2-remediation-report.md`

## Current State
- **Backend:** FastAPI (Async) + SQLAlchemy 2.0. Repository pattern strictly enforced.
- **Frontend:** Next.js 15 (App Router).
- **Tests:** 72/84 tests passing. 5 skipped (architectural), 5 xfailed (known service logic bugs).
- **Production:** Rate limiting (`slowapi`), Security Headers, and Sentry (API/Web) are active. Dockerfile optimized for pip/editable mode.

## Immediate Task: Initialize Stage 3
1. Review `docs/specs/05-prd-stage3.md` for mastery logic requirements.
2. Implement Mastery Progress visualizations in the Parent Dashboard.
3. Align `LearningPlanService` with the `standard_id` schema fixes made in Stage 2.

## Critical Patterns
1. **Repository Pattern:** All DB access via `src/repositories/`.
2. **Lazy Rules:** Path-scoped rules are in `.claude/rules/*.md`.
3. **COPPA:** Local LLM (Ollama/Qwen2.5) for all student tutoring.
