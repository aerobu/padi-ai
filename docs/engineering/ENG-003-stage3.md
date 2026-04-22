# Engineering Plan — Stage 3: Adaptive Practice Engine

**Document ID:** ENG-003  
**Version:** 1.0  
**Stage:** 3 of 6  
**Timeline:** Months 7–10  
**Status:** Draft  
**Last Updated:** 2026-04-04  
**Author:** Principal AI Systems Architect  

> **Stage 3 Solo Development Estimate:** 180–240 agent-hours | Calendar: 6–8 months  
> **Agent breakdown:**  
> - LangGraph StateGraph skeleton: 35–50 hrs  
> - Assessment Agent: 25–35 hrs  
> - Tutor Agent (Socratic hints): 30–45 hrs  
> - Question Generator Agent: 20–30 hrs  
> - Progress Tracker (BKT real-time): 20–30 hrs  
> - WebSocket protocol: 25–35 hrs  
> - Session UI: 25–35 hrs  

---

## Executive Summary

Stage 3 transforms PADI.AI from a content-delivery platform into a fully adaptive, AI-powered learning engine. This stage introduces the LangGraph multi-agent practice engine, real-time Bayesian Knowledge Tracing (BKT) with IRT-informed question selection, a dual memory system (working + long-term), and a Socratic tutoring agent powered by Claude Sonnet 4.6. All interactions are delivered over persistent WebSocket connections for sub-second responsiveness.

**Key Deliverables:**
- LangGraph StateGraph-based adaptive practice engine with 7+ specialized agent nodes
- Real-time BKT mastery tracking with per-skill state persistence
- IRT-informed adaptive difficulty selection (Maximum Fisher Information)
- Dual memory system: Redis working memory + PostgreSQL long-term memory
- Socratic tutor agent with 3-level hint ladder and frustration detection
- Full WebSocket protocol for real-time student–server interaction
- Comprehensive agent interaction logging for auditability

---

## 1. High-Level Architecture

### 1.1 System Evolution (What Changes from Previous Stage)

**Existing (end of Stage 2):**
- Next.js 15 web app on Vercel — student dashboard, learning plan viewer, content browser
- FastAPI API server on AWS ECS — REST endpoints for auth, student profiles, learning plans, content management
- PostgreSQL 17 on RDS — user accounts, learning plans, question bank, content metadata
- Redis 7 on ElastiCache — session tokens, rate limiting, general caching
- S3 — static assets, content media

**New in Stage 3:**

| Component | Type | Description |
|-----------|------|-------------|
| Agent Engine | Embedded in FastAPI (ECS) | LangGraph StateGraph runtime for adaptive practice sessions |
| WebSocket Layer | FastAPI endpoint | Persistent bidirectional connections for practice sessions |
| BKT Engine | Python module (embedded) | Real-time Bayesian Knowledge Tracing updates per skill |
| Working Memory | Redis keyspace | Session-scoped interaction history, last 10 exchanges |
| Long-Term Memory | PostgreSQL tables | Student learning profiles, error patterns, mastery timestamps |
| Agent Interaction Logs | PostgreSQL table | Full audit trail of every LLM call (model, tokens, latency) |
| SQS Question Queue | AWS SQS | Async question pre-generation for upcoming skills |
| Prompt Registry | File system + versioned | Jinja2 prompt templates with version tracking |

**Architectural Decision: Agent Engine Deployment**

The Agent Engine is **embedded within the FastAPI application** at Stage 3, not deployed as a separate ECS service. Rationale:

| Factor | Embedded (chosen) | Separate Service |
|--------|--------------------|------------------|
| Latency | ~0ms (in-process) | +5-15ms per call (network hop) |
| Complexity | Single deployment unit | Service discovery, health checks, separate CI/CD |
| Debugging | Single log stream, single debugger | Distributed tracing required |
| Scaling | Scales with API | Independent scaling |
| **Verdict** | **Best for Stage 3 (≤500 concurrent sessions)** | Consider at Stage 5 if load requires |

The Agent Engine communicates with PostgreSQL and Redis **directly** (not through the REST API layer). This avoids unnecessary serialization/deserialization overhead and REST round-trips during latency-sensitive practice loops. The Agent Engine imports the same SQLAlchemy models and Redis client as the REST layer—they share the same connection pools within the FastAPI process.

### 1.2 Updated Container Diagram (C4 Level 2)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          PADI.AI — Stage 3                         │
│                         Container Diagram (C4 L2)                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────────────────┐       ┌────────────────────────────────────┐  │
│  │    Next.js 15 Web App    │       │      FastAPI API Server (ECS)      │  │
│  │       (Vercel)           │       │                                    │  │
│  │                          │ WSS   │  ┌──────────┐  ┌───────────────┐  │  │
│  │  - Student Dashboard     ├──────►│  │ REST API │  │  WebSocket    │  │  │
│  │  - Practice UI           │ HTTPS │  │ Endpoints│  │  Endpoint     │  │  │
│  │  - Learning Plan View    ├──────►│  │          │  │  /ws/practice │  │  │
│  │  - Progress Visualization│       │  └────┬─────┘  └──────┬────────┘  │  │
│  │                          │       │       │               │            │  │
│  └──────────────────────────┘       │  ┌────┴───────────────┴─────────┐  │  │
│                                     │  │       Agent Engine            │  │  │
│                                     │  │    (LangGraph StateGraph)     │  │  │
│                                     │  │                               │  │  │
│                                     │  │  ┌─────────┐ ┌────────────┐  │  │  │
│                                     │  │  │  Tutor   │ │ Assessment │  │  │  │
│                                     │  │  │  Agent   │ │   Agent    │  │  │  │
│                                     │  │  │(Sonnet)  │ │ (o3-mini)  │  │  │  │
│                                     │  │  └─────────┘ └────────────┘  │  │  │
│                                     │  │  ┌─────────┐ ┌────────────┐  │  │  │
│                                     │  │  │  BKT    │ │ Question   │  │  │  │
│                                     │  │  │ Engine  │ │ Selector   │  │  │  │
│                                     │  │  └─────────┘ └────────────┘  │  │  │
│                                     │  └──────────────────────────────┘  │  │
│                                     │                                    │  │
│                                     └──────────┬──────────┬──────────────┘  │
│                                                │          │                  │
│                          ┌─────────────────────┤          │                  │
│                          │                     │          │                  │
│                          ▼                     ▼          ▼                  │
│  ┌──────────────────────────┐  ┌──────────────────┐  ┌────────────────┐    │
│  │   PostgreSQL 17 (RDS)    │  │ Redis 7           │  │  AWS SQS       │    │
│  │                          │  │ (ElastiCache)     │  │                │    │
│  │  - User accounts         │  │                   │  │ - Question     │    │
│  │  - Learning plans        │  │  - Session tokens │  │   pre-gen jobs │    │
│  │  - Question bank         │  │  - WS session map │  │ - DLQ attached │    │
│  │  - Practice sessions     │  │  - Working memory │  │                │    │
│  │  - BKT state history     │  │  - BKT state cache│  └────────┬───────┘    │
│  │  - Long-term memory      │  │  - LangGraph      │           │            │
│  │  - Agent interaction logs│  │    checkpoints    │           ▼            │
│  │  - pgvector embeddings   │  │                   │  ┌────────────────┐    │
│  │                          │  │                   │  │  SQS Worker    │    │
│  └──────────────────────────┘  └───────────────────┘  │  (ECS Task)    │    │
│                                                       │                │    │
│                                                       │ - Pre-generates│    │
│                                                       │   questions    │    │
│                                                       │   via o3-mini  │    │
│                                                       └────────────────┘    │
│                                                                             │
│                          ┌──────────────────────────┐                       │
│                          │       AWS S3              │                       │
│                          │  - Static assets          │                       │
│                          │  - Content media           │                       │
│                          └──────────────────────────┘                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.3 Multi-Agent System Architecture (Deep Dive)

> **LLM Local-First Routing (Updated April 2026):** Per ADR-009, all student-facing LLM inference uses local Ollama/Qwen2.5 models by default until COPPA DPAs are obtained. Do NOT import `anthropic` or `openai` SDKs directly in agent node code. All LLM calls must go through `llm_client.get_llm_response(role, messages)`.
>
> **Active routing at Stage 3 launch:**
> ```
> tutor_agent      → ollama/qwen2.5:72b   (local, COPPA-safe)
> assessment_agent → ollama/qwen2.5:32b   (local, COPPA-safe)
> question_gen     → anthropic/claude-sonnet-4-6  (cloud OK, no student PII)
> progress_tracker → no LLM (pure pyBKT)
> ```
>
> **To switch to Claude Sonnet for student-facing roles:** Change `LLM_ROUTING["tutor"]` in `config.py` — no other code changes needed. Only do this after COPPA DPA is confirmed in writing from Anthropic.

#### 1.3.1 State Definition

```python
# services/agent-engine/src/graph/state.py

from __future__ import annotations

from typing import TypedDict, Annotated, Literal
from uuid import UUID
from datetime import datetime


class QuestionPayload(TypedDict):
    """Question data sent to client and used in evaluation."""
    question_id: str
    skill_code: str
    question_text: str
    question_type: Literal["multiple_choice", "numeric", "free_response", "drag_drop"]
    choices: list[dict] | None          # For MC: [{"id": "A", "text": "..."}, ...]
    correct_answer: str                 # Canonical correct answer
    difficulty: float                   # IRT b-parameter (difficulty)
    discrimination: float               # IRT a-parameter
    guessing: float                     # IRT c-parameter
    domain: str                         # e.g., "Number & Operations"
    standard_code: str                  # Oregon CCSS code e.g., "3.OA.A.1"
    scaffold_hints: list[str]           # Pre-authored hints (fallback)
    word_problem_theme: str | None      # e.g., "sports", "animals", "cooking"


class ResponseRecord(TypedDict):
    """Record of a single student response within a session."""
    question_id: str
    skill_code: str
    answer: str
    is_correct: bool
    error_type: str | None              # "computational", "conceptual", "procedural", "careless", None
    hint_count: int
    attempt_number: int
    time_to_answer_ms: int
    difficulty_used: float
    irt_info_value: float


class WorkingMemory(TypedDict):
    """Last N interactions for in-context learning by agents."""
    recent_interactions: list[dict]     # Last 10 Q&A pairs with metadata
    current_streak: int                 # Consecutive correct (positive) or incorrect (negative)
    session_error_types: list[str]      # Error types seen this session
    time_pressure_detected: bool        # True if response times are accelerating abnormally


class LongTermMemory(TypedDict):
    """Persisted student profile loaded at session start."""
    preferred_explanation_style: Literal["visual", "verbal", "example_based", "step_by_step"]
    common_error_patterns: dict[str, list[str]]   # skill_code → [error_types]
    engagement_pattern: dict                       # {"avg_session_length_min": float, "best_time_of_day": str, ...}
    mastery_timestamps: dict[str, str]             # skill_code → ISO timestamp of mastery
    total_sessions_completed: int
    cumulative_correct_rate: float


class SessionState(TypedDict):
    """Complete state for a single adaptive practice session.
    
    This TypedDict is the LangGraph StateGraph state schema.
    Every node reads from and writes to this state.
    LangGraph checkpointing serializes this between graph steps.
    """
    # --- Session identity ---
    session_id: str
    student_id: str
    plan_module_id: str
    
    # --- Current question context ---
    current_skill_code: str
    current_question: QuestionPayload | None
    attempt_count: int                  # Attempts on current question (1-indexed)
    max_attempts: int                   # Default 3
    hints_used: int                     # Hints used on current question
    
    # --- Session-level tracking ---
    session_responses: list[ResponseRecord]
    questions_presented: int
    correct_count: int
    skills_attempted: list[str]
    skills_mastered_this_session: list[str]
    
    # --- BKT state ---
    bkt_states: dict[str, float]        # skill_code → P(mastered) current posterior
    bkt_params: dict[str, dict]         # skill_code → {"p_transit", "p_slip", "p_guess", "p_prior"}
    mastery_threshold: float            # Default 0.95
    mastery_streak_required: int        # Default 5 consecutive correct after threshold
    
    # --- Frustration & affect ---
    frustration_score: float            # 0.0–1.0, computed by TutorAgent
    frustration_history: list[float]    # Track frustration across session
    scaffolded_mode: bool               # True = lower difficulty, more hints
    
    # --- Dual memory ---
    working_memory: WorkingMemory
    long_term_memory: LongTermMemory
    
    # --- Skill progression ---
    skill_queue: list[str]              # Ordered skills remaining in this module
    current_skill_index: int
    
    # --- IRT state ---
    theta_estimate: float               # Current ability estimate
    theta_sem: float                    # Standard error of measurement
    
    # --- Control flow ---
    session_started_at: str             # ISO timestamp
    session_complete: bool
    end_reason: str | None              # "mastery_complete", "fatigue", "time_limit", "error", "user_quit"
    
    # --- Error handling ---
    error: str | None
    error_count: int                    # Cumulative errors this session
    max_errors: int                     # Default 3 before session termination
```

#### 1.3.2 Graph Nodes — Complete Specifications

Each node is an `async` function that receives the full `SessionState` and returns a partial state update dict.

---

**Node: `initialize_session_node`**

```python
# services/agent-engine/src/graph/nodes/initialize.py

from __future__ import annotations
import logging
from datetime import datetime, timezone
from uuid import uuid4

from ..state import SessionState, WorkingMemory, LongTermMemory

logger = logging.getLogger(__name__)


async def initialize_session_node(state: SessionState) -> dict:
    """Initialize a new practice session by loading student context.
    
    Algorithm:
    1. Load the student's long-term memory (LTM) from PostgreSQL:
       - preferred_explanation_style
       - common_error_patterns per skill
       - engagement_pattern (avg session length, best time of day)
       - mastery_timestamps for all previously mastered skills
    2. Load current BKT states for all skills in the module's skill_queue
       from the bkt_state_history table (most recent per skill).
    3. Load the module's skill queue from the learning_plan_modules table.
    4. Compute initial theta estimate from historical BKT states using
       a weighted average of P(mastered) across skills.
    5. Initialize working memory as empty.
    6. Set session metadata (timestamps, counters).
    
    If LTM does not exist (first session), create defaults:
       - preferred_explanation_style = "step_by_step"
       - common_error_patterns = {}
       - engagement_pattern = {"avg_session_length_min": 15.0}
    
    Returns:
        Partial state update with loaded LTM, BKT states, skill queue,
        and initialized counters.
    
    Raises:
        Never raises — on DB failure, returns defaults with error flag.
    """
    from ...memory.long_term import LongTermMemoryStore
    from ...memory.working import WorkingMemoryStore
    from ...services.bkt_service import BKTService
    from ...services.plan_service import PlanService
    
    ltm_store = LongTermMemoryStore()
    bkt_service = BKTService()
    plan_service = PlanService()
    
    try:
        # 1. Load long-term memory
        ltm = await ltm_store.load(state["student_id"])
        if ltm is None:
            ltm = LongTermMemory(
                preferred_explanation_style="step_by_step",
                common_error_patterns={},
                engagement_pattern={"avg_session_length_min": 15.0, "best_time_of_day": "unknown"},
                mastery_timestamps={},
                total_sessions_completed=0,
                cumulative_correct_rate=0.5,
            )
        
        # 2. Load skill queue for this module
        skill_queue = await plan_service.get_module_skill_queue(
            state["plan_module_id"], state["student_id"]
        )
        # Filter out already-mastered skills
        skill_queue = [
            sk for sk in skill_queue
            if sk not in ltm.get("mastery_timestamps", {})
        ]
        if not skill_queue:
            # All skills mastered — edge case
            return {
                "session_complete": True,
                "end_reason": "mastery_complete",
                "error": None,
            }
        
        # 3. Load BKT states for all skills in queue
        bkt_states = await bkt_service.load_current_states(
            state["student_id"], skill_queue
        )
        bkt_params = await bkt_service.load_params(skill_queue)
        
        # 4. Compute initial theta from BKT states
        if bkt_states:
            theta = sum(bkt_states.values()) / len(bkt_states) * 2.0 - 1.0  # Map [0,1] → [-1,1]
        else:
            theta = 0.0  # Prior: average ability
        
        # 5. Initialize working memory
        working_mem = WorkingMemory(
            recent_interactions=[],
            current_streak=0,
            session_error_types=[],
            time_pressure_detected=False,
        )
        
        return {
            "long_term_memory": ltm,
            "working_memory": working_mem,
            "bkt_states": bkt_states,
            "bkt_params": bkt_params,
            "skill_queue": skill_queue,
            "current_skill_code": skill_queue[0],
            "current_skill_index": 0,
            "theta_estimate": theta,
            "theta_sem": 1.0,  # High uncertainty at session start
            "session_started_at": datetime.now(timezone.utc).isoformat(),
            "session_responses": [],
            "questions_presented": 0,
            "correct_count": 0,
            "skills_attempted": [skill_queue[0]],
            "skills_mastered_this_session": [],
            "attempt_count": 0,
            "hints_used": 0,
            "frustration_score": 0.0,
            "frustration_history": [],
            "scaffolded_mode": False,
            "session_complete": False,
            "end_reason": None,
            "error": None,
            "error_count": 0,
        }
    
    except Exception as e:
        logger.error(f"Session initialization failed: {e}", exc_info=True)
        return {
            "error": f"initialization_failed: {str(e)}",
            "error_count": state.get("error_count", 0) + 1,
        }
```

---

**Node: `select_question_node`**

