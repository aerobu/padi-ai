# Engineering Plan — Stage 2: Adaptive Learning Engine (Months 4–6)

**Document ID:** ENG-002  
**Version:** 1.0  
**Date:** 2026-04-04  
**Author:** Principal Software Engineer  
**Status:** Draft  
**Prerequisite:** ENG-001 (Stage 1) must be complete and deployed.

> **Stage 2 Solo Development Estimate:** 120–160 agent-hours | Calendar: 5–6 months  
> **Key tasks:** Skill dependency graph (25–35 hrs), Learning plan generator (30–40 hrs), LLM generation pipeline (35–50 hrs), Dashboards (20–30 hrs)  
> **External dependency:** Curriculum specialist contractor must be engaged before generated questions go into production

**Scope:** Skill dependency graph, AI question generation pipeline with validation, learning plan generator, student and parent dashboards with progress tracking, badges, and streaks.

---

## 1. High-Level Architecture

### 1.1 System Context Diagram (C4 Level 1)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        EXTERNAL ACTORS                                  │
│                                                                         │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────────┐     │
│   │  Parent   │    │ Student  │    │  Admin   │    │Content       │     │
│   │ (Browser) │    │(Browser) │    │(Browser) │    │Reviewer      │     │
│   └────┬─────┘    └────┬─────┘    └────┬─────┘    └──────┬───────┘     │
│        │               │               │                  │             │
└────────┼───────────────┼───────────────┼──────────────────┼─────────────┘
         │ HTTPS         │ HTTPS         │ HTTPS            │ HTTPS
         ▼               ▼               ▼                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                   PADI.AI SYSTEM BOUNDARY                       │
│                                                                         │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                    Next.js Web App (Vercel)                     │   │
│   │   • Parent dashboard (child progress, learning plan view)      │   │
│   │   • Student dashboard (current lesson, badges, streaks)        │   │
│   │   • Admin: generation jobs, review queue, skill graph editor   │   │
│   │   • Content reviewer: question approval/rejection interface    │   │
│   └────────────────────────────┬────────────────────────────────────┘   │
│                                │ HTTPS (REST API)                       │
│   ┌────────────────────────────▼────────────────────────────────────┐   │
│   │                  FastAPI API Server (ECS/Fargate)               │   │
│   │   • All Stage 1 capabilities (auth, standards, assessment)     │   │
│   │   • Skill dependency graph service                             │   │
│   │   • Learning plan generator                                    │   │
│   │   • Question generation job dispatcher                         │   │
│   │   • Content review queue management                            │   │
│   │   • Badge and streak tracking                                  │   │
│   └──────┬─────────────┬───────────────┬───────────────────────────┘   │
│          │             │               │                               │
│   ┌──────▼──────┐ ┌───▼────────┐ ┌────▼───────────┐                   │
│   │ PostgreSQL  │ │   Redis    │ │ LangGraph 0.2  │                   │
│   │   17 RDS    │ │ElastiCache │ │ Worker Process │                   │
│   │ + pgvector  │ │   7.x      │ │ (ECS Task)     │                   │
│   │ + ltree     │ │            │ │                │                   │
│   └─────────────┘ └────────────┘ └────────┬───────┘                   │
│                                           │                            │
└───────────────────────────────────────────┼────────────────────────────┘
         │          │           │            │           │
         ▼          ▼           ▼            ▼           ▼
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐
│  Auth0   │ │ AWS SES  │ │ PostHog  │ │ OpenAI   │ │ Anthropic    │
│(Identity)│ │ (Email)  │ │(Analytic)│ │ (o3-mini)│ │(Claude 4.6)  │
└──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────────┘
```

**New in Stage 2:**
- **Content Reviewer** actor: educators who review AI-generated questions
- **LangGraph Worker**: Separate ECS task running the question generation pipeline
- **OpenAI (o3-mini)**: Primary model for math question generation (structured output)
- **Anthropic (Claude Sonnet 4.6)**: Backup model and age-appropriateness classification

### 1.2 Container Diagram (C4 Level 2)

```
┌──────────────────────────────────────────────────────────────────────┐
│                     DEPLOYMENT CONTAINERS (Stage 2)                  │
│                                                                      │
│  ┌─────────────────────────────────────┐                             │
│  │   Next.js 15 Web App               │ ← Vercel Edge Network       │
│  │   ─────────────────────             │                             │
│  │   NEW pages:                        │                             │
│  │   • /students/{id}/dashboard        │                             │
│  │   • /students/{id}/learning-plan    │                             │
│  │   • /students/{id}/practice         │                             │
│  │   • /admin/skill-graph              │                             │
│  │   • /admin/generation-jobs          │                             │
│  │   • /admin/review-queue             │                             │
│  └──────────┬──────────────────────────┘                             │
│             │ HTTPS/JSON                                             │
│             ▼                                                        │
│  ┌─────────────────────────────────────┐                             │
│  │   FastAPI API Server                │ ← ECS Fargate               │
│  │   ─────────────────────             │                             │
│  │   NEW routers:                      │                             │
│  │   • /skill-graph                    │                             │
│  │   • /learning-plans                 │                             │
│  │   • /admin/generation-jobs          │                             │
│  │   • /admin/review-queue             │                             │
│  │   • /students/{id}/badges           │                             │
│  │   • /students/{id}/streak           │                             │
│  └──────┬──────────┬──────────┬────────┘                             │
│         │          │          │                                       │
│  TCP:5432    TCP:6379   HTTPS (internal)                             │
│         │          │          │                                       │
│  ┌──────▼──────┐ ┌▼──────────┐ ┌──────▼───────────────────┐         │
│  │ PostgreSQL  │ │  Redis    │ │ LangGraph Question Gen   │         │
│  │   17 RDS    │ │ElastiCache│ │ Worker (ECS Fargate)     │         │
│  │             │ │           │ │ ─────────────────────     │         │
│  │ NEW tables: │ │ NEW usage:│ │ • Polls generation_jobs  │         │
│  │ • skill_dep │ │ • Job     │ │ • Calls o3-mini API      │         │
│  │   _graph    │ │   queues  │ │ • Validates via sandbox   │         │
│  │ • learning_ │ │ • LPlan   │ │ • pgvector dedup check   │         │
│  │   plans     │ │   cache   │ │ • Routes to review queue  │         │
│  │ • gen_jobs  │ │ • Badge   │ └───────────┬──────────────┘         │
│  │ • review_q  │ │   events  │             │                         │
│  │ • badges    │ └───────────┘       ┌─────▼──────┐                  │
│  │ • streaks   │                     │  OpenAI    │                  │
│  └─────────────┘                     │  o3-mini   │                  │
│                                      └────────────┘                  │
└──────────────────────────────────────────────────────────────────────┘

Data Flows (NEW in Stage 2):
  FastAPI ──HTTPS──▶ LangGraph Worker (internal ALB or SQS)
  LangGraph ──HTTPS──▶ OpenAI API (o3-mini, structured output)
  LangGraph ──HTTPS──▶ Anthropic API (Claude 4.6, content safety)
  LangGraph ──TCP──▶ PostgreSQL (pgvector similarity search, job status)
  LangGraph ──subprocess──▶ Python sandbox (solution verification)
  Redis ◀──TCP──▶ FastAPI (job queue, learning plan cache)
```

### 1.3 Component Diagram (C4 Level 3) — Backend

```
┌─────────────────────────────────────────────────────────────────────────┐
│              FastAPI API Server — Stage 2 Components                    │
│                                                                         │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────┐  ┌──────────────┐ │
│  │ SkillGraph   │  │LearningPlan  │  │ Generation  │  │ Review Queue │ │
│  │ Router       │  │  Router      │  │ Jobs Router │  │   Router     │ │
│  │ /skill-graph │  │/learning-    │  │/admin/gen-  │  │/admin/review │ │
│  │              │  │  plans       │  │  jobs       │  │  -queue      │ │
│  └──────┬───────┘  └──────┬───────┘  └─────┬───────┘  └──────┬───────┘ │
│         │                 │                │                  │         │
│  ┌──────▼───────┐  ┌──────▼───────┐  ┌─────▼────────┐ ┌─────▼───────┐ │
│  │ SkillGraph   │  │LearningPlan  │  │ Question     │ │ Review      │ │
│  │ Service      │  │  Service     │  │ Generation   │ │ Service     │ │
│  │              │  │              │  │ Service      │ │             │ │
│  │• get_graph() │  │• generate()  │  │              │ │• get_queue()│ │
│  │• get_prereqs │  │• determine_  │  │• gen_for_    │ │• approve()  │ │
│  │• topo_sort() │  │  track()     │  │  standard()  │ │• reject()   │ │
│  │• remediation │  │• sequence_   │  │• validate()  │ │• bulk_      │ │
│  │  _sequence() │  │  modules()   │  │• batch_gen() │ │  approve()  │ │
│  └──────┬───────┘  │• estimate_   │  └──────┬───────┘ └──────┬──────┘ │
│         │          │  completion() │         │                │        │
│         │          └──────┬───────┘         │                │        │
│  ┌──────▼───────┐  ┌──────▼───────┐  ┌──────▼───────┐ ┌─────▼──────┐ │
│  │NetworkX      │  │ BKT Service  │  │LangGraph     │ │ Question   │ │
│  │DiGraph       │  │ (Stage 1)    │  │Pipeline      │ │ Repository │ │
│  │(in-memory    │  └──────────────┘  │Orchestrator  │ │ (Stage 1)  │ │
│  │ graph cache) │                    │              │ └────────────┘ │
│  └──────────────┘                    │• prompt_build│                 │
│                                      │• llm_call    │                 │
│  ┌──────────────┐  ┌──────────────┐  │• sandbox_run │                 │
│  │ Badge        │  │ Streak       │  │• dedup_check │                 │
│  │ Service      │  │ Service      │  │• route_review│                 │
│  │              │  │              │  └──────────────┘                 │
│  │• check_and   │  │• record_     │                                   │
│  │  _award()    │  │  activity()  │                                   │
│  │• get_all()   │  │• get_streak()│                                   │
│  └──────────────┘  └──────────────┘                                   │
│                                                                         │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  REPOSITORY LAYER (NEW)                                           │ │
│  │  SkillGraphRepo · LearningPlanRepo · GenerationJobRepo ·         │ │
│  │  ReviewQueueRepo · BadgeRepo · StreakRepo                         │ │
│  └────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.4 Component Diagram — Frontend (Next.js, Stage 2 Additions)

```
app/
├── ... (all Stage 1 routes preserved)
│
├── (dashboard)/
│   ├── ... (Stage 1 routes)
│   ├── students/
│   │   └── [studentId]/
│   │       ├── page.tsx               # SC+CC: Student dashboard (progress overview)
│   │       ├── learning-plan/
│   │       │   └── page.tsx           # SC+CC: Learning plan view + module list
│   │       ├── practice/
│   │       │   ├── page.tsx           # CC: Practice session launcher
│   │       │   └── [sessionId]/
│   │       │       └── page.tsx       # CC: Practice question session
│   │       ├── badges/
│   │       │   └── page.tsx           # SC: Badge collection display
│   │       └── progress/
│   │           └── page.tsx           # SC+CC: Detailed progress charts
│   └── overview/
│       └── page.tsx                   # SC: Multi-child overview for parent
│
├── (admin)/
│   ├── ... (Stage 1 admin routes)
│   ├── skill-graph/
│   │   └── page.tsx                   # CC: Interactive graph visualization (D3)
│   ├── generation-jobs/
│   │   ├── page.tsx                   # CC: Job list + create form
│   │   └── [jobId]/
│   │       └── page.tsx               # CC: Job detail + generated questions
│   └── review-queue/
│       └── page.tsx                   # CC: Question review interface

components/
├── ... (all Stage 1 components)
├── dashboard/
│   ├── student-progress-card.tsx      # CC: Progress ring + mastery bars
│   ├── learning-plan-timeline.tsx     # CC: Visual module timeline
│   ├── skill-mastery-chart.tsx        # CC: Radar/bar chart (Recharts)
│   ├── streak-calendar.tsx            # CC: GitHub-style activity heatmap
│   ├── badge-grid.tsx                 # CC: Badge collection display
│   └── daily-goal-tracker.tsx         # CC: Ring progress for daily goal
├── practice/
│   ├── practice-question-card.tsx     # CC: Question with hints + scaffolding
│   └── session-complete.tsx           # CC: Session summary + badges earned
├── admin/
│   ├── graph-editor.tsx               # CC: D3 force-directed graph
│   ├── job-form.tsx                   # CC: Generation job creation form
│   ├── review-card.tsx                # CC: Question review with approve/reject
│   └── review-diff.tsx               # CC: Side-by-side original vs edited

stores/
├── ... (Stage 1 stores)
├── learning-plan-store.ts             # Current plan, active module, progress
├── practice-store.ts                  # Practice session state (like assessment-store)
└── dashboard-store.ts                 # Dashboard filters, time range
```

**New Zustand Store (Stage 2):**

