# MathPath Oregon — Claude Code Skills & Plugins Specification

## Document 17 | Version 1.0 | April 2026

> **Document ID:** CC-017  
> **Status:** Final Draft — Internal Reference  
> **Last Updated:** 2026-04-08  
> **Owner:** Engineering Lead  
> **Audience:** Solo developer, AI coding agents, Claude Code sessions, future contributors  
> **Prerequisites:** ENG-000 (Foundations), Doc 09 (Design System), LC-001–LC-005 (Lifecycle), OPS-000 (Cross-Cutting Ops)

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Skills Architecture Overview](#2-skills-architecture-overview)
3. [Complete Skill Inventory Table](#3-complete-skill-inventory-table)
4. [CLAUDE.md Template](#4-claudemd-template)
5. [Modular Rule Files](#5-modular-rule-files)
6. [Detailed Skill Specifications](#6-detailed-skill-specifications)
7. [Custom Slash Commands](#7-custom-slash-commands)
8. [Hook Configuration](#8-hook-configuration)
9. [Subagent Definitions](#9-subagent-definitions)
10. [MCP Server Configuration](#10-mcp-server-configuration)
11. [Context Management Strategy](#11-context-management-strategy)
12. [Implementation Roadmap](#12-implementation-roadmap)
13. [Skills-to-Lifecycle Mapping Matrix](#13-skills-to-lifecycle-mapping-matrix)
14. [Marketplace vs. Custom Analysis](#14-marketplace-vs-custom-analysis)
15. [Appendix: Configuration File Reference](#15-appendix-configuration-file-reference)

---

## 1. Executive Summary

### 1.1 Purpose

This document defines the complete Claude Code customization layer for MathPath Oregon — an AI-powered adaptive math learning platform serving Oregon elementary students (Grades 1–5). Claude Code is the primary development environment for this project, running on an M4 Max MacBook Pro with 64 GB of unified memory. Every line of code, every test, every deployment, and every design decision flows through Claude Code sessions.

Without intentional customization, Claude Code operates as a general-purpose coding assistant. It generates syntactically correct code but lacks knowledge of MathPath's architectural conventions, design system tokens, Oregon math standards, COPPA compliance requirements, BKT model patterns, or the 5-stage SDLC lifecycle that governs development. This document transforms Claude Code from a general assistant into a MathPath-aware development partner through six complementary mechanisms:

1. **CLAUDE.md** — The root context file that Claude reads at session start, providing project overview, tech stack, essential commands, and pointers to deeper context.
2. **Modular Rule Files** (`.claude/rules/*.md`) — Path-scoped instructions that auto-load when Claude edits files matching specific glob patterns, enforcing domain-specific conventions without consuming context on unrelated tasks.
3. **Skills** (`.claude/skills/*/SKILL.md`) — Rich, structured instruction sets for complex capabilities that Claude loads on demand — design token enforcement, BKT model patterns, LangGraph agent orchestration, COPPA compliance checks.
4. **Hooks** (`.claude/settings.json`) — Automated lifecycle events that fire at session start, before compaction, after file edits, and on session stop to enforce quality gates, preserve context, and prevent destructive operations.
5. **Custom Slash Commands** (`.claude/commands/*.md`) — Developer-facing workflows triggered by `/custom:name` that orchestrate multi-step operations like implementing a ticket, running targeted tests, or searching the 24-document specification suite.
6. **Subagents** (`.claude/agents/*.md`) — Specialized Claude instances that fork from the main session to perform isolated work — test execution, security scanning, spec research, code review — without polluting the primary context window.

Together, these six mechanisms encode approximately 100 hours of configuration work into a system that reduces per-session ramp-up from ~15 minutes of manual context injection to ~3 seconds of automated loading. Over the 20-month, 5-stage development lifecycle, this investment yields an estimated 300+ hours of recovered development time.

### 1.2 Scope

This specification covers every configuration file, skill definition, hook script, slash command, subagent definition, and MCP server integration required to operate Claude Code effectively on the MathPath Oregon monorepo. It is organized as a reference document — each section is self-contained and can be consulted independently during implementation.

### 1.3 Key Metrics

| Metric | Value |
|--------|-------|
| Total skills defined | 16 |
| Modular rule files | 8 |
| Custom slash commands | 7 |
| Hook event handlers | 8 |
| Subagent definitions | 5 |
| MCP server integrations | 6 |
| Estimated implementation effort | ~100 hours over 10 weeks |
| Context savings per session | ~12,000 tokens (80% reduction in manual context injection) |
| CLAUDE.md template size | 148 lines |

### 1.4 Document Relationships

| Document | Relationship to This Document |
|----------|-------------------------------|
| ENG-000 (Foundations) | Provides repo structure, coding standards, and ADRs that rule files and skills enforce |
| Doc 09 (Design System) | Provides design tokens, component specs, and accessibility standards embedded in the `mathpath-design-tokens` and `mathpath-component-library` skills |
| LC-001–LC-005 (Lifecycle Stages) | Provide the SDLC phases that the `sprint-lifecycle` skill enforces |
| OPS-000 (Cross-Cutting Ops) | Provides MLOps, FinOps, SecOps, and DevSecOps standards that hooks and subagents validate |
| Doc 16 (Multi-Grade Expansion) | Provides grade-specific UI requirements and Oregon standards that the `grade-specific-patterns` and `oregon-standards-validator` skills reference |

---

## 2. Skills Architecture Overview

### 2.1 System Architecture

Claude Code's customization system is a layered architecture where each layer narrows context progressively — from broad project awareness (CLAUDE.md) to task-specific expertise (skills) to automated enforcement (hooks). The following diagram shows how these layers interact:

```
┌─────────────────────────────────────────────────────────────────────┐
│                     CLAUDE CODE SESSION                              │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  Layer 1: CLAUDE.md (Always loaded — ~148 lines)            │    │
│  │  • Project overview, tech stack, essential commands          │    │
│  │  • Repository structure summary                             │    │
│  │  • Non-default conventions, common gotchas                  │    │
│  │  • Progressive disclosure → @rules, @skills                 │    │
│  └─────────────┬───────────────────────────────────────────────┘    │
│                │ References                                          │
│  ┌─────────────▼───────────────────────────────────────────────┐    │
│  │  Layer 2: Rule Files (.claude/rules/*.md) — Auto-loaded     │    │
│  │                                                              │    │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │    │
│  │  │frontend  │ │backend   │ │agent     │ │test      │       │    │
│  │  │-rules.md │ │-rules.md │ │-rules.md │ │-rules.md │       │    │
│  │  │apps/web/*│ │apps/api/*│ │services/ │ │**/tests/*│       │    │
│  │  └──────────┘ └──────────┘ │agent-*/* │ └──────────┘       │    │
│  │  ┌──────────┐ ┌──────────┐ └──────────┘ ┌──────────┐       │    │
│  │  │infra     │ │design-   │ ┌──────────┐ │coppa     │       │    │
│  │  │-rules.md │ │system    │ │database  │ │-rules.md │       │    │
│  │  │infra/**  │ │-rules.md │ │-rules.md │ │**/secur* │       │    │
│  │  └──────────┘ │packages/ │ │**/db/**  │ │**/consen*│       │    │
│  │               │ui/**     │ │**/migra* │ └──────────┘       │    │
│  │               └──────────┘ └──────────┘                     │    │
│  └─────────────┬───────────────────────────────────────────────┘    │
│                │ On-demand loading                                    │
│  ┌─────────────▼───────────────────────────────────────────────┐    │
│  │  Layer 3: Skills (.claude/skills/*/SKILL.md) — On-demand    │    │
│  │                                                              │    │
│  │  ┌─────────────────┐  ┌─────────────────┐                  │    │
│  │  │ Design Tokens    │  │ Component Lib   │  Capability      │    │
│  │  │ Test Coverage    │  │ BDD Scenarios   │  Uplift          │    │
│  │  │ BKT Patterns     │  │ LangGraph       │  Skills          │    │
│  │  │ Oregon Standards │  │ Grade Patterns  │                  │    │
│  │  └─────────────────┘  └─────────────────┘                  │    │
│  │  ┌─────────────────┐  ┌─────────────────┐                  │    │
│  │  │ COPPA Security   │  │ Sprint Lifecycle│  Encoded         │    │
│  │  │ Architecture     │  │ Story Tracker   │  Preference      │    │
│  │  │ API Contracts    │  │ Cost Optimizer  │  Skills          │    │
│  │  │ Accessibility    │  │ Compaction      │                  │    │
│  │  └─────────────────┘  └─────────────────┘                  │    │
│  └─────────────┬───────────────────────────────────────────────┘    │
│                │ Automated enforcement                                │
│  ┌─────────────▼───────────────────────────────────────────────┐    │
│  │  Layer 4: Hooks (settings.json) — Automated                 │    │
│  │                                                              │    │
│  │  SessionStart ──→ Load env, verify deps, inject stage ctx   │    │
│  │  PreCompact ───→ Preserve sprint info, BKT state, tokens    │    │
│  │  PostToolUse ──→ Auto-lint .tsx/.css, validate tokens       │    │
│  │  PreToolUse ───→ Block destructive bash, validate patterns  │    │
│  │  Stop ─────────→ Verify test coverage, check COPPA          │    │
│  │  SubagentStop ─→ Verify subagent output quality             │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                      │
│  ┌───────────────────┐  ┌───────────────────┐                       │
│  │  Slash Commands    │  │  Subagents        │                       │
│  │  /custom:implement │  │  test-runner      │                       │
│  │  /custom:test      │  │  security-scanner │                       │
│  │  /custom:deploy    │  │  spec-researcher  │                       │
│  │  /custom:story     │  │  code-reviewer    │                       │
│  │  /custom:spec      │  │  grade-validator  │                       │
│  │  /custom:stage     │  │                   │                       │
│  │  /custom:grade     │  │                   │                       │
│  └───────────────────┘  └───────────────────┘                       │
│                                                                      │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  MCP Servers (External Tool Integrations)                     │  │
│  │  GitHub · PostgreSQL · Figma · Playwright · Sentry · Context7 │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 Token Budget Model

Claude Code operates with a ~200K token context window. Effective session management requires understanding how each customization layer contributes to context usage:

| Layer | Tokens (Approx.) | When Loaded | Persistence |
|-------|-------------------|-------------|-------------|
| CLAUDE.md | ~800 | Session start | Always present |
| Active rule files (2–3) | ~300–600 each | Auto on file glob match | While editing matched files |
| Skill description scan (all 16) | ~100 each × 16 = 1,600 | Session start (descriptions only) | Always present |
| Active skill full content (1–2) | ~2,000–4,500 each | On-demand when relevant | Until context pressure |
| Hook overhead | ~200 per hook event | On event fire | Transient |
| Slash command content | ~500–1,500 | On `/custom:name` invocation | Until task complete |
| Subagent context | Separate window | On fork | Isolated |
| **Baseline session overhead** | **~4,000–6,000** | — | ~3% of 200K budget |

The 80/20 principle applies: 80% of context budget (160K tokens) remains available for code, documentation, and reasoning. The remaining 20% (40K tokens) is the maximum allocation for all customization layers combined. In practice, the baseline overhead of ~5,000 tokens leaves 195K tokens for productive work.

### 2.3 Skill Types

Following the Claude Code community classification, MathPath skills fall into two categories:

| Type | Definition | MathPath Examples |
|------|-----------|-------------------|
| **Capability Uplift** | Teaches Claude something it cannot do natively — domain-specific knowledge, specialized algorithms, or external tool integration | BKT model patterns, LangGraph agent patterns, Oregon standards validation, grade-specific UI adaptation |
| **Encoded Preference** | Encodes project-specific conventions that Claude could discover but should not have to re-learn each session — coding standards, design tokens, testing practices, deployment checklists | Design tokens, component library patterns, test coverage requirements, API contract enforcement, architecture boundaries |

### 2.4 File Layout

All Claude Code configuration files reside within the `.claude/` directory at the monorepo root, with the exception of `CLAUDE.md` which sits at the repository root per convention:

```
mathpath/
├── CLAUDE.md                           # Root context file (~148 lines)
├── .claude/
│   ├── settings.json                   # Hooks, permissions, project settings
│   ├── settings.local.json             # Developer-local overrides (gitignored)
│   ├── rules/                          # Auto-loading rule files
│   │   ├── frontend-rules.md
│   │   ├── backend-rules.md
│   │   ├── agent-rules.md
│   │   ├── test-rules.md
│   │   ├── infra-rules.md
│   │   ├── design-system-rules.md
│   │   ├── database-rules.md
│   │   └── coppa-rules.md
│   ├── skills/                         # On-demand skill definitions
│   │   ├── mathpath-design-tokens/
│   │   │   └── SKILL.md
│   │   ├── mathpath-component-library/
│   │   │   └── SKILL.md
│   │   ├── mathpath-test-coverage/
│   │   │   └── SKILL.md
│   │   ├── bdd-scenario-writer/
│   │   │   └── SKILL.md
│   │   ├── security-coppa-compliance/
│   │   │   └── SKILL.md
│   │   ├── sprint-lifecycle/
│   │   │   └── SKILL.md
│   │   ├── user-story-tracker/
│   │   │   └── SKILL.md
│   │   ├── architecture-enforcer/
│   │   │   └── SKILL.md
│   │   ├── bkt-model-patterns/
│   │   │   └── SKILL.md
│   │   ├── langgraph-agent-patterns/
│   │   │   └── SKILL.md
│   │   ├── api-contract-enforcement/
│   │   │   └── SKILL.md
│   │   ├── oregon-standards-validator/
│   │   │   └── SKILL.md
│   │   ├── grade-specific-patterns/
│   │   │   └── SKILL.md
│   │   ├── strategic-compaction/
│   │   │   └── SKILL.md
│   │   ├── llm-cost-optimizer/
│   │   │   └── SKILL.md
│   │   └── accessibility-enforcer/
│   │       └── SKILL.md
│   ├── commands/                        # Custom slash commands
│   │   ├── implement.md
│   │   ├── test.md
│   │   ├── deploy-check.md
│   │   ├── story-status.md
│   │   ├── spec-search.md
│   │   ├── stage-context.md
│   │   └── grade-check.md
│   └── agents/                          # Subagent definitions
│       ├── test-runner.md
│       ├── security-scanner.md
│       ├── spec-researcher.md
│       ├── code-reviewer.md
│       └── grade-content-validator.md
```

---

## 3. Complete Skill Inventory Table

The following table catalogs all 16 skills with their classification, priority, implementation strategy, stage relevance, and estimated effort.

| # | Skill Name | Category | Build/Buy/Customize | Priority | Stages | Description | Effort (hrs) |
|---|-----------|----------|-------------------|----------|--------|-------------|--------------|
| 1 | `mathpath-design-tokens` | Encoded Preference | Build | P0 | 1–5 | Enforces color, typography, spacing, elevation, border radius, and motion tokens from Doc 09. Validates that every component uses semantic tokens, never raw hex values or pixel literals. | 8 |
| 2 | `mathpath-component-library` | Encoded Preference | Build | P0 | 1–5 | Enforces Atomic Design component patterns (atoms, molecules, organisms, templates) with MathPath-specific math UI components (FractionBuilder, NumberLine, MathDisplay). | 6 |
| 3 | `mathpath-test-coverage` | Encoded Preference | Build | P0 | 1–5 | Enforces the testing pyramid — unit (70%), integration (20%), E2E (10%). Validates coverage gates: 80% line coverage for services, 90% for BKT engine, 100% for COPPA consent flows. | 6 |
| 4 | `bdd-scenario-writer` | Capability Uplift | Build | P1 | 1–5 | Generates Gherkin `.feature` files from user story acceptance criteria defined in LC-001 through LC-005. Produces scenarios with Given/When/Then steps mapped to Playwright step definitions. | 5 |
| 5 | `security-coppa-compliance` | Capability Uplift | Build | P0 | 1–5 | Validates COPPA compliance (parental consent, data minimization, PII encryption, retention limits) and OWASP API Security Top 10. Blocks code that collects child PII without consent checks. | 8 |
| 6 | `sprint-lifecycle` | Encoded Preference | Build | P0 | 1–5 | Enforces the 7-phase SDLC gate: PRD → Design → Architecture → Implement → Test → QA → Ops. Validates that each phase's entry/exit criteria are met before proceeding. | 7 |
| 7 | `user-story-tracker` | Encoded Preference | Build | P1 | 1–5 | Tracks implementation progress against user stories from LC-001 through LC-005. Maps code changes to story acceptance criteria and reports completion status. | 5 |
| 8 | `architecture-enforcer` | Encoded Preference | Build | P0 | 1–5 | Enforces monorepo boundaries from ENG-000: no cross-app imports, correct layer dependencies (routes → services → repositories → DB), no business logic in route handlers. | 6 |
| 9 | `bkt-model-patterns` | Capability Uplift | Build | P1 | 1–4 | Provides pyBKT implementation patterns: parameter initialization, Roster API usage, mastery threshold configuration, calibration routines, and integration with question selection. | 6 |
| 10 | `langgraph-agent-patterns` | Capability Uplift | Build | P1 | 2–5 | Multi-agent orchestration patterns for LangGraph 0.2: graph definition, state schemas, node implementations, conditional edges, tool definitions, checkpointing, and LLM provider abstraction. | 8 |
| 11 | `api-contract-enforcement` | Encoded Preference | Build | P0 | 1–5 | Validates OpenAPI spec consistency with Pydantic v2 models. Ensures request/response types in `packages/types/` mirror FastAPI route schemas. Catches contract drift between frontend and backend. | 5 |
| 12 | `oregon-standards-validator` | Capability Uplift | Build | P1 | 1–5 | Validates that math question content, assessment parameters, and BKT skill mappings align with Oregon 2021 Math Standards (K–5). Cross-references standard codes against the authoritative JSON. | 6 |
| 13 | `grade-specific-patterns` | Capability Uplift | Build | P2 | 3–5 | Age-appropriate UI adaptation rules from Doc 16: touch target sizes, font minimums, TTS requirements, interaction modalities, and session length caps per grade band. | 5 |
| 14 | `strategic-compaction` | Encoded Preference | Build | P0 | 1–5 | Context management discipline: when to trigger `/compact`, what must be preserved (sprint context, active standards, BKT state), recovery procedures after compaction. | 4 |
| 15 | `llm-cost-optimizer` | Capability Uplift | Build | P2 | 2–5 | Token usage tracking, model routing rules (Sonnet for tutoring, o3-mini for question gen, Haiku for classification), cost alerts, and per-student cost attribution from OPS-000 FinOps framework. | 5 |
| 16 | `accessibility-enforcer` | Encoded Preference | Build | P0 | 1–5 | WCAG AA/AAA enforcement, ARIA attributes, keyboard navigation, screen reader compatibility, focus management, `prefers-reduced-motion` support, and contrast verification. | 6 |

**Totals:**

| Category | Count | Total Effort |
|----------|-------|-------------|
| Capability Uplift | 7 | 43 hrs |
| Encoded Preference | 9 | 53 hrs |
| **All Skills** | **16** | **96 hrs** |

---

## 4. CLAUDE.md Template

The following is the complete, ready-to-use root `CLAUDE.md` file for the MathPath Oregon monorepo. It follows the Claude Code best practice of staying under 200 lines and using progressive disclosure to reference rule files and skills for domain-specific depth.

```markdown
# MathPath Oregon

AI-powered adaptive math learning platform for Oregon elementary students (Grades 1–5).
Built with Bayesian Knowledge Tracing (BKT) and LLM tutoring. Targeting COPPA compliance.

## Tech Stack

**Frontend:** React 19 · Next.js 15 (App Router) · TypeScript 5.5 (strict) · Tailwind CSS 4 · KaTeX 0.16
**Backend:** Python 3.12 · FastAPI 0.115 · SQLAlchemy 2.0 (async) · Pydantic v2 · Alembic
**AI/ML:** LangGraph 0.2 · LangChain 0.3 · pyBKT 1.4 · Claude Sonnet 4.6 · o3-mini · GPT-4o
**Data:** PostgreSQL 17 (pgvector, pgcrypto, ltree) · Redis 7 · S3
**Auth:** Auth0 (COPPA-compliant tenant)
**Infra:** AWS ECS Fargate · Vercel · Terraform · GitHub Actions
**Testing:** Vitest + Testing Library · pytest · Playwright · MSW
**Monorepo:** pnpm workspaces · Turborepo

## Essential Commands

```bash
# Development
pnpm dev                          # Start all TS packages (Turborepo)
make api-dev                      # Start FastAPI (uvicorn --reload)
make agent-dev                    # Start agent engine
docker compose up -d              # Start Postgres + Redis locally

# Testing
pnpm test                         # Run all TS tests (Vitest)
pnpm test:e2e                     # Run Playwright E2E suite
make api-test                     # Run pytest (backend)
make bkt-test                     # Run BKT engine tests
make test-all                     # Run entire test suite

# Build & Lint
pnpm build                        # Build all TS packages
pnpm lint                         # ESLint + Prettier check
pnpm typecheck                    # TypeScript strict check
make api-lint                     # Ruff + mypy (backend)

# Database
make db-migrate                   # Run Alembic migrations
make db-seed                      # Seed standards + questions
make db-reset                     # Drop, recreate, migrate, seed

# Deploy
make deploy-staging               # Deploy to staging (requires AWS creds)
make deploy-prod                  # Deploy to production (requires approval)
```

## Repository Structure

```
mathpath/
├── apps/web/                  # Next.js 15 frontend (App Router)
│   └── src/app/, components/, hooks/, lib/, stores/, styles/
├── apps/api/                  # FastAPI backend
│   └── src/api/v1/, models/, service/, repository/, db/, core/
├── services/agent-engine/     # LangGraph AI agents (tutor, diagnostic, plan)
├── services/question-generator/ # LLM question generation pipeline
├── services/bkt-engine/       # Bayesian Knowledge Tracing (pyBKT)
├── packages/ui/               # Shared design system components
├── packages/math-renderer/    # KaTeX wrapper components
├── packages/types/            # Shared TypeScript types
├── packages/config/           # Shared ESLint, TS, Prettier configs
├── packages/db-schema/        # TypeScript types mirroring DB schema
├── infrastructure/terraform/  # AWS IaC (ECS, RDS, ElastiCache, S3)
├── infrastructure/docker/     # Dockerfiles, docker-compose
├── docs/                      # Product docs (01–17), ADRs, runbooks
└── eng-docs/                  # Engineering docs (ENG-000–ENG-006)
```

## Non-Default Conventions

- **State management:** Zustand (NOT Redux). Stores live in `apps/web/src/stores/`.
- **Backend framework:** FastAPI (NOT Django). Async-first. No Django ORM.
- **CSS approach:** Tailwind CSS utility classes. No CSS modules, no styled-components.
- **Type sharing:** `packages/types/` is the source of truth for API contracts. Frontend and backend types must match.
- **Python services:** NOT managed by Turborepo. Use `make` targets and `pyproject.toml`.
- **Database models:** SQLAlchemy 2.0 declarative (NOT 1.x style). All queries async.
- **LLM abstraction:** LangChain 0.3 `BaseChatModel` for model switching. Never call provider APIs directly.
- **Feature flags:** LaunchDarkly SDK. All new features behind flags. No `if ENV === "production"` guards.
- **Branching:** Trunk-based development. Short-lived feature branches merge to `main`. No `develop` branch.

## Common Gotchas

1. **KaTeX in SSR:** KaTeX components must be dynamically imported with `next/dynamic` and `ssr: false`. Server-side rendering of KaTeX causes hydration mismatches.
2. **Pydantic v2 vs v1:** Use `model_validate()` not `parse_obj()`. Use `model_dump()` not `.dict()`. Field aliases use `alias=` not `alias_generator`.
3. **Auth0 JWT in tests:** Use `conftest.py::mock_jwt_payload` fixture — never make real Auth0 calls in tests.
4. **PostgreSQL ltree:** The `prerequisite_relationships` table uses `ltree` for standard hierarchy paths. Use `@>` and `<@` operators for ancestor/descendant queries.
5. **pyBKT Roster API:** Always use `model.fit(data, forgets=True)` in Stage 3+. Stage 1 uses pre-seeded parameters without fitting.
6. **Turborepo + Python:** `turbo.json` only manages TS packages. Running `pnpm test` does NOT run Python tests. Use `make test-all`.
7. **COPPA middleware guard:** Every endpoint that accesses student data MUST pass through the `verify_consent_active` dependency. Missing this is a P0 compliance bug.
8. **Tailwind v4:** Uses CSS-first configuration (not `tailwind.config.ts`). Design tokens defined in `@theme` blocks in CSS.

## Stage Awareness

MathPath is built in 5 stages over 20 months. Always check which stage is active:
- **Stage 1** (Mo 1–3): Standards DB & Diagnostic Assessment
- **Stage 2** (Mo 4–6): Learning Plan Generator + AI Question Gen
- **Stage 3** (Mo 7–10): Adaptive Practice Engine + LangGraph Tutoring
- **Stage 4** (Mo 11–14): End-of-Grade Assessment + Reporting (MVP)
- **Stage 5** (Mo 15–20): Monetization, School Onboarding, Spanish (MMP)

The current stage determines which components exist, which tests should pass, and which
features are in scope. Do NOT implement features from future stages unless explicitly asked.
See `.claude/skills/sprint-lifecycle/SKILL.md` for the full phase-gate model.

## Rules & Skills

Domain-specific rules auto-load based on the files being edited:
- Frontend conventions → `.claude/rules/frontend-rules.md`
- Backend conventions → `.claude/rules/backend-rules.md`
- Agent patterns → `.claude/rules/agent-rules.md`
- Testing standards → `.claude/rules/test-rules.md`
- Infrastructure → `.claude/rules/infra-rules.md`
- Design system → `.claude/rules/design-system-rules.md`
- Database patterns → `.claude/rules/database-rules.md`
- COPPA compliance → `.claude/rules/coppa-rules.md`

Skills provide deep expertise on demand. Key skills:
- `mathpath-design-tokens` — Color, typography, spacing token enforcement
- `mathpath-test-coverage` — Testing pyramid and coverage gates
- `security-coppa-compliance` — COPPA + OWASP compliance checks
- `sprint-lifecycle` — 7-phase SDLC gate enforcement
- `bkt-model-patterns` — pyBKT implementation patterns
- `langgraph-agent-patterns` — Multi-agent orchestration

## Documentation Suite

24 specification documents live in `docs/` and `eng-docs/`. Use `/custom:spec-search` to
find requirements. Key docs: Doc 03 (PRD), Doc 09 (Design System), LC-001–LC-005
(Lifecycle), ENG-000 (Foundations), OPS-000 (Cross-Cutting Ops), Doc 16 (Multi-Grade).
```

**Line count: 148 lines** — within the recommended <200 line limit for CLAUDE.md files.

---

## 5. Modular Rule Files

Rule files live in `.claude/rules/` and auto-load based on `globs:` frontmatter when Claude edits files matching the specified patterns. Each rule file focuses on a single domain and contains concise, actionable instructions that fit within ~300–600 tokens.

### 5.1 frontend-rules.md

```markdown
---
globs: apps/web/**/*.tsx, apps/web/**/*.ts, packages/ui/**/*.tsx, packages/math-renderer/**/*.tsx
---

# Frontend Rules — MathPath Oregon

## Framework
- React 19 with Next.js 15 App Router. Use Server Components by default; add "use client" only when needed (hooks, event handlers, browser APIs).
- TypeScript strict mode. No `any` types. No `@ts-ignore` without a linked issue.
- Tailwind CSS 4 for all styling. No CSS modules. No styled-components. No inline style objects.

## Component Patterns
- Atomic Design: atoms in `packages/ui/`, molecules and organisms in `apps/web/src/components/`.
- Every component gets its own folder: `ComponentName/index.tsx`, `types.ts`, `ComponentName.test.tsx`.
- Props use TypeScript interfaces (not types) with JSDoc descriptions on each prop.
- Use `forwardRef` for all interactive atoms (Button, Input, Select).

## State Management
- Zustand for client state. One store per domain: `assessment-store.ts`, `session-store.ts`, `preferences-store.ts`.
- No Redux. No React Context for state (Context is for DI only — theme, auth provider).
- Server state via `fetch` in Server Components or React Query for client-side data fetching.

## Imports
- Absolute imports via `@/` alias for `apps/web/src/`.
- Internal packages via `@mathpath/ui`, `@mathpath/math-renderer`, `@mathpath/types`.
- Never import from `apps/api/` — frontend and backend communicate only via HTTP.

## Naming
- Components: PascalCase (`QuestionCard.tsx`).
- Hooks: `use` prefix, camelCase (`useAssessmentState.ts`).
- Stores: kebab-case with `-store` suffix (`assessment-store.ts`).
- Utilities: camelCase (`formatMathExpression.ts`).
- Test files: `ComponentName.test.tsx` colocated in component folder.

## Math Rendering
- All mathematical expressions use KaTeX via `@mathpath/math-renderer`.
- KaTeX components must be dynamically imported: `const MathDisplay = dynamic(() => import("@mathpath/math-renderer").then(m => m.MathDisplay), { ssr: false })`.
- Use `type-math-display` (28px) for block equations, `type-math-inline` (18px) for inline.
- Student input fields for numbers use `type-math-input` (24px JetBrains Mono).

## Performance
- Images: Always use `next/image` with explicit width/height. WebP preferred.
- Fonts: DM Sans and Inter loaded via `next/font/google`. JetBrains Mono for math.
- Bundle: Keep each page under 150KB gzipped JS. Use `@next/bundle-analyzer` to verify.
- Lazy load below-fold components with `React.lazy` + `Suspense`.
```

### 5.2 backend-rules.md

```markdown
---
globs: apps/api/**/*.py, services/**/*.py
---

# Backend Rules — MathPath Oregon

## Framework
- FastAPI 0.115+ with async everywhere. Every route handler is `async def`.
- Pydantic v2 for all request/response models. Use `model_validate()`, `model_dump()`, `ConfigDict`.
- SQLAlchemy 2.0 declarative models with async session factory. No 1.x patterns.
- Alembic for all schema changes. No raw SQL DDL outside migrations.

## Architecture Layers
- **Routes** (`api/v1/*.py`): Thin controllers. Validate input, call service, return response. No business logic.
- **Services** (`service/*.py`): Business logic. Orchestrate repositories. Handle transactions.
- **Repositories** (`repository/*.py`): Data access only. Raw SQLAlchemy queries. No HTTP concerns.
- **Models** (`models/*.py`): Pydantic v2 schemas. Request models, response models, internal DTOs.
- **DB Tables** (`db/tables/*.py`): SQLAlchemy ORM table definitions. Mirror PostgreSQL schema.

## Async Patterns
- Use `async with AsyncSession() as session` for all DB operations.
- Use `asyncio.gather()` for concurrent independent operations (e.g., parallel DB queries).
- Never use `time.sleep()` — use `asyncio.sleep()`.
- LLM calls via `await llm_client.ainvoke()` — never synchronous `.invoke()`.

## Error Handling
- Custom exception hierarchy in `core/exceptions.py`. All exceptions extend `MathPathError`.
- Route handlers catch service exceptions and map to HTTP status codes via exception handlers.
- Never return raw 500 errors. Always structured `ErrorResponse(detail=..., code=...)`.
- Log exceptions with `structlog` — include `request_id`, `user_id`, `student_id` in context.

## Security
- Auth0 JWT validation via `core/security.py::get_current_user` dependency.
- Every student-data endpoint requires `verify_consent_active` dependency.
- PII fields encrypted with pgcrypto AES-256. Never log PII (email, name, IP).
- Rate limiting: 100 req/min per authenticated user. Stricter for auth endpoints.

## Testing
- Fixtures in `tests/conftest.py`. Use `mock_jwt_payload` for auth. `test_db` for isolated DB.
- FastAPI TestClient for integration tests. No real Auth0 calls.
- pytest-asyncio for async test functions. Always `@pytest.mark.asyncio`.

## Naming
- Files: snake_case (`assessment_service.py`).
- Classes: PascalCase (`AssessmentService`).
- Functions/methods: snake_case (`get_next_question`).
- Constants: SCREAMING_SNAKE (`MAX_DIAGNOSTIC_QUESTIONS = 40`).
```

### 5.3 agent-rules.md

```markdown
---
globs: services/agent-engine/**/*.py, services/question-generator/**/*.py
---

# Agent Rules — MathPath Oregon

## Framework
- LangGraph 0.2 for all agent workflows. Graphs defined in `services/agent-engine/src/graphs/`.
- LangChain 0.3 as the LLM abstraction layer. Use `BaseChatModel` interface for model switching.
- State defined as TypedDict classes in `services/agent-engine/src/state/`.

## Graph Patterns
- Every graph has a single entry node and explicit END node.
- State mutations happen only in node functions. Edges are pure routing logic.
- Conditional edges use named functions (not lambdas) for debuggability.
- Use `add_messages` reducer for conversation history in state.
- Checkpointing enabled for all student-facing graphs (assessment, tutoring, practice).

## LLM Provider Rules
- Claude Sonnet 4.6: Tutoring conversations, learning plan generation, report narratives.
- o3-mini: Question generation (better at math reasoning, lower cost).
- GPT-4o: Orchestration, intent classification, content safety filtering.
- Haiku: Quick classification tasks, cost-sensitive operations.
- Never hardcode model names. Use `core/config.py::LLMConfig` with environment-based switching.

> **LLM Routing Update (April 2026 — ADR-009):** For student-facing agent tasks (Tutor Agent, Assessment Agent), always route to `ollama/qwen2.5:72b` or `ollama/qwen2.5:32b` via the `llm_client.get_llm_response(role, messages)` wrapper until COPPA DPAs are confirmed in writing. For question generation (no student PII), Claude Sonnet 4.6 via the `question_gen` role is appropriate. Claude Code agents building the application should never import `anthropic` or `openai` directly in agent/service code — always use the `llm_client` wrapper.

## Prompt Templates
- All prompts are Jinja2 templates in `services/*/prompts/`.
- Version prompts: `{component}_v{MAJOR}.{MINOR}.jinja2` (e.g., `tutor_hint_v1.0.jinja2`).
- Every prompt template must include: system instructions, few-shot examples, output format, safety constraints.
- Math content in prompts uses LaTeX notation wrapped in `$...$` delimiters.

## Tool Definitions
- LangGraph tools are defined in `services/agent-engine/src/tools/`.
- Each tool is a decorated function with docstring, type hints, and error handling.
- Tools that modify state must be idempotent.
- Tools that call external services must have timeout and retry logic.

## Testing
- Node functions tested in isolation with deterministic state fixtures from `tests/fixtures/mock_states.py`.
- Golden input/output pairs in `tests/fixtures/golden_outputs/` for regression testing.
- LLM calls mocked in unit tests. Integration tests use real LLM calls with assertions on structure (not exact text).
- LLM contract tests run weekly via `llm-contract-tests.yml` to catch output schema drift.

## Safety
- All student-facing LLM output passes through the content safety filter node before delivery.
- Filter checks: age-appropriateness, no PII generation, growth mindset language, mathematical accuracy.
- Safety filter failures log to `safety_events` table and block the response.
```

### 5.4 test-rules.md

```markdown
---
globs: **/tests/**/*.py, **/tests/**/*.ts, **/tests/**/*.tsx, **/*.test.ts, **/*.test.tsx, **/*.spec.ts, **/features/**/*.feature
---

# Test Rules — MathPath Oregon

## Testing Pyramid
- **Unit tests (70%):** Isolated component/function tests. Mock all dependencies.
- **Integration tests (20%):** Multi-component interactions. Real DB (test container), mocked external services.
- **E2E tests (10%):** Full user journeys via Playwright. Real browser, real API, test database.

## Coverage Gates
| Layer | Minimum Line Coverage | Enforced By |
|-------|----------------------|-------------|
| Frontend components | 80% | Vitest coverage report |
| Backend services | 80% | pytest-cov |
| BKT engine | 90% | pytest-cov |
| COPPA consent flows | 100% | pytest-cov + CI gate |
| Agent nodes | 75% | pytest-cov |
| E2E critical paths | All P0 stories | Playwright test count |

## Frontend Testing (Vitest + Testing Library)
- Test behavior, not implementation. Query by role, label, or test-id — never by class name.
- Use `@testing-library/user-event` for interactions (not `fireEvent`).
- MSW (Mock Service Worker) for API mocking in integration tests.
- KaTeX components: test that math renders (check for `.katex` class), not the rendered HTML.

## Backend Testing (pytest)
- Fixtures in `conftest.py`: `test_db` (async session), `mock_jwt_payload`, `sample_student`, `sample_assessment`.
- Use `httpx.AsyncClient` with `app=create_app()` for integration tests.
- Always test both success and error paths. Every custom exception must have a test that triggers it.
- BKT tests: Use deterministic response sequences from `fixtures/response_sequences/`.

## E2E Testing (Playwright)
- Page Object Model for all pages. Page objects in `tests/e2e/pages/`.
- Test critical user journeys: registration → consent → child profile → diagnostic → results.
- Visual regression tests for question rendering (KaTeX, fraction builders, number lines).
- Accessibility audit on every page: `await expect(page).toPassAxeTests()`.

## BDD (Gherkin)
- Feature files in `tests/features/*.feature`.
- Step definitions in `tests/features/steps/`.
- Write scenarios from user perspective, not system perspective.
- Use scenario outlines for parameterized tests across grade levels.

## Naming
- Test files: `test_*.py` (Python), `*.test.tsx` (React), `*.spec.ts` (Playwright).
- Test names: `test_<method>_<scenario>_<expected>` (Python), `it("should <behavior> when <condition>")` (TS).
- Feature files: `<epic>_<feature>.feature` (e.g., `diagnostic_assessment.feature`).
```

### 5.5 infra-rules.md

```markdown
---
globs: infrastructure/**/*.tf, infrastructure/**/*.yml, infrastructure/**/*.yaml, .github/workflows/**/*.yml, infrastructure/docker/**
---

# Infrastructure Rules — MathPath Oregon

## Terraform
- Terraform 1.7+ with AWS provider 5.x.
- All resources in modules: `infrastructure/terraform/modules/{ecs,rds,elasticache,s3,cloudfront,secrets,vpc,monitoring}`.
- Environment-specific configs in `infrastructure/terraform/environments/{staging,production}/`.
- Remote state in S3 + DynamoDB lock table. Never local state in production.
- Every resource must have `tags = { Project = "mathpath", Environment = var.environment, ManagedBy = "terraform" }`.
- No inline policies. Use IAM policy documents and attachments.

## Docker
- Multi-stage builds for all Python services. Builder stage installs deps, final stage copies only needed files.
- Base image: `python:3.12-slim` for Python services. `node:20-alpine` for TS builds.
- No `latest` tags. Pin exact image digests in production Dockerfiles.
- `docker-compose.yml` for local dev: Postgres 17, Redis 7, LocalStack (S3 emulation).

## CI/CD (GitHub Actions)
- `ci.yml`: Runs on every PR. Steps: lint → typecheck → unit test → integration test → build.
- `deploy-staging.yml`: Auto-deploy on merge to `main`. Runs full test suite first.
- `deploy-production.yml`: Manual trigger with approval gate. Runs E2E suite on staging first.
- `llm-contract-tests.yml`: Weekly cron. Validates LLM output schemas against Pydantic models.
- `dependency-audit.yml`: Weekly cron. Runs `npm audit`, `pip-audit`, Trivy container scan.

## AWS Resources
- ECS Fargate: 1 vCPU / 2GB per task. Auto-scale 1–10 tasks at 70% CPU. Health check on `/health`.
- RDS PostgreSQL 17: db.t4g.medium, Multi-AZ (prod), encrypted at rest, automated backups 7-day retention.
- ElastiCache Redis 7: cache.t4g.small, TLS in-transit, AUTH token.
- S3: Versioning enabled on model artifacts bucket. Lifecycle rules for log rotation.

## Security
- No secrets in code, environment variables, or CI logs. Use AWS Secrets Manager.
- Security groups: API containers in private subnet, ALB in public subnet, DB in isolated subnet.
- All traffic encrypted in transit (TLS 1.2+). All data encrypted at rest (AES-256).
- WAF on ALB with rate limiting and SQL injection rules.
```

### 5.6 design-system-rules.md

```markdown
---
globs: packages/ui/**/*.tsx, packages/ui/**/*.ts, packages/ui/**/*.css, packages/math-renderer/**/*.tsx, apps/web/src/styles/**/*.css, apps/web/src/components/**/*.tsx
---

# Design System Rules — MathPath Oregon

## Token Enforcement
- ALWAYS use semantic design tokens. NEVER use raw hex values (`#4CAF50`), pixel literals (`16px`), or hardcoded font names.
- Color tokens: `color-bg-primary`, `color-text-body`, `color-accent-primary`, etc. (see Doc 09 §4.1).
- Spacing tokens: `space-1` (4px) through `space-13` (96px). All spacing is multiples of 4px.
- Typography tokens: `type-body-lg` (18px student), `type-display-md` (24px), `type-math-input` (24px JetBrains Mono).
- Load skill `mathpath-design-tokens` for the complete token reference.

## Color Rules
- No red for wrong answers. Use gentle shake animation + neutral feedback color.
- Mastered = teal (`color-accent-mastered`), not green. Green is for momentary "correct" feedback only.
- In-progress = amber (`color-accent-in-progress`). Not started = gray (`color-accent-not-started`).
- Background is always quiet: `color-bg-primary` (neutral-50 light / dark-bg dark).
- Accent color ratio: ≤15% of screen surface should be teal or warm.

## Typography
- Student-facing body text: 18px minimum (`type-body-lg`). Primary reading size for questions.
- Minimum text size: 12px. Only for badges and tertiary labels.
- Math expressions: always JetBrains Mono via `type-math-display` or `type-math-inline`.
- Number rendering: `font-variant-numeric: tabular-nums lining-nums` on all numeric values.
- Line length: 45–65 characters maximum for question text.

## Accessibility (Non-Negotiable)
- WCAG AA minimum. AAA for student-facing content.
- Touch targets: 48×48px minimum for student app. 44×44px minimum for dashboards.
- Color independence: never rely on color alone. Pair with icons (✓, ◐, •).
- Focus visible: 2px teal ring on keyboard focus. No ring on pointer interaction.
- `prefers-reduced-motion`: replace all transforms with instant opacity changes.
- Screen reader: all interactive elements have accessible names. All images have alt text.

## Component Structure (Atomic Design)
- **Atoms** (`packages/ui/`): Button, Input, Badge, ProgressBar, ProgressDot, ProgressRing.
- **Molecules** (`apps/web/src/components/`): QuestionCard, SkillMapNode, KPICard, HintPanel.
- **Organisms** (`apps/web/src/components/`): AssessmentScreen, SkillMap, DashboardHeader, DiagnosticResults.
- **Templates** (`apps/web/src/app/`): Page layouts — StudentLayout, ParentLayout, TeacherLayout.

## Math-Specific UI
- FractionBuilder: Visual drag-and-drop fraction creation. Touch-friendly for tablet.
- NumberLine: Interactive number line with snap-to-value. Range adapts to question.
- MathDisplay: KaTeX block rendering for equations. Centered, 28px.
- MathInput: Number pad or text input with live KaTeX preview. 24px JetBrains Mono.
```

### 5.7 database-rules.md

```markdown
---
globs: apps/api/src/db/**/*.py, apps/api/alembic/**/*.py, apps/api/src/repository/**/*.py, services/bkt-engine/src/repository/**/*.py
---

# Database Rules — MathPath Oregon

## PostgreSQL 17
- Extensions in use: pgvector 0.7, pgcrypto, ltree, pg_trgm.
- Connection: async via asyncpg driver. Session factory in `apps/api/src/db/session.py`.
- Connection pooling: PgBouncer in transaction mode. Pool size 100.

## SQLAlchemy 2.0 Patterns
- Declarative base with `DeclarativeBase` class (NOT legacy `declarative_base()` function).
- Mixins for common columns: `TimestampMixin` (created_at, updated_at), `SoftDeleteMixin`, `AuditMixin`.
- Relationships use `Mapped[]` type annotations. No `relationship()` without explicit type.
- Always use `select()` with `async session.execute()`. No legacy `session.query()` patterns.

## Migrations (Alembic)
- Every schema change requires a migration. No raw DDL.
- Migration naming: `{revision}_{descriptive_slug}.py` (auto-generated revision hash).
- Every migration must have both `upgrade()` and `downgrade()` functions.
- Data migrations (seed data, backfills) are separate from schema migrations.
- Test migrations in CI: `alembic upgrade head` then `alembic downgrade base` must succeed.

## Query Patterns
- Repository methods return domain models (Pydantic), not ORM objects.
- Use `select().where()` with explicit column references. No string-based queries.
- Pagination: cursor-based for student-facing APIs. Offset for admin APIs.
- Soft delete: `deleted_at IS NULL` filter in base repository. Hard delete only for COPPA data deletion.

## PII Handling
- `email_encrypted`: AES-256-CBC via pgcrypto. Encrypted at write, decrypted at read.
- `email_hash`: SHA-256 for lookups without decryption.
- `name_encrypted`: Same pattern. Never store plaintext PII.
- Consent records: append-only. Never UPDATE or DELETE (legal retention).

## Redis Caching
- Assessment CAT state: Redis key `assessment:{id}:state`, TTL 7 days.
- Double-write: every state update writes to both Redis and PostgreSQL.
- Cache invalidation: explicit delete on assessment completion.
- Fallback: if Redis read fails, fall through to PostgreSQL. Log warning, do not error.

## Performance
- All queries must use indexes. No sequential scans on tables > 1,000 rows.
- `EXPLAIN ANALYZE` for any query with JOINs across 3+ tables.
- Batch inserts for bulk operations (question import, seed data). Use `insert().values([...])`.
- The `assessment_responses` table partitions by month starting Stage 3 (1M+ rows expected).
```

### 5.8 coppa-rules.md

```markdown
---
globs: apps/api/src/core/security.py, apps/api/src/service/consent_service.py, apps/api/src/api/v1/auth.py, apps/api/src/api/v1/parents.py, apps/api/src/db/tables/consent.py, apps/api/src/db/tables/audit_log.py, apps/web/src/app/(auth)/**/*.tsx, apps/web/src/app/(onboarding)/**/*.tsx
---

# COPPA Compliance Rules — MathPath Oregon

## Core COPPA Requirements (FTC 2025 Rule Update)
- No PII collection from children under 13 without verifiable parental consent.
- "Verifiable" means email-plus: parent email confirmation with 24-hour revocation window.
- Data minimization: collect only what is strictly necessary for the service.
- Data retention: define explicit retention periods. Delete when no longer needed.
- Parent rights: review child data, request deletion, revoke consent at any time.
- Written information security program documented and maintained.

## Code Enforcement
- Every endpoint accessing `student`, `assessment_responses`, `student_skill_states`, or `learning_plans` tables MUST include the `verify_consent_active` FastAPI dependency.
- The `verify_consent_active` dependency checks: consent record exists, status is "active", consent has not been revoked, student belongs to authenticated parent.
- Adding a new endpoint that touches student data without `verify_consent_active` is a P0 compliance bug. This must trigger an immediate fix.

## PII Rules
- **Never log PII.** Not in application logs, not in error messages, not in Sentry events.
- **Never include PII in LLM prompts.** Student names, parent emails, and school names must be stripped before any LLM call. Use opaque IDs (`student_id: UUID`).
- **Encrypt at rest.** `email_encrypted` and `name_encrypted` use pgcrypto AES-256.
- **Hash for lookups.** `email_hash` (SHA-256) for duplicate detection without decryption.

## Consent Records
- `consent_records` table is append-only. Rows are NEVER updated or deleted.
- Every consent state change (granted, revoked, re-accepted) creates a new row.
- Each row stores: `consent_type`, `privacy_policy_version`, `tos_version`, `consented`, `consented_at`, `ip_address_hash`, `user_agent`, `consent_text_hash`.
- The `audit_log` table records every access to consent records.

## Data Deletion
- On parent deletion request: hard-delete all student PII from `students`, `assessment_responses`, `student_skill_states`, `learning_plans`.
- Retain: `consent_records` (legal requirement), anonymized usage statistics.
- Deletion must complete within 48 hours per FTC guidance.
- Deletion triggers cascade: S3 objects (question response images), Redis cache entries, PostHog anonymization.

## Testing
- 100% test coverage on consent flow. Every branch, every edge case.
- E2E test: full registration → consent → child profile → revocation → data deletion.
- Security test: attempt to access student data without consent → verify 403.
- Security test: attempt to access another parent's child data → verify 403.
```
## 6. Detailed Skill Specifications

Each skill is defined in a `SKILL.md` file within `.claude/skills/<skill-name>/`. The file uses YAML frontmatter for metadata and markdown for instructions. Claude Code scans skill descriptions at session start (~100 tokens each) and loads the full content on demand when relevant.

---

### 6.1 mathpath-design-tokens

**File:** `.claude/skills/mathpath-design-tokens/SKILL.md`

```markdown
---
name: mathpath-design-tokens
description: "Enforces MathPath Oregon design tokens for color, typography, spacing, elevation, border radius, and motion. Validates that all UI code uses semantic tokens from Doc 09 — never raw hex values, pixel literals, or hardcoded font names. Activates when editing .tsx, .css, or Tailwind config files."
allowed-tools: Read Grep Edit Write Bash
---

# MathPath Design Token Enforcement

When generating or editing UI code for MathPath Oregon, enforce these design tokens from the
UI/UX Design System (Doc 09). Every visual property must reference a semantic token — never a
raw value.

## Color Tokens (Semantic Layer)

### Light Mode Mappings
| Semantic Token | Primitive | Hex | Usage |
|----------------|-----------|-----|-------|
| `color-bg-primary` | neutral-50 | #F8F9FA | Page background |
| `color-bg-surface` | neutral-0 | #FFFFFF | Card/container fill |
| `color-bg-surface-alt` | neutral-100 | #F1F3F5 | Secondary surface |
| `color-bg-interactive` | teal-600 | #009199 | Primary button fill |
| `color-bg-interactive-hover` | teal-700 | #007078 | Button hover |
| `color-bg-correct` | green-100 | #D3F9D8 | Correct answer feedback |
| `color-bg-hint` | amber-100 | #FFF3BF | Hint / in-progress feedback |
| `color-bg-error` | red-100 | #FFE3E3 | System errors only |
| `color-text-primary` | neutral-800 | #212529 | Headings, emphasis |
| `color-text-body` | neutral-600 | #495057 | Body copy |
| `color-text-muted` | neutral-500 | #868E96 | Secondary, captions |
| `color-text-on-interactive` | neutral-0 | #FFFFFF | Text on buttons |
| `color-text-link` | teal-600 | #009199 | Links, inline actions |
| `color-border-default` | neutral-200 | #E9ECEF | Dividers, card borders |
| `color-border-interactive` | teal-600 | #009199 | Focused input borders |
| `color-accent-primary` | teal-600 | #009199 | Brand accent |
| `color-accent-warm` | warm-500 | #FF8C00 | Streak, celebration |
| `color-accent-mastered` | teal-600 | #009199 | Mastered skill node |
| `color-accent-in-progress` | amber-500 | #F59F00 | In-progress skill node |
| `color-accent-not-started` | neutral-300 | #DEE2E6 | Not-started skill node |

### Dark Mode Mappings
| Semantic Token | Dark Primitive | Hex |
|----------------|---------------|-----|
| `color-bg-primary` | dark-bg | #1A1B1E |
| `color-bg-surface` | dark-surface | #25262B |
| `color-bg-surface-alt` | dark-surface-alt | #2C2E33 |
| `color-bg-interactive` | teal-500 | #00B2BD |
| `color-text-primary` | dark-text-bright | #E9ECEF |
| `color-text-body` | dark-text | #C1C2C5 |
| `color-text-muted` | dark-text-muted | #909296 |
| `color-border-default` | dark-border | #373A40 |
| `color-accent-primary` | teal-400 | #26BEC7 |

### Color Rules
1. **No red for wrong answers.** Wrong = shake animation + neutral feedback. Red = system errors only.
2. **Mastered = teal, not green.** Green is momentary "correct" feedback.
3. **In-progress = amber.** Not started = gray.
4. **Background = quiet.** `color-bg-primary` always. Never colored backgrounds behind math.
5. **Accent ratio ≤15%.** No more than 15% of any screen surface is teal or warm.

## Typography Tokens

### Student App
| Token | Size | Line Height | Weight | Font | Usage |
|-------|------|-------------|--------|------|-------|
| `type-display-lg` | 32px | 40px | DM Sans 700 | Celebration, hero |
| `type-display-md` | 24px | 32px | DM Sans 700 | Screen titles |
| `type-display-sm` | 20px | 28px | DM Sans 500 | Section headers |
| `type-body-lg` | 18px | 28px | Inter 400 | Question text (PRIMARY student reading size) |
| `type-body-md` | 16px | 24px | Inter 400 | Supporting text |
| `type-body-sm` | 14px | 20px | Inter 400 | Captions, labels |
| `type-label-lg` | 14px | 20px | Inter 600 | Button labels |
| `type-label-sm` | 12px | 16px | Inter 500 | Badges, tags (MINIMUM size) |
| `type-math-display` | 28px | 36px | JetBrains Mono 400 | Block equations |
| `type-math-inline` | 18px | 28px | JetBrains Mono 400 | Inline math |
| `type-math-input` | 24px | 32px | JetBrains Mono 500 | Student answer fields |
| `type-number` | 24px | 32px | Inter 600 | KPI values, counters |

### Parent/Teacher Dashboard
| Token | Size | Line Height | Weight | Usage |
|-------|------|-------------|--------|-------|
| `type-dash-h1` | 28px | 36px | DM Sans 700 | Page title |
| `type-dash-h2` | 20px | 28px | DM Sans 600 | Section header |
| `type-dash-h3` | 16px | 24px | DM Sans 500 | Card title |
| `type-dash-body` | 14px | 22px | Inter 400 | Body text |
| `type-dash-label` | 12px | 16px | Inter 500 | Form labels |
| `type-dash-kpi` | 36px | 44px | DM Sans 700 | KPI values |

## Spacing Tokens (4px Base Grid)

| Token | Value | Usage |
|-------|-------|-------|
| `space-1` | 4px | Icon-label gap |
| `space-2` | 8px | Tight padding, list gap |
| `space-3` | 12px | Inline spacing |
| `space-4` | 16px | Standard padding, form gap |
| `space-5` | 20px | Card padding (small) |
| `space-6` | 24px | Card padding (standard) |
| `space-7` | 32px | Section spacing |
| `space-8` | 40px | Section spacing (large) |
| `space-9` | 48px | Page section breaks |
| `space-10` | 56px | Major separators |
| `space-11` | 64px | Page-level rhythm |
| `space-12` | 80px | Hero spacing |
| `space-13` | 96px | Maximum spacing |

## Elevation Tokens

| Token | Shadow | Usage |
|-------|--------|-------|
| `elevation-0` | none | Flat surfaces |
| `elevation-1` | `0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.06)` | Cards at rest |
| `elevation-2` | `0 4px 6px rgba(0,0,0,0.07), 0 2px 4px rgba(0,0,0,0.06)` | Cards on hover |
| `elevation-3` | `0 10px 15px rgba(0,0,0,0.07), 0 4px 6px rgba(0,0,0,0.05)` | Modals |
| `elevation-4` | `0 20px 25px rgba(0,0,0,0.08), 0 10px 10px rgba(0,0,0,0.04)` | Tooltips |

Student screens: `elevation-0` and `elevation-1` ONLY. Question screen is flat.

## Border Radius Tokens

| Token | Value | Usage |
|-------|-------|-------|
| `radius-sm` | 4px | Tags, chips |
| `radius-md` | 8px | Cards, buttons (DEFAULT) |
| `radius-lg` | 12px | Modals |
| `radius-xl` | 16px | Featured cards |
| `radius-2xl` | 24px | Pill shapes |
| `radius-full` | 9999px | Circles, avatars |

## Motion Tokens

| Token | Duration | Easing | Usage |
|-------|----------|--------|-------|
| `duration-instant` | 100ms | ease-out | Toggle, hover |
| `duration-fast` | 200ms | ease-out | Button press, focus |
| `duration-normal` | 300ms | ease-in-out | Card transitions, answer feedback |
| `duration-slow` | 500ms | ease-in-out | Screen transitions, progress bar |
| `duration-celebration` | 800ms | cubic-bezier(0.34,1.56,0.64,1) | Confetti, badges |

All animations MUST respect `prefers-reduced-motion: reduce`.

## Validation Rules

When reviewing or generating code, flag these violations:
- Raw hex color values (e.g., `bg-[#009199]`) → replace with token
- Hardcoded pixel values in spacing (e.g., `p-[13px]`) → use nearest token
- Font size not from token scale (e.g., `text-[15px]`) → use nearest token
- Missing `prefers-reduced-motion` handling on animations
- Text below 12px minimum
- Student-facing text below 18px
- Numeric values without `tabular-nums lining-nums`
```

---

### 6.2 mathpath-component-library

**File:** `.claude/skills/mathpath-component-library/SKILL.md`

```markdown
---
name: mathpath-component-library
description: "Enforces Atomic Design component patterns for MathPath Oregon. Provides templates for atoms (packages/ui/), molecules, organisms, and templates. Includes math-specific UI component patterns: FractionBuilder, NumberLine, MathDisplay, MathInput."
allowed-tools: Read Grep Edit Write
---

# MathPath Component Library Patterns

## Atomic Design Hierarchy

### Atoms (packages/ui/src/components/)
Stateless, themeable UI primitives. No business logic. No API calls.

**Required structure for each atom:**
```
packages/ui/src/components/Button/
├── index.tsx          # Component implementation with forwardRef
├── types.ts           # Props interface with JSDoc
├── Button.test.tsx    # Unit tests (behavior, not implementation)
└── Button.stories.tsx # Storybook stories (optional, Stage 2+)
```

**Button atom template:**
```tsx
// packages/ui/src/components/Button/index.tsx
import { forwardRef, type ButtonHTMLAttributes } from "react";
import { type ButtonProps } from "./types";

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = "primary", size = "default", isLoading, children, className, ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={cn(
          "inline-flex items-center justify-center font-semibold transition-transform",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-400 focus-visible:ring-offset-2",
          "disabled:opacity-50 disabled:pointer-events-none",
          "active:scale-[0.96]",
          variantStyles[variant],
          sizeStyles[size],
          className
        )}
        disabled={isLoading || props.disabled}
        {...props}
      >
        {isLoading ? <Spinner size={size === "sm" ? 16 : 20} /> : children}
      </button>
    );
  }
);
Button.displayName = "Button";
```

**Student app atoms:** Button, Input, Badge, ProgressBar, ProgressDots, ProgressRing, Avatar, Card, Modal, Tooltip.

### Molecules (apps/web/src/components/)
Composed from atoms. May contain local state. No direct API calls.

**Key molecules:**
- **QuestionCard** — Question text + visual manipulative + answer input area. The most-viewed molecule.
- **SkillMapNode** — Single standard node with mastery ring, label, and status badge.
- **KPICard** — Value + label + delta + optional sparkline.
- **HintPanel** — Slide-up hint with progressive levels (visual → scaffold → tutor chat).
- **AnswerFeedback** — Correct (✓ + green glow) or incorrect (shake animation) overlay.

### Organisms (apps/web/src/components/)
Composed from molecules. May fetch data, manage complex state, handle business logic.

**Key organisms:**
- **AssessmentScreen** — Full question flow: QuestionCard + ProgressDots + navigation + auto-advance.
- **SkillMap** — Interactive grid of SkillMapNodes grouped by math domain.
- **DiagnosticResults** — Results display with skill breakdown charts and gap analysis.
- **DashboardHeader** — Avatar + greeting + KPI cards row.
- **ParentWeeklyDigest** — Activity log + progress summary + action items.

### Templates (apps/web/src/app/)
Page-level layouts that compose organisms into complete screens.

**Templates by context:**
- **StudentLayout** — Tablet-first. Nav bar (56px), content area (centered, max 640px), answer area (bottom third).
- **ParentLayout** — Mobile-first. Header, KPI row, content panels, settings.
- **TeacherLayout** — Desktop-first. Sidebar nav, main content, data tables, heatmaps.

## Math-Specific Components (packages/math-renderer/)

### MathDisplay
Block-level KaTeX rendering. Used for equations that need their own visual space.
- Props: `expression: string` (LaTeX), `size?: "sm" | "md" | "lg"`, `className?: string`
- Size maps: sm=18px, md=24px, lg=28px (uses `type-math-display`)
- Must be dynamically imported: `ssr: false`

### MathInline
Inline KaTeX rendering within text content.
- Props: `expression: string`, `className?: string`
- Uses `type-math-inline` (18px)
- Wraps in `<span>` to sit inline with surrounding text

### MathInput
Number input with live KaTeX preview for student answers.
- Props: `value: string`, `onChange: (value: string) => void`, `placeholder?: string`
- Uses `type-math-input` (24px JetBrains Mono)
- Shows live preview of LaTeX as student types
- Validates input is a valid math expression

### FractionBuilder
Visual drag-and-drop fraction creation tool.
- Props: `onSubmit: (numerator: number, denominator: number) => void`, `maxDenominator?: number`
- Touch-friendly: 48px minimum touch targets
- Visual: divided rectangle or circle showing the fraction
- Haptic feedback on snap (if supported)

### NumberLine
Interactive number line with snap-to-value functionality.
- Props: `min: number`, `max: number`, `step: number`, `onSelect: (value: number) => void`
- Adapts range to question requirements
- Labels at endpoints and key intervals
- Drag or tap to place marker

## Component Conventions

1. Every component folder must contain `index.tsx`, `types.ts`, and a test file.
2. Props interfaces always use JSDoc comments describing each prop.
3. Interactive atoms use `forwardRef` for ref forwarding.
4. All components support `className` prop for Tailwind overrides.
5. Touch targets: 48×48px minimum in student context, 44×44px in dashboard.
6. Focus management: visible focus ring on keyboard navigation, no ring on pointer.
7. All text content supports `prefers-reduced-motion`.
```

---

### 6.3 mathpath-test-coverage

**File:** `.claude/skills/mathpath-test-coverage/SKILL.md`

```markdown
---
name: mathpath-test-coverage
description: "Enforces the MathPath Oregon testing pyramid and coverage gates. Validates unit (70%), integration (20%), and E2E (10%) test distribution. Checks coverage thresholds: 80% services, 90% BKT, 100% COPPA. Provides test patterns for Vitest, pytest, and Playwright."
allowed-tools: Read Grep Bash
---

# MathPath Test Coverage Enforcement

## Testing Pyramid Requirements

| Layer | Target % of Total Tests | Framework | Location |
|-------|------------------------|-----------|----------|
| Unit | 70% | Vitest (frontend), pytest (backend) | `tests/unit/`, `*.test.tsx` |
| Integration | 20% | MSW + Vitest (frontend), TestClient (backend) | `tests/integration/` |
| E2E | 10% | Playwright | `tests/e2e/`, `*.spec.ts` |

## Coverage Gates (CI Enforcement)

| Component | Min Line Coverage | Min Branch Coverage | Failure Action |
|-----------|------------------|--------------------|----|
| `apps/web/src/components/` | 80% | 75% | Block merge |
| `apps/api/src/service/` | 80% | 75% | Block merge |
| `apps/api/src/repository/` | 80% | 75% | Block merge |
| `services/bkt-engine/` | 90% | 85% | Block merge |
| `apps/api/src/core/security.py` | 100% | 100% | Block merge |
| `apps/api/src/service/consent_service.py` | 100% | 100% | Block merge |
| `services/agent-engine/src/nodes/` | 75% | 70% | Warn, allow merge |
| `packages/ui/src/` | 85% | 80% | Block merge |
| `packages/math-renderer/src/` | 85% | 80% | Block merge |

## When Writing Code

After implementing any feature or fixing any bug:
1. Check if tests exist for the modified code.
2. If no tests exist, write them BEFORE marking the task complete.
3. Verify coverage: `pnpm test -- --coverage` (frontend), `make api-test-cov` (backend).
4. If coverage drops below the gate threshold, add tests until it recovers.

## Test Patterns

### Frontend Unit Test (Vitest + Testing Library)
```tsx
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";
import { Button } from "./index";

describe("Button", () => {
  it("should call onClick when pressed", async () => {
    const user = userEvent.setup();
    const handleClick = vi.fn();
    render(<Button onClick={handleClick}>Submit</Button>);

    await user.click(screen.getByRole("button", { name: "Submit" }));

    expect(handleClick).toHaveBeenCalledOnce();
  });

  it("should be disabled when isLoading is true", () => {
    render(<Button isLoading>Submit</Button>);
    expect(screen.getByRole("button")).toBeDisabled();
  });
});
```

### Backend Unit Test (pytest)
```python
import pytest
from unittest.mock import AsyncMock
from src.service.assessment_service import AssessmentService

@pytest.mark.asyncio
async def test_start_assessment_requires_active_consent(
    assessment_service: AssessmentService,
    mock_consent_repo: AsyncMock,
):
    mock_consent_repo.get_active_consent.return_value = None

    with pytest.raises(ConsentRequiredError):
        await assessment_service.start_assessment(
            student_id=uuid4(), assessment_type="diagnostic"
        )

    mock_consent_repo.get_active_consent.assert_called_once()
```

### E2E Test (Playwright)
```typescript
import { test, expect } from "@playwright/test";
import { DiagnosticPage } from "./pages/diagnostic-page";

test("student completes full diagnostic assessment", async ({ page }) => {
  const diagnostic = new DiagnosticPage(page);
  await diagnostic.goto();
  await diagnostic.startAssessment();

  for (let i = 0; i < 25; i++) {
    await diagnostic.answerCurrentQuestion();
    await diagnostic.waitForNextQuestion();
  }

  await expect(diagnostic.completionScreen).toBeVisible();
  await expect(diagnostic.skillMap).toHaveAttribute("data-skills-count", "29");
});
```

## COPPA Test Requirements

The following must have 100% coverage:
- `consent_service.initiate_consent()` — all branches
- `consent_service.confirm_consent()` — valid token, expired token, tampered token, already-used token
- `consent_service.revoke_consent()` — active consent, already-revoked, nonexistent
- `verify_consent_active` dependency — active, revoked, missing, expired
- Data deletion endpoint — full cascade, partial cascade, idempotent re-deletion
```

---

### 6.4 bdd-scenario-writer

**File:** `.claude/skills/bdd-scenario-writer/SKILL.md`

```markdown
---
name: bdd-scenario-writer
description: "Generates Gherkin .feature files from user story acceptance criteria in MathPath lifecycle documents (LC-001 through LC-005). Maps Given/When/Then steps to Playwright step definitions. Activates when creating test scenarios or implementing user stories."
allowed-tools: Read Grep Write
---

# BDD Scenario Writer

## Purpose
Convert user story acceptance criteria from MathPath lifecycle documents into executable
Gherkin scenarios. Each acceptance criterion becomes at least one scenario. Complex criteria
with multiple conditions generate scenario outlines with data tables.

## Source Documents
- LC-001: `docs/10-lifecycle-stage1.md` — Epics 1–5 (Parent Account, Standards DB, Questions, Diagnostic, Results)
- LC-002: `docs/11-lifecycle-stage2.md` — Learning Plan Generator, AI Question Gen
- LC-003: `docs/12-lifecycle-stage3.md` — Adaptive Practice, LangGraph Tutoring
- LC-004: `docs/13-lifecycle-stage4.md` — End-of-Grade Assessment, Reporting
- LC-005: `docs/14-lifecycle-stage5.md` — Monetization, School Onboarding, Spanish

## Output Format
Feature files go in `apps/api/tests/features/` (backend) or `apps/web/tests/features/` (frontend).

```gherkin
# File: apps/api/tests/features/diagnostic_assessment.feature

Feature: Diagnostic Assessment
  As a student starting MathPath Oregon
  I want to complete a diagnostic assessment
  So that MathPath can identify my math strengths and gaps

  Background:
    Given a parent account with active COPPA consent
    And a student profile for "Jayden" in Grade 4
    And the Oregon 4th grade standards are seeded (29 standards)
    And the question bank has at least 3 questions per standard

  Scenario: Start a new diagnostic assessment
    When the parent starts a diagnostic for "Jayden"
    Then a new assessment is created with status "in_progress"
    And the assessment has a Redis cache entry with TTL 7 days
    And the first question targets the lowest-coverage standard

  Scenario: Answer a question correctly adjusts BKT mastery
    Given an active diagnostic assessment for "Jayden"
    And the current P(mastery) for standard "4.OA.A.1" is 0.10
    When "Jayden" answers the current question correctly
    Then P(mastery) for "4.OA.A.1" increases
    And the next question difficulty increases by 1

  Scenario: Complete diagnostic after covering all standards
    Given an active diagnostic with 38 questions answered
    And all 29 standards have been assessed at least once
    When "Jayden" answers the final question
    Then the assessment status changes to "completed"
    And per-skill accuracy is calculated and stored
    And each standard is classified as Below/On/Above Par
    And a "diagnostic_completed" event is published to Redis Streams
    And a results-ready email is sent to the parent

  Scenario Outline: Diagnostic accommodates different accuracy levels
    Given an active diagnostic assessment
    When the student answers with <accuracy>% accuracy on standard <standard>
    Then the standard is classified as "<classification>"

    Examples:
      | accuracy | standard   | classification |
      | 100      | 4.OA.A.1   | Above Par      |
      | 67       | 4.NF.B.3   | On Par         |
      | 33       | 4.GM.A.1   | Below Par      |
      | 0        | 4.NBT.B.4  | Below Par      |
```

## Step Definition Patterns

Map Gherkin steps to implementation in `tests/features/steps/`:

```python
# tests/features/steps/diagnostic_steps.py
from pytest_bdd import given, when, then, parsers

@given("a parent account with active COPPA consent")
async def parent_with_consent(test_db, mock_auth):
    parent = await create_test_parent(test_db)
    await create_active_consent(test_db, parent.id)
    return parent

@when(parsers.parse('the parent starts a diagnostic for "{student_name}"'))
async def start_diagnostic(client, parent_with_consent, student_name):
    student = await get_student_by_name(student_name)
    response = await client.post(
        f"/api/v1/assessments",
        json={"student_id": str(student.id), "type": "diagnostic"},
    )
    assert response.status_code == 201
    return response.json()
```

## Rules
1. Every acceptance criterion from the lifecycle doc generates at least one scenario.
2. Use Background for shared setup (auth, test data, seeded standards).
3. Scenario Outlines for parameterized behavior (grade levels, accuracy ranges).
4. Steps are declarative (user intent), not imperative (click button, fill field).
5. Include negative scenarios: unauthorized access, invalid input, consent revocation.
6. Tag scenarios by epic: `@epic-1`, `@epic-2`, etc.
7. Tag scenarios by priority: `@p0`, `@p1`, `@p2`.
```

---

### 6.5 security-coppa-compliance

**File:** `.claude/skills/security-coppa-compliance/SKILL.md`

```markdown
---
name: security-coppa-compliance
description: "Validates COPPA compliance and OWASP API Security Top 10 for MathPath Oregon. Checks for PII exposure, missing consent guards, data minimization violations, and common API security vulnerabilities. Critical for a children's education platform. Blocks code that collects child PII without consent checks."
allowed-tools: Read Grep Bash Edit
---

# Security & COPPA Compliance Checker

## COPPA Compliance Checklist

### Endpoint Protection
For every API endpoint, verify:

| Check | How to Verify | Severity |
|-------|---------------|----------|
| Student data endpoint has `verify_consent_active` dependency | Grep for route decorator, verify deps list | P0 — Block |
| No PII in response unless necessary | Check response model fields | P0 — Block |
| Student data scoped to authenticated parent | Verify ownership check in service layer | P0 — Block |
| No cross-student data leakage | Verify student_id filtering in repository | P0 — Block |
| Audit log entry on sensitive data access | Check audit_log writes in service | P1 — Warn |

### PII Audit
Scan codebase for PII exposure:

```bash
# Detect potential PII logging
grep -rn "logger\.\(info\|debug\|warning\|error\)" apps/api/src/ | grep -i "email\|name\|address\|phone"

# Detect PII in LLM prompts
grep -rn "student\.name\|student\.email\|parent\.email" services/*/src/prompts/

# Detect raw PII in error messages
grep -rn "raise.*email\|raise.*name" apps/api/src/

# Verify encryption on PII columns
grep -rn "Column.*String" apps/api/src/db/tables/ | grep -v "encrypted\|hash\|_id\|_type\|_status\|_code"
```

### Data Minimization
- Only collect data strictly necessary for the service.
- Student profile: first name (for personalization), grade (for standards), avatar choice. NO last name, NO date of birth, NO school address.
- Session data: question responses (for BKT), time spent (for engagement). NO IP address stored, NO device fingerprint.
- Analytics: aggregate and anonymized. NO individual student tracking in PostHog.

### Data Retention & Deletion
- Assessment data: retained for 3 years or until parent requests deletion.
- Session logs: 90 days, then purged.
- Consent records: retained indefinitely (legal requirement, even after deletion).
- On deletion: hard-delete from `students`, `assessment_responses`, `student_skill_states`, `learning_plans`. Cascade to Redis, S3, PostHog.

## OWASP API Security Top 10 Checks

| # | Vulnerability | MathPath Defense | Verification |
|---|--------------|-----------------|-------------|
| API1 | Broken Object Level Authorization | Ownership check in every repository query: `WHERE student.parent_id = current_user.id` | Review repo queries |
| API2 | Broken Authentication | Auth0 JWT with RS256 + JWKS rotation. Token refresh in secure httpOnly cookies | Check middleware |
| API3 | Broken Object Property Level Authorization | Pydantic response models exclude sensitive fields. `response_model_exclude` on routes | Check response models |
| API4 | Unrestricted Resource Consumption | Rate limiting: 100 req/min per user. Max request body 1MB. Assessment pagination max 50 | Check middleware config |
| API5 | Broken Function Level Authorization | Role-based access: student, parent, teacher, admin. Route-level role checks | Check deps |
| API6 | Unrestricted Access to Sensitive Business Flows | Assessment start limited to 1 active per student. Consent flow rate-limited | Check service logic |
| API7 | Server Side Request Forgery | No user-supplied URLs fetched. LLM prompts sanitized for injection | Review LLM inputs |
| API8 | Security Misconfiguration | CORS allowlist (no wildcard). Debug mode off in production. Error messages sanitized | Check config |
| API9 | Improper Inventory Management | OpenAPI spec auto-generated. No shadow endpoints | Check route registration |
| API10 | Unsafe Consumption of APIs | Auth0 JWKS validated. LLM responses parsed via Pydantic before use | Check integrations |

## Content Safety (Student-Facing LLM Output)

All LLM-generated content shown to students must pass through the content safety filter:
1. No PII in generated text (student names, locations, real people).
2. Age-appropriate language (Flesch-Kincaid Grade Level ≤ student grade + 1).
3. Growth mindset framing (no "wrong", "failed", "bad"). Use "not quite", "let's try another way".
4. Mathematical accuracy validation (generated answers must be computationally verified).
5. No culturally insensitive content. No gender stereotypes in word problem contexts.
```

---

### 6.6 sprint-lifecycle

**File:** `.claude/skills/sprint-lifecycle/SKILL.md`

```markdown
---
name: sprint-lifecycle
description: "Enforces the 7-phase SDLC gate for MathPath Oregon: PRD → Design → Architecture → Implement → Test → QA → Ops. Validates entry/exit criteria for each phase. Prevents skipping phases. Maps to the 5-stage development plan (Months 1–20)."
disable-model-invocation: true
allowed-tools: Read Grep
---

# Sprint Lifecycle Gate Enforcement

## The 7-Phase SDLC Model

Every feature in MathPath follows this lifecycle. Phases are sequential gates — a feature
cannot advance to the next phase until the current phase's exit criteria are met.

```
PRD → Design → Architecture → Implement → Test → QA → Ops
 │       │          │             │          │      │     │
 │       │          │             │          │      │     └─ Monitoring, runbooks
 │       │          │             │          │      └─ Manual testing, UAT
 │       │          │             │          └─ Automated tests pass
 │       │          │             └─ Code written and reviewed
 │       │          └─ ADR, data model, API design
 │       └─ UI mockups, token mapping, component spec
 └─ User stories, acceptance criteria, priority
```

## Phase Entry/Exit Criteria

### Phase 1: PRD (Product Requirements)
**Entry:** Feature is prioritized in the stage backlog.
**Deliverables:**
- User stories with acceptance criteria (Given/When/Then)
- Priority classification (P0–P3)
- Story point estimates
- Dependencies identified
**Exit:** All stories reviewed and approved. No ambiguous acceptance criteria.
**Source:** Lifecycle documents LC-001 through LC-005.

### Phase 2: Design
**Entry:** PRD phase complete.
**Deliverables:**
- Figma mockups for all new screens/components
- Design token mapping (which tokens apply to which elements)
- Component specification (new atoms, molecules, organisms needed)
- Responsive breakpoint behavior
- Animation specifications with duration tokens
- Accessibility annotations (focus order, ARIA labels, contrast verification)
**Exit:** Design reviewed against Doc 09 design system. All tokens mapped.

### Phase 3: Architecture
**Entry:** Design phase complete.
**Deliverables:**
- ADR for any significant technical decisions
- Data model changes (Alembic migration plan)
- API endpoint design (OpenAPI draft)
- Sequence diagrams for complex flows
- Integration point identification
- Performance budget (latency targets per endpoint)
**Exit:** Architecture reviewed. ADRs approved. Migration plan validated.

### Phase 4: Implement
**Entry:** Architecture phase complete.
**Deliverables:**
- Working code implementing all acceptance criteria
- Code passes linting (ESLint, Ruff, mypy)
- Code passes type checking (TypeScript strict, mypy)
- Design tokens used correctly (no raw values)
- COPPA compliance verified (consent guards present)
**Exit:** Code compiles, lints, type-checks. Self-review complete.

### Phase 5: Test
**Entry:** Implementation complete.
**Deliverables:**
- Unit tests for all new code (meeting coverage gates)
- Integration tests for service interactions
- E2E tests for P0 user journeys
- BDD scenarios matching acceptance criteria
- LLM contract tests for any new prompts
- Security tests for new endpoints
**Exit:** All tests pass. Coverage gates met. No P0 test gaps.

### Phase 6: QA
**Entry:** All automated tests pass.
**Deliverables:**
- Manual testing of happy path and edge cases
- Cross-browser testing (Chrome, Safari, Firefox on iPad/Chromebook/iPhone)
- Accessibility manual audit (keyboard navigation, screen reader)
- Performance check against latency targets
- Visual regression check against Figma mockups
**Exit:** No P0/P1 bugs open. Manual QA checklist signed off.

### Phase 7: Ops
**Entry:** QA complete.
**Deliverables:**
- Feature flag configured in LaunchDarkly
- Monitoring alerts configured (CloudWatch, Sentry)
- Runbook updated if new operational procedures needed
- Database migration tested in staging
- Rollback plan documented
**Exit:** Feature deployed to staging. Smoke test passes. Ready for production.

## Stage-Phase Matrix

| Stage | Months | Focus | Key Epics |
|-------|--------|-------|-----------|
| 1 | 1–3 | Standards DB & Diagnostic | Parent Account, Standards, Questions, Diagnostic, Results |
| 2 | 4–6 | Learning Plan + Question Gen | Learning Plans, AI Question Generation, Content Review |
| 3 | 7–10 | Practice + Tutoring | Adaptive Practice, LangGraph Tutoring, Real-time WebSocket |
| 4 | 11–14 | Assessment + Reporting (MVP) | End-of-Grade Assessment, IRT/CAT, Parent/Teacher Reports |
| 5 | 15–20 | Monetization + Scale (MMP) | Stripe Billing, School Onboarding, Spanish Localization |

## Enforcement

When implementing a feature:
1. Identify the current lifecycle phase.
2. Verify all prior phase exit criteria are met.
3. Do not skip phases. If asked to "just code it", first verify that PRD, Design, and Architecture are complete.
4. If a phase is incomplete, identify what is missing and address it before proceeding.
```

---

### 6.7 user-story-tracker

**File:** `.claude/skills/user-story-tracker/SKILL.md`

```markdown
---
name: user-story-tracker
description: "Tracks implementation progress against user stories from MathPath lifecycle documents (LC-001 through LC-005). Maps code changes to story acceptance criteria and reports completion status. Use with /custom:story-status command."
disable-model-invocation: true
allowed-tools: Read Grep
---

# User Story Tracker

## Purpose
Map code implementations to user story acceptance criteria and track progress.
Every code change should trace back to a user story ID (US-X.Y format).

## Story Registry

### Stage 1 Stories (LC-001)
| Epic | ID Range | Stories | Total Points |
|------|----------|---------|-------------|
| Epic 1: Parent Account & COPPA | US-1.1 – US-1.10 | 10 | 55 |
| Epic 2: Oregon Standards DB | US-2.1 – US-2.8 | 8 | 42 |
| Epic 3: Seed Question Bank | US-3.1 – US-3.7 | 7 | 39 |
| Epic 4: Diagnostic Assessment | US-4.1 – US-4.10 | 10 | 63 |
| Epic 5: Results & Gap Analysis | US-5.1 – US-5.6 | 6 | 34 |
| **Stage 1 Total** | | **41** | **233** |

## Tracking Methodology

### Acceptance Criteria Mapping
For each story, map acceptance criteria to code artifacts:

```
US-1.3 — COPPA Consent Multi-Step Form
├── AC-1: Plain-language privacy summary → apps/web/src/app/(onboarding)/consent/page.tsx
├── AC-2: Two separate checkboxes → apps/web/src/components/consent/ConsentForm.tsx
├── AC-3: Submit validation → apps/web/src/components/consent/ConsentForm.tsx
├── AC-4: Confirmation email → apps/api/src/service/consent_service.py::initiate_consent()
├── AC-5: Consent record storage → apps/api/src/repository/consent_repo.py::create_consent()
├── AC-6: Audit log → apps/api/src/service/consent_service.py (audit decorator)
├── AC-7: Deletion retention → apps/api/src/service/deletion_service.py (exclude consent)
└── AC-8: Policy re-acceptance → apps/api/src/core/middleware.py (version check)
```

### Status Definitions
| Status | Definition |
|--------|-----------|
| Not Started | No code artifacts exist for this story |
| In Progress | Some acceptance criteria implemented, not all |
| Code Complete | All acceptance criteria implemented, tests pending |
| Test Complete | All tests pass, coverage gates met |
| QA Complete | Manual QA passed, no open P0/P1 bugs |
| Done | Deployed to staging, smoke test passed |

### Progress Reporting
When asked for story status, report:
1. Total stories in the current stage
2. Count by status (Not Started / In Progress / Code Complete / Done)
3. P0 stories completion percentage
4. Blocked stories and blocking reasons
5. Estimated remaining effort

## Commit Convention
All commits reference story IDs:
```
feat(US-1.3): implement COPPA consent multi-step form
test(US-1.3): add 100% coverage tests for consent flow
fix(US-4.7): correct BKT mastery threshold calculation
```
```

---

### 6.8 architecture-enforcer

**File:** `.claude/skills/architecture-enforcer/SKILL.md`

```markdown
---
name: architecture-enforcer
description: "Enforces monorepo boundaries and architectural layering rules from ENG-000. Prevents cross-app imports, validates layer dependencies (routes → services → repositories → DB), and catches business logic in route handlers. Activates when editing code across package boundaries."
allowed-tools: Read Grep Bash
---

# Architecture Enforcer

## Monorepo Boundary Rules

### Import Boundaries
| From | Can Import | Cannot Import |
|------|-----------|---------------|
| `apps/web/` | `packages/*`, external deps | `apps/api/`, `services/*` |
| `apps/api/` | `services/*` (via HTTP or direct import), external deps | `apps/web/`, `packages/ui/`, `packages/math-renderer/` |
| `services/agent-engine/` | `services/bkt-engine/` (via import), external deps | `apps/*`, `packages/ui/` |
| `services/bkt-engine/` | external deps only | `apps/*`, `packages/*`, other `services/*` |
| `services/question-generator/` | external deps only | `apps/*`, `packages/*` |
| `packages/ui/` | `packages/types/`, external React deps | `apps/*`, `services/*`, `packages/math-renderer/` |
| `packages/math-renderer/` | `packages/types/`, KaTeX | `apps/*`, `services/*`, `packages/ui/` |
| `packages/types/` | external deps only | Everything else |
| `infrastructure/` | N/A (Terraform, Docker, scripts) | All application code |

### Layer Dependency Rules (Backend)
```
Routes (api/v1/*.py)
  └── Services (service/*.py)
       └── Repositories (repository/*.py)
            └── DB Tables (db/tables/*.py)
```

**Violations to detect:**
- Route handler containing business logic (conditionals, calculations, multi-step operations).
- Route handler directly accessing repositories (skipping service layer).
- Service directly executing SQL queries (skipping repository layer).
- Repository importing from service layer (circular dependency).
- Any layer importing from route layer.

### Validation Script

```bash
#!/bin/bash
# .claude/skills/architecture-enforcer/validate-boundaries.sh
# Check for common boundary violations

echo "=== Checking import boundaries ==="

# Frontend importing from backend
if grep -rn "from.*apps/api" apps/web/src/; then
  echo "VIOLATION: Frontend importing from backend"
  exit 1
fi

# Backend importing from frontend
if grep -rn "from.*apps/web\|from.*packages/ui\|from.*packages/math-renderer" apps/api/src/; then
  echo "VIOLATION: Backend importing from frontend packages"
  exit 1
fi

# Route handlers with business logic patterns
echo "=== Checking route handler complexity ==="
for file in apps/api/src/api/v1/*.py; do
  # Count lines between route decorator and return
  complex_routes=$(python3 -c "
import ast, sys
with open('$file') as f:
    tree = ast.parse(f.read())
for node in ast.walk(tree):
    if isinstance(node, ast.AsyncFunctionDef):
        body_len = len(node.body)
        if body_len > 10:
            print(f'  WARNING: {node.name} in $file has {body_len} statements (max 10)')
")
  if [ -n "$complex_routes" ]; then
    echo "$complex_routes"
  fi
done

# Repository importing from service
if grep -rn "from.*service\." apps/api/src/repository/; then
  echo "VIOLATION: Repository importing from service layer"
  exit 1
fi

echo "=== Architecture check complete ==="
```

## Monorepo Workspace Rules

- TypeScript packages use `workspace:*` protocol for internal dependencies.
- Python services are NOT in the Turborepo task graph. Use `make` targets.
- Shared types between frontend and backend go in `packages/types/`.
- Never duplicate type definitions. One source of truth per type.
- Database schema types in `packages/db-schema/` must mirror `apps/api/src/db/tables/`.

## Naming Conventions

| Artifact | Convention | Example |
|----------|-----------|---------|
| TS packages | `@mathpath/<name>` | `@mathpath/ui`, `@mathpath/types` |
| Python services | `services/<name>/` | `services/bkt-engine/` |
| API routes | `/api/v1/<resource>` | `/api/v1/assessments` |
| DB tables | snake_case plural | `assessment_responses` |
| Alembic migrations | auto-generated hash | `a1b2c3d4_add_standards_table.py` |
| ADRs | `ADR-{NNN}-{slug}.md` | `ADR-009-redis-caching.md` |
```
### 6.9 bkt-model-patterns

**File:** `.claude/skills/bkt-model-patterns/SKILL.md`

```markdown
---
name: bkt-model-patterns
description: "Provides pyBKT implementation patterns for MathPath Oregon: parameter initialization from research baselines, Roster API usage, mastery threshold configuration, calibration routines, and integration with the diagnostic question selection engine. Domain-specific knowledge for Bayesian Knowledge Tracing in educational technology."
allowed-tools: Read Grep Write Edit
---

# BKT Model Patterns for MathPath Oregon

## Overview
Bayesian Knowledge Tracing (BKT) estimates the probability that a student has mastered a skill
based on their sequence of correct/incorrect responses. MathPath uses pyBKT 1.4 as the core
library with custom extensions for per-student priors, real-time mastery updates, and
integration with the question selection engine.

## Core BKT Parameters

Each skill (Oregon math standard) has four parameters:

| Parameter | Symbol | Description | Range |
|-----------|--------|-------------|-------|
| P(L₀) | Prior knowledge | Probability student knew skill before instruction | 0.0–1.0 |
| P(T) | Learn rate | Probability of learning skill after each opportunity | 0.0–1.0 |
| P(G) | Guess rate | Probability of correct answer despite not knowing | 0.0–0.4 |
| P(S) | Slip rate | Probability of incorrect answer despite knowing | 0.0–0.3 |

## Default Parameter Sets (Research Baselines)

### Stage 1: Pre-calibration Defaults
Before calibration data is available, use these research-validated defaults:

```python
# services/bkt-engine/src/engine/defaults.py

BKT_DEFAULTS = {
    # Category: Procedural skills (addition, subtraction, multiplication)
    "procedural": {
        "prior": 0.20,   # Low prior — assume students need instruction
        "learn": 0.15,   # Moderate learning rate
        "guess": 0.25,   # Multiple choice → ~25% guess rate
        "slip": 0.10,    # Low slip — procedural errors are rare once mastered
    },
    # Category: Conceptual skills (fractions, place value understanding)
    "conceptual": {
        "prior": 0.10,   # Very low prior — conceptual understanding develops slowly
        "learn": 0.10,   # Slower learning rate for concepts
        "guess": 0.20,   # Lower guess rate — conceptual questions are harder to guess
        "slip": 0.15,    # Higher slip — conceptual understanding can be fragile
    },
    # Category: Application skills (word problems, multi-step)
    "application": {
        "prior": 0.05,   # Lowest prior — application requires both procedural and conceptual
        "learn": 0.08,   # Slowest learning rate
        "guess": 0.15,   # Low guess rate — hard to guess multi-step problems
        "slip": 0.20,    # Highest slip — many opportunities for error
    },
}

# Standard-to-category mapping (Grade 4 examples)
STANDARD_CATEGORIES = {
    "4.OA.A.1": "application",    # Multi-step word problems
    "4.OA.A.2": "application",    # Multiplicative comparison
    "4.OA.B.4": "procedural",     # Factor pairs, prime/composite
    "4.NBT.A.1": "conceptual",    # Place value understanding
    "4.NBT.B.4": "procedural",    # Multi-digit addition/subtraction
    "4.NBT.B.5": "procedural",    # Multi-digit multiplication
    "4.NF.A.1": "conceptual",     # Equivalent fractions
    "4.NF.B.3": "procedural",     # Add/subtract fractions (same denom)
    "4.NF.C.6": "procedual",      # Decimal notation for fractions
    "4.GM.A.1": "conceptual",     # Angle measurement
    "4.GM.B.4": "application",    # Area and perimeter problems
    "4.DR.A.1": "procedural",     # Line plots with fractions
    # ... remaining standards follow same pattern
}
```

### Diagnostic-Informed Priors (Post-Assessment)
After the diagnostic assessment, update P(L₀) based on diagnostic accuracy:

```python
# services/bkt-engine/src/engine/tracker.py

def compute_diagnostic_prior(
    diagnostic_accuracy: float,
    standard_category: str,
) -> float:
    """
    Map diagnostic accuracy to BKT prior P(L₀).

    Buckets:
    - 0–33% accuracy → P(L₀) = category default × 0.5 (below par)
    - 34–66% accuracy → P(L₀) = category default × 1.0 (on par)
    - 67–100% accuracy → P(L₀) = category default × 2.5 (above par), capped at 0.85
    """
    base = BKT_DEFAULTS[standard_category]["prior"]

    if diagnostic_accuracy <= 0.33:
        return max(0.01, base * 0.5)
    elif diagnostic_accuracy <= 0.66:
        return base
    else:
        return min(0.85, base * 2.5)
```

## Mastery Threshold Configuration

```python
# services/bkt-engine/src/engine/thresholds.py

MASTERY_THRESHOLDS = {
    "mastered": 0.90,       # P(mastery) ≥ 0.90 → skill mastered
    "in_progress": 0.50,    # 0.50 ≤ P(mastery) < 0.90 → working on it
    "not_started": 0.50,    # P(mastery) < 0.50 → needs instruction
    "prerequisite_gap": 0.30,  # P(mastery) < 0.30 for a prerequisite → flag gap
}

# Minimum observations before trusting BKT estimate
MIN_OBSERVATIONS = {
    "mastery_declaration": 5,  # Need at least 5 responses before declaring mastery
    "gap_declaration": 3,      # Need at least 3 responses before flagging a gap
}
```

## pyBKT Integration Patterns

### Initializing a Model
```python
from pyBKT.models import Model

def create_bkt_model(skill_params: dict) -> Model:
    """Create a pyBKT model with MathPath parameters."""
    model = Model(seed=42, num_fits=5)
    model.coef_ = {
        "default": {
            "prior": skill_params["prior"],
            "learns": [skill_params["learn"]],
            "guesses": [skill_params["guess"]],
            "slips": [skill_params["slip"]],
            "forgets": [0.01],  # Low forget rate
        }
    }
    return model
```

### Updating Mastery (Real-time)
```python
async def update_mastery(
    student_id: UUID,
    standard_code: str,
    is_correct: bool,
    current_state: MasteryState,
) -> MasteryState:
    """
    Update BKT mastery estimate after a student response.
    Uses the forward algorithm for O(1) per-response updates.
    """
    params = await load_skill_params(standard_code)

    # Forward algorithm
    p_known = current_state.p_mastery

    if is_correct:
        p_correct_given_known = 1 - params["slip"]
        p_correct_given_unknown = params["guess"]
    else:
        p_correct_given_known = params["slip"]
        p_correct_given_unknown = 1 - params["guess"]

    # Posterior after observing response
    numerator = p_known * p_correct_given_known
    denominator = numerator + (1 - p_known) * p_correct_given_unknown
    p_known_posterior = numerator / denominator if denominator > 0 else p_known

    # Learning transition
    p_mastery_new = p_known_posterior + (1 - p_known_posterior) * params["learn"]

    return MasteryState(
        student_id=student_id,
        standard_code=standard_code,
        p_mastery=p_mastery_new,
        total_responses=current_state.total_responses + 1,
        correct_responses=current_state.correct_responses + (1 if is_correct else 0),
        updated_at=datetime.utcnow(),
    )
```

## Integration with Question Selection

The BKT mastery estimate drives question difficulty selection:

```python
# services/bkt-engine/src/service/mastery_service.py

def select_difficulty(p_mastery: float) -> int:
    """
    Map mastery probability to question difficulty (1–5 scale).
    Target the zone of proximal development: not too easy, not too hard.
    """
    if p_mastery < 0.20:
        return 1  # Foundational
    elif p_mastery < 0.40:
        return 2  # Building
    elif p_mastery < 0.65:
        return 3  # Developing
    elif p_mastery < 0.85:
        return 4  # Proficient
    else:
        return 5  # Advanced (challenge problems)
```

## Testing BKT

- Use deterministic response sequences from `tests/fixtures/response_sequences/`.
- Verify monotonic mastery increase for all-correct sequences.
- Verify mastery stays below threshold for all-incorrect sequences.
- Verify guess rate prevents mastery from spiking on a few lucky guesses.
- Edge case: verify behavior at P(mastery) = 0.0 and P(mastery) = 1.0.
```

---

### 6.10 langgraph-agent-patterns

**File:** `.claude/skills/langgraph-agent-patterns/SKILL.md`

```markdown
---
name: langgraph-agent-patterns
description: "Multi-agent orchestration patterns for LangGraph 0.2 in MathPath Oregon. Covers graph definition, TypedDict state schemas, node implementations, conditional edges, tool definitions, checkpointing, and LLM provider abstraction. Used for tutoring, diagnostic, and learning plan agent workflows."
allowed-tools: Read Grep Write Edit
---

# LangGraph Agent Patterns for MathPath Oregon

## Agent Architecture

MathPath uses three primary LangGraph graphs:

| Graph | Location | LLM | Purpose | Stage |
|-------|----------|-----|---------|-------|
| `diagnostic_graph` | `services/agent-engine/src/graphs/diagnostic_graph.py` | N/A (rule-based) | Orchestrate diagnostic assessment flow | 1 |
| `plan_graph` | `services/agent-engine/src/graphs/plan_graph.py` | Claude Sonnet 4.6 | Generate personalized learning plans | 2 |
| `tutor_graph` | `services/agent-engine/src/graphs/tutor_graph.py` | Claude Sonnet 4.6 | Interactive tutoring conversations | 3 |

## State Schema Pattern

Every graph state is a TypedDict with Annotated fields for reducers:

```python
# services/agent-engine/src/state/tutor_state.py
from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

class TutorState(TypedDict):
    """State for the tutoring conversation graph."""

    # Conversation history (append-only via add_messages reducer)
    messages: Annotated[list[BaseMessage], add_messages]

    # Student context (set once at session start)
    student_id: str
    grade: int
    current_standard: str
    current_question_id: str
    p_mastery: float

    # Session tracking (updated by nodes)
    hint_level: int                # 0=none, 1=visual, 2=scaffold, 3=tutor_chat
    attempts: int                  # Number of attempts on current question
    is_correct: bool | None        # Latest answer correctness
    should_advance: bool           # Whether to move to next question
    safety_flag: bool              # Content safety violation detected

    # Working memory (ephemeral per question)
    student_response: str          # Raw student input
    feedback_text: str             # Generated feedback to display
    hint_text: str                 # Generated hint text
```

## Graph Definition Pattern

```python
# services/agent-engine/src/graphs/tutor_graph.py
from langgraph.graph import StateGraph, END
from .state.tutor_state import TutorState

def create_tutor_graph() -> StateGraph:
    """Build the tutoring conversation graph."""

    graph = StateGraph(TutorState)

    # Add nodes
    graph.add_node("classify_intent", classify_intent_node)
    graph.add_node("evaluate_response", evaluate_response_node)
    graph.add_node("generate_hint", generate_hint_node)
    graph.add_node("generate_feedback", generate_feedback_node)
    graph.add_node("update_mastery", update_mastery_node)
    graph.add_node("safety_filter", safety_filter_node)

    # Set entry point
    graph.set_entry_point("classify_intent")

    # Add edges
    graph.add_conditional_edges(
        "classify_intent",
        route_intent,
        {
            "answer_submitted": "evaluate_response",
            "hint_requested": "generate_hint",
            "question_asked": "generate_feedback",
        },
    )
    graph.add_edge("evaluate_response", "update_mastery")
    graph.add_conditional_edges(
        "update_mastery",
        route_after_evaluation,
        {
            "correct_advance": "generate_feedback",
            "incorrect_hint": "generate_hint",
            "incorrect_scaffold": "generate_hint",
            "mastered": "generate_feedback",
        },
    )
    graph.add_edge("generate_hint", "safety_filter")
    graph.add_edge("generate_feedback", "safety_filter")
    graph.add_conditional_edges(
        "safety_filter",
        route_safety,
        {
            "safe": END,
            "unsafe": "generate_feedback",  # Regenerate with safety constraints
        },
    )

    return graph.compile(checkpointer=MemorySaver())
```

## Node Implementation Pattern

```python
# services/agent-engine/src/nodes/evaluate_response.py
from langchain_core.messages import AIMessage
from ..state.tutor_state import TutorState

async def evaluate_response_node(state: TutorState) -> dict:
    """
    Evaluate the student's response for correctness.
    Uses the question's expected answer for deterministic evaluation,
    with LLM fallback for free-response questions.
    """
    question = await get_question(state["current_question_id"])
    student_response = state["student_response"]

    # Deterministic evaluation for structured answers
    if question.answer_type in ("multiple_choice", "numeric"):
        is_correct = evaluate_deterministic(student_response, question.correct_answer)
    else:
        # LLM evaluation for free-response
        is_correct = await evaluate_with_llm(student_response, question)

    return {
        "is_correct": is_correct,
        "attempts": state["attempts"] + 1,
        "messages": [
            AIMessage(content=f"Response evaluated: {'correct' if is_correct else 'incorrect'}")
        ],
    }
```

## Conditional Edge Pattern

```python
# services/agent-engine/src/graphs/tutor_graph.py

def route_after_evaluation(state: TutorState) -> str:
    """Route based on evaluation result and mastery state."""
    if state["is_correct"]:
        if state["p_mastery"] >= 0.90:
            return "mastered"
        return "correct_advance"
    else:
        if state["attempts"] >= 3:
            return "incorrect_scaffold"  # Show worked solution after 3 attempts
        return "incorrect_hint"
```

## LLM Provider Abstraction

Never hardcode model names. Use the configuration system:

```python
# services/agent-engine/src/core/llm_client.py
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI

def get_llm(purpose: str) -> BaseChatModel:
    """Get the appropriate LLM for the given purpose."""
    config = LLMConfig.from_env()

    model_map = {
        "tutoring": ChatAnthropic(model=config.tutor_model, temperature=0.3),
        "question_gen": ChatOpenAI(model=config.question_gen_model, temperature=0.7),
        "orchestration": ChatOpenAI(model=config.orchestration_model, temperature=0.1),
        "classification": ChatAnthropic(model=config.classification_model, temperature=0.0),
        "safety_filter": ChatAnthropic(model=config.safety_model, temperature=0.0),
    }
    return model_map[purpose]
```

## Checkpointing

All student-facing graphs MUST use checkpointing for session recovery:
- Diagnostic graph: checkpoint after every question response.
- Tutor graph: checkpoint after every student message.
- Plan graph: checkpoint after each plan section generation.
- Store checkpoints in Redis with PostgreSQL fallback.

## Testing Agent Graphs

1. Unit test each node in isolation with mock state.
2. Test conditional edges with all possible state combinations.
3. Integration test full graph execution with mock LLM.
4. Golden output tests: fixed input states → expected output states.
5. Contract tests: verify LLM output structure matches Pydantic models.
```

---

### 6.11 api-contract-enforcement

**File:** `.claude/skills/api-contract-enforcement/SKILL.md`

```markdown
---
name: api-contract-enforcement
description: "Validates OpenAPI specification consistency with Pydantic v2 models and TypeScript types. Ensures frontend types in packages/types/ mirror backend FastAPI route schemas. Catches contract drift before it becomes a runtime error."
allowed-tools: Read Grep Bash
---

# API Contract Enforcement

## The Contract Chain

```
FastAPI Route (Pydantic v2 models) → OpenAPI spec (auto-generated) → TypeScript types (packages/types/)
```

All three MUST be consistent. A mismatch at any point causes runtime errors.

## Pydantic v2 Model Patterns

### Request Models
```python
# apps/api/src/models/assessment.py
from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID

class StartAssessmentRequest(BaseModel):
    model_config = ConfigDict(strict=True)

    student_id: UUID = Field(..., description="UUID of the student to assess")
    assessment_type: Literal["diagnostic", "practice", "end_of_grade"] = Field(
        ..., description="Type of assessment to start"
    )
```

### Response Models
```python
class AssessmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    student_id: UUID
    assessment_type: str
    status: Literal["in_progress", "completed", "abandoned"]
    created_at: datetime
    total_questions: int
    questions_answered: int
```

## TypeScript Type Mirroring

For every Pydantic response model, there MUST be a matching TypeScript interface:

```typescript
// packages/types/src/assessment.ts
export interface AssessmentResponse {
  id: string;           // UUID serialized as string
  studentId: string;    // camelCase in TS, snake_case in Python
  assessmentType: "diagnostic" | "practice" | "end_of_grade";
  status: "in_progress" | "completed" | "abandoned";
  createdAt: string;    // ISO 8601 datetime string
  totalQuestions: number;
  questionsAnswered: number;
}
```

## Validation Rules

1. Every FastAPI route with a response_model MUST have a matching TS interface in `packages/types/`.
2. Field names: Python uses snake_case, TypeScript uses camelCase. Pydantic `alias_generator = to_camel` handles serialization.
3. UUID fields serialize to `string` in TypeScript.
4. datetime fields serialize to ISO 8601 `string` in TypeScript.
5. Enum/Literal types must match exactly between Python and TypeScript.
6. Optional fields in Python → `| undefined` in TypeScript (not `| null` unless explicitly nullable).
7. Pagination follows a consistent envelope: `{ data: T[], meta: { total: number, page: number, pageSize: number } }`.

## Contract Drift Detection

Run weekly (and before each release):

```bash
#!/bin/bash
# scripts/validate-api-contract.sh

# Generate fresh OpenAPI spec
cd apps/api && python -c "
from src.main import create_app
import json
app = create_app()
spec = app.openapi()
with open('/tmp/openapi.json', 'w') as f:
    json.dump(spec, f, indent=2, default=str)
"

# Compare against committed spec
diff /tmp/openapi.json docs/api/openapi.json
if [ $? -ne 0 ]; then
    echo "WARNING: OpenAPI spec has drifted from committed version"
    echo "Run: cp /tmp/openapi.json docs/api/openapi.json"
fi

# Check TypeScript types match OpenAPI schemas
echo "Checking TypeScript type coverage..."
python3 scripts/check-type-coverage.py /tmp/openapi.json packages/types/src/
```

## Versioning

- API versioned via URL prefix: `/api/v1/`, `/api/v2/`.
- Breaking changes require a new version. Non-breaking additions are fine in current version.
- Deprecated fields: add `deprecated=True` in Pydantic model. Remove after 2 stages.
```

---

### 6.12 oregon-standards-validator

**File:** `.claude/skills/oregon-standards-validator/SKILL.md`

```markdown
---
name: oregon-standards-validator
description: "Validates that math questions, assessment parameters, BKT skill mappings, and UI content align with Oregon 2021 Math Standards (K–5). Cross-references standard codes against the authoritative JSON. Ensures every question maps to a real standard and every standard has adequate question coverage."
allowed-tools: Read Grep Bash
---

# Oregon Standards Validator

## Standards Reference

The authoritative standards reference is `docs/standards/or-math-k8-standards.json` and the
complete catalog in Doc 16 (Multi-Grade Expansion).

### Standard Code Format
```
{grade}.{domain}.{cluster}.{standard}

Examples:
  4.OA.A.1    → Grade 4, Operations & Algebraic Thinking, Cluster A, Standard 1
  1.NBT.B.3   → Grade 1, Number & Base Ten, Cluster B, Standard 3
  K.NCC.A.1   → Kindergarten, Counting & Cardinality, Cluster A, Standard 1
```

### Domain Codes
| Code | Domain | Grades |
|------|--------|--------|
| OA | Algebraic Reasoning: Operations | K–5 |
| NCC | Numeric Reasoning: Counting & Cardinality | K only |
| NBT | Numeric Reasoning: Base Ten Arithmetic | 1–5 |
| NF | Numeric Reasoning: Fractions | 3–5 |
| GM | Geometric Reasoning & Measurement | K–5 |
| DR | Data Reasoning | 1–5 |

### Standards Count by Grade
| Grade | Standards | Supported in Stage |
|-------|----------|-------------------|
| K (prerequisites) | 23 | Prerequisite pool only |
| 1 | 22 | Post-MVP expansion |
| 2 | 26 | Post-MVP expansion |
| 3 | 25 | Post-MVP expansion |
| 4 | 29 | Stage 1 (launch grade) |
| 5 | 26 | Post-MVP expansion |

## Validation Rules

### Question Validation
1. Every question MUST map to a valid Oregon standard code.
2. Standard code must exist in `or-math-k8-standards.json`.
3. Question difficulty (1–5) must be appropriate for the standard's DOK level.
4. Question content must align with the standard's full text description.
5. Number ranges must be appropriate for the grade level:
   - Grade 1: within 20 (addition/subtraction), within 100 (place value)
   - Grade 2: within 100 (add/sub), within 1000 (place value)
   - Grade 3: within 1000 (multiply/divide), fractions with denominators 2,3,4,6,8
   - Grade 4: multi-digit (up to 1,000,000), fractions with unlike denominators
   - Grade 5: decimals to thousandths, coordinate plane, volume

### Assessment Validation
1. Diagnostic assessment must cover all standards for the target grade.
2. Minimum 3 questions per standard in the question bank.
3. Question difficulty distribution: at least 1 question at difficulty 1–2, 1 at 3, 1 at 4–5 per standard.
4. Cross-grade prerequisites: if a student fails a Grade 4 standard, the system should be able to present prerequisite questions from Grade 3.

### BKT Mapping Validation
1. Every Oregon standard has a corresponding BKT skill entry.
2. BKT parameters exist for each standard (even if defaults).
3. Prerequisite relationships form a valid DAG (no cycles).
4. Every Grade 4 standard with Grade 3 prerequisites has those prerequisites mapped.

## Validation Script

```bash
#!/bin/bash
# scripts/validate-standards.sh

echo "=== Validating Oregon Standards Coverage ==="

# Check question bank coverage
python3 -c "
import json

with open('docs/standards/or-math-k8-standards.json') as f:
    standards = json.load(f)

grade4_standards = [s for s in standards if s['grade'] == 4]
print(f'Grade 4 standards: {len(grade4_standards)}')

# Verify all 29 Grade 4 standards present
assert len(grade4_standards) == 29, f'Expected 29, got {len(grade4_standards)}'
print('✓ All 29 Grade 4 standards present')

# Check for required fields
for s in grade4_standards:
    assert 'code' in s, f'Missing code field in {s}'
    assert 'domain' in s, f'Missing domain for {s[\"code\"]}'
    assert 'cluster' in s, f'Missing cluster for {s[\"code\"]}'
    assert 'description' in s, f'Missing description for {s[\"code\"]}'
    assert 'dok_level' in s, f'Missing DOK level for {s[\"code\"]}'
print('✓ All required fields present')
"

echo "=== Standards validation complete ==="
```
```

---

### 6.13 grade-specific-patterns

**File:** `.claude/skills/grade-specific-patterns/SKILL.md`

```markdown
---
name: grade-specific-patterns
description: "Age-appropriate UI adaptation rules for MathPath Oregon Grades 1–5. Covers touch target sizes, font minimums, TTS requirements, interaction modalities, session length caps, and visual complexity per grade band. Based on Doc 16 multi-grade expansion requirements."
allowed-tools: Read Grep Write
---

# Grade-Specific UI Patterns

## Grade Band Profiles

| Property | Grade 1 (6–7) | Grade 2 (7–8) | Grade 3 (8–9) | Grade 4 (9–10) | Grade 5 (10–11) |
|----------|---------------|---------------|---------------|----------------|-----------------|
| Min touch target | 60px | 56px | 48px | 48px | 44px |
| Min body font | 22px | 20px | 18px | 18px | 16px |
| Keyboard input | None | Minimal | Yes | Yes | Yes |
| TTS | Mandatory (all text) | On-demand | On-demand | None | None |
| Session cap | 12 min | 15 min | 18 min | 20 min | 25 min |
| Max Q per session | 8 | 10 | 12 | 15 | 18 |
| Interaction mode | Tap, drag | Tap, drag, simple type | All | All | All |
| Visual complexity | Minimal, large icons | Low | Moderate | Moderate | Higher density |
| Dark mode | No | Optional | Optional | Optional | Optional |
| Number range | ≤100 | ≤1,000 | ≤10,000 | ≤1,000,000 | Decimals, coordinates |

## Grade 1 Special Requirements

Grade 1 is the most different from the Grade 4 baseline:

1. **Mandatory TTS:** Every question stem and instruction must be read aloud. TTS auto-plays on question load.
   A speaker icon allows replay. Text remains visible for emerging readers.
2. **No keyboard input:** All answers are tap-to-select, drag-to-place, or tap-on-number-pad (on-screen).
3. **Enlarged touch targets:** 60px minimum. MCQ answer buttons are full-width cards, not small options.
4. **Picture-based questions:** Counters, base-ten blocks, and picture sets replace abstract notation.
5. **Pip mascot (verbose mode):** The Pip mascot guides every step with TTS-synced dialogue balloons.
6. **Simplified navigation:** No hamburger menus. Large back button with icon. Swipe gestures only.

## Grade 5 Special Requirements

Grade 5 introduces mathematical complexity beyond Grade 4:

1. **Coordinate plane component:** Interactive (x,y) grid for plotting points. Supports all four quadrants.
2. **Volume manipulative:** 3D cube builder for volume concepts. CSS 3D transforms or Three.js.
3. **Mixed number input:** Extended FractionBuilder supporting whole number + fraction.
4. **Decimal input:** Number pad with decimal point support. Thousandths place.
5. **Higher information density:** More text per screen, smaller fonts (16px body acceptable), denser data tables.

## Implementation Pattern

When building a component that varies by grade, use a grade-aware configuration:

```tsx
// packages/ui/src/components/Button/grade-config.ts
export const GRADE_BUTTON_CONFIG = {
  1: { minHeight: 60, fontSize: 22, padding: 20 },
  2: { minHeight: 56, fontSize: 20, padding: 18 },
  3: { minHeight: 48, fontSize: 18, padding: 16 },
  4: { minHeight: 48, fontSize: 18, padding: 16 },
  5: { minHeight: 44, fontSize: 16, padding: 14 },
} as const;

// Usage in component
const config = GRADE_BUTTON_CONFIG[studentGrade];
```

## Session Length Enforcement

```typescript
// apps/web/src/hooks/useSessionTimer.ts
const SESSION_CAPS: Record<number, number> = {
  1: 12 * 60 * 1000,  // 12 minutes
  2: 15 * 60 * 1000,
  3: 18 * 60 * 1000,
  4: 20 * 60 * 1000,
  5: 25 * 60 * 1000,
};

// Soft cap: show "Take a break?" prompt
// Hard cap: auto-save and show "Great session!" screen
```
```

---

### 6.14 strategic-compaction

**File:** `.claude/skills/strategic-compaction/SKILL.md`

```markdown
---
name: strategic-compaction
description: "Context management strategy for Claude Code sessions on MathPath Oregon. Defines when to trigger /compact, what must be preserved via PreCompact hooks, recovery procedures after compaction, and multi-session patterns for the 200K token context window."
allowed-tools: Read Bash
---

# Strategic Compaction

## The 80/20 Rule

Of the ~200K token context window:
- **80% (160K)** is available for active work: code, docs, reasoning.
- **20% (40K)** is the overhead budget: CLAUDE.md, rules, skill descriptions, conversation history.

When context usage exceeds 75% (150K tokens), compaction becomes imminent. Plan accordingly.

## Compaction Triggers

### Automatic Compaction
Claude Code auto-compacts when the context window fills. This is disruptive — it drops
conversation history, reasoning chains, and ephemeral context.

### Manual Compaction (`/compact`)
Trigger manually when:
1. Session has accumulated >100K tokens of conversation history.
2. Switching from one epic/feature to a different one.
3. After completing a major implementation task (before starting the next).
4. Context feels "stale" — Claude is repeating itself or forgetting recent changes.

### PreCompact Preservation

The PreCompact hook (see Section 8) saves critical context to a file before compaction:

**Must preserve:**
- Current development stage (1–5) and active sprint
- Active user story IDs and their status
- Files modified in the current session
- BKT parameters currently in use (if working on BKT)
- Design tokens referenced in current task
- Test results from the current session
- Any decisions made during the session (mini-ADRs)

**Can let go:**
- Full file contents (Claude can re-read files)
- Verbose error logs (save the summary only)
- Exploration paths that were abandoned
- Intermediate reasoning steps

## Post-Compaction Recovery

After compaction, the SessionStart hook re-injects:
1. The saved context file from PreCompact
2. Current stage and sprint information
3. The last 5 files modified

Claude should:
1. Read the recovery file
2. Verify understanding of the current task
3. Ask for clarification only if the recovery file is insufficient

## Multi-Session Patterns

For long features that span multiple sessions:

1. **One stage at a time.** Do not mix Stage 1 work with Stage 3 planning in the same session.
2. **One epic at a time.** A session should focus on a single epic (e.g., Epic 3: Seed Question Bank).
3. **Horizontal scaling.** Use subagents for parallel workstreams (tests in one, implementation in another).
4. **Session handoff.** End each session by writing a brief handoff note to `docs/session-notes/YYYY-MM-DD.md`.

## Token Budget Breakdown

| Component | Estimated Tokens | Notes |
|-----------|-----------------|-------|
| CLAUDE.md | 800 | Always loaded |
| Active rules (2–3) | 1,200 | Auto-loaded per glob |
| Skill descriptions (16) | 1,600 | Always loaded (scan only) |
| Active skill (1) | 3,000 | On-demand |
| Conversation history | 20,000–100,000 | Grows during session |
| Code context (open files) | 10,000–50,000 | Varies by task |
| Reasoning/output | 10,000–30,000 | Claude's responses |
| **Total typical session** | **50,000–180,000** | Compact at ~150K |
```

---

### 6.15 llm-cost-optimizer

**File:** `.claude/skills/llm-cost-optimizer/SKILL.md`

```markdown
---
name: llm-cost-optimizer
description: "Token usage tracking, model routing rules, cost alerts, and per-student cost attribution for MathPath Oregon. Implements the FinOps framework from OPS-000. Ensures LLM costs stay within budget by routing to the right model for each task."
allowed-tools: Read Grep Bash
---

# LLM Cost Optimizer

## Model Routing Matrix

| Task | Primary Model | Fallback Model | Max Tokens | Est. Cost/Call |
|------|-------------|---------------|------------|---------------|
| Tutoring hint (Level 3) | Claude Sonnet 4.6 | GPT-4o | 500 out | $0.008 |
| Question generation | o3-mini | Claude Sonnet 4.6 | 800 out | $0.003 |
| Learning plan generation | Claude Sonnet 4.6 | GPT-4o | 2,000 out | $0.025 |
| Intent classification | Haiku 3.5 | — | 50 out | $0.0002 |
| Content safety filter | Haiku 3.5 | — | 100 out | $0.0003 |
| Report narrative | Claude Sonnet 4.6 | GPT-4o | 1,500 out | $0.020 |
| Spanish translation | Claude Sonnet 4.6 | GPT-4o | 1,000 out | $0.012 |

## Per-Student Cost Budget

From OPS-000 FinOps framework:

| Component | Monthly Budget per Student | Alert Threshold |
|-----------|---------------------------|----------------|
| Tutoring LLM calls | $0.50 | $0.40 (80%) |
| Question generation | $0.20 | $0.16 (80%) |
| Total LLM spend | $1.00 | $0.80 (80%) |
| Infrastructure (amortized) | $0.30 | — |
| **Total per student** | **$1.30** | **$1.04** |

## Cost Tracking Implementation

```python
# apps/api/src/core/llm_cost_tracker.py
from dataclasses import dataclass
from datetime import datetime

@dataclass
class LLMUsageEvent:
    student_id: str | None
    model: str
    purpose: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    timestamp: datetime

async def track_llm_usage(event: LLMUsageEvent) -> None:
    """Record LLM usage for cost attribution and alerting."""
    # Write to llm_usage_events table
    await usage_repo.insert(event)

    # Check per-student monthly budget
    if event.student_id:
        monthly_total = await usage_repo.get_monthly_total(event.student_id)
        if monthly_total >= ALERT_THRESHOLD:
            await send_cost_alert(event.student_id, monthly_total)

# Model pricing (as of April 2026)
MODEL_PRICING = {
    "claude-sonnet-4.6": {"input": 3.00 / 1_000_000, "output": 15.00 / 1_000_000},
    "claude-haiku-3.5":  {"input": 0.25 / 1_000_000, "output": 1.25 / 1_000_000},
    "gpt-4o":            {"input": 2.50 / 1_000_000, "output": 10.00 / 1_000_000},
    "o3-mini":           {"input": 1.10 / 1_000_000, "output": 4.40 / 1_000_000},
}
```

## Optimization Strategies

1. **Classification before generation:** Use Haiku for intent/routing before invoking expensive models.
2. **Caching:** Cache question generation results. Same standard + same difficulty = same question pool.
3. **Streaming:** Stream tutor responses to reduce perceived latency (does not reduce cost).
4. **Token limits:** Set explicit `max_tokens` on every LLM call. Never allow unbounded generation.
5. **Batch generation:** Generate question sets in batches during off-peak hours, not on-demand per student.
6. **Model downgrade under budget pressure:** If monthly budget is at 90%, downgrade tutoring to Haiku.
```

---

### 6.16 accessibility-enforcer

**File:** `.claude/skills/accessibility-enforcer/SKILL.md`

```markdown
---
name: accessibility-enforcer
description: "WCAG AA/AAA enforcement for MathPath Oregon. Validates ARIA attributes, keyboard navigation, screen reader compatibility, focus management, prefers-reduced-motion support, color contrast, and touch target sizes. AAA standard required for student-facing content."
allowed-tools: Read Grep Bash Edit
---

# Accessibility Enforcer

## Standards

| Context | WCAG Level | Rationale |
|---------|-----------|-----------|
| Student-facing UI | AAA | Children with disabilities are a protected class. Maximum accessibility. |
| Parent dashboard | AA | Standard professional web application requirement. |
| Teacher dashboard | AA | Standard professional web application requirement. |

## Checklist for Every Component

### Semantic HTML
- [ ] Use semantic elements: `<button>` not `<div onClick>`, `<nav>`, `<main>`, `<article>`, `<section>`.
- [ ] Headings follow hierarchy: `<h1>` → `<h2>` → `<h3>`. No skipped levels.
- [ ] Lists use `<ul>/<ol>/<li>`. Navigation uses `<nav>`.
- [ ] Tables use `<th scope="col/row">` for headers.
- [ ] Forms use `<label htmlFor>` on every input. No placeholder-only labels.

### Keyboard Navigation
- [ ] All interactive elements reachable via Tab key.
- [ ] Focus order matches visual order (no `tabindex > 0`).
- [ ] Focus visible: 2px teal ring on `:focus-visible` (not `:focus` to avoid pointer ring).
- [ ] Escape key closes modals and dropdowns.
- [ ] Enter/Space activates buttons and links.
- [ ] Arrow keys navigate within groups (tabs, radio buttons, dropdown options).
- [ ] Focus trapped in modals (no tabbing out of modal while open).

### Screen Reader
- [ ] All images have `alt` text (descriptive, not decorative — decorative images use `alt=""`).
- [ ] Icons have `aria-label` or are `aria-hidden="true"` if decorative.
- [ ] Dynamic content updates announced via `aria-live` regions.
- [ ] Math content: KaTeX outputs include `aria-label` with spoken form of expression.
  Example: `<span aria-label="three fourths">¾</span>`
- [ ] Progress indicators: `aria-valuenow`, `aria-valuemin`, `aria-valuemax` on progress bars.
- [ ] Question state: `aria-live="polite"` on answer feedback area.

### Color & Contrast
- [ ] Body text on background: ≥4.5:1 contrast ratio (AA) or ≥7:1 (AAA for student).
- [ ] Large text (≥18px or ≥14px bold): ≥3:1 contrast ratio.
- [ ] Never use color alone to convey information. Pair with: icons, text labels, patterns.
- [ ] Correct answer: green + ✓ icon (not just green).
- [ ] In-progress: amber + ◐ icon (not just amber).
- [ ] Error state: red + ✕ icon + text description (not just red).

### Motion & Animation
- [ ] All animations wrapped in `@media (prefers-reduced-motion: no-preference)`.
- [ ] Reduced motion fallback: instant opacity transitions (no movement).
- [ ] No auto-playing animations that last > 5 seconds.
- [ ] Confetti celebration: replaced with static badge + text in reduced motion.
- [ ] Shake animation: replaced with border color change in reduced motion.

### Touch Targets
- [ ] Student app: 48×48px minimum for all interactive elements.
- [ ] Dashboard: 44×44px minimum.
- [ ] Adequate spacing between targets: minimum 8px gap.

### Math-Specific Accessibility
- [ ] KaTeX expressions have screen reader text via `aria-label`.
- [ ] FractionBuilder: keyboard-accessible numerator/denominator inputs.
- [ ] NumberLine: keyboard arrow keys to move marker, Enter to place.
- [ ] Drag-and-drop: keyboard alternative (select + place via arrow keys + Enter).
- [ ] Visual manipulatives: equivalent text description for screen readers.

## Automated Testing

Run accessibility checks in CI:

```bash
# Playwright axe integration
# apps/web/tests/e2e/accessibility.spec.ts

import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

test("student dashboard passes WCAG AAA", async ({ page }) => {
  await page.goto("/student/dashboard");
  const results = await new AxeBuilder({ page })
    .withTags(["wcag2aaa", "wcag21aa"])
    .analyze();
  expect(results.violations).toEqual([]);
});

test("question screen passes WCAG AAA", async ({ page }) => {
  await page.goto("/student/assessment/test-session");
  const results = await new AxeBuilder({ page })
    .withTags(["wcag2aaa", "wcag21aa"])
    .analyze();
  expect(results.violations).toEqual([]);
});
```
```
## 7. Custom Slash Commands

Custom slash commands live in `.claude/commands/` and are invoked via `/custom:name` in the Claude Code CLI. Each command file uses YAML frontmatter for metadata and markdown for the prompt template that Claude receives when the command is invoked.

---

### 7.1 /custom:implement

**File:** `.claude/commands/implement.md`

```markdown
---
name: implement
description: "Pick up a user story or ticket, load all relevant context, and implement it end-to-end following the sprint lifecycle."
argument-hint: "[story-id] e.g., US-1.3"
allowed-tools: Read Grep Edit Write Bash
---

# Implement User Story: $ARGUMENTS

## Step 1: Load Context
1. Identify the story ID from the argument (format: US-X.Y).
2. Search lifecycle documents for the story and its acceptance criteria:
   - Stage 1: `docs/10-lifecycle-stage1.md`
   - Stage 2: `docs/11-lifecycle-stage2.md`
   - Stage 3: `docs/12-lifecycle-stage3.md`
   - Stage 4: `docs/13-lifecycle-stage4.md`
   - Stage 5: `docs/14-lifecycle-stage5.md`
3. Read the acceptance criteria carefully. Each criterion maps to a testable behavior.
4. Identify the epic and related stories for broader context.
5. Check which development stage this story belongs to.

## Step 2: Verify Prerequisites
1. Check that the sprint lifecycle phase is "Implement" or later for this story.
2. Verify that architecture/design decisions exist (ADRs, Figma references).
3. Identify dependent stories — are they complete?
4. List the files that will be created or modified.

## Step 3: Implement
1. Follow the architecture enforcer rules: correct layer (routes → services → repos → DB).
2. Use design tokens from the design system (no raw hex values, no pixel literals).
3. Add COPPA consent guards where required (any endpoint touching student data).
4. Write code that addresses EVERY acceptance criterion — not just the happy path.
5. Include error handling following `core/exceptions.py` patterns.

## Step 4: Write Tests
1. Write unit tests covering all new code (meeting coverage gates).
2. Write integration tests for service-level interactions.
3. Generate BDD scenarios from acceptance criteria using the bdd-scenario-writer skill.
4. Verify test coverage: `pnpm test -- --coverage` or `make api-test-cov`.

## Step 5: Verify
1. Run linting: `pnpm lint` and `make api-lint`.
2. Run type checking: `pnpm typecheck`.
3. Run the full test suite: `make test-all`.
4. Verify no COPPA violations: check consent guard presence.
5. Verify design token usage: no raw values in UI code.

## Step 6: Report
Summarize what was implemented:
- Story ID and title
- Files created/modified
- Acceptance criteria coverage (which ACs are met)
- Test count and coverage
- Any open items or follow-up needed
```

---

### 7.2 /custom:test

**File:** `.claude/commands/test.md`

```markdown
---
name: test
description: "Run the appropriate test suite for the current changes. Detects modified files, selects the right test framework, and reports coverage."
argument-hint: "[scope] e.g., 'unit', 'integration', 'e2e', 'all', or a file path"
allowed-tools: Bash Read Grep
---

# Run Tests: $ARGUMENTS

## Detect Scope
If no argument provided, detect based on recently modified files:
- `.tsx` / `.ts` files in `apps/web/` → run Vitest
- `.py` files in `apps/api/` → run pytest
- `.py` files in `services/bkt-engine/` → run BKT tests
- `.py` files in `services/agent-engine/` → run agent tests
- `.spec.ts` files → run Playwright
- `.feature` files → run BDD tests

## Run Commands by Scope

| Scope | Command | Coverage Report |
|-------|---------|----------------|
| `unit` (frontend) | `cd apps/web && pnpm test -- --coverage` | `apps/web/coverage/` |
| `unit` (backend) | `cd apps/api && make test-unit-cov` | `apps/api/htmlcov/` |
| `integration` (frontend) | `cd apps/web && pnpm test:integration` | — |
| `integration` (backend) | `cd apps/api && make test-integration` | — |
| `e2e` | `pnpm test:e2e` | Playwright report |
| `bkt` | `cd services/bkt-engine && make test-cov` | `services/bkt-engine/htmlcov/` |
| `agent` | `cd services/agent-engine && make test-cov` | `services/agent-engine/htmlcov/` |
| `all` | `make test-all` | All reports |
| File path | Run tests matching the path | — |

## Post-Test Report
After tests complete, report:
1. Total tests run, passed, failed, skipped.
2. Coverage summary (lines, branches) compared to gates.
3. Any failing tests with error summary.
4. Suggestions for missing test coverage.
```

---

### 7.3 /custom:deploy-check

**File:** `.claude/commands/deploy-check.md`

```markdown
---
name: deploy-check
description: "Pre-deployment verification checklist. Validates that all quality gates pass before deploying to staging or production."
argument-hint: "[environment] e.g., 'staging' or 'production'"
allowed-tools: Bash Read Grep
---

# Pre-Deployment Check: $ARGUMENTS

Run the following verification steps before deploying to $ARGUMENTS:

## 1. Code Quality
```bash
pnpm lint                    # ESLint + Prettier
pnpm typecheck               # TypeScript strict
make api-lint                # Ruff + mypy (Python)
```
All must pass with zero errors.

## 2. Test Suite
```bash
make test-all                # Full test suite
```
All tests must pass. Zero failures.

## 3. Coverage Gates
Verify minimum coverage thresholds:
- Frontend components: ≥80% lines
- Backend services: ≥80% lines
- BKT engine: ≥90% lines
- COPPA consent flows: 100% lines

## 4. Security Checks
```bash
npm audit --production       # Frontend dependency audit
pip-audit                    # Python dependency audit
```
No critical or high vulnerabilities.

## 5. Database Migration
```bash
cd apps/api && alembic check  # Verify no pending migrations
cd apps/api && alembic upgrade head --sql  # Preview SQL (dry run)
```
Migration must be reversible: `alembic downgrade -1` then `alembic upgrade head`.

## 6. OpenAPI Contract
```bash
bash scripts/validate-api-contract.sh  # Check for spec drift
```

## 7. Environment-Specific Checks

### For Staging:
- Feature flags verified in LaunchDarkly staging environment
- Staging database has representative test data
- All environment variables set in AWS Secrets Manager

### For Production:
- Staging deployment successful and smoke-tested
- Rollback plan documented
- Monitoring alerts configured (CloudWatch, Sentry)
- On-call engineer notified

## Report
Generate a go/no-go deployment report with pass/fail for each check.
```

---

### 7.4 /custom:story-status

**File:** `.claude/commands/story-status.md`

```markdown
---
name: story-status
description: "Check implementation progress against user stories for the current stage. Reports story completion, coverage, and blockers."
argument-hint: "[stage-number] e.g., '1' for Stage 1"
allowed-tools: Read Grep Bash
---

# Story Status Report: Stage $ARGUMENTS

## Process
1. Read the lifecycle document for Stage $ARGUMENTS.
2. Extract all user stories (US-X.Y format) with their acceptance criteria.
3. For each story, check implementation status:
   - Search codebase for commit references: `git log --oneline --grep="US-$ARGUMENTS"`
   - Check for test files matching story patterns
   - Verify code artifacts exist for each acceptance criterion
4. Classify each story:
   - **Done**: All ACs implemented, tests pass, no open bugs
   - **Code Complete**: All ACs implemented, tests pending
   - **In Progress**: Some ACs implemented
   - **Not Started**: No code artifacts found
   - **Blocked**: Dependencies not met

## Report Format
```
Stage $ARGUMENTS Story Status
═══════════════════════════════

Epic 1: [Epic Name]
  US-X.1  [Title]              ■■■■□ Code Complete (4/5 ACs)
  US-X.2  [Title]              ■■■■■ Done
  US-X.3  [Title]              ■■□□□ In Progress (2/5 ACs)

Summary:
  Total: XX stories | Done: XX | In Progress: XX | Not Started: XX
  P0 completion: XX%
  Story points completed: XX / XX
  Estimated remaining effort: XX hours
```
```

---

### 7.5 /custom:spec-search

**File:** `.claude/commands/spec-search.md`

```markdown
---
name: spec-search
description: "Search the 24-document MathPath specification suite for requirements, decisions, or standards. Searches product docs (01–17), engineering docs (ENG-000–ENG-006), and lifecycle docs."
argument-hint: "[search-query] e.g., 'COPPA consent flow' or 'BKT parameters'"
allowed-tools: Read Grep Bash
---

# Spec Search: $ARGUMENTS

## Search Scope
Search across all MathPath specification documents:

### Product Documents (docs/)
- `docs/01-strategy.md` — Business strategy & market analysis
- `docs/02-competitive-analysis.md` — Competitive landscape
- `docs/03-prd-stage1.md` — PRD for Stage 1
- `docs/04-prd-stage2.md` — PRD for Stage 2
- `docs/05-prd-stage3.md` — PRD for Stage 3
- `docs/06-prd-stage4.md` — PRD for Stage 4
- `docs/07-prd-stage5.md` — PRD for Stage 5
- `docs/08-information-architecture.md` — IA and navigation
- `docs/09-design-system.md` — UI/UX design system and tokens
- `docs/10-lifecycle-stage1.md` — SDLC Stage 1 (LC-001)
- `docs/11-lifecycle-stage2.md` — SDLC Stage 2 (LC-002)
- `docs/12-lifecycle-stage3.md` — SDLC Stage 3 (LC-003)
- `docs/13-lifecycle-stage4.md` — SDLC Stage 4 (LC-004)
- `docs/14-lifecycle-stage5.md` — SDLC Stage 5 (LC-005)
- `docs/15-lifecycle-crosscutting-ops.md` — Cross-cutting ops (OPS-000)
- `docs/16-multigrade-expansion.md` — Multi-grade expansion plan
- `docs/17-claude-code-skills-spec.md` — This document

### Engineering Documents (eng-docs/)
- `eng-docs/ENG-000-foundations.md` — Engineering foundations
- `eng-docs/ENG-001-frontend.md` — Frontend engineering guide
- `eng-docs/ENG-002-backend.md` — Backend engineering guide
- `eng-docs/ENG-003-ai-ml.md` — AI/ML engineering guide
- `eng-docs/ENG-004-data.md` — Data engineering guide
- `eng-docs/ENG-005-infra.md` — Infrastructure guide
- `eng-docs/ENG-006-crosscutting.md` — Cross-cutting engineering

## Search Method
```bash
grep -rn -i "$ARGUMENTS" docs/ eng-docs/ --include="*.md" -l
```
Then read the matching sections from the top results.

Report: document name, section heading, and relevant content for each match.
```

---

### 7.6 /custom:stage-context

**File:** `.claude/commands/stage-context.md`

```markdown
---
name: stage-context
description: "Load comprehensive context for a specific development stage. Reads the stage's lifecycle document, associated PRD, and engineering guides. Sets the session focus to that stage."
argument-hint: "[stage-number] e.g., '1'"
allowed-tools: Read Grep
---

# Load Stage $ARGUMENTS Context

## Load Documents
Based on stage $ARGUMENTS, read the following documents:

### Stage 1 (Months 1–3): Standards DB & Diagnostic Assessment
- PRD: `docs/03-prd-stage1.md`
- Lifecycle: `docs/10-lifecycle-stage1.md`
- Ops: `docs/15-lifecycle-crosscutting-ops.md` (Section 1 for BKT, Section 3.1 for COPPA)

### Stage 2 (Months 4–6): Learning Plan + AI Question Gen
- PRD: `docs/04-prd-stage2.md`
- Lifecycle: `docs/11-lifecycle-stage2.md`
- Ops: `docs/15-lifecycle-crosscutting-ops.md` (Section 1.2 for LLM governance)

### Stage 3 (Months 7–10): Practice Engine + LangGraph Tutoring
- PRD: `docs/05-prd-stage3.md`
- Lifecycle: `docs/12-lifecycle-stage3.md`
- AI/ML: `eng-docs/ENG-003-ai-ml.md`

### Stage 4 (Months 11–14): End-of-Grade Assessment + Reporting (MVP)
- PRD: `docs/06-prd-stage4.md`
- Lifecycle: `docs/13-lifecycle-stage4.md`
- Ops: `docs/15-lifecycle-crosscutting-ops.md` (Section 2 for FinOps at scale)

### Stage 5 (Months 15–20): Monetization, School Onboarding, Spanish (MMP)
- PRD: `docs/07-prd-stage5.md`
- Lifecycle: `docs/14-lifecycle-stage5.md`
- Multi-grade: `docs/16-multigrade-expansion.md`

## Context Summary
After loading, provide:
1. Stage overview and timeline
2. Key epics and their status
3. Technical components being built
4. Active risks and mitigations
5. Quality gates for this stage
```

---

### 7.7 /custom:grade-check

**File:** `.claude/commands/grade-check.md`

```markdown
---
name: grade-check
description: "Validate that content, questions, or UI components are appropriate for a specific grade level. Checks against Oregon standards, age-appropriate UI rules, and grade-specific parameters."
argument-hint: "[grade] e.g., '4' or '1'"
allowed-tools: Read Grep Bash
---

# Grade Level Validation: Grade $ARGUMENTS

## Validation Checks

### 1. Standards Alignment
- Verify all referenced standard codes start with "$ARGUMENTS." prefix.
- Cross-reference against `docs/standards/or-math-k8-standards.json`.
- Check that question content aligns with the standard's DOK level.

### 2. Number Range Validation
| Grade | Addition/Subtraction | Multiplication/Division | Fractions | Decimals |
|-------|---------------------|------------------------|-----------|----------|
| 1 | Within 20 | N/A | N/A | N/A |
| 2 | Within 100 | N/A | N/A | N/A |
| 3 | Within 1,000 | Within 100 | Denominators 2,3,4,6,8 | N/A |
| 4 | Multi-digit | Multi-digit | Unlike denominators | Tenths, hundredths |
| 5 | Multi-digit | Multi-digit | Mixed numbers | Thousandths |

### 3. UI Compliance (from grade-specific-patterns skill)
- Touch target size meets grade minimum
- Font size meets grade minimum
- Session length cap configured correctly
- TTS requirements met (mandatory for Grade 1, on-demand for 2–3)
- Interaction modality appropriate (no keyboard for Grade 1)

### 4. Reading Level
- Question text Flesch-Kincaid Grade Level ≤ target grade + 1
- Instructions ≤ 15 words for Grade 1–2, ≤ 25 words for Grade 3–5
- Growth mindset language (no "wrong", "failed", "bad")

Report all violations with specific remediation guidance.
```

---

## 8. Hook Configuration

Hooks are configured in `.claude/settings.json` and fire at specific lifecycle events during a Claude Code session. Each hook runs a command, sends an HTTP request, or injects a prompt. The following configuration provides the complete hook setup for MathPath Oregon.

### 8.1 Complete settings.json Hook Configuration

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup",
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/session-start.sh"
          }
        ]
      },
      {
        "matcher": "compact",
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/post-compact-recovery.sh"
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/pre-bash-guard.sh"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/post-edit-validate.sh"
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/stop-verify.sh"
          }
        ]
      }
    ],
    "SubagentStop": [
      {
        "hooks": [
          {
            "type": "prompt",
            "prompt": "Review the subagent's output for quality. Verify: (1) code follows MathPath conventions, (2) tests are included, (3) no COPPA violations, (4) design tokens used correctly. Summarize any issues found. Input: $ARGUMENTS"
          }
        ]
      }
    ]
  },
  "permissions": {
    "allow": [
      "Read",
      "Grep",
      "Glob",
      "Bash(pnpm *)",
      "Bash(make *)",
      "Bash(npx *)",
      "Bash(cd * && *)",
      "Bash(grep *)",
      "Bash(cat *)",
      "Bash(ls *)",
      "Bash(git log *)",
      "Bash(git diff *)",
      "Bash(git status *)",
      "Bash(python3 *)",
      "Bash(pytest *)",
      "Edit",
      "Write"
    ],
    "deny": [
      "Bash(rm -rf *)",
      "Bash(DROP TABLE *)",
      "Bash(DROP DATABASE *)",
      "Bash(git push --force *)",
      "Bash(git reset --hard *)",
      "Bash(curl * | bash *)",
      "Bash(sudo *)"
    ]
  }
}
```

### 8.2 SessionStart Hook Script

**File:** `.claude/hooks/session-start.sh`

```bash
#!/bin/bash
# .claude/hooks/session-start.sh
# Fires on every session start. Loads environment context and verifies dependencies.

set -euo pipefail

echo "=== MathPath Oregon — Session Startup ==="

# 1. Detect current development stage from active branch or environment
CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")
echo "Branch: $CURRENT_BRANCH"

# 2. Check Node.js and Python versions
NODE_VERSION=$(node --version 2>/dev/null || echo "not installed")
PYTHON_VERSION=$(python3 --version 2>/dev/null || echo "not installed")
echo "Node: $NODE_VERSION | Python: $PYTHON_VERSION"

# 3. Check if Docker services are running
POSTGRES_RUNNING=$(docker ps --filter "name=mathpath-postgres" --format "{{.Status}}" 2>/dev/null || echo "not running")
REDIS_RUNNING=$(docker ps --filter "name=mathpath-redis" --format "{{.Status}}" 2>/dev/null || echo "not running")
echo "PostgreSQL: $POSTGRES_RUNNING | Redis: $REDIS_RUNNING"

# 4. Report current stage context
if [ -f ".claude/context/current-stage.txt" ]; then
    STAGE=$(cat .claude/context/current-stage.txt)
    echo "Active Stage: $STAGE"
else
    echo "Active Stage: Not set (use /custom:stage-context to set)"
fi

# 5. Check for recovery file from previous compaction
if [ -f ".claude/context/recovery.md" ]; then
    echo ""
    echo "=== Recovery Context from Previous Compaction ==="
    cat .claude/context/recovery.md
    echo "=== End Recovery Context ==="
fi

# 6. Report recent git activity
echo ""
echo "=== Recent Activity (last 5 commits) ==="
git log --oneline -5 2>/dev/null || echo "No git history"

# 7. Check for uncommitted changes
CHANGES=$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')
if [ "$CHANGES" -gt 0 ]; then
    echo ""
    echo "WARNING: $CHANGES uncommitted changes detected"
    git status --short 2>/dev/null
fi

echo ""
echo "=== Session ready ==="
```

### 8.3 PreCompact / Post-Compact Recovery Hook Script

**File:** `.claude/hooks/post-compact-recovery.sh`

```bash
#!/bin/bash
# .claude/hooks/post-compact-recovery.sh
# Fires on SessionStart after compaction. Re-injects preserved context.

set -euo pipefail

RECOVERY_FILE=".claude/context/recovery.md"

if [ -f "$RECOVERY_FILE" ]; then
    echo "=== Restoring Context After Compaction ==="
    cat "$RECOVERY_FILE"
    echo ""
    echo "=== Context restored. Verify understanding before continuing. ==="
else
    echo "No recovery context found. Starting fresh session."
    echo "Use /custom:stage-context [stage] to load stage context."
fi
```

The PreCompact preservation is handled by a `Stop` hook variant that saves context before any session ends:

**File:** `.claude/hooks/save-context.sh`

```bash
#!/bin/bash
# .claude/hooks/save-context.sh
# Called periodically to save critical context for compaction recovery.

set -euo pipefail

CONTEXT_DIR=".claude/context"
mkdir -p "$CONTEXT_DIR"

RECOVERY_FILE="$CONTEXT_DIR/recovery.md"

# Capture current context
cat > "$RECOVERY_FILE" << 'RECOVERY'
# Session Recovery Context
RECOVERY

# Add current stage
if [ -f "$CONTEXT_DIR/current-stage.txt" ]; then
    echo "## Active Stage" >> "$RECOVERY_FILE"
    cat "$CONTEXT_DIR/current-stage.txt" >> "$RECOVERY_FILE"
    echo "" >> "$RECOVERY_FILE"
fi

# Add recently modified files
echo "## Recently Modified Files" >> "$RECOVERY_FILE"
git diff --name-only HEAD~5 2>/dev/null | head -20 >> "$RECOVERY_FILE" || echo "No recent changes" >> "$RECOVERY_FILE"
echo "" >> "$RECOVERY_FILE"

# Add current task context if set
if [ -f "$CONTEXT_DIR/current-task.md" ]; then
    echo "## Current Task" >> "$RECOVERY_FILE"
    cat "$CONTEXT_DIR/current-task.md" >> "$RECOVERY_FILE"
    echo "" >> "$RECOVERY_FILE"
fi

echo "Context saved to $RECOVERY_FILE"
```

### 8.4 PreToolUse Bash Guard

**File:** `.claude/hooks/pre-bash-guard.sh`

```bash
#!/bin/bash
# .claude/hooks/pre-bash-guard.sh
# Validates bash commands before execution. Blocks destructive operations.

set -euo pipefail

# Read the command from stdin (hook input JSON)
INPUT=$(cat)
COMMAND=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('command',''))" 2>/dev/null || echo "")

if [ -z "$COMMAND" ]; then
    # No command to validate, allow
    echo '{"decision": "allow"}'
    exit 0
fi

# Block destructive commands
BLOCKED_PATTERNS=(
    "rm -rf /"
    "rm -rf ~"
    "rm -rf ."
    "DROP TABLE"
    "DROP DATABASE"
    "TRUNCATE"
    "git push --force"
    "git reset --hard"
    "curl.*| bash"
    "curl.*| sh"
    "sudo rm"
    "mkfs"
    "dd if="
    "> /dev/sd"
)

for pattern in "${BLOCKED_PATTERNS[@]}"; do
    if echo "$COMMAND" | grep -qi "$pattern"; then
        echo "{\"decision\": \"block\", \"reason\": \"Blocked destructive command matching pattern: $pattern\"}"
        exit 0
    fi
done

# Warn on production-affecting commands
WARN_PATTERNS=(
    "deploy.*prod"
    "alembic.*upgrade.*head"
    "docker.*push"
)

for pattern in "${WARN_PATTERNS[@]}"; do
    if echo "$COMMAND" | grep -qi "$pattern"; then
        echo "{\"decision\": \"allow\", \"message\": \"WARNING: Production-affecting command detected. Proceed with caution.\"}"
        exit 0
    fi
done

# Allow all other commands
echo '{"decision": "allow"}'
```

### 8.5 PostToolUse Edit/Write Validation

**File:** `.claude/hooks/post-edit-validate.sh`

```bash
#!/bin/bash
# .claude/hooks/post-edit-validate.sh
# Validates files after edit/write operations. Checks design token usage and linting.

set -euo pipefail

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('file_path',''))" 2>/dev/null || echo "")

if [ -z "$FILE_PATH" ]; then
    exit 0
fi

WARNINGS=""

# Check for raw hex colors in TSX/CSS files
if echo "$FILE_PATH" | grep -qE '\.(tsx|css|ts)$'; then
    RAW_HEX=$(grep -nE '#[0-9a-fA-F]{6}' "$FILE_PATH" 2>/dev/null | grep -v "// token:" | grep -v "/* token:" | head -5 || true)
    if [ -n "$RAW_HEX" ]; then
        WARNINGS="$WARNINGS\nWARNING: Raw hex color values found. Use design tokens instead:\n$RAW_HEX"
    fi
fi

# Check for hardcoded pixel values in TSX files
if echo "$FILE_PATH" | grep -qE '\.tsx$'; then
    RAW_PX=$(grep -nE '\b(padding|margin|gap|width|height).*[0-9]+px' "$FILE_PATH" 2>/dev/null | grep -v "space-" | grep -v "// token:" | head -5 || true)
    if [ -n "$RAW_PX" ]; then
        WARNINGS="$WARNINGS\nWARNING: Hardcoded pixel values found. Use spacing tokens:\n$RAW_PX"
    fi
fi

# Check for PII in Python files
if echo "$FILE_PATH" | grep -qE '\.py$'; then
    PII_LOG=$(grep -nE 'log(ger)?\.(info|debug|warning|error).*\b(email|name|address|phone)\b' "$FILE_PATH" 2>/dev/null | head -5 || true)
    if [ -n "$PII_LOG" ]; then
        WARNINGS="$WARNINGS\nCRITICAL: Possible PII in log statement (COPPA violation):\n$PII_LOG"
    fi
fi

if [ -n "$WARNINGS" ]; then
    echo -e "$WARNINGS"
fi
```

### 8.6 Stop Verification Hook

**File:** `.claude/hooks/stop-verify.sh`

```bash
#!/bin/bash
# .claude/hooks/stop-verify.sh
# Fires when Claude finishes responding. Verifies quality gates.

set -euo pipefail

# Save context for potential compaction recovery
bash .claude/hooks/save-context.sh 2>/dev/null || true

# Check if any files were modified in this session
MODIFIED=$(git diff --name-only 2>/dev/null || echo "")

if [ -n "$MODIFIED" ]; then
    echo "=== Session Quality Check ==="
    echo "Modified files:"
    echo "$MODIFIED"

    # Check for new Python files missing test coverage
    NEW_PY=$(echo "$MODIFIED" | grep '\.py$' | grep -v 'test_' | grep -v 'conftest' | grep -v '__init__' || true)
    for file in $NEW_PY; do
        TEST_FILE=$(echo "$file" | sed 's|src/|tests/unit/test_|' | sed 's|\.py$|.py|')
        if [ ! -f "$TEST_FILE" ]; then
            echo "WARNING: No test file found for $file (expected $TEST_FILE)"
        fi
    done

    # Check for new TSX files missing test coverage
    NEW_TSX=$(echo "$MODIFIED" | grep '\.tsx$' | grep -v '.test.' | grep -v '.spec.' || true)
    for file in $NEW_TSX; do
        TEST_FILE=$(echo "$file" | sed 's|\.tsx$|.test.tsx|')
        if [ ! -f "$TEST_FILE" ]; then
            echo "WARNING: No test file found for $file (expected $TEST_FILE)"
        fi
    done
fi
```

---

## 9. Subagent Definitions

Subagents are forked Claude Code instances that operate in an isolated context window. They inherit the project's CLAUDE.md and rules but maintain a separate conversation history. Subagents are defined in `.claude/agents/` and can be invoked from skills or directly.

### 9.1 test-runner

**File:** `.claude/agents/test-runner.md`

```markdown
---
name: test-runner
description: "Isolated test execution agent. Runs the appropriate test suite, collects coverage reports, and summarizes results. Use when you need to run tests without polluting the main session context."
allowed-tools: Bash Read Grep
model: claude-sonnet-4-6-20250414
---

# Test Runner Agent

You are a test execution specialist for MathPath Oregon. Your job is to:

1. Identify which tests to run based on the provided context.
2. Execute the test suite.
3. Parse the output for failures and coverage.
4. Return a structured summary.

## Execution Steps

1. Read the list of modified files from the parent context.
2. Determine the test scope:
   - TypeScript changes → `pnpm test`
   - Python API changes → `cd apps/api && pytest`
   - BKT changes → `cd services/bkt-engine && pytest`
   - Agent changes → `cd services/agent-engine && pytest`
3. Run tests with coverage: add `--coverage` (Vitest) or `--cov` (pytest).
4. Parse the output:
   - Count: total, passed, failed, skipped
   - Coverage: line %, branch %
   - Failures: test name, error message (first 3 lines)
5. Return a concise summary.

## Output Format

```
TEST RESULTS
════════════
Scope: [frontend | backend | bkt | agent | all]
Total: XX | Passed: XX | Failed: XX | Skipped: XX
Coverage: XX% lines | XX% branches

Failures (if any):
  1. test_name — ErrorType: brief message
  2. test_name — ErrorType: brief message

Coverage Gates:
  ✓ services: 82% (≥80%)
  ✗ bkt-engine: 87% (≥90%) — BELOW THRESHOLD
  ✓ consent: 100% (≥100%)
```

Do NOT include full stack traces. Summarize to actionable information.
```

### 9.2 security-scanner

**File:** `.claude/agents/security-scanner.md`

```markdown
---
name: security-scanner
description: "Scans for COPPA compliance violations, OWASP API Security Top 10 issues, and dependency vulnerabilities. Reports findings with severity and remediation guidance."
allowed-tools: Bash Read Grep
model: claude-sonnet-4-6-20250414
---

# Security Scanner Agent

You are a security specialist for MathPath Oregon, a children's education platform subject to
COPPA regulations. Your job is to identify security and compliance issues.

## Scan Procedures

### 1. COPPA Compliance Scan
```bash
# Check all student-data endpoints have consent guard
grep -rn "async def " apps/api/src/api/v1/ | while read line; do
  FILE=$(echo "$line" | cut -d: -f1)
  FUNC=$(echo "$line" | grep -oP 'def \K\w+')
  if grep -q "student\|assessment\|learning_plan\|practice" "$FILE"; then
    if ! grep -B5 "async def $FUNC" "$FILE" | grep -q "verify_consent_active"; then
      echo "COPPA: $FILE::$FUNC — Missing consent guard"
    fi
  fi
done
```

### 2. PII Exposure Scan
```bash
# Log statements with potential PII
grep -rn "log.*email\|log.*name\|log.*address" apps/api/src/ services/
# LLM prompts with potential PII
grep -rn "student\.name\|parent\.email\|\.first_name" services/*/src/prompts/
# Error messages with potential PII
grep -rn "raise.*email\|raise.*name\|Exception.*email" apps/api/src/
```

### 3. Dependency Vulnerability Scan
```bash
cd apps/web && npm audit --production 2>&1 | tail -20
cd apps/api && pip-audit 2>&1 | tail -20
```

### 4. OWASP API Top 10 Review
Check each vulnerability category against the codebase (see security-coppa-compliance skill).

## Output Format

```
SECURITY SCAN RESULTS
═════════════════════
Scan Date: [timestamp]

CRITICAL (P0):
  1. [Finding] — [File:Line] — [Remediation]

HIGH (P1):
  1. [Finding] — [File:Line] — [Remediation]

MEDIUM (P2):
  1. [Finding] — [File:Line] — [Remediation]

LOW (P3):
  1. [Finding] — [File:Line] — [Remediation]

Dependencies:
  Frontend: X critical, X high, X moderate
  Backend: X critical, X high, X moderate

COPPA Compliance: [PASS/FAIL]
  Endpoints without consent guard: X
  PII in logs: X instances
  PII in LLM prompts: X instances
```
```

### 9.3 spec-researcher

**File:** `.claude/agents/spec-researcher.md`

```markdown
---
name: spec-researcher
description: "Searches the 24-document MathPath specification suite for requirements, design decisions, and standards. Returns relevant excerpts with document references. Use when implementing features that need requirement traceability."
allowed-tools: Read Grep Bash
model: claude-sonnet-4-6-20250414
---

# Spec Researcher Agent

You are a requirements researcher for MathPath Oregon. Your job is to find relevant
specifications, requirements, and design decisions from the 24-document suite.

## Document Index

| ID | File | Content |
|----|------|---------|
| 01 | `docs/01-strategy.md` | Business strategy, market analysis |
| 02 | `docs/02-competitive-analysis.md` | Competitive landscape |
| 03 | `docs/03-prd-stage1.md` | Stage 1 PRD |
| 09 | `docs/09-design-system.md` | Design tokens, components, accessibility |
| 10 | `docs/10-lifecycle-stage1.md` | Stage 1 SDLC (stories, tests, ops) |
| 15 | `docs/15-lifecycle-crosscutting-ops.md` | MLOps, FinOps, SecOps |
| 16 | `docs/16-multigrade-expansion.md` | Multi-grade plan |
| E0 | `eng-docs/ENG-000-foundations.md` | Repo structure, ADRs, coding standards |

## Research Process

1. Parse the research query from the parent context.
2. Grep across all docs for matching terms: `grep -rni "$QUERY" docs/ eng-docs/ --include="*.md"`.
3. Read the surrounding context (20 lines before and after each match).
4. Synthesize findings into a structured response.

## Output Format

```
SPEC RESEARCH: [Query]
═══════════════════════

Finding 1: [Document Title]
  Source: [file.md], Section [X.Y]
  Relevant excerpt: "..."
  Implication for implementation: [brief guidance]

Finding 2: [Document Title]
  Source: [file.md], Section [X.Y]
  Relevant excerpt: "..."
  Implication for implementation: [brief guidance]

Summary: [1-2 sentence synthesis of all findings]
```
```

### 9.4 code-reviewer

**File:** `.claude/agents/code-reviewer.md`

```markdown
---
name: code-reviewer
description: "Reviews code changes against MathPath engineering standards, design system tokens, architecture boundaries, and COPPA compliance. Provides actionable feedback with severity levels."
allowed-tools: Read Grep Bash
model: claude-sonnet-4-6-20250414
---

# Code Reviewer Agent

You are a senior code reviewer for MathPath Oregon. Review the provided code changes against
the project's engineering standards.

## Review Checklist

### Architecture (from ENG-000)
- [ ] Correct layer placement (routes → services → repos → DB)
- [ ] No cross-boundary imports
- [ ] Business logic in service layer, not routes
- [ ] Repository returns Pydantic models, not ORM objects

### Design System (from Doc 09)
- [ ] Semantic design tokens used (no raw hex, no hardcoded px)
- [ ] Correct typography tokens for context (student vs dashboard)
- [ ] Touch targets meet minimum size (48px student, 44px dashboard)
- [ ] Animations respect prefers-reduced-motion

### COPPA Compliance
- [ ] Student data endpoints have verify_consent_active
- [ ] No PII in logs, error messages, or LLM prompts
- [ ] Audit trail for sensitive data access

### Code Quality
- [ ] TypeScript strict mode compliance (no any, no ts-ignore)
- [ ] Pydantic v2 patterns (model_validate, model_dump, ConfigDict)
- [ ] Async patterns (no sync calls in async context)
- [ ] Error handling (custom exceptions, structured responses)
- [ ] Naming conventions followed

### Testing
- [ ] Tests exist for all new code
- [ ] Coverage gates will be met
- [ ] Both happy path and error paths tested
- [ ] COPPA paths have 100% coverage

## Output Format

```
CODE REVIEW: [files reviewed]
═════════════════════════════

Issues Found: X critical, X high, X medium, X low

CRITICAL:
  1. [file:line] — [issue] — [fix suggestion]

HIGH:
  1. [file:line] — [issue] — [fix suggestion]

MEDIUM:
  1. [file:line] — [issue] — [fix suggestion]

Commendations:
  1. [positive observation]

Overall: [APPROVE / REQUEST CHANGES / NEEDS DISCUSSION]
```
```

### 9.5 grade-content-validator

**File:** `.claude/agents/grade-content-validator.md`

```markdown
---
name: grade-content-validator
description: "Validates math content (questions, hints, explanations) against Oregon 2021 Math Standards for a specific grade level. Checks mathematical accuracy, standard alignment, age-appropriate language, and number range compliance."
allowed-tools: Read Grep Bash
model: claude-sonnet-4-6-20250414
---

# Grade Content Validator Agent

You are a math content validation specialist for MathPath Oregon. Your job is to verify that
math questions, hints, and explanations are correct, aligned to Oregon standards, and
appropriate for the target grade level.

## Validation Procedures

### 1. Mathematical Accuracy
- Verify the correct answer is mathematically correct.
- Verify all distractors (wrong answers) are plausible but definitively wrong.
- Check that the solution method matches the grade-level expectations (no shortcuts beyond grade level).

### 2. Standard Alignment
- Verify the question maps to the claimed Oregon standard code.
- Check that the question actually tests what the standard describes.
- Verify DOK level is appropriate (DOK 1 = recall, DOK 2 = application, DOK 3 = strategic thinking).

### 3. Number Range Compliance
Verify numbers in the question fall within grade-appropriate ranges (see grade-specific-patterns skill).

### 4. Language Level
- Flesch-Kincaid Grade Level ≤ target grade + 1.
- No jargon or vocabulary beyond grade level.
- Growth mindset language (no "wrong", "failed", "can't").
- Word problems use familiar, culturally inclusive contexts.

### 5. Visual Compliance
- Fraction visuals use equal-sized parts (not approximate).
- Number lines have consistent intervals.
- Geometric shapes are clearly labeled.
- All visuals have alt text for screen readers.

## Output Format

```
CONTENT VALIDATION: [Question/Content ID]
══════════════════════════════════════════

Standard: [code] — [standard text]
Grade: [grade]

✓ Mathematical accuracy: [PASS/FAIL] — [details if fail]
✓ Standard alignment: [PASS/FAIL] — [details if fail]
✓ Number range: [PASS/FAIL] — [details if fail]
✓ Language level: [PASS/FAIL] — FK grade [X], target ≤ [Y]
✓ Visual compliance: [PASS/FAIL] — [details if fail]

Overall: [VALID / NEEDS REVISION]
Revision notes (if any): [specific fixes needed]
```
```
## 10. MCP Server Configuration

MCP (Model Context Protocol) servers extend Claude Code's capabilities by connecting to external services. MathPath Oregon uses six MCP servers for GitHub integration, database access, design-to-code sync, browser testing, error monitoring, and documentation lookup.

### 10.1 GitHub MCP Server

**Purpose:** PR management, issue tracking, code search, and repository operations without leaving the Claude Code terminal.

**Installation:**
```bash
claude mcp add --scope project github -- npx -y @modelcontextprotocol/server-github
```

**Configuration (`.mcp.json`):**
```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_PAT}"
      }
    }
  }
}
```

**When to use:**
- Creating and reviewing pull requests
- Searching for issues and linking to user stories
- Checking CI/CD workflow status
- Comparing branches for deploy verification

**Integration with skills:**
- `sprint-lifecycle` — Use GitHub MCP to verify PR has passing CI before marking QA phase complete.
- `user-story-tracker` — Search commit history for story IDs (`US-X.Y` references).

---

### 10.2 PostgreSQL MCP Server

**Purpose:** Direct database queries during development — inspect schema, run diagnostic queries, verify migration results, and check seed data.

**Installation:**
```bash
claude mcp add --scope project postgres -- npx -y @modelcontextprotocol/server-postgres
```

**Configuration:**
```json
{
  "mcpServers": {
    "postgres": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres"],
      "env": {
        "DATABASE_URL": "postgresql://mathpath:mathpath@localhost:5432/mathpath_dev"
      }
    }
  }
}
```

**When to use:**
- Inspecting table schemas after migrations
- Verifying seed data (standards, questions) was loaded correctly
- Debugging query performance with `EXPLAIN ANALYZE`
- Checking BKT mastery state values during development
- Verifying COPPA consent records structure

**Safety:** This MCP connects to the LOCAL development database only. The connection string points to `localhost:5432`. Production credentials are never configured in MCP.

**Integration with skills:**
- `oregon-standards-validator` — Query `standards` table to verify all 29 Grade 4 standards are seeded.
- `bkt-model-patterns` — Query `student_skill_states` to inspect BKT mastery values.
- `database-rules` — Verify migration results after `alembic upgrade head`.

---

### 10.3 Figma MCP Server

**Purpose:** Design-to-code sync. Read Figma designs, extract component specs, and verify implementation matches design mockups.

**Installation:**
```bash
claude mcp add --scope project figma -- npx -y @anthropic/figma-mcp-server
```

**Configuration:**
```json
{
  "mcpServers": {
    "figma": {
      "command": "npx",
      "args": ["-y", "@anthropic/figma-mcp-server"],
      "env": {
        "FIGMA_ACCESS_TOKEN": "${FIGMA_PAT}"
      }
    }
  }
}
```

**When to use:**
- Implementing new UI components — extract exact measurements, colors, and typography from Figma.
- Verifying implementation matches design during QA phase.
- Extracting design tokens when design system updates are made.
- Sprint lifecycle Phase 2 (Design) — review Figma mockups before implementation.

**Integration with skills:**
- `mathpath-design-tokens` — Compare implemented tokens against Figma variable collections.
- `mathpath-component-library` — Extract component specs from Figma frames.
- `sprint-lifecycle` — Use Figma MCP during Design phase to verify designs are complete before Implementation.

---

### 10.4 Playwright MCP Server

**Purpose:** Browser automation and testing. Run E2E tests, capture screenshots, and debug UI issues from within Claude Code.

**Installation:**
```bash
claude mcp add --scope project playwright -- npx -y @anthropic/playwright-mcp-server
```

**Configuration:**
```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["-y", "@anthropic/playwright-mcp-server"],
      "env": {
        "BASE_URL": "http://localhost:3000"
      }
    }
  }
}
```

**When to use:**
- Running targeted E2E tests during development
- Capturing screenshots for visual regression comparison
- Debugging UI rendering issues (KaTeX, fraction builders, responsive layout)
- Verifying accessibility with axe-core integration
- Testing cross-browser behavior (Chrome, Safari, Firefox)

**Integration with skills:**
- `mathpath-test-coverage` — Run E2E tests and verify coverage of P0 user journeys.
- `accessibility-enforcer` — Run axe accessibility audit on rendered pages.
- `bdd-scenario-writer` — Execute Gherkin scenarios against the running application.

---

### 10.5 Sentry MCP Server

**Purpose:** Error monitoring and performance tracking. View errors, investigate stack traces, and check error trends from within Claude Code.

**Installation:**
```bash
claude mcp add --scope project sentry -- npx -y @sentry/mcp-server
```

**Configuration:**
```json
{
  "mcpServers": {
    "sentry": {
      "command": "npx",
      "args": ["-y", "@sentry/mcp-server"],
      "env": {
        "SENTRY_AUTH_TOKEN": "${SENTRY_AUTH_TOKEN}",
        "SENTRY_ORG": "mathpath-oregon",
        "SENTRY_PROJECT": "mathpath-api"
      }
    }
  }
}
```

**When to use:**
- Investigating production or staging errors during bug triage
- Checking error frequency and user impact
- Viewing stack traces for reported issues
- Monitoring performance metrics (response times, throughput)
- Verifying that a deploy resolved a specific error

**Integration with skills:**
- `sprint-lifecycle` — Check Sentry for open errors before marking Ops phase complete.
- `security-coppa-compliance` — Monitor for PII exposure in error reports.

---

### 10.6 Context7 MCP Server

**Purpose:** Documentation lookup for third-party libraries. Retrieves up-to-date documentation for React, Next.js, FastAPI, LangGraph, pyBKT, and other dependencies to reduce hallucination risk.

**Installation:**
```bash
claude mcp add --scope project context7 -- npx -y @upstash/context7-mcp@latest
```

**Configuration:**
```json
{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp@latest"]
    }
  }
}
```

**When to use:**
- Looking up current API signatures for React 19, Next.js 15, FastAPI 0.115
- Checking LangGraph 0.2 graph definition patterns and breaking changes
- Verifying pyBKT API usage and available methods
- Checking Pydantic v2 migration patterns (v1 → v2)
- Looking up Tailwind CSS 4 configuration syntax

**Integration with skills:**
- `langgraph-agent-patterns` — Fetch latest LangGraph docs for graph patterns.
- `bkt-model-patterns` — Fetch pyBKT documentation for API details.
- All development work — reduces hallucination by grounding in current docs.

---

### 10.7 Complete MCP Configuration File

**File:** `.mcp.json` (project root, committed to git)

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_PAT}"
      }
    },
    "postgres": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres"],
      "env": {
        "DATABASE_URL": "postgresql://mathpath:mathpath@localhost:5432/mathpath_dev"
      }
    },
    "figma": {
      "command": "npx",
      "args": ["-y", "@anthropic/figma-mcp-server"],
      "env": {
        "FIGMA_ACCESS_TOKEN": "${FIGMA_PAT}"
      }
    },
    "playwright": {
      "command": "npx",
      "args": ["-y", "@anthropic/playwright-mcp-server"],
      "env": {
        "BASE_URL": "http://localhost:3000"
      }
    },
    "sentry": {
      "command": "npx",
      "args": ["-y", "@sentry/mcp-server"],
      "env": {
        "SENTRY_AUTH_TOKEN": "${SENTRY_AUTH_TOKEN}",
        "SENTRY_ORG": "mathpath-oregon",
        "SENTRY_PROJECT": "mathpath-api"
      }
    },
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp@latest"]
    }
  }
}
```

**Note:** Environment variables (`${GITHUB_PAT}`, etc.) are resolved from the developer's shell environment or `.env.local` file. Secrets are never committed to the repository.

---

## 11. Context Management Strategy

### 11.1 The Context Budget

Claude Code operates with a ~200K token context window. This section defines how to manage this finite resource across the complex MathPath Oregon codebase.

#### Token Budget Allocation

```
┌─────────────────────────────────────────────────────────────────┐
│                    200K Token Context Window                      │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Fixed Overhead (~5K tokens, 2.5%)                       │    │
│  │  CLAUDE.md (800) + Skill descriptions (1,600) +          │    │
│  │  Active rules (1,200) + Hook overhead (400)              │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Active Skill Content (~3K–5K tokens, 1.5–2.5%)         │    │
│  │  Full content of 1–2 active skills loaded on demand      │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Working Context (~140K–170K tokens, 70–85%)             │    │
│  │  Code files, documentation, reasoning, conversation      │    │
│  │  THIS IS THE PRODUCTIVE WORKSPACE                        │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Conversation History (~20K–40K tokens, 10–20%)          │    │
│  │  Accumulates over session — triggers compaction          │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### 11.2 Stage-Scoped Sessions

The single most effective context management strategy: **work on one stage at a time.**

Each development stage involves different components, different libraries, and different documentation. Loading Stage 1 (diagnostic assessment) context alongside Stage 3 (LangGraph tutoring) context wastes tokens on irrelevant information.

| Session Type | Scope | Key Files in Context | Estimated Tokens |
|-------------|-------|---------------------|-----------------|
| Stage 1: Diagnostic | Backend routes, BKT, assessment service | `assessment_service.py`, `bkt_service.py`, `question_selection_service.py` | ~30K |
| Stage 1: Frontend | Registration, consent, assessment UI | `consent/page.tsx`, `assessment/[sessionId]/page.tsx`, Zustand stores | ~25K |
| Stage 2: Learning Plans | LLM integration, plan generation | `plan_graph.py`, `learning_plan_service.py`, prompt templates | ~35K |
| Stage 3: Tutoring | LangGraph agents, WebSocket, real-time | `tutor_graph.py`, nodes/, state/, WebSocket handler | ~40K |
| Stage 4: Assessment | IRT/CAT, reporting, PDF generation | `irt_engine.py`, `report_service.py`, chart components | ~35K |
| Stage 5: Billing | Stripe, school onboarding, i18n | `billing_service.py`, i18n configs, school admin | ~30K |

### 11.3 Multi-Session Horizontal Scaling

For complex features that touch multiple system layers, use parallel sessions:

```
Session A (Main)          Session B (Subagent: Test Runner)
├── Implement feature     ├── Run test suite
├── Write code            ├── Report coverage
├── Iterate on design     └── Return results
└── Review test results

Session A (Main)          Session C (Subagent: Spec Researcher)
├── Implement feature     ├── Search 24 docs for requirements
├── Wait for research     ├── Compile findings
└── Apply findings        └── Return research summary
```

This pattern keeps the main session focused on implementation while subagents handle research and validation in isolated context windows.

### 11.4 PreCompact Preservation Strategy

When context approaches the compaction threshold (~150K tokens), the PreCompact hook fires to save critical context. The following information MUST be preserved:

| Category | What to Save | Where to Save |
|----------|-------------|---------------|
| Sprint Context | Current stage, active epic, active story ID | `.claude/context/current-task.md` |
| Decisions Made | Mini-ADRs from this session | `.claude/context/session-decisions.md` |
| Modified Files | List of files changed | `.claude/context/modified-files.txt` |
| Test Results | Pass/fail summary, coverage numbers | `.claude/context/test-results.md` |
| BKT State | Active parameters, thresholds under test | `.claude/context/bkt-context.md` |
| Design Tokens | Tokens referenced in current task | `.claude/context/active-tokens.md` |
| Blocked Items | Issues needing resolution | `.claude/context/blockers.md` |

**What to let go:**
- Full file contents (Claude can re-read files via `Read` tool)
- Verbose error logs (save summary only)
- Exploration paths that were abandoned
- Intermediate reasoning that led to a final decision (save the decision, not the process)
- Large code blocks already committed to git

### 11.5 Compaction Recovery Protocol

After compaction (manual `/compact` or automatic):

1. **SessionStart hook fires** with `compact` matcher → runs `post-compact-recovery.sh`
2. Recovery script reads `.claude/context/recovery.md` and outputs it to stdout
3. Claude receives the recovery context in its new, clean context window
4. Claude should:
   a. Confirm understanding of the current task
   b. Re-read any files listed in the modified files list
   c. Resume work from where the session left off
   d. Ask for clarification only if the recovery context is insufficient

### 11.6 Memory Management Heuristics

| Signal | Action |
|--------|--------|
| Claude repeats previously stated information | Context is getting stale → consider `/compact` |
| Claude forgets a decision made earlier in the session | Conversation history is being pushed out → save decision to file, compact |
| Response quality degrades (generic, less specific) | Context window is full → compact immediately |
| Switching from frontend to backend work | Context domains are diverging → start a new session or compact |
| Finishing one story and starting another | Clean break point → compact and load new story context |
| Error debugging going in circles | Bad context accumulated → compact, re-read error, fresh approach |

---

## 12. Implementation Roadmap

### 12.1 Phase Overview

| Phase | Weeks | Focus | Effort | Dependencies |
|-------|-------|-------|--------|-------------|
| 1 | 1–2 | Foundation | ~16 hrs | None |
| 2 | 3–4 | Core Skills | ~24 hrs | Phase 1 |
| 3 | 5–6 | Domain Skills | ~28 hrs | Phase 2 |
| 4 | 7–8 | Commands, Subagents, MCP | ~18 hrs | Phase 3 |
| 5 | 9–10 | Integration & Tuning | ~14 hrs | Phase 4 |
| **Total** | **10 weeks** | | **~100 hrs** | |

### 12.2 Phase 1: Foundation (Weeks 1–2, ~16 hours)

| Item | Effort | Deliverable |
|------|--------|-------------|
| CLAUDE.md template | 2 hrs | Root `CLAUDE.md` file (148 lines) |
| `.claude/` directory structure | 1 hr | Directory scaffolding |
| `settings.json` base | 2 hrs | Permissions, basic hooks |
| `frontend-rules.md` | 1.5 hrs | React/Next.js/TS conventions |
| `backend-rules.md` | 1.5 hrs | FastAPI/SQLAlchemy/Pydantic conventions |
| `test-rules.md` | 1.5 hrs | Testing pyramid and coverage gates |
| `design-system-rules.md` | 1.5 hrs | Token enforcement basics |
| `database-rules.md` | 1.5 hrs | PostgreSQL/Alembic patterns |
| `coppa-rules.md` | 1.5 hrs | COPPA compliance rules |
| `agent-rules.md` | 1 hr | LangGraph/LLM patterns |
| `infra-rules.md` | 1 hr | Terraform/Docker/CI patterns |
| **Phase 1 Total** | **~16 hrs** | CLAUDE.md + 8 rule files + settings.json |

### 12.3 Phase 2: Core Skills (Weeks 3–4, ~24 hours)

| Item | Effort | Deliverable | Priority |
|------|--------|-------------|----------|
| `mathpath-design-tokens` | 8 hrs | Full token reference skill | P0 |
| `mathpath-test-coverage` | 6 hrs | Testing pyramid enforcement skill | P0 |
| `architecture-enforcer` | 6 hrs | Boundary enforcement + validation script | P0 |
| `api-contract-enforcement` | 4 hrs | OpenAPI/Pydantic/TS contract validation | P0 |
| **Phase 2 Total** | **~24 hrs** | 4 core skills |

### 12.4 Phase 3: Domain Skills (Weeks 5–6, ~28 hours)

| Item | Effort | Deliverable | Priority |
|------|--------|-------------|----------|
| `bkt-model-patterns` | 6 hrs | pyBKT implementation patterns | P1 |
| `security-coppa-compliance` | 8 hrs | COPPA + OWASP compliance checks | P0 |
| `sprint-lifecycle` | 7 hrs | 7-phase SDLC gate enforcement | P0 |
| `bdd-scenario-writer` | 5 hrs | Gherkin generation from user stories | P1 |
| `accessibility-enforcer` | 6 hrs | WCAG AA/AAA enforcement | P0 |
| SessionStart hook | 2 hrs | Environment verification script | P0 |
| PreBash guard hook | 2 hrs | Destructive command blocking | P0 |
| PostEdit validation hook | 2 hrs | Token and PII validation | P0 |
| Stop verification hook | 2 hrs | Quality gate checks | P1 |
| **Phase 3 Total** | **~28 hrs** | 5 domain skills + 4 hooks (note: some items overlap with hook budgets) |

### 12.5 Phase 4: Commands, Subagents, MCP (Weeks 7–8, ~18 hours)

| Item | Effort | Deliverable | Priority |
|------|--------|-------------|----------|
| `/custom:implement` | 2 hrs | Story implementation workflow | P0 |
| `/custom:test` | 1.5 hrs | Test execution command | P0 |
| `/custom:deploy-check` | 1.5 hrs | Deployment verification | P1 |
| `/custom:story-status` | 1.5 hrs | Story tracking report | P1 |
| `/custom:spec-search` | 1 hr | Documentation search | P1 |
| `/custom:stage-context` | 1 hr | Stage context loading | P0 |
| `/custom:grade-check` | 1 hr | Grade-level validation | P2 |
| `test-runner` subagent | 2 hrs | Isolated test execution | P0 |
| `security-scanner` subagent | 2 hrs | Security/COPPA scanning | P0 |
| `spec-researcher` subagent | 1.5 hrs | Documentation research | P1 |
| `code-reviewer` subagent | 2 hrs | Automated code review | P1 |
| `grade-content-validator` subagent | 1.5 hrs | Content validation | P2 |
| MCP server configuration | 2 hrs | 6 MCP servers configured | P1 |
| **Phase 4 Total** | **~18 hrs** | 7 commands + 5 subagents + MCP |

### 12.6 Phase 5: Integration & Tuning (Weeks 9–10, ~14 hours)

| Item | Effort | Deliverable |
|------|--------|-------------|
| Remaining skills: `mathpath-component-library` | 3 hrs | Component patterns skill |
| Remaining skills: `user-story-tracker` | 2 hrs | Story tracking skill |
| Remaining skills: `langgraph-agent-patterns` | 4 hrs | LangGraph patterns skill |
| Remaining skills: `oregon-standards-validator` | 2 hrs | Standards validation skill |
| Remaining skills: `grade-specific-patterns` | 2 hrs | Grade adaptation skill |
| Remaining skills: `strategic-compaction` | 1 hr | Compaction strategy skill |
| Remaining skills: `llm-cost-optimizer` | 2 hrs | Cost optimization skill |
| Integration testing | 4 hrs | Test all skills/hooks/commands together |
| Tuning and iteration | 4 hrs | Adjust based on real usage feedback |
| Documentation | 2 hrs | Update this document with learnings |
| **Phase 5 Total** | **~14 hrs** | 7 remaining skills + integration + tuning |

> **Solo Development Context:** The 100-hour / 10-week estimate above assumes dedicated developer time. For a solo developer with AI agent assistance running this alongside product development, plan for 15–20 hours/month over 5–6 months, meaning Claude Code customization matures progressively through Stage 1–2 rather than being fully built upfront.

---

## 13. Skills-to-Lifecycle Mapping Matrix

This matrix shows which skills, hooks, commands, and subagents are relevant at each development stage and lifecycle phase.

### 13.1 Stage Activation Matrix

| Skill / Component | S1 | S2 | S3 | S4 | S5 | Notes |
|-------------------|:--:|:--:|:--:|:--:|:--:|-------|
| **Skills** | | | | | | |
| `mathpath-design-tokens` | ● | ● | ● | ● | ● | All stages — UI exists in every stage |
| `mathpath-component-library` | ● | ● | ● | ● | ● | All stages |
| `mathpath-test-coverage` | ● | ● | ● | ● | ● | All stages |
| `bdd-scenario-writer` | ● | ● | ● | ● | ● | All stages |
| `security-coppa-compliance` | ● | ● | ● | ● | ● | All stages — COPPA always applies |
| `sprint-lifecycle` | ● | ● | ● | ● | ● | All stages |
| `user-story-tracker` | ● | ● | ● | ● | ● | All stages |
| `architecture-enforcer` | ● | ● | ● | ● | ● | All stages |
| `bkt-model-patterns` | ● | ● | ● | ● | ○ | S1–S4 (BKT is core to assessment) |
| `langgraph-agent-patterns` | ○ | ● | ● | ● | ● | S2+ (agents introduced in S2) |
| `api-contract-enforcement` | ● | ● | ● | ● | ● | All stages |
| `oregon-standards-validator` | ● | ● | ● | ● | ● | All stages |
| `grade-specific-patterns` | ○ | ○ | ● | ● | ● | S3+ (multi-grade expansion) |
| `strategic-compaction` | ● | ● | ● | ● | ● | All stages |
| `llm-cost-optimizer` | ○ | ● | ● | ● | ● | S2+ (LLM costs start in S2) |
| `accessibility-enforcer` | ● | ● | ● | ● | ● | All stages |
| **Hooks** | | | | | | |
| SessionStart | ● | ● | ● | ● | ● | All stages |
| PreToolUse (Bash guard) | ● | ● | ● | ● | ● | All stages |
| PostToolUse (Edit validate) | ● | ● | ● | ● | ● | All stages |
| Stop (Verify) | ● | ● | ● | ● | ● | All stages |
| SubagentStop (Quality) | ● | ● | ● | ● | ● | All stages |
| **Commands** | | | | | | |
| `/custom:implement` | ● | ● | ● | ● | ● | All stages |
| `/custom:test` | ● | ● | ● | ● | ● | All stages |
| `/custom:deploy-check` | ● | ● | ● | ● | ● | All stages |
| `/custom:story-status` | ● | ● | ● | ● | ● | All stages |
| `/custom:spec-search` | ● | ● | ● | ● | ● | All stages |
| `/custom:stage-context` | ● | ● | ● | ● | ● | All stages |
| `/custom:grade-check` | ○ | ○ | ● | ● | ● | S3+ (multi-grade) |
| **Subagents** | | | | | | |
| `test-runner` | ● | ● | ● | ● | ● | All stages |
| `security-scanner` | ● | ● | ● | ● | ● | All stages |
| `spec-researcher` | ● | ● | ● | ● | ● | All stages |
| `code-reviewer` | ● | ● | ● | ● | ● | All stages |
| `grade-content-validator` | ○ | ○ | ● | ● | ● | S3+ (multi-grade) |

**Legend:** ● = Active, ○ = Not yet needed

### 13.2 Lifecycle Phase Activation Matrix

| Skill / Component | PRD | Design | Arch | Impl | Test | QA | Ops |
|-------------------|:---:|:------:|:----:|:----:|:----:|:--:|:---:|
| `mathpath-design-tokens` | | ● | | ● | | ● | |
| `mathpath-component-library` | | ● | | ● | | ● | |
| `mathpath-test-coverage` | | | | | ● | | |
| `bdd-scenario-writer` | ● | | | | ● | | |
| `security-coppa-compliance` | | | ● | ● | ● | ● | ● |
| `sprint-lifecycle` | ● | ● | ● | ● | ● | ● | ● |
| `user-story-tracker` | ● | | | ● | ● | | |
| `architecture-enforcer` | | | ● | ● | | ● | |
| `bkt-model-patterns` | | | ● | ● | ● | | |
| `langgraph-agent-patterns` | | | ● | ● | ● | | |
| `api-contract-enforcement` | | | ● | ● | ● | | |
| `oregon-standards-validator` | ● | | | ● | ● | ● | |
| `grade-specific-patterns` | | ● | | ● | | ● | |
| `strategic-compaction` | | | | ● | | | |
| `llm-cost-optimizer` | | | ● | ● | | | ● |
| `accessibility-enforcer` | | ● | | ● | ● | ● | |
| `/custom:implement` | | | | ● | | | |
| `/custom:test` | | | | | ● | | |
| `/custom:deploy-check` | | | | | | | ● |
| `/custom:story-status` | ● | | | ● | ● | | |
| `/custom:spec-search` | ● | ● | ● | ● | | | |
| `test-runner` (subagent) | | | | | ● | | |
| `security-scanner` (subagent) | | | | | ● | ● | ● |
| `code-reviewer` (subagent) | | | | | | ● | |

---

## 14. Marketplace vs. Custom Analysis

This section evaluates each skill against existing community resources to determine build, buy, or customize decisions.

### 14.1 Analysis Table

| Skill | Community Option | Install Command | Customization Needed | Decision | Rationale |
|-------|-----------------|-----------------|---------------------|----------|-----------|
| `mathpath-design-tokens` | Frontend Design skill (277K installs) | `/install anthropics/skills#frontend-design` | Heavy — MathPath has its own token system | **Build custom** | The community skill enforces general design principles. MathPath needs exact token values from Doc 09 (specific hex codes, type scale, spacing) that no generic skill provides. |
| `mathpath-component-library` | Vercel Composition Patterns | `/install vercel/skills#composition-patterns` | Heavy — MathPath uses Atomic Design + math components | **Build custom** | Vercel patterns are useful but generic. MathPath needs FractionBuilder, NumberLine, and other math-specific patterns. |
| `mathpath-test-coverage` | TDD Workflow (marketplace) | `/install anthropics/skills#tdd-workflow` | Moderate — add MathPath coverage gates | **Build custom** | TDD skill enforces test-first workflow but not project-specific coverage thresholds (90% BKT, 100% COPPA). |
| `bdd-scenario-writer` | None | — | N/A | **Build from scratch** | No community skill generates Gherkin from user story acceptance criteria with project-specific step definitions. |
| `security-coppa-compliance` | Trail of Bits Security | `/install trailofbits/skills#security` | Heavy — add COPPA-specific checks | **Build custom** | Trail of Bits covers general security (CodeQL, Semgrep) but nothing COPPA-specific. Children's privacy law requires custom rules. |
| `sprint-lifecycle` | None | — | N/A | **Build from scratch** | The 7-phase SDLC gate model is unique to MathPath. No community skill enforces project-specific lifecycle phases. |
| `user-story-tracker` | None | — | N/A | **Build from scratch** | Tightly coupled to MathPath's lifecycle documents and story ID format. |
| `architecture-enforcer` | Superpowers (40.9K stars) | `/install obra/superpowers` | Moderate — extract boundary enforcement patterns | **Build custom** | Superpowers provides general multi-step planning but not MathPath-specific boundary rules. Can borrow planning patterns. |
| `bkt-model-patterns` | None | — | N/A | **Build from scratch** | Bayesian Knowledge Tracing is a niche educational technology domain. No community resources exist. |
| `langgraph-agent-patterns` | None specific to LangGraph 0.2 | — | N/A | **Build from scratch** | LangGraph patterns are evolving rapidly. Community skills exist for general agent patterns but not the specific graph architectures MathPath needs. |
| `api-contract-enforcement` | None | — | N/A | **Build from scratch** | Contract enforcement between Pydantic v2 and TypeScript types is project-specific. |
| `oregon-standards-validator` | None | — | N/A | **Build from scratch** | Oregon math standards are domain-specific educational content. No community skill exists. |
| `grade-specific-patterns` | None | — | N/A | **Build from scratch** | Grade-band-specific UI rules are unique to children's educational software. |
| `strategic-compaction` | Simplify skill (community) | `/install community/simplify` | Light — add MathPath-specific preservation rules | **Build custom** | The Simplify skill helps with code simplification. Compaction strategy is broader — context preservation, recovery, multi-session patterns. |
| `llm-cost-optimizer` | None | — | N/A | **Build from scratch** | Per-student cost attribution with model routing is project-specific. |
| `accessibility-enforcer` | Vercel Web Design Guidelines | `/install vercel/skills#web-guidelines` | Moderate — add AAA for student content, math accessibility | **Build custom** | Vercel guidelines cover 100+ accessibility rules. MathPath needs AAA (not just AA) for student content and math-specific accessibility (KaTeX aria-labels, fraction builder keyboard nav). |

### 14.2 Summary

| Decision | Count | Skills |
|----------|-------|--------|
| Build from scratch | 9 | bdd-scenario-writer, sprint-lifecycle, user-story-tracker, bkt-model-patterns, langgraph-agent-patterns, api-contract-enforcement, oregon-standards-validator, grade-specific-patterns, llm-cost-optimizer |
| Build custom (inspired by community) | 7 | mathpath-design-tokens, mathpath-component-library, mathpath-test-coverage, security-coppa-compliance, architecture-enforcer, strategic-compaction, accessibility-enforcer |
| Use community directly | 0 | — (all require at least moderate customization for MathPath's domain) |

### 14.3 Recommended Community Skills to Install Alongside

While none replace MathPath custom skills, these community skills complement them:

| Community Skill | Purpose | Install |
|----------------|---------|---------|
| Frontend Design | General design direction for non-token decisions | `/install anthropics/skills#frontend-design` |
| Simplify | Post-implementation code cleanup | `/install community/simplify` |
| TDD Workflow | General test-first discipline | `/install anthropics/skills#tdd-workflow` |
| Trail of Bits Security | General security scanning (CodeQL, Semgrep) | `/install trailofbits/skills#security` |
| Superpowers | Multi-step planning and subagent coordination | `/install obra/superpowers` |

---

## 15. Appendix: Configuration File Reference

### 15.1 Complete File Tree

```
mathpath/
├── CLAUDE.md                              # Root context (148 lines)
├── .mcp.json                              # MCP server config (6 servers)
├── .claude/
│   ├── settings.json                      # Hooks, permissions, project settings
│   ├── settings.local.json                # Developer-local overrides (gitignored)
│   ├── context/                           # Session context preservation
│   │   ├── current-stage.txt              # Active development stage
│   │   ├── current-task.md                # Active task description
│   │   ├── recovery.md                    # Compaction recovery context
│   │   ├── session-decisions.md           # Decisions made this session
│   │   ├── modified-files.txt             # Files changed this session
│   │   └── test-results.md                # Latest test run results
│   ├── hooks/                             # Hook scripts
│   │   ├── session-start.sh               # SessionStart handler
│   │   ├── post-compact-recovery.sh       # Post-compaction recovery
│   │   ├── pre-bash-guard.sh              # PreToolUse Bash validation
│   │   ├── post-edit-validate.sh          # PostToolUse Edit/Write validation
│   │   ├── stop-verify.sh                 # Stop quality verification
│   │   └── save-context.sh                # Context preservation utility
│   ├── rules/                             # Auto-loading rule files
│   │   ├── frontend-rules.md              # apps/web/**/*.tsx, *.ts
│   │   ├── backend-rules.md               # apps/api/**/*.py, services/**/*.py
│   │   ├── agent-rules.md                 # services/agent-engine/**/*.py
│   │   ├── test-rules.md                  # **/tests/**/*
│   │   ├── infra-rules.md                 # infrastructure/**/*
│   │   ├── design-system-rules.md         # packages/ui/**/*
│   │   ├── database-rules.md              # **/db/**/*.py, **/alembic/**/*
│   │   └── coppa-rules.md                 # **/security.py, **/consent*
│   ├── skills/                            # Skill definitions (16 skills)
│   │   ├── mathpath-design-tokens/SKILL.md
│   │   ├── mathpath-component-library/SKILL.md
│   │   ├── mathpath-test-coverage/SKILL.md
│   │   ├── bdd-scenario-writer/SKILL.md
│   │   ├── security-coppa-compliance/SKILL.md
│   │   ├── sprint-lifecycle/SKILL.md
│   │   ├── user-story-tracker/SKILL.md
│   │   ├── architecture-enforcer/SKILL.md
│   │   ├── bkt-model-patterns/SKILL.md
│   │   ├── langgraph-agent-patterns/SKILL.md
│   │   ├── api-contract-enforcement/SKILL.md
│   │   ├── oregon-standards-validator/SKILL.md
│   │   ├── grade-specific-patterns/SKILL.md
│   │   ├── strategic-compaction/SKILL.md
│   │   ├── llm-cost-optimizer/SKILL.md
│   │   └── accessibility-enforcer/SKILL.md
│   ├── commands/                           # Slash commands (7 commands)
│   │   ├── implement.md                   # /custom:implement [story-id]
│   │   ├── test.md                        # /custom:test [scope]
│   │   ├── deploy-check.md               # /custom:deploy-check [env]
│   │   ├── story-status.md               # /custom:story-status [stage]
│   │   ├── spec-search.md                # /custom:spec-search [query]
│   │   ├── stage-context.md              # /custom:stage-context [stage]
│   │   └── grade-check.md                # /custom:grade-check [grade]
│   └── agents/                            # Subagent definitions (5 agents)
│       ├── test-runner.md                 # Isolated test execution
│       ├── security-scanner.md            # COPPA + OWASP scanning
│       ├── spec-researcher.md             # Documentation research
│       ├── code-reviewer.md               # Code review automation
│       └── grade-content-validator.md     # Math content validation
```

### 15.2 .gitignore Additions

```gitignore
# Claude Code local settings
.claude/settings.local.json

# Session context (ephemeral)
.claude/context/

# MCP local env (if not using shell env vars)
.env.mcp.local
```

### 15.3 settings.local.json Template

Developer-local overrides that are not committed to the repository:

```json
{
  "preferences": {
    "model": "claude-sonnet-4-6-20250414",
    "effort": "high",
    "auto_compact": true,
    "notifications": true
  },
  "mcp_env": {
    "GITHUB_PAT": "ghp_xxxxxxxxxxxxxxxxxxxx",
    "FIGMA_PAT": "figd_xxxxxxxxxxxxxxxxxxxx",
    "SENTRY_AUTH_TOKEN": "sntrys_xxxxxxxxxxxx"
  }
}
```

### 15.4 Quick Reference Card

For daily use, the following commands and patterns should be memorized:

| Action | Command |
|--------|---------|
| Start implementing a story | `/custom:implement US-1.3` |
| Run tests for current changes | `/custom:test` |
| Check deployment readiness | `/custom:deploy-check staging` |
| Find a requirement | `/custom:spec-search COPPA consent flow` |
| Load stage context | `/custom:stage-context 1` |
| Check story progress | `/custom:story-status 1` |
| Validate grade content | `/custom:grade-check 4` |
| Compact with context preservation | `/compact` (hooks handle preservation) |
| View active hooks | `/hooks` |
| View installed skills | `/skills` |

---

*End of Document CC-017 — MathPath Oregon Claude Code Skills & Plugins Specification*