```python
# services/agent-engine/src/graph/nodes/select_question.py

from __future__ import annotations
import logging
import random
from ..state import SessionState, QuestionPayload

logger = logging.getLogger(__name__)


async def select_question_node(state: SessionState) -> dict:
    """Select the optimal next question using IRT Maximum Fisher Information.
    
    Algorithm:
    1. Retrieve the item bank for the current skill from PostgreSQL.
    2. Filter out:
       a. Questions already presented this session.
       b. Questions presented in the student's last 3 sessions (exposure control).
    3. If in scaffolded_mode, further filter to items with b < theta_estimate
       (easier questions only).
    4. For each remaining item, compute Fisher Information at current theta:
       I(θ) = a² * (P(θ) - c)² / ((1-c)² * P(θ) * Q(θ))
       where P(θ) = c + (1-c) / (1 + exp(-a*(θ-b)))
    5. Select the item with maximum I(θ).
       - Tie-breaking: prefer items whose word_problem_theme differs from
         the last 2 questions (context diversity enforcement).
    6. If item bank is exhausted (< 3 items remaining), enqueue a
       question generation job to SQS for this skill.
    
    Returns:
        Partial state with current_question set, attempt_count reset to 0,
        hints_used reset to 0.
    """
    import math
    from ...services.question_bank import QuestionBankService
    from ...services.sqs_client import SQSClient
    
    qb = QuestionBankService()
    skill_code = state["current_skill_code"]
    theta = state["theta_estimate"]
    
    try:
        # 1. Fetch item bank
        items = await qb.get_items_for_skill(skill_code)
        
        # 2a. Exclude items presented this session
        presented_ids = {r["question_id"] for r in state["session_responses"]}
        items = [i for i in items if i["question_id"] not in presented_ids]
        
        # 2b. Exposure control — exclude items from last 3 sessions
        recent_ids = await qb.get_recently_presented(
            state["student_id"], skill_code, session_count=3
        )
        items = [i for i in items if i["question_id"] not in recent_ids]
        
        # 3. Scaffolded mode filter
        if state.get("scaffolded_mode", False):
            easier = [i for i in items if i["difficulty"] < theta]
            if easier:
                items = easier
        
        if not items:
            # Fallback: allow repeats but warn
            items = await qb.get_items_for_skill(skill_code)
            items = [i for i in items if i["question_id"] not in presented_ids]
            logger.warning(f"Item bank nearly exhausted for {skill_code}, allowing repeats from older sessions")
        
        if not items:
            return {
                "error": f"no_items_available: {skill_code}",
                "error_count": state.get("error_count", 0) + 1,
            }
        
        # 4. Compute Fisher Information for each item
        def irt_probability(theta: float, a: float, b: float, c: float) -> float:
            exponent = -a * (theta - b)
            exponent = max(min(exponent, 35.0), -35.0)  # Prevent overflow
            return c + (1 - c) / (1 + math.exp(exponent))
        
        def fisher_information(theta: float, a: float, b: float, c: float) -> float:
            p = irt_probability(theta, a, b, c)
            q = 1.0 - p
            if p < 1e-10 or q < 1e-10:
                return 0.0
            numerator = a ** 2 * (p - c) ** 2
            denominator = (1 - c) ** 2 * p * q
            return numerator / denominator if denominator > 0 else 0.0
        
        for item in items:
            item["_info"] = fisher_information(
                theta, item["discrimination"], item["difficulty"], item["guessing"]
            )
        
        # 5. Sort by information, then apply diversity tie-breaking
        items.sort(key=lambda x: x["_info"], reverse=True)
        
        # Take top 5 candidates for diversity selection
        top_candidates = items[:min(5, len(items))]
        
        # Context diversity: prefer different word problem themes
        recent_themes = []
        for r in state["session_responses"][-2:]:
            if q := state.get("current_question"):
                if t := q.get("word_problem_theme"):
                    recent_themes.append(t)
        
        # Prefer candidates with different themes
        diverse = [c for c in top_candidates if c.get("word_problem_theme") not in recent_themes]
        selected = diverse[0] if diverse else top_candidates[0]
        
        # 6. Check if item bank is running low — enqueue generation job
        remaining_count = len(items)
        if remaining_count < 3:
            sqs = SQSClient()
            await sqs.enqueue_question_generation(
                skill_code=skill_code,
                target_difficulty=theta,
                count=10,
            )
            logger.info(f"Enqueued question generation for {skill_code}, only {remaining_count} items remain")
        
        question_payload = QuestionPayload(
            question_id=selected["question_id"],
            skill_code=selected["skill_code"],
            question_text=selected["question_text"],
            question_type=selected["question_type"],
            choices=selected.get("choices"),
            correct_answer=selected["correct_answer"],
            difficulty=selected["difficulty"],
            discrimination=selected["discrimination"],
            guessing=selected["guessing"],
            domain=selected["domain"],
            standard_code=selected["standard_code"],
            scaffold_hints=selected.get("scaffold_hints", []),
            word_problem_theme=selected.get("word_problem_theme"),
        )
        
        return {
            "current_question": question_payload,
            "attempt_count": 0,
            "hints_used": 0,
            "questions_presented": state["questions_presented"] + 1,
        }
    
    except Exception as e:
        logger.error(f"Question selection failed: {e}", exc_info=True)
        return {
            "error": f"question_selection_failed: {str(e)}",
            "error_count": state.get("error_count", 0) + 1,
        }
```

---

**Node: `present_question_node`**

```python
# services/agent-engine/src/graph/nodes/present_question.py

from __future__ import annotations
from ..state import SessionState


async def present_question_node(state: SessionState) -> dict:
    """Format the current question for WebSocket delivery to the frontend.
    
    Algorithm:
    1. Read current_question from state.
    2. Strip server-only fields (correct_answer, scaffold_hints, IRT params)
       to produce a client-safe payload.
    3. If a hint was just generated (hints_used > 0 and we're re-presenting),
       include the hint in the output.
    4. Increment attempt_count.
    
    This node is primarily a pass-through that signals the WebSocket handler
    to emit a QUESTION or HINT ServerMessage. The actual WebSocket send
    is handled by the graph runner's stream-to-WS bridge.
    
    Returns:
        Partial state with attempt_count incremented.
        The stream handler reads current_question to build the WS message.
    """
    return {
        "attempt_count": state["attempt_count"] + 1,
    }
```

---

**Node: `evaluate_response_node`**

```python
# services/agent-engine/src/graph/nodes/evaluate_response.py

from __future__ import annotations
import logging
import time
from ..state import SessionState, ResponseRecord

logger = logging.getLogger(__name__)


async def evaluate_response_node(state: SessionState) -> dict:
    """Assessment Agent — evaluate the student's answer using o3-mini.
    
    Algorithm:
    1. Compare submitted answer against correct_answer:
       a. For multiple_choice: exact match on choice ID.
       b. For numeric: parse both as floats, allow ±0.01 tolerance.
       c. For free_response: invoke o3-mini to evaluate equivalence.
    2. If answer is incorrect, classify the error type using o3-mini:
       - "computational": correct approach but arithmetic error
       - "conceptual": fundamental misunderstanding of the concept
       - "procedural": wrong method or algorithm applied
       - "careless": minor mistake (sign error, copying error)
       Use structured output (Pydantic model) to enforce classification.
    3. Measure response time (client-reported time_to_answer_ms).
    4. Create a ResponseRecord and append to session_responses.
    5. Update working memory with this interaction.
    
    Returns:
        Partial state with updated session_responses, working_memory,
        correct_count, and the is_correct flag for routing.
    """
    from ...agents.assessment import AssessmentAgent
    
    agent = AssessmentAgent()
    question = state["current_question"]
    
    if question is None:
        return {"error": "evaluate_called_without_question", "error_count": state["error_count"] + 1}
    
    # The student's answer is injected into state by the WebSocket handler
    # before invoking the graph continuation.
    student_answer = state.get("_pending_answer", "")
    time_to_answer_ms = state.get("_pending_time_ms", 0)
    
    try:
        # 1. Evaluate correctness
        q_type = question["question_type"]
        is_correct = False
        error_type = None
        
        if q_type == "multiple_choice":
            is_correct = student_answer.strip().upper() == question["correct_answer"].strip().upper()
        elif q_type == "numeric":
            try:
                student_val = float(student_answer.replace(",", "").strip())
                correct_val = float(question["correct_answer"])
                is_correct = abs(student_val - correct_val) < 0.01
            except ValueError:
                is_correct = False
        elif q_type in ("free_response", "drag_drop"):
            # Use o3-mini for semantic evaluation
            eval_result = await agent.evaluate_free_response(
                question_text=question["question_text"],
                correct_answer=question["correct_answer"],
                student_answer=student_answer,
                skill_code=question["skill_code"],
            )
            is_correct = eval_result.is_correct
            error_type = eval_result.error_type
        
        # 2. If incorrect and error_type not yet classified, classify
        if not is_correct and error_type is None:
            error_result = await agent.classify_error(
                question_text=question["question_text"],
                correct_answer=question["correct_answer"],
                student_answer=student_answer,
                skill_code=question["skill_code"],
            )
            error_type = error_result.error_type
        
        # 3. Compute IRT information value for this response
        import math
        theta = state["theta_estimate"]
        a, b, c = question["discrimination"], question["difficulty"], question["guessing"]
        exp_val = -a * (theta - b)
        exp_val = max(min(exp_val, 35.0), -35.0)
        p = c + (1 - c) / (1 + math.exp(exp_val))
        q = 1.0 - p
        info_value = (a ** 2 * (p - c) ** 2) / ((1 - c) ** 2 * p * q) if (p > 1e-10 and q > 1e-10) else 0.0
        
        # 4. Create response record
        record = ResponseRecord(
            question_id=question["question_id"],
            skill_code=question["skill_code"],
            answer=student_answer,
            is_correct=is_correct,
            error_type=error_type,
            hint_count=state["hints_used"],
            attempt_number=state["attempt_count"],
            time_to_answer_ms=time_to_answer_ms,
            difficulty_used=question["difficulty"],
            irt_info_value=info_value,
        )
        
        new_responses = state["session_responses"] + [record]
        new_correct = state["correct_count"] + (1 if is_correct else 0)
        
        # 5. Update working memory
        wm = dict(state["working_memory"])
        interaction = {
            "question_id": question["question_id"],
            "skill_code": question["skill_code"],
            "is_correct": is_correct,
            "error_type": error_type,
            "hint_count": state["hints_used"],
            "attempt": state["attempt_count"],
        }
        recent = list(wm["recent_interactions"])
        recent.append(interaction)
        if len(recent) > 10:
            recent = recent[-10:]
        
        # Update streak
        streak = wm["current_streak"]
        if is_correct:
            streak = max(0, streak) + 1
        else:
            streak = min(0, streak) - 1
        
        # Track error types
        error_types = list(wm["session_error_types"])
        if error_type:
            error_types.append(error_type)
        
        updated_wm = {
            **wm,
            "recent_interactions": recent,
            "current_streak": streak,
            "session_error_types": error_types,
        }
        
        return {
            "session_responses": new_responses,
            "correct_count": new_correct,
            "working_memory": updated_wm,
            "_last_is_correct": is_correct,
            "_last_error_type": error_type,
        }
    
    except Exception as e:
        logger.error(f"Response evaluation failed: {e}", exc_info=True)
        return {
            "error": f"evaluation_failed: {str(e)}",
            "error_count": state["error_count"] + 1,
        }
```

---

**Node: `update_bkt_node`**

```python
# services/agent-engine/src/graph/nodes/update_bkt.py

from __future__ import annotations
import logging
from ..state import SessionState

logger = logging.getLogger(__name__)


async def update_bkt_node(state: SessionState) -> dict:
    """Progress Tracker Agent — run BKT update for the current skill.
    
    Algorithm (Corbett & Anderson 1994):
    1. Get current P(L_t) for the skill from bkt_states.
    2. Get BKT parameters: p_transit, p_slip, p_guess.
    3. Get the last response's is_correct flag.
    4. Compute posterior:
       If correct:
         P(L_t | correct) = P(L_t) * (1 - p_slip) / 
                            (P(L_t) * (1 - p_slip) + (1 - P(L_t)) * p_guess)
       If incorrect:
         P(L_t | incorrect) = P(L_t) * p_slip / 
                              (P(L_t) * p_slip + (1 - P(L_t)) * (1 - p_guess))
    5. Apply learning transition:
       P(L_{t+1}) = P(L_t | obs) + (1 - P(L_t | obs)) * p_transit
    6. Clamp to [0.001, 0.999] to avoid degenerate states.
    7. Update bkt_states dict.
    8. Update theta_estimate from BKT states (weighted average).
    9. Persist BKT state snapshot to bkt_state_history for audit.
    
    Returns:
        Partial state with updated bkt_states, theta_estimate.
    """
    from ...services.bkt_service import BKTService
    
    bkt_service = BKTService()
    skill_code = state["current_skill_code"]
    
    # Get current mastery probability
    p_mastered = state["bkt_states"].get(skill_code, 0.5)
    
    # Get BKT parameters for this skill
    params = state["bkt_params"].get(skill_code, {
        "p_transit": 0.1,
        "p_slip": 0.1,
        "p_guess": 0.2,
    })
    p_transit = params["p_transit"]
    p_slip = params["p_slip"]
    p_guess = params["p_guess"]
    
    # Get last response
    last_response = state["session_responses"][-1] if state["session_responses"] else None
    if last_response is None:
        return {}
    
    is_correct = last_response["is_correct"]
    
    # BKT Update (see Algorithm section §3.1 for full derivation)
    if is_correct:
        numerator = p_mastered * (1.0 - p_slip)
        denominator = p_mastered * (1.0 - p_slip) + (1.0 - p_mastered) * p_guess
    else:
        numerator = p_mastered * p_slip
        denominator = p_mastered * p_slip + (1.0 - p_mastered) * (1.0 - p_guess)
    
    if denominator < 1e-10:
        p_posterior = p_mastered  # Avoid division by zero
    else:
        p_posterior = numerator / denominator
    
    # Learning transition
    p_updated = p_posterior + (1.0 - p_posterior) * p_transit
    
    # Clamp
    p_updated = max(0.001, min(0.999, p_updated))
    
    # Update states dict
    new_bkt_states = dict(state["bkt_states"])
    new_bkt_states[skill_code] = p_updated
    
    # Update theta estimate from all BKT states
    if new_bkt_states:
        avg_mastery = sum(new_bkt_states.values()) / len(new_bkt_states)
        theta = avg_mastery * 4.0 - 2.0  # Map [0,1] → [-2, 2]
    else:
        theta = state["theta_estimate"]
    
    # Persist to history (fire-and-forget, don't block graph)
    try:
        await bkt_service.persist_state_snapshot(
            student_id=state["student_id"],
            skill_code=skill_code,
            p_mastered=p_updated,
            p_transit=p_transit,
            p_slip=p_slip,
            p_guess=p_guess,
            session_id=state["session_id"],
        )
    except Exception as e:
        logger.warning(f"BKT state persistence failed (non-fatal): {e}")
    
    return {
        "bkt_states": new_bkt_states,
        "theta_estimate": theta,
    }
```

---

**Node: `check_mastery_node`**

```python
# services/agent-engine/src/graph/nodes/check_mastery.py

from __future__ import annotations
from ..state import SessionState


async def check_mastery_node(state: SessionState) -> dict:
    """Conditional node — check if student has mastered current skill.
    
    Mastery criteria (both must be met):
    1. P(mastered) ≥ mastery_threshold (default 0.95)
    2. Student has answered correctly on the last mastery_streak_required
       questions for this skill (default 5 consecutive correct).
    
    This is a routing node — it returns a flag that the conditional
    edge reads to decide the next node.
    
    Returns:
        Partial state with _mastery_achieved flag.
    """
    skill_code = state["current_skill_code"]
    p_mastered = state["bkt_states"].get(skill_code, 0.0)
    threshold = state.get("mastery_threshold", 0.95)
    streak_required = state.get("mastery_streak_required", 5)
    
    # Check BKT threshold
    bkt_met = p_mastered >= threshold
    
    # Check consecutive correct streak for this skill
    skill_responses = [
        r for r in state["session_responses"]
        if r["skill_code"] == skill_code
    ]
    
    streak_met = False
    if len(skill_responses) >= streak_required:
        last_n = skill_responses[-streak_required:]
        streak_met = all(r["is_correct"] for r in last_n)
    
    mastery_achieved = bkt_met and streak_met
    
    return {
        "_mastery_achieved": mastery_achieved,
    }
```

---

**Node: `generate_hint_node`**

```python
# services/agent-engine/src/graph/nodes/generate_hint.py

from __future__ import annotations
import logging
from ..state import SessionState

logger = logging.getLogger(__name__)


async def generate_hint_node(state: SessionState) -> dict:
    """Tutor Agent — generate a level-appropriate Socratic hint via Claude Sonnet 4.6.
    
    Hint Ladder:
    - Level 1: Conceptual nudge. Point toward the relevant concept without
      revealing the method. Example: "Think about what multiplication means
      when we have groups of things."
    - Level 2: Procedural guidance. Describe the steps without computing.
      Example: "First, count how many groups there are. Then, figure out
      how many are in each group. What operation combines those?"
    - Level 3: Worked partial example. Show a similar problem solved
      partway, leaving the final step for the student.
      Example: "If there were 3 bags with 4 apples each, we'd do 3 × 4.
      Now, in your problem, how many bags and how many apples?"
    
    Algorithm:
    1. Determine hint_level = hints_used + 1 (capped at 3).
    2. Check for pre-authored scaffold_hints in the question payload.
       If available for this level, use them (faster, cheaper).
    3. If no pre-authored hint, invoke Claude Sonnet 4.6 with:
       - The question text (NO correct answer in prompt)
       - The student's incorrect answer
       - The error_type (if classified)
       - The hint_level description
       - Student's preferred_explanation_style from LTM
       - Working memory context (last 3 interactions)
    4. Validate hint output:
       - Must NOT contain the correct answer or a direct equivalent
       - Must be age-appropriate (grade-level vocabulary)
       - Must be ≤ 150 words
    5. If Claude fails or validation fails, fall back to pre-authored hints.
    6. Log the interaction to agent_interaction_logs.
    
    Returns:
        Partial state with hints_used incremented, _hint_text set.
    """
    from ...agents.tutor import TutorAgent
    
    tutor = TutorAgent()
    question = state["current_question"]
    hint_level = min(state["hints_used"] + 1, 3)
    
    try:
        # Try pre-authored hints first (cheaper, faster)
        scaffold_hints = question.get("scaffold_hints", [])
        if scaffold_hints and hint_level <= len(scaffold_hints):
            hint_text = scaffold_hints[hint_level - 1]
        else:
            # Generate via Claude Sonnet 4.6
            last_response = state["session_responses"][-1] if state["session_responses"] else None
            error_type = last_response["error_type"] if last_response else None
            student_answer = last_response["answer"] if last_response else ""
            
            context = {
                "explanation_style": state["long_term_memory"]["preferred_explanation_style"],
                "recent_interactions": state["working_memory"]["recent_interactions"][-3:],
                "grade_level": _infer_grade_from_skill(question["skill_code"]),
                "error_type": error_type,
            }
            
            hint_response = await tutor.generate_hint(
                question=question,
                hint_level=hint_level,
                student_answer=student_answer,
                context=context,
            )
            hint_text = hint_response.hint_text
            
            # Validate: hint must not contain the answer
            correct = question["correct_answer"].lower()
            if correct in hint_text.lower():
                logger.warning(f"Hint contained answer, falling back to generic hint")
                hint_text = _generic_hint(hint_level)
        
        return {
            "hints_used": hint_level,
            "_hint_text": hint_text,
            "_hint_level": hint_level,
        }
    
    except Exception as e:
        logger.error(f"Hint generation failed: {e}", exc_info=True)
        # Fallback to generic hints
        return {
            "hints_used": hint_level,
            "_hint_text": _generic_hint(hint_level),
            "_hint_level": hint_level,
            "error": None,  # Don't propagate — graceful degradation
        }


def _generic_hint(level: int) -> str:
    """Fallback hints when LLM is unavailable."""
    hints = {
        1: "Take another look at the problem. What information does it give you?",
        2: "Try breaking the problem into smaller steps. What's the first thing you need to figure out?",
        3: "Let's work through it together. Start by writing down what you know, then think about what operation to use.",
    }
    return hints.get(level, hints[3])


def _infer_grade_from_skill(skill_code: str) -> int:
    """Extract grade level from skill code like '3.OA.A.1' → 3."""
    try:
        return int(skill_code.split(".")[0])
    except (ValueError, IndexError):
        return 4  # Default
```

