# Contributing to MathPath Oregon

Thank you for your interest in contributing to MathPath Oregon! This project is currently in pre-MVP development (Stage 0–1). Contributions are welcome, but please read this guide first.

---

## 🎯 Project Status

**Current Phase:** Stage 0 — Infrastructure Setup (April 2026)  
**Development Model:** Solo developer + Claude Code AI agents  
**Target Audience for Contributions:** Team members starting from Stage 2 onward

If you're interested in contributing now (Stages 0–1), please contact the maintainer directly rather than opening unsolicited PRs.

---

## 🏗️ Development Setup

### Prerequisites
- macOS (M1/M4) or Linux with Docker
- Git, Docker Compose, pnpm, Python 3.12+
- Auth0 account (free developer tier)
- Ollama (for local LLM inference)

### First-Time Setup
```bash
# Clone the repo
git clone git@github.com:aerobu/mathpath-oregon.git
cd mathpath-oregon

# Install dependencies
pnpm install

# Pull environment variables from Vercel
vercel link --yes --project mathpath-oregon
vercel env pull .env.local --yes

# Start local infrastructure
docker-compose up -d

# Verify setup
pnpm run health  # Runs health checks on all services
```

See [README.md](README.md) for detailed setup.

---

## 📋 Development Workflow

### Branch Naming
```
feature/S{stage}-{epic}-{short-description}  # e.g., feature/S1-001-parent-consent-flow
bugfix/S{stage}-{issue-id}-{description}     # e.g., bugfix/S1-045-bkt-update-race
hotfix/critical-{description}                 # e.g., hotfix/critical-coppa-consent-bug
```

### Commits
```
{type}({scope}): {description}

# Examples:
feat(auth): add COPPA consent email verification
fix(bkt): correct mastery probability update formula
test(assessment): add CAT item selection tests
docs(readme): update setup instructions
refactor(api): extract question validation service
```

### Code Review Checklist
Every PR must satisfy:

- [ ] **Tests passing** — `pnpm test` (frontend) + `pytest` (backend) both green
- [ ] **Types valid** — `pnpm type-check` + `mypy apps/api/`
- [ ] **Linting clean** — `pnpm lint` + `ruff check apps/api/`
- [ ] **Coverage maintained** — no reduction in overall coverage
- [ ] **COPPA rules followed** — no student PII before consent validation
- [ ] **No direct LLM SDK imports** — all calls via `llm_client.get_llm_response()`
- [ ] **Architecture Decision Record (if applicable)** — major decisions documented in `docs/adr/`
- [ ] **Documentation updated** — new features have docstrings + relevant README/ADR updates
- [ ] **One reviewer approval** — for routine changes; two for auth/COPPA/payments

### PR Template

```markdown
## Description
Brief summary of what this PR does.

## Related Ticket
Closes #123 or Relates to #456

## Type of Change
- [ ] Feature
- [ ] Bugfix
- [ ] Refactor
- [ ] Documentation
- [ ] Chore

## How to Test
Step-by-step instructions for manual QA.

## COPPA/Security Checklist
- [ ] No hardcoded secrets
- [ ] No student PII outside COPPA-verified paths
- [ ] Parameterized queries (no raw SQL)
- [ ] Input validation on all endpoints

## Screenshots (if UI change)
[Attach screenshots if applicable]
```

---

## 🧪 Testing Requirements

### Unit Tests
```bash
# Frontend (Jest + React Testing Library)
cd apps/web
pnpm test --coverage

# Backend (Pytest)
cd apps/api
pytest --cov=src/ --cov-report=term-missing
```

### Integration Tests
```bash
# Test API integration with real PostgreSQL + Redis
cd apps/api
pytest tests/integration/ --cov=src/

# Test frontend API integration
cd apps/web
pnpm test:integration
```

### E2E Tests
```bash
# Full user journey with Playwright
cd apps/web
pnpm test:e2e

# Run against staging environment
pnpm test:e2e --baseURL=https://staging.mathpath.local
```

### Coverage Thresholds
- **Backend business logic:** ≥80% line coverage
- **Frontend components:** ≥75% coverage
- **API endpoints:** ≥90% coverage (critical COPPA paths: 100%)

---

## 🔐 Security Guidelines

### Never Commit
- API keys, tokens, secrets
- Credentials for external services
- Student/parent PII in test fixtures
- Unencrypted passwords

### Always
- Use `sqlite_pgvector` parameterized queries in SQLAlchemy
- Validate input at system boundaries (user input, external APIs)
- Hash passwords with bcrypt (never store plaintext)
- Encrypt PII at rest (AES-256) and in transit (TLS 1.3)
- Log security events with context (user ID, timestamp, action)
- Review COPPA/FERPA implications of data flows before implementation

