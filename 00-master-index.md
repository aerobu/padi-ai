# PADI.AI — Complete Product & Engineering Documentation Suite

> **Prepared:** April 2026  
> **Scope:** Oregon Grades 1–5 Adaptive Math Learning App  
> **Status:** Pre-Development Planning

---

## Document Suite Overview

This documentation suite covers the complete product strategy, detailed requirements, engineering implementation plan, full SDLC lifecycle documentation, multi-grade expansion plan, and Claude Code development environment specification for **PADI.AI** — an AI-powered adaptive math learning application for Oregon elementary students (Grades 1–5). It consists of seventeen product documents totaling ~45,000 lines of planning material, plus eight engineering documents.

---

## Document Index

| # | Document | Stage | Purpose | Key Contents |
|---|----------|-------|---------|-------------|
| 01 | [Product Strategy](./01-strategy.md) | All | Why & How to build PADI.AI | Vision, GTM, competitive moat, risk register, OKRs |
| 02 | [Product Plan](./02-product-plan.md) | All | What to build and when | Milestones, feature roadmap, resource plan, investment summary |
| 03 | [PRD Stage 1](./03-prd-stage1.md) | Months 1–3 | Standards DB & Diagnostic | COPPA flow, Oregon standards schema, 132+ question seed bank, CAT diagnostic |
| 04 | [PRD Stage 2](./04-prd-stage2.md) | Months 4–6 | Learning Plan Generator | Skill dependency graph, AI question generation pipeline, student/parent dashboards |
| 05 | [PRD Stage 3](./05-prd-stage3.md) | Months 7–10 | Adaptive Practice Engine | LangGraph agents, BKT/IRT adaptation, dual memory, Socratic tutor |
| 06 | [PRD Stage 4](./06-prd-stage4.md) | Months 11–14 | EOG Assessment + Reporting | **MVP Milestone** — Summative assessment, remediation loop, teacher/parent dashboards |
| 07 | [PRD Stage 5](./07-prd-stage5.md) | Months 15–20 | MMP — Polish & Monetization | **MMP Milestone** — Stripe billing, school onboarding, Spanish, analytics, COPPA cert |
| 08 | [Software Dev Plan](./08-software-dev-plan.md) | All | Engineering implementation | 37 sprints, 107+ tickets, Terraform, migrations, test strategy, CI/CD |
| 09 | [UI/UX Design System](./09-design-system.md) | All | Complete design system for Figma | Personas, workflows, color/typography/spacing tokens, component specs, math UI patterns, accessibility, Figma guide |
| 10 | [Lifecycle: Stage 1](./10-lifecycle-stage1.md) | Months 1–3 | Full SDLC lifecycle for Stage 1 | Architecture review, 29 user stories, 142 test cases, ops plan (MLOps/FinOps/SecOps), manual QA |
| 11 | [Lifecycle: Stage 2](./11-lifecycle-stage2.md) | Months 4–6 | Full SDLC lifecycle for Stage 2 | Architecture review, 24 user stories, 78+ test cases, LLM contract testing, ops plan, manual QA |
| 12 | [Lifecycle: Stage 3](./12-lifecycle-stage3.md) | Months 7–10 | Full SDLC lifecycle for Stage 3 | Multi-agent architecture review, 33 user stories, agent testing, WebSocket tests, ops plan, manual QA |
| 13 | [Lifecycle: Stage 4](./13-lifecycle-stage4.md) | Months 11–14 | Full SDLC lifecycle for Stage 4 (MVP) | CAT/IRT architecture review, 43 user stories, MVP acceptance suite, ops plan, manual QA |
| 14 | [Lifecycle: Stage 5](./14-lifecycle-stage5.md) | Months 15–20 | Full SDLC lifecycle for Stage 5 (MMP) | Stripe/SSO/i18n architecture, 44 user stories, MMP launch gate, ops plan, manual QA |
| 15 | [Cross-Cutting Operations](./15-lifecycle-crosscutting-ops.md) | All | Unified operational framework | MLOps, FinOps, SecOps, DevSecOps pipeline, runbooks, DR, compliance calendar |
| 16 | [Multi-Grade Expansion](./16-multigrade-expansion.md) | Post-MMP | Grades 1, 2, 3, 5 expansion | 99 new standards, prerequisite graphs, age-appropriate UI, architecture plan, rollout strategy |
| 17 | [Claude Code Skills & Plugins](./17-claude-code-skills-spec.md) | All | AI-assisted development spec | 16 skills, 8 rule files, 7 commands, 8 hooks, 5 subagents, 6 MCP servers, CLAUDE.md template, implementation roadmap |