```typescript
// stores/learning-plan-store.ts
import { create } from 'zustand';

interface PlanModule {
  id: string;
  standardCode: string;
  standardTitle: string;
  status: 'locked' | 'available' | 'in_progress' | 'completed';
  lessonCount: number;
  lessonsCompleted: number;
  estimatedMinutes: number;
  prerequisites: string[];
}

interface LearningPlanState {
  planId: string | null;
  studentId: string | null;
  track: 'catch_up' | 'on_track' | 'accelerate' | null;
  modules: PlanModule[];
  activeModuleId: string | null;
  overallProgress: number; // 0.0 to 1.0
  estimatedCompletionDate: string | null;

  // Actions
  loadPlan: (plan: {
    planId: string;
    studentId: string;
    track: string;
    modules: PlanModule[];
    estimatedCompletionDate: string;
  }) => void;
  setActiveModule: (moduleId: string) => void;
  updateModuleProgress: (moduleId: string, lessonsCompleted: number) => void;
  completeModule: (moduleId: string) => void;
}

export const useLearningPlanStore = create<LearningPlanState>()((set, get) => ({
  planId: null,
  studentId: null,
  track: null,
  modules: [],
  activeModuleId: null,
  overallProgress: 0,
  estimatedCompletionDate: null,

  loadPlan: (plan) =>
    set({
      planId: plan.planId,
      studentId: plan.studentId,
      track: plan.track as any,
      modules: plan.modules,
      overallProgress: plan.modules.filter((m) => m.status === 'completed').length / plan.modules.length,
      estimatedCompletionDate: plan.estimatedCompletionDate,
    }),

  setActiveModule: (moduleId) =>
    set({ activeModuleId: moduleId }),

  updateModuleProgress: (moduleId, lessonsCompleted) =>
    set((state) => ({
      modules: state.modules.map((m) =>
        m.id === moduleId
          ? { ...m, lessonsCompleted, status: lessonsCompleted >= m.lessonCount ? 'completed' : 'in_progress' }
          : m
      ),
    })),

  completeModule: (moduleId) =>
    set((state) => {
      const updated = state.modules.map((m) =>
        m.id === moduleId ? { ...m, status: 'completed' as const, lessonsCompleted: m.lessonCount } : m
      );
      // Unlock modules whose prerequisites are all completed
      const completedCodes = new Set(updated.filter((m) => m.status === 'completed').map((m) => m.standardCode));
      const unlocked = updated.map((m) => {
        if (m.status === 'locked' && m.prerequisites.every((p) => completedCodes.has(p))) {
          return { ...m, status: 'available' as const };
        }
        return m;
      });
      return {
        modules: unlocked,
        overallProgress: unlocked.filter((m) => m.status === 'completed').length / unlocked.length,
      };
    }),
}));
```

### 1.5 Data Flow Diagrams

**Flow 3: AI Question Generation Pipeline**

```
Step  Actor/Component          Action                                Data
────  ────────────────────    ──────────────────────────            ──────────────────
 1    Admin (Browser)         Creates generation job                standard_code, count, difficulties
 2    Next.js (CC)            POST /admin/generation-jobs           { standard: '4.NF.B.3', count: 20,
                                                                      difficulties: [1,2,3,4,5] }
 3    FastAPI GenJobs Router  Validates admin auth, creates job     →
 4    FastAPI                 INSERT INTO generation_jobs           status='queued'
 5    FastAPI                 PUBLISH to Redis queue                job_id message
 6    FastAPI                 Returns { jobId, status: 'queued' }

 7    LangGraph Worker        SUBSCRIBE Redis queue, picks up job   job_id
 8    LangGraph Worker        UPDATE generation_jobs status='running'
 9    LangGraph Worker        FOR EACH (difficulty, batch) in job:

10      LangGraph             Build prompt from standard template:
                              • Standard code + description
                              • Difficulty level (1-5)
                              • Context theme (randomly selected: animals, sports, cooking, etc.)
                              • Oregon-specific context (Portland, Crater Lake, etc.)
                              • Age-appropriate vocabulary constraints
                              • Structured output JSON schema

11      LangGraph             Call o3-mini API with structured output
                              model: 'o3-mini'
                              response_format: { type: 'json_schema', schema: QuestionSchema }

12      LangGraph             Parse response → GeneratedQuestion    stem, options, correct, explanation,
                                                                    solution_code (Python)

13      LangGraph             VALIDATION STEP 1: Execute solution_code
                              • Create subprocess with 5s timeout
                              • Run embedded Python solution
                              • Verify output matches expected answer
                              IF FAILS: mark validation_failed, continue

14      LangGraph             VALIDATION STEP 2: Age-appropriateness
                              • Call Claude Sonnet 4.6 classifier:
                                "Is this math question appropriate for a 9-10 year old?"
                              • Check for: violence, inappropriate themes, bias, 
                                cultural insensitivity
                              IF FAILS: mark content_flagged, continue

15      LangGraph             VALIDATION STEP 3: Dedup check (pgvector)
                              • Generate embedding of question stem
                              • SELECT * FROM questions WHERE 
                                1 - (content_embedding <=> new_embedding) > 0.90
                              IF SIMILAR FOUND: mark duplicate, continue

16      LangGraph             VALIDATION STEP 4: Mathematical correctness
                              • Verify all distractors are wrong
                              • Verify correct answer is unambiguous
                              • Check difficulty alignment (word count, operation count)

17      LangGraph             Compute confidence score:
                              confidence = (solution_passed * 0.4 +
                                          age_appropriate * 0.2 +
                                          not_duplicate * 0.2 +
                                          math_correct * 0.2)

18      LangGraph             INSERT INTO generated_questions      all validation results
19      LangGraph             INSERT INTO question_validation_results

20      LangGraph             IF confidence >= 0.85:
                                INSERT INTO questions (status='active', source='ai_generated')
                                AUTO-APPROVED
                              ELSE:
                                INSERT INTO content_review_queue (status='pending')
                                NEEDS HUMAN REVIEW

 [End FOR EACH loop]

21    LangGraph Worker        UPDATE generation_jobs status='completed'
                              results: { total: 20, auto_approved: 14, needs_review: 4, failed: 2 }
22    FastAPI                 (Polling) Admin checks GET /admin/generation-jobs/{id}
23    Admin (Browser)         Views results, navigates to review queue
```

> **Curriculum Specialist Integration (Stage 2):** The automated validation pipeline must be supplemented with human expert review from Stage 2 onward. Engage an Oregon-credentialed elementary math educator (10–15 hrs/month, $75–$100/hr via Upwork) to review 30–50 generated questions per sprint. See 04-prd-stage2.md for full role spec. Build an admin review queue UI (simple CRUD with approve/reject/edit) to make this workflow efficient — budget 8–12 hrs for the review queue component.

**Flow 4: Learning Plan Generation**

```
Step  Actor/Component          Action                                Data
────  ────────────────────    ──────────────────────────            ──────────────────
 1    System (auto-trigger)   Assessment completed (Stage 1 flow)   assessment_id, student_id
      OR Parent (Browser)     Clicks "Generate Learning Plan"

 2    Next.js (CC)            POST /learning-plans                  { studentId, assessmentId? }
 3    FastAPI LPlan Router    Validates parent auth, student ownership

 4    LearningPlan Service    Load latest BKT skill states:
                              SELECT * FROM student_skill_states
                              WHERE student_id = :student_id

 5    LearningPlan Service    Determine track:
                              overall_score = AVG(p_mastery) across all standards
                              IF overall_score < 0.40: track = 'catch_up'
                              ELIF overall_score < 0.70: track = 'on_track'
                              ELSE: track = 'accelerate'

 6    SkillGraph Service      Load dependency graph into NetworkX DiGraph
                              (cached in Redis for 1 hour)

 7    LearningPlan Service    Identify deficient skills:
                              deficient = [s for s in skill_states 
                                          if s.p_mastery < MASTERY_THRESHOLD]

 8    SkillGraph Service      Get remediation sequence:
                              • For each deficient skill, find all prerequisites
                              • Build subgraph of needed skills
                              • Topological sort with priority weighting:
                                weight = centrality * (1 - p_mastery)
                              • Return ordered list of skills to learn

 9    LearningPlan Service    Sequence modules:
                              FOR EACH skill IN remediation_sequence:
                                Create PlanModule:
                                  • standard_code
                                  • lesson_count based on (1 - p_mastery) * base_lessons
                                  • estimated_minutes = lesson_count * 15
                                  • prerequisites = graph.predecessors(skill)
                                  • status = 'locked' | 'available' (if no prereqs)

10    LearningPlan Service    Estimate completion:
                              total_minutes = SUM(module.estimated_minutes)
                              sessions_per_week = 3 (configurable)
                              minutes_per_session = 20
                              weeks = total_minutes / (sessions_per_week * minutes_per_session)
                              completion_date = today + weeks

11    FastAPI                 INSERT INTO learning_plans            plan record
12    FastAPI                 INSERT INTO plan_modules              one per module
13    FastAPI                 INSERT INTO plan_lessons              lessons per module

14    FastAPI                 Cache plan in Redis: `plan:{studentId}:current`
15    FastAPI                 Returns full LearningPlan response

16    Next.js (CC)            Renders learning plan timeline
17    Next.js (CC)            Highlights first available module
```


---

## 2. Detailed System Design

### 2.1 Database Schema (Stage 2 Additions)

All Stage 1 tables remain unchanged. The following tables are added in Stage 2.

