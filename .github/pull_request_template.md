## 📝 Description
Brief summary of what this PR accomplishes.

## 🎫 Related Issue(s)
- Closes #123
- Relates to #456

## 🔀 Type of Change
- [ ] Feature (new functionality)
- [ ] Bugfix (fixes existing bug)
- [ ] Refactor (no behavior change)
- [ ] Documentation
- [ ] Chore (dependencies, build, etc.)
- [ ] Performance improvement

## 🏗️ Architecture / Design Changes
(If applicable) How does this change the system? Any new tables, APIs, agent nodes?

## ✅ Testing
### Unit Tests
- [ ] New tests written for new logic
- [ ] All tests passing: `pnpm test` + `pytest`

### Integration Tests
- [ ] If API change: tested with real DB/Redis
- [ ] If frontend change: tested in multiple browsers

### Manual Testing
Steps to manually verify this change:
1. 
2. 
3. 

### Coverage
- [ ] Line coverage maintained or improved
- [ ] Critical paths (COPPA, payments) have ≥90% coverage

## 🔒 Security & Compliance Checklist
- [ ] No hardcoded secrets
- [ ] No student PII outside COPPA-verified paths
- [ ] All SQLAlchemy queries (no raw SQL)
- [ ] Input validation on public endpoints
- [ ] All LLM calls via `llm_client.get_llm_response()`
- [ ] If touching auth/payments: approved by maintainer
- [ ] If touching student data: COPPA implications reviewed

## 📚 Documentation
- [ ] Docstrings added for new functions/classes
- [ ] README updated (if user-facing)
- [ ] ADR created (if architectural decision)
- [ ] Inline comments for non-obvious logic

## 🎨 Code Quality
- [ ] `pnpm lint` passing (ESLint, Prettier)
- [ ] `pnpm type-check` passing (TypeScript)
- [ ] `ruff check` + `mypy` passing (Python)
- [ ] No console warnings or errors in dev

## 🚀 Deployment Notes
- [ ] Feature flag added (if user-facing)
- [ ] Database migration included (if schema change)
- [ ] Environment variables documented (if new config)
- [ ] Backward-compatible (if upgrading existing systems)

## 📸 Screenshots (UI changes)
[Attach screenshots or GIFs showing the change]

## 🔄 Reviewer Checklist (For Maintainer)
- [ ] Code quality and patterns
- [ ] Test coverage adequate
- [ ] COPPA/security rules followed
- [ ] Architecture sensible
- [ ] Performance acceptable
- [ ] Documentation clear

## 📋 Additional Context
Any additional information the reviewer should know?

---

## Pre-Merge Checklist
- [ ] All CI checks passing (lint, test, build, security)
- [ ] At least one approval
- [ ] Branch up-to-date with `develop`
- [ ] No merge conflicts
- [ ] Commits are atomic and well-message (can rebase if needed)
