"""Typed state schemas for the LangGraph adaptive-practice orchestrator.

Mirrors PRD Stage 3 § 3.2 verbatim so downstream agent code can be
implemented incrementally against a stable contract.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional, TypedDict


class BKTState(TypedDict, total=False):
    """Per-skill BKT state held in SessionState.bkt_states."""

    skill_id: str
    p_mastered: float
    p_transit: float
    p_slip: float
    p_guess: float
    correct_streak: int
    attempt_count: int
    last_updated: datetime


class QuestionContext(TypedDict, total=False):
    """Currently-served question with everything the tutor needs."""

    question_id: str
    skill_id: str
    question_text: str
    question_type: Literal["multiple_choice", "numeric", "fraction", "drag_drop", "multi_step"]
    options: Optional[list[str]]
    correct_answer: str
    solution_steps: list[str]
    difficulty_b: float
    context_theme: str
    prerequisite_skills: list[str]


class WorkingMemoryEntry(TypedDict, total=False):
    """One historical exchange the tutor can reference."""

    question_id: str
    question_text: str
    student_answer: str
    is_correct: bool
    hints_used: int
    error_type: Optional[str]
    response_time_ms: int
    timestamp: datetime


class AssessmentResult(TypedDict, total=False):
    """Result produced by AssessmentAgent.evaluate()."""

    is_correct: bool
    normalized_answer: str
    error_type: Optional[str]
    error_code: Optional[str]
    feedback_level: Literal["correct", "minor_error", "major_error", "conceptual_gap"]
    partial_credit: float
    confidence: float
    assessment_reasoning: str


SessionMode = Literal["adaptive", "scaffolded", "challenge", "review"]
NextAgent = Literal[
    "question_generator",
    "assessment",
    "tutor",
    "progress_tracker",
    "await_answer",
    "end",
]
ExplanationStyle = Literal["step_by_step", "visual", "analogy", "auto"]


class SessionState(TypedDict, total=False):
    """LangGraph state for one practice session."""

    # Identity
    student_id: str
    session_id: str
    learning_plan_id: str

    # Current position
    current_skill_id: str
    current_module_id: str
    current_question: Optional[QuestionContext]

    # Attempt tracking
    attempt_count: int
    hints_used: int
    consecutive_correct: int
    consecutive_wrong: int

    # Session history (last 10)
    session_history: list[WorkingMemoryEntry]

    # BKT states touched this session
    bkt_states: dict[str, BKTState]

    # Affect
    frustration_score: float

    # Personalization
    preferred_explanation_style: ExplanationStyle

    # Metadata
    session_start_time: datetime
    questions_answered: int
    questions_correct: int
    session_mode: SessionMode

    # Flow control
    next_agent: NextAgent
    session_complete: bool

    # Tutor context (last 3 interactions)
    tutor_context: list[dict]

    # Error from any agent (for retry)
    last_error: Optional[str]

    # Last student answer and assessment result
    last_student_answer: str
    last_assessment: Optional[AssessmentResult]
