# CLAUDE.md - PADI.AI Project Guidance

This project is an AI-powered adaptive math learning platform for Oregon elementary students (Grades 1-5, starting with Grade 4).

## 🚀 Optimized Context Management
To minimize token usage and avoid rate limits:
- **Active Task:** Refer to `ACTIVE_CONTEXT.md` for current goals and focus.
- **Documentation:** Most strategy and historical files are moved to `docs/`.
- **Path-Scoped Rules:** Critical instructions are now in `.claude/rules/*.md`. These load automatically when you edit relevant files.
- **Session Reset:** Start a new chat session after completing a major sub-task to clear token history.

## 🏛️ Architectural Guardrails (Mandatory)
1. **Repository Pattern:** All database operations in `apps/api` MUST go through a repository. Direct DB access in services or routers is forbidden.
2. **Strict Isolation:** No direct imports between `apps/api` and `apps/web`. Share types via `packages/types`.
3. **Pydantic V2:** Use strictly for all request/response validation in the backend.
4. **Validation First:** Qwen implements; Opus performs architectural review ONLY after tests and lint pass.

## 🛡️ Critical COPPA Compliance
- **STUDENT DATA:** ALWAYS use local Ollama models. NEVER send student PII to cloud LLMs.
- **ADMIN FEATURES:** Cloud LLMs (Claude, o3-mini) are permitted for teacher/admin tasks only.

## 🛠️ Tech Stack
- **Frontend:** Next.js 15 (App Router), React 19, Tailwind CSS.
- **Backend:** Python 3.12, FastAPI, SQLAlchemy 2.0 (Async), Pydantic v2.
- **AI:** LiteLLM (Local routing for students), Ollama (Qwen2.5).

## 📁 Project Structure
```
padi-ai/
├── apps/
│   ├── web/          # Next.js frontend
│   └── api/          # FastAPI backend
├── docs/             # Strategy, Specs, Lifecycle, History (Moved from root)
├── packages/
│   ├── types/        # TypeScript shared types
│   ├── config/       # Shared configuration
│   └── ui/           # Shared UI components
└── ACTIVE_CONTEXT.md # CURRENT TASK AND TARGETS
```

## 📋 Common Tasks
```bash
pnpm dev             # Start dev server
pnpm docker:up       # Start infrastructure
pnpm test            # Run all tests
pnpm lint            # Run all linters
```

## 📖 Important Documents
- `docs/engineering/ENG-000-foundations.md` - Architecture & ADRs
- `docs/specs/04-prd-stage2.md` - Active Phase Requirements
- `ACTIVE_CONTEXT.md` - Current Task Status
