"""Question Generator Agent — pick the next question at the target difficulty.

PRD Stage 3 § 3.2 Question Generator. Two strategies:
1. Cached selection from the `questions` table for the current skill, within
   the IRT-targeted difficulty band (Phase 4-C).
2. Live LLM generation with answer-verification fallback when the cache is
   exhausted (Phase 4-C).

This Phase-3 stub deterministically returns a placeholder question so the
orchestrator can be wired and tested.
"""

from __future__ import annotations

from typing import Optional
from uuid import uuid4

from src.agents.state import QuestionContext, SessionState
from src.clients.llm_client import LLMClient, LLMPurpose, get_llm_client


class QuestionGeneratorAgent:
    """Select or generate the next question for the active skill."""

    def __init__(self, llm_client: Optional[LLMClient] = None) -> None:
        self.llm_client = llm_client or get_llm_client()

    async def next_question(self, state: SessionState) -> QuestionContext:
        skill_id = state.get("current_skill_id", "unknown")
        return QuestionContext(
            question_id=str(uuid4()),
            skill_id=skill_id,
            question_text=f"[Phase-3 stub] Sample question for {skill_id}",
            question_type="multiple_choice",
            options=["A) 1", "B) 2", "C) 3", "D) 4"],
            correct_answer="A",
            solution_steps=["See Phase 4-C for real generation."],
            difficulty_b=0.0,
            context_theme="placeholder",
            prerequisite_skills=[],
        )

    async def __call__(self, state: SessionState) -> SessionState:
        state["current_question"] = await self.next_question(state)
        state["attempt_count"] = 0
        state["hints_used"] = 0
        state["next_agent"] = "await_answer"
        return state


QGEN_LLM_PURPOSE = LLMPurpose.QUESTION_GENERATION