---

**Node: `handle_frustration_node`**

```python
# services/agent-engine/src/graph/nodes/handle_frustration.py

from __future__ import annotations
import logging
from ..state import SessionState

logger = logging.getLogger(__name__)


async def handle_frustration_node(state: SessionState) -> dict:
    """Handle detected student frustration — adapt or recommend a break.
    
    Algorithm:
    1. Evaluate frustration_score (computed by TutorAgent.detect_frustration):
       - Severe (> 0.85): Recommend session end. Set end_reason = "fatigue".
       - High (0.7–0.85): Enter scaffolded_mode:
         a. Lower effective difficulty (filter to easier items)
         b. Provide more encouraging feedback
         c. Reduce mastery_streak_required to 3 temporarily
       - Moderate (0.5–0.7): Add encouraging message, continue normally.
    2. Log frustration episode to session metadata.
    3. If 3+ frustration episodes in one session → recommend break regardless.
    
    Returns:
        Partial state with scaffolded_mode flag, possibly session_complete.
    """
    from ...agents.tutor import TutorAgent
    
    tutor = TutorAgent()
    frustration = state["frustration_score"]
    episodes = len([f for f in state.get("frustration_history", []) if f > 0.7])
    
    # Count frustration episodes this session
    if episodes >= 3:
        # Too many frustration episodes — end session gently
        encouragement = await tutor.generate_encouragement(
            is_correct=False,
            attempt_count=state["attempt_count"],
            context={
                "reason": "multiple_frustration_episodes",
                "session_correct_rate": state["correct_count"] / max(1, state["questions_presented"]),
            },
        )
        return {
            "session_complete": True,
            "end_reason": "fatigue",
            "_encouragement_text": encouragement,
            "frustration_history": state.get("frustration_history", []) + [frustration],
        }
    
    if frustration > 0.85:
        # Severe — recommend break
        return {
            "session_complete": True,
            "end_reason": "fatigue",
            "_encouragement_text": "You've been working really hard! Let's take a break and come back fresh. You're making great progress!",
            "frustration_history": state.get("frustration_history", []) + [frustration],
        }
    
    elif frustration > 0.7:
        # High — enter scaffolded mode
        logger.info(f"Entering scaffolded mode for student {state['student_id']}, frustration={frustration:.2f}")
        return {
            "scaffolded_mode": True,
            "mastery_streak_required": 3,  # Temporarily lower
            "_encouragement_text": "Let's try some problems that build up to this step by step. You've got this!",
            "frustration_history": state.get("frustration_history", []) + [frustration],
        }
    
    else:
        # Moderate — continue with encouragement
        return {
            "_encouragement_text": "Keep going! Making mistakes is how we learn.",
            "frustration_history": state.get("frustration_history", []) + [frustration],
        }
```

---

**Node: `advance_skill_node`**

```python
# services/agent-engine/src/graph/nodes/advance_skill.py

from __future__ import annotations
import logging
from datetime import datetime, timezone
from ..state import SessionState

logger = logging.getLogger(__name__)


async def advance_skill_node(state: SessionState) -> dict:
    """Move to the next skill in the module's skill queue.
    
    Algorithm:
    1. Record the mastered skill and timestamp.
    2. Increment current_skill_index.
    3. If more skills remain in skill_queue:
       a. Set current_skill_code to next skill.
       b. Load BKT state for new skill (may already be in bkt_states).
       c. Add to skills_attempted.
       d. Reset scaffolded_mode to False.
    4. If no more skills → set _all_skills_done flag.
    5. Persist mastery event to long-term memory.
    
    Returns:
        Partial state with updated skill tracking.
    """
    from ...memory.long_term import LongTermMemoryStore
    
    ltm_store = LongTermMemoryStore()
    mastered_skill = state["current_skill_code"]
    
    # Record mastery
    mastered_list = list(state["skills_mastered_this_session"])
    mastered_list.append(mastered_skill)
    
    new_index = state["current_skill_index"] + 1
    skill_queue = state["skill_queue"]
    
    # Persist mastery timestamp
    try:
        await ltm_store.record_mastery(
            student_id=state["student_id"],
            skill_code=mastered_skill,
            mastered_at=datetime.now(timezone.utc).isoformat(),
        )
    except Exception as e:
        logger.warning(f"LTM mastery persistence failed (non-fatal): {e}")
    
    if new_index < len(skill_queue):
        next_skill = skill_queue[new_index]
        skills_attempted = list(state["skills_attempted"])
        if next_skill not in skills_attempted:
            skills_attempted.append(next_skill)
        
        return {
            "skills_mastered_this_session": mastered_list,
            "current_skill_index": new_index,
            "current_skill_code": next_skill,
            "skills_attempted": skills_attempted,
            "scaffolded_mode": False,
            "attempt_count": 0,
            "hints_used": 0,
            "_mastery_achieved": False,
            "_all_skills_done": False,
        }
    else:
        return {
            "skills_mastered_this_session": mastered_list,
            "_all_skills_done": True,
        }
```

---

**Node: `end_session_node`**

```python
# services/agent-engine/src/graph/nodes/end_session.py

from __future__ import annotations
import logging
from datetime import datetime, timezone
from ..state import SessionState

logger = logging.getLogger(__name__)


async def end_session_node(state: SessionState) -> dict:
    """Generate session summary, persist all state, emit completion events.
    
    Algorithm:
    1. Compute session summary statistics:
       - Total questions answered
       - Correct count and percentage
       - Skills attempted and mastered
       - Total time
       - Frustration episodes count
    2. Persist session record to practice_sessions table.
    3. Persist all session_questions and session_responses.
    4. Update long-term memory:
       - Update common_error_patterns with new errors
       - Update engagement_pattern with session length
       - Increment total_sessions_completed
       - Update cumulative_correct_rate
    5. Flush working memory from Redis.
    6. Set session_complete = True.
    
    Returns:
        Partial state with session_complete=True and summary data.
    """
    from ...services.session_persistence import SessionPersistenceService
    from ...memory.long_term import LongTermMemoryStore
    from ...memory.working import WorkingMemoryStore
    
    persistence = SessionPersistenceService()
    ltm_store = LongTermMemoryStore()
    wm_store = WorkingMemoryStore()
    
    end_reason = state.get("end_reason") or "complete"
    total_questions = state["questions_presented"]
    correct = state["correct_count"]
    correct_pct = correct / max(total_questions, 1)
    frustration_episodes = len([f for f in state.get("frustration_history", []) if f > 0.7])
    
    summary = {
        "session_id": state["session_id"],
        "student_id": state["student_id"],
        "questions_answered": total_questions,
        "correct_count": correct,
        "correct_percentage": round(correct_pct * 100, 1),
        "skills_attempted": state["skills_attempted"],
        "skills_mastered": state["skills_mastered_this_session"],
        "frustration_episodes": frustration_episodes,
        "end_reason": end_reason,
        "started_at": state["session_started_at"],
        "ended_at": datetime.now(timezone.utc).isoformat(),
    }
    
    try:
        # Persist session
        await persistence.save_session(
            session_id=state["session_id"],
            student_id=state["student_id"],
            plan_module_id=state["plan_module_id"],
            summary=summary,
            responses=state["session_responses"],
        )
        
        # Update LTM
        ltm = dict(state["long_term_memory"])
        
        # Update error patterns
        for resp in state["session_responses"]:
            if resp["error_type"]:
                skill = resp["skill_code"]
                errors = ltm.get("common_error_patterns", {})
                if skill not in errors:
                    errors[skill] = []
                errors[skill].append(resp["error_type"])
                # Keep last 20 errors per skill
                errors[skill] = errors[skill][-20:]
                ltm["common_error_patterns"] = errors
        
        ltm["total_sessions_completed"] = ltm.get("total_sessions_completed", 0) + 1
        
        # Rolling average correct rate
        prev_rate = ltm.get("cumulative_correct_rate", 0.5)
        prev_sessions = ltm.get("total_sessions_completed", 1)
        ltm["cumulative_correct_rate"] = (
            (prev_rate * (prev_sessions - 1) + correct_pct) / prev_sessions
        )
        
        await ltm_store.save(state["student_id"], ltm)
        
        # Flush working memory
        await wm_store.flush(state["session_id"])
        
    except Exception as e:
        logger.error(f"Session persistence failed: {e}", exc_info=True)
        # Don't fail the session end — data loss is bad but crashing is worse
    
    return {
        "session_complete": True,
        "end_reason": end_reason,
        "_session_summary": summary,
    }
```

---

**Node: `error_recovery_node`**

```python
# services/agent-engine/src/graph/nodes/error_recovery.py

from __future__ import annotations
import logging
from ..state import SessionState

logger = logging.getLogger(__name__)


async def error_recovery_node(state: SessionState) -> dict:
    """Handle errors gracefully — the session must never crash on the student.
    
    Algorithm:
    1. Log the error with full context.
    2. Check error_count against max_errors (default 3):
       a. If under limit:
          - Clear the error flag.
          - If error was in evaluate_response: mark answer as "needs_review",
            give benefit of the doubt (treat as correct for flow, flag for
            human review later).
          - If error was in generate_hint: use fallback generic hint.
          - If error was in select_question: try a random question from
            the current skill's item bank.
       b. If at or over limit:
          - End session gracefully with end_reason = "error".
          - Persist whatever state we have.
    3. Never expose internal error messages to the student.
    
    Returns:
        Partial state that either clears the error or ends the session.
    """
    error = state.get("error", "unknown_error")
    error_count = state.get("error_count", 0)
    max_errors = state.get("max_errors", 3)
    
    logger.error(
        f"Error recovery invoked: error={error}, count={error_count}/{max_errors}, "
        f"session={state['session_id']}, student={state['student_id']}"
    )
    
    if error_count >= max_errors:
        # Too many errors — end session gracefully
        return {
            "session_complete": True,
            "end_reason": "error",
            "error": None,
            "_encouragement_text": "We're having a bit of trouble right now. Let's save your progress and try again later!",
        }
    
    # Clear error and attempt recovery
    recovery_state: dict = {"error": None}
    
    if "evaluation_failed" in str(error):
        # Benefit of the doubt — treat as correct, flag for review
        logger.info("Recovery: treating failed evaluation as correct (flagged for review)")
        recovery_state["_last_is_correct"] = True
        recovery_state["_flagged_for_review"] = True
    
    elif "question_selection_failed" in str(error):
        # Try to continue with a simpler approach
        logger.info("Recovery: will retry question selection with relaxed constraints")
    
    elif "hint_generation_failed" in str(error):
        # Already handled in generate_hint_node with fallback
        logger.info("Recovery: hint fallback should have been applied")
    
    return recovery_state
```

#### 1.3.3 Graph Edges — Complete Conditional Routing Logic

```python
# services/agent-engine/src/graph/edges/routing.py

from __future__ import annotations
from typing import Literal
from ..state import SessionState


def route_after_initialize(state: SessionState) -> str:
    """After initialization, either select first question or end if error/complete."""
    if state.get("session_complete"):
        return "end_session"
    if state.get("error"):
        return "error_recovery"
    return "select_question"


def route_after_select_question(state: SessionState) -> str:
    """After question selection, present it or handle error."""
    if state.get("error"):
        return "error_recovery"
    return "present_question"


def route_after_evaluate(
    state: SessionState,
) -> Literal["update_bkt", "generate_hint", "handle_frustration", "error_recovery"]:
    """After evaluating a response, route based on correctness and frustration.
    
    Routing logic:
    1. If error occurred → error_recovery
    2. If correct → update_bkt (always update BKT on any response)
    3. If incorrect:
       a. Compute frustration score first.
       b. If frustration_score > 0.7 AND hints_used >= 2 → handle_frustration
       c. If hints_used < max_hints (3) → generate_hint
       d. If hints_used >= 3 (all hints exhausted) → update_bkt (move on)
    """
    if state.get("error"):
        return "error_recovery"
    
    is_correct = state.get("_last_is_correct", False)
    
    if is_correct:
        return "update_bkt"
    
    # Incorrect response
    hints_used = state.get("hints_used", 0)
    frustration = state.get("frustration_score", 0.0)
    
    # Compute frustration inline (fast — no LLM needed)
    frustration = _compute_frustration_fast(state)
    
    if frustration > 0.7 and hints_used >= 2:
        return "handle_frustration"
    
    if hints_used < 3:
        return "generate_hint"
    
    # All hints exhausted — update BKT with incorrect and move on
    return "update_bkt"


def route_after_bkt_update(state: SessionState) -> str:
    """After BKT update, check mastery."""
    return "check_mastery"


def route_after_mastery_check(state: SessionState) -> str:
    """After mastery check, advance skill or continue practicing."""
    if state.get("_mastery_achieved"):
        return "advance_skill"
    
    # Check session time limit (30 minutes max)
    from datetime import datetime, timezone
    started = state.get("session_started_at", "")
    if started:
        try:
            start_dt = datetime.fromisoformat(started)
            elapsed = (datetime.now(timezone.utc) - start_dt).total_seconds()
            if elapsed > 1800:  # 30 minutes
                return "end_session"
        except ValueError:
            pass
    
    # Check question count limit
    if state.get("questions_presented", 0) >= 30:
        return "end_session"
    
    return "select_question"


def route_after_hint(state: SessionState) -> str:
    """After generating a hint, re-present the question."""
    return "present_question"


def route_after_frustration(state: SessionState) -> str:
    """After frustration handling, either end session or continue with lower difficulty."""
    if state.get("session_complete"):
        return "end_session"
    return "select_question"


def route_after_advance(state: SessionState) -> str:
    """After advancing skill, continue with next skill or end."""
    if state.get("_all_skills_done"):
        return "end_session"
    return "select_question"


def route_after_error_recovery(state: SessionState) -> str:
    """After error recovery, either end or retry the last step."""
    if state.get("session_complete"):
        return "end_session"
    # Route back to select_question as a safe re-entry point
    return "select_question"


def _compute_frustration_fast(state: SessionState) -> float:
    """Fast frustration score computation (no LLM).
    
    Weights:
    - Consecutive wrong answers: 40%
    - Hints used per question: 30%
    - Response time spike: 20%
    - Overall correct rate: 10%
    
    Returns: float 0.0–1.0
    """
    responses = state.get("session_responses", [])
    if not responses:
        return 0.0
    
    # 1. Consecutive wrong (40%)
    consecutive_wrong = 0
    for r in reversed(responses):
        if not r["is_correct"]:
            consecutive_wrong += 1
        else:
            break
    wrong_score = min(consecutive_wrong / 5.0, 1.0)  # 5+ consecutive = max
    
    # 2. Hints per question (30%)
    recent = responses[-5:] if len(responses) >= 5 else responses
    avg_hints = sum(r["hint_count"] for r in recent) / len(recent)
    hint_score = min(avg_hints / 3.0, 1.0)  # 3 hints = max
    
    # 3. Response time spike (20%)
    if len(responses) >= 3:
        times = [r["time_to_answer_ms"] for r in responses]
        avg_time = sum(times) / len(times)
        last_time = times[-1]
        if avg_time > 0:
            spike_ratio = last_time / avg_time
            time_score = min(max(spike_ratio - 1.0, 0.0) / 2.0, 1.0)  # 3x avg = max
        else:
            time_score = 0.0
    else:
        time_score = 0.0
    
    # 4. Correct rate (10%)
    total = len(responses)
    correct = sum(1 for r in responses if r["is_correct"])
    rate = correct / total if total > 0 else 0.5
    rate_score = max(1.0 - rate * 2.0, 0.0)  # 0% correct = 1.0, 50%+ = 0.0
    
    frustration = (
        0.40 * wrong_score +
        0.30 * hint_score +
        0.20 * time_score +
        0.10 * rate_score
    )
    
    return round(min(max(frustration, 0.0), 1.0), 3)
```

#### 1.3.4 Graph Assembly

