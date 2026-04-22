---
globs: **/tests/**/*.py, **/tests/**/*.ts, **/tests/**/*.tsx, **/*.test.ts, **/*.test.tsx, **/*.spec.ts, **/features/**/*.feature
---

# Testing Rules — PADI.AI

## 📐 Testing Pyramid
- **Unit (70%):** Isolated logic. Mock dependencies.
- **Integration (20%):** Service/Component interactions.
- **E2E (10%):** Playwright journeys (registration, assessment).

## 🚦 Coverage Gates (Strict)
- **General Services:** 80% line coverage.
- **BKT Engine:** 90% line coverage.
- **COPPA/Security Flows:** 100% line coverage (MANDATORY).

## 📝 Standards
- **Frontend:** Vitest + Testing Library. Test behavior (roles, labels), not implementation.
- **Backend:** Pytest. Use `conftest.py` fixtures.
- **E2E:** Playwright. Page Object Model required.
- **BDD:** Feature files in `tests/features/`.

## 🛡️ COPPA Testing
- 100% coverage required for `consent_service.py` and `security.py`.
- Must verify: missing consent, revoked consent, and data deletion cascades.
