# PADI.AI

> AI-powered adaptive math learning for Oregon elementary students (Grades 1–5), with an initial focus on Grade 4.

**Status:** Pre-Development Planning (April 2026)  
**Current Phase:** Stage 0 — Infrastructure Setup  
**Projected MVP:** Month 14 | **Projected MMP:** Month 30–36

---

## 🎯 Mission

PADI.AI closes the math proficiency gap for Oregon elementary students by delivering AI-generated, standards-aligned adaptive instruction — diagnosing exactly where each student is, building personalized learning paths from the ground up, and continuously adapting until mastery is real and measured.

Oregon 4th graders score 8 points below the national NAEP average; only 31% reach proficiency. **PADI.AI targets this gap with**:

1. **Prerequisite gap remediation** — diagnose and fix Grade 3 foundations before Grade 4 content
2. **Step-level Socratic tutoring** — AI-powered hints that guide students through reasoning (d=0.76 vs. answer-level d=0.30)
3. **BKT mastery gating** — students advance only when Bayesian Knowledge Tracing confirms P(mastered) ≥ 0.85
4. **Error-type classification** — different error types receive different instructional interventions

Expected outcome: **15–25 percentage point proficiency improvement** among engaged students (vs. ~5% for existing platforms).

---

## 📚 Documentation Structure

### Product Documentation (Planning)
- **[00-master-index.md](00-master-index.md)** — Overview of entire suite, stage gates, tech stack, investment summary
- **[01-strategy.md](01-strategy.md)** — Vision, GTM, competitive moat, risk register, OKRs, pedagogical hypothesis
- **[02-product-plan.md](02-product-plan.md)** — Milestones, feature roadmap, resource plan, solo dev timeline
- **[03-07-prd-stage*.md](03-prd-stage1.md)** — Detailed PRDs for Stages 1–5 (functional requirements, acceptance criteria)
- **[09-design-system.md](09-design-system.md)** — UI/UX design system, tokens, personas, accessibility, tablet-first strategy
- **[16-multigrade-expansion.md](16-multigrade-expansion.md)** — Post-MVP expansion plan (Grades 1, 2, 3, 5)
- **[adaptive-math-app-viability.md](adaptive-math-app-viability.md)** — Research-backed viability study (Oregon standards, competitive landscape, AI feasibility)

### Engineering Documentation
- **[ENG-MASTER-INDEX.md](ENG-MASTER-INDEX.md)** — Engineering overview, ADRs, model routing, non-negotiable rules
- **[ENG-000-foundations.md](ENG-000-foundations.md)** — Monorepo structure, 8 ADRs, coding standards, COPPA security baseline
- **[ENG-001 through ENG-005](ENG-001-stage1.md)** — Stage-specific engineering: architecture, DDL, algorithms, API specs, test plans
- **[ENG-006-crosscutting.md](ENG-006-crosscutting.md)** — Testing strategy, observability, security, data governance, MLOps

### Lifecycle Documentation
- **[10-lifecycle-stage*.md](10-lifecycle-stage1.md)** — Full SDLC for each stage: user stories, test cases, ops runbooks
- **[15-lifecycle-crosscutting-ops.md](15-lifecycle-crosscutting-ops.md)** — MLOps, FinOps, SecOps, DevSecOps, compliance

### Development Environment
- **[17-claude-code-skills-spec.md](17-claude-code-skills-spec.md)** — Claude Code customization: skills, rules, commands, hooks, MCP servers

---

## 🏗️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 19, Next.js 15 (Vercel), TypeScript, Tailwind CSS, KaTeX |
| **Backend** | Python 3.12, FastAPI, SQLAlchemy, Pydantic v2 |
| **AI/Agents** | LangGraph 0.2, LiteLLM (abstraction layer for local + cloud LLMs) |
| **LLMs** | Qwen2.5:72b/32b (local, Ollama) for student-facing; Claude Sonnet 4.6 for admin |
| **Knowledge Tracing** | pyBKT 1.4 + custom IRT implementation |
| **Database** | PostgreSQL 17 + pgvector |
| **Cache/Session** | Redis 7 |
| **Auth** | Auth0 (COPPA-compliant) |
| **Infra** | AWS (ECS/Fargate, RDS, ElastiCache, S3) + Vercel (frontend) |
| **Payments** | Stripe (MMP) |
| **Analytics** | PostHog (COPPA-safe, cookieless) |
| **Testing** | Pytest, Jest, React Testing Library, Playwright |