```python
# services/agent-engine/src/graph/graph.py

from __future__ import annotations
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from .state import SessionState
from .nodes.initialize import initialize_session_node
from .nodes.select_question import select_question_node
from .nodes.present_question import present_question_node
from .nodes.evaluate_response import evaluate_response_node
from .nodes.update_bkt import update_bkt_node
from .nodes.check_mastery import check_mastery_node
from .nodes.generate_hint import generate_hint_node
from .nodes.handle_frustration import handle_frustration_node
from .nodes.advance_skill import advance_skill_node
from .nodes.end_session import end_session_node
from .nodes.error_recovery import error_recovery_node
from .edges.routing import (
    route_after_initialize,
    route_after_select_question,
    route_after_evaluate,
    route_after_bkt_update,
    route_after_mastery_check,
    route_after_hint,
    route_after_frustration,
    route_after_advance,
    route_after_error_recovery,
)


def build_practice_graph() -> StateGraph:
    """Assemble the complete adaptive practice StateGraph.
    
    Returns a compiled graph ready to be used with a checkpointer.
    """
    graph = StateGraph(SessionState)
    
    # --- Add nodes ---
    graph.add_node("initialize_session", initialize_session_node)
    graph.add_node("select_question", select_question_node)
    graph.add_node("present_question", present_question_node)
    graph.add_node("evaluate_response", evaluate_response_node)
    graph.add_node("update_bkt", update_bkt_node)
    graph.add_node("check_mastery", check_mastery_node)
    graph.add_node("generate_hint", generate_hint_node)
    graph.add_node("handle_frustration", handle_frustration_node)
    graph.add_node("advance_skill", advance_skill_node)
    graph.add_node("end_session", end_session_node)
    graph.add_node("error_recovery", error_recovery_node)
    
    # --- Set entry point ---
    graph.set_entry_point("initialize_session")
    
    # --- Add edges ---
    
    # After initialize → conditional routing
    graph.add_conditional_edges(
        "initialize_session",
        route_after_initialize,
        {
            "select_question": "select_question",
            "end_session": "end_session",
            "error_recovery": "error_recovery",
        },
    )
    
    # After select_question → present or error
    graph.add_conditional_edges(
        "select_question",
        route_after_select_question,
        {
            "present_question": "present_question",
            "error_recovery": "error_recovery",
        },
    )
    
    # present_question is a "wait" node — graph pauses here.
    # The WebSocket handler resumes the graph when the student submits an answer.
    # For the graph definition, present_question → evaluate_response.
    graph.add_edge("present_question", "evaluate_response")
    
    # After evaluate → conditional routing
    graph.add_conditional_edges(
        "evaluate_response",
        route_after_evaluate,
        {
            "update_bkt": "update_bkt",
            "generate_hint": "generate_hint",
            "handle_frustration": "handle_frustration",
            "error_recovery": "error_recovery",
        },
    )
    
    # After BKT update → always check mastery
    graph.add_edge("update_bkt", "check_mastery")
    
    # After mastery check → conditional
    graph.add_conditional_edges(
        "check_mastery",
        route_after_mastery_check,
        {
            "advance_skill": "advance_skill",
            "select_question": "select_question",
            "end_session": "end_session",
        },
    )
    
    # After hint → re-present question
    graph.add_edge("generate_hint", "present_question")
    
    # After frustration → conditional
    graph.add_conditional_edges(
        "handle_frustration",
        route_after_frustration,
        {
            "end_session": "end_session",
            "select_question": "select_question",
        },
    )
    
    # After advance → conditional
    graph.add_conditional_edges(
        "advance_skill",
        route_after_advance,
        {
            "select_question": "select_question",
            "end_session": "end_session",
        },
    )
    
    # After error recovery → conditional
    graph.add_conditional_edges(
        "error_recovery",
        route_after_error_recovery,
        {
            "end_session": "end_session",
            "select_question": "select_question",
        },
    )
    
    # End session → terminal
    graph.add_edge("end_session", END)
    
    return graph


# Module-level compiled graph (singleton)
_compiled_graph = None


async def get_compiled_graph(db_uri: str):
    """Get or create the compiled graph with PostgreSQL checkpointer."""
    global _compiled_graph
    if _compiled_graph is None:
        checkpointer = AsyncPostgresSaver.from_conn_string(db_uri)
        await checkpointer.setup()
        graph = build_practice_graph()
        _compiled_graph = graph.compile(checkpointer=checkpointer)
    return _compiled_graph
```

#### 1.3.5 ASCII Flowchart

```
                          ┌──────────────────────┐
                          │   SESSION_START       │
                          │   (WebSocket msg)     │
                          └──────────┬───────────┘
                                     │
                                     ▼
                    ┌────────────────────────────────┐
                    │    initialize_session_node      │
                    │  Load LTM, BKT states, skills  │
                    └────────────────┬───────────────┘
                                     │
                        ┌────────────┼────────────┐
                        │ error?     │ complete?   │
                        ▼            │             ▼
                ┌──────────────┐     │    ┌──────────────┐
                │error_recovery│     │    │ end_session   │
                └──────┬───────┘     │    └──────┬────────┘
                       │             │           │
                       ▼             ▼           ▼
         ┌──────────────────────────────┐     ┌──────┐
    ┌───►│    select_question_node      │     │ END  │
    │    │  IRT Max Fisher Information  │     └──────┘
    │    └─────────────┬────────────────┘
    │                  │
    │                  ▼
    │    ┌──────────────────────────────┐
    │    │    present_question_node     │◄──────────────────────┐
    │    │  Send QUESTION via WS       │                       │
    │    └─────────────┬────────────────┘                       │
    │                  │                                        │
    │         [WAIT for SUBMIT_ANSWER via WS]                  │
    │                  │                                        │
    │                  ▼                                        │
    │    ┌──────────────────────────────┐                       │
    │    │   evaluate_response_node     │                       │
    │    │  o3-mini Assessment Agent    │                       │
    │    └─────────────┬────────────────┘                       │
    │                  │                                        │
    │     ┌────────────┼─────────────────────┐                 │
    │     │ correct    │ incorrect           │ error           │
    │     │            │                     │                 │
    │     │    ┌───────┴──────┐              │                 │
    │     │    │ hints < 3?   │              │                 │
    │     │    │ frust > 0.7? │              │                 │
    │     │    └──┬───┬───┬───┘              │                 │
    │     │       │   │   │                  ▼                 │
    │     │       │   │   │      ┌──────────────────┐          │
    │     │       │   │   │      │ error_recovery   │          │
    │     │       │   │   │      └────────┬─────────┘          │
    │     │       │   │   │               │                    │
    │     │       │   │   ▼               │                    │
    │     │       │   │ ┌───────────────────────┐              │
    │     │       │   │ │ handle_frustration    │              │
    │     │       │   │ │ ┌──────┐ ┌─────────┐ │              │
    │     │       │   │ │ │severe│ │ moderate│ │              │
    │     │       │   │ │ │→ END │ │→ select │ │              │
    │     │       │   │ └─┴──────┴─┴─────────┴─┘              │
    │     │       │   │                  │                     │
    │     │       │   ▼                  │                     │
    │     │       │ ┌───────────────────────────┐              │
    │     │       │ │  generate_hint_node       │──────────────┘
    │     │       │ │  Claude Sonnet 4.6 Tutor  │  (→ present_question)
    │     │       │ └───────────────────────────┘
    │     │       │
    │     ▼       ▼ (hints exhausted, also update BKT)
    │    ┌──────────────────────────────┐
    │    │     update_bkt_node          │
    │    │  Corbett & Anderson 1994     │
    │    └─────────────┬────────────────┘
    │                  │
    │                  ▼
    │    ┌──────────────────────────────┐
    │    │     check_mastery_node       │
    │    │  P(L) ≥ 0.95 AND 5 correct? │
    │    └─────────────┬────────────────┘
    │                  │
    │        ┌─────────┼──────────┐
    │        │ mastered │ not yet  │ time/count limit
    │        ▼         │          ▼
    │  ┌──────────┐    │   ┌──────────┐
    │  │ advance  │    │   │end_session│
    │  │  skill   │    │   └──────────┘
    │  └────┬─────┘    │
    │       │          │
    │  ┌────┴────┐     │
    │  │more     │     │
    │  │skills?  │     │
    │  ├─yes─────┤     │
    │  │         │     │
    └──┘    ┌────┘     │
            │no        │
            ▼          │
     ┌──────────┐      │
     │end_session│◄────┘
     └──────────┘
```

#### 1.3.6 Checkpointing Strategy

**Decision: PostgreSQL Checkpointer (`langgraph-checkpoint-postgres`)**

| Factor | PostgreSQL | Redis |
|--------|-----------|-------|
| Durability | Full ACID — survives process crash | In-memory, persistence is async (risk of data loss) |
| Auditability | Checkpoints queryable via SQL for debugging | Requires custom tooling |
| Performance | ~1ms get (with connection pooling) | ~0.3ms get |
| Practice session duration | 10–30 min — checkpoint frequency is low (per student message) | Overkill for this frequency |
| Existing infra | Already have RDS | Already have ElastiCache |
| LangGraph maturity | Official, production-optimized since v0.2 | Community-maintained, breaking changes in 0.1.0 |

**Verdict:** PostgreSQL checkpointer. The ~0.7ms latency difference is negligible for our use case (students submit answers every 15–60 seconds). ACID durability means a crashed ECS task can recover the exact session state. SQL queryability enables debugging and audit.

**Checkpoint Key Strategy:**

```python
# Each practice session gets its own LangGraph "thread"
# thread_id = session_id (UUID)
config = {
    "configurable": {
        "thread_id": state["session_id"],  # Unique per session
    }
}
```

The graph is invoked once at SESSION_START, then **resumed** from checkpoint on each subsequent SUBMIT_ANSWER. The present_question node is the natural "pause point" — after emitting a QUESTION message, the graph's execution completes and its state is checkpointed. When the student submits an answer, the WebSocket handler loads the checkpoint and invokes the graph starting from evaluate_response.

### 1.4 WebSocket Protocol Design

#### 1.4.1 Client → Server Messages

```typescript
// lib/types/websocket.ts

/** Messages sent from the React client to the FastAPI server. */
export type ClientMessage =
  | { type: 'SESSION_START'; studentId: string; skillCode: string; moduleId: string }
  | { type: 'SUBMIT_ANSWER'; questionId: string; answer: string; timeMs: number }
  | { type: 'REQUEST_HINT'; questionId: string }
  | { type: 'SKIP_QUESTION'; reason: 'dont_know' | 'technical_issue' }
  | { type: 'END_SESSION'; reason: 'complete' | 'fatigue' | 'user_quit' }
  | { type: 'HEARTBEAT' };
```

#### 1.4.2 Server → Client Messages

```typescript
// lib/types/websocket.ts

/** Messages sent from the FastAPI server to the React client. */
export type ServerMessage =
  | {
      type: 'SESSION_INITIALIZED';
      sessionId: string;
      moduleName: string;
      estimatedQuestions: number;
      currentSkill: { code: string; name: string };
    }
  | {
      type: 'QUESTION';
      question: ClientQuestion;
      attemptNumber: number;
      skillCode: string;
      progress: { questionsAnswered: number; correctCount: number; currentSkillMastery: number };
    }
  | {
      type: 'FEEDBACK';
      isCorrect: boolean;
      encouragement: string;
      errorType: string | null;
      showNextButton: boolean;
      showHintButton: boolean;
      hintsRemaining: number;
    }
  | {
      type: 'HINT';
      hintLevel: 1 | 2 | 3;
      hintText: string;
      hintsRemaining: number;
    }
  | {
      type: 'SKILL_MASTERED';
      skillCode: string;
      skillName: string;
      nextSkillCode: string | null;
      celebration: string;  // Encouraging message
    }
  | {
      type: 'FRUSTRATION_BREAK';
      message: string;
      suggestedBreakMinutes: number;
    }
  | {
      type: 'SESSION_SUMMARY';
      questionsAnswered: number;
      correctCount: number;
      correctPercentage: number;
      skillsAdvanced: string[];
      totalTimeMinutes: number;
      encouragement: string;
    }
  | {
      type: 'ERROR';
      code: string;
      message: string;
      recoverable: boolean;
    }
  | { type: 'HEARTBEAT_ACK'; timestamp: number };

/** Question payload safe for the client (no correct answer). */
export interface ClientQuestion {
  questionId: string;
  questionText: string;
  questionType: 'multiple_choice' | 'numeric' | 'free_response' | 'drag_drop';
  choices: { id: string; text: string }[] | null;
  domain: string;
  standardCode: string;
}
```

#### 1.4.3 Connection Lifecycle

**Authentication during WebSocket handshake:**

```python
# api/websocket/practice.py

from fastapi import WebSocket, WebSocketDisconnect, Query, HTTPException
from starlette.websockets import WebSocketState
import jwt


@app.websocket("/ws/practice")
async def practice_websocket(
    websocket: WebSocket,
    token: str = Query(...),  # JWT passed as query parameter: wss://api.padi.ai/ws/practice?token=xxx
):
    """
    Auth flow:
    1. Client connects with JWT in query string (WebSocket API doesn't support
       custom headers in browser, so query param or cookie is required).
    2. Server validates JWT before calling websocket.accept().
    3. If invalid → close with 4001 (Unauthorized).
    4. If valid → accept connection, extract student_id from JWT claims.
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        student_id = payload["sub"]
        role = payload.get("role", "student")
        if role != "student":
            await websocket.close(code=4003, reason="Students only")
            return
    except jwt.InvalidTokenError:
        await websocket.close(code=4001, reason="Invalid token")
        return
    
    await websocket.accept()
    
    # Register connection in Redis for monitoring
    await redis.set(f"ws:conn:{student_id}", websocket.client.host, ex=3600)
    
    try:
        while True:
            raw = await websocket.receive_json()
            msg_type = raw.get("type")
            
            if msg_type == "HEARTBEAT":
                await websocket.send_json({"type": "HEARTBEAT_ACK", "timestamp": time.time()})
                continue
            
            if msg_type == "SESSION_START":
                await handle_session_start(websocket, student_id, raw)
            elif msg_type == "SUBMIT_ANSWER":
                await handle_submit_answer(websocket, student_id, raw)
            elif msg_type == "REQUEST_HINT":
                await handle_request_hint(websocket, student_id, raw)
            elif msg_type == "SKIP_QUESTION":
                await handle_skip(websocket, student_id, raw)
            elif msg_type == "END_SESSION":
                await handle_end_session(websocket, student_id, raw)
                break
            else:
                await websocket.send_json({
                    "type": "ERROR",
                    "code": "UNKNOWN_MESSAGE",
                    "message": f"Unknown message type: {msg_type}",
                    "recoverable": True,
                })
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: student={student_id}")
        await handle_disconnect(student_id)
    finally:
        await redis.delete(f"ws:conn:{student_id}")
```

**Reconnection Logic (Client-Side):**

```typescript
// hooks/usePracticeWebSocket.ts

const RECONNECT_DELAYS = [1000, 2000, 4000, 8000, 15000]; // Exponential backoff, max 15s
const MAX_RECONNECT_ATTEMPTS = 5;

export function usePracticeWebSocket(sessionId: string | null) {
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [connectionState, setConnectionState] = useState<'connecting' | 'connected' | 'disconnected' | 'reconnecting'>('disconnected');
  const reconnectAttempt = useRef(0);
  const heartbeatInterval = useRef<NodeJS.Timeout>();

  const connect = useCallback(() => {
    const token = getAuthToken(); // From auth context
    const socket = new WebSocket(
      `${process.env.NEXT_PUBLIC_WS_URL}/ws/practice?token=${token}`
    );

    socket.onopen = () => {
      setConnectionState('connected');
      reconnectAttempt.current = 0;
      
      // Start heartbeat every 30s
      heartbeatInterval.current = setInterval(() => {
        if (socket.readyState === WebSocket.OPEN) {
          socket.send(JSON.stringify({ type: 'HEARTBEAT' }));
        }
      }, 30_000);
      
      // If reconnecting with existing session, server will restore from checkpoint
      if (sessionId) {
        socket.send(JSON.stringify({
          type: 'SESSION_START',
          studentId: getCurrentStudentId(),
          moduleId: getCurrentModuleId(),
          skillCode: getCurrentSkillCode(),
          resumeSessionId: sessionId,  // Signal reconnection
        }));
      }
    };

    socket.onclose = (event) => {
      clearInterval(heartbeatInterval.current);
      
      if (event.code === 4001) {
        // Auth failure — don't retry, redirect to login
        setConnectionState('disconnected');
        redirectToLogin();
        return;
      }
      
      if (reconnectAttempt.current < MAX_RECONNECT_ATTEMPTS) {
        setConnectionState('reconnecting');
        const delay = RECONNECT_DELAYS[
          Math.min(reconnectAttempt.current, RECONNECT_DELAYS.length - 1)
        ];
        setTimeout(() => {
          reconnectAttempt.current++;
          connect();
        }, delay);
      } else {
        setConnectionState('disconnected');
        // Show "connection lost" UI with manual retry button
      }
    };

    setWs(socket);
  }, [sessionId]);
  
  // ...
}
```

**Session Recovery After Network Interruption:**

When a student's WebSocket connection drops and reconnects:

1. Client sends `SESSION_START` with `resumeSessionId` field.
2. Server detects resume request, loads checkpoint from PostgreSQL for that session_id.
3. If checkpoint exists and session is not expired (< 1 hour old):
   - Restore `SessionState` from checkpoint.
   - Re-send the last `QUESTION` or `FEEDBACK` message.
   - Continue graph from the checkpointed state.
4. If checkpoint is stale or missing:
   - Start a fresh session, preserving BKT states from the DB.
   - Inform client: "We saved your progress! Starting from where you left off."

---

## 2. Detailed System Design

### 2.1 Database Schema (Complete DDL)

