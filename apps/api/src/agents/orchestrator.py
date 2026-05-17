"""Adaptive-practice session orchestrator.

Phase 3 ships a hand-rolled async state machine that round-trips the four
agents and exposes the same `__call__(state)` signature LangGraph nodes
will adopt. Phase 4-E swaps the routing core to `langgraph.graph.StateGraph`
without touching the agent modules.

Why hand-rolled first: it lets us land the full session loop, WebSocket
endpoint, and tests today without pulling in `langgraph` (which is heavy
and pins LangChain). Each agent already mirrors the LangGraph node
contract (`async def __call__(self, state) -> state`), so the swap is
mechanical.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from src.agents.assessment_agent import AssessmentAgent
from src.agents.progress_tracker import ProgressTrackerAgent
from src.agents.qgen_agent import QuestionGeneratorAgent
from src.agents.state import SessionState
from src.agents.tutor_agent import TutorAgent


def route_after_assessment(state: SessionState) -> str:
    """PRD § 3.2 routing logic, lightly adapted for the Phase-3 stub.

    Returns the name of the next agent to invoke.
    """
    if state.get("session_complete"):
        return "end"
    if state.get("frustration_score", 0.0) > 7.0:
        return "tutor"
    assessment = state.get("last_assessment") or {}
    if assessment.get("is_correct"):
        return "progress_tracker"
    if state.get("attempt_count", 0) >= 3:
        return "progress_tracker"
    return "tutor"


def route_after_progress_tracker(state: SessionState) -> str:
    """After a BKT step, decide whether to end or pull a new question."""
    if state.get("session_complete"):
        return "end"
    if state.get("questions_answered", 0) >= 10:
        return "end"
    return "question_generator"


class SessionOrchestrator:
    """Owns one practice session's lifecycle across all four agents."""

    def __init__(
        self,
        assessment: Optional[AssessmentAgent] = None,
        tutor: Optional[TutorAgent] = None,
        qgen: Optional[QuestionGeneratorAgent] = None,
        progress_tracker: Optional[ProgressTrackerAgent] = None,
    ) -> None:
        self.assessment = assessment or AssessmentAgent()
        self.tutor = tutor or TutorAgent()
        self.qgen = qgen or QuestionGeneratorAgent()
        self.progress_tracker = progress_tracker or ProgressTrackerAgent()

    async def start_session(
        self,
        student_id: str,
        session_id: str,
        learning_plan_id: str,
        current_skill_id: str,
        current_module_id: str = "",
    ) -> SessionState:
        """Create a fresh `SessionState` and emit the first question."""
        state: SessionState = SessionState(
            student_id=student_id,
            session_id=session_id,
            learning_plan_id=learning_plan_id,
            current_skill_id=current_skill_id,
            current_module_id=current_module_id,
            attempt_count=0,
            hints_used=0,
            consecutive_correct=0,
            consecutive_wrong=0,
            session_history=[],
            bkt_states={},
            frustration_score=0.0,
            preferred_explanation_style="auto",
            session_start_time=datetime.now(timezone.utc),
            questions_answered=0,
            questions_correct=0,
            session_mode="adaptive",
            next_agent="question_generator",
            session_complete=False,
            tutor_context=[],
            last_error=None,
        )
        return await self.qgen(state)

    async def submit_answer(
        self,
        state: SessionState,
        student_answer: str,
    ) -> SessionState:
        """Drive the four-agent loop for one student answer.

        Returns the updated state after at most one round of:
        assessment -> (tutor | progress_tracker -> qgen).
        """
        state["last_student_answer"] = student_answer
        state["attempt_count"] = state.get("attempt_count", 0) + 1

        state = await self.assessment(state)
        decision = route_after_assessment(state)

        if decision == "tutor":
            state = await self.tutor(state)
            return state

        # decision in {"progress_tracker", "end"}
        state = await self.progress_tracker(state)
        nxt = route_after_progress_tracker(state)
        if nxt == "end":
            state["session_complete"] = True
            state["next_agent"] = "end"
            return state
        return await self.qgen(state)
