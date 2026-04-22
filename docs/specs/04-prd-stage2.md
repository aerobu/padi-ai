# PRD Stage 2: Personalized Learning Plan Generator
## PADI.AI | Version 1.0 | Target Completion: Month 6

---

## Table of Contents

1. [Overview & Objectives](#21-overview--objectives)
2. [Functional Requirements](#22-functional-requirements)
   - FR-6: Skill Dependency Graph Engine
   - FR-7: Learning Plan Generation
   - FR-8: AI-Powered Learning Content Generation
   - FR-9: Learning Plan Dashboard (Student View)
   - FR-10: Learning Plan Dashboard (Parent View)
3. [Non-Functional Requirements](#23-non-functional-requirements)
4. [Data Models](#24-data-models)
5. [API Endpoints](#25-api-endpoints)
6. [AI Prompt Templates](#26-ai-prompt-templates)
7. [Acceptance Criteria](#27-acceptance-criteria)

---

## 2.1 Overview & Objectives

### Stage Summary

Stage 2 transforms the raw diagnostic data produced in Stage 1 — a student's BKT-initialized skill state vector and per-skill proficiency classifications — into a structured, personalized learning plan that sequences content optimally for each student. This stage also establishes the AI-powered question generation pipeline that will supply the adaptive practice engine in Stage 3 with a deep, high-quality question pool targeting 5,000+ items.

The learning plan is the product's core value proposition to parents: a clear, actionable, individualized roadmap that tells a family not just "here's what your child doesn't know" (the diagnostic's job), but "here's exactly how we'll fix it, in what order, and in approximately how long." The plan is generated automatically within 5 seconds of diagnostic completion, requiring no teacher intervention and no parent configuration. It is both machine-readable (consumed by the adaptive practice engine) and human-readable (displayed as a visual learning roadmap on the student and parent dashboards).

### What "Personalized Learning Plan" Means in This System

A learning plan in PADI.AI is a **hierarchically structured, dependency-sorted sequence of learning modules**, where:

- **The sequence** is determined by the skill dependency graph (FR-6): foundational skills first, derived skills after. A student who needs both 3.OA.C.7 and 4.NBT.B.5 sees multiplication facts before multi-digit multiplication.
- **The content** of each module is calibrated to the student's BKT P(mastered) state: a student at P(mastered) = 0.10 starts with foundational concept-building questions; a student at P(mastered) = 0.50 starts with application-level practice.
- **The track** (Catch Up / On Track / Accelerate) determines whether the plan begins with prerequisite remediation, proceeds directly to Grade 4 content, or extends into enrichment/deeper problems.
- **The milestones** (module mastery thresholds) adapt dynamically: as a student practices, BKT P(mastered) updates, and when it crosses 0.85, the module is marked mastered and the next module unlocks. The plan is not static after generation — it recalculates sequence dynamically as progress changes.

### Business Objectives

- **Core product delivery**: Deliver a working personalized learning plan generator and student/parent dashboards by Month 6, enabling the product's core adaptive loop (Diagnostic → Plan → Practice → Mastery) to operate end-to-end for the pilot cohort.
- **Question supply chain**: Establish the AI question generation pipeline with automated validation, targeting 5,000+ high-quality questions by end of Stage 2 (vs. 142 seed questions at end of Stage 1), enabling Stage 3's adaptive practice engine to have sufficient question variety.
- **Engagement foundation**: Deliver gamification elements (streak tracking, achievement badges, visual roadmap) that establish daily practice habits. Target: 40% of students who generate a learning plan complete at least 3 practice sessions within the first week.
- **Parent transparency**: Ensure parents can, within 2 minutes of opening the parent dashboard, understand their child's full plan, current progress, and estimated completion timeline — reducing parent anxiety and building retention.
- **Cost discipline**: Keep LLM question generation costs under $0.05/question. At 5,000 questions, total LLM cost must not exceed $250.

### Success Criteria (Measurable)

| Metric | Target | Measurement |
|--------|--------|-------------|
| Learning plan generation time (P95) | < 5 seconds post-diagnostic | Server-side timing |
| Plan sequence accuracy | 100% of prerequisite relationships respected | Automated graph validation test |
| AI question generation throughput | ≥ 100 questions/hour validated | Pipeline monitoring |
| Total generated question pool by Month 6 | ≥ 5,000 questions | DB count |
| LLM cost per question | ≤ $0.05 | LLM API cost tracking |
| Question validation pass rate (auto) | ≥ 85% pass without human review | Pipeline metrics |
| Student dashboard load time (P95) | < 2 seconds | Synthetic monitoring |
| Parent dashboard load time (P95) | < 2 seconds | Synthetic monitoring |
| Streak tracking accuracy | 100% (no missed streaks) | Unit tests + integration tests |
| Badge award latency | < 2 seconds after qualifying event | Event processing timing |

### Dependencies on Stage 1

Stage 2 has hard dependencies on the following Stage 1 deliverables:

| Stage 1 Artifact | How Stage 2 Uses It |
|-----------------|---------------------|
| `standards` table (all 38 standards seeded) | Nodes in the skill dependency graph (FR-6) |
| `prerequisite_relationships` table (30 edges) | Edges in the dependency graph; topological sort for plan sequencing (FR-6) |
| `student_skill_states` table with BKT state | Initial P(mastered) for each student that seeds plan generation (FR-7) |
| `assessments` table with `diagnostic_completed` event | Trigger for plan generation (FR-7) |
| `questions` table with seed bank | Baseline question pool; generated questions use same schema (FR-8) |
| Question validation workflow | Template for AI-generated question validation pipeline (FR-8) |
| Parent/student authentication and sessions | Dashboard authentication (FR-9, FR-10) |

Stage 2 development can begin in parallel with Stage 1 for the dependency graph modeling (FR-6) and LLM prompt engineering (FR-8) workstreams, but plan generation (FR-7) and dashboards (FR-9, FR-10) are blocked on Stage 1 completion.

---

## 2.2 Functional Requirements

---

### FR-6: Skill Dependency Graph Engine

**FR-6.1 — Graph Data Model**

The skill dependency graph is a Directed Acyclic Graph (DAG) where:
- **Nodes** = standards (one per row in the `standards` table, both Grade 3 prerequisites and Grade 4 standards)
- **Edges** = prerequisite relationships (one per row in `prerequisite_relationships`)
- **Edge direction**: `prerequisite_code → dependent_code` (reads: "must master X before working on Y")
- **Edge weight (strength)**: `required` (must be addressed first) or `recommended` (beneficial but not blocking)

The graph is stored relationally in PostgreSQL but loaded into memory as a Python NetworkX `DiGraph` object for traversal operations.

```python
import networkx as nx
from typing import Generator

def build_skill_graph(db) -> nx.DiGraph:
    """
    Load the skill dependency graph from the database into a NetworkX DiGraph.
    Nodes have attributes: grade, domain, dok_level, is_prerequisite, description.
    Edges have attributes: strength.
    """
    G = nx.DiGraph()
    
    # Add all active standard nodes
    standards = db.query("SELECT * FROM standards WHERE is_active = TRUE")
    for std in standards:
        G.add_node(std['code'], **{
            'grade': std['grade'],
            'domain': std['domain'],
            'dok_level': std['dok_level'],
            'is_prerequisite': std['is_prerequisite'],
            'description': std['description'],
            'strand': std['strand']
        })
    
    # Add all prerequisite relationship edges
    edges = db.query("SELECT * FROM prerequisite_relationships")
    for edge in edges:
        G.add_edge(
            edge['prerequisite_code'],
            edge['dependent_code'],
            strength=edge['strength']
        )
    
    # Validate: graph must be a DAG (no cycles)
    if not nx.is_directed_acyclic_graph(G):
        raise ValueError("Skill dependency graph contains a cycle — check prerequisite_relationships data")
    
    return G
```

The graph SHALL be cached in memory (module-level singleton, rebuilt on application restart or when standards/prerequisites are updated via admin). A cache invalidation signal is published to Redis when admin changes prerequisite relationships.

**FR-6.2 — Topological Sort for Remediation Sequence**

The topological sort determines the optimal learning sequence: all prerequisites before dependents, respecting the partial order defined by the graph.

```python
def get_topological_sequence(G: nx.DiGraph, relevant_codes: list[str]) -> list[str]:
    """
    Given a set of standard codes the student needs to work on, return them in
    topologically sorted order (prerequisites first). Only returns codes in
    relevant_codes (not the full graph).
    
    Uses Kahn's algorithm (BFS-based topological sort) for stable ordering.
    """
    # Build subgraph containing only relevant nodes + their ancestors
    subgraph_nodes = set(relevant_codes)
    for code in relevant_codes:
        ancestors = nx.ancestors(G, code)
        subgraph_nodes.update(ancestors)
    
    subgraph = G.subgraph(subgraph_nodes)
    
    # Kahn's algorithm
    in_degree = {node: subgraph.in_degree(node) for node in subgraph.nodes()}
    queue = [node for node, deg in in_degree.items() if deg == 0]
    queue.sort()  # stable ordering for identical in-degrees
    result = []
    
    while queue:
        node = queue.pop(0)
        if node in relevant_codes:
            result.append(node)
        for successor in subgraph.successors(node):
            in_degree[successor] -= 1
            if in_degree[successor] == 0:
                queue.append(successor)
                queue.sort()
    
    return result
```

**FR-6.3 — Priority Scoring**

Not all skills are equally urgent. Priority is scored as a composite of:

1. **Foundational centrality** (in-degree in the subgraph × 10): Skills that many other skills depend on get higher priority. Multiplication facts (3.OA.C.7) has the highest centrality in the Grade 4 graph.
2. **Deficiency severity** (1 − P(mastered) × 20): Skills further from mastery are more urgent.
3. **Grade level** (Grade 3 prerequisites get +5 bonus): Prerequisite remediation is always done before Grade 4 content.

```python
def compute_priority_score(
    standard_code: str,
    p_mastered: float,
    G: nx.DiGraph
) -> float:
    """
    Compute a priority score for a skill (higher = more urgent to address).
    """
    # In-degree centrality (number of direct descendants in Grade 4 subgraph)
    out_degree = G.out_degree(standard_code)
    centrality_score = out_degree * 10
    
    # Deficiency severity
    deficiency_score = (1.0 - p_mastered) * 20
    
    # Grade-level bonus
    grade = G.nodes[standard_code].get('grade', 4)
    grade_bonus = 5 if grade == 3 else 0
    
    return centrality_score + deficiency_score + grade_bonus


def rank_skills_by_priority(
    skill_states: dict[str, float],  # standard_code → p_mastered
    G: nx.DiGraph
) -> list[tuple[str, float]]:
    """
    Returns skills sorted by priority (highest first), excluding already-mastered skills.
    """
    non_mastered = {code: p for code, p in skill_states.items() if p < 0.85}
    scored = [(code, compute_priority_score(code, p, G)) for code, p in non_mastered.items()]
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored
```

**FR-6.4 — Prerequisite Chain Detection**

When a student fails a Grade 4 standard, the system traces back through the prerequisite chain to find the root cause:

```python
def get_remediation_chain(
    failed_code: str,
    skill_states: dict[str, float],
    G: nx.DiGraph,
    mastery_threshold: float = 0.85
) -> list[str]:
    """
    Given a failed Grade 4 standard, traverse the prerequisite graph backwards
    to identify all prerequisite skills that are also below mastery threshold.
    Returns an ordered list (deepest prerequisite first) of skills to remediate.
    
    Example: failed_code = '4.NBT.B.5' (multi-digit multiplication)
    → may identify 3.OA.C.7 (multiplication facts) as root cause
    → returns ['3.OA.C.7', '3.NBT.A.3', '4.NBT.B.5']
    """
    chain = []
    visited = set()
    
    def dfs_predecessors(code: str):
        if code in visited:
            return
        visited.add(code)
        for predecessor in G.predecessors(code):
            p_mastered = skill_states.get(predecessor, 0.5)
            if p_mastered < mastery_threshold:
                dfs_predecessors(predecessor)
        p_mastered = skill_states.get(code, 0.5)
        if p_mastered < mastery_threshold:
            chain.append(code)
    
    dfs_predecessors(failed_code)
    return chain
```

**FR-6.5 — Full Prerequisite Graph for Grade 4 Oregon Standards**

The complete directed edge set loaded into the `prerequisite_relationships` table at Stage 2 launch (inclusive of Stage 1 edges, plus additional Grade 4 internal dependencies identified during Stage 2 design):

```
# Grade 3 → Grade 4 prerequisite edges (from Stage 1)
3.OA.C.7  → 4.OA.A.1   (required)
3.OA.C.7  → 4.OA.A.2   (required)
3.OA.C.7  → 4.NBT.B.5  (required)
3.OA.C.7  → 4.NBT.B.6  (required)
3.OA.C.7  → 4.NF.B.4   (required)
3.OA.A.4  → 4.OA.A.2   (required)
3.OA.D.8  → 4.OA.A.3   (required)
3.NBT.A.2 → 4.NBT.B.4  (required)
3.NBT.A.3 → 4.NBT.B.5  (required)
3.NBT.A.2 → 4.NBT.A.2  (recommended)
3.NF.A.1  → 4.NF.A.1   (required)
3.NF.A.1  → 4.NF.B.3   (required)
3.NF.A.3  → 4.NF.A.2   (required)
3.GM.C.7  → 4.GM.D.9   (required)
3.GM.D.8  → 4.GM.D.9   (recommended)

# Grade 4 internal dependency edges
4.NBT.A.1 → 4.NBT.A.2  (required)
4.NBT.A.2 → 4.NBT.A.3  (required)
4.NBT.B.4 → 4.OA.A.3   (required)
4.NBT.B.5 → 4.OA.A.3   (required)
4.NBT.B.5 → 4.NBT.B.6  (required)
4.NF.A.1  → 4.NF.A.2   (required)
4.NF.A.1  → 4.NF.B.3   (required)
4.NF.A.1  → 4.NF.C.5   (required)
4.NF.B.3  → 4.NF.B.4   (required)
4.NF.B.4  → 4.DR.A.1   (recommended)
4.NF.C.5  → 4.NF.C.6   (required)
4.NF.C.6  → 4.NF.C.7   (required)
4.NF.C.7  → 4.DR.A.1   (recommended)
4.GM.A.1  → 4.GM.A.2   (required)
4.GM.A.2  → 4.GM.A.3   (required)
4.GM.C.6  → 4.GM.C.7   (required)
4.GM.C.7  → 4.GM.C.8   (required)
4.GM.D.9  → 4.GM.B.5   (recommended)
4.OA.B.4  → 4.OA.C.5   (recommended)
4.DR.B.2  → 4.DR.C.3   (required)
```

**FR-6.6 — API: generate_learning_sequence**

```
POST /api/v1/learning-plans/generate-sequence
Auth: internal service-to-service (not exposed to client directly)
```

```python
def generate_learning_sequence(student_id: str) -> list[dict]:
    """
    Generate an ordered list of skills (modules) for a student's learning plan.
    Returns a list of dicts with: standard_code, priority_score, remediation_chain,
    estimated_sessions, track.
    """
    skill_states = get_student_skill_states(student_id)  # from student_skill_states table
    G = get_skill_graph()  # cached singleton
    
    # 1. Determine student track
    below_par_count = sum(1 for s in skill_states.values() if s['proficiency_level'] == 'Below Par')
    above_par_count = sum(1 for s in skill_states.values() if s['proficiency_level'] == 'Above Par')
    total_assessed = len(skill_states)
    
    if below_par_count / total_assessed >= 0.40:
        track = 'catch_up'
    elif above_par_count / total_assessed >= 0.70:
        track = 'accelerate'
    else:
        track = 'on_track'
    
    # 2. Identify non-mastered skills (P(mastered) < 0.85)
    p_mastered_map = {code: s['p_mastered'] for code, s in skill_states.items()}
    non_mastered = {code: p for code, p in p_mastered_map.items() if p < 0.85}
    
    # 3. Topological sort on non-mastered skills
    sorted_codes = get_topological_sequence(G, list(non_mastered.keys()))
    
    # 4. Apply priority within topological level groups
    priority_scores = {code: compute_priority_score(code, non_mastered.get(code, 0.5), G)
                       for code in sorted_codes}
    
    # 5. For catch_up track: prepend all below-par Grade 3 prerequisites
    if track == 'catch_up':
        prereq_below_par = [code for code in sorted_codes
                            if G.nodes[code]['grade'] == 3 and p_mastered_map.get(code, 0) < 0.85]
        grade4_below_par = [code for code in sorted_codes
                            if G.nodes[code]['grade'] == 4 and p_mastered_map.get(code, 0) < 0.85]
        ordered_codes = prereq_below_par + grade4_below_par
    else:
        ordered_codes = sorted_codes
    
    # 6. Build module descriptors
    modules = []
    for code in ordered_codes:
        p_m = p_mastered_map.get(code, 0.5)
        modules.append({
            'standard_code': code,
            'priority_score': priority_scores.get(code, 0),
            'p_mastered_initial': p_m,
            'estimated_sessions': _estimate_sessions_to_mastery(p_m),
            'track': track
        })
    
    return modules


def _estimate_sessions_to_mastery(p_mastered: float) -> int:
    """
    Rough estimate of 20-minute practice sessions to reach mastery (P > 0.85).
    Based on BKT default P(learn) = 0.10 per session.
    """
    if p_mastered >= 0.85:
        return 0
    if p_mastered >= 0.70:
        return 2
    if p_mastered >= 0.50:
        return 4
    if p_mastered >= 0.30:
        return 6
    return 8
```

**FR-6.7 — Partial Completion Support**

The skill graph engine MUST handle students who return after partially completing their learning plan:

- On each plan re-evaluation trigger (daily, or after each practice session), re-fetch all `student_skill_states` for the student.
- Any skill where `p_mastered >= 0.85` is treated as mastered and excluded from the sequence.
- New skills that have become unblocked (all prerequisites now mastered) are added to the plan.
- If a previously "On Par" skill has regressed (P(mastered) drops due to incorrect practice answers — possible in BKT), it is re-inserted into the plan at the appropriate position.
- The re-sequencing is computed in < 1 second (graph traversal is O(V+E), V ≈ 38 nodes, E ≈ 35 edges).

**FR-6.8 — Dynamic Re-Sequencing**

The learning plan is not a static document generated once. After each practice session completes, the system:
1. Updates all BKT states for practiced skills.
2. Checks for newly mastered skills (P(mastered) ≥ 0.85 crossed for the first time).
3. Re-evaluates the learning sequence.
4. If the sequence changes, updates `plan_modules` table records (status, order).
5. If a new module unlocks, publishes a `module_unlocked` event (used for badge awards in FR-9).

The student dashboard reflects the re-sequenced plan on next load (no real-time push required in Stage 2).

---

### FR-7: Learning Plan Generation

**FR-7.1 — Plan Hierarchy**

```
Learning Plan (1 per student)
  └── Module (1 per skill/standard being worked on)
        └── Lesson (1–3 lessons per module; each = one learning session)
              └── Practice Session (adaptive question set: 10–15 questions, ~20 minutes)
```

- **Learning Plan**: The top-level entity, tied to one student. A student has exactly one active plan at a time. Completed plans are archived (status = 'completed') and a new plan is generated if the student's diagnostic is retaken.
- **Module**: Represents one skill/standard (e.g., "Multiplication Facts Fluency" = 3.OA.C.7). A module may be in status: `locked`, `available`, `in_progress`, `mastered`. Modules unlock sequentially when prerequisites are mastered. Duration: 1–8 practice sessions depending on starting P(mastered).
- **Lesson**: A conceptual grouping within a module. Lesson 1 = "Introduction" (lower difficulty, concept-building). Lesson 2 = "Practice" (medium difficulty, application). Lesson 3 = "Challenge" (higher difficulty, word problems). Not all modules require 3 lessons — BKT determines when mastery is reached.
- **Practice Session**: The actual student interaction unit. Each session contains 10–15 questions selected by the adaptive engine from the question bank for the current module's standard. Sessions target ~20 minutes of focused practice.

**FR-7.2 — Module Definition**

Each module in the `plan_modules` table encapsulates:
- The target standard (`standard_code`)
- The child-friendly module name (e.g., "Multiplication Facts")
- The starting BKT state (copied from `student_skill_states` at plan generation time)
- The current BKT state (updated after each practice session)
- The module status (locked / available / in_progress / mastered)
- Estimated sessions to mastery (updated dynamically)
- Actual sessions completed

Module names (child-friendly labels mapped to standard codes):

| Standard Code | Module Name |
|--------------|-------------|
| 3.OA.A.4 | Finding the Missing Number |
| 3.OA.C.7 | Multiplication & Division Facts |
| 3.OA.D.8 | Two-Step Problem Solving |
| 3.NBT.A.2 | Adding & Subtracting Big Numbers |
| 3.NBT.A.3 | Multiplying by Tens |
| 3.NF.A.1 | Understanding Fractions |
| 3.NF.A.3 | Comparing Fractions |
| 3.GM.C.7 | Finding Area |
| 3.GM.D.8 | Measuring Perimeter |
| 4.OA.A.1 | Multiplicative Comparisons |
| 4.OA.A.2 | Comparison Word Problems |
| 4.OA.A.3 | Multi-Step Problem Solving |
| 4.OA.B.4 | Factors, Multiples & Primes |
| 4.OA.C.5 | Number Patterns |
| 4.NBT.A.1 | Place Value: How Digits Work |
| 4.NBT.A.2 | Reading & Writing Big Numbers |
| 4.NBT.A.3 | Rounding to Any Place |
| 4.NBT.B.4 | Adding & Subtracting Large Numbers |
| 4.NBT.B.5 | Multi-Digit Multiplication |
| 4.NBT.B.6 | Division with Remainders |
| 4.NF.A.1 | Equivalent Fractions |
| 4.NF.A.2 | Comparing Fractions (Different Denominators) |
| 4.NF.B.3 | Adding & Subtracting Fractions |
| 4.NF.B.4 | Multiplying Fractions by Whole Numbers |
| 4.NF.C.5 | Fractions and Hundredths |
| 4.NF.C.6 | Decimal Notation |
| 4.NF.C.7 | Comparing Decimals |
| 4.GM.A.1 | Lines, Rays & Angles |
| 4.GM.A.2 | Classifying Shapes |
| 4.GM.A.3 | Lines of Symmetry |
| 4.GM.B.4 | Measurement Conversions |
| 4.GM.B.5 | Measurement Word Problems |
| 4.GM.C.6 | Understanding Angles |
| 4.GM.C.7 | Measuring Angles |
| 4.GM.C.8 | Adding Angles |
| 4.GM.D.9 | Area & Perimeter |
| 4.DR.A.1 | Line Plots with Fractions |
| 4.DR.B.2 | Reading Bar Graphs & Tables |
| 4.DR.C.3 | Mean, Median, Mode, Range |

**FR-7.3 — Lesson Structure Within a Module**

Each lesson within a module is defined as:

```json
{
  "lesson_id": "uuid",
  "module_id": "uuid",
  "lesson_number": 1,
  "lesson_title": "Introduction: Multiplication Facts",
  "lesson_type": "intro",  // "intro" | "practice" | "challenge"
  "difficulty_range": [1, 2],
  "question_count_target": 10,
  "mastery_threshold_to_advance": 0.70,
  "status": "available",  // "locked" | "available" | "completed"
  "completed_at": null,
  "p_mastered_at_completion": null
}
```

Lesson progression within a module:
1. **Intro lesson**: 10 questions, difficulty 1–2. Target: build confidence, re-activate prior knowledge.
2. **Practice lesson**: 12 questions, difficulty 2–4. Target: skill application and fluency.
3. **Challenge lesson**: 10 questions, difficulty 3–5. Target: push toward mastery; word problems, multi-step.

BKT P(mastered) is evaluated after each lesson. If P(mastered) ≥ 0.85 after the intro lesson, the module is marked mastered and subsequent lessons are skipped (above-par students with high P(mastered) initial values move very quickly).

**FR-7.4 — Practice Session Structure**

A practice session is created dynamically when a student starts a lesson. It is NOT pre-computed — questions are selected at session start using the current BKT state and available question pool.

```json
{
  "session_id": "uuid",
  "lesson_id": "uuid",
  "student_id": "uuid",
  "standard_code": "3.OA.C.7",
  "question_count": 12,
  "difficulty_target": 3,
  "started_at": "2024-09-10T15:00:00Z",
  "completed_at": null,
  "status": "in_progress",
  "questions": [
    {"question_id": "uuid", "sequence": 1, "difficulty": 2},
    {"question_id": "uuid", "sequence": 2, "difficulty": 2},
    ...
  ],
  "bkt_state_before": {"p_mastered": 0.40, "p_t": 0.10, "p_s": 0.10, "p_g": 0.20},
  "bkt_state_after": null
}
```

**FR-7.5 — Estimated Time to Mastery per Module**

Based on BKT default learning rate P(T) = 0.10 (10% chance of learning the skill per practice opportunity):

| Starting P(mastered) | Estimated Sessions | Estimated Wall-Clock Time |
|---------------------|-------------------|--------------------------|
| 0.10 (Below Par) | 6–8 sessions | 2–2.5 hours / 8–10 days @ 20 min/day |
| 0.40 (Low On Par) | 4–5 sessions | 1.5 hours / 6–7 days |
| 0.50 (On Par) | 3–4 sessions | 1 hour / 4–5 days |
| 0.75 (High On Par) | 1–2 sessions | 30–40 minutes / 2 days |
| 0.80 (Above Par) | 1 session | 20 minutes / 1 day |

These estimates are displayed to parents on the plan dashboard and are updated dynamically based on actual BKT learning rate calibration (Stage 3 enhancement).

**FR-7.6 — Total Plan Timeline Estimate**

The total plan timeline (weeks to grade-level proficiency) is displayed on the parent dashboard:

```python
def estimate_plan_duration_weeks(modules: list[dict], minutes_per_day: int = 20) -> float:
    """
    Estimate total weeks to complete the learning plan.
    modules: list of module dicts with 'estimated_sessions' field.
    Assumes 20 minutes/day, 5 days/week.
    """
    total_sessions = sum(m['estimated_sessions'] for m in modules if m['estimated_sessions'] > 0)
    total_minutes = total_sessions * 20
    minutes_per_week = minutes_per_day * 5
    return round(total_minutes / minutes_per_week, 1)
```

The estimate is shown as "Approximately X weeks with 20 minutes/day" and is updated weekly based on actual pace.

**FR-7.7 — Plan Generation Algorithm**

The full plan generation algorithm, triggered by `diagnostic_completed` event:

```python
async def generate_learning_plan(student_id: str) -> str:  # returns plan_id
    """
    Full plan generation pipeline. Called asynchronously after diagnostic completion.
    Should complete in < 5 seconds.
    """
    # Step 1: Load student skill states from diagnostic
    skill_states = await db.fetch_all(
        "SELECT standard_code, p_mastered, proficiency_level "
        "FROM student_skill_states WHERE student_id = $1",
        student_id
    )
    
    # Step 2: Load skill dependency graph (cached)
    G = get_skill_graph()
    
    # Step 3: Generate ordered module sequence
    p_mastered_map = {s['standard_code']: s['p_mastered'] for s in skill_states}
    module_sequence = generate_learning_sequence(student_id)
    
    # Step 4: Determine track
    track = module_sequence[0]['track'] if module_sequence else 'on_track'
    
    # Step 5: Calculate plan-level estimates
    total_weeks = estimate_plan_duration_weeks(module_sequence)
    
    # Step 6: Create learning_plan record
    plan_id = await db.fetchval(
        """
        INSERT INTO learning_plans (student_id, track, status, estimated_weeks, total_modules)
        VALUES ($1, $2, 'active', $3, $4)
        RETURNING plan_id
        """,
        student_id, track, total_weeks, len(module_sequence)
    )
    
    # Step 7: Create plan_modules records
    for i, module_def in enumerate(module_sequence):
        module_status = 'available' if i == 0 else 'locked'
        # First module always available; rest locked until predecessors mastered
        
        await db.execute(
            """
            INSERT INTO plan_modules (
                plan_id, standard_code, module_name, sequence_order,
                status, p_mastered_initial, estimated_sessions
            ) VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
            plan_id,
            module_def['standard_code'],
            get_module_name(module_def['standard_code']),  # lookup from name mapping
            i + 1,
            module_status,
            module_def['p_mastered_initial'],
            module_def['estimated_sessions']
        )
    
    # Step 8: Create lessons for the first available module
    first_module = await db.fetchrow(
        "SELECT * FROM plan_modules WHERE plan_id = $1 AND status = 'available' "
        "ORDER BY sequence_order LIMIT 1",
        plan_id
    )
    await create_lessons_for_module(first_module['module_id'])
    
    # Step 9: Update student diagnostic_status
    await db.execute(
        "UPDATE students SET diagnostic_status = 'COMPLETED' WHERE student_id = $1",
        student_id
    )
    
    # Step 10: Publish plan_generated event
    await redis.xadd('padi:events', {
        'event_type': 'plan_generated',
        'student_id': student_id,
        'plan_id': plan_id,
        'track': track,
        'timestamp': datetime.utcnow().isoformat()
    })
    
    return plan_id
```

**FR-7.8 — Three Learning Tracks**

| Track | Trigger Condition | Plan Behavior |
|-------|-------------------|---------------|
| **Catch Up** | ≥ 40% of assessed skills Below Par | Plan starts with ALL below-par Grade 3 prerequisites. Grade 4 content unlocks only after all prerequisite modules are mastered. Emphasis on foundational fluency. |
| **On Track** | Neither Catch Up nor Accelerate | Plan addresses below-par skills in topological order, mixing prerequisite remediation with Grade 4 content as prerequisites clear. |
| **Accelerate** | ≥ 70% of assessed skills Above Par | Plan skips all skills with P(mastered) ≥ 0.80. Prioritizes Grade 4 content; includes difficulty-4/5 and DOK-3/4 questions. Adds enrichment modules (math puzzles, real-world applications) as bonus content. |

Track is displayed on the parent dashboard with a brief plain-language explanation (e.g., "Jayden is on a Catch Up track. This means we'll build his foundational multiplication and fraction skills before moving to Grade 4 content.").

**FR-7.9 — Plan JSON Schema**

Complete learning plan JSON structure (as serialized for API responses):

```json
{
  "plan_id": "550e8400-e29b-41d4-a716-446655440000",
  "student_id": "uuid",
  "student_display_name": "Jayden",
  "track": "catch_up",
  "status": "active",
  "created_at": "2024-09-05T16:00:00Z",
  "estimated_weeks": 8.5,
  "minutes_per_day_assumed": 20,
  "progress": {
    "modules_total": 12,
    "modules_mastered": 1,
    "modules_in_progress": 1,
    "modules_locked": 10,
    "percent_complete": 8.3
  },
  "current_module": {
    "module_id": "uuid",
    "standard_code": "3.OA.C.7",
    "module_name": "Multiplication & Division Facts",
    "status": "in_progress",
    "sequence_order": 2,
    "p_mastered_initial": 0.10,
    "p_mastered_current": 0.31,
    "estimated_sessions": 6,
    "sessions_completed": 2,
    "lessons": [
      {
        "lesson_id": "uuid",
        "lesson_number": 1,
        "lesson_title": "Introduction: Multiplication Facts",
        "lesson_type": "intro",
        "status": "completed",
        "completed_at": "2024-09-06T15:30:00Z",
        "p_mastered_at_completion": 0.22
      },
      {
        "lesson_id": "uuid",
        "lesson_number": 2,
        "lesson_title": "Practice: Multiplication Facts",
        "lesson_type": "practice",
        "status": "available",
        "completed_at": null,
        "p_mastered_at_completion": null
      },
      {
        "lesson_id": "uuid",
        "lesson_number": 3,
        "lesson_title": "Challenge: Multiplication Facts",
        "lesson_type": "challenge",
        "status": "locked",
        "completed_at": null,
        "p_mastered_at_completion": null
      }
    ]
  },
  "modules": [
    {
      "module_id": "uuid",
      "standard_code": "3.OA.C.7",
      "module_name": "Multiplication & Division Facts",
      "status": "in_progress",
      "sequence_order": 1,
      "p_mastered_current": 0.31,
      "estimated_sessions": 6,
      "sessions_completed": 2
    },
    {
      "module_id": "uuid",
      "standard_code": "4.NBT.B.5",
      "module_name": "Multi-Digit Multiplication",
      "status": "locked",
      "sequence_order": 2,
      "p_mastered_current": 0.20,
      "estimated_sessions": 7,
      "sessions_completed": 0
    }
  ]
}
```

**FR-7.10 — Plan Storage in PostgreSQL**

Plan data is stored in the `learning_plans` and `plan_modules` tables (schemas defined in Section 2.4). Key constraints:
- One active plan per student (`UNIQUE(student_id)` partial index on `status = 'active'`).
- Module sequence order is enforced; reordering requires an explicit re-sequence operation.
- Module status transitions are tracked with timestamps: `available_at`, `started_at`, `mastered_at`.
- All BKT state snapshots (before/after each session) are stored in `plan_modules.bkt_history` as a JSONB array for analytics.

---

### FR-8: AI-Powered Learning Content Generation

**FR-8.1 — LLM Question Generation Pipeline Overview**

The pipeline uses o3-mini as the primary generation model, with the following 5-step flow for each question:

```
Step 1: GENERATE    — o3-mini generates question + solution code (Program of Thought)
Step 2: EXECUTE     — Python sandboxed execution verifies the answer is correct
Step 3: CLASSIFY    — Automated quality checks (solvability, age-appropriateness, alignment)
Step 4: VERIFY      — Standard code alignment check (automated + threshold-gated human review)
Step 5: STORE       — Approved questions stored in generated_questions → promoted to questions table
```

Each step can produce a PASS or FAIL outcome. A question must PASS all 5 steps to be stored as validated. Failures at any step are logged in `question_validation_results` with the failure reason.

**FR-8.2 — Question Generation Prompt Template**

Full prompt template for o3-mini question generation (see also Section 2.6 for complete prompts):

```
SYSTEM:
You are an expert elementary mathematics question writer creating content for PADI.AI,
an adaptive math learning app for Oregon 4th graders. You write questions that are:
- Mathematically accurate and unambiguous
- Written at a 4th-grade reading level (Flesch-Kincaid Grade Level 3-5)
- Culturally inclusive, using diverse names (Maya, Jordan, Alex, Sam, Mia, etc.)
- Oregon-relevant where possible (mention Oregon geography, nature, and activities)
- Free of bias, stereotypes, or culturally insensitive content
- Precise: one and only one correct answer

USER:
Generate a math question with the following specifications:

Standard Code: {standard_code}
Standard Description: {standard_description}
Difficulty Level: {difficulty_level} (1=easiest recall, 5=hardest application; target DOK {dok_level})
Question Type: {question_type} (multiple_choice | short_numeric | fraction_input)
Context Type: {context_type} (word_problem | computation | visual | mixed)
Context Theme: {context_theme} (one of: {themes_list})

If question_type is "multiple_choice", generate:
- Exactly 4 answer choices (A, B, C, D)
- Exactly one correct answer
- Three distractors that each reflect a specific common student misconception (describe each misconception)

Include a step-by-step solution (maximum 5 steps, each in plain English).

Output your response as a JSON object with this exact structure:
{
  "question_text": "...",  // Use \\(...\\) for inline LaTeX/KaTeX math
  "question_type": "...",
  "answer_options": [     // null if not multiple_choice
    {"id": "A", "text": "...", "is_correct": false, "misconception": "..."},
    {"id": "B", "text": "...", "is_correct": true,  "misconception": null},
    {"id": "C", "text": "...", "is_correct": false, "misconception": "..."},
    {"id": "D", "text": "...", "is_correct": false, "misconception": "..."}
  ],
  "correct_answer": "...",         // For MC: option id; for numeric: value as string
  "correct_answer_alt": [],        // Alternative acceptable answers
  "numeric_tolerance": null,       // float or null
  "solution_steps": [
    {"step": 1, "text": "..."},
    ...
  ],
  "solution_python_code": "...",   // Python code that computes the answer; last line: print(answer)
  "difficulty_level": {difficulty_level},
  "dok_level": {dok_level},
  "context_type": "{context_type}",
  "tags": [],
  "reading_level_estimate": "...", // "Grade 3" | "Grade 4" | "Grade 5"
  "estimated_completion_minutes": 2
}
```

**FR-8.3 — Generation Validation Pipeline Detail**

**Step 1: Generate** (o3-mini API call)
- Input: Filled prompt template from FR-8.2.
- Output: JSON object (may require JSON extraction from model response if model adds preamble).
- Validation: JSON parseable, all required fields present, answer_options has exactly 4 items if MC, correct answer id exists in options.
- On failure: retry once with adjusted prompt. Log failure.

**Step 2: Execute** (Python sandbox)
- Extract `solution_python_code` from the model output.
- Execute in a sandboxed subprocess with 10-second timeout, no network access, no file system access.
- Capture stdout (the printed answer).
- Compare stdout to `correct_answer` (with numeric tolerance if applicable).

```python
import subprocess
import sys
import ast

def execute_solution_safely(code: str, expected_answer: str, tolerance: float = 0) -> dict:
    """
    Execute the solution Python code in a restricted subprocess.
    Returns {'passed': bool, 'actual_answer': str, 'error': str | None}
    """
    # Security: allow only safe builtins
    restricted_code = f"""
import math
from fractions import Fraction

{code}
"""
    try:
        result = subprocess.run(
            [sys.executable, '-c', restricted_code],
            capture_output=True,
            text=True,
            timeout=10,
            env={},  # no environment variables
        )
        actual = result.stdout.strip()
        
        if tolerance > 0:
            try:
                passed = abs(float(actual) - float(expected_answer)) <= tolerance
            except ValueError:
                passed = actual == expected_answer
        else:
            # Try numeric equality first, then string
            try:
                passed = float(actual) == float(expected_answer)
            except ValueError:
                passed = actual.lower() == expected_answer.lower()
        
        return {'passed': passed, 'actual_answer': actual, 'error': result.stderr or None}
    
    except subprocess.TimeoutExpired:
        return {'passed': False, 'actual_answer': None, 'error': 'Execution timeout (10s)'}
    except Exception as e:
        return {'passed': False, 'actual_answer': None, 'error': str(e)}
```

**Step 3: Classify** (Automated quality checks)
All checks run synchronously in Python. A question passes Step 3 if all classifiers return PASS:

```python
def classify_question_quality(question: dict) -> dict:
    """
    Run automated quality classifiers on a generated question.
    Returns {'passed': bool, 'checks': {check_name: {'passed': bool, 'score': float, 'reason': str}}}
    """
    checks = {}
    
    # 3a: Reading level check (Flesch-Kincaid Grade Level must be between 2.5 and 5.5)
    from textstat import flesch_kincaid_grade
    fk_grade = flesch_kincaid_grade(question['question_text'])
    checks['reading_level'] = {
        'passed': 2.5 <= fk_grade <= 5.5,
        'score': fk_grade,
        'reason': f'FK Grade Level: {fk_grade}'
    }
    
    # 3b: Question length check (15–200 words for word problems; 5–50 for computation)
    word_count = len(question['question_text'].split())
    if question['context_type'] == 'computation':
        length_ok = 5 <= word_count <= 50
    else:
        length_ok = 15 <= word_count <= 200
    checks['question_length'] = {
        'passed': length_ok,
        'score': word_count,
        'reason': f'{word_count} words'
    }
    
    # 3c: No PII / inappropriate content keywords
    PROHIBITED_WORDS = ['kill', 'die', 'weapon', 'gun', 'alcohol', 'drug', 'violence']
    found_prohibited = [w for w in PROHIBITED_WORDS if w in question['question_text'].lower()]
    checks['content_safety'] = {
        'passed': len(found_prohibited) == 0,
        'score': len(found_prohibited),
        'reason': f'Found prohibited words: {found_prohibited}' if found_prohibited else 'Clean'
    }
    
    # 3d: Answer uniqueness for MC (exactly one is_correct = True)
    if question['question_type'] == 'multiple_choice':
        correct_count = sum(1 for opt in question['answer_options'] if opt.get('is_correct'))
        checks['mc_answer_uniqueness'] = {
            'passed': correct_count == 1,
            'score': correct_count,
            'reason': f'{correct_count} options marked correct (must be 1)'
        }
    
    # 3e: Solution steps present (1–5 steps)
    step_count = len(question.get('solution_steps', []))
    checks['solution_steps_present'] = {
        'passed': 1 <= step_count <= 5,
        'score': step_count,
        'reason': f'{step_count} solution steps'
    }
    
    overall_passed = all(c['passed'] for c in checks.values())
    return {'passed': overall_passed, 'checks': checks}
```

**Step 4: Standard Alignment Verification**

An LLM call (cheaper model: GPT-4o-mini or Claude Haiku) verifies that the generated question actually tests the target standard:

```python
async def verify_standard_alignment(
    question_text: str,
    standard_code: str,
    standard_description: str
) -> dict:
    """
    Use a lightweight LLM to verify that the question tests the target standard.
    Returns {'passed': bool, 'confidence': float, 'reasoning': str}
    """
    prompt = f"""
Does the following math question test the standard described?

Standard Code: {standard_code}
Standard Description: {standard_description}

Question: {question_text}

Answer with a JSON object:
{{
  "tests_the_standard": true | false,
  "confidence": 0.0 to 1.0,
  "reasoning": "Brief explanation"
}}
"""
    response = await call_llm(prompt, model='claude-haiku-3')  # cheap model for classification
    result = parse_json_from_response(response)
    return {
        'passed': result['tests_the_standard'] and result['confidence'] >= 0.85,
        'confidence': result['confidence'],
        'reasoning': result['reasoning']
    }
```

Questions with alignment confidence < 0.85 are routed to the human review queue (Step 5).

**Step 5: Human Review Queue**

Questions that fail any automated step, or pass automated steps with borderline confidence (0.70–0.84 on alignment), are inserted into a `question_validation_results` record with `requires_human_review = TRUE` and appear in the admin question review queue (same UI as seed question validation from Stage 1).

Questions that pass all 5 steps with confidence ≥ 0.85 are automatically marked `is_validated = TRUE` and promoted to the `questions` table with `source = 'llm_generated'`.

> **Curriculum Specialist Required (Stage 2 Kickoff):** Starting at Stage 2, a part-time Oregon-credentialed elementary math educator must be engaged as a contractor to review AI-generated questions. Budget: $750–$1,500/month (10–15 hrs at $75–$100/hr). Find via Upwork ("Oregon elementary math teacher") or Oregon Education Association referrals. This role validates mathematical accuracy, Oregon OSAS format alignment, and age-appropriateness for a 30–50 question sample per month. Without this review, the automated validation pipeline alone is insufficient for student-facing content.

**FR-8.4 — Generation Throughput Requirements**

- The pipeline SHALL generate and validate ≥ 100 questions per hour in steady-state operation.
- This is achieved through parallel processing: N worker processes (N configurable, default 4), each processing one question at a time through the 5-step pipeline.
- Generation jobs are queued in `generation_jobs` table and processed by Celery workers (Python async task queue with Redis broker).
- o3-mini API call latency target: < 8 seconds per question. Step 2 (code execution): < 10 seconds. Step 3 (classification): < 0.5 seconds (local Python). Step 4 (alignment LLM): < 3 seconds.
- Total pipeline latency per question: < 25 seconds → at 4 workers: ~10 questions/minute → ~600 questions/hour (exceeds 100/hour requirement with significant headroom).

**FR-8.5 — Generated Question Storage**

Generated questions are first stored in `generated_questions` table (with validation status tracking) before being promoted to the main `questions` table. This separation allows:
- Validation pipeline to work on draft questions without affecting the live question bank.
- Analytics on generation quality (pass rates by standard, by model version, by prompt version).
- Rollback if a batch of questions is found to have systematic issues.

Promotion to `questions` table is done by a daily batch job that:
1. Selects all `generated_questions` where `validation_status = 'passed'` and `promoted_at IS NULL`.
2. Inserts them into `questions` table.
3. Updates `generated_questions.promoted_at = NOW()`.

**FR-8.6 — Question Caching Strategy**

To avoid generating semantically duplicate questions:
- Before generating a new question for a `(standard_code, difficulty_level, question_type, context_type)` combination, check if the pool already has ≥ 20 validated questions for that combination. If yes, skip generation for that combination.
- A Redis set `padi:gen:pool:{standard_code}:{difficulty}:{type}:{context}` tracks current count. Updated when questions are promoted.
- Embedding-based deduplication: new generated questions are embedded using a lightweight sentence embedding model (all-MiniLM-L6-v2, 384 dimensions, stored in pgvector). Before storing a new question, compute cosine similarity against all questions for the same standard. If any question has cosine similarity > 0.92, the new question is flagged as a near-duplicate and discarded.

```python
from sentence_transformers import SentenceTransformer
import numpy as np

model = SentenceTransformer('all-MiniLM-L6-v2')

def is_near_duplicate(new_question_text: str, standard_code: str, db) -> bool:
    """
    Returns True if a semantically near-duplicate question already exists in the bank.
    """
    new_embedding = model.encode(new_question_text)
    
    # pgvector cosine similarity search
    similar = db.query(
        """
        SELECT question_id, 1 - (embedding <=> $1::vector) AS similarity
        FROM questions
        WHERE standard_code = $2
          AND 1 - (embedding <=> $1::vector) > 0.92
        LIMIT 1
        """,
        new_embedding.tolist(), standard_code
    )
    return len(similar) > 0
```

**FR-8.7 — Context/Theme Diversity Requirements**

Each generation batch for a standard SHALL include a variety of word problem contexts. The 12 permitted context themes (and their sub-themes) are:

| Theme | Examples for Oregon Context |
|-------|---------------------------|
| `food` | Pizza, apples from Hood River, salmon, trail mix |
| `sports` | Basketball, soccer, hiking, Timbers FC, Blazers |
| `animals` | Deer, beavers, sea otters, bald eagles, salmon |
| `oregon_geography` | Columbia River, Crater Lake, Mount Hood, Willamette Valley |
| `school` | Classroom, library books, pencils, school supplies |
| `money` | Allowance, market stalls, farmers market |
| `transportation` | Bikes, MAX light rail (Portland), road trips |
| `nature` | Forests, rain, camping, Oregon coast tidepools |
| `science` | Measuring experiments, recycling, weather data |
| `art` | Crafts, painting supplies, beads |
| `community` | Neighborhood park, food bank donations, team projects |
| `computation` | No story context; pure symbolic (for difficulty 1–2 questions) |

Each `(standard_code, question_type)` combination SHALL have at most 30% of its questions from any single theme. The generation job rotates themes using a round-robin schedule stored in `generation_jobs.context_theme`.

**FR-8.8 — DOK Level Targeting**

Generation prompts explicitly target DOK levels matched to the standard's canonical DOK level:

| Standard DOK | Questions at DOK-1 | Questions at DOK-2 | Questions at DOK-3 |
|-------------|-------------------|--------------------|-------------------|
| 1 | 60% | 40% | 0% |
| 2 | 20% | 60% | 20% |
| 3 | 10% | 30% | 60% |

DOK level is specified in the generation prompt (`dok_level` placeholder). The automated classifier checks that `solution_steps` complexity is consistent with the target DOK (DOK-1: 1–2 steps; DOK-2: 2–3 steps; DOK-3: 3–5 steps).

**FR-8.9 — Distractor Generation for Multiple Choice**

For MC questions, distractors are generated by o3-mini as part of the same prompt (integrated, not a separate call). The prompt requires each wrong answer to be accompanied by a `misconception` field explaining what error a student would make to arrive at that wrong answer.

Distractor quality requirements enforced by automated classifier:
- No distractor may be equal to the correct answer (numeric comparison with tolerance).
- No two distractors may be equal to each other.
- For computation questions: at least one distractor must be within ±20% of the correct answer (plausible wrong answer, not obviously off).
- For word problems: at least one distractor must represent a common operation error (e.g., adding instead of multiplying).

**FR-8.10 — Content Safety Filtering**

Two-layer content safety filtering:
1. **Keyword blocklist** (Step 3c above): blocks prohibited words synchronously.
2. **LLM safety classifier** (separate call, runs in parallel with Step 4): evaluates question for subtle bias, cultural insensitivity, or inappropriate scenarios.

```python
async def check_content_safety_llm(question_text: str) -> dict:
    """
    LLM-based content safety check for subtle issues not caught by keyword blocklist.
    """
    prompt = f"""
Review this math word problem for use with 9-year-old students:

"{question_text}"

Check for:
1. Cultural stereotypes or bias
2. Scenarios inappropriate for children (violence, adult content, scary topics)
3. Assumptions about family structure, income, or background that may exclude students
4. Any other concerns

Respond with JSON:
{{
  "safe": true | false,
  "concerns": ["list of concerns, or empty array if none"],
  "severity": "none" | "minor" | "major"
}}
"""
    response = await call_llm(prompt, model='claude-haiku-3')
    result = parse_json_from_response(response)
    return {
        'passed': result['safe'] and result['severity'] != 'major',
        'concerns': result['concerns'],
        'severity': result['severity']
    }
```

**FR-8.11 — Rate Limiting and Cost Management**

- **o3-mini** (generation): 4 parallel workers × 1 call/25 seconds = ~576 calls/hour. At average 500 tokens input + 400 tokens output = 900 tokens/call. o3-mini pricing: ~$0.0011/1K input tokens + ~$0.0044/1K output tokens. Cost per question: ~$0.55/1K × 0.9K = ~$0.0022. Total for 5,000 questions: ~$11. Well within budget.
- **Claude Haiku** (alignment + safety): 2 calls/question × 200 tokens average = 400 tokens/call. Haiku pricing ~$0.00025/1K input. Cost per question: ~$0.0001. Negligible.
- **Rate limiting**: A global rate limiter (token bucket, implemented in Redis) caps o3-mini calls at 500 RPM to stay within API tier limits. Workers check rate limit before each API call.
- **Cost tracking**: Each LLM API call records tokens used and estimated cost in `generation_jobs.llm_cost_usd`. A daily alert fires if daily LLM spend exceeds $5.
- **Budget hard stop**: A Redis counter `padi:llm:daily_spend_cents` accumulates daily spend. If it exceeds 1000 cents ($10), generation workers stop accepting new jobs for the remainder of the day and alert the ops team.

**FR-8.12 — Generation Job Management**

Generation jobs are managed via the `generation_jobs` table and Celery:

```python
# Celery task definition
from celery import Celery

app = Celery('padi-ai', broker='redis://redis:6379/1')

@app.task(max_retries=2, default_retry_delay=60)
def generate_question_batch(job_id: str):
    """
    Process a single generation job: generate one question, validate it, store result.
    """
    job = db.get_generation_job(job_id)
    
    try:
        # Step 1: Generate
        question_draft = call_o3_mini(
            fill_prompt_template(job['standard_code'], job['difficulty_level'],
                               job['question_type'], job['context_type'],
                               job['context_theme'])
        )
        
        # Step 2: Execute solution
        exec_result = execute_solution_safely(
            question_draft['solution_python_code'],
            question_draft['correct_answer'],
            question_draft.get('numeric_tolerance', 0)
        )
        
        # Step 3: Quality classification
        quality_result = classify_question_quality(question_draft)
        
        # Step 4: Standard alignment + safety (async, run in parallel)
        alignment_result, safety_result = asyncio.gather(
            verify_standard_alignment(question_draft['question_text'],
                                       job['standard_code'],
                                       get_standard_description(job['standard_code'])),
            check_content_safety_llm(question_draft['question_text'])
        )
        
        # Compile all validation results
        all_passed = (exec_result['passed'] and quality_result['passed'] and
                      safety_result['passed'])
        requires_human_review = (alignment_result['confidence'] < 0.85)
        
        # Step 5: Store
        store_generated_question(
            job_id=job_id,
            question_data=question_draft,
            validation_results={
                'execution': exec_result,
                'quality': quality_result,
                'alignment': alignment_result,
                'safety': safety_result
            },
            all_passed=all_passed,
            requires_human_review=requires_human_review
        )
        
        # Update job status
        db.update_generation_job(job_id, status='completed', llm_cost_usd=calculate_cost())
    
    except Exception as exc:
        db.update_generation_job(job_id, status='failed', error_message=str(exc))
        raise self.retry(exc=exc)
```

---

### FR-9: Learning Plan Dashboard (Student View)

**FR-9.1 — Visual Learning Roadmap**

The student dashboard's primary visual element is a "Path" metaphor: a winding illustrated path (SVG, not a photograph) from bottom-left to top-right of the screen, with module nodes placed along the path.

- Each module appears as a circular node on the path with an icon representing the skill domain (times table grid for multiplication, fraction circle for fractions, ruler for measurement, etc.).
- Node states are visually distinct:
  - **Locked**: Gray circle, lock icon, dimmed label.
  - **Available**: Colored circle (domain color), pulsing glow animation, "Start" label.
  - **In Progress**: Colored circle with a progress ring showing % complete, "Continue" label.
  - **Mastered**: Green circle with star icon, check mark, bright and solid.
- The path line connecting nodes fills with color as modules are mastered (visual progress from bottom to top).
- Maximum 8 modules visible at one time (the path "scrolls" as progress is made). A summary counter at the top shows "X of Y modules completed."
- Tapping a locked module shows a tooltip: "Complete [previous module name] to unlock this!"
- Tapping an available or in-progress module opens the module detail view with a "Start Practice" / "Continue Practice" CTA.

**FR-9.2 — Module Status Indicators**

Module status renders consistently across all surfaces (roadmap path, module list, parent view):

| Status | Color | Icon | Label |
|--------|-------|------|-------|
| Locked | Gray (`#9E9E9E`) | Lock | "Locked" |
| Available | Blue (`#3B7DD8`) | Play arrow | "Start" |
| In Progress | Teal (`#26A69A`) | Progress ring | "Continue" |
| Mastered | Green (`#4CAF50`) | Star / checkmark | "Mastered!" |

**FR-9.3 — Current Module Focus**

When the student has an in-progress module, the dashboard prominently features it at the top of the screen (above the roadmap):

```
┌─────────────────────────────────────────────────────┐
│ 🧮 Keep Going, Jayden!                              │
│ Multiplication & Division Facts                      │
│ Progress: ████████░░░░ 40% (2 of 5 sessions)        │
│                   [Continue Practice →]              │
└─────────────────────────────────────────────────────┘
```

The "Continue Practice" CTA starts a new practice session for the current lesson. If a session was paused mid-way, a "Resume" button shows instead.

**FR-9.4 — Progress Percentage**

Two progress metrics are displayed:
1. **Overall plan progress**: "X of Y modules mastered" and a large percentage (e.g., "17%") displayed in a donut chart or circular progress indicator.
2. **Current module progress**: Within the module card, a linear progress bar showing "N of M sessions completed" and the current P(mastered) expressed as a level label (not a raw float — label says "Getting There" for 0.3–0.5, "Almost There" for 0.5–0.7, "Nearly Mastered!" for 0.7–0.85, "Mastered!" for ≥ 0.85).

**FR-9.5 — Streak Tracking**

A daily practice streak is tracked per student:

```python
def update_streak(student_id: str, session_completed_at: datetime, db) -> dict:
    """
    Update streak after a practice session. Returns updated streak record.
    A 'streak day' is any calendar day (Pacific Time) in which at least one
    practice session was completed.
    """
    streak = db.get_or_create_student_streak(student_id)
    
    today = session_completed_at.astimezone(pytz.timezone('America/Los_Angeles')).date()
    last_practice_date = streak['last_practice_date']
    
    if last_practice_date is None:
        # First ever practice
        new_streak = 1
    elif last_practice_date == today:
        # Already practiced today; no change to streak count
        new_streak = streak['current_streak']
    elif last_practice_date == today - timedelta(days=1):
        # Practiced yesterday; extend streak
        new_streak = streak['current_streak'] + 1
    else:
        # Streak broken; reset
        new_streak = 1
    
    longest = max(streak['longest_streak'], new_streak)
    
    db.update_streak(student_id, {
        'current_streak': new_streak,
        'longest_streak': longest,
        'last_practice_date': today,
        'total_practice_days': streak['total_practice_days'] + (0 if last_practice_date == today else 1)
    })
    
    return db.get_student_streak(student_id)
```

The streak is displayed as a flame icon + number: "🔥 5-day streak!" Students within 1 hour of midnight without a practice session see a gentle reminder: "Practice today to keep your streak!"

**FR-9.6 — Estimated Completion Date**

Calculated from the plan's `estimated_weeks` value and the student's actual practice frequency (trailing 7-day average of sessions/day):

```python
def estimate_completion_date(plan: dict, student_id: str, db) -> date:
    """Calculate estimated completion date based on recent practice pace."""
    recent_sessions = db.count_sessions_last_7_days(student_id)
    avg_sessions_per_day = recent_sessions / 7
    
    if avg_sessions_per_day < 0.1:
        # Student hasn't practiced recently; use assumption of 1 session/day
        avg_sessions_per_day = 1.0
    
    remaining_sessions = sum(
        m['estimated_sessions'] - m['sessions_completed']
        for m in plan['modules']
        if m['status'] not in ('mastered',)
    )
    
    days_remaining = math.ceil(remaining_sessions / avg_sessions_per_day)
    return date.today() + timedelta(days=days_remaining)
```

Displayed as: "At your current pace, you'll finish by [Month Day, Year]" or "Keep up the great work — you're on track!"

**FR-9.7 — Achievement Badges**

Badges are awarded automatically when qualifying events occur. Badge awards are asynchronous (event-driven) with < 2-second latency from qualifying event to badge display.

Initial badge set at Stage 2 launch:

| Badge ID | Name | Trigger Condition | Icon |
|----------|------|------------------|------|
| `first_session` | Math Explorer | Complete first practice session | Compass |
| `first_mastery` | Skill Master | Master first module | Star |
| `streak_3` | On a Roll! | 3-day practice streak | Flame |
| `streak_7` | Week Warrior | 7-day practice streak | Trophy |
| `streak_14` | Math Champion | 14-day streak | Lightning bolt |
| `halfway` | Halfway Hero | 50% of plan modules mastered | Half-filled donut |
| `plan_complete` | Grade Ready! | 100% of plan modules mastered | Mountain peak |
| `comeback` | Back in the Game | Practice after 3+ day absence | Sunrise |
| `perfect_session` | Perfect Practice | Complete a session with 100% accuracy | Diamond |
| `fast_learner` | Fast Learner | Master a module in 2 or fewer sessions | Rocket |
| `oregon_explorer` | Oregon Explorer | Complete 5 word problems with Oregon context | State outline |

Badge award events are published to Redis Streams (`padi:events`) and consumed by a badge worker that checks conditions and inserts into `student_badges` table. The student dashboard polls for new badges on load and shows a celebration animation (confetti + modal) for any badge earned since last login.

**FR-9.8 — Mobile-Responsive Layout**

- Primary layout target: iPad portrait (1024×1366 safe area).
- Secondary: iPhone (390×844 safe area): roadmap path becomes a vertical scrollable list of module cards (no SVG path on small screens).
- Breakpoints: `< 768px` = mobile layout; `≥ 768px` = tablet/desktop layout.
- Touch targets: minimum 48×48px for all interactive elements (WCAG 2.5.5).
- Roadmap SVG scales proportionally on tablet; degrades gracefully to card list on phone.
- Pinch-to-zoom is disabled on the assessment screens to prevent accidental zoom disrupting the keypad UI.

---

### FR-10: Learning Plan Dashboard (Parent View)

**FR-10.1 — Child's Current Plan Overview**

The parent dashboard opens to a summary card for each child with an active plan:

```
┌──────────────────────────────────────────────────────────┐
│ Jayden  •  Grade 4  •  Catch Up Track                    │
│ Started: Sept 5, 2024  •  Est. completion: Nov 14, 2024  │
│                                                          │
│ Overall Progress: [████████░░░░░░░░░░░░] 17%             │
│ 2 of 12 modules mastered                                 │
│                                                          │
│ Current Focus: Multiplication & Division Facts           │
│ [View Full Plan →]                                       │
└──────────────────────────────────────────────────────────┘
```

Multiple children are shown as tabs or swipeable cards. Clicking "View Full Plan" opens the detailed plan view (FR-10.2).

**FR-10.2 — Module-by-Module Progress**

The full plan view shows a vertical list of all modules with:
- Module name, standard code, domain icon.
- Status badge (Locked / Available / In Progress / Mastered) with mastery date for completed modules.
- For mastered modules: a green checkmark and "Mastered on [date]."
- For in-progress modules: a progress bar (P(mastered) as a percentage, labeled "Mastery Progress").
- For locked modules: "Unlocks after [prerequisite module name]."
- Estimated sessions remaining (for in-progress and available modules).

The module list is grouped by track section header:
- "Prerequisite Skills" (Grade 3 remediation modules)
- "Grade 4 Content" (Oregon Grade 4 standards)

**FR-10.3 — Time Spent Per Week**

A bar chart (7 bars, one per day of the week, trailing 7 days) shows daily minutes of practice. Data is computed from `plan_lessons.completed_at` and `plan_lessons.started_at` (time difference per session).

```
Time Spent This Week:
Mon  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  20 min
Tue  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  20 min
Wed  ░                       0 min (no practice)
Thu  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  20 min
Fri  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  20 min
Sat  ░                       0 min
Sun  ░                       0 min

Total this week: 80 min  •  Goal: 100 min/week
```

The "Goal" is configurable in parent settings (default: 100 min/week = 20 min × 5 days).

**FR-10.4 — Questions Answered & Accuracy Rate**

Lifetime stats card:

| Metric | Value |
|--------|-------|
| Total questions answered | 187 |
| Correct | 142 (75.9%) |
| Sessions completed | 12 |
| Modules mastered | 2 |
| Current streak | 4 days |
| Longest streak | 7 days |

Displayed as a 2×3 grid of stat cards (large number, small label). Accuracy rate shown as a percentage with a color indicator (green ≥ 70%, yellow 50–69%, orange < 50%).

**FR-10.5 — Skills Mastered vs. In Progress**

A visual summary showing:
- Mastered skills: list of module names with green checkmarks and mastery dates.
- In Progress: module name + progress bar (P(mastered) percentage + "Getting There / Almost There" label).
- Not Started / Locked: count only ("8 more modules to go!").

**FR-10.6 — Next Recommended Session**

The parent dashboard prominently features the recommended next action:

```
┌─────────────────────────────────────────────────────┐
│ Next Recommended Session                            │
│ Multiplication & Division Facts — Practice          │
│ Estimated time: 20 minutes                          │
│ Best time: After school (based on Jayden's history) │
│                  [Send Reminder to Jayden →]        │
└─────────────────────────────────────────────────────┘
```

"Best time" is computed from the hour distribution of the student's past practice sessions (mode hour of day). "Send Reminder to Jayden" is a placeholder for Stage 3's notification feature (disabled button in Stage 2 with "Coming Soon" tooltip).

**FR-10.7 — Weekly Summary Email**

An optional weekly email (opt-in, default: enabled) is sent to the parent every Sunday at 6 PM Pacific with:
- Subject: "Jayden's PADI.AI Week in Review — [Date Range]"
- Content: time spent, sessions completed, skills mastered this week, current streak, encouragement, CTA to view full plan.
- Template: HTML email, responsive, tested on Gmail, Apple Mail, Outlook.
- Unsubscribe link in every email (CANSPAM compliance).
- Email generated by a Celery scheduled task (cron: `0 18 * * 0` Pacific time), templated with Jinja2.

**FR-10.8 — Notification Preferences**

Parents can configure in Account Settings:
- Weekly summary email: on/off
- Module mastered notification (immediate email): on/off
- Streak milestone notifications: on/off
- Time of day preference for reminders (informational only; actual reminder system is Stage 3)

Preferences stored in `users.notification_preferences` JSONB column.

---

## 2.3 Non-Functional Requirements

### LLM Generation Performance
- o3-mini question generation API call: < 8 seconds P95 (per call, single question).
- Full pipeline per question (all 5 steps): < 25 seconds P95.
- Pipeline throughput with 4 workers: ≥ 100 validated questions/hour.
- Alignment verification LLM call (Claude Haiku): < 3 seconds P95.
- Content safety LLM call (Claude Haiku): < 3 seconds P95 (runs in parallel with alignment).

### Question Validation Throughput
- Automated validation pipeline SHALL process ≥ 100 questions/hour without human intervention for the ≥ 85% that pass all automated checks.
- Human review queue SHALL be reviewable at a rate of ≥ 30 questions/hour by a math educator (each question review: < 2 minutes).

### Learning Plan Generation
- From `diagnostic_completed` event to fully written `learning_plan` + `plan_modules` records: < 5 seconds (measured P95 on production hardware).
- Plan generation is synchronous from the API perspective (the parent results screen polls for plan readiness). It is processed asynchronously in the backend (Celery task) but completes fast enough that the polling client receives a ready response within 1–2 poll cycles (3-second poll interval).

### Generated Content Storage
- Target: 5,000+ validated questions in the `questions` table by end of Stage 2 (Month 6).
- At 100 questions/hour throughput × 8 hours/day of generation × ~63 days (Months 4–6) = 50,400 questions possible; actual target is 5,000 (conservative, accounting for generation quality filters).
- pgvector index on question embeddings: IVFFlat index with `lists = 100` for efficient similarity search as the question pool grows.

### LLM Cost Management
- Per-question LLM cost: ≤ $0.05 (fully loaded: generation + validation LLM calls).
- At 5,000 questions: total LLM spend ≤ $250.
- Daily spend alert threshold: $5.
- Daily spend hard stop: $10.
- Monthly LLM budget tracked and reported in admin dashboard.

### Dashboard Performance
- Student dashboard initial load (plan + module list): < 2 seconds P95.
- Parent dashboard initial load: < 2 seconds P95.
- Streak/badge queries: cached in Redis with 60-second TTL. Cache invalidated on session completion.
- Module re-sequencing after a session: < 1 second (in-memory graph traversal, O(V+E)).

---

## 2.4 Data Models

New tables added in Stage 2 (all Stage 1 tables remain unchanged):

```sql
-- ============================================================
-- LEARNING PLANS
-- ============================================================
CREATE TABLE learning_plans (
    plan_id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id          UUID NOT NULL REFERENCES students(student_id) ON DELETE CASCADE,
    track               VARCHAR(20) NOT NULL CHECK (track IN ('catch_up', 'on_track', 'accelerate')),
    status              VARCHAR(20) NOT NULL DEFAULT 'active'
                            CHECK (status IN ('active', 'completed', 'archived')),
    estimated_weeks     DECIMAL(4,1),
    total_modules       SMALLINT NOT NULL DEFAULT 0,
    modules_mastered    SMALLINT NOT NULL DEFAULT 0,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at        TIMESTAMPTZ
);

-- Enforce one active plan per student
CREATE UNIQUE INDEX idx_lp_student_active 
    ON learning_plans(student_id) 
    WHERE status = 'active';

CREATE INDEX idx_lp_student ON learning_plans(student_id);
CREATE INDEX idx_lp_status ON learning_plans(status);


-- ============================================================
-- PLAN MODULES
-- ============================================================
CREATE TABLE plan_modules (
    module_id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_id                 UUID NOT NULL REFERENCES learning_plans(plan_id) ON DELETE CASCADE,
    standard_code           VARCHAR(20) NOT NULL REFERENCES standards(code),
    module_name             VARCHAR(200) NOT NULL,
    sequence_order          SMALLINT NOT NULL,
    status                  VARCHAR(20) NOT NULL DEFAULT 'locked'
                                CHECK (status IN ('locked', 'available', 'in_progress', 'mastered')),
    p_mastered_initial      DECIMAL(6,5) NOT NULL,
    p_mastered_current      DECIMAL(6,5) NOT NULL,
    estimated_sessions      SMALLINT NOT NULL DEFAULT 4,
    sessions_completed      SMALLINT NOT NULL DEFAULT 0,
    bkt_history             JSONB NOT NULL DEFAULT '[]',  -- array of {session_id, p_before, p_after, timestamp}
    available_at            TIMESTAMPTZ,
    started_at              TIMESTAMPTZ,
    mastered_at             TIMESTAMPTZ,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(plan_id, sequence_order),
    UNIQUE(plan_id, standard_code)
);

CREATE INDEX idx_pm_plan ON plan_modules(plan_id);
CREATE INDEX idx_pm_status ON plan_modules(status);
CREATE INDEX idx_pm_standard ON plan_modules(standard_code);


-- ============================================================
-- PLAN LESSONS
-- ============================================================
CREATE TABLE plan_lessons (
    lesson_id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    module_id                   UUID NOT NULL REFERENCES plan_modules(module_id) ON DELETE CASCADE,
    lesson_number               SMALLINT NOT NULL CHECK (lesson_number BETWEEN 1 AND 3),
    lesson_title                VARCHAR(200) NOT NULL,
    lesson_type                 VARCHAR(20) NOT NULL CHECK (lesson_type IN ('intro', 'practice', 'challenge')),
    difficulty_range_min        SMALLINT NOT NULL DEFAULT 1,
    difficulty_range_max        SMALLINT NOT NULL DEFAULT 3,
    question_count_target       SMALLINT NOT NULL DEFAULT 12,
    mastery_threshold_to_advance DECIMAL(4,3) NOT NULL DEFAULT 0.70,
    status                      VARCHAR(20) NOT NULL DEFAULT 'locked'
                                    CHECK (status IN ('locked', 'available', 'in_progress', 'completed')),
    p_mastered_at_completion    DECIMAL(6,5),
    started_at                  TIMESTAMPTZ,
    completed_at                TIMESTAMPTZ,
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(module_id, lesson_number)
);

CREATE INDEX idx_pl_module ON plan_lessons(module_id);
CREATE INDEX idx_pl_status ON plan_lessons(status);


-- ============================================================
-- GENERATED QUESTIONS (Draft staging table before promotion)
-- ============================================================
CREATE TABLE generated_questions (
    gen_question_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id                  UUID NOT NULL REFERENCES generation_jobs(job_id),
    standard_code           VARCHAR(20) NOT NULL REFERENCES standards(code),
    question_type           VARCHAR(30) NOT NULL,
    question_text           TEXT NOT NULL,
    answer_options          JSONB,
    correct_answer          TEXT NOT NULL,
    correct_answer_alt      TEXT[] DEFAULT '{}',
    solution_steps          JSONB NOT NULL DEFAULT '[]',
    solution_python_code    TEXT,
    difficulty_level        SMALLINT NOT NULL,
    dok_level               SMALLINT NOT NULL,
    context_type            VARCHAR(30) NOT NULL,
    context_theme           VARCHAR(50),
    tags                    TEXT[] DEFAULT '{}',
    embedding               vector(384),             -- sentence embedding for deduplication
    validation_status       VARCHAR(20) NOT NULL DEFAULT 'pending'
                                CHECK (validation_status IN ('pending', 'passed', 'failed', 'human_review')),
    validation_results      JSONB NOT NULL DEFAULT '{}',
    requires_human_review   BOOLEAN NOT NULL DEFAULT FALSE,
    human_review_notes      TEXT,
    human_approved          BOOLEAN,
    human_reviewed_by       VARCHAR(100),
    human_reviewed_at       TIMESTAMPTZ,
    promoted_at             TIMESTAMPTZ,  -- set when copied to questions table
    promoted_question_id    UUID,         -- FK to questions.question_id after promotion
    llm_model               VARCHAR(50) NOT NULL DEFAULT 'o3-mini',
    llm_prompt_version      VARCHAR(20) NOT NULL DEFAULT 'v1.0',
    generation_cost_usd     DECIMAL(10,6),
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_gq_job ON generated_questions(job_id);
CREATE INDEX idx_gq_standard ON generated_questions(standard_code);
CREATE INDEX idx_gq_validation ON generated_questions(validation_status);
CREATE INDEX idx_gq_pending_review ON generated_questions(requires_human_review) 
    WHERE requires_human_review = TRUE AND human_approved IS NULL;
CREATE INDEX idx_gq_embedding ON generated_questions USING ivfflat(embedding vector_cosine_ops) WITH (lists = 100);


-- ============================================================
-- QUESTION VALIDATION RESULTS
-- ============================================================
CREATE TABLE question_validation_results (
    result_id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    gen_question_id     UUID NOT NULL REFERENCES generated_questions(gen_question_id) ON DELETE CASCADE,
    step_name           VARCHAR(50) NOT NULL,  -- 'execution', 'quality_classification', 'alignment', 'safety'
    step_number         SMALLINT NOT NULL,
    passed              BOOLEAN NOT NULL,
    score               DECIMAL(6,4),
    details             JSONB NOT NULL DEFAULT '{}',
    error_message       TEXT,
    duration_ms         INTEGER,
    ran_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_qvr_gen_question ON question_validation_results(gen_question_id);
CREATE INDEX idx_qvr_step ON question_validation_results(step_name, passed);


-- ============================================================
-- GENERATION JOBS
-- ============================================================
CREATE TABLE generation_jobs (
    job_id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    batch_id            VARCHAR(50),              -- groups related jobs (e.g., 'batch_20240905_001')
    standard_code       VARCHAR(20) NOT NULL REFERENCES standards(code),
    difficulty_level    SMALLINT NOT NULL,
    question_type       VARCHAR(30) NOT NULL,
    context_type        VARCHAR(30) NOT NULL,
    context_theme       VARCHAR(50),
    target_dok_level    SMALLINT NOT NULL,
    llm_model           VARCHAR(50) NOT NULL DEFAULT 'o3-mini',
    prompt_version      VARCHAR(20) NOT NULL DEFAULT 'v1.0',
    status              VARCHAR(20) NOT NULL DEFAULT 'queued'
                            CHECK (status IN ('queued', 'processing', 'completed', 'failed', 'skipped')),
    attempts            SMALLINT NOT NULL DEFAULT 0,
    max_attempts        SMALLINT NOT NULL DEFAULT 2,
    llm_cost_usd        DECIMAL(10,6),
    total_tokens        INTEGER,
    error_message       TEXT,
    celery_task_id      VARCHAR(100),
    queued_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at          TIMESTAMPTZ,
    completed_at        TIMESTAMPTZ
);

CREATE INDEX idx_gj_status ON generation_jobs(status);
CREATE INDEX idx_gj_standard ON generation_jobs(standard_code);
CREATE INDEX idx_gj_batch ON generation_jobs(batch_id);
CREATE INDEX idx_gj_queued ON generation_jobs(queued_at) WHERE status = 'queued';


-- ============================================================
-- STUDENT BADGES
-- ============================================================
CREATE TABLE student_badges (
    award_id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id          UUID NOT NULL REFERENCES students(student_id) ON DELETE CASCADE,
    badge_id            VARCHAR(50) NOT NULL,
    badge_name          VARCHAR(100) NOT NULL,
    badge_description   TEXT,
    badge_icon          VARCHAR(50),
    awarded_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    triggering_event    VARCHAR(100),   -- e.g., 'session_completed', 'module_mastered'
    shown_to_student    BOOLEAN NOT NULL DEFAULT FALSE,
    shown_to_student_at TIMESTAMPTZ,
    UNIQUE(student_id, badge_id)  -- each badge awarded once per student
);

CREATE INDEX idx_sb_student ON student_badges(student_id);
CREATE INDEX idx_sb_unshown ON student_badges(student_id, shown_to_student) 
    WHERE shown_to_student = FALSE;


-- ============================================================
-- STUDENT STREAKS
-- ============================================================
CREATE TABLE student_streaks (
    streak_id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id          UUID NOT NULL UNIQUE REFERENCES students(student_id) ON DELETE CASCADE,
    current_streak      INTEGER NOT NULL DEFAULT 0,
    longest_streak      INTEGER NOT NULL DEFAULT 0,
    last_practice_date  DATE,
    total_practice_days INTEGER NOT NULL DEFAULT 0,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_ss_student ON student_streaks(student_id);


-- ============================================================
-- NOTIFICATION PREFERENCES (extends users table)
-- ============================================================
-- Add to users table via migration:
ALTER TABLE users ADD COLUMN IF NOT EXISTS 
    notification_preferences JSONB NOT NULL DEFAULT '{
        "weekly_summary_email": true,
        "module_mastered_email": true,
        "streak_milestone_email": true,
        "practice_goal_minutes_per_week": 100
    }';
```

---

## 2.5 API Endpoints

All new Stage 2 endpoints. Base URL: `https://api.padi.ai/api/v1`

---

### Learning Plan Endpoints

#### GET /students/:student_id/learning-plan
Get the active learning plan for a student.

**Auth required**: Yes (parent of student, or internal service token)

**Response 200** — Full plan JSON (see FR-7.9 schema):
```json
{
  "plan_id": "uuid",
  "student_id": "uuid",
  "track": "catch_up",
  "status": "active",
  "estimated_weeks": 8.5,
  "progress": {
    "modules_total": 12,
    "modules_mastered": 2,
    "modules_in_progress": 1,
    "percent_complete": 16.7
  },
  "current_module": { /* ... */ },
  "modules": [ /* ... */ ]
}
```

**Response 404**: `{"error": "NO_ACTIVE_PLAN", "message": "No active learning plan found. Complete the diagnostic first."}`

---

#### GET /students/:student_id/learning-plan/status
Lightweight plan status check (for polling after diagnostic).

**Auth required**: Yes (parent)

**Response 200**:
```json
{
  "plan_ready": true,
  "plan_id": "uuid",
  "track": "catch_up",
  "total_modules": 12,
  "estimated_weeks": 8.5
}
```

**Response 200** (not yet ready):
```json
{"plan_ready": false, "message": "Plan is being generated..."}
```

---

#### GET /students/:student_id/learning-plan/modules
List all modules in a student's plan.

**Auth required**: Yes (parent or student session)

**Query params**: `status` (filter by status), `include_locked` (default: true)

**Response 200**:
```json
{
  "modules": [
    {
      "module_id": "uuid",
      "standard_code": "3.OA.C.7",
      "module_name": "Multiplication & Division Facts",
      "status": "in_progress",
      "sequence_order": 1,
      "p_mastered_current": 0.42,
      "estimated_sessions": 4,
      "sessions_completed": 2,
      "mastered_at": null
    }
  ]
}
```

---

#### GET /students/:student_id/learning-plan/modules/:module_id
Get details for a single module including lessons.

**Auth required**: Yes (parent or student)

**Response 200**: Full module object with `lessons` array.

---

#### POST /students/:student_id/learning-plan/modules/:module_id/lessons/:lesson_id/start
Start a practice session for a lesson.

**Auth required**: Yes (student session scoped to this student)

**Business rules**: Lesson must be in `available` status. Creates a `plan_lessons` record with `status = 'in_progress'` and selects questions for the session.

**Response 201**:
```json
{
  "session_id": "uuid",
  "lesson_id": "uuid",
  "module_name": "Multiplication & Division Facts",
  "lesson_title": "Practice: Multiplication Facts",
  "questions": [
    {
      "question_id": "uuid",
      "sequence": 1,
      "question_text": "What is \\(8 \\times 7\\)?",
      "question_type": "multiple_choice",
      "answer_options": [/* ... */]
    }
  ],
  "question_count": 12,
  "estimated_minutes": 20
}
```

---

#### POST /sessions/:session_id/answer
Submit an answer in a practice session (identical interface to diagnostic answer endpoint).

**Auth required**: Yes (student session)

**Request body**: `{"question_id": "uuid", "sequence": 1, "answer": "B", "time_taken_seconds": 15}`

**Response 200**:
```json
{
  "accepted": true,
  "is_correct": true,          // REVEALED immediately in practice (unlike diagnostic)
  "correct_answer": "B",       // Revealed post-answer in practice
  "solution_steps": [          // Available if is_correct == false
    {"step": 1, "text": "Recall that 8 × 7 = 56"}
  ],
  "session_status": "in_progress",
  "questions_remaining": 10
}
```

*Note: Unlike the diagnostic, practice sessions reveal correct/incorrect immediately after each answer to support learning.*

---

#### POST /sessions/:session_id/complete
Complete a practice session, trigger BKT update and re-sequencing.

**Auth required**: Yes (student session)

**Response 200**:
```json
{
  "session_id": "uuid",
  "questions_answered": 12,
  "correct_count": 9,
  "accuracy": 0.75,
  "bkt_before": {"p_mastered": 0.42},
  "bkt_after": {"p_mastered": 0.58},
  "module_status": "in_progress",
  "new_badges": [
    {
      "badge_id": "streak_3",
      "badge_name": "On a Roll!",
      "badge_description": "3 days in a row — keep it up!"
    }
  ],
  "current_streak": 3,
  "next_lesson": {
    "lesson_id": "uuid",
    "lesson_title": "Challenge: Multiplication Facts",
    "available": true
  }
}
```

---

### Skill Dependency Graph Endpoints

#### GET /graph/skill-sequence/:student_id
Get the recommended skill sequence for a student.

**Auth required**: Yes (internal, admin, or parent)

**Response 200**:
```json
{
  "student_id": "uuid",
  "track": "catch_up",
  "sequence": [
    {
      "standard_code": "3.OA.C.7",
      "module_name": "Multiplication & Division Facts",
      "priority_score": 35.2,
      "p_mastered": 0.10,
      "estimated_sessions": 8,
      "prerequisite_for": ["4.OA.A.1", "4.NBT.B.5", "4.NBT.B.6"]
    }
  ]
}
```

---

#### GET /graph/prerequisites/:standard_code
Get prerequisite chain for a standard code (deep traversal).

**Auth required**: Yes

**Response 200**:
```json
{
  "standard_code": "4.NBT.B.5",
  "prerequisite_chain": [
    {"code": "3.OA.C.7", "depth": 1, "strength": "required"},
    {"code": "3.NBT.A.3", "depth": 1, "strength": "required"}
  ],
  "all_ancestors": ["3.OA.C.7", "3.NBT.A.3"]
}
```

---

### AI Generation Endpoints (Admin Only)

#### POST /admin/generation/schedule-batch
Schedule a batch of question generation jobs.

**Auth required**: Yes (admin)

**Request body**:
```json
{
  "standard_codes": ["3.OA.C.7", "4.NBT.B.5"],
  "questions_per_standard": 50,
  "difficulty_distribution": {
    "1": 0.10, "2": 0.25, "3": 0.35, "4": 0.20, "5": 0.10
  },
  "question_type_distribution": {
    "multiple_choice": 0.60, "short_numeric": 0.25, "fraction_input": 0.15
  },
  "batch_label": "batch_sept_2024_prereqs"
}
```

**Response 201**:
```json
{
  "batch_id": "batch_sept_2024_prereqs",
  "jobs_created": 100,
  "estimated_completion_hours": 1.0,
  "estimated_cost_usd": 0.22
}
```

---

#### GET /admin/generation/batches
List all generation batches with status summary.

**Auth required**: Yes (admin)

**Response 200**: Paginated list of batches with job counts by status.

---

#### GET /admin/generation/batches/:batch_id/jobs
List all jobs in a batch.

**Auth required**: Yes (admin)

**Response 200**: Paginated job list.

---

#### GET /admin/generation/review-queue
Get questions pending human review.

**Auth required**: Yes (admin)

**Query params**: `standard_code`, `page`, `per_page`

**Response 200**:
```json
{
  "total_pending": 47,
  "questions": [
    {
      "gen_question_id": "uuid",
      "standard_code": "3.OA.C.7",
      "question_text": "...",
      "validation_results": { /* step results */ },
      "alignment_confidence": 0.78,
      "safety_severity": "none"
    }
  ]
}
```

---

#### POST /admin/generation/review-queue/:gen_question_id/approve
Approve a question from the human review queue.

**Auth required**: Yes (admin)

**Request body**: `{"reviewer_name": "Dr. Kim", "notes": "Mathematically accurate."}`

**Response 200**: Question promoted to `questions` table. Returns promoted `question_id`.

---

#### POST /admin/generation/review-queue/:gen_question_id/reject
Reject a question from the review queue.

**Auth required**: Yes (admin)

**Request body**: `{"reason": "Incorrect distractor — option C is equivalent to the correct answer."}`

**Response 200**: `{"gen_question_id": "uuid", "validation_status": "failed"}`

---

### Gamification Endpoints

#### GET /students/:student_id/badges
Get all badges earned by a student.

**Auth required**: Yes (parent or student)

**Response 200**:
```json
{
  "badges": [
    {
      "badge_id": "first_session",
      "badge_name": "Math Explorer",
      "badge_description": "You completed your first practice session!",
      "awarded_at": "2024-09-06T15:30:00Z",
      "badge_icon": "compass"
    }
  ],
  "total": 3,
  "new_badges_since_last_login": ["streak_3"]
}
```

---

#### POST /students/:student_id/badges/mark-shown
Mark all new badges as shown to the student.

**Auth required**: Yes (student session)

**Response 200**: `{"badges_marked": 2}`

---

#### GET /students/:student_id/streak
Get current streak information.

**Auth required**: Yes (parent or student)

**Response 200**:
```json
{
  "current_streak": 4,
  "longest_streak": 7,
  "last_practice_date": "2024-09-09",
  "total_practice_days": 12,
  "streak_at_risk": false  // true if last practice was yesterday and no practice today
}
```

---

### Parent Dashboard Endpoints

#### GET /parents/:user_id/dashboard
Get consolidated parent dashboard data (all children + summaries).

**Auth required**: Yes (parent)

**Response 200**:
```json
{
  "children": [
    {
      "student_id": "uuid",
      "display_name": "Jayden",
      "grade": 4,
      "avatar_id": 5,
      "plan_track": "catch_up",
      "plan_status": "active",
      "percent_complete": 17,
      "current_streak": 4,
      "modules_mastered": 2,
      "modules_total": 12,
      "last_session_at": "2024-09-09T16:30:00Z",
      "new_badges": []
    }
  ]
}
```

---

#### GET /students/:student_id/parent-report
Get detailed parent report data.

**Auth required**: Yes (parent of student)

**Response 200**:
```json
{
  "student": { /* student profile */ },
  "plan": { /* full plan object */ },
  "weekly_activity": {
    "sessions": 4,
    "minutes": 80,
    "questions_answered": 48,
    "accuracy": 0.77,
    "days": [
      {"date": "2024-09-04", "minutes": 20},
      {"date": "2024-09-05", "minutes": 20},
      {"date": "2024-09-07", "minutes": 20},
      {"date": "2024-09-08", "minutes": 20}
    ]
  },
  "lifetime_stats": {
    "total_questions": 187,
    "correct": 142,
    "accuracy": 0.759,
    "sessions_completed": 12,
    "modules_mastered": 2,
    "current_streak": 4,
    "longest_streak": 7
  },
  "next_recommended_session": {
    "module_name": "Multiplication & Division Facts",
    "lesson_title": "Practice: Multiplication Facts",
    "estimated_minutes": 20,
    "recommended_time_of_day": "15:00"
  }
}
```

---

#### PATCH /parents/:user_id/notification-preferences
Update notification preferences.

**Auth required**: Yes (parent, self only)

**Request body**: Any subset of notification preferences object.

**Response 200**: Updated preferences.

---

## 2.6 AI Prompt Templates

Full production prompt templates for all LLM calls in the Stage 2 pipeline.

---

### PT-1: Question Generation Prompt (o3-mini)

```
SYSTEM:
You are an expert elementary mathematics question writer for PADI.AI, an adaptive 
math learning app for Oregon 4th graders (typically age 9). Your questions are used in an 
adaptive learning system and must meet strict quality standards.

Writing requirements:
- Mathematical accuracy: every number, operation, and answer must be 100% correct
- Reading level: Flesch-Kincaid Grade 3–5 (short sentences, common words, clear structure)
- Names in word problems: use diverse names — Maya, Jordan, Alex, Sam, Mia, Kai, Rivera, 
  Amara, Ethan, Sofia (rotate; never use the same name twice in one question)
- Oregon context: when context_type is word_problem, set the problem in Oregon when natural 
  (Columbia River, Mount Hood, Crater Lake, Willamette Valley, Portland, Bend, Eugene, 
  Tillamook, Oregon coast, Oregon Trail, farmers markets, salmon fishing, timber industry)
- No bias: avoid gender assumptions, socioeconomic assumptions, or cultural stereotypes
- One correct answer: the question must have exactly one unambiguous correct answer
- No trick questions: the correct answer should be obtainable by a student who understands 
  the standard, without needing obscure knowledge or tricks

Output format: Respond with ONLY a JSON object. Do not include any text before or after the JSON.

USER:
Generate one math question with these exact specifications:

Standard Code: {{standard_code}}
Standard Description: {{standard_description}}
Difficulty Level: {{difficulty_level}} out of 5
  (1=pure recall, 2=skill application, 3=moderate complexity, 4=complex application, 5=challenge)
Target DOK Level: {{dok_level}}
  (1=recall, 2=skill/concept, 3=strategic thinking)
Question Type: {{question_type}}
  (multiple_choice: 4 options A/B/C/D | short_numeric: student enters a number | 
   fraction_input: student enters numerator and denominator)
Context Type: {{context_type}}
  (word_problem: real-world story | computation: pure symbolic | visual: requires diagram description)
Context Theme: {{context_theme}}
  (the real-world setting for word problems; use "computation" for pure symbolic questions)

{{#if question_type == "multiple_choice"}}
For the 4 answer choices:
- Exactly ONE must be correct
- The other THREE are distractors. Each distractor MUST reflect a specific, documented 
  common student misconception for this standard. Name the misconception for each distractor.
- Distractors should be plausible (not obviously wrong). At least one distractor should 
  be within 20% of the correct numeric value.
{{/if}}

Include a Python code solution that computes the correct answer programmatically.
The last line of the Python code must be: print(answer)
Use only Python standard library (math, fractions). No external imports.

Respond with this exact JSON structure:
{
  "question_text": "string — the full question text. Use \\( ... \\) for inline LaTeX math.",
  "question_type": "{{question_type}}",
  "answer_options": [
    {"id": "A", "text": "string", "is_correct": false, "misconception": "string describing error"},
    {"id": "B", "text": "string", "is_correct": true,  "misconception": null},
    {"id": "C", "text": "string", "is_correct": false, "misconception": "string describing error"},
    {"id": "D", "text": "string", "is_correct": false, "misconception": "string describing error"}
  ],
  "correct_answer": "string — option id (A/B/C/D) for MC; numeric string for others",
  "correct_answer_alt": ["list of equivalent acceptable answers, e.g. ['0.5', '1/2']"],
  "numeric_tolerance": null,
  "solution_steps": [
    {"step": 1, "text": "Plain English explanation of this step"},
    {"step": 2, "text": "..."}
  ],
  "solution_python_code": "# Python code\nanswer = ...\nprint(answer)",
  "difficulty_level": {{difficulty_level}},
  "dok_level": {{dok_level}},
  "context_type": "{{context_type}}",
  "context_theme": "{{context_theme}}",
  "tags": ["relevant", "tags"],
  "reading_level_estimate": "Grade 3 | Grade 4 | Grade 5",
  "estimated_completion_minutes": 2
}
```

---

### PT-2: Distractor Generation Prompt (o3-mini — used when initial MC generation produces weak distractors)

```
SYSTEM:
You are an expert math educator specializing in student error analysis for Grade 3–4 mathematics.
You understand common misconceptions students have and can generate plausible wrong answers 
(distractors) that reflect real student errors.

USER:
A math question has been generated for this standard:
Standard Code: {{standard_code}}
Standard Description: {{standard_description}}

The question is:
{{question_text}}

The correct answer is: {{correct_answer}}

The current distractors are weak or invalid. Generate 3 new distractors that:
1. Each reflect a SPECIFIC, documented student misconception (name the misconception)
2. Are plausible — a student who made that specific error would genuinely arrive at this answer
3. Are numerically distinct from each other and from the correct answer
4. For numeric questions: at least one distractor should be within ±20% of the correct answer
5. For word problems: at least one distractor should reflect a wrong operation choice 
   (e.g., adding instead of multiplying)

Respond with ONLY this JSON:
{
  "distractors": [
    {
      "id": "A",
      "text": "string — the wrong answer",
      "misconception": "string — specific error type, e.g., 'Adds the numbers instead of multiplying'"
    },
    {
      "id": "C",
      "text": "string",
      "misconception": "string"
    },
    {
      "id": "D",
      "text": "string",
      "misconception": "string"
    }
  ]
}
```

---

### PT-3: Solution Validation Prompt (used when Python code execution fails — asks LLM to re-derive)

```
SYSTEM:
You are a precise mathematician and Python programmer. You will be given a math question 
and must compute the correct answer, then write Python code to verify it.

USER:
A math question was generated but the Python solution code failed to execute correctly.
Please re-derive the answer and rewrite the Python solution.

Standard: {{standard_code}} — {{standard_description}}
Question: {{question_text}}
Original Python code (which failed): 
{{failed_python_code}}
Failure reason: {{failure_reason}}

Steps:
1. Manually solve the problem step by step, showing your work
2. Verify your answer is mathematically correct
3. Write new clean Python code (standard library only: math, fractions) that computes 
   the same answer. Last line must be: print(answer)

Respond with ONLY this JSON:
{
  "manual_solution": "Step-by-step solution in plain English",
  "correct_answer": "string — the final answer",
  "python_code": "# Clean Python code\nfrom fractions import Fraction\nanswer = ...\nprint(answer)",
  "confidence": "high | medium | low"
}
```

---

### PT-4: Content Safety Check Prompt (Claude Haiku)

```
SYSTEM:
You are a content safety reviewer for an educational app used by children ages 8–10 
(4th graders). You review math word problems to ensure they are appropriate, inclusive, 
and free of bias.

Review criteria:
- AGE APPROPRIATENESS: No violence, death, weapons, adult substances (alcohol, drugs, gambling)
- INCLUSIVITY: No cultural stereotypes, no assumptions about family income, no gender stereotypes
- DIVERSITY: Names and contexts should feel welcoming to all Oregon families
- FAMILY SENSITIVITY: Avoid scenarios implying single-parent vs. two-parent distinctions; 
  say "family" not "mom and dad"
- OREGON CONTEXT: Oregon-specific references are welcome (geography, activities), 
  but should not stereotype rural vs. urban communities

USER:
Review this math word problem for use with 4th-grade students (ages 9):

"{{question_text}}"

Standard being tested: {{standard_code}} — {{standard_description}}

Respond with ONLY this JSON:
{
  "safe": true | false,
  "severity": "none | minor | major",
  "concerns": [
    "List each concern here. Empty array [] if no concerns."
  ],
  "suggested_revision": "Optional: a revised question text that addresses concerns, or null if no revision needed"
}

Severity definitions:
- "none": no concerns
- "minor": small wording issue, easy fix, question can still be used with revision
- "major": fundamentally inappropriate for children; question should be discarded
```

---

### PT-5: Standard Alignment Verification Prompt (Claude Haiku)

```
SYSTEM:
You are a math curriculum specialist with expertise in Oregon elementary math standards 
(aligned with Common Core). You evaluate whether math questions accurately test their 
target learning standards.

USER:
Evaluate whether this math question accurately tests the specified Oregon math standard.

Standard Code: {{standard_code}}
Standard Description: {{standard_description}}

Question:
"{{question_text}}"

Question Type: {{question_type}}
Difficulty Level: {{difficulty_level}}/5
Target DOK Level: {{dok_level}}

Evaluate:
1. Does this question require the mathematical skill described in the standard?
2. Is the difficulty level appropriate for the stated level (1=recall → 5=challenge)?
3. Is the DOK level (1=recall, 2=skill/concept, 3=strategic) accurate for this question?
4. Are there any mathematical errors in the question or answer options?

Respond with ONLY this JSON:
{
  "tests_the_standard": true | false,
  "confidence": 0.0 to 1.0,
  "difficulty_accurate": true | false,
  "dok_accurate": true | false,
  "mathematical_errors": ["list any errors, or empty array"],
  "reasoning": "2–4 sentence explanation of your evaluation",
  "suggested_standard_code": "alternative standard code if misaligned, or null"
}
```

---

## 2.7 Acceptance Criteria

### AC-11: Learning Plan Generation

- [ ] AC-11.1: A `learning_plan` record is created within 5 seconds of the `diagnostic_completed` event being published to Redis Streams.
- [ ] AC-11.2: The learning plan sequence respects all prerequisite relationships: no `plan_module` with sequence_order N has a prerequisite skill that appears at sequence_order > N.
- [ ] AC-11.3: A student with ≥ 40% Below Par skills receives `track = 'catch_up'`.
- [ ] AC-11.4: A student with ≥ 70% Above Par skills receives `track = 'accelerate'`.
- [ ] AC-11.5: A student with all skills at P(mastered) ≥ 0.85 receives an empty module list (plan with 0 modules) and a completion badge.
- [ ] AC-11.6: The first module in every plan has `status = 'available'`; all others have `status = 'locked'`.
- [ ] AC-11.7: `GET /students/:student_id/learning-plan/status` returns `plan_ready: false` before plan generation completes and `plan_ready: true` within 10 seconds of diagnostic completion.
- [ ] AC-11.8: The plan JSON structure matches the schema defined in FR-7.9 exactly (validated by JSON Schema validator in test suite).
- [ ] AC-11.9: Topological sort test: given a known diagnostic result where 3.OA.C.7 is Below Par and 4.NBT.B.5 is Below Par, 3.OA.C.7 appears before 4.NBT.B.5 in the module sequence.

### AC-12: Skill Dependency Graph

- [ ] AC-12.1: The skill graph loads from the database without error and contains exactly V = 38 nodes (29 Grade 4 + 9 Grade 3) and E ≥ 35 edges.
- [ ] AC-12.2: The graph is validated as a DAG (no cycles) on every application startup. A cycle introduction causes application startup to fail with a clear error.
- [ ] AC-12.3: `GET /graph/prerequisites/4.NBT.B.5` returns `3.OA.C.7` and `3.NBT.A.3` in the prerequisite chain.
- [ ] AC-12.4: `get_remediation_chain('4.NBT.B.5', {}, G)` where all states are below mastery returns `['3.OA.C.7', '3.NBT.A.3', '4.NBT.B.5']` in that order.
- [ ] AC-12.5: Graph cache is invalidated and rebuilt within 30 seconds of an admin update to prerequisite_relationships.
- [ ] AC-12.6: Module re-sequencing after a practice session completes in < 1 second (measured in unit test with the full 38-node graph).

### AC-13: AI Question Generation Pipeline

- [ ] AC-13.1: A valid generation job completes all 5 pipeline steps and produces a question in the `generated_questions` table within 30 seconds.
- [ ] AC-13.2: A question with an incorrect Python solution (Step 2 fail) is stored with `validation_status = 'failed'` and is NOT promoted to the `questions` table.
- [ ] AC-13.3: A question with alignment confidence < 0.85 is stored with `requires_human_review = TRUE` and appears in the admin review queue.
- [ ] AC-13.4: A question that passes all 5 steps automatically receives `is_validated = TRUE` and `source = 'llm_generated'` in the `questions` table after the daily promotion job runs.
- [ ] AC-13.5: A question containing a prohibited keyword (e.g., "alcohol") fails Step 3c (content safety keyword) and is stored with `validation_status = 'failed'`.
- [ ] AC-13.6: Deduplication: generating a semantically identical question (cosine similarity > 0.92) to an existing question results in the new question being discarded (not stored).
- [ ] AC-13.7: Pipeline throughput: 4 workers sustain ≥ 100 validated questions per hour in a load test (simulated with mocked LLM responses).
- [ ] AC-13.8: LLM cost tracking: each completed generation job records a non-zero `llm_cost_usd` value in the `generation_jobs` table.
- [ ] AC-13.9: Daily spend hard stop: when `padi:llm:daily_spend_cents` > 1000, new generation jobs are not dequeued by workers (verified in integration test with mocked Redis counter).
- [ ] AC-13.10: By the end of a simulated 30-day generation run (using mocked LLM, pipeline runs real validation logic), the `questions` table contains ≥ 5,000 validated records.
- [ ] AC-13.11: Every generated question for standard code X is rejected if the alignment verification model returns `tests_the_standard: false` with high confidence. Verified via test with a deliberately off-standard question injected into pipeline.

### AC-14: Practice Sessions

- [ ] AC-14.1: Starting a practice session for a lesson in `available` status creates the session and returns 10–15 questions from the `questions` table for the correct standard code.
- [ ] AC-14.2: Questions served in a practice session are within the lesson's `difficulty_range_min` to `difficulty_range_max` (may adapt during session in Stage 3; in Stage 2, static range).
- [ ] AC-14.3: Practice sessions (unlike diagnostic) return `is_correct` and `correct_answer` in the answer submission response.
- [ ] AC-14.4: Solution steps are returned in the answer response when `is_correct == false`.
- [ ] AC-14.5: Completing a practice session updates the `student_skill_states.p_mastered` field for the practiced standard.
- [ ] AC-14.6: If `p_mastered` crosses 0.85 after a session, the `plan_modules.status` is updated to `mastered` and the next module in sequence changes from `locked` to `available`.
- [ ] AC-14.7: A student cannot start a practice session for a `locked` lesson (API returns 403 LESSON_LOCKED).

### AC-15: Student Dashboard

- [ ] AC-15.1: The student dashboard renders the learning roadmap with correct module status icons for all modules (locked/available/in-progress/mastered) within 2 seconds of load.
- [ ] AC-15.2: Clicking a locked module displays a tooltip naming the prerequisite module.
- [ ] AC-15.3: The "Continue Practice" CTA is visible and links to the correct in-progress lesson.
- [ ] AC-15.4: Module status badges use the correct colors as specified in FR-9.2.
- [ ] AC-15.5: On mobile (< 768px), the roadmap degrades to a vertical card list without the SVG path.
- [ ] AC-15.6: Progress percentage is accurate (matches `modules_mastered / modules_total × 100`).
- [ ] AC-15.7: Streak display shows the correct current streak value matching the `student_streaks` table.

### AC-16: Gamification

- [ ] AC-16.1: The `first_session` badge is awarded within 2 seconds of the first practice session completing.
- [ ] AC-16.2: The `streak_3` badge is awarded on the 3rd consecutive day with at least one completed session.
- [ ] AC-16.3: Streak is NOT incremented if a student completes two sessions on the same calendar day (Pacific time).
- [ ] AC-16.4: Streak resets to 1 if a student resumes after a gap of 2+ days.
- [ ] AC-16.5: Each badge is awarded at most once per student (UNIQUE constraint prevents duplicates).
- [ ] AC-16.6: New badges are flagged as `shown_to_student = FALSE` until the student's dashboard loads and calls `POST /students/:id/badges/mark-shown`.
- [ ] AC-16.7: Celebration animation (confetti) plays on student dashboard load if `new_badges_since_last_login` is non-empty.

### AC-17: Parent Dashboard

- [ ] AC-17.1: The parent dashboard loads within 2 seconds and displays correct data for all children.
- [ ] AC-17.2: Weekly activity chart correctly shows 7 daily bars with minutes matching practice session durations stored in the database.
- [ ] AC-17.3: Lifetime accuracy rate is computed correctly: `correct_count / total_questions_answered`.
- [ ] AC-17.4: Weekly summary email is sent (via email service) every Sunday at 6 PM Pacific for all parents with `weekly_summary_email: true` in notification preferences.
- [ ] AC-17.5: The weekly summary email contains an unsubscribe link that, when clicked, sets `notification_preferences.weekly_summary_email = false`.
- [ ] AC-17.6: Module mastery date shown in parent plan view matches `plan_modules.mastered_at` for all mastered modules.

### AC-18: Non-Functional

- [ ] AC-18.1: Learning plan generation (diagnostic_completed event → plan fully written to DB): < 5 seconds P95 in production load test.
- [ ] AC-18.2: Student dashboard initial load: < 2 seconds P95 under 500 concurrent users.
- [ ] AC-18.3: Parent dashboard initial load: < 2 seconds P95 under 500 concurrent users.
- [ ] AC-18.4: Skill graph re-sequencing (module re-order after session): < 1 second in production.
- [ ] AC-18.5: Pipeline throughput: ≥ 100 validated questions per hour with 4 workers (load test).
- [ ] AC-18.6: Total questions in `questions` table (seed + generated) ≥ 5,000 by end of Stage 2.
- [ ] AC-18.7: Average LLM cost per generated question (as recorded in `generation_jobs.llm_cost_usd`) ≤ $0.05.
- [ ] AC-18.8: pgvector embedding index (IVFFlat) returns similarity search results in < 100ms for a pool of 5,000 questions.
- [ ] AC-18.9: All Stage 2 student-facing screens pass axe-core automated accessibility scan with zero critical or serious violations.

---

*End of PRD Stage 2 — Version 1.0*  
*PADI.AI | Personalized Learning Plan Generator*  
*Target Completion: Month 6*
