# Engineering Foundations: MathPath Oregon

> **Document ID:** ENG-000  
> **Status:** Living Document  
> **Last Updated:** 2026-04-04  
> **Owner:** Engineering Lead  
> **Audience:** Every engineer, every AI coding agent, every contributor — read this FIRST.

MathPath Oregon is an AI-powered adaptive math learning application aligned with Oregon's K–8 mathematics standards. It combines Bayesian Knowledge Tracing (BKT) with frontier LLM tutoring to deliver personalized diagnostic assessments, learning plans, and practice sessions for students.

This document defines how ALL code is written, reviewed, tested, and deployed across all 5 development stages. No code is merged that violates these standards — whether written by a human or an AI model.

---

## 1. Repository Structure (Monorepo)

We use a **pnpm workspaces + Turborepo** monorepo. Turborepo handles task orchestration and caching; pnpm handles dependency management with strict isolation. Python services live alongside TypeScript packages but are managed independently via `pyproject.toml` and virtual environments.

### 1.1 Full Directory Tree

```
mathpath/
├── .github/
│   ├── workflows/
│   │   ├── ci.yml                      # PR checks: lint, type, test, build
│   │   ├── deploy-staging.yml          # Deploy to staging on merge to main
│   │   ├── deploy-production.yml       # Deploy to production on release tag
│   │   ├── llm-contract-tests.yml      # Weekly LLM output schema validation
│   │   └── dependency-audit.yml        # Weekly dependency vulnerability scan
│   ├── PULL_REQUEST_TEMPLATE.md
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.md
│   │   ├── feature_request.md
│   │   └── adr_proposal.md
│   └── CODEOWNERS
│
├── apps/
│   ├── web/                            # Next.js 15 frontend application
│   │   ├── src/
│   │   │   ├── app/                    # Next.js App Router pages & layouts
│   │   │   │   ├── (auth)/             # Auth-gated route group
│   │   │   │   ├── (public)/           # Public marketing pages
│   │   │   │   ├── (student)/          # Student dashboard routes
│   │   │   │   ├── (parent)/           # Parent dashboard routes
│   │   │   │   ├── api/                # Next.js API routes (BFF layer)
│   │   │   │   ├── layout.tsx
│   │   │   │   └── global-error.tsx
│   │   │   ├── components/             # App-specific components
│   │   │   │   ├── assessment/         # Diagnostic assessment UI
│   │   │   │   ├── practice/           # Practice session UI
│   │   │   │   ├── dashboard/          # Dashboard widgets
│   │   │   │   ├── learning-plan/      # Learning plan display
│   │   │   │   └── layout/             # Header, sidebar, nav
│   │   │   ├── hooks/                  # App-specific custom hooks
│   │   │   ├── lib/                    # App utilities (api client, auth helpers)
│   │   │   ├── stores/                 # Zustand stores
│   │   │   │   ├── assessment-store.ts
│   │   │   │   ├── session-store.ts
│   │   │   │   └── preferences-store.ts
│   │   │   └── styles/                 # Global styles, Tailwind config
│   │   ├── public/                     # Static assets
│   │   ├── tests/
│   │   │   ├── unit/                   # Jest + RTL component tests
│   │   │   ├── integration/            # MSW-powered API integration tests
│   │   │   └── e2e/                    # Playwright E2E tests
│   │   ├── next.config.ts
│   │   ├── tailwind.config.ts
│   │   ├── tsconfig.json
│   │   ├── jest.config.ts
│   │   ├── playwright.config.ts
│   │   ├── CLAUDE.md                   # Claude Code context for frontend
│   │   └── package.json
│   │
│   └── api/                            # FastAPI backend application
│       ├── src/
│       │   ├── __init__.py
│       │   ├── main.py                 # FastAPI app factory, middleware, lifespan
│       │   ├── api/                    # Route definitions (thin controllers)
│       │   │   ├── __init__.py
│       │   │   ├── v1/
│       │   │   │   ├── __init__.py
│       │   │   │   ├── router.py       # v1 router aggregator
│       │   │   │   ├── assessments.py
│       │   │   │   ├── students.py
│       │   │   │   ├── learning_plans.py
│       │   │   │   ├── practice.py
│       │   │   │   ├── parents.py
│       │   │   │   └── health.py
│       │   │   └── deps.py             # Shared FastAPI dependencies
│       │   ├── models/                 # Pydantic v2 request/response schemas
│       │   │   ├── __init__.py
│       │   │   ├── assessment.py
│       │   │   ├── student.py
│       │   │   ├── learning_plan.py
│       │   │   ├── practice.py
│       │   │   └── common.py           # Shared base models, pagination
│       │   ├── service/                # Business logic layer
│       │   │   ├── __init__.py
│       │   │   ├── assessment_service.py
│       │   │   ├── student_service.py
│       │   │   ├── learning_plan_service.py
│       │   │   ├── practice_service.py
│       │   │   └── parent_service.py
│       │   ├── repository/             # Data access layer (SQLAlchemy)
│       │   │   ├── __init__.py
│       │   │   ├── base.py             # Base repository with common CRUD
│       │   │   ├── assessment_repo.py
│       │   │   ├── student_repo.py
│       │   │   ├── learning_plan_repo.py
│       │   │   └── practice_repo.py
│       │   ├── db/                     # Database configuration
│       │   │   ├── __init__.py
│       │   │   ├── session.py          # Async session factory
│       │   │   ├── base.py             # Declarative base, mixins
│       │   │   └── tables/             # SQLAlchemy table models
│       │   │       ├── __init__.py
│       │   │       ├── student.py
│       │   │       ├── assessment.py
│       │   │       ├── learning_plan.py
│       │   │       ├── practice.py
│       │   │       ├── consent.py
│       │   │       └── audit_log.py
│       │   ├── core/                   # Cross-cutting concerns
│       │   │   ├── __init__.py
│       │   │   ├── config.py           # Pydantic Settings (env vars)
│       │   │   ├── security.py         # Auth0 JWT validation, COPPA checks
│       │   │   ├── exceptions.py       # Custom exception hierarchy
│       │   │   ├── middleware.py        # Request logging, CORS, rate limiting
│       │   │   └── constants.py
│       │   └── clients/                # External service clients
│       │       ├── __init__.py
│       │       ├── llm_client.py       # LiteLLM wrapper — ALL LLM calls go through here; see ADR-009
│       │       ├── redis_client.py
│       │       └── s3_client.py
│       ├── alembic/
│       │   ├── alembic.ini
│       │   ├── env.py
│       │   └── versions/               # Migration files
│       ├── tests/
│       │   ├── unit/
│       │   ├── integration/
│       │   ├── conftest.py
│       │   └── fixtures/
│       ├── prompts/                    # LLM prompt templates
│       │   ├── tutor_hint_v1.0.jinja2
│       │   ├── question_gen_v1.0.jinja2
│       │   └── learning_plan_v1.0.jinja2
│       ├── pyproject.toml
│       ├── CLAUDE.md                   # Claude Code context for API
│       └── README.md
│
├── packages/
│   ├── ui/                             # Shared React component library
│   │   ├── src/
│   │   │   ├── components/
│   │   │   │   ├── Button/
│   │   │   │   ├── Card/
│   │   │   │   ├── Modal/
│   │   │   │   ├── ProgressBar/
│   │   │   │   ├── Badge/
│   │   │   │   └── index.ts
│   │   │   └── index.ts
│   │   ├── package.json
│   │   └── tsconfig.json
│   │
│   ├── math-renderer/                  # KaTeX wrapper components
│   │   ├── src/
│   │   │   ├── MathDisplay.tsx         # Block math rendering
│   │   │   ├── MathInline.tsx          # Inline math rendering
│   │   │   ├── MathInput.tsx           # Math input with preview
│   │   │   ├── FractionBuilder.tsx     # Visual fraction builder
│   │   │   ├── NumberLine.tsx          # Interactive number line
│   │   │   └── index.ts
│   │   ├── package.json
│   │   └── tsconfig.json
│   │
│   ├── types/                          # Shared TypeScript type definitions
│   │   ├── src/
│   │   │   ├── api.ts                  # API request/response types
│   │   │   ├── assessment.ts           # Assessment domain types
│   │   │   ├── student.ts              # Student domain types
│   │   │   ├── learning-plan.ts        # Learning plan types
│   │   │   ├── practice.ts             # Practice session types
│   │   │   ├── standards.ts            # Oregon math standards types
│   │   │   └── index.ts
│   │   ├── package.json
│   │   └── tsconfig.json
│   │
│   ├── config/                         # Shared tooling configurations
│   │   ├── eslint/
│   │   │   └── base.js                 # Base ESLint flat config
│   │   ├── typescript/
│   │   │   ├── base.json               # Base tsconfig
│   │   │   ├── nextjs.json             # Next.js tsconfig
│   │   │   └── library.json            # Library tsconfig
│   │   ├── prettier/
│   │   │   └── index.js                # Prettier config
│   │   └── package.json
│   │
│   └── db-schema/                      # Shared DB schema reference
│       ├── src/
│       │   ├── schema.ts               # TypeScript types mirroring DB schema
│       │   └── enums.ts                # Shared enums (grade levels, domains)
│       ├── package.json
│       └── tsconfig.json
│
├── services/
│   ├── agent-engine/                   # LangGraph AI agent system
│   │   ├── src/
│   │   │   ├── __init__.py
│   │   │   ├── graphs/                 # LangGraph graph definitions
│   │   │   │   ├── __init__.py
│   │   │   │   ├── tutor_graph.py      # Tutoring conversation graph
│   │   │   │   ├── diagnostic_graph.py # Diagnostic assessment graph
│   │   │   │   └── plan_graph.py       # Learning plan generation graph
│   │   │   ├── nodes/                  # Individual graph nodes
│   │   │   │   ├── __init__.py
│   │   │   │   ├── classify_intent.py
│   │   │   │   ├── generate_hint.py
│   │   │   │   ├── evaluate_response.py
│   │   │   │   ├── select_question.py
│   │   │   │   └── update_mastery.py
│   │   │   ├── state/                  # Graph state definitions
│   │   │   │   ├── __init__.py
│   │   │   │   ├── tutor_state.py
│   │   │   │   └── diagnostic_state.py
│   │   │   ├── tools/                  # LangGraph tool definitions
│   │   │   ├── prompts/                # Agent-specific prompt templates
│   │   │   │   ├── hint_generation_v1.0.jinja2
│   │   │   │   ├── response_eval_v1.0.jinja2
│   │   │   │   └── scaffolding_v1.0.jinja2
│   │   │   └── core/
│   │   │       ├── __init__.py
│   │   │       ├── config.py
│   │   │       └── llm_client.py
│   │   ├── tests/
│   │   │   ├── unit/
│   │   │   ├── integration/
│   │   │   └── fixtures/
│   │   │       ├── mock_states.py      # Deterministic state fixtures
│   │   │       └── golden_outputs/     # Golden input/output pairs
│   │   ├── pyproject.toml
│   │   ├── CLAUDE.md
│   │   └── README.md
│   │
│   ├── question-generator/             # LLM question generation pipeline
│   │   ├── src/
│   │   │   ├── __init__.py
│   │   │   ├── generator.py            # Main generation pipeline
│   │   │   ├── validators.py           # Math correctness validators
│   │   │   ├── templates/              # Question template structures
│   │   │   ├── standards/              # Oregon standards mapping data
│   │   │   │   └── or_math_k8.json     # All 38+ standards with metadata
│   │   │   └── prompts/
│   │   │       ├── question_gen_v1.0.jinja2
│   │   │       └── distractor_gen_v1.0.jinja2
│   │   ├── tests/
│   │   ├── pyproject.toml
│   │   └── README.md
│   │
│   └── bkt-engine/                     # Bayesian Knowledge Tracing service
│       ├── src/
│       │   ├── __init__.py
│       │   ├── models/                 # Pydantic models for BKT I/O
│       │   │   ├── __init__.py
│       │   │   ├── mastery.py          # Mastery state models
│       │   │   └── skill.py            # Skill parameter models
│       │   ├── engine/                 # Core BKT logic
│       │   │   ├── __init__.py
│       │   │   ├── tracker.py          # pyBKT wrapper + extensions
│       │   │   ├── roster.py           # Student roster management
│       │   │   └── calibration.py      # Parameter calibration routines
│       │   ├── repository/
│       │   │   ├── __init__.py
│       │   │   └── mastery_repo.py     # Mastery state persistence
│       │   ├── service/
│       │   │   ├── __init__.py
│       │   │   └── mastery_service.py  # Business logic for mastery updates
│       │   └── api/
│       │       ├── __init__.py
│       │       └── router.py           # FastAPI router (if standalone)
│       ├── tests/
│       │   ├── unit/
│       │   │   ├── test_tracker.py
│       │   │   └── test_calibration.py
│       │   ├── integration/
│       │   └── fixtures/
│       │       ├── skill_params.json   # Pre-calibrated skill parameters
│       │       └── response_sequences/ # Test response sequences
│       ├── pyproject.toml
│       ├── CLAUDE.md
│       └── README.md
│
├── infrastructure/
│   ├── terraform/
│   │   ├── environments/
│   │   │   ├── staging/
│   │   │   │   ├── main.tf
│   │   │   │   ├── variables.tf
│   │   │   │   └── terraform.tfvars
│   │   │   └── production/
│   │   │       ├── main.tf
│   │   │       ├── variables.tf
│   │   │       └── terraform.tfvars
│   │   ├── modules/
│   │   │   ├── ecs/                    # ECS/Fargate cluster & services
│   │   │   ├── rds/                    # RDS PostgreSQL 17
│   │   │   ├── elasticache/            # Redis 7 cluster
│   │   │   ├── s3/                     # S3 buckets (assets, backups)
│   │   │   ├── cloudfront/             # CDN distribution
│   │   │   ├── secrets/                # Secrets Manager
│   │   │   ├── vpc/                    # VPC, subnets, security groups
│   │   │   └── monitoring/             # CloudWatch, alarms
│   │   └── backend.tf                  # Remote state (S3 + DynamoDB)
│   │
│   ├── docker/
│   │   ├── api.Dockerfile              # FastAPI production image
│   │   ├── agent-engine.Dockerfile     # Agent engine image
│   │   ├── bkt-engine.Dockerfile       # BKT service image
│   │   ├── docker-compose.yml          # Local dev: Postgres, Redis, LocalStack
│   │   ├── docker-compose.test.yml     # Test environment
│   │   └── .dockerignore
│   │
│   └── scripts/
│       ├── setup.sh                    # One-command dev environment setup
│       ├── seed-db.sh                  # Database seeding
│       ├── migrate.sh                  # Run Alembic migrations
│       ├── rotate-secrets.sh           # Secret rotation helper
│       └── health-check.sh             # Service health verification
│
├── docs/
│   ├── adr/                            # Architecture Decision Records
│   │   ├── template.md
│   │   ├── ADR-001-monorepo.md
│   │   ├── ADR-002-fastapi.md
│   │   ├── ADR-003-pgvector.md
│   │   ├── ADR-004-langgraph.md
│   │   ├── ADR-005-auth0-coppa.md
│   │   ├── ADR-006-pybkt.md
│   │   ├── ADR-007-hybrid-infra.md
│   │   └── ADR-008-feature-flags.md
│   ├── api/                            # Auto-generated OpenAPI docs
│   │   └── openapi.json
│   ├── runbooks/                       # Operational runbooks
│   │   ├── incident-response.md
│   │   ├── database-failover.md
│   │   ├── secret-rotation.md
│   │   ├── llm-fallback.md
│   │   └── coppa-data-deletion.md
│   └── standards/                      # Oregon math standards reference
│       └── or-math-k8-standards.json
│
├── .claudecode/                        # Claude Code project configuration
│   └── settings.json
├── CLAUDE.md                           # Root Claude Code context file
├── turbo.json                          # Turborepo pipeline config
├── pnpm-workspace.yaml                 # pnpm workspace definition
├── package.json                        # Root package.json (scripts, devDeps)
├── Makefile                            # Developer command reference
├── .pre-commit-config.yaml             # Pre-commit hooks
├── .env.example                        # Environment variable template
├── .gitignore
└── README.md
```

### 1.2 Folder-by-Folder Reference

#### `.github/workflows/`
**Purpose:** All CI/CD pipeline definitions as GitHub Actions workflows.  
**Belongs here:** Workflow YAML files for build, test, deploy, and scheduled jobs.  
**Does NOT belong here:** Application code, scripts that aren't workflow-specific (use `infrastructure/scripts/`).  
**Key files:** `ci.yml` (runs on every PR), `deploy-staging.yml` (auto-deploy on merge to `main`), `llm-contract-tests.yml` (weekly cron to validate LLM output schemas against Pydantic models).

#### `apps/web/`
**Purpose:** The Next.js 15 frontend application — everything a student, parent, or teacher sees.  
**Belongs here:** React components, pages, hooks, stores, styles, and frontend tests specific to this application.  
**Does NOT belong here:** Reusable UI primitives (use `packages/ui/`), math rendering logic (use `packages/math-renderer/`), shared types (use `packages/types/`), or any backend logic.  
**Key files:** `src/app/` (App Router pages), `src/stores/` (Zustand state), `src/lib/api-client.ts` (typed API client), `CLAUDE.md` (frontend-specific Claude Code context).

#### `apps/api/`
**Purpose:** The FastAPI backend API — handles all HTTP requests, authentication, and orchestrates business logic.  
**Belongs here:** API routes, Pydantic request/response models, service layer, repository layer, database models, Alembic migrations, prompt templates.  
**Does NOT belong here:** LangGraph agent definitions (use `services/agent-engine/`), BKT engine logic (use `services/bkt-engine/`), question generation pipelines (use `services/question-generator/`), or frontend code.  
**Key files:** `src/main.py` (app factory), `src/core/config.py` (settings), `src/core/security.py` (Auth0 JWT validation), `alembic/` (migrations).

#### `packages/ui/`
**Purpose:** Shared React component library for design-system primitives used across the web app.  
**Belongs here:** Buttons, cards, modals, progress bars, badges — stateless, themeable UI primitives.  
**Does NOT belong here:** Business-logic-aware components (those belong in `apps/web/src/components/`), API calls, stores.  
**Key files:** Component folders each containing `index.tsx`, `types.ts`, and `*.test.tsx`.

#### `packages/math-renderer/`
**Purpose:** KaTeX 0.16 wrapper components for rendering mathematical notation.  
**Belongs here:** Math display components, math input components, visual math builders (fraction builder, number line).  
**Does NOT belong here:** Assessment logic, question selection, scoring.  
**Key files:** `MathDisplay.tsx` (block LaTeX), `MathInline.tsx` (inline LaTeX), `MathInput.tsx` (input with live preview), `FractionBuilder.tsx` (drag-and-drop fraction building).

#### `packages/types/`
**Purpose:** Shared TypeScript type definitions that mirror the API contract and domain model.  
**Belongs here:** Interfaces and types for API requests/responses, domain entities, enums.  
**Does NOT belong here:** Runtime code, validation logic (Zod schemas live in the consuming app), React components.  
**Key files:** `api.ts` (generic API envelope types), `assessment.ts`, `student.ts`, `standards.ts` (Oregon math standards types).

#### `packages/config/`
**Purpose:** Shared tooling configurations for consistent linting, formatting, and TypeScript across all packages.  
**Belongs here:** ESLint flat config, tsconfig bases, Prettier config.  
**Does NOT belong here:** Application configuration, environment variables, secrets.  
**Key files:** `eslint/base.js`, `typescript/base.json`, `prettier/index.js`.

#### `packages/db-schema/`
**Purpose:** TypeScript types mirroring the PostgreSQL schema for frontend type safety.  
**Belongs here:** TypeScript interfaces that exactly match DB table structures, shared enums (grade levels, math domains).  
**Does NOT belong here:** SQLAlchemy models (those live in `apps/api/src/db/tables/`), migration files, query logic.  
**Key files:** `schema.ts` (auto-generated or manually maintained types), `enums.ts`.

#### `services/agent-engine/`
**Purpose:** LangGraph-based AI agent system for tutoring, diagnostics, and learning plan generation.  
**Belongs here:** LangGraph graph definitions, node implementations, agent state schemas, agent-specific prompt templates.  
**Does NOT belong here:** HTTP routing (this service is called by `apps/api/`), database models, frontend code.  
**Key files:** `src/graphs/tutor_graph.py` (main tutoring workflow), `src/nodes/` (individual agent actions), `src/state/` (TypedDict state schemas), `src/prompts/` (Jinja2 prompt templates).

