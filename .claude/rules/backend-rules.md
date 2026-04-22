---
globs: apps/api/**/*.py, services/**/*.py
---

# Backend Rules — PADI.AI

## 🏛️ Architectural Guardrails
1. **Repository Pattern:** DO NOT access DB models directly in routers. Use `src/repositories/`.
2. **Async Everything:** All DB and LLM calls must be `async/await`.
3. **Pydantic Schemas:** Use schemas for ALL inputs and outputs. Never return SQLAlchemy models directly.

## 🛡️ COPPA Compliance
- **Student Data:** MUST use `LLMPurpose.STUDENT_TUTORING`.
- **Local LLM:** Always route through Ollama via LiteLLM for student tutoring.

## 🏗️ Structure
- **Routes (`api/v1/`):** Thin controllers.
- **Services:** Business logic orchestration.
- **Repositories:** ALL database access logic.

## 📋 Linting & Formatting
- **Ruff:** Linting and auto-fixing.
- **Black:** Code formatting.
- **Mypy:** Strict type checking.
