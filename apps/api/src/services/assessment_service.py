"""
Assessment service for diagnostic assessment orchestration.
Integrates BKT and CAT for adaptive testing.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Any, Tuple
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.assessment_repository import (
    AssessmentRepository,
    AssessmentSessionRepository,
)
from src.repositories.student_repository import StudentRepository
from src.repositories.standard_repository import StandardRepository
from src.repositories.question_repository import QuestionRepository
from src.repositories.consent_repository import ConsentRepository
from src.services.bkt_service import get_bkt_service, BKTService
from src.services.question_selection_service import (
    get_question_selection_service,
    QuestionSelectionService,
)
from src.core.redis_client import get_redis_client, RedisClient

logger = logging.getLogger(__name__)


class AssessmentService:
    """Service for diagnostic assessment management."""

    TARGET_QUESTION_COUNT = 35

    def __init__(
        self,
        assessment_repository: AssessmentRepository,
        session_repository: AssessmentSessionRepository,
        student_repository: StudentRepository,
        standard_repository: StandardRepository,
        question_repository: QuestionRepository,
        consent_repository: ConsentRepository,
        bkt_service: BKTService,
        cat_service: QuestionSelectionService,
        redis_client: RedisClient,
        async_session_factory: Any = None,
    ):
        """
        Initialize assessment service.

        Args:
            assessment_repository: Assessment CRUD operations
            session_repository: Assessment session management
            student_repository: Student operations
            standard_repository: Standards data
            question_repository: Question bank
            consent_repository: Consent validation
            bkt_service: Bayesian Knowledge Tracing
            cat_service: Computerized Adaptive Testing
            redis_client: Redis caching
            async_session_factory: SQLAlchemy async session factory
        """
        self.assessment_repository = assessment_repository
        self.session_repository = session_repository
        self.student_repository = student_repository
        self.standard_repository = standard_repository
        self.question_repository = question_repository
        self.consent_repository = consent_repository
        self.bkt_service = bkt_service
        self.cat_service = cat_service
        self.redis_client = redis_client
        self._async_session_factory = async_session_factory

    async def start_assessment(
        self, student_id: str, assessment_type: str = "diagnostic"
    ) -> Dict[str, Any]:
        """
        Start a new diagnostic assessment for a student.

        Args:
            student_id: Student ID
            assessment_type: Type of assessment

        Returns:
            Assessment start response
        """
        # Verify student exists
        student = await self.student_repository.get_by_id(student_id)
        if not student:
            raise ValueError("Student not found")

        # Verify active consent
        parent_id = student.parent_id
        has_consent = await self.consent_repository.has_active_consent(parent_id)
        if not has_consent:
            raise ValueError("Active COPPA consent required to start assessment")

        # Check for existing active assessment
        existing = await self.assessment_repository.get_active_diagnostic(student_id)
        if existing:
            raise ValueError("Student already has an active diagnostic assessment")

        # Create assessment record
        assessment = await self.assessment_repository.create({
            "student_id": student_id,
            "assessment_type": assessment_type,
            "version": "1.0",
            "status": "in_progress",
            "metadata_json": {},
        })

        # Create session
        session = await self.assessment_repository.create_session(
            assessment.id, student_id
        )

        # Load question pool
        question_pool = await self._load_question_pool(student.grade_level)

        # Initialize CAT state
        cat_state = self.cat_service.initialize_assessment(
            assessment.id, question_pool, self.TARGET_QUESTION_COUNT
        )

        # Store state in Redis
        state = {
            "theta": cat_state.theta,
            "covered_standards": {},
            "question_pool_size": len(question_pool),
        }
        await self.redis_client.save_assessment_state(assessment.id, state)

        logger.info(
            f"Assessment started: assessment_id={assessment.id}, "
            f"student_id={student_id}"
        )

        return {
            "assessment_id": assessment.id,
            "session_id": session.id,
            "student_id": student_id,
            "assessment_type": assessment_type,
            "target_question_count": self.TARGET_QUESTION_COUNT,
            "status": "in_progress",
            "started_at": datetime.utcnow(),
        }

    async def get_next_question(
        self,
        assessment_id: str,
        student_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Get the next question for an assessment.

        Args:
            assessment_id: Assessment ID
            student_id: Student ID (for permission check)

        Returns:
            Question presentation or None if assessment should end
        """
        # Get assessment state from Redis
        state = await self.redis_client.get_assessment_state(assessment_id)
        if not state:
            raise ValueError("Assessment state not found")

        # Verify student owns assessment
        student = await self.student_repository.get_by_id(student_id)
        if not student:
            raise ValueError("Student not found")

        # Get questions answered from state
        questions_answered = state.get("questions_answered", 0)

        # Get question pool
        question_pool = await self.redis_client.get_question_pool(assessment_id)
        if not question_pool:
            question_pool = await self._load_question_pool(student.grade_level)
            await self.redis_client.set_question_pool(assessment_id, question_pool)

        # Get currently answered question IDs (from DB)
        responses = await self.assessment_repository.get_responses_for_session(
            state.get("session_id")
        )
        answered_ids = [r.question_id for r in responses]

        # Select next question using CAT
        next_question = self.cat_service.select_next_question(
            assessment_id=assessment_id,
            student_id=student_id,
            covered_standards=state.get("covered_standards", {}),
            questions_answered=questions_answered,
            question_pool=question_pool,
            exclude_question_ids=answered_ids,
        )

        if not next_question:
            # Check if assessment should end
            should_end, end_reason = self.cat_service.should_end_assessment(
                questions_answered=questions_answered,
                covered_standards=state.get("covered_standards", {}),
            )

            if should_end:
                return {
                    "question": None,
                    "should_end": True,
                    "end_reason": end_reason,
                    "progress": self.cat_service.get_progress(
                        questions_answered=questions_answered,
                        covered_standards=state.get("covered_standards", {}),
                    ),
                }

            raise ValueError("No more questions available")

        # Mark question as current
        await self.redis_client.set_current_question(assessment_id, next_question["id"])

        # Get question with options
        question_data = await self.question_repository.get_question_with_options(
            next_question["id"]
        )

        # Build presentation
        question_number = questions_answered + 1
        standard = await self.standard_repository.get_by_code(next_question.get("standard_code"))

        return {
            "question": {
                "question_id": next_question["id"],
                "question_number": question_number,
                "standard_domain": standard.domain if standard else "Unknown",
                "stem": question_data["question_text"],
                "options": [
                    {
                        "key": chr(65 + i),  # A, B, C, D
                        "text": opt["option_text"],
                        "image_url": None,
                    }
                    for i, opt in enumerate(question_data["options"])
                ],
                "question_type": question_data["question_type"],
            },
            "progress": self.cat_service.get_progress(
                questions_answered=questions_answered,
                covered_standards=state.get("covered_standards", {}),
            ),
            "should_end": False,
        }

    async def submit_response(
        self,
        assessment_id: str,
        student_id: str,
        question_id: str,
        selected_answer: str,
        time_spent_ms: int,
    ) -> Dict[str, Any]:
        """
        Submit a question response.

        Args:
            assessment_id: Assessment ID
            student_id: Student ID
            question_id: Answered question ID
            selected_answer: Selected option (A-D) or numeric answer
            time_spent_ms: Time spent on question in milliseconds

        Returns:
            Response submission result with progress
        """
        # Get assessment state
        state = await self.redis_client.get_assessment_state(assessment_id)
        if not state:
            raise ValueError("Assessment state not found")

        # Get current question
        current_question_id = await self.redis_client.get_current_question(assessment_id)
        if current_question_id != question_id:
            raise ValueError(
                f"Question mismatch. Expected {current_question_id}, got {question_id}"
            )

        # Verify question ownership
        question = await self.question_repository.get_by_id(question_id)
        if not question:
            raise ValueError("Question not found")

        # Get correct answer
        question_data = await self.question_repository.get_question_with_options(question_id)
        correct_option = next(
            (opt for opt in question_data["options"] if opt["is_correct"]),
            None,
        )

        is_correct = correct_option and correct_option["option_text"] == selected_answer

        # Get session
        session = await self.assessment_repository.get_session(state.get("session_id"))
        if not session:
            raise ValueError("Session not found")

        # Record response
        await self.assessment_repository.record_response(
            session_id=session.id,
            question_id=question_id,
            student_answer=selected_answer,
            is_correct=is_correct,
            points_earned=1.0 if is_correct else 0.0,
            time_spent_seconds=time_spent_ms // 1000,
        )

        # Update BKT state
        standard_code = question.standard_id  # Using standard_id as standard_code
        bkt_state = self.bkt_service.update_state(
            standard_code=standard_code,
            response_correct=is_correct,
        )

        # Save BKT state to Redis
        await self.redis_client.save_bkt_state(
            assessment_id, standard_code, self.bkt_service.get_state_dict(bkt_state)
        )

        # Update CAT state
        covered = state.get("covered_standards", {}).copy()
        covered[standard_code] = covered.get(standard_code, 0) + 1

        state["covered_standards"] = covered
        state["questions_answered"] = state.get("questions_answered", 0) + 1

        # Update theta estimate
        state["theta"] = bkt_state.p_mastery  # Simplified: use mastery as proxy

        await self.redis_client.save_assessment_state(assessment_id, state)

        logger.info(
            f"Response submitted: question={question_id}, correct={is_correct}, "
            f"bkt_mastery={bkt_state.p_mastery:.3f}"
        )

        return {
            "is_correct": is_correct,
            "correct_answer": correct_option["option_text"] if correct_option else None,
            "explanation": correct_option["explanation"] if correct_option else None,
            "progress": self.cat_service.get_progress(
                questions_answered=state["questions_answered"],
                covered_standards=covered,
            ),
        }

    async def complete_assessment(
        self, assessment_id: str, db_session: AsyncSession
    ) -> Dict[str, Any]:
        """
        Complete an assessment and generate results.

        Args:
            assessment_id: Assessment ID
            db_session: Database session for saving BKT states

        Returns:
            Completion response with results URL
        """
        # Get assessment state
        state = await self.redis_client.get_assessment_state(assessment_id)
        if not state:
            raise ValueError("Assessment state not found")

        questions_answered = state.get("questions_answered", 0)
        if questions_answered < 35:
            raise ValueError(f"Minimum 35 questions required; only {questions_answered} answered")

        # Get all responses
        assessment_session = await self.assessment_repository.get_session(state.get("session_id"))
        responses = await self.assessment_repository.get_responses_for_session(assessment_session.id)

        # Calculate score
        total_correct = sum(1 for r in responses if r.is_correct)
        overall_score = total_correct / len(responses) if responses else 0

        # Finalize BKT states to database
        for standard_code, bkt_data in state.get("bkt_states", {}).items():
            await self._save_skill_state(
                state.get("student_id"), standard_code, bkt_data, db_session
            )

        # Complete session
        completed_at = datetime.utcnow()
        await self.assessment_repository.complete_session(assessment_session.id, completed_at)

        # Update assessment
        await self.assessment_repository.update_assessment_status(
            assessment_id, "completed", overall_score
        )

        # Delete assessment state from Redis
        await self.redis_client.delete_assessment_state(assessment_id)

        logger.info(
            f"Assessment completed: assessment_id={assessment_id}, "
            f"score={overall_score:.2f}, questions={questions_answered}"
        )

        return {
            "assessment_id": assessment_id,
            "status": "completed",
            "total_questions": questions_answered,
            "total_correct": total_correct,
            "overall_score": overall_score,
            "duration_minutes": questions_answered * 1.5,  # Estimate
            "completed_at": completed_at,
            "results_url": f"/diagnostic/results?assessment={assessment_id}",
        }

    async def get_results(self, assessment_id: str, student_id: str) -> Dict[str, Any]:
        """
        Get assessment results.

        Args:
            assessment_id: Assessment ID
            student_id: Student ID (for permission)

        Returns:
            Complete assessment results
        """
        # Get assessment
        assessment = await self.assessment_repository.get_by_id(assessment_id)
        if not assessment:
            raise ValueError("Assessment not found")

        if assessment.student_id != student_id:
            raise ValueError("Access denied")

        if assessment.status != "completed":
            raise ValueError("Assessment not completed")

        # Get student
        student = await self.student_repository.get_by_id(student_id)

        # Get all responses
        session = await self.assessment_repository.get_session(state.get("session_id"))
        responses = await self.assessment_repository.get_responses_for_session(session.id)

        # Calculate domain results
        domain_results = await self._calculate_domain_results(responses)

        # Calculate skill states
        skill_states = await self._calculate_skill_states(assessment_id, student_id)

        # Generate gap analysis
        gap_analysis = self._generate_gap_analysis(skill_states)

        # Classify overall performance
        overall_score = assessment.total_score or 0
        if overall_score >= 0.8:
            classification = "above_par"
        elif overall_score >= 0.6:
            classification = "on_par"
        else:
            classification = "below_par"

        return {
            "assessment_id": assessment_id,
            "student_name": f"{student.first_name} {student.last_name}",
            "assessment_type": assessment.assessment_type,
            "completed_at": assessment.completed_at or datetime.utcnow(),
            "duration_minutes": len(responses) * 1.5,
            "overall_score": overall_score,
            "total_questions": len(responses),
            "total_correct": sum(1 for r in responses if r.is_correct),
            "overall_classification": classification,
            "domain_results": domain_results,
            "skill_states": skill_states,
            "gap_analysis": gap_analysis,
        }

    async def _load_question_pool(
        self,
        grade_level: int,
        limit: int = 200,
    ) -> List[Dict[str, Any]]:
        """Load question pool for a grade level."""
        # Get all active standards for grade
        standards = await self.standard_repository.get_by_grade(grade_level)
        standard_ids = [s.id for s in standards]
        standard_codes = [s.standard_code for s in standards]

        # Get questions for these standards
        questions = await self.question_repository.get_available_questions(
            standard_ids=standard_ids,
            limit=limit,
        )

        # Build pool with standard codes
        pool = []
        for q in questions:
            pool.append({
                "id": q.id,
                "standard_id": q.standard_id,
                "standard_code": next(
                    (code for code in standard_codes if code.startswith(q.standard_id[:5])),
                    "Unknown",
                ),
                "difficulty": q.difficulty,
                "is_active": q.is_active,
            })

        return pool

    async def _save_skill_state(
        self,
        student_id: str,
        standard_code: str,
        bkt_data: Dict[str, float],
        db_session: AsyncSession,
    ) -> None:
        """Save skill state to database."""
        from src.models.models import StudentSkillState
        from sqlalchemy import select

        # Get standard ID
        standards = await self.standard_repository.get_by_codes([standard_code])
        if not standards:
            return

        standard_id = standards[0].id

        # Check if exists
        result = await db_session.execute(
            select(StudentSkillState)
            .where(
                StudentSkillState.student_id == student_id,
                StudentSkillState.standard_id == standard_id,
            )
        )
        state = result.scalar_one_or_none()

        if state:
            # Update existing
            state.p_mastery = bkt_data.get("p_mastery", 0.0)
            state.p_guess = bkt_data.get("p_guess", 0.25)
            state.p_slip = bkt_data.get("p_slip", 0.20)
            state.p_learning = bkt_data.get("p_learning", 0.50)
            state.times_practiced += 1
            state.last_practiced_at = datetime.utcnow()
        else:
            # Create new
            state = StudentSkillState(
                student_id=student_id,
                standard_id=standard_id,
                p_mastery=bkt_data.get("p_mastery", 0.0),
                p_guess=bkt_data.get("p_guess", 0.25),
                p_slip=bkt_data.get("p_slip", 0.20),
                p_learning=bkt_data.get("p_learning", 0.50),
                times_practiced=1,
                last_practiced_at=datetime.utcnow(),
            )
            db_session.add(state)

        await db_session.commit()

    async def _calculate_domain_results(
        self,
        responses: List[Any],
    ) -> List[Dict[str, Any]]:
        """Calculate results by domain."""
        domain_stats = {}

        for response in responses:
            question = await self.question_repository.get_by_id(response.question_id)
            standard = await self.standard_repository.get_by_id(question.standard_id)

            domain_key = standard.domain if standard else "Unknown"
            if domain_key not in domain_stats:
                domain_stats[domain_key] = {"total": 0, "correct": 0}

            domain_stats[domain_key]["total"] += 1
            if response.is_correct:
                domain_stats[domain_key]["correct"] += 1

        results = []
        for domain, stats in domain_stats.items():
            score = stats["correct"] / stats["total"] if stats["total"] > 0 else 0
            if score >= 0.8:
                classification = "above_par"
            elif score >= 0.6:
                classification = "on_par"
            else:
                classification = "below_par"

            results.append({
                "domain_code": domain,
                "domain_name": domain,
                "questions_count": stats["total"],
                "correct_count": stats["correct"],
                "score": score,
                "classification": classification,
            })

        return results

    async def _calculate_skill_states(
        self,
        assessment_id: str,
        student_id: str,
    ) -> List[Dict[str, Any]]:
        """Calculate skill states from BKT."""
        # Get BKT states from Redis
        skill_states = []

        # Get all BKT keys for this assessment
        # In production, would use Redis scan
        # For now, query from responses
        responses = await self.assessment_repository.get_responses_for_session(
            state.get("session_id")
        )

        # Group responses by standard
        standard_responses = {}
        for response in responses:
            question = await self.question_repository.get_by_id(response.question_id)
            standard_code = question.standard_id

            if standard_code not in standard_responses:
                standard_responses[standard_code] = []

            standard_responses[standard_code].append(response.is_correct)

        # Calculate BKT for each standard
        for standard_code, responses_list in standard_responses.items():
            bkt_state = self.bkt_service.batch_update(
                standard_code=standard_code,
                responses=responses_list,
            )

            standard = await self.standard_repository.get_by_code(standard_code)

            skill_states.append({
                "standard_code": standard_code,
                "standard_title": standard.title if standard else "Unknown",
                "p_mastery": bkt_state.p_mastery,
                "mastery_level": self.bkt_service.classify_mastery(bkt_state.p_mastery),
                "questions_attempted": len(responses_list),
                "questions_correct": sum(responses_list),
            })

        return skill_states

    def _generate_gap_analysis(
        self,
        skill_states: List[Dict[str, Any]],
    ) -> Dict[str, List[str]]:
        """Generate gap analysis from skill states."""
        strengths = []
        on_track = []
        needs_work = []
        recommended_order = []

        for state in skill_states:
            code = state["standard_code"]
            p_mastery = state["p_mastery"]

            if p_mastery >= 0.8:
                strengths.append(code)
            elif p_mastery >= 0.6:
                on_track.append(code)
            else:
                needs_work.append(code)
                recommended_order.append(code)

        # Sort needs_work by impact (simplified: by mastery probability)
        recommended_order.sort(key=lambda c: next(
            s["p_mastery"] for s in skill_states if s["standard_code"] == c
        ))

        return {
            "strengths": strengths,
            "on_track": on_track,
            "needs_work": needs_work,
            "recommended_focus_order": recommended_order,
        }


# Singleton instance
_assessment_service: Optional[AssessmentService] = None


def get_assessment_service() -> AssessmentService:
    """Get singleton assessment service instance."""
    global _assessment_service
    if _assessment_service is None:
        raise RuntimeError("AssessmentService not initialized")
    return _assessment_service


def initialize_assessment_service(
    assessment_repository: AssessmentRepository,
    session_repository: AssessmentSessionRepository,
    student_repository: StudentRepository,
    standard_repository: StandardRepository,
    question_repository: QuestionRepository,
    consent_repository: ConsentRepository,
) -> AssessmentService:
    """
    Initialize and return assessment service.
    """
    global _assessment_service
    _assessment_service = AssessmentService(
        assessment_repository=assessment_repository,
        session_repository=session_repository,
        student_repository=student_repository,
        standard_repository=standard_repository,
        question_repository=question_repository,
        consent_repository=consent_repository,
        bkt_service=get_bkt_service(),
        cat_service=get_question_selection_service(),
        redis_client=get_redis_client(),
    )
    return _assessment_service
