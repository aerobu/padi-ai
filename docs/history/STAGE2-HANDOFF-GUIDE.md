# Stage 2 Handoff Guide for Qwen3.5
**Prepared:** 2026-04-17  
**Status:** Ready to Begin Implementation

---

## TL;DR

✅ **YES** — Extensive Stage 2 documentation exists and is 95% implementation-ready.

**8,098 lines of specifications** across 3 markdown files contain:
- Complete architecture diagrams
- 5 functional requirements (FR-6 through FR-10) with detailed algorithms
- Data models and API endpoints
- LLM prompt templates
- ~30 prerequisite relationship edges to seed
- Frontend mockups and component specs
- Performance SLAs and cost targets

**You can start building immediately** with only minor clarifications needed for non-blocking items (badge points, email templates, caching invalidation policy).

---

## Documentation Files to Read

### 1. **04-prd-stage2.md** (2,574 lines) — Start here
**What you need from this file:**
- Overview of what "personalized learning plan" means (section 2.1)
- All 5 functional requirements (FR-6 through FR-10)
- Data models for LearningPlan, Module, Lesson, PracticeSession
- Module name mappings (38 standards → child-friendly names)
- API endpoint signatures
- Success metrics and performance targets
- Dependencies on Stage 1 artifacts

**Read in order:**
1. Sections 2.1 (Overview & Objectives)
2. Section 2.2 (Functional Requirements) — all 5 of them
3. Section 2.4 (Data Models)
4. Section 2.5 (API Endpoints)

### 2. **ENG-002-stage2.md** (2,845 lines) — Technical deep-dive
**What you need from this file:**
- Architecture diagrams (C4 Level 1 & 2)
- Technology decisions (NetworkX, LangGraph, OpenAI vs Claude)
- Prerequisite relationships edge set (30+ edges with strength = required/recommended)
- Skill dependency graph implementation details
- LLM question generation pipeline
- Database migration checklist
- Performance benchmarks and monitoring

**Read sections:**
1. Section 1 (High-Level Architecture)
2. Section 2 (Skill Dependency Graph implementation)
3. Section 3 (LLM Question Generation)
4. Section 4 (Database migrations)
5. Section 5 (API & Frontend specs)

### 3. **11-lifecycle-stage2.md** (2,679 lines) — User flows
**What you need from this file:**
- End-to-end user flow diagrams (student → plan → practice → mastery)
- Parent onboarding journey
- Admin review queue workflow
- Badge and streak triggering events
- Error handling paths

**Read this after building the core, for integration testing.**

### 4. **ENG-000-foundations.md** — Architecture baseline
Reference for coding standards, directory structure, and design principles.

### 5. **ENG-MASTER-INDEX.md** — Cross-reference guide
Links to all other ENG documents.

---

## What You Need to Build (Execution Checklist)

### Phase 1: Data Layer (Days 1–3)
- [ ] Create Alembic migration for new tables:
  - `learning_plans` (1 per student, tied to assessment)
  - `plan_modules` (1+ per plan, one per skill)
  - `plan_lessons` (1–3 per module: intro/practice/challenge)
  - `practice_sessions` (created dynamically when lesson starts)
  - `badges` (achievement records)
  - `streaks` (daily practice tracking)
  - `prerequisite_relationships` seed data (30+ edges from ENG-002 section 2.4.3)

- [ ] Update SQLAlchemy models in `apps/api/src/models/models.py`

- [ ] Create repository layer classes:
  - `LearningPlanRepository`
  - `PlanModuleRepository`
  - `PlanLessonRepository`
  - `PracticeSessionRepository`

### Phase 2: Service Layer (Days 4–7)
- [ ] **SkillGraphService** — loads `prerequisite_relationships` into NetworkX DiGraph
  - Implement `topological_sort()` (FR-6.2)
  - Implement `priority_score()` (FR-6.3)
  - Implement `find_prerequisite_chain()` (FR-6.4)
  - Cache in memory, invalidate on admin changes

- [ ] **LearningPlanService** — generates and updates plans
  - Implement `generate_learning_plan()` (FR-7.1)
  - Implement `generate_learning_sequence()` (FR-6.6)
  - Implement `unlock_next_module()` when P(mastered) ≥ 0.85
  - Implement time-to-mastery estimation (FR-7.5 table)