```sql
-- =============================================================================
-- PADI.AI — Stage 2 Database Schema (Additions)
-- =============================================================================

-- =============================================================================
-- TABLE: skill_dependency_graph_edges
-- Directed graph edges for skill prerequisite relationships.
-- Uses ltree for hierarchical path queries alongside explicit edges.
-- =============================================================================
CREATE TABLE skill_dependency_graph_edges (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    from_standard   VARCHAR(20) NOT NULL REFERENCES standards(code),
    to_standard     VARCHAR(20) NOT NULL REFERENCES standards(code),
    
    -- Edge properties
    edge_type       VARCHAR(20) NOT NULL DEFAULT 'prerequisite'
                    CHECK (edge_type IN ('prerequisite', 'builds_on', 'corequisite', 'enrichment')),
    weight          NUMERIC(3,2) NOT NULL DEFAULT 1.0
                    CHECK (weight BETWEEN 0.0 AND 1.0),
    -- Higher weight = stronger dependency
    
    -- ltree path for hierarchical queries
    from_path       LTREE NOT NULL,  -- e.g., '4.OA.A.1'
    to_path         LTREE NOT NULL,  -- e.g., '4.OA.A.2'
    
    -- Metadata
    source          VARCHAR(20) NOT NULL DEFAULT 'manual'
                    CHECK (source IN ('manual', 'inferred', 'research')),
    confidence      NUMERIC(3,2) NOT NULL DEFAULT 1.0,
    notes           TEXT,
    
    created_by      UUID REFERENCES users(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Prevent duplicate edges
    CONSTRAINT uq_graph_edge UNIQUE (from_standard, to_standard, edge_type),
    -- Prevent self-loops
    CONSTRAINT chk_no_self_loop CHECK (from_standard <> to_standard)
);

-- Forward traversal: find what depends on this standard
CREATE INDEX idx_graph_from ON skill_dependency_graph_edges (from_standard);
-- Backward traversal: find prerequisites of this standard
CREATE INDEX idx_graph_to ON skill_dependency_graph_edges (to_standard);
-- ltree: find all descendants/ancestors
CREATE INDEX idx_graph_from_path ON skill_dependency_graph_edges USING gist (from_path);
CREATE INDEX idx_graph_to_path ON skill_dependency_graph_edges USING gist (to_path);
-- Edge type filtering
CREATE INDEX idx_graph_type ON skill_dependency_graph_edges (edge_type);

CREATE TRIGGER trg_graph_edges_updated_at
    BEFORE UPDATE ON skill_dependency_graph_edges
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

-- =============================================================================
-- TABLE: learning_plans
-- Generated learning plan for a student based on diagnostic results
-- =============================================================================
CREATE TABLE learning_plans (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id      UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    
    -- Source assessment
    assessment_id   UUID REFERENCES assessments(id),
    
    -- Plan configuration
    track           VARCHAR(20) NOT NULL
                    CHECK (track IN ('catch_up', 'on_track', 'accelerate')),
    status          VARCHAR(20) NOT NULL DEFAULT 'active'
                    CHECK (status IN ('draft', 'active', 'completed', 'archived', 'superseded')),
    
    -- Plan scope
    total_modules   SMALLINT NOT NULL,
    completed_modules SMALLINT NOT NULL DEFAULT 0,
    total_lessons   SMALLINT NOT NULL,
    completed_lessons SMALLINT NOT NULL DEFAULT 0,
    
    -- Estimates
    estimated_total_minutes INTEGER NOT NULL,
    actual_total_minutes    INTEGER NOT NULL DEFAULT 0,
    sessions_per_week       SMALLINT NOT NULL DEFAULT 3,
    minutes_per_session     SMALLINT NOT NULL DEFAULT 20,
    estimated_completion_date DATE NOT NULL,
    
    -- Progress
    overall_progress NUMERIC(5,4) NOT NULL DEFAULT 0.0
                     CHECK (overall_progress BETWEEN 0.0 AND 1.0),
    
    -- Timestamps
    activated_at    TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ,
    
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Current plan for a student (most recent active)
CREATE INDEX idx_plans_student_active ON learning_plans (student_id, status)
    WHERE status = 'active';
-- Assessment linkage
CREATE INDEX idx_plans_assessment ON learning_plans (assessment_id);

CREATE TRIGGER trg_plans_updated_at
    BEFORE UPDATE ON learning_plans
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

CREATE TRIGGER trg_plans_audit
    AFTER INSERT OR UPDATE OR DELETE ON learning_plans
    FOR EACH ROW EXECUTE FUNCTION trigger_audit_log();

-- =============================================================================
-- TABLE: plan_modules
-- Ordered modules within a learning plan, each targeting a specific standard
-- =============================================================================
CREATE TABLE plan_modules (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_id         UUID NOT NULL REFERENCES learning_plans(id) ON DELETE CASCADE,
    
    standard_code   VARCHAR(20) NOT NULL REFERENCES standards(code),
    sequence_order  SMALLINT NOT NULL,       -- Order within plan
    
    -- Module configuration
    status          VARCHAR(20) NOT NULL DEFAULT 'locked'
                    CHECK (status IN ('locked', 'available', 'in_progress', 'completed', 'skipped')),
    
    lesson_count    SMALLINT NOT NULL,
    completed_lessons SMALLINT NOT NULL DEFAULT 0,
    
    -- Timing
    estimated_minutes INTEGER NOT NULL,
    actual_minutes    INTEGER NOT NULL DEFAULT 0,
    
    -- Prerequisites (standard codes that must be completed first)
    prerequisite_module_ids UUID[] DEFAULT '{}',
    
    -- BKT state at module start and end
    entry_p_mastery NUMERIC(5,4),
    exit_p_mastery  NUMERIC(5,4),
    
    started_at      TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ,
    
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT uq_module_plan_order UNIQUE (plan_id, sequence_order),
    CONSTRAINT uq_module_plan_standard UNIQUE (plan_id, standard_code)
);

-- Ordered module retrieval for a plan
CREATE INDEX idx_modules_plan_order ON plan_modules (plan_id, sequence_order);
-- Find available modules
CREATE INDEX idx_modules_status ON plan_modules (plan_id, status)
    WHERE status IN ('available', 'in_progress');

CREATE TRIGGER trg_modules_updated_at
    BEFORE UPDATE ON plan_modules
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

-- =============================================================================
-- TABLE: plan_lessons
-- Individual lessons within a module (question sets with scaffolding)
-- =============================================================================
CREATE TABLE plan_lessons (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    module_id       UUID NOT NULL REFERENCES plan_modules(id) ON DELETE CASCADE,
    
    sequence_order  SMALLINT NOT NULL,
    lesson_type     VARCHAR(20) NOT NULL DEFAULT 'practice'
                    CHECK (lesson_type IN ('instruction', 'practice', 'review', 'assessment')),
    
    title           VARCHAR(200) NOT NULL,
    description     TEXT,
    
    -- Lesson content config
    question_count  SMALLINT NOT NULL DEFAULT 5,
    difficulty_range INT4RANGE NOT NULL DEFAULT '[2,4]',
    
    -- Progress
    status          VARCHAR(20) NOT NULL DEFAULT 'locked'
                    CHECK (status IN ('locked', 'available', 'in_progress', 'completed')),
    score           NUMERIC(5,4),
    time_spent_ms   BIGINT DEFAULT 0,
    
    started_at      TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ,
    
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT uq_lesson_module_order UNIQUE (module_id, sequence_order)
);

CREATE INDEX idx_lessons_module_order ON plan_lessons (module_id, sequence_order);

CREATE TRIGGER trg_lessons_updated_at
    BEFORE UPDATE ON plan_lessons
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

-- =============================================================================
-- TABLE: generation_jobs
-- AI question generation job tracking
-- =============================================================================
CREATE TABLE generation_jobs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Job spec
    standard_code   VARCHAR(20) NOT NULL REFERENCES standards(code),
    requested_count SMALLINT NOT NULL CHECK (requested_count BETWEEN 1 AND 100),
    difficulty_levels SMALLINT[] NOT NULL DEFAULT '{1,2,3,4,5}',
    context_themes  TEXT[] DEFAULT NULL,         -- Optional theme constraints
    model           VARCHAR(50) NOT NULL DEFAULT 'o3-mini',
    
    -- Job status
    status          VARCHAR(20) NOT NULL DEFAULT 'queued'
                    CHECK (status IN ('queued', 'running', 'completed', 'failed', 'cancelled')),
    
    -- Results
    total_generated SMALLINT DEFAULT 0,
    auto_approved   SMALLINT DEFAULT 0,
    needs_review    SMALLINT DEFAULT 0,
    failed_validation SMALLINT DEFAULT 0,
    
    -- Error tracking
    error_message   TEXT,
    retry_count     SMALLINT NOT NULL DEFAULT 0,
    max_retries     SMALLINT NOT NULL DEFAULT 3,
    
    -- Cost tracking
    input_tokens    INTEGER DEFAULT 0,
    output_tokens   INTEGER DEFAULT 0,
    estimated_cost_usd NUMERIC(8,4) DEFAULT 0,
    
    -- Timing
    started_at      TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ,
    
    created_by      UUID NOT NULL REFERENCES users(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Job queue: find next queued job
CREATE INDEX idx_jobs_status ON generation_jobs (status, created_at)
    WHERE status = 'queued';
-- Admin dashboard: recent jobs
CREATE INDEX idx_jobs_created ON generation_jobs (created_at DESC);
-- Jobs by standard
CREATE INDEX idx_jobs_standard ON generation_jobs (standard_code);

CREATE TRIGGER trg_jobs_updated_at
    BEFORE UPDATE ON generation_jobs
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

-- =============================================================================
-- TABLE: generated_questions
-- Raw output from AI generation (before promotion to questions table)
-- =============================================================================
CREATE TABLE generated_questions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id          UUID NOT NULL REFERENCES generation_jobs(id) ON DELETE CASCADE,
    
    -- Content (same schema as questions table)
    standard_code   VARCHAR(20) NOT NULL REFERENCES standards(code),
    difficulty      SMALLINT NOT NULL CHECK (difficulty BETWEEN 1 AND 5),
    question_type   VARCHAR(20) NOT NULL DEFAULT 'multiple_choice',
    stem            TEXT NOT NULL,
    options         JSONB NOT NULL DEFAULT '[]',
    correct_answer  VARCHAR(10) NOT NULL,
    explanation     TEXT,
    solution_code   TEXT,           -- Python code that validates the answer
    
    -- Generation metadata
    model_used      VARCHAR(50) NOT NULL,
    prompt_template VARCHAR(50),
    raw_response    JSONB,          -- Full LLM response for debugging
    generation_time_ms INTEGER,
    
    -- Validation results
    validation_status VARCHAR(20) NOT NULL DEFAULT 'pending'
                      CHECK (validation_status IN ('pending', 'passed', 'failed')),
    confidence_score  NUMERIC(5,4),
    
    -- Embedding for dedup
    content_embedding VECTOR(1536),
    
    -- Promotion tracking
    promoted_to_question_id UUID REFERENCES questions(id),
    promoted_at     TIMESTAMPTZ,
    
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Lookup by job
CREATE INDEX idx_gen_questions_job ON generated_questions (job_id);
-- Dedup: vector similarity search
CREATE INDEX idx_gen_questions_embedding ON generated_questions
    USING ivfflat (content_embedding vector_cosine_ops) WITH (lists = 50);
-- Find by validation status
CREATE INDEX idx_gen_questions_validation ON generated_questions (validation_status);

CREATE TRIGGER trg_gen_questions_updated_at
    BEFORE UPDATE ON generated_questions
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

-- =============================================================================
-- TABLE: question_validation_results
-- Detailed validation results per generated question
-- =============================================================================
CREATE TABLE question_validation_results (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    generated_question_id UUID NOT NULL REFERENCES generated_questions(id) ON DELETE CASCADE,
    
    -- Individual validation checks
    solution_execution_passed BOOLEAN NOT NULL DEFAULT FALSE,
    solution_output           TEXT,
    solution_error            TEXT,
    solution_execution_time_ms INTEGER,
    
    age_appropriateness_passed BOOLEAN NOT NULL DEFAULT FALSE,
    age_appropriateness_score  NUMERIC(5,4),
    age_appropriateness_notes  TEXT,
    
    dedup_passed              BOOLEAN NOT NULL DEFAULT FALSE,
    max_similarity_score      NUMERIC(5,4),     -- Highest cosine similarity found
    similar_question_id       UUID,             -- Most similar existing question
    
    math_correctness_passed   BOOLEAN NOT NULL DEFAULT FALSE,
    math_correctness_notes    TEXT,
    
    difficulty_alignment_passed BOOLEAN NOT NULL DEFAULT FALSE,
    estimated_difficulty        SMALLINT,
    
    -- Aggregate
    overall_passed            BOOLEAN NOT NULL DEFAULT FALSE,
    confidence_score          NUMERIC(5,4) NOT NULL,
    
    created_at                TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_validation_gen_question ON question_validation_results (generated_question_id);

-- =============================================================================
-- TABLE: content_review_queue
-- Human review queue for AI-generated questions that need manual approval
-- =============================================================================
CREATE TABLE content_review_queue (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    generated_question_id UUID NOT NULL REFERENCES generated_questions(id),
    
    status          VARCHAR(20) NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending', 'in_review', 'approved', 'rejected', 'needs_edit')),
    priority        SMALLINT NOT NULL DEFAULT 5
                    CHECK (priority BETWEEN 1 AND 10),
    
    -- Review assignment
    assigned_to     UUID REFERENCES users(id),
    assigned_at     TIMESTAMPTZ,
    
    -- Review decision
    decision_by     UUID REFERENCES users(id),
    decision_at     TIMESTAMPTZ,
    decision_notes  TEXT,
    
    -- If edited before approval
    edited_stem     TEXT,
    edited_options  JSONB,
    edited_answer   VARCHAR(10),
    edited_explanation TEXT,
    
    -- Flags from validation
    flags           TEXT[] DEFAULT '{}',        -- e.g., ['low_confidence', 'near_duplicate']
    confidence_score NUMERIC(5,4),
    
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Pending reviews, highest priority first
CREATE INDEX idx_review_pending ON content_review_queue (status, priority DESC, created_at)
    WHERE status IN ('pending', 'in_review');
-- Assignment tracking
CREATE INDEX idx_review_assigned ON content_review_queue (assigned_to, status);

CREATE TRIGGER trg_review_updated_at
    BEFORE UPDATE ON content_review_queue
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

-- =============================================================================
-- TABLE: student_badges
-- Gamification: badges earned by students
-- =============================================================================
CREATE TABLE student_badges (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id      UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    
    badge_type      VARCHAR(50) NOT NULL,
    -- Badge types: 'first_assessment', 'domain_mastered_OA', 'domain_mastered_NBT',
    -- 'domain_mastered_NF', 'domain_mastered_GM', 'domain_mastered_DR',
    -- 'streak_3', 'streak_7', 'streak_14', 'streak_30',
    -- 'plan_25_pct', 'plan_50_pct', 'plan_75_pct', 'plan_complete',
    -- 'speed_demon' (5 correct in < 30s each), 'perfect_lesson',
    -- 'all_standards_attempted', 'comeback_kid' (improved from below_par to on_par)
    
    badge_name      VARCHAR(100) NOT NULL,
    badge_description TEXT NOT NULL,
    badge_icon_url  VARCHAR(255) NOT NULL,
    badge_tier      VARCHAR(20) NOT NULL DEFAULT 'bronze'
                    CHECK (badge_tier IN ('bronze', 'silver', 'gold', 'platinum')),
    
    -- Context
    earned_context  JSONB,     -- { "standard_code": "4.OA", "streak_days": 7, etc. }
    
    earned_at       TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Prevent duplicate badge awards
    CONSTRAINT uq_student_badge UNIQUE (student_id, badge_type)
);

-- Student's badge collection
CREATE INDEX idx_badges_student ON student_badges (student_id, earned_at DESC);
-- Badge type analytics
CREATE INDEX idx_badges_type ON student_badges (badge_type);

-- =============================================================================
-- TABLE: student_streaks
-- Daily activity tracking for streak calculation
-- =============================================================================
CREATE TABLE student_streaks (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id      UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    
    -- Current streak
    current_streak_days INTEGER NOT NULL DEFAULT 0,
    longest_streak_days INTEGER NOT NULL DEFAULT 0,
    
    -- Last activity
    last_activity_date DATE NOT NULL DEFAULT CURRENT_DATE,
    
    -- Activity log (per-day record)
    activity_dates  DATE[] DEFAULT '{}',        -- Array of active dates (last 90 days)
    
    -- Weekly/monthly aggregates
    activities_this_week  SMALLINT NOT NULL DEFAULT 0,
    activities_this_month SMALLINT NOT NULL DEFAULT 0,
    
    -- Total statistics
    total_practice_sessions INTEGER NOT NULL DEFAULT 0,
    total_questions_answered INTEGER NOT NULL DEFAULT 0,
    total_time_spent_minutes INTEGER NOT NULL DEFAULT 0,
    
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT uq_student_streak UNIQUE (student_id)
);

-- Quick lookup by student
CREATE INDEX idx_streaks_student ON student_streaks (student_id);
-- Find students with active streaks (for badge checks)
CREATE INDEX idx_streaks_active ON student_streaks (current_streak_days DESC)
    WHERE current_streak_days > 0;

CREATE TRIGGER trg_streaks_updated_at
    BEFORE UPDATE ON student_streaks
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

-- =============================================================================
-- RLS POLICIES (Stage 2 additions)
-- =============================================================================
ALTER TABLE learning_plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE plan_modules ENABLE ROW LEVEL SECURITY;
ALTER TABLE plan_lessons ENABLE ROW LEVEL SECURITY;
ALTER TABLE student_badges ENABLE ROW LEVEL SECURITY;
ALTER TABLE student_streaks ENABLE ROW LEVEL SECURITY;

-- Learning plans: parent can see their children's plans
CREATE POLICY plans_parent_children ON learning_plans
    FOR ALL
    USING (
        student_id IN (
            SELECT id FROM students
            WHERE parent_id = current_setting('app.current_user_id', true)::uuid
        )
    );

-- Badges: parent can see their children's badges
CREATE POLICY badges_parent_children ON student_badges
    FOR ALL
    USING (
        student_id IN (
            SELECT id FROM students
            WHERE parent_id = current_setting('app.current_user_id', true)::uuid
        )
    );

-- Streaks: parent can see their children's streaks
CREATE POLICY streaks_parent_children ON student_streaks
    FOR ALL
    USING (
        student_id IN (
            SELECT id FROM students
            WHERE parent_id = current_setting('app.current_user_id', true)::uuid
        )
    );

-- Admin full access on all new tables
CREATE POLICY admin_full_plans ON learning_plans FOR ALL
    USING (current_setting('app.current_user_role', true) = 'admin');
CREATE POLICY admin_full_badges ON student_badges FOR ALL
    USING (current_setting('app.current_user_role', true) = 'admin');
CREATE POLICY admin_full_streaks ON student_streaks FOR ALL
    USING (current_setting('app.current_user_role', true) = 'admin');
```