### COPPA-Specific
1. **Consent first** — Never write student PII without `consent_records.confirmed_at IS NOT NULL` verification
2. **Parental gate** — All student account creation must be via parent account
3. **Data minimization** — Collect only what's necessary for learning
4. **Data deletion** — Implement parent-initiated deletion workflows
5. **Third-party vendors** — All LLM calls for student data require DPAs confirming zero data retention

---

## 📚 Documentation Standards

### Code Comments
```python
def update_bkt_mastery(
    prior: float, correct: bool, params: BKTParams
) -> float:
    """
    Update Bayesian Knowledge Tracing probability of mastery given a response.
    
    Uses the standard BKT update rule: P(mastered | correct) = 
    P(correct | mastered) * P(mastered) / P(correct)
    
    Reference: Corbett & Anderson (1995) "Knowledge Tracing: Modeling 
    the Acquisition of Procedural Knowledge"
    
    Args:
        prior: P(mastered) before this response (0.0–1.0)
        correct: Whether the student answered correctly
        params: BKT parameters (T, G, S)
    
    Returns:
        Updated P(mastered) after response
    
    Raises:
        ValueError: If prior not in [0, 1] or params invalid
    """
```

### Architecture Decision Records (ADRs)
Major decisions should be documented in `docs/adr/ADR-###-title.md`:

```markdown
# ADR-010: [Decision Title]

## Status
Proposed | Accepted | Deprecated | Superseded by ADR-###

## Context
Why we're making this decision; what problem does it solve?

## Decision
What we're deciding to do.

## Consequences
Positive and negative impacts of this decision.

## Alternatives Considered
Other options and why we rejected them.

## References
Links to related issues, research, etc.
```

See [ENG-000-foundations.md](ENG-000-foundations.md) for existing ADRs.

---

## 🚀 Deployment & CI/CD

### GitHub Actions CI Pipeline
Every PR automatically runs:
1. Lint (`ruff` for Python, `eslint` for TypeScript)
2. Type check (`mypy` for Python, `tsc` for TypeScript)
3. Unit tests (`pytest` for Python, `jest` for TypeScript)
4. Coverage report (must not decrease)
5. Security scan (`bandit` for Python, `npm audit` for dependencies)
6. Build check (`next build` + `poetry build`)

All checks must pass before merging.

### Staging Deployment
Merging to `main` automatically deploys to staging:
- Frontend: `https://staging.mathpath.local` (Vercel)
- API: Fargate staging cluster (AWS)

Manual testing required before production promotion.

### Production Deployment
Only tagged releases deploy to production:
```bash
git tag -a v0.1.0-alpha -m "Alpha release: Diagnostic assessment working"
git push origin v0.1.0-alpha
```

Requires approval from maintainer + passing staging QA.

---

## 🤝 Getting Help

- **Documentation**: See [README.md](README.md), planning docs (`0*.md`, `ENG-*.md`), and inline code comments
- **Architecture**: Refer to [ENG-000-foundations.md](ENG-000-foundations.md) for system design
- **Stage specs**: Check the relevant `ENG-00X-stageX.md` and `0X-prd-stageX.md`
- **Questions**: Open a GitHub Discussion or contact the maintainer

---

## 📖 Useful Commands

```bash
# Development
pnpm dev                    # Start Next.js + FastAPI locally
pnpm test                   # Run all tests
pnpm lint                   # Lint code
pnpm type-check             # Type checking

# Database
alembic upgrade head        # Run pending migrations
alembic downgrade -1        # Rollback one migration
alembic revision --autogenerate -m "Add users table"

# Git
git log --oneline --graph   # View commit history
git diff origin/main        # View changes vs main
gh pr view                  # View current PR (if gh CLI installed)

# Environment
vercel env pull .env.local  # Refresh Vercel env vars
vercel env list             # List all env vars on Vercel
```

---

## ✅ Checklist Before Submitting a PR

- [ ] Branch created from `develop` with correct naming
- [ ] All tests passing locally
- [ ] Coverage thresholds met
- [ ] Linting and type checking passing
- [ ] No console errors or warnings in dev
- [ ] COPPA/security rules reviewed
- [ ] Commit messages follow convention
- [ ] PR description filled out completely
- [ ] Screenshots attached (if UI change)
- [ ] Documentation updated (README, docstrings, ADR if applicable)

---

## 📞 Code of Conduct

This project adheres to a Code of Conduct (to be added). In short: be respectful, constructive, and assume good intent.

---

## 📄 License

By contributing, you agree that your contributions will be licensed under the same license as the project (to be determined — likely Apache 2.0 or MIT).

---

**Happy contributing!**  
Questions? Open a GitHub Discussion or contact [@aerobu](https://github.com/aerobu).