- [ ] **BKTService** improvements (from Stage 1)
  - Add P(mastered) threshold logic for module advancement

### Phase 3: API Endpoints (Days 8–10)
Create `apps/api/src/api/v1/endpoints/learning_plans.py`:
- [ ] `POST /api/v1/learning-plans/generate-sequence` (FR-6.6)
- [ ] `GET /api/v1/learning-plans/{student_id}` — return plan with modules
- [ ] `GET /api/v1/learning-plans/{plan_id}/next-lesson` — unlock lesson
- [ ] `POST /api/v1/practice-sessions/start` — create practice session
- [ ] `POST /api/v1/practice-sessions/{session_id}/complete` — update BKT, unlock next

Also needed (in `questions.py` or new `question_generation.py`):
- [ ] `POST /api/v1/questions/generate-batch` — async job dispatcher (LLM)
- [ ] `POST /api/v1/questions/{question_id}/validate` — manual review

And admin/analytics:
- [ ] `GET /api/v1/admin/skill-graph` — visualize DAG
- [ ] `GET /api/v1/admin/generation-jobs` — view LLM job queue
- [ ] `GET /api/v1/admin/review-queue` — content reviewer queue

### Phase 4: LLM Question Generation (Days 11–14)
- [ ] Implement `LLMQuestionGenerator` service
  - Use OpenAI o3-mini for math questions (FR-8)
  - Use Claude 4.6 for age-appropriateness validation
  - Parse structured JSON output (question, options, correct_answer, explanation)
  - Validate against criteria (grade-level, clarity, correctness)
  - Track cost per question (target ≤ $0.05)

- [ ] Set up async job queue (Celery + Redis or LangGraph agent)
  - Batch generate 100+ questions per run
  - Retry failed validations with different LLM
  - Store generation metadata (model, cost, validation_status)

### Phase 5: Frontend — Student Dashboard (Days 15–17)
Create `apps/web/app/(dashboard)/learning-plan/page.tsx`:
- [ ] Display learning plan (all modules with status)
- [ ] Show current module/lesson (if in_progress)
- [ ] Display "Start Lesson" button for available modules
- [ ] Show streak counter (consecutive days practiced)
- [ ] Show earned badges with animation

Create lesson start flow:
- [ ] `apps/web/app/(dashboard)/[studentId]/lesson/[lessonId]/page.tsx`
- [ ] Launch practice session
- [ ] Display 10–15 questions in CAT format
- [ ] Capture responses

### Phase 6: Frontend — Parent Dashboard (Days 18–20)
Create `apps/web/app/(dashboard)/parent/page.tsx`:
- [ ] Child selector (if multiple students)
- [ ] Learning plan summary (all modules, current progress)
- [ ] Time-to-mastery estimates (from FR-7.5)
- [ ] Module completion % bar chart
- [ ] Time trend (estimated completion date)
- [ ] Recent activity log

### Phase 7: Tests & Performance (Days 21–23)
- [ ] Unit tests for SkillGraphService (topological sort, prerequisite chains)
- [ ] Integration tests for learning plan generation (BKT state → plan)
- [ ] Performance tests: plan generation < 5 sec (FR benchmark)
- [ ] Dashboard load time < 2 sec P95
- [ ] E2E test: full flow (diagnostic → plan → lesson → badge award)

### Phase 8: Admin & Content Review UI (Days 24–25)
- [ ] Skill graph visualization (admin/skill-graph)
- [ ] Generation job monitoring dashboard
- [ ] Content review queue with approve/reject

---

## Critical Data You Need to Seed

### prerequisite_relationships (30+ edges)

From ENG-002 section 2.4.3, here are the key edges to seed:

```python
# Grade 3 → Grade 4 prerequisites (required)
prerequisites = [
    ("3.OA.C.7", "4.OA.A.1"),  # mult facts → comparisons
    ("3.OA.C.7", "4.OA.B.4"),  # mult facts → factors
    ("3.OA.C.7", "4.NBT.B.5"), # mult facts → multi-digit mult
    ("3.NBT.A.2", "4.NBT.B.4"), # add/sub → large number add/sub
    ("3.NF.A.1", "4.NF.A.1"),  # frac intro → equiv fracs
    ("3.NF.A.3", "4.NF.A.2"),  # comparing fracs → diff denominators
    # ... 24+ more (all listed in ENG-002)
]

# Grade 4 internal prerequisites (recommended/required)
# E.g., place value before multi-digit operations
prerequisites.extend([
    ("4.NBT.A.1", "4.NBT.B.5"),  # place value → multi-digit mult
    ("4.NBT.A.3", "4.NBT.B.6"),  # rounding → division
    # ... more
])
```