---

## Engineering Documentation

See the [Engineering Master Index](../eng-docs/ENG-MASTER-INDEX.md) for the full engineering document suite (8 documents).

---

## SDLC Lifecycle Documentation

Documents 10–15 provide the full software development lifecycle for each stage, covering:

| Section | Description |
|---------|-------------|
| Architecture Review | Component analysis, data flow, decisions, risks |
| User Story Breakup | Epics → stories with acceptance criteria, priorities, points |
| Detailed Test Plan | Unit, integration, E2E, BDD, robustness, repeatability, security, acceptance criteria |
| Operations Plan | MLOps, FinOps, SecOps, DevSecOps per stage |
| Manual QA Plan | Tests requiring human judgment: accessibility, content accuracy, UX |

**Aggregate statistics across all lifecycle documents:**

| Metric | Total |
|--------|-------|
| Total lines | ~18,800 |
| User stories | 173 |
| Named test cases | 450+ |
| Code examples | 130+ |
| Operational runbooks | 7 |
| BDD feature files | 15+ |

---

## Claude Code Development Environment

Document 17 defines the complete Claude Code customization layer — the configuration files, skills, hooks, commands, subagents, and MCP server integrations that transform Claude Code from a general-purpose assistant into a PADI.AI-aware development partner.

| Component | Count | Purpose |
|-----------|-------|---------|
| Skills (`.claude/skills/`) | 16 | Domain-specific knowledge: design tokens, BKT patterns, LangGraph agents, COPPA compliance, Oregon standards |
| Rule Files (`.claude/rules/`) | 8 | Path-scoped conventions that auto-load when editing matched files |
| Slash Commands (`.claude/commands/`) | 7 | Developer workflows: implement story, run tests, search specs, load stage context |
| Hook Handlers | 8 | Automated enforcement: lint on save, context preservation on compact, quality gates on stop |
| Subagent Definitions (`.claude/agents/`) | 5 | Isolated workers: test runner, security scanner, spec researcher, code reviewer, grade validator |
| MCP Server Integrations | 6 | External tools: GitHub, PostgreSQL, Figma, Playwright, Sentry, Context7 |

Estimated implementation: ~100 hours over 10 weeks, phased alongside Stage 1 development.

---

## Product Stage Gates

```
Month 3 ──────── Month 6 ──────────── Month 10 ──────────── Month 14 ──────────── Month 20 ──────────── Month 24
   │                  │                    │                      │                      │                    │
[Stage 1]         [Stage 2]            [Stage 3]              [Stage 4]              [Stage 5]           [Stage 6]
Standards DB    Learning Plan        Adaptive AI            End-of-Grade           Monetization        Full Product
& Diagnostic    Generator            Tutoring Engine        Assessment             & School             v1.0
                                                            ← MVP MILESTONE →      ← MMP MILESTONE →
```

### Stage Gate Definitions

| Gate | Milestone | Month | Minimum Conditions |
|------|-----------|-------|--------------------|
| **PoC** | Internal prototype | ~Month 2 | Diagnostic works end-to-end with seed questions; BKT initializes correctly |
| **Alpha** | Closed beta with 10–20 families | Month 6 | Stages 1+2 complete; learning plan generates; AI questions validate |
| **MVP** | Minimum Viable Product | Month 14 | Complete core loop: diagnostic → plan → practice → summative → remediation |
| **MMP** | Minimum Marketable Product | Month 20 | Paid subscriptions, school onboarding, COPPA Safe Harbor, Spanish, analytics |
| **v1.0** | Full Product | Month 24 | All grades 3–5 in Oregon, district contracts, 10,000+ question bank |

### Solo Development Timeline Adjustment

```
Week 1 ─── Month 5 ──────── Month 11 ──────────── Month 19 ──────────── Month 26 ──────────── Month 36
  │              │                │                      │                      │                    │
[Stage 0]    [Stage 1]        [Stage 2]              [Stage 3]              [Stage 4]          [Stage 5]
  Setup      Diagnostic       Learning Plan          AI Tutoring              MVP                  MMP
            & Standards       Generator              Engine                ← MVP →              ← MMP →
```

*Original plan assumed 3–7 person team. Revised timeline is solo developer + Claude Code agents at 25–35 hrs/week. All stage definitions and quality gates remain identical — only the calendar duration changes.*

---

## Technology Stack at a Glance

