# PADI.AI — Engineering Development Plan: Master Index

> **Prepared:** April 2026  
> **Scope:** Oregon Grade 4 Adaptive Math Learning App — Full SDLC  
> **Total documentation:** ~28,000 lines across 7 engineering documents  
> **Development tool:** Claude Code (Claude Sonnet 4.6 + o3-mini + local models on M4 Max 64GB)

---

## How to Use This Document Suite

These seven documents collectively define **how to build** PADI.AI. They complement the Product Documentation Suite (PRDs, Product Plan, Strategy) with engineering-specific guidance: architecture, system design, algorithms, infrastructure-as-code, testing plans, QA checklists, and operational runbooks.

**Start here → ENG-000 (Foundations)**. Every developer (human or Claude Code) must read this before writing any code. It defines the monorepo structure, all coding standards, the Claude Code workflow, ADRs, and security baseline that all subsequent stages must conform to.

**Then read your stage document** (ENG-001 through ENG-005) for the stage you're actively building.

**Reference ENG-006 (Cross-Cutting)** for testing, observability, security, SDLC governance, and the Claude Code operating manual — these apply to all stages simultaneously.

---

## Document Index

| Doc | File | Stage | Size | What It Covers |
|-----|------|-------|------|---------------|
| **ENG-000** | `ENG-000-foundations.md` | All | 175KB / 4,533 lines | Monorepo structure, 8 ADRs, Claude Code workflow + model routing, coding standards (Python/TS/DB/AI), testing strategy, security baseline, performance budgets |
| **ENG-001** | `ENG-001-stage1.md` | Months 1–3 | 165KB / 3,954 lines | Foundation + Diagnostic: C4 architecture, full PostgreSQL DDL (10 tables), 17 API endpoints with Pydantic models, BKT initialization algorithm, CAT question selection, COPPA consent flow, Terraform modules, GitHub Actions CI/CD, 5 operational runbooks |
| **ENG-002** | `ENG-002-stage2.md` | Months 4–6 | 119KB / 2,839 lines | Learning Plan Engine: skill dependency graph (NetworkX), learning plan generator, LLM question generation pipeline (o3-mini + 5-step validation), pgvector dedup, generation worker ECS task, 10 new DB tables, learning plan algorithms |
| **ENG-003** | `ENG-003-stage3.md` | Months 7–10 | 166KB / 4,431 lines | Adaptive AI Tutoring: complete LangGraph StateGraph (11 nodes + routing), WebSocket protocol (TypeScript types), BKT real-time update implementation, frustration score algorithm, IRT item selection, dual memory architecture, TutorAgent (Claude Sonnet), k6 WebSocket load test |
| **ENG-004** | `ENG-004-stage4.md` | Months 11–14 | 102KB / 2,542 lines | **MVP Stage**: 3PL IRT + EAP theta estimation (Python), proficiency classification (Oregon OSAS aligned), PDF report pipeline (WeasyPrint + S3), parent/teacher dashboards, notification system, 55-item MVP QA checklist, production readiness runbook |
| **ENG-005** | `ENG-005-stage5.md` | Months 15–20 | 143KB / 3,256 lines | **MMP Stage**: Stripe billing state machine + idempotent webhooks, feature gating middleware, school/district multi-tenancy (RLS), Clever SSO OAuth, i18n (next-intl, Spanish), PostHog COPPA-compliant analytics, auto-scaling to 10K users, 63-item MMP QA checklist |
| **ENG-006** | `ENG-006-crosscutting.md` | All Stages | 106KB / 2,234 lines | Testing master strategy (LLM contract tests, Playwright E2E, k6 load), 30+ Datadog metrics, 27 alerts (P1/P2/P3), STRIDE threat model, SDLC governance, data governance, CLAUDE.md templates for root + all sub-packages, model selection decision tree |

**Total:** ~976KB / ~23,789 lines of engineering specification

---

## Architecture at a Glance

```
┌─────────────────────────────────────────────────────────────┐
│                    PADI.AI — MMP ARCHITECTURE        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────┐    HTTPS     ┌─────────────────────────┐   │
│  │  Next.js 15 │◄────────────►│   FastAPI 0.115         │   │
│  │  (Vercel)   │    WSS       │   (AWS ECS/Fargate)     │   │
│  │  React 19   │◄────────────►│   + LangGraph Agents    │   │
│  │  TypeScript │              │   + BKT/IRT Engine      │   │
│  └─────────────┘              └────────────┬────────────┘   │
│                                            │                 │
│              ┌─────────────────────────────┼──────────────┐  │
│              │                             │              │  │
│         ┌────▼────┐    ┌──────────┐   ┌───▼────┐         │  │
│         │Postgres │    │  Redis   │   │   S3   │         │  │
│         │17+      │    │  7       │   │(reports│         │  │
│         │pgvector │    │(session/ │   │ media) │         │  │
│         │(RDS)    │    │ cache)   │   └────────┘         │  │
│         └─────────┘    └──────────┘                      │  │
│              └─────────────────────────────────────────┘  │  │
│                                                            │  │
│  External: Auth0 · Stripe · Clever · Claude API · OpenAI  │  │
│            AWS SES · PostHog · Datadog · Sentry            │  │
└─────────────────────────────────────────────────────────────┘
```

