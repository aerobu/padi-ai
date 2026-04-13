# CLAUDE.md - PADI.AI Project Guidance

This project is an AI-powered adaptive math learning platform for Oregon elementary students (Grades 1-5, starting with Grade 4).

## Critical COPPA Compliance

**STUDENT FACING FEATURES:**
- ALWAYS use local Ollama models (Qwen2.5:72b, Qwen2.5:32b)
- NEVER send student data to cloud LLMs (Claude, OpenAI)
- Student responses must be processed locally before any cloud API calls

**ADMIN FEATURES:**
- Cloud LLMs (Claude Sonnet 4.6, o3-mini) can be used for:
  - Question generation (by teachers/admins)
  - Analytics aggregation (no PII)
  - Dashboard reporting (summarized only)

## Tech Stack

- **Frontend:** Next.js 15, React 19, TypeScript, Tailwind CSS
- **Backend:** Python 3.12, FastAPI, SQLAlchemy, Pydantic v2
- **AI/Agents:** LiteLLM, LangGraph (future), pyBKT (future)
- **Database:** PostgreSQL 17 + pgvector
- **Cache:** Redis 7
- **Auth:** Auth0 (COPPA-compliant)
- **Infra:** Docker, AWS (future), Vercel (frontend)

## Project Structure

```
padi-ai/
├── apps/
│   ├── web/          # Next.js frontend
│   │   ├── app/      # App Router pages
│   │   ├── components/
│   │   └── providers/
│   └── api/          # FastAPI backend
│       ├── src/
│       │   ├── core/        # config, security
│       │   ├── api/v1/      # API endpoints
│       │   └── clients/     # LLM client
├── packages/
│   ├── types/        # TypeScript shared types
│   ├── config/       # Shared configuration
│   └── ui/           # Shared UI components
└── infrastructure/
    └── docker/       # Docker Compose config
```

## Environment Variables

All 57+ environment variables are defined in `.env.example`. Key ones:

- `AUTH0_*`: Auth0 configuration for COPPA-compliant auth
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `LLM_ROUTING__TUTOR`: Always `ollama/qwen2.5:72b` (never override)
- `LLM_ROUTING__QUESTION_GEN`: `anthropic/claude-3-5-sonnet-20241022`

## Common Tasks

```bash
# Start dev server (all apps)
pnpm dev

# Start infrastructure (Postgres, Redis, Ollama)
pnpm docker:up

# Run backend API
cd apps/api && uvicorn src.main:app --reload

# Run frontend
cd apps/web && pnpm dev

# Run tests
pnpm test

# Run type checking
pnpm type-check

# Run lint
pnpm lint
```

## Implementation Guidelines

1. **For new API endpoints:**
   - Create in `apps/api/src/api/v1/`
   - Follow existing patterns in `health.py`
   - Use Pydantic v2 for request/response validation

2. **For new frontend components:**
   - Create in `packages/ui/` for shared components
   - Use `@padi/ui` import in Next.js
   - Follow Tailwind design system

3. **For new database models:**
   - Define in `packages/types/index.ts` (TypeScript)
   - Create SQLAlchemy model in `apps/api/src/models/`
   - Add to `eng-001-stage1.md` spec for Stage 1

## Important Files

- `ENG-000-foundations.md` - Architecture, ADRs, coding standards
- `ENG-001-stage1.md` - Stage 1 database schema and requirements
- `03-prd-stage1.md` - Stage 1 product requirements
- `.env.example` - All environment variable definitions

## References

- Next.js 15: https://nextjs.org/docs
- FastAPI: https://fastapi.tiangolo.com/
- Litellm: https://docs.litellm.ai/
- Auth0: https://auth0.com/