### 2.2 API Design (Stage 2 Endpoints)

---

#### POST /learning-plans

**Auth:** Bearer JWT (parent scope)  
**Rate Limit:** 3 req/min per user  
**Purpose:** Generate a new learning plan based on diagnostic results.

```python
class CreateLearningPlanRequest(BaseModel):
    student_id: UUID
    assessment_id: UUID | None = None  # If None, uses latest completed assessment
    sessions_per_week: int = Field(default=3, ge=1, le=7)
    minutes_per_session: int = Field(default=20, ge=10, le=60)

class CreateLearningPlanResponse(BaseModel):
    plan_id: UUID
    student_id: UUID
    track: Literal['catch_up', 'on_track', 'accelerate']
    status: Literal['active']
    total_modules: int
    total_lessons: int
    estimated_total_minutes: int
    estimated_completion_date: date
    modules: list[PlanModuleSummary]
    created_at: datetime

class PlanModuleSummary(BaseModel):
    module_id: UUID
    standard_code: str
    standard_title: str
    sequence_order: int
    status: Literal['locked', 'available', 'in_progress', 'completed']
    lesson_count: int
    estimated_minutes: int
    prerequisites: list[str]

# Errors:
# 400 Bad Request: {"detail": "No completed assessment found for this student"}
# 403 Forbidden:   {"detail": "Access denied"}
# 409 Conflict:    {"detail": "Active learning plan already exists. Archive it first."}
```

**Side Effects:**
- Run plan generation algorithm (skill graph traversal + module sequencing)
- INSERT into `learning_plans`, `plan_modules`, `plan_lessons`
- Supersede previous active plan (SET status='superseded')
- Cache plan in Redis: `plan:{studentId}:current`

---

#### GET /learning-plans/{id}

**Auth:** Bearer JWT (parent scope — must own student)  
**Rate Limit:** 30 req/min per user

```python
class LearningPlanDetailResponse(BaseModel):
    plan_id: UUID
    student_id: UUID
    track: str
    status: str
    overall_progress: float
    total_modules: int
    completed_modules: int
    total_lessons: int
    completed_lessons: int
    estimated_total_minutes: int
    actual_total_minutes: int
    estimated_completion_date: date
    modules: list[PlanModuleDetail]
    created_at: datetime
    updated_at: datetime

class PlanModuleDetail(BaseModel):
    module_id: UUID
    standard_code: str
    standard_title: str
    sequence_order: int
    status: str
    lesson_count: int
    completed_lessons: int
    estimated_minutes: int
    actual_minutes: int
    entry_p_mastery: float | None
    exit_p_mastery: float | None
    prerequisites: list[str]
    lessons: list[PlanLessonSummary]
    started_at: datetime | None
    completed_at: datetime | None

class PlanLessonSummary(BaseModel):
    lesson_id: UUID
    sequence_order: int
    lesson_type: str
    title: str
    status: str
    score: float | None
    time_spent_ms: int

# Errors:
# 404 Not Found, 403 Forbidden
```

---

#### GET /students/{id}/learning-plan

**Auth:** Bearer JWT (parent scope — must own student)  
**Rate Limit:** 30 req/min per user  
**Purpose:** Get the currently active learning plan for a student.

```python
# Returns same LearningPlanDetailResponse as GET /learning-plans/{id}
# but looks up the active plan automatically.

# Errors:
# 404 Not Found: {"detail": "No active learning plan for this student"}
# 403 Forbidden
```

---

#### GET /skill-graph

**Auth:** Bearer JWT (any authenticated)  
**Rate Limit:** 30 req/min per user

```python
class SkillGraphResponse(BaseModel):
    nodes: list[SkillGraphNode]
    edges: list[SkillGraphEdge]
    metadata: GraphMetadata

class SkillGraphNode(BaseModel):
    standard_code: str
    domain: str
    title: str
    cognitive_level: str
    difficulty: float
    # Optional: student-specific mastery overlay
    p_mastery: float | None = None
    mastery_level: str | None = None

class SkillGraphEdge(BaseModel):
    from_standard: str
    to_standard: str
    edge_type: str
    weight: float

class GraphMetadata(BaseModel):
    total_nodes: int
    total_edges: int
    domains: list[str]
    max_depth: int  # Longest prerequisite chain
```

---

#### POST /admin/generation-jobs

**Auth:** Bearer JWT (admin scope)  
**Rate Limit:** 10 req/min per admin

```python
class CreateGenerationJobRequest(BaseModel):
    standard_code: str = Field(..., pattern=r'^4\.\w+\.\w+(\.\d+)?$')
    count: int = Field(..., ge=1, le=100)
    difficulty_levels: list[int] = Field(default=[1,2,3,4,5])
    context_themes: list[str] | None = None  # Optional: ['animals', 'sports']
    model: Literal['o3-mini', 'claude-sonnet-4.6'] = 'o3-mini'

    @field_validator('difficulty_levels')
    @classmethod
    def validate_difficulties(cls, v):
        assert all(1 <= d <= 5 for d in v), "Difficulty levels must be 1-5"
        return sorted(set(v))

class CreateGenerationJobResponse(BaseModel):
    job_id: UUID
    status: Literal['queued']
    standard_code: str
    requested_count: int
    difficulty_levels: list[int]
    model: str
    created_at: datetime
    estimated_time_minutes: int  # Based on count * avg gen time

# Errors:
# 400 Bad Request: {"detail": "Standard code not found"}
# 403 Forbidden:   {"detail": "Admin access required"}
# 429 Rate Limit
```

**Side Effects:**
- INSERT into `generation_jobs` with `status='queued'`
- PUBLISH job_id to Redis queue `padi:generation:queue`

---

#### GET /admin/generation-jobs/{id}

**Auth:** Bearer JWT (admin scope)  
**Rate Limit:** 30 req/min per admin

```python
class GenerationJobDetailResponse(BaseModel):
    job_id: UUID
    standard_code: str
    standard_title: str
    requested_count: int
    difficulty_levels: list[int]
    model: str
    status: str
    total_generated: int
    auto_approved: int
    needs_review: int
    failed_validation: int
    input_tokens: int
    output_tokens: int
    estimated_cost_usd: float
    error_message: str | None
    created_by: str  # display_name of admin
    started_at: datetime | None
    completed_at: datetime | None
    duration_seconds: float | None
    generated_questions: list[GeneratedQuestionSummary]

class GeneratedQuestionSummary(BaseModel):
    id: UUID
    stem: str  # Truncated to 100 chars
    difficulty: int
    validation_status: str
    confidence_score: float | None
    promoted_to_question_id: UUID | None
```

---

#### GET /admin/review-queue

**Auth:** Bearer JWT (admin scope)  
**Rate Limit:** 30 req/min per admin

```python
class ReviewQueueQueryParams(BaseModel):
    status: Literal['pending', 'in_review', 'approved', 'rejected'] | None = None
    standard_code: str | None = None
    assigned_to_me: bool = False
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)

class ReviewQueueResponse(BaseModel):
    items: list[ReviewQueueItem]
    total: int
    page: int
    page_size: int
    total_pages: int

class ReviewQueueItem(BaseModel):
    review_id: UUID
    generated_question_id: UUID
    standard_code: str
    standard_title: str
    difficulty: int
    stem: str
    options: list[dict]
    correct_answer: str
    explanation: str | None
    status: str
    priority: int
    flags: list[str]
    confidence_score: float
    validation_details: ValidationSummary
    assigned_to: str | None
    created_at: datetime

class ValidationSummary(BaseModel):
    solution_passed: bool
    age_appropriate: bool
    dedup_passed: bool
    math_correct: bool
    max_similarity: float | None
```

---

#### PUT /admin/review-queue/{question_id}

**Auth:** Bearer JWT (admin scope)  
**Rate Limit:** 30 req/min per admin

```python
class ReviewDecisionRequest(BaseModel):
    decision: Literal['approved', 'rejected', 'needs_edit']
    notes: str | None = Field(None, max_length=1000)
    # If decision is 'approved' with edits:
    edited_stem: str | None = None
    edited_options: list[dict] | None = None
    edited_answer: str | None = None
    edited_explanation: str | None = None

class ReviewDecisionResponse(BaseModel):
    review_id: UUID
    status: str
    promoted_to_question_id: UUID | None  # If approved
    decision_at: datetime

# Errors:
# 400 Bad Request: {"detail": "Question is not in reviewable state"}
# 404 Not Found
```

**Side Effects (if approved):**
- INSERT into `questions` with `status='active', source='ai_generated'`
- UPDATE `generated_questions` SET `promoted_to_question_id=..., promoted_at=now()`
- UPDATE `content_review_queue` SET `status='approved', decision_by=..., decision_at=now()`
- UPDATE question count caches

---

#### GET /students/{id}/badges

**Auth:** Bearer JWT (parent scope — must own student)  
**Rate Limit:** 30 req/min per user

```python
class StudentBadgesResponse(BaseModel):
    student_id: UUID
    total_badges: int
    badges: list[BadgeItem]
    next_achievable: list[BadgeProgress]  # Closest unearned badges

class BadgeItem(BaseModel):
    badge_type: str
    badge_name: str
    badge_description: str
    badge_icon_url: str
    badge_tier: str
    earned_at: datetime
    earned_context: dict | None

class BadgeProgress(BaseModel):
    badge_type: str
    badge_name: str
    badge_description: str
    badge_icon_url: str
    progress: float  # 0.0 to 1.0
    requirement_text: str  # "Complete 3 more days for 7-day streak"
```

---

#### GET /students/{id}/streak

**Auth:** Bearer JWT (parent scope — must own student)  
**Rate Limit:** 30 req/min per user

```python
class StudentStreakResponse(BaseModel):
    student_id: UUID
    current_streak_days: int
    longest_streak_days: int
    last_activity_date: date
    is_active_today: bool
    activities_this_week: int
    activities_this_month: int
    total_practice_sessions: int
    total_questions_answered: int
    total_time_spent_minutes: int
    activity_heatmap: list[ActivityDay]  # Last 90 days

class ActivityDay(BaseModel):
    date: date
    questions_answered: int
    time_spent_minutes: int
    sessions: int
    intensity: Literal['none', 'low', 'medium', 'high']
```


### 2.3 Service Layer Design (Stage 2)