Create a migration script to seed these. **This is CRITICAL** — the entire skill graph depends on it.

---

## Non-Blocking Clarifications Needed (Ask if you get stuck)

These don't need answers NOW; clarify during implementation as needed:

1. **Badge points**: How many XP per badge type? (FR-9)
   - Module completion: ? points
   - Streak milestone (5 days): ? points
   - Perfect lesson (100% correct): ? points
   
2. **Parent email notifications**: When to notify?
   - Plan generated?
   - Module mastered?
   - Streak broken?
   - Weekly summary?

3. **Caching invalidation for skill graph**: How to signal updates?
   - Admin UI updates prerequisites → publish Redis event?
   - Subscribers (services) rebuild graph?

4. **Question review queue**: Who reviews? How fast?
   - SLA for human review?
   - Auto-reject criteria?
   - How many reviewers in pilot?

5. **Mobile responsiveness**: Desktop-first design in spec, but also need mobile?

---

## Stage 1 Artifacts Available to You

- ✅ `standards` table (38 Oregon Grade 3–4 standards, seeded)
- ✅ `prerequisite_relationships` table (exists, needs your seed data)
- ✅ `student_skill_states` table (BKT P(mastered) per student)
- ✅ `assessments` table (diagnostic results)
- ✅ `questions` table (20 seed questions; you'll generate 5,000+)
- ✅ Auth0 authentication (working)
- ✅ Encryption service (for PII)
- ✅ SES email client (for notifications)

All foundational services from Stage 1 are ready to use.

---

## Technology Stack You'll Use

**Backend additions:**
- `networkx>=3.0` — skill dependency graph
- `langgraph>=0.2` — LLM question generation agent/workflow
- `openai>=1.3.0` — o3-mini for question generation
- `anthropic>=0.7.0` — Claude Sonnet for validation

**Frontend additions:**
- `recharts` — charts for parent dashboard (progress bars, trend lines)
- `react-confetti` — badge award animation 🎉
- `date-fns` — time-to-mastery countdown

All are low-risk, well-maintained libraries.

---

## Success Criteria for Handoff

You're done with Stage 2 when:

- [ ] `pytest tests/ -v` — all Stage 1 tests + new Stage 2 tests pass
- [ ] Diagnostic → Learning plan generation works end-to-end (< 5 sec)
- [ ] Student can start a lesson, answer 10 questions, see BKT update
- [ ] Next module unlocks when current module reaches P(mastered) ≥ 0.85
- [ ] Parent dashboard shows plan with time-to-completion estimate
- [ ] 100+ questions generated via LLM and validated
- [ ] Skill graph topological sort verified (prerequisites always before dependents)
- [ ] Dashboard loads in < 2 sec (P95)
- [ ] Badge awarded on module completion (animated celebration)
- [ ] Streak counter accurate (daily practice tracking)

---

## Questions for Qwen Before You Start

1. Should `plan_lessons` be pre-computed (3 lessons per module in plan) or created dynamically?
   - **Recommendation**: Pre-compute at plan generation (FR-7.1), avoid runtime complexity.

2. Should the prerequisite graph be rebuilt on every request or cached?
   - **Recommendation**: Cache in memory (module-level singleton), invalidate on admin action via Redis event.

3. For LLM question generation, should you use Celery task queue or LangGraph?
   - **Recommendation**: LangGraph (it's already in tech stack). 1-3 agents: (1) generate, (2) auto-validate, (3) escalate-to-human.

---

## Ready to Begin?

1. Read **04-prd-stage2.md** (sections 2.1, 2.2, 2.4, 2.5)
2. Read **ENG-002-stage2.md** (sections 1, 2, 3, 4)
3. Create database migration file
4. Implement SkillGraphService
5. Implement LearningPlanService
6. Build API endpoints
7. Build frontend dashboards

**Estimated duration:** 5–6 weeks (120–160 agent-hours as per spec)

Good luck! 🚀
