# MathPath Oregon — SDLC Lifecycle Document
## Stage 2: Personalized Learning Plan Generator + AI Question Generation Pipeline
### Months 4–6 | Document Version 1.0 | Status: Final

---

## Table of Contents

1. [Architecture Review](#1-architecture-review)
   - 1.1 Component Overview
   - 1.2 Data Flow Diagrams
   - 1.3 Key Architectural Decisions
   - 1.4 Integration with Stage 1
   - 1.5 Risk Areas and Mitigation
   - 1.6 Performance and Scalability
2. [User Story Breakup](#2-user-story-breakup)
   - Epic A: Skill Dependency Graph Engine (FR-6)
   - Epic B: Learning Plan Generation (FR-7)
   - Epic C: AI Question Generation Pipeline (FR-8)
   - Epic D: Student Dashboard (FR-9)
   - Epic E: Parent Dashboard (FR-10)
3. [Detailed Test Plan](#3-detailed-test-plan)
   - 3.1 Unit Tests
   - 3.2 Integration Tests
   - 3.3 End-to-End Tests (Playwright)
   - 3.4 Behavioral / BDD Tests
   - 3.5 Robustness & Resilience Tests
   - 3.6 Repeatability Tests
   - 3.7 Security Tests
   - 3.8 LLM Behavioral Contract Tests
   - 3.9 Baseline Acceptance Criteria
4. [Operations Plan](#4-operations-plan)
   - 4.1 MLOps
   - 4.2 FinOps
   - 4.3 SecOps
   - 4.4 DevSecOps Pipeline
5. [Manual QA Plan](#5-manual-qa-plan)

---

## 1. Architecture Review

**Stage 2 Solo Development Total Estimate:** 110–155 agent-hours | Calendar: 5–6 months (optimistic) to 6–7 months (realistic)

### 1.1 Component Overview

Stage 2 introduces four major subsystems layered on top of Stage 1's standards database, diagnostic engine, and Auth0-secured authentication: the **Skill Dependency Graph Engine**, the **Learning Plan Generator**, the **LangGraph Question Generation Pipeline**, and the **Student/Parent Dashboard layer**. These form a complete end-to-end adaptive loop: Diagnostic → Plan → Practice Supply Chain.

#### C4 Level 1 — System Context (Stage 2 Additions)

```
┌───────────────────────────────────────────────────────────────────┐
│                      EXTERNAL ACTORS                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────────────┐     │
│  │  Parent  │  │ Student  │  │  Admin   │  │ Content       │     │
│  │(Browser) │  │(Browser) │  │(Browser) │  │ Reviewer      │     │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └──────┬────────┘     │
└───────┼─────────────┼─────────────┼────────────────┼─────────────┘
        │ HTTPS       │ HTTPS       │ HTTPS          │ HTTPS
        ▼             ▼             ▼                ▼
┌───────────────────────────────────────────────────────────────────┐
│            MATHPATH OREGON SYSTEM BOUNDARY (Stage 2)              │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │            Next.js 15 Web App (Vercel)                      │  │
│  │  NEW: Student dashboard • Parent dashboard • Admin gen jobs  │  │
│  │       Admin review queue • Skill graph editor               │  │
│  └─────────────────────┬───────────────────────────────────────┘  │
│                        │ HTTPS/REST                               │
│  ┌─────────────────────▼───────────────────────────────────────┐  │
│  │           FastAPI API Server (ECS Fargate)                  │  │
│  │  NEW: /skill-graph • /learning-plans • /admin/gen-jobs      │  │
│  │       /admin/review-queue • /students/{id}/badges • /streak │  │
│  └──────────┬────────────┬─────────────┬──────────────────────┘  │
│             │            │             │                          │
│  ┌──────────▼──┐ ┌───────▼──┐  ┌───────▼──────────────────┐      │
│  │PostgreSQL 17│ │  Redis 7 │  │ LangGraph 0.2 Worker      │      │
│  │+ pgvector   │ │ElastiCache│  │ (ECS Fargate — NEW)       │      │
│  │+ ltree      │ │           │  │ Polls gen queue → o3-mini │      │
│  └─────────────┘ └───────────┘  └──────────┬───────────────┘      │
└───────────────────────────────────────────┼─────────────────────┘
          │           │                     │           │
    ┌─────▼──┐  ┌─────▼──┐  ┌──────────────▼─┐  ┌─────▼──────────┐
    │ Auth0  │  │AWS SES  │  │  OpenAI o3-mini │  │Anthropic       │
    │        │  │(Weekly  │  │  (Question gen) │  │Claude Sonnet   │
    │        │  │ email)  │  │                 │  │4.6 (Safety)    │
    └────────┘  └────────┘  └─────────────────┘  └────────────────┘
```

#### Component Inventory

| Component | Location | Language/Framework | New in Stage 2? |
|---|---|---|---|
| SkillGraphService | `apps/api/src/service/skill_graph_service.py` | Python / NetworkX 3.x | Yes |
| SkillGraphRepo | `apps/api/src/repository/skill_graph_repo.py` | Python / SQLAlchemy 2.0 | Yes |
| LearningPlanService | `apps/api/src/service/learning_plan_service.py` | Python / FastAPI | Yes |
| LearningPlanRepo | `apps/api/src/repository/learning_plan_repo.py` | Python / SQLAlchemy 2.0 | Yes |
| QuestionGenerationService | `apps/api/src/service/question_generation_service.py` | Python / Celery | Yes |
| LangGraph Worker | `services/question-generator/src/generator.py` | Python / LangGraph 0.2 | Yes |
| ValidationPipeline | `services/question-generator/src/validators.py` | Python | Yes |
| BadgeService | `apps/api/src/service/badge_service.py` | Python | Yes |
| StreakService | `apps/api/src/service/streak_service.py` | Python | Yes |
| ReviewQueueService | `apps/api/src/service/review_service.py` | Python | Yes |
| Student Dashboard | `apps/web/src/app/(student)/students/[id]/page.tsx` | TypeScript / React 19 | Yes |
| Learning Plan View | `apps/web/src/app/(student)/students/[id]/learning-plan/page.tsx` | TypeScript / Next.js 15 | Yes |
| Parent Dashboard | `apps/web/src/app/(parent)/overview/page.tsx` | TypeScript / React 19 | Yes |
| LearningPlanStore | `apps/web/src/stores/learning-plan-store.ts` | TypeScript / Zustand | Yes |
| Skill Graph Editor | `apps/web/src/app/(admin)/skill-graph/page.tsx` | TypeScript / D3.js | Yes |
| Generation Jobs Admin | `apps/web/src/app/(admin)/generation-jobs/page.tsx` | TypeScript / React 19 | Yes |
| NetworkX DiGraph cache | In-memory singleton, rebuilt from `skill_dependency_graph_edges` | Python | Yes |

#### New Database Tables (Stage 2)

| Table | Purpose | Key Constraints |
|---|---|---|
| `skill_dependency_graph_edges` | DAG edges; `from_standard → to_standard` with `edge_type`, `weight` | `UNIQUE(from_standard, to_standard, edge_type)`, no self-loops, ltree indexes |
| `learning_plans` | One active plan per student | `UNIQUE INDEX WHERE status = 'active'` on `student_id` |
| `plan_modules` | Ordered modules within a plan | `UNIQUE(plan_id, sequence_order)`, `UNIQUE(plan_id, standard_code)` |
| `plan_lessons` | Intro/Practice/Challenge lessons per module | `UNIQUE(module_id, lesson_number)` |
| `generation_jobs` | AI question generation job queue | Status FSM: queued→running→completed/failed |
| `generated_questions` | Draft questions from pipeline (pre-promotion) | pgvector `VECTOR(1536)` for dedup |
| `question_validation_results` | Per-question step-by-step validation audit trail | FK → `generated_questions` |
| `content_review_queue` | Human review queue for borderline questions | Priority queue; `status IN ('pending','in_review','approved','rejected')` |
| `student_badges` | Earned gamification badges | `UNIQUE(student_id, badge_type)` prevents duplicate awards |
| `student_streaks` | Daily practice streak tracking | One row per student; updated on session completion |

---

### 1.2 Data Flow Diagrams

#### Flow A: Learning Plan Generation (< 5 seconds end-to-end)

```
diagnostic_completed event (Redis Stream)
          │
          ▼
LearningPlanService.generate_learning_plan(student_id)
    │
    ├─► [1] SELECT * FROM student_skill_states WHERE student_id = ?
    │         (BKT p_mastered for all 38 standards)
    │
    ├─► [2] get_skill_graph()
    │         (NetworkX DiGraph singleton; cached in Redis `graph:v1` for 1h)
    │
    ├─► [3] determine_track(skill_states)
    │         catch_up (≥40% Below Par) / on_track / accelerate (≥70% Above Par)
    │
    ├─► [4] get_topological_sequence(G, non_mastered_codes)
    │         Kahn's algorithm → stable topological order; prerequisites first
    │
    ├─► [5] compute_priority_scores(sorted_codes, p_mastered_map, G)
    │         centrality × 10 + (1 - p_mastered) × 20 + grade_bonus
    │
    ├─► [6] INSERT INTO learning_plans (track, status, estimated_weeks, ...)
    │
    ├─► [7] INSERT INTO plan_modules (one per non-mastered skill, status=locked/available)
    │
    ├─► [8] INSERT INTO plan_lessons (intro/practice/challenge for first available module)
    │
    ├─► [9] SET Redis `plan:{student_id}:current` → serialized plan JSON (TTL 3600s)
    │
    └─► [10] XADD `mathpath:events` plan_generated → badge worker + notification worker
```

#### Flow B: AI Question Generation Pipeline (LangGraph 0.2)

```
Admin → POST /admin/generation-jobs  { standard_code, count, difficulties }
                │
                ▼
        INSERT generation_jobs (status='queued')
        LPUSH Redis queue `mathpath:gen:queue` job_id
                │
                ▼
     LangGraph Worker (ECS Task) — BLPOP queue
                │
                ▼
    FOR EACH (difficulty, theme) in job spec:
    ┌────────────────────────────────────────────────────────────┐
    │ Node 1: BUILD_PROMPT                                       │
    │   Fill question_gen_v1.0.jinja2 with:                     │
    │   standard_code, description, difficulty, dok_level,       │
    │   question_type, context_theme, Oregon context             │
    │                                                            │
    │ Node 2: LLM_GENERATE (o3-mini structured output)          │
    │   response_format: { type: 'json_schema', QuestionSchema } │
    │   → stem, options[4], correct_answer, solution_code, etc. │
    │                                                            │
    │ Node 3: EXECUTE_SANDBOX                                    │
    │   subprocess.run(solution_code, timeout=10s, env={})       │
    │   PASS: stdout matches correct_answer                      │
    │   FAIL: mark validation_failed → continue                  │
    │                                                            │
    │ Node 4a: CLASSIFY_QUALITY (sync Python)                    │
    │   • Flesch-Kincaid Grade 2.5–5.5                          │
    │   • Word count in range for context_type                   │
    │   • Keyword blocklist (prohibited content)                  │
    │   • MC: exactly 1 correct answer, distractors ≠ correct   │
    │   • Solution steps 1–5                                     │
    │                                                            │
    │ Node 4b: VERIFY_ALIGNMENT (Claude Haiku, async)           │
    │   "Does this question test {standard_code}?"               │
    │   confidence ≥ 0.85 → auto-approve; < 0.85 → human review │
    │                                                            │
    │ Node 4c: SAFETY_CHECK (Claude Haiku, async, parallel 4b)  │
    │   Check for bias, inappropriate themes, stereotypes        │
    │                                                            │
    │ Node 5: DEDUP_CHECK (pgvector)                             │
    │   embed(stem) → cosine similarity vs all same-standard Qs │
    │   > 0.92 similarity → discard as near-duplicate            │
    │                                                            │
    │ Node 6: STORE                                              │
    │   confidence = exec*0.4 + age*0.2 + dedup*0.2 + math*0.2  │
    │   ≥ 0.85 → INSERT questions (auto-approved)               │
    │   < 0.85 → INSERT content_review_queue (human review)     │
    └────────────────────────────────────────────────────────────┘
                │
                ▼
     UPDATE generation_jobs status='completed'
     results: { total, auto_approved, needs_review, failed }
```

#### Flow C: Badge Award (Event-Driven, < 2 seconds)

```
practice_session.completed event (Redis Stream `mathpath:events`)
          │
          ▼
    BadgeWorker.check_and_award(student_id, event_payload)
          │
          ├─► check first_session: sessions_completed == 1?
          ├─► check first_mastery: modules_mastered == 1?
          ├─► check streak_N: current_streak in [3, 7, 14]?
          ├─► check perfect_session: accuracy == 1.0?
          ├─► check fast_learner: mastered in ≤ 2 sessions?
          │
          ▼
    INSERT INTO student_badges (student_id, badge_type, ...)
    ON CONFLICT (student_id, badge_type) DO NOTHING   ← idempotent
          │
          ▼
    XADD `mathpath:events` badge_earned
    SET Redis `badges:{student_id}:pending` badge_ids (TTL 3600s)
```

---

### 1.3 Key Architectural Decisions

#### ADR-2.1: NetworkX In-Memory DAG vs. Pure SQL Graph Traversal

**Decision**: Load the skill dependency graph into a NetworkX `DiGraph` singleton cached in application memory (with a Redis-backed invalidation signal), rather than performing graph traversal queries in SQL.

**Rationale**: The graph is tiny (≤ 38 nodes, ≤ 35 edges at Stage 2). NetworkX topological sort runs in O(V + E) ≈ microseconds in memory. A SQL recursive CTE approach (using ltree or `WITH RECURSIVE`) adds database round-trips and query planning overhead that would hurt the ≤ 5 second plan generation SLA. The ltree column on `skill_dependency_graph_edges` remains for admin querying and audit but is not in the hot path.

**Trade-off accepted**: Memory synchronization across multiple ECS API tasks. Mitigated by publishing a Redis `graph:invalidated` signal when admin edits edges; each API task rebuilds on next request after signal receipt.

#### ADR-2.2: LangGraph Worker as Separate ECS Task

**Decision**: The question generation pipeline runs as a dedicated `services/question-generator` ECS Fargate task rather than being embedded in the main API server.

**Rationale**: Generation is CPU/IO-intensive (subprocess sandboxing, multiple LLM calls per question), non-interactive (no user waiting for response), and requires independent scaling (burst on nights/weekends without affecting API SLA). Isolation also constrains LLM cost: the worker can be stopped immediately if daily spend approaches budget hard-stop.

**Trade-off accepted**: Operational complexity of two ECS services. Mitigated by shared Docker base image and unified GitHub Actions CI pipeline.

#### ADR-2.3: Celery + Redis vs. AWS SQS for Job Queue

**Decision**: Use Redis (same ElastiCache instance as the app cache) as the Celery broker for question generation jobs, not AWS SQS.

**Rationale**: Avoids SQS message visibility timeout complexity during long-running validation steps (up to 25 seconds/question). Redis BLPOP gives deterministic pop semantics. Stage 5 may migrate to SQS for durability guarantees at scale.

**Trade-off accepted**: Redis is not infinitely durable; job queue survives restart via AOF persistence. Job state also persisted in PostgreSQL `generation_jobs` table, providing recovery path.

#### ADR-2.4: Program of Thought (PoT) for Answer Verification

**Decision**: Require o3-mini to generate a Python `solution_code` field alongside every question, then execute it in a sandbox to verify correctness, rather than asking a second LLM to verify the answer.

**Rationale**: Programmatic verification is deterministic, cheap (no extra LLM call), and eliminates a class of subtle math errors. PoT is well-suited to elementary math (exact integer/fraction arithmetic). The sandbox uses `subprocess.run()` with `env={}` (no environment variables), `timeout=10s`, and restricted builtins — no network or filesystem access.

**Trade-off accepted**: Questions that require geometric reasoning or visual interpretation cannot have Python verification. These are flagged as `solution_code = NULL` and routed to human review queue unconditionally.

#### ADR-2.5: Confidence Score Gate (0.85) for Auto-Approval

**Decision**: Questions that pass all automated checks with aggregate confidence ≥ 0.85 are auto-promoted to the live `questions` table. Below 0.85, they wait in `content_review_queue`.

**Rationale**: Targeting ≥ 85% auto-approval rate (per NFR). At 5,000 question target, this means ≤ 750 questions need human review — manageable for a part-time content reviewer. Setting the gate too high wastes reviewer time on clearly good questions; too low risks math errors reaching students.

#### ADR-2.6: pgvector Deduplication with all-MiniLM-L6-v2

**Decision**: Embed question stems using `all-MiniLM-L6-v2` (384 dimensions) and use pgvector cosine similarity for near-duplicate detection (threshold: 0.92).

**Rationale**: Prevents the LLM from generating semantically identical questions for the same standard (observed in testing). The small embedding model runs in < 100ms locally, avoiding another LLM API call. The 0.92 threshold is empirically calibrated to flag near-duplicates without rejecting legitimately different questions about the same concept.

---

### 1.4 Integration with Stage 1

Stage 2 has hard dependencies on the following Stage 1 artifacts:

| Stage 1 Artifact | Stage 2 Dependency | Verified By |
|---|---|---|
| `standards` table (38 rows: 9 Grade 3 + 29 Grade 4) | Graph nodes loaded into `build_skill_graph()` | `test_graph_loads_all_38_standards` |
| `prerequisite_relationships` table (30 edges) | Graph edges; topological sort basis | `test_dag_has_no_cycles` |
| `student_skill_states` with BKT state | Seed for `generate_learning_plan()` | `test_plan_generation_uses_bkt_states` |
| `assessments` table with `diagnostic_completed` event | Plan generation trigger | `test_plan_generated_on_diagnostic_complete` |
| `questions` table (142 seed questions) | Template schema for `generated_questions` | DB migration contract test |
| Parent/student Auth0 sessions | Dashboard authentication | E2E auth flow tests |

The Stage 2 codebase reads but never writes to Stage 1 tables (except `students.diagnostic_status` which is updated to `'COMPLETED'` by plan generation). All Stage 2 schema additions are additive migrations; rolling back Stage 2 leaves Stage 1 fully intact.

---

### 1.5 Risk Areas and Mitigation

| Risk | Severity | Probability | Mitigation |
|---|---|---|---|
| LLM cost overrun: o3-mini pricing increases or generation volume spikes | High | Medium | Hard daily budget stop at $10 (Redis counter); weekly FinOps review; three-tier model strategy (use Haiku for classification calls) |
| Question quality degradation: model produces math errors at scale | High | Medium | Programmatic PoT execution verification; LLM alignment check; 15% human review queue; weekly golden set regression tests |
| Plan generation > 5 second SLA | Medium | Low | Graph traversal is O(V+E) with V≈38; cached singleton; benchmark enforced by CI performance gate |
| pgvector dedup threshold miscalibration (too aggressive/lenient) | Medium | Medium | Threshold A/B tested on 200 seed questions; adjusted during Month 4 calibration sprint; monitored via `duplicate_rate` metric |
| LangGraph Worker ECS task instability | Medium | Low | Celery retry logic (max_retries=2); dead-letter job queue; generation_jobs table as recovery source; health endpoint monitored by Datadog |
| Streak tracking timezone bugs (Pacific Time boundary) | Medium | Medium | All streak calculations in `pytz.timezone('America/Los_Angeles')`; mutation tests on streak logic; dedicated robustness test suite |
| Student data in dashboards exposed to wrong parent | High | Low | Row-level security in PostgreSQL; all student queries filtered by `parent_id`; Auth0 RBAC claims verified on every request |
| COPPA violation via student PII in LLM prompts | Critical | Low | Question generation prompts contain ONLY standard codes and math content — no student identifiers; PII scrubbing middleware on all LLM inputs |

---

### 1.6 Performance and Scalability Considerations

| Metric | Target | Architecture Mechanism |
|---|---|---|
| Learning plan generation P95 | < 5 seconds | In-memory graph, single DB transaction for plan write, Redis cache for subsequent reads |
| Student dashboard load P95 | < 2 seconds | Server-side rendering (Next.js SSR) + Redis plan cache with 60s TTL |
| Parent dashboard load P95 | < 2 seconds | Aggregated progress queries indexed on `(student_id, status)` |
| Question generation throughput | ≥ 100 validated/hour | 4 parallel Celery workers; pipeline ≤ 25s/question → ~600/hour at 4 workers |
| Module re-sequencing after session | < 1 second | O(V+E) graph traversal, V≈38 nodes; no database round-trip for sort |
| Badge award latency | < 2 seconds | Redis Streams consumer; badge check is single indexed SELECT |
| pgvector dedup search | < 200ms | IVFFlat index with lists=50 (grows to lists=100 at 5K questions) |
| Daily LLM spend hard stop | $10/day | Redis atomic counter; Celery worker checks before each API call |

At 50 concurrent pilot students, the ECS API task is not a bottleneck (plan generation and dashboard loads are lightweight read-heavy operations). The LangGraph Worker scales independently — additional ECS tasks can be added by increasing Celery concurrency setting without API changes.

---

## 2. User Story Breakup

Stories derived from PRD Section 2.2 (FR-6 through FR-10). Priority levels: P0 = must-have for Stage 2 launch; P1 = high value; P2 = nice to have; P3 = deferred to Stage 3.

---

### Epic A: Skill Dependency Graph Engine (FR-6)

**Solo Development Estimate:** 25–35 agent-hours | Calendar: ~3–4 weeks

**Epic Goal**: Build a reliable, in-memory directed acyclic graph (DAG) of Oregon Grade 3/4 math skill prerequisites that serves as the sequencing backbone for all learning plans.

---

**US-A1: Load Dependency Graph from Database**

| Field | Value |
|---|---|
| ID | US-A1 |
| Title | Load skill dependency graph from PostgreSQL into NetworkX |
| As a | Backend system (plan generator) |
| I want | A singleton NetworkX DiGraph loaded from `skill_dependency_graph_edges` |
| So that | Plan generation can perform graph traversal without database round-trips in the hot path |
| Priority | P0 |
| Story Points | 3 |
| Dependencies | Stage 1: `standards` table populated; `skill_dependency_graph_edges` seeded with 30+ edges |

**Acceptance Criteria:**
- Given the database has 38 standard nodes and 30 prerequisite edges seeded, when `build_skill_graph(db)` is called, then a NetworkX `DiGraph` is returned with exactly 38 nodes and exactly N edges matching the database rows.
- Given the graph is loaded, when `nx.is_directed_acyclic_graph(G)` is called, then it returns `True` (no cycles).
- Given admin adds a new prerequisite edge via API, when the Redis `graph:invalidated` signal is published, then the next call to `get_skill_graph()` triggers a rebuild from the database.
- Given a database connection failure during graph rebuild, when the error is caught, the existing cached graph continues to serve requests and the error is logged to Datadog with `graph.load.failure` metric.
- The graph singleton must load in < 500ms from cold start.

---

**US-A2: Topological Sort for Learning Sequence**

| Field | Value |
|---|---|
| ID | US-A2 |
| Title | Topological sort of non-mastered skills using Kahn's algorithm |
| As a | Learning plan generator |
| I want | An ordered list of skills to work on with prerequisites guaranteed to appear before dependents |
| So that | Students never encounter a skill before its foundation is built |
| Priority | P0 |
| Story Points | 5 |
| Dependencies | US-A1 |

**Acceptance Criteria:**
- Given student needs skills `[4.NBT.B.5, 3.OA.C.7]`, when `get_topological_sequence(G, codes)` is called, then `3.OA.C.7` appears before `4.NBT.B.5` in the result (prerequisite ordering enforced).
- Given a student who has mastered all Grade 3 prerequisites (P(mastered) ≥ 0.85), when sequencing is run, then no Grade 3 standards appear in the returned list.
- Given a student on the Catch Up track with 5 below-par Grade 3 prerequisites, when sequencing is run, then all 5 appear contiguously at the front of the sequence, before any Grade 4 content.
- Given two skills at the same topological level (no ordering dependency between them), when sequencing is run, then the skill with the higher centrality score (more dependents) appears first.
- The sort must produce a stable, deterministic order: identical inputs yield identical outputs across multiple invocations.
- `get_topological_sequence()` must complete in < 10ms for any valid input (V ≤ 38, E ≤ 35).

---

**US-A3: Priority Scoring for Skill Urgency**

| Field | Value |
|---|---|
| ID | US-A3 |
| Title | Compute composite priority score for each non-mastered skill |
| As a | Learning plan generator |
| I want | Each non-mastered skill ranked by a composite urgency score (centrality + deficiency + grade bonus) |
| So that | The most foundational and most deficient skills are addressed first within each topological level |
| Priority | P0 |
| Story Points | 3 |
| Dependencies | US-A1 |

**Acceptance Criteria:**
- Given skill `3.OA.C.7` (multiplication facts, Grade 3, high out-degree = 5) with P(mastered)=0.10, when `compute_priority_score()` is called, then the score > any Grade 4 skill with P(mastered)=0.10 and out-degree=1.
- The Grade 3 prerequisite bonus (+5) is only applied to skills in the `standards` table where `grade = 3`.
- Given two skills with identical centrality and grade level, the skill with lower P(mastered) gets a higher priority score.
- Priority scores are recalculated on each plan generation (not cached between students).
- `rank_skills_by_priority()` excludes skills with `p_mastered >= 0.85`.

---

**US-A4: Prerequisite Chain Detection (Remediation Chain)**

| Field | Value |
|---|---|
| ID | US-A4 |
| Title | Trace prerequisite chain for a failed Grade 4 standard |
| As a | Learning plan generator |
| I want | Given a failed Grade 4 skill, a complete ordered list of prerequisite skills also below mastery |
| So that | Remediation begins at the deepest root cause, not superficially at the Grade 4 level |
| Priority | P0 |
| Story Points | 3 |
| Dependencies | US-A1 |

**Acceptance Criteria:**
- Given student fails `4.NBT.B.5` (multi-digit multiplication) and has `3.OA.C.7` below mastery, when `get_remediation_chain('4.NBT.B.5', skill_states, G)` is called, then `3.OA.C.7` appears in the result before `4.NBT.B.5`.
- Given all predecessors of a failed skill are above mastery threshold (0.85), when remediation chain is computed, then only the failed skill itself is in the result.
- Given a cycle (should not exist — caught by DAG validation), when remediation chain is computed, the `visited` set prevents infinite recursion.
- The function handles missing skill states gracefully (default P(mastered)=0.5 for unknown skills).

---

**US-A5: Partial Completion Re-Sequencing**

| Field | Value |
|---|---|
| ID | US-A5 |
| Title | Dynamic re-sequencing of learning plan after each practice session |
| As a | Learning plan system |
| I want | The plan module order to update dynamically as student BKT states change |
| So that | Newly mastered prerequisites unlock dependent modules in real time |
| Priority | P0 |
| Story Points | 5 |
| Dependencies | US-A1, US-A2; Stage 1: BKT update pipeline |

**Acceptance Criteria:**
- Given a student completes a practice session and BKT P(mastered) crosses 0.85, when re-sequencing runs, then the newly mastered module's status is updated to `mastered` in `plan_modules` and dependent modules transition from `locked` to `available`.
- Re-sequencing completes in < 1 second (verifiable by timing log in Datadog).
- Given a skill that regresses (BKT P(mastered) drops below 0.85 due to incorrect answers), when re-sequencing runs, the skill is re-inserted into the plan at the appropriate topological position.
- A `module_unlocked` event is published to Redis Streams when a module transitions from `locked` to `available`.
- The `plan_modules` table is updated atomically in a single database transaction.

---

**US-A6: Admin Skill Graph Editor**

| Field | Value |
|---|---|
| ID | US-A6 |
| Title | Interactive D3.js skill graph visualization and edge editor for admins |
| As an | Admin |
| I want | A visual editor where I can see and modify prerequisite relationships between standards |
| So that | Curriculum experts can tune the dependency graph without writing SQL |
| Priority | P1 |
| Story Points | 8 |
| Dependencies | US-A1 |

**Acceptance Criteria:**
- Given an admin navigates to `/admin/skill-graph`, the force-directed D3 graph renders with all 38 standard nodes and prerequisite edges within 2 seconds.
- Admin can click an edge to see its properties (edge_type, weight, source).
- Admin can add a new edge by drag-and-drop between nodes; the new edge is validated for cycle introduction before saving (POST `/api/v1/skill-graph/edges`).
- If adding an edge would create a cycle, the API returns HTTP 409 Conflict with error message and the edge is not saved.
- After any edge change, the Redis `graph:invalidated` signal is published automatically.
- Admin actions are logged to the audit log.

---

### Epic B: Learning Plan Generation (FR-7)

**Solo Development Estimate:** 30–40 agent-hours | Calendar: ~3–5 weeks

**Epic Goal**: Automatically generate a structured, dependency-respecting, BKT-calibrated learning plan within 5 seconds of diagnostic completion, covering the full Plan → Module → Lesson → Session hierarchy.

---

**US-B1: End-to-End Learning Plan Generation**

| Field | Value |
|---|---|
| ID | US-B1 |
| Title | Automatically generate full learning plan on diagnostic completion |
| As a | Parent |
| I want | A complete personalized learning plan generated automatically when my child finishes the diagnostic |
| So that | We can start practicing immediately without manual setup |
| Priority | P0 |
| Story Points | 13 |
| Dependencies | US-A1, US-A2, US-A3; Stage 1: diagnostic completion pipeline |

**Acceptance Criteria:**
- Given a student completes the diagnostic, when the `diagnostic_completed` event is consumed, then a complete learning plan (plan record + all module records + first module lessons) is persisted to the database within 5 seconds (P95).
- The generated plan contains exactly the non-mastered skills in topological order.
- The plan track is correctly assigned: `catch_up` if ≥ 40% of assessed skills Below Par; `accelerate` if ≥ 70% Above Par; `on_track` otherwise.
- The first module has `status = 'available'`; all others have `status = 'locked'`.
- `plan_id` is returned via polling endpoint `GET /api/v1/students/{id}/learning-plan/status`.
- Only one active plan exists per student (`UNIQUE INDEX` constraint enforced — attempting to generate a second active plan archives the first).
- The plan is cached in Redis `plan:{student_id}:current` with TTL 3600s.

---

**US-B2: Three-Track Plan Behavior**

| Field | Value |
|---|---|
| ID | US-B2 |
| Title | Correct track-specific plan sequencing (Catch Up / On Track / Accelerate) |
| As a | Student and parent |
| I want | The plan to reflect my actual learning level (remediation, standard, or enrichment) |
| So that | The content feels appropriately challenging without being overwhelming or too easy |
| Priority | P0 |
| Story Points | 5 |
| Dependencies | US-B1 |

**Acceptance Criteria:**
- For Catch Up track: ALL below-par Grade 3 prerequisites appear in the first N positions of the plan, before any Grade 4 content.
- For Accelerate track: skills with P(mastered) ≥ 0.80 are entirely excluded from the plan (not merely deprioritized).
- For On Track: Grade 3 prerequisites appear before the Grade 4 skills that depend on them, but may be interleaved with Grade 4 skills that have no dependency on the low-mastery Grade 3 skills.
- Track label and plain-language explanation is displayed on both student and parent dashboards.
- Track is stored as an immutable field on `learning_plans` (changing track requires generating a new plan).

---

**US-B3: Estimated Sessions to Mastery**

| Field | Value |
|---|---|
| ID | US-B3 |
| Title | Accurate per-module session estimates based on starting BKT state |
| As a | Parent |
| I want | An honest estimate of how many practice sessions each module requires |
| So that | I can realistically plan my child's study schedule |
| Priority | P0 |
| Story Points | 3 |
| Dependencies | US-B1 |

**Acceptance Criteria:**
- For a student starting a module at P(mastered) = 0.10, the estimate is 6–8 sessions.
- For P(mastered) = 0.50, the estimate is 3–4 sessions.
- For P(mastered) ≥ 0.80, the estimate is 1 session.
- The total plan duration estimate in weeks is `sum(estimated_sessions × 20min) / (sessions_per_week × 20min)`.
- The completion date shown to parents updates each week based on actual practice pace (trailing 7-day session average).
- If a student hasn't practiced in 7 days, the estimate defaults to 1 session/day for projection purposes.

---

**US-B4: Module Name Mapping (Child-Friendly Labels)**

| Field | Value |
|---|---|
| ID | US-B4 |
| Title | Map standard codes to child-friendly module names |
| As a | Student (age 9–10) |
| I want | My learning plan to show names like "Multiplication & Division Facts" instead of "3.OA.C.7" |
| So that | The plan feels approachable and I understand what I'm working on |
| Priority | P0 |
| Story Points | 1 |
| Dependencies | US-B1 |

**Acceptance Criteria:**
- All 38 standards have a corresponding child-friendly module name in `get_module_name()`.
- The mapping is implemented as a constant dictionary in `apps/api/src/service/learning_plan_service.py`.
- The standard code is displayed in smaller secondary text next to the module name on the student dashboard (for parent reference).
- No standard code appears as the primary display name in any student-facing UI.

---

**US-B5: Weekly Summary Email Trigger**

| Field | Value |
|---|---|
| ID | US-B5 |
| Title | Send weekly progress summary email to parent |
| As a | Parent |
| I want | A Sunday evening email summarizing my child's week in math |
| So that | I stay informed about progress without needing to log in every day |
| Priority | P1 |
| Story Points | 5 |
| Dependencies | US-B1; Stage 1: AWS SES integration |

**Acceptance Criteria:**
- A Celery cron task fires at `0 18 * * 0` Pacific Time (Sunday 6 PM).
- The email contains: child's name, week's practice minutes, sessions completed, modules mastered this week, current streak, and a CTA link to the parent dashboard.
- Weekly email is opt-in (default: enabled); controlled by `users.notification_preferences.weekly_summary`.
- Every email includes an unsubscribe link (CAN-SPAM compliance).
- Email is HTML-responsive and tested on Gmail, Apple Mail, Outlook (via Litmus screenshot tests).
- No student PII beyond the child's first name is included in the email body.

---

### Epic C: AI Question Generation Pipeline (FR-8)

**Solo Development Estimate:** 35–50 agent-hours | Calendar: ~4–6 weeks (LLM validation pipeline is the bottleneck)

**Epic Goal**: Build and validate an AI-powered pipeline that generates 5,000+ high-quality, mathematically accurate, age-appropriate questions aligned to Oregon Grade 4 standards, at ≤ $0.05/question.

---

**US-C1: LangGraph Worker ECS Service**

| Field | Value |
|---|---|
| ID | US-C1 |
| Title | Deploy LangGraph question generation worker as independent ECS task |
| As a | Admin |
| I want | A dedicated background worker that processes generation jobs from the Redis queue |
| So that | Question generation does not affect API server performance or availability |
| Priority | P0 |
| Story Points | 8 |
| Dependencies | Stage 1: Redis ElastiCache, ECS cluster |

**Acceptance Criteria:**
- Worker is deployed as a separate ECS Fargate task defined in `infrastructure/terraform/environments/staging/main.tf`.
- Worker polls Redis queue `mathpath:gen:queue` using BLPOP with 30-second timeout (no busy-waiting).
- Worker health endpoint `GET /health` returns `200 OK` with current job count.
- Worker auto-restarts on crash (ECS task restart policy).
- Datadog monitors `mathpath.gen.worker.heartbeat` metric; alert fires if no heartbeat for 5 minutes.
- Multiple worker instances can process jobs concurrently without conflict (Celery worker model).

---

**US-C2: o3-mini Question Generation with Structured Output**

| Field | Value |
|---|---|
| ID | US-C2 |
| Title | Generate questions via o3-mini with JSON schema-constrained output |
| As a | Admin (content team) |
| I want | The LLM to produce complete, schema-valid question JSON including solution verification code |
| So that | Generated questions are programmatically verifiable without manual formatting |
| Priority | P0 |
| Story Points | 8 |
| Dependencies | US-C1 |

**Acceptance Criteria:**
- Generation uses `response_format: { type: 'json_schema', schema: QuestionSchema }` to enforce structured output.
- Every generated question includes: `question_text`, `answer_options[4]` (for MC), `correct_answer`, `solution_python_code`, `solution_steps[1-5]`, `difficulty_level`, `dok_level`, `reading_level_estimate`.
- The prompt is loaded from `apps/api/prompts/question_gen_v1.0.jinja2` (versioned file — not hardcoded).
- On JSON parse failure, the worker retries once with an adjusted prompt; on second failure, the question is discarded and `generation_jobs.failed_validation` incremented.
- o3-mini API latency P95 < 8 seconds per call, tracked in `mathpath.gen.llm.latency_ms`.
- Each API call records `input_tokens`, `output_tokens`, and `estimated_cost_usd` to `generation_jobs` table.

---

**US-C3: Python Sandbox Execution (Program of Thought)**

| Field | Value |
|---|---|
| ID | US-C3 |
| Title | Execute LLM-generated solution code in sandboxed subprocess for answer verification |
| As a | Question generation pipeline |
| I want | To programmatically verify that each generated question's stated answer is mathematically correct |
| So that | Mathematically incorrect questions never reach the student question bank |
| Priority | P0 |
| Story Points | 5 |
| Dependencies | US-C2 |

**Acceptance Criteria:**
- `execute_solution_safely()` uses `subprocess.run()` with `env={}` (no environment inheritance), `timeout=10s`, `capture_output=True`.
- Only `math` and `fractions` modules are importable in the sandbox; any import that triggers a network call raises an error.
- Given a Python solution that prints the correct answer, the function returns `{'passed': True, 'actual_answer': '...'}`.
- Given a solution that times out after 10 seconds, the function returns `{'passed': False, 'error': 'Execution timeout (10s)'}`.
- Numeric answers are compared with float precision: `abs(float(actual) - float(expected)) <= tolerance` (tolerance from question schema).
- Fraction answers support string comparison after simplification (e.g., `"3/4"` == `"6/8"` after Fraction normalization).

---

**US-C4: Automated Quality Classification**

| Field | Value |
|---|---|
| ID | US-C4 |
| Title | Classify generated question quality with automated checks |
| As a | Question generation pipeline |
| I want | Automated quality checks for reading level, content safety, MC answer uniqueness, and solution steps |
| So that | Only grade-appropriate, safe, well-structured questions proceed to the question bank |
| Priority | P0 |
| Story Points | 5 |
| Dependencies | US-C2 |

**Acceptance Criteria:**
- Flesch-Kincaid grade level check: passes if `2.5 ≤ FK_grade ≤ 5.5` using the `textstat` library.
- Word count check: computation questions 5–50 words; word problems 15–200 words.
- Content safety keyword check: any match from `PROHIBITED_WORDS` = immediate fail.
- MC answer uniqueness: exactly one `is_correct = True` in `answer_options`; no two options with equal numeric value.
- Solution steps: between 1 and 5 steps; DOK-1 ≤ 2 steps, DOK-2 ≤ 3 steps, DOK-3 ≤ 5 steps.
- All checks run synchronously in < 500ms (no LLM call).
- Classification results stored in `question_validation_results` per check.

---

**US-C5: Standard Alignment and Content Safety LLM Verification**

| Field | Value |
|---|---|
| ID | US-C5 |
| Title | Verify question alignment to target standard and content safety via Claude Haiku |
| As a | Question generation pipeline |
| I want | Lightweight LLM verification that the question actually tests the targeted Oregon standard and is free of subtle bias |
| So that | The question bank is pedagogically accurate and culturally safe |
| Priority | P0 |
| Story Points | 5 |
| Dependencies | US-C2 |

**Acceptance Criteria:**
- Alignment verification calls Claude Haiku (not o3-mini — cheaper) with structured JSON output.
- Alignment confidence ≥ 0.85 → auto-approved; < 0.85 → routed to `content_review_queue`.
- Safety check runs in parallel with alignment check (asyncio.gather) — not sequentially.
- A question that passes alignment but has `severity = 'major'` in safety check is routed to human review regardless of confidence.
- Both checks complete in < 3 seconds P95 (combined parallel wall time).
- Total cost per question for Haiku calls < $0.001.

---

**US-C6: pgvector Deduplication**

| Field | Value |
|---|---|
| ID | US-C6 |
| Title | Detect and discard near-duplicate questions using pgvector cosine similarity |
| As a | Question generation pipeline |
| I want | Semantic deduplication of generated questions against the existing question bank |
| So that | Students do not see essentially the same question presented with minor wording changes |
| Priority | P0 |
| Story Points | 5 |
| Dependencies | US-C2; pgvector extension enabled in Stage 1 |

**Acceptance Criteria:**
- Question stems are embedded with `all-MiniLM-L6-v2` (384 dimensions) via SentenceTransformer.
- Similarity query uses pgvector `<=>` operator against `questions.embedding` with a `WHERE standard_code = ?` filter.
- Cosine similarity > 0.92 → question discarded; `generation_jobs.failed_validation` incremented; log includes the most-similar question ID.
- IVFFlat index on `generated_questions(content_embedding)` with `lists=50` used for all dedup queries.
- Dedup check completes in < 200ms for a bank of 5,000 questions.

---

**US-C7: Human Review Queue Management**

| Field | Value |
|---|---|
| ID | US-C7 |
| Title | Admin/reviewer interface for approving or rejecting borderline generated questions |
| As a | Content reviewer (math educator) |
| I want | A queue UI showing generated questions with their validation scores, flags, and approve/reject/edit actions |
| So that | Borderline questions receive expert human judgment before reaching students |
| Priority | P1 |
| Story Points | 8 |
| Dependencies | US-C5 |

**Acceptance Criteria:**
- Review queue accessible at `/admin/review-queue`, showing questions sorted by priority (highest first).
- Each queue item shows: question text, standard code, confidence score, flags, validation check results.
- Reviewer can: Approve (promotes to `questions` table), Reject (marks as rejected), or Edit+Approve (save edited text then promote).
- Bulk approve for questions with confidence 0.80–0.84 and no safety flags.
- Throughput target: 30 questions/hour (< 2 minutes per question review).
- Review decisions logged with `reviewer_id`, `decision_at`, `decision_notes`.

---

**US-C8: Context Theme Diversity and DOK Targeting**

| Field | Value |
|---|---|
| ID | US-C8 |
| Title | Enforce theme diversity and DOK level distribution in generated question batches |
| As a | Admin |
| I want | Generated questions to be distributed across 12 context themes with no single theme > 30%, and DOK levels proportional to the standard |
| So that | Students see a variety of question contexts and appropriately leveled challenge |
| Priority | P1 |
| Story Points | 3 |
| Dependencies | US-C2 |

**Acceptance Criteria:**
- Generation job spec includes theme rotation schedule (round-robin from the 12 permitted themes).
- For each `(standard_code, question_type)` combination, at most 30% of questions share a single theme (validated by a post-generation batch check).
- DOK level in generated questions matches the proportions in FR-8.8 for the standard's canonical DOK level.
- Oregon-specific context (Portland, Crater Lake, Mount Hood, Willamette Valley) present in at least 20% of word problem questions.

---

### Epic D: Student Dashboard (FR-9)

**Solo Development Estimate:** 20–30 agent-hours | Calendar: ~2–3 weeks

**Epic Goal**: Deliver an engaging, age-appropriate visual learning roadmap with streak tracking and achievement badges that motivates daily practice.

---

**US-D1: Visual Learning Roadmap (Path Metaphor)**

| Field | Value |
|---|---|
| ID | US-D1 |
| Title | Interactive SVG learning path with module nodes showing status |
| As a | Student (age 9–10) |
| I want | A visual path showing my learning journey with clearly distinct locked, available, in-progress, and mastered modules |
| So that | I can see exactly where I am and what comes next in an exciting, game-like way |
| Priority | P0 |
| Story Points | 13 |
| Dependencies | US-B1 |

**Acceptance Criteria:**
- Roadmap renders in `apps/web/src/components/dashboard/learning-plan-timeline.tsx` as an SVG path.
- Maximum 8 modules visible at once; roadmap "scrolls" as progress is made.
- Node states are visually distinct: Locked (gray + lock icon), Available (blue + pulsing glow + "Start"), In Progress (teal + progress ring + "Continue"), Mastered (green + star + "Mastered!").
- Tapping a locked node shows tooltip: "Complete [prerequisite name] to unlock this!"
- Tapping available/in-progress node navigates to module detail view.
- On mobile (< 768px), the SVG path degrades to a vertical scrollable card list.
- Roadmap renders without layout shift (CLS = 0 on Lighthouse audit).
- WCAG 2.1 AA: all interactive nodes have `aria-label` and are keyboard-navigable.

---

**US-D2: Streak Tracking**

| Field | Value |
|---|---|
| ID | US-D2 |
| Title | Daily practice streak tracking and display |
| As a | Student |
| I want | A visible streak counter that rewards me for practicing every day |
| So that | I'm motivated to maintain a daily practice habit |
| Priority | P0 |
| Story Points | 5 |
| Dependencies | US-B1 |

**Acceptance Criteria:**
- Streak is calculated in Pacific Time (America/Los_Angeles); a "streak day" = at least one completed practice session on that calendar date.
- Practicing twice in one day does not add 2 to the streak (idempotent).
- Missing a day resets `current_streak` to 1 on the next practice day (not to 0).
- Streak display shows flame icon + current streak count + longest streak.
- A "Keep your streak!" reminder message appears if the student has not yet practiced today (checked on dashboard load).
- `student_streaks` table is updated atomically within the session completion transaction.
- 100% streak accuracy required (zero tolerance for missed or double-counted streaks in unit tests).

---

**US-D3: Achievement Badges**

| Field | Value |
|---|---|
| ID | US-D3 |
| Title | Award and display achievement badges for qualifying events |
| As a | Student |
| I want | To earn badges for reaching milestones like completing my first session or maintaining a streak |
| So that | I feel recognized for my hard work and stay motivated |
| Priority | P0 |
| Story Points | 8 |
| Dependencies | US-D2 |

**Acceptance Criteria:**
- All 11 badges defined in FR-9.7 are implemented: `first_session`, `first_mastery`, `streak_3`, `streak_7`, `streak_14`, `halfway`, `plan_complete`, `comeback`, `perfect_session`, `fast_learner`, `oregon_explorer`.
- Badge awards are idempotent: `ON CONFLICT (student_id, badge_type) DO NOTHING` ensures no duplicate awards.
- Badge award latency from qualifying event to database insert: < 2 seconds.
- Newly earned badges trigger a celebration animation (confetti modal) on next dashboard load.
- The badge collection page at `/students/{id}/badges` shows earned badges (full color) and unearned badges (grayscale with unlock hint).
- Parents also see the badge collection on the parent dashboard.

---

**US-D4: Progress Metrics Display**

| Field | Value |
|---|---|
| ID | US-D4 |
| Title | Display overall plan progress and current module progress |
| As a | Student and parent |
| I want | Clear, motivating progress indicators showing how much of the plan is complete and how close I am to mastering the current module |
| So that | Progress feels visible and the goal feels achievable |
| Priority | P0 |
| Story Points | 5 |
| Dependencies | US-B1 |

**Acceptance Criteria:**
- Overall plan progress: donut chart showing "X of Y modules mastered" with percentage; rendered via Recharts.
- Current module progress: linear progress bar with "N of M sessions completed" label.
- BKT P(mastered) is displayed with human-readable labels: 0.30–0.50 = "Getting There", 0.50–0.70 = "Almost There", 0.70–0.85 = "Nearly Mastered!", ≥ 0.85 = "Mastered!"
- Raw float values (e.g., "0.4213") are never shown to students.
- Estimated completion date displayed as "At your current pace, you'll finish by [Month Day, Year]."
- Dashboard load time P95 < 2 seconds (plan data served from Redis cache; charts rendered client-side).

---

### Epic E: Parent Dashboard (FR-10)

**Solo Development Estimate:** 20–30 agent-hours | Calendar: ~2–3 weeks

**Epic Goal**: Give parents clear, actionable visibility into their child's learning plan, weekly progress, and upcoming milestones — buildable within 2 minutes of opening the dashboard.

---

**US-E1: Child Plan Overview Card**

| Field | Value |
|---|---|
| ID | US-E1 |
| Title | Summary card showing each child's active learning plan |
| As a | Parent |
| I want | An at-a-glance summary of each child's plan, current focus, and completion estimate |
| So that | I understand my child's learning status immediately without digging through detail screens |
| Priority | P0 |
| Story Points | 8 |
| Dependencies | US-B1 |

**Acceptance Criteria:**
- Parent dashboard loads at `/overview` and shows one summary card per child with an active plan.
- Each card shows: child display name, grade level, track label, plan start date, estimated completion date, overall progress percentage, and current module name.
- Multi-child families see cards as tabs or a swipeable carousel.
- "View Full Plan" CTA navigates to the detailed module-by-module view (US-E2).
- Dashboard load time P95 < 2 seconds.
- If a child has no active plan (diagnostic not completed), the card shows a "Start Diagnostic" CTA instead.

---

**US-E2: Module-by-Module Progress View**

| Field | Value |
|---|---|
| ID | US-E2 |
| Title | Detailed module list with status, mastery dates, and progress bars |
| As a | Parent |
| I want | A complete list of all plan modules with their current status, estimated effort, and mastery dates |
| So that | I can have informed conversations with my child about what they're working on and celebrate mastery milestones |
| Priority | P0 |
| Story Points | 5 |
| Dependencies | US-E1 |

**Acceptance Criteria:**
- Module list is grouped by section: "Prerequisite Skills" (Grade 3) and "Grade 4 Content."
- Mastered modules show a green checkmark and "Mastered on [date]."
- In-progress modules show a progress bar with P(mastered) percentage and "Getting There / Almost There" label.
- Locked modules show "Unlocks after [prerequisite module name]."
- Estimated sessions remaining shown for in-progress and available modules.
- Module standard code (e.g., "4.NBT.B.5") shown in secondary text for parent reference.

---

**US-E3: Time Spent and Practice Frequency Chart**

| Field | Value |
|---|---|
| ID | US-E3 |
| Title | Bar chart of daily practice minutes for the trailing 7 days |
| As a | Parent |
| I want | A simple bar chart showing how many minutes my child practiced each day this week |
| So that | I can see if my child is meeting the 20-minute daily practice goal |
| Priority | P0 |
| Story Points | 3 |
| Dependencies | US-E1 |

**Acceptance Criteria:**
- 7-bar chart (Recharts BarChart) covering the trailing 7 calendar days.
- Each bar represents total practice minutes computed from `plan_lessons.completed_at - plan_lessons.started_at`.
- Days with no practice show a "0 min" empty bar (not omitted).
- A horizontal reference line at 20 minutes shows the daily goal.
- Total weekly minutes and weekly goal displayed below the chart.
- Chart is WCAG 2.1 AA accessible: title states the insight, bars have `aria-label`, data table provided as accessible fallback.

---

**US-E4: Lifetime Stats Card**

| Field | Value |
|---|---|
| ID | US-E4 |
| Title | Parent-facing lifetime statistics grid (questions answered, accuracy, modules mastered) |
| As a | Parent |
| I want | Key cumulative statistics in a clean grid layout |
| So that | I can quantify my child's learning effort over time |
| Priority | P1 |
| Story Points | 3 |
| Dependencies | US-E1 |

**Acceptance Criteria:**
- Stats grid shows: total questions answered, correct answers + accuracy percentage, sessions completed, modules mastered, current streak, longest streak.
- Accuracy percentage is color-coded: green ≥ 70%, yellow 50–69%, orange < 50%.
- Stats are computed from the database (not approximated) and update on each dashboard load (cached with 60s Redis TTL).

---

## 3. Detailed Test Plan

### Coverage Targets

| Layer | Target | Enforcement |
|---|---|---|
| Core business logic (graph algorithms, plan generator, BKT, streak) | ≥ 90% line coverage | `pytest --cov --fail-under=90` in CI |
| API endpoints and service layers | ≥ 80% | `pytest --cov --fail-under=80` in CI |
| UI components | ≥ 70% | Vitest coverage gate |
| LLM behavioral contracts (golden set) | ≥ 90% pass rate | Weekly GitHub Actions workflow |
| Mutation score (graph algorithms, streak logic) | ≥ 80% | Monthly `mutmut` run |
| Accessibility | Zero axe-core violations | Playwright axe check on every PR with UI changes |

---

### 3.1 Unit Tests

Unit tests in `apps/api/tests/unit/` (pytest) and `apps/web/tests/unit/` (Vitest). No I/O — all external dependencies mocked.

#### 3.1.1 Skill Graph Algorithms

**File**: `apps/api/tests/unit/test_skill_graph_service.py`

```python
# TC-U-SG-001: Graph loads correct node count
def test_build_skill_graph_node_count(mock_db_with_38_standards):
    G = build_skill_graph(mock_db_with_38_standards)
    assert len(G.nodes) == 38

# TC-U-SG-002: Graph loads correct edge count  
def test_build_skill_graph_edge_count(mock_db_with_30_edges):
    G = build_skill_graph(mock_db_with_30_edges)
    assert len(G.edges) == 30

# TC-U-SG-003: Graph is a valid DAG
def test_skill_graph_is_dag(skill_graph_fixture):
    assert nx.is_directed_acyclic_graph(skill_graph_fixture)

# TC-U-SG-004: Topological sort respects prerequisite ordering
def test_topological_sort_respects_prerequisites(skill_graph_fixture):
    codes = ['4.NBT.B.5', '3.OA.C.7']  # 3.OA.C.7 is prerequisite of 4.NBT.B.5
    result = get_topological_sequence(skill_graph_fixture, codes)
    assert result.index('3.OA.C.7') < result.index('4.NBT.B.5')

# TC-U-SG-005: Topological sort is deterministic (stable ordering)
def test_topological_sort_is_deterministic(skill_graph_fixture):
    codes = ['4.NF.B.4', '4.NF.B.3', '4.NF.A.1', '3.NF.A.1']
    result_1 = get_topological_sequence(skill_graph_fixture, codes)
    result_2 = get_topological_sequence(skill_graph_fixture, codes)
    assert result_1 == result_2

# TC-U-SG-006: Topological sort excludes mastered skills
def test_topological_sort_excludes_mastered(skill_graph_fixture):
    all_codes = ['3.OA.C.7', '4.NBT.B.5']
    relevant = [c for c in all_codes]
    # 3.OA.C.7 mastered → only 4.NBT.B.5 returned
    result = get_topological_sequence(skill_graph_fixture, ['4.NBT.B.5'])
    # 4.NBT.B.5 should appear (prerequisite 3.OA.C.7 not in relevant codes)
    assert '4.NBT.B.5' in result
    assert '3.OA.C.7' not in result

# TC-U-SG-007: Priority score — Grade 3 bonus applied correctly
def test_priority_score_grade3_bonus(skill_graph_fixture):
    grade3_score = compute_priority_score('3.OA.C.7', 0.50, skill_graph_fixture)
    grade4_score = compute_priority_score('4.OA.A.1', 0.50, skill_graph_fixture)
    # Grade 3 bonus = +5; same p_mastered and similar centrality assumed
    # Grade 3 skill should score at least 5 points higher for same deficiency
    assert grade3_score > grade4_score - 5

# TC-U-SG-008: Remediation chain finds root cause
def test_remediation_chain_finds_root_prerequisite(skill_graph_fixture):
    skill_states = {'4.NBT.B.5': 0.20, '3.OA.C.7': 0.15, '3.NBT.A.3': 0.80}
    chain = get_remediation_chain('4.NBT.B.5', skill_states, skill_graph_fixture)
    assert '3.OA.C.7' in chain
    assert chain.index('3.OA.C.7') < chain.index('4.NBT.B.5')

# TC-U-SG-009: Remediation chain handles no failing prerequisites
def test_remediation_chain_no_failing_prereqs(skill_graph_fixture):
    skill_states = {'4.NBT.B.5': 0.30, '3.OA.C.7': 0.90, '3.NBT.A.3': 0.90}
    chain = get_remediation_chain('4.NBT.B.5', skill_states, skill_graph_fixture)
    assert chain == ['4.NBT.B.5']

# TC-U-SG-010: Cycle detection raises ValueError
def test_cycle_in_graph_raises_error(mock_db_with_cycle):
    with pytest.raises(ValueError, match="cycle"):
        build_skill_graph(mock_db_with_cycle)
```

#### 3.1.2 Learning Plan Generator

**File**: `apps/api/tests/unit/test_learning_plan_service.py`

```python
# TC-U-LP-001: Track assignment — catch_up when ≥40% below par
def test_track_catch_up_threshold(skill_states_40pct_below_par):
    track = determine_track(skill_states_40pct_below_par)
    assert track == 'catch_up'

# TC-U-LP-002: Track assignment — accelerate when ≥70% above par
def test_track_accelerate_threshold(skill_states_70pct_above_par):
    track = determine_track(skill_states_70pct_above_par)
    assert track == 'accelerate'

# TC-U-LP-003: Track assignment — on_track for mixed performance
def test_track_on_track_middle(skill_states_mixed):
    track = determine_track(skill_states_mixed)
    assert track == 'on_track'

# TC-U-LP-004: Session estimate — below par student gets 6-8 sessions
def test_session_estimate_below_par():
    assert _estimate_sessions_to_mastery(0.10) in range(6, 9)

# TC-U-LP-005: Session estimate — on par student gets 3-5 sessions
def test_session_estimate_on_par():
    assert _estimate_sessions_to_mastery(0.50) in range(3, 6)

# TC-U-LP-006: Plan duration calculation
def test_estimate_plan_duration_weeks():
    modules = [{'estimated_sessions': 6}, {'estimated_sessions': 4}]
    weeks = estimate_plan_duration_weeks(modules, minutes_per_day=20)
    # Total: 10 sessions × 20 min = 200 min; 20 min/day × 5 days = 100 min/week; 200/100 = 2.0
    assert weeks == 2.0

# TC-U-LP-007: Module name mapping covers all 38 standards
def test_all_standards_have_module_names(all_38_standard_codes):
    for code in all_38_standard_codes:
        assert get_module_name(code) != code  # Should return human-readable name

# TC-U-LP-008: Catch-up track places grade 3 skills first
def test_catch_up_grade3_skills_appear_first(skill_graph_fixture, catch_up_skill_states):
    modules = generate_learning_sequence_for_states(catch_up_skill_states, skill_graph_fixture, 'catch_up')
    grade3_indices = [i for i, m in enumerate(modules) if m['grade'] == 3]
    grade4_indices = [i for i, m in enumerate(modules) if m['grade'] == 4]
    assert max(grade3_indices) < min(grade4_indices)

# TC-U-LP-009: Mastered skills excluded from plan
def test_mastered_skills_excluded_from_plan(skill_graph_fixture):
    skill_states = {code: 0.90 for code in ALL_GRADE4_CODES}  # all mastered
    skill_states['3.OA.C.7'] = 0.20  # one below mastery
    modules = generate_learning_sequence_for_states(skill_states, skill_graph_fixture, 'on_track')
    assert all(m['p_mastered_initial'] < 0.85 for m in modules)
```

#### 3.1.3 Streak Service

**File**: `apps/api/tests/unit/test_streak_service.py`

```python
# TC-U-ST-001: First practice ever sets streak to 1
def test_first_practice_sets_streak_to_1(mock_streak_db_empty):
    result = update_streak('student-1', datetime(2024, 9, 10, 15, 0, tzinfo=UTC), mock_streak_db_empty)
    assert result['current_streak'] == 1

# TC-U-ST-002: Practicing same day does not increase streak
def test_same_day_practice_no_streak_increase(mock_streak_db_streak3):
    # Already practiced today; streak should stay at 3
    result = update_streak('student-1', datetime(2024, 9, 12, 18, 0, tzinfo=UTC), mock_streak_db_streak3)
    assert result['current_streak'] == 3

# TC-U-ST-003: Practicing next day extends streak
def test_consecutive_days_extend_streak(mock_streak_db_streak3_yesterday):
    result = update_streak('student-1', datetime(2024, 9, 13, 15, 0, tzinfo=UTC), mock_streak_db_streak3_yesterday)
    assert result['current_streak'] == 4

# TC-U-ST-004: Missing a day resets streak to 1
def test_missed_day_resets_streak(mock_streak_db_streak5_two_days_ago):
    result = update_streak('student-1', datetime(2024, 9, 14, 15, 0, tzinfo=UTC), mock_streak_db_streak5_two_days_ago)
    assert result['current_streak'] == 1

# TC-U-ST-005: Longest streak preserved after reset
def test_longest_streak_preserved_after_reset(mock_streak_db_streak5_two_days_ago):
    result = update_streak('student-1', datetime(2024, 9, 14, 15, 0, tzinfo=UTC), mock_streak_db_streak5_two_days_ago)
    assert result['longest_streak'] == 5
    assert result['current_streak'] == 1

# TC-U-ST-006: Streak boundary at midnight Pacific (not UTC)
def test_streak_uses_pacific_time():
    # 23:30 UTC on Sept 10 = 16:30 PDT on Sept 10; 08:00 UTC Sept 11 = 01:00 PDT Sept 10 still
    dt_utc_late = datetime(2024, 9, 11, 6, 30, tzinfo=UTC)  # 23:30 PDT Sept 10
    dt_utc_next = datetime(2024, 9, 11, 8, 0, tzinfo=UTC)   # 01:00 PDT Sept 11
    # These are different PDT dates and should extend streak
    streak1 = update_streak('s1', dt_utc_late, build_mock_db(last_practice=date(2024, 9, 9)))
    streak2 = update_streak('s1', dt_utc_next, build_mock_db(last_practice=date(2024, 9, 10)))
    assert streak1['last_practice_date'] == date(2024, 9, 10)
    assert streak2['last_practice_date'] == date(2024, 9, 10)  # PDT date

# TC-U-ST-007: Total practice days incremented correctly
def test_total_practice_days_increments():
    result = update_streak('student-1', datetime(2024, 9, 11, 15, 0, tzinfo=UTC), 
                           mock_streak_db(total_days=10, last_date=date(2024, 9, 10)))
    assert result['total_practice_days'] == 11
```

#### 3.1.4 Sandbox Executor

**File**: `services/question-generator/tests/unit/test_sandbox_executor.py`

```python
# TC-U-SB-001: Correct arithmetic solution passes
def test_sandbox_correct_arithmetic():
    code = "answer = 342 * 6\nprint(answer)"
    result = execute_solution_safely(code, '2052')
    assert result['passed'] is True
    assert result['actual_answer'] == '2052'

# TC-U-SB-002: Incorrect solution fails
def test_sandbox_incorrect_solution():
    code = "answer = 342 + 6\nprint(answer)"
    result = execute_solution_safely(code, '2052')
    assert result['passed'] is False

# TC-U-SB-003: Timeout returns failed with error message
def test_sandbox_timeout():
    code = "import time\ntime.sleep(15)\nprint(42)"
    result = execute_solution_safely(code, '42', timeout=1)
    assert result['passed'] is False
    assert 'timeout' in result['error'].lower()

# TC-U-SB-004: Network access raises error (no env vars)
def test_sandbox_no_network_access():
    code = "import urllib.request\nresponse = urllib.request.urlopen('https://example.com')\nprint(response.read())"
    result = execute_solution_safely(code, 'anything')
    assert result['passed'] is False

# TC-U-SB-005: Fraction answer comparison
def test_sandbox_fraction_comparison():
    code = "from fractions import Fraction\nprint(Fraction(3, 4))"
    result = execute_solution_safely(code, '3/4')
    assert result['passed'] is True

# TC-U-SB-006: Float tolerance comparison
def test_sandbox_float_tolerance():
    code = "print(0.333)"
    result = execute_solution_safely(code, '0.33333', tolerance=0.01)
    assert result['passed'] is True
```

#### 3.1.5 Quality Classifier

**File**: `services/question-generator/tests/unit/test_quality_classifier.py`

```python
# TC-U-QC-001: Reading level within range passes
def test_reading_level_within_range():
    question = {'question_text': 'Sam has 12 apples. He gives 4 to Maya. How many apples does Sam have left?',
                'context_type': 'word_problem', ...}
    result = classify_question_quality(question)
    assert result['checks']['reading_level']['passed'] is True

# TC-U-QC-002: Reading level too high fails
def test_reading_level_too_high_fails():
    question = {'question_text': 'Given the multiplicative relationship established by the preceding arithmetic sequence, determine the quotient when the antecedent is divided by the consequent.', ...}
    result = classify_question_quality(question)
    assert result['checks']['reading_level']['passed'] is False

# TC-U-QC-003: Prohibited word in question fails
def test_prohibited_word_fails():
    question = {'question_text': 'If a weapon costs 5 dollars...', ...}
    result = classify_question_quality(question)
    assert result['checks']['content_safety']['passed'] is False

# TC-U-QC-004: MC with two correct answers fails
def test_mc_duplicate_correct_answer_fails():
    question = {'question_type': 'multiple_choice',
                'answer_options': [
                    {'id': 'A', 'is_correct': True},
                    {'id': 'B', 'is_correct': True},  # two correct!
                    {'id': 'C', 'is_correct': False},
                    {'id': 'D', 'is_correct': False}
                ], ...}
    result = classify_question_quality(question)
    assert result['checks']['mc_answer_uniqueness']['passed'] is False

# TC-U-QC-005: Zero solution steps fails
def test_no_solution_steps_fails():
    question = {'solution_steps': [], ...}
    result = classify_question_quality(question)
    assert result['checks']['solution_steps_present']['passed'] is False

# TC-U-QC-006: Overall passed iff all checks pass
def test_overall_requires_all_checks_pass(valid_question_fixture):
    result = classify_question_quality(valid_question_fixture)
    assert result['passed'] == all(c['passed'] for c in result['checks'].values())
```

---

### 3.2 Integration Tests

Integration tests use `testcontainers` to spin up real PostgreSQL 17 + pgvector and Redis 7. All tests run against migration-applied schema.

**File**: `apps/api/tests/integration/test_learning_plan_integration.py`

```python
# TC-I-LP-001: Full plan generation writes all records to DB
async def test_plan_generation_creates_complete_records(db_container, redis_container, student_with_diagnostic):
    plan_id = await generate_learning_plan(student_with_diagnostic.student_id)
    # Verify plan record
    plan = await db_container.fetchrow("SELECT * FROM learning_plans WHERE plan_id = $1", plan_id)
    assert plan['status'] == 'active'
    assert plan['total_modules'] > 0
    # Verify modules
    modules = await db_container.fetch("SELECT * FROM plan_modules WHERE plan_id = $1", plan_id)
    assert len(modules) == plan['total_modules']
    # Verify first module is available
    first = sorted(modules, key=lambda m: m['sequence_order'])[0]
    assert first['status'] == 'available'

# TC-I-LP-002: Plan cached in Redis after generation
async def test_plan_cached_in_redis(db_container, redis_container, student_with_diagnostic):
    plan_id = await generate_learning_plan(student_with_diagnostic.student_id)
    cached = await redis_container.get(f"plan:{student_with_diagnostic.student_id}:current")
    assert cached is not None
    cached_plan = json.loads(cached)
    assert cached_plan['plan_id'] == plan_id

# TC-I-LP-003: Unique active plan constraint enforced
async def test_unique_active_plan_per_student(db_container, redis_container, student_with_diagnostic):
    plan_id_1 = await generate_learning_plan(student_with_diagnostic.student_id)
    plan_id_2 = await generate_learning_plan(student_with_diagnostic.student_id)
    # First plan should be archived
    plan_1 = await db_container.fetchrow("SELECT status FROM learning_plans WHERE plan_id = $1", plan_id_1)
    assert plan_1['status'] == 'superseded'
    plan_2 = await db_container.fetchrow("SELECT status FROM learning_plans WHERE plan_id = $1", plan_id_2)
    assert plan_2['status'] == 'active'

# TC-I-LP-004: Module unlocking after mastery
async def test_module_unlocks_after_prerequisite_mastered(db_container, plan_with_locked_modules):
    # Simulate mastering the first module
    await db_container.execute(
        "UPDATE plan_modules SET status='mastered', exit_p_mastery=0.90 WHERE module_id=$1",
        plan_with_locked_modules.first_module_id
    )
    await resequence_plan(plan_with_locked_modules.plan_id)
    # Dependent module should now be available
    second = await db_container.fetchrow(
        "SELECT status FROM plan_modules WHERE module_id = $1", 
        plan_with_locked_modules.second_module_id
    )
    assert second['status'] == 'available'

# TC-I-LP-005: Generation job queued and picked up by worker
async def test_generation_job_queued_in_redis(db_container, redis_container, admin_user):
    response = await test_client.post("/api/v1/admin/generation-jobs", json={
        "standard_code": "4.OA.A.1",
        "requested_count": 5,
        "difficulty_levels": [1, 2, 3]
    }, headers=admin_auth_headers)
    assert response.status_code == 201
    job_id = response.json()['job_id']
    # Job should be in Redis queue
    queued = await redis_container.lrange('mathpath:gen:queue', 0, -1)
    assert job_id.encode() in queued

# TC-I-LP-006: pgvector dedup detects near-duplicate
async def test_pgvector_dedup_detects_near_duplicate(db_container):
    # Insert a question
    embedding = generate_embedding("Sam has 12 apples and gives 4 away. How many remain?")
    await db_container.execute("INSERT INTO questions (stem, embedding, standard_code, ...) VALUES (...)")
    # Near-duplicate question
    is_dup = is_near_duplicate("Sam has 12 apples. He gives 4 to his friend. How many apples are left?", 
                               "4.OA.A.1", db_container)
    assert is_dup is True

# TC-I-SG-007: Graph cache invalidation on edge addition
async def test_graph_cache_invalidated_on_edge_add(db_container, redis_container):
    # Get graph before
    G_before = get_skill_graph()
    edge_count_before = len(G_before.edges)
    # Add a new edge via API
    await db_container.execute("INSERT INTO skill_dependency_graph_edges ...")
    await redis_container.publish('graph:invalidated', '1')
    # Next call should rebuild
    G_after = get_skill_graph()
    assert len(G_after.edges) == edge_count_before + 1
```

---

### 3.3 End-to-End Tests (Playwright)

**File**: `apps/web/tests/e2e/stage2/`

```typescript
// TC-E2E-001: Student Dashboard — Learning Roadmap Renders
test('student dashboard renders learning roadmap after plan generation', async ({ page }) => {
  await loginAsStudent(page, testStudent);
  await page.goto(`/students/${testStudent.id}`);
  // Roadmap SVG should be visible
  await expect(page.locator('[data-testid="learning-roadmap-svg"]')).toBeVisible();
  // At least one available module node
  await expect(page.locator('[data-testid="module-node-available"]').first()).toBeVisible();
  // Plan progress donut chart
  await expect(page.locator('[data-testid="plan-progress-donut"]')).toBeVisible();
});

// TC-E2E-002: Student taps available module — navigates to detail view
test('tapping available module navigates to module detail', async ({ page }) => {
  await loginAsStudent(page, testStudent);
  await page.goto(`/students/${testStudent.id}`);
  await page.locator('[data-testid="module-node-available"]').first().click();
  await expect(page).toHaveURL(/\/learning-plan\/modules\//);
  await expect(page.locator('[data-testid="start-practice-cta"]')).toBeVisible();
});

// TC-E2E-003: Student taps locked module — tooltip shown
test('tapping locked module shows prerequisite tooltip', async ({ page }) => {
  await loginAsStudent(page, testStudent);
  await page.goto(`/students/${testStudent.id}`);
  await page.locator('[data-testid="module-node-locked"]').first().hover();
  await expect(page.locator('[data-testid="locked-tooltip"]')).toContainText('Complete');
});

// TC-E2E-004: Parent Dashboard — Child plan overview card
test('parent dashboard shows child plan overview card', async ({ page }) => {
  await loginAsParent(page, testParent);
  await page.goto('/overview');
  await expect(page.locator('[data-testid="child-plan-card"]')).toBeVisible();
  await expect(page.locator('[data-testid="child-plan-card"]')).toContainText('Overall Progress');
  await expect(page.locator('[data-testid="child-plan-card"]')).toContainText('Est. completion');
});

// TC-E2E-005: Parent views module-by-module plan
test('parent can view full module list with status indicators', async ({ page }) => {
  await loginAsParent(page, testParent);
  await page.goto('/overview');
  await page.locator('[data-testid="view-full-plan-cta"]').click();
  await expect(page.locator('[data-testid="module-list-section-grade3"]')).toBeVisible();
  await expect(page.locator('[data-testid="module-list-section-grade4"]')).toBeVisible();
  // Mastered module shows checkmark
  await expect(page.locator('[data-testid="module-status-mastered"]').first()).toBeVisible();
});

// TC-E2E-006: Badge earned — celebration modal shown on next load
test('badge earned triggers celebration modal on dashboard load', async ({ page }) => {
  // Simulate badge earned (inject pending badge into Redis)
  await injectPendingBadge(testStudent.id, 'first_session');
  await loginAsStudent(page, testStudent);
  await page.goto(`/students/${testStudent.id}`);
  // Celebration modal should appear
  await expect(page.locator('[data-testid="badge-celebration-modal"]')).toBeVisible();
  await expect(page.locator('[data-testid="badge-celebration-modal"]')).toContainText('Math Explorer');
});

// TC-E2E-007: Streak display shows correct count
test('student dashboard shows current streak', async ({ page }) => {
  await setStudentStreak(testStudent.id, 5);
  await loginAsStudent(page, testStudent);
  await page.goto(`/students/${testStudent.id}`);
  await expect(page.locator('[data-testid="streak-display"]')).toContainText('5');
});

// TC-E2E-008: Admin generation job creation flow
test('admin can create and monitor generation job', async ({ page }) => {
  await loginAsAdmin(page, testAdmin);
  await page.goto('/admin/generation-jobs');
  await page.locator('[data-testid="create-job-btn"]').click();
  await page.selectOption('[name="standard_code"]', '4.NF.B.3');
  await page.fill('[name="requested_count"]', '10');
  await page.locator('[data-testid="submit-job-btn"]').click();
  await expect(page.locator('[data-testid="job-status"]').first()).toContainText('queued');
});

// TC-E2E-009: Visual regression — student dashboard baseline
test('student dashboard visual regression', async ({ page }) => {
  await loginAsStudent(page, testStudentFixture);
  await page.goto(`/students/${testStudentFixture.id}`);
  await page.waitForLoadState('networkidle');
  await expect(page).toHaveScreenshot('student-dashboard-baseline.png', { threshold: 0.001 });
});

// TC-E2E-010: Accessibility — axe-core zero violations on student dashboard
test('student dashboard has zero axe-core violations', async ({ page }) => {
  await loginAsStudent(page, testStudent);
  await page.goto(`/students/${testStudent.id}`);
  const results = await checkA11y(page, '[data-testid="main-content"]');
  expect(results.violations).toHaveLength(0);
});
```

**Cross-Browser Testing Matrix:**

| Browser | Version | Platform | Priority | Run Frequency |
|---|---|---|---|---|
| Chrome | Latest | Linux | P0 | Every PR |
| Firefox | Latest | Linux | P0 | Every PR |
| Safari | Latest | macOS | P1 | Pre-deploy |
| Chrome Mobile | Latest | Android | P1 | Pre-deploy |
| Safari Mobile | Latest | iOS | P1 | Pre-deploy |

---

### 3.4 Behavioral / BDD Tests

**File**: `apps/api/tests/bdd/features/learning_plan.feature`

```gherkin
Feature: Learning Plan Generation
  As a parent of a 4th grade student
  I want a personalized learning plan generated after my child completes the diagnostic
  So that we have a clear roadmap to grade-level math proficiency

  Background:
    Given the Oregon Grade 4 skill dependency graph is loaded with 38 standards
    And the student "Jayden" has completed the diagnostic assessment

  Scenario: Catch-Up track plan starts with Grade 3 prerequisites
    Given Jayden's diagnostic results show 50% of skills below par
    And Jayden has P(mastered) = 0.10 for "3.OA.C.7" (Multiplication Facts)
    When the learning plan is generated
    Then Jayden's track is "catch_up"
    And the first module in the plan is "Multiplication & Division Facts"
    And no Grade 4 module appears before all below-par Grade 3 prerequisites

  Scenario: On-Track plan respects topological ordering
    Given Jayden's diagnostic shows 30% below par
    And Jayden needs both "3.NF.A.1" and "4.NF.A.1"
    And "3.NF.A.1" is a prerequisite of "4.NF.A.1"
    When the learning plan is generated
    Then "Understanding Fractions" (3.NF.A.1) appears before "Equivalent Fractions" (4.NF.A.1)

  Scenario: Accelerate track skips mastered skills
    Given 75% of Jayden's skills are above par (P(mastered) ≥ 0.80)
    When the learning plan is generated
    Then Jayden's track is "accelerate"
    And all modules in the plan have P(mastered_initial) < 0.80

  Scenario: Plan generates within 5 seconds
    Given Jayden's skill states are loaded
    When the plan generation is triggered
    Then the plan is fully written to the database within 5 seconds

  Scenario: Module unlocks after prerequisite mastery
    Given Jayden has an active plan with "Multiplication Facts" (module 1, available)
    And "Multi-Digit Multiplication" (module 2, locked)
    When Jayden completes enough practice sessions to achieve P(mastered) = 0.90 for module 1
    And the BKT state is updated
    Then module 2 transitions to "available"
    And a "module_unlocked" event is published to Redis Streams

Feature: Streak Tracking
  As a student
  I want my daily practice streak to be accurately tracked
  So that I can see my consistency rewarded

  Scenario: First practice starts a streak of 1
    Given student "Maya" has never practiced before
    When Maya completes her first practice session today
    Then Maya's current streak is 1
    And her longest streak is 1

  Scenario: Practicing on consecutive days extends streak
    Given Maya has a 3-day streak, last practiced yesterday
    When Maya completes a practice session today
    Then Maya's current streak is 4
    And her longest streak is updated if 4 exceeds her previous longest

  Scenario: Missing a day breaks the streak
    Given Maya has a 5-day streak, last practiced 2 days ago
    When Maya practices today
    Then Maya's current streak is 1
    And her longest streak remains 5

  Scenario: Practicing twice in one day does not double-count
    Given Maya has practiced once today (streak = 3)
    When Maya completes a second practice session later today
    Then Maya's current streak is still 3

Feature: AI Question Generation Pipeline
  As a content administrator
  I want to generate high-quality, verified math questions at scale
  So that the student practice engine has sufficient question variety

  Scenario: Valid question passes all automated checks and is auto-approved
    Given a generation job for standard "4.OA.A.1" at difficulty 3
    When o3-mini generates a valid multiple-choice question with correct solution code
    And the solution code executes and produces the correct answer
    And the reading level is between grade 2.5 and 5.5
    And the question contains no prohibited content
    And alignment confidence is 0.90
    Then the question is inserted into the "questions" table with status "active"
    And the generation job "auto_approved" counter is incremented

  Scenario: Question with low alignment confidence goes to human review
    Given a generated question where alignment confidence is 0.75
    When all other checks pass
    Then the question is inserted into "content_review_queue" with status "pending"
    And the question does NOT appear in the live "questions" table

  Scenario: Near-duplicate question is discarded
    Given a question "Sam has 12 apples and gives 4 away. How many remain?" exists in the bank
    When the pipeline generates "Sam has 12 apples. He gives 4 to his friend. How many apples does he have left?"
    And cosine similarity between the two stems is 0.94
    Then the new question is discarded as a near-duplicate
    And "failed_validation" counter on the job is incremented
```

---

### 3.5 Robustness & Resilience Tests

#### 3.5.1 LLM Failure Handling

**File**: `services/question-generator/tests/robustness/test_llm_failure.py`

```python
# TC-R-001: o3-mini returns invalid JSON — retry once then discard
@patch('services.question_generator.generator.call_o3_mini')
async def test_invalid_json_triggers_retry(mock_llm):
    mock_llm.side_effect = [JSONDecodeError("msg", "", 0), VALID_QUESTION_JSON]
    result = await generate_question(standard='4.OA.A.1', difficulty=3)
    assert result is not None  # Second attempt succeeded
    assert mock_llm.call_count == 2

# TC-R-002: o3-mini fails twice — question discarded, job continues
@patch('services.question_generator.generator.call_o3_mini')
async def test_double_failure_discards_question(mock_llm):
    mock_llm.side_effect = [JSONDecodeError("msg", "", 0), JSONDecodeError("msg", "", 0)]
    result = await generate_question(standard='4.OA.A.1', difficulty=3)
    assert result is None

# TC-R-003: o3-mini rate limit (429) — backs off and retries
@patch('services.question_generator.generator.call_o3_mini')
async def test_rate_limit_backoff(mock_llm):
    mock_llm.side_effect = [RateLimitError(retry_after=2), VALID_QUESTION_JSON]
    start = time.time()
    result = await generate_question(standard='4.OA.A.1', difficulty=3)
    elapsed = time.time() - start
    assert elapsed >= 2.0  # Backed off at least 2 seconds
    assert result is not None

# TC-R-004: Daily budget hard stop blocks new jobs
async def test_daily_budget_hardstop(redis_client):
    await redis_client.set('mathpath:llm:daily_spend_cents', 1001)  # Over $10
    with pytest.raises(BudgetExceededError):
        await generate_question(standard='4.OA.A.1', difficulty=3)

# TC-R-005: Claude Haiku timeout — alignment check defaults to human review
@patch('services.question_generator.generator.verify_standard_alignment')
async def test_alignment_timeout_routes_to_review(mock_align):
    mock_align.side_effect = asyncio.TimeoutError()
    result = await run_validation_pipeline(VALID_GENERATED_QUESTION)
    assert result['requires_human_review'] is True
    assert result['all_passed'] is False

# TC-R-006: LangGraph worker crash — Celery retries job
def test_celery_task_retried_on_crash():
    with pytest.raises(Retry):
        generate_question_batch.apply(args=['job-id-123'], throw=True)
    # Verify retry was scheduled
    assert generate_question_batch.request.retries == 1
```

#### 3.5.2 Plan Generation Resilience

```python
# TC-R-007: Plan generation with empty BKT states — graceful handling
async def test_plan_generation_empty_skill_states():
    # Student has no skill states (new student, diagnostic not yet processed)
    with pytest.raises(PlanGenerationError, match="No skill states found"):
        await generate_learning_plan(student_id='student-no-states')

# TC-R-008: Redis unavailable — plan generation falls back to DB
@patch('apps.api.src.clients.redis_client.get')
async def test_plan_generation_redis_failure_fallback(mock_redis_get):
    mock_redis_get.side_effect = RedisConnectionError()
    # Should still work by reading directly from DB
    plan_id = await generate_learning_plan(student_id='student-valid')
    assert plan_id is not None

# TC-R-009: DB transaction failure — plan generation rolls back
@patch('apps.api.src.db.session.execute')
async def test_plan_generation_db_rollback(mock_execute, db_container):
    mock_execute.side_effect = [MagicMock(), Exception("DB error")]  # Fail on module insert
    with pytest.raises(Exception):
        await generate_learning_plan(student_id='student-valid')
    # Verify no partial plan left in DB
    plan_count = await db_container.fetchval("SELECT COUNT(*) FROM learning_plans WHERE student_id = 'student-valid'")
    assert plan_count == 0
```

#### 3.5.3 Load Tests

**File**: `tests/load/k6_stage2.js`

```javascript
// TC-LOAD-001: Student dashboard under concurrent load
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '30s', target: 50 },   // ramp to 50 users
    { duration: '2m',  target: 50 },   // stay at 50 users
    { duration: '30s', target: 0 },    // ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<2000'],  // P95 < 2 seconds
    http_req_failed: ['rate<0.01'],     // < 1% errors
  },
};

export default function () {
  // Student dashboard load
  const res = http.get(`${BASE_URL}/api/v1/students/${STUDENT_IDS[Math.floor(Math.random()*10)]}/learning-plan`, 
    { headers: authHeaders });
  check(res, {
    'dashboard loads < 2s': (r) => r.timings.duration < 2000,
    'status 200': (r) => r.status === 200,
  });
  sleep(1);
}
```

---

### 3.6 Repeatability Tests

These tests verify that deterministic components produce identical outputs across multiple invocations with the same inputs.

```python
# TC-REP-001: Plan generation is deterministic for same skill states
async def test_plan_generation_deterministic():
    skill_states = load_fixture('skill_states_catch_up_sample.json')
    plan_1 = simulate_plan_generation(skill_states)
    plan_2 = simulate_plan_generation(skill_states)
    assert [m['standard_code'] for m in plan_1['modules']] == [m['standard_code'] for m in plan_2['modules']]

# TC-REP-002: Topological sort is idempotent
def test_topological_sort_idempotent(skill_graph_fixture):
    codes = ['4.NF.B.4', '3.NF.A.1', '4.NF.A.1', '4.NF.B.3']
    result_1 = get_topological_sequence(skill_graph_fixture, codes)
    result_2 = get_topological_sequence(skill_graph_fixture, codes)
    result_3 = get_topological_sequence(skill_graph_fixture, codes)
    assert result_1 == result_2 == result_3

# TC-REP-003: Priority scores are reproducible
def test_priority_scores_reproducible(skill_graph_fixture):
    skill_states = {'4.NBT.B.5': 0.30, '3.OA.C.7': 0.15, '4.NF.A.1': 0.50}
    scores_1 = {code: compute_priority_score(code, p, skill_graph_fixture) for code, p in skill_states.items()}
    scores_2 = {code: compute_priority_score(code, p, skill_graph_fixture) for code, p in skill_states.items()}
    assert scores_1 == scores_2

# TC-REP-004: Streak calculation is idempotent (calling twice same day yields same result)
async def test_streak_update_same_day_idempotent(db_container):
    dt = datetime(2024, 9, 10, 15, 0, tzinfo=UTC)
    result_1 = await update_streak_async('student-1', dt, db_container)
    result_2 = await update_streak_async('student-1', dt, db_container)
    assert result_1['current_streak'] == result_2['current_streak']

# TC-REP-005: Badge award is idempotent
async def test_badge_award_no_duplicates(db_container):
    await award_badge('student-1', 'first_session', db_container)
    await award_badge('student-1', 'first_session', db_container)  # second call
    count = await db_container.fetchval(
        "SELECT COUNT(*) FROM student_badges WHERE student_id='student-1' AND badge_type='first_session'"
    )
    assert count == 1

# TC-REP-006: Module re-sequencing converges to same result after multiple re-runs
async def test_resequencing_convergence(plan_fixture):
    seq_1 = await resequence_plan(plan_fixture.plan_id)
    seq_2 = await resequence_plan(plan_fixture.plan_id)
    assert [m['module_id'] for m in seq_1] == [m['module_id'] for m in seq_2]

# TC-REP-007: Plan generation after skill regression includes regressed skill
async def test_plan_includes_regressed_skill(db_container, active_plan_fixture):
    # Skill was mastered, now regressed
    await db_container.execute(
        "UPDATE student_skill_states SET p_mastered = 0.50 WHERE standard_code='4.NF.A.1' AND student_id=$1",
        active_plan_fixture.student_id
    )
    await resequence_plan(active_plan_fixture.plan_id)
    modules = await db_container.fetch(
        "SELECT * FROM plan_modules WHERE plan_id=$1 AND standard_code='4.NF.A.1'",
        active_plan_fixture.plan_id
    )
    assert len(modules) == 1
    assert modules[0]['status'] != 'mastered'
```

---

### 3.7 Security Tests

#### 3.7.1 OWASP Top 10 Coverage

| OWASP Category | Threat in Stage 2 | Test Case | Tool |
|---|---|---|---|
| A01 Broken Access Control | Parent reads another parent's child plan | `test_parent_cannot_access_other_childs_plan` | pytest / httpx |
| A01 Broken Access Control | Student accesses parent dashboard | `test_student_cannot_access_parent_view` | pytest / httpx |
| A01 Broken Access Control | Admin generation job endpoint accessible by student | `test_student_cannot_create_gen_job` | pytest / httpx |
| A02 Cryptographic Failures | Student PII in LLM prompts | `test_llm_prompt_contains_no_pii` | pytest (static analysis) |
| A03 Injection | SQL injection via student_id in plan API | `test_sql_injection_student_id` | OWASP ZAP |
| A03 Injection | Prompt injection via student name in generation | `test_prompt_injection_blocked` | pytest |
| A05 Security Misconfiguration | Redis queue accessible without auth | Terraform / Redis AUTH config test | Trivy IaC scan |
| A06 Vulnerable Components | Celery, LangGraph, NetworkX CVEs | Weekly Trivy container scan | Trivy |
| A07 Auth Failures | JWT token forgery on /learning-plans | `test_forged_jwt_rejected` | pytest / httpx |
| A09 Security Logging | Audit log records admin generation job creation | `test_audit_log_records_gen_job` | pytest |

```python
# TC-SEC-001: Parent A cannot read Plan belonging to Parent B's child
async def test_parent_cannot_access_other_childs_plan(async_client, parent_a_token, student_b_plan_id):
    response = await async_client.get(
        f"/api/v1/learning-plans/{student_b_plan_id}",
        headers={"Authorization": f"Bearer {parent_a_token}"}
    )
    assert response.status_code == 403

# TC-SEC-002: Student cannot create generation jobs (admin-only endpoint)
async def test_student_cannot_create_gen_job(async_client, student_token):
    response = await async_client.post(
        "/api/v1/admin/generation-jobs",
        json={"standard_code": "4.OA.A.1", "requested_count": 5},
        headers={"Authorization": f"Bearer {student_token}"}
    )
    assert response.status_code == 403

# TC-SEC-003: LLM generation prompts contain no student PII
def test_llm_prompt_contains_no_student_pii():
    prompt = build_generation_prompt(
        standard_code="4.OA.A.1",
        difficulty=3,
        question_type="multiple_choice",
        context_theme="animals",
        student_id="student-12345",  # Should NOT appear in prompt
        student_name="Jayden Smith"  # Should NOT appear in prompt
    )
    assert "student-12345" not in prompt
    assert "Jayden Smith" not in prompt
    assert "jayden" not in prompt.lower()

# TC-SEC-004: Generation sandbox cannot access filesystem
def test_sandbox_cannot_read_filesystem():
    malicious_code = """
import os
files = os.listdir('/')
print(files)
"""
    result = execute_solution_safely(malicious_code, '')
    # Should fail or return empty (no filesystem access)
    assert result['passed'] is False or 'etc' not in str(result.get('actual_answer', ''))

# TC-SEC-005: Forged JWT token rejected on plan endpoint
async def test_forged_jwt_rejected(async_client):
    forged_token = create_token_with_wrong_signing_key(subject="student-12345")
    response = await async_client.get(
        "/api/v1/students/student-12345/learning-plan",
        headers={"Authorization": f"Bearer {forged_token}"}
    )
    assert response.status_code == 401

# TC-SEC-006: COPPA — student_id not in any LLM API request body
@patch('services.question_generator.generator.openai_client.chat.completions.create')
def test_no_student_id_in_openai_api_call(mock_openai):
    run_generation_pipeline(standard='4.OA.A.1', difficulty=3)
    call_args = mock_openai.call_args
    prompt_text = str(call_args)
    assert 'student' not in prompt_text.lower() or 'student_id' not in prompt_text
```

#### 3.7.2 SAST / DAST / SCA Configuration

| Tool | Scope | When | Failure Condition |
|---|---|---|---|
| Bandit | Python API and services | Every PR | Any HIGH severity finding |
| eslint-plugin-security | TypeScript frontend | Every PR | Any HIGH severity finding |
| OWASP ZAP | Full API (staging) | Weekly + pre-release | Any Critical/High finding |
| Trivy | Docker images | Every build | Any CRITICAL CVE |
| Trivy | Terraform IaC | Every PR with infra changes | Any CRITICAL misconfiguration |
| npm audit / pip-audit | Dependencies | Weekly scheduled job | Any Critical vulnerability |

---

### 3.8 LLM Behavioral Contract Tests

This section is central to Stage 2's distinguishing feature: the AI question generation pipeline. These tests verify properties and invariants of LLM outputs rather than exact strings.

#### 3.8.1 Question Generation Contracts

**File**: `services/question-generator/tests/contracts/test_question_gen_contracts.py`

```python
"""
LLM behavioral contract tests for the question generation pipeline.
Run on every PR that touches prompt templates or generator.py.
Full golden set run weekly via .github/workflows/llm-contract-tests.yml.
"""

import pytest
import re
import textstat
from textblob import TextBlob
from services.question_generator.generator import QuestionGenerator
from services.question_generator.validators import classify_question_quality

@pytest.fixture
def generator():
    return QuestionGenerator(model='o3-mini', prompt_version='v1.0')


class TestMathematicalCorrectnessContracts:
    """Every generated question must be mathematically verifiable."""

    @pytest.mark.parametrize('standard_code,difficulty', [
        ('4.OA.A.1', 1), ('4.OA.A.1', 3), ('4.OA.A.1', 5),
        ('4.NBT.B.5', 2), ('4.NBT.B.5', 4),
        ('4.NF.B.3', 1), ('4.NF.B.3', 3),
        ('4.NBT.B.6', 2), ('4.NBT.B.6', 5),
    ])
    async def test_generated_question_is_mathematically_correct(
        self, generator, standard_code, difficulty
    ):
        """Generated question's embedded solution code must verify the stated answer."""
        question = await generator.generate(standard_code=standard_code, difficulty=difficulty)
        exec_result = execute_solution_safely(
            question.solution_python_code, 
            question.correct_answer, 
            tolerance=question.numeric_tolerance or 0
        )
        assert exec_result['passed'], (
            f"Math verification failed for {standard_code} d={difficulty}: "
            f"expected {question.correct_answer}, got {exec_result['actual_answer']}\n"
            f"Question: {question.question_text}"
        )

    async def test_mc_exactly_one_correct_answer(self, generator):
        """Multiple choice questions must have exactly one correct option."""
        question = await generator.generate(standard_code='4.OA.A.2', difficulty=3, 
                                            question_type='multiple_choice')
        correct_count = sum(1 for opt in question.answer_options if opt.is_correct)
        assert correct_count == 1, f"Expected 1 correct answer, found {correct_count}"

    async def test_mc_distractors_are_wrong(self, generator):
        """All distractor options must be numerically distinct from correct answer."""
        question = await generator.generate(standard_code='4.NBT.B.5', difficulty=2,
                                            question_type='multiple_choice')
        correct_val = float(question.correct_answer)
        for opt in question.answer_options:
            if not opt.is_correct:
                try:
                    distractor_val = float(opt.text.replace(',', ''))
                    assert abs(distractor_val - correct_val) > 0.001, (
                        f"Distractor {opt.text} equals correct answer {question.correct_answer}"
                    )
                except ValueError:
                    pass  # Text answer, not numeric


class TestReadingLevelContracts:
    """Questions must be readable by 4th graders (Flesch-Kincaid 2.5–5.5)."""

    @pytest.mark.parametrize('standard_code', ['4.OA.A.1', '4.NF.B.3', '4.GM.C.7', '4.DR.A.1'])
    async def test_question_grade_appropriate_reading_level(self, generator, standard_code):
        question = await generator.generate(standard_code=standard_code, difficulty=3)
        fk_grade = textstat.flesch_kincaid_grade(question.question_text)
        assert 2.0 <= fk_grade <= 7.0, (
            f"FK Grade {fk_grade} outside [2.0, 7.0] for {standard_code}: {question.question_text}"
        )

    async def test_difficulty_5_question_not_too_simple(self, generator):
        """Difficulty-5 questions should have appropriate complexity (not trivial)."""
        question = await generator.generate(standard_code='4.NBT.B.5', difficulty=5)
        word_count = len(question.question_text.split())
        assert word_count >= 20, f"Difficulty-5 question too short ({word_count} words): {question.question_text}"
        assert len(question.solution_steps) >= 2, "Difficulty-5 should have multi-step solution"


class TestContentSafetyContracts:
    """All generated questions must be appropriate for children aged 9–10."""

    PROHIBITED_PATTERNS = [
        r'\b(gun|weapon|kill|die|dead|drug|alcohol|cigarette|violence|hurt|harm)\b',
        r'\b(hate|stupid|dumb|ugly|idiot)\b',
        r'\b(sexy|naked|inappropriate)\b',
    ]

    @pytest.mark.parametrize('standard_code,difficulty', [
        ('4.OA.A.1', 2), ('4.NBT.B.5', 3), ('4.NF.B.4', 1), ('4.GM.C.7', 4),
    ])
    async def test_question_contains_no_prohibited_content(self, generator, standard_code, difficulty):
        question = await generator.generate(standard_code=standard_code, difficulty=difficulty)
        for pattern in self.PROHIBITED_PATTERNS:
            match = re.search(pattern, question.question_text, re.IGNORECASE)
            assert match is None, (
                f"Prohibited content detected (pattern: {pattern}) in: {question.question_text}"
            )

    async def test_question_uses_inclusive_names(self, generator):
        """Over a batch of 10 questions, diverse names should appear."""
        questions = [
            await generator.generate(standard_code='4.OA.A.1', difficulty=3)
            for _ in range(10)
        ]
        all_text = ' '.join(q.question_text for q in questions)
        # At least some names from the inclusive list should appear
        inclusive_names = ['Maya', 'Jordan', 'Alex', 'Sam', 'Mia', 'Taylor', 'River']
        names_found = [name for name in inclusive_names if name in all_text]
        assert len(names_found) >= 2, f"Too few diverse names in batch. Found: {names_found}"


class TestOregonContextContracts:
    """Word problem questions should include Oregon-relevant contexts."""

    async def test_oregon_context_appears_in_word_problems(self, generator):
        """At least 1 in 5 word problems should reference Oregon."""
        oregon_keywords = ['Oregon', 'Portland', 'Crater Lake', 'Mount Hood', 'Willamette', 
                           'Pacific', 'Columbia', 'beaver', 'Blazers', 'Timbers']
        questions = [
            await generator.generate(standard_code='4.OA.A.1', difficulty=3, 
                                     context_type='word_problem')
            for _ in range(10)
        ]
        oregon_count = sum(
            1 for q in questions
            if any(kw.lower() in q.question_text.lower() for kw in oregon_keywords)
        )
        assert oregon_count >= 2, f"Only {oregon_count}/10 questions had Oregon context"


class TestStandardAlignmentContracts:
    """Generated questions must test the targeted Oregon standard."""

    @pytest.mark.parametrize('standard_code,expected_operation', [
        ('4.OA.A.1', ['times as many', 'times as much', 'multiplicative']),
        ('4.NBT.B.5', ['multiply', 'product', 'times']),
        ('4.NF.B.3', ['add', 'subtract', 'fraction']),
        ('4.NF.C.6', ['decimal', '0.', 'tenths', 'hundredths']),
        ('4.GM.C.7', ['degree', 'angle', 'protractor']),
    ])
    async def test_question_tests_target_standard(
        self, generator, standard_code, expected_operation
    ):
        """Question text should contain vocabulary associated with the standard."""
        question = await generator.generate(standard_code=standard_code, difficulty=3)
        text_lower = question.question_text.lower()
        found = any(op.lower() in text_lower for op in expected_operation)
        # Note: This is a soft check — alignment LLM is authoritative. This tests for obvious misalignment.
        assert found, (
            f"Question for {standard_code} may not test the right skill. "
            f"Expected one of {expected_operation} in: {question.question_text}"
        )


class TestDOKLevelContracts:
    """Questions must match the requested Depth of Knowledge level."""

    async def test_dok1_question_minimal_steps(self, generator):
        """DOK-1 questions should require at most 2 solution steps."""
        question = await generator.generate(standard_code='4.OA.A.1', difficulty=1)
        assert len(question.solution_steps) <= 2, (
            f"DOK-1 question has too many steps ({len(question.solution_steps)}): {question.question_text}"
        )

    async def test_dok3_question_multiple_steps(self, generator):
        """DOK-3 questions should have 3–5 solution steps."""
        question = await generator.generate(standard_code='4.OA.A.3', difficulty=5)
        assert len(question.solution_steps) >= 3, (
            f"DOK-3 question has too few steps ({len(question.solution_steps)}): {question.question_text}"
        )
```

#### 3.8.2 Golden Set Testing

**File**: `services/question-generator/tests/golden/test_golden_set.py`

```python
"""
Weekly golden set regression test.
Run via: .github/workflows/llm-contract-tests.yml
50 hand-verified (standard, difficulty, expected_properties) tuples.
Alert threshold: > 10% failure rate.
"""

import json
import pytest
from pathlib import Path

GOLDEN_SET_PATH = Path("tests/golden/question_golden_set.json")
FAILURE_THRESHOLD = 0.10  # Alert if > 10% fail any contract

@pytest.fixture
def golden_set():
    with open(GOLDEN_SET_PATH) as f:
        return json.load(f)

async def test_golden_set_question_contracts(generator, golden_set):
    """
    Run all 50 golden set items through behavioral contracts.
    Each item specifies: standard_code, difficulty, expected minimum properties.
    """
    failures = []

    for item in golden_set:
        try:
            question = await generator.generate(
                standard_code=item['standard_code'],
                difficulty=item['difficulty'],
                question_type=item.get('question_type', 'multiple_choice')
            )

            # Contract 1: Math correctness
            exec_result = execute_solution_safely(question.solution_python_code, question.correct_answer)
            if not exec_result['passed']:
                failures.append({
                    'id': item['id'],
                    'contract': 'math_correctness',
                    'question': question.question_text,
                    'expected': question.correct_answer,
                    'actual': exec_result['actual_answer']
                })
                continue

            # Contract 2: Reading level
            fk = textstat.flesch_kincaid_grade(question.question_text)
            if not (1.5 <= fk <= 7.5):
                failures.append({'id': item['id'], 'contract': 'reading_level', 'fk_grade': fk})

            # Contract 3: Content safety
            for pattern in PROHIBITED_PATTERNS:
                if re.search(pattern, question.question_text, re.IGNORECASE):
                    failures.append({'id': item['id'], 'contract': 'content_safety', 'pattern': pattern})

            # Contract 4: Standard-specific vocabulary
            if item.get('expected_vocabulary'):
                found = any(v.lower() in question.question_text.lower() 
                           for v in item['expected_vocabulary'])
                if not found:
                    failures.append({'id': item['id'], 'contract': 'standard_alignment',
                                   'expected_vocab': item['expected_vocabulary']})

        except Exception as e:
            failures.append({'id': item['id'], 'contract': 'exception', 'error': str(e)})

    failure_rate = len(failures) / len(golden_set)
    assert failure_rate <= FAILURE_THRESHOLD, (
        f"Golden set failure rate {failure_rate:.1%} exceeds {FAILURE_THRESHOLD:.0%} threshold.\n"
        f"Failures ({len(failures)}/{len(golden_set)}):\n"
        + json.dumps(failures[:10], indent=2)  # Show first 10 failures
    )
```

#### 3.8.3 Model Version Regression Testing

```python
@pytest.mark.parametrize("model", ["o3-mini", "gpt-4o-mini"])
async def test_model_version_regression(model, golden_set):
    """Compare behavioral contract pass rates between model versions before upgrade."""
    gen = QuestionGenerator(model=model)
    pass_count = 0
    cost_total = 0.0

    for item in golden_set[:20]:  # Sample of 20 for cost management
        question = await gen.generate(standard_code=item['standard_code'], difficulty=item['difficulty'])
        exec_result = execute_solution_safely(question.solution_python_code, question.correct_answer)
        if exec_result['passed']:
            pass_count += 1
        cost_total += question.estimated_cost_usd

    pass_rate = pass_count / 20
    avg_cost = cost_total / 20
    print(f"Model {model}: {pass_rate:.0%} math pass rate, ${avg_cost:.4f}/question avg cost")
    assert pass_rate >= 0.85, f"Model {model} below 85% math correctness threshold"
    assert avg_cost <= 0.05, f"Model {model} exceeds $0.05/question cost target"
```

---

### 3.9 Baseline Acceptance Criteria

Before Stage 2 can be declared production-ready, all of the following gates must pass:

| Gate | Target | Measurement Method |
|---|---|---|
| Plan generation latency P95 | < 5 seconds | Datadog APM trace on `learning_plan.generate` |
| Student dashboard load P95 | < 2 seconds | Synthetic monitoring (Datadog Synthetics) |
| Parent dashboard load P95 | < 2 seconds | Synthetic monitoring |
| Unit test coverage: graph algorithms + streak | ≥ 90% | `pytest --cov --fail-under=90` |
| Unit test coverage: API services | ≥ 80% | `pytest --cov --fail-under=80` |
| UI component coverage | ≥ 70% | Vitest coverage gate |
| LLM golden set pass rate | ≥ 90% | Weekly GitHub Actions job |
| LLM cost per question | ≤ $0.05 | Calculated from generation_jobs.estimated_cost_usd |
| Auto-approval rate (question pipeline) | ≥ 85% | Ratio: auto_approved / total_generated |
| Security: Critical/High findings | 0 | Bandit + OWASP ZAP + Trivy |
| Accessibility: axe-core violations | 0 | Playwright axe-core check |
| Streak tracking accuracy | 100% (all unit tests pass) | `pytest tests/unit/test_streak_service.py` |
| Badge idempotency | 0 duplicate badges | Verified by `UNIQUE(student_id, badge_type)` + unit test |
| Question math correctness rate | ≥ 98% (on random sample) | Monthly manual review of 50 random live questions |

---

## 4. Operations Plan

### 4.1 MLOps

#### 4.1.1 LLM Prompt Versioning

All prompts are versioned Jinja2 templates stored in version control. No prompt text appears as hardcoded strings in application code.

| Prompt File | Location | Version | Triggers for New Version |
|---|---|---|---|
| Question generation | `apps/api/prompts/question_gen_v1.0.jinja2` | v1.0 | Standard code set change, quality degradation, DOK targeting change |
| Standard alignment check | `apps/api/prompts/alignment_check_v1.0.jinja2` | v1.0 | Alignment accuracy drops below 85% on golden set |
| Content safety check | `apps/api/prompts/safety_check_v1.0.jinja2` | v1.0 | Any new category of safety concern identified |
| Weekly summary email | `apps/api/prompts/weekly_email_v1.0.jinja2` | v1.0 | Email engagement metrics drop; unsubscribe rate increases |

**Prompt Version Protocol:**
1. New prompt version created as `question_gen_v1.1.jinja2` (never overwrite previous versions).
2. A/B test: 10% of generation jobs use `v1.1`, 90% use `v1.0`. Compare auto-approval rate and math correctness.
3. If `v1.1` wins: update `DEFAULT_PROMPT_VERSION` config key; old version retained for rollback.
4. Generation job records include `prompt_template` field — historical traceability.

#### 4.1.2 Question Quality Monitoring

| Metric | Dashboard | Alert Threshold | Action |
|---|---|---|---|
| `gen.auto_approval_rate` (daily) | Datadog dashboard "Question Quality" | < 80% for 3 consecutive days | Review recent prompt changes; inspect failure breakdown |
| `gen.math_correctness_rate` (daily) | Same | < 95% | Immediately pause generation; review sandbox executor |
| `gen.avg_fk_grade` (rolling 100 questions) | Same | > 6.0 or < 2.0 | Adjust reading level constraints in prompt |
| `gen.duplicate_rate` (daily) | Same | > 15% | Widen context themes; check pgvector threshold calibration |
| `gen.cost_per_question_usd` (daily) | FinOps dashboard | > $0.04 (warning) / > $0.05 (alert) | Switch to cheaper model tier; reduce o3-mini token budget |
| `gen.pipeline_throughput_per_hour` | Same | < 80 questions/hour | Scale Celery workers; check API rate limit |

Datadog SLO: Auto-approval rate ≥ 85% over any rolling 7-day window.

#### 4.1.3 LLM Behavioral Contract — Weekly Golden Set Run

```yaml
# .github/workflows/llm-contract-tests.yml
name: Weekly LLM Contract Tests
on:
  schedule:
    - cron: '0 8 * * 1'  # Every Monday 8 AM UTC
  workflow_dispatch:

jobs:
  golden-set:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run question generation golden set
        run: pytest services/question-generator/tests/golden/ -v --tb=short
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
      - name: Upload results to Datadog
        run: python scripts/upload_golden_set_results.py ${{ github.run_id }}
      - name: Alert on failure
        if: failure()
        uses: slackapi/slack-github-action@v1
        with:
          payload: '{"text":"⚠️ Stage 2 LLM golden set failure rate exceeded threshold. Review: ${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}"}'
```

#### 4.1.4 BKT Model Monitoring (Inherited from Stage 1, Extended in Stage 2)

| Metric | Monitoring | Stage 2 Addition |
|---|---|---|
| BKT P(mastered) distribution across students | Datadog histogram daily | Alert if < 5% of students ever reach mastery (plan not working) |
| Average sessions to module mastery | Datadog metric | Compare to `estimated_sessions`; alert if actual > 2× estimated |
| Module skip rate (mastered on first session) | Datadog metric | Alert if > 30% (questions may be too easy for accelerate-track students) |
| Plan completion rate by track | Weekly BI report | Baseline for Stage 3 adaptive improvements |

---

### 4.2 FinOps

#### 4.2.1 AWS Cost Allocation Tagging Strategy

All Stage 2 infrastructure resources are tagged consistently:

```hcl
# infrastructure/terraform/environments/staging/main.tf
locals {
  common_tags = {
    Project     = "mathpath-oregon"
    Stage       = "stage2"
    Environment = var.environment  # "dev" | "staging" | "production"
    Team        = "engineering"
    CostCenter  = "product"
    Feature     = "question-generation"  # per-feature tag for LangGraph Worker
  }
}
```

| Resource | Feature Tag | Expected Monthly Cost (Prod) |
|---|---|---|
| ECS Fargate — API Server | `api` | ~$45/month (0.5 vCPU, 1GB, 2 tasks) |
| ECS Fargate — LangGraph Worker | `question-generation` | ~$30/month (1 vCPU, 2GB, 1–4 tasks) |
| RDS PostgreSQL 17 (with pgvector) | `database` | ~$80/month (db.t4g.medium) |
| ElastiCache Redis 7 | `cache-queue` | ~$25/month (cache.t4g.medium) |
| S3 (badge icons, email assets) | `assets` | ~$2/month |
| OpenAI API (o3-mini) | `llm-generation` | ~$11 total for 5,000 questions |
| Anthropic API (Claude Haiku) | `llm-validation` | ~$0.50 total for 5,000 questions |

#### 4.2.2 Three-Tier LLM Token Strategy

| Tier | Model | Use Case | Price Approx. | Stage 2 Usage |
|---|---|---|---|---|
| Fast/Cheap | `gpt-4o-mini` | Alignment confidence 0.75–0.84 re-review; fallback | ~$0.15/1M input | Fallback if o3-mini unavailable |
| Balanced | `o3-mini` | Primary question generation (PoT + structured output) | ~$1.10/1M input | Primary — all generation calls |
| Premium | `claude-sonnet-4.6` | Safety classification for flagged content; content review assistance | ~$3.00/1M input | Moderate — only safety flags |
| Classification | `claude-haiku-3` | Standard alignment + routine safety checks | ~$0.25/1M input | High volume — every question |

**Daily Spend Controls:**

```python
# In Celery worker, before every o3-mini call:
async def check_daily_budget_gate():
    spend_cents = int(await redis.get('mathpath:llm:daily_spend_cents') or 0)
    if spend_cents >= 1000:  # $10 hard stop
        raise BudgetExceededError(f"Daily LLM budget exhausted (${spend_cents/100:.2f} spent)")
    if spend_cents >= 500:   # $5 warning
        logger.warning(f"LLM daily spend at ${spend_cents/100:.2f} — approaching limit")
```

**Budget Alerts:**

| Environment | Daily Alert Threshold | Daily Hard Stop | Monthly Budget |
|---|---|---|---|
| Development | $2 | $5 | $20 |
| Staging | $3 | $8 | $50 |
| Production | $5 | $10 | $100 |

#### 4.2.3 Resource Right-Sizing

- **LangGraph Worker ECS task**: Start with 1 task (1 vCPU, 2 GB). Auto-scale to 4 tasks during active generation campaigns based on Redis queue depth (CloudWatch custom metric: `mathpath.gen.queue.depth > 10` → scale out).
- **API Server ECS tasks**: 2 tasks minimum for HA; auto-scale on CPU > 70%.
- **RDS PostgreSQL**: `db.t4g.medium` during Stage 2 (small pilot). Upgrade to `db.t4g.large` if p_mastered query becomes slow (monitor `pg_stat_statements`).
- **ElastiCache Redis**: `cache.t4g.medium` — single node (Stage 2 pilot; add replica in Stage 3 for production reliability).

#### 4.2.4 FinOps Review Cadence

| Frequency | Scope | Participants | Output |
|---|---|---|---|
| Weekly (Months 4–6) | AWS + LLM API spend vs. budget | Engineer + Product | Slack post with spend breakdown, anomaly flag |
| Monthly | Full cost allocation by tag | Engineer + Founder | Cost report; right-sizing recommendations |

---

### 4.3 SecOps

#### 4.3.1 COPPA Compliance for Stage 2 Features

Stage 2 introduces new data flows involving student learning data. Compliance checklist:

| Requirement | Stage 2 Implementation | Verified By |
|---|---|---|
| No student PII in LLM prompts | Generation prompts contain only standard codes and math content; `test_llm_prompt_contains_no_pii` | Unit test + code review |
| Student data encrypted at rest (AES-256) | RDS encryption enabled; `plan_modules.bkt_history` JSONB encrypted via pgcrypto column | Terraform config + Trivy scan |
| Data minimization: only necessary fields in dashboards | Dashboard API responses exclude `student.email`, `student.full_name` (only `display_name` served) | Code review + API response tests |
| Parental consent required before displaying student plan | Dashboard route middleware checks `parent.consent_status = 'verified'` before serving plan data | Integration test + E2E |
| 72-hour FTC breach notification | See Incident Response Plan | Runbook `runbooks/coppa-breach-response.md` |
| Data deletion within 48 hours | `DELETE /api/v1/students/{id}` cascades to all Stage 2 tables (FK `ON DELETE CASCADE`) | Integration test |
| No third-party analytics receiving student PII | PostHog events contain only `student_id` hash; no name, email, or school | Privacy review + PostHog config audit |

**COPPA 2025 Final Rule Updates (Effective April 22, 2026):**
- Strengthened data minimization: Stage 2 audit confirms `plan_modules.bkt_history` contains only mathematical state (no behavioral/interest data).
- New security requirements: Redis keys containing student data use separate keyspace (`mathpath:student:*`) with Redis AUTH; LangGraph Worker has read-only access to student-adjacent tables.
- Expanded PII definition: `plan_modules` timestamps (e.g., `started_at`) could infer behavioral patterns; these are restricted to parent/admin access only (student API responses omit timestamps).

#### 4.3.2 Incident Response Plan

**For Stage 2 specific incidents:**

| Incident Type | Detect | Contain | Eradicate | Recover | Post-Mortem |
|---|---|---|---|---|---|
| LLM generates inappropriate question that reaches students | Student/parent report → Datadog content_flagged alert | Immediately set `questions.is_active = FALSE` for flagged question; stop generation worker | Review entire question batch from same job; audit prompt template | Re-enable worker after root cause fixed | Within 48 hours; update safety contracts |
| Student plan data exposed to wrong parent | Auth0 anomaly detection → Datadog 403 spike | Revoke affected JWT tokens; log all access to affected plan | Fix RBAC middleware; audit recent access logs | Deploy fix; notify affected parents | 72-hour COPPA breach assessment |
| LLM API key leaked in logs | Secret scanning (Trufflehog) detects in logs | Immediately rotate key; disable old key in AWS Secrets Manager | Purge logs containing key; rotate all secrets as precaution | Deploy with new key | Audit all log sinks for PII/secrets |
| Generation budget exceeded ($10/day hard stop) | Redis counter → BudgetExceededError | Workers automatically stop; alert fires | Review anomalous spend (large batch job, pricing change) | Adjust budget limits; resume workers | FinOps review; consider generation rate limiting |

#### 4.3.3 Secret Rotation Schedule

| Secret | Store | Rotation Period | Rotation Method |
|---|---|---|---|
| OpenAI API Key | AWS Secrets Manager | 90 days | Manual rotation; update in ECS task environment |
| Anthropic API Key | AWS Secrets Manager | 90 days | Manual rotation |
| Auth0 Client Secret | AWS Secrets Manager | 90 days | Auth0 API + Secrets Manager Lambda rotator |
| PostgreSQL password | AWS Secrets Manager | 90 days | RDS Password Rotation Lambda |
| Redis AUTH token | AWS Secrets Manager | 90 days | ElastiCache maintenance window rotation |

#### 4.3.4 RBAC Access Control Matrix

| Role | Read Plan | Write Plan | Create Gen Job | Approve Question | View All Students | Access Admin Routes |
|---|---|---|---|---|---|---|
| Student | Own only | No | No | No | No | No |
| Parent | Own children only | No | No | No | No | No |
| Content Reviewer | No | No | No | Yes (review queue) | No | Review only |
| Admin | All | All | Yes | Yes | Yes | Yes |
| LangGraph Worker (service) | No student data | Write `generated_questions` only | No | No | No | No |

---

### 4.4 DevSecOps Pipeline

```yaml
# .github/workflows/ci.yml — Stage 2 security gates

name: CI — Stage 2
on: [pull_request, push]

jobs:
  python-sast:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Bandit SAST scan
        run: bandit -r apps/api/src services/ -l -ii --exit-zero -f json -o bandit_report.json
      - name: Fail on HIGH severity
        run: python scripts/bandit_gate.py bandit_report.json --fail-on HIGH

  typescript-sast:
    runs-on: ubuntu-latest
    steps:
      - name: ESLint security plugin
        run: pnpm --filter web lint:security

  container-scan:
    runs-on: ubuntu-latest
    steps:
      - name: Trivy — API image
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: mathpath-api:${{ github.sha }}
          severity: CRITICAL,HIGH
          exit-code: 1
      - name: Trivy — LangGraph Worker image
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: mathpath-gen-worker:${{ github.sha }}
          severity: CRITICAL,HIGH
          exit-code: 1

  sbom-generation:
    runs-on: ubuntu-latest
    steps:
      - name: Generate SBOM (CycloneDX)
        run: trivy image --format cyclonedx --output sbom-stage2.json mathpath-api:${{ github.sha }}
      - uses: actions/upload-artifact@v4
        with:
          name: sbom-stage2
          path: sbom-stage2.json

  dependency-audit:
    runs-on: ubuntu-latest
    steps:
      - name: Python dependencies audit
        run: pip-audit --requirement apps/api/requirements.txt
      - name: Node dependencies audit
        run: pnpm audit --audit-level high

  terraform-scan:
    runs-on: ubuntu-latest
    if: contains(github.event.pull_request.changed_files, 'infrastructure/')
    steps:
      - name: Trivy IaC scan
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: config
          scan-ref: infrastructure/terraform/
          exit-code: 1
          severity: CRITICAL,HIGH

  dast-weekly:
    runs-on: ubuntu-latest
    if: github.event_name == 'schedule'
    steps:
      - name: OWASP ZAP API scan (staging)
        uses: zaproxy/action-api-scan@v0.5.0
        with:
          target: ${{ secrets.STAGING_API_URL }}/api/v1/openapi.json
          fail_action: true
          cmd_options: '-c zap-config.conf'
```

---

## 5. Manual QA Plan

Manual QA covers the test categories that cannot be fully automated: mathematical content accuracy review, child-appropriate experience validation, real-device testing, and LLM output spot-checks.

---

### 5.1 Question Content Accuracy Review

**Who**: Math educator with K–4 experience (minimum 1 hour/week during Months 4–6 active generation phase).

**Process**: Reviewer works through the `content_review_queue` in the admin UI. Each question is reviewed against:

| Check | Description | Pass Criterion |
|---|---|---|
| Mathematical correctness | Is the stated answer definitively correct? | Yes — no ambiguity |
| Distractor plausibility | Do wrong answers reflect genuine student misconceptions? | Each distractor has a believable error path |
| Question clarity | Would a 4th grader understand what's being asked? | No ambiguous language; no double-barrel questions |
| Solution steps accuracy | Are the solution steps pedagogically correct? | Steps lead unambiguously to the correct answer |
| Standard alignment | Does the question actually test the tagged standard? | Primary skill required matches standard description |
| Reading level feel | Does it feel right for a 9-year-old? | Not dumbed down; not unexpectedly complex |
| Oregon context authenticity | Are Oregon references accurate and not stereotyping? | References are geographically/culturally accurate |

**Random Spot-Check Protocol** (for auto-approved questions):
- Weekly: Sample 20 auto-approved questions randomly from the past week's generation runs.
- Reviewer rates each: Pass / Pass with Minor Issue / Fail.
- If Fail rate > 5%: halt auto-approval; increase human review threshold.
- If Fail rate > 10%: pause generation; audit prompt template.

**Question Pool Coverage Audit** (Monthly):
- Count questions per `(standard_code, difficulty_level, question_type)` combination.
- Flag any combination with < 5 validated questions (insufficient for adaptive engine).
- Schedule targeted generation jobs to fill gaps.

---

### 5.2 Dashboard Usability Testing with Children

**Who**: 2–4 children aged 9–10 (recruited from founder network; parental consent required; COPPA-compliant session recording consent obtained).

**When**: End of Month 5 (after dashboards are feature-complete) and once more at end of Month 6 (after first round of feedback incorporated).

**Session Format**: 30-minute observed session, child uses the student dashboard on an iPad.

**Scenarios**:

1. **Onboarding scenario**: "Your math test is done! Open the app and find out what you're going to learn."
   - Observe: Does the student understand the learning roadmap metaphor without explanation?
   - Observe: Does the student understand what "Locked" means?
   - Observe: Can the student find and tap the "Start" button for their first module?

2. **Progress understanding**: After 1 practice session (completed before the test), ask: "How far along are you in your math journey?"
   - Observe: Can the student interpret the progress donut/percentage?
   - Observe: Does the student understand what "Getting There" means for their current module?

3. **Badge scenario**: Award a `first_session` badge mid-session. Observe: Does the celebration modal delight the student? Can they find their badge collection?

4. **Streak scenario**: Show a streak of 3. Ask: "What does this mean?" Observe: Do they understand the streak concept?

**Pass Criteria**:
- 3 out of 4 children complete scenario 1 without adult guidance.
- All 4 children express positive emotional response to badge award (facial expression / verbal exclamation).
- No child expresses confusion about locked modules (tooltip explains clearly).

**Documentation**: Screencasted session (face not recorded; screen + audio only). Findings written up in `docs/usability-findings-stage2.md`.

---

### 5.3 Accessibility Testing with Assistive Technology

**Who**: QA engineer with VoiceOver proficiency.

**When**: Prior to each deployment to production.

**Scope**: Student dashboard (`/students/{id}`), parent dashboard (`/overview`), learning plan view (`/students/{id}/learning-plan`).

**Test Cases:**

| Test | Tool | Pass Criterion |
|---|---|---|
| TAB-001: Keyboard navigation through learning roadmap | Keyboard only (no mouse) | All module nodes reachable and activatable via Tab/Enter |
| TAB-002: Screen reader announces module status | VoiceOver (Safari/iOS) | "Multiplication Facts, Available, Start button" (or equivalent) announced for each node |
| TAB-003: Badge celebration modal accessible | VoiceOver | Modal focus trap works; Escape closes; badge name announced |
| TAB-004: Streak counter announced | VoiceOver | "5-day streak" announced; not just emoji |
| TAB-005: Progress percentage announced | VoiceOver | "17 percent complete" announced on donut chart |
| TAB-006: Parent weekly chart accessible | Keyboard + VoiceOver | Bar chart has accessible title; data table fallback visible to screen reader |
| TAB-007: Locked module tooltip keyboard-accessible | Keyboard only | Tooltip triggered by focus (not just hover); tooltip text read by screen reader |
| TAB-008: Touch target size on iPad | Physical measurement | All interactive elements ≥ 48×48px (WCAG 2.5.5) |

**Color contrast verification** (performed with Colour Contrast Analyser):
- Module status colors against white background: all must meet WCAG AA (4.5:1 for normal text, 3:1 for large text/UI).
- Streak flame icon: text adjacent to icon has sufficient contrast.
- Progress bars: bar color against background track meets 3:1.

---

### 5.4 Cross-Device Manual Testing Matrix

| Device | OS | Browser | Screen Size | Dashboard | Priority |
|---|---|---|---|---|---|
| iPad Pro 11" | iPadOS 17 | Safari | 1024×1366 | Student + Parent | P0 |
| iPhone 14 | iOS 17 | Safari | 390×844 | Student (mobile layout) | P0 |
| MacBook Pro 14" | macOS 14 | Chrome | 1440×900 | Parent + Admin | P0 |
| Samsung Galaxy S21 | Android 14 | Chrome | 384×854 | Student (mobile layout) | P1 |
| iPad mini 6 | iPadOS 17 | Safari | 744×1133 | Student | P1 |
| Windows 11 PC | Windows 11 | Edge | 1920×1080 | Parent | P1 |
| Chromebook | ChromeOS | Chrome | 1366×768 | Student (school use case) | P1 |

**Mobile Layout Checklist (iPhone-class < 768px):**
- SVG learning roadmap replaces with vertical card list (no horizontal scroll).
- All tap targets ≥ 48×48px.
- No content clipped or overflowing off-screen.
- Streak/badge displays legible without pinch-to-zoom.
- "Continue Practice" CTA button visible without scrolling when module is in progress.

---

### 5.5 LLM Output Quality Spot-Checks (Admin-Facing)

**Who**: Engineer + content reviewer during Months 4–6 weekly review meeting.

**Process**: Admin reviews a randomly sampled set of 10 questions from the past week's auto-approved pool using the admin review interface.

**Spot-check checklist:**
- [ ] Read each question aloud — does it sound natural for a 4th grader?
- [ ] Verify the correct answer by hand (independent calculation, not relying on solution_code).
- [ ] Check that all distractors are clearly wrong (but believably wrong).
- [ ] Confirm no cultural insensitivity, gender bias, or family structure assumptions.
- [ ] Verify Oregon context references are accurate (e.g., Crater Lake is in southern Oregon, not northern).
- [ ] For word problems: ensure all numbers in the problem are internally consistent.
- [ ] Confirm reading level "feels right" — not condescending, not above grade level.

**Document findings** in `docs/qa-log-stage2.md` with date, sample size, issues found, and prompt changes triggered.

---

### 5.6 Parent Experience Walkthrough

**Who**: Engineer acting as a parent persona (no prior system knowledge of specific test student data).

**Scenario**: "You are a parent. Your child just completed their diagnostic assessment. Walk through the parent experience from receiving the plan-ready notification to understanding your child's full learning roadmap."

**Walkthrough steps:**
1. Open email notification: "Jayden's Learning Plan is Ready!" — CTA to parent dashboard.
2. Log in (Auth0 flow) — measure time from link click to dashboard render.
3. Read child plan summary card: within 30 seconds, can you state: (a) your child's track, (b) how many modules they need to complete, (c) the estimated completion date?
4. Click "View Full Plan" — read the module-by-module list. Can you identify: (a) what Jayden is working on NOW, (b) which modules are locked and why, (c) one module Jayden has already mastered?
5. Find the "Time Spent This Week" chart — can you understand it without explanation?
6. Find the badge collection — can you understand what badges Jayden has earned?
7. Find notification preferences — can you turn off weekly emails?

**Pass Criterion**: All 7 steps completable in < 5 minutes with no instructions (self-service).

**Document results**: Note any friction points; create UX issues in GitHub labeled `ux/parent-dashboard`.

---

### 5.7 Performance Perception Testing

**Who**: Engineer with browser DevTools.

**When**: Prior to each production deployment.

**Method**: Navigate key flows on a throttled connection (4G LTE equivalent: 12 Mbps down, 1.5 Mbps up, 50ms RTT) using Chrome DevTools network throttling.

| Page | Acceptable Perceived Load | Actual Measurement | Pass? |
|---|---|---|---|
| Student dashboard first load (cold) | Content visible in < 2s; fully interactive in < 3s | Measure with Lighthouse | |
| Parent dashboard first load (cold) | < 2s to meaningful content | Measure with Lighthouse | |
| Learning plan module detail | < 1s (data already loaded in plan cache) | Measure with Lighthouse | |
| Badge celebration animation | Smooth (no jank); confetti renders in < 500ms | Manual observation | |
| Module roadmap scroll | 60fps on iPad Air 5 | Safari Web Inspector timeline | |

**Core Web Vitals targets** (measured with Lighthouse on staging, simulated desktop):
- LCP (Largest Contentful Paint): < 2.5 seconds.
- CLS (Cumulative Layout Shift): < 0.1 (roadmap SVG must not cause layout shift).
- FID / INP (Interaction to Next Paint): < 200ms.

---

### 5.8 COPPA Consent Flow Manual Walkthrough

**Who**: Engineer + legal reviewer (once per stage deployment).

**Scope**: Every user journey that involves collecting or displaying student data must pass through a verifiable parental consent gate.

**Walkthrough checklist for Stage 2:**
- [ ] Creating a student account → verify consent screen displayed before any diagnostic starts (Stage 1 flow).
- [ ] Accessing student learning plan as parent → verify `consent_status = 'verified'` check is enforced.
- [ ] Parent opts out of weekly email → verify `notification_preferences.weekly_summary = false` stored; next Sunday's Celery job skips this parent.
- [ ] Data deletion request (simulated): call `DELETE /api/v1/students/{id}` → verify cascade deletes `learning_plans`, `plan_modules`, `student_badges`, `student_streaks` → verify Redis cache keys for student cleared within 60 seconds.
- [ ] Verify LLM generation prompts contain no student identifiers by inspecting the most recent 10 `generation_jobs.raw_response` records.
- [ ] Audit log captures: plan generation, badge awards, parent login, data deletion requests.

**Zero-defect requirement**: Any COPPA consent flow bug discovered in this walkthrough is a P0 critical issue — blocks deployment to production until resolved.

---

*End of Document — MathPath Oregon Stage 2 SDLC Lifecycle Document*
*Generated: 2026-04-04 | Next Review: Start of Stage 3 (Month 7)*