```python
# ─────────────────────────────────────────────────────────────────────
# services/skill_graph_service.py
# ─────────────────────────────────────────────────────────────────────
from uuid import UUID
from typing import Optional
import networkx as nx

from app.repositories.skill_graph_repository import SkillGraphRepository
from app.core.redis_client import RedisClient


class SkillGraphService:
    """Manages the skill dependency graph using NetworkX.
    
    The graph is loaded from PostgreSQL into a NetworkX DiGraph and cached
    in Redis for 1 hour. All graph operations run in-memory for performance.
    """

    CACHE_TTL_SECONDS: int = 3600  # 1 hour
    CACHE_KEY: str = "skill_graph:v1"

    def __init__(
        self,
        graph_repo: SkillGraphRepository,
        redis: RedisClient,
    ):
        self._repo = graph_repo
        self._redis = redis
        self._graph: Optional[nx.DiGraph] = None

    async def get_dependency_graph(self) -> nx.DiGraph:
        """Load or retrieve cached skill dependency graph.
        
        Returns a NetworkX DiGraph where:
        - Nodes are standard codes with attributes: { domain, title, difficulty, cognitive_level }
        - Edges represent prerequisites with attributes: { edge_type, weight, confidence }
        - Edge direction: prerequisite → dependent (from_standard → to_standard)
        """
        ...

    def get_prerequisites(self, standard_code: str) -> list[str]:
        """Get immediate prerequisites for a standard.
        
        Returns list of standard codes that are direct prerequisites.
        """
        ...

    def get_all_prerequisites(self, standard_code: str) -> list[str]:
        """Get ALL prerequisites (transitive closure) for a standard.
        
        Uses DFS traversal backwards through the graph.
        Returns topologically sorted list.
        """
        ...

    def topological_sort(self, target_standards: list[str]) -> list[str]:
        """Topological sort of a subgraph containing only target standards.
        
        Args:
            target_standards: Standard codes to include
        
        Returns:
            Ordered list where each standard appears after all its prerequisites
        
        Raises:
            CycleDetectedError: If the subgraph contains a cycle
        """
        ...

    def get_remediation_sequence(
        self,
        deficient_skills: list[str],
        skill_states: dict[str, float],
    ) -> list[str]:
        """Generate optimal learning sequence for deficient skills.
        
        Algorithm (see Algorithm 4):
        1. Build subgraph of deficient skills + their unmastered prerequisites
        2. Topological sort
        3. Apply priority scoring: weight = centrality * (1 - p_mastery)
        4. Return ordered sequence
        
        Args:
            deficient_skills: Standards where P(L) < mastery threshold
            skill_states: { standard_code: p_mastery } for all standards
        
        Returns:
            Ordered list of standard codes to learn
        """
        ...

    def detect_cycles(self) -> list[list[str]]:
        """Detect and return all cycles in the graph.
        
        Returns list of cycles, each as a list of standard codes.
        Used by admin graph editor to validate before saving.
        """
        ...

    def get_graph_stats(self) -> dict:
        """Return graph statistics for the admin dashboard.
        
        Returns: { total_nodes, total_edges, max_depth, domains, 
                    avg_in_degree, avg_out_degree, connected_components }
        """
        ...


# ─────────────────────────────────────────────────────────────────────
# services/learning_plan_service.py
# ─────────────────────────────────────────────────────────────────────
from uuid import UUID
from datetime import date, timedelta
from typing import Optional
import networkx as nx

from app.models.learning_plan import LearningPlan, PlanModule, PlanLesson
from app.schemas.assessment import AssessmentResults
from app.schemas.learning_plan import PlanTrack
from app.services.skill_graph_service import SkillGraphService
from app.services.bkt_service import BKTService
from app.repositories.learning_plan_repository import LearningPlanRepository
from app.repositories.student_repository import StudentRepository


class LearningPlanService:
    """Generates and manages personalized learning plans.
    
    The plan generation algorithm:
    1. Analyze diagnostic BKT states to determine overall track
    2. Identify deficient skills (below mastery threshold)
    3. Use skill graph to determine learning sequence
    4. Create modules for each skill with appropriate lesson count
    5. Estimate completion based on session frequency
    """

    MASTERY_THRESHOLD: float = 0.80
    BASE_LESSONS_PER_MODULE: int = 5
    
    # Track thresholds
    CATCH_UP_THRESHOLD: float = 0.40
    ON_TRACK_THRESHOLD: float = 0.70

    def __init__(
        self,
        plan_repo: LearningPlanRepository,
        student_repo: StudentRepository,
        skill_graph: SkillGraphService,
        bkt_service: BKTService,
    ):
        self._plan_repo = plan_repo
        self._student_repo = student_repo
        self._skill_graph = skill_graph
        self._bkt = bkt_service

    async def generate_plan(
        self,
        student_id: UUID,
        assessment_id: UUID | None = None,
        sessions_per_week: int = 3,
        minutes_per_session: int = 20,
    ) -> LearningPlan:
        """Generate a personalized learning plan.
        
        Args:
            student_id: Target student
            assessment_id: Source assessment (latest if None)
            sessions_per_week: Planned study frequency
            minutes_per_session: Planned session duration
        
        Returns:
            Complete LearningPlan with modules and lessons
        
        Raises:
            NoAssessmentError: No completed assessment found
            ActivePlanExistsError: Student already has active plan
        """
        ...

    def determine_track(self, skill_states: dict[str, float]) -> PlanTrack:
        """Classify student into learning track based on overall diagnostic score.
        
        Args:
            skill_states: { standard_code: p_mastery }
        
        Returns:
            PlanTrack enum: CATCH_UP, ON_TRACK, or ACCELERATE
        
        Algorithm:
            overall = weighted_mean(p_mastery values, weighted by standard centrality)
            if overall < 0.40: CATCH_UP
            elif overall < 0.70: ON_TRACK
            else: ACCELERATE
        """
        ...

    def sequence_modules(
        self,
        deficient_skills: list[str],
        skill_states: dict[str, float],
        graph: nx.DiGraph,
        track: PlanTrack,
    ) -> list[PlanModule]:
        """Create ordered list of modules with lesson counts.
        
        Args:
            deficient_skills: Standards below mastery
            skill_states: All BKT states
            graph: Skill dependency graph
            track: Student's learning track
        
        Returns:
            Ordered list of PlanModule objects
        
        Algorithm (see Algorithm 5):
            1. Get remediation sequence from skill graph
            2. For CATCH_UP: prepend prerequisite review modules
            3. Calculate lesson count per module based on gap size
            4. Set module prerequisites and initial statuses
        """
        ...

    def _calculate_lesson_count(
        self,
        p_mastery: float,
        track: PlanTrack,
    ) -> int:
        """Determine number of lessons for a module based on current mastery.
        
        Higher gap → more lessons. Track adjusts baseline:
        - CATCH_UP: base * 1.5 (more practice needed)
        - ON_TRACK: base * 1.0
        - ACCELERATE: base * 0.7 (less review needed)
        
        lesson_count = ceil(BASE_LESSONS * track_multiplier * (1 - p_mastery))
        Clamped to [2, 12]
        """
        ...

    def estimate_completion_date(
        self,
        modules: list[PlanModule],
        sessions_per_week: int,
        minutes_per_session: int,
    ) -> date:
        """Estimate plan completion date.
        
        total_minutes = sum(module.estimated_minutes)
        weekly_minutes = sessions_per_week * minutes_per_session
        weeks = ceil(total_minutes / weekly_minutes)
        return today + timedelta(weeks=weeks)
        """
        ...

    def _create_lessons_for_module(
        self,
        module: PlanModule,
        lesson_count: int,
    ) -> list[PlanLesson]:
        """Create lesson sequence within a module.
        
        Pattern:
        1. Instruction lesson (concept review)
        2-N-1. Practice lessons (graduated difficulty)
        N. Assessment lesson (module mastery check)
        """
        ...


# ─────────────────────────────────────────────────────────────────────
# services/question_generation_service.py
# ─────────────────────────────────────────────────────────────────────
from uuid import UUID
from typing import Optional
from dataclasses import dataclass

from app.models.generation import GenerationJob, GeneratedQuestion, ValidationResult
from app.repositories.generation_repository import GenerationRepository
from app.repositories.question_repository import QuestionRepository
from app.core.llm_client import LLMClient
from app.core.sandbox import PythonSandbox
from app.core.redis_client import RedisClient


@dataclass
class GenerationConfig:
    model: str = 'o3-mini'
    temperature: float = 0.7
    max_tokens: int = 2000
    sandbox_timeout_seconds: int = 5
    dedup_similarity_threshold: float = 0.90
    auto_approve_confidence: float = 0.85
    max_retries_per_question: int = 2


class QuestionGenerationService:
    """AI-powered math question generation with multi-stage validation.
    
    Pipeline (see Algorithm 6):
    1. Build prompt from standard + difficulty + context
    2. Call LLM with structured output
    3. Validate: solution execution, age-appropriateness, dedup, math correctness
    4. Route: auto-approve if confidence >= 0.85, else queue for review
    """

    def __init__(
        self,
        gen_repo: GenerationRepository,
        question_repo: QuestionRepository,
        llm_client: LLMClient,
        sandbox: PythonSandbox,
        redis: RedisClient,
        config: GenerationConfig = GenerationConfig(),
    ):
        self._gen_repo = gen_repo
        self._question_repo = question_repo
        self._llm = llm_client
        self._sandbox = sandbox
        self._redis = redis
        self._config = config

    async def generate_questions_for_standard(
        self,
        standard_code: str,
        count: int,
        difficulty_levels: list[int],
        context_themes: list[str] | None = None,
    ) -> list[GeneratedQuestion]:
        """Generate questions for a single standard.
        
        Distributes count across difficulty levels evenly.
        Each question goes through the full validation pipeline.
        
        Returns list of GeneratedQuestion with validation results attached.
        """
        ...

    async def validate_question(
        self,
        question: GeneratedQuestion,
    ) -> ValidationResult:
        """Run full validation pipeline on a single generated question.
        
        Steps:
        1. Execute embedded solution code in sandbox
        2. Run age-appropriateness classifier
        3. pgvector dedup check
        4. Mathematical correctness verification
        5. Compute aggregate confidence score
        
        Returns ValidationResult with per-check pass/fail and overall confidence.
        """
        ...

    async def batch_generate(
        self,
        job: GenerationJob,
    ) -> 'GenerationJobResult':
        """Process an entire generation job.
        
        Called by LangGraph worker. Updates job status in DB as it progresses.
        Handles retries for failed individual questions.
        Tracks token usage and cost.
        
        Returns aggregate results.
        """
        ...

    async def _build_prompt(
        self,
        standard_code: str,
        standard_description: str,
        difficulty: int,
        theme: str | None,
    ) -> str:
        """Build the LLM prompt for question generation.
        
        Prompt structure:
        - System: You are an expert math educator creating questions for Oregon 4th graders.
        - Standard details (code, description, examples)
        - Difficulty guidelines (word count, operation complexity, number ranges per level)
        - Context theme (if provided)
        - Oregon-specific context suggestions
        - Structured output schema (JSON)
        - Constraints (age-appropriate vocabulary, no bias, clear language)
        """
        ...

    async def _execute_solution_code(
        self,
        code: str,
        expected_answer: str,
    ) -> tuple[bool, str | None, str | None]:
        """Execute generated Python solution in sandboxed subprocess.
        
        Returns (passed, stdout, stderr).
        Timeout: 5 seconds.
        No network access, limited imports (math, fractions, decimal only).
        """
        ...

    async def _check_age_appropriateness(
        self,
        question: GeneratedQuestion,
    ) -> tuple[bool, float, str | None]:
        """Run content safety check via Claude Sonnet 4.6.
        
        Checks for:
        - Violence, death, or disturbing content
        - Inappropriate themes for children
        - Cultural insensitivity or bias
        - Gender/racial stereotypes
        - Overly complex vocabulary (> 5th grade reading level)
        
        Returns (passed, score 0-1, notes).
        """
        ...

    async def _check_duplicate(
        self,
        embedding: list[float],
        standard_code: str,
    ) -> tuple[bool, float, UUID | None]:
        """Check for duplicate/near-duplicate questions via pgvector.
        
        Query:
            SELECT id, 1 - (content_embedding <=> :embedding) AS similarity
            FROM questions
            WHERE standard_code = :standard_code AND content_embedding IS NOT NULL
            ORDER BY content_embedding <=> :embedding
            LIMIT 1
        
        Returns (is_unique, max_similarity, similar_question_id).
        is_unique = True if max_similarity < 0.90
        """
        ...
```

---

## 3. Key Algorithms (Stage 2)

### Algorithm 4: Skill Dependency Graph Traversal

