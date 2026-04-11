# PRD Stage 3: Adaptive Practice Engine & Multi-Agent AI Tutoring
## MathPath Oregon | Version 1.0 | Target Completion: Month 10

**Document Status:** Draft  
**Owner:** Product — AI Learning Systems  
**Reviewers:** Engineering (AI/ML), Engineering (Frontend), Engineering (Backend), Curriculum, QA  
**Dependencies:** Stage 1 (Standards DB + Diagnostic), Stage 2 (Learning Plan Generator)  
**Epic Reference:** MATH-300 series

---

## Table of Contents

1. [Overview & Objectives](#31-overview--objectives)
2. [Multi-Agent Architecture Specification](#32-multi-agent-architecture-specification)
3. [Functional Requirements](#33-functional-requirements)
4. [Non-Functional Requirements](#34-non-functional-requirements)
5. [LangGraph State & Flow Specification](#35-langgraph-state--flow-specification)
6. [Data Models](#36-data-models)
7. [API Endpoints](#37-api-endpoints)
8. [Acceptance Criteria](#38-acceptance-criteria)

---

## 3.1 Overview & Objectives

### What "Adaptive Practice" Means in MathPath Oregon

Adaptive practice is not simply varying question difficulty. In MathPath Oregon, adaptive practice is a closed-loop cognitive feedback system that continuously models a student's knowledge state, selects the most informative next learning event, delivers that event with appropriately scaffolded support, evaluates the response with error-level granularity, and updates the knowledge model — all within a single real-time session and across sessions over weeks.

The system adapts along six dimensions simultaneously:

| Dimension | Mechanism | Timescale |
|---|---|---|
| **Difficulty** | IRT theta-matched question selection | Within-question |
| **Knowledge state** | pyBKT Bayesian update | After each response |
| **Hint depth** | 3-tier hint ladder based on attempt count | Within-question |
| **Explanation style** | Preference learning (step-by-step / visual / analogy) | Across sessions |
| **Session pacing** | Fatigue and engagement signal detection | Within-session |
| **Skill sequencing** | Prerequisite graph traversal + BKT mastery gating | Across skills |

The result is an experience where every student, regardless of their starting point, encounters problems at exactly the right difficulty to maximize learning gain — not too easy to be boring, not so hard as to be discouraging (Vygotsky's Zone of Proximal Development operationalized computationally).

### How the Multi-Agent Architecture Works End-to-End

Stage 3 introduces a **LangGraph StateGraph** orchestrating four specialized agents. Each agent is a discrete, independently testable component with defined inputs, outputs, and LLM assignments:

```
Student Input
      │
      ▼
┌─────────────────────────────────────────────────┐
│          LangGraph Orchestrator                 │
│  (SessionState router + conditional edges)      │
└──┬──────────────┬────────────────┬──────────────┘
   │              │                │
   ▼              ▼                ▼
Assessment     Tutor           Question
  Agent        Agent           Generator
(o3-mini)   (Claude 4.6)      Agent
   │              │            (o3-mini +
   │              │             DB cache)
   └──────────────┴────────────────┘
                  │
                  ▼
         Progress Tracker
              Agent
         (pyBKT — no LLM)
                  │
                  ▼
         PostgreSQL (LTM)
              Redis (WM)
```

The session loop is:
1. **Orchestrator** loads student BKT state from LTM → initializes Working Memory in Redis
2. **Question Generator Agent** selects/generates the next question at the IRT-targeted difficulty
3. Question displayed to student; student submits answer
4. **Assessment Agent** evaluates the answer, classifies error type
5. Orchestrator routes: if correct → **Progress Tracker** updates BKT → check mastery → loop; if incorrect → **Tutor Agent** delivers hint → loop back to answer attempt
6. After session end (mastery threshold met, 10 questions reached, or student exits): **Progress Tracker** writes LTM, generates session summary

> **LLM Routing — Local-First for Student-Facing Agents (Updated April 2026):** The Tutor Agent and Assessment Agent use **local Ollama/Qwen2.5 models by default** until COPPA Data Processing Agreements (DPAs) confirming zero data retention are obtained from Anthropic and OpenAI. Student session data cannot be transmitted to cloud LLMs under COPPA without such agreements. All LLM calls go through the `llm_client.get_llm_response(role, messages)` wrapper (see ADR-009); switching to Claude Sonnet 4.6 for student-facing roles requires only a config change once DPAs are in place. The Question Generator Agent (no student PII) may use cloud models immediately.
>
> | Agent | Default Model | Can Use Cloud When | Estimated Latency |
> |---|---|---|---|
> | Tutor Agent | `ollama/qwen2.5:72b` | COPPA DPA in place | 0.5–2s |
> | Assessment Agent | `ollama/qwen2.5:32b` | COPPA DPA in place | 0.3–1s |
> | Question Generator | `anthropic/claude-sonnet-4-6` | Immediately (no student PII) | 0.2–0.5s |
> | Progress Tracker | No LLM (pure BKT) | N/A | <10ms |

### Business Objectives

| Objective | Metric | Target | Measurement Method |
|---|---|---|---|
| Engagement | Avg session length | ≥ 12 minutes | PostHog session analytics |
| Learning efficacy | Avg BKT P(mastery) gain per session | ≥ 0.08 | PostgreSQL BKT state diff |
| Hint effectiveness | % sessions where hints lead to correct answer | ≥ 65% | session_responses table |
| Retention | D7 return rate after first practice session | ≥ 55% | Cohort analysis |
| Cost efficiency | LLM cost per session | < $0.15 | AWS Cost Explorer |
| Latency | P95 tutor response time | < 3 seconds | APM |
| Parent confidence | Parent NPS post-Stage 3 | ≥ 45 | Post-session survey |

### Success Criteria (Stage 3 Go/No-Go)

- [ ] All four agents operational and integrated via LangGraph
- [ ] BKT state updates correctly after every response (unit-tested against pyBKT reference)
- [ ] Hint ladder delivers contextually correct hints at each level for ≥ 90% of test cases
- [ ] Question generator produces valid, grade-appropriate questions for all 29 Oregon standards
- [ ] P95 tutor response latency < 3 seconds under 100 concurrent sessions
- [ ] LLM cost per 10-question session < $0.15 (load tested)
- [ ] COPPA-compliant: no PII in LLM prompt logs; all student data encrypted at rest
- [ ] Frustration detection triggers correctly in ≥ 85% of simulated frustration scenarios

---

## 3.2 Multi-Agent Architecture Specification

### The Agent System

#### Orchestrator (LangGraph StateGraph)

The Orchestrator is the central LangGraph `StateGraph` that owns session state and routes between agents. It is **not** an LLM — it is a deterministic Python state machine that applies conditional routing logic.

##### State Schema

```python
from typing import TypedDict, Optional, List, Literal
from datetime import datetime

class BKTState(TypedDict):
    skill_id: str                    # e.g., "4.OA.A.1"
    p_mastered: float                # 0.0 to 1.0
    p_transit: float                 # BKT transition probability
    p_slip: float                    # BKT slip probability
    p_guess: float                   # BKT guess probability
    correct_streak: int              # consecutive correct responses
    attempt_count: int               # total attempts this skill
    last_updated: datetime

class QuestionContext(TypedDict):
    question_id: str
    skill_id: str
    question_text: str
    question_type: Literal["multiple_choice","numeric","fraction","drag_drop"]
    options: Optional[List[str]]     # for multiple_choice
    correct_answer: str
    solution_steps: List[str]
    difficulty_b: float              # IRT b-parameter
    context_theme: str               # e.g., "Oregon wildlife", "food", "sports"
    prerequisite_skills: List[str]

class WorkingMemoryEntry(TypedDict):
    question_id: str
    question_text: str
    student_answer: str
    is_correct: bool
    hints_used: int
    error_type: Optional[str]
    response_time_ms: int
    timestamp: datetime

class SessionState(TypedDict):
    # Identity
    student_id: str
    session_id: str
    learning_plan_id: str

    # Current position
    current_skill_id: str
    current_module_id: str
    current_question: Optional[QuestionContext]

    # Attempt tracking
    attempt_count: int               # attempts on current question
    hints_used: int                  # hints on current question
    consecutive_correct: int         # streak within session
    consecutive_wrong: int           # wrong streak within session

    # Session history (Working Memory — last 10 entries)
    session_history: List[WorkingMemoryEntry]

    # BKT states for all skills touched this session
    bkt_states: dict[str, BKTState]

    # Frustration signal
    frustration_score: float         # 0.0 to 10.0

    # Explanation style preference
    preferred_explanation_style: Literal["step_by_step","visual","analogy","auto"]

    # Session metadata
    session_start_time: datetime
    questions_answered: int
    questions_correct: int
    session_mode: Literal["adaptive","scaffolded","challenge","review"]

    # Flow control
    next_agent: Literal["question_generator","assessment","tutor","progress_tracker","end"]
    session_complete: bool

    # Tutor context window (last 3 tutor interactions)
    tutor_context: List[dict]

    # Error from any agent (for retry logic)
    last_error: Optional[str]
```

##### Session Lifecycle

```
Session Start
    │
    ├── Load BKT states from PostgreSQL (LTM)
    ├── Initialize Redis WM (session_id as key, 24h TTL)
    ├── Load student learning preferences from LTM
    ├── Select current_skill from active learning plan module
    │
    ▼
Question Loop ──────────────────────────────────┐
    │                                           │
    ├── [Question Generator] → Emit question    │
    ├── Display to student                      │
    ├── Await student answer (WebSocket)        │
    │                                           │
    ├── [Assessment Agent] → Evaluate response  │
    │       │                                   │
    │       ├── is_correct = True               │
    │       │       ├── [Progress Tracker] BKT update
    │       │       ├── Mastery check           │
    │       │       │   ├── P(mastered) ≥ 0.95 AND correct_streak ≥ 5
    │       │       │   │       └── Skill mastered → advance or end session
    │       │       │   └── P(mastered) < 0.95  │
    │       │       │           └── Continue loop ──────────────────────┘
    │       │       └── Celebration animation trigger
    │       │
    │       └── is_correct = False
    │               ├── attempt_count < 3
    │               │       └── [Tutor Agent] → Deliver hint (level = attempt_count)
    │               ├── attempt_count ≥ 3
    │               │       └── [Tutor Agent] → Deliver worked example (level 3 hint)
    │               │           [Progress Tracker] BKT update (incorrect)
    │               │           Advance to next question (question not re-served)
    │               └── frustration_score > 7.0
    │                       └── Switch session_mode to "scaffolded"
    │
Session End Triggers (any one):
    ├── questions_answered ≥ 10
    ├── session_duration ≥ 20 min AND accuracy < 50%  (fatigue)
    ├── session_duration ≥ 30 min (hard cap)
    ├── All skills in current module mastered
    └── Student clicks "End Session"
    │
    ▼
Session End
    ├── [Progress Tracker] Write BKT states → PostgreSQL
    ├── [Progress Tracker] Generate session summary
    ├── Flush WM context → session_summaries table
    └── Display session summary screen
```

##### Routing Logic (LangGraph Conditional Edges)

```python
def route_after_assessment(state: SessionState) -> str:
    """Routes after Assessment Agent evaluates a response."""
    if state["frustration_score"] > 7.0:
        return "tutor"  # forced scaffolding

    if state["current_question"] is None:
        return "question_generator"

    # Routed to progress_tracker first (BKT update), then re-evaluated
    if state["next_agent"] == "tutor":
        return "tutor"
    if state["next_agent"] == "question_generator":
        return "question_generator"
    if state["session_complete"]:
        return "end"
    return "progress_tracker"

def route_after_progress_tracker(state: SessionState) -> str:
    """Routes after BKT update."""
    if state["session_complete"]:
        return "end"
    if state["questions_answered"] >= 10:
        return "end"
    return "question_generator"

def route_after_tutor(state: SessionState) -> str:
    """Routes after Tutor delivers hint/explanation."""
    # Return to await student answer — orchestrator waits for WebSocket
    return "await_answer"
```

---

#### Assessment Agent

**Role:** Evaluate student responses with mathematical rigor, classify error types, and determine the appropriate feedback level. This agent is the source of truth for correctness and error pattern data that feeds both BKT updates and tutor personalization.

**LLM:** `o3-mini` — selected for its superior mathematical reasoning at low latency and cost. It reliably handles: arithmetic verification, fraction comparison, algebraic evaluation, and multi-step problem checking.

**Input Schema:**

```json
{
  "student_answer": "3/4",
  "correct_answer": "3/4",
  "question_text": "If Maria ran 3 miles and completed 4 equal laps, how far was each lap?",
  "question_type": "fraction",
  "solution_steps": [
    "Total distance = 3 miles",
    "Number of laps = 4",
    "Each lap = 3 ÷ 4 = 3/4 miles"
  ],
  "skill_id": "4.NF.B.4",
  "student_id": "stu_abc123",
  "attempt_number": 1,
  "session_history_summary": "Student has struggled with fraction division in last 3 attempts."
}
```

**Output Schema:**

```json
{
  "is_correct": true,
  "normalized_answer": "3/4",
  "error_type": null,
  "error_code": null,
  "feedback_level": 1,
  "partial_credit": false,
  "confidence": 0.98,
  "assessment_reasoning": "Student answer 3/4 matches correct answer exactly."
}
```

**Error Taxonomy (Grade 4 Math):**

| Code | Error Type | Category | Description | Example |
|---|---|---|---|---|
| `ERR-OA-01` | Operator confusion | Conceptual | Uses wrong operation (add instead of multiply) | 4×3 answered as 7 |
| `ERR-OA-02` | Commutativity misapplication | Conceptual | Believes subtraction/division are commutative | 8-3 = 3-8 |
| `ERR-NBT-01` | Place value collapse | Conceptual | Misaligns place values in multi-digit operations | 34+27 → 511 |
| `ERR-NBT-02` | Regrouping error | Procedural | Carries/borrows incorrectly | 53-27 → 34 |
| `ERR-NBT-03` | Long division remainder error | Procedural | Incorrect remainder computation | 47÷5 → 9 r1 |
| `ERR-NF-01` | Common denominator omission | Procedural | Adds/subtracts numerators without common denom | 1/3 + 1/4 → 2/7 |
| `ERR-NF-02` | Fraction-whole confusion | Conceptual | Treats fraction denominator as whole | 3/4 of 8 → 3 |
| `ERR-NF-03` | Equivalent fraction error | Conceptual | Incorrect scaling of numerator/denominator | 1/2 ≠ 2/4 |
| `ERR-NF-04` | Mixed number decomposition | Procedural | Error converting mixed to improper fraction | 2¾ → 9/4 |
| `ERR-MD-01` | Unit conversion error | Conceptual | Confuses metric/customary units | 1 yard = 12 inches |
| `ERR-MD-02` | Area/perimeter confusion | Conceptual | Uses perimeter formula for area problem | Rectangle area = 2(l+w) |
| `ERR-MD-03` | Measurement estimation | Procedural | Off by factor of 10+ on estimation questions | |
| `ERR-G-01` | Angle classification | Conceptual | Mislabels acute/obtuse/right angles | |
| `ERR-G-02` | Line of symmetry error | Conceptual | Identifies non-symmetrical axis | |
| `ERR-GUESS` | Random/guessing | Behavioral | Answer statistically likely to be a guess | Multiple choice: wrong 3+ consecutive, no pattern |

**Feedback Level Determination:**

| Level | Condition | Tutor Instruction |
|---|---|---|
| 1 | First attempt wrong | Deliver Hint Level 1 (subtle nudge) |
| 2 | Second attempt wrong | Deliver Hint Level 2 (conceptual clue) |
| 3 | Third attempt wrong | Deliver Hint Level 3 (worked example), move on |

**System Prompt Template (o3-mini):**

```
You are a precise math assessment engine for 4th-grade students in Oregon.

TASK: Evaluate whether the student's answer is mathematically correct for the given question. 
Classify any error using the provided taxonomy.

RULES:
- Accept mathematically equivalent forms (e.g., "0.75" = "3/4" = "75/100")
- For fraction answers, accept unsimplified fractions if mathematically equal (1/2 = 2/4)
- For word problems, check only the final numerical answer, not units unless units are required
- Classify ONE primary error type. If multiple errors, classify the most fundamental.
- Return JSON only. No prose.

QUESTION: {question_text}
CORRECT ANSWER: {correct_answer}
STUDENT ANSWER: {student_answer}
SOLUTION STEPS: {solution_steps}
ATTEMPT NUMBER: {attempt_number}

Return JSON matching this schema exactly:
{output_schema}
```

**BKT Update Trigger:** After every Assessment Agent response (correct or incorrect), the orchestrator immediately invokes Progress Tracker Agent to update `P(mastered)` before any routing decision.

---

#### Tutor Agent

**Role:** The pedagogical heart of MathPath Oregon. Delivers Socratic, scaffolded guidance that helps students arrive at understanding rather than answers. Never discouraging, always warm, always mathematically precise.

**LLM:** `claude-sonnet-4-6` — selected for explanation quality, instruction-following reliability, and appropriate emotional register for children.

##### Hint Ladder System

Each question in the system has a pre-authored or dynamically generated 3-level hint ladder:

| Level | Name | Character | Constraint | Example (for 4×7=?) |
|---|---|---|---|---|
| 1 | Nudge | Subtle, non-directive | Must NOT reveal operation or answer. Should redirect attention to a key element of the problem. | "Look carefully at what the problem is asking you to find. What does 'times' mean?" |
| 2 | Conceptual Clue | Clear concept, no calculation | Must NOT give numerical steps. Should explain the concept. | "Multiplication means adding equal groups. How many groups of 7 would you need?" |
| 3 | Worked Example | Full scaffolding | Show full solution for a **similar but different** problem, then prompt student to apply same method. | "Let me show you 3×4: that's 3 groups of 4: 4+4+4=12. Now can you try the same with 4 groups of 7?" |

**Pre-authored hint ladder storage:** Each question record in `practice_questions` table has `hint_1`, `hint_2`, `hint_3` fields. For live-generated questions, Tutor Agent generates hints dynamically using the same level constraints.

##### Frustration Detection Protocol

Frustration score is computed in real time and stored in `SessionState.frustration_score` (0–10):

```python
def compute_frustration_score(state: SessionState) -> float:
    score = 0.0

    # Wrong answer streak
    score += min(state["consecutive_wrong"] * 1.5, 4.5)

    # Hints exhausted (at level 3 repeatedly)
    hints_exhausted_count = sum(
        1 for entry in state["session_history"] if entry["hints_used"] >= 3
    )
    score += min(hints_exhausted_count * 1.0, 3.0)

    # "I don't know" button presses this session
    idk_count = sum(
        1 for entry in state["session_history"] if entry.get("idk_pressed", False)
    )
    score += min(idk_count * 0.5, 2.0)

    # Session accuracy drop (if >5 questions answered)
    if state["questions_answered"] > 5:
        recent_accuracy = sum(
            1 for e in state["session_history"][-5:] if e["is_correct"]
        ) / 5.0
        if recent_accuracy < 0.3:
            score += 1.5

    return min(score, 10.0)
```

**Frustration threshold → Scaffolded Mode (`score > 7.0`):**
- Difficulty immediately drops by 0.5 IRT b-parameter
- Hint level auto-advances to Level 2 on first wrong attempt
- Tutor tone shifts to maximum encouragement language
- Session length capped at 5 more questions (avoid burnout)
- Parent notification queued: "Alex had a challenging session today — the app adjusted to help."

##### Explanation Style Adaptation

The Tutor Agent learns each student's preferred explanation style across sessions:

| Style | Description | Detection Signal |
|---|---|---|
| `step_by_step` | Sequential numbered steps | Student accuracy improves after step-by-step hints; requests "show me how" |
| `visual` | Spatial/diagrammatic descriptions | Student accuracy improves after visual hints; responds to "imagine" framing |
| `analogy` | Real-world comparison | Student accuracy improves after analogy hints; responds to story contexts |
| `auto` | Default; system rotates until pattern emerges | Initial state for new students |

Style detection logic: After 15+ hint interactions, compute accuracy improvement rate per hint style delivered. If one style shows >20% higher post-hint accuracy than others, set `preferred_explanation_style` in LTM.

##### Socratic Questioning Protocol

The Tutor Agent must follow this protocol on Hints 1 and 2:

1. **Never state the answer** — not directly, not indirectly through strong hinting
2. **Ask one question** — do not ask multiple questions in a single hint (cognitive overload)
3. **Reference the student's work** — where possible, reference what the student did ("You wrote 7 — can you tell me what the 7 represents?")
4. **Use "I wonder" language** for Hint 1 — "I wonder if the word 'each' gives us a clue..."
5. **Confirm progress** — if student's second attempt is closer to correct (e.g., correct operation but arithmetic error), acknowledge it explicitly

##### Child-Appropriate Language Constraints

All Tutor Agent outputs are post-processed through a language constraint checker before delivery:

- **Flesch-Kincaid Grade Level:** Target 4.0–5.0 for all explanations. Score checked via `textstat` library.
- **Sentence length:** Maximum 15 words per sentence
- **Vocabulary:** No words above 8th-grade Dolch/Fry list without inline definition
- **Banned phrases:** "That's wrong", "Incorrect", "You failed", "No", "That's not right" (replaced by positive redirects: "Almost!", "Good try — let's think about this differently", "You're getting closer!")
- **Maximum response length:** 3 sentences (approximately 45–60 words)

```python
BANNED_NEGATIVE_PHRASES = [
    "that's wrong", "incorrect", "you failed", "that is not right",
    "no,", "wrong answer", "you got it wrong", "mistaken", "error"
]

def validate_tutor_response(response: str) -> tuple[bool, str]:
    """Returns (is_valid, rejection_reason)"""
    import textstat
    fk_grade = textstat.flesch_kincaid_grade(response)
    word_count = len(response.split())

    if fk_grade > 5.5:
        return False, f"Reading level too high: {fk_grade:.1f}"
    if word_count > 75:
        return False, f"Too long: {word_count} words"
    response_lower = response.lower()
    for phrase in BANNED_NEGATIVE_PHRASES:
        if phrase in response_lower:
            return False, f"Contains negative phrase: {phrase}"
    return True, ""
```

If validation fails, the Tutor Agent is re-prompted with the rejection reason and constraint reminder (max 2 retries, then fallback to canned response).

##### Safety Constraints

- **Off-topic deflection:** If student input is not related to the current math problem or general math concepts, Tutor responds: "I'm your math helper for today! Let's stay focused on [skill name]. What part of the problem is tricky for you?"
- **Profanity/inappropriate content:** Input filtered via profanity library pre-prompt; if flagged, Tutor responds: "Let's keep our math work positive! What part of the problem can I help you with?"
- **Personal information attempt:** If student attempts to share personal information in chat (detected via regex for phone/email/address patterns), input is not sent to LLM and Tutor responds with redirect.

**Tutor System Prompt Template (Claude Sonnet 4.6):**

```
You are Pip, a friendly, encouraging math tutor helping a 4th grader in Oregon learn math. 
You are warm, patient, and never make the student feel bad for getting something wrong.

STUDENT CONTEXT:
- Current skill: {skill_name} ({skill_id})
- Learning preference: {preferred_explanation_style}
- Frustration score: {frustration_score}/10
- This is hint #{hint_level} for this question

CURRENT QUESTION:
{question_text}

STUDENT'S ANSWER (incorrect): {student_answer}
ERROR TYPE DETECTED: {error_type} — {error_description}

HINT LEVEL INSTRUCTIONS:
{hint_level_instruction}

RECENT SESSION HISTORY (last 3 interactions):
{tutor_context}

RULES — READ CAREFULLY:
1. Write exactly 2-3 sentences maximum.
2. NEVER give the answer directly.
3. Use simple words (Grade 4-5 reading level).
4. Be warm and encouraging — start with brief praise if student tried.
5. Ask ONE question at the end to guide student thinking.
6. If hint_level = 3, show a worked example with a DIFFERENT but similar problem, then ask student to try theirs.
7. Reference the student's actual answer when possible.
8. Do not mention grades, other students, or performance comparisons.

Respond with ONLY the hint text. No JSON, no labels, no explanation of your reasoning.
```

---

#### Question Generator Agent

**Role:** Select or generate the next practice question, ensuring it is at the right difficulty, covers the right skill, and provides variety in context and presentation.

**LLM:** `o3-mini` (for live generation) + PostgreSQL query (for cached selection)

##### Selection Logic (Priority Order)

```
1. CACHED SELECTION (preferred — faster, pre-validated):
   Query practice_questions WHERE:
     skill_id = current_skill_id
     AND difficulty_b BETWEEN (theta - 0.5) AND (theta + 0.5)
     AND question_id NOT IN (session_history[].question_id)
     AND question_id NOT IN (student_recent_history last 48h)
   If result count > 0: SELECT randomly from top 5 matches

2. LIVE GENERATION (fallback — used when cache empty or diversity required):
   Call o3-mini with question generation prompt
   Validate generated question against Oregon standard
   Run answer verification (generate question + solve independently, confirm match)
   Store generated question in practice_questions with is_generated=true

3. PREREQUISITE CHECK (before ANY selection):
   If advancing to new skill:
     Query bkt_states WHERE skill_id IN prerequisite_skills
     ALL must have p_mastered >= 0.95
     If not: override skill selection → route to weakest prerequisite
```

##### IRT Difficulty Targeting

```python
def select_target_difficulty(theta: float, session_mode: str) -> tuple[float, float]:
    """
    Returns (b_min, b_max) for question selection.
    theta: current IRT ability estimate
    """
    if session_mode == "challenge":
        return (theta + 0.3, theta + 1.0)    # Above current ability
    elif session_mode == "scaffolded":
        return (theta - 1.0, theta - 0.3)    # Well below current ability
    elif session_mode == "review":
        return (theta - 0.5, theta + 0.0)    # Slightly below (should be easy)
    else:  # adaptive (default)
        return (theta - 0.3, theta + 0.5)    # ZPD targeting
```

##### Context Diversity Rules

To prevent monotony, the Question Generator enforces:
- No repeated `context_theme` in the same session (rotate through: Oregon wildlife, food, sports, family, school, space, nature, community)
- No repeated question structure (MC → numeric → fraction → drag_drop → MC…)
- For word problems: character names rotated (Oregon-appropriate names: Mia, Caleb, Sofía, Ethan, Luna, Jaylen, Hazel, Diego)
- Minimum 2 word problems per 10-question session (Oregon OSAS format expectation)

##### Live Generation Prompt Template (o3-mini):

```
You are a math question generator for 4th-grade Oregon students.

TASK: Generate ONE math question for the following specification.

SKILL: {skill_name} — {skill_description}
OREGON STANDARD: {standard_id}
TARGET DIFFICULTY: {b_parameter} on IRT scale (−3 to +3; 0 = grade level)
QUESTION TYPE: {question_type}
CONTEXT THEME: {context_theme}
EXCLUDE THESE CONTEXTS USED THIS SESSION: {used_contexts}

REQUIREMENTS:
- The question must directly assess {standard_id}
- Use Oregon-relevant context: {context_theme} (e.g., Oregon wildlife, Willamette Valley, Portland, Oregon coast)
- Reading level: Grade 3-4 Flesch-Kincaid
- One correct answer only (no ambiguity)
- For multiple choice: 4 options, exactly 1 correct, 3 plausible distractors based on common errors

Return ONLY valid JSON matching this schema:
{
  "question_text": "...",
  "question_type": "multiple_choice|numeric|fraction|drag_drop",
  "options": ["A", "B", "C", "D"],      // null if not multiple_choice
  "correct_answer": "...",
  "solution_steps": ["step 1", "step 2", ...],
  "difficulty_b": 0.0,                  // your estimate on IRT scale
  "hint_1": "...",                      // subtle nudge, no answer
  "hint_2": "...",                      // conceptual clue
  "hint_3": "...",                      // worked example with DIFFERENT numbers
  "context_theme": "{context_theme}",
  "standard_id": "{standard_id}"
}
```

##### Answer Verification (Live Generation Only)

To prevent incorrect questions from reaching students, every live-generated question undergoes verification:

```python
async def verify_generated_question(question: dict) -> bool:
    """Double-check: generate question, solve independently, verify answer matches."""
    verification_prompt = f"""
    Solve this math problem step by step and give the final answer:
    {question['question_text']}
    Return JSON: {{"answer": "...", "steps": [...]}}
    """
    verification_result = await o3_mini_call(verification_prompt)
    return answers_equivalent(verification_result["answer"], question["correct_answer"])
```

If verification fails: regenerate (max 3 attempts). If still failing: fall back to cached question.

---

#### Progress Tracker Agent

**Role:** Maintain the mathematical source of truth about what each student knows. Update BKT probability estimates, persist long-term memory, and generate session summaries. This agent contains no LLM — it is pure deterministic computation.

**Implementation:** Python module using `pyBKT` library + direct PostgreSQL writes.

##### BKT Update Equations

Standard Bayesian Knowledge Tracing (Corbett & Anderson, 1994) with the following parameters per skill:

| Parameter | Symbol | Description | Initialization |
|---|---|---|---|
| P(Known₀) | L₀ | Prior probability of knowing the skill | From diagnostic assessment result |
| P(Transit) | T | Prob of learning skill after one opportunity | Default: 0.09 (calibrated per skill) |
| P(Slip) | S | Prob of wrong answer despite knowing | Default: 0.10 |
| P(Guess) | G | Prob of right answer despite not knowing | Default: 0.20 |

**After a CORRECT response:**

```
P(Known | correct) = [P(Known) × (1 - S)] / [P(Known) × (1 - S) + (1 - P(Known)) × G]

Then transit:
P(Known_new) = P(Known | correct) + (1 - P(Known | correct)) × T
```

**After an INCORRECT response:**

```
P(Known | incorrect) = [P(Known) × S] / [P(Known) × S + (1 - P(Known)) × (1 - G)]

Then transit:
P(Known_new) = P(Known | incorrect) + (1 - P(Known | incorrect)) × T
```

**Python implementation:**

```python
def bkt_update(p_known: float, is_correct: bool,
               p_transit: float, p_slip: float, p_guess: float) -> float:
    """
    Update BKT P(Known) after one response opportunity.
    Returns updated P(Known).
    """
    if is_correct:
        # Posterior: probability student knew it given correct answer
        p_known_given_obs = (p_known * (1 - p_slip)) / (
            p_known * (1 - p_slip) + (1 - p_known) * p_guess
        )
    else:
        # Posterior: probability student knew it given incorrect answer
        p_known_given_obs = (p_known * p_slip) / (
            p_known * p_slip + (1 - p_known) * (1 - p_guess)
        )

    # Transit: student may have learned from this opportunity
    p_known_new = p_known_given_obs + (1 - p_known_given_obs) * p_transit

    return p_known_new
```

##### Mastery Threshold

A skill is declared **mastered** when ALL of the following conditions are true:
1. `P(mastered) ≥ 0.95`
2. `correct_streak ≥ 5` (consecutive correct responses, may span sessions)
3. `attempt_count ≥ 5` (minimum exposure, prevents lucky guessing)
4. At least 3 of the 5 correct responses must be at difficulty `b ≥ (student_theta - 0.2)` (not too easy)

When mastery is declared:
- `skill_mastery_states.mastered_at` is set to current timestamp
- Learning plan `module_skills` entry is updated: `status = 'mastered'`
- Next skill in module's prerequisite-respecting order is unlocked
- Session summary includes "You mastered [Skill Name]!" celebration

##### Long-Term Memory Schema

```python
class StudentLongTermMemory(TypedDict):
    student_id: str

    # Skill mastery
    skill_mastery: dict[str, SkillMasteryRecord]  # skill_id → record

    # Learning style preferences
    preferred_explanation_style: str  # "step_by_step" | "visual" | "analogy" | "auto"
    style_confidence: float           # 0.0-1.0; how confident we are in style classification
    style_evidence_count: int         # number of hint interactions used to determine style

    # Error patterns (domain-level)
    error_frequency: dict[str, int]   # error_code → count
    error_last_seen: dict[str, str]   # error_code → ISO timestamp

    # Engagement patterns
    avg_session_length_minutes: float
    best_session_hour: int            # 0-23 (hour of day with highest accuracy)
    typical_questions_per_session: float
    avg_session_accuracy: float

    # Milestone history
    milestones: List[MilestoneRecord]

    last_updated: datetime

class SkillMasteryRecord(TypedDict):
    skill_id: str
    p_mastered: float
    p_transit: float
    p_slip: float
    p_guess: float
    correct_streak: int
    attempt_count: int
    mastered_at: Optional[datetime]   # null if not yet mastered
    mastery_history: List[dict]       # [{p_mastered, timestamp}] — last 50 updates
    estimated_time_to_mastery: Optional[float]  # minutes, ML-estimated
```

##### Session Summary Generation

Triggered at session end (≥5 minutes elapsed OR ≥10 questions answered):

```python
def generate_session_summary(state: SessionState, ltm: StudentLongTermMemory) -> dict:
    return {
        "session_id": state["session_id"],
        "duration_minutes": (datetime.now() - state["session_start_time"]).seconds / 60,
        "questions_answered": state["questions_answered"],
        "questions_correct": state["questions_correct"],
        "accuracy_pct": round(state["questions_correct"] / state["questions_answered"] * 100),
        "skills_practiced": list(set(e["skill_id"] for e in state["session_history"])),
        "skills_mastered_this_session": [
            s for s, r in state["bkt_states"].items()
            if r["p_mastered"] >= 0.95 and r["correct_streak"] >= 5
        ],
        "bkt_gains": {  # p_mastered delta vs session start
            skill_id: state["bkt_states"][skill_id]["p_mastered"] - ltm["skill_mastery"][skill_id]["p_mastered"]
            for skill_id in state["bkt_states"]
        },
        "hints_used_total": sum(e["hints_used"] for e in state["session_history"]),
        "frustration_peak": max(
            # computed across session, stored in history
            state.get("frustration_peak", 0.0),
            state["frustration_score"]
        ),
        "next_skill_preview": None  # populated by learning plan module
    }
```

---

## 3.3 Functional Requirements

### FR-11: Practice Session UI

#### FR-11.1: Session Start Screen
- Display the current skill name (human-readable: "Adding Fractions with Like Denominators") and Oregon standard code (4.NF.B.3)
- Show estimated session time: "About 10 minutes"
- Display student's progress in the current module: "Skill 3 of 6 in Fractions"
- Mascot Pip delivers a contextual welcome message based on recent performance:
  - If previous session accuracy ≥ 70%: "Great job last time! Ready to keep going?"
  - If previous session accuracy < 50%: "Today's a fresh start — let's practice together!"
- CTA button: "Start Practice" (large, prominent, tappable — minimum 44×44px touch target per WCAG)
- Secondary option: "Practice a different skill" (shows alternative available skills from learning plan)

#### FR-11.2: Question Display
- Question text rendered at minimum 18px font (desktop), 20px (mobile)
- Mathematical expressions rendered via **KaTeX** (client-side, zero-latency):
  - Fractions: `\frac{3}{4}` renders as proper fraction display
  - Multiplication: `\times` symbol (not ×)
  - Division: `\div` symbol
  - Equations: inline and display math modes
- Word problem images (where provided): max-width 100% of question container, alt-text required
- Question number indicator: "Question 3 of 10"
- Skill indicator banner: "Skill: Equivalent Fractions" (subtle, non-distracting)

#### FR-11.3: Answer Input Modes

**Multiple Choice (MC):**
- 4 answer options displayed as large tappable cards (full-width on mobile)
- Option labels: A, B, C, D
- Selected state: highlighted border + background color change (not just color — shape change for color-blind accessibility)
- Submit button appears after selection (does not auto-submit on tap — prevents accidental submission)
- Options rendered with KaTeX if they contain math expressions

**Numeric Keypad:**
- Custom numeric keypad (no system keyboard) for whole number answers
- Includes: 0-9, decimal point, negative sign, backspace, clear, submit
- Display field shows current entry (large, visible)
- Validation: rejects non-numeric input, highlights field red if empty on submit

**Fraction Input Widget:**
- Two stacked input fields: numerator (top) and denominator (bottom)
- Horizontal fraction bar between them (styled via CSS)
- Separate numeric pads for each field
- Tab/tap to switch between numerator and denominator
- Validation: denominator cannot be 0 (error message: "The bottom number of a fraction can't be zero!")

**Drag-and-Drop (Ordering/Matching):**
- Touch-enabled drag handles on mobile (HammerJS or similar)
- Keyboard accessible: tab to select, arrow keys to reorder
- Drop zones visually indicated with dashed borders
- Snap-to-grid animation on drop
- Reset button: returns all items to original positions

#### FR-11.4: Hint System UI
- "Need a hint?" button: appears after first incorrect attempt (not before)
- Button styling: warm color, animated pulse (subtle — 1 pulse per 8 seconds to draw attention without distraction)
- Hint display: speech bubble style emanating from mascot Pip
- Hint text fades in (300ms fade animation)
- Hint counter: "Hint 1 of 3" shown in hint bubble header
- Each hint level has distinct visual treatment:
  - Level 1: yellow background ("Nudge")
  - Level 2: orange background ("Clue")
  - Level 3: blue background ("Explanation") with "Let's look at an example" header
- After Level 3 hint is shown: "Next question" button appears (student moves on, answer shown)

#### FR-11.5: "I Don't Know" Button
- Displayed alongside "Need a hint?" after first wrong attempt
- Pressing once: triggers Level 2 hint immediately + sets a soft flag
- Pressing twice in one session: triggers `session_mode = "scaffolded"` + frustration score += 2.0
- Button label: "I need more help" (not "I don't know" — avoids negative self-labeling)

#### FR-11.6: Correct Answer Celebration
- Immediate positive feedback: Pip mascot animates (simple bounce/sparkle — CSS animation, not video)
- Text feedback: randomly selected from approved responses:
  - "That's right! Great work!"
  - "You got it! 🌟"
  - "Excellent thinking!"
  - "Nice job — you're getting this!"
- Duration: 1.5 seconds, then auto-advance to next question (with 0.5s pause)
- Session streak indicator: if 3+ consecutive correct, show "3 in a row!" badge
- **Intentionally not over-the-top:** no full-screen explosions, no 5-second animations — brief and warm

#### FR-11.7: Wrong Answer Feedback
- Gentle, encouraging response:
  - First attempt: "Good try! Would you like a hint?" (Hint button highlights)
  - Second attempt: "You're getting closer — let's look at a clue!" (auto-show Level 2 hint)
  - Third attempt: Level 3 hint shown automatically, answer revealed, "Let's try the next one"
- No negative sounds (no buzzer, no sad music)
- Answer field cleared and refocused for retry

#### FR-11.8: Session Progress Bar
- Horizontal progress bar at top of session screen
- Fills left-to-right as questions are completed
- Color: green fill on neutral background
- Tick marks at every 2 questions (for 10-question sessions)
- Tooltip on hover (desktop): "3 of 10 questions complete"
- Accessible label: aria-label="Session progress: 3 of 10 questions"

#### FR-11.9: Pause / Resume
- Pause button: top-right of session screen (icon button with label)
- On pause: session timer pauses, question blurred (integrity), overlay shown: "Session paused. Ready to continue?"
- Resume button: resumes from exact state (question, hint state, progress)
- Session state persisted in Redis on every question transition (survives browser refresh)
- Maximum pause duration: 30 minutes. After 30 min: session auto-ended, progress saved, student prompted to start new session

#### FR-11.10: Session Summary Screen
- Displayed at session end
- Sections:
  1. **Overall:** "You answered 8 out of 10 questions correctly! (80%)"
  2. **Progress:** "You made progress on: Adding Fractions (4.NF.B.3)" — BKT gauge showing P(mastered) before and after
  3. **Mastery unlocked (if applicable):** "You mastered: Equivalent Fractions! 🎉" — skill badge animation
  4. **Time:** "You practiced for 12 minutes"
  5. **Encouragement:** Pip delivers contextual message based on session accuracy
  6. **Next up:** "Next: Adding Fractions with Unlike Denominators — unlocking in [X more questions on current skill]"
- CTAs: "Keep going!" (starts next session on current or next skill) and "I'm done for now" (exits to dashboard)

#### FR-11.11: Mascot (Pip)
- Pip is a friendly, gender-neutral animated character (placeholder: SVG-based)
- Appears: session start, correct answers, end of session, hint delivery
- Pip does NOT appear during questions (avoids distraction)
- Pip has 5 animation states: neutral, happy, thinking, encouraging, celebrating
- Animations: CSS keyframe animations (performant, no video files for initial release)
- WCAG: all Pip animations respect `prefers-reduced-motion` media query (static images shown if user prefers)

#### FR-11.12: Conversational Tutor Interface (within session)
- Text input field at bottom of question screen (collapsible; expands on tap)
- Suggested prompt chips: "Show me a hint", "I don't understand this", "Can you explain differently?", "What does [word] mean?"
- Student types or selects; Tutor Agent responds in chat bubble
- Max 3 exchanges visible at once (scrollable history within session)
- Profanity filter on student input (pre-send)
- If input is off-topic: Tutor deflects as specified in agent spec
- Interface collapses when student is entering answer (reduce distraction)

---

### FR-12: Adaptive Difficulty Adjustment

#### FR-12.1: Real-Time Difficulty Adjustment
After each response (correct or incorrect), the system recomputes:
1. Updated `P(mastered)` via BKT (Progress Tracker Agent)
2. Updated `theta` (IRT ability estimate) using EAP (Expected A Posteriori) estimation
3. New target difficulty range `[theta - 0.3, theta + 0.5]`
4. Next question selected from this range by Question Generator Agent

IRT theta update (simplified EAP for real-time use):
```python
def update_theta_eap(theta: float, is_correct: bool, b: float,
                      a: float = 1.0, c: float = 0.25) -> float:
    """
    Simple online theta update using gradient of log-likelihood.
    a = discrimination, b = difficulty, c = guessing parameter.
    """
    p = c + (1 - c) / (1 + math.exp(-a * (theta - b)))
    gradient = a * (1 - c) * math.exp(-a * (theta - b)) / (
        (1 + math.exp(-a * (theta - b)))**2 * p
    )
    if is_correct:
        delta = 0.1 * (1 - p) * gradient / p
    else:
        delta = -0.1 * p * gradient / (1 - p)
    return max(-3.0, min(3.0, theta + delta))
```

#### FR-12.2: IRT-Based Question Selection
- Question database: each question has `difficulty_b` (IRT b-parameter), `discrimination_a`, `guessing_c`
- Selection: query for questions where `difficulty_b BETWEEN (theta - 0.3) AND (theta + 0.5)`
- If fewer than 3 cached questions in range: widen to `±0.8`, then trigger live generation if still empty
- For multiple qualifying questions: select the one with highest information value:
  ```
  I(theta) = a² × P(theta) × (1 - P(theta)) / c²
  ```
  (Fisher Information — most informative question for current theta)

#### FR-12.3: BKT Mastery Gating
- A student will not be advanced to a new skill until:
  - `P(mastered) ≥ 0.95` for current skill
  - `correct_streak ≥ 5`
  - `attempt_count ≥ 5`
- Prerequisite graph enforced: if Skill B requires Skill A, Skill A must be mastered first
- Exception: during "review" mode, students may revisit mastered skills (no mastery gate check needed)

#### FR-12.4: Spiral Review
- Every 5th session, the session begins with 1-2 "review warm-up" questions per previously mastered skill
- Review questions target difficulty `b ≈ theta - 0.5` (should be answerable correctly to maintain confidence)
- If student answers review question incorrectly: `P(mastered)` is downgraded by BKT update; skill may be re-added to active learning plan
- Review questions are labeled "Quick Review" on question display
- Spiral review is not announced to student in advance (prevents gaming)

#### FR-12.5: Struggle Detection & Response
- Trigger: 3+ consecutive incorrect responses on same or adjacent skills
- Response actions (in order):
  1. Immediately lower target difficulty by 0.5 IRT b-parameter
  2. Escalate hint level: next wrong answer → Level 2 hint (not Level 1)
  3. If frustration_score > 5.0: switch to scaffolded mode
  4. After session: flag skill for increased practice frequency in learning plan

#### FR-12.6: Acceleration Detection
- Trigger: 5+ consecutive correct responses on questions at difficulty `b ≥ theta`
- Response: offer "Challenge Mode" — optional, student must opt in
  - CTA: "Wow, you're on a roll! Want to try some harder problems?"
  - If accepted: target difficulty rises to `theta + 0.5` to `theta + 1.2`
  - Challenge Mode badge shown on session summary
  - BKT and theta update normally in challenge mode

#### FR-12.7: Session Length Adaptation
- **Fatigue detection** (ALL must be true):
  - Session duration > 20 minutes
  - Last 5 questions accuracy < 40%
  - Response times increasing (>20% longer than session average)
  - Action: Pip says "You've been working hard! Want to take a break?" → offer to end session
- **Engagement extension** (session at 10 questions):
  - If student accuracy ≥ 80% AND frustration_score < 3.0:
  - Offer: "Nice work! Keep going?" (extend by 5 more questions, max 20 total)
- **Hard caps:** Maximum session length: 30 minutes regardless of engagement (child welfare)

#### FR-12.8: Cross-Session Continuity
- On session start: load most recent `bkt_states` from PostgreSQL for all skills in active learning plan
- `theta` estimate initialized from last session's final theta (or re-estimated from BKT P(mastered) if session gap > 7 days)
- If session gap > 14 days: apply "forgetting" adjustment:
  ```python
  days_since = (datetime.now() - last_session_date).days
  if days_since > 14:
      forgetting_factor = max(0.85, 1.0 - (days_since - 14) * 0.005)
      p_mastered_adjusted = p_mastered * forgetting_factor
  ```
- Hint ladder resets per question (not carried over from previous sessions)

---

### FR-13: Dual Memory System

#### FR-13.1: Long-Term Memory (LTM) — PostgreSQL

LTM persists across all sessions. Updated by Progress Tracker Agent at session end (and for mastery events: immediately).

**skill_mastery_states table** (one row per student-skill pair):
```sql
CREATE TABLE skill_mastery_states (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id      UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    skill_id        VARCHAR(20) NOT NULL REFERENCES standards(standard_id),
    p_mastered      FLOAT NOT NULL DEFAULT 0.0,
    p_transit       FLOAT NOT NULL DEFAULT 0.09,
    p_slip          FLOAT NOT NULL DEFAULT 0.10,
    p_guess         FLOAT NOT NULL DEFAULT 0.20,
    correct_streak  INTEGER NOT NULL DEFAULT 0,
    attempt_count   INTEGER NOT NULL DEFAULT 0,
    mastered_at     TIMESTAMPTZ,
    last_updated    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT p_mastered_valid CHECK (p_mastered BETWEEN 0.0 AND 1.0),
    CONSTRAINT unique_student_skill UNIQUE (student_id, skill_id)
);
CREATE INDEX idx_skill_mastery_student ON skill_mastery_states(student_id);
```

**student_learning_preferences table:**
```sql
CREATE TABLE student_learning_preferences (
    student_id              UUID PRIMARY KEY REFERENCES students(id) ON DELETE CASCADE,
    preferred_style         VARCHAR(20) NOT NULL DEFAULT 'auto',
    style_confidence        FLOAT NOT NULL DEFAULT 0.0,
    style_evidence_count    INTEGER NOT NULL DEFAULT 0,
    avg_session_length_min  FLOAT,
    best_session_hour       INTEGER,
    avg_session_accuracy    FLOAT,
    last_updated            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT style_valid CHECK (preferred_style IN ('step_by_step','visual','analogy','auto'))
);
```

**student_error_patterns table:**
```sql
CREATE TABLE student_error_patterns (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id      UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    error_code      VARCHAR(20) NOT NULL,
    error_count     INTEGER NOT NULL DEFAULT 1,
    last_seen       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    domain          VARCHAR(10) NOT NULL,
    CONSTRAINT unique_student_error UNIQUE (student_id, error_code)
);
CREATE INDEX idx_error_student ON student_error_patterns(student_id);
```

#### FR-13.2: Working Memory (WM) — Redis

WM is session-scoped. Created at session start, expires 24 hours after session end (to allow parent/teacher review of session data).

**Redis Key Structure:**
```
wm:{session_id}:context        → JSON: List[WorkingMemoryEntry] (last 10 Q&A pairs)
wm:{session_id}:trajectory     → JSON: List[{question_id, b, is_correct, theta}]
wm:{session_id}:tutor_ctx      → JSON: List[{role, content}] (last 3 tutor exchanges)
wm:{session_id}:frustration    → Float (current frustration score)
wm:{session_id}:state          → JSON: Full SessionState snapshot
```

**TTL policy:**
- All WM keys: `EXPIRE wm:{session_id}:* 86400` (24 hours from last write)
- On session end: `EXPIRE wm:{session_id}:* 86400` (reset timer to 24h from end)
- On session resume (within 30 min): restore full state from `wm:{session_id}:state`

#### FR-13.3: Memory Retrieval in Agent Prompts

Each agent receives a curated subset of memory in its prompt context:

| Agent | LTM Injected | WM Injected |
|---|---|---|
| Assessment Agent | Error patterns for this skill (top 3) | Last 2 Q&A pairs |
| Tutor Agent | Preferred style, frustration score, error type | Last 3 tutor interactions |
| Question Generator | Mastery history, session question history | Full difficulty trajectory |
| Progress Tracker | Full skill mastery record | Full session context |

#### FR-13.4–FR-13.8: Additional Memory Requirements
- **FR-13.4 Mastery timestamps:** `mastered_at` field in `skill_mastery_states` — used for milestone notifications and reporting
- **FR-13.5 LTM retention:** Per privacy policy: LTM retained while account is active + 90 days post-deletion (COPPA). All records pseudonymized with `student_id` UUID (no name/email in LTM tables).
- **FR-13.6 WM expiry:** Session WM expires 24 hours after session end. Parent can review session transcript within this window.
- **FR-13.7 Estimated time-to-mastery:** ML estimate stored in `student_learning_preferences.estimated_time_to_mastery` per skill. Computed from: average attempts to mastery across similar students (PostgreSQL aggregate), adjusted for current P(mastered).
- **FR-13.8 LTM write optimization:** BKT state writes use PostgreSQL `INSERT ... ON CONFLICT DO UPDATE` (upsert). Batch write at session end (not per-question) except for mastery events (immediate write).

---

### FR-14: Conversational Tutor Interface

#### FR-14.1: Interface Scope
- The in-session chat interface is a constrained, math-focused channel
- Not a general-purpose chatbot — Tutor Agent is explicitly scoped to:
  - Hints for the current question
  - Explanations of the current skill concept
  - Definitions of math vocabulary in the curriculum
  - Encouragement and motivation
- Out of scope: homework help for other subjects, personal conversation, information retrieval

#### FR-14.2: Student Input Methods
- **Free-text input:** Keyboard (mobile: software keyboard triggers on tap)
- **Suggested prompt chips:** Pre-defined phrases displayed above input field:
  - "Show me a hint"
  - "I don't understand this"
  - "Can you explain differently?"
  - "What does [word] mean?" — [word] is dynamically populated from the current question's vocabulary
  - "Can you give me an example?"
- Chips are scrollable horizontally (up to 6 chips visible at once)
- Student can tap a chip OR type custom message

#### FR-14.3: Tutor Response Format
- Text response in speech bubble (left-aligned, Pip icon at left)
- Optional visual aid: if Tutor references a diagram or visual, it is described in text (Stage 3) or as a simple SVG (Stage 5)
- Math in response: rendered via KaTeX inline
- Response delivered with a typing indicator (3-dot animation, max 3 seconds before response or timeout)
- On timeout (>5 seconds): fallback to canned response from appropriate hint level

#### FR-14.4: Conversation Scoping
- Tutor Agent receives system prompt instruction: "You may ONLY discuss the current question and the math skill it tests. If asked anything else, redirect warmly to the current math problem."
- Off-topic detection: Tutor Agent handles via system prompt (no separate classifier in v1)
- Math vocabulary questions: allowed even if not on the current question (e.g., "what is a denominator?" is in-scope for any fraction question)

#### FR-14.5: Safety Filtering
**Pre-send (client-side):**
- Profanity list check: simple client-side wordlist (fast, prevents obvious cases)
- Personal info regex: detect patterns matching phone numbers, email addresses
- If flagged: message not sent; instead show: "Let's keep our math chat positive!"

**Post-response (server-side):**
- All tutor responses logged to `agent_interaction_logs`
- Automated moderation: `better-profanity` Python library on all responses
- If a response fails moderation (should be rare with good prompt): replace with canned fallback, alert engineering team via Slack webhook

#### FR-14.6: Response Length Constraints
- Tutor Agent system prompt enforces: "Write exactly 2-3 sentences. Maximum 60 words."
- Server-side truncation: if response exceeds 75 words, truncate at sentence boundary + append "Would you like more explanation?"
- This is a hard constraint, not a guideline.

#### FR-14.7: Conversation History Display
- Last 3 exchanges (student message + Pip response) visible in session
- Earlier messages accessible via scroll (within session)
- Each exchange timestamped (relative: "2 min ago")
- Student's messages: right-aligned blue bubbles
- Pip's responses: left-aligned, white/cream bubbles with Pip icon

#### FR-14.8: Parent Conversation Review
- All tutor conversation exchanges stored in `session_responses` table (text of student input + tutor response)
- Parent dashboard: "Session Transcript" tab within each session detail view
- Shows full conversation history for any completed session
- Data retained per LTM retention policy (account active + 90 days)
- Parents can flag a conversation for review (sends alert to support team)

---

## 3.4 Non-Functional Requirements

| Requirement | Target | Measurement | Priority |
|---|---|---|---|
| Tutor Agent P95 response latency | < 3 seconds | APM (Datadog/New Relic) | P0 |
| Question selection (cached) | < 500ms end-to-end | APM | P0 |
| Question generation (live) | < 8 seconds | APM | P1 |
| BKT update latency | < 100ms | APM (in-process timing) | P0 |
| LLM cost per 10-question session | < $0.15 | AWS Cost Explorer | P0 |
| Concurrent sessions supported | 500 (Stage 3 target) | Load test | P1 |
| Session state persistence | Survive browser refresh | QA test: refresh mid-session | P0 |
| Session state survival (network drop) | Survive up to 30 min of network interruption, resume on reconnect | QA | P1 |
| Uptime during school hours | 99.5% | CloudWatch | P0 |
| COPPA: PII in LLM logs | Zero PII in any prompt sent to LLM | Log audit | P0 |
| Child language compliance | FK Grade 4.0-5.5 on ≥ 95% of tutor responses | Automated post-hoc scoring | P0 |
| Accessibility | WCAG 2.1 AA | Axe automated scan + manual audit | P0 |
| Math rendering correctness | KaTeX renders correctly on iOS Safari, Chrome Android, Chrome Desktop, Firefox | QA cross-browser | P0 |

---

## 3.5 LangGraph State & Flow Specification

### Complete Graph Definition

```python
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.redis import RedisSaver

# All agent functions are imported from their respective modules
from agents.assessment import assessment_agent
from agents.tutor import tutor_agent
from agents.question_generator import question_generator_agent
from agents.progress_tracker import progress_tracker_agent

def build_practice_graph() -> StateGraph:
    graph = StateGraph(SessionState)

    # ── Nodes ────────────────────────────────────────────────────────────────
    graph.add_node("session_init", session_init_node)
    graph.add_node("question_generator", question_generator_agent)
    graph.add_node("await_answer", await_answer_node)       # WebSocket pause
    graph.add_node("assessment", assessment_agent)
    graph.add_node("tutor", tutor_agent)
    graph.add_node("progress_tracker", progress_tracker_agent)
    graph.add_node("session_end", session_end_node)

    # ── Entry point ──────────────────────────────────────────────────────────
    graph.set_entry_point("session_init")

    # ── Edges ────────────────────────────────────────────────────────────────
    graph.add_edge("session_init", "question_generator")
    graph.add_edge("question_generator", "await_answer")

    # Conditional: after assessment
    graph.add_conditional_edges(
        "assessment",
        route_after_assessment,
        {
            "tutor": "tutor",
            "progress_tracker": "progress_tracker",
            "end": "session_end"
        }
    )

    # After tutor delivers hint → await new answer attempt
    graph.add_edge("tutor", "await_answer")

    # Conditional: after await_answer (student submits)
    graph.add_conditional_edges(
        "await_answer",
        route_after_await,      # checks if answer received or timeout
        {
            "assessment": "assessment",
            "end": "session_end"   # student clicked "End Session"
        }
    )

    # Conditional: after progress tracker
    graph.add_conditional_edges(
        "progress_tracker",
        route_after_progress_tracker,
        {
            "question_generator": "question_generator",
            "end": "session_end"
        }
    )

    graph.add_edge("session_end", END)

    # ── Checkpointing (for pause/resume) ────────────────────────────────────
    memory = RedisSaver.from_conn_string(settings.REDIS_URL)
    return graph.compile(checkpointer=memory)

practice_graph = build_practice_graph()
```

### Node Specifications

| Node | Type | Description |
|---|---|---|
| `session_init` | Sync function | Load BKT states from PostgreSQL, initialize WM in Redis, set `next_agent = "question_generator"` |
| `question_generator` | Async LLM agent | Select or generate next question, update `current_question` in state |
| `await_answer` | Async WebSocket wait | Pause graph execution; resume when student submits answer via WebSocket |
| `assessment` | Async LLM agent | Evaluate answer; set `is_correct`, `error_type`, `feedback_level`, `next_agent` |
| `tutor` | Async LLM agent | Generate hint/explanation based on `feedback_level` and `error_type` |
| `progress_tracker` | Sync Python | Update BKT, update WM, check mastery, determine `session_complete` |
| `session_end` | Async function | Write LTM, generate summary, expire WM (set 24h TTL) |

### Terminal States

- `session_complete = True` in state → route to `session_end`
- `questions_answered >= 10` → route to `session_end`
- Student WebSocket sends `{"action": "end_session"}` → `await_answer` routes to `session_end`
- Session duration > 30 minutes → Progress Tracker sets `session_complete = True`

---

## 3.6 Data Models

### New Tables for Stage 3

#### practice_sessions
```sql
CREATE TABLE practice_sessions (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id          UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    learning_plan_id    UUID NOT NULL REFERENCES learning_plans(id),
    session_number      INTEGER NOT NULL,  -- session count for this student
    started_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ended_at            TIMESTAMPTZ,
    duration_seconds    INTEGER,
    session_mode        VARCHAR(20) NOT NULL DEFAULT 'adaptive',
    questions_answered  INTEGER NOT NULL DEFAULT 0,
    questions_correct   INTEGER NOT NULL DEFAULT 0,
    accuracy_pct        FLOAT,
    frustration_peak    FLOAT DEFAULT 0.0,
    skills_practiced    TEXT[] NOT NULL DEFAULT '{}',
    skills_mastered     TEXT[] NOT NULL DEFAULT '{}',
    session_summary     JSONB,
    langgraph_thread_id VARCHAR(100),  -- for graph checkpointing
    CONSTRAINT session_mode_valid CHECK (session_mode IN (
        'adaptive','scaffolded','challenge','review'
    ))
);
CREATE INDEX idx_sessions_student ON practice_sessions(student_id);
CREATE INDEX idx_sessions_started ON practice_sessions(started_at DESC);
```

#### session_questions
```sql
CREATE TABLE session_questions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id      UUID NOT NULL REFERENCES practice_sessions(id) ON DELETE CASCADE,
    question_id     UUID REFERENCES practice_questions(id),  -- null if generated live
    sequence_num    INTEGER NOT NULL,   -- 1-based order within session
    skill_id        VARCHAR(20) NOT NULL REFERENCES standards(standard_id),
    question_text   TEXT NOT NULL,
    question_type   VARCHAR(20) NOT NULL,
    correct_answer  TEXT NOT NULL,
    difficulty_b    FLOAT NOT NULL,
    theta_at_time   FLOAT,             -- IRT theta when question was served
    is_generated    BOOLEAN NOT NULL DEFAULT FALSE,
    generated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT sequence_positive CHECK (sequence_num > 0)
);
CREATE INDEX idx_sq_session ON session_questions(session_id);
```

#### session_responses
```sql
CREATE TABLE session_responses (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id          UUID NOT NULL REFERENCES practice_sessions(id) ON DELETE CASCADE,
    session_question_id UUID NOT NULL REFERENCES session_questions(id),
    attempt_number      INTEGER NOT NULL,   -- 1 = first attempt, 2 = second, etc.
    student_answer      TEXT NOT NULL,
    is_correct          BOOLEAN NOT NULL,
    error_type          VARCHAR(30),
    error_code          VARCHAR(20),
    response_time_ms    INTEGER,
    hints_used_before   INTEGER NOT NULL DEFAULT 0,
    responded_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    -- Tutor conversation for this response
    student_message     TEXT,   -- if student typed something before answering
    tutor_response      TEXT,   -- last tutor response before this attempt
    CONSTRAINT attempt_positive CHECK (attempt_number > 0)
);
CREATE INDEX idx_sr_session ON session_responses(session_id);
CREATE INDEX idx_sr_session_question ON session_responses(session_question_id);
```

#### hint_interactions
```sql
CREATE TABLE hint_interactions (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id          UUID NOT NULL REFERENCES practice_sessions(id) ON DELETE CASCADE,
    session_question_id UUID NOT NULL REFERENCES session_questions(id),
    hint_level          INTEGER NOT NULL,   -- 1, 2, or 3
    trigger_type        VARCHAR(20) NOT NULL,  -- 'button_press','idk_button','auto_trigger'
    hint_text           TEXT NOT NULL,
    explanation_style   VARCHAR(20),        -- style used for this hint
    followed_by_correct BOOLEAN,           -- did student get correct after this hint?
    response_time_ms    INTEGER,           -- time from hint display to next attempt
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT hint_level_valid CHECK (hint_level BETWEEN 1 AND 3)
);
CREATE INDEX idx_hint_session ON hint_interactions(session_id);
```

#### bkt_state_history
```sql
CREATE TABLE bkt_state_history (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id      UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    skill_id        VARCHAR(20) NOT NULL REFERENCES standards(standard_id),
    session_id      UUID REFERENCES practice_sessions(id),
    p_mastered      FLOAT NOT NULL,
    p_transit       FLOAT NOT NULL,
    p_slip          FLOAT NOT NULL,
    p_guess         FLOAT NOT NULL,
    correct_streak  INTEGER NOT NULL DEFAULT 0,
    attempt_count   INTEGER NOT NULL DEFAULT 0,
    trigger         VARCHAR(30) NOT NULL,  -- 'correct_response','incorrect_response','mastery','forgetting_adjustment'
    recorded_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_bkt_student_skill ON bkt_state_history(student_id, skill_id);
CREATE INDEX idx_bkt_session ON bkt_state_history(session_id);
```

#### student_long_term_memory
```sql
-- This table stores scalar/aggregate LTM fields not covered by skill_mastery_states
CREATE TABLE student_long_term_memory (
    student_id              UUID PRIMARY KEY REFERENCES students(id) ON DELETE CASCADE,
    preferred_style         VARCHAR(20) NOT NULL DEFAULT 'auto',
    style_confidence        FLOAT NOT NULL DEFAULT 0.0,
    style_evidence_count    INTEGER NOT NULL DEFAULT 0,
    avg_session_length_min  FLOAT,
    best_session_hour       INTEGER,        -- 0-23
    avg_session_accuracy    FLOAT,
    total_sessions          INTEGER NOT NULL DEFAULT 0,
    total_practice_minutes  FLOAT NOT NULL DEFAULT 0.0,
    last_session_at         TIMESTAMPTZ,
    last_theta_estimate     FLOAT,
    last_updated            TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

#### agent_interaction_logs
```sql
CREATE TABLE agent_interaction_logs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id      UUID NOT NULL REFERENCES practice_sessions(id) ON DELETE CASCADE,
    agent_name      VARCHAR(30) NOT NULL,   -- 'assessment','tutor','question_generator'
    invocation_num  INTEGER NOT NULL,
    input_tokens    INTEGER,
    output_tokens   INTEGER,
    latency_ms      INTEGER,
    model_used      VARCHAR(50),
    -- Prompt/response stored without PII (student_id only, no name/email)
    prompt_hash     VARCHAR(64),           -- SHA-256 of prompt (for dedup/audit)
    response_hash   VARCHAR(64),
    error_occurred  BOOLEAN NOT NULL DEFAULT FALSE,
    error_message   TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT agent_name_valid CHECK (agent_name IN (
        'assessment','tutor','question_generator','orchestrator'
    ))
);
CREATE INDEX idx_agent_log_session ON agent_interaction_logs(session_id);
CREATE INDEX idx_agent_log_agent ON agent_interaction_logs(agent_name, created_at DESC);
```

#### practice_questions (extended — Stage 3 additions)
```sql
-- New columns added to existing practice_questions table
ALTER TABLE practice_questions ADD COLUMN IF NOT EXISTS difficulty_b FLOAT;
ALTER TABLE practice_questions ADD COLUMN IF NOT EXISTS discrimination_a FLOAT DEFAULT 1.0;
ALTER TABLE practice_questions ADD COLUMN IF NOT EXISTS guessing_c FLOAT DEFAULT 0.25;
ALTER TABLE practice_questions ADD COLUMN IF NOT EXISTS hint_1 TEXT;
ALTER TABLE practice_questions ADD COLUMN IF NOT EXISTS hint_2 TEXT;
ALTER TABLE practice_questions ADD COLUMN IF NOT EXISTS hint_3 TEXT;
ALTER TABLE practice_questions ADD COLUMN IF NOT EXISTS context_theme VARCHAR(50);
ALTER TABLE practice_questions ADD COLUMN IF NOT EXISTS is_generated BOOLEAN DEFAULT FALSE;
ALTER TABLE practice_questions ADD COLUMN IF NOT EXISTS times_served INTEGER DEFAULT 0;
ALTER TABLE practice_questions ADD COLUMN IF NOT EXISTS times_correct INTEGER DEFAULT 0;
```

---

## 3.7 API Endpoints

### WebSocket: Real-Time Session

#### `WS /ws/sessions/{session_id}`

Real-time bidirectional channel for the practice session. All in-session events flow through this socket.

**Client → Server Messages:**

```json
// Start or resume session
{"type": "session_start", "student_id": "stu_abc", "session_id": "ses_xyz"}

// Submit answer
{"type": "answer_submit", "answer": "3/4", "response_time_ms": 12000}

// Request hint
{"type": "hint_request", "hint_level": 1}

// Press "I need more help"
{"type": "idk_press"}

// Send chat message to tutor
{"type": "tutor_message", "message": "I don't understand what 'times' means"}

// Pause session
{"type": "session_pause"}

// Resume session
{"type": "session_resume"}

// End session voluntarily
{"type": "session_end_voluntary"}
```

**Server → Client Messages:**

```json
// Session initialized
{
  "type": "session_ready",
  "session_id": "ses_xyz",
  "current_skill": {"id": "4.NF.B.3", "name": "Adding Fractions with Like Denominators"},
  "session_number": 12,
  "module_progress": {"current": 3, "total": 6}
}

// Next question
{
  "type": "question",
  "sequence_num": 1,
  "question_id": "q_123",
  "question_text": "Sofía ran \\frac{2}{5} of a mile in the morning and \\frac{1}{5} of a mile after school. How far did she run in total?",
  "question_type": "fraction",
  "options": null,
  "katex_expressions": ["\\frac{2}{5}", "\\frac{1}{5}"],
  "skill_id": "4.NF.B.3",
  "context_theme": "Oregon wildlife"
}

// Assessment result (correct)
{
  "type": "assessment_correct",
  "celebration_variant": "nice_job",
  "consecutive_correct": 3,
  "streak_badge": true
}

// Assessment result (incorrect)
{
  "type": "assessment_incorrect",
  "attempt_number": 1,
  "hint_available": true,
  "feedback_text": "Good try! Would you like a hint?"
}

// Hint delivery
{
  "type": "hint",
  "hint_level": 1,
  "hint_text": "Think about what the numbers on the bottom of the fractions tell you. Are they the same?",
  "explanation_style_used": "step_by_step"
}

// Tutor chat response
{
  "type": "tutor_response",
  "message": "Denominators tell us how many equal pieces the whole is cut into. If both fractions have the same denominator, can you just add the top numbers?"
}

// BKT progress update
{
  "type": "bkt_update",
  "skill_id": "4.NF.B.3",
  "p_mastered_before": 0.72,
  "p_mastered_after": 0.79,
  "mastery_achieved": false
}

// Mastery celebration
{
  "type": "mastery_achieved",
  "skill_id": "4.NF.B.3",
  "skill_name": "Adding Fractions with Like Denominators",
  "next_skill": {"id": "4.NF.B.4", "name": "Multiplying Fractions by Whole Numbers"}
}

// Session summary
{
  "type": "session_summary",
  "session_id": "ses_xyz",
  "duration_minutes": 14,
  "questions_answered": 10,
  "questions_correct": 8,
  "accuracy_pct": 80,
  "bkt_gains": {"4.NF.B.3": 0.15},
  "skills_mastered": [],
  "hints_used_total": 3,
  "next_session_preview": "Continue: Adding Fractions with Unlike Denominators"
}
```

### REST Endpoints

#### Sessions

```
POST   /api/v1/sessions                         Start a new practice session
GET    /api/v1/sessions/{session_id}            Get session details
GET    /api/v1/sessions/{session_id}/summary    Get session summary (post-session)
GET    /api/v1/students/{student_id}/sessions   List all sessions for student
       ?limit=20&offset=0&skill_id=4.NF.B.3
```

**POST /api/v1/sessions — Request:**
```json
{
  "student_id": "stu_abc123",
  "learning_plan_id": "lp_def456",
  "skill_id": "4.NF.B.3",       // optional; overrides plan default
  "session_mode": "adaptive"     // optional; default "adaptive"
}
```

**POST /api/v1/sessions — Response:**
```json
{
  "session_id": "ses_xyz789",
  "websocket_url": "wss://api.mathpathorgon.com/ws/sessions/ses_xyz789",
  "session_token": "st_...",     // JWT for WS auth
  "current_skill": {
    "id": "4.NF.B.3",
    "name": "Adding Fractions with Like Denominators",
    "domain": "Number and Operations – Fractions"
  },
  "bkt_state": {
    "p_mastered": 0.72,
    "attempt_count": 12,
    "correct_streak": 2
  }
}
```

#### Student Memory / Progress

```
GET    /api/v1/students/{student_id}/memory           Get full LTM snapshot
GET    /api/v1/students/{student_id}/bkt              Get all BKT states
GET    /api/v1/students/{student_id}/bkt/{skill_id}   Get BKT state for one skill
PATCH  /api/v1/students/{student_id}/preferences      Update learning preferences
```

#### Questions (internal use; also supports content management)

```
POST   /api/v1/questions/generate         Manually trigger question generation (admin/QA)
GET    /api/v1/questions/{question_id}    Get question details
PATCH  /api/v1/questions/{question_id}    Update question (fix errors, adjust difficulty)
GET    /api/v1/questions?skill_id=...&b_min=...&b_max=...   Query question bank
```

---

## 3.8 Acceptance Criteria

### AC-3.1: Agent Initialization

**Given** a student with a completed diagnostic assessment and active learning plan  
**When** a new practice session is initiated via `POST /api/v1/sessions`  
**Then**:
- Session record created in `practice_sessions`
- BKT states loaded from `skill_mastery_states` for all skills in active module
- WM initialized in Redis with all required keys
- WebSocket URL returned with valid session token
- Response time < 2 seconds

### AC-3.2: Question Generator — Cached Selection

**Given** a student session where the current skill has ≥ 3 cached questions in range `[theta - 0.3, theta + 0.5]`  
**When** the Question Generator Agent is invoked  
**Then**:
- A cached question is returned within 500ms
- The question's `difficulty_b` falls within `[theta - 0.5, theta + 0.8]`
- The question has not appeared in the student's last 48 hours of practice
- The question's `context_theme` differs from the previous question in this session

### AC-3.3: Question Generator — Live Generation

**Given** fewer than 3 cached questions available in difficulty range  
**When** Question Generator triggers live generation via o3-mini  
**Then**:
- Generated question is returned within 8 seconds
- Generated question has been verified (independent solution matches `correct_answer`)
- Question is stored in `practice_questions` with `is_generated = true`
- If verification fails: a cached question (with widened range) is served instead

### AC-3.4: Assessment Agent — Correct Answer

**Given** a student submits "3/5" and the correct answer is "6/10"  
**When** the Assessment Agent evaluates the response  
**Then**:
- `is_correct = true` (equivalent fractions accepted)
- `error_type = null`
- `feedback_level = 1`
- Response stored in `session_responses`
- BKT state update triggered immediately

### AC-3.5: Assessment Agent — Error Classification

**Given** a student submits "1/7" for the question "1/3 + 1/4 = ?" (correct answer: 7/12)  
**When** the Assessment Agent evaluates the response  
**Then**:
- `is_correct = false`
- `error_code = "ERR-NF-01"` (common denominator omission — student added 1+1/3+4=2/7 → simplified badly to 1/7 or directly added denominators)
- `feedback_level = 1` (first attempt)
- Error logged to `student_error_patterns`

### AC-3.6: Tutor Agent — Hint Level 1

**Given** a student has answered incorrectly once on a fraction addition question  
**When** the student presses "Need a hint?" and Tutor Agent generates Level 1 hint  
**Then**:
- Hint does not contain the correct answer or the computation steps
- Hint is 1-2 sentences
- Flesch-Kincaid grade level of hint ≤ 5.5
- Hint does not contain any banned negative phrases
- Hint delivered within 3 seconds

### AC-3.7: Tutor Agent — Frustration Detection

**Given** a student has answered incorrectly 3 consecutive times and used Level 3 hint once  
**When** the next question response is evaluated  
**Then**:
- `frustration_score ≥ 7.0` is computed (3 × 1.5 + 1 × 1.0 = 5.5 + additional factors ≥ 7.0)
- `session_mode` is updated to `"scaffolded"`
- Next question's target difficulty range is lowered by 0.5 IRT b-parameter
- Pip displays an extra-encouraging message
- A parent notification is queued (delivered after session end)

### AC-3.8: BKT Update — Correctness

**Given** a student with P(mastered) = 0.60, P(transit) = 0.09, P(slip) = 0.10, P(guess) = 0.20  
**When** they answer correctly  
**Then** the updated P(mastered) = approximately 0.752 (within ±0.001):
- P(Known | correct) = (0.60 × 0.90) / (0.60 × 0.90 + 0.40 × 0.20) = 0.54/0.62 ≈ 0.871
- P(Known_new) = 0.871 + (0.129 × 0.09) ≈ 0.871 + 0.012 = 0.883
- Written to `skill_mastery_states` within 100ms
- Written to `bkt_state_history`

### AC-3.9: Mastery Threshold

**Given** a student's BKT state reaches P(mastered) = 0.96 after a correct answer  
**When** the Progress Tracker checks mastery conditions  
**Then**:
- If `correct_streak ≥ 5` AND `attempt_count ≥ 5`: mastery declared
- `skill_mastery_states.mastered_at` set to current timestamp
- `practice_sessions.skills_mastered` array updated
- `session_questions` table: next question serves the next skill in learning plan
- If `correct_streak < 5`: mastery NOT declared; session continues on current skill

### AC-3.10: Spiral Review

**Given** a student begins their 5th session (session_number = 5)  
**When** the session initializes  
**Then**:
- Session begins with 1 review question for each previously mastered skill (max 2 review questions total for sessions with ≥ 2 mastered skills)
- Review questions have difficulty `b ≈ student_theta - 0.5`
- Review questions are not labeled as "review" to the student
- If student answers review question incorrectly: BKT update applied, skill considered for re-addition to plan

### AC-3.11: Session Persistence

**Given** a student is mid-session at question 6 of 10  
**When** their browser is refreshed or network connection drops for < 30 minutes  
**Then**:
- Session state is restored from Redis within 2 seconds of reconnection
- Question 6 is re-displayed in the same state as before refresh
- Progress bar shows 5/10 (questions already answered count preserved)
- No duplicate entries in `session_responses`

### AC-3.12: COPPA Compliance — LLM Prompts

**Given** any invocation of Assessment Agent, Tutor Agent, or Question Generator Agent  
**When** the prompt is constructed and sent to the LLM provider  
**Then**:
- Prompt contains no student name, email, or any other PII
- Only `student_id` (UUID) is referenced
- Prompt content is logged to `agent_interaction_logs` as a SHA-256 hash (not plaintext)
- All LLM API calls are made server-side (never client-side with exposed keys)

### AC-3.13: Child Language Compliance

**Given** 100 randomly sampled Tutor Agent responses from a test session  
**When** analyzed with the `textstat` library  
**Then**:
- ≥ 95% have Flesch-Kincaid grade level between 3.5 and 5.5
- 100% contain no banned negative phrases
- 100% are ≤ 75 words in length
- Average response length: 30-55 words

### AC-3.14: Cost Per Session

**Given** a 10-question session with 3 hint requests and 2 tutor chat messages  
**When** LLM cost is computed from `agent_interaction_logs` (input_tokens × rate + output_tokens × rate)  
**Then**:
- Total LLM cost ≤ $0.15 per session
- Breakdown expected: Assessment (o3-mini × 10) + Tutor (Claude × 5) + QGen (o3-mini × 2 generated) < $0.15

---

*End of PRD Stage 3*