```sql
-- ============================================================================
-- Stage 3: Practice Session Tables
-- ============================================================================

-- Practice session container
CREATE TABLE practice_sessions (
    session_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id      UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    plan_module_id  UUID NOT NULL REFERENCES learning_plan_modules(id) ON DELETE CASCADE,
    started_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ended_at        TIMESTAMPTZ,
    status          VARCHAR(20) NOT NULL DEFAULT 'active'
                    CHECK (status IN ('active', 'completed', 'abandoned', 'error')),
    total_questions INT NOT NULL DEFAULT 0,
    correct_count   INT NOT NULL DEFAULT 0,
    frustration_episodes INT NOT NULL DEFAULT 0,
    scaffolded_mode_activated BOOLEAN NOT NULL DEFAULT FALSE,
    end_reason      VARCHAR(30) CHECK (end_reason IN (
                        'mastery_complete', 'fatigue', 'time_limit', 
                        'question_limit', 'error', 'user_quit'
                    )),
    summary         JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_practice_sessions_student ON practice_sessions(student_id);
CREATE INDEX idx_practice_sessions_student_started ON practice_sessions(student_id, started_at DESC);
CREATE INDEX idx_practice_sessions_status ON practice_sessions(status) WHERE status = 'active';
CREATE INDEX idx_practice_sessions_module ON practice_sessions(plan_module_id);


-- Individual question presentations within a session
CREATE TABLE session_questions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id      UUID NOT NULL REFERENCES practice_sessions(session_id) ON DELETE CASCADE,
    question_id     UUID NOT NULL REFERENCES questions(id),
    skill_code      VARCHAR(20) NOT NULL,
    presented_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    answered_at     TIMESTAMPTZ,
    attempt_number  INT NOT NULL DEFAULT 1 CHECK (attempt_number BETWEEN 1 AND 10),
    is_correct      BOOLEAN,
    time_to_answer_ms INT CHECK (time_to_answer_ms >= 0),
    difficulty_used FLOAT NOT NULL,
    irt_info_value  FLOAT NOT NULL DEFAULT 0.0,
    hints_used      INT NOT NULL DEFAULT 0 CHECK (hints_used BETWEEN 0 AND 3),
    skipped         BOOLEAN NOT NULL DEFAULT FALSE,
    flagged_for_review BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_session_questions_session ON session_questions(session_id);
CREATE INDEX idx_session_questions_question ON session_questions(question_id);
CREATE INDEX idx_session_questions_skill ON session_questions(skill_code);
CREATE INDEX idx_session_questions_flagged ON session_questions(flagged_for_review)
    WHERE flagged_for_review = TRUE;


-- Individual student responses (multiple attempts per question)
CREATE TABLE session_responses (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_question_id UUID NOT NULL REFERENCES session_questions(id) ON DELETE CASCADE,
    answer_text         TEXT NOT NULL,
    submitted_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    is_correct          BOOLEAN NOT NULL,
    error_type          VARCHAR(20) CHECK (error_type IN (
                            'computational', 'conceptual', 'procedural', 'careless', NULL
                        )),
    confidence_score    FLOAT CHECK (confidence_score BETWEEN 0.0 AND 1.0),
    model_evaluated     BOOLEAN NOT NULL DEFAULT FALSE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_session_responses_question ON session_responses(session_question_id);
CREATE INDEX idx_session_responses_error ON session_responses(error_type)
    WHERE error_type IS NOT NULL;


-- Hint interactions
CREATE TABLE hint_interactions (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_question_id UUID NOT NULL REFERENCES session_questions(id) ON DELETE CASCADE,
    hint_level          INT NOT NULL CHECK (hint_level BETWEEN 1 AND 3),
    requested_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    hint_text           TEXT NOT NULL,
    hint_source         VARCHAR(20) NOT NULL DEFAULT 'generated'
                        CHECK (hint_source IN ('generated', 'pre_authored', 'fallback')),
    model_used          VARCHAR(50),
    input_tokens        INT,
    output_tokens       INT,
    latency_ms          INT CHECK (latency_ms >= 0),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_hint_interactions_question ON hint_interactions(session_question_id);


-- BKT state history (append-only audit trail)
CREATE TABLE bkt_state_history (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id  UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    skill_code  VARCHAR(20) NOT NULL,
    p_mastered  FLOAT NOT NULL CHECK (p_mastered BETWEEN 0.0 AND 1.0),
    p_transit   FLOAT NOT NULL CHECK (p_transit BETWEEN 0.0 AND 1.0),
    p_slip      FLOAT NOT NULL CHECK (p_slip BETWEEN 0.0 AND 1.0),
    p_guess     FLOAT NOT NULL CHECK (p_guess BETWEEN 0.0 AND 1.0),
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    session_id  UUID REFERENCES practice_sessions(session_id) ON DELETE SET NULL,
    trigger     VARCHAR(20) NOT NULL DEFAULT 'response'
                CHECK (trigger IN ('response', 'session_start', 'manual_reset', 'calibration'))
);

CREATE INDEX idx_bkt_state_student_skill ON bkt_state_history(student_id, skill_code, recorded_at DESC);
CREATE INDEX idx_bkt_state_session ON bkt_state_history(session_id);

-- Materialized view for current BKT state (latest per student-skill pair)
CREATE MATERIALIZED VIEW bkt_current_states AS
SELECT DISTINCT ON (student_id, skill_code)
    student_id,
    skill_code,
    p_mastered,
    p_transit,
    p_slip,
    p_guess,
    recorded_at
FROM bkt_state_history
ORDER BY student_id, skill_code, recorded_at DESC;

CREATE UNIQUE INDEX idx_bkt_current_states_pk ON bkt_current_states(student_id, skill_code);


-- Student long-term memory profile
CREATE TABLE student_long_term_memory (
    student_id                  UUID PRIMARY KEY REFERENCES students(id) ON DELETE CASCADE,
    preferred_explanation_style  VARCHAR(20) NOT NULL DEFAULT 'step_by_step'
                                CHECK (preferred_explanation_style IN (
                                    'visual', 'verbal', 'example_based', 'step_by_step'
                                )),
    common_error_patterns       JSONB NOT NULL DEFAULT '{}',
    engagement_pattern          JSONB NOT NULL DEFAULT '{}',
    mastery_timestamps          JSONB NOT NULL DEFAULT '{}',
    total_sessions_completed    INT NOT NULL DEFAULT 0,
    cumulative_correct_rate     FLOAT NOT NULL DEFAULT 0.5
                                CHECK (cumulative_correct_rate BETWEEN 0.0 AND 1.0),
    updated_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- Agent interaction logs (full audit trail of every LLM call)
CREATE TABLE agent_interaction_logs (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id              UUID NOT NULL REFERENCES practice_sessions(session_id) ON DELETE CASCADE,
    node_name               VARCHAR(50) NOT NULL,
    agent_name              VARCHAR(50) NOT NULL,
    model_used              VARCHAR(50) NOT NULL,
    prompt_template_version VARCHAR(20),
    input_tokens            INT NOT NULL CHECK (input_tokens >= 0),
    output_tokens           INT NOT NULL CHECK (output_tokens >= 0),
    latency_ms              INT NOT NULL CHECK (latency_ms >= 0),
    structured_output_valid BOOLEAN NOT NULL DEFAULT TRUE,
    error_message           TEXT,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_agent_logs_session ON agent_interaction_logs(session_id);
CREATE INDEX idx_agent_logs_model ON agent_interaction_logs(model_used);
CREATE INDEX idx_agent_logs_created ON agent_interaction_logs(created_at);
CREATE INDEX idx_agent_logs_errors ON agent_interaction_logs(session_id)
    WHERE error_message IS NOT NULL;


-- LangGraph checkpoint tables (managed by langgraph-checkpoint-postgres)
-- These are created automatically by AsyncPostgresSaver.setup()
-- Documented here for awareness:
-- - checkpoints: thread_id, checkpoint_id, parent_id, checkpoint JSONB, metadata JSONB
-- - checkpoint_writes: thread_id, checkpoint_id, task_id, idx, channel, type, blob BYTEA
-- - checkpoint_blobs: thread_id, checkpoint_ns, channel, version, type, blob BYTEA
```

### 2.2 Service Layer Design

```python
# ============================================================================
# Stage 3 — Complete Python Class Interfaces
# ============================================================================

# --- services/practice_session.py ---

from uuid import UUID
from datetime import datetime
from typing import AsyncIterator
from pydantic import BaseModel


class EndReason(str, Enum):
    MASTERY_COMPLETE = "mastery_complete"
    FATIGUE = "fatigue"
    TIME_LIMIT = "time_limit"
    QUESTION_LIMIT = "question_limit"
    ERROR = "error"
    USER_QUIT = "user_quit"


class SessionSummary(BaseModel):
    session_id: UUID
    student_id: UUID
    questions_answered: int
    correct_count: int
    correct_percentage: float
    skills_attempted: list[str]
    skills_mastered: list[str]
    frustration_episodes: int
    end_reason: str
    started_at: datetime
    ended_at: datetime
    total_time_minutes: float


class PracticeSessionService:
    """Orchestrates practice session lifecycle.
    
    This service is the bridge between the WebSocket endpoint and the
    LangGraph agent engine. It handles session creation, message routing,
    and session teardown.
    """
    
    async def start_session(
        self, student_id: UUID, module_id: UUID
    ) -> tuple[str, list[dict]]:
        """Create a new practice session and initialize the agent graph.
        
        1. Create practice_sessions DB record with status='active'.
        2. Initialize SessionState with student_id, module_id.
        3. Invoke the LangGraph graph from entry point.
        4. Graph runs initialize_session → select_question → present_question.
        5. Collect all ServerMessages emitted during this initial run.
        6. Return (session_id, list_of_server_messages).
        """
        ...
    
    async def process_message(
        self, session_id: UUID, message: dict
    ) -> list[dict]:
        """Process an incoming WebSocket message by resuming the graph.
        
        1. Load checkpoint for session_id from PostgreSQL.
        2. Inject the message data into state (e.g., _pending_answer).
        3. Resume graph execution from the checkpointed node.
        4. Collect all ServerMessages emitted during this run.
        5. Return list of server messages to send to client.
        """
        ...
    
    async def end_session(
        self, session_id: UUID, reason: EndReason
    ) -> SessionSummary:
        """Force-end a session (user-initiated or error).
        
        1. Load checkpoint, inject end_reason into state.
        2. Route to end_session node.
        3. Return summary.
        """
        ...
    
    async def get_session_summary(self, session_id: UUID) -> SessionSummary:
        """Retrieve summary for a completed session."""
        ...


class AgentOrchestrator:
    """LangGraph graph runner with streaming support.
    
    Wraps the compiled StateGraph to provide async streaming of
    ServerMessages as the graph executes through nodes.
    """
    
    def __init__(
        self,
        graph,  # CompiledGraph
        checkpointer,  # AsyncPostgresSaver
    ):
        self.graph = graph
        self.checkpointer = checkpointer
    
    async def invoke(
        self, state: dict, config: dict
    ) -> dict:
        """Run graph to completion, return final state."""
        return await self.graph.ainvoke(state, config)
    
    async def stream(
        self, state: dict, config: dict
    ) -> AsyncIterator[dict]:
        """Stream graph execution, yielding ServerMessages at each node.
        
        Uses LangGraph's astream_events to capture node outputs and
        convert them to WebSocket ServerMessage dicts.
        """
        async for event in self.graph.astream(state, config, stream_mode="values"):
            messages = self._extract_server_messages(event)
            for msg in messages:
                yield msg
    
    def _extract_server_messages(self, state_snapshot: dict) -> list[dict]:
        """Convert graph state updates into ServerMessage dicts.
        
        Looks for underscore-prefixed transient keys in state:
        - _hint_text, _hint_level → HINT message
        - _session_summary → SESSION_SUMMARY message
        - _encouragement_text → part of FEEDBACK message
        - _mastery_achieved → SKILL_MASTERED message
        - current_question changed → QUESTION message
        """
        ...


class TutorAgent:
    """Claude Sonnet 4.6-powered Socratic tutor.
    
    Responsible for:
    - Generating level-appropriate hints (Socratic method)
    - Generating encouraging feedback messages
    - Detecting student frustration from behavioral signals
    
    All LLM calls use structured output (Pydantic models) to ensure
    predictable, parseable responses. Every call is logged to
    agent_interaction_logs.
    """
    
    def __init__(self):
        self.model = "claude-sonnet-4-6-20260401"  # Pin version
        self.prompt_registry = PromptRegistry()
    
    async def generate_hint(
        self,
        question: dict,
        hint_level: int,  # 1, 2, or 3
        student_answer: str,
        context: dict,
    ) -> HintResponse:
        """Generate a Socratic hint at the specified level.
        
        Uses the tutor_hint_v1.0.jinja2 prompt template.
        
        Structured output schema:
        class HintResponse(BaseModel):
            hint_text: str = Field(max_length=500)
            hint_strategy: str  # "nudge", "guided", "worked_example"
            contains_answer: bool  # Self-check — must be False
        
        Args:
            question: Full question payload (correct answer included for context).
            hint_level: 1=nudge, 2=guided, 3=worked example.
            student_answer: What the student wrote (for targeted feedback).
            context: LTM preferences, recent interactions, grade level.
        
        Returns:
            HintResponse with validated hint text.
        """
        ...
    
    async def generate_encouragement(
        self,
        is_correct: bool,
        attempt_count: int,
        context: dict,
    ) -> str:
        """Generate age-appropriate encouraging feedback.
        
        Uses the tutor_encouragement_v1.0.jinja2 prompt template.
        
        Returns a short (< 50 words) encouraging message appropriate
        for the student's grade level and emotional state.
        """
        ...
    
    def detect_frustration(self, state: dict) -> float:
        """Compute frustration score from behavioral signals.
        
        This is a deterministic computation (no LLM), computed inline
        for speed. See _compute_frustration_fast() in routing.py.
        
        Weights:
        - Consecutive wrong answers: 40%
        - Hints used per question: 30%
        - Response time spike: 20%
        - Session correct rate: 10%
        
        Returns:
            Float 0.0–1.0 representing frustration level.
        """
        ...


class BKTService:
    """Bayesian Knowledge Tracing service.
    
    Manages BKT parameter storage, real-time state updates, and
    mastery determination. Uses pre-calibrated parameters from pyBKT
    fitting (run offline during content authoring).
    """
    
    async def load_current_states(
        self, student_id: str, skill_codes: list[str]
    ) -> dict[str, float]:
        """Load current P(mastered) for each skill from DB.
        
        Uses the bkt_current_states materialized view for efficiency.
        Falls back to p_prior from skill_bkt_params for untracked skills.
        """
        ...
    
    async def load_params(
        self, skill_codes: list[str]
    ) -> dict[str, dict]:
        """Load BKT parameters (p_transit, p_slip, p_guess) for skills.
        
        Parameters are pre-calibrated via pyBKT offline fitting and stored
        in the skill_bkt_params table.
        """
        ...
    
    def update(
        self,
        p_mastered: float,
        is_correct: bool,
        p_transit: float,
        p_slip: float,
        p_guess: float,
    ) -> float:
        """Single-step BKT update. See §3.1 for full implementation."""
        ...
    
    async def persist_state_snapshot(
        self,
        student_id: str,
        skill_code: str,
        p_mastered: float,
        p_transit: float,
        p_slip: float,
        p_guess: float,
        session_id: str,
    ) -> None:
        """Append to bkt_state_history for audit trail."""
        ...


class IRTService:
    """Item Response Theory service for question selection.
    
    Provides Fisher Information computation and Maximum Fisher
    Information item selection. Used by select_question_node.
    """
    
    def compute_probability(
        self, theta: float, a: float, b: float, c: float
    ) -> float:
        """3PL IRT probability of correct response."""
        ...
    
    def compute_information(
        self, theta: float, a: float, b: float, c: float
    ) -> float:
        """Fisher Information at theta for a 3PL item."""
        ...
    
    def select_best_item(
        self,
        theta: float,
        items: list[dict],
        excluded_ids: set[str],
    ) -> dict:
        """Select item maximizing Fisher Information at theta.
        
        Applies exposure control and context diversity.
        """
        ...
```

### 2.3 LangGraph Implementation Guide

#### 2.3.1 Project Structure

```
services/agent-engine/
├── src/
│   ├── __init__.py
│   ├── config.py                   # Settings, env vars, model configs
│   ├── graph/
│   │   ├── __init__.py
│   │   ├── state.py                # SessionState TypedDict
│   │   ├── nodes/
│   │   │   ├── __init__.py
│   │   │   ├── initialize.py       # initialize_session_node
│   │   │   ├── select_question.py  # select_question_node
│   │   │   ├── present_question.py # present_question_node
│   │   │   ├── evaluate_response.py# evaluate_response_node
│   │   │   ├── update_bkt.py       # update_bkt_node
│   │   │   ├── check_mastery.py    # check_mastery_node
│   │   │   ├── generate_hint.py    # generate_hint_node
│   │   │   ├── handle_frustration.py# handle_frustration_node
│   │   │   ├── advance_skill.py    # advance_skill_node
│   │   │   ├── end_session.py      # end_session_node
│   │   │   └── error_recovery.py   # error_recovery_node
│   │   ├── edges/
│   │   │   ├── __init__.py
│   │   │   └── routing.py          # All conditional edge functions
│   │   └── graph.py                # StateGraph assembly + compilation
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base.py                 # BaseAgent with logging, retry, metrics
│   │   ├── tutor.py                # TutorAgent (Claude Sonnet 4.6)
│   │   ├── assessment.py           # AssessmentAgent (o3-mini)
│   │   └── question_gen.py         # QuestionGeneratorAgent (o3-mini)
│   ├── memory/
│   │   ├── __init__.py
│   │   ├── long_term.py            # LTM CRUD (PostgreSQL)
│   │   └── working.py              # Working memory (Redis)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── bkt_service.py          # BKT computation + persistence
│   │   ├── irt_service.py          # IRT probability + information
│   │   ├── question_bank.py        # Question retrieval + filtering
│   │   ├── session_persistence.py  # Session/response DB persistence
│   │   ├── plan_service.py         # Learning plan / module queries
│   │   └── sqs_client.py           # SQS queue client
│   └── prompts/
│       ├── tutor_hint_v1.0.jinja2
│       ├── tutor_hint_v1.1.jinja2  # Future versions coexist
│       ├── tutor_encouragement_v1.0.jinja2
│       ├── assessment_evaluate_v1.0.jinja2
│       └── assessment_classify_error_v1.0.jinja2
├── tests/
│   ├── unit/
│   │   ├── test_bkt_update.py
│   │   ├── test_frustration_score.py
│   │   ├── test_irt_selection.py
│   │   ├── test_nodes/
│   │   │   ├── test_initialize.py
│   │   │   ├── test_evaluate_response.py
│   │   │   └── test_routing.py
│   │   └── test_agents/
│   │       ├── test_tutor_agent.py
│   │       └── test_assessment_agent.py
│   ├── integration/
│   │   ├── test_graph_flow.py
│   │   ├── test_websocket.py
│   │   └── test_session_persistence.py
│   └── contract/
│       ├── test_claude_hint_contract.py
│       └── test_o3mini_eval_contract.py
├── pyproject.toml
└── Dockerfile
```

#### 2.3.2 WebSocket ↔ LangGraph Integration