#### `services/question-generator/`
**Purpose:** LLM-powered pipeline for generating math questions aligned to Oregon standards.  
**Belongs here:** Question generation logic, math correctness validators, standards mapping data, generation prompt templates.  
**Does NOT belong here:** Question serving/API (that's in `apps/api/`), student state management, BKT logic.  
**Key files:** `src/generator.py`, `src/validators.py`, `src/standards/or_math_k8.json`.

#### `services/bkt-engine/`
**Purpose:** Bayesian Knowledge Tracing service using pyBKT with custom extensions for mastery estimation.  
**Belongs here:** pyBKT wrapper, mastery state models, calibration routines, roster management.  
**Does NOT belong here:** HTTP routing for end users, LLM calls, frontend code.  
**Key files:** `src/engine/tracker.py` (pyBKT integration), `src/engine/calibration.py`, `tests/fixtures/skill_params.json`.

#### `infrastructure/terraform/`
**Purpose:** All AWS resources defined as Terraform Infrastructure as Code.  
**Belongs here:** Terraform modules, environment configs, variable definitions, remote state config.  
**Does NOT belong here:** Application code, Docker configs (use `infrastructure/docker/`), CI/CD workflows.  
**Key files:** `modules/` (reusable modules for ECS, RDS, etc.), `environments/` (staging/production var files).

#### `infrastructure/docker/`
**Purpose:** Dockerfiles and Compose configurations for containerized services.  
**Belongs here:** Production Dockerfiles, local development Docker Compose, test Docker Compose.  
**Does NOT belong here:** Terraform, deployment scripts, application source code.  
**Key files:** `docker-compose.yml` (local dev stack), `api.Dockerfile` (multi-stage FastAPI build).

#### `infrastructure/scripts/`
**Purpose:** Operational scripts for setup, deployment, maintenance, and troubleshooting.  
**Belongs here:** Shell scripts for environment setup, database seeding, migrations, health checks.  
**Does NOT belong here:** Application logic, CI/CD workflows (use `.github/workflows/`).  
**Key files:** `setup.sh` (one-command local setup), `seed-db.sh` (seed test data), `migrate.sh`.

#### `docs/adr/`
**Purpose:** Architecture Decision Records documenting every significant technical decision.  
**Belongs here:** ADR markdown files following the template, one file per decision.  
**Does NOT belong here:** API docs (use `docs/api/`), runbooks (use `docs/runbooks/`), code.  
**Key files:** `template.md`, `ADR-001-monorepo.md` through `ADR-008-feature-flags.md`.

#### `docs/runbooks/`
**Purpose:** Step-by-step operational guides for incidents, maintenance, and emergency procedures.  
**Belongs here:** Incident response procedures, database failover steps, secret rotation guides, COPPA data deletion procedures.  
**Does NOT belong here:** Architecture decisions (use ADRs), API reference (auto-generated), feature specs.  
**Key files:** `incident-response.md`, `coppa-data-deletion.md`, `llm-fallback.md`.

### 1.3 Workspace Configuration

**`pnpm-workspace.yaml`:**
```yaml
packages:
  - "apps/*"
  - "packages/*"
```

**`turbo.json`:**
```json
{
  "$schema": "https://turbo.build/schema.json",
  "globalDependencies": ["**/.env.*local"],
  "tasks": {
    "build": {
      "dependsOn": ["^build"],
      "outputs": [".next/**", "!.next/cache/**", "dist/**"]
    },
    "dev": {
      "cache": false,
      "persistent": true
    },
    "lint": {
      "dependsOn": ["^build"]
    },
    "typecheck": {
      "dependsOn": ["^build"]
    },
    "test": {
      "dependsOn": ["^build"],
      "outputs": ["coverage/**"]
    }
  }
}
```

> **Note:** Python services (`apps/api/`, `services/*`) are NOT managed by Turborepo. They have their own `pyproject.toml` and are orchestrated via Makefile targets and Docker Compose. Turborepo manages only the TypeScript workspace graph.

---
## 2. Architecture Decision Records (ADR)

### 2.1 ADR Template

Every significant technical decision is documented as an ADR. File naming: `ADR-{NNN}-{slug}.md`.

```markdown
# ADR-{NNN}: {Title}

**Status:** Proposed | Accepted | Deprecated | Superseded by ADR-{NNN}
**Date:** {YYYY-MM-DD}
**Deciders:** {names/roles}

## Context

{What is the issue that we're seeing that is motivating this decision or change?}

## Decision

{What is the change that we're proposing and/or doing?}

## Consequences

### Positive
- {benefit}

### Negative
- {cost/risk}

## Alternatives Considered

### {Alternative 1}
- Pros: ...
- Cons: ...
- Why rejected: ...

### {Alternative 2}
- Pros: ...
- Cons: ...
- Why rejected: ...
```

---

### ADR-001: Monorepo over Polyrepo

**Status:** Accepted  
**Date:** 2026-04-04  
**Deciders:** Engineering Lead

#### Context

MathPath Oregon consists of a Next.js frontend, a FastAPI backend, three Python microservices (agent-engine, question-generator, bkt-engine), shared TypeScript packages, and infrastructure-as-code. The codebase will be developed by a solo developer (or tiny team of 1–2) using Claude Code as the primary development tool. We need a repository strategy that maximizes developer velocity, simplifies cross-cutting changes, and minimizes operational overhead.

#### Decision

Use a **monorepo** managed by pnpm workspaces (TypeScript) and Turborepo (task orchestration). Python services co-locate in the same repo but are managed independently via `pyproject.toml` and virtual environments.

#### Consequences

**Positive:**
- Atomic cross-cutting changes: a schema change in `packages/types/` and the corresponding API change in `apps/api/` and frontend change in `apps/web/` can be a single commit and single PR
- Claude Code can see the entire codebase in one repository, enabling better cross-project reasoning and consistent patterns
- Single CI/CD pipeline with Turborepo's affected-project detection
- Shared configs (ESLint, TypeScript, Prettier) enforced uniformly
- Simplified dependency management — internal packages use `workspace:*` protocol
- No version synchronization across repos

**Negative:**
- Larger clone size over time (mitigated: sparse checkout available if needed)
- CI must be smart about only running affected tests (mitigated: Turborepo caching + GitHub Actions path filters)
- Python and TypeScript toolchains must coexist (mitigated: separate dependency management, Docker for isolation)

#### Alternatives Considered

**Polyrepo (one repo per service):**
- Pros: Clear ownership boundaries, independent deploy cycles, smaller repos
- Cons: Cross-cutting changes require coordinated PRs across 5+ repos; Claude Code loses cross-project context; dependency versioning becomes a maintenance burden; dramatically higher operational overhead for a solo developer
- Why rejected: The coordination overhead of polyrepo is prohibitive for a 1–2 person team. The primary advantage (team isolation) is irrelevant at this scale.

**Nx instead of Turborepo:**
- Pros: Richer project graph, generators, boundary enforcement
- Cons: Heavier learning curve, more concepts to absorb, overkill for this project size
- Why rejected: Turborepo provides sufficient task orchestration and caching with minimal configuration. We don't need Nx's enterprise features.

---

### ADR-002: FastAPI over Django for Backend

**Status:** Accepted  
**Date:** 2026-04-04  
**Deciders:** Engineering Lead

#### Context

The backend must serve a REST API consumed by the Next.js frontend, handle async LLM calls (Anthropic, OpenAI), manage database operations, and integrate with Python ML libraries (pyBKT, LangGraph). We need a Python web framework that excels at async I/O, has first-class Pydantic integration, and produces OpenAPI documentation automatically.

#### Decision

Use **FastAPI 0.115** as the backend framework with **SQLAlchemy 2.0** (async) for database access and **Pydantic v2** for data validation.

#### Consequences

**Positive:**
- Native async/await — critical for non-blocking LLM API calls and concurrent database queries
- Pydantic v2 integration generates automatic request validation, response serialization, and OpenAPI schemas
- Auto-generated OpenAPI/Swagger docs reduce API documentation burden
- Dependency injection system is simple and testable
- Lightweight — no ORM opinions, no template engine, no admin panel we don't need
- Excellent performance (one of the fastest Python frameworks)
- Python ecosystem access to pyBKT, LangGraph, NumPy, and other ML libraries

**Negative:**
- No built-in admin panel (mitigated: we don't need one; parent/admin features are in the React app)
- Less "batteries included" than Django — must choose and wire up each component (auth, CORS, rate limiting)
- Smaller ecosystem of third-party plugins compared to Django
- No built-in ORM — requires explicit SQLAlchemy setup

#### Alternatives Considered

**Django + Django REST Framework:**
- Pros: Batteries included (admin, auth, ORM), massive ecosystem, well-documented
- Cons: Async support is still catching up; Django ORM is synchronous by default; Pydantic integration requires extra libraries; heavier framework for an API-only backend; the admin panel is unnecessary since we have a React frontend
- Why rejected: Django's sync-first architecture is a poor fit for an LLM-heavy application that makes 3–5 concurrent API calls per request. The admin panel and template system are dead weight.

**Node.js (Express/Fastify) for unified JS stack:**
- Pros: Single language across frontend and backend, shared types natively
- Cons: Python ML ecosystem (pyBKT, LangGraph, NumPy) is not available; would require Python microservices anyway for the AI layer; loses the benefit of a unified stack
- Why rejected: The AI/ML requirements make Python mandatory for the backend. Running a Node.js API that calls Python services adds an unnecessary network hop.

---

### ADR-003: PostgreSQL + pgvector over Dedicated Vector DB

**Status:** Accepted  
**Date:** 2026-04-04  
**Deciders:** Engineering Lead

#### Context

MathPath Oregon needs to store and query vector embeddings for: (a) semantic search over math questions to find similar problems, (b) embedding-based clustering of student misconceptions, and (c) potential RAG over Oregon math standards documentation. We need a vector storage and similarity search solution.

#### Decision

Use **PostgreSQL 17 with the pgvector 0.7 extension** for all vector operations, running on AWS RDS.

#### Consequences

**Positive:**
- Single database for both relational and vector data — no additional infrastructure to manage, monitor, or pay for
- ACID transactions across relational and vector data (e.g., insert a question AND its embedding atomically)
- pgvector supports HNSW and IVFFlat indexes for approximate nearest neighbor search
- Simpler backup/restore — one database to manage
- Lower cost — no additional managed service fees
- SQLAlchemy integration via `pgvector-python` library
- At our scale (thousands of questions, not millions), pgvector performance is more than adequate

**Negative:**
- pgvector is less feature-rich than dedicated vector DBs (no built-in hybrid search, fewer distance metrics)
- Performance ceiling lower than Pinecone/Weaviate at very large scale (>10M vectors)
- Must manage pgvector extension updates alongside PostgreSQL upgrades

#### Alternatives Considered

**Pinecone (managed vector DB):**
- Pros: Purpose-built for vector search, fully managed, excellent performance at scale, rich filtering
- Cons: Additional managed service cost (~$70/month minimum), another system to monitor, data synchronization complexity between Postgres and Pinecone, overkill for our initial dataset size
- Why rejected: Adding a dedicated vector DB for fewer than 10,000 vectors is over-engineering. We can migrate to Pinecone later if we outgrow pgvector.

**Weaviate / Qdrant (self-hosted):**
- Pros: Feature-rich vector search, hybrid search capabilities
- Cons: Additional infrastructure to deploy and manage on AWS, operational overhead for a solo developer, same data sync complexity as Pinecone
- Why rejected: Operational burden is not justified at our scale.

**ChromaDB (embedded):**
- Pros: Simple, Python-native, no server needed
- Cons: Not suitable for production multi-process access, no ACID guarantees, limited scalability
- Why rejected: Not production-ready for a multi-user web application.

---

### ADR-004: LangGraph over LangChain LCEL or Custom Agent Loop

**Status:** Accepted  
**Date:** 2026-04-04  
**Deciders:** Engineering Lead

#### Context

MathPath Oregon's AI layer requires multi-step agent workflows: diagnostic assessment flow (select question → present → evaluate response → update mastery → decide next action), tutoring flow (classify intent → generate hint → scaffold explanation), and learning plan generation. These workflows have conditional branching, cycles (retry with different hint), and side effects (DB writes). We need an agent orchestration framework.

#### Decision

Use **LangGraph 0.2** for all multi-step AI agent workflows, with LangChain 0.3 as the underlying LLM abstraction layer.

#### Consequences

**Positive:**
- Graph-based state machines map naturally to our educational workflows (diagnostic flow, tutoring flow, plan generation)
- Built-in support for conditional edges, cycles, and human-in-the-loop interrupts
- Checkpointing/persistence — can resume a student's assessment session if they disconnect
- Each node is a pure function `(state) -> state`, making unit testing straightforward
- Parallel node execution for independent steps (e.g., generating a hint while logging analytics)
- Active development and strong community (LangChain ecosystem)
- Integrates naturally with LangChain's LLM abstractions for model switching

**Negative:**
- LangGraph adds conceptual overhead (graph concepts, state reducers, conditional edges)
- Debugging graph execution requires understanding the graph visualization
- Tight coupling to LangChain ecosystem — if LangChain's abstractions change, we're affected
- Relatively new framework — may have breaking changes

#### Alternatives Considered

**LangChain LCEL (LangChain Expression Language) chains:**
- Pros: Simpler mental model (linear chains), less code for simple workflows
- Cons: No native support for cycles or conditional branching — our tutoring flow needs both; no built-in state persistence; difficult to add human-in-the-loop; testing individual steps requires decomposing chains
- Why rejected: LCEL is designed for linear pipelines. Our educational workflows are inherently cyclic and conditional.

**Custom agent loop (raw Python with asyncio):**
- Pros: Full control, no framework dependency, zero abstraction overhead
- Cons: Must implement state management, checkpointing, error recovery, and observability from scratch; significantly more code to write and maintain; no community patterns to follow; harder for Claude Code to reason about without established patterns
- Why rejected: We'd be rebuilding 80% of LangGraph's functionality. The framework's conventions also help Claude Code generate consistent agent code.

**CrewAI:**
- Pros: Higher-level multi-agent abstraction, role-based agent definition
- Cons: Less control over state transitions, opinionated about agent communication patterns, less suitable for our structured educational workflows
- Why rejected: CrewAI is designed for open-ended multi-agent collaboration. Our workflows are structured state machines, not free-form agent conversations.

---

### ADR-005: Auth0 over Custom Auth for COPPA Compliance

**Status:** Accepted  
**Date:** 2026-04-04  
**Deciders:** Engineering Lead

#### Context

MathPath Oregon serves children under 13, making it subject to COPPA (Children's Online Privacy Protection Act). The FTC's 2025 COPPA Rule update (full compliance deadline: April 22, 2026) requires verifiable parental consent before collecting personal information from children, explicit data retention policies, a written information security program, and the ability for parents to review and delete their child's data. We need an authentication and authorization solution that supports COPPA-compliant workflows.

#### Decision

Use **Auth0** with their COPPA-compliant plan for authentication, authorization, and parental consent management.

#### Consequences

**Positive:**
- Auth0 provides pre-built COPPA-compliant flows: age gating, parental consent collection, consent storage with audit trail
- JWT-based authentication integrates cleanly with FastAPI via standard JWT validation middleware
- Role-based access control (student, parent, teacher, admin) is built-in
- Social login for parents (Google, Apple) reduces onboarding friction
- MFA support for parent accounts
- Auth0 maintains SOC 2 Type II compliance, reducing our security audit burden
- Handles password hashing, session management, brute-force protection — security-critical code we don't write ourselves
- Auth0 Actions (serverless hooks) allow custom logic during auth flows (e.g., enforce consent check before child login)

**Negative:**
- Vendor lock-in for a critical security component
- Cost scales with monthly active users (mitigated: free tier covers development; paid plans start at $35/month)
- Must trust Auth0's COPPA compliance claims (mitigated: they participate in KidSAFE+ Safe Harbor program)
- Adds a network dependency — if Auth0 is down, authentication fails (mitigated: JWT validation is local after initial login)
- Learning curve for Auth0 Actions and custom flows

#### Alternatives Considered

**Custom auth with `python-jose` + bcrypt:**
- Pros: Full control, no vendor dependency, no per-user costs
- Cons: We become responsible for COPPA-compliant consent flows, secure password storage, brute-force protection, session management, MFA, and security audits — enormous effort and liability for a solo developer; any bug in auth code is a security vulnerability and potential COPPA violation with fines up to $53,088 per violation per day
- Why rejected: Building COPPA-compliant auth from scratch is irresponsible for a solo developer. The liability risk alone justifies the Auth0 cost.

**Clerk:**
- Pros: Developer-friendly, excellent React components, fast integration
- Cons: No explicit COPPA compliance tooling, no Safe Harbor certification, less mature enterprise features
- Why rejected: Lack of COPPA-specific features is a dealbreaker for a children's education app.

**Supabase Auth:**
- Pros: Open source, integrated with Supabase ecosystem, generous free tier
- Cons: No COPPA compliance features, limited parental consent workflows, would require significant custom development
- Why rejected: Same COPPA gap as Clerk.

---

### ADR-006: pyBKT with Custom Extensions over Pure Custom BKT

**Status:** Accepted  
**Date:** 2026-04-04  
**Deciders:** Engineering Lead

#### Context

MathPath Oregon uses Bayesian Knowledge Tracing (BKT) to estimate student mastery of math skills. BKT has four core parameters per skill: P(L₀) prior knowledge, P(T) learn rate, P(G) guess rate, P(S) slip rate. We need an implementation that supports standard BKT plus extensions for individual student priors, multi-guess/slip, and forgetting.

#### Decision

Use **pyBKT** as the core BKT library, wrapped in a custom service layer that adds: (a) per-student prior initialization from diagnostic assessment results, (b) real-time roster management via pyBKT's Roster API, (c) custom mastery thresholds per Oregon standard, and (d) an integration layer that feeds BKT outputs to the LangGraph agent for question selection decisions.

#### Consequences

**Positive:**
- pyBKT is a peer-reviewed, published library (EDM 2021) with validated implementations of BKT and 5+ variants
- Supports individual student priors, multi-guess/slip, forgetting, and item-order effects out of the box
- Roster API enables real-time per-student mastery tracking without re-fitting the model
- Cross-validation and evaluation utilities for parameter calibration
- Computationally efficient — BKT updates in microseconds
- Reduces risk of mathematical implementation errors in a critical educational algorithm

**Negative:**
- pyBKT's API is designed for batch research use — the Roster API for real-time use is newer and less documented
- Limited control over the internal EM algorithm implementation
- Must maintain compatibility with pyBKT updates
- Some desired extensions (integrating IRT difficulty with BKT) require custom code around pyBKT

#### Alternatives Considered

**Pure custom BKT implementation:**
- Pros: Full control over every parameter, can deeply integrate with our domain model, no dependency
- Cons: Risk of mathematical errors in the forward algorithm; must implement and validate EM fitting from scratch; no peer review; 2–4 weeks of development for what pyBKT provides in a pip install
- Why rejected: Implementing BKT correctly is deceptively complex. The forward-backward algorithm, EM fitting, and parameter identifiability constraints require careful mathematical implementation. Using a validated library and extending it is safer.

**Deep Knowledge Tracing (DKT) with neural networks:**
- Pros: Potentially better predictive accuracy, can capture complex skill interactions
- Cons: Requires significant training data we don't have at launch; black-box predictions are harder to explain to parents/teachers; much higher computational cost; over-engineering for an MVP
- Why rejected: BKT's interpretable parameters (learn rate, guess rate, slip rate) are a feature for an educational product where we need to explain to parents why their child is at a certain mastery level. DKT can be added as an enhancement in later stages.

---

### ADR-007: Hybrid Vercel + AWS over Pure AWS or Pure GCP

**Status:** Accepted  
**Date:** 2026-04-04  
**Deciders:** Engineering Lead

#### Context

MathPath Oregon has two distinct deployment concerns: (a) a Next.js 15 frontend that benefits from edge rendering, ISR, and automatic preview deployments, and (b) a Python backend with GPU-free ML services that need persistent connections to PostgreSQL and Redis. We need an infrastructure strategy that optimizes for both workloads.

#### Decision

Deploy the **Next.js frontend on Vercel** and the **Python backend + services on AWS** (ECS/Fargate for compute, RDS for PostgreSQL, ElastiCache for Redis, S3 + CloudFront for static assets).

#### Consequences

**Positive:**
- Vercel is purpose-built for Next.js — automatic edge rendering, ISR, image optimization, preview deployments on every PR, zero-config CDN
- AWS ECS/Fargate provides serverless container hosting — no EC2 instances to manage, automatic scaling
- AWS RDS provides managed PostgreSQL with automated backups, failover, and pgvector support
- Clear separation: Vercel handles frontend CDN/SSR concerns, AWS handles data and compute
- Vercel's preview deployments enable stakeholder review of frontend changes before merge
- Cost-effective: Vercel's free tier covers development; AWS costs are predictable with Fargate's per-second billing

**Negative:**
- Two cloud providers to manage (mitigated: Vercel is nearly zero-ops for Next.js)
- Cross-provider networking: Next.js API routes on Vercel must call AWS-hosted FastAPI over the public internet or via a VPN (mitigated: use AWS API Gateway as a stable endpoint; latency is acceptable since Vercel edge → AWS us-west-2 is ~20ms)
- Two billing systems to monitor
- Terraform manages AWS only; Vercel is configured via `vercel.json` and dashboard

#### Alternatives Considered

**Pure AWS (ECS for both frontend and backend):**
- Pros: Single provider, single billing, single Terraform config, private networking between all services
- Cons: Hosting Next.js on ECS/Fargate requires manual CDN configuration (CloudFront), no automatic preview deployments, must configure ISR caching ourselves, significantly more DevOps work for a solo developer
- Why rejected: Vercel eliminates 20+ hours of CDN/ISR/preview-deployment DevOps work. The cross-provider complexity is minimal compared to the saved effort.

**Pure GCP (Cloud Run + Cloud SQL):**
- Pros: Cloud Run is excellent for containers, GCP's AI/ML integration
- Cons: Less mature Next.js hosting (no equivalent to Vercel), would still want Vercel for frontend; team has stronger AWS familiarity
- Why rejected: No compelling advantage over AWS for our workload, and we'd still want Vercel for the frontend.

**Pure Vercel (including Vercel Serverless Functions for backend):**
- Pros: Single provider, simple
- Cons: Vercel serverless functions have a 60-second timeout (LLM calls can exceed this), no persistent connections to PostgreSQL, no support for background workers, can't run Python ML services
- Why rejected: Vercel serverless is unsuitable for long-running LLM calls and Python-based ML workloads.

---

### ADR-008: Unleash (Self-Hosted) for Feature Flags

**Status:** Accepted  
**Date:** 2026-04-04  
**Deciders:** Engineering Lead

#### Context

MathPath Oregon is built in 5 stages with progressive feature rollout. We need feature flags for: (a) stage-gating features (don't expose Stage 3 features until Stage 2 is stable), (b) A/B testing of tutoring strategies, (c) gradual rollout of new question types, (d) kill switches for LLM features if costs spike, and (e) COPPA-compliant user segmentation (never flag children into experimental cohorts without parental consent).

#### Decision

Use **Unleash (open-source, self-hosted)** deployed as a Docker container on ECS/Fargate, with the Unleash Node.js SDK in the frontend and a Python SDK in the backend.

#### Consequences

**Positive:**
- Open source and self-hosted — all feature flag evaluation data stays within our AWS infrastructure (critical for COPPA: no child user data sent to third-party SaaS)
- Free at our scale — no per-seat or per-flag costs
- Supports all required strategies: gradual rollout, user-based targeting, environment-based flags, custom constraints
- Simple deployment: single Docker container + PostgreSQL (can share our existing RDS instance)
- SDKs available for both Node.js (frontend) and Python (backend)
- Audit log of all flag changes
- API-driven — can automate flag changes in CI/CD

**Negative:**
- Self-hosted = we manage uptime, backups, and upgrades (mitigated: it's a single stateless container; the PostgreSQL state is in our managed RDS)
- Fewer advanced features than LaunchDarkly (no built-in experimentation platform, limited analytics)
- Must build our own COPPA consent check layer on top of flag evaluation
- No enterprise support without paid plan

#### Alternatives Considered

**LaunchDarkly:**
- Pros: Industry-leading feature flag platform, built-in experimentation, excellent SDKs, managed service
- Cons: Expensive ($10/seat/month minimum, scales quickly), sends user context to LaunchDarkly's servers for evaluation — problematic for COPPA compliance with child user data, vendor lock-in for a core development workflow
- Why rejected: Sending child user data to a third-party service for feature flag evaluation creates COPPA compliance risk. The cost is also disproportionate for a solo developer.

**Homegrown feature flags (database table + config):**
- Pros: Zero additional infrastructure, full control, simple
- Cons: Must build evaluation logic, gradual rollout, targeting rules, audit logging, and a management UI from scratch; no SDK; error-prone; no separation between flag management and application code
- Why rejected: Building a feature flag system is a distraction from the core product. Unleash provides this for free with better reliability.

**PostHog Feature Flags (bundled with analytics):**
- Pros: Already using PostHog for analytics, integrated A/B testing
- Cons: PostHog is cloud-hosted — same COPPA data-sharing concerns as LaunchDarkly; feature flags are a secondary product; less mature than Unleash
- Why rejected: COPPA data-sharing concern, and we want feature flags to be independent of our analytics vendor.

---

### ADR-009: LiteLLM as Universal LLM Abstraction Layer (Local-First)

**Status:** Accepted  
**Date:** April 2026  
**Deciders:** Engineering Lead  
**Context:** Solo development with COPPA compliance requirements

#### Context

MathPath requires three distinct LLM use cases with different COPPA sensitivity levels:

1. **Student-facing inference** (tutor hints, error feedback): Involves student session data and behavioral responses. Under COPPA, transmitting this data to a third-party LLM API requires a Data Processing Agreement (DPA) confirming zero data retention. Anthropic and OpenAI standard API terms are not automatically COPPA-sufficient vendor agreements. Risk: high.

2. **Admin/batch tasks** (question generation, prompt engineering): No student PII involved. Cloud LLMs acceptable immediately.

3. **Developer tooling** (Claude Code, code review): No production data involved. Unrestricted.

Additionally, the development environment runs on an M4 Max 64GB MacBook Pro capable of running Qwen2.5:72b at production-quality inference speeds. Local inference eliminates per-token API costs for student-facing calls entirely.

#### Decision

Use **LiteLLM** as the single, universal interface for all LLM calls in the application codebase. LiteLLM provides:
- Identical API surface (`litellm.completion()`) for Ollama local models, Anthropic, OpenAI, Gemini, and 100+ other providers
- Automatic fallback chains (local model → cloud if local unavailable)
- Built-in token counting, cost tracking, and structured logging
- Config-only model switching — no application code changes required to swap models

Student-facing roles default to **Ollama/Qwen2.5** (local, COPPA-safe). Admin roles default to **claude-sonnet-4-6** (cloud, no student PII).

#### Implementation

```python
# apps/api/src/clients/llm_client.py

from litellm import completion
from app.core.config import settings
import structlog

logger = structlog.get_logger()

# LLM_ROUTING is set per-environment in config.py
# To swap a model: change config only. No code changes.
LLM_ROUTING = {
    # Student-facing (local only until COPPA DPAs obtained from Anthropic/OpenAI)
    "tutor":       "ollama/qwen2.5:72b",      # Tutor Agent hints + Socratic guidance
    "assessment":  "ollama/qwen2.5:32b",      # Error classification + answer evaluation
    
    # Admin/batch (cloud OK — no student PII)
    "question_gen": "anthropic/claude-sonnet-4-6",   # Question generation pipeline
    "admin":        "anthropic/claude-sonnet-4-6",   # Internal tooling
}

def get_llm_response(role: str, messages: list, **kwargs) -> str:
    model = settings.LLM_ROUTING.get(role) or LLM_ROUTING[role]
    logger.info("llm_call", role=role, model=model)
    response = completion(model=model, messages=messages, **kwargs)
    return response.choices[0].message.content
```

```python
# apps/api/src/core/config.py (partial)
class Settings(BaseSettings):
    # Override any routing entry via environment variable
    LLM_ROUTING: dict = {
        "tutor":        "ollama/qwen2.5:72b",
        "assessment":   "ollama/qwen2.5:32b",
        "question_gen": "anthropic/claude-sonnet-4-6",
        "admin":        "anthropic/claude-sonnet-4-6",
    }
    # Set to "anthropic/claude-sonnet-4-6" once DPAs are in place:
    # LLM_ROUTING__tutor: str = "anthropic/claude-sonnet-4-6"
```

#### Local Model Selection (M4 Max 64GB)

| Role | Model | Approx. VRAM | Inference Speed | Notes |
|---|---|---|---|---|
| Tutor Agent | `qwen2.5:72b` (Q4_K_M) | ~40GB | ~15–25 tok/sec | Best reasoning; adequate for Socratic hints |
| Assessment Agent | `qwen2.5:32b` (Q4_K_M) | ~20GB | ~25–40 tok/sec | Error classification; faster turnaround |
| Question Generation | `claude-sonnet-4-6` (cloud) | — | — | No student PII; run as batch |

#### Path to Cloud LLM for Student Inference

Switching student-facing roles to Claude or GPT-4o requires ALL of the following:
1. BAA/DPA from Anthropic confirming zero data retention for API calls
2. BAA/DPA from OpenAI (if using GPT-4o)
3. Privacy notice updated to describe third-party data flows
4. Legal counsel sign-off

Until these are in place: `tutor` and `assessment` roles MUST use local models only.

#### Consequences

**Positive:**
- Zero COPPA risk for student-facing inference from day one
- Zero per-token cost for student-facing inference (hardware cost only)
- Config-only model switching — no code changes to upgrade or downgrade model
- Provider-agnostic: can adopt new frontier models without touching application code

**Negative:**
- Local inference requires M4 Max hardware to be available for production (development) or a GPU server for staging/production
- Qwen2.5:72b response latency (~500ms–2s) is higher than cloud APIs (~200–400ms)
- Must manage Ollama service availability as part of infrastructure

#### Alternatives Considered

| Alternative | Reason Rejected |
|---|---|
| Direct `anthropic` SDK client | Lock-in to single provider; code changes required to switch models |
| Direct `openai` SDK client | Same lock-in; COPPA risk for student data |
| No abstraction (hardcoded model per use case) | Tight coupling; changing models requires code changes; violates the plug-and-unplug requirement |
| Custom LLM router | Reinventing LiteLLM; maintenance burden |

#### Related Files

- `apps/api/src/clients/llm_client.py` — LiteLLM wrapper
- `apps/api/src/core/config.py` — `LLM_ROUTING` config dict
- `services/agent-engine/agents/` — All agent nodes import `get_llm_response()`, never call LLM SDKs directly
- `ADR-005` — Auth0 for COPPA compliance (same principle: use proven vendor for compliance-critical path)

---

## 3. Claude Code Workflow — How to Build This App with AI

Claude Code is the primary development tool. Every feature, every bug fix, every refactor flows through Claude Code or a comparable AI coding agent. This section defines how to use it effectively for maximum leverage.

### 3.1 Model Routing Strategy

Not all tasks require frontier models. Route tasks to the cheapest model that can handle them reliably.

| Task | Model | Rationale |
|------|-------|-----------|
| Architecture design & ADRs | Claude Opus 4 (frontier) | Deep reasoning, multi-constraint analysis |
| Feature implementation (complex) | Claude Sonnet 4 (frontier) | Best code quality, understands full context |
| Feature implementation (routine) | Qwen2.5-Coder 32B (local, Q4_K_M) | Cost-free, fast, good for known patterns |
| Boilerplate & CRUD generation | Qwen2.5-Coder 14B (local, Q4_K_M) | Very fast, handles templates well |
| Security-sensitive code (auth, payments) | Claude Sonnet 4 (frontier) | NEVER use local models for security code |
| SQL migrations | Claude Sonnet 4 (frontier) | Schema mistakes are expensive to fix |
| Test writing | Qwen2.5-Coder 32B (local, Q4_K_M) | High quality for structured test patterns |
| Documentation writing | Claude Haiku 3.5 (frontier) | Cost-effective, good prose |
| LLM prompt engineering | Claude Opus 4 (frontier) | Critical to tutoring quality |
| Debugging complex issues | Claude Sonnet 4 (frontier) | Needs full context + deep reasoning |
| Code review | Claude Sonnet 4 (frontier) | Must catch subtle bugs |
| Simple refactoring | Qwen2.5-Coder 32B (local, Q4_K_M) | Pattern-based, low risk |

#### Running Local Models via Ollama on M4 Max

The Apple M4 Max with 64GB unified memory can comfortably run quantized 32B models. Setup:

```bash
# Install Ollama
brew install ollama

# Pull models
ollama pull qwen2.5-coder:32b-instruct-q4_K_M    # 20GB, primary local model
ollama pull qwen2.5-coder:14b-instruct-q4_K_M    # 9GB, fast boilerplate model

# Create custom model with 64K context (required for agentic coding)
cat > Qwen32bModelfile << 'EOF'
FROM qwen2.5-coder:32b-instruct-q4_K_M
PARAMETER num_ctx 65536
EOF
ollama create qwen2.5-coder-64k -f Qwen32bModelfile

# Verify it's running
ollama list
ollama run qwen2.5-coder-64k "Write a hello world FastAPI app"
```

#### Using Local Models with Claude Code

Claude Code can connect to Ollama via the Anthropic-compatible API:

```bash
# Set environment variables for local model usage
export ANTHROPIC_BASE_URL=http://localhost:11434/v1
export ANTHROPIC_API_KEY=ollama   # Ollama doesn't need a real key

# Launch Claude Code with local model
claude --model qwen2.5-coder-64k

# Or for the smaller model (boilerplate tasks)
claude --model qwen2.5-coder:14b-instruct-q4_K_M
```

**Switching between local and frontier models:**
```bash
# Terminal 1: Claude Code with Sonnet (frontier) for complex work
claude   # Uses default Anthropic API

# Terminal 2: Claude Code with local model for boilerplate
ANTHROPIC_BASE_URL=http://localhost:11434/v1 ANTHROPIC_API_KEY=ollama claude --model qwen2.5-coder-64k
```

**Important caveats for local models:**
- Local models DO NOT have the same tool-use reliability as Claude. Expect occasional tool-call failures.
- Never use local models for: security code, auth flows, payment logic, database migrations, or COPPA-sensitive features.
- If a local model produces code that seems reasonable but you're not sure, re-review it with Claude Sonnet before committing.
- Local model context windows (64K) are smaller than Claude's (200K). For large-context tasks, use frontier models.

---

### 3.2 Claude Code Project Setup

#### Root `CLAUDE.md`

This is the most important file in the repository for AI-assisted development. Claude reads it at the start of every session.

```markdown
# MathPath Oregon — Project Context for Claude Code

## What This Is
MathPath Oregon is an AI-powered adaptive math learning app for K-8 students
aligned with Oregon math standards. It uses Bayesian Knowledge Tracing (pyBKT)
for mastery estimation and LLM-powered tutoring (Claude Sonnet, GPT-4o) for
personalized hints and explanations.

## Architecture Overview
- Frontend: Next.js 15 (App Router) + React 19 + TypeScript 5 + Tailwind CSS 4
- Backend: FastAPI 0.115 + SQLAlchemy 2.0 (async) + Pydantic v2
- AI: LangGraph 0.2 (agent orchestration) + pyBKT (mastery tracking)
- Database: PostgreSQL 17 + pgvector 0.7 + Redis 7
- Auth: Auth0 (COPPA-compliant plan)
- Deploy: Vercel (frontend) + AWS ECS/Fargate (backend)

## Monorepo Structure
- apps/web/ — Next.js frontend
- apps/api/ — FastAPI backend
- services/agent-engine/ — LangGraph AI agents
- services/bkt-engine/ — Bayesian Knowledge Tracing
- services/question-generator/ — LLM question generation
- packages/ui/ — Shared React components
- packages/math-renderer/ — KaTeX math rendering
- packages/types/ — Shared TypeScript types

## CRITICAL Rules (Never Violate)
1. COPPA COMPLIANCE: Never log, store, or transmit child PII without
   verifiable parental consent. When in doubt, don't collect the data.
2. LAYERED ARCHITECTURE: API layer → Service layer → Repository layer.
   Never skip layers. Never import FastAPI types in the service layer.
3. NO HARDCODED PROMPTS: All LLM prompts go in .jinja2 template files
   in the prompts/ directory. Never inline prompts in Python code.
4. NO ANY TYPES: TypeScript strict mode, Python mypy strict mode.
   Use proper types everywhere. Mark external library boundaries explicitly.
5. TESTS REQUIRED: Every PR must include tests. No exceptions.
6. NO SECRETS IN CODE: All secrets via environment variables. Use
   .env.local (gitignored) for local dev.
7. PYDANTIC V2: Use model_validator, field_validator, ConfigDict.
   Do NOT use Pydantic v1 syntax (class Config, @validator).
8. ASYNC BY DEFAULT: All FastAPI endpoints are async def. All DB
   operations use async SQLAlchemy. Sync only for CPU-bound pyBKT.
9. UUID PRIMARY KEYS: All tables use UUID v4 primary keys, never serial.
10. KEYSET PAGINATION: Never use OFFSET pagination. Always keyset.
11. **No direct LLM SDK imports in agent nodes** — all LLM calls go through `llm_client.get_llm_response(role, messages)` only; `anthropic`, `openai`, or `litellm` SDKs are never imported directly in agent code or service code outside `clients/llm_client.py`
12. **No cloud LLM for student-facing roles without COPPA DPAs** — `tutor` and `assessment` LLM routing roles must point to local Ollama models until written DPAs are obtained from the relevant cloud provider; this is enforced by config, not code

## Commands Reference
- `make dev` — Start full dev stack (frontend + backend + services)
- `make test` — Run all tests
- `make test-unit` — Run only unit tests
- `make lint` — Lint all code
- `make typecheck` — TypeScript + mypy type checking
- `make migrate` — Run Alembic migrations
- `make seed` — Seed database with test data

## Coding Patterns
- See docs/ENG-000-foundations.md for comprehensive standards
- See apps/api/CLAUDE.md for backend-specific patterns
- See apps/web/CLAUDE.md for frontend-specific patterns
- See services/agent-engine/CLAUDE.md for LangGraph patterns
```

#### Sub-Package `CLAUDE.md` Files

**`apps/web/CLAUDE.md`:**
```markdown
# Frontend Context — Next.js 15

## Architecture
- App Router with route groups: (auth), (public), (student), (parent)
- Server Components by default. Client Components only when needed
  (interactivity, browser APIs, hooks).
- Zustand for session state (assessment in progress, user preferences)
- SWR for remote API state (server data with cache/revalidation)

## Patterns
- Components: PascalCase files, Props interface at top, export default
- Hooks: camelCase files, prefix with "use"
- API client: src/lib/api-client.ts — always use typed fetch wrapper
- Forms: React Hook Form + Zod schema validation
- Math: Import from @mathpath/math-renderer, never use KaTeX directly

## DO NOT
- Use `any` type — strict TypeScript
- Use `useEffect` for data fetching — use SWR or Server Components
- Put business logic in components — extract to hooks or lib/
- Use CSS modules or styled-components — Tailwind only
- Import from apps/api/ or services/ — use packages/types/ for types
```

**`apps/api/CLAUDE.md`:**
```markdown
# Backend Context — FastAPI 0.115

## Layered Architecture (STRICTLY ENFORCED)
- api/ layer: Route definitions, request validation, auth checks,
  call service layer. NO business logic. NO database queries.
- service/ layer: Business logic, orchestration. Calls repository
  layer and external clients. NO FastAPI types. NO SQLAlchemy queries.
- repository/ layer: SQLAlchemy queries only. NO business logic.
  NO HTTP calls. Returns domain objects, not ORM models.
- models/ layer: Pydantic v2 schemas for request/response contracts.

## Dependency Injection
```python
# Standard pattern for all endpoints
@router.post("/assessments", response_model=AssessmentResponse)
async def create_assessment(
    request: CreateAssessmentRequest,
    student: Student = Depends(get_current_student),
    service: AssessmentService = Depends(get_assessment_service),
) -> AssessmentResponse:
    return await service.create_assessment(student.id, request)
```

## Error Handling
- All errors inherit from AppError (see core/exceptions.py)
- Services raise domain exceptions (NotFoundError, ValidationError)
- Global exception handler maps them to HTTP responses
- Never raise HTTPException in service layer

## Async Rules
- All endpoints: async def
- All DB operations: async SQLAlchemy session
- BKT computations: run_in_executor (CPU-bound)
- LLM calls: async with concurrent gathering where possible

## DO NOT
- Import FastAPI types in service/ or repository/ layers
- Use raw SQL strings — SQLAlchemy ORM or Core only
- Return SQLAlchemy ORM objects from endpoints — convert to Pydantic
- Use Pydantic v1 syntax (class Config, @validator)
- Skip error handling — wrap all external calls in try/except
```

**`services/agent-engine/CLAUDE.md`:**
```markdown
# Agent Engine Context — LangGraph 0.2

## Architecture
- Each workflow is a LangGraph StateGraph with typed state
- Nodes are pure functions: (state: GraphState) -> dict
- Side effects (DB, API calls) happen in dedicated "effect" nodes
- Prompts are Jinja2 templates in prompts/ directory

## State Pattern
```python
class TutorState(TypedDict):
    student_id: str
    current_question: Question
    student_response: str
    mastery_state: dict[str, float]
    hint_history: list[str]
    messages: Annotated[list, add_messages]
    next_action: Literal["hint", "explain", "next_question", "end"]
```

## Node Pattern
```python
def generate_hint(state: TutorState) -> dict:
    """Generate a contextual hint. Pure function — no side effects."""
    prompt = render_template("hint_generation_v1.0.jinja2", state)
    hint = llm_client.generate(prompt, model="claude-sonnet-4")
    return {
        "hint_history": [hint],
        "messages": [AIMessage(content=hint)]
    }
```

## DO NOT
- Make DB calls inside graph nodes (use effect nodes)
- Hardcode prompts in node functions
- Use mutable state — always return new dict
- Skip validation of LLM outputs — always validate with Pydantic
```

#### Claude Code Settings

Create `.claudecode/settings.json` at the repo root:
```json
{
  "permissions": {
    "allow": [
      "Read",
      "Write",
      "Edit",
      "Bash(make *)",
      "Bash(pnpm *)",
      "Bash(pytest *)",
      "Bash(python *)",
      "Bash(git *)",
      "Bash(alembic *)",
      "Bash(ollama *)"
    ],
    "deny": [
      "Bash(rm -rf /)",
      "Bash(curl * | bash)",
      "Bash(* --force-with-lease)",
      "Bash(terraform apply *)",
      "Bash(docker push *)"
    ]
  }
}
```

#### Context Management Across Sessions

- **Start each session** with: "Read CLAUDE.md and the CLAUDE.md in [relevant sub-package]"
- **Clear context** when token usage exceeds 60K (use `/clear` or start a new session)
- **Use `/context`** mid-session to check how much context is consumed
- **End each session** by asking Claude to update any relevant dev docs (plan files, task lists)
- **Use git worktrees** for parallel features — each worktree gets its own Claude Code session

---

### 3.3 Claude Code Prompt Patterns for This Project

These are reusable prompt templates. Copy, fill in the blanks, and paste into Claude Code.

#### Pattern 1: Add a New API Endpoint

```
Add a new API endpoint to apps/api/:

**Endpoint:** {METHOD} /api/v1/{resource}
**Purpose:** {what it does}
**Request body:** {describe fields or say "see existing pattern in assessments.py"}
**Response:** {describe shape}
**Auth:** {student | parent | admin | public}
**Business rules:**
- {rule 1}
- {rule 2}

Follow the layered architecture:
1. Add Pydantic request/response models in models/{resource}.py
2. Add repository method in repository/{resource}_repo.py
3. Add service method in service/{resource}_service.py
4. Add route in api/v1/{resource}.py
5. Add unit tests for service layer
6. Add integration test for the endpoint

Reference the existing assessment endpoint pattern for structure.
```

#### Pattern 2: Add a New React Component

```
Create a new React component in apps/web/:

**Component:** {ComponentName}
**Location:** src/components/{category}/{ComponentName}/
**Purpose:** {what it renders}
**Props:**
- {prop1}: {type} — {description}
- {prop2}: {type} — {description}
**State:** {what local state it needs, or "none — server component"}
**API data:** {which API endpoint it calls, or "receives data via props"}
**Interactions:** {click handlers, form submissions, etc.}

Requirements:
- Use Tailwind CSS for styling
- Use components from @mathpath/ui for primitives
- Use @mathpath/math-renderer for any math notation
- Include aria labels and keyboard navigation
- Write a Jest + RTL test covering the primary user interaction
- {Server Component | Client Component} — justify the choice
```

#### Pattern 3: Write Tests for a Module

```
Write comprehensive tests for {module path}:

**Module under test:** {file path}
**Test type:** {unit | integration | e2e}
**Key behaviors to test:**
1. {behavior 1 — happy path}
2. {behavior 2 — edge case}
3. {behavior 3 — error case}

**Test framework:** {pytest | jest + RTL | playwright}
**Mocking requirements:**
- Mock {external dependency} with {mock strategy}
- Use real {component} (no mocking)

**Fixtures needed:**
- {fixture 1}: {description}
- {fixture 2}: {description}

Follow existing test patterns in {path to example test file}.
Test behavior, not implementation. Each test gets a descriptive name
that reads as a specification.
```

#### Pattern 4: Add a New Alembic Migration

```
Create an Alembic migration for:

**Change description:** {what schema change is needed}
**Tables affected:** {table names}
**New columns:**
- {column_name}: {type} {constraints} — {purpose}
**New indexes:**
- {index description and rationale}
**Data migration needed:** {yes/no — if yes, describe}

Rules:
- Migration must be forward-only (no down_revision that drops data)
- Use UUID for any new primary keys
- Add created_at and updated_at to any new tables
- PII fields must be prefixed with pii_ and commented
- Test the migration against a fresh database AND against the current schema
- Naming: {YYYYMMDD_HHMMSS}_{descriptive_name}.py
```

#### Pattern 5: Implement a New LangGraph Node

```
Add a new node to the {graph_name} graph in services/agent-engine/:

**Node name:** {node_function_name}
**Purpose:** {what this node does in the workflow}
**Input state fields it reads:**
- {field}: {type}
**Output state fields it writes:**
- {field}: {type}
**LLM call needed:** {yes/no — if yes, which model and prompt template}
**Side effects:** {none | DB write | API call — if any, this must be an "effect" node}

The node must be a pure function: (state: GraphState) -> dict
If it needs an LLM call, use the LLMClient wrapper (never call SDK directly).
If it has side effects, separate the pure logic from the effect.
Write a unit test with a mock state fixture that tests the node in isolation.
```

#### Pattern 6: Add a New BKT Skill

```
Add tracking for a new math skill in services/bkt-engine/:

**Skill name:** {Oregon standard identifier, e.g., "3.OA.A.1"}
**Display name:** {human-readable name, e.g., "Multiply within 100"}
**Grade level:** {K-8}
**Domain:** {OA | NBT | NF | MD | G | RP | EE | SP | F}
**Initial parameters (if known):**
- P(L₀): {prior probability, default 0.1}
- P(T): {learn rate, default 0.2}
- P(G): {guess rate, default 0.15}
- P(S): {slip rate, default 0.10}
**Mastery threshold:** {default 0.95}
**Prerequisite skills:** {list of skill IDs this depends on}

Steps:
1. Add skill definition to standards/or_math_k8.json
2. Add skill parameters to test fixtures
3. Add calibration test with sample response sequence
4. Update the Roster to include the new skill
5. Add to the question generator's skill mapping
```

#### Pattern 7: Debug a FastAPI Error

```
I'm seeing this error in the FastAPI backend:

**Error message:** {paste full error/traceback}
**Endpoint:** {METHOD /path}
**Request body:** {paste request body if relevant}
**Expected behavior:** {what should happen}
**Actual behavior:** {what actually happens}
**Relevant logs:** {paste any relevant log lines}

Please:
1. Read the relevant source files (endpoint, service, repository)
2. Identify the root cause
3. Propose a fix
4. Verify the fix doesn't break existing tests (run pytest)
5. Add a test that would have caught this bug
```

#### Pattern 8: Refactor a Module

```
Refactor {module path} for better separation of concerns:

**Current problem:** {describe what's wrong — mixed responsibilities,
  layer violations, duplicated logic, etc.}
**Desired state:** {describe the target structure}
**Constraints:**
- Must not change the public API (existing callers must work unchanged)
- Must not change database schema
- All existing tests must continue to pass
- {any other constraints}

Please:
1. Read the current module and all its callers
2. Propose a refactoring plan (don't code yet)
3. After I approve the plan, implement it incrementally
4. Run tests after each step to verify nothing breaks
5. Update any affected CLAUDE.md files
```

#### Pattern 9: Add Observability to a Service

```
Add observability to {service/module}:

**What to instrument:**
- {operation 1}: latency, success/failure, {custom dimension}
- {operation 2}: latency, token count, model used
- {operation 3}: count, error rate

**Tools:**
- Sentry for error tracking (already configured)
- Datadog for metrics and APM (already configured)
- Structured logging via Python's structlog

**Requirements:**
- Add structured log entries at INFO level for happy paths
- Add structured log entries at ERROR level with full context for failures
- Add Datadog custom metrics for LLM call duration and token counts
- Add Sentry breadcrumbs for the request lifecycle
- Do NOT log any PII (student names, parent emails) — COPPA requirement
- DO log: student_id (UUID), skill_id, mastery_probability, model_used, token_count
```

#### Pattern 10: Security Review This Code

```
Perform a security review of {file/module path}:

Check for:
1. OWASP Top 10 vulnerabilities relevant to this code
2. SQL injection (even through SQLAlchemy — check for raw SQL, text())
3. Authentication/authorization bypass
4. PII exposure in logs, error messages, or API responses
5. COPPA violations:
   - Is child data being collected without consent checks?
   - Is PII being sent to third-party services?
   - Is data being retained beyond what's necessary?
6. Insecure deserialization (Pydantic validation bypass)
7. Rate limiting on sensitive endpoints
8. Input validation gaps

For each finding, classify as:
- CRITICAL: Must fix before merge
- HIGH: Must fix before staging deploy
- MEDIUM: Fix within the sprint
- LOW: Add to backlog
```

#### Bonus Pattern 11: Generate Oregon Standards Fixtures

```
Generate test fixture data for Oregon math standards:

**Grade:** {grade level}
**Domain:** {math domain}
**Standards to cover:** {list of standard IDs}

For each standard, generate:
1. 5 questions at varying difficulty (easy, medium, hard, very hard, expert)
2. Each question must have: stem, 4 answer choices, correct answer, 
   KaTeX-formatted math notation where applicable, hint text, 
   full solution explanation
3. Questions must be mathematically correct — verify the answer
4. Distractors must represent common student misconceptions

Output as JSON matching the QuestionBank Pydantic model in 
services/question-generator/src/templates/.
```

---

### 3.4 Staged Context Management

Claude Code's context window is finite. Managing it well is the difference between productive sessions and confused, hallucinating ones.

#### Files to Always Include in Context
These files should be referenced at the start of relevant sessions:
- `CLAUDE.md` (root) — always
- `{sub-package}/CLAUDE.md` — when working in that sub-package
- `apps/api/src/core/exceptions.py` — when working on backend code
- `apps/api/src/core/config.py` — when working on backend code
- `packages/types/src/index.ts` — when working on frontend code
- The specific file being modified and its direct dependencies

#### Files to Exclude from Context
Add these to `.gitignore`-style exclusions:
- `node_modules/` — never
- `.next/` — never
- `__pycache__/` — never
- `*.pyc` — never
- `alembic/versions/` — only include when writing migrations
- `dist/`, `build/` — never
- Generated OpenAPI docs — only include when verifying API contracts
- Test coverage reports — never

#### Focused Context Windows by Sub-System

**Frontend session:** CLAUDE.md → apps/web/CLAUDE.md → packages/types/ → packages/ui/ → the specific component
**Backend API session:** CLAUDE.md → apps/api/CLAUDE.md → the specific layer files (route + service + repo + models)
**Agent engine session:** CLAUDE.md → services/agent-engine/CLAUDE.md → the specific graph + nodes + state
**BKT session:** CLAUDE.md → services/bkt-engine/CLAUDE.md → engine/ + models/ + fixtures
**Infrastructure session:** CLAUDE.md → infrastructure/terraform/modules/{specific module}

#### When to Start a New Session
- Token usage exceeds 60K (check with `/context`)
- Switching between sub-systems (frontend → backend)
- After completing a feature and before starting the next
- If Claude Code starts repeating itself or producing inconsistent code
- After a long debugging session (context is often polluted with error traces)

---

### 3.5 Code Review Workflow with Claude Code

Use Claude Code for self-review before creating a PR. This catches 80% of issues before human eyes see the code.

#### Security Review Prompt
```
Review all files changed in this branch (git diff main...HEAD) for security issues.
Focus on: SQL injection, auth bypass, PII exposure, COPPA violations,
insecure dependencies, missing input validation, error message information leakage.
Rate each finding: CRITICAL / HIGH / MEDIUM / LOW.
```

#### Performance Review Prompt
```
Review all files changed in this branch for performance issues.
Focus on: N+1 queries, missing database indexes, unbounded queries,
unnecessary LLM calls, missing caching opportunities, large payload sizes,
blocking operations in async context.
Rate each finding by estimated impact.
```

#### COPPA Compliance Check Prompt
```
Review all files changed in this branch for COPPA compliance.
Check: Is any child PII being collected, stored, or transmitted?
Is parental consent verified before any data collection?
Are there any third-party services receiving child data?
Is data retention limited to what's necessary?
Are there any analytics or tracking that could identify a child?
```

#### Pattern Compliance Prompt
```
Review all files changed in this branch against our coding standards:
- Does the backend code follow the layered architecture? (API → Service → Repo)
- Are all LLM prompts in .jinja2 template files?
- Are all new Pydantic models using v2 syntax?
- Do all new endpoints have proper auth dependencies?
- Are all new database queries using keyset pagination (not OFFSET)?
- Do all new components follow the component patterns (Server vs Client)?
- Are there tests for all new functionality?
```

---
## 4. Coding Standards & Patterns

### 4.1 Python Backend Standards

#### 4.1.1 Module Structure

Every Python service follows this standard layout:

```
services/{service-name}/
├── src/
│   ├── __init__.py
│   ├── models/              # Pydantic v2 input/output contracts
│   │   ├── __init__.py
│   │   └── {domain}.py
│   ├── repository/          # Database access layer
│   │   ├── __init__.py
│   │   ├── base.py          # Base repository with common CRUD
│   │   └── {domain}_repo.py
│   ├── service/             # Business logic layer
│   │   ├── __init__.py
│   │   └── {domain}_service.py
│   ├── api/                 # FastAPI routers
│   │   ├── __init__.py
│   │   └── router.py
│   └── core/                # Shared utilities, config, exceptions
│       ├── __init__.py
│       ├── config.py
│       └── exceptions.py
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── conftest.py
│   └── fixtures/
├── alembic/                 # Only if this service owns tables
├── pyproject.toml
├── CLAUDE.md
└── README.md
```

#### 4.1.2 Layered Architecture Rules

These rules are **strictly enforced**. Code that violates them will not be merged.

**API Layer (`api/`)** — The HTTP boundary:
- ONLY: Parse request, validate with Pydantic, check auth, call service layer, serialize response
- CAN import: FastAPI, Pydantic models, service classes, auth dependencies
- CANNOT import: SQLAlchemy, repository classes, direct DB session
- CANNOT contain: Business logic, database queries, direct LLM calls

**Service Layer (`service/`)** — The business logic:
- ONLY: Orchestrate business rules, call repository layer, call external clients (LLM, Redis)
- CAN import: Repository classes, Pydantic models, external clients, domain exceptions
- CANNOT import: FastAPI types (`Request`, `Response`, `HTTPException`, `Depends`)
- CANNOT contain: SQL queries, HTTP-specific logic, request parsing

**Repository Layer (`repository/`)** — The data access boundary:
- ONLY: SQLAlchemy queries, data transformation from ORM to domain objects
- CAN import: SQLAlchemy, database table models, Pydantic models (for return types)
- CANNOT import: FastAPI types, service classes, external HTTP clients
- CANNOT contain: Business logic, HTTP calls, LLM calls

**Enforcement:** We use a custom `ruff` rule (or `import-linter`) in CI to verify import boundaries:

```toml
# pyproject.toml — import boundary enforcement
[tool.importlinter]
root_packages = ["src"]

[[tool.importlinter.contracts]]
name = "API layer cannot import repository"
type = "forbidden"
source_modules = ["src.api"]
forbidden_modules = ["src.repository", "sqlalchemy"]

[[tool.importlinter.contracts]]
name = "Service layer cannot import FastAPI"
type = "forbidden"
source_modules = ["src.service"]
forbidden_modules = ["fastapi", "starlette"]

[[tool.importlinter.contracts]]
name = "Repository layer cannot import service or API"
type = "forbidden"
source_modules = ["src.repository"]
forbidden_modules = ["src.service", "src.api", "fastapi"]
```

#### 4.1.3 Dependency Injection Pattern

```python
# apps/api/src/api/deps.py — Shared FastAPI dependencies

from collections.abc import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import Settings, get_settings
from src.core.security import get_current_student, get_current_parent
from src.db.session import async_session_factory
from src.repository.assessment_repo import AssessmentRepository
from src.repository.student_repo import StudentRepository
from src.service.assessment_service import AssessmentService
from src.service.student_service import StudentService
from src.clients.llm_client import LLMClient


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session, auto-commit on success, rollback on error."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def get_assessment_repo(
    session: AsyncSession = Depends(get_db_session),
) -> AssessmentRepository:
    return AssessmentRepository(session)


def get_llm_client(
    settings: Settings = Depends(get_settings),
) -> LLMClient:
    return LLMClient(settings=settings)


def get_assessment_service(
    repo: AssessmentRepository = Depends(get_assessment_repo),
    llm_client: LLMClient = Depends(get_llm_client),
) -> AssessmentService:
    return AssessmentService(repo=repo, llm_client=llm_client)


# Usage in route:
@router.post("/assessments/{assessment_id}/submit", response_model=SubmitResponse)
async def submit_answer(
    assessment_id: UUID,
    request: SubmitAnswerRequest,
    student: StudentProfile = Depends(get_current_student),
    service: AssessmentService = Depends(get_assessment_service),
) -> SubmitResponse:
    return await service.submit_answer(
        assessment_id=assessment_id,
        student_id=student.id,
        answer=request.answer,
    )
```

#### 4.1.4 Error Handling

**Custom exception hierarchy:**

```python
# apps/api/src/core/exceptions.py

from typing import Any


class AppError(Exception):
    """Base exception for all application errors."""

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class ValidationError(AppError):
    """Input validation failed."""
    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, code="VALIDATION_ERROR", status_code=422, details=details)


class NotFoundError(AppError):
    """Requested resource does not exist."""
    def __init__(self, resource: str, resource_id: str) -> None:
        super().__init__(
            message=f"{resource} not found",
            code="NOT_FOUND",
            status_code=404,
            details={"resource": resource, "id": resource_id},
        )


class AuthError(AppError):
    """Authentication or authorization failure."""
    def __init__(self, message: str = "Unauthorized") -> None:
        super().__init__(message, code="AUTH_ERROR", status_code=401)


class ForbiddenError(AppError):
    """User lacks permission for this action."""
    def __init__(self, message: str = "Forbidden") -> None:
        super().__init__(message, code="FORBIDDEN", status_code=403)


class ConsentRequiredError(AppError):
    """COPPA: Parental consent required before this action."""
    def __init__(self, student_id: str) -> None:
        super().__init__(
            message="Parental consent required",
            code="CONSENT_REQUIRED",
            status_code=403,
            details={"student_id": student_id},
        )


class LLMError(AppError):
    """LLM call failed after all retries."""
    def __init__(self, model: str, message: str) -> None:
        super().__init__(
            message=f"LLM call failed: {message}",
            code="LLM_ERROR",
            status_code=502,
            details={"model": model},
        )


class BKTError(AppError):
    """Bayesian Knowledge Tracing computation failed."""
    def __init__(self, skill_id: str, message: str) -> None:
        super().__init__(
            message=f"BKT error for skill {skill_id}: {message}",
            code="BKT_ERROR",
            status_code=500,
            details={"skill_id": skill_id},
        )


class RateLimitError(AppError):
    """Request rate limit exceeded."""
    def __init__(self, retry_after: int = 60) -> None:
        super().__init__(
            message="Rate limit exceeded",
            code="RATE_LIMIT",
            status_code=429,
            details={"retry_after_seconds": retry_after},
        )
```

**Global exception handler:**

```python
# apps/api/src/main.py (excerpt)

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import structlog

logger = structlog.get_logger()


def create_app() -> FastAPI:
    app = FastAPI(title="MathPath Oregon API", version="1.0.0")

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        logger.error(
            "app_error",
            code=exc.code,
            message=exc.message,
            path=request.url.path,
            method=request.method,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details,
                }
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception(
            "unhandled_error",
            path=request.url.path,
            method=request.method,
        )
        # NEVER expose stack traces to clients
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred",
                    "details": {},
                }
            },
        )

    return app
```

#### 4.1.5 Pydantic v2 Patterns

```python
# Standard Pydantic v2 patterns for this project

from datetime import datetime
from uuid import UUID, uuid4
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class BaseSchema(BaseModel):
    """Base schema for all API models."""
    model_config = ConfigDict(
        from_attributes=True,         # Enable ORM mode (was orm_mode in v1)
        populate_by_name=True,        # Allow field aliases
        str_strip_whitespace=True,    # Strip whitespace from strings
        json_schema_extra={"examples": []},  # OpenAPI examples
    )


class TimestampMixin(BaseModel):
    """Mixin for created_at/updated_at timestamps."""
    created_at: datetime
    updated_at: datetime


class CreateAssessmentRequest(BaseSchema):
    """Request to start a new diagnostic assessment."""
    grade_level: int = Field(..., ge=0, le=8, description="Student grade level K-8")
    domains: list[str] = Field(
        ...,
        min_length=1,
        description="Math domains to assess (OA, NBT, NF, etc.)",
    )

    @field_validator("domains")
    @classmethod
    def validate_domains(cls, v: list[str]) -> list[str]:
        valid_domains = {"OA", "NBT", "NF", "MD", "G", "RP", "EE", "SP", "F"}
        invalid = set(v) - valid_domains
        if invalid:
            msg = f"Invalid domains: {invalid}. Valid: {valid_domains}"
            raise ValueError(msg)
        return v


class AssessmentResponse(BaseSchema, TimestampMixin):
    """Response containing assessment details."""
    id: UUID
    student_id: UUID
    grade_level: int
    status: str
    current_question_index: int
    total_questions: int


class PaginatedResponse(BaseSchema):
    """Generic paginated response using keyset pagination."""
    items: list  # Override in subclass with specific type
    next_cursor: str | None = Field(
        None, description="Cursor for next page. None if last page."
    )
    has_more: bool


class SubmitAnswerRequest(BaseSchema):
    """Request to submit an answer to an assessment question."""
    answer: str = Field(..., max_length=1000)
    time_spent_ms: int = Field(..., ge=0, le=300_000, description="Time in milliseconds")

    @model_validator(mode="after")
    def validate_answer_not_empty(self) -> "SubmitAnswerRequest":
        if not self.answer.strip():
            msg = "Answer cannot be empty or whitespace"
            raise ValueError(msg)
        return self
```

#### 4.1.6 Async Patterns

```python
# When to use async def vs def:

# ASYNC: All FastAPI endpoints
@router.get("/students/{student_id}")
async def get_student(student_id: UUID) -> StudentResponse: ...

# ASYNC: All database operations
async def get_student_by_id(self, student_id: UUID) -> Student | None:
    result = await self.session.execute(
        select(StudentTable).where(StudentTable.id == student_id)
    )
    return result.scalar_one_or_none()

# ASYNC: All LLM API calls
async def generate_hint(self, context: HintContext) -> str:
    response = await self.anthropic_client.messages.create(...)
    return response.content[0].text

# SYNC (run in executor): CPU-bound BKT computations
import asyncio
from concurrent.futures import ThreadPoolExecutor

_bkt_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="bkt")

async def update_mastery(self, student_id: UUID, skill_id: str, correct: bool) -> float:
    """Run BKT update in thread pool (CPU-bound)."""
    loop = asyncio.get_event_loop()
    mastery = await loop.run_in_executor(
        _bkt_executor,
        self._sync_update_mastery,
        student_id,
        skill_id,
        correct,
    )
    return mastery

def _sync_update_mastery(self, student_id: UUID, skill_id: str, correct: bool) -> float:
    """Synchronous BKT computation — runs in thread pool."""
    response = 1 if correct else 0
    self.roster.update_state(skill_id, str(student_id), response)
    return self.roster.get_mastery_prob(skill_id, str(student_id))


# ASYNC: Concurrent LLM calls
async def generate_hint_and_log(self, context: HintContext) -> HintResult:
    """Run hint generation and analytics logging concurrently."""
    hint_task = self.llm_client.generate_hint(context)
    log_task = self.analytics.log_hint_request(context)
    hint, _ = await asyncio.gather(hint_task, log_task)
    return HintResult(hint=hint)
```

#### 4.1.7 Type Safety

```toml
# pyproject.toml — mypy strict configuration
[tool.mypy]
python_version = "3.12"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_any_generics = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
no_implicit_reexport = true

# Allow `Any` only at explicit external library boundaries
[[tool.mypy.overrides]]
module = ["pyBKT.*", "langchain.*", "langgraph.*"]
ignore_missing_imports = true
disallow_any_explicit = false
```

**Type boundary pattern for external libraries:**

```python
from typing import Any

# External library boundary — Any is acceptable HERE ONLY
def _call_pybkt_fit(data: Any) -> Any:
    """Thin wrapper around pyBKT. Any types are acceptable at this boundary."""
    from pyBKT.models import Model
    model = Model(seed=42, num_fits=1)
    model.fit(data=data)
    return model.params()

# Internal interface — fully typed, no Any
def fit_bkt_model(responses: list[StudentResponse]) -> SkillParameters:
    """Fit BKT model to student responses. Fully typed internal API."""
    data = _prepare_pybkt_dataframe(responses)
    raw_params = _call_pybkt_fit(data)
    return SkillParameters.from_pybkt(raw_params)  # Pydantic validation
```

---

### 4.2 TypeScript Frontend Standards

#### 4.2.1 Component Patterns

**Server Components vs. Client Components (Next.js 15 App Router):**

| Use Server Component When | Use Client Component When |
|---------------------------|--------------------------|
| Fetching data (no interactivity) | User interactions (clicks, inputs, forms) |
| Displaying static or cached content | Browser APIs (localStorage, geolocation) |
| Accessing backend resources directly | React hooks (useState, useEffect, useRef) |
| Rendering markdown, math notation | Animations, transitions |
| SEO-critical content | Real-time updates (WebSocket, SSE) |

**Component file structure:**

```typescript
// apps/web/src/components/practice/QuestionCard/index.tsx
"use client"; // Only if this is a Client Component

import { type FC } from "react";
import { MathDisplay } from "@mathpath/math-renderer";
import { Card, Badge } from "@mathpath/ui";

// 1. Props interface — always exported, always named {Component}Props
export interface QuestionCardProps {
  question: Question;
  questionNumber: number;
  totalQuestions: number;
  onAnswerSelect: (answerId: string) => void;
  selectedAnswer: string | null;
  isSubmitting: boolean;
}

// 2. Component function — default export
const QuestionCard: FC<QuestionCardProps> = ({
  question,
  questionNumber,
  totalQuestions,
  onAnswerSelect,
  selectedAnswer,
  isSubmitting,
}) => {
  return (
    <Card className="p-6">
      <div className="flex items-center justify-between mb-4">
        <Badge variant="secondary">
          Question {questionNumber} of {totalQuestions}
        </Badge>
        <Badge variant="outline">{question.domain}</Badge>
      </div>

      <div className="mb-6">
        <MathDisplay latex={question.stem} />
      </div>

      <div className="space-y-3" role="radiogroup" aria-label="Answer choices">
        {question.choices.map((choice) => (
          <AnswerChoice
            key={choice.id}
            choice={choice}
            isSelected={selectedAnswer === choice.id}
            onSelect={() => onAnswerSelect(choice.id)}
            disabled={isSubmitting}
          />
        ))}
      </div>
    </Card>
  );
};

export default QuestionCard;

// 3. Subcomponents — in the same file if small
interface AnswerChoiceProps {
  choice: AnswerOption;
  isSelected: boolean;
  onSelect: () => void;
  disabled: boolean;
}

const AnswerChoice: FC<AnswerChoiceProps> = ({
  choice,
  isSelected,
  onSelect,
  disabled,
}) => (
  <button
    onClick={onSelect}
    disabled={disabled}
    role="radio"
    aria-checked={isSelected}
    aria-label={`Answer option: ${choice.label}`}
    className={`w-full p-4 rounded-lg border-2 text-left transition-colors
      ${isSelected
        ? "border-blue-500 bg-blue-50"
        : "border-gray-200 hover:border-gray-300"
      }
      ${disabled ? "opacity-50 cursor-not-allowed" : "cursor-pointer"}
    `}
  >
    <MathDisplay latex={choice.text} />
  </button>
);
```

#### 4.2.2 File Naming Conventions

| Type | Convention | Example |
|------|-----------|---------|
| Components | PascalCase directory + index.tsx | `QuestionCard/index.tsx` |
| Hooks | camelCase, `use` prefix | `useAssessmentSession.ts` |
| Utilities | camelCase | `formatMastery.ts` |
| Pages/routes | kebab-case | `app/(student)/practice/page.tsx` |
| Types | PascalCase | `AssessmentTypes.ts` |
| Stores | camelCase, `-store` suffix | `assessment-store.ts` |
| API client | camelCase | `api-client.ts` |
| Constants | UPPER_SNAKE_CASE in file | `constants.ts` → `MAX_QUESTIONS` |

#### 4.2.3 State Management Tiers

```
Tier 1: Server State (Next.js Server Components + cache)
├── Use for: Page data that doesn't change during the session
├── Pattern: async Server Component with fetch() + cache tags
└── Example: Student profile, standards list, completed assessments

Tier 2: Remote State (SWR for API data)
├── Use for: Data that may change and needs cache/revalidation
├── Pattern: useSWR with typed fetcher
└── Example: Current mastery levels, recent practice results

Tier 3: Session State (Zustand)
├── Use for: Client-side state that persists across page navigations
├── Pattern: Zustand store with typed actions
└── Example: Active assessment session, user preferences, UI settings

Tier 4: Local State (useState)
├── Use for: UI state scoped to a single component
├── Pattern: useState with typed initial value
└── Example: Form inputs, dropdown open/close, animation state
```

**Zustand store pattern:**

```typescript
// apps/web/src/stores/assessment-store.ts
import { create } from "zustand";
import { devtools } from "zustand/middleware";
import type { Question, AssessmentSession, SubmitResult } from "@mathpath/types";

interface AssessmentState {
  // State
  session: AssessmentSession | null;
  currentQuestion: Question | null;
  selectedAnswer: string | null;
  isSubmitting: boolean;
  error: string | null;

  // Actions
  startSession: (session: AssessmentSession) -> void;
  setCurrentQuestion: (question: Question) -> void;
  selectAnswer: (answerId: string) -> void;
  submitAnswer: () -> Promise<SubmitResult>;
  endSession: () -> void;
  clearError: () -> void;
}

export const useAssessmentStore = create<AssessmentState>()(
  devtools(
    (set, get) => ({
      // Initial state
      session: null,
      currentQuestion: null,
      selectedAnswer: null,
      isSubmitting: false,
      error: null,

      // Actions
      startSession: (session) => set({ session, error: null }),

      setCurrentQuestion: (question) =>
        set({ currentQuestion: question, selectedAnswer: null }),

      selectAnswer: (answerId) => set({ selectedAnswer: answerId }),

      submitAnswer: async () => {
        const { session, currentQuestion, selectedAnswer } = get();
        if (!session || !currentQuestion || !selectedAnswer) {
          throw new Error("Cannot submit: missing session, question, or answer");
        }

        set({ isSubmitting: true, error: null });
        try {
          const result = await apiClient.submitAnswer({
            assessmentId: session.id,
            questionId: currentQuestion.id,
            answer: selectedAnswer,
          });
          set({ isSubmitting: false });
          return result;
        } catch (err) {
          set({ isSubmitting: false, error: "Failed to submit answer" });
          throw err;
        }
      },

      endSession: () =>
        set({
          session: null,
          currentQuestion: null,
          selectedAnswer: null,
          isSubmitting: false,
          error: null,
        }),

      clearError: () => set({ error: null }),
    }),
    { name: "assessment-store" },
  ),
);
```

#### 4.2.4 API Client Pattern

```typescript
// apps/web/src/lib/api-client.ts

import type {
  AssessmentResponse,
  CreateAssessmentRequest,
  SubmitAnswerRequest,
  SubmitResult,
  PaginatedResponse,
  StudentProfile,
} from "@mathpath/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

class APIError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
    public details: Record<string, unknown> = {},
  ) {
    super(message);
    this.name = "APIError";
  }
}

async function fetchAPI<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const url = `${API_BASE}/api/v1${path}`;

  const response = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    credentials: "include",
  });

  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({}));
    throw new APIError(
      response.status,
      errorBody.error?.code ?? "UNKNOWN",
      errorBody.error?.message ?? `HTTP ${response.status}`,
      errorBody.error?.details ?? {},
    );
  }

  return response.json() as Promise<T>;
}

export const apiClient = {
  // Assessments
  createAssessment: (data: CreateAssessmentRequest) =>
    fetchAPI<AssessmentResponse>("/assessments", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  submitAnswer: (data: SubmitAnswerRequest & { assessmentId: string }) =>
    fetchAPI<SubmitResult>(
      `/assessments/${data.assessmentId}/submit`,
      { method: "POST", body: JSON.stringify(data) },
    ),

  // Students
  getProfile: () =>
    fetchAPI<StudentProfile>("/students/me"),

  // Practice
  getPracticeSession: (skillId: string) =>
    fetchAPI<PracticeSession>(`/practice/sessions?skill=${skillId}`, {
      method: "POST",
    }),
} as const;
```

#### 4.2.5 Form Pattern (React Hook Form + Zod)

```typescript
// Example: Assessment answer form
"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";

const answerSchema = z.object({
  selectedAnswer: z.string().min(1, "Please select an answer"),
  confidence: z.enum(["guess", "unsure", "confident"]).optional(),
});

type AnswerFormData = z.infer<typeof answerSchema>;

export function AnswerForm({
  onSubmit,
  choices,
}: {
  onSubmit: (data: AnswerFormData) => Promise<void>;
  choices: AnswerOption[];
}) {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<AnswerFormData>({
    resolver: zodResolver(answerSchema),
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)} aria-label="Answer submission form">
      <fieldset disabled={isSubmitting}>
        <legend className="sr-only">Select your answer</legend>
        {choices.map((choice) => (
          <label key={choice.id} className="flex items-center gap-3 p-3">
            <input
              type="radio"
              value={choice.id}
              {...register("selectedAnswer")}
              aria-describedby={errors.selectedAnswer ? "answer-error" : undefined}
            />
            <span>{choice.text}</span>
          </label>
        ))}
        {errors.selectedAnswer && (
          <p id="answer-error" role="alert" className="text-red-600 text-sm">
            {errors.selectedAnswer.message}
          </p>
        )}
      </fieldset>

      <button
        type="submit"
        disabled={isSubmitting}
        className="mt-4 px-6 py-2 bg-blue-600 text-white rounded-lg disabled:opacity-50"
      >
        {isSubmitting ? "Submitting…" : "Submit Answer"}
      </button>
    </form>
  );
}
```

#### 4.2.6 Accessibility Standards

WCAG 2.1 AA is the minimum. This is a children's education app — accessibility is non-negotiable.

**Mandatory requirements:**
- All interactive elements must be keyboard accessible (Tab, Enter, Space, Escape)
- All images must have `alt` text (decorative images use `alt=""`)
- All form inputs must have associated `<label>` elements or `aria-label`
- Color is never the sole indicator of state (always combine with text/icon)
- Minimum contrast ratio: 4.5:1 for normal text, 3:1 for large text
- Focus indicators must be visible (never `outline: none` without replacement)
- All dynamic content changes announced via `aria-live` regions
- Page navigation announces route changes to screen readers
- Math content rendered via KaTeX includes `aria-label` with spoken math equivalent

**Testing:** Every component test includes `jest-axe` accessibility assertions:
```typescript
import { axe, toHaveNoViolations } from "jest-axe";
expect.extend(toHaveNoViolations);

it("has no accessibility violations", async () => {
  const { container } = render(<QuestionCard {...props} />);
  const results = await axe(container);
  expect(results).toHaveNoViolations();
});
```

---

### 4.3 Database Standards

#### 4.3.1 Migration Rules

1. **Forward-only after staging deploy.** Once a migration has run in staging, never modify it. Create a new migration instead.
2. **Idempotent where possible.** Use `IF NOT EXISTS` for index creation, `IF EXISTS` for drops.
3. **No raw SQL in application code.** All queries use SQLAlchemy ORM or Core expressions. The only raw SQL lives in Alembic migrations.
4. **Naming convention:** `{YYYYMMDD_HHMMSS}_{descriptive_name}.py` (e.g., `20260404_143000_add_mastery_state_table.py`)
5. **Every migration has a description** in the `"""docstring"""` explaining what and why.
6. **Test against fresh AND existing:** CI runs migrations against an empty DB (from scratch) and against the current schema (incremental).

#### 4.3.2 Schema Patterns

**Base table mixin:**

```python
# apps/api/src/db/base.py
import uuid
from datetime import datetime
from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    """All tables include created_at and updated_at."""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class SoftDeleteMixin:
    """Opt-in soft delete support."""
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )


class BaseTable(Base, TimestampMixin):
    """Standard base for all tables: UUID PK + timestamps."""
    __abstract__ = True

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
```

**Example table with PII annotation:**

```python
# apps/api/src/db/tables/student.py
from sqlalchemy import String, Integer, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import BaseTable, SoftDeleteMixin


class StudentTable(BaseTable, SoftDeleteMixin):
    """Student profile. Contains PII — subject to COPPA."""
    __tablename__ = "students"

    # PII fields — prefixed with pii_ for easy identification
    # These fields are encrypted at rest via RDS encryption
    pii_display_name: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="COPPA PII: student display name"
    )
    grade_level: Mapped[int] = mapped_column(Integer, nullable=False)
    parent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("parents.id", ondelete="CASCADE"),
        nullable=False,
    )
    auth0_user_id: Mapped[str] = mapped_column(
        String(128), unique=True, nullable=False,
        comment="Auth0 user identifier — not PII itself but links to PII in Auth0"
    )

    # Relationships
    parent = relationship("ParentTable", back_populates="students")
    assessments = relationship("AssessmentTable", back_populates="student")

    # Indexes with rationale
    __table_args__ = (
        Index("ix_students_parent_id", "parent_id"),        # Parent lookups
        Index("ix_students_grade_level", "grade_level"),     # Grade filtering
        Index("ix_students_auth0_id", "auth0_user_id"),      # Auth lookups
        Index("ix_students_not_deleted", "deleted_at",       # Soft delete filter
              postgresql_where=mapped_column("deleted_at").is_(None)),
    )
```

#### 4.3.3 Query Patterns

**N+1 prevention:**
```python
# WRONG — triggers N+1 when accessing student.assessments
students = await session.execute(select(StudentTable))

# RIGHT — eager load relationships you know you'll use
from sqlalchemy.orm import selectinload

students = await session.execute(
    select(StudentTable)
    .where(StudentTable.grade_level == grade)
    .options(selectinload(StudentTable.assessments))
)
```

**Keyset pagination (never OFFSET):**
```python
# apps/api/src/repository/base.py

from sqlalchemy import select, and_
from uuid import UUID

async def paginate_keyset(
    self,
    query,
    cursor: UUID | None = None,
    limit: int = 20,
):
    """Keyset pagination — O(1) regardless of page depth."""
    if cursor:
        query = query.where(
            and_(
                self.model.created_at <= select(self.model.created_at).where(
                    self.model.id == cursor
                ).scalar_subquery(),
                self.model.id < cursor,  # Tiebreaker for same timestamp
            )
        )

    query = query.order_by(
        self.model.created_at.desc(),
        self.model.id.desc(),
    ).limit(limit + 1)  # Fetch one extra to determine has_more

    result = await self.session.execute(query)
    items = list(result.scalars().all())

    has_more = len(items) > limit
    if has_more:
        items = items[:limit]

    next_cursor = str(items[-1].id) if has_more and items else None
    return items, next_cursor, has_more
```

**Soft delete filter (applied globally):**
```python
# Event listener to auto-filter soft-deleted records
from sqlalchemy import event

@event.listens_for(Session, "do_orm_execute")
def _apply_soft_delete_filter(orm_execute_state):
    """Automatically filter out soft-deleted records on all SELECT queries."""
    if (
        orm_execute_state.is_select
        and not orm_execute_state.execution_options.get("include_deleted", False)
    ):
        orm_execute_state.statement = orm_execute_state.statement.options(
            with_loader_criteria(
                SoftDeleteMixin,
                lambda cls: cls.deleted_at.is_(None),
                include_aliases=True,
            )
        )
```

---

### 4.4 AI/LLM Code Standards

#### 4.4.1 Prompt Management

**All prompts are Jinja2 templates stored in `prompts/` directories. Never hardcode prompts in Python files.**

```
apps/api/prompts/
├── tutor_hint_v1.0.jinja2
├── tutor_hint_v1.1.jinja2      # Version bump for modified prompt
├── question_gen_v1.0.jinja2
├── learning_plan_v1.0.jinja2
└── response_eval_v1.0.jinja2

services/agent-engine/src/prompts/
├── hint_generation_v1.0.jinja2
├── response_eval_v1.0.jinja2
├── scaffolding_v1.0.jinja2
└── intent_classification_v1.0.jinja2
```

**Prompt template pattern:**
```jinja2
{# prompts/tutor_hint_v1.0.jinja2 #}
{# Version: 1.0 | Author: eng-lead | Date: 2026-04-04 #}
{# Purpose: Generate a contextual hint for a student struggling with a math problem #}
{# Model: Claude Sonnet 4 | Max tokens: 300 #}

You are a patient, encouraging math tutor helping a {{ grade_level }} grade student
with {{ domain_name }} (Oregon standard {{ standard_id }}).

## Current Problem
{{ question_stem }}

## Student's Response
{{ student_response }}

## What the student got wrong
{{ error_analysis }}

## Previous hints given (do not repeat)
{% for hint in hint_history %}
- {{ hint }}
{% endfor %}

## Instructions
Generate a hint that:
1. Does NOT give away the answer directly
2. Addresses the specific misconception shown in the student's response
3. Uses age-appropriate language for grade {{ grade_level }}
4. Includes a concrete example or visual analogy when helpful
5. Is encouraging and growth-mindset oriented
6. Uses LaTeX notation (delimited by $) for any math expressions

Respond with ONLY the hint text. No preamble.
```

#### 4.4.2 LLM Client Wrapper

**All LLM calls go through this wrapper. Never call Anthropic or OpenAI SDKs directly in business logic.**

```python
# apps/api/src/clients/llm_client.py

import time
import asyncio
import structlog
from typing import TypeVar
from pydantic import BaseModel
from anthropic import AsyncAnthropic
from openai import AsyncOpenAI
from jinja2 import Environment, FileSystemLoader

from src.core.config import Settings
from src.core.exceptions import LLMError

logger = structlog.get_logger()
T = TypeVar("T", bound=BaseModel)


class LLMClient:
    """Unified LLM interface with retry, fallback, cost tracking, and validation."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.anthropic = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.openai = AsyncOpenAI(api_key=settings.openai_api_key)
        self.jinja_env = Environment(
            loader=FileSystemLoader(settings.prompts_dir),
            autoescape=False,
        )
        self._session_cost = 0.0
        self._session_tokens = 0

    async def generate(
        self,
        template_name: str,
        template_vars: dict,
        *,
        model: str = "claude-sonnet-4",
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> str:
        """Generate text from an LLM using a Jinja2 prompt template."""
        prompt = self._render_template(template_name, template_vars)
        return await self._call_with_retry(
            prompt=prompt,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
        )

    async def generate_structured(
        self,
        template_name: str,
        template_vars: dict,
        response_model: type[T],
        *,
        model: str = "claude-sonnet-4",
        max_tokens: int = 1024,
    ) -> T:
        """Generate structured output validated against a Pydantic model."""
        prompt = self._render_template(template_name, template_vars)
        prompt += f"\n\nRespond with valid JSON matching this schema:\n{response_model.model_json_schema()}"

        raw = await self._call_with_retry(
            prompt=prompt, model=model, max_tokens=max_tokens, temperature=0.3,
        )

        try:
            return response_model.model_validate_json(raw)
        except Exception as e:
            logger.error("llm_structured_output_validation_failed", model=model, error=str(e))
            raise LLMError(model=model, message=f"Output validation failed: {e}")

    async def _call_with_retry(
        self,
        prompt: str,
        model: str,
        max_tokens: int,
        temperature: float,
        max_retries: int = 3,
    ) -> str:
        """Call LLM with exponential backoff retry and model fallback."""
        last_error: Exception | None = None

        for attempt in range(max_retries):
            try:
                start = time.monotonic()
                result = await self._dispatch_call(prompt, model, max_tokens, temperature)
                duration = time.monotonic() - start

                logger.info(
                    "llm_call_success",
                    model=model,
                    duration_ms=round(duration * 1000),
                    input_tokens=result.input_tokens,
                    output_tokens=result.output_tokens,
                )
                self._track_cost(model, result.input_tokens, result.output_tokens)
                return result.text

            except Exception as e:
                last_error = e
                wait = 2 ** attempt
                logger.warning(
                    "llm_call_retry",
                    model=model,
                    attempt=attempt + 1,
                    wait_seconds=wait,
                    error=str(e),
                )
                await asyncio.sleep(wait)

        # All retries failed — try fallback model
        fallback = self._get_fallback_model(model)
        if fallback:
            logger.warning("llm_fallback", from_model=model, to_model=fallback)
            try:
                result = await self._dispatch_call(prompt, fallback, max_tokens, temperature)
                return result.text
            except Exception as e:
                last_error = e

        raise LLMError(model=model, message=str(last_error))

    def _get_fallback_model(self, model: str) -> str | None:
        """Model fallback chain."""
        fallbacks = {
            "claude-sonnet-4": "gpt-4o",
            "gpt-4o": "o3-mini",
            "claude-opus-4": "claude-sonnet-4",
        }
        return fallbacks.get(model)

    def _track_cost(self, model: str, input_tokens: int, output_tokens: int) -> None:
        """Track per-session cost. Alert if exceeding budget."""
        # Approximate costs per 1K tokens (update as pricing changes)
        costs_per_1k = {
            "claude-sonnet-4": {"input": 0.003, "output": 0.015},
            "claude-opus-4": {"input": 0.015, "output": 0.075},
            "gpt-4o": {"input": 0.0025, "output": 0.01},
            "o3-mini": {"input": 0.0011, "output": 0.0044},
        }
        rates = costs_per_1k.get(model, {"input": 0.01, "output": 0.03})
        cost = (input_tokens / 1000 * rates["input"]) + (output_tokens / 1000 * rates["output"])
        self._session_cost += cost
        self._session_tokens += input_tokens + output_tokens

        if self._session_cost > 0.15:
            logger.warning(
                "llm_session_cost_alert",
                session_cost=round(self._session_cost, 4),
                session_tokens=self._session_tokens,
            )

    def _render_template(self, template_name: str, variables: dict) -> str:
        template = self.jinja_env.get_template(template_name)
        return template.render(**variables)
```

#### 4.4.3 Agent Patterns (LangGraph)

**Every agent node is a pure function:**

```python
# services/agent-engine/src/nodes/evaluate_response.py

from typing import Literal
from src.state.tutor_state import TutorState
from src.core.llm_client import LLMClient


async def evaluate_response(state: TutorState, llm_client: LLMClient) -> dict:
    """
    Evaluate student's response to a math question.
    Pure function — no side effects (DB writes happen in effect nodes).

    Returns: dict with evaluation_result, error_analysis, next_action
    """
    result = await llm_client.generate_structured(
        template_name="response_eval_v1.0.jinja2",
        template_vars={
            "question": state["current_question"],
            "student_response": state["student_response"],
            "grade_level": state["grade_level"],
            "standard_id": state["current_standard"],
        },
        response_model=EvaluationResult,
    )

    # Determine next action based on evaluation
    next_action: Literal["hint", "explain", "next_question", "end"]
    if result.is_correct:
        next_action = "next_question"
    elif len(state.get("hint_history", [])) >= 3:
        next_action = "explain"  # After 3 hints, give full explanation
    else:
        next_action = "hint"

    return {
        "evaluation_result": result,
        "error_analysis": result.error_analysis,
        "next_action": next_action,
    }
```

**Side effects in dedicated effect nodes:**

```python
# services/agent-engine/src/nodes/persist_mastery.py

async def persist_mastery_update(state: TutorState, mastery_service) -> dict:
    """
    Effect node — writes mastery update to database.
    This is the ONLY place DB writes happen in the tutor graph.
    """
    await mastery_service.update_mastery(
        student_id=state["student_id"],
        skill_id=state["current_standard"],
        correct=state["evaluation_result"].is_correct,
    )
    # Effect nodes still return state updates
    return {"mastery_persisted": True}
```

#### 4.4.4 Cost Controls

```python
# Cost control configuration
LLM_COST_CONFIG = {
    "max_session_cost_usd": 0.15,         # Alert threshold per student session
    "max_daily_cost_usd": 50.0,           # Hard daily cap
    "prefer_local_for": [                  # Tasks routed to local models when available
        "intent_classification",
        "answer_validation_simple",
        "difficulty_estimation",
    ],
    "require_frontier_for": [             # Tasks that MUST use frontier models
        "hint_generation",
        "explanation_generation",
        "learning_plan_creation",
        "question_generation",
    ],
}
```

---
## 5. Testing Strategy (Master Reference)

### 5.1 Test Pyramid

```
                    ┌─────────┐
                    │   E2E   │  10% — Critical user journeys (Playwright)
                    │ (slow)  │
                   ┌┴─────────┴┐
                   │Integration │  20% — API + DB + mocked LLMs
                   │ (medium)   │
                  ┌┴────────────┴┐
                  │  Unit Tests   │  70% — Pure functions, business logic
                  │  (fast)       │
                  └───────────────┘
```

| Layer | What to Test | Tools | Run When |
|-------|-------------|-------|----------|
| Unit (70%) | Pure functions, business logic, BKT calculations, IRT scoring, question selection algorithms, Pydantic validators, Zustand store actions, utility functions | Pytest (Python), Jest (TypeScript) | Every commit, pre-push hook |
| Integration (20%) | API endpoints with real DB (testcontainers), LangGraph agent flows with mocked LLMs, repository queries against real PostgreSQL, Redis cache integration | Pytest + testcontainers (Python), Jest + MSW (TypeScript) | Every PR in CI |
| E2E (10%) | Critical user journeys: diagnostic assessment flow, learning plan generation, practice session, parent dashboard, consent flow | Playwright | Nightly + before release |

**Test count targets by stage:**

| Stage | Unit | Integration | E2E | Total |
|-------|------|-------------|-----|-------|
| Stage 1 (Diagnostic) | ~120 | ~30 | ~5 | ~155 |
| Stage 2 (Learning Plan) | ~200 | ~50 | ~10 | ~260 |
| Stage 3 (Practice) | ~300 | ~80 | ~15 | ~395 |
| Stage 4 (Parent) | ~380 | ~100 | ~20 | ~500 |
| Stage 5 (Payments) | ~450 | ~120 | ~25 | ~595 |

---

### 5.2 Test Patterns

#### 5.2.1 Python Unit Test Pattern (Pytest)

**Rules:**
- Test file mirrors source file: `src/service/assessment_service.py` → `tests/unit/test_assessment_service.py`
- Fixtures in `conftest.py` at appropriate scope level (function, module, session)
- Use `pytest-asyncio` for async tests with `mode = "auto"` in `pyproject.toml`
- **Never** use `unittest.TestCase` — pure pytest functions only
- Descriptive test names that read as specifications: `test_submit_answer_updates_mastery_when_correct`

**BKT unit test example:**

```python
# services/bkt-engine/tests/unit/test_tracker.py

import pytest
import numpy as np
from src.engine.tracker import MasteryTracker
from src.models.skill import SkillParameters
from src.models.mastery import MasteryState


@pytest.fixture
def skill_params() -> SkillParameters:
    """Pre-calibrated parameters for 3.OA.A.1 (Multiply within 100)."""
    return SkillParameters(
        skill_id="3.OA.A.1",
        prior=0.1,
        learn=0.2,
        guess=0.15,
        slip=0.10,
        mastery_threshold=0.95,
    )


@pytest.fixture
def tracker(skill_params: SkillParameters) -> MasteryTracker:
    return MasteryTracker(skills=[skill_params])


class TestMasteryTracker:
    """Tests for BKT mastery estimation."""

    def test_initial_mastery_equals_prior(
        self, tracker: MasteryTracker, skill_params: SkillParameters
    ) -> None:
        """A new student's mastery probability should equal the prior."""
        state = tracker.get_mastery("student-1", "3.OA.A.1")
        assert state.probability == pytest.approx(skill_params.prior, abs=0.01)

    def test_correct_answer_increases_mastery(self, tracker: MasteryTracker) -> None:
        """A correct answer should increase mastery probability."""
        initial = tracker.get_mastery("student-1", "3.OA.A.1")
        tracker.update("student-1", "3.OA.A.1", correct=True)
        updated = tracker.get_mastery("student-1", "3.OA.A.1")
        assert updated.probability > initial.probability

    def test_incorrect_answer_decreases_mastery(self, tracker: MasteryTracker) -> None:
        """An incorrect answer should decrease (or not increase) mastery probability."""
        # First get some mastery built up
        for _ in range(3):
            tracker.update("student-1", "3.OA.A.1", correct=True)
        before_wrong = tracker.get_mastery("student-1", "3.OA.A.1")
        tracker.update("student-1", "3.OA.A.1", correct=False)
        after_wrong = tracker.get_mastery("student-1", "3.OA.A.1")
        assert after_wrong.probability <= before_wrong.probability

    def test_mastery_reached_after_consecutive_correct(
        self, tracker: MasteryTracker
    ) -> None:
        """Student should reach mastery after enough consecutive correct answers."""
        for _ in range(15):
            tracker.update("student-1", "3.OA.A.1", correct=True)
        state = tracker.get_mastery("student-1", "3.OA.A.1")
        assert state.is_mastered is True
        assert state.probability >= 0.95

    def test_different_students_have_independent_states(
        self, tracker: MasteryTracker
    ) -> None:
        """Two students' mastery states should be completely independent."""
        tracker.update("student-1", "3.OA.A.1", correct=True)
        tracker.update("student-1", "3.OA.A.1", correct=True)
        s1 = tracker.get_mastery("student-1", "3.OA.A.1")
        s2 = tracker.get_mastery("student-2", "3.OA.A.1")
        assert s1.probability > s2.probability

    def test_guess_parameter_bounds(self, tracker: MasteryTracker) -> None:
        """Mastery should never be negative or exceed 1.0."""
        # Submit many incorrect answers
        for _ in range(20):
            tracker.update("student-1", "3.OA.A.1", correct=False)
        state = tracker.get_mastery("student-1", "3.OA.A.1")
        assert 0.0 <= state.probability <= 1.0
```

**Service layer unit test example:**

```python
# apps/api/tests/unit/test_assessment_service.py

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from src.service.assessment_service import AssessmentService
from src.models.assessment import CreateAssessmentRequest, AssessmentResponse
from src.core.exceptions import NotFoundError, ConsentRequiredError


@pytest.fixture
def mock_repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mock_llm_client() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mock_consent_service() -> AsyncMock:
    service = AsyncMock()
    service.has_valid_consent.return_value = True
    return service


@pytest.fixture
def service(mock_repo, mock_llm_client, mock_consent_service) -> AssessmentService:
    return AssessmentService(
        repo=mock_repo,
        llm_client=mock_llm_client,
        consent_service=mock_consent_service,
    )


class TestCreateAssessment:
    async def test_creates_assessment_for_consented_student(
        self, service: AssessmentService, mock_repo: AsyncMock
    ) -> None:
        """Should create assessment when student has valid parental consent."""
        student_id = uuid4()
        request = CreateAssessmentRequest(grade_level=3, domains=["OA", "NBT"])
        mock_repo.create.return_value = MagicMock(id=uuid4(), status="in_progress")

        result = await service.create_assessment(student_id, request)

        mock_repo.create.assert_called_once()
        assert result is not None

    async def test_raises_consent_required_without_consent(
        self, service: AssessmentService, mock_consent_service: AsyncMock
    ) -> None:
        """Should raise ConsentRequiredError when parental consent is missing."""
        mock_consent_service.has_valid_consent.return_value = False
        student_id = uuid4()
        request = CreateAssessmentRequest(grade_level=3, domains=["OA"])

        with pytest.raises(ConsentRequiredError):
            await service.create_assessment(student_id, request)

    async def test_validates_grade_level_against_domains(
        self, service: AssessmentService
    ) -> None:
        """Grade K-2 should not have RP (Ratios & Proportions) domain."""
        student_id = uuid4()
        request = CreateAssessmentRequest(grade_level=1, domains=["RP"])

        with pytest.raises(ValueError, match="RP is not available for grade 1"):
            await service.create_assessment(student_id, request)
```

**Repository integration test example:**

```python
# apps/api/tests/integration/test_assessment_repo.py

import pytest
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession

from src.repository.assessment_repo import AssessmentRepository
from src.db.tables.assessment import AssessmentTable
from tests.fixtures.factories import StudentFactory, AssessmentFactory


@pytest.fixture
async def repo(db_session: AsyncSession) -> AssessmentRepository:
    return AssessmentRepository(db_session)


class TestAssessmentRepository:
    async def test_create_and_retrieve_assessment(
        self, repo: AssessmentRepository, db_session: AsyncSession
    ) -> None:
        """Should persist and retrieve an assessment with all fields."""
        student = await StudentFactory.create(session=db_session)
        assessment = await repo.create(
            student_id=student.id,
            grade_level=3,
            domains=["OA", "NBT"],
        )

        retrieved = await repo.get_by_id(assessment.id)
        assert retrieved is not None
        assert retrieved.student_id == student.id
        assert retrieved.grade_level == 3

    async def test_soft_delete_excludes_from_queries(
        self, repo: AssessmentRepository, db_session: AsyncSession
    ) -> None:
        """Soft-deleted assessments should not appear in standard queries."""
        student = await StudentFactory.create(session=db_session)
        assessment = await repo.create(
            student_id=student.id, grade_level=3, domains=["OA"]
        )
        await repo.soft_delete(assessment.id)

        result = await repo.get_by_id(assessment.id)
        assert result is None  # Soft-deleted, so not found

    async def test_keyset_pagination_returns_correct_pages(
        self, repo: AssessmentRepository, db_session: AsyncSession
    ) -> None:
        """Keyset pagination should return consistent pages."""
        student = await StudentFactory.create(session=db_session)
        # Create 5 assessments
        for _ in range(5):
            await repo.create(
                student_id=student.id, grade_level=3, domains=["OA"]
            )

        # First page of 2
        items, cursor, has_more = await repo.list_by_student(
            student.id, cursor=None, limit=2
        )
        assert len(items) == 2
        assert has_more is True
        assert cursor is not None

        # Second page of 2
        items2, cursor2, has_more2 = await repo.list_by_student(
            student.id, cursor=cursor, limit=2
        )
        assert len(items2) == 2
        assert has_more2 is True

        # Third page (last item)
        items3, cursor3, has_more3 = await repo.list_by_student(
            student.id, cursor=cursor2, limit=2
        )
        assert len(items3) == 1
        assert has_more3 is False
```

#### 5.2.2 React Component Test Pattern (Jest + RTL)

```typescript
// apps/web/tests/unit/components/QuestionCard.test.tsx

import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { axe, toHaveNoViolations } from "jest-axe";
import QuestionCard from "@/components/assessment/QuestionCard";
import type { Question } from "@mathpath/types";

expect.extend(toHaveNoViolations);

const mockQuestion: Question = {
  id: "q-1",
  stem: "What is 3 \\times 4?",
  domain: "OA",
  standardId: "3.OA.A.1",
  choices: [
    { id: "a", text: "7" },
    { id: "b", text: "12" },
    { id: "c", text: "34" },
    { id: "d", text: "1" },
  ],
  correctAnswer: "b",
};

describe("QuestionCard", () => {
  const defaultProps = {
    question: mockQuestion,
    questionNumber: 1,
    totalQuestions: 10,
    onAnswerSelect: jest.fn(),
    selectedAnswer: null,
    isSubmitting: false,
  };

  it("renders the question stem with math notation", () => {
    render(<QuestionCard {...defaultProps} />);
    // KaTeX renders math — check for the rendered output
    expect(screen.getByText(/3/)).toBeInTheDocument();
    expect(screen.getByText(/4/)).toBeInTheDocument();
  });

  it("renders all answer choices", () => {
    render(<QuestionCard {...defaultProps} />);
    const radioGroup = screen.getByRole("radiogroup");
    const options = within(radioGroup).getAllByRole("radio");
    expect(options).toHaveLength(4);
  });

  it("calls onAnswerSelect when a choice is clicked", async () => {
    const user = userEvent.setup();
    const onSelect = jest.fn();
    render(<QuestionCard {...defaultProps} onAnswerSelect={onSelect} />);

    const option = screen.getByRole("radio", { name: /Answer option: 12/ });
    await user.click(option);
    expect(onSelect).toHaveBeenCalledWith("b");
  });

  it("shows selected state for the chosen answer", () => {
    render(<QuestionCard {...defaultProps} selectedAnswer="b" />);
    const selected = screen.getByRole("radio", { name: /Answer option: 12/ });
    expect(selected).toHaveAttribute("aria-checked", "true");
  });

  it("disables all choices when submitting", () => {
    render(<QuestionCard {...defaultProps} isSubmitting={true} />);
    const options = screen.getAllByRole("radio");
    options.forEach((option) => {
      expect(option).toBeDisabled();
    });
  });

  it("displays question progress", () => {
    render(<QuestionCard {...defaultProps} questionNumber={3} totalQuestions={10} />);
    expect(screen.getByText("Question 3 of 10")).toBeInTheDocument();
  });

  it("has no accessibility violations", async () => {
    const { container } = render(<QuestionCard {...defaultProps} />);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it("supports keyboard navigation between choices", async () => {
    const user = userEvent.setup();
    render(<QuestionCard {...defaultProps} />);

    // Tab to first choice
    await user.tab();
    const firstOption = screen.getAllByRole("radio")[0];
    expect(firstOption).toHaveFocus();
  });
});
```

#### 5.2.3 LLM/Agent Test Patterns

**Unit test (mock LLMClient entirely):**

```python
# services/agent-engine/tests/unit/test_evaluate_response.py

import pytest
from unittest.mock import AsyncMock
from src.nodes.evaluate_response import evaluate_response
from src.state.tutor_state import TutorState
from tests.fixtures.mock_states import make_tutor_state


@pytest.fixture
def mock_llm() -> AsyncMock:
    client = AsyncMock()
    client.generate_structured.return_value = EvaluationResult(
        is_correct=False,
        error_analysis="Student multiplied instead of adding",
        confidence=0.92,
    )
    return client


async def test_incorrect_answer_routes_to_hint(mock_llm: AsyncMock) -> None:
    """When student answers incorrectly, next_action should be 'hint'."""
    state = make_tutor_state(
        student_response="15",  # Wrong answer
        hint_history=[],        # No hints given yet
    )
    result = await evaluate_response(state, mock_llm)
    assert result["next_action"] == "hint"
    assert result["error_analysis"] == "Student multiplied instead of adding"


async def test_incorrect_after_three_hints_routes_to_explain(mock_llm: AsyncMock) -> None:
    """After 3 failed hints, should route to full explanation."""
    state = make_tutor_state(
        student_response="15",
        hint_history=["hint1", "hint2", "hint3"],  # Already gave 3 hints
    )
    result = await evaluate_response(state, mock_llm)
    assert result["next_action"] == "explain"


async def test_correct_answer_routes_to_next_question(mock_llm: AsyncMock) -> None:
    """Correct answer should advance to next question."""
    mock_llm.generate_structured.return_value = EvaluationResult(
        is_correct=True,
        error_analysis="",
        confidence=0.98,
    )
    state = make_tutor_state(student_response="12")
    result = await evaluate_response(state, mock_llm)
    assert result["next_action"] == "next_question"
```

**Contract tests (validate real model outputs — weekly in CI):**

```python
# services/agent-engine/tests/contract/test_llm_output_schemas.py

import pytest
from src.core.llm_client import LLMClient
from src.models.evaluation import EvaluationResult
from src.models.hint import HintOutput


@pytest.mark.contract  # Only runs in weekly CI job, not on every PR
@pytest.mark.asyncio
class TestLLMOutputContracts:
    """Validate that real LLM outputs conform to our Pydantic schemas.

    These tests call real LLM APIs with deterministic inputs and verify
    the outputs parse correctly. Run weekly to catch model behavior drift.
    """

    async def test_evaluation_output_matches_schema(
        self, real_llm_client: LLMClient
    ) -> None:
        result = await real_llm_client.generate_structured(
            template_name="response_eval_v1.0.jinja2",
            template_vars={
                "question": "What is 3 + 4?",
                "student_response": "12",
                "grade_level": 2,
                "standard_id": "2.OA.B.2",
            },
            response_model=EvaluationResult,
        )
        assert isinstance(result, EvaluationResult)
        assert isinstance(result.is_correct, bool)
        assert isinstance(result.error_analysis, str)

    async def test_hint_output_matches_schema(
        self, real_llm_client: LLMClient
    ) -> None:
        result = await real_llm_client.generate(
            template_name="hint_generation_v1.0.jinja2",
            template_vars={
                "question_stem": "What is 3 + 4?",
                "student_response": "12",
                "error_analysis": "Student multiplied instead of adding",
                "grade_level": 2,
                "domain_name": "Operations & Algebraic Thinking",
                "standard_id": "2.OA.B.2",
                "hint_history": [],
            },
        )
        assert isinstance(result, str)
        assert len(result) > 10  # Hint should be substantive
        assert len(result) < 2000  # But not excessively long
```

**Prompt regression tests (golden input/output pairs):**

```python
# services/agent-engine/tests/regression/test_prompt_stability.py

import json
import pytest
from pathlib import Path
from difflib import SequenceMatcher

GOLDEN_DIR = Path(__file__).parent / "golden_outputs"


@pytest.mark.contract
async def test_hint_prompt_stability(real_llm_client: LLMClient) -> None:
    """Verify hint outputs haven't drifted significantly from golden examples."""
    with open(GOLDEN_DIR / "hint_golden_001.json") as f:
        golden = json.load(f)

    result = await real_llm_client.generate(
        template_name=golden["template"],
        template_vars=golden["input"],
    )

    # Check structural similarity (not exact match — LLMs are non-deterministic)
    similarity = SequenceMatcher(None, golden["expected_output"], result).ratio()
    assert similarity > 0.4, (
        f"Hint output drifted significantly (similarity: {similarity:.2f}). "
        f"Expected structure similar to golden output. Got: {result[:200]}"
    )

    # Check key properties are present
    assert any(keyword in result.lower() for keyword in golden["required_keywords"])
```

---

### 5.3 Test Data Management

#### 5.3.1 Test Database

Each test suite gets an isolated PostgreSQL instance:

```python
# apps/api/tests/conftest.py

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from testcontainers.postgres import PostgresContainer

from src.db.base import Base


@pytest.fixture(scope="session")
def postgres_container():
    """Spin up a real PostgreSQL container for integration tests."""
    with PostgresContainer("postgres:17-alpine") as pg:
        pg.with_env("POSTGRES_DB", "mathpath_test")
        yield pg


@pytest_asyncio.fixture(scope="session")
async def engine(postgres_container):
    """Create async engine connected to test container."""
    url = postgres_container.get_connection_url().replace("psycopg2", "asyncpg")
    engine = create_async_engine(url, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(engine) -> AsyncSession:
    """Provide a transactional session that rolls back after each test."""
    async_session = async_sessionmaker(engine, class_=AsyncSession)
    async with async_session() as session:
        async with session.begin():
            yield session
            await session.rollback()
```

#### 5.3.2 Test Factories (Factory Boy)

```python
# apps/api/tests/fixtures/factories.py

import factory
from uuid import uuid4
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.tables.student import StudentTable
from src.db.tables.assessment import AssessmentTable


class AsyncFactory(factory.Factory):
    """Base factory with async create support."""

    class Meta:
        abstract = True

    @classmethod
    async def create(cls, session: AsyncSession, **kwargs):
        obj = cls.build(**kwargs)
        session.add(obj)
        await session.flush()
        return obj


class StudentFactory(AsyncFactory):
    class Meta:
        model = StudentTable

    id = factory.LazyFunction(uuid4)
    pii_display_name = factory.Faker("first_name")
    grade_level = factory.Faker("random_int", min=0, max=8)
    auth0_user_id = factory.LazyFunction(lambda: f"auth0|{uuid4().hex[:24]}")
    created_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))
    updated_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))


class AssessmentFactory(AsyncFactory):
    class Meta:
        model = AssessmentTable

    id = factory.LazyFunction(uuid4)
    status = "in_progress"
    grade_level = 3
    total_questions = 15
    current_question_index = 0
```

#### 5.3.3 Seed Data

Deterministic, reproducible fixture sets:

```python
# infrastructure/scripts/seed_data.py

"""
Seed data for development and testing.
Covers all 38 Oregon K-8 math standards with sample questions.
Run via: make seed
"""

SEED_STANDARDS = [
    {"id": "K.CC.A.1", "name": "Count to 100 by ones and tens", "grade": 0, "domain": "CC"},
    {"id": "K.CC.A.2", "name": "Count forward from a given number", "grade": 0, "domain": "CC"},
    {"id": "1.OA.A.1", "name": "Add and subtract within 20", "grade": 1, "domain": "OA"},
    {"id": "1.OA.A.2", "name": "Solve word problems within 20", "grade": 1, "domain": "OA"},
    # ... all 38+ standards
    {"id": "8.F.A.1", "name": "Understand functions as rules", "grade": 8, "domain": "F"},
]

SEED_QUESTIONS_PER_STANDARD = 5  # Minimum for testing
# Total seed questions: 38 * 5 = 190 questions minimum

SEED_BKT_PARAMS = {
    "K.CC.A.1": {"prior": 0.15, "learn": 0.25, "guess": 0.20, "slip": 0.05},
    "3.OA.A.1": {"prior": 0.10, "learn": 0.20, "guess": 0.15, "slip": 0.10},
    # ... calibrated parameters for each standard
}
```

---
## 6. Operational Standards

### 6.1 Environment Configuration

| Environment | Purpose | Data | LLMs | Feature Flags | URL |
|-------------|---------|------|------|---------------|-----|
| **Local** | Developer workstation | Docker Compose Postgres + Redis; seeded test data | Mock LLM client OR local Ollama models | All flags ON (dev override) | `localhost:3000` / `localhost:8000` |
| **CI** | GitHub Actions | Testcontainers (ephemeral Postgres per run) | Mock LLM client only (no real API calls) | All flags ON | N/A (headless) |
| **Staging** | Pre-production validation | Copy of production schema with synthetic data; never real student data | Real LLM APIs (Claude, GPT-4o) with lower rate limits | Flags mirror production + unreleased features enabled | `staging.mathpath.org` |
| **Production** | Live users | Real student data (encrypted, COPPA-compliant) | Real LLM APIs with production rate limits and cost alerts | Controlled rollout per flag | `app.mathpath.org` |

**12-Factor Config — all config via environment variables:**

```bash
# .env.example — checked into git with placeholder values
# Copy to .env.local (gitignored) and fill in real values

# === Application ===
APP_ENV=local                          # local | ci | staging | production
APP_DEBUG=true                         # true | false
APP_LOG_LEVEL=DEBUG                    # DEBUG | INFO | WARNING | ERROR
APP_SECRET_KEY=CHANGE_ME               # Random 64-char hex string

# === Database ===
DATABASE_URL=postgresql+asyncpg://mathpath:mathpath@localhost:5432/mathpath
DATABASE_POOL_SIZE=5
DATABASE_MAX_OVERFLOW=10

# === Redis ===
REDIS_URL=redis://localhost:6379/0

# === Auth0 ===
AUTH0_DOMAIN=mathpath-dev.us.auth0.com
AUTH0_CLIENT_ID=CHANGE_ME
AUTH0_CLIENT_SECRET=CHANGE_ME
AUTH0_AUDIENCE=https://api.mathpath.org
AUTH0_CALLBACK_URL=http://localhost:3000/api/auth/callback

# === LLM APIs ===
ANTHROPIC_API_KEY=CHANGE_ME
OPENAI_API_KEY=CHANGE_ME
LLM_MAX_SESSION_COST_USD=0.15
LLM_MAX_DAILY_COST_USD=50.0

# === Feature Flags (Unleash) ===
UNLEASH_URL=http://localhost:4242/api
UNLEASH_API_KEY=CHANGE_ME
UNLEASH_APP_NAME=mathpath
UNLEASH_ENVIRONMENT=development

# === Monitoring ===
SENTRY_DSN=CHANGE_ME
SENTRY_ENVIRONMENT=local
DATADOG_API_KEY=CHANGE_ME
POSTHOG_API_KEY=CHANGE_ME
POSTHOG_HOST=https://app.posthog.com

# === AWS (for LocalStack in local dev) ===
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test
AWS_REGION=us-west-2
AWS_ENDPOINT_URL=http://localhost:4566     # LocalStack

# === Vercel (frontend only) ===
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_AUTH0_DOMAIN=mathpath-dev.us.auth0.com
NEXT_PUBLIC_AUTH0_CLIENT_ID=CHANGE_ME
NEXT_PUBLIC_POSTHOG_KEY=CHANGE_ME
```

**Rule: No `.env` files are ever committed. Only `.env.example` (with placeholders) is tracked in git.**

---

### 6.2 Secret Management

| Secret Type | Local Dev | CI (GitHub Actions) | Staging/Production |
|-------------|-----------|--------------------|--------------------|
| DB passwords | `.env.local` | GitHub Actions Secrets | AWS Secrets Manager |
| API keys (Anthropic, OpenAI) | `.env.local` | GitHub Actions Secrets | AWS Secrets Manager |
| Auth0 secrets | `.env.local` | GitHub Actions Secrets | AWS Secrets Manager |
| Stripe keys (Stage 5) | `.env.local` | GitHub Actions Secrets | AWS Secrets Manager |
| Sentry DSN | `.env.local` | GitHub Actions Secrets | AWS Secrets Manager |
| AWS credentials | Local AWS profile | GitHub OIDC (no static keys) | ECS Task Role (no static keys) |

**Secret rotation:**
- Database passwords: Rotate every 90 days via `infrastructure/scripts/rotate-secrets.sh`
- API keys: Rotate if compromised; Anthropic and OpenAI support key regeneration
- Auth0 client secret: Rotate every 180 days

**Pre-commit secret detection:**
```yaml
# .pre-commit-config.yaml (secret detection portion)
repos:
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.5.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.18.0
    hooks:
      - id: gitleaks
```

**Team secret sync (solo dev / small team):**
```bash
# For a solo developer, 1Password CLI provides a simple sync mechanism:
# Install: brew install 1password-cli

# Store secrets in 1Password vault "MathPath Dev"
# Populate .env.local from 1Password:
op inject -i .env.example -o .env.local

# This replaces {{ op://MathPath Dev/Database/password }} style references
# with actual values from your 1Password vault
```

---

### 6.3 Local Development Setup

#### Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Docker Desktop | Latest | `brew install --cask docker` |
| Python | 3.12.x | `brew install pyenv && pyenv install 3.12` |
| Node.js | 22.x LTS | `brew install nvm && nvm install 22` |
| pnpm | 9.x | `corepack enable && corepack prepare pnpm@latest --activate` |
| AWS CLI | v2 | `brew install awscli` |
| Terraform | 1.9+ | `brew install terraform` |
| Ollama | Latest | `brew install ollama` (optional, for local models) |
| pre-commit | Latest | `brew install pre-commit` |

#### One-Command Setup

```bash
git clone git@github.com:your-org/mathpath.git
cd mathpath
make setup
```

**What `make setup` does:**

1. Checks prerequisites (Docker, Python, Node, pnpm)
2. Copies `.env.example` to `.env.local` (if not exists)
3. Installs pnpm dependencies: `pnpm install`
4. Creates Python virtual environments for each Python service
5. Installs Python dependencies: `pip install -e ".[dev]"` in each service
6. Starts Docker Compose (Postgres, Redis, LocalStack)
7. Waits for services to be healthy
8. Runs database migrations: `alembic upgrade head`
9. Seeds the database with test data
10. Installs pre-commit hooks: `pre-commit install`
11. Prints success message with URLs

#### Docker Compose for Local Services

```yaml
# infrastructure/docker/docker-compose.yml
version: "3.9"

services:
  postgres:
    image: pgvector/pgvector:pg17
    ports:
      - "5432:5432"
    environment:
      POSTGRES_DB: mathpath
      POSTGRES_USER: mathpath
      POSTGRES_PASSWORD: mathpath
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./init-db.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U mathpath"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5

  localstack:
    image: localstack/localstack:3
    ports:
      - "4566:4566"
    environment:
      SERVICES: s3,secretsmanager
      DEFAULT_REGION: us-west-2
    volumes:
      - localstackdata:/var/lib/localstack

  unleash:
    image: unleashorg/unleash-server:latest
    ports:
      - "4242:4242"
    environment:
      DATABASE_URL: postgres://mathpath:mathpath@postgres:5432/unleash
      DATABASE_SSL: "false"
    depends_on:
      postgres:
        condition: service_healthy

volumes:
  pgdata:
  localstackdata:
```

#### Running the Full Stack Locally

```bash
# Terminal 1: Start infrastructure services
make docker-up

# Terminal 2: Start the FastAPI backend (with hot reload)
make dev-api

# Terminal 3: Start the Next.js frontend (with hot reload)
make dev-web

# Terminal 4 (optional): Start Ollama for local LLM testing
ollama serve
```

**URLs after startup:**
- Frontend: http://localhost:3000
- API: http://localhost:8000
- API docs (Swagger): http://localhost:8000/docs
- API docs (ReDoc): http://localhost:8000/redoc
- Unleash dashboard: http://localhost:4242
- PostgreSQL: `localhost:5432` (user: mathpath, password: mathpath)
- Redis: `localhost:6379`

#### Common Troubleshooting

| Problem | Solution |
|---------|----------|
| Port 5432 in use | `lsof -i :5432` and kill the process, or change port in docker-compose |
| Python version mismatch | `pyenv local 3.12` in the repo root |
| Node version mismatch | `nvm use 22` (`.nvmrc` in repo root) |
| Docker Compose services won't start | `make docker-reset` (removes volumes and restarts) |
| Alembic migration fails | Check if database is running: `make docker-up`; check migration order: `alembic history` |
| pnpm install fails | Delete `node_modules` and `pnpm-lock.yaml`, then `pnpm install` |
| Auth0 callback error | Verify `AUTH0_CALLBACK_URL` in `.env.local` matches Auth0 dashboard config |
| LLM calls timeout | Check API keys in `.env.local`; use `make test-llm-connection` to verify |

---

### 6.4 Makefile Reference

```makefile
# Makefile — MathPath Oregon Developer Commands
# Run `make help` to see all available targets

.PHONY: help setup install dev dev-api dev-web test test-unit test-integration \
        test-e2e lint format typecheck migrate seed docker-up docker-down \
        docker-reset build deploy-staging logs shell-api shell-db clean

# Default: show help
help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ============================================================
# SETUP
# ============================================================

setup: ## One-command project setup (first time)
	@echo "🔧 Setting up MathPath Oregon..."
	@./infrastructure/scripts/setup.sh

install: ## Install all dependencies (pnpm + Python)
	pnpm install
	@for svc in apps/api services/agent-engine services/question-generator services/bkt-engine; do \
		echo "Installing $$svc..."; \
		cd $$svc && pip install -e ".[dev]" && cd -; \
	done

# ============================================================
# DEVELOPMENT
# ============================================================

dev: docker-up dev-api dev-web ## Start full development stack

dev-api: ## Start FastAPI backend with hot reload
	cd apps/api && uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

dev-web: ## Start Next.js frontend with hot reload
	cd apps/web && pnpm dev

dev-agent: ## Start agent engine in dev mode
	cd services/agent-engine && uvicorn src.main:app --reload --port 8001

# ============================================================
# TESTING
# ============================================================

test: test-unit test-integration ## Run all tests (unit + integration)

test-unit: ## Run unit tests only (fast)
	cd apps/api && pytest tests/unit -v --tb=short
	cd services/bkt-engine && pytest tests/unit -v --tb=short
	cd services/agent-engine && pytest tests/unit -v --tb=short
	pnpm --filter @mathpath/web test -- --watchAll=false

test-integration: ## Run integration tests (requires Docker services)
	cd apps/api && pytest tests/integration -v --tb=short
	pnpm --filter @mathpath/web test:integration

test-e2e: ## Run E2E tests with Playwright
	pnpm --filter @mathpath/web exec playwright test

test-e2e-ui: ## Run E2E tests with Playwright UI mode
	pnpm --filter @mathpath/web exec playwright test --ui

test-coverage: ## Run tests with coverage report
	cd apps/api && pytest --cov=src --cov-report=html --cov-report=term-missing
	pnpm --filter @mathpath/web test -- --coverage --watchAll=false

test-llm-connection: ## Verify LLM API keys and connectivity
	cd apps/api && python -c "from src.clients.llm_client import LLMClient; import asyncio; asyncio.run(LLMClient.health_check())"

# ============================================================
# CODE QUALITY
# ============================================================

lint: ## Lint all code (Python + TypeScript)
	cd apps/api && ruff check src tests
	cd services/bkt-engine && ruff check src tests
	cd services/agent-engine && ruff check src tests
	pnpm turbo lint

format: ## Auto-format all code
	cd apps/api && ruff format src tests
	cd services/bkt-engine && ruff format src tests
	cd services/agent-engine && ruff format src tests
	pnpm turbo format

typecheck: ## Type-check all code (mypy + tsc)
	cd apps/api && mypy src
	cd services/bkt-engine && mypy src
	cd services/agent-engine && mypy src
	pnpm turbo typecheck

security-scan: ## Run security scanners
	cd apps/api && bandit -r src -c pyproject.toml
	cd apps/api && pip-audit
	pnpm audit --audit-level=high

# ============================================================
# DATABASE
# ============================================================

migrate: ## Run Alembic migrations (upgrade to head)
	cd apps/api && alembic upgrade head

migrate-new: ## Create a new migration (usage: make migrate-new MSG="add_foo_table")
	cd apps/api && alembic revision --autogenerate -m "$(MSG)"

migrate-rollback: ## Rollback last migration
	cd apps/api && alembic downgrade -1

migrate-history: ## Show migration history
	cd apps/api && alembic history --verbose

seed: ## Seed database with test data
	cd apps/api && python -m scripts.seed_data

shell-db: ## Open psql shell to local database
	docker exec -it $$(docker ps -qf "name=postgres") psql -U mathpath -d mathpath

# ============================================================
# DOCKER
# ============================================================

docker-up: ## Start Docker infrastructure services
	docker compose -f infrastructure/docker/docker-compose.yml up -d
	@echo "Waiting for services to be healthy..."
	@sleep 5
	@docker compose -f infrastructure/docker/docker-compose.yml ps

docker-down: ## Stop Docker infrastructure services
	docker compose -f infrastructure/docker/docker-compose.yml down

docker-reset: ## Reset Docker (remove volumes, fresh start)
	docker compose -f infrastructure/docker/docker-compose.yml down -v
	docker compose -f infrastructure/docker/docker-compose.yml up -d
	@sleep 5
	$(MAKE) migrate
	$(MAKE) seed

# ============================================================
# BUILD & DEPLOY
# ============================================================

build: ## Build all services for production
	pnpm turbo build
	docker build -f infrastructure/docker/api.Dockerfile -t mathpath-api:latest apps/api/
	docker build -f infrastructure/docker/agent-engine.Dockerfile -t mathpath-agent:latest services/agent-engine/

deploy-staging: ## Deploy to staging (requires AWS credentials)
	@echo "Deploying to staging..."
	@./infrastructure/scripts/deploy.sh staging

# ============================================================
# UTILITIES
# ============================================================

shell-api: ## Open Python shell with app context
	cd apps/api && python -c "from src.main import create_app; app = create_app(); print('App ready')"

logs: ## Tail logs from all Docker services
	docker compose -f infrastructure/docker/docker-compose.yml logs -f

clean: ## Remove all generated files and caches
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "node_modules" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".next" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "dist" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true

pre-commit-run: ## Run all pre-commit hooks on all files
	pre-commit run --all-files
```

---
## 7. Security Baseline

### 7.1 OWASP Top 10 Mitigations (Specific to This Stack)

#### A01:2021 — Broken Access Control

**Risk:** Students accessing other students' data; parents viewing non-linked children; unauthenticated access to assessment endpoints.

**Mitigations:**
- Every API endpoint uses Auth0 JWT validation via `Depends(get_current_student)` or `Depends(get_current_parent)`
- Row-level filtering: all repository queries include `student_id = current_user.student_id` or `parent_id = current_user.parent_id` — never trust client-provided IDs for authorization
- Parent–child linkage enforced in the database: a parent can only access students where `students.parent_id = parent.id`
- Role-based access: `student`, `parent`, `admin` roles enforced via Auth0 RBAC
- No direct object references in URLs without server-side ownership validation
- Audit log for all data access (who accessed what, when)

```python
# Pattern: Every student-facing query is scoped
async def get_student_assessments(
    self, student_id: UUID, requesting_user: AuthUser
) -> list[Assessment]:
    """Always filter by the authenticated user's identity."""
    if requesting_user.role == "student":
        assert requesting_user.student_id == student_id  # Or raise ForbiddenError
    elif requesting_user.role == "parent":
        # Verify parent owns this student
        await self._verify_parent_student_link(requesting_user.parent_id, student_id)
    # ... query with student_id filter
```

#### A02:2021 — Cryptographic Failures

**Risk:** Student PII exposed in transit or at rest; LLM API keys leaked.

**Mitigations:**
- TLS everywhere: all external connections (API, database, Redis, LLM APIs) use TLS 1.2+
- RDS encryption at rest enabled (AWS KMS)
- PII fields identified via `pii_` prefix convention and documented in schema comments
- No PII in log statements — enforced by structured logging review
- API keys and secrets stored in AWS Secrets Manager, never in code or environment files in production
- `detect-secrets` pre-commit hook prevents accidental secret commits

#### A03:2021 — Injection

**Risk:** SQL injection via assessment answers; template injection in LLM prompts; XSS via math notation rendering.

**Mitigations:**
- **SQL injection:** All database queries use SQLAlchemy ORM/Core (parameterized queries). Raw SQL is forbidden in application code. The only raw SQL lives in Alembic migrations. Import-linter enforces this.
- **LLM prompt injection:** Student inputs (answers, free-text responses) are sanitized before insertion into prompt templates. Prompt templates use Jinja2 with `|e` (escape) filter on all user inputs. Structured output validation via Pydantic rejects unexpected fields.
- **XSS:** KaTeX sanitizes math input by default (it does not evaluate JavaScript). React's JSX escapes all string values. `Content-Security-Policy` headers restrict script sources. User-generated text is never rendered with `dangerouslySetInnerHTML`.

```python
# LLM prompt injection defense: sanitize user input before templating
def sanitize_for_prompt(user_input: str) -> str:
    """Strip potential prompt injection patterns from student input."""
    # Remove instruction-like patterns
    dangerous_patterns = [
        r"ignore\s+(previous|above|all)\s+(instructions?|rules?|prompts?)",
        r"system\s*:",
        r"<\|.*?\|>",
        r"\[INST\]",
        r"```\s*(system|instruction)",
    ]
    sanitized = user_input
    for pattern in dangerous_patterns:
        sanitized = re.sub(pattern, "[filtered]", sanitized, flags=re.IGNORECASE)
    return sanitized[:1000]  # Hard length limit
```

#### A04:2021 — Insecure Design

**Mitigations:**
- Threat modeling performed for each stage before implementation
- COPPA compliance review for every feature that touches student data
- Data minimization principle: collect only what's needed for the educational function
- Defense in depth: Auth0 (identity) + API authorization (access control) + row-level DB filtering (data isolation)

#### A05:2021 — Security Misconfiguration

**Mitigations:**
- CORS configured to allow only the frontend domain (`app.mathpath.org`, `localhost:3000` in dev)
- Security headers set via middleware: `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Strict-Transport-Security`, `Content-Security-Policy`, `Referrer-Policy: strict-origin-when-cross-origin`
- Debug mode disabled in staging/production (`APP_DEBUG=false`)
- Default credentials never used — Docker Compose uses non-default passwords even locally
- Terraform enforces security group rules — no wide-open ports

```python
# apps/api/src/core/middleware.py
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

def configure_security_headers(app: FastAPI) -> None:
    @app.middleware("http")
    async def add_security_headers(request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "0"  # Disabled per OWASP (use CSP instead)
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
        return response
```

#### A06:2021 — Vulnerable and Outdated Components

**Mitigations:**
- `pip-audit` runs in CI on every PR (Python dependency vulnerability check)
- `pnpm audit` runs in CI (Node.js dependency vulnerability check)
- Dependabot configured for automated dependency update PRs
- Weekly `dependency-audit.yml` GitHub Action for comprehensive scan
- Docker base images pinned to specific versions and updated monthly

#### A07:2021 — Identification and Authentication Failures

**Mitigations:**
- Auth0 handles all authentication — password hashing, session management, brute-force protection, MFA
- JWT tokens validated on every request (signature, expiration, audience, issuer)
- No session state on the server — stateless JWT authentication
- Account lockout after 10 failed attempts (Auth0 configuration)
- No password reuse for parent accounts (Auth0 policy)

#### A08:2021 — Software and Data Integrity Failures

**Mitigations:**
- GitHub Actions uses pinned action versions (`uses: actions/checkout@v4.1.1`, not `@latest`)
- Docker images built in CI, signed, and pushed to ECR (image scanning enabled)
- `pip install` uses `--require-hashes` in production Dockerfiles
- Alembic migrations are append-only after deployment — never modified retroactively
- Pre-commit hooks prevent force-push to `main`

#### A09:2021 — Security Logging and Monitoring Failures

**Mitigations:**
- Structured logging via `structlog` — all logs include request ID, user ID (UUID only, not PII), timestamp
- Sentry captures all unhandled exceptions with full context (minus PII)
- Datadog APM traces all API requests end-to-end
- Auth0 logs all authentication events (login, failed login, consent granted, consent revoked)
- Audit log table records all data access and modifications for COPPA compliance
- Alerting configured for: >5% error rate, P95 latency >2s, LLM daily cost >80% of budget

#### A10:2021 — Server-Side Request Forgery (SSRF)

**Mitigations:**
- No user-supplied URLs are fetched by the backend
- LLM API calls go to hardcoded endpoints (api.anthropic.com, api.openai.com)
- LocalStack (S3 emulation) in dev uses a hardcoded endpoint URL, not user input
- If URL fetching is ever needed (e.g., importing content), use an allowlist of domains

---

### 7.2 COPPA Security Requirements

These are non-negotiable legal requirements. Violation can result in FTC fines of up to $53,088 per violation per day.

#### 7.2.1 Parental Consent Storage and Audit Trail

```python
# Consent audit trail — every consent event is immutable
class ConsentRecord(BaseTable):
    __tablename__ = "consent_records"

    parent_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("parents.id"))
    student_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("students.id"))
    consent_type: Mapped[str] = mapped_column(String(50))  # "initial", "update", "revoke"
    consent_scope: Mapped[str] = mapped_column(String(200)) # What was consented to
    verification_method: Mapped[str] = mapped_column(String(50))  # "email", "credit_card", "video_call"
    ip_address: Mapped[str] = mapped_column(String(45))  # IPv4 or IPv6
    user_agent: Mapped[str] = mapped_column(String(500))
    consented_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    # This table is APPEND-ONLY — no updates, no deletes
```

**Rules:**
- Consent records are **never deleted**, even when a student account is deleted
- Every consent action (grant, update, revoke) creates a new row
- Consent must be re-verified if the data use scope changes
- Parent can request a full export of their consent history

#### 7.2.2 Child Data Encryption Requirements

| Data Type | At Rest | In Transit | In Logs |
|-----------|---------|------------|---------|
| Student display name | RDS encryption (AES-256) | TLS 1.2+ | **NEVER logged** |
| Parent email | RDS encryption (AES-256) | TLS 1.2+ | **NEVER logged** |
| Student responses | RDS encryption (AES-256) | TLS 1.2+ | Logged as aggregate only (correct/incorrect) |
| Mastery probabilities | RDS encryption (AES-256) | TLS 1.2+ | Logged with student UUID only |
| Assessment scores | RDS encryption (AES-256) | TLS 1.2+ | Logged with student UUID only |
| Auth0 tokens | In-memory only | TLS 1.2+ | **NEVER logged** |

#### 7.2.3 Access Control for Student Records

```python
# Role-based data access matrix
ACCESS_CONTROL = {
    "student": {
        "own_profile": "read",
        "own_assessments": "read",
        "own_mastery": "read",
        "own_practice": "read_write",
        "other_students": "none",
    },
    "parent": {
        "linked_children_profiles": "read",
        "linked_children_assessments": "read",
        "linked_children_mastery": "read",
        "linked_children_practice": "read",
        "consent_management": "read_write",
        "data_export": "read",
        "data_deletion": "write",
        "other_families": "none",
    },
    "admin": {
        "all_students": "read",  # Aggregated/anonymized only
        "individual_student_pii": "none",  # Admins cannot see PII
        "system_metrics": "read",
        "feature_flags": "read_write",
    },
}
```

#### 7.2.4 Data Breach Notification

- Incident response plan documented in `docs/runbooks/incident-response.md`
- 72-hour notification requirement to affected parents (per updated COPPA rule and FTC guidance)
- Notification must include: what data was exposed, when, what mitigation steps taken
- Pre-drafted notification templates in `docs/runbooks/breach-notification-templates/`
- Annual breach simulation exercise

#### 7.2.5 Third-Party Data Sharing Restrictions

| Third-Party Service | Data Shared | COPPA Compliance |
|--------------------|-------------|------------------|
| Auth0 | Parent email, auth events | Auth0 COPPA plan; DPA signed; no secondary use |
| Anthropic (Claude) | Question/answer text (no PII) | No student identifiers sent in prompts |
| OpenAI (GPT-4o) | Question/answer text (no PII) | No student identifiers sent in prompts |
| Sentry | Error traces with UUIDs | No PII; UUIDs only; Sentry DPA signed |
| PostHog | Anonymous events (no PII) | COPPA-compliant config; no persistent identifiers |
| Datadog | Performance metrics (no PII) | No user-level data; aggregate metrics only |
| Stripe (Stage 5) | Parent payment info only | Children never interact with Stripe |

**LLM prompt PII stripping:**
```python
def prepare_llm_context(student_response: str, student_id: UUID) -> dict:
    """Prepare context for LLM call — NEVER include student PII."""
    return {
        # OK: anonymous identifiers
        "session_id": str(uuid4()),  # Ephemeral, not the real student ID
        "grade_level": 3,
        "response_text": student_response,
        "skill_id": "3.OA.A.1",
        # NEVER: student name, parent email, school name, location
    }
```

---

### 7.3 Pre-commit Security Hooks

```yaml
# .pre-commit-config.yaml
repos:
  # Secret detection
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.5.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']
        exclude: 'pnpm-lock.yaml|package-lock.json'

  # Git leak scanning
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.18.0
    hooks:
      - id: gitleaks

  # Python security linter
  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.9
    hooks:
      - id: bandit
        args: ['-c', 'pyproject.toml', '-r', 'apps/api/src', 'services/']
        additional_dependencies: ['bandit[toml]']

  # Python dependency vulnerability check
  - repo: https://github.com/pypa/pip-audit
    rev: v2.7.3
    hooks:
      - id: pip-audit
        args: ['--strict', '--desc']

  # Python linting and formatting
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.7.0
    hooks:
      - id: ruff
        args: ['--fix']
      - id: ruff-format

  # Python type checking
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.12.0
    hooks:
      - id: mypy
        additional_dependencies: ['pydantic>=2.0', 'sqlalchemy>=2.0']
        args: ['--strict']

  # TypeScript / JavaScript
  - repo: https://github.com/pre-commit/mirrors-eslint
    rev: v9.12.0
    hooks:
      - id: eslint
        files: '\.[jt]sx?$'
        types: [file]

  # General file checks
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-json
      - id: check-added-large-files
        args: ['--maxkb=1000']
      - id: no-commit-to-branch
        args: ['--branch', 'main']
```

---

## 8. Performance Baselines

### 8.1 Performance Budgets by Category

| Category | Metric | Target | Measurement Tool | Alert Threshold |
|----------|--------|--------|-----------------|-----------------|
| **API Response** | P50 latency | < 200ms | Datadog APM | > 300ms |
| **API Response** | P95 latency | < 500ms | Datadog APM | > 750ms |
| **API Response** | P99 latency | < 1,500ms | Datadog APM | > 2,000ms |
| **API Response** | Error rate | < 0.1% | Datadog/Sentry | > 0.5% |
| **LLM Call** | Hint generation P50 | < 2,000ms | Custom Datadog metric | > 3,000ms |
| **LLM Call** | Hint generation P95 | < 4,000ms | Custom Datadog metric | > 5,000ms |
| **LLM Call** | Question generation P50 | < 3,000ms | Custom Datadog metric | > 5,000ms |
| **LLM Call** | Response evaluation P50 | < 1,500ms | Custom Datadog metric | > 2,500ms |
| **LLM Call** | Fallback rate | < 5% | Custom metric | > 10% |
| **BKT** | Mastery update latency | < 50ms | Custom metric | > 100ms |
| **BKT** | Roster initialization | < 200ms | Custom metric | > 500ms |
| **Database** | Query P50 | < 20ms | Datadog APM (DB spans) | > 50ms |
| **Database** | Query P95 | < 100ms | Datadog APM (DB spans) | > 200ms |
| **Database** | Connection pool utilization | < 70% | Datadog | > 85% |
| **Frontend** | Largest Contentful Paint (LCP) | < 2,500ms | Core Web Vitals / Lighthouse | > 3,000ms |
| **Frontend** | First Input Delay (FID) | < 100ms | Core Web Vitals | > 200ms |
| **Frontend** | Cumulative Layout Shift (CLS) | < 0.1 | Core Web Vitals | > 0.15 |
| **Frontend** | Time to Interactive (TTI) | < 3,000ms | Lighthouse | > 4,000ms |
| **Frontend** | JS bundle size (initial) | < 200KB gzipped | `next build` analyzer | > 250KB |
| **Frontend** | KaTeX render time | < 50ms per expression | Custom metric | > 100ms |
| **Infrastructure** | ECS task startup time | < 30s | CloudWatch | > 60s |
| **Infrastructure** | Health check endpoint | < 50ms | Datadog synthetic | > 100ms |
| **Cost** | LLM cost per session | < $0.15 | Custom tracking | > $0.20 |
| **Cost** | LLM cost per day | < $50 | Custom tracking | > $40 (warning) |
| **Cost** | AWS monthly infrastructure | < $500 (staging) | AWS Cost Explorer | > $600 |

### 8.2 Performance Budgets by Stage

| Stage | Max Concurrent Users | API RPS Target | LLM Calls/min | DB Connections |
|-------|---------------------|----------------|---------------|----------------|
| Stage 1 (Diagnostic) | 10 | 50 | 20 | 10 |
| Stage 2 (Learning Plans) | 25 | 100 | 40 | 15 |
| Stage 3 (Practice) | 50 | 200 | 80 | 20 |
| Stage 4 (Parent Dashboard) | 75 | 250 | 80 | 25 |
| Stage 5 (Payments + Scale) | 200 | 500 | 150 | 40 |

### 8.3 Performance Testing Approach

**Load testing** (run before each stage release):
- Tool: `locust` (Python-based, easy to script)
- Scenarios: Simulate the stage's max concurrent users performing typical workflows
- Duration: 15-minute sustained load test
- Assertions: All P95 latencies within budget, zero 5xx errors, no connection pool exhaustion

**Frontend performance** (run in CI):
- Lighthouse CI on every PR (performance score > 90)
- Bundle size check via `@next/bundle-analyzer` (fail if initial bundle > 250KB gzipped)
- Core Web Vitals monitoring via Vercel Analytics in production

**Database performance:**
- `EXPLAIN ANALYZE` for all new queries added in a PR (documented in PR description)
- Index coverage check: no sequential scans on tables with >1,000 rows
- Connection pool monitoring via Datadog

### 8.4 Performance Optimization Playbook

| Symptom | First Check | Common Fix |
|---------|-------------|------------|
| API P95 > 500ms | Datadog APM trace waterfall | N+1 query → add `selectinload`; slow LLM call → check model choice |
| LCP > 2.5s | Lighthouse performance audit | Large images → next/image; blocking JS → dynamic import; uncached data → ISR |
| LLM call > 3s | Model and prompt length | Reduce prompt size; switch to faster model (Haiku); add caching for repeated prompts |
| BKT update > 100ms | CPU profiling | Check if pyBKT is re-fitting (should use Roster.update_state, not Model.fit) |
| DB query > 100ms | `EXPLAIN ANALYZE` | Missing index; sequential scan; large result set → add pagination |
| Bundle > 250KB | `@next/bundle-analyzer` | Large dependency → lazy load; unused code → tree-shake; KaTeX → dynamic import |

---

## Appendix A: Git Workflow

### Branch Naming

| Type | Pattern | Example |
|------|---------|---------|
| Feature | `feat/{stage}-{short-description}` | `feat/s1-diagnostic-assessment-flow` |
| Bug fix | `fix/{issue-number}-{description}` | `fix/42-bkt-mastery-overflow` |
| Chore | `chore/{description}` | `chore/update-dependencies` |
| Docs | `docs/{description}` | `docs/adr-009-caching-strategy` |
| Refactor | `refactor/{description}` | `refactor/extract-llm-client` |

### Commit Messages

Follow Conventional Commits:
```
<type>(<scope>): <description>

[optional body]
[optional footer]
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `ci`, `perf`  
Scopes: `web`, `api`, `agent`, `bkt`, `qgen`, `infra`, `ci`, `docs`

Examples:
```
feat(api): add diagnostic assessment submission endpoint
fix(bkt): prevent mastery probability from exceeding 1.0
test(agent): add unit tests for hint generation node
docs(adr): add ADR-009 for caching strategy
chore(ci): update GitHub Actions to Node 22
```

### PR Requirements

Every PR must:
1. Pass all CI checks (lint, typecheck, test)
2. Include tests for new functionality
3. Have a descriptive title following Conventional Commits format
4. Include a description explaining what and why
5. Be self-reviewed with Claude Code before requesting human review (see Section 3.5)
6. Not exceed 400 lines of non-test code changes (break larger changes into stacked PRs)

---

## Appendix B: Glossary

| Term | Definition |
|------|-----------|
| **BKT** | Bayesian Knowledge Tracing — probabilistic model for estimating student knowledge state |
| **COPPA** | Children's Online Privacy Protection Act — US federal law governing data collection from children under 13 |
| **IRT** | Item Response Theory — framework for modeling question difficulty and student ability |
| **LCP** | Largest Contentful Paint — Core Web Vital measuring perceived load speed |
| **LCEL** | LangChain Expression Language — declarative chain composition syntax |
| **P(L₀)** | Prior probability — initial probability that a student has mastered a skill before any observations |
| **P(T)** | Transition/learn probability — probability of transitioning from unmastered to mastered state |
| **P(G)** | Guess probability — probability of correct response given the skill is not mastered |
| **P(S)** | Slip probability — probability of incorrect response given the skill is mastered |
| **VPC** | Verifiable Parental Consent — COPPA requirement for age-appropriate consent verification |

---

*This is a living document. Update it when standards change, new ADRs are accepted, or patterns evolve. Every update requires a PR review.*