```
FUNCTION get_remediation_sequence(deficient_skills, skill_states, graph):
    """Generate optimal learning sequence using topological sort with priority.
    
    Args:
        deficient_skills: list of standard codes where P(L) < MASTERY_THRESHOLD
        skill_states: dict { standard_code: p_mastery } for ALL standards
        graph: NetworkX DiGraph (edges: prerequisite → dependent)
    
    Returns:
        Ordered list of standard codes to study
    """
    
    # ─── Step 1: Expand to include unmastered prerequisites ──────
    all_needed = set(deficient_skills)
    
    FOR EACH skill IN deficient_skills:
        # Get all transitive prerequisites
        ancestors = nx.ancestors(graph, skill)
        FOR EACH ancestor IN ancestors:
            IF skill_states.get(ancestor, 0) < MASTERY_THRESHOLD:
                all_needed.add(ancestor)
    
    # ─── Step 2: Build subgraph ──────────────────────────────────
    subgraph = graph.subgraph(all_needed).copy()
    
    # ─── Step 3: Detect and handle cycles ────────────────────────
    cycles = list(nx.simple_cycles(subgraph))
    IF cycles:
        # Break cycles by removing the lowest-weight edge in each cycle
        FOR EACH cycle IN cycles:
            min_weight_edge = None
            min_weight = float('inf')
            FOR i IN range(len(cycle)):
                u = cycle[i]
                v = cycle[(i + 1) % len(cycle)]
                edge_weight = subgraph[u][v].get('weight', 1.0)
                IF edge_weight < min_weight:
                    min_weight = edge_weight
                    min_weight_edge = (u, v)
            subgraph.remove_edge(*min_weight_edge)
            LOG_WARNING(f"Cycle detected and broken: removed edge {min_weight_edge}")
    
    # ─── Step 4: Compute priority scores ─────────────────────────
    # Betweenness centrality: how many shortest paths pass through this node
    centrality = nx.betweenness_centrality(subgraph)
    
    priority_scores = {}
    FOR EACH node IN subgraph.nodes():
        p_mastery = skill_states.get(node, 0.0)
        c = centrality.get(node, 0.0)
        
        # Priority = centrality * gap_size
        # High centrality + low mastery = highest priority
        priority_scores[node] = (c + 0.1) * (1 - p_mastery)
        # +0.1 baseline so leaf nodes still have non-zero priority
    
    # ─── Step 5: Priority-weighted topological sort ───────────────
    # Modified Kahn's algorithm with priority queue
    in_degree = dict(subgraph.in_degree())
    ready_queue = []  # min-heap (negative priority for max-first)
    
    # Initialize: nodes with no prerequisites
    FOR EACH node IN subgraph.nodes():
        IF in_degree[node] == 0:
            heapq.heappush(ready_queue, (-priority_scores[node], node))
    
    sequence = []
    
    WHILE ready_queue is not empty:
        _, current = heapq.heappop(ready_queue)
        sequence.append(current)
        
        FOR EACH successor IN subgraph.successors(current):
            in_degree[successor] -= 1
            IF in_degree[successor] == 0:
                heapq.heappush(ready_queue, (-priority_scores[successor], successor))
    
    ASSERT len(sequence) == len(all_needed), "Topological sort incomplete — check for cycles"
    
    RETURN sequence

COMPLEXITY: O(V + E) for topological sort, O(V * E) for betweenness centrality
EXPECTED: O(28 + 45) ≈ O(73) — sub-millisecond for our graph size
```

### Algorithm 5: Learning Plan Track Assignment and Module Sequencing

```
FUNCTION generate_learning_plan(student_id, skill_states, graph, config):
    """Generate a complete learning plan.
    
    Args:
        student_id: UUID
        skill_states: { standard_code: BKTState }
        graph: NetworkX DiGraph
        config: { sessions_per_week, minutes_per_session }
    
    Returns:
        LearningPlan with ordered modules and lessons
    """
    
    # ─── Step 1: Determine track ─────────────────────────────────
    # Weighted average by centrality
    centrality = nx.betweenness_centrality(graph)
    
    total_weighted = 0.0
    total_weight = 0.0
    FOR EACH code, state IN skill_states:
        w = centrality.get(code, 0.1) + 0.1  # Ensure non-zero
        total_weighted += state.p_mastery * w
        total_weight += w
    
    overall_score = total_weighted / total_weight
    
    IF overall_score < 0.40:
        track = 'catch_up'
        track_multiplier = 1.5
    ELIF overall_score < 0.70:
        track = 'on_track'
        track_multiplier = 1.0
    ELSE:
        track = 'accelerate'
        track_multiplier = 0.7
    
    # ─── Step 2: Identify deficient skills ────────────────────────
    MASTERY_THRESHOLD = 0.80
    deficient = [code for code, state in skill_states.items()
                 if state.p_mastery < MASTERY_THRESHOLD]
    
    IF track == 'accelerate':
        # For advanced students, only focus on skills below 0.90
        MASTERY_THRESHOLD = 0.90
        deficient = [code for code, state in skill_states.items()
                     if state.p_mastery < MASTERY_THRESHOLD]
    
    IF not deficient:
        # Student has mastered everything — create enrichment plan
        RETURN create_enrichment_plan(student_id, skill_states)
    
    # ─── Step 3: Get learning sequence ────────────────────────────
    sequence = get_remediation_sequence(deficient, 
                                         {c: s.p_mastery for c, s in skill_states.items()},
                                         graph)
    
    # ─── Step 4: For CATCH_UP, prepend prerequisite review ────────
    modules = []
    IF track == 'catch_up':
        # Find 3rd grade prerequisite skills that are weak
        for code in sequence:
            prereqs_3rd = [p for p in graph.predecessors(code) 
                          if p.startswith('3.')]
            IF prereqs_3rd:
                # Add a lightweight review module (2 lessons)
                review_module = PlanModule(
                    standard_code=f"REVIEW_{code}",
                    lesson_count=2,
                    estimated_minutes=30,
                    module_type='prerequisite_review',
                )
                modules.append(review_module)
    
    # ─── Step 5: Create modules with calibrated lesson counts ─────
    BASE_LESSONS = 5
    MINUTES_PER_LESSON = 15
    
    FOR EACH i, standard_code IN enumerate(sequence):
        p_mastery = skill_states[standard_code].p_mastery
        
        # Gap-proportional lesson count
        gap = 1 - p_mastery
        lesson_count = ceil(BASE_LESSONS * track_multiplier * gap)
        lesson_count = CLAMP(lesson_count, 2, 12)
        
        # Estimate minutes
        estimated_minutes = lesson_count * MINUTES_PER_LESSON
        
        # Determine initial status
        prerequisites_in_plan = [m.standard_code for m in modules
                                 if m.standard_code in graph.predecessors(standard_code)]
        
        IF not prerequisites_in_plan:
            status = 'available'  # No unmet prereqs in this plan
        ELSE:
            status = 'locked'
        
        module = PlanModule(
            standard_code=standard_code,
            sequence_order=i + 1,
            status=status,
            lesson_count=lesson_count,
            estimated_minutes=estimated_minutes,
            entry_p_mastery=p_mastery,
            prerequisite_module_ids=[m.id for m in modules 
                                     if m.standard_code in graph.predecessors(standard_code)],
        )
        modules.append(module)
    
    # ─── Step 6: Create lessons within each module ────────────────
    FOR EACH module IN modules:
        lessons = []
        
        # Lesson 1: Instruction (concept review)
        lessons.append(PlanLesson(
            sequence_order=1,
            lesson_type='instruction',
            title=f"Review: {standard_title}",
            question_count=0,
            difficulty_range='[1,2]',
        ))
        
        # Lessons 2 to N-1: Practice (graduated difficulty)
        practice_count = module.lesson_count - 2  # subtract instruction + assessment
        FOR j IN range(practice_count):
            difficulty_floor = 1 + (j * 4) // practice_count
            difficulty_ceil = min(5, difficulty_floor + 2)
            lessons.append(PlanLesson(
                sequence_order=j + 2,
                lesson_type='practice',
                title=f"Practice {j+1}: {standard_title}",
                question_count=5,
                difficulty_range=f'[{difficulty_floor},{difficulty_ceil}]',
            ))
        
        # Final lesson: Module assessment
        lessons.append(PlanLesson(
            sequence_order=module.lesson_count,
            lesson_type='assessment',
            title=f"Check: {standard_title}",
            question_count=8,
            difficulty_range='[2,4]',
        ))
        
        module.lessons = lessons
    
    # ─── Step 7: Estimate completion ──────────────────────────────
    total_minutes = sum(m.estimated_minutes for m in modules)
    weekly_minutes = config.sessions_per_week * config.minutes_per_session
    weeks = ceil(total_minutes / max(1, weekly_minutes))
    estimated_completion = today() + timedelta(weeks=weeks)
    
    RETURN LearningPlan(
        student_id=student_id,
        track=track,
        status='active',
        total_modules=len(modules),
        total_lessons=sum(m.lesson_count for m in modules),
        estimated_total_minutes=total_minutes,
        sessions_per_week=config.sessions_per_week,
        minutes_per_session=config.minutes_per_session,
        estimated_completion_date=estimated_completion,
        modules=modules,
    )
```

### Algorithm 6: LLM Question Generation with Validation Pipeline

```
ASYNC FUNCTION generate_and_validate_question(standard, difficulty, theme, config):
    """Generate a single math question with full validation pipeline.
    
    Args:
        standard: { code, description, examples, domain }
        difficulty: int 1-5
        theme: str | None (e.g., 'animals', 'Oregon geography')
        config: GenerationConfig
    
    Returns:
        (GeneratedQuestion, ValidationResult)
    """
    
    # ─── Step 1: Build prompt ─────────────────────────────────────
    difficulty_guidelines = {
        1: "Single operation, numbers ≤ 20, simple vocabulary, no multi-step",
        2: "Single operation, numbers ≤ 100, basic word problems",
        3: "Two operations or multi-step, numbers ≤ 1000, grade-level vocabulary",
        4: "Multi-step with mixed operations, larger numbers, requires reasoning",
        5: "Complex multi-step, fraction/decimal operations, abstract reasoning",
    }
    
    system_prompt = """
    You are an expert 4th grade math teacher in Oregon creating assessment questions.
    
    RULES:
    - Question must assess the given standard precisely
    - Use age-appropriate vocabulary (4th grade reading level)
    - Include Oregon-specific context when possible (Portland, Crater Lake, Oregon Trail)
    - Multiple choice with exactly 4 options (A, B, C, D)
    - Distractors must be plausible (common mistakes, not random numbers)
    - Include a Python solution that outputs ONLY the answer
    - Explanation should be clear and instructive for a 9-10 year old
    """
    
    user_prompt = f"""
    Generate a math question for:
    
    Standard: {standard.code} — {standard.description}
    Difficulty: {difficulty}/5 — {difficulty_guidelines[difficulty]}
    {"Theme: " + theme if theme else ""}
    
    Respond with this exact JSON schema:
    {{
        "stem": "The question text",
        "options": [
            {{"key": "A", "text": "answer option"}},
            {{"key": "B", "text": "answer option"}},
            {{"key": "C", "text": "answer option"}},
            {{"key": "D", "text": "answer option"}}
        ],
        "correct_answer": "B",
        "explanation": "Step-by-step explanation for a 4th grader",
        "solution_code": "print(42)  # Python code that outputs the answer"
    }}
    """
    
    # ─── Step 2: Call LLM ─────────────────────────────────────────
    response = AWAIT llm_client.create(
        model=config.model,  # 'o3-mini'
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        response_format={"type": "json_schema", "schema": QUESTION_JSON_SCHEMA},
        temperature=config.temperature,
        max_tokens=config.max_tokens,
    )
    
    question = parse_question_from_response(response)
    
    # ─── Step 3: Validate — Solution Execution ────────────────────
    solution_passed = False
    solution_output = None
    solution_error = None
    
    TRY:
        result = AWAIT sandbox.execute(
            code=question.solution_code,
            timeout=config.sandbox_timeout_seconds,
            allowed_imports=['math', 'fractions', 'decimal'],
            no_network=True,
        )
        solution_output = result.stdout.strip()
        
        # Compare output with correct answer (normalize for numeric comparison)
        IF normalize_answer(solution_output) == normalize_answer(question.correct_answer):
            solution_passed = True
        ELSE:
            solution_error = f"Expected '{question.correct_answer}', got '{solution_output}'"
    EXCEPT TimeoutError:
        solution_error = "Solution execution timed out (5s)"
    EXCEPT SandboxError as e:
        solution_error = f"Execution error: {str(e)}"
    
    # ─── Step 4: Validate — Age Appropriateness ───────────────────
    age_passed = False
    age_score = 0.0
    age_notes = None
    
    classifier_response = AWAIT llm_client.create(
        model='claude-sonnet-4-6',
        messages=[{
            "role": "user",
            "content": f"""Rate this math question for a 9-10 year old student (4th grade):
            
            Question: {question.stem}
            Options: {question.options}
            
            Check for:
            1. Age-appropriate vocabulary (no words above 5th grade level)
            2. No violence, death, or disturbing content
            3. No cultural insensitivity or stereotypes
            4. No gender or racial bias
            5. No inappropriate themes
            
            Respond JSON: {{"score": 0.0-1.0, "passed": true/false, "notes": "any issues"}}"""
        }],
        response_format={"type": "json_object"},
        max_tokens=200,
    )
    
    age_result = parse_json(classifier_response)
    age_passed = age_result.passed
    age_score = age_result.score
    age_notes = age_result.notes
    
    # ─── Step 5: Validate — Dedup Check (pgvector) ────────────────
    dedup_passed = False
    max_similarity = 0.0
    similar_id = None
    
    # Generate embedding for the question stem
    embedding = AWAIT llm_client.create_embedding(
        model='text-embedding-3-small',
        input=question.stem,
    )
    
    # Query pgvector for similar questions
    similar = AWAIT db.execute("""
        SELECT id, 1 - (content_embedding <=> :embedding) AS similarity
        FROM questions
        WHERE standard_code = :standard_code
          AND content_embedding IS NOT NULL
        ORDER BY content_embedding <=> :embedding
        LIMIT 1
    """, {"embedding": embedding, "standard_code": standard.code})
    
    IF similar.row:
        max_similarity = similar.row.similarity
        similar_id = similar.row.id
        dedup_passed = max_similarity < config.dedup_similarity_threshold  # 0.90
    ELSE:
        dedup_passed = True  # No existing questions to compare
    
    # ─── Step 6: Validate — Mathematical Correctness ──────────────
    math_passed = True
    math_notes = None
    
    # Check: all distractor answers are different from correct answer
    option_values = {opt.text for opt in question.options}
    IF len(option_values) < 4:
        math_passed = False
        math_notes = "Duplicate answer options detected"
    
    # Check: correct answer appears in options
    correct_option = next((o for o in question.options if o.key == question.correct_answer), None)
    IF correct_option is None:
        math_passed = False
        math_notes = "Correct answer key does not match any option"
    
    # ─── Step 7: Compute Confidence Score ─────────────────────────
    confidence = (
        (1.0 if solution_passed else 0.0) * 0.40 +
        (age_score if age_passed else 0.0) * 0.20 +
        (1.0 if dedup_passed else 0.0) * 0.20 +
        (1.0 if math_passed else 0.0) * 0.20
    )
    
    validation = ValidationResult(
        solution_execution_passed=solution_passed,
        solution_output=solution_output,
        solution_error=solution_error,
        age_appropriateness_passed=age_passed,
        age_appropriateness_score=age_score,
        age_appropriateness_notes=age_notes,
        dedup_passed=dedup_passed,
        max_similarity_score=max_similarity,
        similar_question_id=similar_id,
        math_correctness_passed=math_passed,
        math_correctness_notes=math_notes,
        overall_passed=confidence >= config.auto_approve_confidence,
        confidence_score=confidence,
    )
    
    # ─── Step 8: Route ────────────────────────────────────────────
    question.content_embedding = embedding
    question.confidence_score = confidence
    question.validation_status = 'passed' if validation.overall_passed else 'failed'
    
    # Store in generated_questions table
    AWAIT gen_repo.save_generated_question(question)
    AWAIT gen_repo.save_validation_result(validation)
    
    IF confidence >= config.auto_approve_confidence:
        # Auto-approve: promote directly to questions table
        promoted_id = AWAIT question_repo.create_from_generated(question)
        question.promoted_to_question_id = promoted_id
        LOG_INFO(f"Auto-approved question {question.id} → {promoted_id}")
    ELSE:
        # Route to human review
        flags = []
        IF NOT solution_passed: flags.append('solution_failed')
        IF NOT age_passed: flags.append('age_inappropriate')
        IF NOT dedup_passed: flags.append('near_duplicate')
        IF NOT math_passed: flags.append('math_error')
        IF confidence < 0.50: flags.append('low_confidence')
        
        AWAIT review_repo.enqueue(question.id, flags, confidence)
        LOG_INFO(f"Queued for review: {question.id}, flags={flags}")
    
    RETURN (question, validation)
```