```python
# api/websocket/handlers.py

from uuid import uuid4
from graph.graph import get_compiled_graph
from graph.state import SessionState


async def handle_session_start(websocket, student_id: str, msg: dict):
    """Initialize a practice session and stream the first question."""
    session_id = str(uuid4())
    module_id = msg["moduleId"]
    skill_code = msg["skillCode"]
    
    graph = await get_compiled_graph(settings.DATABASE_URL)
    
    # Create initial state
    initial_state = {
        "session_id": session_id,
        "student_id": student_id,
        "plan_module_id": module_id,
        "current_skill_code": skill_code,
        "current_question": None,
        "attempt_count": 0,
        "max_attempts": 3,
        "hints_used": 0,
        "session_responses": [],
        "questions_presented": 0,
        "correct_count": 0,
        "skills_attempted": [],
        "skills_mastered_this_session": [],
        "bkt_states": {},
        "bkt_params": {},
        "mastery_threshold": 0.95,
        "mastery_streak_required": 5,
        "frustration_score": 0.0,
        "frustration_history": [],
        "scaffolded_mode": False,
        "working_memory": {"recent_interactions": [], "current_streak": 0, "session_error_types": [], "time_pressure_detected": False},
        "long_term_memory": {},
        "skill_queue": [],
        "current_skill_index": 0,
        "theta_estimate": 0.0,
        "theta_sem": 1.0,
        "session_started_at": "",
        "session_complete": False,
        "end_reason": None,
        "error": None,
        "error_count": 0,
        "max_errors": 3,
    }
    
    config = {"configurable": {"thread_id": session_id}}
    
    # Stream graph execution until it reaches present_question (wait point)
    server_messages = []
    
    async for event in graph.astream(initial_state, config, stream_mode="values"):
        msgs = extract_server_messages(event, session_id)
        server_messages.extend(msgs)
    
    # Store session_id mapping in Redis for this WebSocket connection
    await redis.set(f"ws:session:{student_id}", session_id, ex=7200)
    
    # Send all collected messages to client
    for msg in server_messages:
        await websocket.send_json(msg)


async def handle_submit_answer(websocket, student_id: str, msg: dict):
    """Resume graph from checkpoint with the student's answer."""
    session_id = await redis.get(f"ws:session:{student_id}")
    if not session_id:
        await websocket.send_json({
            "type": "ERROR", "code": "NO_SESSION", 
            "message": "No active session", "recoverable": False,
        })
        return
    
    graph = await get_compiled_graph(settings.DATABASE_URL)
    config = {"configurable": {"thread_id": session_id}}
    
    # Get current state from checkpoint
    checkpoint = await graph.aget_state(config)
    current_state = checkpoint.values
    
    # Inject the student's answer into state
    state_update = {
        "_pending_answer": msg["answer"],
        "_pending_time_ms": msg.get("timeMs", 0),
    }
    
    # Update state and resume from evaluate_response
    await graph.aupdate_state(config, state_update)
    
    # Stream execution from evaluate_response onward
    server_messages = []
    async for event in graph.astream(None, config, stream_mode="values"):
        msgs = extract_server_messages(event, session_id)
        server_messages.extend(msgs)
    
    for msg_out in server_messages:
        await websocket.send_json(msg_out)


def extract_server_messages(state: dict, session_id: str) -> list[dict]:
    """Convert graph state snapshot to WebSocket ServerMessage dicts."""
    messages = []
    
    # SESSION_INITIALIZED
    if state.get("session_started_at") and not state.get("_init_sent"):
        messages.append({
            "type": "SESSION_INITIALIZED",
            "sessionId": session_id,
            "moduleName": state.get("_module_name", "Practice"),
            "estimatedQuestions": len(state.get("skill_queue", [])) * 6,
            "currentSkill": {
                "code": state.get("current_skill_code", ""),
                "name": state.get("_current_skill_name", ""),
            },
        })
    
    # QUESTION
    if state.get("current_question") and state.get("attempt_count") == 1:
        q = state["current_question"]
        messages.append({
            "type": "QUESTION",
            "question": {
                "questionId": q["question_id"],
                "questionText": q["question_text"],
                "questionType": q["question_type"],
                "choices": q.get("choices"),
                "domain": q["domain"],
                "standardCode": q["standard_code"],
            },
            "attemptNumber": state["attempt_count"],
            "skillCode": state["current_skill_code"],
            "progress": {
                "questionsAnswered": state["questions_presented"],
                "correctCount": state["correct_count"],
                "currentSkillMastery": round(
                    state["bkt_states"].get(state["current_skill_code"], 0.0) * 100
                ),
            },
        })
    
    # FEEDBACK (after evaluation)
    if "_last_is_correct" in state:
        encouragement = state.get("_encouragement_text", "")
        if not encouragement:
            encouragement = "Great job!" if state["_last_is_correct"] else "Keep trying!"
        
        messages.append({
            "type": "FEEDBACK",
            "isCorrect": state["_last_is_correct"],
            "encouragement": encouragement,
            "errorType": state.get("_last_error_type"),
            "showNextButton": state["_last_is_correct"],
            "showHintButton": not state["_last_is_correct"] and state.get("hints_used", 0) < 3,
            "hintsRemaining": 3 - state.get("hints_used", 0),
        })
    
    # HINT
    if "_hint_text" in state and state["_hint_text"]:
        messages.append({
            "type": "HINT",
            "hintLevel": state["_hint_level"],
            "hintText": state["_hint_text"],
            "hintsRemaining": 3 - state.get("hints_used", 0),
        })
    
    # SKILL_MASTERED
    if state.get("_mastery_achieved"):
        messages.append({
            "type": "SKILL_MASTERED",
            "skillCode": state["current_skill_code"],
            "skillName": state.get("_current_skill_name", state["current_skill_code"]),
            "nextSkillCode": state["skill_queue"][state["current_skill_index"] + 1]
                if state["current_skill_index"] + 1 < len(state["skill_queue"]) else None,
            "celebration": "Amazing work! You've mastered this skill! 🌟",
        })
    
    # SESSION_SUMMARY
    if state.get("session_complete") and "_session_summary" in state:
        s = state["_session_summary"]
        messages.append({
            "type": "SESSION_SUMMARY",
            "questionsAnswered": s["questions_answered"],
            "correctCount": s["correct_count"],
            "correctPercentage": s["correct_percentage"],
            "skillsAdvanced": s["skills_mastered"],
            "totalTimeMinutes": round(s.get("total_time_minutes", 0), 1),
            "encouragement": "Fantastic practice session! Every question makes you stronger.",
        })
    
    # ERROR
    if state.get("error"):
        messages.append({
            "type": "ERROR",
            "code": state["error"].split(":")[0] if ":" in state["error"] else "UNKNOWN",
            "message": "Something went wrong. We're saving your progress.",
            "recoverable": state.get("error_count", 0) < state.get("max_errors", 3),
        })
    
    return messages
```

#### 2.3.3 Error Handling in Agents

```python
# agents/base.py

from __future__ import annotations
import logging
import time
from typing import TypeVar, Type
from pydantic import BaseModel
from anthropic import AsyncAnthropic, APIError, RateLimitError
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)


class BaseAgent:
    """Base class for all LLM-powered agents.
    
    Provides:
    - Automatic retry with exponential backoff (2 retries)
    - Structured output parsing and validation
    - Latency + token logging to agent_interaction_logs
    - Graceful fallback on failure
    """
    
    MAX_RETRIES = 2
    RETRY_DELAYS = [1.0, 3.0]  # seconds
    
    def __init__(self, session_id: str | None = None):
        self.session_id = session_id
        self.anthropic = AsyncAnthropic()
        self.openai = AsyncOpenAI()
    
    async def call_claude(
        self,
        prompt: str,
        system: str,
        response_model: Type[T],
        node_name: str,
        model: str = "claude-sonnet-4-6-20260401",
        max_tokens: int = 1024,
        temperature: float = 0.3,
    ) -> T:
        """Call Claude with structured output, retry, and logging.
        
        Retry policy:
        - Retry on RateLimitError and 5xx APIError.
        - Do NOT retry on 4xx (bad request) — those are bugs.
        - After MAX_RETRIES exhausted, raise to caller.
        """
        last_error = None
        
        for attempt in range(self.MAX_RETRIES + 1):
            start_ms = time.monotonic()
            try:
                response = await self.anthropic.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system=system,
                    messages=[{"role": "user", "content": prompt}],
                )
                
                latency_ms = int((time.monotonic() - start_ms) * 1000)
                
                # Parse structured output
                raw_text = response.content[0].text
                parsed = response_model.model_validate_json(raw_text)
                
                # Log success
                await self._log_interaction(
                    node_name=node_name,
                    agent_name=self.__class__.__name__,
                    model_used=model,
                    input_tokens=response.usage.input_tokens,
                    output_tokens=response.usage.output_tokens,
                    latency_ms=latency_ms,
                    structured_output_valid=True,
                )
                
                return parsed
            
            except RateLimitError as e:
                last_error = e
                if attempt < self.MAX_RETRIES:
                    await asyncio.sleep(self.RETRY_DELAYS[attempt])
                    logger.warning(f"Rate limited, retrying ({attempt + 1}/{self.MAX_RETRIES})")
            
            except APIError as e:
                last_error = e
                if e.status_code and e.status_code >= 500 and attempt < self.MAX_RETRIES:
                    await asyncio.sleep(self.RETRY_DELAYS[attempt])
                    logger.warning(f"API 5xx error, retrying ({attempt + 1}/{self.MAX_RETRIES})")
                else:
                    break  # 4xx — don't retry
            
            except Exception as e:
                last_error = e
                latency_ms = int((time.monotonic() - start_ms) * 1000)
                await self._log_interaction(
                    node_name=node_name,
                    agent_name=self.__class__.__name__,
                    model_used=model,
                    input_tokens=0,
                    output_tokens=0,
                    latency_ms=latency_ms,
                    structured_output_valid=False,
                    error_message=str(e),
                )
                break
        
        raise AgentError(f"{self.__class__.__name__} failed after retries: {last_error}")
    
    async def _log_interaction(self, **kwargs):
        """Log to agent_interaction_logs table (fire-and-forget)."""
        try:
            from services.agent_log import AgentLogService
            log_service = AgentLogService()
            await log_service.log(session_id=self.session_id, **kwargs)
        except Exception as e:
            logger.warning(f"Failed to log agent interaction: {e}")


class AgentError(Exception):
    """Raised when an agent fails after all retries."""
    pass
```

---

## 3. Key Algorithms

### 3.1 Algorithm: BKT Real-Time Update

```python
# services/bkt_service.py — core BKT update function

def bkt_update(
    p_mastered: float,   # P(L_t) — current mastery probability
    is_correct: bool,    # Observed response
    p_transit: float,    # P(T) — probability of transitioning to mastered
    p_slip: float,       # P(S) — probability of slipping (correct answer despite not mastered... no: slip = incorrect despite mastered)
    p_guess: float,      # P(G) — probability of guessing correctly
) -> float:
    """
    BKT update rule (Corbett & Anderson 1994).
    
    The BKT model assumes a binary latent state: mastered (L=1) or not (L=0).
    Given an observed response (correct/incorrect), we update the posterior
    probability of mastery using Bayes' theorem, then apply the learning
    transition.
    
    Step 1: Posterior update (Bayesian update given observation)
    
      If response is CORRECT:
        P(L_t | correct) = P(correct | L_t=1) * P(L_t=1) / P(correct)
                         = (1 - P_slip) * P(L_t) / 
                           ((1 - P_slip) * P(L_t) + P_guess * (1 - P(L_t)))
    
      If response is INCORRECT:
        P(L_t | incorrect) = P(incorrect | L_t=1) * P(L_t=1) / P(incorrect)
                           = P_slip * P(L_t) / 
                             (P_slip * P(L_t) + (1 - P_guess) * (1 - P(L_t)))
    
    Step 2: Learning transition
      P(L_{t+1}) = P(L_t | obs) + (1 - P(L_t | obs)) * P_transit
    
    This captures the intuition that even if the student hasn't mastered
    the skill yet, there's a chance they learn it on each opportunity.
    
    Args:
        p_mastered: Current mastery probability P(L_t), in (0, 1).
        is_correct: Whether the student answered correctly.
        p_transit: Learning rate, typically 0.05–0.20.
        p_slip: Slip probability, typically 0.05–0.15.
        p_guess: Guess probability, typically 0.10–0.30.
    
    Returns:
        Updated mastery probability P(L_{t+1}), clamped to [0.001, 0.999].
    
    Examples:
        >>> bkt_update(0.5, True, 0.1, 0.1, 0.2)   # Correct: mastery increases
        0.5888...
        >>> bkt_update(0.5, False, 0.1, 0.1, 0.2)   # Incorrect: mastery decreases
        0.2...
        >>> bkt_update(0.95, True, 0.1, 0.1, 0.2)   # Near mastery + correct: stays high
        0.97...
    """
    # --- Step 1: Posterior update ---
    if is_correct:
        # P(correct | mastered) = 1 - p_slip
        # P(correct | not mastered) = p_guess
        likelihood_mastered = 1.0 - p_slip
        likelihood_not_mastered = p_guess
    else:
        # P(incorrect | mastered) = p_slip
        # P(incorrect | not mastered) = 1 - p_guess
        likelihood_mastered = p_slip
        likelihood_not_mastered = 1.0 - p_guess
    
    # Bayes' theorem
    numerator = likelihood_mastered * p_mastered
    denominator = (
        likelihood_mastered * p_mastered +
        likelihood_not_mastered * (1.0 - p_mastered)
    )
    
    if denominator < 1e-15:
        # Degenerate case — avoid division by zero
        p_posterior = p_mastered
    else:
        p_posterior = numerator / denominator
    
    # --- Step 2: Learning transition ---
    p_updated = p_posterior + (1.0 - p_posterior) * p_transit
    
    # --- Clamp to avoid degenerate states ---
    p_updated = max(0.001, min(0.999, p_updated))
    
    return p_updated
```

### 3.2 Algorithm: Frustration Score Computation

```python
# agents/tutor.py — frustration detection

from dataclasses import dataclass


@dataclass
class FrustrationInputs:
    """Inputs to the frustration score computation."""
    session_responses: list[dict]   # Each has is_correct, hint_count, time_to_answer_ms
    bkt_mastery: float              # Current P(mastered) for active skill


def compute_frustration_score(inputs: FrustrationInputs) -> float:
    """
    Compute a frustration score from observable behavioral signals.
    
    This is a deterministic, rule-based computation — no LLM needed.
    Designed to be fast (< 1ms) so it can run in the graph's routing logic.
    
    Components and Weights:
    ┌──────────────────────────┬────────┬───────────────────────────────────┐
    │ Signal                   │ Weight │ Rationale                         │
    ├──────────────────────────┼────────┼───────────────────────────────────┤
    │ Consecutive wrong answers│  40%   │ Strongest frustration signal —    │
    │                          │        │ 5+ consecutive wrong is severe    │
    ├──────────────────────────┼────────┼───────────────────────────────────┤
    │ Hints used per question  │  30%   │ Heavy hint reliance signals       │
    │                          │        │ student is lost, not just stuck   │
    ├──────────────────────────┼────────┼───────────────────────────────────┤
    │ Response time spike      │  20%   │ Sudden increase in response time  │
    │                          │        │ may indicate disengagement or     │
    │                          │        │ confusion (but also thinking)     │
    ├──────────────────────────┼────────┼───────────────────────────────────┤
    │ Overall correct rate     │  10%   │ Low session accuracy correlates   │
    │                          │        │ with frustration but is noisy     │
    └──────────────────────────┴────────┴───────────────────────────────────┘
    
    Args:
        inputs: FrustrationInputs containing session history.
    
    Returns:
        Float in [0.0, 1.0]. Thresholds:
        - 0.0–0.3: Low frustration (normal)
        - 0.3–0.5: Moderate (monitor)
        - 0.5–0.7: Elevated (add encouragement)
        - 0.7–0.85: High (enter scaffolded mode)
        - 0.85–1.0: Severe (recommend session break)
    """
    responses = inputs.session_responses
    if not responses:
        return 0.0
    
    # ── Component 1: Consecutive wrong answers (40%) ──
    consecutive_wrong = 0
    for r in reversed(responses):
        if not r["is_correct"]:
            consecutive_wrong += 1
        else:
            break
    # Normalize: 0 wrong → 0.0, 5+ wrong → 1.0
    wrong_score = min(consecutive_wrong / 5.0, 1.0)
    
    # ── Component 2: Hints per question (30%) ──
    # Look at last 5 questions (or fewer if session is shorter)
    recent = responses[-5:] if len(responses) >= 5 else responses
    avg_hints = sum(r.get("hint_count", 0) for r in recent) / len(recent)
    # Normalize: 0 hints → 0.0, 3 hints (max) → 1.0
    hint_score = min(avg_hints / 3.0, 1.0)
    
    # ── Component 3: Response time spike (20%) ──
    if len(responses) >= 3:
        times = [r["time_to_answer_ms"] for r in responses if r["time_to_answer_ms"] > 0]
        if len(times) >= 3:
            avg_time = sum(times) / len(times)
            last_time = times[-1]
            if avg_time > 0:
                # How many times above average is the last response?
                spike_ratio = last_time / avg_time
                # Normalize: 1x (normal) → 0.0, 3x → 1.0
                time_score = min(max(spike_ratio - 1.0, 0.0) / 2.0, 1.0)
            else:
                time_score = 0.0
        else:
            time_score = 0.0
    else:
        time_score = 0.0
    
    # ── Component 4: Overall correct rate (10%) ──
    total = len(responses)
    correct = sum(1 for r in responses if r["is_correct"])
    rate = correct / total if total > 0 else 0.5
    # Normalize: 0% correct → 1.0, 50%+ → 0.0
    rate_score = max(1.0 - rate * 2.0, 0.0)
    
    # ── Weighted combination ──
    frustration = (
        0.40 * wrong_score +
        0.30 * hint_score +
        0.20 * time_score +
        0.10 * rate_score
    )
    
    return round(min(max(frustration, 0.0), 1.0), 3)
```

### 3.3 Algorithm: Adaptive Difficulty Selection (Maximum Fisher Information)

```python
# services/irt_service.py

import math
from dataclasses import dataclass


@dataclass
class IRTItem:
    """An item from the question bank with IRT parameters."""
    question_id: str
    a: float    # Discrimination parameter
    b: float    # Difficulty parameter
    c: float    # Guessing parameter (pseudo-chance)
    word_problem_theme: str | None = None


def irt_3pl_probability(theta: float, a: float, b: float, c: float) -> float:
    """
    Three-Parameter Logistic (3PL) IRT model.
    
    P(X=1 | θ, a, b, c) = c + (1 - c) * 1 / (1 + exp(-a * (θ - b)))
    
    Where:
    - θ (theta): Student ability parameter (typically -3 to +3)
    - a: Item discrimination (how well the item differentiates abilities)
    - b: Item difficulty (ability level at which P ≈ (1+c)/2)
    - c: Pseudo-guessing parameter (lower asymptote, P of correct for very low θ)
    
    Args:
        theta: Student ability estimate.
        a: Discrimination, typically 0.5–2.5.
        b: Difficulty, typically -3.0 to +3.0.
        c: Guessing probability, typically 0.0–0.35.
    
    Returns:
        Probability of correct response, in [c, 1.0].
    """
    exponent = -a * (theta - b)
    # Clamp to prevent overflow
    exponent = max(min(exponent, 35.0), -35.0)
    p = c + (1.0 - c) / (1.0 + math.exp(exponent))
    return p


def fisher_information(theta: float, a: float, b: float, c: float) -> float:
    """
    Fisher Information for a 3PL item at a given ability level.
    
    I(θ) = a² * (P(θ) - c)² / ((1 - c)² * P(θ) * (1 - P(θ)))
    
    This measures how much information this item provides about the
    student's ability at the given theta. Higher information = the item
    is better at discriminating ability around this theta level.
    
    The Maximum Fisher Information (MFI) criterion selects the item
    that maximizes I(θ) at the current ability estimate.
    
    Args:
        theta: Current ability estimate.
        a, b, c: Item parameters.
    
    Returns:
        Fisher Information value. Higher = more informative.
    """
    p = irt_3pl_probability(theta, a, b, c)
    q = 1.0 - p
    
    if p < 1e-10 or q < 1e-10 or (1.0 - c) < 1e-10:
        return 0.0
    
    numerator = a ** 2 * (p - c) ** 2
    denominator = (1.0 - c) ** 2 * p * q
    
    return numerator / denominator


def select_next_item(
    theta: float,
    item_bank: list[IRTItem],
    excluded_ids: set[str],
    recent_themes: list[str] | None = None,
    scaffolded: bool = False,
) -> IRTItem | None:
    """
    Select the optimal next item using Maximum Fisher Information.
    
    Algorithm:
    1. Filter: Remove excluded items (already presented or recently used).
    2. If scaffolded mode: Keep only items with b < theta (easier items).
    3. Compute Fisher Information I(θ) for each remaining item.
    4. Sort by I(θ) descending.
    5. Take top 5 candidates.
    6. Apply context diversity: prefer items whose word_problem_theme
       differs from recent_themes (last 2 questions).
    7. Return the best diverse candidate (or best overall if no diversity possible).
    
    Exposure Control:
    - excluded_ids includes items from the last 3 sessions.
    - This prevents over-exposure of high-information items.
    
    Args:
        theta: Current EAP ability estimate.
        item_bank: Available items for the current skill.
        excluded_ids: Item IDs to exclude.
        recent_themes: Themes of the last 2 questions (for diversity).
        scaffolded: If True, restrict to easier items.
    
    Returns:
        Selected IRTItem, or None if bank is exhausted.
    """
    # Step 1: Filter
    candidates = [item for item in item_bank if item.question_id not in excluded_ids]
    
    if not candidates:
        return None
    
    # Step 2: Scaffolded mode filter
    if scaffolded:
        easier = [item for item in candidates if item.b < theta]
        if easier:
            candidates = easier
    
    # Step 3: Compute information
    scored = [
        (item, fisher_information(theta, item.a, item.b, item.c))
        for item in candidates
    ]
    
    # Step 4: Sort by information (descending)
    scored.sort(key=lambda x: x[1], reverse=True)
    
    # Step 5: Top 5
    top = scored[:min(5, len(scored))]
    
    # Step 6: Context diversity
    if recent_themes:
        diverse = [(item, info) for item, info in top 
                   if item.word_problem_theme not in recent_themes]
        if diverse:
            return diverse[0][0]
    
    # Step 7: Return best overall
    return top[0][0]
```