---

## 📋 Stage Overview

| Stage | Duration | Key Deliverables | Gate |
|-------|----------|---|---|
| **Stage 0** | Weeks 1–4 | Monorepo, LiteLLM, Ollama, CI/CD, Auth0 setup | Infrastructure ready |
| **Stage 1** | Months 1–5 | Oregon standards DB, COPPA consent, diagnostic assessment, 500+ seed questions | Internal PoC |
| **Stage 2** | Months 6–10 | Learning plan generator, LLM question generation pipeline, dashboards | Alpha (10–50 students) |
| **Stage 3** | Months 11–17 | Multi-agent LangGraph tutoring, real-time BKT, WebSocket sessions | Tutoring validated |
| **Stage 4** | Months 18–24 | End-of-grade assessment, IRT, parent/teacher dashboards, PDF reports | **MVP** ✓ |
| **Stage 5** | Months 25–32 | Stripe billing, school onboarding, Spanish i18n, COPPA cert | **MMP** ✓ |
| **Stage 6** | Months 33–36+ | Multi-grade (Grades 1–5), district contracts, 10K+ question bank | v1.0 |

---

## 🚀 Quick Start (Development)

### Prerequisites
- macOS (M1/M4 with 16GB+ RAM) or Linux with Docker
- Git, Docker Compose
- Python 3.12+, Node.js 20+, pnpm
- Auth0 account (free developer tier OK)
- Ollama (for local LLM inference)

### 1. Clone & Install
```bash
git clone git@github.com:<your-org>/padi-ai.git
cd padi-ai

# Install dependencies
pnpm install

# Python virtual environment (when app/ directory exists)
cd apps/api
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

### 2. Environment Variables
```bash
# Copy template files when generated
cp .env.example .env.local
# Edit .env.local with:
# - AUTH0_CLIENT_ID, AUTH0_CLIENT_SECRET
# - DATABASE_URL (local PostgreSQL)
# - REDIS_URL (local Redis)
# - OPENAI_API_KEY, ANTHROPIC_API_KEY (for question generation)
```

### 3. Local Development
```bash
# Start local infrastructure (PostgreSQL, Redis, Ollama)
docker-compose up -d

# Run migrations
cd apps/api && alembic upgrade head

# Start Next.js frontend
cd apps/web && pnpm dev  # http://localhost:3000

# Start FastAPI backend (in another terminal)
cd apps/api && uvicorn main:app --reload  # http://localhost:8000/docs
```

### 4. Verify Local LLM
```bash
# Check Ollama health
curl http://localhost:11434/api/tags

# In Python, verify LiteLLM routing
python -c "from app.clients.llm_client import get_llm_response; print(get_llm_response('tutor', [{'role': 'user', 'content': 'Hi'}]))"
```

---

## 🎓 Development Workflow (Solo + Claude Code)

This is a **solo development project** using Claude Code AI agents for heavy lifting. Key principles:

1. **Agent-executable chunks** — Tasks are sized for a Claude Code agent to complete in 2–4 hours (single endpoint, single component, single algorithm)
2. **Tests first** — Every agent task begins with tests; never merge unverified agent output
3. **Context loading mandatory** — Agents load CLAUDE.md + stage engineering doc before starting
4. **Parallel work** — Run multiple agents on independent modules (frontend/backend, different epics)

### Running an Agent Task
```bash
# Load the relevant context files first
# See 17-claude-code-skills-spec.md for Claude Code setup