---

## 4. Infrastructure & Deployment (Stage 2 Additions)

### 4.1 Terraform Additions

**New ECS Task: LangGraph Worker**

```hcl
# modules/ecs/worker.tf

resource "aws_ecs_task_definition" "worker" {
  family                   = "padi-ai-worker-${var.environment}"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = 1024    # Higher CPU for sandbox execution
  memory                   = 2048
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.ecs_worker_task.arn
  
  container_definitions = jsonencode([{
    name  = "padi-ai-worker"
    image = "${var.ecr_repository_url}:${var.image_tag}-worker"
    environment = [
      { name = "WORKER_MODE", value = "true" },
      { name = "ENVIRONMENT", value = var.environment },
      { name = "REDIS_QUEUE", value = "padi:generation:queue" },
      { name = "SANDBOX_TIMEOUT", value = "5" },
    ]
    secrets = [
      { name = "DATABASE_URL",     valueFrom = "${var.secrets_arn}:DATABASE_URL::" },
      { name = "REDIS_URL",        valueFrom = "${var.secrets_arn}:REDIS_URL::" },
      { name = "OPENAI_API_KEY",   valueFrom = "${var.secrets_arn}:OPENAI_API_KEY::" },
      { name = "ANTHROPIC_API_KEY", valueFrom = "${var.secrets_arn}:ANTHROPIC_API_KEY::" },
    ]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = "/ecs/padi-ai-worker-${var.environment}"
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "worker"
      }
    }
  }])
}

resource "aws_ecs_service" "worker" {
  name            = "padi-ai-worker"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.worker.arn
  desired_count   = var.environment == "prod" ? 2 : 1
  launch_type     = "FARGATE"
  
  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [var.worker_security_group_id]
    assign_public_ip = false
  }
  
  # No load balancer — worker processes from Redis queue
}
```

### 4.2 Environment Variable Reference (Stage 2 Additions)

```bash
# ─── LLM Configuration (added to FastAPI .env) ────────────────────
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
QUESTION_GENERATION_MODEL=o3-mini
QUESTION_GENERATION_TEMPERATURE=0.7
CONTENT_SAFETY_MODEL=claude-sonnet-4-6
EMBEDDING_MODEL=text-embedding-3-small

# ─── Worker Configuration ─────────────────────────────────────────
WORKER_MODE=false
REDIS_QUEUE=padi:generation:queue
WORKER_POLL_INTERVAL_SECONDS=5
SANDBOX_TIMEOUT_SECONDS=5
SANDBOX_MAX_MEMORY_MB=128
AUTO_APPROVE_CONFIDENCE=0.85
DEDUP_SIMILARITY_THRESHOLD=0.90
MAX_RETRIES_PER_QUESTION=2
MAX_CONCURRENT_GENERATIONS=5

# ─── Learning Plan Configuration ──────────────────────────────────
DEFAULT_SESSIONS_PER_WEEK=3
DEFAULT_MINUTES_PER_SESSION=20
MASTERY_THRESHOLD=0.80
CATCH_UP_THRESHOLD=0.40
ON_TRACK_THRESHOLD=0.70
BASE_LESSONS_PER_MODULE=5
```

### 4.3 GitHub Actions Additions (Stage 2)

Add to CI/CD pipeline:

```yaml
  # ─────────────────────────────────────────────────────────────
  test-worker:
    name: Test Worker (LangGraph Pipeline)
    runs-on: ubuntu-latest
    needs: [lint-backend]
    services:
      postgres:
        image: pgvector/pgvector:pg17
        env:
          POSTGRES_DB: padi_ai_test
          POSTGRES_USER: padi-ai
          POSTGRES_PASSWORD: testpassword
        ports: ["5432:5432"]
        options: >-
          --health-cmd pg_isready --health-interval 10s --health-timeout 5s --health-retries 5
      redis:
        image: redis:7-alpine
        ports: ["6379:6379"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt -r requirements-dev.txt
      - name: Run worker tests
        run: |
          cd backend
          pytest tests/worker/ \
            --cov=app/services/question_generation_service \
            --cov=app/worker \
            -v --timeout=120
        env:
          DATABASE_URL: postgresql+asyncpg://padi:testpassword@localhost:5432/padi_ai_test
          REDIS_URL: redis://localhost:6379/0
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY_TEST }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY_TEST }}
          ENVIRONMENT: test

  build-and-push-worker:
    name: Build & Push Worker Image
    runs-on: ubuntu-latest
    needs: [test-worker, test-backend, security-scan]
    if: github.event_name == 'push'
    steps:
      - uses: actions/checkout@v4
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_DEPLOY_ROLE_ARN }}
          aws-region: us-west-2
      - name: Login to ECR
        uses: aws-actions/amazon-ecr-login@v2
      - name: Build and push Worker image
        run: |
          IMAGE_TAG="${{ github.sha }}-worker"
          FULL_TAG="${{ steps.ecr-login.outputs.registry }}/padi-ai-worker:${IMAGE_TAG}"
          docker build -t ${FULL_TAG} -f backend/Dockerfile.worker backend/
          docker push ${FULL_TAG}
```

---

## 5. Testing Plan (Stage 2)

### 5.1 Unit Test Coverage Requirements

| Module | Coverage Target | Key Test Cases |
|--------|----------------|----------------|
| `SkillGraphService` | 90% | Graph loads from DB correctly; get_prerequisites returns correct list; topological sort produces valid order; cycle detection identifies known cycles; cycle breaking removes lowest-weight edge; get_remediation_sequence includes unmastered prerequisites; empty graph handled; single-node graph handled; disconnected components handled |
| `LearningPlanService` | 90% | Track determination: score <0.40 → catch_up, <0.70 → on_track, else accelerate; module sequencing follows topological order; lesson count proportional to gap size; CATCH_UP prepends prereq review; completion estimate matches manual calculation; all modules have at least 2 lessons; prerequisite locking correct; enrichment plan for mastered students |
| `QuestionGenerationService` | 85% | Prompt builds correctly for each difficulty level; structured output parses correctly; solution execution sandbox works with timeout; age classifier processes response; pgvector dedup query returns correct similarity; confidence score calculation correct; auto-approve at ≥0.85; review queue routing with correct flags; token tracking accurate; retry logic works for transient failures |
| `PythonSandbox` | 95% | Successful code execution returns output; timeout enforced at 5s; memory limit enforced; network access blocked; only allowed imports (math, fractions, decimal); malicious code caught (os.system, subprocess); Unicode handling; empty output handled |
| `ReviewService` | 85% | Pending queue sorts by priority+time; approve promotes to questions table; reject does not promote; needs_edit preserves edits; assignment tracking works; bulk approve works |
| `BadgeService` | 90% | First assessment badge awarded; domain mastery badge triggers correctly; streak badges at 3/7/14/30 days; plan progress badges at 25/50/75/100%; duplicate badge prevented; badge context stored |
| `StreakService` | 90% | Daily activity records correctly; consecutive days increment streak; gap resets streak; longest streak preserved; activity_dates array maintained for 90 days; weekly/monthly aggregates correct; timezone handling (PST/PDT) |

### 5.2 Integration Test Scenarios

**IT-S2-01: Learning Plan Generation from Diagnostic**
- **Setup:** Completed diagnostic with mixed results (some below_par, some above_par), full skill graph seeded
- **Action:** `POST /learning-plans` with student_id
- **Expected:** Plan created with correct track. Modules ordered by topological sort. Module count matches deficient skills + prerequisites. Lessons created per module. Completion estimate reasonable (4-12 weeks).
- **Teardown:** Delete plan records

**IT-S2-02: Skill Graph API Returns Valid Graph**
- **Setup:** Full skill graph edges seeded (28 standards, ~45 edges)
- **Action:** `GET /skill-graph`
- **Expected:** Response contains all nodes and edges. Every edge references valid node. Graph has no self-loops. Metadata counts match.
- **Teardown:** None (read-only)

**IT-S2-03: Question Generation Job Lifecycle**
- **Setup:** Admin user, standard '4.OA.A.1' exists
- **Action:** `POST /admin/generation-jobs` → poll `GET /admin/generation-jobs/{id}` until completed
- **Expected:** Job transitions: queued → running → completed. Generated questions stored. Validation results stored. Some auto-approved, some in review queue. Token count > 0.
- **Teardown:** Delete job + generated questions

**IT-S2-04: Review Queue Approve Flow**
- **Setup:** Generated question in review queue (status='pending')
- **Action:** `PUT /admin/review-queue/{id}` with decision='approved'
- **Expected:** Review item status → 'approved'. New question created in `questions` table with source='ai_generated'. Generated question marked as promoted.
- **Teardown:** Delete promoted question

**IT-S2-05: Review Queue Reject Flow**
- **Setup:** Generated question in review queue
- **Action:** `PUT /admin/review-queue/{id}` with decision='rejected', notes='Incorrect distractor'
- **Expected:** Review item status → 'rejected'. No new question in `questions` table. Decision notes stored.
- **Teardown:** None

**IT-S2-06: Badge Award on Domain Mastery**
- **Setup:** Student with all 4.OA standards at P(L) ≥ 0.90 (no badge yet)
- **Action:** Complete a practice session that updates BKT → triggers badge check
- **Expected:** Badge 'domain_mastered_OA' awarded. Badge details include domain and timestamp. Duplicate award prevented on subsequent triggers.
- **Teardown:** Delete badge

**IT-S2-07: Streak Tracking Across Days**
- **Setup:** Student with 3-day streak
- **Action:** Record activity today → `GET /students/{id}/streak`
- **Expected:** current_streak_days = 4. activity_dates includes today. activities_this_week incremented.
- **Teardown:** Reset streak

**IT-S2-08: Learning Plan Module Unlock Flow**
- **Setup:** Active plan with Module A (available) → Module B (locked, prereq: A) → Module C (locked, prereq: B)
- **Action:** Complete Module A via practice sessions → check Module B status
- **Expected:** Module B transitions from 'locked' to 'available'. Module C remains 'locked'. Plan progress updates correctly.
- **Teardown:** Reset plan