---

## 4. Infrastructure (Stage 3)

### 4.1 New AWS Resources

#### 4.1.1 WebSocket Support — ALB

**Decision: ALB WebSocket (not API Gateway WebSocket API)**

| Factor | ALB WebSocket | API Gateway WebSocket |
|--------|--------------|----------------------|
| Complexity | ALB already exists — just needs idle timeout increase | Separate resource, new routing, IAM, Lambda integration or HTTP endpoint |
| Cost | No additional cost (already paying for ALB) | Per-connection + per-message charges |
| Latency | Direct to ECS | +5–15ms API Gateway overhead |
| Stickiness | Built-in sticky sessions via target group | Stateless by design — need separate state management |
| Scaling | ECS auto-scaling handles it | Connection-based scaling is complex |
| **Verdict** | **Chosen — simpler, cheaper, sufficient for MVP** | Better for serverless architectures |

**Configuration changes:**

```hcl
# terraform/modules/alb/main.tf

# Increase ALB idle timeout for WebSocket connections
resource "aws_lb" "main" {
  name               = "padi-ai-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = var.public_subnet_ids

  idle_timeout = 300  # 5 minutes (up from default 60s)
  # WebSocket sessions with 30s heartbeat will keep connection alive.
  # If a student goes idle for 5+ min, connection drops gracefully
  # and client reconnects.

  tags = {
    Stage = "3"
  }
}

# Target group health check — use HTTP endpoint, not WS
resource "aws_lb_target_group" "api" {
  name        = "padi-ai-api-tg"
  port        = 8000
  protocol    = "HTTP"
  target_type = "ip"
  vpc_id      = var.vpc_id

  health_check {
    enabled             = true
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
    path                = "/health"
    matcher             = "200"
  }

  stickiness {
    type            = "lb_cookie"
    cookie_duration = 3600  # 1 hour — keep student on same task during session
    enabled         = true
  }
}

# Listener rule for WebSocket path
resource "aws_lb_listener_rule" "websocket" {
  listener_arn = aws_lb_listener.https.arn
  priority     = 10

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.api.arn
  }

  condition {
    path_pattern {
      values = ["/ws/*"]
    }
  }
}
```

#### 4.1.2 Agent Engine Deployment Decision

**Decision: Embedded in FastAPI, not a separate ECS service.**

As documented in §1.1, the Agent Engine lives within the FastAPI process. No new ECS service is needed for the engine itself.

**ECS task definition changes:**

```hcl
# terraform/modules/ecs/task_definition.tf

resource "aws_ecs_task_definition" "api" {
  family                   = "padi-ai-api"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  
  # Increase resources for LangGraph + LLM calls
  cpu    = 1024   # 1 vCPU (up from 512 in Stage 2)
  memory = 2048   # 2 GB (up from 1024 in Stage 2)
  
  execution_role_arn = aws_iam_role.ecs_execution.arn
  task_role_arn      = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name  = "api"
      image = "${var.ecr_repo_url}:${var.api_image_tag}"
      
      portMappings = [
        {
          containerPort = 8000
          protocol      = "tcp"
        }
      ]
      
      environment = [
        { name = "DATABASE_URL", value = var.database_url },
        { name = "REDIS_URL", value = var.redis_url },
        { name = "SQS_QUEUE_URL", value = aws_sqs_queue.question_gen.url },
        { name = "ANTHROPIC_API_KEY_SSM", value = "/padi-ai/anthropic-api-key" },
        { name = "OPENAI_API_KEY_SSM", value = "/padi-ai/openai-api-key" },
      ]
      
      # Graceful shutdown for WebSocket connections
      stopTimeout = 120  # 2 minutes to drain connections
      
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = "/ecs/padi-ai-api"
          "awslogs-region"        = var.region
          "awslogs-stream-prefix" = "api"
        }
      }
    }
  ])
}
```

#### 4.1.3 SQS Queue for Question Generation

```hcl
# terraform/modules/sqs/main.tf

# Main queue for async question generation jobs
resource "aws_sqs_queue" "question_gen" {
  name                       = "padi-ai-question-gen"
  visibility_timeout_seconds = 300     # 5 min — long enough for LLM generation
  message_retention_seconds  = 86400   # 24 hours
  receive_wait_time_seconds  = 20      # Long polling
  max_message_size           = 4096    # 4KB — plenty for job payloads
  
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.question_gen_dlq.arn
    maxReceiveCount     = 3
  })

  tags = {
    Stage = "3"
    Purpose = "question-generation"
  }
}

# Dead letter queue
resource "aws_sqs_queue" "question_gen_dlq" {
  name                      = "padi-ai-question-gen-dlq"
  message_retention_seconds = 1209600  # 14 days — DLQ messages need investigation
  
  tags = {
    Stage = "3"
    Purpose = "question-generation-dlq"
  }
}

# CloudWatch alarm on DLQ messages
resource "aws_cloudwatch_metric_alarm" "dlq_messages" {
  alarm_name          = "padi-ai-question-gen-dlq-messages"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = 300
  statistic           = "Sum"
  threshold           = 0
  alarm_description   = "Messages in question generation DLQ"
  alarm_actions       = [var.sns_alerts_arn]

  dimensions = {
    QueueName = aws_sqs_queue.question_gen_dlq.name
  }
}

# IAM policy for ECS task to access SQS
resource "aws_iam_role_policy" "ecs_sqs" {
  name = "padi-ai-ecs-sqs"
  role = aws_iam_role.ecs_task.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sqs:SendMessage",
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes"
        ]
        Resource = [
          aws_sqs_queue.question_gen.arn,
          aws_sqs_queue.question_gen_dlq.arn
        ]
      }
    ]
  })
}
```

**SQS Worker Service:**

```hcl
# terraform/modules/ecs/worker.tf

resource "aws_ecs_task_definition" "question_worker" {
  family                   = "padi-ai-question-worker"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 512
  memory                   = 1024
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name    = "worker"
      image   = "${var.ecr_repo_url}:${var.worker_image_tag}"
      command = ["python", "-m", "workers.question_generator"]
      
      environment = [
        { name = "SQS_QUEUE_URL", value = aws_sqs_queue.question_gen.url },
        { name = "DATABASE_URL", value = var.database_url },
        { name = "OPENAI_API_KEY_SSM", value = "/padi-ai/openai-api-key" },
      ]
      
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = "/ecs/padi-ai-question-worker"
          "awslogs-region"        = var.region
          "awslogs-stream-prefix" = "worker"
        }
      }
    }
  ])
}

resource "aws_ecs_service" "question_worker" {
  name            = "padi-ai-question-worker"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.question_worker.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = false
  }
}
```

### 4.2 Redis Key Namespacing

```
# Redis key structure for Stage 3

# WebSocket session mapping
ws:conn:{student_id}          → connection host (TTL: 3600s)
ws:session:{student_id}       → session_id (TTL: 7200s)

# Working memory (session-scoped)
wm:{session_id}               → JSON of WorkingMemory (TTL: 7200s)
wm:{session_id}:interactions  → List of recent interactions (TTL: 7200s)

# BKT state cache (hot cache, backed by PostgreSQL)
bkt:{student_id}:{skill_code} → p_mastered float (TTL: 86400s)

# Rate limiting for LLM calls
rl:llm:{model}:{minute}       → call count (TTL: 120s)
```

---

## 5. Testing Plan

### 5.1 LangGraph Agent Tests

#### 5.1.1 Unit Testing Agents (Mocking LLMs)

```python
# tests/unit/test_agents/test_tutor_agent.py

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from agents.tutor import TutorAgent
from agents.base import AgentError


@pytest.fixture
def mock_anthropic():
    """Returns a mocked AsyncAnthropic client."""
    with patch("agents.base.AsyncAnthropic") as MockClient:
        client = AsyncMock()
        MockClient.return_value = client
        
        # Default successful response
        response = MagicMock()
        response.content = [MagicMock(text='{"hint_text": "Think about what multiplication means.", "hint_strategy": "nudge", "contains_answer": false}')]
        response.usage.input_tokens = 150
        response.usage.output_tokens = 30
        client.messages.create = AsyncMock(return_value=response)
        
        yield client


@pytest.fixture
def tutor_agent(mock_anthropic):
    """Returns a TutorAgent with mocked Claude Sonnet client."""
    agent = TutorAgent()
    agent.session_id = "test-session-123"
    return agent


@pytest.fixture
def sample_question():
    return {
        "question_id": "q-001",
        "skill_code": "3.OA.A.1",
        "question_text": "A farmer has 4 rows of apple trees with 6 trees in each row. How many apple trees does the farmer have in total?",
        "question_type": "numeric",
        "correct_answer": "24",
        "difficulty": 0.2,
        "discrimination": 1.2,
        "guessing": 0.1,
        "domain": "Operations & Algebraic Thinking",
        "standard_code": "3.OA.A.1",
        "scaffold_hints": [],
        "word_problem_theme": "farming",
    }


class TestTutorAgentHints:
    """Test hint generation across all levels."""
    
    @pytest.mark.asyncio
    async def test_generate_hint_level_1_is_subtle_nudge(
        self, tutor_agent, sample_question, mock_anthropic
    ):
        """Hint level 1 should be a subtle nudge, not the answer."""
        context = {
            "explanation_style": "step_by_step",
            "recent_interactions": [],
            "grade_level": 3,
            "error_type": "conceptual",
        }
        
        result = await tutor_agent.generate_hint(
            question=sample_question,
            hint_level=1,
            student_answer="10",
            context=context,
        )
        
        # Assertions on hint properties
        assert result.hint_text  # Not empty
        assert len(result.hint_text) <= 500  # Within length limit
        assert result.hint_strategy == "nudge"
        assert result.contains_answer is False
        
        # Verify Claude was called with correct model
        call_args = mock_anthropic.messages.create.call_args
        assert "claude-sonnet-4-6" in call_args.kwargs.get("model", "")
    
    @pytest.mark.asyncio
    async def test_hint_must_not_contain_answer(
        self, tutor_agent, sample_question, mock_anthropic
    ):
        """If Claude accidentally includes the answer, fallback should trigger."""
        # Mock Claude returning a hint that contains the answer
        bad_response = MagicMock()
        bad_response.content = [MagicMock(
            text='{"hint_text": "The answer is 24 trees.", "hint_strategy": "nudge", "contains_answer": true}'
        )]
        bad_response.usage.input_tokens = 150
        bad_response.usage.output_tokens = 30
        mock_anthropic.messages.create = AsyncMock(return_value=bad_response)
        
        # The agent should detect this and use a fallback
        result = await tutor_agent.generate_hint(
            question=sample_question,
            hint_level=1,
            student_answer="10",
            context={"explanation_style": "step_by_step", "recent_interactions": [], "grade_level": 3, "error_type": None},
        )
        
        assert "24" not in result.hint_text  # Must NOT contain the answer
    
    @pytest.mark.asyncio
    async def test_hint_fallback_on_api_error(
        self, tutor_agent, sample_question, mock_anthropic
    ):
        """On API failure, should return a generic fallback hint."""
        from anthropic import APIError
        mock_anthropic.messages.create.side_effect = APIError(
            message="Service unavailable", request=MagicMock(), body=None
        )
        
        # Should NOT raise — should return fallback
        result = await tutor_agent.generate_hint(
            question=sample_question,
            hint_level=2,
            student_answer="10",
            context={"explanation_style": "step_by_step", "recent_interactions": [], "grade_level": 3, "error_type": None},
        )
        
        assert result.hint_text  # Got a fallback hint
        assert "break" not in result.hint_text.lower()  # Not confused with frustration


class TestTutorAgentFrustration:
    """Test frustration detection."""
    
    def test_no_frustration_on_fresh_session(self, tutor_agent):
        """Empty session should have zero frustration."""
        from agents.tutor import compute_frustration_score, FrustrationInputs
        
        score = compute_frustration_score(FrustrationInputs(
            session_responses=[],
            bkt_mastery=0.5,
        ))
        assert score == 0.0
    
    def test_high_frustration_on_consecutive_wrong(self, tutor_agent):
        """5+ consecutive wrong answers should trigger high frustration."""
        from agents.tutor import compute_frustration_score, FrustrationInputs
        
        responses = [
            {"is_correct": False, "hint_count": 2, "time_to_answer_ms": 15000}
            for _ in range(6)
        ]
        
        score = compute_frustration_score(FrustrationInputs(
            session_responses=responses,
            bkt_mastery=0.3,
        ))
        
        assert score > 0.7  # Should be high frustration
    
    def test_low_frustration_on_mixed_results(self, tutor_agent):
        """Mixed correct/incorrect should have moderate frustration."""
        from agents.tutor import compute_frustration_score, FrustrationInputs
        
        responses = [
            {"is_correct": True, "hint_count": 0, "time_to_answer_ms": 8000},
            {"is_correct": False, "hint_count": 1, "time_to_answer_ms": 12000},
            {"is_correct": True, "hint_count": 0, "time_to_answer_ms": 7000},
            {"is_correct": True, "hint_count": 0, "time_to_answer_ms": 9000},
        ]
        
        score = compute_frustration_score(FrustrationInputs(
            session_responses=responses,
            bkt_mastery=0.6,
        ))
        
        assert score < 0.5  # Should be moderate or low
```

#### 5.1.2 Testing the LangGraph Graph

```python
# tests/integration/test_graph_flow.py

import pytest
from unittest.mock import AsyncMock, patch
from graph.graph import build_practice_graph
from graph.state import SessionState
from langgraph.checkpoint.memory import MemorySaver


@pytest.fixture
def graph():
    """Build graph with in-memory checkpointer for testing."""
    g = build_practice_graph()
    checkpointer = MemorySaver()
    return g.compile(checkpointer=checkpointer)


@pytest.fixture
def initial_state():
    """Minimal initial state for testing."""
    return {
        "session_id": "test-session-001",
        "student_id": "student-001",
        "plan_module_id": "module-001",
        "current_skill_code": "3.OA.A.1",
        "current_question": None,
        "attempt_count": 0,
        "max_attempts": 3,
        "hints_used": 0,
        "session_responses": [],
        "questions_presented": 0,
        "correct_count": 0,
        "skills_attempted": [],
        "skills_mastered_this_session": [],
        "bkt_states": {"3.OA.A.1": 0.5},
        "bkt_params": {"3.OA.A.1": {"p_transit": 0.1, "p_slip": 0.1, "p_guess": 0.2}},
        "mastery_threshold": 0.95,
        "mastery_streak_required": 5,
        "frustration_score": 0.0,
        "frustration_history": [],
        "scaffolded_mode": False,
        "working_memory": {"recent_interactions": [], "current_streak": 0, "session_error_types": [], "time_pressure_detected": False},
        "long_term_memory": {
            "preferred_explanation_style": "step_by_step",
            "common_error_patterns": {},
            "engagement_pattern": {},
            "mastery_timestamps": {},
            "total_sessions_completed": 0,
            "cumulative_correct_rate": 0.5,
        },
        "skill_queue": ["3.OA.A.1", "3.OA.A.2"],
        "current_skill_index": 0,
        "theta_estimate": 0.0,
        "theta_sem": 1.0,
        "session_started_at": "2026-04-04T12:00:00Z",
        "session_complete": False,
        "end_reason": None,
        "error": None,
        "error_count": 0,
        "max_errors": 3,
    }


class TestGraphRouting:
    
    @pytest.mark.asyncio
    @patch("graph.nodes.initialize.LongTermMemoryStore")
    @patch("graph.nodes.initialize.BKTService")
    @patch("graph.nodes.initialize.PlanService")
    @patch("graph.nodes.select_question.QuestionBankService")
    async def test_graph_routes_to_hint_on_wrong_answer(
        self, mock_qb, mock_plan, mock_bkt, mock_ltm, graph, initial_state
    ):
        """After wrong answer with hints remaining, graph should route to generate_hint_node."""
        # Setup mocks
        mock_ltm_instance = AsyncMock()
        mock_ltm_instance.load.return_value = initial_state["long_term_memory"]
        mock_ltm.return_value = mock_ltm_instance
        
        # Configure question bank to return a sample question
        mock_qb_instance = AsyncMock()
        mock_qb_instance.get_items_for_skill.return_value = [{
            "question_id": "q-001",
            "skill_code": "3.OA.A.1",
            "question_text": "4 × 6 = ?",
            "question_type": "numeric",
            "correct_answer": "24",
            "difficulty": 0.2,
            "discrimination": 1.2,
            "guessing": 0.1,
            "domain": "OA",
            "standard_code": "3.OA.A.1",
            "scaffold_hints": ["Think about groups.", "Count 4 groups of 6.", "4 × 6 = ?"],
            "word_problem_theme": None,
        }]
        mock_qb_instance.get_recently_presented.return_value = set()
        mock_qb.return_value = mock_qb_instance
        
        config = {"configurable": {"thread_id": "test-1"}}
        
        # First invocation: initialize → select_question → present_question
        result = await graph.ainvoke(initial_state, config)
        
        assert result["current_question"] is not None
        assert result["questions_presented"] == 1
    
    @pytest.mark.asyncio
    async def test_session_ends_after_max_questions(self, graph, initial_state):
        """Session should end after reaching question count limit."""
        initial_state["questions_presented"] = 30
        initial_state["_mastery_achieved"] = False
        
        # The route_after_mastery_check should return "end_session"
        from graph.edges.routing import route_after_mastery_check
        result = route_after_mastery_check(initial_state)
        assert result == "end_session"


class TestBKTRouting:
    
    def test_mastery_check_triggers_advance(self):
        """When BKT >= 0.95 and streak met, should advance to next skill."""
        from graph.edges.routing import route_after_mastery_check
        
        state = {
            "current_skill_code": "3.OA.A.1",
            "bkt_states": {"3.OA.A.1": 0.97},
            "mastery_threshold": 0.95,
            "mastery_streak_required": 5,
            "session_responses": [
                {"skill_code": "3.OA.A.1", "is_correct": True}
                for _ in range(6)
            ],
            "_mastery_achieved": True,
            "questions_presented": 10,
            "session_started_at": "2026-04-04T12:00:00Z",
        }
        
        assert route_after_mastery_check(state) == "advance_skill"
```