---

## Stage Gate Summary

| Gate | Stage | Month | Key Engineering Milestone |
|------|-------|-------|--------------------------|
| **PoC** | Stage 1 partial | Month 2 | Diagnostic runs end-to-end; BKT initializes; COPPA consent saves to DB |
| **Alpha** | Stage 2 complete | Month 6 | Question generation pipeline live; learning plans generate; dashboards show data |
| **MVP** | Stage 4 complete | Month 14 | Full loop: diagnostic→practice→assessment→remediation; all QA checklist items pass |
| **MMP** | Stage 5 complete | Month 20 | Stripe live; school onboarding works; Spanish live; 10K user load test passes |
| **v1.0** | Stage 6 | Month 24 | Multi-grade Oregon + district contracts |

---

## Claude Code Quick-Start

Before starting any development session with Claude Code:

1. **Always load the root CLAUDE.md** — located at `padi-ai/CLAUDE.md` (template in ENG-006 §6.1)
2. **Load the sub-package CLAUDE.md** for the area you're working in (`apps/api/CLAUDE.md`, `apps/web/CLAUDE.md`, `services/agent-engine/CLAUDE.md`)
3. **Check the model routing table** (ENG-000 §3.1) to select the right model for your task
4. **Reference the stage engineering plan** (ENG-001 through ENG-005) for the component you're building — feed the relevant section directly to Claude Code
5. **Run tests after every Claude Code feature** — never accumulate unverified Claude Code output

### Model Routing at a Glance

| Task | Model |
|------|-------|
| Architecture / ADRs / security design | Claude Opus 4.6 (frontier) |
| Feature implementation (complex) | Claude Sonnet 4.6 (frontier) |
| Auth, payments, COPPA flows | Claude Sonnet 4.6 (frontier — non-negotiable) |
| Feature implementation (routine CRUD) | Qwen2.5-Coder 32B via Ollama (local, free) |
| Test writing | DeepSeek-Coder V3 via Ollama (local, free) |
| Boilerplate / scaffolding | Qwen2.5-Coder 14B via Ollama (local, free) |
| LLM prompt engineering | Claude Opus 4.6 (frontier) |
| Documentation | Claude Haiku 3.5 or local Qwen |

---

## Key Engineering Decisions (ADR Summary)

| ADR | Decision | Rationale |
|-----|----------|-----------|
| ADR-001 | Monorepo (Turborepo) | Shared types, coordinated deploys, single CI pipeline |
| ADR-002 | FastAPI over Django | Async-native, Pydantic v2 integration, smaller footprint |
| ADR-003 | pgvector over Pinecone | Eliminate external dependency at early stage; migrate if > 10M vectors |
| ADR-004 | LangGraph over custom loop | Production-proven, checkpointing, streaming, graph visualization |
| ADR-005 | Auth0 over custom auth | COPPA-compliant plan, OAuth 2.0 + PKCE, no auth liability |
| ADR-006 | pyBKT + custom extensions | Proven BKT library + custom IRT layer for assessment |
| ADR-007 | Vercel (frontend) + AWS (backend) | Best-in-class DX for Next.js + full AWS ecosystem for AI workloads |
| ADR-008 | Unleash for feature flags | Open-source, self-hostable, no vendor lock-in |

---

## Non-Negotiable Engineering Rules

These rules apply to every line of code in every stage. Claude Code must be instructed to follow these without exception:

1. **No COPPA data before consent** — any code path that writes student PII to the DB must first verify `consent_records.confirmed_at IS NOT NULL`
2. **No raw SQL** — SQLAlchemy ORM or Core only; `bandit` will catch parameterized query violations in CI
3. **No hardcoded secrets** — `detect-secrets` pre-commit hook; `gitleaks` in CI
4. **No LLM output served to students without validation** — every generated question passes the 5-step validation pipeline before storage; no live/unvalidated output reaches students
5. **No frontend answer keys** — correct answers are never sent to the browser; all validation is server-side
6. **Every API endpoint is authenticated** — no unauthenticated endpoints except `/health`, `/auth/register`, `/auth/login`, `/auth/verify-email`
7. **No direct DB access from agent nodes** — LangGraph nodes call service layer only; repositories are not imported in agent code
8. **Feature flags for all new user-facing features** — no dark launches; every feature has a flag with documented expiry

---

*This engineering documentation suite is a living reference. Update the relevant document whenever architecture changes, ADRs are superseded, or operational runbooks are revised.*