### 5.3 E2E Test Scenarios (Playwright)

**E2E-S2-01: Student Dashboard Displays Learning Plan**
```typescript
test('student dashboard shows learning plan with progress', async ({ page }) => {
  await loginAsParentWithPlan(page);
  
  // Navigate to student dashboard
  await page.click('[data-testid="student-card-timmy"]');
  await page.waitForURL(/\/students\/[a-f0-9-]+$/);
  
  // Verify dashboard components
  await expect(page.locator('[data-testid="progress-ring"]')).toBeVisible();
  await expect(page.locator('[data-testid="current-streak"]')).toBeVisible();
  await expect(page.locator('[data-testid="badges-preview"]')).toBeVisible();
  
  // Verify learning plan section
  await page.click('a:has-text("Learning Plan")');
  await page.waitForURL(/\/learning-plan$/);
  
  await expect(page.locator('[data-testid="plan-track"]')).toContainText(/catch up|on track|accelerate/i);
  await expect(page.locator('[data-testid="module-list"]')).toBeVisible();
  
  // Verify first module is available
  const firstModule = page.locator('[data-testid="plan-module"]').first();
  await expect(firstModule).toHaveAttribute('data-status', 'available');
  
  // Verify locked modules show lock icon
  const lockedModule = page.locator('[data-status="locked"]').first();
  await expect(lockedModule.locator('[data-testid="lock-icon"]')).toBeVisible();
});
```

**E2E-S2-02: Admin Creates and Monitors Generation Job**
```typescript
test('admin can create generation job and see results', async ({ page }) => {
  await loginAsAdmin(page);
  
  await page.goto('/admin/generation-jobs');
  await page.click('button:has-text("New Job")');
  
  // Fill job form
  await page.selectOption('[name="standardCode"]', '4.NF.B.3');
  await page.fill('[name="count"]', '5');
  await page.click('[data-difficulty="1"]');
  await page.click('[data-difficulty="2"]');
  await page.click('[data-difficulty="3"]');
  await page.click('button:has-text("Start Generation")');
  
  // Should show job created
  await expect(page.getByText(/job created/i)).toBeVisible();
  
  // Poll until completed (with timeout)
  await page.waitForSelector('[data-status="completed"]', { timeout: 120000 });
  
  // Verify results
  await expect(page.locator('[data-testid="total-generated"]')).not.toHaveText('0');
  await expect(page.locator('[data-testid="auto-approved"]')).toBeVisible();
  await expect(page.locator('[data-testid="needs-review"]')).toBeVisible();
});
```

**E2E-S2-03: Admin Reviews and Approves Question**
```typescript
test('admin can review and approve AI-generated question', async ({ page }) => {
  await loginAsAdmin(page);
  
  await page.goto('/admin/review-queue');
  await expect(page.locator('[data-testid="review-item"]').first()).toBeVisible();
  
  // Click first review item
  await page.click('[data-testid="review-item"]:first-child');
  
  // Verify question details displayed
  await expect(page.locator('[data-testid="question-stem"]')).toBeVisible();
  await expect(page.locator('[data-testid="options"]')).toBeVisible();
  await expect(page.locator('[data-testid="validation-details"]')).toBeVisible();
  
  // Approve the question
  await page.click('button:has-text("Approve")');
  await expect(page.getByText(/approved/i)).toBeVisible();
  
  // Verify it's removed from queue
  await expect(page.locator('[data-testid="review-item"]:first-child')).not.toHaveAttribute(
    'data-question-id', 
    await page.locator('[data-testid="review-item"]:first-child').getAttribute('data-question-id') ?? ''
  );
});
```

**E2E-S2-04: Badge Earned During Practice**
```typescript
test('student earns badge after completing first practice session', async ({ page }) => {
  await loginAsParentWithActivePlan(page);
  
  // Navigate to student's first available module
  await page.click('[data-testid="student-card-timmy"]');
  await page.click('a:has-text("Learning Plan")');
  await page.click('[data-status="available"]:first-child');
  await page.click('button:has-text("Start Practice")');
  
  // Answer 5 practice questions
  for (let i = 0; i < 5; i++) {
    await page.click('[data-testid="option-A"]'); // Correct for seeded data
    await page.click('button:has-text("Submit")');
    await page.waitForSelector('[data-testid="feedback"]');
    if (i < 4) await page.click('button:has-text("Next")');
  }
  
  // Complete session
  await page.click('button:has-text("Complete Session")');
  
  // Check for badge notification
  await expect(page.locator('[data-testid="badge-earned-toast"]')).toBeVisible({ timeout: 5000 });
  
  // Navigate to badges page
  await page.click('a:has-text("Badges")');
  await expect(page.locator('[data-testid="badge-item"]')).toHaveCount(1);
});
```

### 5.4 Performance Tests (Stage 2)

**Learning Plan Generation Benchmark:**
```python
# tests/performance/test_plan_generation_benchmark.py

def test_plan_generation_under_2_seconds(benchmark, seeded_graph, seeded_skill_states):
    """Learning plan generation for a student with 15 deficient skills must complete in < 2s."""
    
    plan_service = LearningPlanService(...)
    
    def generate():
        return asyncio.run(plan_service.generate_plan(
            student_id=test_student_id,
            sessions_per_week=3,
            minutes_per_session=20,
        ))
    
    result = benchmark.pedantic(generate, iterations=5, rounds=3)
    
    assert result.total_modules >= 15
    assert result.track in ('catch_up', 'on_track', 'accelerate')
    assert benchmark.stats['mean'] < 2.0
```

**pgvector Dedup Search Performance:**
```python
def test_pgvector_dedup_under_50ms(benchmark, seeded_questions_with_embeddings):
    """pgvector cosine similarity search across 10K questions must complete in < 50ms."""
    
    embedding = generate_random_embedding(1536)
    
    async def search():
        return await db.execute("""
            SELECT id, 1 - (content_embedding <=> :embedding) AS similarity
            FROM questions
            WHERE standard_code = '4.OA.A.1' AND content_embedding IS NOT NULL
            ORDER BY content_embedding <=> :embedding
            LIMIT 5
        """, {"embedding": embedding})
    
    result = benchmark.pedantic(lambda: asyncio.run(search()), iterations=50, rounds=5)
    assert benchmark.stats['mean'] < 0.05
```

---

## 6. QA Plan

### 6.2 QA Checklist (Stage 2 Exit Criteria)

#### Functional QA

- [ ] Learning plan generates correctly from diagnostic results
- [ ] Track assignment matches thresholds (catch_up <0.40, on_track <0.70, accelerate ≥0.70)
- [ ] Plan modules are in valid topological order (no module before its prerequisites)
- [ ] Locked modules cannot be started
- [ ] Completing a module unlocks dependent modules
- [ ] Plan progress percentage updates accurately
- [ ] Estimated completion date is reasonable (4-16 weeks)
- [ ] Student dashboard shows progress ring, streak, and badge preview
- [ ] Streak increments correctly for daily activity
- [ ] Streak resets after missed day
- [ ] Badges award at correct milestones (first assessment, domain mastery, streaks)
- [ ] Duplicate badges are prevented
- [ ] Activity heatmap displays last 90 days correctly
- [ ] Admin can create question generation job
- [ ] Generation job runs and produces questions
- [ ] Auto-approved questions appear in question bank with source='ai_generated'
- [ ] Questions needing review appear in review queue
- [ ] Admin can approve, reject, or request edits on review items
- [ ] Approved review items are promoted to question bank
- [ ] Rejected items are not added to question bank
- [ ] Skill graph visualization renders all nodes and edges
- [ ] Skill graph can be queried via API with optional student mastery overlay
- [ ] Practice sessions draw questions from AI-generated pool when available
- [ ] Parent overview page shows all children's progress
- [ ] BKT updates during practice sessions reflect in skill states
- [ ] Multiple children per parent each have independent plans

#### Performance QA

- [ ] Learning plan generation completes in < 2s
- [ ] pgvector dedup search completes in < 50ms for 10K questions
- [ ] Skill graph API responds in < 200ms
- [ ] Student dashboard loads in < 3s (including chart data)
- [ ] Review queue page loads in < 2s with 100+ pending items
- [ ] Generation job for 20 questions completes in < 5 minutes
- [ ] Badge check computation completes in < 100ms

#### Security QA

- [ ] LLM API keys stored in AWS Secrets Manager (not in env vars or code)
- [ ] Sandbox execution cannot access network
- [ ] Sandbox execution cannot access filesystem outside temp directory
- [ ] Sandbox process runs with minimal privileges
- [ ] Generated question content is sanitized before display
- [ ] Admin-only endpoints reject non-admin JWT with 403
- [ ] Review queue does not expose validation internals to non-admin users
- [ ] Token/cost tracking data accessible only to admin
- [ ] Student data isolation maintained across all new endpoints

#### Accessibility QA

- [ ] Learning plan timeline is navigable by screen reader
- [ ] Badge images have descriptive alt text
- [ ] Skill graph visualization has text alternative (table view)
- [ ] Practice session keyboard navigation works
- [ ] Streak calendar has aria-label for each day cell
- [ ] Progress indicators use aria-valuenow/aria-valuemax

### 6.3 Bug Triage Severity Levels

(Same as Stage 1 — see ENG-001 Section 6.3)

**Additional Stage 2 P0 examples:**
- AI-generated question contains inappropriate content that passed validation
- Sandbox escape: generated code executes outside sandbox
- LLM API key exposed in logs or error responses

**Additional Stage 2 P1 examples:**
- Learning plan generates with circular module dependencies
- Badge awarded incorrectly (false positive)
- Question generation job stuck in 'running' for > 30 minutes

---

## 7. Operational Runbooks (Stage 2 Additions)

### Runbook 6: LangGraph Worker Stuck or Unresponsive

**Trigger:** Generation jobs remain in 'running' status for > 30 minutes. Worker ECS task health check failing.

| Step | Action | Command / Detail |
|------|--------|-----------------|
| 1 | **Check worker logs** | `aws logs get-log-events --log-group /ecs/padi-ai-worker-prod --log-stream-prefix worker` |
| 2 | **Check Redis queue** | `redis-cli LLEN padi:generation:queue` — check backlog size |
| 3 | **Check LLM API status** | Verify OpenAI/Anthropic status pages. Test API call manually. |
| 4 | **Force restart worker** | `aws ecs update-service --cluster padi-ai-prod --service padi-ai-worker --force-new-deployment` |
| 5 | **Reset stuck jobs** | `UPDATE generation_jobs SET status='queued', retry_count=retry_count+1 WHERE status='running' AND started_at < now() - interval '30 minutes'` |
| 6 | **Verify recovery** | Poll job status. Check worker logs for resumed processing. |
| 7 | **Scale if needed** | `aws ecs update-service --cluster padi-ai-prod --service padi-ai-worker --desired-count 4` |

### Runbook 7: AI-Generated Content Safety Incident

**Trigger:** Report of inappropriate content in an AI-generated question visible to students.

| Step | Action | Detail |
|------|--------|--------|
| 1 | **Immediately retire question** | `UPDATE questions SET status='retired' WHERE id = :question_id` |
| 2 | **Remove from active sessions** | Flush Redis caches containing the question ID |
| 3 | **Audit trail** | `SELECT * FROM generated_questions WHERE promoted_to_question_id = :question_id` — identify generation job and validation results |
| 4 | **Review validation failure** | Check: did age_appropriateness_passed = true? Was confidence score > 0.85? Identify why validation missed this. |
| 5 | **Bulk audit** | Query all questions from the same generation job. Retire any with similar issues. |
| 6 | **Pause auto-approval** | Set `AUTO_APPROVE_CONFIDENCE=1.0` temporarily (forces all to review queue) |
| 7 | **Update validation prompt** | Improve age-appropriateness classifier prompt to catch the missed pattern |
| 8 | **Re-validate existing pool** | Run batch re-validation on all ai_generated questions with updated classifier |
| 9 | **Communicate** | If student was exposed: notify parent. Log incident for COPPA compliance. |
| 10 | **Restore auto-approval** | After validation prompt fix is verified on staging, restore normal threshold |

### Runbook 8: Skill Graph Corruption

**Trigger:** Cycle detected in skill graph, or learning plans generating with impossible module ordering.

| Step | Action | Detail |
|------|--------|--------|
| 1 | **Detect cycles** | `SELECT * FROM skill_dependency_graph_edges` → load into NetworkX → `nx.find_cycle(G)` |
| 2 | **Identify bad edge** | Determine which edge was most recently added/modified |
| 3 | **Remove bad edge** | `DELETE FROM skill_dependency_graph_edges WHERE id = :edge_id` |
| 4 | **Invalidate cache** | `redis-cli DEL skill_graph:v1` |
| 5 | **Re-generate affected plans** | Find plans with modules referencing the affected standards. Flag for regeneration. |
| 6 | **Notify admin** | Alert graph editor of the corrected cycle |
| 7 | **Add validation** | Implement pre-save cycle check in graph editor API |