#### 5.1.3 Contract Tests (Weekly, Against Real Models)

```python
# tests/contract/test_claude_hint_contract.py
# Run weekly via CI: schedule: cron(0 6 * * 1)  # Every Monday 6am UTC

import pytest
from pydantic import BaseModel, Field
from agents.tutor import TutorAgent


class HintResponseContract(BaseModel):
    """Expected schema of Claude Sonnet hint output."""
    hint_text: str = Field(min_length=10, max_length=500)
    hint_strategy: str  # Must be one of: nudge, guided, worked_example
    contains_answer: bool  # Must be False


@pytest.mark.contract
@pytest.mark.asyncio
async def test_claude_hint_output_conforms_to_schema():
    """Validate Claude Sonnet's hint output still conforms to expected schema.
    
    This test hits the real Claude API. Run weekly to detect:
    - Model behavior drift
    - Schema compliance issues
    - Content quality degradation
    """
    agent = TutorAgent()
    agent.session_id = "contract-test"
    
    question = {
        "question_id": "contract-q1",
        "skill_code": "3.OA.A.1",
        "question_text": "A store has 5 shelves with 8 books on each shelf. How many books does the store have in total?",
        "correct_answer": "40",
        "question_type": "numeric",
    }
    
    for hint_level in [1, 2, 3]:
        result = await agent.generate_hint(
            question=question,
            hint_level=hint_level,
            student_answer="13",
            context={
                "explanation_style": "step_by_step",
                "recent_interactions": [],
                "grade_level": 3,
                "error_type": "conceptual",
            },
        )
        
        # Validate against contract
        validated = HintResponseContract.model_validate(result.model_dump())
        
        assert validated.contains_answer is False, f"Level {hint_level} hint contains answer!"
        assert "40" not in validated.hint_text, f"Level {hint_level} hint literally contains '40'"
        assert len(validated.hint_text) >= 10, f"Level {hint_level} hint too short"
        
        # Strategy should match level
        expected_strategies = {1: "nudge", 2: "guided", 3: "worked_example"}
        assert validated.hint_strategy == expected_strategies[hint_level], \
            f"Level {hint_level}: expected {expected_strategies[hint_level]}, got {validated.hint_strategy}"
```

#### 5.1.4 Load Testing WebSocket Connections

```javascript
// tests/load/k6_websocket_load.js
// Run: k6 run --vus 500 --duration 10m k6_websocket_load.js

import ws from 'k6/ws';
import { check, sleep } from 'k6';
import { Counter, Trend } from 'k6/metrics';

const wsUrl = __ENV.WS_URL || 'wss://api-staging.padi.ai/ws/practice';
const authToken = __ENV.AUTH_TOKEN || 'test-load-token';

const questionLatency = new Trend('question_latency_ms');
const feedbackLatency = new Trend('feedback_latency_ms');
const hintLatency = new Trend('hint_latency_ms');
const errorCount = new Counter('ws_errors');

export const options = {
  stages: [
    { duration: '2m', target: 100 },   // Ramp up to 100
    { duration: '3m', target: 300 },   // Ramp to 300
    { duration: '3m', target: 500 },   // Ramp to 500 (target)
    { duration: '2m', target: 0 },     // Ramp down
  ],
  thresholds: {
    'question_latency_ms': ['p(95)<2000'],  // 95th percentile < 2s
    'feedback_latency_ms': ['p(95)<3000'],  // < 3s (includes LLM call)
    'ws_errors': ['count<50'],               // < 50 errors total
  },
};

export default function () {
  const url = `${wsUrl}?token=${authToken}`;
  
  const res = ws.connect(url, {}, function (socket) {
    let questionReceived = false;
    let questionStartTime = 0;
    
    socket.on('open', () => {
      // Start session
      socket.send(JSON.stringify({
        type: 'SESSION_START',
        studentId: `load-test-${__VU}`,
        skillCode: '3.OA.A.1',
        moduleId: 'load-test-module',
      }));
      questionStartTime = Date.now();
    });
    
    socket.on('message', (data) => {
      const msg = JSON.parse(data);
      
      if (msg.type === 'QUESTION') {
        questionLatency.add(Date.now() - questionStartTime);
        questionReceived = true;
        
        // Simulate student thinking time (3-15 seconds)
        sleep(3 + Math.random() * 12);
        
        // Submit answer (randomly correct 60% of the time)
        questionStartTime = Date.now();
        socket.send(JSON.stringify({
          type: 'SUBMIT_ANSWER',
          questionId: msg.question.questionId,
          answer: Math.random() > 0.4 ? '24' : '10',
          timeMs: 5000 + Math.random() * 10000,
        }));
      }
      
      if (msg.type === 'FEEDBACK') {
        feedbackLatency.add(Date.now() - questionStartTime);
        questionStartTime = Date.now();
        
        if (!msg.isCorrect && msg.showHintButton && Math.random() > 0.5) {
          // Request hint 50% of the time on wrong answer
          socket.send(JSON.stringify({
            type: 'REQUEST_HINT',
            questionId: 'current',
          }));
        }
      }
      
      if (msg.type === 'HINT') {
        hintLatency.add(Date.now() - questionStartTime);
      }
      
      if (msg.type === 'SESSION_SUMMARY') {
        socket.close();
      }
      
      if (msg.type === 'ERROR') {
        errorCount.add(1);
        if (!msg.recoverable) {
          socket.close();
        }
      }
    });
    
    socket.on('error', (e) => {
      errorCount.add(1);
    });
    
    // Heartbeat
    socket.setInterval(() => {
      socket.send(JSON.stringify({ type: 'HEARTBEAT' }));
    }, 30000);
    
    // Max session duration: 5 minutes
    socket.setTimeout(() => {
      socket.send(JSON.stringify({
        type: 'END_SESSION',
        reason: 'complete',
      }));
    }, 300000);
  });
  
  check(res, {
    'WebSocket connected': (r) => r && r.status === 101,
  });
}
```

---

## 6. QA Plan

### 6.1 Stage 3 QA Checklist (Exit Criteria)

All items must pass before Stage 3 is considered complete.

#### WebSocket Protocol (8 items)
- [ ] **WS-01**: SESSION_START message creates a new session and returns SESSION_INITIALIZED with valid sessionId, moduleName, and estimatedQuestions.
- [ ] **WS-02**: QUESTION message delivers a valid question with no correct_answer field visible to client.
- [ ] **WS-03**: SUBMIT_ANSWER returns FEEDBACK within 3 seconds (p95).
- [ ] **WS-04**: REQUEST_HINT returns HINT message with correct hintLevel (1, 2, or 3 in sequence).
- [ ] **WS-05**: END_SESSION returns SESSION_SUMMARY with accurate statistics.
- [ ] **WS-06**: HEARTBEAT/HEARTBEAT_ACK cycle maintains connection. Connection drops after 5 min of silence.
- [ ] **WS-07**: Invalid token in handshake → connection closed with code 4001.
- [ ] **WS-08**: Malformed JSON message → ERROR response with recoverable=true, session continues.

#### Hint Ladder (5 items)
- [ ] **HL-01**: Hints progress correctly: Level 1 → 2 → 3, never skipping levels.
- [ ] **HL-02**: No hint contains the correct answer (tested across 100 random questions).
- [ ] **HL-03**: Level 1 hints are conceptual nudges (≤ 50 words, no procedure).
- [ ] **HL-04**: Level 3 hints include a partial worked example.
- [ ] **HL-05**: After 3 hints exhausted, next incorrect answer updates BKT and moves on.

#### BKT Accuracy (5 items)
- [ ] **BKT-01**: BKT state increases after correct response (verified with known parameters).
- [ ] **BKT-02**: BKT state decreases after incorrect response.
- [ ] **BKT-03**: P(mastered) = 0.95 with 5 consecutive correct triggers SKILL_MASTERED event.
- [ ] **BKT-04**: BKT state history is persisted to bkt_state_history table with correct session_id.
- [ ] **BKT-05**: BKT states are correctly loaded from DB at session start (not reset to prior).

#### Frustration Detection (4 items)
- [ ] **FD-01**: 5+ consecutive wrong answers → frustration_score > 0.7, scaffolded_mode activated.
- [ ] **FD-02**: Severe frustration (> 0.85) → session ends with FRUSTRATION_BREAK message.
- [ ] **FD-03**: 3+ frustration episodes in one session → session ends regardless of current score.
- [ ] **FD-04**: Scaffolded mode presents easier questions (b < theta).

#### Session Recovery (4 items)
- [ ] **SR-01**: WebSocket disconnect + reconnect within 60s → session resumes from last checkpoint.
- [ ] **SR-02**: Reconnected session re-sends the last QUESTION message.
- [ ] **SR-03**: Checkpoint persists after every student message (verified by checking checkpoint table).
- [ ] **SR-04**: Expired session (> 1 hour) → fresh session start, BKT states preserved.

#### Content Safety (3 items)
- [ ] **CS-01**: All Claude-generated hints pass child-safe vocabulary check (no violence, profanity, sexual content).
- [ ] **CS-02**: Encouragement messages are age-appropriate for grades 3–8.
- [ ] **CS-03**: Error messages shown to students never expose internal technical details.

#### Agent Logging (4 items)
- [ ] **AL-01**: Every LLM call logged in agent_interaction_logs with model, tokens, latency.
- [ ] **AL-02**: Failed LLM calls logged with error_message.
- [ ] **AL-03**: structured_output_valid = false logged when Pydantic parsing fails.
- [ ] **AL-04**: Log entries include correct session_id and node_name.

#### Data Integrity (3 items)
- [ ] **DI-01**: All session_questions FK to valid practice_sessions.
- [ ] **DI-02**: All hint_interactions FK to valid session_questions.
- [ ] **DI-03**: Long-term memory updated correctly after session end (error patterns, mastery timestamps).

**Total: 36 items.**

---

## 7. Operational Runbooks

### 7.1 Runbook: WebSocket Connection Leak Investigation

**Trigger:** CloudWatch alarm for WebSocket connections exceeding threshold (> 600 active when expected < 500), or ECS memory usage climbing steadily.

**Steps:**

1. **Assess scope:**
   ```bash
   # Check active WebSocket connections via Redis
   redis-cli -h $REDIS_HOST KEYS "ws:conn:*" | wc -l
   
   # Compare with ECS task count
   aws ecs describe-services --cluster padi-ai --services padi-ai-api \
     --query 'services[0].runningCount'
   ```

2. **Identify stale connections:**
   ```bash
   # Find connections older than 2 hours (abnormal — sessions max 30 min)
   redis-cli -h $REDIS_HOST --scan --pattern "ws:conn:*" | while read key; do
     ttl=$(redis-cli -h $REDIS_HOST TTL "$key")
     if [ "$ttl" -lt 3600 ]; then  # Less than 1 hour remaining on 2-hour TTL
       echo "STALE: $key (TTL: $ttl)"
     fi
   done
   ```

3. **Check ECS task network connections:**
   ```bash
   # SSH into ECS task (via ECS Exec)
   aws ecs execute-command --cluster padi-ai --task $TASK_ID \
     --container api --interactive --command "ss -s"
   
   # Count ESTABLISHED WebSocket connections
   aws ecs execute-command --cluster padi-ai --task $TASK_ID \
     --container api --interactive \
     --command "ss -tn state established | grep :8000 | wc -l"
   ```

4. **Remediate:**
   - If connections are genuinely leaked (no matching Redis keys): restart the specific ECS task via `aws ecs stop-task`.
   - If ALB is holding connections: check ALB idle timeout (should be 300s). Reduce if connections are piling up.
   - Deploy fix: ensure all WebSocket handlers have `finally` blocks that clean up Redis keys.

5. **Post-remediation:**
   - Verify connection count returns to normal within 10 minutes.
   - Check that no active student sessions were interrupted.

### 7.2 Runbook: LLM API Outage During Live Sessions

**Trigger:** CloudWatch alarm for LLM error rate > 50% over 2 minutes, or agent_interaction_logs showing consecutive failures.

**Steps:**

1. **Detect and confirm:**
   ```bash
   # Check recent agent errors
   psql $DATABASE_URL -c "
     SELECT model_used, COUNT(*), 
            COUNT(*) FILTER (WHERE error_message IS NOT NULL) as errors,
            AVG(latency_ms) as avg_latency
     FROM agent_interaction_logs
     WHERE created_at > NOW() - INTERVAL '5 minutes'
     GROUP BY model_used;
   "
   ```

2. **Assess impact:**
   ```bash
   # Count active sessions
   redis-cli -h $REDIS_HOST KEYS "ws:session:*" | wc -l
   
   # Check which nodes are failing
   psql $DATABASE_URL -c "
     SELECT node_name, COUNT(*) 
     FROM agent_interaction_logs
     WHERE error_message IS NOT NULL 
       AND created_at > NOW() - INTERVAL '5 minutes'
     GROUP BY node_name;
   "
   ```

3. **Activate fallback mode:**
   
   The system has built-in fallbacks:
   - **Hint generation**: Falls back to pre-authored scaffold_hints or generic hints.
   - **Response evaluation**: Falls back to exact-match for numeric/MC, treats free-response as correct (flagged for review).
   - **Error recovery node**: Handles up to 3 errors per session before graceful termination.
   
   If the outage is prolonged (> 10 minutes), set a feature flag to bypass LLM calls entirely:
   ```bash
   redis-cli -h $REDIS_HOST SET "feature:llm_bypass" "true" EX 3600
   ```

4. **Notify affected sessions:**
   - Sessions will automatically receive ERROR messages with `recoverable: true`.
   - Students will see: "We're having a bit of trouble right now. Hints might be simpler than usual."

5. **Monitor recovery:**
   ```bash
   # Watch error rate in real-time
   watch -n 10 'psql $DATABASE_URL -c "
     SELECT COUNT(*) FILTER (WHERE error_message IS NULL) as success,
            COUNT(*) FILTER (WHERE error_message IS NOT NULL) as errors
     FROM agent_interaction_logs
     WHERE created_at > NOW() - INTERVAL '1 minute';
   "'
   ```

6. **Post-outage:**
   - Clear the bypass flag: `redis-cli -h $REDIS_HOST DEL "feature:llm_bypass"`
   - Review flagged_for_review responses and re-evaluate with LLM.
   - Write incident report documenting impact (sessions affected, questions flagged).

### 7.3 Runbook: BKT State Corruption Recovery

**Trigger:** Support report that a student's mastery levels appear incorrect (e.g., showing 0.99 mastery on a skill they haven't practiced, or 0.01 on a mastered skill).

**Steps:**

1. **Identify affected state:**
   ```sql
   -- Check current BKT state for the student
   SELECT skill_code, p_mastered, recorded_at, session_id, trigger
   FROM bkt_state_history
   WHERE student_id = $STUDENT_ID
   ORDER BY skill_code, recorded_at DESC;
   
   -- Check the materialized view
   SELECT * FROM bkt_current_states
   WHERE student_id = $STUDENT_ID;
   ```

2. **Trace the corruption source:**
   ```sql
   -- Find the transition where state jumped unexpectedly
   WITH ranked AS (
     SELECT *,
            LAG(p_mastered) OVER (PARTITION BY skill_code ORDER BY recorded_at) as prev_mastery,
            p_mastered - LAG(p_mastered) OVER (PARTITION BY skill_code ORDER BY recorded_at) as delta
     FROM bkt_state_history
     WHERE student_id = $STUDENT_ID AND skill_code = $SKILL_CODE
   )
   SELECT * FROM ranked
   WHERE ABS(delta) > 0.3  -- Suspicious jumps > 0.3
   ORDER BY recorded_at;
   ```

3. **Re-derive correct state:**
   ```sql
   -- Get all responses for this student-skill, in order
   SELECT sq.skill_code, sr.is_correct, sq.presented_at
   FROM session_questions sq
   JOIN session_responses sr ON sr.session_question_id = sq.id
   WHERE sq.skill_code = $SKILL_CODE
     AND sq.session_id IN (
       SELECT session_id FROM practice_sessions WHERE student_id = $STUDENT_ID
     )
   ORDER BY sq.presented_at;
   ```
   
   Then replay BKT updates using the known parameters to compute the correct current state.

4. **Correct the state:**
   ```sql
   -- Insert corrected state
   INSERT INTO bkt_state_history (student_id, skill_code, p_mastered, p_transit, p_slip, p_guess, trigger)
   VALUES ($STUDENT_ID, $SKILL_CODE, $CORRECT_P_MASTERED, $P_TRANSIT, $P_SLIP, $P_GUESS, 'manual_reset');
   
   -- Refresh materialized view
   REFRESH MATERIALIZED VIEW CONCURRENTLY bkt_current_states;
   ```

5. **Invalidate cache:**
   ```bash
   redis-cli -h $REDIS_HOST DEL "bkt:$STUDENT_ID:$SKILL_CODE"
   ```

6. **Notify support:**
   - Confirm the corrected mastery level to the support agent.
   - If the student was incorrectly advanced past a skill, discuss with the teacher whether to reset the learning plan module.