| Layer | Technology |
|-------|-----------|
| Frontend | React 19, Next.js 15, TypeScript, Tailwind CSS, KaTeX |
| Mobile | React Native (post-MMP) |
| Backend | Python 3.12, FastAPI, SQLAlchemy, Pydantic v2 |
| AI Agents | LangGraph 0.2, LangChain 0.3 |
| LLMs | **Local (COPPA-safe, student-facing):** Qwen2.5:72b + :32b via Ollama. **Cloud (admin/question gen only):** Claude Sonnet 4.6, o3-mini. All calls via LiteLLM abstraction (ADR-009; config-only switching). |
| Knowledge Tracing | pyBKT 1.4 + custom IRT implementation |
| Primary DB | PostgreSQL 17 + pgvector |
| Cache/Session | Redis 7 |
| Auth | Auth0 (COPPA plan) |
| Infra | AWS (ECS/Fargate, RDS, ElastiCache, S3, CloudFront) + Vercel |
| Payments | Stripe |
| Analytics | PostHog (COPPA-compliant, cookieless for students) |
| Testing | Pytest, Jest, React Testing Library, Playwright |
| CI/CD | GitHub Actions |

---

## Investment Summary

| Stage | Duration | Team Size | Monthly Burn | Stage Total |
|-------|----------|-----------|-------------|-------------|
| Stage 1 (Foundation) | Months 1–3 | 3 | ~$32K | ~$96K |
| Stage 2 (Learning Plan) | Months 4–6 | 4 | ~$45K | ~$135K |
| Stage 3 (AI Tutoring) | Months 7–10 | 5 | ~$58K | ~$232K |
| Stage 4 (MVP) | Months 11–14 | 5 | ~$58K | ~$232K |
| Stage 5 (MMP) | Months 15–20 | 6 | ~$74K | ~$444K |
| Stage 6 (Full Product) | Months 21–24 | 7 | ~$89K | ~$356K |
| **Total 24 months** | | | | **~$1.50M** |

> **Solo Development Mode (Updated April 2026):** The investment summary above reflects a team-based model. For solo development with Claude Code AI agents as the primary development force, the revised estimates are:

| Stage | Original (Team) | Solo Optimistic | Solo Realistic |
|---|---|---|---|
| Stage 0 (New — Pre-Dev Setup) | — | ~$0 (self) | ~$0 (self) |
| Stage 1 (Foundation) | ~$96K | ~$128K (4 mo) | ~$160K (5 mo) |
| Stage 2 (Learning Plan) | ~$135K | ~$180K (5 mo) | ~$216K (6 mo) |
| Stage 3 (AI Tutoring) | ~$232K | ~$279K (6 mo) | ~$372K (8 mo) |
| Stage 4 (MVP) | ~$232K | ~$232K (5 mo) | ~$325K (7 mo) |
| Stage 5 (MMP) | ~$444K | ~$444K (8 mo) | ~$555K (10 mo) |
| **Total to MMP** | **~$1.14M** | **~$1.26M** | **~$1.63M** |

*These estimates assume a solo developer working 25–35 hrs/week at market-rate equivalent. Actual cash outlay is dramatically lower if the developer is the founder. Key external costs: Auth0 ($23/mo), AWS (~$300–500/mo at development scale), Claude API (~$50–200/mo for question generation), curriculum specialist contractor ($750–1,500/mo from Stage 2), legal consultation (~$3,000–5,000 one-time for COPPA review).*

---

## Key Risks to Monitor

1. **COPPA compliance** — Engage privacy counsel before any user data collection (Month 1)
2. **LLM question accuracy** — All generated questions must pass 5-step validation pipeline before student exposure
3. **BKT parameter calibration** — Requires real student data; initial parameters from pyBKT defaults, recalibrated after 500+ students
4. **School sales cycle** — 6–12 month typical cycle; begin school outreach at Month 10 (not Month 15)
5. **LLM API costs** — Monitor per-session cost; target < $0.15/session; cache aggressively
6. **COPPA + LLM API data flow** — Student responses sent to cloud LLMs (Claude, GPT-4o) for real-time tutoring require written DPAs confirming zero data retention. Default to local Ollama/Qwen models for all student-facing inference until legal review confirms cloud DPAs are in place. See ADR-009.
7. **Solo development timeline realism** — 20-month plan assumed a 3–7 person team. Solo + AI agents requires 30–36 months to MMP. Reduce scope within stages if timeline pressure increases — never cut COPPA compliance or BKT accuracy corners.

---

*This suite was generated as a planning artifact. All estimates are subject to revision based on team composition, technical discoveries during development, and market feedback.*