# Example: Build a single API endpoint
# 1. Create Jira/GitHub ticket with spec
# 2. Load CLAUDE.md (root + apps/api)
# 3. Load ENG-001 (Stage 1 spec) or relevant stage
# 4. Describe the agent task narrowly (single endpoint, not full stage)
# 5. Run agent via Claude Code
# 6. Run tests: pytest apps/api/tests/
# 7. Merge to develop branch
```

See **[08-software-dev-plan.md](08-software-dev-plan.md)** for detailed stage/sprint breakdown and time estimates.

---

## 🔐 Security & Compliance (COPPA/FERPA)

### Non-Negotiable Rules
1. **No COPPA data before consent** — any code writing student PII must first verify `consent_records.confirmed_at IS NOT NULL`
2. **No raw SQL** — SQLAlchemy ORM only; parameterized queries enforced by `bandit` in CI
3. **No hardcoded secrets** — `detect-secrets` pre-commit hook
4. **No LLM output to students unvalidated** — all generated questions pass 5-step validation (execution, accuracy, appropriateness, standards tagging, human review)
5. **All LLM calls via `llm_client.get_llm_response()`** — no direct `anthropic` or `openai` SDK imports in agent code
6. **No student data to cloud LLMs without COPPA DPAs** — default to Ollama/Qwen2.5 for student-facing inference until legal clearance
7. **Every API endpoint authenticated** — except `/health`, `/auth/*`, marketing pages
8. **Feature flags for all user-facing features** — no dark launches

See **[ENG-000-foundations.md](ENG-000-foundations.md)** for full ADRs and security baseline.

---

## 📊 Pedagogical Hypothesis

PADI.AI will achieve **15–25pp proficiency improvement** among engaged students (vs. ~5% for existing platforms) because:

| Mechanism | Research | Effect |
|---|---|---|
| **Prerequisite gap remediation** | Fuchs et al. (2021) — IES What Works Clearinghouse | Eliminates silent foundational gaps before grade-level content |
| **Step-level Socratic feedback** | VanLehn (2011) — meta-analysis of 62 studies | d = 0.76 vs. answer-level systems' d = 0.30 |
| **BKT mastery gating + spaced practice** | Bloom (1984), Cepeda et al. (2006) | Durable mastery, not shallow fluency |
| **Error-type classification** | Pashler et al. (2007) — IES guidance | Targeted feedback matched to error root cause |

See **[01-strategy.md § 5a](01-strategy.md)** and **[adaptive-math-app-viability.md](adaptive-math-app-viability.md)** for full research backing.

---

## 💰 Investment Summary

| Phase | Duration | Solo Cost (Realistic) |
|---|---|---|
| **Stage 0** | 3–4 weeks | ~$0 (self) |
| **Stage 1** | 4–5 months | ~$160K |
| **Stage 2** | 5–6 months | ~$216K |
| **Stage 3** | 6–8 months | ~$372K |
| **Stage 4 (MVP)** | 5–7 months | ~$325K |
| **Stage 5 (MMP)** | 8–10 months | ~$555K |
| **Total to MMP** | **30–36 months** | **~$1.63M** |

*Assumes solo developer at market equivalent rate. Actual cash outlay is much lower for founder-led development. External costs: Auth0 ($23/mo), AWS ($300–500/mo dev), curriculum specialist contractor ($750–$1,500/mo from Stage 2), legal (~$3–5K COPPA review).*

---

## 📞 Key Contacts & Resources

- **Pedagogical Research**: See [adaptive-math-app-viability.md](adaptive-math-app-viability.md) for 20+ citations
- **Engineering ADRs**: [ENG-000-foundations.md](ENG-000-foundations.md)
- **Oregon Standards**: [Oregon Department of Education](https://www.oregon.gov/ode/educator-resources/standards/mathematics/pages/mathstandards.aspx)
- **Claude Code Setup**: [17-claude-code-skills-spec.md](17-claude-code-skills-spec.md)

---

## 📄 License

[To be determined — recommend Apache 2.0 or MIT for open-source components]

---

## 🤝 Contributing

This is a pre-MVP project. Contributions welcome after Stage 1 completion. See [CONTRIBUTING.md](CONTRIBUTING.md) (to be created) for guidelines.

---

**Last Updated:** April 10, 2026  
**Author:** Prabu Ravindren  
**Development Model:** Solo + Claude Code AI agents
