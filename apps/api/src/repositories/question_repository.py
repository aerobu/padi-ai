"""
Question repository for question bank management.
"""

from typing import Optional, List, Dict, Any
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from .base import AsyncRepository
from src.models.models import Question, QuestionOption


class QuestionRepository(AsyncRepository[Question]):
    """Repository for Question model."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Question)

    async def get_by_standard_id(self, standard_id: str) -> List[Question]:
        """Get all questions for a standard."""
        result = await self.session.execute(
            select(Question)
            .where(Question.standard_id == standard_id, Question.is_active == True)
        )
        return list(result.scalars().all())

    async def get_available_questions(
        self,
        standard_ids: List[str],
        question_type: str = None,
        difficulty: int = None,
        limit: int = 50,
        exclude_ids: List[str] = None,
    ) -> List[Question]:
        """Get available questions with optional filters."""
        query = select(Question).where(
            Question.is_active == True,
            Question.standard_id.in_(standard_ids),
        )

        if question_type:
            query = query.where(Question.question_type == question_type)

        if difficulty:
            query = query.where(Question.difficulty == difficulty)

        if exclude_ids:
            query = query.where(~Question.id.in_(exclude_ids))

        query = query.order_by(Question.difficulty, Question.id).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_question_with_options(
        self, question_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get question with its options."""
        question = await self.get_by_id(question_id)
        if not question:
            return None

        result = await self.session.execute(
            select(QuestionOption)
            .where(QuestionOption.question_id == question_id)
            .order_by(QuestionOption.order)
        )
        options = result.scalars().all()

        return {
            "id": question.id,
            "standard_id": question.standard_id,
            "question_text": question.question_text,
            "question_type": question.question_type,
            "difficulty": question.difficulty,
            "options": [
                {
                    "id": opt.id,
                    "option_text": opt.option_text,
                    "is_correct": opt.is_correct,
                    "explanation": opt.explanation,
                    "order": opt.order,
                }
                for opt in options
            ],
        }

    async def get_questions_by_difficulty_range(
        self,
        min_difficulty: int,
        max_difficulty: int,
        limit: int = 100,
        exclude_ids: List[str] = None,
    ) -> List[Question]:
        """Get questions within a difficulty range."""
        query = (
            select(Question)
            .where(
                Question.is_active == True,
                Question.difficulty >= min_difficulty,
                Question.difficulty <= max_difficulty,
            )
            .order_by(Question.difficulty)
            .limit(limit)
        )

        if exclude_ids:
            query = query.where(~Question.id.in_(exclude_ids))

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def increment_shown_count(self, question_id: str) -> bool:
        """Increment question shown count (for item response theory)."""
        statement = text(
            "UPDATE questions SET times_shown = times_shown + 1 WHERE id = :question_id"
        )
        result = await self.session.execute(statement, {"question_id": question_id})
        await self.session.commit()
        return result.rowcount > 0
